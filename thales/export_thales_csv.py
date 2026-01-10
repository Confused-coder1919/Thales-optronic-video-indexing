from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime


# =========================
# Helpers
# =========================
def safe_float(x: Any) -> Optional[float]:
    try:
        if x is None or x == "":
            return None
        return float(x)
    except Exception:
        return None


def mmss(seconds: Optional[float]) -> str:
    if seconds is None:
        return ""
    s = max(0.0, float(seconds))
    m = int(s // 60)
    sec = int(s % 60)
    return f"{m:02d}:{sec:02d}"


def hhmmss(seconds: Optional[float]) -> str:
    """Convert seconds to HH:MM:SS."""
    if seconds is None:
        return ""
    s = max(0.0, float(seconds))
    h = int(s // 3600)
    m = int((s % 3600) // 60)
    sec = int(s % 60)
    return f"{h:02d}:{m:02d}:{sec:02d}"


def iter_jsonl(path: Path) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                out.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return out


def parse_video_number(video_stem: str) -> str:
    # "video_1" -> "1"
    try:
        return video_stem.split("_", 1)[1]
    except Exception:
        return video_stem


def default_video_date_time(video_stem: str) -> Tuple[str, str]:
    """
    If you don't have real acquisition date/time, we put generation date/time.
    Thales-friendly placeholders: today's date and current time.
    """
    now = datetime.now()
    return now.strftime("%d/%m/%Y"), now.strftime("%H:%M:%S")


def get_video_duration_from_files(project_root: Path, video_stem: str) -> Optional[float]:
    """
    Optional: try to read duration from actual video file if present under ./data/video_X.mp4.
    If not found or no cv2, return None.
    """
    video_num = parse_video_number(video_stem)
    candidates = [
        project_root / "data" / f"video_{video_num}.mp4",
        project_root / "data" / f"video_{video_num}.mkv",
        project_root / "data" / f"{video_stem}.mp4",
        project_root / "data" / f"{video_stem}.mkv",
    ]
    video_path = next((p for p in candidates if p.exists()), None)
    if video_path is None:
        return None

    try:
        import cv2  # type: ignore
    except Exception:
        return None

    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        return None

    fps = cap.get(cv2.CAP_PROP_FPS)
    frame_count = cap.get(cv2.CAP_PROP_FRAME_COUNT)
    cap.release()

    if fps and fps > 0:
        return float(frame_count) / float(fps)
    return None


# =========================
# Core: export events
# =========================
def export_thales_csv(
    pivot_dir: Path = Path("reports") / "pivot",
    out_csv: Path = Path("reports") / "thales_metadata.csv",
    project_root: Path = Path("."),
):
    merged_files = sorted(pivot_dir.glob("*_merged.jsonl"))
    if not merged_files:
        raise FileNotFoundError(f"No *_merged.jsonl found in: {pivot_dir.resolve()}")

    rows: List[Dict[str, Any]] = []

    # We'll put one "Video start" line and one "Video stop" line per video (like a log header),
    # then the observation lines (appear/disappear).
    for merged_path in merged_files:
        video_stem = merged_path.name.replace("_merged.jsonl", "")  # e.g. video_1
        events = iter_jsonl(merged_path)

        # Collect all timestamps from merged file to determine start/stop
        times = [safe_float(e.get("t")) for e in events if safe_float(e.get("t")) is not None]
        t_min = min(times) if times else 0.0

        # Try to get real duration from video file; otherwise use max event time
        duration = get_video_duration_from_files(project_root, video_stem)
        t_max = duration if duration is not None else (max(times) if times else 0.0)

        date_str, hour_str = default_video_date_time(video_stem)

        # --- Video start row
        rows.append({
            "Date (dd/mm/YYYY)": date_str,
            "Hour (HH:MM:SS)": hour_str,
            "Start/Stop": "Video start",
            # observations
            "Video": video_stem,
            "Entity": "",
            "Event": "",
            "Timecode (MM:SS)": mmss(t_min),
            "Time (sec)": round(float(t_min), 3),
            "Speech context": "",
            "Speech seg start (sec)": "",
            "Speech seg end (sec)": "",
        })

        # --- Observation rows (vision appear/disappear)
        for e in sorted(events, key=lambda x: safe_float(x.get("t")) or 0.0):
            if e.get("source") != "vision":
                continue

            t = safe_float(e.get("t"))
            if t is None:
                continue

            ev = str(e.get("event", "")).strip().lower()
            if ev not in {"appear", "disappear"}:
                continue

            targets = e.get("targets") or []
            if not isinstance(targets, list) or not targets:
                continue

            sc = e.get("speech_context")
            sc_text = ""
            sc_ts = ""
            sc_te = ""
            if isinstance(sc, dict):
                sc_text = str(sc.get("text", "")).strip()
                _ts = safe_float(sc.get("t_start"))
                _te = safe_float(sc.get("t_end"))
                sc_ts = "" if _ts is None else round(_ts, 3)
                sc_te = "" if _te is None else round(_te, 3)

            for entity in targets:
                entity = str(entity).strip()
                if not entity:
                    continue

                rows.append({
                    "Date (dd/mm/YYYY)": date_str,
                    "Hour (HH:MM:SS)": hour_str,
                    "Start/Stop": "",  # blank for observations
                    # observations
                    "Video": video_stem,
                    "Entity": entity,
                    "Event": ev,
                    "Timecode (MM:SS)": mmss(t),
                    "Time (sec)": round(float(t), 3),
                    "Speech context": sc_text,
                    "Speech seg start (sec)": sc_ts,
                    "Speech seg end (sec)": sc_te,
                })

        # --- Video stop row
        rows.append({
            "Date (dd/mm/YYYY)": date_str,
            "Hour (HH:MM:SS)": hour_str,
            "Start/Stop": "Video stop",
            # observations
            "Video": video_stem,
            "Entity": "",
            "Event": "",
            "Timecode (MM:SS)": mmss(t_max),
            "Time (sec)": round(float(t_max), 3),
            "Speech context": "",
            "Speech seg start (sec)": "",
            "Speech seg end (sec)": "",
        })

    out_csv.parent.mkdir(parents=True, exist_ok=True)

    headers = [
        "Date (dd/mm/YYYY)",
        "Hour (HH:MM:SS)",
        "Start/Stop",
        "Video",
        "Entity",
        "Event",
        "Timecode (MM:SS)",
        "Time (sec)",
        "Speech context",
        "Speech seg start (sec)",
        "Speech seg end (sec)",
    ]

    with open(out_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=headers, delimiter=";")
        writer.writeheader()
        writer.writerows(rows)

    print(f"[OK] Thales CSV generated: {out_csv} ({len(rows)} rows)")


if __name__ == "__main__":
    export_thales_csv()
