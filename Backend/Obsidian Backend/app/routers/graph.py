"""Read-only API over the pipeline's precomputed output.

Nothing here does any AI/embedding work at request time — that all already
happened in the pipeline (see app/pipeline/build_graph.py) and lives in
Supabase. This layer just serves it, with a short in-process TTL cache so
concurrent Discover page loads don't each re-query Supabase — the graph only
changes when the pipeline reruns.
"""
import time

from fastapi import APIRouter, HTTPException

from .. import config
from ..clients import get_supabase

router = APIRouter(prefix="/api/v1/graph", tags=["graph"])

_cache: dict[str, tuple[float, object]] = {}


def _cached(key: str, builder):
    now = time.time()
    hit = _cache.get(key)
    if hit and now - hit[0] < config.GRAPH_CACHE_TTL_SECONDS:
        return hit[1]
    value = builder()
    _cache[key] = (now, value)
    return value


def _fetch_nodes() -> list[dict]:
    sb = get_supabase()
    rows: list[dict] = []
    offset = 0
    page_size = 500
    while True:
        page = (
            sb.table("cultural_nodes")
            .select(
                "node_id, title, category, heritage_group, era, district, "
                "latitude, longitude, content, content_source, trust_status, photo_url"
            )
            .is_("merged_into", "null")
            .range(offset, offset + page_size - 1)
            .execute()
            .data
        )
        if not page:
            break
        rows.extend(page)
        offset += page_size
    return rows


def _fetch_clusters() -> list[dict]:
    sb = get_supabase()
    return sb.table("clusters").select("cluster_id, name, kind, parent_id, description").execute().data


def _fetch_node_clusters() -> list[dict]:
    sb = get_supabase()
    rows: list[dict] = []
    offset = 0
    page_size = 1000
    while True:
        page = (
            sb.table("node_clusters")
            .select("node_id, cluster_id")
            .range(offset, offset + page_size - 1)
            .execute()
            .data
        )
        if not page:
            break
        rows.extend(page)
        offset += page_size
    return rows


def _fetch_edges() -> list[dict]:
    sb = get_supabase()
    rows: list[dict] = []
    offset = 0
    page_size = 1000
    while True:
        page = (
            sb.table("synapse_edges")
            .select("edge_id, source_id, target_id, tier, score, rationale")
            .range(offset, offset + page_size - 1)
            .execute()
            .data
        )
        if not page:
            break
        rows.extend(page)
        offset += page_size
    return rows


@router.get("/nodes")
def get_nodes():
    try:
        return _cached("nodes", _fetch_nodes)
    except Exception as e:  # noqa: BLE001
        raise HTTPException(status_code=503, detail=f"Graph backend unavailable: {e}")


@router.get("/clusters")
def get_clusters():
    try:
        return _cached("clusters", _fetch_clusters)
    except Exception as e:  # noqa: BLE001
        raise HTTPException(status_code=503, detail=f"Graph backend unavailable: {e}")


@router.get("/edges")
def get_edges():
    try:
        return _cached("edges", _fetch_edges)
    except Exception as e:  # noqa: BLE001
        raise HTTPException(status_code=503, detail=f"Graph backend unavailable: {e}")


@router.get("/full")
def get_full_graph():
    """One round trip for the Discover frontend: nodes + clusters + node-
    cluster membership + synapse edges."""
    try:
        nodes = _cached("nodes", _fetch_nodes)
        clusters = _cached("clusters", _fetch_clusters)
        node_clusters = _cached("node_clusters", _fetch_node_clusters)
        edges = _cached("edges", _fetch_edges)
    except Exception as e:  # noqa: BLE001
        raise HTTPException(status_code=503, detail=f"Graph backend unavailable: {e}")

    if not nodes:
        raise HTTPException(
            status_code=503,
            detail="Graph is empty — the pipeline hasn't been run yet "
            "(python -m app.pipeline.build_graph).",
        )

    return {
        "nodes": nodes,
        "clusters": clusters,
        "node_clusters": node_clusters,
        "edges": edges,
        "generated_from_cache": True,
    }
