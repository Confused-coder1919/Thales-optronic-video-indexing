# Thales Optronic Video Indexing Pipeline

A full‑stack video intelligence platform that converts unstructured video into a searchable, analyst‑friendly index of entities, timelines, frames, and transcripts. The system extracts frames, detects entities, aggregates time ranges, generates reports (JSON/PDF/CSV), and provides a web UI for upload, inspection, and unified search.

---

## TL;DR

- Upload a **video file** or paste a **public URL**
- The backend extracts frames, detects entities, and generates reports
- Search across indexed videos using exact + semantic similarity
- Export reports as JSON/PDF/CSV
- Share a **public report link** (read‑only)

---

## Key Features

- **Frame Extraction** at configurable intervals (ffmpeg)
- **Object Detection** with YOLOv8 + domain label mapping
- **Discovery Mode** (caption → entity extraction) for open‑ended labels
- **Smart Sampling** to focus on scene changes
- **Verification Pass** to confirm discovery entities (CLIP)
- **Entity Aggregation** (counts, presence %, time ranges)
- **OCR Extraction** for markings, tail numbers, ship names
- **Audio Cleanup + Speech Detection** to improve transcripts on mixed audio
- **Confidence Scoring** combines detection sources + consistency + OCR evidence
- **Semantic Search** using sentence embeddings
- **Transcription** via Whisper (faster‑whisper)
- **Reports** in JSON / PDF / CSV
- **UI** for upload, progress, timelines, frame gallery, transcript
- **Clickable timeline** → jump video preview + highlight nearest frame
- **Shareable report links** for read‑only viewing

---

## Architecture Overview

**Frontend**
- React + Vite + TypeScript + Tailwind CSS
- Upload UI, progress view, timeline, frames, transcript, search

**Backend API**
- FastAPI + SQLAlchemy (SQLite)
- REST endpoints for upload, status, report, frames, search, sharing

**Worker**
- Celery + Redis queue
- Handles heavy processing asynchronously

**Storage**
- Local filesystem for frames, reports, transcripts
- SQLite for metadata

---

## Processing Pipeline

1. **Upload** video via UI/API (file or URL)
2. **Extract frames** every N seconds
3. **Detect entities** in each frame (YOLO + discovery + open‑vocab)
4. **Aggregate results** (counts, presence %, time ranges)
5. **Generate reports** JSON/PDF/CSV
6. **Index entities** for semantic search
7. **Serve** results in UI (timelines, frames, transcript)

Progress stages:

```
extracting_frames (0–20)
transcribing_audio (20)
detecting_entities (20–80)
aggregating_report (80–95)
indexing_search (95–100)
```

---

## Tech Stack

**Backend**
- FastAPI, SQLAlchemy, SQLite
- Celery, Redis
- ffmpeg, OpenCV
- ultralytics (YOLOv8)
- sentence‑transformers
- faster‑whisper
- pytesseract + webrtcvad

**Frontend**
- React, TypeScript
- Vite, Tailwind CSS

**Infra**
- Docker + docker‑compose

---

## Repo Structure

```
backend/               FastAPI + worker + pipeline code
frontend/              React UI (Vite + Tailwind)
data/entity_indexing/  Frames, reports, db, index (runtime data)
reports/               Sample outputs
scripts/               Utility scripts
tests/                 API/unit tests
```

---

## Quick Start (Docker)

```bash
# from repo root
docker-compose up --build
```

Services:
- Frontend UI:  http://localhost:5173
- Backend API:  http://localhost:8010
- Redis:        localhost:6379

Usage:
1. Open the UI
2. Upload a video (file or URL)
3. Wait for processing to complete
4. View the report, timeline, frames, and transcript
5. Use the search page
6. Share a public report link from the Video Details page

---

## Local Setup (No Docker)

### 1) Install system dependencies

```bash
brew install ffmpeg tesseract
```

If `webrtcvad` fails to build on macOS, install Xcode command line tools:

```bash
xcode-select --install
```

### 2) Setup Python

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 3) Start Redis

```bash
redis-server
```

### 4) Start API

```bash
uvicorn backend.src.entity_api:app --host 0.0.0.0 --port 8000
```

### 5) Start Worker

```bash
celery -A backend.src.entity_indexing.celery_app.celery_app worker --loglevel=info
```

### 6) Start Frontend

```bash
cd frontend
npm install
VITE_API_BASE=http://localhost:8000 npm run dev
```

---

## Upload from URL (YouTube, etc.)

