"""Step 5: build the supercluster/subcluster taxonomy and assign membership.

Every active (non-merged) node gets: root + heritage_type + subtype +
era_band always, plus district and craft_family when the data supports one.
Purely rule-based (see taxonomy.py) — deterministic and free, no LLM calls,
so it's safe to re-run any time the underlying node data changes.
"""
from ..clients import get_supabase
from . import taxonomy

FETCH_PAGE_SIZE = 200
UPSERT_BATCH_SIZE = 200


def _upsert_cluster(clusters_by_id: dict, cluster_id: str, name: str, kind: str, parent_id: str | None, description: str = ""):
    clusters_by_id[cluster_id] = {
        "cluster_id": cluster_id,
        "name": name,
        "kind": kind,
        "parent_id": parent_id,
        "description": description,
    }


def _fetch_all_nodes(sb) -> list[dict]:
    rows: list[dict] = []
    offset = 0
    while True:
        page = (
            sb.table("cultural_nodes")
            .select("node_id, title, category, heritage_group, era, district")
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


def run() -> tuple[int, int]:
    sb = get_supabase()
    nodes = _fetch_all_nodes(sb)
    print(f"[cluster] assigning taxonomy for {len(nodes)} active node(s)...")

    clusters_by_id: dict[str, dict] = {}
    root_id, root_name, root_kind, root_parent, root_desc = taxonomy.ROOT_CLUSTER
    _upsert_cluster(clusters_by_id, root_id, root_name, root_kind, root_parent, root_desc)

    for group, (cid, name, desc) in taxonomy.HERITAGE_TYPE_CLUSTERS.items():
        _upsert_cluster(clusters_by_id, cid, name, "heritage_type", root_id, desc)

    membership: list[tuple[str, str]] = []  # (node_id, cluster_id)

    for node in nodes:
        node_id = node["node_id"]
        group = node.get("heritage_group") or "tangible"
        heritage_cid = taxonomy.HERITAGE_TYPE_CLUSTERS.get(group, taxonomy.HERITAGE_TYPE_CLUSTERS["tangible"])[0]

        membership.append((node_id, root_id))
        membership.append((node_id, heritage_cid))

        subtype_id, subtype_name = taxonomy.subtype_for(node.get("category"))
        _upsert_cluster(clusters_by_id, subtype_id, subtype_name, "subtype", heritage_cid)
        membership.append((node_id, subtype_id))

        era_id, era_name = taxonomy.era_band_for(node.get("era"))
        _upsert_cluster(clusters_by_id, era_id, era_name, "era_band", root_id)
        membership.append((node_id, era_id))

        if node.get("district"):
            dist_id, dist_name = taxonomy.district_cluster_for(node["district"])
            _upsert_cluster(clusters_by_id, dist_id, dist_name, "district", root_id)
            membership.append((node_id, dist_id))

        craft = taxonomy.craft_family_for(node.get("title"))
        if craft:
            craft_id, craft_name = craft
            _upsert_cluster(clusters_by_id, craft_id, craft_name, "craft_family", None)
            membership.append((node_id, craft_id))

    cluster_rows = list(clusters_by_id.values())
    for i in range(0, len(cluster_rows), UPSERT_BATCH_SIZE):
        sb.table("clusters").upsert(cluster_rows[i : i + UPSERT_BATCH_SIZE], on_conflict="cluster_id").execute()
    print(f"[cluster] upserted {len(cluster_rows)} cluster(s).")

    # node_clusters has no natural "update" — clear and rewrite membership
    # for the nodes we just processed so removed memberships don't linger.
    node_ids = [n["node_id"] for n in nodes]
    for i in range(0, len(node_ids), UPSERT_BATCH_SIZE):
        chunk = node_ids[i : i + UPSERT_BATCH_SIZE]
        sb.table("node_clusters").delete().in_("node_id", chunk).execute()

    membership_rows = [{"node_id": n, "cluster_id": c} for n, c in membership]
    for i in range(0, len(membership_rows), UPSERT_BATCH_SIZE):
        sb.table("node_clusters").upsert(
            membership_rows[i : i + UPSERT_BATCH_SIZE], on_conflict="node_id,cluster_id"
        ).execute()
    print(f"[cluster] wrote {len(membership_rows)} node-cluster membership row(s).")

    return len(cluster_rows), len(membership_rows)


if __name__ == "__main__":
    run()
