# thales/stt_runner.py
from __future__ import annotations

import os
from pathlib import Path
from datetime import datetime, timezone
import pandas as pd

from backend.src.core import transcribe as stt_transcribe
from backend.src.core import analyze_outputs as stt_analyze


def run_stt(audio_path: str, config_path: str = "backend/config/settings.yaml",
            output_dir: str = "backend/data/output") -> Path:
    """
    Run colleague STT on an audio file and write outputs into a timestamped job folder.
    Returns the job folder path.
    """
    config = stt_transcribe.load_config(config_path)

    # build job_id like colleague CLI does
    filename = Path(audio_path).stem
    timestamp = datetime.now(timezone.utc).strftime(config["output"]["timestamp_format"])
    job_dir = Path(output_dir) / f"{filename}_{timestamp}"
    job_dir.mkdir(parents=True, exist_ok=True)

    # transcribe
    lang, segments, words = stt_transcribe.transcribe_audio(audio_path, config)

    # save segments.csv
    seg_path = job_dir / "segments.csv"
    stt_transcribe.save_to_csv(
        segments,
        str(seg_path),
        ["segment_id", "start", "end", "text", "avg_logprob"]
    )

    # analyze -> sitrep.json (optional but nice to keep)
    df = stt_analyze.load_data(str(job_dir))
    report = stt_analyze.generate_intel_report(df, config)
    import json
    with open(job_dir / "sitrep.json", "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    return job_dir


def load_segments(job_dir: Path) -> pd.DataFrame:
    """Load segments.csv as a DataFrame."""
    return pd.read_csv(job_dir / "segments.csv")
