"""Offline checks for the deterministic decision layer (no API keys needed)."""
import xml.etree.ElementTree as ET

import pytest

from app.models.analysis import Candidate, FinalBreak, Scene, SelectedBrand
from app.models.brand import Brand, BrandCatalog
from app.rules.hard_constraints import check_negative_context_violation
from app.rules.pacing_rules import Rules
from app.services import brand_matcher, where_engine, whether_engine
from app.services.llm import LLMUnavailable
from app.services.vmap_generator import generate_vmap_xml, hms


def scene(i, start, end, **kw):
    return Scene(scene_id=f"scene_{i:02d}", start=start, end=end, **kw)


# ---------- hard block ----------
def test_negative_context_blocks_on_word_subset():
    assert check_negative_context_violation(["funeral_mourning", "village"], ["funeral"])[0]
    assert check_negative_context_violation(["emergency medical ward"], ["medical emergency"])[0]


def test_negative_context_no_false_block_on_partial_phrase():
    # scene about food must not trip a brand whose negative is "food poisoning"
    assert not check_negative_context_violation(["food", "kitchen"], ["food poisoning"])[0]


# ---------- WHERE ----------
SPEECH = [
    {"start": 10.0, "end": 19.0, "text": "আমি বাজারে যাচ্ছি।", "words": []},
    {"start": 19.2, "end": 24.0, "text": "তুমি কি আসবে", "words": []},   # no terminal punctuation
    {"start": 24.1, "end": 28.0, "text": "হ্যাঁ চলো।", "words": []},
]


def test_where_rejects_mid_speech_and_accepts_clean_cut():
    scenes = [scene(1, 0, 21.5), scene(2, 21.5, 40.0), scene(3, 40.0, 80.0)]
    cands, _ = where_engine.evaluate(scenes, SPEECH, shot_cuts=[21.5, 40.0], min_score=60)
    mid, clean = cands
    assert mid.status == "rejected" and mid.rejection_code in ("MID_SPEECH", "MID_SENTENCE")
    assert clean.status == "accepted" and clean.timestamp == 40.0 and clean.features.shot_cut_aligned


def test_where_rejects_when_conversation_continues():
    scenes = [scene(1, 0, 40.0, conversation_continues=True), scene(2, 40.0, 80.0)]
    cands, _ = where_engine.evaluate(scenes, SPEECH, shot_cuts=[40.0], min_score=60)
    assert cands[0].rejection_code == "CONVERSATION_CONTINUES"


# ---------- WHETHER ----------
def cand(cid, t, score=80):
    return Candidate(candidate_id=cid, timestamp=t, scene_before="a", scene_after="b", where_score=score)


def test_whether_min_gap_prefers_higher_score():
    rules = Rules(min_gap_seconds=300, edge_buffer_seconds=60, max_breaks_per_hour=10, max_ad_load_percent=50)
    chosen, _ = whether_engine.select([cand("c1", 400, 70), cand("c2", 500, 95)], {}, 3600, rules)
    assert [c.candidate_id for c in chosen] == ["c2"]


def test_whether_rolling_hour_and_ad_load():
    rules = Rules(min_gap_seconds=60, edge_buffer_seconds=0, max_breaks_per_hour=2, max_ad_load_percent=50)
    chosen, _ = whether_engine.select([cand(f"c{i}", 100 + i * 200) for i in range(5)], {}, 7200, rules)
    assert len(chosen) == 2
    rules = Rules(min_gap_seconds=60, edge_buffer_seconds=0, max_breaks_per_hour=99,
                  max_ad_load_percent=0.9, ad_duration_seconds=15)
    chosen, _ = whether_engine.select([cand(f"c{i}", 100 + i * 200) for i in range(5)], {}, 1500, rules)
    assert len(chosen) == 0  # one 15 s ad in 1500 s = 1.0% > 0.9%


