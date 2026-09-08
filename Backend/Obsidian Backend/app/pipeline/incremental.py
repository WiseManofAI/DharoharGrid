"""Promotes one approved community submission into a fully-processed graph
node — the same AI steps build_graph.py runs in bulk (enrich, embed, dedupe,
cluster, synapse), just scoped to a single new node so it's fast enough to
run synchronously from the admin dashboard's Approve click instead of
waiting for the next full pipeline run.
"""
import re
import uuid

import numpy as np

from .. import config
from ..clients import LLMError, get_embedder, get_supabase, LLMClient
from . import attributes, taxonomy
from .synapse import _describe, _hints, VALID_TIERS  # reuse the exact adjudication shape

DEDUPE_SYSTEM_PROMPT = (
    "You are verifying whether two heritage-archive records describe the "
    "same real-world site, artifact, or tradition (a duplicate entry), as "
    "opposed to two different things that merely sound or read similarly. "
    "Reply with a JSON object: "
    '{"same_subject": true|false, "reason": "one short sentence"}.'
)

SYNAPSE_SYSTEM_PROMPT = (
    "You are a research assistant for a cultural-heritage knowledge graph. "
    "You will be shown candidate connections between ONE new node and "
    "several existing nodes, and must decide, for EACH pair independently, "
    "whether there is a genuine, worthwhile connection.\n\n"
    "Ground every judgment ONLY in the facts given — never use outside "
    "historical knowledge, never invent a relationship. Most pairs should "
    "be rejected (connect=false).\n\n"
    "Tiers: source_supported (facts directly establish the link), "
    "potential (a plausible research lead, phrase it as a lead, not a "
    "fact), contradictory (facts conflict), verified (essentially certain).\n\n"
    'Reply with a JSON object: {"results": [{"index": 0, "connect": '
    'true|false, "tier": "...", "rationale": "one grounded sentence, or '
    'empty string if connect is false"}, ...]}'
)


