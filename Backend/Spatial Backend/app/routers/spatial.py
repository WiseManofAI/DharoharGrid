from typing import Dict

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from .. import config
from ..clients import get_supabase
from ..spatial_math import calculate_haversine_distance

router = APIRouter(prefix="/api/v1/spatial", tags=["spatial"])


class LocationScanRequest(BaseModel):
    latitude: float
    longitude: float
    radius_km: float = 10.0
    is_teleport_mode: bool = False
    session_id: str = "default_session"


# Per-session ENTERED / INSIDE / EXITED state. In-memory by design — this is
# a single-process demo service; if it's ever run behind multiple workers,
# swap this for a Redis/Supabase-backed session store instead.
user_state_cache: Dict[str, Dict[str, str]] = {}


def determine_trigger_state(previous_state: str | None, distance_km: float, radius_km: float) -> str:
    outer_boundary_km = radius_km + config.BUFFER_KM

    if distance_km <= radius_km:
        if previous_state in (None, "EXITED"):
            return "ENTERED"
        return "INSIDE"
    elif distance_km > outer_boundary_km:
        return "EXITED"
    else:
        return previous_state if previous_state is not None else "EXITED"


@router.post("/scan")
def scan_location(request: LocationScanRequest):
    supabase = get_supabase()

    try:
        response = (
            supabase.table("cultural_nodes")
            .select("node_id,title,content,latitude,longitude,heritage_group,category")
            .not_.is_("latitude", "null")
            .not_.is_("longitude", "null")
            .is_("merged_into", "null")
            .execute()
        )
    except Exception as e:  # noqa: BLE001
        raise HTTPException(status_code=503, detail=f"Supabase query failed: {e}")

    nodes = response.data or []
    session_cache = user_state_cache.setdefault(request.session_id, {})
    triggered_nodes = []

    for node in nodes:
        distance_km = calculate_haversine_distance(
            request.latitude, request.longitude, node["latitude"], node["longitude"]
        )
        previous_state = session_cache.get(node["node_id"])
        new_state = determine_trigger_state(previous_state, distance_km, request.radius_km)
        session_cache[node["node_id"]] = new_state

        if new_state in ("ENTERED", "INSIDE"):
            triggered_nodes.append(
                {
                    "node_id": node["node_id"],
                    "title": node["title"],
                    "category": node.get("category"),
                    "heritage_group": node.get("heritage_group"),
                    "latitude": node["latitude"],
                    "longitude": node["longitude"],
                    "distance_km": round(distance_km, 2),
                    "trigger_state": new_state,
                }
            )

    return {
        "triggered_nodes": triggered_nodes,
        "count": len(triggered_nodes),
        "user_mode": "teleport" if request.is_teleport_mode else "normal",
    }


@router.post("/reset-session")
def reset_session(session_id: str = "default_session"):
    """Clears a session's ENTERED/INSIDE/EXITED state (e.g. on page reload)."""
    user_state_cache.pop(session_id, None)
    return {"cleared": session_id}
