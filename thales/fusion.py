from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Any, List, Optional


def read_jsonl(path: Path) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    if not path.exists():
        return rows
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rows.append(json.loads(line))
    return rows


def write_jsonl(rows: List[Dict[str, Any]], path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


def find_speech_for_time(speech: List[Dict[str, Any]], t: float) -> Optional[Dict[str, Any]]:
    """
    Return the speech unit active at time t (t_start <= t <= t_end),
    else None.
    Assumes speech entries are sorted by t_start.
    """
    for s in speech:
        if float(s["t_start"]) <= t <= float(s["t_end"]):
            return s
    return None


def fuse_speech_and_vision(
    speech_jsonl: Path,
    vision_jsonl: Path,
    out_jsonl: Path,
) -> List[Dict[str, Any]]:
    speech = read_jsonl(speech_jsonl)
    vision = read_jsonl(vision_jsonl)

    # sort for safety
    speech.sort(key=lambda x: float(x.get("t_start", 0.0)))
    vision.sort(key=lambda x: float(x.get("t", 0.0)))

    merged: List[Dict[str, Any]] = []

    # 1) keep speech units as timeline context
    for s in speech:
        merged.append({
            "t": float(s["t"]),
            "t_start": float(s["t_start"]),
            "t_end": float(s["t_end"]),
            "source": "speech",
            "event": s.get("event", "mention"),
            "text": s.get("text", ""),
            "avg_logprob": s.get("avg_logprob", None),
        })

    # 2) enrich each vision event with the speech context at same time
    for v in vision:
        t = float(v["t"])
        s = find_speech_for_time(speech, t)

        merged.append({
            "t": t,
            "source": "vision",
            "event": v.get("event"),
            "targets": v.get("targets", []),
            "speech_context": None if s is None else {
                "t_start": float(s["t_start"]),
                "t_end": float(s["t_end"]),
                "text": s.get("text", ""),
            }
        })

    merged.sort(key=lambda x: float(x["t"]))
    write_jsonl(merged, out_jsonl)
    return merged
