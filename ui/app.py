import base64
import json
import os
import re
import shutil
import sys
import time
from collections import Counter
from pathlib import Path

import pandas as pd
import streamlit as st
from dotenv import load_dotenv

from utils import ALLOWED_VIDEO_EXTS, find_videos, run_pipeline

ROOT_DIR = Path(__file__).resolve().parents[1]
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

.section-title {
  color: var(--ink);
  font-size: 1.25rem;
  font-weight: 600;
  margin: 2rem 0 0.4rem 0;
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
  margin-bottom: 1rem;
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
  filter: brightness(0.98);
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
  background: #0f172a;
  color: #ffffff;
  border-radius: 12px;
  padding: 0.6rem 1.6rem;
  font-weight: 600;
  border: none;
  box-shadow: 0 12px 22px rgba(12, 18, 36, 0.2);
}

div[data-testid="stDownloadButton"] > button:hover {
  filter: brightness(1.05);
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

<div class="deliverables fade-up">
  <div class="deliverable-card">
    <div class="deliverable-title">Entity report</div>
    <div class="deliverable-body">
      Per-entity detections, confidence stats, and time ranges.
    </div>
  </div>
  <div class="deliverable-card">
    <div class="deliverable-title">Merged timeline</div>
    <div class="deliverable-body">
      Speech and vision events aligned into a single JSONL stream.
    </div>
  </div>
  <div class="deliverable-card">
    <div class="deliverable-title">Exports</div>
    <div class="deliverable-body">
      Summary report plus optional CSV for downstream systems.
    </div>
  </div>
</div>
""",
    unsafe_allow_html=True,
)

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
    with st.expander("Developer options", expanded=False):
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
    with st.expander("Processing options", expanded=False):
        frame_interval = st.number_input(
            "Frame interval (seconds)", min_value=1, value=30, step=1
        )
        output_dir_input = st.text_input("Output directory", value="reports_ui")
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
            log_placeholder.code(logs_text)

        status_placeholder.info(
            "Running the pipeline. First-time model downloads can take a few minutes."
        )
        with st.spinner("Running the pipeline..."):
            returncode, logs_text, produced_files = run_pipeline(
                sys.executable,
                run_dir or data_dir,
                int(frame_interval),
                out_dir,
                env_overrides,
                selected_pair_id=None,
                log_callback=on_log,
            )

        if pair_id:
            generated_voice = ROOT_DIR / "data" / f"voice_{pair_id}.txt"
            if generated_voice.exists():
                st.session_state["voice_path"] = str(generated_voice)

        st.session_state["logs"] = logs_text
        st.session_state["produced_files"] = produced_files
        st.session_state["returncode"] = returncode

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

if summary_path or video_report_path:
    st.markdown("<div class='section-title'>Results</div>", unsafe_allow_html=True)

summary_data = load_json(Path(summary_path)) if summary_path else None
video_report_data = load_json(Path(video_report_path)) if video_report_path else None

if summary_data or video_report_data:
    entity_count = None
    total_videos = None
    total_confirmed_frames = None

    if summary_data:
        entity_count = summary_data.get("unique_entity_count")
        total_videos = summary_data.get("total_videos")

    if video_report_data:
        entities = video_report_data.get("entities", {})
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
        entities = video_report_data.get("entities", {})
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

        entity_names = list(entities.keys())
        if entity_names:
            selected_entity = st.selectbox("Entity timeline", entity_names)
            entity_data = entities.get(selected_entity, {})
            detections = entity_data.get("detections", [])

            st.subheader(f"Timeline: {selected_entity}")
            if detections:
                timeline_rows = [
                    {"second": d.get("second", 0), "present": int(d.get("present", False))}
                    for d in detections
                ]
                timeline_df = pd.DataFrame(timeline_rows).sort_values("second")
                try:
                    import altair as alt

                    chart = (
                        alt.Chart(timeline_df)
                        .mark_line(color="#1d4ed8", strokeWidth=2)
                        .encode(
                            x=alt.X("second:Q", title="Second"),
                            y=alt.Y("present:Q", title="Presence"),
                        )
                        .properties(height=220)
                        .configure_view(strokeOpacity=0)
                        .configure_axis(
                            labelColor="#0b1020",
                            titleColor="#0b1020",
                            gridColor="#e2e8f0",
                            tickColor="#cbd5f5",
                        )
                    )
                    st.altair_chart(chart, use_container_width=True)
                except Exception:
                    st.line_chart(timeline_df.set_index("second"))

                present_times = [
                    d.get("timestamp") for d in detections if d.get("present")
                ]
                if present_times:
                    st.write("Present at:", ", ".join(present_times))
                else:
                    st.write("No confirmed frames for this entity.")
            elif entity_data.get("time_ranges"):
                st.write("Time ranges:")
                st.table(entity_data.get("time_ranges"))
            else:
                st.info("No timeline data available for this entity.")

voice_path_for_search = st.session_state.get("voice_path")
voice_segments = []
if voice_path_for_search:
    voice_path_obj = Path(voice_path_for_search)
    if voice_path_obj.exists():
        voice_segments = load_voice_segments(voice_path_obj)

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
        entity_times: dict[str, list[str]] = {}
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
                entity_times[name] = times

        transcript_hits, transcript_matches = search_transcript(voice_segments, query)

        metrics = st.columns(2)
        metrics[0].metric("Matching entities", len(entity_rows))
        metrics[1].metric("Transcript hits", transcript_hits)

        tabs = st.tabs(["Entity matches", "Transcript matches"])
        with tabs[0]:
            if entity_rows:
                st.dataframe(pd.DataFrame(entity_rows), use_container_width=True)
                for name, times in entity_times.items():
                    if times:
                        preview = ", ".join(times[:20])
                        suffix = " ..." if len(times) > 20 else ""
                        st.caption(f"{name} present at: {preview}{suffix}")
            else:
                st.info("No entity matches for this keyword.")

        with tabs[1]:
            if transcript_matches:
                st.dataframe(pd.DataFrame(transcript_matches), use_container_width=True)
            else:
                st.info("No transcript matches for this keyword.")

if summary_path and Path(summary_path).exists():
    with open(summary_path, "rb") as handle:
        st.download_button(
            "Download summary_report.json",
            handle,
            file_name=Path(summary_path).name,
        )

if video_report_path and Path(video_report_path).exists():
    with open(video_report_path, "rb") as handle:
        st.download_button(
            "Download video report JSON",
            handle,
            file_name=Path(video_report_path).name,
        )
