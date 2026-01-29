from __future__ import annotations

import json
import random
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from PIL import Image

from backend.src.entity_indexing.config import DATA_DIR
from backend.src.entity_indexing.db import SessionLocal
from backend.src.entity_indexing.models import Video
from backend.src.entity_indexing.storage import frames_dir, frames_index_path


@dataclass
class FrameRecord:
    frame_index: int
    timestamp_sec: float
    filename: str
    annotated_filename: Optional[str]
    detections: List[Dict]


class DetectionAdapter:
    """Abstract adapter for retrieving frames + detections."""

    def list_videos(self) -> List[str]:
        raise NotImplementedError

    def load_frames(self, video_id: str) -> List[FrameRecord]:
        raise NotImplementedError


class FramesJsonAdapter(DetectionAdapter):
    def __init__(self, data_dir: Optional[Path] = None):
        self.data_dir = data_dir or DATA_DIR

    def list_videos(self) -> List[str]:
        frames_root = self.data_dir / "frames"
        if not frames_root.exists():
            return []
        video_ids = []
        for path in frames_root.iterdir():
            if path.is_dir() and (path / "frames.json").exists():
                video_ids.append(path.name)
        return sorted(video_ids)

    def load_frames(self, video_id: str) -> List[FrameRecord]:
        path = frames_index_path(video_id)
        if not path.exists():
            return []
        data = json.loads(path.read_text(encoding="utf-8"))
        records: List[FrameRecord] = []
        for frame in data.get("frames", []):
            records.append(
                FrameRecord(
                    frame_index=int(frame.get("frame_index", frame.get("index", 0))),
                    timestamp_sec=float(frame.get("timestamp_sec", 0.0)),
                    filename=str(frame.get("filename")),
                    annotated_filename=frame.get("annotated_filename"),
                    detections=list(frame.get("detections", [])),
                )
            )
        return records


class DatabaseAdapter(DetectionAdapter):
    """Placeholder adapter for future DB-based detections.

    Currently the DB stores aggregated entities only, so this adapter falls back
    to frames.json if present. This keeps the interface extensible without
    breaking the exporter.
    """

    def list_videos(self) -> List[str]:
        with SessionLocal() as session:
            rows = session.query(Video.id).all()
        return sorted([row[0] for row in rows])

    def load_frames(self, video_id: str) -> List[FrameRecord]:
        return FramesJsonAdapter().load_frames(video_id)


@dataclass
class ExportConfig:
    output_dir: Path
    splits: Tuple[float, float, float] = (0.7, 0.2, 0.1)
    seed: int = 42
    min_confidence: float = 0.0
    include_sources: Optional[List[str]] = None
    use_annotated: bool = False
    taxonomy: Optional[List[str]] = None


def _normalize_bbox_xyxy(
    bbox: List[float], width: int, height: int
) -> Optional[Tuple[float, float, float, float]]:
    if len(bbox) != 4:
        return None
    x1, y1, x2, y2 = [float(v) for v in bbox]
    x1 = max(0.0, min(x1, width))
    y1 = max(0.0, min(y1, height))
    x2 = max(0.0, min(x2, width))
    y2 = max(0.0, min(y2, height))
    w = max(0.0, x2 - x1)
    h = max(0.0, y2 - y1)
    if w <= 1e-3 or h <= 1e-3:
        return None
    return x1, y1, w, h


def split_videos(
    video_ids: List[str], splits: Tuple[float, float, float], seed: int
) -> Dict[str, List[str]]:
    rng = random.Random(seed)
    shuffled = video_ids[:]
    rng.shuffle(shuffled)
    total = len(shuffled)
    train_count = int(total * splits[0])
    val_count = int(total * splits[1])
    train = shuffled[:train_count]
    val = shuffled[train_count : train_count + val_count]
    test = shuffled[train_count + val_count :]
    return {"train": train, "val": val, "test": test}


def _ensure_dirs(output_dir: Path) -> Dict[str, Path]:
    paths = {
        "images": output_dir / "images",
        "labels": output_dir / "labels",
        "annotations": output_dir / "annotations",
    }
    for path in paths.values():
        path.mkdir(parents=True, exist_ok=True)
    for split in ["train", "val", "test"]:
        (paths["images"] / split).mkdir(parents=True, exist_ok=True)
        (paths["labels"] / split).mkdir(parents=True, exist_ok=True)
    return paths


