"""Community contribution intake + admin review.

Security note (being honest about it rather than pretending otherwise): this
whole project's "admin login" is a client-side check in index.html with no
real backend session/token — matching that existing scope, these endpoints
don't enforce server-side admin auth either. Don't point this at a public
deployment without adding real auth first; that's a pre-existing property of
the project, not something this feature introduces.
"""
import uuid

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from pydantic import BaseModel

from ..clients import get_supabase
from ..pipeline import taxonomy
from ..pipeline.incremental import promote_submission

router = APIRouter(prefix="/api/v1/submissions", tags=["submissions"])

BUCKET = "community-photos"
ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif"}
MAX_PHOTO_BYTES = 8 * 1024 * 1024  # 8MB


@router.get("/categories")
def list_categories():
    """The taxonomy's known category strings, for the admin dashboard's
    category picker — one source of truth, no hand-duplicated list."""
    return sorted(set(taxonomy.SUBTYPE_RULES.keys()))


@router.post("")
async def create_submission(
    title: str = Form(...),
    description: str = Form(...),
    latitude: float = Form(...),
    longitude: float = Form(...),
    category_guess: str | None = Form(None),
    contributor_name: str | None = Form(None),
    contributor_note: str | None = Form(None),
    photo: UploadFile | None = File(None),
):
    if not title.strip() or not description.strip():
        raise HTTPException(status_code=400, detail="title and description are required.")

    sb = get_supabase()
    photo_path = None

    if photo is not None:
        if photo.content_type not in ALLOWED_IMAGE_TYPES:
            raise HTTPException(status_code=400, detail=f"Unsupported photo type: {photo.content_type}")
        data = await photo.read()
        if len(data) > MAX_PHOTO_BYTES:
            raise HTTPException(status_code=400, detail="Photo too large (max 8MB).")
        ext = (photo.filename or "").split(".")[-1][:5] or "jpg"
        photo_path = f"{uuid.uuid4().hex}.{ext}"
        try:
            sb.storage.from_(BUCKET).upload(photo_path, data, {"content-type": photo.content_type})
        except Exception as e:  # noqa: BLE001
            raise HTTPException(status_code=502, detail=f"Photo upload failed: {e}")

    row = {
        "title": title.strip(),
        "description": description.strip(),
        "category": category_guess,
        "latitude": latitude,
        "longitude": longitude,
        "photo_path": photo_path,
        "contributor_name": (contributor_name or "").strip() or None,
        "contributor_note": (contributor_note or "").strip() or None,
        "status": "pending",
    }
    try:
        result = sb.table("community_submissions").insert(row).execute()
    except Exception as e:  # noqa: BLE001
        raise HTTPException(status_code=503, detail=f"Could not save submission: {e}")

    return result.data[0]


def _with_photo_url(sb, row: dict) -> dict:
    if row.get("photo_path"):
        row["photo_url"] = sb.storage.from_(BUCKET).get_public_url(row["photo_path"])
    else:
        row["photo_url"] = None
    return row


@router.get("")
def list_submissions(status: str = "pending"):
    sb = get_supabase()
    try:
        rows = (
            sb.table("community_submissions")
            .select("*")
            .eq("status", status)
            .order("created_at", desc=True)
            .execute()
            .data
        )
    except Exception as e:  # noqa: BLE001
        raise HTTPException(status_code=503, detail=f"Could not list submissions: {e}")
    return [_with_photo_url(sb, r) for r in rows]


class TagUpdate(BaseModel):
    category: str | None = None
    tags: list[str] | None = None


@router.patch("/{submission_id}")
def update_submission(submission_id: str, patch: TagUpdate):
    sb = get_supabase()
    updates = {k: v for k, v in patch.model_dump().items() if v is not None}
    if not updates:
        raise HTTPException(status_code=400, detail="Nothing to update.")
    result = sb.table("community_submissions").update(updates).eq("submission_id", submission_id).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Submission not found.")
    return _with_photo_url(sb, result.data[0])


@router.post("/{submission_id}/reject")
def reject_submission(submission_id: str, reviewed_by: str = "admin"):
    sb = get_supabase()
    result = (
        sb.table("community_submissions")
        .update({"status": "rejected", "reviewed_by": reviewed_by, "reviewed_at": "now()"})
        .eq("submission_id", submission_id)
        .execute()
    )
    if not result.data:
        raise HTTPException(status_code=404, detail="Submission not found.")
    return result.data[0]


@router.post("/{submission_id}/approve")
def approve_submission(submission_id: str, reviewed_by: str = "admin"):
    sb = get_supabase()
    rows = sb.table("community_submissions").select("*").eq("submission_id", submission_id).execute().data
    if not rows:
        raise HTTPException(status_code=404, detail="Submission not found.")
    submission = rows[0]
    if submission["status"] != "pending":
        raise HTTPException(status_code=409, detail=f"Submission is already {submission['status']}.")

    submission = _with_photo_url(sb, submission)

    try:
        outcome = promote_submission(submission)
    except Exception as e:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=f"AI evaluation failed: {e}")

    sb.table("community_submissions").update(
        {
            "status": "approved",
            "reviewed_by": reviewed_by,
            "reviewed_at": "now()",
            "promoted_node_id": outcome["node_id"] if outcome["status"] == "added" else outcome["merged_into"],
        }
    ).eq("submission_id", submission_id).execute()

    return {"submission_id": submission_id, **outcome}
