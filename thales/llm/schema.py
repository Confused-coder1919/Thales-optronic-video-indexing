from __future__ import annotations

import json
import re
from typing import Any, Dict, List

_JSON_BLOCK_RE = re.compile(r"\{.*\}", re.DOTALL)
_CODE_FENCE_RE = re.compile(r"^```(?:json)?\s*|\s*```$", re.IGNORECASE)
_FALLBACK_ENTITY_KEYS = ("entity_list", "result", "entities_found", "items")


def _clean_raw_json(text: str) -> str:
    cleaned = (text or "").strip()
    cleaned = _CODE_FENCE_RE.sub("", cleaned).strip()
    return cleaned


def parse_json_payload(text: str) -> Dict[str, Any]:
    """
    Parse LLM response into JSON object with lightweight repair for fenced output.
    """
    cleaned = _clean_raw_json(text)
    if not cleaned:
        raise ValueError("LLM returned empty response.")

    try:
        parsed = json.loads(cleaned)
    except json.JSONDecodeError:
        match = _JSON_BLOCK_RE.search(cleaned)
        if not match:
            raise ValueError("LLM response is not valid JSON.")
        parsed = json.loads(match.group(0))

    return validate_index_payload(parsed)


def validate_index_payload(payload: Any) -> Dict[str, Any]:
    """
    Validate/normalize payload for existing extraction schema: {"entities": [...]}.
    """
    entities: List[Any] | None = None

    if isinstance(payload, dict):
        if isinstance(payload.get("entities"), list):
            entities = payload["entities"]
        else:
            for key in _FALLBACK_ENTITY_KEYS:
                if isinstance(payload.get(key), list):
                    entities = payload[key]
                    break
            if entities is None:
                for value in payload.values():
                    if isinstance(value, list):
                        entities = value
                        break
    elif isinstance(payload, list):
        entities = payload

    if entities is None:
        raise ValueError("Indexed payload missing 'entities' list.")

    normalized: List[str] = []
    for item in entities:
        value = str(item).strip()
        if value:
            normalized.append(value)

    return {"entities": normalized}


def build_index_prompt(segment_input: Dict[str, Any]) -> str:
    """
    Build strict-JSON prompt for entity indexing extraction.
    """
    transcript = (
        segment_input.get("transcript")
        or segment_input.get("text")
        or ""
    )
    timestamps = segment_input.get("timestamps") or {}
    vision_detections = segment_input.get("vision_detections") or []

    timestamp_text = json.dumps(timestamps, ensure_ascii=False)
    vision_text = json.dumps(vision_detections, ensure_ascii=False)

    return f"""Extract all military-relevant entities from this segment and normalize to HIGH-LEVEL, SEARCHABLE terms.

Return ONLY valid JSON (no markdown), exactly:
{{"entities": ["entity_a", "entity_b"]}}

Rules:
1. Use general categories, NOT verbose descriptions.
2. Normalize synonyms consistently.
3. Distinguish military personnel vs civilian.
4. Exclude clothing-only descriptors and generic vehicle part words.
5. Include license plates if present (e.g. "AAB960A").
6. If no entities are found, return: {{"entities": []}}.

Normalization hints:
- driver/operator/crew member/soldier/commander/officer -> military personnel
- civilian/bystander/passerby/spectator -> civilian
- military transport/semi/logistics truck -> military truck
- tank/APC/IFV -> armored vehicle
- self-propelled artillery/howitzer -> artillery vehicle
- flatbed/low loader/transport trailer -> trailer
- UAV/unmanned aerial vehicle -> drone
- gun/cannon/missile/rocket -> weapon
- turret/gun barrel -> turret

Segment transcript:
{transcript}

Segment timestamps:
{timestamp_text}

Vision detections context (if any):
{vision_text}
"""


def build_json_repair_prompt(
    bad_output: str,
    segment_input: Dict[str, Any],
) -> str:
    """
    Re-ask prompt used once if provider returns invalid JSON.
    """
    schema = '{"entities": ["entity_a", "entity_b"]}'
    return (
        "Return ONLY valid JSON matching this schema exactly:\n"
        f"{schema}\n\n"
        "Do not include markdown, prose, or extra keys.\n\n"
        f"Original invalid output:\n{bad_output}\n\n"
        f"Transcript:\n{segment_input.get('transcript') or segment_input.get('text') or ''}\n"
    )

