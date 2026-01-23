from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import cv2

from .config import YOLO_WEIGHTS

LABEL_MAP = {
    "person": "military personnel",
    "car": "military vehicle",
    "truck": "military vehicle",
    "bus": "military vehicle",
    "motorcycle": "military vehicle",
    "train": "military vehicle",
    "airplane": "aircraft",
    "boat": "military vehicle",
}

@dataclass
class FrameDetection:
    index: int
    timestamp_sec: float
    filename: str
    detections: List[Dict]


class Detector:
    def __init__(self, weights: str = YOLO_WEIGHTS):
        self.weights = weights
        self.model = None

    def _ensure_model(self):
        if self.model is None:
            try:
                from ultralytics import YOLO
            except Exception as exc:  # pragma: no cover - heavy dependency
                raise RuntimeError(
                    "ultralytics is required for object detection"
                ) from exc
            self.model = YOLO(self.weights)

    def detect(self, frame_path: Path) -> List[Dict]:
        self._ensure_model()
        results = self.model(str(frame_path), verbose=False)
        if not results:
            return []
        result = results[0]
        detections: List[Dict] = []
        names = result.names
        for box in result.boxes:
            cls_id = int(box.cls[0])
            name = names.get(cls_id, str(cls_id)).lower()
            label = LABEL_MAP.get(name)
            if label is None:
                continue
            confidence = float(box.conf[0])
            xyxy = box.xyxy[0].tolist()
            detections.append(
                {
                    "label": label,
                    "confidence": confidence,
                    "bbox": [round(v, 2) for v in xyxy],
                }
            )
        return detections


def extract_duration(video_path: Path) -> float:
    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        raise RuntimeError(f"Unable to open video: {video_path}")
    fps = cap.get(cv2.CAP_PROP_FPS) or 0
    frame_count = cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0
    cap.release()
    if fps <= 0:
        return 0.0
    return float(frame_count / fps)


def extract_frames_ffmpeg(video_path: Path, frames_dir: Path, interval_sec: int) -> List[Path]:
    frames_dir.mkdir(parents=True, exist_ok=True)
    output_pattern = frames_dir / "frame_%06d.jpg"
    cmd = [
        "ffmpeg",
        "-i",
        str(video_path),
        "-vf",
        f"fps=1/{interval_sec}",
        "-q:v",
        "2",
        str(output_pattern),
    ]
    subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return sorted(frames_dir.glob("frame_*.jpg"))


def extract_frames_opencv(video_path: Path, frames_dir: Path, interval_sec: int) -> List[Path]:
    frames_dir.mkdir(parents=True, exist_ok=True)
    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        raise RuntimeError(f"Unable to open video: {video_path}")
    fps = cap.get(cv2.CAP_PROP_FPS)
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    frames: List[Path] = []
    if fps <= 0:
        fps = 25
    interval_frames = max(1, int(fps * interval_sec))
    index = 0
    frame_idx = 0
    while frame_idx < frame_count:
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
        success, frame = cap.read()
        if not success:
            break
        filename = frames_dir / f"frame_{index:06d}.jpg"
        cv2.imwrite(str(filename), frame)
        frames.append(filename)
        index += 1
        frame_idx += interval_frames
    cap.release()
    return frames


def merge_time_ranges(timestamps: List[float], interval_sec: int) -> List[Dict]:
    if not timestamps:
        return []
    timestamps = sorted(timestamps)
    ranges: List[Tuple[float, float]] = []
    start = timestamps[0]
    end = timestamps[0]
    for ts in timestamps[1:]:
        if ts - end <= interval_sec + 1e-6:
            end = ts
        else:
            ranges.append((start, end))
            start = ts
            end = ts
    ranges.append((start, end))
    return [
        {"start_sec": float(s), "end_sec": float(e)}
        for s, e in ranges
    ]


def aggregate_detections(
    frame_detections: List[FrameDetection],
    duration_sec: float,
    interval_sec: int,
) -> Dict:
    total_frames = len(frame_detections)
    entity_frames: Dict[str, List[float]] = {}
    entity_conf: Dict[str, List[float]] = {}

    for frame in frame_detections:
        present_labels = set()
        for det in frame.detections:
            label = det["label"]
            present_labels.add(label)
            entity_conf.setdefault(label, []).append(det.get("confidence", 0.0))
        for label in present_labels:
            entity_frames.setdefault(label, []).append(frame.timestamp_sec)

    entities: Dict[str, Dict] = {}
    for label, times in entity_frames.items():
        count = len(times)
        presence = count / total_frames if total_frames else 0.0
        time_ranges = merge_time_ranges(times, interval_sec)
        avg_conf = (
            sum(entity_conf.get(label, [])) / len(entity_conf.get(label, []))
            if entity_conf.get(label)
            else 0.0
        )
        entities[label] = {
            "count": count,
            "presence": round(presence, 4),
            "avg_confidence": round(avg_conf, 4),
            "time_ranges": time_ranges,
        }

    report = {
        "duration_sec": round(duration_sec, 2),
        "interval_sec": interval_sec,
        "frames_analyzed": total_frames,
        "unique_entities": len(entities),
        "entities": entities,
    }
    return report


def build_frames_index(frame_detections: List[FrameDetection]) -> Dict:
    return {
        "frames": [
            {
                "index": frame.index,
                "timestamp_sec": frame.timestamp_sec,
                "filename": frame.filename,
                "detections": frame.detections,
            }
            for frame in frame_detections
        ]
    }
