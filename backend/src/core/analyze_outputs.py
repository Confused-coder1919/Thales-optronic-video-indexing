import argparse
import os
import json
import yaml
import pandas as pd
import numpy as np

# -----------------------------------------------------------------------------
# CONFIGURATION LOADER
# -----------------------------------------------------------------------------
def load_config(config_path: str = "backend/config/settings.yaml") -> dict:
    """Load settings from YAML configuration file."""
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Configuration file not found: {config_path}")
    
    with open(config_path, "r") as f:
        return yaml.safe_load(f)

# -----------------------------------------------------------------------------
# INTELLIGENCE DICTIONARIES
# -----------------------------------------------------------------------------
# These lists allow us to "tag" the audio with specific alert levels.
THREAT_TERMS = ["enemy", "hostile", "ied", "contact", "fire", "rifle", "armed", "sniper", "ambush", "casualty"]
PROCEDURE_TERMS = ["roger", "copy", "solid", "break", "over", "out", "repeat", "wilco"]
ASSET_TERMS = ["uav", "drone", "helo", "bird", "convoy", "alpha", "bravo", "extract"]

def load_data(folder):
    """Safely loads the segments CSV from a job folder."""
    path = os.path.join(folder, "segments.csv")
    if not os.path.exists(path):
        return pd.DataFrame() # Return empty if processing failed
    return pd.read_csv(path)

def generate_intel_report(df: pd.DataFrame, config: dict):
    if df.empty:
        return {"status": "NO_DATA", "risk_level": "UNKNOWN"}

    # Load thresholds from config
    low_conf_threshold = config["analysis"]["low_confidence_threshold"]
    expected_jargon = config["analysis"]["expected_jargon"]

    # SIGNAL INTEGRITY (0-100%)
    # Whisper's 'avg_logprob' usually ranges from 0 (perfect) to -1 (good) to -5 (bad).
    # We map this to a percentage for the client.
    raw_confidence = df["avg_logprob"].mean()
    # Math: map -2.0 to 0.0 logprob into a 0-100 score. 
    # Any logprob < -2 is considered "0% quality" (garbage audio).
    is_low_confidence = bool(raw_confidence < low_conf_threshold)  # Convert to Python bool
    integrity_score = max(0, min(100, (1.0 + (raw_confidence / 2.0)) * 100))

    # ACTIVITY ANALYSIS
    # Calculate "Words Per Minute" to detect panic or urgency.
    total_duration = df["end"].max() - df["start"].min()
    total_words = df["text"].str.split().str.len().sum()
    wpm = (total_words / (total_duration / 60)) if total_duration > 0 else 0

    # CONTENT MINING
    # We scan the full text for our keywords
    full_text = " ".join(df["text"].astype(str)).lower()
    
    threats_detected = [t for t in THREAT_TERMS if t in full_text]
    threat_level = "LOW"
    if "critical" in threats_detected or "enemy" in threats_detected:
        threat_level = "CRITICAL"
    elif len(threats_detected) >= 3:
        threat_level = "HIGH"
    elif len(threats_detected) > 0:
        threat_level = "MEDIUM" 
    assets_detected = [a for a in ASSET_TERMS if a in full_text]
    jargon_detected = [j for j in expected_jargon if j in full_text]
    
    # COMMS DISCIPLINE SCORE
    # How many "procedure words" per 100 words? 
    # Professional soldiers use >5%. Civilians use <1%.
    proc_count = sum(full_text.count(p) for p in PROCEDURE_TERMS)
    discipline_score = "LOW (Civilian?)"
    if total_words > 0:
        ratio = proc_count / total_words
        if ratio > 0.05: discipline_score = "HIGH (Professional)"
        elif ratio > 0.02: discipline_score = "MEDIUM (Militia/Trained)"

    # -------------------------------------------------------------------------
    # CLIENT OUTPUT ( The "SITREP" )
    # -------------------------------------------------------------------------
    # ... inside generate_intel_report ...
    return {
        "meta": {
            "duration_sec": round(total_duration, 1),
            "total_words": int(total_words)
        },
        "signal_intelligence": {
            "integrity_score": int(integrity_score),
            "confidence_alert": is_low_confidence
        },
        "tactical_intelligence": {
            "threat_level": threat_level,
            "threats_detected": list(set(threats_detected)), 
            "jargon_hit_rate": f"{len(jargon_detected)}/{len(expected_jargon)}",
            "jargon_found": list(set(jargon_detected)),
            "discipline": discipline_score
        }
    }

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("job_folder", help="Path to the processed job folder")
    parser.add_argument("--config", default="backend/config/settings.yaml", help="Path to config file")
    args = parser.parse_args()

    config = load_config(args.config)
    df = load_data(args.job_folder)
    report = generate_intel_report(df, config)

    # Save as specific "SITREP" file for the Frontend to read
    output_path = os.path.join(args.job_folder, "sitrep.json")
    with open(output_path, "w") as f:
        json.dump(report, f, indent=2)

    print(json.dumps(report, indent=2))

if __name__ == "__main__":
    main()