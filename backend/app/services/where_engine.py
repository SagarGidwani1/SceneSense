"""
WHERE: is this exact timestamp a natural, non-jarring cut?
Candidates = scene boundaries. For each, the best cut point within +-SEARCH_WINDOW s is chosen
among shot cuts and silence-gap midpoints, then scored. Mid-speech / mid-sentence /
conversation-carrying-over cuts are hard rejects, not low scores.
"""
from typing import List, Tuple

from app.models.analysis import AuditRecord, Candidate, CandidateFeatures, Scene

SEARCH_WINDOW = 4.0
SPEECH_MARGIN = 0.15
SENTENCE_END = tuple("।॥?!.…\"'”’")


MAX_WORD = 1.5  # seconds; longer "words" are Whisper alignment smearing over silence/music
KEEP = 1.0


def speech_tokens(speech: List[dict]) -> List[Tuple[float, float, str, bool]]:
    """(start, end, text, is_segment_final). Word-level when available, else segment-level.
    Smeared words are clipped to where the word really sits: first word -> its tail
    (start was pulled back into the preceding silence), last word -> its head, middle -> both edges."""
    out = []
    for s in speech:
        words = s.get("words") or []
        if not words:
            out.append((s["start"], s["end"], s.get("text", ""), True))
            continue
        n = len(words)
        for i, w in enumerate(words):
            a, b, txt, last = w["start"], w["end"], w.get("word", ""), i == n - 1
            if b - a <= MAX_WORD or n == 1:
                out.append((a, b, txt, last))
            elif i == 0:
                out.append((b - KEEP, b, txt, last))
            elif last:
                out.append((a, a + KEEP, txt, last))
            else:
                out += [(a, a + KEEP, txt, False), (b - KEEP, b, txt, False)]
    return sorted(out)


def features_at(t: float, tokens, shot_cuts, before: Scene) -> CandidateFeatures:
    in_speech = any(a - SPEECH_MARGIN < t < b + SPEECH_MARGIN for a, b, _, _ in tokens)
    prev = max((tk for tk in tokens if tk[1] <= t + SPEECH_MARGIN), key=lambda tk: tk[1], default=None)
    next_start = min((a for a, b, _, _ in tokens if a >= t - SPEECH_MARGIN), default=None)
    silence_before = min(10.0, t - prev[1]) if prev else 10.0
    silence_after = min(10.0, next_start - t) if next_start is not None else 10.0

    if prev is None:
        sentence_complete = True
    elif prev[2].strip():
        sentence_complete = (prev[2].rstrip().endswith(SENTENCE_END) or silence_before >= 1.2
                             or (prev[3] and silence_before >= 0.8))
    else:  # VAD-only: no text, rely on pause length
        sentence_complete = silence_before >= 0.8

    return CandidateFeatures(
        in_speech=in_speech,
        silence_before=round(max(0.0, silence_before), 2),
        silence_after=round(max(0.0, silence_after), 2),
        sentence_complete=sentence_complete,
        shot_cut_aligned=any(abs(c - t) <= 0.2 for c in shot_cuts),
        conversation_continues=before.conversation_continues,
    )


def score(f: CandidateFeatures, before: Scene) -> Tuple[float, List[str]]:
    s, why = 0.0, []
    if f.sentence_complete:
        s += 30; why.append("previous sentence complete")
    pause = min(3.0, f.silence_before + f.silence_after)
    s += 25 * pause / 3; why.append(f"{pause:.1f}s of silence around cut")
    if f.shot_cut_aligned:
        s += 20; why.append("aligned to a visual shot cut")
    if not f.conversation_continues:
        s += 15; why.append("conversation closed at scene end")
    s += 5 * (1 - before.tension_score) + 5 * (1 - before.cliffhanger_score)
    return round(min(100.0, s), 1), why


def evaluate(scenes: List[Scene], speech: List[dict], shot_cuts: List[float],
             min_score: float) -> Tuple[List[Candidate], List[AuditRecord]]:
    tokens = speech_tokens(speech)
    gaps = [(x[1] + y[0]) / 2 for x, y in zip(tokens, tokens[1:]) if y[0] - x[1] >= 0.6]
    candidates, audits = [], []

    for i in range(len(scenes) - 1):
        before, after = scenes[i], scenes[i + 1]
        b = before.end
        options = {b, *(c for c in shot_cuts if abs(c - b) <= SEARCH_WINDOW),
                   *(g for g in gaps if abs(g - b) <= SEARCH_WINDOW)}
        best = None
        for t in options:
            f = features_at(t, tokens, shot_cuts, before)
            sc, why = score(f, before)
            rank = (not f.in_speech and f.sentence_complete, sc, -abs(t - b))
            if best is None or rank > best[0]:
                best = (rank, t, f, sc, why)
        _, t, f, sc, why = best

        c = Candidate(candidate_id=f"cand_{i + 1:02d}", timestamp=round(t, 3), scene_before=before.scene_id,
                      scene_after=after.scene_id, features=f, where_score=sc, where_reasons=why)
        if f.in_speech:
            c.where_score = 0.0
            c.reject("MID_SPEECH", "Someone is speaking at this timestamp")
        elif not f.sentence_complete:
            c.where_score = 0.0
            c.reject("MID_SENTENCE", "Previous sentence is not finished")
        elif f.conversation_continues:
            c.where_score = min(c.where_score, 30.0)
            c.reject("CONVERSATION_CONTINUES", "Dialogue carries on into the next scene")
        elif sc < min_score:
            c.reject("LOW_NATURALNESS", f"Naturalness {sc} below threshold {min_score}")

        audits.append(AuditRecord(
            timestamp=c.timestamp, engine="WHERE",
            status="ACCEPTED" if c.status == "accepted" else "REJECTED",
            reason_code=c.rejection_code or "NATURAL_BREAK_POINT",
            reason=c.rejection_reason or f"Natural break point (score {sc}): " + ", ".join(why),
            details={"candidate_id": c.candidate_id, "scene_before": before.scene_id, "scene_after": after.scene_id},
        ))
        candidates.append(c)
    return candidates, audits