def slugify(title: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
    return f"community-{slug[:40]}-{uuid.uuid4().hex[:6]}"


def _enrich_if_needed(sb, node: dict) -> str:
    """Rewrites the content if it's too thin — same rule as pipeline/enrich.py."""
    if not attributes.is_boilerplate(node.get("famous_for") or "", node.get("docent_details") or ""):
        return node["content"]

    llm = LLMClient()
    prompt = (
        f"Title: {node['title']}\n"
        f"Category: {attributes.pretty_category(node.get('category'))}\n"
        f"District: {node.get('district') or 'unknown'}\n"
        f"Community-submitted note: {node.get('famous_for') or node['content']}"
    )
    system = (
        "Rewrite this community-submitted heritage note into a clean 2-4 "
        "sentence description. Preserve every fact given — do not invent "
        "new ones. Reply with JSON: {\"description\": \"...\"}"
    )
    try:
        result = llm.chat_json(system, prompt)
        description = (result or {}).get("description", "").strip()
        return description or node["content"]
    except LLMError:
        return node["content"]


def _dedupe_check(sb, node: dict, embedding: list[float]) -> str | None:
    """Returns the canonical node_id this duplicates, or None if it's unique."""
    norm_title = attributes.normalize_title(node["title"])

    existing = (
        sb.table("cultural_nodes")
        .select("node_id, title, category, district, content")
        .is_("merged_into", "null")
        .execute()
        .data
    )
    for other in existing:
        if attributes.normalize_title(other["title"]) == norm_title and norm_title:
            return other["node_id"]

    # Embedding pass against everyone with a vector, same threshold as the
    # bulk dedupe step.
    embedded = [
        e for e in sb.table("cultural_nodes")
        .select("node_id, title, category, district, content, vector_embedding")
        .is_("merged_into", "null")
        .execute()
        .data
        if e.get("vector_embedding")
    ]
    if not embedded:
        return None

    matrix = np.array([e["vector_embedding"] for e in embedded], dtype=np.float32)
    vec = np.array(embedding, dtype=np.float32)
    norms = np.linalg.norm(matrix, axis=1) * (np.linalg.norm(vec) or 1e-9)
    norms[norms == 0] = 1e-9
    sims = (matrix @ vec) / norms

    llm = LLMClient()
    for other, score in zip(embedded, sims):
        if float(score) < config.DEDUPE_COSINE_THRESHOLD:
            continue
        prompt = (
            f"Record A — Title: {node['title']}; Category: {node.get('category')}; "
            f"District: {node.get('district') or 'unknown'}; Content: {node['content']}\n\n"
            f"Record B — Title: {other['title']}; Category: {other.get('category')}; "
            f"District: {other.get('district') or 'unknown'}; Content: {other['content']}\n\n"
            f"Cosine similarity: {float(score):.3f}"
        )
        try:
            result = llm.chat_json(DEDUPE_SYSTEM_PROMPT, prompt)
        except LLMError:
            continue
        if (result or {}).get("same_subject"):
            return other["node_id"]
    return None


def _assign_clusters(sb, node: dict):
    root_id, root_name, root_kind, root_parent, root_desc = taxonomy.ROOT_CLUSTER
    heritage_cid, heritage_name, heritage_desc = taxonomy.HERITAGE_TYPE_CLUSTERS[node["heritage_group"]]
    subtype_id, subtype_name = taxonomy.subtype_for(node["category"])
    era_id, era_name = taxonomy.era_band_for(node.get("era"))

    cluster_rows = [
        {"cluster_id": root_id, "name": root_name, "kind": root_kind, "parent_id": root_parent, "description": root_desc},
        {"cluster_id": heritage_cid, "name": heritage_name, "kind": "heritage_type", "parent_id": root_id, "description": heritage_desc},
        {"cluster_id": subtype_id, "name": subtype_name, "kind": "subtype", "parent_id": heritage_cid, "description": ""},
        {"cluster_id": era_id, "name": era_name, "kind": "era_band", "parent_id": root_id, "description": ""},
    ]
    membership = [
        (node["node_id"], root_id),
        (node["node_id"], heritage_cid),
        (node["node_id"], subtype_id),
        (node["node_id"], era_id),
    ]

    if node.get("district"):
        dist_id, dist_name = taxonomy.district_cluster_for(node["district"])
        cluster_rows.append({"cluster_id": dist_id, "name": dist_name, "kind": "district", "parent_id": root_id, "description": ""})
        membership.append((node["node_id"], dist_id))

    craft = taxonomy.craft_family_for(node["title"])
    if craft:
        craft_id, craft_name = craft
        cluster_rows.append({"cluster_id": craft_id, "name": craft_name, "kind": "craft_family", "parent_id": None, "description": ""})
        membership.append((node["node_id"], craft_id))

    sb.table("clusters").upsert(cluster_rows, on_conflict="cluster_id").execute()
    sb.table("node_clusters").upsert(
        [{"node_id": n, "cluster_id": c} for n, c in membership], on_conflict="node_id,cluster_id"
    ).execute()


def _form_synapses(sb, node: dict, embedding: list[float]):
    others = [
        o for o in sb.table("cultural_nodes")
        .select("node_id, title, category, heritage_group, era, district, gi_type, content, vector_embedding")
        .is_("merged_into", "null")
        .neq("node_id", node["node_id"])
        .execute()
        .data
        if o.get("vector_embedding")
    ]
    if not others:
        return 0

    matrix = np.array([o["vector_embedding"] for o in others], dtype=np.float32)
    vec = np.array(embedding, dtype=np.float32)
    denom = np.linalg.norm(matrix, axis=1) * (np.linalg.norm(vec) or 1e-9)
    denom[denom == 0] = 1e-9
    sims = (matrix @ vec) / denom

    ranked = sorted(zip(others, sims), key=lambda x: -x[1])[: config.SYNAPSE_TOP_K]
    candidates = [(o, float(s)) for o, s in ranked if s >= config.SYNAPSE_MIN_COSINE]
    if not candidates:
        return 0

    llm = LLMClient()
    prompt_parts = []
    for idx, (other, score) in enumerate(candidates):
        prompt_parts.append(
            f"Pair {idx}:\nNode A — {_describe(node)}\nNode B — {_describe(other)}\n"
            f"Embedding cosine similarity: {score:.3f}\nStructural overlap: {_hints(node, other)}"
        )
    try:
        result = llm.chat_json(SYNAPSE_SYSTEM_PROMPT, "\n\n".join(prompt_parts))
    except LLMError:
        return 0

    by_index = {r.get("index"): r for r in (result or {}).get("results", []) if isinstance(r, dict)}
    edge_rows = []
    for idx, (other, score) in enumerate(candidates):
        verdict = by_index.get(idx)
        if not verdict or not verdict.get("connect"):
            continue
        tier = verdict.get("tier")
        rationale = (verdict.get("rationale") or "").strip()
        if tier not in VALID_TIERS or not rationale:
            continue
        src, tgt = sorted([node["node_id"], other["node_id"]])
        edge_rows.append(
            {"source_id": src, "target_id": tgt, "tier": tier, "score": round(score, 4), "rationale": rationale, "formed_by": "ai_pipeline"}
        )

    if edge_rows:
        sb.table("synapse_edges").upsert(edge_rows, on_conflict="source_id,target_id").execute()
    return len(edge_rows)


def promote_submission(submission: dict) -> dict:
    """Turns an approved community_submissions row into a live, connected
    cultural_nodes row. Returns {status, node_id, merged_into?, edges_formed}."""
    sb = get_supabase()

    category = submission.get("category") or "TANGIBLE_HERITAGE"
    title = submission["title"]
    description = submission["description"]
    node_id = slugify(title)

    node = {
        "node_id": node_id,
        "title": title,
        "category": category,
        "heritage_group": attributes.group_for_category(category),
        "era": None,
        "district": attributes.extract_place(title, description, ""),
        "gi_type": None,
        "latitude": submission.get("latitude"),
        "longitude": submission.get("longitude"),
        "famous_for": description,
        "docent_details": description,
        "nearby_culture": submission.get("contributor_note"),
        "content": description,
        "content_source": "original",
        "trust_status": "community_contributed",
        "photo_url": submission.get("photo_url"),
        "source_refs": {"contributor": submission.get("contributor_name") or "anonymous", "submission_id": submission["submission_id"]},
    }

    node["content"] = _enrich_if_needed(sb, node)
    if node["content"] != description:
        node["content_source"] = "ai_enriched"

    embedder = get_embedder()
    embedding = embedder.encode(node["content"]).tolist()

    duplicate_of = _dedupe_check(sb, node, embedding)
    if duplicate_of:
        return {"status": "merged", "node_id": node_id, "merged_into": duplicate_of, "edges_formed": 0}

    node["vector_embedding"] = embedding
    sb.table("cultural_nodes").insert(node).execute()

    _assign_clusters(sb, node)
    edges_formed = _form_synapses(sb, node, embedding)

    return {"status": "added", "node_id": node_id, "merged_into": None, "edges_formed": edges_formed}
