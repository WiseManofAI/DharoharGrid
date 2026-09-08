"""Step 6: form the AI-reasoned synapse edges (Master Spec §5, Feature 2).

Two stages, matching the spec's own description of how this should work at
scale ("embeddings -> offline batch cosine similarity -> LLM articulates
what's shared"):

  1. Candidate generation — real embedding cosine similarity (numpy, exact,
     not approximate) picks each node's top-K nearest neighbors above
     SYNAPSE_MIN_COSINE. Cheap, deterministic, no LLM cost.
  2. AI adjudication — the LLM is handed each candidate pair's actual
     content (plus structured hints: shared district/era/GI-type/heritage
     group) and DECIDES whether a genuine connection exists, at what
     confidence tier, and writes the one-line rationale. This is the model
     actually reading and reasoning about the nodes, not a keyword score
     being relabelled — reject is a valid, expected outcome.

Batched SYNAPSE_BATCH_SIZE pairs per LLM call for throughput. Resumable: any
pair already present in synapse_edges is skipped, so an interrupted run can
just be re-started.
"""
import numpy as np

from .. import config
from ..clients import LLMError, get_supabase, LLMClient
from . import attributes

FETCH_PAGE_SIZE = 200
VALID_TIERS = {"verified", "source_supported", "potential", "contradictory"}

SYSTEM_PROMPT = (
    "You are a research assistant for a cultural-heritage knowledge graph. "
    "You will be shown pairs of heritage-archive records and must decide, "
    "for EACH pair independently, whether there is a genuine, worthwhile "
    "connection between them.\n\n"
    "Ground every judgment ONLY in the facts given for that pair — never "
    "use outside historical knowledge, never invent a relationship. Most "
    "pairs should be rejected (connect=false); only flag a connection when "
    "the given facts actually support one.\n\n"
    "Tiers:\n"
    "- source_supported: the facts given directly establish the link (same "
    "district AND same protection/registration status, same specific "
    "documented era, same GI craft family with an explicit registry fact).\n"
    "- potential: a plausible, evidence-adjacent research lead — thematically "
    "or geographically related, but the given facts don't fully establish "
    "the link. Phrase the rationale as a lead for a researcher to "
    "investigate, never as an established relationship.\n"
    "- contradictory: the facts given actually conflict with each other.\n"
    "- verified: only if the facts make the connection essentially certain.\n\n"
    "Reply with a JSON object: {\"results\": [{\"index\": 0, \"connect\": "
    "true|false, \"tier\": \"source_supported\"|\"potential\"|\"verified\"|"
    "\"contradictory\", \"rationale\": \"one grounded sentence, or empty "
    "string if connect is false\"}, ...]} — one entry per pair, in order."
)


def _fetch_active_nodes(sb) -> list[dict]:
    rows: list[dict] = []
    offset = 0
    while True:
        page = (
            sb.table("cultural_nodes")
            .select("node_id, title, category, heritage_group, era, district, gi_type, content, vector_embedding")
            .is_("merged_into", "null")
            .range(offset, offset + FETCH_PAGE_SIZE - 1)
            .execute()
            .data
        )
        if not page:
            break
        rows.extend(page)
        offset += FETCH_PAGE_SIZE
    return [r for r in rows if r.get("vector_embedding")]


def _fetch_existing_edge_keys(sb) -> set[tuple[str, str]]:
    rows: list[dict] = []
    offset = 0
    while True:
        page = (
            sb.table("synapse_edges")
            .select("source_id, target_id")
            .range(offset, offset + FETCH_PAGE_SIZE - 1)
            .execute()
            .data
        )
        if not page:
            break
        rows.extend(page)
        offset += FETCH_PAGE_SIZE
    return {(r["source_id"], r["target_id"]) for r in rows}


def _candidate_pairs(nodes: list[dict]) -> list[tuple[int, int, float]]:
    matrix = np.array([n["vector_embedding"] for n in nodes], dtype=np.float32)
    norms = np.linalg.norm(matrix, axis=1, keepdims=True)
    norms[norms == 0] = 1e-9
    unit = matrix / norms
    sims = unit @ unit.T
    np.fill_diagonal(sims, -1.0)

    n = len(nodes)
    pairs: dict[tuple[int, int], float] = {}
    for i in range(n):
        top_k_idx = np.argpartition(-sims[i], min(config.SYNAPSE_TOP_K, n - 1))[: config.SYNAPSE_TOP_K]
        for j in top_k_idx:
            j = int(j)
            score = float(sims[i, j])
            if score < config.SYNAPSE_MIN_COSINE:
                continue
            key = (i, j) if i < j else (j, i)
            if key not in pairs or score > pairs[key]:
                pairs[key] = score
    return [(i, j, score) for (i, j), score in pairs.items()]


