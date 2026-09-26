"""
Semantic scene segmentation + labelling.
AI proposes scene ranges and labels from keyframes + timestamped transcript;
deterministic code snaps boundaries to real shot cuts and adds a keyword safety net.
"""
import logging
from pathlib import Path
from typing import List, Tuple

from app.models.analysis import Scene
from app.services.llm import LLMUnavailable, llm_json

logger = logging.getLogger("scenesense.scenes")

# Default sensitive vocabulary; the live catalog's negative_contexts are merged in at call time.
BASE_SENSITIVE = ["funeral", "death", "grief", "mourning", "hospital", "illness", "medical emergency",
                  "injury", "accident", "violence", "crime", "blood", "bathroom", "financial distress",
                  "alcohol", "suicide", "abuse"]

# Transcript keyword safety net (Bengali script + romanised + English). Adds, never removes.
KEYWORD_SENSITIVE = {
    "death": ["মারা গে", "মৃত্যু", "মরে গে", "লাশ", "dead body", "died", "death"],
    "funeral": ["শ্মশান", "শ্রাদ্ধ", "কবর", "জানাজা", "দাহ", "funeral", "burial"],
    "hospital": ["হাসপাতাল", "হসপিটাল", "ডাক্তার", "অপারেশন", "hospital", "icu"],
    "violence": ["খুন", "মার্ডার", "রক্ত", "গুলি", "ছুরি", "murder", "blood"],
    "accident": ["অ্যাক্সিডেন্ট", "এক্সিডেন্ট", "দুর্ঘটনা", "accident"],
}


def fmt(t: float) -> str:
    return f"{int(t // 60):02d}:{t % 60:04.1f}"


def keyword_sensitive(text: str) -> List[str]:
    low = text.lower()
    return [ctx for ctx, kws in KEYWORD_SENSITIVE.items() if any(k.lower() in low for k in kws)]


def _transcript_for(speech: List[dict], start: float, end: float) -> str:
    return " ".join(s["text"] for s in speech if s["text"] and s["start"] < end and s["end"] > start)


def _frame_time(i: int, interval: float) -> float:
    return (i - 1) * interval


def build_scenes(video_id: str, duration: float, shot_cuts: List[float], speech: List[dict],
                 frames_dir: Path, frame_interval: float, extra_sensitive: List[str]) -> Tuple[List[Scene], str, List[str]]:
    """Returns (scenes, provider_label, warnings)."""
    frames = sorted(frames_dir.glob("f_*.jpg"))
    vocab = sorted({*BASE_SENSITIVE, *(c.lower() for c in extra_sensitive)})
    warnings: List[str] = []
    try:
        raw, provider = _ask_llm(duration, shot_cuts, speech, frames, frame_interval, vocab)
        boundaries = [float(s.get("start", 0)) for s in raw][1:]
    except (LLMUnavailable, ValueError, KeyError, TypeError) as e:
        logger.error("Scene AI unavailable, using heuristic segmentation: %s", e)
        warnings.append(f"Scene AI unavailable — heuristic segmentation used, labels are minimal. ({str(e)[:160]})")
        raw, provider = [], "heuristic (no AI)"
        boundaries = _heuristic_boundaries(duration, shot_cuts, speech)

    cuts = _snap_boundaries(boundaries, shot_cuts, duration)
    edges = [0.0, *cuts, duration]
    scenes: List[Scene] = []
    for i in range(len(edges) - 1):
        start, end = edges[i], edges[i + 1]
        src = _best_overlap(raw, start, end)
        transcript = _transcript_for(speech, start, end)
        # Union over every overlapping AI scene: merging must never drop a sensitive tag.
        sensitive = {str(x).lower() for s in _overlapping(raw, start, end) for x in s.get("sensitive_contexts", [])}
        sensitive |= set(keyword_sensitive(transcript))
        thumb_idx = min(len(frames), int((start + min(3.0, (end - start) / 3)) / frame_interval) + 1) if frames else 0
        scenes.append(Scene(
            scene_id=f"scene_{i + 1:02d}",
            start=round(start, 3),
            end=round(end, 3),
            summary=src.get("summary") or f"Scene {i + 1} ({fmt(start)}–{fmt(end)})",
            dominant_activity=str(src.get("dominant_activity") or "unknown").lower().replace(" ", "_"),
            context_tags=[str(t).lower() for t in src.get("context_tags", [])][:12],
            emotion=str(src.get("emotion") or "neutral").lower(),
            tension_score=_clamp(src.get("tension_score", 0.3)),
            cliffhanger_score=_clamp(src.get("cliffhanger_score", 0.2)),
            sensitive_contexts=sorted(sensitive),
            conversation_continues=bool(src.get("conversation_continues", False)),
            thumbnail_url=f"/public/scenes/{video_id}/{frames[thumb_idx - 1].name}" if thumb_idx else None,
            transcript=transcript[:2000],
        ))
    return scenes, provider, warnings


