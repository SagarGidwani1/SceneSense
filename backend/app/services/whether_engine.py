"""
WHETHER: is a break warranted here, given pacing rules?
Greedy by quality (WHERE score blended with brand fit), each pick checked against:
edge buffer, min gap to every accepted break, max breaks in ANY rolling 60-minute window,
and total ad load. ponytail: greedy, not a global optimum — fine for <50 candidates.
"""
from typing import Dict, List, Tuple

from app.models.analysis import AuditRecord, Candidate
from app.rules.pacing_rules import Rules


def _max_in_window(times: List[float], window: float = 3600.0) -> int:
    times = sorted(times)
    return max((sum(1 for u in times if t <= u < t + window) for t in times), default=0)


def select(cands: List[Candidate], brand_scores: Dict[str, float], duration: float,
           rules: Rules) -> Tuple[List[Candidate], List[AuditRecord]]:
    pool = [c for c in cands if c.status == "accepted"]
    pool.sort(key=lambda c: 0.7 * c.where_score + 0.3 * brand_scores.get(c.candidate_id, 0), reverse=True)
    accepted: List[Candidate] = []
    audits: List[AuditRecord] = []

    for c in pool:
        t = c.timestamp
        times = [a.timestamp for a in accepted]
        load = (len(accepted) + 1) * rules.ad_duration_seconds / max(duration, 1.0) * 100
        nearest = min((abs(t - u) for u in times), default=None)

        if t < rules.edge_buffer_seconds or t > duration - rules.edge_buffer_seconds:
            code, why = "EDGE_BUFFER", f"Within {rules.edge_buffer_seconds:.0f}s of episode start/end"
        elif nearest is not None and nearest < rules.min_gap_seconds:
            code, why = "MIN_GAP", f"Only {nearest:.0f}s from another break (min {rules.min_gap_seconds:.0f}s)"
        elif _max_in_window(times + [t]) > rules.max_breaks_per_hour:
            code, why = "MAX_BREAKS_PER_HOUR", f"Would exceed {rules.max_breaks_per_hour} breaks in a 60-min window"
        elif load > rules.max_ad_load_percent:
            code, why = "MAX_AD_LOAD", f"Ad load would be {load:.1f}% (max {rules.max_ad_load_percent}%)"
        else:
            accepted.append(c)
            audits.append(AuditRecord(timestamp=t, status="ACCEPTED", engine="WHETHER", reason_code="PACING_OK",
                                      reason=f"Pacing satisfied — ad load {load:.1f}%",
                                      details={"candidate_id": c.candidate_id}))
            continue
        c.reject(code, why)
        audits.append(AuditRecord(timestamp=t, status="REJECTED", engine="WHETHER", reason_code=code, reason=why,
                                  details={"candidate_id": c.candidate_id}))

    return sorted(accepted, key=lambda c: c.timestamp), audits
