from backend.src.entity_indexing.processing import FrameDetection, aggregate_detections, merge_time_ranges


def test_merge_time_ranges():
    ranges = merge_time_ranges([0, 5, 10, 25, 30], interval_sec=5)
    assert ranges == [
        {"start_sec": 0.0, "end_sec": 10.0},
        {"start_sec": 25.0, "end_sec": 30.0},
    ]


def test_aggregate_detections():
    frames = [
        FrameDetection(index=0, timestamp_sec=0, filename="f0.jpg", detections=[{"label": "aircraft", "confidence": 0.9}]),
        FrameDetection(index=1, timestamp_sec=5, filename="f1.jpg", detections=[{"label": "aircraft", "confidence": 0.8}]),
        FrameDetection(index=2, timestamp_sec=10, filename="f2.jpg", detections=[]),
    ]
    report = aggregate_detections(frames, duration_sec=15, interval_sec=5)
    assert report["frames_analyzed"] == 3
    assert report["unique_entities"] == 1
    assert report["entities"]["aircraft"]["count"] == 2
    assert round(report["entities"]["aircraft"]["presence"], 4) == round(2 / 3, 4)
