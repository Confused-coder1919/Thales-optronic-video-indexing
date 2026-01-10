"""
Video processing utilities for frame extraction.
"""

import cv2
import numpy as np
from typing import List, Tuple, Optional
from pathlib import Path
from backend.src.utils.extract_audio import extract_audio_from_video


def get_video_duration(video_path: str) -> float:
    """
    Get the duration of a video in seconds.
    
    Args:
        video_path: Path to the video file
        
    Returns:
        Duration in seconds
    """
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise ValueError(f"Could not open video: {video_path}")
    
    fps = cap.get(cv2.CAP_PROP_FPS)
    frame_count = cap.get(cv2.CAP_PROP_FRAME_COUNT)
    duration = frame_count / fps if fps > 0 else 0
    
    cap.release()
    return duration


def extract_frame_at_second(video_path: str, second: int) -> Optional[np.ndarray]:
    """
    Extract a single frame from the video at a specific second.
    
    Args:
        video_path: Path to the video file
        second: Second number (0-indexed)
        
    Returns:
        Frame as numpy array (BGR format), or None if extraction fails
    """
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print(f"Error: Could not open video {video_path}")
        return None
    
    fps = cap.get(cv2.CAP_PROP_FPS)
    if fps <= 0:
        print(f"Error: Invalid FPS for video {video_path}")
        cap.release()
        return None
    
    # Calculate frame number for the given second
    frame_number = int(second * fps)
    
    # Set the video position to the desired frame
    cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
    
    ret, frame = cap.read()
    cap.release()
    
    if ret:
        return frame
    else:
        print(f"Warning: Could not read frame at second {second}")
        return None


def extract_frames_at_intervals(
    video_path: str, 
    interval_seconds: int = 1
) -> List[Tuple[int, np.ndarray]]:
    """
    Extract frames from video at regular intervals.
    
    Args:
        video_path: Path to the video file
        interval_seconds: Interval between frames in seconds (default: 1)
        
    Returns:
        List of tuples (second, frame) for each extracted frame
    """
    duration = get_video_duration(video_path)
    total_seconds = int(duration)
    
    print(f"Video duration: {duration:.2f} seconds")
    print(f"Extracting frames every {interval_seconds} second(s)...")
    
    frames = []
    cap = cv2.VideoCapture(video_path)
    
    if not cap.isOpened():
        raise ValueError(f"Could not open video: {video_path}")
    
    fps = cap.get(cv2.CAP_PROP_FPS)
    
    for second in range(0, total_seconds + 1, interval_seconds):
        frame_number = int(second * fps)
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
        
        ret, frame = cap.read()
        if ret:
            frames.append((second, frame))
            if (second + 1) % 10 == 0:
                print(f"  Extracted {second + 1}/{total_seconds + 1} frames...")
        else:
            print(f"Warning: Could not read frame at second {second}")
    
    cap.release()
    print(f"Extracted {len(frames)} frames total")
    return frames


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


def extract_audio_for_stt(video_path: str, out_audio_path: str) -> str:
    """
    Extract audio from a video into backend/data/input/... using colleague helper.
    """
    Path(out_audio_path).parent.mkdir(parents=True, exist_ok=True)
    return extract_audio_from_video(video_path, out_audio_path)
