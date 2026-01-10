"""
Voice file parser for extracting timestamped segments from transcripts.
"""

import re
from typing import Dict, List, Tuple
from pathlib import Path


def parse_voice_file(voice_file_path: str) -> Dict[str, str]:
    """
    Parse a voice file to extract timestamped segments.
    
    Args:
        voice_file_path: Path to the voice file
        
    Returns:
        Dictionary mapping timestamps (MM:SS format) to text descriptions
    """
    with open(voice_file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Pattern to match timestamps like "Speaker 1  (00:01)" or "(01:23)"
    timestamp_pattern = r'\((\d{2}):(\d{2})\)'
    
    segments = {}
    lines = content.split('\n')
    current_timestamp = None
    current_text = []
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        # Check if line contains a timestamp
        match = re.search(timestamp_pattern, line)
        if match:
            # Save previous segment if exists
            if current_timestamp is not None and current_text:
                segments[current_timestamp] = ' '.join(current_text)
            
            # Extract timestamp
            minutes, seconds = match.groups()
            current_timestamp = f"{minutes}:{seconds}"
            current_text = []
            
            # Extract text after timestamp on the same line
            text_after_timestamp = line[match.end():].strip()
            if text_after_timestamp:
                current_text.append(text_after_timestamp)
        else:
            # Continue accumulating text for current segment
            if current_timestamp is not None:
                current_text.append(line)
    
    # Don't forget the last segment
    if current_timestamp is not None and current_text:
        segments[current_timestamp] = ' '.join(current_text)
    
    return segments


def get_all_segments(voice_file_path: str) -> List[Tuple[str, str]]:
    """
    Get all timestamped segments as a list of (timestamp, text) tuples.
    
    Args:
        voice_file_path: Path to the voice file
        
    Returns:
        List of (timestamp, text) tuples, sorted by timestamp
    """
    segments = parse_voice_file(voice_file_path)
    
    # Convert to list and sort by timestamp
    result = []
    for timestamp, text in segments.items():
        minutes, seconds = map(int, timestamp.split(':'))
        total_seconds = minutes * 60 + seconds
        result.append((timestamp, text, total_seconds))
    
    # Sort by total seconds
    result.sort(key=lambda x: x[2])
    
    return [(ts, text) for ts, text, _ in result]

