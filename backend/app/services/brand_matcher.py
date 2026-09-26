"""
WHAT: which synthetic brand belongs in each surviving slot.
- Catalog is pure data (brands_catalog.json) -> a 9th brand needs zero code changes.
- Hard block = lexical match OR AI semantic match of negative_contexts against BOTH adjacent scenes.
  Blocks are only ever added, never overridden by relevance.
- Relevance = AI score (dominant activity first) blended with lexical overlap.
"""
import json
import logging
import zlib
from typing import Dict, List, Tuple

from app.config import BASE_DIR, STORAGE_PATH
from app.models.analysis import AuditRecord, BrandEval, Candidate, Scene, SelectedBrand
from app.models.brand import Brand, BrandCatalog
from app.rules.hard_constraints import _words, check_negative_context_violation
from app.services.llm import LLMUnavailable, llm_json
from app.utils.ffmpeg import make_ad_creative

logger = logging.getLogger("scenesense.what")
CATALOG_PATH = BASE_DIR / "data" / "brands_catalog.json"
MIN_RELEVANCE = 20.0


def load_catalog() -> BrandCatalog:
    return BrandCatalog(**json.loads(CATALOG_PATH.read_text(encoding="utf-8")))


def save_catalog(catalog: BrandCatalog):
    CATALOG_PATH.write_text(json.dumps(catalog.model_dump(), indent=2, ensure_ascii=False), encoding="utf-8")


def creative_url(brand: Brand, duration: float) -> str:
    if brand.creative_url:
        return brand.creative_url
    name = f"{brand.brand_id}_{int(duration)}s.mp4"
    path = STORAGE_PATH / "ads" / name
    if not path.exists():
        make_ad_creative(path, brand.brand_name, brand.category, duration, zlib.crc32(brand.brand_id.encode()) % 360)
    return f"/public/ads/{name}"


def _scene_terms(s: Scene) -> List[str]:
    return [*s.context_tags, *s.sensitive_contexts, s.dominant_activity]


def _lexical_relevance(brand: Brand, scene: Scene) -> float:
    terms = [_words(t) for t in scene.context_tags]
    activity = _words(scene.dominant_activity)
    score = 0.0
    for p in {*brand.positive_contexts, *brand.keywords}:
        pw = _words(p)
        if pw and pw <= activity:
            score += 50  # dominant activity wins
        elif pw and any(pw <= t for t in terms):
            score += 15
    return min(100.0, score)


def _ai_evaluate(cands: List[Candidate], scenes: Dict[str, Scene], brands: List[Brand]) -> Tuple[Dict, str]:
    def sc(s: Scene):
        return {"summary": s.summary, "dominant_activity": s.dominant_activity, "tags": s.context_tags,
                "sensitive_contexts": s.sensitive_contexts, "emotion": s.emotion}

    slots = [{"candidate_id": c.candidate_id, "scene_before_ad": sc(scenes[c.scene_before]),
              "scene_after_ad": sc(scenes[c.scene_after])} for c in cands]
    catalog = [{"brand_id": b.brand_id, "category": b.category, "description": b.description,
                "positive_contexts": b.positive_contexts, "negative_contexts": b.negative_contexts,
                "keywords": b.keywords} for b in brands]
    prompt = f"""You place synthetic brand ads in ad breaks of a Bengali drama. For EVERY slot x brand pair decide:

1. violates_negative: true if ANY of the brand's negative_contexts is present, implied or semantically equivalent
   in EITHER the scene before or after the ad (e.g. "death" ~ mourning/cremation/dead body; "illness" ~ hospital
   visit/fever; "violence" ~ fight/assault). This is a hard safety block — when in doubt, say true.
   List the matching negative_contexts in violated_contexts.
2. relevance 0-100: how well the brand fits the scene BEFORE the ad. The dominant_activity matters most,
   then tags and summary. Unrelated = under 20.

Slots: {json.dumps(slots, ensure_ascii=False)}
Brands: {json.dumps(catalog, ensure_ascii=False)}

Return JSON: {{"evaluations": [{{"candidate_id": str, "brand_id": str, "violates_negative": bool,
"violated_contexts": [str], "relevance": number, "reason": "max 15 words"}}]}} with exactly
{len(slots) * len(brands)} items."""
    data, provider = llm_json(prompt)
    out = {}
    for e in data.get("evaluations", []) if isinstance(data, dict) else []:
        out[(str(e.get("candidate_id")), str(e.get("brand_id")))] = e
    return out, provider


