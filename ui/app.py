import base64
import json
import os
import re
import shutil
import sys
import time
from collections import Counter
from datetime import datetime
from pathlib import Path

import pandas as pd
import streamlit as st
from dotenv import load_dotenv
import yaml

from utils import ALLOWED_VIDEO_EXTS, find_videos, run_pipeline

try:
    from thales.config import MISTRAL_MODEL, PIXTRAL_MODEL
except Exception:
    MISTRAL_MODEL = "mistral-large-latest"
    PIXTRAL_MODEL = "pixtral-large-latest"

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))
DATA_DIR = ROOT_DIR / "data"
WORK_DIR = ROOT_DIR / "ui" / "work"
LOGO_SVG_PATH = ROOT_DIR / "ui" / "assets" / "thales-logo.svg"
load_dotenv(ROOT_DIR / ".env", override=True)


def get_streamlit_secret(name: str) -> str | None:
    try:
        return st.secrets[name]
    except Exception:
        return None


def ensure_mistral_api_key():
    if os.getenv("MISTRAL_API_KEY"):
        return
    secret = get_streamlit_secret("MISTRAL_API_KEY")
    if secret:
        os.environ["MISTRAL_API_KEY"] = secret


def load_json(path: Path):
    try:
        with open(path, "r", encoding="utf-8") as handle:
            return json.load(handle)
    except Exception:
        return None


def format_video_label(video: dict) -> str:
    video_name = Path(video["video_path"]).name
    pair_id = video.get("pair_id")
    return f"{pair_id}: {video_name}" if pair_id else video_name


def ensure_work_dir():
    WORK_DIR.mkdir(parents=True, exist_ok=True)


def load_logo_data() -> str:
    try:
        logo_svg = LOGO_SVG_PATH.read_text(encoding="utf-8")
    except Exception:
        return ""
    return base64.b64encode(logo_svg.encode("utf-8")).decode("ascii")


def load_voice_segments(voice_path: Path) -> list[dict]:
    try:
        from thales.voice_parser import get_all_segments

        segments = get_all_segments(str(voice_path))
    except Exception:
        return []

    rows = []
    for timestamp, text in segments:
        cleaned = str(text).strip()
        if not cleaned:
            continue
        rows.append({"timestamp": timestamp, "text": cleaned})
    return rows


def format_iso(ts: float | None = None) -> str:
    if ts is None:
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M:%S")


def load_stt_config() -> dict:
    config_path = ROOT_DIR / "backend" / "config" / "settings.yaml"
    if not config_path.exists():
        return {}
    try:
        with open(config_path, "r", encoding="utf-8") as handle:
            return yaml.safe_load(handle) or {}
    except Exception:
        return {}


def update_step_times(line: str):
    if not line:
        return
    step_times = st.session_state.get("step_times", {})
    if not isinstance(step_times, dict):
        step_times = {}
    line_lower = line.lower()
    now = format_iso()

    def set_if_missing(key: str):
        if key not in step_times:
            step_times[key] = now

    if "extracting audio" in line_lower:
        set_if_missing("audio_extraction")
    if "loading model" in line_lower or "detected language" in line_lower:
        set_if_missing("speech_to_text")
    if "extracting entities from" in line_lower or "mistral" in line_lower:
        set_if_missing("entity_extraction")
    if "initializing pixtral" in line_lower or "detecting entities in" in line_lower:
        set_if_missing("vision_verification")
    if "merged timeline saved" in line_lower or "saved report" in line_lower:
        set_if_missing("fusion_reports")
    if "thales csv generated" in line_lower:
        set_if_missing("csv_export")

    st.session_state["step_times"] = step_times


def build_pipeline_steps(
    logs_text: str,
    produced_files: dict,
    export_csv: bool | None,
    returncode: int | None,
    step_times: dict | None,
) -> list[dict]:
    logs_text = logs_text or ""
    logs_lower = logs_text.lower()
    step_times = step_times or {}

    def has(token: str) -> bool:
        return token in logs_lower

    def status(done: bool, skipped: bool = False) -> str:
        if skipped:
            return "Skipped"
        if done:
            return "Done"
        if returncode is None:
            return "Pending"
        if returncode != 0:
            return "Failed"
        return "Pending"

    steps = [
        {
            "step": "Audio extraction",
            "status": status(has("extracting audio")),
            "timestamp": step_times.get("audio_extraction", "—"),
        },
        {
            "step": "Speech to text (Whisper)",
            "status": status(has("loading model") or has("detected language")),
            "timestamp": step_times.get("speech_to_text", "—"),
        },
        {
            "step": "Entity extraction (Mistral)",
            "status": status(has("extracting entities from") or has("mistral")),
            "timestamp": step_times.get("entity_extraction", "—"),
        },
        {
            "step": "Vision verification (Pixtral)",
            "status": status(has("initializing pixtral") or has("detecting entities in")),
            "timestamp": step_times.get("vision_verification", "—"),
        },
        {
            "step": "Fusion + reports",
            "status": status(
                has("merged timeline saved")
                or bool(produced_files.get("video_report"))
                or bool(produced_files.get("summary_report"))
            ),
            "timestamp": step_times.get("fusion_reports", "—"),
        },
        {
            "step": "CSV export",
            "status": status(
                bool(produced_files.get("thales_csv")),
                skipped=not export_csv,
            ),
            "timestamp": step_times.get("csv_export", "—"),
        },
    ]
    return steps


def segments_df_to_segments(segments_df: pd.DataFrame) -> list[dict]:
    if segments_df is None or segments_df.empty:
        return []
    rows = []
    for _, row in segments_df.iterrows():
        text = str(row.get("text", "")).strip()
        if not text:
            continue
        start = row.get("start", None)
        timestamp = format_time_value(start) if start is not None else "N/A"
        rows.append({"timestamp": timestamp, "text": text})
    return rows


def search_transcript(segments: list[dict], query: str) -> tuple[int, list[dict]]:
    if not query:
        return 0, []
    query_lower = query.lower()
    matches = []
    total_hits = 0
    for segment in segments:
        text = segment["text"]
        count = text.lower().count(query_lower)
        if count:
            total_hits += count
            matches.append(
                {
                    "timestamp": segment["timestamp"],
                    "hits": count,
                    "text": text,
                }
            )
    return total_hits, matches


def extract_keywords(segments: list[dict], limit: int = 8) -> list[str]:
    if not segments:
        return []
    text = " ".join(segment["text"] for segment in segments if segment.get("text"))
    if not text:
        return []
    tokens = re.findall(r"[A-Za-z0-9][A-Za-z0-9_-]{2,}", text)
    if not tokens:
        return []
    stopwords = {
        "the",
        "and",
        "for",
        "with",
        "this",
        "that",
        "from",
        "into",
        "over",
        "their",
        "there",
        "about",
        "then",
        "they",
        "them",
        "were",
        "have",
        "has",
        "had",
        "not",
        "you",
        "your",
        "but",
        "are",
        "was",
        "our",
        "out",
        "all",
        "can",
        "could",
        "should",
        "mission",
        "location",
        "report",
        "video",
        "audio",
        "intel",
    }
    counts: Counter[str] = Counter()
    for token in tokens:
        lowered = token.lower()
        if lowered in stopwords or lowered.isdigit():
            continue
        counts[lowered] += 1
    return [token for token, _ in counts.most_common(limit)]


def recommend_search_terms(
    entities: dict,
    segments: list[dict],
    limit: int = 12,
) -> list[str]:
    recommendations: list[str] = []
    if entities:
        def score(item: tuple[str, dict]) -> int:
            stats = item[1].get("statistics", {})
            return int(stats.get("frames_with_entity", 0))

        for name, _data in sorted(entities.items(), key=score, reverse=True):
            cleaned = str(name).strip()
            if cleaned and cleaned not in recommendations:
                recommendations.append(cleaned)
            if len(recommendations) >= limit:
                return recommendations

    for keyword in extract_keywords(segments, limit=limit):
        if keyword not in recommendations:
            recommendations.append(keyword)
        if len(recommendations) >= limit:
            break

    return recommendations


def timestamp_to_seconds(timestamp: str) -> int | None:
    if not timestamp:
        return None
    parts = timestamp.strip().split(":")
    if not all(part.isdigit() for part in parts):
        return None
    if len(parts) == 2:
        minutes, seconds = [int(part) for part in parts]
        return minutes * 60 + seconds
    if len(parts) == 3:
        hours, minutes, seconds = [int(part) for part in parts]
        return hours * 3600 + minutes * 60 + seconds
    return None


def format_seconds(total_seconds: int) -> str:
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60
    if hours:
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    return f"{minutes:02d}:{seconds:02d}"


def max_segment_seconds(segments: list[dict]) -> int | None:
    seconds = [
        ts for seg in segments if (ts := timestamp_to_seconds(seg.get("timestamp", ""))) is not None
    ]
    return max(seconds) if seconds else None


def resolve_report_video_path(video_report: dict) -> Path | None:
    if not video_report:
        return None
    video_path = video_report.get("video_path") or video_report.get("video")
    if not video_path:
        return None
    candidate = Path(video_path)
    if candidate.is_absolute():
        return candidate
    return ROOT_DIR / candidate