def export_dataset(
    adapter: DetectionAdapter,
    config: ExportConfig,
    video_ids: Optional[List[str]] = None,
) -> Path:
    output_dir = config.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)
    paths = _ensure_dirs(output_dir)

    available_videos = video_ids or adapter.list_videos()
    if not available_videos:
        raise RuntimeError("No videos found with detections.")

    split_map = split_videos(available_videos, config.splits, config.seed)

    labels_set = set(config.taxonomy or [])
    coco = {"train": _empty_coco(), "val": _empty_coco(), "test": _empty_coco()}
    yolo_labels: Dict[Path, List[Tuple[str, float, float, float, float]]] = {}

    image_id = 1
    ann_id = 1

    for split, vids in split_map.items():
        for video_id in vids:
            frame_records = adapter.load_frames(video_id)
            if not frame_records:
                continue
            for frame in frame_records:
                detections = frame.detections or []
                if config.include_sources:
                    detections = [
                        det
                        for det in detections
                        if det.get("source") in config.include_sources
                    ]
                if config.min_confidence > 0:
                    detections = [
                        det
                        for det in detections
                        if float(det.get("confidence", 0.0)) >= config.min_confidence
                    ]

                usable = [det for det in detections if len(det.get("bbox", [])) == 4]
                if not usable:
                    continue

                src_name = frame.filename
                if config.use_annotated and frame.annotated_filename:
                    src_name = frame.annotated_filename
                src_path = frames_dir(video_id) / src_name
                if not src_path.exists():
                    continue

                image_name = f"{video_id}_{frame.filename}"
                dest_path = paths["images"] / split / image_name
                dest_path.write_bytes(src_path.read_bytes())

                with Image.open(dest_path) as img:
                    width, height = img.size

                coco[split]["images"].append(
                    {
                        "id": image_id,
                        "file_name": f"images/{split}/{image_name}",
                        "width": width,
                        "height": height,
                        "video_id": video_id,
                        "timestamp_sec": frame.timestamp_sec,
                    }
                )

                yolo_lines: List[Tuple[str, float, float, float, float]] = []
                for det in usable:
                    label = str(det.get("label", "")).strip()
                    if not label:
                        continue
                    labels_set.add(label)
                    bbox = _normalize_bbox_xyxy(det.get("bbox", []), width, height)
                    if not bbox:
                        continue
                    x, y, w, h = bbox
                    coco[split]["annotations"].append(
                        {
                            "id": ann_id,
                            "image_id": image_id,
                            "category_id": label,
                            "bbox": [round(x, 2), round(y, 2), round(w, 2), round(h, 2)],
                            "area": round(w * h, 2),
                            "iscrowd": 0,
                            "confidence": float(det.get("confidence", 0.0)),
                            "source": det.get("source", ""),
                        }
                    )
                    ann_id += 1

                    xc = (x + w / 2) / width
                    yc = (y + h / 2) / height
                    yolo_lines.append((label, xc, yc, w / width, h / height))

                if yolo_lines:
                    label_path = paths["labels"] / split / f"{Path(image_name).stem}.txt"
                    yolo_labels[label_path] = yolo_lines

                image_id += 1

    labels = config.taxonomy or sorted(labels_set)
    label_to_id = {label: idx for idx, label in enumerate(labels)}

    (output_dir / "labels.txt").write_text("\n".join(labels), encoding="utf-8")
    (output_dir / "labels.json").write_text(
        json.dumps({"labels": labels, "label_to_id": label_to_id}, indent=2),
        encoding="utf-8",
    )

    for split in ["train", "val", "test"]:
        coco[split]["categories"] = [
            {"id": idx + 1, "name": label} for idx, label in enumerate(labels)
        ]
        for ann in coco[split]["annotations"]:
            label = ann["category_id"]
            ann["category_id"] = label_to_id[label] + 1
        (paths["annotations"] / f"instances_{split}.json").write_text(
            json.dumps(coco[split], indent=2),
            encoding="utf-8",
        )

    for label_path, lines in yolo_labels.items():
        label_path.write_text(
            "\n".join(
                f"{label_to_id[label]} {xc:.6f} {yc:.6f} {ww:.6f} {hh:.6f}"
                for label, xc, yc, ww, hh in lines
            ),
            encoding="utf-8",
        )

    manifest = {
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "output_dir": str(output_dir),
        "source_data_dir": str(DATA_DIR),
        "videos": split_map,
        "splits": {
            "train": config.splits[0],
            "val": config.splits[1],
            "test": config.splits[2],
        },
        "seed": config.seed,
        "min_confidence": config.min_confidence,
        "include_sources": config.include_sources,
        "use_annotated": config.use_annotated,
        "taxonomy": labels,
        "adapter": adapter.__class__.__name__,
    }
    (output_dir / "dataset_manifest.json").write_text(
        json.dumps(manifest, indent=2), encoding="utf-8"
    )

    return output_dir


def _empty_coco() -> Dict:
    return {"images": [], "annotations": [], "categories": []}
