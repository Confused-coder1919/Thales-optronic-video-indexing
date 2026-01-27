import subprocess
import os

def extract_audio_from_video(video_path: str, output_audio_path: str = None) -> str:
    """
    Extracts audio track from a video file using FFmpeg.
    Returns the path to the extracted audio file.
    """
    if not os.path.exists(video_path):
        raise FileNotFoundError(f"Video file not found: {video_path}")

    # Default to WAV (16kHz, mono) for Whisper reliability
    if output_audio_path is None:
        base, _ = os.path.splitext(video_path)
        output_audio_path = f"{base}.wav"

    command = [
        "ffmpeg",
        "-i", video_path,
        "-vn",
        "-ac", "1",
        "-ar", "16000",
        "-y",
        "-loglevel", "error",
        output_audio_path
    ]

    print(f"Extracting audio: {video_path} -> {output_audio_path}")

    subprocess.run(command, check=True)
    return output_audio_path
