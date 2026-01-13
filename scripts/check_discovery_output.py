#!/usr/bin/env python3
"""
Smoke check for discovery-mode report output.

Usage:
  python scripts/check_discovery_output.py path/to/video_report.json
  python scripts/check_discovery_output.py path/to/video_report.json --require-discovery
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


REQUIRED_ENTITY_KEYS = {"statistics", "time_ranges", "detections"}


def load_json(path: Path) -> dict:
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def validate_report(report: dict, require_discovery: bool) -> int:
    missing = {"video", "video_path", "entities"} - set(report.keys())
    if missing:
        print(f"Missing top-level keys: {', '.join(sorted(missing))}")
        return 1

    entities = report.get("entities", {})
    if not isinstance(entities, dict) or not entities:
        print("No entities found in report.")
        return 1

    discovery_fields_seen = False
    for name, payload in entities.items():
        if not isinstance(payload, dict):
            print(f"Invalid entity payload for {name}.")
            return 1
        missing_keys = REQUIRED_ENTITY_KEYS - set(payload.keys())
        if missing_keys:
            print(f"Entity {name} missing keys: {', '.join(sorted(missing_keys))}")
            return 1

        if "source" in payload or "discovered_only" in payload:
            discovery_fields_seen = True

    if require_discovery and not discovery_fields_seen:
        print("Expected discovery fields but none were found.")
        return 1

    print("Report structure OK.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("report", help="Path to a *_report.json file.")
    parser.add_argument(
        "--require-discovery",
        action="store_true",
        help="Fail if discovery fields are not present.",
    )
    args = parser.parse_args()

    report_path = Path(args.report)
    if not report_path.exists():
        print(f"Report not found: {report_path}")
        return 1

    report = load_json(report_path)
    return validate_report(report, args.require_discovery)


if __name__ == "__main__":
    sys.exit(main())
