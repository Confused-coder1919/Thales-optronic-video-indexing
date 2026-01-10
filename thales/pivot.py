# thales/pivot.py
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Dict, Any, List, Iterator, Tuple, Optional

import pandas as pd


def ensure_dir(path: Path):
    path.mkdir(parents=True, exist_ok=True)


_SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?])\s+")


def split_sentences(text: str) -> List[str]:
    """
    Split into sentences using simple punctuation rules.
    Keeps it lightweight (no NLP deps).
    """
    text = (text or "").strip()
    if not text:
        return []
    parts = _SENTENCE_SPLIT_RE.split(text)
    # cleanup
    out = []
    for p in parts:
        p = p.strip()
        if p:
            out.append(p)
    return out


def allocate_sentence_times(
    t_start: float,
    t_end: float,
    sentences: List[str],
) -> List[Tuple[float, float, str]]:
    """
    Allocate sub-intervals inside [t_start, t_end] to each sentence.
    We use proportional allocation based on character length.
    Returns list of (sub_start, sub_end, sentence).
    """
    t_start = float(t_start)
    t_end = float(t_end)
    dur = max(0.0, t_end - t_start)

    if not sentences:
        return []

    if len(sentences) == 1 or dur <= 0.0:
        return [(t_start, t_end, sentences[0])]

    weights = [max(1, len(s)) for s in sentences]
    total = float(sum(weights))

    allocated: List[Tuple[float, float, str]] = []
    cursor = t_start
    for i, (s, w) in enumerate(zip(sentences, weights)):
        # last sentence ends exactly at t_end (avoid float drift)
        if i == len(sentences) - 1:
            sub_start, sub_end = cursor, t_end
        else:
            piece = dur * (w / total)
            sub_start, sub_end = cursor, cursor + piece
        allocated.append((sub_start, sub_end, s))
        cursor = sub_end

    return allocated


def iter_speech_units(segments_df: pd.DataFrame) -> Iterator[Dict[str, Any]]:
    """
    Yield finer-grained speech units:
    - if a segment contains multiple sentences, split and allocate times
    - adds a punctual timestamp t = midpoint of (t_start, t_end)
    """
    for _, row in segments_df.iterrows():
        t_start = float(row["start"])
        t_end = float(row["end"])
        text = str(row["text"] if "text" in row else "").strip()
        if not text:
            continue

        avg_logprob = None
        try:
            val = row.get("avg_logprob", None)
            if val is not None and not pd.isna(val):
                avg_logprob = float(val)
        except Exception:
            avg_logprob = None

        sentences = split_sentences(text)
        chunks = allocate_sentence_times(t_start, t_end, sentences)

        for sub_start, sub_end, sent in chunks:
            mid = (float(sub_start) + float(sub_end)) / 2.0
            yield {
                "t_start": round(float(sub_start), 3),
                "t_end": round(float(sub_end), 3),
                "t": round(mid, 3),
                "source": "speech",
                "event": "mention",
                "text": sent,
                "avg_logprob": avg_logprob,
            }


def write_speech_pivot_jsonl(segments_df: pd.DataFrame, out_path: Path):
    """
    Write speech events as JSONL.
    Now outputs finer-grained, 'event-like' items:
      - t_start/t_end for interval
      - t midpoint for easy alignment with vision events
      - event='mention'
    """
    ensure_dir(out_path.parent)
    with open(out_path, "w", encoding="utf-8") as f:
        for obj in iter_speech_units(segments_df):
            f.write(json.dumps(obj, ensure_ascii=False) + "\n")


def detections_to_vision_events(detection_results: Dict[str, List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
    """
    Convert per-entity boolean timeline into appear/disappear events (MVP).
    """
    events: List[Dict[str, Any]] = []
    for entity, dets in detection_results.items():
        prev = None
        for d in dets:
            cur = bool(d["present"])
            t = float(d["second"])
            if prev is None:
                prev = cur
                continue
            if (not prev) and cur:
                events.append({"t": t, "source": "vision", "event": "appear", "targets": [entity]})
            elif prev and (not cur):
                events.append({"t": t, "source": "vision", "event": "disappear", "targets": [entity]})
            prev = cur
    events.sort(key=lambda x: x["t"])
    return events


def write_vision_pivot_jsonl(detection_results: Dict[str, List[Dict[str, Any]]], out_path: Path):
    ensure_dir(out_path.parent)
    events = detections_to_vision_events(detection_results)
    with open(out_path, "w", encoding="utf-8") as f:
        for e in events:
            f.write(json.dumps(e, ensure_ascii=False) + "\n")


def segments_to_voice_txt(segments_df: pd.DataFrame, out_voice_path: Path):
    """
    Generate a voice_*.txt compatible with your existing voice_parser.py.
    Format: '(MM:SS) text...'

    Now splits segments into sentence-level lines with allocated timestamps.
    """
    ensure_dir(out_voice_path.parent)

    def to_mmss(t: float) -> str:
        t = max(0.0, float(t))
        m = int(t // 60)
        s = int(t % 60)
        return f"{m:02d}:{s:02d}"

    with open(out_voice_path, "w", encoding="utf-8") as f:
        for unit in iter_speech_units(segments_df):
            ts = to_mmss(unit["t_start"])
            text = str(unit["text"]).strip()
            if not text:
                continue
            f.write(f"({ts}) {text}\n")