def _hints(a: dict, b: dict) -> str:
    hints = []
    if a.get("district") and a["district"] == b.get("district"):
        hints.append(f"same district ({a['district']})")
    if a.get("era") and a["era"] == b.get("era"):
        hints.append(f"same specific era ({a['era']})")
    if a.get("gi_type") and a["gi_type"] == b.get("gi_type"):
        hints.append(f"same GI type ({a['gi_type']})")
    if a.get("heritage_group") == b.get("heritage_group"):
        hints.append("same heritage group")
    return "; ".join(hints) if hints else "no structural overlap detected"


def _describe(node: dict) -> str:
    return (
        f"Title: {node['title']}; Category: {attributes.pretty_category(node.get('category'))}; "
        f"District: {node.get('district') or 'unknown'}; Era: {node.get('era') or 'unspecified'}; "
        f"Content: {node['content']}"
    )


def run() -> int:
    sb = get_supabase()
    nodes = _fetch_active_nodes(sb)
    print(f"[synapse] {len(nodes)} embedded active node(s).")
    if len(nodes) < 2:
        print("[synapse] not enough embedded nodes yet — run embed.py first.")
        return 0

    existing_keys = _fetch_existing_edge_keys(sb)
    raw_pairs = _candidate_pairs(nodes)
    print(f"[synapse] {len(raw_pairs)} candidate pair(s) above cosine {config.SYNAPSE_MIN_COSINE} (top-{config.SYNAPSE_TOP_K}/node).")

    pending = []
    for i, j, score in raw_pairs:
        a, b = nodes[i], nodes[j]
        src, tgt = sorted([a["node_id"], b["node_id"]])
        if (src, tgt) in existing_keys:
            continue
        pending.append((a, b, score, src, tgt))

    print(f"[synapse] {len(pending)} pair(s) not yet adjudicated.")
    if not pending:
        return 0

    llm = LLMClient()
    formed = 0
    batch_size = config.SYNAPSE_BATCH_SIZE

    for i in range(0, len(pending), batch_size):
        batch = pending[i : i + batch_size]
        prompt_parts = []
        for idx, (a, b, score, _src, _tgt) in enumerate(batch):
            prompt_parts.append(
                f"Pair {idx}:\n"
                f"Node A — {_describe(a)}\n"
                f"Node B — {_describe(b)}\n"
                f"Embedding cosine similarity: {score:.3f}\n"
                f"Structural overlap: {_hints(a, b)}"
            )
        user_prompt = "\n\n".join(prompt_parts)

        try:
            result = llm.chat_json(SYSTEM_PROMPT, user_prompt)
        except LLMError as e:
            print(f"[synapse] SKIP batch {i}-{i+len(batch)}: {e}")
            continue

        results = (result or {}).get("results", [])
        by_index = {r.get("index"): r for r in results if isinstance(r, dict)}

        edge_rows = []
        for idx, (a, b, score, src, tgt) in enumerate(batch):
            verdict = by_index.get(idx)
            if not verdict or not verdict.get("connect"):
                continue
            tier = verdict.get("tier")
            rationale = (verdict.get("rationale") or "").strip()
            if tier not in VALID_TIERS or not rationale:
                print(f"[synapse] SKIP malformed verdict for {a['node_id']}/{b['node_id']}")
                continue
            edge_rows.append(
                {
                    "source_id": src,
                    "target_id": tgt,
                    "tier": tier,
                    "score": round(score, 4),
                    "rationale": rationale,
                    "formed_by": "ai_pipeline",
                }
            )

        if edge_rows:
            sb.table("synapse_edges").upsert(edge_rows, on_conflict="source_id,target_id").execute()
            formed += len(edge_rows)

        print(f"[synapse] processed {min(i + batch_size, len(pending))}/{len(pending)} pairs, {formed} edge(s) formed so far.")

    print(f"[synapse] done — {formed} synapse edge(s) formed.")
    return formed


if __name__ == "__main__":
    run()
