# SceneSense AI — Context-Aware Video Segmentation & Intelligent Ad Placement

## 0. Mission

Build a live, generic, data-driven system for Problem 1 of the hoichoi hackathon:

> Ingest a long-form Bengali drama, segment it into semantically coherent scenes, score which scene boundaries are safe to interrupt, decide whether a break is warranted under pacing/ad-load rules, match each surviving break to the most contextually appropriate synthetic brand, and emit a VMAP manifest, debug JSON, and playable demo.

The system must generalize to an unseen 9th synthetic brand **without code changes** and must never place a brand in a scene matching that brand's `negative_contexts`.

---

## 1. Non-Negotiable Hackathon Requirements

The official Problem 1 statement says the system must solve three questions:

### WHERE
Is this timestamp a natural, non-jarring place to cut?
- Mid-sentence cuts are heavily penalized.

### WHETHER
Should a break be placed here at all?
- Respect maximum breaks/hour.
- Respect minimum gap between breaks.
- Respect maximum ad-load percentage.

### WHAT
Which synthetic brand/creative belongs in the slot?
- Dominant scene activity/context matters.
- `negative_contexts` are a **hard block**, not a soft penalty.

### MVP must produce
- Video input
- Scene segmentation
- Break candidate scoring
- Generic brand matching
- Unseen 9th brand support without code changes
- VMAP manifest
- Debug JSON
- Playable demo that inserts the ad and resumes the episode

### Auto-disqualifier defense
NEVER:
- Hard-code timestamps for sample videos.
- Hard-code brand assignments for sample videos.
- Violate a brand's negative context.
- Depend on a prerecorded/non-live-only demo.
- Replace synthetic brands with real company names.

---

## 2. Product Concept

### Product name
**SceneSense AI**

### One-line pitch

> SceneSense uses AI to find the safest narrative break, decides whether an ad should be inserted, and selects a contextually relevant synthetic brand while enforcing hard safety constraints.

### Judge demo story

1. Upload/select a Bengali drama video.
2. System analyzes it.
3. Timeline shows detected scenes and candidate breaks.
4. System explains accepted/rejected candidates.
5. Show selected brand and why it fits.
6. Show a blocked brand because of a negative context.
7. Generate/show VMAP XML.
8. Play the episode; at the selected time the synthetic ad plays and the episode resumes.
9. Add or load a new 9th brand and demonstrate that no code change is required.

---

# 3. High-Level Architecture

```text
                       VIDEO
                         |
                         v
              +----------------------+
              | Video Ingestion      |
              | FFmpeg / metadata    |
              +----------+-----------+
                         |
          +--------------+--------------+
          |                             |
          v                             v
+--------------------+       +----------------------+
| Visual Segmentation|       | Audio/Speech         |
| PySceneDetect      |       | ASR + timestamps     |
+---------+----------+       +----------+-----------+
          |                             |
          +--------------+--------------+
                         v
              +----------------------+
              | Scene Understanding  |
              | AI structured JSON   |
              +----------+-----------+
                         |
                         v
              +----------------------+
              | Candidate Generator  |
              | pause + sentence +    |
              | scene-boundary logic  |
              +----------+-----------+
                         |
                         v
              +----------------------+
              | WHERE Engine          |
              | naturalness scoring   |
              +----------+-----------+
                         |
                         v
              +----------------------+
              | WHETHER Engine        |
              | pacing constraints    |
              | ad-load constraints   |
              +----------+-----------+
                         |
                         v
              +----------------------+
              | WHAT Engine           |
              | hard-block negatives  |
              | semantic brand rank   |
              +----------+-----------+
                         |
              +----------+----------+
              |                     |
              v                     v
      +---------------+     +---------------+
      | VMAP Generator|     | Debug JSON    |
      +-------+-------+     +---------------+
              |
              v
      +------------------+
      | Playable Player  |
      | content -> ad -> |
      | content resumes  |
      +------------------+
```

---

