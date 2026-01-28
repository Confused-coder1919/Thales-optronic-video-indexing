from __future__ import annotations

import re


CANONICAL_MAP = {
    "naval ship": "warship",
    "military ship": "warship",
    "carrier ship": "aircraft carrier",
    "naval carrier": "aircraft carrier",
    "carrier vessel": "aircraft carrier",
    "aircraft-carrier": "aircraft carrier",
    "fighter aircraft": "fighter jet",
    "combat aircraft": "fighter jet",
    "attack helicopter": "military helicopter",
    "combat helicopter": "military helicopter",
    "gunship helicopter": "military helicopter",
    "helicopter gunship": "military helicopter",
    "armored vehicle": "military vehicle",
    "armoured vehicle": "military vehicle",
    "armored car": "military vehicle",
    "armoured car": "military vehicle",
    "armored personnel carrier": "military vehicle",
    "armoured personnel carrier": "military vehicle",
    "main battle tank": "tank",
    "armored tank": "tank",
    "armoured tank": "tank",
    "self propelled gun": "artillery",
    "self-propelled gun": "artillery",
    "unmanned aerial vehicle": "drone",
    "unmanned aircraft": "drone",
    "machine gun": "weapon",
    "surface to air missile": "missile",
}


def canonicalize_label(label: str) -> str:
    if not label:
        return label
    text = label.strip().lower()
    if re.match(r"^[A-Z0-9-]{3,}$", label) and any(ch.isdigit() for ch in label):
        return label.strip().upper()
    text = re.sub(r"\\s+", " ", text)
    if text in CANONICAL_MAP:
        return CANONICAL_MAP[text]
    if text in {"apc", "ifv"}:
        return "military vehicle"
    if "carrier" in text and ("aircraft" in text or "naval" in text):
        return "aircraft carrier"
    if "fighter" in text and ("jet" in text or "aircraft" in text):
        return "fighter jet"
    if text.endswith("s") and len(text) > 3:
        singular = text[:-1]
        if singular in CANONICAL_MAP:
            return CANONICAL_MAP[singular]
        return singular
    return text
