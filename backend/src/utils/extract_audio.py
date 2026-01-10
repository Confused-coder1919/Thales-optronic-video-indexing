import subprocess
import os

def extract_audio_from_video(video_path: str, output_audio_path: str = None) -> str:
    """
    Extracts audio track from a video file using FFmpeg.
    Returns the path to the extracted audio file.
    """
    if not os.path.exists(video_path):
        raise FileNotFoundError(f"Video file not found: {video_path}")

    # If no output path is provided, save it next to the video with .m4a extension
    if output_audio_path is None:
        base, _ = os.path.splitext(video_path)
        output_audio_path = f"{base}.m4a"

    # FFmpeg command:
    # -i input_video  : Input file
    # -vn             : No Video (discard video stream)
    # -acodec copy    : Copy audio stream without re-encoding (FASTEST)
    # -y              : Overwrite output file if it exists
    # -loglevel error : Suppress logs unless it's an error
    command = [
        "ffmpeg",
        "-i", video_path,
        "-vn",
        "-acodec", "copy", 
        "-y",
        "-loglevel", "error",
        output_audio_path
    ]

    print(f"Extracting audio: {video_path} -> {output_audio_path}")
    
    try:
        subprocess.run(command, check=True)
        return output_audio_path
    except subprocess.CalledProcessError as e:
        # Fallback: Sometimes 'copy' fails if the container is weird. 
        # Try converting to mp3 explicitly.
        print("Direct copy failed, re-encoding to mp3...")
        fallback_path = output_audio_path.replace(".m4a", ".mp3")
        subprocess.run([
            "ffmpeg", "-i", video_path, "-vn", "-acodec", "libmp3lame", "-y", fallback_path
        ], check=True)
        return fallback_path