# 4. Core Design Principle

## AI understands; deterministic code decides.

Use AI for:
- Bengali speech/content understanding
- Scene semantic labeling
- Activity/context extraction
- Emotion/tension estimation
- Semantic brand relevance

Use deterministic Python logic for:
- Hard negative-context blocking
- Min-gap enforcement
- Maximum breaks/hour
- Maximum ad-load
- Candidate validity
- Final scheduling
- VMAP generation

Do NOT ask one LLM call to make the entire ad-placement decision.

---

# 5. Recommended Tech Stack

## Frontend
- Next.js
- TypeScript
- Tailwind CSS
- Lucide icons
- Native HTML5 video or Video.js

## Backend
- Python 3.11+
- FastAPI
- Pydantic
- Uvicorn

## Video
- FFmpeg
- PySceneDetect

## Speech
- Whisper-compatible ASR with word timestamps.
- Keep provider/model configurable through environment variables.
- Groq Whisper may be used when available for fast transcription.

## AI scene understanding
- Gemini video-capable model with structured JSON output.
- Keep model ID configurable via environment variable.

## Storage
- Local filesystem for hackathon MVP.
- JSON/SQLite is enough; no need for Postgres/Redis unless required later.

## Output
- VMAP XML
- Debug JSON
- Generated preview assets

---

# 6. Repository Structure

```text
scenesense-ai/
|
├── README.md
├── PROJECT_PLAN.md
├── .env.example
├── .gitignore
├── docker-compose.yml                 # optional
|
├── backend/
│   ├── requirements.txt
│   ├── app/
│   │   ├── main.py
│   │   ├── config.py
│   │   │
│   │   ├── api/
│   │   │   ├── routes_health.py
│   │   │   ├── routes_videos.py
│   │   │   ├── routes_analysis.py
│   │   │   ├── routes_brands.py
│   │   │   └── routes_outputs.py
│   │   │
│   │   ├── models/
│   │   │   ├── video.py
│   │   │   ├── scene.py
│   │   │   ├── candidate.py
│   │   │   ├── brand.py
│   │   │   ├── break_result.py
│   │   │   └── analysis.py
│   │   │
│   │   ├── services/
│   │   │   ├── video_service.py
│   │   │   ├── scene_detector.py
│   │   │   ├── speech_service.py
│   │   │   ├── scene_understanding.py
│   │   │   ├── candidate_generator.py
│   │   │   ├── where_engine.py
│   │   │   ├── whether_engine.py
│   │   │   ├── brand_matcher.py
│   │   │   ├── scheduler.py
│   │   │   ├── vmap_generator.py
│   │   │   └── playback_service.py
│   │   │
│   │   ├── rules/
│   │   │   ├── pacing_rules.py
│   │   │   ├── hard_constraints.py
│   │   │   └── scoring_weights.py
│   │   │
│   │   ├── prompts/
│   │   │   └── scene_understanding_prompt.txt
│   │   │
│   │   └── utils/
│   │       ├── ffmpeg.py
│   │       ├── timestamps.py
│   │       ├── json_utils.py
│   │       └── logging.py
│   │
│   ├── data/
│   │   ├── brands_catalog.json
│   │   ├── rules.json
│   │   └── sample_metadata/
│   │
│   ├── storage/
│   │   ├── uploads/
│   │   ├── audio/
│   │   ├── scenes/
│   │   ├── ads/
│   │   ├── manifests/
│   │   └── debug/
│   │
│   └── tests/
│       ├── test_brand_blocking.py
│       ├── test_pacing.py
│       ├── test_timestamp_validation.py
│       ├── test_generalization.py
│       └── test_vmap.py
│
├── frontend/
│   ├── package.json
│   ├── next.config.ts
│   ├── app/
│   │   ├── page.tsx
│   │   ├── layout.tsx
│   │   └── globals.css
│   │
│   ├── components/
│   │   ├── UploadPanel.tsx
│   │   ├── VideoPlayer.tsx
│   │   ├── Timeline.tsx
│   │   ├── SceneList.tsx
│   │   ├── BreakCard.tsx
│   │   ├── BrandMatchCard.tsx
│   │   ├── DebugAudit.tsx
│   │   ├── VmapViewer.tsx
│   │   ├── ProcessingProgress.tsx
│   │   └── UnseenBrandTest.tsx
│   │
│   ├── lib/
│   │   ├── api.ts
│   │   ├── types.ts
│   │   └── format.ts
│   │
│   └── public/
│       └── ads/
│
├── scripts/
│   ├── analyze_video.py
│   ├── seed_demo_data.py
│   ├── validate_catalog.py
│   └── add_unseen_brand_demo.py
│
└── docs/
    ├── ARCHITECTURE.md
    ├── API.md
    └── DEMO_SCRIPT.md
```

