from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path


def classify_report(report: dict) -> tuple[list[tuple[str, dict]], list[tuple[str, dict]]]:
    transcript_only: list[tuple[str, dict]] = []
    suspicious_visual: list[tuple[str, dict]] = []

    transcript_entities = report.get("transcript_entities", {}) or {}
    for label, data in transcript_entities.items():
        transcript_only.append((label, data))

    for label, data in (report.get("entities", {}) or {}).items():
        sources = set(data.get("sources", []) or [])
        if not sources:
            continue
        if sources <= {"clip"} or sources <= {"clip", "discovery"}:
            suspicious_visual.append((label, data))

    # Legacy reports may still have transcript-only entities mixed into entities.
    for label, data in (report.get("entities", {}) or {}).items():
        sources = data.get("sources", []) or []
        if sources == ["transcript"]:
            transcript_only.append((label, data))

    return transcript_only, suspicious_visual


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit entity reports for weak evidence patterns.")
    parser.add_argument(
        "--reports-dir",
        default="data/entity_indexing/reports",
        help="Directory containing per-video report.json files",
    )
    args = parser.parse_args()

    reports_dir = Path(args.reports_dir)
    report_files = sorted(reports_dir.glob("*/report.json"))
    if not report_files:
        print("No reports found.")
        return 1

    totals = Counter()
    transcript_findings: list[tuple[str, str, str, list[str]]] = []
    suspicious_findings: list[tuple[str, str, str, list[str], float]] = []

    for report_file in report_files:
        report = json.loads(report_file.read_text(encoding="utf-8"))
        video_id = report.get("video_id") or report_file.parent.name
        filename = report.get("filename") or report_file.parent.name
        transcript_only, suspicious_visual = classify_report(report)
        if transcript_only:
            totals["reports_with_transcript_only"] += 1
        if suspicious_visual:
            totals["reports_with_suspicious_visual"] += 1
        for label, data in transcript_only:
            totals["transcript_only_entities"] += 1
            transcript_findings.append(
                (video_id, filename, label, data.get("sources", []) or [])
            )
        for label, data in suspicious_visual:
            totals["suspicious_visual_entities"] += 1
            suspicious_findings.append(
                (
                    video_id,
                    filename,
                    label,
                    data.get("sources", []) or [],
                    float(data.get("confidence_score", 0.0) or 0.0),
                )
            )

    print(f"reports_scanned={len(report_files)}")
    print(f"reports_with_transcript_only={totals['reports_with_transcript_only']}")
    print(f"transcript_only_entities={totals['transcript_only_entities']}")
    print(f"reports_with_suspicious_visual={totals['reports_with_suspicious_visual']}")
    print(f"suspicious_visual_entities={totals['suspicious_visual_entities']}")

    if transcript_findings:
        print("\n[transcript_only_entities]")
        for video_id, filename, label, sources in transcript_findings:
            print(f"{video_id}\t{filename}\t{label}\t{','.join(sources)}")

    if suspicious_findings:
        print("\n[suspicious_visual_entities]")
        for video_id, filename, label, sources, confidence in suspicious_findings:
            print(f"{video_id}\t{filename}\t{label}\t{','.join(sources)}\t{confidence:.4f}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
