import argparse
import csv
import os
import shutil
import yaml
from datetime import datetime, timezone
from typing import List, Dict, Optional
from faster_whisper import WhisperModel

# -----------------------------------------------------------------------------
# CONFIGURATION LOADER
# -----------------------------------------------------------------------------
def load_config(config_path: str = "backend/config/settings.yaml") -> dict:
    """Load settings from YAML configuration file."""
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Configuration file not found: {config_path}")
    
    with open(config_path, "r") as f:
        return yaml.safe_load(f)

def ensure_ffmpeg():
    if shutil.which("ffmpeg") is None:
        raise RuntimeError("ffmpeg is required. Please install it (apt install ffmpeg).")
    
def get_mission_prompt(config: dict, mission_name: str = None, location: str = None) -> str:
    """
    Builds the initial prompt from config settings with optional overrides.
    """
    mission = mission_name or config["prompts"]["default_mission"]
    loc = location or config["prompts"]["default_location"]
    military_context = config["prompts"]["military_context"]
    
    mission_context = f"Mission: {mission}. Location: {loc}. "
    return mission_context + military_context

def transcribe_audio(
    audio_path: str,
    config: dict,
    mission_name: str = None,
    location: str = None,
):
    """
    Transcribes audio with specific tuning for noisy/war environments.
    Always translates output to English.
    """
    # Load settings from config
    model_size = config["model"]["size"]
    device = config["model"]["device"]
    compute_type = config["model"]["compute_type"]
    
    # Auto-select device (GPU if available)
    if device == "auto":
        device = "cuda" if os.getenv("CUDA_VISIBLE_DEVICES") else "cpu"
        # If on CPU, force int8 to avoid errors, otherwise float16 for speed on GPU
        if device == "cpu":
            compute_type = "int8"
    
    print(f"Loading model '{model_size}' on {device}...")
    model = WhisperModel(model_size, device=device, compute_type=compute_type)

    # -------------------------------------------------------------------------
    # WAR SETTING TUNING
    # -------------------------------------------------------------------------
    trans_config = config["transcription"]
    segments_iter, info = model.transcribe(
        audio_path,
        task=trans_config["task"],
        language=trans_config["language"],
        initial_prompt=get_mission_prompt(config, mission_name, location),
        beam_size=trans_config["beam_size"],
        vad_filter=trans_config["vad_filter"],
        vad_parameters=trans_config["vad_parameters"],
        word_timestamps=trans_config["word_timestamps"],
        # Additional segmentation controls
        condition_on_previous_text=trans_config.get("condition_on_previous_text", True),
        compression_ratio_threshold=trans_config.get("compression_ratio_threshold", 2.4),
        log_prob_threshold=trans_config.get("log_prob_threshold", -1.0),
        no_speech_threshold=trans_config.get("no_speech_threshold", 0.6),
    )

    print(f"Detected Language: {info.language} (Confidence: {info.language_probability:.2f})")

    out_segments = []
    out_words = []

    for i, seg in enumerate(segments_iter):
        # Print real-time progress for the user
        print(f"[{seg.start:.2f}s -> {seg.end:.2f}s] {seg.text}")
        
        out_segments.append({
            "segment_id": i,
            "start": round(seg.start, 3),
            "end": round(seg.end, 3),
            "text": seg.text.strip(),
            "avg_logprob": getattr(seg, "avg_logprob", None),
        })
        
        if seg.words:
            for w in seg.words:
                out_words.append({
                    "segment_id": i,
                    "start": round(w.start, 3),
                    "end": round(w.end, 3),
                    "word": w.word,
                })

    return info.language, out_segments, out_words

def save_to_csv(data: List[Dict], path: str, headers: List[str]):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        writer.writerows(data)

def main():
    parser = argparse.ArgumentParser(description="War-Setting Speech to Text (Always English Output)")
    parser.add_argument("audio", help="Path to input audio file")
    parser.add_argument("--config", default="backend/config/settings.yaml", help="Path to config file")
    parser.add_argument("--out-dir", default=None, help="Output directory (overrides config)")
    parser.add_argument("--mission", default=None, help="Mission name (overrides config)")
    parser.add_argument("--location", default=None, help="Location (overrides config)")
    args = parser.parse_args()

    ensure_ffmpeg()
    
    # Load configuration
    config = load_config(args.config)

    if not os.path.isfile(args.audio):
        raise FileNotFoundError(f"File not found: {args.audio}")

    # Generate filename based on timestamp
    filename = os.path.splitext(os.path.basename(args.audio))[0]
    timestamp_format = config["output"]["timestamp_format"]
    timestamp = datetime.now(timezone.utc).strftime(timestamp_format)
    
    # Use output directory from config or command line override
    output_dir = args.out_dir or config["paths"]["output_dir"]
    job_dir = os.path.join(output_dir, f"{filename}_{timestamp}")
    
    language, segments, words = transcribe_audio(
        args.audio, 
        config, 
        mission_name=args.mission,
        location=args.location
    )

    # Save outputs based on config settings
    output_config = config["output"]
    
    if output_config["save_segments"]:
        seg_path = os.path.join(job_dir, "segments.csv")
        seg_headers = ["segment_id", "start", "end", "text", "avg_logprob"]
        save_to_csv(segments, seg_path, seg_headers)

    if output_config["save_words"]:
        word_path = os.path.join(job_dir, "words.csv")
        word_headers = ["segment_id", "start", "end", "word"]
        save_to_csv(words, word_path, word_headers)

    print(f"\n[SUCCESS] processing complete.")
    print(f"Files saved in: {job_dir}")

if __name__ == "__main__":
    main()