"""
Report generation for entity detection results.
"""

import json
from typing import Dict, List, Any
from pathlib import Path


def seconds_to_timestamp(seconds: int) -> str:
    """
    Convert seconds to MM:SS timestamp format.
    
    Args:
        seconds: Number of seconds
        
    Returns:
        Timestamp string in MM:SS format
    """
    minutes = seconds // 60
    secs = seconds % 60
    return f"{minutes:02d}:{secs:02d}"


def generate_report(
    video_path: str,
    detection_results: Dict[str, List[Dict[str, Any]]],
    output_path: str = None,
    entity_metadata: Dict[str, Dict[str, Any]] | None = None,
) -> Dict:
    """
    Generate a JSON report from detection results.
    
    Args:
        video_path: Path to the video file
        detection_results: Dictionary mapping entity names to detection lists
        output_path: Optional path to save the report JSON file
        entity_metadata: Optional per-entity metadata (e.g., source/discovered_only)
        
    Returns:
        Dictionary containing the report data
    """
    video_name = Path(video_path).name
    
    report = {
        "video": video_name,
        "video_path": str(video_path),
        "entities": {}
    }
    
    for entity, detections in detection_results.items():
        present_detections = [d for d in detections if d['present']]
        
        total_frames = len(detections)
        present_frames = len(present_detections)
        presence_percentage = (present_frames / total_frames * 100) if total_frames > 0 else 0
        
        # Calculate time ranges where entity is present
        time_ranges = []
        if present_detections:
            current_range_start = None
            current_range_end = None
            
            for det in detections:
                if det['present']:
                    if current_range_start is None:
                        current_range_start = det['second']
                    current_range_end = det['second']
                else:
                    if current_range_start is not None:
                        time_ranges.append({
                            "start": seconds_to_timestamp(current_range_start),
                            "end": seconds_to_timestamp(current_range_end),
                            "start_second": current_range_start,
                            "end_second": current_range_end,
                            "duration_seconds": current_range_end - current_range_start + 1
                        })
                        current_range_start = None
                        current_range_end = None
            
            if current_range_start is not None:
                time_ranges.append({
                    "start": seconds_to_timestamp(current_range_start),
                    "end": seconds_to_timestamp(current_range_end),
                    "start_second": current_range_start,
                    "end_second": current_range_end,
                    "duration_seconds": current_range_end - current_range_start + 1
                })
        
        entity_payload: Dict[str, Any] = {
            "statistics": {
                "total_frames_analyzed": total_frames,
                "frames_with_entity": present_frames,
                "presence_percentage": round(presence_percentage, 2)
            },
            "time_ranges": time_ranges,
            "detections": detections
        }
        if entity_metadata:
            metadata = entity_metadata.get(entity)
            if metadata:
                if "source" in metadata:
                    entity_payload["source"] = metadata["source"]
                if "discovered_only" in metadata:
                    entity_payload["discovered_only"] = metadata["discovered_only"]

        report["entities"][entity] = entity_payload
    
    if output_path:
        output_dir = Path(output_path).parent
        output_dir.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print(f"Report saved to: {output_path}")
    
    return report


def generate_summary_report(reports: List[Dict], output_path: str = None) -> Dict:
    """
    Generate a summary report combining multiple video reports.
    
    Args:
        reports: List of individual video reports
        output_path: Optional path to save the summary report
        
    Returns:
        Dictionary containing the summary report
    """
    summary = {
        "total_videos": len(reports),
        "videos": []
    }
    
    all_entities = set()
    for report in reports:
        all_entities.update(report["entities"].keys())
        summary["videos"].append({
            "video": report["video"],
            "entities_detected": list(report["entities"].keys()),
            "entity_count": len(report["entities"])
        })
    
    summary["all_entities"] = sorted(list(all_entities))
    summary["unique_entity_count"] = len(all_entities)
    
    if output_path:
        output_dir = Path(output_path).parent
        output_dir.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
        
        print(f"Summary report saved to: {output_path}")
    
    return summary
