"""
Vision-first discovery mode for proposing entities from sampled frames.
"""

from __future__ import annotations

import base64
import io
import json
import re
from typing import Any, Dict, List, Optional

import cv2
import numpy as np
from PIL import Image
from mistralai import Mistral

from thales.config import MISTRAL_API_KEY, MAX_IMAGE_SIZE, PIXTRAL_MODEL
from thales.entity_extractor import normalize_entity
from thales.video_processor import extract_frames_at_intervals, seconds_to_timestamp


DISCOVERY_PROMPT = (
    "List key visible entities/objects relevant to military context in this frame. "
    "Return ONLY a JSON array of strings. Example: "
    "[\"military truck\", \"armored vehicle\", \"soldier\"]."
)


def get_pixtral_client() -> Mistral:
    """
    Get an initialized Mistral client for Pixtral vision model.
    """
    if not MISTRAL_API_KEY:
        raise ValueError(
            "MISTRAL_API_KEY not found in .env file. "
            "Please add MISTRAL_API_KEY=your_api_key to your .env file."
        )
    return Mistral(api_key=MISTRAL_API_KEY)


def frame_to_base64(frame: np.ndarray) -> str:
    """
    Convert OpenCV frame (BGR) to base64-encoded JPEG string.
    """
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    pil_image = Image.fromarray(rgb_frame)

    if pil_image.width > MAX_IMAGE_SIZE or pil_image.height > MAX_IMAGE_SIZE:
        pil_image.thumbnail((MAX_IMAGE_SIZE, MAX_IMAGE_SIZE), Image.Resampling.LANCZOS)

    buffer = io.BytesIO()
    pil_image.save(buffer, format="JPEG", quality=85)
    buffer.seek(0)

    return base64.standard_b64encode(buffer.read()).decode("utf-8")


def _parse_entity_list(content: str) -> List[str]:
    content = (content or "").strip()
    if not content:
        return []

    try:
        parsed = json.loads(content)
        if isinstance(parsed, list):
            return [str(item).strip() for item in parsed if str(item).strip()]
        if isinstance(parsed, dict):
            for key in ("entities", "items", "objects", "result"):
                value = parsed.get(key)
                if isinstance(value, list):
                    return [str(item).strip() for item in value if str(item).strip()]
    except json.JSONDecodeError:
        pass

    array_match = re.search(r"\[[^\]]*\]", content, re.DOTALL)
    if array_match:
        try:
            parsed = json.loads(array_match.group(0))
            if isinstance(parsed, list):
                return [str(item).strip() for item in parsed if str(item).strip()]
        except json.JSONDecodeError:
            pass

    candidates = []
    for line in content.splitlines():
        cleaned = line.strip().lstrip("-*").strip().strip('"').strip("'")
        if cleaned:
            candidates.append(cleaned)
    return candidates


def discover_entities_in_frame(
    client: Mistral,
    frame: np.ndarray,
) -> List[str]:
    try:
        image_base64 = frame_to_base64(frame)
        response = client.chat.complete(
            model=PIXTRAL_MODEL,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": f"data:image/jpeg;base64,{image_base64}",
                        },
                        {
                            "type": "text",
                            "text": DISCOVERY_PROMPT,
                        },
                    ],
                }
            ],
            temperature=0.1,
        )
        content = response.choices[0].message.content.strip()
        return _parse_entity_list(content)
    except Exception as exc:
        print(f"Warning: discovery frame analysis failed: {exc}")
        return []


def discover_entities_in_video(
    video_path: str,
    interval_seconds_discovery: int = 10,
    max_frames: Optional[int] = None,
    progress_cb=None,
) -> List[Dict[str, Any]]:
    """
    Discover entities from sampled frames using Pixtral.

    Returns a list of dicts: {"timestamp": "MM:SS", "second": <int>, "entities": [...]}
    """
    client = get_pixtral_client()
    frames = extract_frames_at_intervals(video_path, interval_seconds_discovery)
    if not frames:
        return []

    if max_frames is not None:
        frames = frames[: max(0, int(max_frames))]

    discoveries: List[Dict[str, Any]] = []
    for idx, (second, frame) in enumerate(frames, 1):
        raw_entities = discover_entities_in_frame(client, frame)
        normalized = []
        for entity in raw_entities:
            normalized_entity = normalize_entity(entity)
            if normalized_entity:
                normalized.append(normalized_entity)

        unique_entities = sorted(set(normalized))
        if unique_entities:
            discoveries.append(
                {
                    "timestamp": seconds_to_timestamp(second),
                    "second": second,
                    "entities": unique_entities,
                }
            )

        if progress_cb:
            progress_cb(idx, len(frames))

    return discoveries
