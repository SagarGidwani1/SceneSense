export type VideoStatus =
  | 'UPLOADED'
  | 'EXTRACTING'
  | 'TRANSCRIBING'
  | 'SEGMENTING'
  | 'UNDERSTANDING'
  | 'GENERATING_CANDIDATES'
  | 'SCORING_WHERE'
  | 'MATCHING_BRANDS'
  | 'APPLYING_PACING'
  | 'GENERATING_VMAP'
  | 'READY'
  | 'FAILED';

export interface HealthStatus {
  status: string;
  ffmpeg: boolean;
  groq: boolean;
  gemini: boolean;
}

export interface VideoSummary {
  video_id: string;
  filename: string;
  duration_seconds: number;
  status: VideoStatus;
  created_at: string;
}

export interface UploadResult {
  video_id: string;
  filename: string;
  duration_seconds: number;
  status: VideoStatus;
}

export interface AnalysisStatus {
  video_id: string;
  status: VideoStatus;
  progress_percent: number;
  current_step: string;
  error?: string | null;
}

export interface Providers {
  asr: string;
  scene_ai: string;
  brand_ai: string;
}

export interface Rules {
  max_breaks_per_hour: number;
  min_gap_seconds: number;
  max_ad_load_percent: number;
  ad_duration_seconds: number;
  edge_buffer_seconds: number;
  min_where_score: number;
}

export interface Scene {
  scene_id: string;
  start: number;
  end: number;
  summary: string;
  dominant_activity: string;
  context_tags: string[];
  emotion: string;
  tension_score: number;
  cliffhanger_score: number;
  sensitive_contexts: string[];
  thumbnail_url: string | null;
  transcript: string;
}

export interface CandidateFeatures {
  in_speech: boolean;
  silence_before: number;
  silence_after: number;
  sentence_complete: boolean;
  shot_cut_aligned: boolean;
  conversation_continues: boolean;
}

export interface BrandEval {
  brand_id: string;
  brand_name: string;
  blocked: boolean;
  blocked_by: string[];
  relevance: number;
  reason: string;
}

export type CandidateStatus = 'accepted' | 'rejected';

export interface Candidate {
  candidate_id: string;
  timestamp: number;
  scene_before: string;
  scene_after: string;
  features: CandidateFeatures;
  where_score: number;
  where_reasons: string[];
  status: CandidateStatus;
  rejection_code: string | null;
  rejection_reason: string | null;
  brand_evaluations: BrandEval[];
}

export interface FinalBreakBrand {
  brand_id: string;
  brand_name: string;
  match_score: number;
  reason: string;
  creative_url: string;
}

export interface FinalBreak {
  break_id: string;
  timestamp: number;
  duration_seconds: number;
  where_score: number;
  scene_before: string;
  scene_after: string;
  brand: FinalBreakBrand;
  reasons: string[];
}

export type AuditEngine = 'WHERE' | 'WHETHER' | 'WHAT';
export type AuditStatus = 'ACCEPTED' | 'REJECTED' | 'BLOCKED';

export interface AuditRecord {
  timestamp: number;
  status: AuditStatus;
  engine: AuditEngine;
  reason_code: string;
  reason: string;
  details?: Record<string, unknown>;
}

export interface AnalysisResult {
  video_id: string;
  filename: string;
  duration_seconds: number;
  video_url: string;
  providers: Providers;
  rules: Rules;
  scenes: Scene[];
  candidates: Candidate[];
  final_breaks: FinalBreak[];
  audit_logs: AuditRecord[];
  vmap_xml: string;
  warnings: string[];
}

export interface Brand {
  brand_id: string;
  brand_name: string;
  category: string;
  description: string;
  positive_contexts: string[];
  negative_contexts: string[];
  keywords: string[];
  creative_url?: string;
}
