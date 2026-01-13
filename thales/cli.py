"""
Command-line interface for the Thales entity detection pipeline.
"""

import argparse
from pathlib import Path
from typing import List

from thales.config import DEFAULT_FRAME_INTERVAL, DEFAULT_OUTPUT_DIR, get_project_root

VIDEO_EXTS = (".mp4", ".mkv", ".avi", ".mov")
from thales.entity_detector import process_video_with_voice
from thales.report_generator import generate_report, generate_summary_report

from thales.stt_runner import run_stt, load_segments
from thales.pivot import write_speech_pivot_jsonl, write_vision_pivot_jsonl, segments_to_voice_txt
from thales.video_processor import extract_audio_for_stt

from thales.fusion import fuse_speech_and_vision


def find_videos(directory: str = ".") -> List[Path]:
    """Find video_*.{mp4,mkv,avi,mov} files in a directory."""
    base = Path(directory)
    candidates = []
    for ext in VIDEO_EXTS:
        candidates.extend(base.glob(f"video_*{ext}"))
    return sorted(set(candidates))


def process_all_videos(
    directory: str = ".",
    output_dir: str = DEFAULT_OUTPUT_DIR,
    interval_seconds: int = DEFAULT_FRAME_INTERVAL,
    export_csv: bool = False,
):
    print("=" * 60)
    print("Thales - STT + Vision Entity Detection Pipeline")
    print("=" * 60)

    videos = find_videos(directory)
    if not videos:
        print(f"No video_*.mp4 found in: {directory}")
        return

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    pivot_dir = output_path / "pivot"
    pivot_dir.mkdir(parents=True, exist_ok=True)

    all_reports = []

    for i, video in enumerate(videos, 1):
        video_path = str(video)
        stem = video.stem  # video_1
        try:
            number = stem.split("_")[1]
        except Exception:
            print(f"Skipping unexpected filename: {video.name} (expected video_<n>.mp4)")
            continue

        print("\n" + "=" * 60)
        print(f"Processing {i}/{len(videos)}: {video.name}")
        print("=" * 60)

        # 1) Extract audio for STT
        audio_out = Path("backend/data/input") / f"audio_{number}.m4a"
        audio_out.parent.mkdir(parents=True, exist_ok=True)
        extract_audio_for_stt(video_path, str(audio_out))

        # 2) Run STT
        job_dir = run_stt(str(audio_out))
        segments_df = load_segments(job_dir)

        # 3) Pivot speech (jsonl)
        speech_pivot_path = pivot_dir / f"{stem}_speech.jsonl"
        write_speech_pivot_jsonl(segments_df, speech_pivot_path)

        # 4) Generate voice_N.txt for ITT pipeline
        voice_path = Path("data") / f"voice_{number}.txt"
        voice_path.parent.mkdir(parents=True, exist_ok=True)
        segments_to_voice_txt(segments_df, voice_path)

        # 5) Run ITT (your existing vision pipeline)
        detection_results = process_video_with_voice(
            video_path,
            str(voice_path),
            interval_seconds=interval_seconds,
        )
        entity_metadata = None
        if isinstance(detection_results, tuple):
            detection_results, entity_metadata = detection_results

        if not detection_results:
            print(f"Warning: no detection results for {video.name}")
            continue

        # 6) Save report
        report_path = output_path / f"{stem}_report.json"
        report = generate_report(
            video_path,
            detection_results,
            str(report_path),
            entity_metadata=entity_metadata,
        )
        all_reports.append(report)

        # 7) Pivot vision (jsonl)
        vision_pivot_path = pivot_dir / f"{stem}_vision.jsonl"
        write_vision_pivot_jsonl(detection_results, vision_pivot_path)

        # 8) Fuse speech and vision pivots
        merged_path = pivot_dir / f"{stem}_merged.jsonl"
        fuse_speech_and_vision(speech_pivot_path, vision_pivot_path, merged_path)
        print(f"✅ Merged timeline saved to: {merged_path}")


        # Quick console summary
        print(f"\nSaved report: {report_path}")
        print("Entities found:")
        for entity, data in report["entities"].items():
            stats = data["statistics"]
            print(
                f"  - {entity}: {stats['frames_with_entity']}/{stats['total_frames_analyzed']} "
                f"({stats['presence_percentage']:.1f}%)"
            )

    # Summary report
    if all_reports:
        summary_path = output_path / "summary_report.json"
        summary = generate_summary_report(all_reports, str(summary_path))
        print("\n" + "=" * 60)
        print(f"Summary saved: {summary_path}")
        print(f"Processed {summary['total_videos']} video(s)")
        print(f"Unique entities: {summary['unique_entity_count']}")
        print("=" * 60)

    if export_csv:
        try:
            from thales.postprocess import generate_thales_csv

            csv_path = output_path / "thales_metadata.csv"
            generated = generate_thales_csv(pivot_dir, csv_path, get_project_root())
            if generated:
                print(f"Thales CSV generated: {generated}")
            else:
                print("Warning: No merged pivot files; CSV not generated.")
        except Exception as e:
            print(f"Warning: CSV export failed: {e}")

    print("\nDone ✅")


def main():
    parser = argparse.ArgumentParser(
        description="Thales - Process videos with STT + vision detection",
    )
    parser.add_argument("--directory", "-d", default="data", help="Directory containing video_*.mp4")
    parser.add_argument("--output", "-o", default=DEFAULT_OUTPUT_DIR, help="Output directory for reports")
    parser.add_argument("--interval", "-i", type=int, default=DEFAULT_FRAME_INTERVAL, help="Frame interval (seconds)")
    parser.add_argument(
        "--export-csv",
        action="store_true",
        help="Export Thales CSV from pivot outputs",
    )
    args = parser.parse_args()

    process_all_videos(args.directory, args.output, args.interval, export_csv=args.export_csv)


if __name__ == "__main__":
    main()
