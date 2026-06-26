from __future__ import annotations

import shutil
from pathlib import Path
from typing import TYPE_CHECKING, Callable, Iterable, List, Sequence

from .config import FRAMES_DIR, REPORTS_DIR

if TYPE_CHECKING:
    from sqlalchemy.orm import Session
    from .models import Video


VALID_REPROCESS_STATUSES = {"queued", "processing", "completed", "failed"}


def parse_statuses(raw_statuses: str) -> List[str]:
    statuses = [item.strip().lower() for item in raw_statuses.split(",") if item.strip()]
    if not statuses:
        return ["completed", "failed"]
    if "all" in statuses:
        return sorted(VALID_REPROCESS_STATUSES)
    invalid = [status for status in statuses if status not in VALID_REPROCESS_STATUSES]
    if invalid:
        raise ValueError(f"Unsupported statuses: {', '.join(sorted(invalid))}")
    return statuses


def select_videos_for_reprocess(
    session: "Session",
    statuses: Sequence[str],
    video_ids: Sequence[str] | None = None,
    limit: int | None = None,
) -> List["Video"]:
    from sqlalchemy import select

    from .models import Video

    stmt = select(Video).order_by(Video.created_at.asc())
    if statuses:
        stmt = stmt.where(Video.status.in_(list(statuses)))
    if video_ids:
        stmt = stmt.where(Video.id.in_(list(video_ids)))
    if limit is not None:
        stmt = stmt.limit(limit)
    return list(session.execute(stmt).scalars().all())


def clear_video_outputs(video_id: str) -> None:
    for path in (FRAMES_DIR / video_id, REPORTS_DIR / video_id):
        if path.exists():
            shutil.rmtree(path, ignore_errors=True)


def reset_video_for_reprocess(video, interval_sec: int | None = None) -> None:
    video.status = "queued"
    video.progress = 0.0
    video.current_stage = "queued"
    video.duration_sec = None
    video.frames_analyzed = None
    video.unique_entities = None
    video.entities_json = None
    video.report_path = None
    video.frames_path = None
    video.error = None
    if interval_sec is not None:
        video.interval_sec = interval_sec


def reset_label_index() -> Path:
    from .embeddings import index_path

    path = index_path()
    path.unlink(missing_ok=True)
    return path


def enqueue_reprocess_tasks(
    session,
    videos: Iterable,
    send_task: Callable[[str, list], object],
    interval_sec: int | None = None,
    clear_outputs: bool = True,
) -> List[dict]:
    queued: List[dict] = []
    materialized = list(videos)

    for video in materialized:
        if not video.original_path:
            raise RuntimeError(f"Video {video.id} has no original_path and cannot be reprocessed.")
        if not Path(video.original_path).exists():
            raise FileNotFoundError(
                f"Original video file missing for {video.id}: {video.original_path}"
            )
        if clear_outputs:
            clear_video_outputs(video.id)
        reset_video_for_reprocess(video, interval_sec=interval_sec)
        session.add(video)
        queued.append(
            {
                "video_id": video.id,
                "filename": video.filename,
                "interval_sec": video.interval_sec,
                "original_path": video.original_path,
            }
        )

    session.commit()

    for item in queued:
        send_task(
            "entity_indexing.process_video",
            [item["video_id"], item["original_path"], item["interval_sec"]],
        )

    return queued
