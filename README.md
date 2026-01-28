# Thales Optronic Video Indexing Pipeline

A full-stack video intelligence platform that converts unstructured video into a searchable, analyst-friendly index of entities, timelines, frames, and transcripts. The system extracts frames, detects entities, aggregates time ranges, generates reports (JSON/PDF/CSV), and provides a web UI for upload, inspection, and unified search.

---

## TL;DR

- Upload a video in the web UI
- The backend extracts frames, detects entities, and generates reports
- Search across indexed videos using exact + semantic similarity
- Export reports as JSON/PDF/CSV

---

## Key Features

- **Frame Extraction** at configurable intervals (ffmpeg)
- **Object Detection** with YOLOv8 + label mapping
- **Discovery Mode** (caption → entity extraction) for open‑ended labels
- **Smart Sampling** to focus on scene changes
- **Verification Pass** to confirm discovery entities
- **Entity Aggregation** (counts, presence %, time ranges)
- **OCR Extraction** for markings, tail numbers, ship names
- **Audio Cleanup + Speech Detection** to improve transcripts on mixed audio
- **Confidence Scoring** combines detection sources + consistency + OCR evidence
- **Semantic Search** using sentence embeddings
- **Transcription** via Whisper (faster-whisper)
- **Reports** in JSON/PDF/CSV
- **UI** for upload, progress, timelines, and frame gallery

---

## Architecture Overview

**Frontend**
- React + Vite + TypeScript + Tailwind CSS
- Upload UI, progress view, timeline, frames, transcript, search

**Backend API**
- FastAPI + SQLAlchemy (SQLite)
- REST endpoints for upload, status, report, frames, search

**Worker**
- Celery + Redis queue
- Handles heavy processing asynchronously

**Storage**
- Local filesystem for frames, reports, and transcripts
- SQLite for metadata

---

## Processing Pipeline

1. **Upload** video via UI/API
2. **Extract frames** every N seconds
3. **Detect entities** in each frame
4. **Aggregate results** (counts, presence %, time ranges)
5. **Generate reports** JSON/PDF/CSV
6. **Index entities** for semantic search
7. **Serve** results in UI (timelines, frames, transcript)

---

## Tech Stack

**Backend**
- FastAPI, SQLAlchemy, SQLite
- Celery, Redis
- ffmpeg, OpenCV
- ultralytics (YOLOv8)
- sentence-transformers
- faster-whisper

**Frontend**
- React, TypeScript
- Vite, Tailwind CSS

**Infra**
- Docker + docker-compose

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

### Upload from URL (YouTube, etc.)

You can paste a public video URL in the Upload page. The backend uses `yt-dlp`
to download the file locally before processing. This is free, but download speed
depends on your network and the source server. Make sure you have the rights
to download and process the content and that it complies with the site's terms.

If you see `HTTP Error 403: Forbidden`, the host is blocking automated downloads.
Two free fixes:

1) **Use cookies from your browser**
   - Export cookies (e.g., with a browser extension) and set:
     - `ENTITY_INDEXING_YTDLP_COOKIES=/path/to/cookies.txt`
   - Or, for local (non‑Docker) runs:
     - `ENTITY_INDEXING_YTDLP_COOKIES_FROM_BROWSER=chrome`

2) **Try a different URL/source**
   - Some sources block hotlinking or require auth. Public MP4 URLs usually work.

You can also upload a cookies `.txt` file directly in the Upload page (URL mode).

---

## Local Setup (No Docker)

### 1) Install system dependencies

