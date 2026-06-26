from pathlib import Path
from types import SimpleNamespace

from backend.src.entity_indexing.reprocess import (
    enqueue_reprocess_tasks,
    parse_statuses,
    reset_video_for_reprocess,
)


def test_parse_statuses_defaults_and_all():
    assert parse_statuses("") == ["completed", "failed"]
    assert parse_statuses("all") == ["completed", "failed", "processing", "queued"]


def test_reset_video_for_reprocess_clears_state():
    video = SimpleNamespace(
        id="vid-1",
        status="completed",
        progress=100.0,
        current_stage="completed",
        duration_sec=33.0,
        frames_analyzed=6,
        unique_entities=3,
        entities_json='{"missile": {}}',
        report_path="/tmp/report.json",
        frames_path="/tmp/frames",
        original_path="/tmp/video.mp4",
        error="old error",
        interval_sec=30,
    )

    reset_video_for_reprocess(video, interval_sec=5)

    assert video.status == "queued"
    assert video.progress == 0.0
    assert video.current_stage == "queued"
    assert video.duration_sec is None
    assert video.frames_analyzed is None
    assert video.unique_entities is None
    assert video.entities_json is None
    assert video.report_path is None
    assert video.frames_path is None
    assert video.error is None
    assert video.interval_sec == 5


def test_enqueue_reprocess_tasks_clears_outputs_and_sends_tasks(tmp_path, monkeypatch):
    frames_root = tmp_path / "frames"
    reports_root = tmp_path / "reports"
    monkeypatch.setattr("backend.src.entity_indexing.reprocess.FRAMES_DIR", frames_root)
    monkeypatch.setattr("backend.src.entity_indexing.reprocess.REPORTS_DIR", reports_root)

    video = SimpleNamespace(
        id="vid-2",
        filename="sample.mp4",
        status="completed",
        progress=100.0,
        current_stage="completed",
        duration_sec=20.0,
        frames_analyzed=4,
        unique_entities=1,
        entities_json='{"truck": {}}',
        report_path="report.json",
        frames_path="frames",
        original_path=str(tmp_path / "video.mp4"),
        error=None,
        interval_sec=30,
    )
    Path(video.original_path).write_bytes(b"video")
    (frames_root / video.id).mkdir(parents=True)
    (reports_root / video.id).mkdir(parents=True)
    (frames_root / video.id / "frame.jpg").write_bytes(b"frame")
    (reports_root / video.id / "report.json").write_text("{}")

    calls = []

    class DummySession:
        def __init__(self) -> None:
            self.added = []
            self.committed = 0

        def add(self, item) -> None:
            self.added.append(item)

        def commit(self) -> None:
            self.committed += 1

    session = DummySession()

    queued = enqueue_reprocess_tasks(
        session,
        [video],
        send_task=lambda name, args: calls.append((name, args)),
        interval_sec=5,
        clear_outputs=True,
    )

    assert queued == [
        {
            "video_id": "vid-2",
            "filename": "sample.mp4",
            "interval_sec": 5,
            "original_path": str(tmp_path / "video.mp4"),
        }
    ]
    assert session.committed == 1
    assert calls == [
        (
            "entity_indexing.process_video",
            ["vid-2", str(tmp_path / "video.mp4"), 5],
        )
    ]
    assert not (frames_root / video.id).exists()
    assert not (reports_root / video.id).exists()
