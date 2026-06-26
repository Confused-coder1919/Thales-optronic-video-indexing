from __future__ import annotations

import re
from pathlib import Path
from typing import Dict, List, Tuple


TRANSCRIPT_PATTERNS: Dict[str, Tuple[str, ...]] = {
    "fighter jet": (
        r"\bfighter jets?\b",
        r"\bcombat jets?\b",
    ),
    "aircraft carrier": (
        r"\baircraft carriers?\b",
        r"\bcarrier ships?\b",
        r"\bnaval carriers?\b",
    ),
    "warship": (
        r"\bwarships?\b",
        r"\bnaval ships?\b",
        r"\bmilitary ships?\b",
        r"\bfrigates?\b",
        r"\bdestroyers?\b",
        r"\bbattleships?\b",
    ),
    "submarine": (
        r"\bsubmarines?\b",
    ),
    "military helicopter": (
        r"\battack helicopters?\b",
        r"\bcombat helicopters?\b",
        r"\bgunships?\b",
        r"\bgunship helicopters?\b",
    ),
    "helicopter": (
        r"\bhelicopters?\b",
    ),
    "aircraft": (
        r"\baircraft\b",
        r"\bairplanes?\b",
        r"\bplanes?\b",
        r"\bbombers?\b",
        r"\bjets?\b",
    ),
    "drone": (
        r"\bdrones?\b",
        r"\buavs?\b",
        r"\bunmanned aerial vehicles?\b",
        r"\bunmanned aircraft\b",
    ),
    "missile": (
        r"\bmissiles?\b",
        r"\brockets?\b",
        r"\bsurface-to-air missiles?\b",
    ),
    "artillery": (
        r"\bartillery\b",
        r"\bhowitzers?\b",
        r"\bself propelled guns?\b",
        r"\bself-propelled guns?\b",
    ),
    "tank": (
        r"\btanks?\b",
        r"\bmain battle tanks?\b",
    ),
    "military vehicle": (
        r"\barmou?red vehicles?\b",
        r"\barmou?red personnel carriers?\b",
        r"\bmilitary vehicles?\b",
        r"\bcombat vehicles?\b",
        r"\bapcs?\b",
        r"\bifvs?\b",
    ),
    "truck": (
        r"\bmilitary trucks?\b",
        r"\btransport trucks?\b",
        r"\btrucks?\b",
    ),
    "vehicle": (
        r"\bvehicles?\b",
        r"\bcars?\b",
        r"\bbuses?\b",
        r"\bmotorcycles?\b",
        r"\bjeeps?\b",
    ),
    "boat": (
        r"\bboats?\b",
    ),
    "train": (
        r"\btrains?\b",
    ),
    "radar": (
        r"\bradars?\b",
        r"\bradar systems?\b",
    ),
    "satellite": (
        r"\bsatellites?\b",
    ),
    "weapon": (
        r"\bweapons?\b",
        r"\brifles?\b",
        r"\bguns?\b",
        r"\bcannons?\b",
        r"\bturrets?\b",
    ),
    "military personnel": (
        r"\bmilitary personnel\b",
        r"\barmed forces\b",
        r"\bsoldiers?\b",
        r"\btroops?\b",
        r"\binfantry\b",
        r"\bmarines?\b",
        r"\bcrew members?\b",
        r"\bgunners?\b",
        r"\boperators?\b",
    ),
    "person": (
        r"\bpeople\b",
        r"\bpersons?\b",
    ),
}


TIMESTAMP_PATTERN = re.compile(r"[\[(](\d{1,2}):(\d{2})[\])]")


def _normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip().lower()


def extract_labels_from_text(text: str) -> List[str]:
    normalized = _normalize_text(text)
    if not normalized:
        return []

    labels: List[str] = []
    for label, patterns in TRANSCRIPT_PATTERNS.items():
        if any(re.search(pattern, normalized) for pattern in patterns):
            labels.append(label)
    return labels


def _read_text_robust(path: Path) -> str:
    data = path.read_bytes()
    for encoding in (
        "utf-8",
        "utf-8-sig",
        "utf-16",
        "utf-16le",
        "utf-16be",
        "cp1252",
        "latin-1",
    ):
        try:
            return data.decode(encoding)
        except UnicodeDecodeError:
            continue
    return data.decode("utf-8", errors="ignore")


