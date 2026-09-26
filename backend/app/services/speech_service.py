"""
ASR with word timestamps. Output: list of segments
  {start, end, text, words: [{start, end, word}]}
Groq Whisper when a key is set; otherwise a local energy VAD that yields untranscribed
speech intervals (enough for the WHERE engine to avoid cutting mid-speech).
"""
import logging
import subprocess
from pathlib import Path
from typing import List, Tuple

from app.config import settings
from app.utils.ffmpeg import get_ffmpeg_exe

logger = logging.getLogger("scenesense.speech")


def _get(obj, key, default=None):
    return obj.get(key, default) if isinstance(obj, dict) else getattr(obj, key, default)


def transcribe(audio_path: str) -> Tuple[List[dict], str]:
    if settings.groq_api_key:
        try:
            return _groq_whisper(audio_path), f"groq:{settings.asr_model}"
        except Exception as e:
            logger.error("Groq Whisper failed, using local VAD: %s", e)
    return _local_vad(audio_path), "local-vad (no transcript)"


def _groq_whisper(audio_path: str) -> List[dict]:
    from groq import Groq

    client = Groq(api_key=settings.groq_api_key)
    with open(audio_path, "rb") as f:
        tr = client.audio.transcriptions.create(
            file=(Path(audio_path).name, f.read()),
            model=settings.asr_model,
            language=settings.asr_language or None,
            response_format="verbose_json",
            timestamp_granularities=["word", "segment"],
            temperature=0.0,
        )
    words = [{"start": float(_get(w, "start")), "end": float(_get(w, "end")), "word": _get(w, "word", "")}
             for w in (_get(tr, "words") or [])]
    segments = []
    for s in _get(tr, "segments") or []:
        # Whisper hallucinates text over music/silence; drop segments it itself flags as non-speech.
        if float(_get(s, "no_speech_prob", 0) or 0) > 0.7:
            continue
        start, end = float(_get(s, "start")), float(_get(s, "end"))
        seg_words = [w for w in words if w["start"] >= start - 0.05 and w["end"] <= end + 0.05]
        if seg_words:  # tighten to actual voiced span
            start, end = seg_words[0]["start"], seg_words[-1]["end"]
        segments.append({"start": round(start, 3), "end": round(end, 3),
                         "text": str(_get(s, "text", "")).strip(), "words": seg_words})
    logger.info("Groq Whisper: %d segments, %d words", len(segments), len(words))
    return segments


def _local_vad(audio_path: str) -> List[dict]:
    """Energy-based voice activity over 100 ms frames. ponytail: music is treated as speech;
    fine as a safety fallback (it only makes the WHERE engine more conservative)."""
    import numpy as np

    raw = subprocess.run([get_ffmpeg_exe(), "-i", audio_path, "-f", "s16le", "-ac", "1", "-ar", "16000", "-"],
                         capture_output=True).stdout
    pcm = np.frombuffer(raw, dtype=np.int16).astype(np.float32)
    hop = 1600
    if len(pcm) < hop:
        return []
    energy = np.sqrt(np.mean(pcm[: len(pcm) // hop * hop].reshape(-1, hop) ** 2, axis=1))
    thresh = max(np.percentile(energy, 30) * 2.0, 200.0)
    voiced = energy > thresh
    segments, start, gap = [], None, 0
    for i, v in enumerate(voiced):
        t = i * 0.1
        if v:
            start = t if start is None else start
            gap = 0
        elif start is not None:
            gap += 1
            if gap >= 5:  # 0.5 s of quiet ends a segment
                end = t - 0.5
                if end - start >= 0.4:
                    segments.append({"start": round(start, 2), "end": round(end, 2), "text": "", "words": []})
                start, gap = None, 0
    if start is not None:
        segments.append({"start": round(start, 2), "end": round(len(voiced) * 0.1, 2), "text": "", "words": []})
    return segments
