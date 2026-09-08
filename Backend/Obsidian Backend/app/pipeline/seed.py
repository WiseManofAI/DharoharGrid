"""Step 1: load the raw dataset and upsert it into cultural_nodes.

Structural only — no embeddings, no AI calls. Fast, cheap, safe to re-run
any time (upsert on node_id). Everything downstream depends on this having
run first.
"""
import json

from .. import config
from ..clients import get_supabase
from . import attributes

BATCH_SIZE = 50


def load_raw_nodes() -> list[dict]:
    if not config.RAW_DATASET_PATH.exists():
        raise FileNotFoundError(
            f"Raw dataset not found at {config.RAW_DATASET_PATH}. Expected "
            "map_rough/SIH/rajasthan_master.json at the repo root."
        )
    with open(config.RAW_DATASET_PATH, encoding="utf-8") as f:
        return json.load(f)


def build_row(raw: dict) -> dict | None:
    coords = raw.get("coordinates") or {}
    lat, lng = coords.get("lat"), coords.get("lng")
    if lat is None or lng is None:
        return None

    title = raw.get("title") or "Untitled Node"
    category = raw.get("category") or "TANGIBLE_HERITAGE"
    famous_for = raw.get("famous_for") or ""
    docent_details = raw.get("docent_details") or ""
    media = raw.get("media") or {}

    return {
        "node_id": raw.get("node_id"),
        "title": title,
        "category": category,
        "heritage_group": attributes.group_for_category(category),
        "era": raw.get("era") or None,
        "district": attributes.extract_place(title, famous_for, docent_details),
        "gi_type": attributes.extract_gi_type(docent_details),
        "latitude": float(lat),
        "longitude": float(lng),
        "famous_for": famous_for or None,
        "docent_details": docent_details or None,
        "nearby_culture": raw.get("nearby_culture") or None,
        "content": docent_details or famous_for or f"{title} is a documented cultural node in Rajasthan.",
        "content_source": "original",
        "trust_status": raw.get("trust_status") or "verified",
        "photo_url": (media.get("photo_url") or "").strip() or None,
        "source_refs": raw.get("source_refs") or None,
    }


def run(dry_run: bool = False) -> int:
    raw_nodes = load_raw_nodes()
    rows = [r for r in (build_row(n) for n in raw_nodes) if r and r["node_id"]]
    print(f"[seed] {len(rows)}/{len(raw_nodes)} raw nodes have usable coordinates + id.")

    if dry_run:
        return len(rows)

    sb = get_supabase()

    # Re-running seed must never clobber work later pipeline steps already
    # did (enrich.py's rewritten content, dedupe.py's merged_into). Find
    # rows that have already been improved and strip the fields seed.py
    # doesn't own from their payload before upserting, so PostgREST's
    # upsert leaves those columns untouched instead of resetting them.
    existing = (
        sb.table("cultural_nodes")
        .select("node_id, content_source, merged_into")
        .execute()
        .data
    )
    already_enriched = {r["node_id"] for r in existing if r.get("content_source") == "ai_enriched"}
    already_merged = {r["node_id"] for r in existing if r.get("merged_into")}

    for row in rows:
        if row["node_id"] in already_enriched:
            row.pop("content", None)
            row.pop("content_source", None)
        if row["node_id"] in already_merged:
            # A prior dedupe pass already decided this node is a duplicate;
            # don't resurrect it by re-upserting its full row.
            row.pop("trust_status", None)

    written = 0
    for i in range(0, len(rows), BATCH_SIZE):
        batch = rows[i : i + BATCH_SIZE]
        sb.table("cultural_nodes").upsert(batch, on_conflict="node_id").execute()
        written += len(batch)
        print(f"[seed] upserted {written}/{len(rows)}")

    return written


if __name__ == "__main__":
    run()
