import json
from datetime import datetime
from typing import List, Optional

from app.config import STORAGE_PATH
from app.models.analysis import VideoMetadata
from app.utils.ffmpeg import probe_video

META_DIR = STORAGE_PATH / "debug"


def get_video(video_id: str) -> Optional[VideoMetadata]:
    p = META_DIR / f"{video_id}_meta.json"
    return VideoMetadata(**json.loads(p.read_text(encoding="utf-8"))) if p.exists() else None


def save_video(meta: VideoMetadata):
    (META_DIR / f"{meta.video_id}_meta.json").write_text(meta.model_dump_json(indent=2), encoding="utf-8")


def register_video(video_id: str, filename: str, filepath: str) -> VideoMetadata:
    duration, fps = probe_video(filepath)
    meta = VideoMetadata(video_id=video_id, filename=filename, filepath=filepath, duration_seconds=duration,
                         fps=fps, created_at=datetime.now().isoformat(timespec="seconds"))
    save_video(meta)
    return meta


def list_videos() -> List[VideoMetadata]:
    metas = [VideoMetadata(**json.loads(p.read_text(encoding="utf-8"))) for p in META_DIR.glob("*_meta.json")]
    return sorted(metas, key=lambda m: m.created_at, reverse=True)
