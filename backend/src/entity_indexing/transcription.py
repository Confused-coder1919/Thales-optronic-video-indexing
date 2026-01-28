from __future__ import annotations

import os
from pathlib import Path
from typing import Dict, List

import torch
from faster_whisper import WhisperModel


def _load_model() -> WhisperModel:
    model_name = os.getenv("ENTITY_INDEXING_WHISPER_MODEL", "base")
    device = "cuda" if torch.cuda.is_available() else "cpu"
    compute_type = "float16" if device == "cuda" else "int8"
    return WhisperModel(model_name, device=device, compute_type=compute_type)


def transcribe_audio(audio_path: Path) -> Dict[str, object]:
    model = _load_model()
    try:
        segments_iter, info = model.transcribe(
            str(audio_path),
            beam_size=5,
            vad_filter=True,
            word_timestamps=False,
        )
    except Exception as exc:  # pragma: no cover - library edge cases
        message = str(exc)
        if "max() arg is an empty sequence" in message:
            return {
                "language": "unknown",
                "segments": [],
                "text": "",
                "error": "No speech detected in the audio track.",
            }
        raise

    segments: List[Dict[str, object]] = []
    text_parts: List[str] = []

    for idx, seg in enumerate(segments_iter):
        segments.append(
            {
                "segment_id": idx,
                "start": round(float(seg.start), 3),
                "end": round(float(seg.end), 3),
                "text": seg.text.strip(),
            }
        )
        text_parts.append(seg.text.strip())

    return {
        "language": getattr(info, "language", "unknown"),
        "segments": segments,
        "text": " ".join(part for part in text_parts if part),
    }
