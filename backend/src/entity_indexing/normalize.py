from __future__ import annotations

import re


CONTROLLED_ENTITY_LABELS = {
    "aircraft",
    "aircraft carrier",
    "artillery",
    "boat",
    "drone",
    "fighter jet",
    "helicopter",
    "military helicopter",
    "military personnel",
    "military vehicle",
    "missile",
    "person",
    "radar",
    "satellite",
    "submarine",
    "tank",
    "train",
    "truck",
    "vehicle",
    "warship",
    "weapon",
}


CANONICAL_MAP = {
    "airplane": "aircraft",
    "plane": "aircraft",
    "jet": "aircraft",
    "bomber": "aircraft",
    "military plane": "aircraft",
    "military aircraft": "aircraft",
    "naval ship": "warship",
    "military ship": "warship",
    "battleship": "warship",
    "destroyer": "warship",
    "frigate": "warship",
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
    "soldier": "military personnel",
    "soldiers": "military personnel",
    "troop": "military personnel",
    "troops": "military personnel",
    "infantry": "military personnel",
    "marine": "military personnel",
    "marines": "military personnel",
    "operator": "military personnel",
    "crew": "military personnel",
    "gunner": "military personnel",
    "pilot": "military personnel",
    "personnel": "person",
    "armored vehicle": "military vehicle",
    "armoured vehicle": "military vehicle",
    "armored car": "military vehicle",
    "armoured car": "military vehicle",
    "armored personnel carrier": "military vehicle",
    "armoured personnel carrier": "military vehicle",
    "vehicle": "vehicle",
    "car": "vehicle",
    "bus": "vehicle",
    "motorcycle": "vehicle",
    "truck": "truck",
    "boat": "boat",
    "train": "train",
    "main battle tank": "tank",
    "armored tank": "tank",
    "armoured tank": "tank",
    "self propelled gun": "artillery",
    "self-propelled gun": "artillery",
    "unmanned aerial vehicle": "drone",
    "unmanned aircraft": "drone",
    "uav": "drone",
    "drone": "drone",
    "machine gun": "weapon",
    "surface to air missile": "missile",
    "rocket": "missile",
    "missile": "missile",
    "weapon": "weapon",
    "rifle": "weapon",
    "gun": "weapon",
    "cannon": "weapon",
    "turret": "weapon",
    "radar": "radar",
    "satellite": "satellite",
    "submarine": "submarine",
    "helicopter": "helicopter",
    "person": "person",
}


NOISE_TERMS = {
    "air",
    "around",
    "back",
    "background",
    "behind",
    "below",
    "bird",
    "black",
    "body",
    "cloud",
    "clouds",
    "cloudy",
    "cockpit",
    "coming",
    "dark",
    "deck",
    "filled",
    "flying",
    "forest",
    "game",
    "glass",
    "goggle",
    "hanging",
    "hat",
    "helmet",
    "inside",
    "jacket",
    "keyboard",
    "large",
    "looking",
    "lot",
    "many",
    "ocean",
    "out",
    "over",
    "screen",
    "seen",
    "sky",
    "smoke",
    "space",
    "standing",
    "station",
    "through",
    "typing",
    "under",
    "video",
    "white",
}


def is_marker_label(label: str) -> bool:
    if not label:
        return False
    return bool(re.match(r"^[A-Z0-9-]{3,}$", label) and any(ch.isdigit() for ch in label))


def is_structured_entity_label(label: str) -> bool:
    return bool(label) and label in CONTROLLED_ENTITY_LABELS


def canonicalize_label(label: str) -> str:
    if not label:
        return ""
    raw = label.strip()
    if not raw:
        return ""
    if is_marker_label(raw):
        return raw.upper()

    text = raw.lower()
    text = re.sub(r"\\s+", " ", text)
    text = text.replace("-", " ").strip()
    if not text:
        return ""
    if text in CANONICAL_MAP:
        return CANONICAL_MAP[text]

    tokens = {token for token in text.split() if token}
    if not tokens:
        return ""

    if "carrier" in tokens and ("aircraft" in tokens or "naval" in tokens):
        return "aircraft carrier"
    if {"fighter", "jet"} <= tokens or ("fighter" in tokens and "aircraft" in tokens):
        return "fighter jet"
    if any(token in tokens for token in {"warship", "destroyer", "frigate", "battleship"}):
        return "warship"
    if "ship" in tokens and ("naval" in tokens or "military" in tokens):
        return "warship"
    if "submarine" in tokens:
        return "submarine"
    if "helicopter" in tokens:
        if any(token in tokens for token in {"attack", "combat", "military", "gunship"}):
            return "military helicopter"
        return "helicopter"
    if any(token in tokens for token in {"drone", "uav", "quadcopter"}):
        return "drone"
    if any(token in tokens for token in {"missile", "rocket", "sam"}):
        return "missile"
    if any(token in tokens for token in {"weapon", "rifle", "gun", "cannon", "turret"}):
        return "weapon"
    if any(token in tokens for token in {"artillery", "howitzer", "spg"}):
        return "artillery"
    if "tank" in tokens:
        return "tank"
    if any(token in tokens for token in {"armored", "armoured", "apc", "ifv"}):
        return "military vehicle"
    if "vehicle" in tokens and "military" in tokens:
        return "military vehicle"
    if "satellite" in tokens:
        return "satellite"
    if "radar" in tokens:
        return "radar"
    if any(token in tokens for token in {"soldier", "troop", "troops", "infantry", "marine", "marines", "crew", "operator", "gunner"}):
        return "military personnel"
    if "personnel" in tokens and "military" in tokens:
        return "military personnel"
    if "person" in tokens or "people" in tokens:
        return "person"
    if "truck" in tokens:
        return "truck"
    if any(token in tokens for token in {"car", "bus", "vehicle", "motorcycle", "jeep"}):
        return "vehicle"
    if "boat" in tokens:
        return "boat"
    if "train" in tokens:
        return "train"
    if any(token in tokens for token in {"aircraft", "airplane", "plane", "jet", "bomber"}):
        return "aircraft"

    meaningful_tokens = {token for token in tokens if token not in NOISE_TERMS}
    if meaningful_tokens and meaningful_tokens != tokens:
        return canonicalize_label(" ".join(sorted(meaningful_tokens)))

    return ""
