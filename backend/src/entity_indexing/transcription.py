from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from typing import Dict, List

import torch
from faster_whisper import WhisperModel


@lru_cache(maxsize=2)
def _load_model(model_name: str) -> WhisperModel:
    device = "cuda" if torch.cuda.is_available() else "cpu"
    compute_type = "float16" if device == "cuda" else "int8"
    return WhisperModel(model_name, device=device, compute_type=compute_type)


def _segments_to_payload(segments_iter, language: str) -> Dict[str, object]:
    segments: List[Dict[str, object]] = []
    text_parts: List[str] = []

    for idx, seg in enumerate(segments_iter):
        text = seg.text.strip()
        segments.append(
            {
                "segment_id": idx,
                "start": round(float(seg.start), 3),
                "end": round(float(seg.end), 3),
                "text": text,
            }
        )
        text_parts.append(text)

    return {
        "language": language,
        "segments": segments,
        "text": " ".join(part for part in text_parts if part),
    }


def transcribe_audio(audio_path: Path) -> Dict[str, object]:
    model_name = os.getenv("ENTITY_INDEXING_WHISPER_MODEL", "base")
    translate_enabled = (
        os.getenv("ENTITY_INDEXING_TRANSLATE_TO_ENGLISH", "1").strip().lower()
        in {"1", "true", "yes", "on"}
    )
    model = _load_model(model_name)
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

    payload = _segments_to_payload(segments_iter, getattr(info, "language", "unknown"))

    language = str(payload.get("language") or "unknown").lower()
    should_translate = (
        translate_enabled
        and payload.get("text")
        and language not in {"unknown", "en", "english"}
        and not model_name.endswith(".en")
    )

    if should_translate:
        try:
            translated_iter, _ = model.transcribe(
                str(audio_path),
                beam_size=5,
                vad_filter=True,
                word_timestamps=False,
                task="translate",
                language=language,
            )
            translated_payload = _segments_to_payload(translated_iter, "en")
            if translated_payload.get("text"):
                payload["translated_text"] = translated_payload["text"]
                payload["translated_segments"] = translated_payload["segments"]
        except Exception as exc:  # pragma: no cover - translation is best-effort
            payload["translation_error"] = str(exc)

    return payload
