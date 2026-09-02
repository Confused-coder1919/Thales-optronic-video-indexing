from __future__ import annotations

import json
from pathlib import Path

import pytest

from backend.src.entity_indexing.normalize import canonicalize_label
from backend.src.entity_indexing.report_csv import generate_csv
from thales.fusion import (
    find_speech_for_time,
    fuse_speech_and_vision,
    read_jsonl,
    write_jsonl,
)


# --------------------------------------------------------------------------
# normalize.canonicalize_label
# --------------------------------------------------------------------------
@pytest.mark.parametrize(
    "raw, expected",
    [
        ("naval ship", "warship"),
        ("Naval Ship", "warship"),
        ("armoured vehicle", "military vehicle"),
        ("armored car", "military vehicle"),
        ("fighter aircraft", "fighter jet"),
        ("attack helicopter", "military helicopter"),
        ("main battle tank", "tank"),
        ("self-propelled gun", "artillery"),
        ("unmanned aerial vehicle", "drone"),
        ("APC", "military vehicle"),
        ("IFV", "military vehicle"),
        ("aircraft carriers", "aircraft carrier"),
        ("drones", "drone"),
        ("T-72", "T-72"),
        ("  warship  ", "warship"),
    ],
)
def test_canonicalize_label(raw, expected):
    assert canonicalize_label(raw) == expected


def test_canonicalize_label_unknown_keeps_lowercased_stripped():
    assert canonicalize_label("  Some Novel Entity  ") == "some novel entity"


def test_canonicalize_label_empty():
    assert canonicalize_label("") == ""


# --------------------------------------------------------------------------
# fusion: jsonl helpers + speech/vision fusion
# --------------------------------------------------------------------------
def test_read_jsonl(tmp_path: Path):
    p = tmp_path / "rows.jsonl"
    p.write_text('{"t": 1}\n\n{"t": 2}\n   \n{"t": 3}\n', encoding="utf-8")
    rows = read_jsonl(p)
    assert [r["t"] for r in rows] == [1, 2, 3]


def test_read_jsonl_missing_file_returns_empty(tmp_path: Path):
    assert read_jsonl(tmp_path / "nope.jsonl") == []


def test_write_jsonl_roundtrip(tmp_path: Path):
    p = tmp_path / "out.jsonl"
    rows = [{"t": 1.5, "text": "héllo"}, {"t": 2.0, "text": "world"}]
    write_jsonl(rows, p)
    assert read_jsonl(p) == rows


def test_find_speech_for_time():
    speech = [
        {"t_start": 0.0, "t_end": 10.0, "text": "a"},
        {"t_start": 10.0, "t_end": 20.0, "text": "b"},
    ]
    assert find_speech_for_time(speech, 5.0)["text"] == "a"
    assert find_speech_for_time(speech, 10.0)["text"] == "a"  # boundary inclusive
    assert find_speech_for_time(speech, 19.9)["text"] == "b"
    assert find_speech_for_time(speech, 25.0) is None


def test_fuse_speech_and_vision(tmp_path: Path):
    speech = tmp_path / "speech.jsonl"
    vision = tmp_path / "vision.jsonl"
    out = tmp_path / "merged.jsonl"

    write_jsonl(
        [
            {"t": 5.0, "t_start": 0.0, "t_end": 20.5, "event": "mention",
             "text": "Man walks on tank.", "avg_logprob": -0.3},
        ],
        speech,
    )
    write_jsonl(
        [
            {"t": 5.0, "event": "appear", "targets": ["military truck"]},
            {"t": 30.0, "event": "disappear", "targets": ["military truck"]},
        ],
        vision,
    )

    merged = fuse_speech_and_vision(speech, vision, out)

    sources = [m["source"] for m in merged]
    assert sources.count("speech") == 1
    assert sources.count("vision") == 2

    # vision event within the speech window carries speech context
    vision_5 = next(m for m in merged if m["source"] == "vision" and m["t"] == 5.0)
    assert vision_5["speech_context"]["text"] == "Man walks on tank."

    # vision event outside any speech window has no context
    vision_30 = next(m for m in merged if m["t"] == 30.0)
    assert vision_30["speech_context"] is None

    # output is sorted by time
    assert [m["t"] for m in merged] == sorted(m["t"] for m in merged)

    # file was written
    assert read_jsonl(out) == merged


# --------------------------------------------------------------------------
# report_csv.generate_csv
# --------------------------------------------------------------------------
def test_generate_csv_with_time_ranges(tmp_path: Path):
    report = {
        "video_id": "video_1",
        "filename": "video_1.mp4",
        "duration_sec": 60,
        "interval_sec": 5,
        "frames_analyzed": 12,
        "unique_entities": 1,
        "entities": {
            "military truck": {
                "count": 2,
                "presence": 0.1667,
                "appearances": 2,
                "confidence_score": 0.82,
                "sources": ["yolo", "clip"],
                "raw_count": 4,
                "time_ranges": [
                    {"start_sec": 5.0, "end_sec": 10.0, "start_label": "00:05", "end_label": "00:10"},
                    {"start_sec": 25.0, "end_sec": 30.0, "start_label": "00:25", "end_label": "00:30"},
                ],
            }
        },
    }
    out = tmp_path / "report.csv"
    assert generate_csv(report, out) is True

    rows = list(__import__("csv").reader(out.open(encoding="utf-8")))
    header = rows[0]
    assert header[0] == "video_id"
    assert header[6] == "entity"
    # one data row per time range
    data_rows = rows[1:]
    assert len(data_rows) == 2
    assert all(r[6] == "military truck" for r in data_rows)
    assert [r[15] for r in data_rows] == ["5.0", "25.0"]  # start_sec
    assert [r[16] for r in data_rows] == ["10.0", "30.0"]  # end_sec
    # presence_pct = presence * 100, rounded
    assert data_rows[0][9] == "16.67"


def test_generate_csv_no_time_ranges_single_row(tmp_path: Path):
    report = {
        "video_id": "video_1",
        "entities": {
            "drone": {"count": 1, "presence": 0.1, "appearances": 1,
                      "sources": [], "time_ranges": []}
        },
    }
    out = tmp_path / "report.csv"
    assert generate_csv(report, out) is True
    rows = list(__import__("csv").reader(out.open(encoding="utf-8")))
    assert len(rows) == 2  # header + one data row
    assert rows[1][6] == "drone"
