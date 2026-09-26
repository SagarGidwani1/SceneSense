"""
Pipeline: audio -> ASR -> shots+keyframes -> AI scenes -> WHERE -> WHAT -> WHETHER -> VMAP.
WHAT runs before WHETHER so a slot with no safe brand never consumes pacing budget.
`rematch` re-runs WHAT+WHETHER+VMAP on the stored analysis (new brand / new rules, no re-ASR).
"""
import json
import logging
import threading
from pathlib import Path
from typing import Dict, Optional

from app.config import STORAGE_PATH
from app.models.analysis import AnalysisResult, AnalysisStatus, FinalBreak
from app.rules.pacing_rules import load_rules
from app.services import brand_matcher, scene_understanding, speech_service, video_service, where_engine, whether_engine
from app.services.vmap_generator import generate_vmap_xml
from app.utils.ffmpeg import detect_shots_and_frames, extract_audio_mp3

logger = logging.getLogger("scenesense.pipeline")
DEBUG = STORAGE_PATH / "debug"
_statuses: Dict[str, AnalysisStatus] = {}
_running: set = set()


def _status_path(vid): return DEBUG / f"{vid}_status.json"
def _result_path(vid): return DEBUG / f"{vid}_result.json"


def get_status(video_id: str) -> AnalysisStatus:
    if video_id in _statuses:
        return _statuses[video_id]
    p = _status_path(video_id)
    if p.exists():
        return AnalysisStatus(**json.loads(p.read_text(encoding="utf-8")))
    return AnalysisStatus(video_id=video_id, status="UPLOADED", current_step="Ready to analyse")


def _set(video_id, status, pct, step, error=None):
    st = AnalysisStatus(video_id=video_id, status=status, progress_percent=pct, current_step=step, error=error)
    _statuses[video_id] = st
    _status_path(video_id).write_text(st.model_dump_json(), encoding="utf-8")
    logger.info("[%s] %s %s", video_id, status, step)


def get_result(video_id: str) -> Optional[AnalysisResult]:
    p = _result_path(video_id)
    return AnalysisResult(**json.loads(p.read_text(encoding="utf-8"))) if p.exists() else None


def save_result(res: AnalysisResult):
    _result_path(res.video_id).write_text(res.model_dump_json(indent=2), encoding="utf-8")


def start(video_id: str) -> bool:
    if video_id in _running:
        return False
    _running.add(video_id)
    threading.Thread(target=run_pipeline, args=(video_id,), daemon=True).start()
    return True


def run_pipeline(video_id: str):
    try:
        meta = video_service.get_video(video_id)
        if not meta or not Path(meta.filepath).exists():
            raise FileNotFoundError("Video file not found — upload it again")
        duration = meta.duration_seconds
        rules = load_rules()
        warnings = []

        _set(video_id, "EXTRACTING", 5, "Extracting audio track")
        audio = STORAGE_PATH / "audio" / f"{video_id}.mp3"
        has_audio = extract_audio_mp3(meta.filepath, str(audio))

        _set(video_id, "TRANSCRIBING", 15, "Transcribing Bengali speech with word timestamps")
        speech_cache = DEBUG / f"{video_id}_speech.json"
        if speech_cache.exists():  # same video re-analysed: reuse its own transcript, save API quota
            speech, asr = json.loads(speech_cache.read_text(encoding="utf-8")), "cached transcript"
        elif has_audio:
            speech, asr = speech_service.transcribe(str(audio))
            if not asr.startswith("local"):
                speech_cache.write_text(json.dumps(speech, ensure_ascii=False), encoding="utf-8")
        else:
            speech, asr = [], "none (no audio track)"
            warnings.append("Video has no audio track — mid-dialogue protection relies on visuals only.")
        if asr.startswith("local"):
            warnings.append("Groq Whisper unavailable — local voice detection used (no transcript text).")

        _set(video_id, "SEGMENTING", 35, "Detecting shot cuts and sampling keyframes")
        frame_interval = max(4.0, duration / 180)
        frames_dir = STORAGE_PATH / "scenes" / video_id
        shot_cuts = detect_shots_and_frames(meta.filepath, frames_dir, frame_interval)

        _set(video_id, "UNDERSTANDING", 50, f"AI scene understanding ({len(shot_cuts)} shots, {len(speech)} lines)")
        negatives = [n for b in brand_matcher.load_catalog().brands for n in b.negative_contexts]
        scenes, scene_ai, w = scene_understanding.build_scenes(
            video_id, duration, shot_cuts, speech, frames_dir, frame_interval, negatives)
        warnings += w

        _set(video_id, "SCORING_WHERE", 70, f"Scoring {len(scenes) - 1} scene boundaries")
        result = AnalysisResult(
            video_id=video_id, filename=meta.filename, duration_seconds=duration,
            video_url=f"/public/uploads/{Path(meta.filepath).name}",
            providers={"asr": asr, "scene_ai": scene_ai},
            scenes=scenes, shot_cuts=shot_cuts, speech=speech, warnings=warnings,
        )
        _decide(result, rules, progress=True)
        save_result(result)
        _set(video_id, "READY", 100, f"Done — {len(result.final_breaks)} ad break(s) placed across {len(scenes)} scenes")
    except Exception as e:
        logger.exception("Pipeline failed for %s", video_id)
        _set(video_id, "FAILED", 0, "Analysis failed", error=str(e))
    finally:
        _running.discard(video_id)


def rematch(video_id: str) -> Optional[AnalysisResult]:
    res = get_result(video_id)
    if res is None:
        return None
    for s in res.scenes:  # catalog may add new negative terms — keep keyword net current
        s.sensitive_contexts = sorted(set(s.sensitive_contexts) | set(scene_understanding.keyword_sensitive(s.transcript)))
    _decide(res, load_rules())
    save_result(res)
    return res


def _decide(res: AnalysisResult, rules, progress: bool = False):
    vid = res.video_id
    candidates, where_audits = where_engine.evaluate(res.scenes, res.speech, res.shot_cuts, rules.min_where_score)

    if progress:
        _set(vid, "MATCHING_BRANDS", 80, "Matching brands with hard negative-context blocking")
    passing = [c for c in candidates if c.status == "accepted"]
    selected, what_audits, brand_ai = brand_matcher.match(passing, res.scenes, rules.ad_duration_seconds)

    if progress:
        _set(vid, "APPLYING_PACING", 90, "Applying pacing and ad-load rules")
    chosen, whether_audits = whether_engine.select(
        candidates, {k: v.match_score for k, v in selected.items()}, res.duration_seconds, rules)

    res.final_breaks = [FinalBreak(
        break_id=f"break_{i + 1:02d}", timestamp=c.timestamp, duration_seconds=rules.ad_duration_seconds,
        where_score=c.where_score, scene_before=c.scene_before, scene_after=c.scene_after,
        brand=selected[c.candidate_id], reasons=c.where_reasons,
    ) for i, c in enumerate(chosen)]
    res.candidates = candidates
    res.audit_logs = sorted(where_audits + what_audits + whether_audits, key=lambda a: a.timestamp)
    res.providers["brand_ai"] = brand_ai
    res.rules = rules.model_dump()
    res.vmap_xml = generate_vmap_xml(res.final_breaks)
