import re
import shutil
import uuid

from fastapi import APIRouter, File, HTTPException, Response, UploadFile

from app.config import STORAGE_PATH
from app.services import scheduler, video_service

router = APIRouter()
ALLOWED = {".mp4", ".mov", ".mkv", ".webm", ".avi", ".m4v"}


def _result_or_404(video_id: str):
    res = scheduler.get_result(video_id)
    if res is None:
        raise HTTPException(404, "No analysis for this video yet — run analyze first")
    return res


@router.get("/videos")
def list_videos():
    out = []
    for m in video_service.list_videos():
        d = m.model_dump(exclude={"filepath"})
        d["status"] = scheduler.get_status(m.video_id).status
        out.append(d)
    return out


@router.post("/videos/upload")
def upload_video(file: UploadFile = File(...)):
    name = re.sub(r"[^\w.\-]+", "_", file.filename or "video.mp4")
    if not any(name.lower().endswith(ext) for ext in ALLOWED):
        raise HTTPException(400, f"Unsupported file type. Allowed: {', '.join(sorted(ALLOWED))}")
    video_id = uuid.uuid4().hex[:8]
    dest = STORAGE_PATH / "uploads" / f"{video_id}_{name}"
    with open(dest, "wb") as out:
        shutil.copyfileobj(file.file, out)
    try:
        meta = video_service.register_video(video_id, name, str(dest))
    except Exception as e:
        dest.unlink(missing_ok=True)
        raise HTTPException(400, str(e))
    return {"video_id": meta.video_id, "filename": meta.filename,
            "duration_seconds": meta.duration_seconds, "status": "UPLOADED"}


@router.post("/videos/{video_id}/analyze")
def analyze(video_id: str):
    if not video_service.get_video(video_id):
        raise HTTPException(404, "Unknown video")
    scheduler.start(video_id)
    return {"video_id": video_id, "status": scheduler.get_status(video_id).status}


@router.get("/videos/{video_id}/status")
def status(video_id: str):
    return scheduler.get_status(video_id)


@router.get("/videos/{video_id}/result")
def result(video_id: str):
    return _result_or_404(video_id).model_dump(exclude={"speech", "shot_cuts"})


@router.post("/videos/{video_id}/rematch")
def rematch(video_id: str):
    res = scheduler.rematch(video_id)
    if res is None:
        raise HTTPException(404, "No analysis for this video yet")
    return res.model_dump(exclude={"speech", "shot_cuts"})


@router.get("/videos/{video_id}/vmap")
def vmap(video_id: str):
    return Response(_result_or_404(video_id).vmap_xml, media_type="application/xml",
                    headers={"Content-Disposition": f'attachment; filename="{video_id}_vmap.xml"'})


@router.get("/videos/{video_id}/debug")
def debug(video_id: str):
    return Response(_result_or_404(video_id).model_dump_json(indent=2), media_type="application/json",
                    headers={"Content-Disposition": f'attachment; filename="{video_id}_debug.json"'})
