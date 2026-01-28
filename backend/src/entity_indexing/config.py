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

OPEN_VOCAB_ENABLED = os.getenv("ENTITY_INDEXING_OPEN_VOCAB_ENABLED", "0").strip().lower() in {
    "1",
    "true",
    "yes",
    "on",
}
OPEN_VOCAB_MODEL = os.getenv("ENTITY_INDEXING_OPEN_VOCAB_MODEL", "openai/clip-vit-base-patch32")
OPEN_VOCAB_THRESHOLD = float(os.getenv("ENTITY_INDEXING_OPEN_VOCAB_THRESHOLD", "0.27"))
OPEN_VOCAB_EVERY_N = int(os.getenv("ENTITY_INDEXING_OPEN_VOCAB_EVERY_N", "1"))
OPEN_VOCAB_MIN_CONSECUTIVE = int(os.getenv("ENTITY_INDEXING_OPEN_VOCAB_MIN_CONSECUTIVE", "1"))

DISCOVERY_ENABLED = os.getenv("ENTITY_INDEXING_DISCOVERY_ENABLED", "1").strip().lower() in {
    "1",
    "true",
    "yes",
    "on",
}
DISCOVERY_MODEL = os.getenv(
    "ENTITY_INDEXING_DISCOVERY_MODEL", "Salesforce/blip-image-captioning-base"
)
DISCOVERY_EVERY_N = int(os.getenv("ENTITY_INDEXING_DISCOVERY_EVERY_N", "1"))
DISCOVERY_MIN_SCORE = float(os.getenv("ENTITY_INDEXING_DISCOVERY_MIN_SCORE", "0.2"))
DISCOVERY_MIN_CONSECUTIVE = int(os.getenv("ENTITY_INDEXING_DISCOVERY_MIN_CONSECUTIVE", "1"))
DISCOVERY_MAX_PHRASES = int(os.getenv("ENTITY_INDEXING_DISCOVERY_MAX_PHRASES", "8"))
DISCOVERY_ONLY_MILITARY = os.getenv("ENTITY_INDEXING_DISCOVERY_ONLY_MILITARY", "1").strip().lower() in {
    "1",
    "true",
    "yes",
    "on",
}
OPEN_VOCAB_LABELS = [
    label.strip()
    for label in os.getenv(
        "ENTITY_INDEXING_OPEN_VOCAB_LABELS",
        "aircraft carrier,fighter jet,satellite,drone,helicopter,aircraft,missile,rocket,tank,armored vehicle,artillery,military vehicle",
    ).split(",")
    if label.strip()
]

EMBEDDING_MODEL = os.getenv(
    "ENTITY_INDEXING_EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2"
)

DEFAULT_INTERVAL_SEC = int(os.getenv("ENTITY_INDEXING_DEFAULT_INTERVAL", "5"))

# Smart sampling (scene change / motion)
SMART_SAMPLING_ENABLED = os.getenv("ENTITY_INDEXING_SMART_SAMPLING_ENABLED", "1").strip().lower() in {
    "1",
    "true",
    "yes",
    "on",
}
SMART_SAMPLING_DIFF_THRESHOLD = float(
    os.getenv("ENTITY_INDEXING_SMART_SAMPLING_DIFF_THRESHOLD", "0.06")
)
SMART_SAMPLING_MIN_KEEP = int(os.getenv("ENTITY_INDEXING_SMART_SAMPLING_MIN_KEEP", "6"))

# Verification pass (CLIP re-check)
VERIFY_ENABLED = os.getenv("ENTITY_INDEXING_VERIFY_ENABLED", "1").strip().lower() in {
    "1",
    "true",
    "yes",
    "on",
}
VERIFY_MODEL = os.getenv("ENTITY_INDEXING_VERIFY_MODEL", "openai/clip-vit-base-patch32")
VERIFY_THRESHOLD = float(os.getenv("ENTITY_INDEXING_VERIFY_THRESHOLD", "0.27"))
VERIFY_EVERY_N = int(os.getenv("ENTITY_INDEXING_VERIFY_EVERY_N", "3"))
VERIFY_MAX_LABELS = int(os.getenv("ENTITY_INDEXING_VERIFY_MAX_LABELS", "12"))

# OCR
OCR_ENABLED = os.getenv("ENTITY_INDEXING_OCR_ENABLED", "1").strip().lower() in {
    "1",
    "true",
    "yes",
    "on",
}
OCR_EVERY_N = int(os.getenv("ENTITY_INDEXING_OCR_EVERY_N", "4"))
OCR_MIN_CONFIDENCE = int(os.getenv("ENTITY_INDEXING_OCR_MIN_CONFIDENCE", "60"))

# Audio cleanup + speech detection
AUDIO_CLEANUP_ENABLED = os.getenv("ENTITY_INDEXING_AUDIO_CLEANUP_ENABLED", "1").strip().lower() in {
    "1",
    "true",
    "yes",
    "on",
}
AUDIO_CLEANUP_FILTER = os.getenv(
    "ENTITY_INDEXING_AUDIO_CLEANUP_FILTER", "highpass=f=200,lowpass=f=3000,afftdn=nf=-25"
)
AUDIO_MUSIC_DETECTION_ENABLED = os.getenv(
    "ENTITY_INDEXING_AUDIO_MUSIC_DETECTION_ENABLED", "1"
).strip().lower() in {"1", "true", "yes", "on"}
AUDIO_SPEECH_THRESHOLD = float(os.getenv("ENTITY_INDEXING_AUDIO_SPEECH_THRESHOLD", "0.1"))
AUDIO_VAD_MODE = int(os.getenv("ENTITY_INDEXING_AUDIO_VAD_MODE", "2"))

# Confidence scoring
CONFIDENCE_MIN_SCORE = float(os.getenv("ENTITY_INDEXING_CONFIDENCE_MIN_SCORE", "0.1"))

FRAMES_DIR = DATA_DIR / "frames"
VIDEOS_DIR = DATA_DIR / "videos"
REPORTS_DIR = DATA_DIR / "reports"
INDEX_DIR = DATA_DIR / "index"



def ensure_dirs() -> None:
    for path in [DATA_DIR, FRAMES_DIR, VIDEOS_DIR, REPORTS_DIR, INDEX_DIR]:
        path.mkdir(parents=True, exist_ok=True)
