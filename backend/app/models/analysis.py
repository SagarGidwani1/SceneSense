from pydantic import BaseModel, Field
from typing import Dict, List, Optional


class VideoMetadata(BaseModel):
    video_id: str
    filename: str
    filepath: str
    duration_seconds: float = 0.0
    fps: float = 25.0
    status: str = "UPLOADED"
    created_at: str = ""


class AnalysisStatus(BaseModel):
    video_id: str
    status: str
    progress_percent: float = 0.0
    current_step: str = ""
    error: Optional[str] = None


class Scene(BaseModel):
    scene_id: str
    start: float
    end: float
    summary: str = ""
    dominant_activity: str = "unknown"
    context_tags: List[str] = Field(default_factory=list)
    emotion: str = "neutral"
    tension_score: float = 0.0
    cliffhanger_score: float = 0.0
    sensitive_contexts: List[str] = Field(default_factory=list)
    conversation_continues: bool = False  # dialogue carries over into the next scene
    thumbnail_url: Optional[str] = None
    transcript: str = ""


class CandidateFeatures(BaseModel):
    in_speech: bool = False
    silence_before: float = 0.0
    silence_after: float = 0.0
    sentence_complete: bool = True
    shot_cut_aligned: bool = False
    conversation_continues: bool = False


class BrandEval(BaseModel):
    brand_id: str
    brand_name: str
    blocked: bool = False
    blocked_by: List[str] = Field(default_factory=list)
    relevance: float = 0.0
    reason: str = ""


class Candidate(BaseModel):
    candidate_id: str
    timestamp: float
    scene_before: str
    scene_after: str
    features: CandidateFeatures = Field(default_factory=CandidateFeatures)
    where_score: float = 0.0
    where_reasons: List[str] = Field(default_factory=list)
    status: str = "accepted"
    rejection_code: Optional[str] = None
    rejection_reason: Optional[str] = None
    brand_evaluations: List[BrandEval] = Field(default_factory=list)

    def reject(self, code: str, reason: str):
        self.status, self.rejection_code, self.rejection_reason = "rejected", code, reason


class SelectedBrand(BaseModel):
    brand_id: str
    brand_name: str
    match_score: float
    reason: str = ""
    creative_url: str = ""


class FinalBreak(BaseModel):
    break_id: str
    timestamp: float
    duration_seconds: float
    where_score: float
    scene_before: str
    scene_after: str
    brand: SelectedBrand
    reasons: List[str] = Field(default_factory=list)


class AuditRecord(BaseModel):
    timestamp: float
    status: str  # ACCEPTED, REJECTED, BLOCKED
    engine: str  # WHERE, WHETHER, WHAT
    reason_code: str
    reason: str
    details: Optional[dict] = None


class AnalysisResult(BaseModel):
    video_id: str
    filename: str = ""
    duration_seconds: float = 0.0
    video_url: str = ""
    providers: Dict[str, str] = Field(default_factory=dict)
    rules: dict = Field(default_factory=dict)
    scenes: List[Scene] = Field(default_factory=list)
    shot_cuts: List[float] = Field(default_factory=list)
    speech: List[dict] = Field(default_factory=list)
    candidates: List[Candidate] = Field(default_factory=list)
    final_breaks: List[FinalBreak] = Field(default_factory=list)
    audit_logs: List[AuditRecord] = Field(default_factory=list)
    vmap_xml: str = ""
    warnings: List[str] = Field(default_factory=list)
