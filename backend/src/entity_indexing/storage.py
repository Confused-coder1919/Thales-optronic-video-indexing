from __future__ import annotations

from pathlib import Path

from .config import FRAMES_DIR, VIDEOS_DIR, REPORTS_DIR


def video_dir(video_id: str) -> Path:
    path = VIDEOS_DIR / video_id
    path.mkdir(parents=True, exist_ok=True)
    return path


def frames_dir(video_id: str) -> Path:
    path = FRAMES_DIR / video_id
    path.mkdir(parents=True, exist_ok=True)
    return path


def reports_dir(video_id: str) -> Path:
    path = REPORTS_DIR / video_id
    path.mkdir(parents=True, exist_ok=True)
    return path


def report_path(video_id: str) -> Path:
    return reports_dir(video_id) / "report.json"


def report_pdf_path(video_id: str) -> Path:
    return reports_dir(video_id) / "report.pdf"

def report_csv_path(video_id: str) -> Path:
    return reports_dir(video_id) / "report.csv"


def frames_index_path(video_id: str) -> Path:
    return frames_dir(video_id) / "frames.json"


def transcript_path(video_id: str) -> Path:
    return reports_dir(video_id) / "transcript.json"
