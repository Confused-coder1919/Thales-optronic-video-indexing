from __future__ import annotations

import re
from pathlib import Path
from typing import Dict, List, Tuple

import torch
from PIL import Image
from transformers import BlipForConditionalGeneration, BlipProcessor

from .config import (
    DISCOVERY_MODEL,
    DISCOVERY_MIN_SCORE,
    DISCOVERY_MAX_PHRASES,
    DISCOVERY_ONLY_MILITARY,
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
    "under",
    "over",
    "through",
    "across",
    "between",
    "near",
    "above",
    "below",
    "around",
    "into",
    "onto",
    "off",
    "up",
    "down",
    "left",
    "right",
    "front",
    "back",
    "behind",
    "before",
    "after",
    "during",
    "while",
    "many",
    "several",
    "various",
    "multiple",
    "few",
    "some",
    "other",
    "large",
    "small",
    "big",
    "tiny",
    "huge",
    "massive",
    "wide",
    "tall",
    "long",
    "short",
    "fast",
    "slow",
    "old",
    "new",
    "modern",
    "ancient",
    "red",
    "blue",
    "green",
    "white",
    "black",
    "gray",
    "grey",
}

BLOCKLIST = {
    "sky",
    "water",
    "sea",
    "ocean",
    "cloud",
    "clouds",
    "under",
    "over",
    "through",
    "across",
    "many",
    "several",
    "various",
    "multiple",
    "few",
    "some",
    "other",
    "large",
    "small",
    "big",
    "tiny",
    "huge",
    "massive",
    "wide",
    "tall",
    "long",
    "short",
    "ground",
    "field",
    "mountain",
    "mountains",
    "forest",
    "trees",
}

MILITARY_ALLOWLIST = {
    "aircraft carrier",
    "fighter jet",
    "attack helicopter",
    "military helicopter",
    "military aircraft",
    "bomber",
    "naval ship",
    "warship",
    "destroyer",
    "submarine",
    "tank",
    "armored vehicle",
    "armoured vehicle",
    "military vehicle",
    "artillery",
    "missile",
    "rocket",
    "weapon",
    "gun",
    "rifle",
    "turret",
    "drone",
    "uav",
    "satellite",
    "radar",
    "troops",
    "soldiers",
    "military personnel",
}

MILITARY_KEYWORDS = {
    "military",
    "tank",
    "armored",
    "armoured",
    "artillery",
    "missile",
    "rocket",
    "weapon",
    "gun",
    "rifle",
    "turret",
    "drone",
    "uav",
    "aircraft",
    "fighter",
    "bomber",
    "helicopter",
    "naval",
    "warship",
    "destroyer",
    "submarine",
    "radar",
    "satellite",
    "troop",
    "soldier",
    "personnel",
    "convoy",
    "armor",
    "armour",
    "infantry",
    "navy",
    "marine",
}


def _is_military_phrase(phrase: str) -> bool:
    if phrase in MILITARY_ALLOWLIST:
        return True
    for keyword in MILITARY_KEYWORDS:
        if keyword in phrase:
            return True
    return False


SYNONYM_MAP = {
    "aircraft carrier": [
        "carrier ship",
        "naval carrier",
        "carrier vessel",
        "aircraft-carrier",
    ],
    "warship": [
        "naval ship",
        "military ship",
        "destroyer",
        "frigate",
        "battleship",
    ],
    "fighter jet": [
        "fighter",
        "fighter aircraft",
        "combat aircraft",
    ],
    "military helicopter": [
        "attack helicopter",
        "combat helicopter",
        "gunship helicopter",
        "helicopter gunship",
    ],
    "military vehicle": [
        "armored vehicle",
        "armoured vehicle",
        "armored car",
        "armoured car",
        "armored personnel carrier",
        "armoured personnel carrier",
        "apc",
        "ifv",
    ],
    "tank": [
        "main battle tank",
        "mbt",
        "armored tank",
        "armoured tank",
    ],
    "artillery": [
        "howitzer",
        "self propelled gun",
        "self-propelled gun",
        "spg",
    ],
    "drone": [
        "unmanned aerial vehicle",
        "unmanned aircraft",
        "uav",
        "quadcopter",
    ],
    "military personnel": [
        "soldier",
        "troop",
        "troops",
        "soldiers",
        "infantry",
        "marine",
        "marines",
        "crew",
        "operator",
        "gunner",
        "pilot",
    ],
    "weapon": [
        "machine gun",
        "rifle",
        "gun",
        "cannon",
    ],
    "missile": [
        "rocket",
        "sam",
        "surface to air missile",
    ],
}


def _canonicalize_phrase(phrase: str) -> str:
    phrase = phrase.strip()
    if "carrier" in phrase and ("aircraft" in phrase or "naval" in phrase):
        return "aircraft carrier"
    if "fighter" in phrase and "jet" in phrase:
        return "fighter jet"
    for canonical, variants in SYNONYM_MAP.items():
        if phrase == canonical:
            return canonical
        for variant in variants:
            if phrase == variant:
                return canonical
    return phrase


GENERIC_ONLY = {
    "large",
    "small",
    "big",
    "tiny",
    "huge",
    "many",
    "several",
    "various",
    "multiple",
    "few",
    "some",
    "other",
    "over",
    "through",
    "across",
    "under",
    "around",
    "above",
    "below",
}


def _is_generic_phrase(phrase: str) -> bool:
    tokens = phrase.split()
    if not tokens:
        return True
    return all(token in GENERIC_ONLY for token in tokens)


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
    phrases = [phrase for phrase in phrases if not _is_generic_phrase(phrase)]
    phrases = [_canonicalize_phrase(phrase) for phrase in phrases]
    phrases = sorted(set(phrases), key=lambda item: (-len(item.split()), item))
    if DISCOVERY_ONLY_MILITARY:
        phrases = [phrase for phrase in phrases if _is_military_phrase(phrase)]
    return phrases[:DISCOVERY_MAX_PHRASES]


class CaptionDiscovery:
    def __init__(self) -> None:
        self._processor = None
        self._model = None

    def _ensure_pipe(self):
        if self._model is not None and self._processor is not None:
            return
        device = "cuda" if torch.cuda.is_available() else "cpu"
        self._processor = BlipProcessor.from_pretrained(DISCOVERY_MODEL)
        self._model = BlipForConditionalGeneration.from_pretrained(DISCOVERY_MODEL).to(device)

    def caption(self, frame_path: Path) -> Tuple[str, float]:
        self._ensure_pipe()
        image = Image.open(frame_path).convert("RGB")
        device = self._model.device
        inputs = self._processor(images=image, return_tensors="pt").to(device)
        output = self._model.generate(**inputs, max_new_tokens=50)
        text = self._processor.decode(output[0], skip_special_tokens=True).strip()
        score = 0.5
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