def load_jsonl(path: Path) -> list[dict]:
    rows = []
    if not path or not path.exists():
        return rows
    with open(path, "r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except Exception:
                continue
    return rows


def infer_pair_id_from_stem(stem: str) -> str | None:
    if stem.startswith("video_"):
        return stem.split("video_", 1)[1]
    return None


def find_latest_stt_job(pair_id: str | None) -> Path | None:
    if not pair_id:
        return None
    base = ROOT_DIR / "backend" / "data" / "output"
    if not base.exists():
        return None
    candidates = sorted(
        base.glob(f"audio_{pair_id}_*"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    return candidates[0] if candidates else None


def format_time_value(value: float | int | None) -> str:
    if value is None:
        return "N/A"
    try:
        return format_seconds(int(float(value)))
    except Exception:
        return str(value)


st.set_page_config(page_title="Thales Video Indexing", layout="wide")
ensure_work_dir()
logo_data = load_logo_data()
if logo_data:
    logo_html = f"<img class=\"logo-img\" src=\"data:image/svg+xml;base64,{logo_data}\" alt=\"Thales logo\" />"
else:
    logo_html = "<span class=\"logo-text\">THALES</span>"

st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500;600;700&family=IBM+Plex+Mono:wght@400;500&display=swap');

:root {
  --ink: #0b1020;
  --ink-soft: #101a2f;
  --muted: #23324b;
  --bg: #f3f5fb;
  --panel: #ffffff;
  --accent: #1d4ed8;
  --accent-2: #0ea5e9;
  --accent-3: #14b8a6;
  --warning: #f59e0b;
  --border: rgba(12, 18, 36, 0.12);
  --shadow: 0 24px 60px rgba(12, 18, 36, 0.18);
  --shadow-soft: 0 16px 30px rgba(12, 18, 36, 0.12);
}

* {
  box-sizing: border-box;
}

html, body, [class*="css"] {
  font-family: "Space Grotesk", sans-serif;
  color: var(--ink);
}

body {
  background-color: var(--bg);
  margin: 0;
}

.stMarkdown p,
.stMarkdown li {
  color: var(--ink-soft);
}

.stMarkdown h1,
.stMarkdown h2,
.stMarkdown h3,
.stMarkdown h4,
.stMarkdown h5,
.stMarkdown h6 {
  color: var(--ink);
}

div[data-testid="stCaption"] p {
  color: var(--ink-soft);
  font-size: 0.9rem;
}

div[data-testid="stMarkdownContainer"] h1,
div[data-testid="stMarkdownContainer"] h2,
div[data-testid="stMarkdownContainer"] h3,
div[data-testid="stMarkdownContainer"] h4,
div[data-testid="stMarkdownContainer"] h5,
div[data-testid="stMarkdownContainer"] h6 {
  color: var(--ink) !important;
}

div[data-testid="stMarkdownContainer"] p,
div[data-testid="stMarkdownContainer"] span,
div[data-testid="stMarkdownContainer"] li {
  color: var(--ink-soft) !important;
}

div[data-testid="stHeading"] h1,
div[data-testid="stHeading"] h2,
div[data-testid="stHeading"] h3,
div[data-testid="stHeading"] h4,
div[data-testid="stHeading"] h5,
div[data-testid="stHeading"] h6 {
  color: var(--ink);
}

div[data-testid="stWidgetLabel"] {
  color: var(--ink);
  font-weight: 600;
}

div[data-testid="stAlert"],
div[data-testid="stAlert"] p {
  color: var(--ink);
}

div[data-testid="stMetricLabel"],
div[data-testid="stMetricValue"],
div[data-testid="stMetricDelta"] {
  color: var(--ink) !important;
}

section[data-testid="stFileUploader"] label,
section[data-testid="stFileUploader"] small,
section[data-testid="stFileUploader"] span,
section[data-testid="stFileUploader"] p {
  color: var(--ink) !important;
}

section[data-testid="stFileUploader"] button {
  color: #fff;
}

div[data-testid="stDataFrame"] {
  background: #ffffff;
  border-radius: 16px;
  border: 1px solid var(--border);
  overflow-x: auto;
}

div[data-testid="stDataFrame"] div[role="grid"],
div[data-testid="stDataFrame"] div[role="gridcell"],
div[data-testid="stDataFrame"] div[role="columnheader"] {
  color: var(--ink) !important;
  background: #ffffff !important;
}

div[data-testid="stDataFrame"] div[role="columnheader"] {
  background: #f4f6fb !important;
  font-weight: 600;
}

div[data-testid="stDataFrame"] div[role="grid"] {
  overflow-x: auto !important;
}

div[data-testid="stDataFrame"]::-webkit-scrollbar,
div[data-testid="stDataFrame"] div[role="grid"]::-webkit-scrollbar {
  height: 10px;
}

div[data-testid="stDataFrame"]::-webkit-scrollbar-track,
div[data-testid="stDataFrame"] div[role="grid"]::-webkit-scrollbar-track {
  background: #e2e8f0;
  border-radius: 999px;
}

div[data-testid="stDataFrame"]::-webkit-scrollbar-thumb,
div[data-testid="stDataFrame"] div[role="grid"]::-webkit-scrollbar-thumb {
  background: #94a3b8;
  border-radius: 999px;
}

code {
  font-family: "IBM Plex Mono", monospace;
  font-size: 0.85em;
  color: var(--ink);
}

header[data-testid="stHeader"],
footer,
#MainMenu,
div[data-testid="stToolbar"],
div[data-testid="stDecoration"] {
  display: none;
}

.stApp {
  background:
    radial-gradient(900px 500px at -10% -20%, rgba(14, 165, 233, 0.18), transparent 60%),
    radial-gradient(600px 400px at 110% 10%, rgba(20, 184, 166, 0.16), transparent 55%),
    radial-gradient(520px 360px at 40% 120%, rgba(29, 78, 216, 0.12), transparent 60%),
    linear-gradient(180deg, #f7f8fd 0%, #eef2fb 60%, #ffffff 100%);
}

section[data-testid="stSidebar"] {
  display: none;
}

.block-container {
  padding-top: 1.2rem;
  max-width: 1200px;
}

.hero {
  position: relative;
  display: grid;
  grid-template-columns: minmax(0, 1.35fr) minmax(0, 0.95fr);
  gap: 2rem;
  align-items: center;
  margin: 1rem 0 1.6rem 0;
  padding: 2.4rem 2.6rem;
  background: rgba(255, 255, 255, 0.9);
  border: 1px solid var(--border);
  border-radius: 28px;
  box-shadow: var(--shadow);
  overflow: hidden;
}

.hero::before {
  content: "";
  position: absolute;
  left: -120px;
  top: -120px;
  width: 240px;
  height: 240px;
  background: radial-gradient(circle, rgba(14, 165, 233, 0.28), transparent 70%);
}

.hero::after {
  content: "";
  position: absolute;
  right: -140px;
  bottom: -140px;
  width: 320px;
  height: 320px;
  background: radial-gradient(circle, rgba(20, 184, 166, 0.28), transparent 70%);
}

.hero-copy,
.hero-panel {
  position: relative;
  z-index: 1;
}

.brand {
  display: flex;
  align-items: center;
  gap: 0.7rem;
  text-transform: uppercase;
  font-size: 0.75rem;
  letter-spacing: 0.2rem;
  color: var(--muted);
  font-weight: 600;
  margin-bottom: 0.7rem;
}

.brand-name {
  font-weight: 600;
}

.logo-img {
  height: 32px;
}

.logo-text {
  font-weight: 700;
  letter-spacing: 0.35rem;
  color: var(--ink);
  font-size: 1rem;
}

.kicker {
  text-transform: uppercase;
  letter-spacing: 0.22rem;
  font-size: 0.7rem;
  color: var(--muted);
  font-weight: 600;
}

.hero h1 {
  font-size: 2.6rem;
  line-height: 1.05;
  margin: 0.45rem 0 0.85rem 0;
  color: var(--ink);
}

.hero p {
  color: var(--ink-soft);
  font-size: 1.05rem;
  max-width: 48ch;
}

.hero-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 0.6rem;
  margin-top: 1.1rem;
}

.tag {
  padding: 0.35rem 0.8rem;
  border-radius: 999px;
  border: 1px solid rgba(29, 78, 216, 0.28);
  background: rgba(29, 78, 216, 0.12);
  color: var(--ink);
  font-size: 0.8rem;
  font-weight: 600;
}

.hero-panel {
  background: rgba(255, 255, 255, 0.92);
  border-radius: 22px;
  padding: 1.4rem 1.5rem;
  border: 1px solid var(--border);
  box-shadow: var(--shadow-soft);
}

.panel-title {
  text-transform: uppercase;
  letter-spacing: 0.18rem;
  font-size: 0.68rem;
  color: var(--muted);
  margin-bottom: 0.6rem;
}

.status-card {
  border-radius: 18px;
  padding: 1rem 1.1rem;
  border: 1px solid var(--border);
  background: rgba(255, 255, 255, 0.9);
  margin-bottom: 1rem;
}

.status-card.ok {
  border-color: rgba(20, 184, 166, 0.35);
  background: rgba(20, 184, 166, 0.12);
}

.status-card.warn {
  border-color: rgba(245, 158, 11, 0.35);
  background: rgba(245, 158, 11, 0.16);
}

.status-title {
  color: var(--ink);
  font-weight: 600;
  font-size: 1rem;
  margin-bottom: 0.25rem;
}

.status-body {
  color: var(--ink-soft);
  font-size: 0.9rem;
}

.pipeline-strip {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 0.6rem;
}

.pipeline-step {
  border-radius: 14px;
  padding: 0.6rem 0.75rem;
  border: 1px solid rgba(12, 18, 36, 0.12);
  background: rgba(255, 255, 255, 0.7);
  font-size: 0.82rem;
  font-weight: 600;
  color: var(--ink);
}

.pipeline-step span {
  font-family: "IBM Plex Mono", monospace;
  font-size: 0.74rem;
  color: var(--ink-soft);
  margin-right: 0.4rem;
}

.deliverables {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: 1.2rem;
  margin: 1.1rem 0 2rem 0;
}

.deliverable-card {
  background: var(--panel);
  border: 1px solid var(--border);
  border-radius: 18px;
  padding: 1.2rem 1.3rem;
  box-shadow: var(--shadow-soft);
}

.deliverable-title {
  color: var(--ink);
  font-weight: 600;
  margin-bottom: 0.4rem;
  font-size: 1rem;
}

.deliverable-body {
  color: var(--ink-soft);
  font-size: 0.92rem;
  line-height: 1.45;
}

.pipeline-detail-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 1rem;
  margin: 1rem 0 1.6rem 0;
}

.pipeline-detail {
  background: var(--panel);
  border: 1px solid var(--border);
  border-radius: 18px;
  padding: 1rem 1.2rem;
  box-shadow: var(--shadow-soft);
}

.pipeline-detail h4 {
  margin: 0 0 0.35rem 0;
  font-size: 1rem;
  color: var(--ink);
}

.pipeline-detail p {
  margin: 0;
  color: var(--ink-soft);
  font-size: 0.92rem;
}

.quickstart-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 1rem;
  margin: 0.6rem 0 1.8rem 0;
}

.quickstart-card {
  background: linear-gradient(180deg, #ffffff 0%, #f6f8fe 100%);
  border: 1px solid var(--border);
  border-radius: 18px;
  padding: 1rem 1.2rem;
  box-shadow: var(--shadow-soft);
}

.quickstart-card h4 {
  margin: 0 0 0.35rem 0;
  font-size: 1rem;
  color: var(--ink);
}

.quickstart-card p {
  margin: 0;
  color: var(--ink-soft);
  font-size: 0.92rem;
}

.section-title {
  color: var(--ink);
  font-size: 1.25rem;
  font-weight: 600;
  margin: 1.6rem 0 0.35rem 0;
  position: relative;
}

.section-title::after {
  content: "";
  display: block;
  width: 78px;
  height: 3px;
  margin-top: 0.45rem;
  border-radius: 999px;
  background: linear-gradient(90deg, var(--accent), var(--accent-2));
}

.section-subtitle {
  color: var(--ink-soft);
  font-size: 0.98rem;
  margin-bottom: 0.85rem;
}

.panel {
  background: rgba(255, 255, 255, 0.95);
  border: 1px solid var(--border);
  border-radius: 20px;
  padding: 1.3rem 1.5rem;
  box-shadow: var(--shadow-soft);
  position: relative;
}

.panel label,
.panel .stMarkdown {
  color: var(--ink);
}

.panel label {
  font-weight: 600;
}

section[data-testid="stFileUploader"] > div {
  border-radius: 16px;
  border: 1px dashed rgba(12, 18, 36, 0.2);
  background: rgba(255, 255, 255, 0.85);
}

div[data-baseweb="input"] input,
div[data-baseweb="textarea"] textarea {
  background: rgba(255, 255, 255, 0.95);
  border: 1px solid rgba(12, 18, 36, 0.16);
  border-radius: 12px;
  padding: 0.55rem 0.75rem;
  box-shadow: inset 0 1px 1px rgba(12, 18, 36, 0.05);
  color: var(--ink);
}

div[data-baseweb="input"] input::placeholder,
div[data-baseweb="textarea"] textarea::placeholder {
  color: rgba(22, 32, 56, 0.75);
}

div[data-baseweb="input"] input:focus,
div[data-baseweb="textarea"] textarea:focus {
  border-color: var(--accent);
  box-shadow: 0 0 0 3px rgba(29, 78, 216, 0.16);
}

div[data-baseweb="select"] > div {
  background: rgba(255, 255, 255, 0.95);
  border: 1px solid rgba(12, 18, 36, 0.16);
  border-radius: 12px;
  color: var(--ink);
}

div[data-baseweb="select"] span {
  color: var(--ink);
}

div[role="listbox"],
div[role="listbox"] * {
  color: var(--ink) !important;
}

div[data-baseweb="tab-list"] {
  gap: 0.4rem;
  padding: 0.3rem;
  background: rgba(255, 255, 255, 0.7);
  border-radius: 999px;
  border: 1px solid var(--border);
}

div[data-baseweb="tab"] {
  border-radius: 999px;
  padding: 0.35rem 1rem;
}

div[data-baseweb="tab"] span {
  color: var(--ink);
  font-weight: 600;
}

div[data-baseweb="tab"][aria-selected="true"] {
  background: rgba(29, 78, 216, 0.16);
  border: 1px solid rgba(29, 78, 216, 0.35);
}

div[data-baseweb="tab"][aria-selected="true"] span {
  color: var(--ink);
}

div[data-testid="stMetric"] {
  background: var(--panel);
  border: 1px solid var(--border);
  border-radius: 16px;
  padding: 1rem;
  box-shadow: var(--shadow-soft);
}

details[data-testid="stExpander"] {
  border: 1px solid var(--border);
  border-radius: 16px;
  background: rgba(255, 255, 255, 0.85);
  padding: 0.2rem 0.8rem;
  box-shadow: var(--shadow-soft);
}

details[data-testid="stExpander"] summary {
  color: var(--ink);
  font-weight: 600;
}

details[data-testid="stExpander"] summary span {
  color: var(--ink) !important;
}

div.stButton > button {
  background: linear-gradient(120deg, var(--accent), var(--accent-2));
  color: #fff;
  border-radius: 12px;
  padding: 0.65rem 1.8rem;
  font-weight: 600;
  border: none;
  box-shadow: 0 14px 26px rgba(12, 18, 36, 0.18);
  transition: transform 0.2s ease, box-shadow 0.2s ease, filter 0.2s ease;
}

div.stButton > button:hover {
  transform: translateY(-2px);
  box-shadow: 0 18px 32px rgba(12, 18, 36, 0.22);
  filter: brightness(1.06);
  color: #fff;
}

div.stButton > button:focus-visible {
  outline: 3px solid rgba(29, 78, 216, 0.45);
  outline-offset: 2px;
}

div.stButton > button:disabled {
  background: #cbd5e1;
  color: #0b1020;
  box-shadow: none;
  opacity: 1;
  cursor: not-allowed;
}

div[data-testid="stDownloadButton"] > button {
  background: linear-gradient(120deg, #0b4dd9, #0ea5e9);
  color: #ffffff;
  border-radius: 12px;
  padding: 0.7rem 1.6rem;
  font-weight: 600;
  border: none;
  box-shadow: 0 14px 26px rgba(12, 18, 36, 0.22);
  width: 100%;
}

div[data-testid="stDownloadButton"] > button:hover {
  filter: brightness(1.05);
  color: #fff;
}

div[data-testid="stDownloadButton"] > button:disabled {
  background: #e2e8f0;
  color: #0b1020;
  border: 1px dashed rgba(12, 18, 36, 0.35);
  box-shadow: none;
  opacity: 1;
}

div[data-testid="stAlert"] {
  border: 1px solid rgba(12, 18, 36, 0.2);
  background: rgba(255, 255, 255, 0.9);
}

a {
  color: #0b4dd9;
  text-decoration: none;
}

a:hover {
  text-decoration: underline;
}

@keyframes fadeUp {
  from { opacity: 0; transform: translateY(12px); }
  to { opacity: 1; transform: translateY(0); }
}

.fade-up {
  animation: fadeUp 0.6s ease both;
}

html {
  scroll-behavior: smooth;
}

.nav-bar {
  position: sticky;
  top: 0.5rem;
  z-index: 120;
  margin: 1.2rem 0 1rem 0;
}

.nav-inner {
  display: flex;
  flex-wrap: wrap;
  gap: 0.6rem;
  align-items: center;
  padding: 0.6rem 1rem;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.92);
  border: 1px solid var(--border);
  box-shadow: var(--shadow-soft);
  backdrop-filter: blur(12px);
  width: 100%;
}

.nav-label {
  font-size: 0.75rem;
  text-transform: uppercase;
  letter-spacing: 0.16rem;
  color: var(--muted);
  font-weight: 600;
  margin-right: 0.4rem;
}

.nav-link {
  padding: 0.35rem 0.85rem;
  border-radius: 999px;
  background: rgba(29, 78, 216, 0.08);
  color: var(--ink);
  font-weight: 600;
  font-size: 0.9rem;
  border: 1px solid transparent;
  transition: all 0.2s ease;
}

.nav-link:hover {
  background: linear-gradient(120deg, #1d4ed8, #0ea5e9);
  color: #ffffff;
  border-color: rgba(29, 78, 216, 0.4);
}

.section-anchor {
  scroll-margin-top: 120px;
}

@media (max-width: 900px) {
  .hero {
    grid-template-columns: 1fr;
    padding: 1.6rem;
  }

  .hero h1 {
    font-size: 2.15rem;
  }

  .pipeline-strip {
    grid-template-columns: 1fr;
  }

  .nav-bar {
    top: 0.25rem;
  }

  .nav-inner {
    border-radius: 18px;
  }

  .nav-label {
    width: 100%;
  }
}
</style>
""",
    unsafe_allow_html=True,
)

data_dir = DATA_DIR

ensure_mistral_api_key()
api_key_present = bool(os.getenv("MISTRAL_API_KEY"))
status_class = "ok" if api_key_present else "warn"
status_title = "Ready to run" if api_key_present else "API key required"
status_body = (
    "Mistral access detected. Upload a video to start."
    if api_key_present
    else "Add MISTRAL_API_KEY in Streamlit secrets to run the pipeline."
)

st.markdown(
    f"""
<div class="hero fade-up">
  <div class="hero-copy">
    <div class="brand">
      {logo_html}
      <span class="brand-name">Thales Optronic</span>
    </div>
    <div class="kicker">Single-video intelligence pipeline</div>
    <h1>Thales Video Indexing</h1>
    <p>
      Upload one video and let the system extract audio, transcribe speech, extract entities,
      verify with vision, and fuse everything into a single timeline.
    </p>
    <div class="hero-tags">
      <span class="tag">Upload video only</span>
      <span class="tag">Auto audio extraction</span>
      <span class="tag">STT + vision fusion</span>
    </div>
  </div>
  <div class="hero-panel">
    <div class="panel-title">Pipeline readiness</div>
    <div class="status-card {status_class}">
      <div class="status-title">{status_title}</div>
      <div class="status-body">{status_body}</div>
    </div>
    <div class="pipeline-strip">
      <div class="pipeline-step"><span>01</span>Audio extraction (FFmpeg)</div>
      <div class="pipeline-step"><span>02</span>Speech to text (Whisper)</div>
      <div class="pipeline-step"><span>03</span>Entity extraction (Mistral)</div>
      <div class="pipeline-step"><span>04</span>Vision verification (Pixtral)</div>
      <div class="pipeline-step"><span>05</span>Fusion + reports</div>
    </div>
  </div>
</div>
""",
    unsafe_allow_html=True,
)

st.markdown(
    """
<div class="nav-bar">
  <div class="nav-inner">
    <span class="nav-label">Navigate</span>
    <a class="nav-link" href="#overview">Overview</a>
    <a class="nav-link" href="#run">Run</a>
    <a class="nav-link" href="#results">Results</a>
    <a class="nav-link" href="#insights">Insights</a>
    <a class="nav-link" href="#transcript">Transcript</a>
    <a class="nav-link" href="#analysis">Analysis Outputs</a>
    <a class="nav-link" href="#downloads">Downloads</a>
    <a class="nav-link" href="#faq">FAQ</a>
  </div>
</div>
""",
    unsafe_allow_html=True,
)

st.markdown("<div id='overview' class='section-anchor'></div>", unsafe_allow_html=True)

st.markdown("<div class='section-title'>Quick start</div>", unsafe_allow_html=True)
st.markdown(
    "<div class='section-subtitle'>Get a full analysis in three steps.</div>",
    unsafe_allow_html=True,
)
st.markdown(
    """
<div class="quickstart-grid">
  <div class="quickstart-card">
    <h4>1) Add API key</h4>
    <p>Set <code>MISTRAL_API_KEY</code> in Streamlit secrets to enable analysis.</p>
  </div>
  <div class="quickstart-card">
    <h4>2) Upload & run</h4>
    <p>Upload a video and click Run pipeline. Audio + vision analysis runs automatically.</p>
  </div>
  <div class="quickstart-card">
    <h4>3) Review outputs</h4>
    <p>Explore scene summaries, entities, keyword timeline, and exports.</p>
  </div>
