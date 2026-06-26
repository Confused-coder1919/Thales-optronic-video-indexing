from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Bulk reprocess indexed videos with the current entity-indexing pipeline."
    )
    parser.add_argument(
        "--status",
        default="completed,failed",
        help="Comma-separated statuses to reprocess: completed,failed,queued,processing,all",
    )
    parser.add_argument(
        "--video-id",
        action="append",
        dest="video_ids",
        default=[],
        help="Restrict to one or more specific video IDs.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Maximum number of videos to queue.",
    )
    parser.add_argument(
        "--interval-sec",
        type=int,
        default=None,
        help="Override the stored frame interval for all selected videos.",
    )
    parser.add_argument(
        "--reset-label-index",
        action="store_true",
        help="Delete the cached semantic label index before reprocessing.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show which videos would be reprocessed without changing state or enqueuing tasks.",
    )
    return parser


def main() -> int:
    from backend.src.entity_indexing.celery_app import celery_app
    from backend.src.entity_indexing.db import SessionLocal, init_db
    from backend.src.entity_indexing.reprocess import (
        enqueue_reprocess_tasks,
        parse_statuses,
        reset_label_index,
        select_videos_for_reprocess,
    )

    parser = build_parser()
    args = parser.parse_args()

    statuses = parse_statuses(args.status)
    init_db()

    with SessionLocal() as session:
        videos = select_videos_for_reprocess(
            session,
            statuses=statuses,
            video_ids=args.video_ids,
            limit=args.limit,
        )

        print(
            f"Selected {len(videos)} video(s) for reprocessing "
            f"(statuses={','.join(statuses)})"
        )
        for video in videos:
            interval = args.interval_sec if args.interval_sec is not None else video.interval_sec
            print(f"- {video.id} | {video.status} | {interval}s | {video.filename}")

        if args.reset_label_index:
            index_file = Path(reset_label_index())
            print(f"Reset label index: {index_file}")

        if args.dry_run:
            print("Dry run only. No videos were re-queued.")
            return 0

        queued = enqueue_reprocess_tasks(
            session,
            videos,
            send_task=lambda name, task_args: celery_app.send_task(name, args=task_args),
            interval_sec=args.interval_sec,
            clear_outputs=True,
        )

    print(f"Queued {len(queued)} video(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
