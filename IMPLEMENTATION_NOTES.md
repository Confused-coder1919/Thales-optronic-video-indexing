# Implementation Notes — Thales Video Indexing System (Updated)

## Summary

This system ingests video, extracts frames, detects military‑relevant entities, aggregates time ranges, and exposes results via a FastAPI + Celery backend and a React UI.

---

## Architecture

### Frontend (React + TypeScript + Vite)

- **Pages**: Home, Videos Library, Upload, Video Details, Unified Entity Search, Share Report
- **Styling**: Tailwind + custom component classes
- **Polling**: status updates every 1500ms during processing
- **UX**: clickable timeline → jumps video + highlights nearest frame

### Backend (FastAPI)

- **Port**: 8010 (Docker) / 8000 (local)
- **Database**: SQLite (`data/entity_indexing/index.db`)
- **Storage**: local filesystem under `data/entity_indexing/`
- **Public Share**: tokens stored in `share_links` table

### Worker (Celery + Redis)

- Processes jobs asynchronously
- Stages update the `Video` record with progress and status

---

## Video Processing Pipeline

### 1) Upload
- File upload or URL download (yt‑dlp)
- Optional cookies file supported
- Video record created with status=processing

### 2) Frame Extraction (0–20%)
- Primary: ffmpeg
- Fallback: OpenCV
- Frames saved to `frames/<video_id>/`

### 3) Entity Detection (20–80%)
- YOLOv8 detection
- Discovery mode (caption → entity extraction)
- Open‑vocab labels via CLIP (optional)
- OCR extraction for text signals

### 4) Aggregation (80–95%)
- Count detections per label
- Presence % = count / total frames
- Time ranges = merge consecutive detections
- Confidence score = weighted source + consistency + OCR

### 5) Indexing (95–100%)
- Store entities JSON in DB
- Persist report JSON + transcript
- Mark video as completed

---

## Data Layout

```
data/entity_indexing/
├── index.db
├── videos/<id>/video.mp4
├── frames/<id>/frame_000001.jpg
├── frames/<id>/annotated/frame_000001.jpg
├── frames/<id>/frames.json
├── reports/<id>/report.json
├── reports/<id>/report.pdf
├── reports/<id>/report.csv
├── reports/<id>/transcript.json
```

---

## Search Implementation

- **Exact match**: token substring on label
- **Semantic match**: sentence‑transformers embeddings
- **Filters**: min presence %, min frames, similarity threshold

---

## Notes on Accuracy

- YOLO uses COCO labels, mapped into military taxonomy
- Discovery mode filters generic phrases if `DISCOVERY_ONLY_MILITARY=true`
- Open‑vocab labels help identify items like *aircraft carrier* and *satellite*
- OCR adds concrete signals (tail numbers, ship names, markings)

---

## Shareable Reports

- `POST /api/videos/{id}/share` returns a token
- `GET /api/share/{token}` returns a public report payload
- UI route `/share/:token` renders a read‑only report page

---

## Dataset Exporter

The exporter builds training‑ready datasets directly from existing frames + detections:

- **COCO** annotations (`instances_train.json`, `instances_val.json`, `instances_test.json`)
- **YOLO** labels (`labels/{split}/*.txt`)
- **Train/val/test** splits **by video** (prevents leakage)
- **Taxonomy** files (`labels.txt`, `labels.json`)
- **Manifest** (`dataset_manifest.json`) for lineage/params

Script:

```
python3 scripts/export_training_dataset.py \
  --output data/entity_indexing/datasets/run_001 \
  --train 0.7 --val 0.2 --test 0.1 \
  --min-confidence 0.3 --sources yolo,clip
```
