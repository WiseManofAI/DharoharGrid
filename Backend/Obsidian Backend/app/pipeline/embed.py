"""Step 3: embed every node whose vector_embedding is missing.

Runs after enrich.py (step 2), which nulls out vector_embedding on any row
it rewrites the content of — so this step naturally re-embeds improved text
without needing to touch untouched rows. Batched through the model for
throughput; batched to Supabase in chunks to stay under request-size limits.
"""
from ..clients import get_embedder, get_supabase

FETCH_PAGE_SIZE = 200
UPDATE_BATCH_SIZE = 25


def run() -> int:
    sb = get_supabase()
    model = get_embedder()

    pending: list[dict] = []
    offset = 0
    while True:
        page = (
            sb.table("cultural_nodes")
            .select("node_id, content")
            .is_("vector_embedding", "null")
            .is_("merged_into", "null")
            .range(offset, offset + FETCH_PAGE_SIZE - 1)
            .execute()
            .data
        )
        if not page:
            break
        pending.extend(page)
        offset += FETCH_PAGE_SIZE

    if not pending:
        print("[embed] nothing to embed — all nodes already have vectors.")
        return 0

    print(f"[embed] embedding {len(pending)} node(s)...")
    texts = [f"{p['content']}" for p in pending]
    vectors = model.encode(texts, show_progress_bar=False, batch_size=32).tolist()

    updated = 0
    for i in range(0, len(pending), UPDATE_BATCH_SIZE):
        chunk = list(zip(pending[i : i + UPDATE_BATCH_SIZE], vectors[i : i + UPDATE_BATCH_SIZE]))
        for node, vec in chunk:
            sb.table("cultural_nodes").update({"vector_embedding": vec}).eq(
                "node_id", node["node_id"]
            ).execute()
        updated += len(chunk)
        print(f"[embed] {updated}/{len(pending)}")

    return updated


if __name__ == "__main__":
    run()
