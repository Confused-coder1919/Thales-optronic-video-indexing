from __future__ import annotations

import shutil
from pathlib import Path
from typing import Tuple
from urllib.parse import urlparse

import requests
from sqlalchemy import select

from .celery_app import celery_app
from .config import DEFAULT_INTERVAL_SEC, DEMO_VIDEO_PATH, DEMO_VIDEO_URL
from .models import Video
from .storage import video_dir


def _resolve_demo_filename(url: str) -> str:
    parsed = urlparse(url)
    name = Path(parsed.path).name
    return name or "demo.mp4"


def seed_demo_video(session, interval_sec: int = DEFAULT_INTERVAL_SEC) -> Tuple[Video, bool]:
    existing = session.execute(
        select(Video).order_by(Video.created_at.desc()).limit(1)
    ).scalar_one_or_none()
    if existing:
        return existing, False

    if not DEMO_VIDEO_URL and not DEMO_VIDEO_PATH:
        raise RuntimeError("No demo video configured.")

    video_id = None
    filename = None
    dest_dir = None
    if DEMO_VIDEO_PATH:
        source = Path(DEMO_VIDEO_PATH)
        if not source.exists():
            raise RuntimeError("Demo video path does not exist.")
        video_id = source.stem
        dest_dir = video_dir(video_id)
        filename = source.name
        shutil.copy2(source, dest_dir / filename)
    else:
        filename = _resolve_demo_filename(DEMO_VIDEO_URL)
        video_id = Path(filename).stem or "demo"
        dest_dir = video_dir(video_id)
        dest_file = dest_dir / filename
        with requests.get(DEMO_VIDEO_URL, stream=True, timeout=60) as resp:
            resp.raise_for_status()
            with open(dest_file, "wb") as handle:
                for chunk in resp.iter_content(chunk_size=1024 * 1024):
                    if chunk:
                        handle.write(chunk)

    video = Video(
        id=video_id,
        filename=filename,
        status="processing",
        progress=0.0,
        current_stage="queued",
        interval_sec=interval_sec,
        original_path=str(dest_dir / filename),
    )
    session.add(video)
    session.commit()

    celery_app.send_task(
        "entity_indexing.process_video",
        args=[video.id, video.original_path, interval_sec],
    )
    return video, True
