#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from backend.src.entity_indexing.dataset_exporter import (
    DatabaseAdapter,
    ExportConfig,
    FramesJsonAdapter,
    export_dataset,
)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Export COCO + YOLO datasets from existing frames/detections"
    )
    parser.add_argument(
        "--output",
        type=str,
        required=True,
        help="Output dataset directory",
    )
    parser.add_argument("--train", type=float, default=0.7, help="Train split ratio")
    parser.add_argument("--val", type=float, default=0.2, help="Val split ratio")
    parser.add_argument("--test", type=float, default=0.1, help="Test split ratio")
    parser.add_argument("--seed", type=int, default=42, help="Split random seed")
    parser.add_argument(
        "--min-confidence",
        type=float,
        default=0.0,
        help="Minimum detection confidence to include",
    )
    parser.add_argument(
        "--sources",
        type=str,
        default="",
        help="Comma-separated detection sources (yolo, clip, discovery, ocr)",
    )
    parser.add_argument(
        "--videos",
        type=str,
        default="",
        help="Comma-separated video IDs to export (default: all)",
    )
    parser.add_argument(
        "--adapter",
        choices=["auto", "json", "db"],
        default="auto",
        help="Detection source adapter",
    )
    parser.add_argument(
        "--annotated",
        action="store_true",
        help="Use annotated frames if available",
    )
    args = parser.parse_args()

    split_sum = args.train + args.val + args.test
    if abs(split_sum - 1.0) > 1e-6:
        raise SystemExit("Split ratios must sum to 1.0")

    if args.adapter == "json":
        adapter = FramesJsonAdapter()
    elif args.adapter == "db":
        adapter = DatabaseAdapter()
    else:
        json_adapter = FramesJsonAdapter()
        adapter = json_adapter if json_adapter.list_videos() else DatabaseAdapter()

    include_sources = [s.strip() for s in args.sources.split(",") if s.strip()]
    video_ids = [s.strip() for s in args.videos.split(",") if s.strip()]

    config = ExportConfig(
        output_dir=Path(args.output),
        splits=(args.train, args.val, args.test),
        seed=args.seed,
        min_confidence=args.min_confidence,
        include_sources=include_sources or None,
        use_annotated=args.annotated,
    )

    export_dataset(adapter, config, video_ids=video_ids or None)
    print(f"Dataset exported to {args.output}")


if __name__ == "__main__":
    main()