---

# 7. Data Models

## 7.1 Brand schema

`backend/data/brands_catalog.json`

```json
{
  "brands": [
    {
      "brand_id": "brand_01",
      "brand_name": "Synthetic_FreshBite",
      "category": "food",
      "creative_file": "ads/freshbite.mp4",
      "description": "Everyday family food and grocery brand",
      "positive_contexts": [
        "family meal",
        "cooking",
        "dining",
        "grocery shopping",
        "celebration"
      ],
      "negative_contexts": [
        "funeral",
        "death",
        "hospital emergency",
        "serious injury"
      ],
      "keywords": [
        "food",
        "meal",
        "kitchen",
        "family",
        "grocery"
      ]
    }
  ]
}
```

Important:
- Brand matching code reads this schema dynamically.
- Never write brand-specific logic in Python.
- Adding a new brand must require only adding JSON data + creative.

---

## 7.2 Scene schema

```json
{
  "scene_id": "scene_07",
  "start": 421.4,
  "end": 508.2,
  "summary": "Family discusses dinner after returning home",
  "dominant_activity": "family_meal",
  "context_tags": [
    "family",
    "dining",
    "home"
  ],
  "emotion": "neutral",
  "tension_score": 0.24,
  "dialogue_density": 0.45,
  "cliffhanger_score": 0.12,
  "dialogue_segments": [],
  "visual_shots": []
}
```

---

## 7.3 Candidate schema

```json
{
  "candidate_id": "candidate_13",
  "timestamp": 433.1,
  "scene_id": "scene_07",
  "speech_state": {
    "speaker_active": false,
    "sentence_complete": true,
    "pause_before": 1.7,
    "pause_after": 1.4
  },
  "visual_state": {
    "near_scene_boundary": true,
    "transition_strength": 0.82
  },
  "where_score": 89,
  "rejection": null
}
```

---

## 7.4 Final break schema

```json
{
  "break_id": "break_01",
  "timestamp": 433.1,
  "duration_seconds": 10,
  "where_score": 89,
  "whether_decision": "accepted",
  "brand": {
    "brand_id": "brand_01",
    "brand_name": "Synthetic_FreshBite",
    "match_score": 93
  },
  "reasons": [
    "scene boundary",
    "sentence completed",
    "dialogue pause",
    "low tension",
    "family meal context"
  ]
}
```

---

# 8. Rules Configuration

`backend/data/rules.json`

```json
{
  "max_breaks_per_hour": 3,
  "min_gap_seconds": 420,
  "max_ad_load_percent": 8,
  "candidate": {
    "min_pause_seconds": 0.8,
    "prefer_sentence_end": true,
    "prefer_scene_boundary": true
  }
}
```

### IMPORTANT
These example values are placeholders only.

**Do not assume the handbook values.** Replace them with the exact official values once available. The code must load them from configuration rather than hard-code them.

---

# 9. WHERE Engine

Goal:
Find natural interruption points.

## Inputs
- Scene boundaries
- Word-level ASR timestamps
- Sentence boundaries
- Pause durations
- Scene semantic metadata

