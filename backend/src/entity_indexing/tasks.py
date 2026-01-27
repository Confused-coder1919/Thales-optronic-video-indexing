from __future__ import annotations

import json
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
    annotate_frame,
    aggregate_detections,
    build_frames_index,
    extract_duration,
    extract_frames_ffmpeg,
    extract_frames_opencv,
)
from .config import ANNOTATE_FRAMES
from .storage import (
    frames_dir,
    report_path,
    frames_index_path,
    transcript_path,
    report_csv_path,
)
from .report_csv import generate_csv
from .transcription import transcribe_audio
from backend.src.utils.extract_audio import extract_audio_from_video


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
            progress=5.0,
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
            progress=10.0,
            current_stage="transcribing_audio",
        )

        transcript_payload = {"language": "unknown", "segments": [], "text": ""}
        try:
            audio_path = extract_audio_from_video(
                video_path, str(Path(video_path).with_suffix(".m4a"))
            )
            audio_file = Path(audio_path)
            if not audio_file.exists() or audio_file.stat().st_size == 0:
                raise RuntimeError("No audio track found for this video.")
            transcript_payload = transcribe_audio(audio_file)
        except Exception as exc:
            transcript_payload["error"] = str(exc)

        transcript_path(video_id).write_text(
            json.dumps(transcript_payload, indent=2), encoding="utf-8"
        )

        update_video(
            session,
            video_id,
            progress=20.0,
            current_stage="detecting_entities",
            frames_analyzed=total_frames,
            duration_sec=duration,
        )

        detector = Detector()
        frame_detections: List[FrameDetection] = []
        annotated_dir = frames_path / "annotated"
        for idx, frame_file in enumerate(frame_files):
            timestamp = idx * interval_sec
            detections = detector.detect(frame_file)
            annotated_name = None
            if ANNOTATE_FRAMES:
                annotated_name = f"annotated/{frame_file.name}"
                annotate_frame(frame_file, detections, frames_path / annotated_name)
            frame_detections.append(
                FrameDetection(
                    index=idx,
                    timestamp_sec=timestamp,
                    filename=frame_file.name,
                    detections=detections,
                    annotated_filename=annotated_name,
                )
            )
            progress = 20.0 + 60.0 * (idx + 1) / total_frames
            if (idx + 1) % 5 == 0 or idx + 1 == total_frames:
                update_video(
                    session,
                    video_id,
                    progress=round(progress, 2),
                    current_stage="detecting_entities",
                )

        update_video(session, video_id, progress=80.0, current_stage="aggregating_report")

        report = aggregate_detections(
            frame_detections,
            duration_sec=duration,
            interval_sec=interval_sec,
        )
        report["video_id"] = video_id
        report["filename"] = Path(video_path).name

        report_path(video_id).write_text(json.dumps(report, indent=2), encoding="utf-8")
        frames_index_path(video_id).write_text(
            json.dumps(build_frames_index(frame_detections), indent=2),
            encoding="utf-8",
        )
        generate_csv(report, report_csv_path(video_id))

        update_video(
            session,
            video_id,
            progress=95.0,
            current_stage="indexing_search",
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
            progress=100.0,
            current_stage="completed",
        )
    except Exception as exc:
        trace = traceback.format_exc()
        update_video(
            session,
            video_id,
            status="failed",
            error=f"{exc}\n{trace}",
            progress=100.0,
            current_stage="failed",
        )
    finally:
        session.close()