def load_voice_segments(path: Path, duration_sec: float) -> List[Dict[str, float | str]]:
    if not path.exists():
        return []

    content = _read_text_robust(path)
    if not content.strip():
        return []

    segments: List[Dict[str, float | str]] = []
    current_start: float | None = None
    current_lines: List[str] = []

    for raw_line in content.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        match = TIMESTAMP_PATTERN.search(line)
        if match:
            if current_start is not None and current_lines:
                segments.append(
                    {
                        "start": current_start,
                        "text": " ".join(current_lines).strip(),
                    }
                )
            minutes, seconds = match.groups()
            current_start = int(minutes) * 60 + int(seconds)
            current_lines = []
            remainder = line[match.end() :].strip()
            if remainder:
                current_lines.append(remainder)
            continue
        if current_start is not None:
            current_lines.append(line)

    if current_start is not None and current_lines:
        segments.append({"start": current_start, "text": " ".join(current_lines).strip()})

    if segments:
        for idx, segment in enumerate(segments):
            next_start = (
                float(segments[idx + 1]["start"])
                if idx + 1 < len(segments)
                else float(duration_sec)
            )
            start = float(segment["start"])
            segment["start"] = max(0.0, start)
            segment["end"] = max(segment["start"], min(float(duration_sec), next_start))
        return segments

    return [{"start": 0.0, "end": float(duration_sec), "text": content.strip()}]


def extract_transcript_mentions(
    transcript_payload: Dict[str, object],
    duration_sec: float,
    voice_segments: List[Dict[str, float | str]] | None = None,
) -> Dict[str, List[Tuple[float, float]]]:
    mentions: Dict[str, List[Tuple[float, float]]] = {}

    segments = transcript_payload.get("translated_segments") or transcript_payload.get("segments") or []
    if isinstance(segments, list):
        for segment in segments:
            if not isinstance(segment, dict):
                continue
            text = str(segment.get("text") or "").strip()
            if not text:
                continue
            start = float(segment.get("start") or 0.0)
            end = float(segment.get("end") or start)
            for label in extract_labels_from_text(text):
                mentions.setdefault(label, []).append((max(0.0, start), max(start, end)))

    for segment in voice_segments or []:
        text = str(segment.get("text") or "").strip()
        if not text:
            continue
        start = float(segment.get("start") or 0.0)
        end = float(segment.get("end") or duration_sec)
        for label in extract_labels_from_text(text):
            mentions.setdefault(label, []).append((max(0.0, start), max(start, end)))

    translated_text = str(transcript_payload.get("translated_text") or "").strip()
    if translated_text and not mentions:
        for label in extract_labels_from_text(translated_text):
            mentions.setdefault(label, []).append((0.0, float(duration_sec)))

    return mentions


def _merge_ranges(ranges: List[Tuple[float, float]]) -> List[Dict[str, float | str]]:
    if not ranges:
        return []
    merged: List[List[float]] = []
    for start, end in sorted(ranges):
        if not merged or start > merged[-1][1]:
            merged.append([start, end])
        else:
            merged[-1][1] = max(merged[-1][1], end)

    return [
        {
            "start_sec": round(start, 2),
            "end_sec": round(end, 2),
            "start_label": f"{int(start // 60):02d}:{int(start % 60):02d}",
            "end_label": f"{int(end // 60):02d}:{int(end % 60):02d}",
        }
        for start, end in merged
    ]


def merge_transcript_entities(
    report: Dict[str, object],
    transcript_mentions: Dict[str, List[Tuple[float, float]]],
    duration_sec: float,
) -> Dict[str, object]:
    entities = dict(report.get("entities") or {})
    transcript_entities: Dict[str, Dict[str, object]] = {}
    safe_duration = max(float(duration_sec or 0.0), 1.0)

    for label, mentions in transcript_mentions.items():
        merged_ranges = _merge_ranges(mentions)
        covered_seconds = sum(
            max(0.0, float(item["end_sec"]) - float(item["start_sec"])) for item in merged_ranges
        )
        transcript_presence = round(min(1.0, covered_seconds / safe_duration), 4)
        transcript_count = len(mentions)
        transcript_confidence = round(min(0.85, 0.35 + 0.1 * min(transcript_count, 3)), 4)
        transcript_entry = {
            "count": transcript_count,
            "presence": transcript_presence,
            "appearances": transcript_count,
            "time_ranges": merged_ranges,
            "raw_count": transcript_count,
            "confidence_score": transcript_confidence,
            "sources": ["transcript"],
        }

        if label in entities:
            existing = dict(entities[label])
            existing["mentioned_in_transcript"] = True
            existing["transcript_count"] = transcript_count
            existing["transcript_time_ranges"] = merged_ranges
            entities[label] = existing
            continue

        transcript_entities[label] = transcript_entry

    report["entities"] = entities
    report["unique_entities"] = len(entities)
    report["transcript_entities"] = transcript_entities
    report["transcript_unique_entities"] = len(transcript_entities)
    return report