## Candidate generation
Generate candidate timestamps around:
1. Visual scene boundaries.
2. Sentence endings.
3. Natural speech pauses.
4. Transitions between semantic sub-events.

## Reject immediately
- Speaker actively speaking.
- Timestamp falls inside a word.
- Timestamp falls inside a sentence unless a strong natural pause exists.
- Candidate is visually/narratively chaotic.

## Example score
Keep weights configurable.

```text
where_score =
    sentence_completion * W1
  + pause_quality        * W2
  + scene_boundary       * W3
  + transition_quality   * W4
  + (1 - tension)        * W5
  + (1 - cliffhanger)    * W6
```

Do not hard-code a particular weight set into architecture. Put weights in `scoring_weights.py` or config so they can be tuned after testing.

---

# 10. Speech / Dialogue Analysis

Extract audio:

```bash
ffmpeg -i input.mp4 -vn -ac 1 -ar 16000 audio.wav
```

Run ASR with word timestamps.

Required information:
- Word start/end
- Segment start/end
- Speaker state when available
- Language
- Sentence/phrase boundaries

Use silence detection only as one signal.

**Do not use a fixed silence threshold as the sole definition of a safe break.**

A 1-second pause inside a dramatic sentence is not automatically safe.

---

# 11. Scene Understanding AI

For each semantic scene, ask the AI for strict JSON.

Example output:

```json
{
  "summary": "A family eats dinner while discussing a recent trip",
  "dominant_activity": "family_meal",
  "context_tags": ["family", "dining", "home", "food"],
  "emotion": "neutral",
  "tension_score": 0.18,
  "cliffhanger_score": 0.08,
  "sensitive_contexts": [],
  "dialogue_state": "conversation_paused",
  "scene_completion_confidence": 0.91
}
```

The model output must be validated with Pydantic before entering the rule engine.

If AI output fails schema validation:
- Retry once with a stricter prompt.
- If still invalid, mark analysis as failed instead of inventing values.

---

# 12. WHETHER Engine

This engine decides whether accepted candidates can become final ad breaks.

Apply rules in this order:

```text
1. Candidate itself must pass WHERE.
2. Enforce episode blackout rules if specified.
3. Enforce minimum gap.
4. Enforce maximum breaks/hour.
5. Enforce maximum ad-load percentage.
6. Rank remaining candidates.
7. Select final slots.
```

Every rejected candidate should create an audit record.

Example:

```json
{
  "timestamp": 495.3,
  "status": "rejected",
  "reason_code": "MIN_GAP_VIOLATION",
  "reason": "Candidate is 62 seconds from previous accepted break"
}
```

---

# 13. WHAT Engine — Brand Matching

## Step 1: Hard block

For each candidate and every brand:

```text
if scene_context intersects brand.negative_contexts:
    status = BLOCKED
```

Blocked brands must never be selected.

## Step 2: Rank survivors

Score eligible brands using:
- Dominant activity similarity
- Positive context similarity
- Description similarity
- Keyword/context overlap

Possible implementation:
- Embeddings + cosine similarity.
- Or structured semantic scoring from the AI, followed by deterministic ranking.

The final choice must come only from the brands surviving the hard-block step.

---

# 14. 9th Brand Generalization Test

Build a UI/API operation that loads a new brand into the catalogue.

Example:

```json
{
  "brand_id": "brand_09",
  "brand_name": "Synthetic_TravelCo",
  "category": "travel",
  "creative_file": "ads/travelco.mp4",
  "positive_contexts": [
    "railway station",
    "packing bags",
    "road trip",
    "vacation"
  ],
  "negative_contexts": [
    "funeral",
    "hospital",
    "serious accident"
  ]
}
```

Then run the same engine.

Expected:
- No Python changes.
- No frontend code changes.
- Brand automatically appears in matching candidates.
- Brand is blocked whenever a negative context is detected.

This should be shown to judges if time permits.

---

# 15. VMAP Generator

