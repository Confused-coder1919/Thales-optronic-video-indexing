from __future__ import annotations

import csv
from pathlib import Path
from typing import Dict


def generate_csv(report: Dict, output_path: Path) -> bool:
    try:
        meta = {
            "video_id": report.get("video_id", ""),
            "filename": report.get("filename", ""),
            "duration_sec": report.get("duration_sec", ""),
            "interval_sec": report.get("interval_sec", ""),
            "frames_analyzed": report.get("frames_analyzed", ""),
            "unique_entities": report.get("unique_entities", ""),
        }
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with output_path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.writer(handle)
            writer.writerow(
                [
                    "video_id",
                    "filename",
                    "duration_sec",
                    "interval_sec",
                    "frames_analyzed",
                    "unique_entities",
                    "entity",
                    "count",
                    "presence",
                    "presence_pct",
                    "appearances",
                    "range_index",
                    "start_sec",
                    "end_sec",
                    "start_label",
                    "end_label",
                    "range_duration_sec",
                ]
            )
            entities = report.get("entities", {}) or {}
            for label, data in entities.items():
                count = data.get("count", 0)
                presence = data.get("presence", 0.0)
                appearances = data.get("appearances", 0)
                ranges = data.get("time_ranges", []) or []
                if not ranges:
                    writer.writerow(
                        [
                            meta["video_id"],
                            meta["filename"],
                            meta["duration_sec"],
                            meta["interval_sec"],
                            meta["frames_analyzed"],
                            meta["unique_entities"],
                            label,
                            count,
                            presence,
                            round(float(presence) * 100, 2) if presence != "" else "",
                            appearances,
                            "",
                            "",
                            "",
                            "",
                            "",
                            "",
                        ]
                    )
                else:
                    for idx, item in enumerate(ranges, 1):
                        start_sec = item.get("start_sec", "")
                        end_sec = item.get("end_sec", "")
                        interval = report.get("interval_sec", 0) or 0
                        duration = ""
                        if start_sec != "" and end_sec != "":
                            duration = round(float(end_sec) - float(start_sec) + float(interval), 2)
                        writer.writerow(
                            [
                                meta["video_id"],
                                meta["filename"],
                                meta["duration_sec"],
                                meta["interval_sec"],
                                meta["frames_analyzed"],
                                meta["unique_entities"],
                                label,
                                count,
                                presence,
                                round(float(presence) * 100, 2) if presence != "" else "",
                                appearances,
                                idx,
                                start_sec,
                                end_sec,
                                item.get("start_label", ""),
                                item.get("end_label", ""),
                                duration,
                            ]
                        )
        return True
    except Exception:
        return False
