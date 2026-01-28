# API Reference — Thales Video Indexing

Base URL (Docker): `http://localhost:8010`

---

## Upload (file)

`POST /api/videos`

**multipart/form-data**:
- `video_file` (required)
- `voice_file` (optional)
- `interval_sec` (optional, default 5)

**Response**:
```json
{ "video_id": "uuid", "status": "processing" }
```

---

## Upload (URL)

`POST /api/videos/from-url`

**JSON**:
```json
{ "url": "https://...", "interval_sec": 5 }
```

---

## Upload (URL + cookies)

`POST /api/videos/from-url-upload`

**multipart/form-data**:
- `url` (required)
- `interval_sec` (optional)
- `cookies_file` (optional)

---

## Test URL

`POST /api/videos/from-url/check`

**multipart/form-data**:
- `url`
- `cookies_file` (optional)

**Response**:
```json
{ "ok": true, "title": "Video", "duration_sec": 120 }
```

---

## List videos

`GET /api/videos?status=&page=&page_size=`

**Response**:
```json
{
  "items": [{
    "video_id": "uuid",
    "filename": "file.mp4",
    "created_at": "2026-01-01T10:00:00",
    "status": "completed",
    "duration_sec": 120,
    "frames_analyzed": 24,
    "entities_found": 6,
    "interval_sec": 5
  }],
  "total": 1,
  "page": 1,
  "page_size": 20
}
```

---

## Video details

`GET /api/videos/{video_id}`

**Response**:
```json
{
  "video_id": "uuid",
  "filename": "file.mp4",
  "created_at": "2026-01-01T10:00:00",
  "status": "completed",
  "duration_sec": 120,
  "interval_sec": 5,
  "frames_analyzed": 24,
  "voice_file_included": false,
  "unique_entities": 6,
  "entities": [{"label": "aircraft", "count": 6, "presence": 0.25}],
  "report_ready": true
}
```

---

## Status (polling)

`GET /api/videos/{video_id}/status`

```json
{ "status": "processing", "progress": 42.5, "current_stage": "detecting_entities" }
```

---

## Report

`GET /api/videos/{video_id}/report`

**Response** (truncated):
```json
{
  "video_id": "uuid",
  "filename": "file.mp4",
  "duration_sec": 120,
  "interval_sec": 5,
  "frames_analyzed": 24,
  "unique_entities": 6,
  "entities": {
    "aircraft": {
      "count": 6,
      "presence": 0.25,
      "appearances": 6,
      "time_ranges": [{"start_sec": 0, "end_sec": 10, "start_label": "00:00", "end_label": "00:10"}],
      "confidence_score": 0.72
    }
  }
}
```

---

## Transcript

`GET /api/videos/{video_id}/transcript`

---

## Frames

`GET /api/videos/{video_id}/frames?page=&page_size=&annotated=&entity=`

`GET /api/videos/{video_id}/frames/{filename}`

`GET /api/videos/{video_id}/frames/nearest?timestamp_sec=&entity=`

---

## Downloads

- `GET /api/videos/{video_id}/download`
- `GET /api/videos/{video_id}/report/download` (JSON/PDF)
- `GET /api/videos/{video_id}/report/csv/download`

---

## Share

`POST /api/videos/{video_id}/share`

`GET /api/share/{token}`

---

## Search

`GET /api/search?q=&similarity=&min_presence=&min_frames=`

