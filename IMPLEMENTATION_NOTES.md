# Implementation Notes: Thales Video Indexing System

## Summary

This document describes the rebuilt video indexing system with a modern React web interface and FastAPI backend.

## Architecture

### Frontend (React + TypeScript + Vite)

- **Pages**: Home, Videos Library, Upload, Video Details, Unified Entity Search
- **Styling**: Tailwind CSS with custom component classes
- **State Management**: React hooks with API polling
- **Port**: 5173 (development) / configurable in production

**Key Features**:

- Real-time progress polling (1500ms interval) during video processing
- Paginated frame gallery (12 frames per page)
- Interactive search with similarity threshold and filter controls
- Responsive grid layouts for video cards and stats

### Backend (FastAPI)

- **Port**: 8010
- **Database**: SQLite (data/entity_indexing/index.db)
- **Processing**: AsyncIO-based background tasks (no Celery required for single-instance)
- **Storage**: Structured file layout under data/entity_indexing/

**API Endpoints**:

```
POST   /api/videos                      - Upload video
GET    /api/videos                      - List videos (filterable, paginated)
GET    /api/videos/{id}                 - Get video details
GET    /api/videos/{id}/status          - Get processing status (for polling)
GET    /api/videos/{id}/report          - Get full analysis report
GET    /api/videos/{id}/frames          - Get frames paginated
GET    /api/videos/{id}/frames/{name}   - Get frame image
GET    /api/videos/{id}/download        - Download original video
GET    /api/videos/{id}/report/download - Download report
DELETE /api/videos/{id}                 - Delete video and files
GET    /api/search                      - Search across videos
GET    /health                          - Health check
```

## Video Processing Pipeline

### 1. Upload Phase

- Video file saved to `data/entity_indexing/videos/{video_id}/`
- Optional voice file also stored
- Database record created with status=queued
- Background task triggered

### 2. Frame Extraction (0-20% progress)

- **Primary**: FFmpeg via `ffmpeg-python` (fastest)
- **Fallback**: OpenCV frame-by-frame extraction
- Frames saved as JPEG to `data/entity_indexing/frames/{video_id}/`
- Configurable interval (default 5 seconds)
- Total frames calculated and stored

### 3. Object Detection (20-80% progress)

- **Model**: YOLOv8 (nano by default, configurable)
- **Library**: ultralytics
- **Process**:
  - Each frame processed individually
  - YOLO detections (bounding box + confidence)
  - Label extraction (e.g., "person", "car")
- Progress updates sent to database every 5 frames

### 4. Entity Aggregation (80-95% progress)

- Count appearances: how many frames contain each entity
- Presence percentage: count / total_frames
- Time ranges: consecutive frame sequences grouped into time segments
- Report generated with:
  ```json
  {
    "video_id": "abc123",
    "filename": "video.mp4",
    "duration_sec": 120.5,
    "interval_sec": 5,
    "frames_analyzed": 25,
    "unique_entities": 3,
    "entities": {
      "person": {
        "count": 15,
        "presence": 0.6,
        "frames": [0, 5, 10, 15, ...]
      },
      ...
    }
  }
  ```

### 5. Search Indexing (95-100% progress)

- Entity names and metadata stored in database
- Report saved to `data/entity_indexing/reports/{video_id}/report.json`
- Frames index saved to `data/entity_indexing/frames/{video_id}/frames.json`
- Status updated to "completed"

### Error Handling

- Exceptions caught and logged to database
- Video status set to "failed" with error message
- User can view error details and retry

## Data Storage Layout

```
data/entity_indexing/
├── index.db                                    # SQLite database
├── videos/
│   ├── {video_id1}/
│   │   ├── video.mp4                         # Original video file
│   │   └── [optional_voice.txt]              # Optional voice description
│   └── {video_id2}/
│       └── ...
├── frames/
│   ├── {video_id1}/
│   │   ├── frame_00000.jpg                   # Frame at 0s
│   │   ├── frame_00001.jpg                   # Frame at 5s
│   │   ├── ...
│   │   └── frames.json                       # Index of all frames
│   └── {video_id2}/
│       └── ...
├── reports/
│   ├── {video_id1}/
│   │   ├── report.json                       # Analysis report
│   │   └── [report.pdf]                      # (Optional) PDF export
│   └── {video_id2}/
│       └── ...
└── index/
    └── labels.json                           # Searchable entity index
```

## Search Implementation

### Exact Matching

- Direct substring match on entity labels
- Case-insensitive comparison
- Fast query execution

### Semantic Matching

- Word overlap-based similarity (simple implementation)
- Can be upgraded to sentence-transformers for better accuracy
- Similarity threshold configurable in UI (0.5 - 1.0)

### Filters Applied to Results

- **Min Presence**: Exclude entities appearing in < X% of frames
- **Min Frames**: Exclude entities appearing in < N frames
- **Similarity**: Adjust threshold for semantic expansion

### Response Format

```json
{
  "exact_matches_count": 2,
  "ai_enhancements_count": 5,
  "total_unique_videos": 3,
  "similar_entities": [
    { "label": "vehicle", "similarity": 0.85 },
    { "label": "military_vehicle", "similarity": 0.92 }
  ],
  "results": [
    {
      "video_id": "abc123",
      "filename": "video.mp4",
      "status": "completed",
      "duration_sec": 120.5,
      "created_at": "2026-01-23T...",
      "matched_entities": [
        { "label": "person", "presence": 45.2, "frames": 12 }
      ]
    }
  ]
}
```

## Object Detection Label Mapping

YOLOv8 (COCO dataset) labels are mapped to domain-specific entity types:

| COCO Label | Domain Entity      | Type      |
| ---------- | ------------------ | --------- |
| person     | military personnel | person    |
| car        | military vehicle   | vehicle   |
| truck      | military vehicle   | vehicle   |
| bus        | military vehicle   | vehicle   |
| bicycle    | equipment          | transport |
| motorcycle | military vehicle   | transport |
| dog        | animal             | exclude   |
| ...        | ...                | ...       |

**Note**: Mapping is best-effort. Fine-tuning available if needed for specific domains.

## Database Schema

### Videos Table

```python
id: str (primary key, 8-char UUID)
filename: str
status: str (queued/processing/completed/failed)
progress: float (0-100)
current_stage: str (extracting_frames/detecting_entities/aggregating_report/indexing_search)
duration_sec: float
interval_sec: int (default 5)
frames_analyzed: int
unique_entities: int
entities_json: str (JSON-serialized dict of entities)
report_path: str (file path to report.json)
frames_path: str (directory path to frames)
original_path: str (file path to original video)
error: str (error message if failed)
created_at: datetime
updated_at: datetime
```

## Environment Configuration

Create `.env` file with:

```env
MISTRAL_API_KEY=your_key_here
ENTITY_INDEXING_DATA_DIR=./data/entity_indexing
ENTITY_INDEXING_DATABASE_URL=sqlite:///./data/entity_indexing/index.db
ENTITY_INDEXING_REDIS_URL=redis://localhost:6379/0
ENTITY_INDEXING_YOLO_WEIGHTS=yolov8n.pt
ENTITY_INDEXING_DEFAULT_INTERVAL=5
```

See `.env.example` for full reference.

## Running the System

### Option 1: Docker Compose (Recommended)

```bash
docker-compose up --build
# Frontend: http://localhost:5173
# Backend: http://localhost:8010
```

### Option 2: Local Development

```bash
# Terminal 1: Backend
source .venv/bin/activate
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8010 --reload

# Terminal 2: Frontend
cd frontend
npm install
npm run dev

# (Optional) Terminal 3: Celery Worker (for async tasks)
celery -A backend.src.entity_indexing.celery_app worker --loglevel=info
```

## Key Technologies

| Component              | Technology                | Purpose                              |
| ---------------------- | ------------------------- | ------------------------------------ |
| **Frame Extraction**   | FFmpeg / OpenCV           | Efficient video sampling             |
| **Object Detection**   | YOLOv8                    | Fast, accurate entity detection      |
| **API Framework**      | FastAPI                   | High-performance async HTTP          |
| **Frontend Framework** | React 18 + TypeScript     | Type-safe interactive UI             |
| **Styling**            | Tailwind CSS              | Utility-first CSS framework          |
| **Database**           | SQLite + SQLAlchemy       | Lightweight, zero-config persistence |
| **Task Queue**         | Celery + Redis (optional) | Distributed processing (future)      |
| **Embeddings**         | sentence-transformers     | Semantic search (optional upgrade)   |

## Performance Considerations

- **Frame Extraction**: ~100-200ms per frame (FFmpeg faster than OpenCV)
- **Object Detection**: ~50-100ms per frame with YOLOv8-nano on CPU
- **Total Time**: Video duration + (num_frames \* detection_time)
  - 2-minute video at 5s interval = 24 frames
  - Typical processing time: 2-3 minutes
  - With GPU: 30-60 seconds

## Security Notes

1. **API Keys**: Store `MISTRAL_API_KEY` in environment variables, never in code
2. **File Access**: All files isolated to `data/` directory
3. **Database**: SQLite adequate for single-instance; use PostgreSQL for production multi-instance
4. **CORS**: Currently allows all origins; restrict in production
5. **File Upload**: Validates file types; could add size limits

## Future Enhancements

1. **Semantic Search**: Integrate sentence-transformers for better similarity matching
2. **Multi-GPU Support**: Distribute detection across GPUs
3. **Custom Model**: Fine-tune YOLOv8 on domain-specific entity types
4. **PDF Reports**: Generate formatted PDF reports with charts
5. **Video Annotations**: Overlay detections on frames for visualization
6. **Batch Processing**: Queue multiple videos, prioritize processing
7. **WebSocket Updates**: Real-time progress via WebSocket instead of polling
8. **S3 Storage**: Store frames/reports in cloud object storage
9. **PostgreSQL**: Migrate from SQLite for production scale
10. **Authentication**: Add user accounts and access control

## Troubleshooting

### "No frames extracted"

- Check video codec support (FFmpeg may not support exotic codecs)
- Try reducing frame interval
- Verify video file is not corrupt

### "Object detection timeout"

- Reduce frame interval to skip frames
- Use smaller YOLOv8 model (nano vs small)
- Enable GPU acceleration

### "Database locked"

- SQLite limitation in concurrent environments
- Migrate to PostgreSQL if >5 concurrent uploads

### "CORS errors"

- Check `docker-compose.yml` service endpoints
- Ensure VITE_API_BASE environment variable is set correctly

## Testing

Frontend components are ready for unit testing with Jest/Vitest.
Backend endpoints tested via FastAPI's TestClient.

Example:

```python
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)
response = client.get("/api/videos")
assert response.status_code == 200
```

## Contributing

1. Frontend changes: update React components in `frontend/src/`
2. Backend changes: update FastAPI routes in `backend/main.py`
3. Database schema: modify `backend/src/entity_indexing/models.py`
4. Dependencies: update `requirements.txt` or `frontend/package.json`
5. Test and commit with clear messages

---

**Last Updated**: January 23, 2026
**Status**: Production Ready for Single-Instance Deployment