def _ask_llm(duration, shot_cuts, speech, frames, interval, vocab):
    lines = "\n".join(f"[{fmt(s['start'])}-{fmt(s['end'])}] {s['text']}" for s in speech if s["text"]) or "(no transcript)"
    prompt = f"""You are segmenting a Bengali TV drama ({fmt(duration)} long, {duration:.1f}s) into SCENES for ad-break planning.

A scene is a continuous narrative unit: same location, same time, same group of characters, one dramatic purpose.
A new scene starts when location/time jumps or the narrative unit clearly changes. Camera shot changes inside one
conversation are NOT scene changes. Typical scene length is 40 s to 5 min.

Inputs:
- Keyframes, each labelled with its timestamp (one every {interval:.1f}s).
- Shot cuts (seconds): {", ".join(f"{c:.1f}" for c in shot_cuts) or "none detected"}
- Timestamped Bengali transcript (ASR, may contain errors):
{lines}

Return JSON: {{"scenes": [ ... ]}} covering 0 to {duration:.1f} contiguously, in order. Each scene:
{{
 "start": seconds (prefer a listed shot cut), "end": seconds,
 "summary": one or two English sentences on what happens,
 "dominant_activity": snake_case of what characters mainly DO (e.g. family_meal, cooking, phone_call, commuting,
   shopping, getting_ready, office_work, romance, argument, celebration, funeral_mourning, hospital_visit, travel),
 "context_tags": 4-10 lowercase tags (setting, objects, activities),
 "emotion": one of warm, joyful, romantic, peaceful, neutral, tense, sad, fearful, angry,
 "tension_score": 0-1, "cliffhanger_score": 0-1 (does the scene END on an unresolved hook?),
 "sensitive_contexts": every item from this list that is present or strongly implied, else []:
   {", ".join(vocab)}
   Be conservative: if a death, illness, injury, grief, violence etc. is discussed or shown, include it.
 "conversation_continues": true if the same conversation carries on across the end of this scene
}}"""
    images = [(f"Frame at {_frame_time(i + 1, interval):.1f}s:", p) for i, p in enumerate(frames)]
    data, provider = llm_json(prompt, images)
    scenes = data["scenes"] if isinstance(data, dict) else data
    if not scenes:
        raise ValueError("LLM returned no scenes")
    return sorted(scenes, key=lambda s: float(s.get("start", 0))), provider


def _heuristic_boundaries(duration, shot_cuts, speech) -> List[float]:
    """Shot cuts sitting in a >=1.5 s silence, at least 40 s apart."""
    out, last = [], 0.0
    for c in shot_cuts:
        if c - last >= 40 and duration - c >= 20 and _silence_around(c, speech) >= 1.5:
            out.append(c)
            last = c
    return out


def _silence_around(t: float, speech: List[dict]) -> float:
    before = max([s["end"] for s in speech if s["end"] <= t] or [0.0])
    after = min([s["start"] for s in speech if s["start"] >= t] or [t + 5])
    if any(s["start"] < t < s["end"] for s in speech):
        return 0.0
    return (t - before) + (after - t)


def _snap_boundaries(boundaries: List[float], shot_cuts: List[float], duration: float) -> List[float]:
    snapped = []
    for b in sorted(boundaries):
        near = min(shot_cuts, key=lambda c: abs(c - b)) if shot_cuts else b
        t = near if abs(near - b) <= 6.0 else b
        if 8.0 <= t <= duration - 8.0 and (not snapped or t - snapped[-1] >= 8.0):
            snapped.append(round(t, 3))
    return snapped


def _overlap(s: dict, start: float, end: float) -> float:
    try:
        return min(end, float(s["end"])) - max(start, float(s["start"]))
    except (KeyError, TypeError, ValueError):
        return 0.0


def _overlapping(raw: List[dict], start: float, end: float) -> List[dict]:
    return [s for s in raw if _overlap(s, start, end) > 1.0]


def _best_overlap(raw: List[dict], start: float, end: float) -> dict:
    return max(raw, key=lambda s: _overlap(s, start, end), default={})


def _clamp(v) -> float:
    try:
        return round(min(1.0, max(0.0, float(v))), 2)
    except (TypeError, ValueError):
        return 0.3
