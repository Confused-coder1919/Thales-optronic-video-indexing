from __future__ import annotations

import json
import math
import traceback
from pathlib import Path
from typing import List

from .celery_app import celery_app

from .config import DEFAULT_INTERVAL_SEC, ensure_dirs
from .db import SessionLocal
from .embeddings import EmbeddingProvider, update_label_index
from .models import Video
from .processing import (
    Detector,
    FrameDetection,
    aggregate_detections,
    build_frames_index,
    extract_duration,
    extract_frames_ffmpeg,
    extract_frames_opencv,
)
from .storage import frames_dir, report_path, frames_index_path


def update_video(
    session, video_id: str, **fields
):
    video = session.get(Video, video_id)
    if not video:
        return
    for key, value in fields.items():
        setattr(video, key, value)
    session.add(video)
    session.commit()


@celery_app.task(name="entity_indexing.process_video")
def process_video_task(video_id: str, video_path: str, interval_sec: int) -> None:
    ensure_dirs()
    provider = EmbeddingProvider()
    session = SessionLocal()
    try:
        update_video(
            session,
            video_id,
            status="processing",
            progress=0.05,
            current_stage="extracting_frames",
        )
        duration = extract_duration(Path(video_path))
        frames_path = frames_dir(video_id)
        try:
            frame_files = extract_frames_ffmpeg(Path(video_path), frames_path, interval_sec)
        except Exception:
            frame_files = extract_frames_opencv(Path(video_path), frames_path, interval_sec)
        total_frames = len(frame_files)
        if total_frames == 0:
            raise RuntimeError("No frames extracted")

        update_video(
            session,
            video_id,
            progress=0.2,
            current_stage="detecting",
            frames_analyzed=total_frames,
            duration_sec=duration,
        )

        detector = Detector()
        frame_detections: List[FrameDetection] = []
        for idx, frame_file in enumerate(frame_files):
            timestamp = idx * interval_sec
            detections = detector.detect(frame_file)
            frame_detections.append(
                FrameDetection(
                    index=idx,
                    timestamp_sec=timestamp,
                    filename=frame_file.name,
                    detections=detections,
                )
            )
            progress = 0.2 + 0.6 * (idx + 1) / total_frames
            if (idx + 1) % 5 == 0 or idx + 1 == total_frames:
                update_video(
                    session,
                    video_id,
                    progress=round(progress, 4),
                    current_stage="detecting",
                )

        update_video(session, video_id, progress=0.85, current_stage="aggregating")

        report = aggregate_detections(
            frame_detections,
            duration_sec=duration,
            interval_sec=interval_sec,
        )

        report_path(video_id).write_text(json.dumps(report, indent=2), encoding="utf-8")
        frames_index_path(video_id).write_text(
            json.dumps(build_frames_index(frame_detections), indent=2),
            encoding="utf-8",
        )

        update_video(
            session,
            video_id,
            progress=0.92,
            current_stage="indexing",
            unique_entities=report.get("unique_entities"),
            entities_json=json.dumps(report.get("entities", {})),
            report_path=str(report_path(video_id)),
            frames_path=str(frames_path),
        )

        update_label_index(list(report.get("entities", {}).keys()), provider)

        update_video(
            session,
            video_id,
            status="completed",
            progress=1.0,
            current_stage="completed",
        )
    except Exception as exc:
        trace = traceback.format_exc()
        update_video(
            session,
            video_id,
            status="failed",
            error=f"{exc}\n{trace}",
            progress=1.0,
            current_stage="failed",
        )
    finally:
        session.close()