# ---------- WHAT (AI mocked) ----------
CATALOG = BrandCatalog(brands=[
    Brand(brand_id="food", brand_name="Brand Food", category="food", positive_contexts=["cooking", "family meal"],
          negative_contexts=["funeral", "death"]),
    Brand(brand_id="tel", brand_name="Brand Tel", category="telecom", positive_contexts=["phone call"],
          negative_contexts=["violence"]),
])


@pytest.fixture
def catalog(monkeypatch):
    monkeypatch.setattr(brand_matcher, "load_catalog", lambda: CATALOG)
    monkeypatch.setattr(brand_matcher, "creative_url", lambda b, d: f"/public/ads/{b.brand_id}.mp4")


def test_ai_semantic_block_wins_over_relevance(catalog, monkeypatch):
    scenes = [scene(1, 0, 100, dominant_activity="family_meal", context_tags=["cremation ground"]),
              scene(2, 100, 200)]
    c = Candidate(candidate_id="c1", timestamp=100, scene_before="scene_01", scene_after="scene_02")
    ai = {("c1", "food"): {"violates_negative": True, "violated_contexts": ["death"], "relevance": 99},
          ("c1", "tel"): {"violates_negative": False, "relevance": 40, "reason": "ok"}}
    monkeypatch.setattr(brand_matcher, "_ai_evaluate", lambda *a: (ai, "mock"))
    selected, _, _ = brand_matcher.match([c], scenes, 15)
    assert selected["c1"].brand_id == "tel"
    assert next(e for e in c.brand_evaluations if e.brand_id == "food").blocked


def test_unseen_ninth_brand_needs_no_code(catalog, monkeypatch):
    CATALOG.brands.append(Brand(brand_id="brand_09", brand_name="Ninth", category="travel",
                                positive_contexts=["train journey"], negative_contexts=["accident"]))
    scenes = [scene(1, 0, 100, dominant_activity="train_journey"), scene(2, 100, 200)]
    c = Candidate(candidate_id="c1", timestamp=100, scene_before="scene_01", scene_after="scene_02")

    def fail(*a):
        raise LLMUnavailable("offline")
    monkeypatch.setattr(brand_matcher, "_ai_evaluate", fail)
    selected, _, provider = brand_matcher.match([c], scenes, 15)
    CATALOG.brands.pop()
    assert selected["c1"].brand_id == "brand_09" and "lexical" in provider


def test_ai_down_sensitive_scene_blocks_everything(catalog, monkeypatch):
    scenes = [scene(1, 0, 100, dominant_activity="cooking", sensitive_contexts=["grief"]), scene(2, 100, 200)]
    c = Candidate(candidate_id="c1", timestamp=100, scene_before="scene_01", scene_after="scene_02")
    monkeypatch.setattr(brand_matcher, "_ai_evaluate", lambda *a: (_ for _ in ()).throw(LLMUnavailable("x")))
    selected, _, _ = brand_matcher.match([c], scenes, 15)
    assert not selected and c.rejection_code == "ALL_BRANDS_BLOCKED"


# ---------- VMAP ----------
def test_vmap_is_well_formed_and_escaped():
    b = FinalBreak(break_id="break_01", timestamp=433.1, duration_seconds=15, where_score=90,
                   scene_before="s1", scene_after="s2",
                   brand=SelectedBrand(brand_id="x", brand_name="A & B <Co>", match_score=80, creative_url="/public/ads/x.mp4"))
    root = ET.fromstring(generate_vmap_xml([b]).split("\n", 1)[1])
    ns = {"vmap": "http://www.iab.net/videosuite/vmap"}
    ab = root.find("vmap:AdBreak", ns)
    assert ab.get("timeOffset") == "00:07:13.100"
    assert root.find(".//AdTitle").text == "A & B <Co> (synthetic)"
    assert root.find(".//Duration").text == "00:00:15"
    assert hms(3725.5) == "01:02:05.500"
