from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from thales.export_thales_csv import export_thales_csv
from thales.fusion import fuse_speech_and_vision
from thales.pivot import write_vision_pivot_jsonl
from thales.voice_parser import get_all_segments


def timestamp_to_seconds(timestamp: str) -> float:
    parts = [p for p in timestamp.strip().split(":") if p]
    try:
        if len(parts) == 2:
            minutes = int(parts[0])
            seconds = float(parts[1])
            return minutes * 60 + seconds
        if len(parts) == 3:
            hours = int(parts[0])
            minutes = int(parts[1])
            seconds = float(parts[2])
            return hours * 3600 + minutes * 60 + seconds
    except Exception:
        return 0.0
    return 0.0


def speech_events_from_voice(
    voice_file_path: str,
    max_window_seconds: int,
) -> List[Dict[str, Any]]:
    segments = get_all_segments(voice_file_path)
    if not segments:
        return []

    window = max(1, int(max_window_seconds))
    starts = [timestamp_to_seconds(ts) for ts, _ in segments]

    events: List[Dict[str, Any]] = []
    for idx, (timestamp, text) in enumerate(segments):
        cleaned = str(text).strip()
        if not cleaned:
            continue

        start = float(starts[idx])
        end = start + window

        if idx + 1 < len(starts):
            next_start = float(starts[idx + 1])
            if next_start > start:
                end = min(next_start, start + window)

        if end < start:
            end = start + window

        mid = start + (end - start) / 2.0
        events.append(
            {
                "t_start": round(start, 3),
                "t_end": round(end, 3),
                "t": round(mid, 3),
                "source": "speech",
                "event": "mention",
                "text": cleaned,
                "avg_logprob": None,
            }
        )

    return events


def write_speech_pivot_from_voice(
    voice_file_path: str,
    out_path: Path,
    max_window_seconds: int,
) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    events = speech_events_from_voice(voice_file_path, max_window_seconds)
    with open(out_path, "w", encoding="utf-8") as handle:
        for event in events:
            handle.write(json.dumps(event, ensure_ascii=False) + "\n")


def write_pivot_files(
    voice_file_path: str,
    detection_results: Dict[str, List[Dict[str, Any]]],
    pivot_dir: Path,
    video_stem: str,
    speech_window_seconds: int,
) -> Dict[str, str]:
    pivot_dir.mkdir(parents=True, exist_ok=True)

    speech_path = pivot_dir / f"{video_stem}_speech.jsonl"
    vision_path = pivot_dir / f"{video_stem}_vision.jsonl"
    merged_path = pivot_dir / f"{video_stem}_merged.jsonl"

    write_speech_pivot_from_voice(
        voice_file_path, speech_path, speech_window_seconds
    )
    write_vision_pivot_jsonl(detection_results, vision_path)
    fuse_speech_and_vision(speech_path, vision_path, merged_path)

    return {
        "speech": str(speech_path),
        "vision": str(vision_path),
        "merged": str(merged_path),
    }


def generate_thales_csv(
    pivot_dir: Path,
    out_csv: Path,
    project_root: Optional[Path] = None,
) -> Optional[Path]:
    pivot_dir = Path(pivot_dir)
    if not pivot_dir.exists():
        return None

    merged_files = list(pivot_dir.glob("*_merged.jsonl"))
    if not merged_files:
        return None

    export_thales_csv(
        pivot_dir=pivot_dir,
        out_csv=out_csv,
        project_root=project_root or Path("."),
    )
    return out_csv
