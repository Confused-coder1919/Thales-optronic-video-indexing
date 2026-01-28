# 🎬 Thales Video Indexing — Implementation Summary (Updated)

## ✅ What Was Built

A **full‑stack video intelligence system** with a pixel‑faithful React UI, FastAPI backend, and Celery worker pipeline. It extracts frames, detects military‑relevant entities, generates reports, and enables cross‑video search with semantic similarity. It also supports **URL uploads**, **OCR**, **audio cleanup**, **confidence scoring**, and **shareable public reports**.

---

## 🏗️ System Architecture

### Frontend (React + TypeScript + Vite + Tailwind)

**Pages**
- Home (`/`) — stats + entry actions
- Videos Library (`/videos`) — filterable list with status pills
- Upload (`/upload`) — file upload + URL upload + cookies support
- Video Details (`/videos/:id`) — progress, analysis report, timeline, frames, transcript
- Unified Search (`/search`) — exact + semantic search with filters
- Share Report (`/share/:token`) — public read‑only report

**UX Highlights**
- Status polling every 1500ms while processing
- Clickable timeline → jumps video preview + frame gallery
- Frame gallery pagination (12 per page) + entity filter
- Share link generation with copy feedback

### Backend (FastAPI)

**Core endpoints**
```
POST   /api/videos                         - Upload video (multipart)
POST   /api/videos/from-url                - Upload via URL (JSON)
POST   /api/videos/from-url-upload         - Upload via URL + cookies (multipart)
POST   /api/videos/from-url/check          - Test URL before download (multipart)
GET    /api/videos                         - List videos (filterable, paginated)
GET    /api/videos/{id}                    - Video details
GET    /api/videos/{id}/status             - Processing status
GET    /api/videos/{id}/report             - Report JSON
GET    /api/videos/{id}/transcript         - Transcript JSON
GET    /api/videos/{id}/frames             - Paginated frames
GET    /api/videos/{id}/frames/nearest     - Nearest frame to timestamp
GET    /api/videos/{id}/frames/{name}      - Frame image
GET    /api/videos/{id}/download           - Download original video
GET    /api/videos/{id}/report/download    - Download report (JSON/PDF)
GET    /api/videos/{id}/report/csv/download - Download CSV
POST   /api/videos/{id}/share              - Create share link
GET    /api/share/{token}                  - Public report JSON
DELETE /api/videos/{id}                    - Delete
GET    /api/search                         - Search
GET    /health                             - Health check
```

### Worker (Celery + Redis)

Handles heavy processing asynchronously:
- frame extraction
- YOLO detection
- discovery + open‑vocab labels
- OCR extraction
- report aggregation
- transcript + audio analysis

---

## 🧠 Pipeline Highlights

- **Frame extraction** (ffmpeg → OpenCV fallback)
- **YOLOv8 detection** + military label mapping
- **Discovery mode** (caption‑based entity extraction)
- **Open‑vocabulary detection** (CLIP)
- **OCR extraction** (tail numbers, markings, ship names)
- **Audio cleanup + speech detection** for better transcripts
- **Confidence scoring** (multi‑source weighted scoring)

---

## 📁 Runtime Data Layout

```
data/entity_indexing/
├── index.db                       # SQLite metadata
├── videos/<id>/                   # original videos
├── frames/<id>/                   # raw + annotated frames
├── reports/<id>/report.json
├── reports/<id>/report.pdf
├── reports/<id>/report.csv
├── reports/<id>/transcript.json
```

---

## ✅ Key Improvements Added

- URL upload + cookies file support
- URL test endpoint before download
- Shareable public report page
- Timeline‑to‑frame/video seek
- OCR + audio cleanup
- Confidence scoring per entity
- CSV export with detailed entity stats

---

## 🧩 Tech Stack

- **Backend**: FastAPI, SQLAlchemy, SQLite
- **Worker**: Celery + Redis
- **Vision**: YOLOv8, CLIP
- **Text**: Whisper (faster‑whisper), Tesseract OCR
- **Search**: Sentence‑Transformers
- **Frontend**: React + Vite + Tailwind
- **Infra**: Docker Compose