Generate standards-compliant VMAP XML from final break objects.

Conceptual structure:

```xml
<vmap:VMAP>
  <vmap:AdBreak
      breakType="linear"
      breakId="break_01"
      timeOffset="00:07:13.100">
    <vmap:AdSource>
      ...
    </vmap:AdSource>
  </vmap:AdBreak>
</vmap:VMAP>
```

Requirements:
- Valid XML.
- Correct timestamps.
- One entry per final break.
- Synthetic brand metadata only.
- Save as `manifest.vmap.xml`.

Also provide a raw XML viewer in the UI.

---

# 16. Playable Demo

The player is mandatory.

## Behavior

```text
episode video
      |
      | reaches break timestamp
      v
pause episode
      |
      v
play synthetic ad
      |
      v
resume episode
```

The frontend may implement this using a single HTML5 player plus a controlled ad-overlay/video element, or another simple reliable mechanism.

Do NOT depend on an external ad server for the hackathon demo.

The ad can be a local synthetic MP4 mapped from the brand catalogue.

---

# 17. Frontend UI

Keep it simple and professional. No unnecessary dashboard screens.

## Main screen

### Header
- SceneSense AI
- `Context-Aware Ad Intelligence`

### Left
Video player.

### Center
Timeline:
- Scene boundaries
- Candidate break markers
- Accepted breaks
- Rejected markers on demand

### Right
Selected break card:

```text
BREAK #1
07:13.1

WHERE
89/100

WHETHER
ACCEPTED

WHAT
Synthetic_FreshBite
93% match

Why?
✓ Sentence completed
✓ Low tension
✓ Family meal context
✓ Safe brand context
```

### Bottom tabs
1. `Scenes`
2. `Audit Log`
3. `VMAP XML`
4. `Brand Match`

---

# 18. Debug Audit Panel

This is a major judge-facing feature.

Show:

```text
WHERE
07:10.4   REJECTED   Mid-dialogue
07:13.1   ACCEPTED   Scene boundary + sentence complete

WHETHER
11:22.0   REJECTED   Minimum-gap violation

WHAT
14:10.0   BLOCKED    Synthetic_FreshBite
                     Reason: funeral context
14:10.0   SELECTED   Synthetic_Insurance
                     Reason: eligible + highest relevance
```

Every decision should have:
- timestamp
- status
- engine
- reason code
- human-readable reason

---

# 19. API Design

## Health

`GET /api/health`

## Upload

`POST /api/videos/upload`

Returns:
```json
{
  "video_id": "uuid",
  "status": "uploaded"
}
```

## Start analysis

`POST /api/videos/{video_id}/analyze`

## Analysis status

`GET /api/videos/{video_id}/status`

## Get scenes

`GET /api/videos/{video_id}/scenes`

## Get candidates

`GET /api/videos/{video_id}/candidates`

## Get final breaks

`GET /api/videos/{video_id}/breaks`

## Get debug audit

`GET /api/videos/{video_id}/audit`

## Get VMAP

`GET /api/videos/{video_id}/vmap`

## Get brand catalogue

`GET /api/brands`

## Add/test brand

`POST /api/brands`

## Run unseen-brand test

`POST /api/videos/{video_id}/test-brand/{brand_id}`

---

# 20. Analysis Job State

For the MVP, use simple background jobs.

```text
UPLOADED
   ↓
EXTRACTING
   ↓
TRANSCRIBING
   ↓
SEGMENTING
   ↓
UNDERSTANDING
   ↓
GENERATING_CANDIDATES
   ↓
SCORING_WHERE
   ↓
APPLYING_PACING
   ↓
MATCHING_BRANDS
   ↓
GENERATING_VMAP
   ↓
READY
```

Store progress in a JSON state file or lightweight SQLite table.

The frontend polls `/status` every 1–2 seconds.

---

# 21. Error Handling

Never silently fabricate results.

Examples:

