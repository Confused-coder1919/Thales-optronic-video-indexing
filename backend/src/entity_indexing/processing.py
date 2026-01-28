from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import cv2

from .config import (
    YOLO_WEIGHTS,
    MIN_CONFIDENCE,
    MIN_CONSECUTIVE,
    ANNOTATE_FRAMES,
    OPEN_VOCAB_MIN_CONSECUTIVE,
    DISCOVERY_MIN_CONSECUTIVE,
    SMART_SAMPLING_DIFF_THRESHOLD,
    SMART_SAMPLING_MIN_KEEP,
    CONFIDENCE_MIN_SCORE,
)

LABEL_MAP = {
    # Personnel
    "person": "military personnel",
    # Vehicles (best-effort mapping from COCO)
    "car": "military vehicle",
    "truck": "armored vehicle",
    "bus": "military vehicle",
    "motorcycle": "military vehicle",
    "bicycle": "military vehicle",
    "train": "military vehicle",
    "boat": "military vehicle",
    # Aircraft
    "airplane": "aircraft",
    "helicopter": "helicopter",
    # Weapons (approximate via COCO sports/utility classes)
    "knife": "weapon",
    "scissors": "weapon",
    "baseball bat": "weapon",
    # Equipment (approximate)
    "backpack": "equipment",
    "handbag": "equipment",
    "suitcase": "equipment",
    "laptop": "equipment",
    "cell phone": "equipment",
    "remote": "equipment",
}

@dataclass
class FrameDetection:
    index: int
    timestamp_sec: float
    filename: str
    detections: List[Dict]
    annotated_filename: Optional[str] = None


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
            if confidence < MIN_CONFIDENCE:
                continue
            xyxy = box.xyxy[0].tolist()
            detections.append(
                {
                    "label": label,
                    "confidence": confidence,
                    "bbox": [round(v, 2) for v in xyxy],
                    "source": "yolo",
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


def filter_frames_by_scene(
    frame_files: List[Path],
    diff_threshold: float = SMART_SAMPLING_DIFF_THRESHOLD,
    min_keep: int = SMART_SAMPLING_MIN_KEEP,
) -> List[Path]:
    if len(frame_files) <= 1:
        return frame_files
    kept: List[Path] = []
    prev_gray = None
    for frame in frame_files:
        image = cv2.imread(str(frame))
        if image is None:
            continue
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        if prev_gray is None:
            kept.append(frame)
            prev_gray = gray
            continue
        diff = cv2.absdiff(prev_gray, gray)
        score = float(diff.mean()) / 255.0
        if score >= diff_threshold:
            kept.append(frame)
            prev_gray = gray
    if len(kept) < max(1, min_keep):
        return frame_files
    return kept

def _format_timestamp(seconds: float) -> str:
    total = int(round(seconds))
    minutes = total // 60
    secs = total % 60
    return f"{minutes:02d}:{secs:02d}"


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
        {
            "start_sec": float(s),
            "end_sec": float(e),
            "start_label": _format_timestamp(s),
            "end_label": _format_timestamp(e),
        }
        for s, e in ranges
    ]


def _filter_consecutive(indices: List[int], min_consecutive: int) -> List[int]:
    if not indices:
        return []
    indices = sorted(indices)
    kept: List[int] = []
    run = [indices[0]]
    last = indices[0]
    for idx in indices[1:]:
        if idx == last + 1:
            run.append(idx)
        else:
            if len(run) >= min_consecutive:
                kept.extend(run)
            run = [idx]
        last = idx
    if len(run) >= min_consecutive:
        kept.extend(run)
    return kept

def annotate_frame(frame_path: Path, detections: List[Dict], output_path: Path) -> None:
    if not detections:
        output_path.write_bytes(frame_path.read_bytes())
        return
    image = cv2.imread(str(frame_path))
    if image is None:
        return
    overlay_labels = []
    for det in detections:
        bbox = det.get("bbox", [])
        label = det.get("label", "object")
        conf = det.get("confidence", 0.0)
        text = f"{label} {conf:.2f}"
        if len(bbox) == 4:
            x1, y1, x2, y2 = [int(float(v)) for v in bbox]
            cv2.rectangle(image, (x1, y1), (x2, y2), (0, 134, 195), 2)
            cv2.putText(
                image,
                text,
                (x1, max(10, y1 - 6)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (0, 134, 195),
                1,
                cv2.LINE_AA,
            )
        else:
            overlay_labels.append(text)
    if overlay_labels:
        y = 18
        for label in overlay_labels[:6]:
            cv2.putText(
                image,
                label,
                (8, y),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (0, 134, 195),
                1,
                cv2.LINE_AA,
            )
            y += 16
    output_path.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(output_path), image)


def aggregate_detections(
    frame_detections: List[FrameDetection],
    duration_sec: float,
    interval_sec: int,
) -> Dict:
    total_frames = len(frame_detections)
    entity_indices_by_source: Dict[str, Dict[str, List[int]]] = {}
    for frame in frame_detections:
        present_labels: Dict[str, set] = {}
        for det in frame.detections:
            label = det.get("label")
            if not label:
                continue
            source = det.get("source", "yolo")
            present_labels.setdefault(label, set()).add(source)
        for label, sources in present_labels.items():
            label_sources = entity_indices_by_source.setdefault(label, {})
            for source in sources:
                label_sources.setdefault(source, []).append(frame.index)

    source_weights = {
        "yolo": 0.6,
        "verify": 0.7,
        "clip": 0.55,
        "discovery": 0.4,
        "ocr": 0.8,
    }
    entities: Dict[str, Dict] = {}
    for label, sources in entity_indices_by_source.items():
        raw_indices: List[int] = []
        kept_set: set[int] = set()
        for source, indices in sources.items():
            raw_indices.extend(indices)
            if source == "clip":
                min_consecutive = OPEN_VOCAB_MIN_CONSECUTIVE
            elif source == "discovery":
                min_consecutive = DISCOVERY_MIN_CONSECUTIVE
            else:
                min_consecutive = MIN_CONSECUTIVE
            kept_set.update(_filter_consecutive(indices, min_consecutive))

        kept_indices = sorted(kept_set)
        if not kept_indices:
            continue
        times = [frame_detections[i].timestamp_sec for i in kept_indices]
        count = len(times)
        presence = count / total_frames if total_frames else 0.0
        time_ranges = merge_time_ranges(times, interval_sec)
        source_score = 0.0
        for source in sources.keys():
            source_score = max(source_score, source_weights.get(source, 0.3))
        ocr_boost = 0.1 if "ocr" in sources else 0.0
        confidence_score = min(1.0, presence * 0.7 + source_score * 0.2 + ocr_boost)

        if confidence_score < CONFIDENCE_MIN_SCORE:
            continue

        entities[label] = {
            "count": count,
            "presence": round(presence, 4),
            "appearances": count,
            "time_ranges": time_ranges,
            "raw_count": len(set(raw_indices)),
            "confidence_score": round(confidence_score, 4),
            "sources": sorted(sources.keys()),
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
                "frame_index": frame.index,
                "timestamp_sec": frame.timestamp_sec,
                "filename": frame.filename,
                "annotated_filename": frame.annotated_filename,
                "detections": frame.detections,
            }
            for frame in frame_detections
        ]
    }
