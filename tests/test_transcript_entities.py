from backend.src.entity_indexing.transcript_entities import (
    extract_labels_from_text,
    extract_transcript_mentions,
    load_voice_segments,
    merge_transcript_entities,
)


def test_extract_labels_from_translated_text_is_explicit_and_conservative():
    labels = extract_labels_from_text(
        "Pakistan's military says missiles engaged targets while drones flew nearby."
    )
    assert "missile" in labels
    assert "drone" in labels
    assert "military personnel" not in labels


def test_extract_transcript_mentions_prefers_translated_segments():
    transcript_payload = {
        "language": "ur",
        "segments": [{"start": 0.0, "end": 3.0, "text": "اصل اردو"}],
        "translated_segments": [
            {"start": 0.0, "end": 3.0, "text": "Two missiles struck the target."}
        ],
    }

    mentions = extract_transcript_mentions(transcript_payload, duration_sec=20.0)

    assert mentions == {"missile": [(0.0, 3.0)]}


def test_load_voice_segments_parses_timestamped_text(tmp_path):
    voice = tmp_path / "voice.txt"
    voice.write_text("(00:05) fighter jets inbound\n(00:12) military trucks arriving\n")

    segments = load_voice_segments(voice, duration_sec=30.0)

    assert segments == [
        {"start": 5.0, "text": "fighter jets inbound", "end": 12.0},
        {"start": 12.0, "text": "military trucks arriving", "end": 30.0},
    ]


def test_merge_transcript_entities_adds_transcript_source():
    report = {
        "duration_sec": 60.0,
        "interval_sec": 5,
        "frames_analyzed": 12,
        "unique_entities": 0,
        "entities": {},
    }

    merged = merge_transcript_entities(
        report,
        {"missile": [(2.0, 8.0)], "truck": [(10.0, 16.0)]},
        duration_sec=60.0,
    )

    assert merged["entities"] == {}
    assert sorted(merged["transcript_entities"].keys()) == ["missile", "truck"]
    assert merged["transcript_entities"]["missile"]["sources"] == ["transcript"]
    assert merged["transcript_entities"]["missile"]["time_ranges"][0]["start_label"] == "00:02"


def test_merge_transcript_entities_marks_visual_entities_without_extending_visual_ranges():
    report = {
        "duration_sec": 60.0,
        "interval_sec": 5,
        "frames_analyzed": 12,
        "unique_entities": 1,
        "entities": {
            "missile": {
                "count": 2,
                "presence": 0.2,
                "appearances": 2,
                "time_ranges": [{"start_sec": 20.0, "end_sec": 25.0, "start_label": "00:20", "end_label": "00:25"}],
                "raw_count": 2,
                "confidence_score": 0.5,
                "sources": ["verify"],
            }
        },
    }

    merged = merge_transcript_entities(
        report,
        {"missile": [(2.0, 8.0)]},
        duration_sec=60.0,
    )

    assert merged["entities"]["missile"]["sources"] == ["verify"]
    assert merged["entities"]["missile"]["time_ranges"] == [
        {"start_sec": 20.0, "end_sec": 25.0, "start_label": "00:20", "end_label": "00:25"}
    ]
    assert merged["entities"]["missile"]["mentioned_in_transcript"] is True
    assert merged["entities"]["missile"]["transcript_time_ranges"][0]["start_label"] == "00:02"
    assert merged["transcript_entities"] == {}
