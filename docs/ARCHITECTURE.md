# Architecture — Thales Video Indexing

## System Overview

This project is a full‑stack video intelligence platform:

```
              ┌────────────────────────────────────────┐
              │                Frontend                │
              │  React + Vite + Tailwind (UI/Reports)  │
              └────────────────────┬───────────────────┘
                                   │ HTTP
                                   ▼
              ┌────────────────────────────────────────┐
              │              Backend API               │
              │ FastAPI + SQLAlchemy + SQLite          │
              └────────────────────┬───────────────────┘
                                   │ Celery task
                                   ▼
              ┌────────────────────────────────────────┐
              │                Worker                  │
              │  Celery + Redis + ML pipeline          │
              └────────────────────┬───────────────────┘
                                   │
                                   ▼
              ┌────────────────────────────────────────┐
              │            Local File Storage          │
              │ frames / reports / transcripts / csv   │
              └────────────────────────────────────────┘
```

---

## Components

### 1) Frontend
- **Routes**: `/`, `/videos`, `/videos/:id`, `/upload`, `/search`, `/share/:token`
- **Core UX**: upload (file/URL), progress view, timeline, frame gallery, transcript, search
- **Share mode**: public read‑only report view

### 2) Backend API
- Stores video metadata in SQLite
- Exposes REST endpoints for upload, status, report, frames, search, sharing
- Serves frame images and report downloads

### 3) Worker Pipeline
- Heavy processing runs in Celery worker
- Updates `videos` table with progress + status
- Generates report.json / report.pdf / report.csv
- Emits transcripts + audio analysis

### 4) Storage
```
data/entity_indexing/
├── index.db
├── videos/<video_id>/video.mp4
├── frames/<video_id>/frame_*.jpg
├── frames/<video_id>/annotated/frame_*.jpg
├── frames/<video_id>/frames.json
├── reports/<video_id>/report.json
├── reports/<video_id>/report.pdf
├── reports/<video_id>/report.csv
├── reports/<video_id>/transcript.json
```

---

## Data Model (SQLite)

### Video
Tracks the full lifecycle:
- status, progress, current_stage
- duration, frames_analyzed
- unique_entities, entities_json
- file paths for video/frames/report

### ShareLink
Stores public share token → video_id mapping

---

## Pipeline Stages

1. **Upload** (file or URL)
2. **Frame extraction** (ffmpeg / OpenCV fallback)
3. **Detection** (YOLO + discovery + open‑vocab + OCR)
4. **Aggregation** (counts, presence, time ranges)
5. **Report generation** (JSON/PDF/CSV)
6. **Indexing** (semantic search embedding)

Progress updates:
```
extracting_frames   0–20%
transcribing_audio  20%
detecting_entities  20–80%
aggregating_report  80–95%
indexing_search     95–100%
```

---

## Search Flow

- Query parsed into tokens
- Exact match: substring against entity labels
- Semantic match: embeddings via sentence‑transformers
- Filters applied: min presence, min frames, similarity threshold

---

## Public Share Flow

1. User clicks **Share Report**
2. API generates share token
3. Public UI fetches `/api/share/{token}`
4. Renders full report without requiring access to original project

