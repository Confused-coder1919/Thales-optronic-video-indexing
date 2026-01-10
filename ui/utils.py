from __future__ import annotations

import os
import re
import shutil
import subprocess
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple

ALLOWED_VIDEO_EXTS = [".mp4", ".mkv", ".avi", ".mov"]


def find_pairs(data_dir: Path) -> List[Dict[str, str]]:
    """
    Find matching voice/video pairs in a directory.

    Returns a list of dicts with pair_id, voice_path, and video_path.
    """
    data_dir = Path(data_dir)
    if not data_dir.exists():
        return []

    pairs: List[Dict[str, str]] = []
    voice_files = sorted(data_dir.glob("voice_*.txt"))

    for voice_file in voice_files:
        match = re.match(r"voice_(\d+)\.txt$", voice_file.name)
        if not match:
            continue
        pair_id = match.group(1)

        video_file = None
        for ext in ALLOWED_VIDEO_EXTS:
            candidate = data_dir / f"video_{pair_id}{ext}"
            if candidate.exists():
                video_file = candidate
                break

        if video_file:
            pairs.append(
                {
                    "pair_id": pair_id,
                    "voice_path": str(voice_file),
                    "video_path": str(video_file),
                }
            )

    return pairs


def run_pipeline(
    python_exe: str,
    data_dir: Path,
    interval: int,
    out_dir: Path,
    env_overrides: Optional[Dict[str, str]],
    selected_pair_id: Optional[str] = None,
    log_callback=None,
) -> Tuple[int, str, Dict[str, str]]:
    """
    Run the CLI pipeline and return (returncode, logs_text, produced_files).
    """
    root_dir = Path(__file__).resolve().parents[1]
    data_dir = Path(data_dir)
    out_dir = Path(out_dir)

    if not data_dir.is_absolute():
        data_dir = root_dir / data_dir
    if not out_dir.is_absolute():
        out_dir = root_dir / out_dir

    out_dir.mkdir(parents=True, exist_ok=True)

    run_dir = data_dir
    selected_video_path: Optional[Path] = None

    if selected_pair_id is not None:
        pairs = find_pairs(data_dir)
        pair_id = str(selected_pair_id)
        selected = next((p for p in pairs if p["pair_id"] == pair_id), None)
        if not selected:
            return 1, f"Pair {pair_id} not found in {data_dir}", {}

        work_dir = root_dir / "ui" / "work"
        work_dir.mkdir(parents=True, exist_ok=True)

        run_dir = work_dir / f"run_{int(time.time())}_pair_{pair_id}"
        run_dir.mkdir(parents=True, exist_ok=True)

        voice_src = Path(selected["voice_path"])
        video_src = Path(selected["video_path"])
        selected_video_path = video_src

        shutil.copy2(voice_src, run_dir / f"voice_{pair_id}.txt")
        shutil.copy2(video_src, run_dir / f"video_{pair_id}{video_src.suffix}")
    else:
        pairs = find_pairs(data_dir)
        if len(pairs) == 1:
            selected_video_path = Path(pairs[0]["video_path"])

    cmd = [
        python_exe,
        "-u",
        "-m",
        "thales",
        "-d",
        str(run_dir),
        "-i",
        str(interval),
        "-o",
        str(out_dir),
    ]

    env = os.environ.copy()
    env["PYTHONUNBUFFERED"] = "1"
    if env_overrides:
        env.update(env_overrides)

    proc = subprocess.Popen(
        cmd,
        cwd=root_dir,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )

    logs: List[str] = []
    if proc.stdout:
        for line in iter(proc.stdout.readline, ""):
            logs.append(line)
            if log_callback:
                log_callback(line, "".join(logs))
        proc.stdout.close()

    returncode = proc.wait()
    logs_text = "".join(logs)

    produced_files: Dict[str, str] = {}
    summary_path = out_dir / "summary_report.json"
    if summary_path.exists():
        produced_files["summary_report"] = str(summary_path)

    video_report = None
    if selected_video_path:
        candidate = out_dir / f"{selected_video_path.stem}_report.json"
        if candidate.exists():
            video_report = candidate
    else:
        candidates = [
            p for p in out_dir.glob("*_report.json") if p.name != "summary_report.json"
        ]
        if candidates:
            video_report = max(candidates, key=lambda p: p.stat().st_mtime)

    if video_report and video_report.exists():
        produced_files["video_report"] = str(video_report)

    return returncode, logs_text, produced_files