```bash
brew install ffmpeg tesseract
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

## Environment Variables

See `.env.example` for full list. Common flags:

- `ENTITY_INDEXING_REDIS_URL` (default: redis://localhost:6379/0)
- `ENTITY_INDEXING_DATABASE_URL` (default: sqlite:///data/entity_indexing/index.db)
- `ENTITY_INDEXING_DATA_DIR` (default: ./data/entity_indexing)
- `ENTITY_INDEXING_WHISPER_MODEL` (default: base)
- `ENTITY_INDEXING_SMART_SAMPLING_ENABLED` (default: true)
- `ENTITY_INDEXING_SMART_SAMPLING_DIFF_THRESHOLD` (default: 0.06)
- `ENTITY_INDEXING_SMART_SAMPLING_MIN_KEEP` (default: 6)
- `ENTITY_INDEXING_MIN_CONFIDENCE` (default: 0.25)
- `ENTITY_INDEXING_MIN_CONSECUTIVE` (default: 2)
- `ENTITY_INDEXING_ANNOTATE_FRAMES` (default: true)
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
- `ENTITY_INDEXING_VERIFY_ENABLED` (default: true)
- `ENTITY_INDEXING_VERIFY_THRESHOLD` (default: 0.27)
- `ENTITY_INDEXING_VERIFY_EVERY_N` (default: 3)
- `ENTITY_INDEXING_VERIFY_MAX_LABELS` (default: 12)
- `ENTITY_INDEXING_OCR_ENABLED` (default: true)
- `ENTITY_INDEXING_OCR_EVERY_N` (default: 4)
- `ENTITY_INDEXING_OCR_MIN_CONFIDENCE` (default: 60)
- `ENTITY_INDEXING_AUDIO_CLEANUP_ENABLED` (default: true)
- `ENTITY_INDEXING_AUDIO_CLEANUP_FILTER` (default: highpass=f=200,lowpass=f=3000,afftdn=nf=-25)
- `ENTITY_INDEXING_AUDIO_MUSIC_DETECTION_ENABLED` (default: true)
- `ENTITY_INDEXING_AUDIO_SPEECH_THRESHOLD` (default: 0.1)
- `ENTITY_INDEXING_AUDIO_VAD_MODE` (default: 2)
- `ENTITY_INDEXING_CONFIDENCE_MIN_SCORE` (default: 0.1)

---

## Outputs

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

Example mapping (in `backend/src/entity_indexing/processing.py`):
- `person` → military personnel
- `airplane` → aircraft
- `helicopter` → helicopter
- `truck` → armored vehicle

**Important:** Detection accuracy depends on video quality and model limitations. If you see false positives or missed objects, tune:
- `ENTITY_INDEXING_MIN_CONFIDENCE` (YOLO threshold)
- `ENTITY_INDEXING_DISCOVERY_MIN_SCORE` (caption confidence threshold)
- `ENTITY_INDEXING_DISCOVERY_EVERY_N` (discovery sampling rate)
- `ENTITY_INDEXING_OPEN_VOCAB_THRESHOLD` (CLIP threshold)
- `ENTITY_INDEXING_MIN_CONSECUTIVE` (filter short blips)
 
**Tip:** Discovery mode filters out generic phrases (e.g., “large”, “many”, “over”) and only keeps military‑centric terms when `ENTITY_INDEXING_DISCOVERY_ONLY_MILITARY=true`.

To audit detections, enable **detection overlays** in the frame gallery.

---

## Search Logic

- **Exact match**: matches entity names directly
- **Semantic match**: uses sentence-transformers + cosine similarity
- Filters: similarity threshold, min presence %, min frames

---

## API Endpoints (Summary)

```
POST   /api/videos
GET    /api/videos
GET    /api/videos/{id}
GET    /api/videos/{id}/status
GET    /api/videos/{id}/report
GET    /api/videos/{id}/frames
GET    /api/videos/{id}/download
GET    /api/videos/{id}/report/download
GET    /api/videos/{id}/report/csv/download
GET    /api/search
```

---

## Troubleshooting

**No transcript**
- Ensure the video has audio
- Ensure the worker is running
- Whisper model downloads on first run

**Search returns nothing**
- Only completed videos are searchable
- Lower filters (min presence / min frames)

**Slow processing**
- Use smaller videos
- Increase frame interval
- Use a GPU for YOLO

---

## Demo Strategy

Hosting background workers for free is unreliable. The recommended recruiter‑friendly demo is:

1) Run locally with Docker
2) Record a short Loom walkthrough
3) Share the video link in your CV/portfolio

---

## Tests

```bash
pytest -q
```

---

## License

Internal / academic usage.
