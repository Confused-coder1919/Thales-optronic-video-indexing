from __future__ import annotations

import re
from pathlib import Path
from typing import Dict, List

from PIL import Image

from .config import OCR_MIN_CONFIDENCE


def _looks_like_marker(text: str) -> bool:
    if len(text) < 3:
        return False
    if text.isdigit():
        return False
    if re.search(r"[A-Z0-9]{2,}-\d{2,}", text):
        return True
    if re.search(r"[A-Z0-9]{3,}", text) and any(ch.isdigit() for ch in text):
        return True
    if text.isupper() and len(text) >= 4:
        return True
    return False


def extract_ocr_entities(frame_path: Path, min_confidence: int = OCR_MIN_CONFIDENCE) -> List[Dict]:
    try:
        import pytesseract
    except Exception:
        return []

    image = Image.open(frame_path).convert("RGB")
    data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)
    detections: List[Dict] = []
    for idx, raw_text in enumerate(data.get("text", [])):
        text = (raw_text or "").strip()
        if not text:
            continue
        conf_str = data.get("conf", [])[idx]
        try:
            conf = float(conf_str)
        except Exception:
            conf = -1
        if conf < min_confidence:
            continue
        token = re.sub(r"[^A-Za-z0-9-]", "", text)
        if not token:
            continue
        token = token.upper()
        if not _looks_like_marker(token):
            continue
        detections.append(
            {
                "label": token,
                "confidence": round(conf / 100.0, 4),
                "bbox": [],
                "source": "ocr",
            }
        )
    return detections