- Missing FFmpeg → clear startup error.
- ASR failure → mark speech analysis failed.
- AI timeout → retry once, then show failure.
- Invalid brand catalogue → reject catalogue with validation error.
- Missing ad creative → brand cannot be selected.
- Invalid VMAP → fail validation before marking analysis ready.

Use structured logs.

---

# 22. Performance Strategy

Do NOT optimize premature processing before correctness.

Priority:

```text
1. Correct
2. Generalizable
3. Reliable live demo
4. Fast enough
5. UI polish
```

For repeated demo runs:
- Cache intermediate analysis by file hash.
- Cache ASR.
- Cache scene metadata.
- Cache AI scene understanding.
- Cache final manifest.

Caching is for speed only; it must not become hard-coded sample output.

---

# 23. Testing Strategy

## Test A — Mid-dialogue

Create/find a timestamp where a visual shot changes while someone is speaking.

Expected:
```text
REJECTED
Reason: dialogue active / sentence incomplete
```

## Test B — Natural boundary

Expected:
```text
ACCEPTED
```

## Test C — Minimum gap

Two otherwise good candidates too close together.

Expected:
```text
first accepted
second rejected
```

## Test D — Ad load

Make enough candidates to exceed configured ad load.

Expected:
```text
later candidates rejected
```

## Test E — Negative context

Funeral scene + food brand.

Expected:
```text
Food brand = BLOCKED
```

## Test F — 9th brand

Add new brand JSON without code modification.

Expected:
```text
new brand participates in ranking automatically
```

## Test G — No hard-coded timestamps

Change input video or trim the sample.

Expected:
- Break positions change based on the analysis.
- No timestamp mapping table exists in code.

---

# 24. Anti-Hardcoding Rules for Developers

Before final submission, search the entire repository for:

- sample video filenames inside decision logic
- exact timestamp constants tied to sample videos
- brand IDs inside `if/elif` matching logic
- `if video == ...`
- `if brand == ...`
- manually selected final breaks

Allowed:
- default configuration
- schema examples
- test fixtures
- generic rules

Not allowed:
- special-casing real submission videos
- special-casing specific brands

---

# 25. 12-Hour Execution Plan

## Hour 0–1: Setup

- Create repo.
- Create FastAPI backend.
- Create Next.js frontend.
- Install FFmpeg/PySceneDetect dependencies.
- Configure `.env`.
- Add one test video and brand catalogue.

## Hour 1–3: Video + Speech

Build:
- upload
- metadata
- FFmpeg audio extraction
- ASR timestamps
- visual scene detection

Goal: produce valid scene + speech JSON.

## Hour 3–5: WHERE

Build:
- sentence/pause detection
- candidate generator
- naturalness scoring
- rejection reasons

Goal: correctly reject obvious mid-dialogue candidates.

## Hour 5–6.5: WHETHER

Build:
- config-driven min-gap
- max breaks/hour
- ad-load
- final break scheduler

Goal: deterministic pacing engine.

## Hour 6.5–8: WHAT

Build:
- scene context extraction
- hard negative filter
- semantic ranking
- unseen-brand support

Goal: no negative-context violation.

## Hour 8–9: VMAP + Playback

Build:
- VMAP XML
- local synthetic ad playback
- resume episode

## Hour 9–10: UI

Build:
- timeline
- selected break card
- audit panel
- brand panel
- VMAP viewer

## Hour 10–11: Testing

Run all seven tests above.

Fix correctness issues first.

## Hour 11–12: Demo hardening

- Test from clean restart.
- Verify `.env`.
- Verify live backend/frontend.
- Verify GitHub README.
- Record backup demo video if allowed.
- Prepare 5-minute explanation.

---

# 26. Demo Script — 5 Minutes

## 0:00–0:30 — Problem

"A normal ad insertion system knows when a scene changes. SceneSense asks three deeper questions: where can we interrupt naturally, whether we should interrupt at all, and which brand is safe and relevant?"

## 0:30–1:30 — Analyze

