"""
Scene-level analysis for describing what is happening in the video over time.
"""

from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional

from thales.entity_detector import frame_to_base64, get_pixtral_client
from thales.video_processor import extract_frames_at_intervals, seconds_to_timestamp
from thales.config import PIXTRAL_MODEL


def describe_frame(client, image_base64: str) -> str:
    prompt = (
        "Describe the scene in 1-2 concise sentences. Focus only on what is visible "
        "in the frame: people, vehicles, objects, actions, and environment. "
        "Do not speculate. If the scene is unclear, say 'Unclear scene.'"
    )

    response = client.chat.complete(
        model=PIXTRAL_MODEL,
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "image_url", "image_url": f"data:image/jpeg;base64,{image_base64}"},
                    {"type": "text", "text": prompt},
                ],
            }
        ],
        temperature=0.2,
    )

    content = response.choices[0].message.content.strip()
    return content.split("\n")[0].strip()


def generate_scene_timeline(
    video_path: str,
    interval_seconds: int = 10,
    max_frames: int = 120,
    progress_cb: Optional[Callable[[int, int, Dict[str, Any]], None]] = None,
) -> List[Dict[str, Any]]:
    client = get_pixtral_client()

    frames = extract_frames_at_intervals(video_path, interval_seconds)
    if not frames:
        return []

    if max_frames and len(frames) > max_frames:
        step = max(1, int(len(frames) / max_frames) + 1)
        frames = frames[::step]

    timeline: List[Dict[str, Any]] = []
    total = len(frames)

    for idx, (second, frame) in enumerate(frames, 1):
        image_base64 = frame_to_base64(frame)
        summary = describe_frame(client, image_base64)
        entry = {
            "timestamp": seconds_to_timestamp(int(second)),
            "second": int(second),
            "summary": summary,
        }
        timeline.append(entry)
        if progress_cb:
            progress_cb(idx, total, entry)

    return timeline
