from fastapi import APIRouter

from app.config import settings
from app.utils.ffmpeg import is_ffmpeg_available

router = APIRouter()


@router.get("/health")
def health():
    return {
        "status": "ok",
        "ffmpeg": is_ffmpeg_available(),
        "groq": bool(settings.groq_api_key),
        "gemini": bool(settings.gemini_api_key),
    }