Upload/select Bengali drama.

Show scenes and timeline appearing.

## 1:30–2:30 — WHERE

Open audit.

Show:
```text
candidate → rejected → mid-dialogue
candidate → accepted → sentence complete
```

## 2:30–3:20 — WHETHER

Show:
```text
candidate → rejected → min gap
```

Explain pacing rules are deterministic/config-driven.

## 3:20–4:10 — WHAT

Show funeral/sensitive context.

Demonstrate:
```text
FoodBrand → BLOCKED
Other eligible brand → SELECTED
```

Then show the unseen 9th brand being added without code changes.

## 4:10–4:40 — VMAP + playback

Open VMAP.

Play video until break.

Ad plays.

Episode resumes.

## 4:40–5:00 — Engineering point

"AI performs video and context understanding. Deterministic rules guarantee pacing and hard safety constraints. Brands are data-driven, so unseen brands require no code changes."

---

# 27. README Requirements

The README must contain:

1. Problem
2. Solution
3. Architecture diagram
4. Tech stack
5. Local setup
6. Environment variables
7. How to run frontend
8. How to run backend
9. How to load a video
10. How to add a new brand
11. How to generate VMAP
12. Example debug output
13. Testing strategy
14. Known limitations

Do not claim production scale or measured business impact unless actually tested.

---

# 28. Environment Variables

`.env.example`

```env
# Backend
APP_ENV=development
UPLOAD_DIR=./storage/uploads

# ASR
ASR_PROVIDER=groq
ASR_MODEL=<configured-whisper-model>
GROQ_API_KEY=

# Gemini
GEMINI_API_KEY=
GEMINI_MODEL=<configured-video-capable-model>

# Frontend
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
```

Never commit API keys.

---

# 29. What NOT to Build

Do not spend hackathon time on:

- Authentication
- User profiles
- Database-heavy architecture
- Cloud microservices
- Real ad-server integration
- Real company brands
- Advanced analytics
- Billing
- Notifications
- Mobile app
- Production-scale deployment
- Fancy animations that do not improve the demo

The winning core is the decision engine + proof of correctness.

---

# 30. Build Order Rule for Antigravity

Antigravity must build in this exact dependency order:

```text
1. Repository + environment
2. Backend foundation
3. Video ingestion
4. ASR + timestamps
5. Scene detection
6. Scene understanding
7. WHERE engine
8. WHETHER engine
9. WHAT engine
10. VMAP
11. Playback
12. Frontend dashboard
13. Tests
14. README/demo polish
```

Do not build the full UI first.

Every stage must produce testable JSON before moving to the next stage.

---

# 31. Definition of Done

The MVP is done only when all are true:

- [ ] Video can be uploaded/selected.
- [ ] Scenes are generated automatically.
- [ ] Speech timestamps are available.
- [ ] Candidate breaks are generated automatically.
- [ ] Mid-dialogue candidates can be rejected.
- [ ] Pacing constraints are enforced from configuration.
- [ ] Negative-context brands are hard-blocked.
- [ ] Eligible brands are semantically ranked.
- [ ] New 9th brand works without code changes.
- [ ] VMAP XML is generated.
- [ ] Player actually inserts the synthetic ad.
- [ ] Episode resumes after ad.
- [ ] Debug audit explains decisions.
- [ ] No sample-specific timestamps/brand assignments exist in decision logic.
- [ ] System runs live from a clean start.

---

# 32. Final Engineering Principle

Do not try to impress judges with the number of AI calls.

Impress them with this:

```text
RAW VIDEO
   ↓
AI understands what is happening
   ↓
Candidate break points
   ↓
WHERE = Is it natural?
   ↓
WHETHER = Is a break allowed?
   ↓
WHAT = Which brand is safe + relevant?
   ↓
VMAP
   ↓
REAL PLAYBACK
```

The strongest feature is not the UI.

It is the **generic, explainable decision engine that survives unseen videos and unseen brands without hard-coding**.
