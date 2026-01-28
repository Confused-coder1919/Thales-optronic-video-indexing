import os
import subprocess
import tempfile
import wave
from typing import Dict, Optional


def _run_ffmpeg(command: list) -> None:
    subprocess.run(command, check=True)


def _build_output_path(input_path: str, suffix: str, ext: str = ".wav") -> str:
    base, _ = os.path.splitext(input_path)
    return f"{base}{suffix}{ext}"


def cleanup_audio_for_transcription(
    audio_path: str,
    output_audio_path: Optional[str] = None,
    ffmpeg_filter: Optional[str] = None,
) -> str:
    """
    Apply basic noise suppression + EQ to improve transcription quality.
    Returns path to cleaned audio.
    """
    if not os.path.exists(audio_path):
        raise FileNotFoundError(f"Audio file not found: {audio_path}")

    if output_audio_path is None:
        output_audio_path = _build_output_path(audio_path, "_clean")

    # Basic cleanup: high-pass + low-pass + spectral noise reduction
    filter_chain = ffmpeg_filter or "highpass=f=200,lowpass=f=3000,afftdn=nf=-25"

    command = [
        "ffmpeg",
        "-i",
        audio_path,
        "-vn",
        "-ac",
        "1",
        "-ar",
        "16000",
        "-af",
        filter_chain,
        "-y",
        "-loglevel",
        "error",
        output_audio_path,
    ]

    print(f"Cleaning audio: {audio_path} -> {output_audio_path}")
    _run_ffmpeg(command)
    return output_audio_path


def _ensure_pcm_wav(audio_path: str) -> str:
    if audio_path.lower().endswith(".wav"):
        return audio_path

    handle = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
    handle.close()
    wav_path = handle.name
    command = [
        "ffmpeg",
        "-i",
        audio_path,
        "-vn",
        "-ac",
        "1",
        "-ar",
        "16000",
        "-acodec",
        "pcm_s16le",
        "-y",
        "-loglevel",
        "error",
        wav_path,
    ]
    _run_ffmpeg(command)
    return wav_path


def analyze_speech_ratio(
    audio_path: str,
    vad_mode: int = 2,
    frame_ms: int = 30,
    speech_threshold: float = 0.1,
) -> Dict[str, object]:
    """
    Estimate speech presence using WebRTC VAD.
    Returns speech_ratio and music_detected (True if little speech).
    """
    try:
        import webrtcvad
    except Exception:
        return {
            "speech_ratio": None,
            "music_detected": None,
            "speech_seconds": None,
            "vad_available": False,
        }

    wav_path = _ensure_pcm_wav(audio_path)
    cleanup_temp = wav_path != audio_path

    try:
        vad = webrtcvad.Vad(vad_mode)
        with wave.open(wav_path, "rb") as wav_file:
            sample_rate = wav_file.getframerate()
            if wav_file.getnchannels() != 1 or wav_file.getsampwidth() != 2:
                raise RuntimeError("Audio must be mono 16-bit PCM for VAD.")

            frame_samples = int(sample_rate * frame_ms / 1000)
            frame_bytes = frame_samples * 2

            total_frames = 0
            speech_frames = 0
            while True:
                frame = wav_file.readframes(frame_samples)
                if len(frame) < frame_bytes:
                    break
                total_frames += 1
                if vad.is_speech(frame, sample_rate):
                    speech_frames += 1

        speech_ratio = speech_frames / total_frames if total_frames else 0.0
        speech_seconds = round((speech_frames * frame_ms) / 1000.0, 2)
        return {
            "speech_ratio": round(speech_ratio, 4),
            "speech_seconds": speech_seconds,
            "music_detected": speech_ratio < speech_threshold,
            "vad_available": True,
        }
    finally:
        if cleanup_temp:
            try:
                os.remove(wav_path)
            except OSError:
                pass

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
        "-i",
        video_path,
        "-vn",
        "-ac",
        "1",
        "-ar",
        "16000",
        "-y",
        "-loglevel",
        "error",
        output_audio_path,
    ]

    print(f"Extracting audio: {video_path} -> {output_audio_path}")

    _run_ffmpeg(command)
    return output_audio_path