You can paste a public video URL in the Upload page. The backend uses `yt‑dlp`
to download the file locally before processing. This is free, but download speed
depends on your network and the source server. Make sure you have the rights
to download and process the content and that it complies with the site's terms.

### If you see `HTTP Error 403: Forbidden`
The host is blocking automated downloads. Two free fixes:

1) **Use cookies from your browser**
   - Export cookies (e.g., with a browser extension) and set:
     - `ENTITY_INDEXING_YTDLP_COOKIES=/path/to/cookies.txt`
   - Or, for local (non‑Docker) runs:
     - `ENTITY_INDEXING_YTDLP_COOKIES_FROM_BROWSER=chrome`

2) **Try a different URL/source**
   - Some sources block hotlinking or require auth. Public MP4 URLs usually work.

You can also upload a cookies `.txt` file directly in the Upload page (URL mode).

---

## Shareable Report Links

From a video’s details page, click **Share Report** to generate a public, read‑only link.
This link renders the full report in the UI (timeline, frames, transcript).

---

## Dataset Exporter (COCO + YOLO)

You can export training‑ready datasets directly from existing pipeline outputs.
You can also trigger an export from the UI via **Video Library → Export Dataset**.

```bash
python3 scripts/export_training_dataset.py \
  --output data/entity_indexing/datasets/run_001 \
  --train 0.7 --val 0.2 --test 0.1 \
  --min-confidence 0.3 \
  --sources yolo,clip
```

Outputs:
- COCO annotations (`annotations/instances_*.json`)
- YOLO labels (`labels/{split}/*.txt`)
- Video‑level splits (prevents leakage)
- Taxonomy (`labels.txt`, `labels.json`)
- Manifest (`dataset_manifest.json`)

See `docs/EXPORT_DATASET.md` for details.

---

## API Endpoints (Summary)

```
POST   /api/videos                         - Upload video (multipart)
POST   /api/videos/from-url                - Upload via URL (JSON)
POST   /api/videos/from-url-upload         - Upload via URL + cookies (multipart)
POST   /api/videos/from-url/check          - Test URL before download (multipart)
GET    /api/videos                         - List videos (filterable, paginated)
GET    /api/videos/{id}                    - Get video details
GET    /api/videos/{id}/status             - Processing status
GET    /api/videos/{id}/report             - Full report JSON
GET    /api/videos/{id}/transcript         - Transcript JSON
GET    /api/videos/{id}/frames             - Paginated frames
GET    /api/videos/{id}/frames/nearest     - Nearest frame to timestamp
GET    /api/videos/{id}/frames/{name}      - Frame image
GET    /api/videos/{id}/download           - Download original video
GET    /api/videos/{id}/report/download    - Download report (JSON/PDF)
GET    /api/videos/{id}/report/csv/download - Download CSV
GET    /api/datasets/export                - Export COCO + YOLO dataset (ZIP)
POST   /api/videos/{id}/share              - Create share link
GET    /api/share/{token}                  - Public share report JSON
DELETE /api/videos/{id}                    - Delete video and files
GET    /api/search                         - Search across videos
GET    /health                             - Health check
```

---

## Output Layout

Generated per video under `data/entity_indexing/`:

- `frames/<video_id>/` (raw + annotated frames)
- `reports/<video_id>/report.json`
- `reports/<video_id>/report.pdf`
- `reports/<video_id>/report.csv`
- `reports/<video_id>/transcript.json`
- `index.db` (SQLite metadata)

---

## Detection Notes (Accuracy)

This system uses **YOLOv8 COCO classes**, then maps them into your entity taxonomy. It also supports:
- **Discovery mode** (caption → entity extraction) to propose labels directly from frames
- **Open‑vocabulary detection** (CLIP) for finer labels such as **aircraft carrier**, **fighter jet**, and **satellite**

Example mapping (see `backend/src/entity_indexing/processing.py`):
- `person` → military personnel
- `airplane` → aircraft
- `helicopter` → helicopter
- `truck` → armored vehicle

Accuracy depends on video quality and model limits. If you see false positives or missed objects, tune:
- `ENTITY_INDEXING_MIN_CONFIDENCE` (YOLO threshold)
- `ENTITY_INDEXING_DISCOVERY_MIN_SCORE` (caption confidence threshold)
- `ENTITY_INDEXING_DISCOVERY_EVERY_N` (discovery sampling rate)
- `ENTITY_INDEXING_OPEN_VOCAB_THRESHOLD` (CLIP threshold)
- `ENTITY_INDEXING_MIN_CONSECUTIVE` (filter short blips)

