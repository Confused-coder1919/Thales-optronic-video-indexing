from __future__ import annotations

import re
from pathlib import Path
from typing import Dict, List, Tuple

from transformers import pipeline

from .config import (
    DISCOVERY_MODEL,
    DISCOVERY_MIN_SCORE,
    DISCOVERY_MAX_PHRASES,
)


STOPWORDS = {
    "a",
    "an",
    "the",
    "and",
    "or",
    "of",
    "to",
    "in",
    "on",
    "at",
    "with",
    "for",
    "from",
    "by",
    "as",
    "is",
    "are",
    "was",
    "were",
    "this",
    "that",
    "these",
    "those",
    "it",
    "its",
    "their",
    "his",
    "her",
    "aerial",
    "view",
    "photo",
    "image",
    "picture",
    "scene",
    "background",
    "front",
    "back",
    "left",
    "right",
    "top",
    "bottom",
    "group",
    "people",
    "person",
    "man",
    "woman",
    "men",
    "women",
    "someone",
    "something",
    "someone's",
    "something's",
}

BLOCKLIST = {
    "sky",
    "water",
    "sea",
    "ocean",
    "cloud",
    "clouds",
    "ground",
    "field",
    "mountain",
    "mountains",
    "forest",
    "trees",
}


def _normalize_phrase(phrase: str) -> str:
    words = []
    for word in phrase.split():
        if word.endswith("s") and len(word) > 3:
            word = word[:-1]
        words.append(word)
    return " ".join(words).strip()


def extract_entities_from_caption(caption: str) -> List[str]:
    text = caption.lower()
    text = re.sub(r"[^a-z0-9\\s-]", " ", text)
    text = text.replace("-", " ")
    tokens = [token for token in text.split() if token]

    chunks: List[List[str]] = []
    current: List[str] = []
    for token in tokens:
        if token in STOPWORDS:
            if current:
                chunks.append(current)
                current = []
            continue
        current.append(token)
    if current:
        chunks.append(current)

    phrases = []
    for chunk in chunks:
        chunk_len = len(chunk)
        max_n = min(3, chunk_len)
        for n in range(1, max_n + 1):
            for idx in range(chunk_len - n + 1):
                phrase = " ".join(chunk[idx : idx + n]).strip()
                if len(phrase) < 3:
                    continue
                if phrase in BLOCKLIST:
                    continue
                if phrase.isdigit():
                    continue
                normalized = _normalize_phrase(phrase)
                if normalized and normalized not in BLOCKLIST:
                    phrases.append(normalized)

    # Prefer longer, more descriptive phrases
    phrases = sorted(set(phrases), key=lambda item: (-len(item.split()), item))
    return phrases[:DISCOVERY_MAX_PHRASES]


class CaptionDiscovery:
    def __init__(self) -> None:
        self._pipe = None

    def _ensure_pipe(self):
        if self._pipe is not None:
            return
        self._pipe = pipeline(
            "image-to-text",
            model=DISCOVERY_MODEL,
        )

    def caption(self, frame_path: Path) -> Tuple[str, float]:
        self._ensure_pipe()
        outputs = self._pipe(str(frame_path), max_new_tokens=50)
        if not outputs:
            return "", 0.0
        result = outputs[0]
        text = (result.get("generated_text") or "").strip()
        score = float(result.get("score") or 0.0)
        return text, score

    def detect(self, frame_path: Path) -> List[Dict]:
        caption, score = self.caption(frame_path)
        if not caption:
            return []
        if score and score < DISCOVERY_MIN_SCORE:
            return []
        entities = extract_entities_from_caption(caption)
        detections: List[Dict] = []
        for label in entities:
            detections.append(
                {
                    "label": label,
                    "confidence": round(score or 0.5, 4),
                    "bbox": [],
                    "source": "discovery",
                }
            )
        return detections