def match(cands: List[Candidate], scenes: List[Scene], ad_duration: float) -> Tuple[Dict[str, SelectedBrand], List[AuditRecord], str]:
    """Fills candidate.brand_evaluations; returns {candidate_id: selected brand} for slots with a safe brand."""
    brands = load_catalog().brands
    smap = {s.scene_id: s for s in scenes}
    audits: List[AuditRecord] = []
    if not cands or not brands:
        return {}, audits, "not needed"

    try:
        ai, provider = _ai_evaluate(cands, smap, brands)
    except LLMUnavailable as e:
        logger.error("Brand AI unavailable: %s", e)
        ai, provider = None, "lexical only (AI unavailable)"

    selected: Dict[str, SelectedBrand] = {}
    for c in cands:
        before, after = smap[c.scene_before], smap[c.scene_after]
        evals = []
        for b in brands:
            _, lex = check_negative_context_violation(_scene_terms(before) + _scene_terms(after), b.negative_contexts)
            blocked_by = set(lex)
            reason = ""
            if ai is None:
                if before.sensitive_contexts or after.sensitive_contexts:
                    blocked_by.add("sensitive scene (AI unavailable — conservative block)")
                relevance = _lexical_relevance(b, before)
                reason = "lexical context overlap"
            else:
                e = ai.get((c.candidate_id, b.brand_id))
                if e is None:
                    blocked_by.add("not evaluated by AI (conservative block)")
                    relevance = 0.0
                else:
                    if e.get("violates_negative"):
                        blocked_by.update(e.get("violated_contexts") or ["semantic negative match"])
                    try:
                        ai_rel = float(e.get("relevance", 0))
                    except (TypeError, ValueError):
                        ai_rel = 0.0
                    relevance = 0.8 * ai_rel + 0.2 * _lexical_relevance(b, before)
                    reason = str(e.get("reason", ""))[:160]
            ev = BrandEval(brand_id=b.brand_id, brand_name=b.brand_name, blocked=bool(blocked_by),
                           blocked_by=sorted(blocked_by), relevance=round(min(100.0, relevance), 1), reason=reason)
            evals.append(ev)
            if ev.blocked:
                audits.append(AuditRecord(
                    timestamp=c.timestamp, status="BLOCKED", engine="WHAT", reason_code="NEGATIVE_CONTEXT_BLOCK",
                    reason=f"{b.brand_name} blocked: {', '.join(ev.blocked_by)}",
                    details={"candidate_id": c.candidate_id, "brand_id": b.brand_id}))
        evals.sort(key=lambda e: (not e.blocked, e.relevance), reverse=True)
        c.brand_evaluations = evals

        best = next((e for e in evals if not e.blocked), None)
        if best is None:
            c.reject("ALL_BRANDS_BLOCKED", "Every brand is blocked by a negative context in the adjacent scenes")
        elif best.relevance < MIN_RELEVANCE:
            c.reject("NO_RELEVANT_BRAND", f"Best safe brand {best.brand_name} only {best.relevance}% relevant")
        else:
            brand = next(b for b in brands if b.brand_id == best.brand_id)
            selected[c.candidate_id] = SelectedBrand(
                brand_id=brand.brand_id, brand_name=brand.brand_name, match_score=best.relevance,
                reason=best.reason, creative_url=creative_url(brand, ad_duration))
            audits.append(AuditRecord(
                timestamp=c.timestamp, status="ACCEPTED", engine="WHAT", reason_code="BRAND_SELECTED",
                reason=f"{brand.brand_name} selected ({best.relevance}%): {best.reason}",
                details={"candidate_id": c.candidate_id, "brand_id": brand.brand_id}))
        if c.status == "rejected":
            audits.append(AuditRecord(timestamp=c.timestamp, status="REJECTED", engine="WHAT",
                                      reason_code=c.rejection_code, reason=c.rejection_reason,
                                      details={"candidate_id": c.candidate_id}))
    return selected, audits, provider
