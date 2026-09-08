"""Step 4: prune duplicate nodes — the same real-world site recorded twice.

Two passes:
  1. Fast, free — group by normalized title (strips parentheticals/case/
     punctuation). Any group of >1 is an unambiguous duplicate (e.g. "Blue
     Pottery of Jaipur" / "Blue Pottery of Jaipur (Logo)").
  2. AI-assisted — among the remaining nodes, find embedding-cosine pairs
     above DEDUPE_COSINE_THRESHOLD that pass 1 did NOT already catch, and
     ask the LLM whether they really describe the same subject (semantic
     near-duplicates with different wording aren't always the same thing —
     two different forts in the same era can be highly similar in embedding
     space without being duplicates, so this is a real judgment call, not a
     threshold auto-merge).

Duplicates are never deleted — merged_into is set to the canonical node's id
and trust_status becomes 'merged_duplicate'. Every read path (the graph API,
the docent RPC) filters merged_into IS NULL, so they simply stop appearing,
but the row and its history stay intact and reversible.
"""
import numpy as np

from .. import config
from ..clients import LLMError, get_supabase, LLMClient
from . import attributes

FETCH_PAGE_SIZE = 200

SYSTEM_PROMPT = (
    "You are verifying whether two heritage-archive records describe the "
    "same real-world site, artifact, or tradition (a duplicate entry), as "
    "opposed to two different things that merely sound or read similarly. "
    "Reply with a JSON object: "
    "{\"same_subject\": true|false, \"reason\": \"one short sentence\"}."
)


def _fetch_all(sb) -> list[dict]:
    rows: list[dict] = []
    offset = 0
    while True:
        page = (
            sb.table("cultural_nodes")
            .select("node_id, title, category, district, content, vector_embedding")
            .is_("merged_into", "null")
            .range(offset, offset + FETCH_PAGE_SIZE - 1)
            .execute()
            .data
        )
        if not page:
            break
        rows.extend(page)
        offset += FETCH_PAGE_SIZE
    return rows


def _merge(sb, duplicate_id: str, canonical_id: str, reason: str):
    sb.table("cultural_nodes").update(
        {"merged_into": canonical_id, "trust_status": "merged_duplicate"}
    ).eq("node_id", duplicate_id).execute()
    print(f"[dedupe] merged {duplicate_id} -> {canonical_id} ({reason})")


def title_pass(sb, rows: list[dict]) -> set[str]:
    groups: dict[str, list[dict]] = {}
    for r in rows:
        key = attributes.normalize_title(r["title"])
        if not key:
            continue
        groups.setdefault(key, []).append(r)

    merged_ids: set[str] = set()
    for key, group in groups.items():
        if len(group) < 2:
            continue
        group.sort(key=lambda r: r["node_id"])
        canonical, *dupes = group
        for dupe in dupes:
            _merge(sb, dupe["node_id"], canonical["node_id"], "identical normalized title")
            merged_ids.add(dupe["node_id"])
    return merged_ids


def embedding_pass(sb, rows: list[dict], already_merged: set[str]) -> int:
    candidates = [r for r in rows if r["node_id"] not in already_merged and r.get("vector_embedding")]
    if len(candidates) < 2:
        print("[dedupe] not enough embedded nodes for the semantic pass yet — run embed.py first.")
        return 0

    ids = [r["node_id"] for r in candidates]
    matrix = np.array([r["vector_embedding"] for r in candidates], dtype=np.float32)
    norms = np.linalg.norm(matrix, axis=1, keepdims=True)
    norms[norms == 0] = 1e-9
    unit = matrix / norms
    sims = unit @ unit.T

    llm = LLMClient()
    merged_now: set[str] = set()
    n = len(candidates)
    checked = 0
    for i in range(n):
        if ids[i] in merged_now:
            continue
        for j in range(i + 1, n):
            if ids[j] in merged_now:
                continue
            score = float(sims[i, j])
            if score < config.DEDUPE_COSINE_THRESHOLD:
                continue

            checked += 1
            a, b = candidates[i], candidates[j]
            prompt = (
                f"Record A — Title: {a['title']}; Category: {a['category']}; "
                f"District: {a.get('district') or 'unknown'}; Content: {a['content']}\n\n"
                f"Record B — Title: {b['title']}; Category: {b['category']}; "
                f"District: {b.get('district') or 'unknown'}; Content: {b['content']}\n\n"
                f"Cosine similarity of their embeddings: {score:.3f}"
            )
            try:
                result = llm.chat_json(SYSTEM_PROMPT, prompt)
            except LLMError as e:
                print(f"[dedupe] SKIP pair {a['node_id']}/{b['node_id']}: {e}")
                continue

            if (result or {}).get("same_subject"):
                canonical, dupe = sorted([a, b], key=lambda r: r["node_id"])
                _merge(sb, dupe["node_id"], canonical["node_id"], result.get("reason", "AI-confirmed duplicate"))
                merged_now.add(dupe["node_id"])

    print(f"[dedupe] checked {checked} high-similarity pair(s) above cosine {config.DEDUPE_COSINE_THRESHOLD}.")
    return len(merged_now)


def run() -> int:
    sb = get_supabase()
    rows = _fetch_all(sb)
    print(f"[dedupe] scanning {len(rows)} active node(s)...")

    merged_by_title = title_pass(sb, rows)
    merged_by_ai = embedding_pass(sb, rows, merged_by_title)

    total = len(merged_by_title) + merged_by_ai
    print(f"[dedupe] done — {total} node(s) merged into a canonical duplicate.")
    return total


if __name__ == "__main__":
    run()