</div>
""",
    unsafe_allow_html=True,
)

st.markdown("<div id='run' class='section-anchor'></div>", unsafe_allow_html=True)
st.markdown("<div class='section-title'>Upload & Run</div>", unsafe_allow_html=True)
st.markdown(
    "<div class='section-subtitle'>Upload a single video and launch the full pipeline in one click.</div>",
    unsafe_allow_html=True,
)

selected_video = None
video_upload = None
use_existing = False

form_cols = st.columns([1.2, 0.8], gap="large")
with form_cols[0]:
    st.markdown("<div class='panel'>", unsafe_allow_html=True)
    st.subheader("Step 1 - Video input")
    st.caption("Upload one video. Audio extraction and transcription run automatically.")
    video_upload = st.file_uploader(
        "Upload video", type=[ext.strip(".") for ext in ALLOWED_VIDEO_EXTS]
    )
    st.caption("Supported formats: mp4, mkv, avi, mov.")
    with st.expander("Advanced options (optional)", expanded=False):
        use_existing = st.checkbox(
            "Use a video already in data/ (skip upload)", value=False
        )
        if use_existing:
            videos = find_videos(DATA_DIR)
            if not videos:
                st.warning("No videos found in data/. Upload a video instead.")
            else:
                labels = {format_video_label(video): video for video in videos}
                selected_label = st.selectbox("Select existing video", list(labels.keys()))
                selected_video = labels[selected_label]
                st.caption("Selected video will replace the uploaded file.")
    st.markdown("</div>", unsafe_allow_html=True)

with form_cols[1]:
    st.markdown("<div class='panel'>", unsafe_allow_html=True)
    st.subheader("Step 2 - Run pipeline")
    st.caption(
        "Extract audio, transcribe, detect entities, and fuse results. Outputs become searchable below."
    )
    with st.expander("Advanced settings (optional)", expanded=False):
        frame_interval = st.number_input(
            "Frame interval (seconds)", min_value=1, value=30, step=1
        )
        output_dir_input = st.text_input("Output directory", value="reports_ui")
        export_csv = st.checkbox("Generate Thales CSV export", value=True)
    has_video = bool(selected_video) if use_existing else bool(video_upload)
    ready_to_run = api_key_present and has_video
    if not api_key_present:
        st.error("MISTRAL_API_KEY is missing. Add it in Streamlit secrets.")
    elif not has_video:
        if use_existing:
            st.info("Select a video from data/ or disable developer options to use uploads.")
        else:
            st.info("Upload a video to enable the pipeline.")
    run_button = st.button("Run pipeline", type="primary", disabled=not ready_to_run)
    st.markdown("</div>", unsafe_allow_html=True)

log_placeholder = st.empty()
status_placeholder = st.empty()

if "logs" not in st.session_state:
    st.session_state["logs"] = ""
if "produced_files" not in st.session_state:
    st.session_state["produced_files"] = {}
if "returncode" not in st.session_state:
    st.session_state["returncode"] = None
if "show_logs_expanded" not in st.session_state:
    st.session_state["show_logs_expanded"] = False

if run_button:
    st.session_state["logs"] = ""
    st.session_state["produced_files"] = {}
    st.session_state["returncode"] = None

    errors = []
    pair_id = None
    run_dir = None

    if not api_key_present:
        errors.append("MISTRAL_API_KEY is missing. Add it in Streamlit secrets.")

    if use_existing:
        if selected_video is None:
            errors.append(
                "Select a video from data/ or disable developer options to use uploads."
            )
        else:
            source_video = Path(selected_video["video_path"])
            if not source_video.exists():
                errors.append("Selected video file is missing.")
            else:
                pair_id = selected_video.get("pair_id") or str(int(time.time()))
                timestamp = int(time.time())
                run_dir = WORK_DIR / f"run_{timestamp}_pair_{pair_id}"
                run_dir.mkdir(parents=True, exist_ok=True)
                dest_path = run_dir / f"video_{pair_id}{source_video.suffix.lower()}"
                shutil.copy2(source_video, dest_path)
    else:
        if video_upload is None:
            errors.append("Upload a video file.")
        else:
            video_ext = Path(video_upload.name).suffix.lower()
            if video_ext not in ALLOWED_VIDEO_EXTS:
                errors.append(
                    f"Video extension {video_ext} is not supported. "
                    f"Allowed: {', '.join(ALLOWED_VIDEO_EXTS)}"
                )

            if not errors:
                pair_id = str(int(time.time()))
                timestamp = int(time.time())
                run_dir = WORK_DIR / f"run_{timestamp}_pair_{pair_id}"
                run_dir.mkdir(parents=True, exist_ok=True)
                dest_path = run_dir / f"video_{pair_id}{video_ext}"
                dest_path.write_bytes(video_upload.getvalue())

    if errors:
        for err in errors:
            st.error(err)
    else:
        st.session_state.pop("voice_path", None)
        if pair_id:
            st.session_state["pair_id"] = pair_id
        env_overrides = {}
        mistral_key = os.getenv("MISTRAL_API_KEY")
        if mistral_key:
            env_overrides["MISTRAL_API_KEY"] = mistral_key

        out_dir = Path(output_dir_input)
        if not out_dir.is_absolute():
            out_dir = ROOT_DIR / out_dir

            def on_log(_line, logs_text):
                st.session_state["logs"] = logs_text
                st.session_state["last_log_at"] = format_iso()
                update_step_times(_line)
                log_placeholder.code(logs_text)

            status_placeholder.info(
                "Running the pipeline. First-time model downloads can take a few minutes."
            )
            with st.spinner("Running the pipeline..."):
                st.session_state["run_started_at"] = format_iso()
                st.session_state["step_times"] = {}
                returncode, logs_text, produced_files = run_pipeline(
                    sys.executable,
                    run_dir or data_dir,
                    int(frame_interval),
                    out_dir,
                env_overrides,
                selected_pair_id=None,
                export_csv=export_csv,
                log_callback=on_log,
            )

            if pair_id:
                generated_voice = ROOT_DIR / "data" / f"voice_{pair_id}.txt"
                if generated_voice.exists():
                    st.session_state["voice_path"] = str(generated_voice)

            st.session_state["run_finished_at"] = format_iso()
            st.session_state["logs"] = logs_text
            st.session_state["produced_files"] = produced_files
            st.session_state["returncode"] = returncode
            st.session_state["output_dir"] = str(out_dir)
            st.session_state["run_params"] = {
                "frame_interval": int(frame_interval),
                "output_dir": str(out_dir),
                "export_csv": bool(export_csv),
                "pair_id": pair_id,
                "video_name": dest_path.name if "dest_path" in locals() else "",
            }

        outputs_found = bool(
            produced_files.get("summary_report") or produced_files.get("video_report")
        )

        if returncode != 0:
            status_placeholder.error("Pipeline failed. Check the logs below for details.")
            st.session_state["show_logs_expanded"] = True
        elif outputs_found:
            status_placeholder.success("Pipeline completed successfully.")
            st.session_state["show_logs_expanded"] = False
        else:
            status_placeholder.warning(
                "Pipeline finished but no output files were found. Check the logs below."
            )
            st.session_state["show_logs_expanded"] = True

if st.session_state.get("logs"):
    with st.expander("Logs", expanded=st.session_state.get("show_logs_expanded", False)):
        st.code(st.session_state["logs"])

produced_files = st.session_state.get("produced_files", {})
summary_path = produced_files.get("summary_report")
video_report_path = produced_files.get("video_report")
csv_report_path = produced_files.get("thales_csv")
run_params = st.session_state.get("run_params", {})
step_times = st.session_state.get("step_times", {})
run_started_at = st.session_state.get("run_started_at")
run_finished_at = st.session_state.get("run_finished_at")
logs_text = st.session_state.get("logs", "")
returncode = st.session_state.get("returncode")
export_csv_enabled = run_params.get("export_csv", True)

st.markdown("<div id='results' class='section-anchor'></div>", unsafe_allow_html=True)
st.markdown("<div class='section-title'>Pipeline timeline</div>", unsafe_allow_html=True)
st.markdown(
    "<div class='section-subtitle'>Status and configuration for the most recent run.</div>",
    unsafe_allow_html=True,
)
timeline_cols = st.columns([1.2, 1])
with timeline_cols[0]:
    steps = build_pipeline_steps(
        logs_text,
        produced_files,
        export_csv_enabled,
        returncode,
        step_times,
    )
    st.dataframe(pd.DataFrame(steps), use_container_width=True)
with timeline_cols[1]:
    st.markdown("<div class='panel'>", unsafe_allow_html=True)
    st.subheader("Run metadata")
    st.write(f"Start: {run_started_at or '—'}")
    st.write(f"Finish: {run_finished_at or '—'}")
    st.write(f"Last log update: {st.session_state.get('last_log_at', '—')}")
    st.write(f"Frame interval: {run_params.get('frame_interval', '—')}s")
    st.write(f"Output dir: {run_params.get('output_dir', '—')}")
    if run_params.get("video_name"):
        st.write(f"Video file: {run_params.get('video_name')}")
    st.markdown("</div>", unsafe_allow_html=True)

st.markdown("<div class='panel'>", unsafe_allow_html=True)
st.subheader("Models & parameters")
st.caption("Configuration used for speech and vision during the latest run.")
stt_config = load_stt_config()
model_cfg = stt_config.get("model", {}) if stt_config else {}
trans_cfg = stt_config.get("transcription", {}) if stt_config else {}
model_rows = [
    {"setting": "Whisper model size", "value": model_cfg.get("size", "unknown")},
    {"setting": "Whisper device", "value": model_cfg.get("device", "unknown")},
    {"setting": "Whisper compute type", "value": model_cfg.get("compute_type", "unknown")},
    {"setting": "Transcription task", "value": trans_cfg.get("task", "unknown")},
    {"setting": "Beam size", "value": trans_cfg.get("beam_size", "unknown")},
    {"setting": "Language", "value": trans_cfg.get("language", "auto")},
    {"setting": "Mistral model", "value": MISTRAL_MODEL},
    {"setting": "Pixtral model", "value": PIXTRAL_MODEL},
]
st.dataframe(pd.DataFrame(model_rows), use_container_width=True)
st.markdown("</div>", unsafe_allow_html=True)

st.markdown("<div class='section-title'>Results</div>", unsafe_allow_html=True)
st.markdown(
    "<div class='section-subtitle'>Key metrics and entity overview from the latest run.</div>",
    unsafe_allow_html=True,
)
summary_data = load_json(Path(summary_path)) if summary_path else None
video_report_data = load_json(Path(video_report_path)) if video_report_path else None
entities = video_report_data.get("entities", {}) if video_report_data else {}

if summary_data or video_report_data:
    entity_count = None
    total_videos = None
    total_confirmed_frames = None

    if summary_data:
        entity_count = summary_data.get("unique_entity_count")
        total_videos = summary_data.get("total_videos")

    if video_report_data:
        if entity_count is None:
            entity_count = len(entities)
        total_confirmed_frames = sum(
            data.get("statistics", {}).get("frames_with_entity", 0)
            for data in entities.values()
        )

    cols = st.columns(3)
    cols[0].metric("Entities", entity_count if entity_count is not None else "N/A")
    cols[1].metric("Videos processed", total_videos if total_videos is not None else "N/A")
    cols[2].metric(
        "Confirmed frames",
        total_confirmed_frames if total_confirmed_frames is not None else "N/A",
    )

    if video_report_data:
        st.markdown("<div class='panel'>", unsafe_allow_html=True)
        st.subheader("Outputs status")
        status_rows = [
            {"artifact": "Summary report", "status": "Ready" if summary_path else "Missing"},
            {"artifact": "Video report", "status": "Ready" if video_report_path else "Missing"},
            {"artifact": "Thales CSV export", "status": "Ready" if csv_report_path else "Missing"},
            {
                "artifact": "Transcript file",
                "status": "Ready" if st.session_state.get("voice_path") else "Missing",
            },
        ]
        st.dataframe(pd.DataFrame(status_rows), use_container_width=True)
        st.caption("Open the Analysis Outputs tab for pivot timelines and STT artifacts.")
        st.markdown("</div>", unsafe_allow_html=True)

        findings = []
        for name, data in entities.items():
            stats = data.get("statistics", {})
            detections = data.get("detections", [])
            present = [d for d in detections if d.get("present")]
            present_sorted = sorted(present, key=lambda d: d.get("second", 0))

            first_seen = None
            last_seen = None
            if present_sorted:
                first_seen = present_sorted[0].get("timestamp")
                last_seen = present_sorted[-1].get("timestamp")
            elif data.get("time_ranges"):
                first_seen = data["time_ranges"][0].get("start")
                last_seen = data["time_ranges"][-1].get("end")

            findings.append(
                {
                    "entity": name,
                    "frames_confirmed": stats.get("frames_with_entity", 0),
                    "presence_percent": stats.get("presence_percentage", 0),
                    "first_seen": first_seen or "N/A",
                    "last_seen": last_seen or "N/A",
                }
            )

        if findings:
            findings_sorted = sorted(
                findings,
                key=lambda row: (row["frames_confirmed"], row["presence_percent"]),
                reverse=True,
            )
            top_findings = findings_sorted[:3]
            st.markdown("<div class='panel'>", unsafe_allow_html=True)
            st.subheader("Key findings")
            st.caption("Top entities detected in the latest run.")
            for entry in top_findings:
                st.markdown(
                    f"**{entry['entity']}** — {entry['frames_confirmed']} confirmed frame(s), "
                    f"{entry['presence_percent']}% presence, "
                    f"{entry['first_seen']} → {entry['last_seen']}"
                )
            st.markdown("</div>", unsafe_allow_html=True)

        rows = []
        for name, data in entities.items():
            stats = data.get("statistics", {})
            detections = data.get("detections", [])
            present = [d for d in detections if d.get("present")]
            present_sorted = sorted(present, key=lambda d: d.get("second", 0))

            first_seen = None
            last_seen = None
            if present_sorted:
                first_seen = present_sorted[0].get("timestamp")
                last_seen = present_sorted[-1].get("timestamp")
            elif data.get("time_ranges"):
                first_seen = data["time_ranges"][0].get("start")
                last_seen = data["time_ranges"][-1].get("end")

            rows.append(
                {
                    "entity": name,
                    "first_seen": first_seen or "N/A",
                    "last_seen": last_seen or "N/A",
                    "frames_confirmed": stats.get("frames_with_entity", 0),
                    "presence_percent": stats.get("presence_percentage", "N/A"),
                }
            )

        st.subheader("Entities")
        st.dataframe(pd.DataFrame(rows), use_container_width=True)
else:
    st.info("Run the pipeline to populate results and metrics.")

st.markdown("<div id='insights' class='section-anchor'></div>", unsafe_allow_html=True)
st.markdown("<div class='section-title'>Insights</div>", unsafe_allow_html=True)
st.markdown(
    "<div class='section-subtitle'>Scene summaries, frame verification, and entity timelines.</div>",
    unsafe_allow_html=True,
)
if video_report_data:
    st.subheader("AI scene timeline")
    st.caption("High-level description of what is visible in the video over time.")
    scene_timeline = st.session_state.get("scene_timeline")
    scene_video_path = resolve_report_video_path(video_report_data)
    output_dir_value = st.session_state.get("output_dir", "reports_ui")
    output_dir_path = Path(output_dir_value)
    if not output_dir_path.is_absolute():
        output_dir_path = ROOT_DIR / output_dir_path

    scene_path = None
    if video_report_path:
        stem = Path(video_report_path).stem.replace("_report", "")
        scene_path = output_dir_path / f"{stem}_scene.json"
        if scene_timeline is None and scene_path.exists():
            scene_timeline = load_json(scene_path)

    if scene_timeline:
        st.dataframe(pd.DataFrame(scene_timeline), use_container_width=True, width=1200)
        with st.expander("Readable scene descriptions", expanded=True):
            filter_text = st.text_input(
                "Filter descriptions",
                placeholder="e.g., tank, convoy, warehouse",
                key="scene_filter",
            )
            filtered = []
            for entry in scene_timeline:
                summary = str(entry.get("summary", "")).lstrip("-•\\ ").strip()
                if not filter_text or filter_text.lower() in summary.lower():
                    filtered.append(
                        {
                            "timestamp": entry.get("timestamp", ""),
                            "summary": summary,
                        }
                    )
            if not filtered:
                st.info("No descriptions match that filter.")
            else:
                st.caption(f"Showing {len(filtered)} descriptions.")
                for entry in filtered:
                    st.markdown(
                        f"**{entry['timestamp']}** — {entry['summary']}"
                    )
    elif not api_key_present:
        st.info("Add MISTRAL_API_KEY to generate the scene timeline.")
    elif not scene_video_path or not scene_video_path.exists():
        st.info("Scene timeline requires the source video to be available.")
    else:
        st.markdown("<div class='panel'>", unsafe_allow_html=True)
        st.subheader("Generate scene timeline")
        st.caption("Uses Pixtral to summarize frames at the chosen interval.")
        scene_interval = st.number_input(
            "Scene analysis interval (seconds)", min_value=5, value=10, step=5
        )
        scene_limit = st.number_input(
            "Max frames to analyze", min_value=20, value=120, step=20
        )
        generate_scene = st.button("Run scene analysis")
        st.markdown("</div>", unsafe_allow_html=True)

        if generate_scene:
            try:
                from thales.scene_analysis import generate_scene_timeline
            except Exception:
                st.warning(
                    "Scene analysis module not found in this deployment. "
                    "Using inline analyzer instead."
                )
                from thales.entity_detector import frame_to_base64, get_pixtral_client
                from thales.video_processor import (
                    extract_frames_at_intervals,
                    seconds_to_timestamp,
                )
                from thales.config import PIXTRAL_MODEL

                def generate_scene_timeline(
                    video_path: str,
                    interval_seconds: int = 10,
                    max_frames: int = 120,
                    progress_cb=None,
                ):
                    client = get_pixtral_client()
                    frames = extract_frames_at_intervals(video_path, interval_seconds)
                    if not frames:
                        return []

                    if max_frames and len(frames) > max_frames:
                        step = max(1, int(len(frames) / max_frames) + 1)
                        frames = frames[::step]

                    timeline = []
                    total = len(frames)
                    prompt = (
                        "Describe the scene in 1-2 concise sentences. Focus only on "
                        "what is visible in the frame: people, vehicles, objects, actions, "
                        "and environment. Do not speculate. If the scene is unclear, say "
                        "'Unclear scene.'"
                    )
                    for idx, (second, frame) in enumerate(frames, 1):
                        image_base64 = frame_to_base64(frame)
                        response = client.chat.complete(
                            model=PIXTRAL_MODEL,
                            messages=[
                                {
                                    "role": "user",
                                    "content": [
                                        {
                                            "type": "image_url",
                                            "image_url": f"data:image/jpeg;base64,{image_base64}",
                                        },
                                        {"type": "text", "text": prompt},
                                    ],
                                }
                            ],
                            temperature=0.2,
                        )
                        content = response.choices[0].message.content.strip()
                        summary = content.split("\n")[0].strip()
                        entry = {
                            "timestamp": seconds_to_timestamp(int(second)),
                            "second": int(second),
                            "summary": summary,
                        }
                        timeline.append(entry)
                        if progress_cb:
                            progress_cb(idx, total, entry)
                    return timeline

            progress = st.progress(0)
            status = st.empty()

            def on_progress(idx: int, total: int, entry: dict):
                progress.progress(min(1.0, idx / total))
                status.info(
                    f"Analyzing {entry['timestamp']} ({idx}/{total})"
                )

            with st.spinner("Running scene analysis..."):
                scene_timeline = generate_scene_timeline(
                    str(scene_video_path),
                    interval_seconds=int(scene_interval),
                    max_frames=int(scene_limit),
                    progress_cb=on_progress,
                )

            progress.empty()
            status.empty()
            st.session_state["scene_timeline"] = scene_timeline
            if scene_path:
                scene_path.parent.mkdir(parents=True, exist_ok=True)
                with open(scene_path, "w", encoding="utf-8") as handle:
                    json.dump(scene_timeline, handle, indent=2)
            if scene_timeline:
                st.dataframe(pd.DataFrame(scene_timeline), use_container_width=True)
            else:
                st.info("Scene timeline could not be generated.")

    st.subheader("AI frame analysis")
    st.caption("Frame-by-frame detections from the vision model.")
    frame_map: dict[int, list[str]] = {}
    all_seconds: set[int] = set()
    for entity_name, data in entities.items():
        detections = data.get("detections", [])
        for det in detections:
            second = int(det.get("second", 0))
            all_seconds.add(second)
            if det.get("present"):
                frame_map.setdefault(second, []).append(entity_name)

    show_only_hits = st.checkbox("Show only frames with detections", value=True)
    frame_rows = []
    seconds_source = sorted(frame_map.keys()) if show_only_hits else sorted(all_seconds)
    for second in seconds_source:
        entities_present = sorted(set(frame_map.get(second, [])))
        frame_rows.append(
            {
                "timestamp": format_seconds(second),
                "second": second,
                "entities_present": ", ".join(entities_present) if entities_present else "None",
            }
        )

    if frame_rows:
        st.dataframe(pd.DataFrame(frame_rows), use_container_width=True)
    else:
        st.info("No frame-by-frame detections available.")

    entity_names = list(entities.keys())
    if entity_names:
        selected_entity = st.selectbox("Entity timeline", entity_names)
        entity_data = entities.get(selected_entity, {})
        detections = entity_data.get("detections", [])

        st.subheader(f"Timeline: {selected_entity}")
        if detections:
            present_detections = [d for d in detections if d.get("present")]
            if present_detections:
                presence_df = pd.DataFrame(
                    {
                        "second": [d.get("second", 0) for d in present_detections],
                        "timestamp": [
                            d.get("timestamp", "") for d in present_detections
                        ],
                    }
                )
                bin_seconds = 30
                duration_seconds = int(presence_df["second"].max()) if not presence_df.empty else 0
                total_bins = int(duration_seconds // bin_seconds) + 1
                hits_by_bin = presence_df.groupby(
                    (presence_df["second"] // bin_seconds) * bin_seconds
                )["second"].count()
                bins = []
                for idx in range(total_bins):
                    start = idx * bin_seconds
                    end = start + bin_seconds
                    bins.append(
                        {
                            "window_start": start,
                            "window_end": end,
                            "detections": int(hits_by_bin.get(start, 0)),
                            "label": f"{format_seconds(start)}–{format_seconds(end)}",
                        }
                    )
                bin_df = pd.DataFrame(bins)

                st.subheader("Detection timeline (30s bins)")
                st.caption("Bars show how often the entity appears over time.")
                try:
                    import altair as alt

                    timeline_chart = (
                        alt.Chart(bin_df)
                        .mark_bar(color="#0b4dd9")
                        .encode(
                            x=alt.X("window_start:Q", title="Second"),
                            y=alt.Y("detections:Q", title="Detections"),
                            tooltip=["label", "detections"],
                        )
                        .properties(height=200)
                        .configure_view(fill="#ffffff", strokeOpacity=0)
                        .configure(background="#ffffff")
                        .configure_axis(
                            labelColor="#0b1020",
                            titleColor="#0b1020",
                            gridColor="#e2e8f0",
                            tickColor="#cbd5f5",
                        )
                    )
                    st.altair_chart(timeline_chart, use_container_width=True)
                except Exception:
                    st.bar_chart(bin_df.set_index("window_start")["detections"])

                st.subheader("Exact detections")
                timestamps = [
                    ts for ts in presence_df["timestamp"].dropna().astype(str).tolist() if ts
                ]
                if timestamps:
                    st.write(", ".join(timestamps))
                else:
                    st.write(", ".join(str(sec) for sec in presence_df["second"].tolist()))
            else:
                st.info("No confirmed frames for this entity.")
        elif entity_data.get("time_ranges"):
            st.write("Time ranges:")
            st.table(entity_data.get("time_ranges"))
        else:
            st.info("No timeline data available for this entity.")


else:
    st.info("Run the pipeline to populate insights.")

voice_path_for_search = st.session_state.get("voice_path")
voice_segments = []
inferred_pair_id = None
if video_report_path:
    inferred_pair_id = infer_pair_id_from_stem(
        Path(video_report_path).stem.replace("_report", "")
    )
if not inferred_pair_id and video_report_data:
    video_path_hint = video_report_data.get("video_path") or video_report_data.get("video")
    if video_path_hint:
        inferred_pair_id = infer_pair_id_from_stem(Path(video_path_hint).stem)

if not voice_path_for_search and inferred_pair_id:
    candidate = ROOT_DIR / "data" / f"voice_{inferred_pair_id}.txt"
    if candidate.exists():
        voice_path_for_search = str(candidate)

if not voice_path_for_search:
    voice_candidates = sorted(
        (ROOT_DIR / "data").glob("voice_*.txt"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    if voice_candidates:
        voice_path_for_search = str(voice_candidates[0])

if voice_path_for_search:
    voice_path_obj = Path(voice_path_for_search)
    if voice_path_obj.exists():
        voice_segments = load_voice_segments(voice_path_obj)
        st.session_state["voice_path"] = str(voice_path_obj)

if not voice_segments:
    stt_job_dir = find_latest_stt_job(inferred_pair_id)
    if not stt_job_dir:
        stt_root = ROOT_DIR / "backend" / "data" / "output"
        if stt_root.exists():
            stt_candidates = sorted(
                [p for p in stt_root.iterdir() if p.is_dir() and p.name.startswith("audio_")],
                key=lambda p: p.stat().st_mtime,
                reverse=True,
            )
            stt_job_dir = stt_candidates[0] if stt_candidates else None
    segments_path = stt_job_dir / "segments.csv" if stt_job_dir else None
    if segments_path and segments_path.exists():
        try:
            segments_df = pd.read_csv(segments_path)
        except Exception:
            segments_df = None
        voice_segments = segments_df_to_segments(segments_df) if segments_df is not None else []

st.markdown("<div id='transcript' class='section-anchor'></div>", unsafe_allow_html=True)
st.markdown("<div class='section-title'>Transcript & Search</div>", unsafe_allow_html=True)
st.markdown(
    "<div class='section-subtitle'>Transcript context, keyword search, and entity matches.</div>",
    unsafe_allow_html=True,
)
if voice_segments:
    st.subheader("Transcript context")
    st.caption("What the AI extracted from the video audio.")
    total_segments = len(voice_segments)
    total_words = sum(len(seg["text"].split()) for seg in voice_segments)
    duration_seconds = max_segment_seconds(voice_segments)

    summary_cols = st.columns(3)
    summary_cols[0].metric("Transcript segments", total_segments)
    summary_cols[1].metric("Total words", total_words)
    summary_cols[2].metric(
        "Transcript duration",
        format_seconds(duration_seconds) if duration_seconds is not None else "N/A",
    )

    context_terms = extract_keywords(voice_segments, limit=10)
    entity_terms = []
    if video_report_data:
        entity_terms = list(video_report_data.get("entities", {}).keys())[:10]
    if context_terms or entity_terms:
        st.markdown("<div class='panel'>", unsafe_allow_html=True)
        st.subheader("Context tags")
        st.caption("Quick view of frequent terms and detected entities.")
        if entity_terms:
            st.markdown("**Entities extracted from transcript**")
            st.write(", ".join(entity_terms))
        if context_terms:
            st.markdown("**Transcript keywords**")
            st.write(", ".join(context_terms))
        st.markdown("</div>", unsafe_allow_html=True)

    with st.expander("View transcript", expanded=False):
        transcript_df = pd.DataFrame(voice_segments)
        st.dataframe(transcript_df, use_container_width=True)
else:
    st.info("Transcript context will appear here after the pipeline runs.")

st.markdown("<div id='analysis' class='section-anchor'></div>", unsafe_allow_html=True)
st.markdown("<div class='section-title'>Analysis outputs</div>", unsafe_allow_html=True)
st.markdown(
    "<div class='section-subtitle'>Detailed artifacts produced by the pipeline.</div>",
    unsafe_allow_html=True,
)
analysis_source_ready = bool(summary_data or video_report_data or voice_segments)
if analysis_source_ready:
    output_dir_value = st.session_state.get("output_dir")
    if output_dir_value:
        output_dir_path = Path(output_dir_value)
        if not output_dir_path.is_absolute():
            output_dir_path = ROOT_DIR / output_dir_path
    else:
        base_dir = None
        if summary_path:
            base_dir = Path(summary_path).parent
        elif video_report_path:
            base_dir = Path(video_report_path).parent
        output_dir_path = (
            base_dir
            if base_dir and base_dir.is_absolute()
            else ROOT_DIR / (base_dir or "reports")
        )

    pivot_dir = output_dir_path / "pivot"
    if not pivot_dir.exists():
        fallback_pivot = ROOT_DIR / "reports" / "pivot"
        if fallback_pivot.exists():
            pivot_dir = fallback_pivot

    video_stem = None
    if video_report_path:
        video_stem = Path(video_report_path).stem.replace("_report", "")
    if not video_stem and pivot_dir.exists():
        merged_candidates = sorted(
            pivot_dir.glob("*_merged.jsonl"),
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )
        if merged_candidates:
            video_stem = merged_candidates[0].name.replace("_merged.jsonl", "")

    pair_id = st.session_state.get("pair_id") or infer_pair_id_from_stem(video_stem or "")
    if not pair_id and voice_path_for_search:
        match = re.search(r"voice_(\d+)", Path(voice_path_for_search).name)
        if match:
            pair_id = match.group(1)

    stt_job_dir = find_latest_stt_job(pair_id)
    if not stt_job_dir:
        stt_root = ROOT_DIR / "backend" / "data" / "output"
        if stt_root.exists():
            candidates = sorted(
                [p for p in stt_root.iterdir() if p.is_dir() and p.name.startswith("audio_")],
                key=lambda p: p.stat().st_mtime,
                reverse=True,
            )
            stt_job_dir = candidates[0] if candidates else None

    segments_path = stt_job_dir / "segments.csv" if stt_job_dir else None
    sitrep_path = stt_job_dir / "sitrep.json" if stt_job_dir else None

    voice_file_path = None
    if voice_path_for_search and Path(voice_path_for_search).exists():
        voice_file_path = Path(voice_path_for_search)
    elif pair_id:
        candidate = ROOT_DIR / "data" / f"voice_{pair_id}.txt"
        if candidate.exists():
            voice_file_path = candidate

    speech_path = (
        pivot_dir / f"{video_stem}_speech.jsonl"
        if video_stem and pivot_dir.exists()
        else None
    )
    vision_path = (
        pivot_dir / f"{video_stem}_vision.jsonl"
        if video_stem and pivot_dir.exists()
        else None
    )
    merged_path = (
        pivot_dir / f"{video_stem}_merged.jsonl"
        if video_stem and pivot_dir.exists()
        else None
    )

    analysis_found = any(
        path and Path(path).exists()
        for path in [
            speech_path,
            vision_path,
            merged_path,
            segments_path,
            sitrep_path,
            voice_file_path,
        ]
    )

    if analysis_found:
        st.caption(f"Output directory: {output_dir_path}")
        if pivot_dir.exists():
            st.caption(f"Pivot timeline: {pivot_dir}")

        speech_rows = load_jsonl(speech_path) if speech_path and speech_path.exists() else []
        vision_rows = load_jsonl(vision_path) if vision_path and vision_path.exists() else []
        merged_rows = load_jsonl(merged_path) if merged_path and merged_path.exists() else []
        segments_df = None
        if segments_path and segments_path.exists():
            try:
                segments_df = pd.read_csv(segments_path)
            except Exception:
                segments_df = None
        sitrep_data = load_json(sitrep_path) if sitrep_path and sitrep_path.exists() else None

        metrics_cols = st.columns(4)
        metrics_cols[0].metric("Speech events", len(speech_rows) if speech_rows else "N/A")
        metrics_cols[1].metric("Vision events", len(vision_rows) if vision_rows else "N/A")
        metrics_cols[2].metric("Merged events", len(merged_rows) if merged_rows else "N/A")
        metrics_cols[3].metric(
            "STT segments", len(segments_df) if segments_df is not None else "N/A"
        )

        tabs = st.tabs(
            [
                "Merged timeline",
                "Speech events",
                "Vision events",
                "STT segments",
                "SITREP summary",
                "Raw transcript",
            ]
        )

        with tabs[0]:
            if merged_rows:
                flattened = []
                for row in merged_rows:
                    entry = dict(row)
                    entry["timestamp"] = format_time_value(entry.get("t"))
                    targets = entry.get("targets")
                    if isinstance(targets, list):
                        entry["targets"] = ", ".join(str(t) for t in targets)
                    context = entry.pop("speech_context", None)
                    if isinstance(context, dict):
                        entry["context_window"] = (
                            f"{format_time_value(context.get('t_start'))}–"
                            f"{format_time_value(context.get('t_end'))}"
                        )
                        entry["context_text"] = context.get("text", "")
                    flattened.append(entry)
                merged_df = pd.DataFrame(flattened)
                st.dataframe(merged_df, use_container_width=True)
                if merged_path and merged_path.exists():
                    st.download_button(
                        "Download merged timeline (JSONL)",
                        data=Path(merged_path).read_bytes(),
                        file_name=Path(merged_path).name,
                        use_container_width=True,
                    )
            else:
                st.info("Merged timeline not available.")

        with tabs[1]:
            if speech_rows:
                speech_preview = []
                for row in speech_rows:
                    entry = dict(row)
                    entry["timestamp"] = format_time_value(entry.get("t"))
                    entry["window"] = (
                        f"{format_time_value(entry.get('t_start'))}–"
                        f"{format_time_value(entry.get('t_end'))}"
                    )
                    speech_preview.append(entry)
                speech_df = pd.DataFrame(speech_preview)
                st.dataframe(speech_df, use_container_width=True)
                if speech_path and speech_path.exists():
                    st.download_button(
                        "Download speech events (JSONL)",
                        data=Path(speech_path).read_bytes(),
                        file_name=Path(speech_path).name,
                        use_container_width=True,
                    )
            else:
                st.info("Speech events not available.")

        with tabs[2]:
            if vision_rows:
                vision_preview = []
                for row in vision_rows:
                    entry = dict(row)
                    entry["timestamp"] = format_time_value(entry.get("t"))
                    targets = entry.get("targets")
                    if isinstance(targets, list):
                        entry["targets"] = ", ".join(str(t) for t in targets)
                    vision_preview.append(entry)
                vision_df = pd.DataFrame(vision_preview)
                st.dataframe(vision_df, use_container_width=True)
                if vision_path and vision_path.exists():
                    st.download_button(
                        "Download vision events (JSONL)",
                        data=Path(vision_path).read_bytes(),
                        file_name=Path(vision_path).name,
                        use_container_width=True,
                    )
            else:
                st.info("Vision events not available.")

        with tabs[3]:
            if segments_df is not None and not segments_df.empty:
                if "start" in segments_df.columns:
                    segments_df["start_ts"] = segments_df["start"].apply(format_time_value)
                if "end" in segments_df.columns:
                    segments_df["end_ts"] = segments_df["end"].apply(format_time_value)
                st.dataframe(segments_df, use_container_width=True)
                if segments_path and segments_path.exists():
                    st.download_button(
                        "Download STT segments (CSV)",
                        data=Path(segments_path).read_bytes(),
                        file_name=Path(segments_path).name,
                        use_container_width=True,
                    )
            else:
                st.info("STT segments not available.")

        with tabs[4]:
            if sitrep_data:
                meta = sitrep_data.get("meta", {})
                signal = sitrep_data.get("signal_intelligence", {})
                tactical = sitrep_data.get("tactical_intelligence", {})
                sitrep_cols = st.columns(4)
                sitrep_cols[0].metric(
                    "Audio duration",
                    format_time_value(meta.get("duration_sec")) if meta else "N/A",
                )
                sitrep_cols[1].metric("Total words", meta.get("total_words", "N/A"))
                sitrep_cols[2].metric(
                    "Integrity score", signal.get("integrity_score", "N/A")
                )
                sitrep_cols[3].metric(
                    "Threat level", tactical.get("threat_level", "N/A")
                )
                st.json(sitrep_data)
                if sitrep_path and sitrep_path.exists():
                    st.download_button(
                        "Download SITREP (JSON)",
                        data=Path(sitrep_path).read_bytes(),
                        file_name=Path(sitrep_path).name,
                        use_container_width=True,
                    )
            else:
                st.info("SITREP summary not available.")

        with tabs[5]:
            if voice_file_path and voice_file_path.exists():
                voice_text = voice_file_path.read_text(encoding="utf-8")
                st.text_area(
                    "Voice transcript file",
                    value=voice_text,
                    height=320,
                )
                st.download_button(
                    "Download transcript (voice file)",
                    data=voice_text.encode("utf-8"),
                    file_name=voice_file_path.name,
                    use_container_width=True,
                )
            else:
                st.info("Transcript file not available.")
    else:
        st.info("Run the pipeline to generate analysis outputs.")

if summary_data or video_report_data or voice_segments:
    st.markdown(
        "<div class='section-title'>Search transcript & entities</div>",
        unsafe_allow_html=True,
    )

    entities = video_report_data.get("entities", {}) if video_report_data else {}
    recommendations = recommend_search_terms(entities, voice_segments)

    if "search_query" not in st.session_state:
        st.session_state["search_query"] = ""

    if recommendations:
        st.markdown("<div class='panel'>", unsafe_allow_html=True)
        st.subheader("Recommended searches")
        st.caption("Click a suggestion to fill the search box.")
        rows = [recommendations[i : i + 4] for i in range(0, len(recommendations), 4)]
        for row_index, row in enumerate(rows):
            cols = st.columns(len(row))
            for col, term in zip(cols, row):
                if col.button(term, key=f"rec_{row_index}_{term}"):
                    st.session_state["search_query"] = term
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<div class='panel'>", unsafe_allow_html=True)
    query = st.text_input(
        "Search keywords",
        placeholder="e.g., drone, convoy, AAB960A",
        key="search_query",
    )
    st.caption(
        "Search across transcript text, callsigns, vehicle types, and detected entities."
    )
    st.markdown("</div>", unsafe_allow_html=True)

    if query:
        query_lower = query.lower().strip()

        entity_rows = []
        presence_rows = []
        for name, data in entities.items():
            if query_lower in name.lower():
                stats = data.get("statistics", {})
                detections = data.get("detections", [])
                present = [d for d in detections if d.get("present")]
                present_sorted = sorted(present, key=lambda d: d.get("second", 0))
                times = [
                    d.get("timestamp") for d in present_sorted if d.get("timestamp")
                ]
                first_seen = times[0] if times else "N/A"
                last_seen = times[-1] if times else "N/A"

                entity_rows.append(
                    {
                        "entity": name,
                        "frames_confirmed": stats.get("frames_with_entity", 0),
                        "presence_percent": stats.get("presence_percentage", "N/A"),
                        "first_seen": first_seen,
                        "last_seen": last_seen,
                    }
                )
                for detection in present_sorted:
                    presence_rows.append(
                        {
                            "entity": name,
                            "second": detection.get("second", 0),
                            "timestamp": detection.get("timestamp", ""),
                        }
                    )

        transcript_hits, transcript_matches = search_transcript(voice_segments, query)

        metrics = st.columns(2)
        metrics[0].metric("Matching entities", len(entity_rows))
        metrics[1].metric("Transcript hits", transcript_hits)

        st.markdown("<div class='panel'>", unsafe_allow_html=True)
        st.subheader("AI explanation")
        if transcript_hits:
            st.write(
                f"The keyword '{query}' appears {transcript_hits} time(s) in the transcript "
                f"across {len(transcript_matches)} segment(s)."
            )
        else:
            st.write(
                f"The keyword '{query}' was not found in the transcript. "
                "If you still see detections below, those come from vision analysis."
            )
        if entity_rows:
            top_entity = max(
                entity_rows, key=lambda row: row.get("frames_confirmed", 0)
            )
            st.write(
                "Vision detections found. Strongest match: "
                f"{top_entity['entity']} "
                f"({top_entity['frames_confirmed']} confirmed frame(s))."
            )
        else:
            st.write("No matching entities detected in vision results.")
        st.markdown("</div>", unsafe_allow_html=True)

        if transcript_hits:
            keyword_rows = []
            for match in transcript_matches:
                second = timestamp_to_seconds(match.get("timestamp", ""))
                if second is None:
                    continue
                keyword_rows.append(
                    {
                        "second": second,
                        "timestamp": match.get("timestamp", ""),
                        "hits": int(match.get("hits", 0) or 0),
                        "text": match.get("text", ""),
                    }
                )

            if keyword_rows:
                keyword_df = pd.DataFrame(keyword_rows)
                total_occurrences = int(keyword_df["hits"].sum())
                unique_segments = keyword_df["timestamp"].nunique()
                first_row = keyword_df.sort_values("second").head(1).to_dict("records")[0]
                last_row = keyword_df.sort_values("second").tail(1).to_dict("records")[0]

                st.subheader("Keyword overview")
                summary_cols = st.columns(4)
                summary_cols[0].metric("Occurrences", total_occurrences)
                summary_cols[1].metric("Transcript segments", unique_segments)
                summary_cols[2].metric("First mention", first_row["timestamp"])
                summary_cols[3].metric("Last mention", last_row["timestamp"])

                duration_seconds = max_segment_seconds(voice_segments)
                if duration_seconds is None:
                    duration_seconds = int(keyword_df["second"].max())

                bin_seconds = 30
                bins = []
                total_bins = int(duration_seconds // bin_seconds) + 1
                hits_by_bin = keyword_df.groupby(
                    (keyword_df["second"] // bin_seconds) * bin_seconds
                )["hits"].sum()
                for idx in range(total_bins):
                    start = idx * bin_seconds
                    end = start + bin_seconds
                    bins.append(
                        {
                            "window_start": start,
                            "window_end": end,
                            "hits": int(hits_by_bin.get(start, 0)),
                            "label": f"{format_seconds(start)}–{format_seconds(end)}",
                        }
                    )

                bin_df = pd.DataFrame(bins)
                st.subheader("Keyword timeline (30s bins)")
                st.caption("Bars show how often the keyword appears over the video timeline.")
                try:
                    import altair as alt

                    timeline_chart = (
                        alt.Chart(bin_df)
                        .mark_bar(color="#0b4dd9")
                        .encode(
                            x=alt.X("window_start:Q", title="Second"),
                            y=alt.Y("hits:Q", title="Occurrences"),
                            tooltip=["label", "hits"],
                        )
                        .properties(height=220)
                        .configure_view(fill="#ffffff", strokeOpacity=0)
                        .configure(background="#ffffff")
                        .configure_axis(
                            labelColor="#0b1020",
                            titleColor="#0b1020",
                            gridColor="#e2e8f0",
                            tickColor="#cbd5f5",
                        )
                    )
                    st.altair_chart(timeline_chart, use_container_width=True)
                except Exception:
                    st.bar_chart(bin_df.set_index("window_start")["hits"])

                st.subheader("Exact transcript mentions")
                mention_df = keyword_df[["timestamp", "hits", "text"]].copy()
                mention_df.rename(
                    columns={
                        "timestamp": "timestamp",
                        "hits": "occurrences",
                        "text": "transcript snippet",
                    },
                    inplace=True,
                )
                st.dataframe(mention_df, use_container_width=True)

        tabs = st.tabs(["Entity matches", "Transcript matches"])
        with tabs[0]:
            if entity_rows:
                st.dataframe(pd.DataFrame(entity_rows), use_container_width=True)
                if presence_rows:
                    st.subheader("Presence summary")
                    presence_df = pd.DataFrame(presence_rows)
                    presence_counts = (
                        presence_df.groupby("entity")["second"]
                        .count()
                        .reset_index(name="detections")
                        .sort_values("detections", ascending=False)
                    )
                    try:
                        import altair as alt

                        chart = (
                            alt.Chart(presence_counts)
                            .mark_bar(color="#0b4dd9")
                            .encode(
                                x=alt.X("detections:Q", title="Confirmed frames"),
                                y=alt.Y("entity:N", sort="-x", title="Entity"),
                                tooltip=["entity", "detections"],
                            )
                            .properties(height=max(160, 32 * len(presence_counts)))
                            .configure_view(fill="#ffffff", strokeOpacity=0)
                            .configure(background="#ffffff")
                            .configure_axis(
                                labelColor="#0b1020",
                                titleColor="#0b1020",
                                gridColor="#e2e8f0",
                                tickColor="#cbd5f5",
                            )
                        )
                        st.altair_chart(chart, use_container_width=True)
                    except Exception:
                        presence_chart_df = presence_counts.set_index("entity")["detections"]
                        st.bar_chart(presence_chart_df)

                    preview_rows = []
                    for entity_name, group in presence_df.groupby("entity"):
                        timestamps = [
                            ts for ts in group["timestamp"].dropna().astype(str).tolist() if ts
                        ]
                        if not timestamps:
                            timestamps = [str(sec) for sec in group["second"].tolist()]
                        preview = ", ".join(timestamps[:12])
                        if len(timestamps) > 12:
                            preview += " ..."
                        preview_rows.append(
                            {"entity": entity_name, "timestamps": preview}
                        )
                    preview_df = pd.DataFrame(preview_rows)
                    preview_df = preview_df.merge(
                        presence_counts, left_on="entity", right_on="entity", how="left"
                    ).sort_values("detections", ascending=False)
                    st.dataframe(
                        preview_df[["entity", "timestamps", "detections"]],
                        use_container_width=True,
                    )
            else:
                st.info("No entity matches for this keyword.")

        with tabs[1]:
            if transcript_matches:
                st.dataframe(pd.DataFrame(transcript_matches), use_container_width=True)
            else:
                st.info("No transcript matches for this keyword.")

st.markdown("<div id='downloads' class='section-anchor'></div>", unsafe_allow_html=True)
if summary_path or video_report_path:
    st.markdown("<div class='section-title'>Download reports</div>", unsafe_allow_html=True)
    st.markdown(
        "<div class='section-subtitle'>Export the intelligence outputs for sharing or archive.</div>",
        unsafe_allow_html=True,
    )
    download_cols = st.columns(2)
    if summary_path and Path(summary_path).exists():
        with open(summary_path, "rb") as handle:
            download_cols[0].download_button(
                "Download summary report",
                handle,
                file_name=Path(summary_path).name,
                use_container_width=True,
            )
    else:
        download_cols[0].download_button(
            "Summary report not available",
            data=b"",
            file_name="summary_report.json",
            disabled=True,
            use_container_width=True,
        )

    if video_report_path and Path(video_report_path).exists():
        with open(video_report_path, "rb") as handle:
            download_cols[1].download_button(
                "Download video report",
                handle,
                file_name=Path(video_report_path).name,
                use_container_width=True,
            )
    else:
        download_cols[1].download_button(
            "Video report not available",
            data=b"",
            file_name="video_report.json",
            disabled=True,
            use_container_width=True,
        )

    if csv_report_path and Path(csv_report_path).exists():
        st.download_button(
            "Download Thales CSV",
            data=Path(csv_report_path).read_bytes(),
            file_name=Path(csv_report_path).name,
            use_container_width=True,
        )
else:
    st.info("Run the pipeline to generate downloadable reports.")

st.markdown("<div id='faq' class='section-anchor'></div>", unsafe_allow_html=True)
st.markdown("<div class='section-title'>FAQ</div>", unsafe_allow_html=True)
st.markdown(
    "<div class='section-subtitle'>Common questions about this project.</div>",
    unsafe_allow_html=True,
)
faq_items = [
    (
        "What operational problem does this solve?",
        "It turns raw video into a searchable intelligence package by aligning "
        "speech, detected entities, and scene summaries on a single timeline."
    ),
    (
        "How is evidence traceability handled?",
        "Every detection is tied to a timestamp and stored in the report JSON. "
        "The timeline can be exported for audit or downstream review."
    ),
    (
        "What is the expected false-positive risk?",
        "Detections are based on sampled frames. Lower sampling intervals improve "
        "coverage but increase compute cost. Human review is still required."
    ),
    (
        "Can this run in an air-gapped or on-prem environment?",
        "Yes, but you need local model hosting or approved API connectivity for "
        "the Mistral/Pixtral calls. The UI can remain local."
    ),
    (
        "What data is sent to external services?",
        "If you use Mistral/Pixtral APIs, frame images and transcript segments are sent "
        "for analysis. To avoid that, deploy an on-prem model endpoint."
    ),
    (
        "What are the performance requirements?",
        "CPU-only works for smaller runs, but GPU accelerates vision analysis. "
        "Frame interval and max frames control runtime."
    ),
    (
        "How does the system handle low-quality audio or missing speech?",
        "If transcription is empty, the pipeline falls back to a baseline vision scan "
        "using known entity categories."
    ),
    (
        "Can results be tuned or validated?",
        "Yes. Analysts can adjust frame intervals, inspect per-frame detections, "
        "and verify outputs using the exported reports."
    ),
    (
        "Does it support multi-analyst review?",
        "Outputs are JSON/CSV and can be shared or versioned; the app does not "
        "yet include collaborative review workflows."
    ),
    (
        "What are the main limitations?",
        "It samples frames rather than analyzing every frame, and it depends on "
        "model accuracy for both transcription and vision verification."
    ),
]

for question, answer in faq_items:
    with st.expander(question):
        st.write(answer)
