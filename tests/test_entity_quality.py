from pathlib import Path

import pytest

pytest.importorskip("cv2")
pytest.importorskip("PIL")
pytest.importorskip("torch")

from backend.src.entity_indexing.discovery import extract_entities_from_caption
from backend.src.entity_indexing.normalize import canonicalize_label
from backend.src.entity_indexing.processing import (
    FrameDetection,
    aggregate_detections,
    annotate_frame,
    normalize_detections,
    prune_unverified_candidate_detections,
)


def test_canonicalize_label_rejects_caption_noise():
    assert canonicalize_label("jacket standing") == ""
    assert canonicalize_label("smoke coming out") == ""
    assert canonicalize_label("military") == ""
    assert canonicalize_label("bird flying over") == ""


def test_canonicalize_label_normalizes_structured_entities():
    assert canonicalize_label("soldier standing") == "military personnel"
    assert canonicalize_label("fighter jet flying") == "fighter jet"
    assert canonicalize_label("military plane") == "aircraft"
    assert canonicalize_label("truck") == "truck"
    assert canonicalize_label("person") == "person"


def test_extract_entities_from_caption_returns_controlled_entities_only():
    labels = extract_entities_from_caption(
        "a soldier standing near a fighter jet over a cloudy sky"
    )
    assert "military personnel" in labels
    assert "fighter jet" in labels
    assert "soldier standing" not in labels
    assert "cloudy sky" not in labels


def test_normalize_detections_drops_invalid_labels():
    detections = normalize_detections(
        [
            {"label": "jacket standing", "source": "discovery", "confidence": 0.5},
            {"label": "fighter jet flying", "source": "discovery", "confidence": 0.5},
            {"label": "AAB960A", "source": "ocr", "confidence": 0.9},
        ]
    )
    assert [det["label"] for det in detections] == ["fighter jet", "AAB960A"]


def test_prune_unverified_candidate_labels_drop_unconfirmed_discovery_and_clip_noise():
    frames = [
        FrameDetection(
            index=0,
            timestamp_sec=0.0,
            filename="f0.jpg",
            detections=[
                {"label": "fighter jet", "source": "discovery", "confidence": 0.5},
                {"label": "warship", "source": "clip", "confidence": 0.4},
                {"label": "vehicle", "source": "yolo", "confidence": 0.8},
            ],
        )
    ]

    prune_unverified_candidate_detections(frames, verified_labels=set())

    assert frames[0].detections == [{"label": "vehicle", "source": "yolo", "confidence": 0.8}]


def test_prune_unverified_candidate_labels_keeps_verified_clip_labels():
    frames = [
        FrameDetection(
            index=0,
            timestamp_sec=0.0,
            filename="f0.jpg",
            detections=[
                {"label": "fighter jet", "source": "clip", "confidence": 0.5},
            ],
        )
    ]

    prune_unverified_candidate_detections(frames, verified_labels={"fighter jet"})

    assert frames[0].detections == [{"label": "fighter jet", "source": "clip", "confidence": 0.5}]


def test_annotate_frame_without_detections_creates_parent_dir(tmp_path):
    src = tmp_path / "frame.jpg"
    src.write_bytes(b"fake-jpg")
    out = tmp_path / "annotated" / "frame.jpg"

    annotate_frame(src, [], out)

    assert out.read_bytes() == b"fake-jpg"


def test_aggregate_detections_keeps_sparse_verify_and_ocr_hits():
    frames = [
        FrameDetection(index=0, timestamp_sec=0.0, filename="f0.jpg", detections=[]),
        FrameDetection(
            index=1,
            timestamp_sec=5.0,
            filename="f1.jpg",
            detections=[{"label": "missile", "source": "verify", "confidence": 0.4}],
        ),
        FrameDetection(
            index=2,
            timestamp_sec=10.0,
            filename="f2.jpg",
            detections=[{"label": "missile", "source": "ocr", "confidence": 0.9}],
        ),
        FrameDetection(
            index=3,
            timestamp_sec=15.0,
            filename="f3.jpg",
            detections=[{"label": "missile", "source": "verify", "confidence": 0.4}],
        ),
    ]

    report = aggregate_detections(frames, duration_sec=20.0, interval_sec=5)

    assert "missile" in report["entities"]
    assert set(report["entities"]["missile"]["sources"]) == {"ocr", "verify"}