Tip: Discovery mode filters generic phrases (e.g., “large”, “many”, “over”) when
`ENTITY_INDEXING_DISCOVERY_ONLY_MILITARY=true`.

---

## Environment Variables (Common)

See `.env.example` for the full list. Common flags:

- `ENTITY_INDEXING_REDIS_URL` (default: redis://localhost:6379/0)
- `ENTITY_INDEXING_DATABASE_URL` (default: sqlite:///data/entity_indexing/index.db)
- `ENTITY_INDEXING_DATA_DIR` (default: ./data/entity_indexing)
- `ENTITY_INDEXING_WHISPER_MODEL` (default: base)

Sampling / detection:
- `ENTITY_INDEXING_SMART_SAMPLING_ENABLED` (default: true)
- `ENTITY_INDEXING_SMART_SAMPLING_DIFF_THRESHOLD` (default: 0.06)
- `ENTITY_INDEXING_SMART_SAMPLING_MIN_KEEP` (default: 6)
- `ENTITY_INDEXING_MIN_CONFIDENCE` (default: 0.25)
- `ENTITY_INDEXING_MIN_CONSECUTIVE` (default: 2)
- `ENTITY_INDEXING_ANNOTATE_FRAMES` (default: true)

Open‑vocab / discovery:
- `ENTITY_INDEXING_OPEN_VOCAB_ENABLED` (default: false)
- `ENTITY_INDEXING_OPEN_VOCAB_THRESHOLD` (default: 0.27)
- `ENTITY_INDEXING_OPEN_VOCAB_EVERY_N` (default: 1)
- `ENTITY_INDEXING_OPEN_VOCAB_MIN_CONSECUTIVE` (default: 1)
- `ENTITY_INDEXING_OPEN_VOCAB_LABELS` (default: aircraft carrier, fighter jet, satellite, ...)
- `ENTITY_INDEXING_DISCOVERY_ENABLED` (default: true)
- `ENTITY_INDEXING_DISCOVERY_MODEL` (default: Salesforce/blip-image-captioning-base)
- `ENTITY_INDEXING_DISCOVERY_EVERY_N` (default: 1)
- `ENTITY_INDEXING_DISCOVERY_MIN_SCORE` (default: 0.2)
- `ENTITY_INDEXING_DISCOVERY_MIN_CONSECUTIVE` (default: 1)
- `ENTITY_INDEXING_DISCOVERY_MAX_PHRASES` (default: 8)
- `ENTITY_INDEXING_DISCOVERY_ONLY_MILITARY` (default: true)

Verification:
- `ENTITY_INDEXING_VERIFY_ENABLED` (default: true)
- `ENTITY_INDEXING_VERIFY_THRESHOLD` (default: 0.27)
- `ENTITY_INDEXING_VERIFY_EVERY_N` (default: 3)
- `ENTITY_INDEXING_VERIFY_MAX_LABELS` (default: 12)

OCR + audio:
- `ENTITY_INDEXING_OCR_ENABLED` (default: true)
- `ENTITY_INDEXING_OCR_EVERY_N` (default: 4)
- `ENTITY_INDEXING_OCR_MIN_CONFIDENCE` (default: 60)
- `ENTITY_INDEXING_AUDIO_CLEANUP_ENABLED` (default: true)
- `ENTITY_INDEXING_AUDIO_CLEANUP_FILTER` (default: highpass=f=200,lowpass=f=3000,afftdn=nf=-25)
- `ENTITY_INDEXING_AUDIO_MUSIC_DETECTION_ENABLED` (default: true)
- `ENTITY_INDEXING_AUDIO_SPEECH_THRESHOLD` (default: 0.1)
- `ENTITY_INDEXING_AUDIO_VAD_MODE` (default: 2)

URL download (yt‑dlp):
- `ENTITY_INDEXING_YTDLP_USER_AGENT`
- `ENTITY_INDEXING_YTDLP_COOKIES`
- `ENTITY_INDEXING_YTDLP_COOKIES_FROM_BROWSER`

Confidence:
- `ENTITY_INDEXING_CONFIDENCE_MIN_SCORE` (default: 0.1)

---

## Troubleshooting

**403 Forbidden on URL upload**
- Use cookies file or `ENTITY_INDEXING_YTDLP_COOKIES_FROM_BROWSER=chrome`

**Transcript error / empty audio**
- Some videos have no speech; audio analysis reports speech ratio

**Frames not showing**
- Ensure worker is running; frames are generated by the Celery worker

**webrtcvad build failure (local)**
- Install build tools (`xcode-select --install` on macOS)

---

## License

Internal / academic use. See LICENSE.
