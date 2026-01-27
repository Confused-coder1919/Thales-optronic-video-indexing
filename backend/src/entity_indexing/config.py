from __future__ import annotations

import os
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[3]

DATA_DIR = Path(
    os.getenv("ENTITY_INDEXING_DATA_DIR", ROOT_DIR / "data" / "entity_indexing")
).resolve()

DB_PATH = Path(os.getenv("ENTITY_INDEXING_DB", DATA_DIR / "index.db"))

DATABASE_URL = os.getenv("ENTITY_INDEXING_DATABASE_URL", f"sqlite:///{DB_PATH}")

REDIS_URL = os.getenv("ENTITY_INDEXING_REDIS_URL", "redis://localhost:6379/0")

YOLO_WEIGHTS = os.getenv("ENTITY_INDEXING_YOLO_WEIGHTS", "yolov8n.pt")
MIN_CONFIDENCE = float(os.getenv("ENTITY_INDEXING_MIN_CONFIDENCE", "0.25"))
MIN_CONSECUTIVE = int(os.getenv("ENTITY_INDEXING_MIN_CONSECUTIVE", "2"))
ANNOTATE_FRAMES = os.getenv("ENTITY_INDEXING_ANNOTATE_FRAMES", "1").strip().lower() in {
    "1",
    "true",
    "yes",
    "on",
}

EMBEDDING_MODEL = os.getenv(
    "ENTITY_INDEXING_EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2"
)

DEFAULT_INTERVAL_SEC = int(os.getenv("ENTITY_INDEXING_DEFAULT_INTERVAL", "5"))

FRAMES_DIR = DATA_DIR / "frames"
VIDEOS_DIR = DATA_DIR / "videos"
REPORTS_DIR = DATA_DIR / "reports"
INDEX_DIR = DATA_DIR / "index"

DEMO_VIDEO_URL = os.getenv("ENTITY_INDEXING_DEMO_VIDEO_URL", "").strip()
DEMO_VIDEO_PATH = os.getenv("ENTITY_INDEXING_DEMO_VIDEO_PATH", "").strip()
AUTO_SEED_DEMO = os.getenv("ENTITY_INDEXING_AUTO_DEMO", "0").strip().lower() in {
    "1",
    "true",
    "yes",
    "on",
}


def ensure_dirs() -> None:
    for path in [DATA_DIR, FRAMES_DIR, VIDEOS_DIR, REPORTS_DIR, INDEX_DIR]:
        path.mkdir(parents=True, exist_ok=True)
