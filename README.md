# SceneSense — Context-Aware Video Segmentation & Ad Placement

Upload a long-form Bengali drama → semantic scenes → safe break points → brand per break → VMAP + debug JSON + a player that cuts to the ad and resumes.

**AI understands; deterministic code decides.** AI labels scenes and judges brand fit. Plain Python enforces every hard rule, so every placement is explainable and reproducible.

## The problem

Mid-roll ads on long-form video are usually dropped at fixed timestamps: mid-sentence, mid-emotion, or right after a funeral scene with a food ad. SceneSense answers three questions for every possible break:

- **WHERE** can a break go without cutting speech, a sentence or a running conversation?
- **WHAT** brand fits the scenes around it, and which brands must be blocked there?
- **WHETHER** a break should be used at all, given pacing and ad-load limits?

## Architecture

```
frontend/  Next.js 14 + Tailwind  ── upload, progress stepper, player, tabs
    │  HTTP (NEXT_PUBLIC_API_BASE_URL)
backend/   FastAPI
    ├── api/        routes: videos, brands, rules, health
    ├── services/   pipeline stages (speech, video, scenes, where/what/whether, vmap)
    ├── rules/      hard constraints + pacing rules (pure Python)
    ├── data/       brands_catalog.json, rules.json
    └── storage/    uploads, audio, keyframes, rendered ads, debug output (git-ignored)
scripts/   analyze_video.py — run the full pipeline from the command line
```

Analysis runs in a background thread per video; the UI polls `/api/videos/{id}/status`.

## Pipeline

| Step | How |
|---|---|
| Audio | ffmpeg → 16 kHz mono mp3 |
| ASR | Groq `whisper-large-v3`, Bengali, **word timestamps**. Smeared words (Whisper stretching a word over music) are clipped |
| Shots + keyframes | One ffmpeg pass: frame-accurate cut detection + a keyframe every ~max(4 s, duration/180) |
| Scenes | Gemini sees the keyframes + timestamped transcript and proposes scenes, labels, `sensitive_contexts` and `conversation_continues`. Boundaries are **snapped to real shot cuts**. A Bengali keyword net adds sensitive tags and never removes them |
| **WHERE** | One candidate per scene boundary; the best exact cut is searched ±4 s among shot cuts / silence gaps. **Hard reject**: mid-speech, unfinished sentence, dialogue carrying over. Score = sentence end, silence, shot alignment, closed conversation, low tension |
| **WHAT** | One batched AI call scores every slot × brand. **Block** = lexical match OR AI semantic match of `negative_contexts` against the scenes **before and after** the ad. Relevance is led by dominant activity. If the AI is down, any sensitive scene blocks all brands |
| **WHETHER** | Greedy by quality: edge buffer, min gap, max breaks in any rolling 60 min, max ad-load % |
| Output | VMAP 1.0 + inline VAST 3.0 (ElementTree, always well-formed), debug JSON, synthetic creatives rendered per brand |

AI fallback chain: `GEMINI_MODEL` list in order → Groq `openai/gpt-oss-120b`. The UI shows which provider actually ran.

ffmpeg: the system `ffmpeg` is used if it's on PATH, otherwise the binary bundled with `imageio-ffmpeg` (installed by `requirements.txt`), so no separate install is needed.

## API

| Method | Path | Purpose |
|---|---|---|
| GET | `/api/health` | ffmpeg + AI provider status |
| GET | `/api/videos` | list uploaded videos |
| POST | `/api/videos/upload` | upload an episode |
| POST | `/api/videos/{id}/analyze` | start the pipeline |
| GET | `/api/videos/{id}/status` | progress of the pipeline |
| GET | `/api/videos/{id}/result` | scenes, candidates, breaks |
| POST | `/api/videos/{id}/rematch` | re-run brand matching only (no re-ASR) |
| GET | `/api/videos/{id}/vmap` | VMAP 1.0 XML |
| GET | `/api/videos/{id}/debug` | full debug JSON |
| GET/POST/DELETE | `/api/brands` | brand catalog |
| GET/PUT | `/api/rules` | pacing rules |

Interactive docs: `http://localhost:8000/docs`.

## Configuration

Secrets live only in `.env` files, which are git-ignored. Copy the examples:

| File | Variables |
|---|---|
| `.env` (from `.env.example`) | `GROQ_API_KEY`, `GEMINI_API_KEY`, `GEMINI_MODEL`, `ASR_MODEL`, `ASR_LANGUAGE`, `GROQ_LLM_MODEL`, `PUBLIC_BASE_URL` |
| `frontend/.env.local` (from `frontend/.env.example`) | `NEXT_PUBLIC_API_BASE_URL` |

Keys: [Groq](https://console.groq.com/keys) and [Google AI Studio](https://aistudio.google.com/apikey), both free tiers work.

## Run locally

```bash
cp .env.example .env                              # add GROQ_API_KEY + GEMINI_API_KEY
cp frontend/.env.example frontend/.env.local
cd backend && pip install -r requirements.txt
cd ../frontend && npm install
cd .. && start.bat                                # Windows; or run the two commands below
# backend:  cd backend && uvicorn app.main:app --port 8000
# frontend: cd frontend && npm run dev
```
Open http://localhost:3000, drop in an episode, and wait ~3 min for a 23-min episode.

- CLI: `python scripts/analyze_video.py episode.mp4`
- Tests: `cd backend && python -m pytest tests -q`

## Deploy

The backend is **not** a fit for serverless (Vercel/Netlify functions): it runs ffmpeg, holds large uploads, processes for minutes in a background thread, and keeps results on disk. Split it:

**Frontend → Vercel**
1. Import the repo, set **Root Directory** to `frontend`.
2. Env var: `NEXT_PUBLIC_API_BASE_URL=https://<your-backend-host>`.

**Backend → Render (or Railway)** as a long-running Python web service
1. Root directory: `backend`
2. Build: `pip install -r requirements.txt`
3. Start: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
4. Env vars: `GROQ_API_KEY`, `GEMINI_API_KEY`, `PUBLIC_BASE_URL=https://<your-backend-host>`
5. Attach a persistent disk mounted at `backend/storage` or uploads and results are lost on every restart/redeploy.

Free tiers sleep when idle and have little RAM; use at least a ~1 GB instance for full episodes.

## Demo walkthrough
1. Upload → watch the stepper; provider pills show real Groq/Gemini runs.
2. **Breaks** tab → chosen brand + reason; expand to see blocked brands and the negative context that blocked each one.
3. **Candidates** → every boundary with its rejection reason (MID_SPEECH, MIN_GAP, ALL_BRANDS_BLOCKED…).
4. Player → **Next break** → the ad plays, then the episode resumes at the break.
5. **Brands** → add a 9th brand → auto-rematch (no re-ASR, no code change).
6. **Outputs** → VMAP download, debug JSON, audit log.

No timestamps or brand assignments are hard-coded; brands are synthetic (`backend/data/brands_catalog.json`), and rules are in `backend/data/rules.json` (created on first save, editable in the UI; defaults apply until then).
