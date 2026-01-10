import base64
import json
import os
import shutil
import sys
import time
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
@import url('https://fonts.googleapis.com/css2?family=Sora:wght@300;400;500;600;700&family=IBM+Plex+Mono:wght@400;500&display=swap');

:root {
  --navy: #0f172a;
  --navy-dark: #0b1020;
  --blue: #2563eb;
  --cyan: #22d3ee;
  --amber: #f59e0b;
  --bg: #f5f7fb;
  --card: #ffffff;
  --glass: rgba(255, 255, 255, 0.72);
  --muted: #2b3a4d;
  --border: rgba(15, 23, 42, 0.12);
  --shadow: 0 18px 45px rgba(15, 23, 42, 0.12);
  --shadow-soft: 0 10px 24px rgba(15, 23, 42, 0.08);
}

* {
  box-sizing: border-box;
}

html, body, [class*="css"] {
  font-family: "Sora", sans-serif;
  color: var(--navy);
}

.stMarkdown p {
  color: var(--navy);
}

div[data-testid="stCaption"] p {
  color: var(--muted);
  font-size: 0.85rem;
}

body {
  background-color: var(--bg);
  margin: 0;
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
    radial-gradient(900px 600px at -10% -20%, rgba(34, 211, 238, 0.18), transparent 60%),
    radial-gradient(820px 520px at 110% 10%, rgba(37, 99, 235, 0.16), transparent 55%),
    repeating-linear-gradient(0deg, rgba(15, 23, 42, 0.05), rgba(15, 23, 42, 0.05) 1px, transparent 1px, transparent 120px),
    repeating-linear-gradient(90deg, rgba(15, 23, 42, 0.05) 0, rgba(15, 23, 42, 0.05) 1px, transparent 1px, transparent 120px),
    linear-gradient(180deg, #f6f8fc 0%, #edf2fb 55%, #fdfdff 100%);
}

section[data-testid="stSidebar"] {
  display: none;
}

.block-container {
  padding-top: 1rem;
  max-width: 1240px;
}

.top-nav {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1.5rem;
  padding: 0.8rem 1.3rem;
  border: 1px solid var(--border);
  border-radius: 18px;
  background: var(--glass);
  backdrop-filter: blur(12px);
  box-shadow: var(--shadow-soft);
}

.logo {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.logo-img {
  height: 28px;
  filter: drop-shadow(0 6px 12px rgba(15, 23, 42, 0.2));
}

.logo-text {
  font-weight: 700;
  letter-spacing: 0.35rem;
  color: var(--navy);
  font-size: 1.2rem;
}

.nav-links {
  display: flex;
  flex-wrap: wrap;
  gap: 0.6rem;
  font-weight: 600;
  font-size: 0.78rem;
  letter-spacing: 0.08rem;
  text-transform: uppercase;
  color: #273447;
  justify-content: center;
  flex: 1;
}

.nav-links span {
  padding: 0.35rem 0.6rem;
  border-radius: 999px;
  background: rgba(15, 23, 42, 0.08);
}

.nav-sub {
  margin-top: 0.25rem;
  font-size: 0.8rem;
  color: var(--muted);
}

.hero {
  position: relative;
  display: grid;
  grid-template-columns: minmax(0, 1.3fr) minmax(0, 0.7fr);
  gap: 2rem;
  align-items: center;
  margin: 1.8rem 0 1.8rem 0;
  padding: 2.1rem 2.4rem;
  background: rgba(255, 255, 255, 0.86);
  border: 1px solid var(--border);
  border-radius: 28px;
  box-shadow: var(--shadow);
  overflow: hidden;
}

.hero::before {
  content: "";
  position: absolute;
  left: -120px;
  bottom: -120px;
  width: 260px;
  height: 260px;
  background: radial-gradient(circle, rgba(34, 211, 238, 0.25), transparent 60%);
}

.hero::after {
  content: "";
  position: absolute;
  right: -140px;
  top: -140px;
  width: 320px;
  height: 320px;
  background: radial-gradient(circle, rgba(37, 99, 235, 0.25), transparent 60%);
}

.hero > div {
  position: relative;
  z-index: 1;
}

.kicker {
  text-transform: uppercase;
  letter-spacing: 0.2rem;
  font-size: 0.72rem;
  color: var(--muted);
  font-weight: 600;
}

.hero h1 {
  font-size: 2.7rem;
  line-height: 1.06;
  margin: 0.4rem 0 0.7rem 0;
}

.hero p {
  color: var(--muted);
  font-size: 1.04rem;
  max-width: 46ch;
}

.card {
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: 20px;
  padding: 1.4rem 1.5rem;
  box-shadow: var(--shadow-soft);
  position: relative;
  overflow: hidden;
}

.card::after {
  content: "";
  position: absolute;
  right: -40px;
  top: -40px;
  width: 120px;
  height: 120px;
  border-radius: 50%;
  background: radial-gradient(circle, rgba(245, 158, 11, 0.2), transparent 60%);
}

.panel-title {
  text-transform: uppercase;
  letter-spacing: 0.18rem;
  font-size: 0.72rem;
  color: var(--muted);
  margin-bottom: 0.5rem;
}

.panel-value {
  font-size: 1.6rem;
  font-weight: 600;
  color: var(--navy);
}

.panel-sub {
  color: var(--muted);
  margin-top: 0.4rem;
}

.status-pill {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  border-radius: 999px;
  padding: 0.25rem 0.75rem;
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.08rem;
  border: 1px solid var(--border);
  margin-top: 0.6rem;
}

.status-pill.ok {
  color: #0f5f4d;
  background: rgba(20, 184, 166, 0.15);
}

.status-pill.warn {
  color: #a64217;
  background: rgba(245, 158, 11, 0.18);
}

.domain-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: 1.5rem;
  margin: 1.2rem 0 2.2rem 0;
}

.domain-card {
  position: relative;
  border-radius: 22px;
  min-height: 210px;
  overflow: hidden;
  display: flex;
  align-items: flex-end;
  box-shadow: var(--shadow-soft);
  border: 1px solid var(--border);
  background-size: cover;
  background-position: center;
  transition: transform 0.25s ease, box-shadow 0.25s ease;
}

.domain-card::before {
  content: "";
  position: absolute;
  inset: 0;
  background: linear-gradient(120deg, rgba(12, 22, 64, 0.12), rgba(12, 22, 64, 0.55));
}

.domain-card .domain-content {
  position: relative;
  z-index: 1;
  margin: 1.2rem;
  padding: 1rem 1.2rem;
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.85);
  color: var(--navy);
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: calc(100% - 2.4rem);
  backdrop-filter: blur(8px);
}

.domain-card .domain-title {
  font-size: 1.1rem;
  font-weight: 600;
}

.domain-card .domain-arrow {
  width: 38px;
  height: 38px;
  border-radius: 50%;
  background: linear-gradient(135deg, var(--cyan), var(--blue));
  color: #fff;
  display: grid;
  place-items: center;
  font-weight: 700;
}

.domain-card:hover {
  transform: translateY(-4px);
  box-shadow: var(--shadow);
}

.domain-card.defense {
  background-image:
    linear-gradient(140deg, rgba(12, 22, 64, 0.1), rgba(12, 22, 64, 0.8)),
    radial-gradient(circle at 20% 20%, rgba(38, 135, 201, 0.55), transparent 60%);
}

.domain-card.aero {
  background-image:
    linear-gradient(160deg, rgba(10, 20, 50, 0.1), rgba(9, 23, 68, 0.9)),
    radial-gradient(circle at 80% 20%, rgba(81, 169, 255, 0.6), transparent 55%);
}

.domain-card.cyber {
  background-image:
    linear-gradient(150deg, rgba(18, 28, 74, 0.1), rgba(15, 23, 58, 0.9)),
    radial-gradient(circle at 15% 80%, rgba(126, 185, 255, 0.5), transparent 60%);
}

.section-title {
  font-size: 1.2rem;
  font-weight: 600;
  margin: 2.2rem 0 1rem 0;
  position: relative;
}

.section-title::after {
  content: "";
  display: block;
  width: 64px;
  height: 3px;
  margin-top: 0.5rem;
  border-radius: 999px;
  background: linear-gradient(90deg, var(--blue), var(--cyan));
}

.panel {
  background: rgba(255, 255, 255, 0.92);
  border: 1px solid var(--border);
  border-radius: 20px;
  padding: 1.3rem 1.5rem;
  box-shadow: var(--shadow-soft);
  position: relative;
}

.panel label, .panel .stMarkdown {
  color: var(--navy);
}

.panel label {
  font-weight: 600;
}

section[data-testid="stFileUploader"] > div {
  border-radius: 16px;
  border: 1px dashed rgba(15, 23, 42, 0.2);
  background: rgba(255, 255, 255, 0.75);
}

div[data-baseweb="input"] input,
div[data-baseweb="textarea"] textarea {
  background: rgba(255, 255, 255, 0.9);
  border: 1px solid rgba(15, 23, 42, 0.16);
  border-radius: 12px;
  padding: 0.55rem 0.75rem;
  box-shadow: inset 0 1px 1px rgba(15, 23, 42, 0.05);
}

div[data-baseweb="input"] input:focus,
div[data-baseweb="textarea"] textarea:focus {
  border-color: var(--blue);
  box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.16);
}

div[data-baseweb="select"] > div {
  background: rgba(255, 255, 255, 0.9);
  border: 1px solid rgba(15, 23, 42, 0.16);
  border-radius: 12px;
}

div[data-baseweb="tab-list"] {
  gap: 0.4rem;
  padding: 0.3rem;
  background: rgba(255, 255, 255, 0.65);
  border-radius: 999px;
  border: 1px solid var(--border);
}

div[data-baseweb="tab"] {
  border-radius: 999px;
  padding: 0.35rem 1rem;
}

div[data-testid="stMetric"] {
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: 16px;
  padding: 1rem;
  box-shadow: var(--shadow-soft);
}

details[data-testid="stExpander"] {
  border: 1px solid var(--border);
  border-radius: 16px;
  background: rgba(255, 255, 255, 0.8);
  padding: 0.2rem 0.8rem;
  box-shadow: var(--shadow-soft);
}

.feature-row {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 1.2rem;
  margin: 0.4rem 0 2rem 0;
}

.feature-card {
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: 18px;
  padding: 1.1rem 1.2rem;
  box-shadow: var(--shadow-soft);
  position: relative;
  overflow: hidden;
}

.feature-card::after {
  content: "";
  position: absolute;
  right: -40px;
  bottom: -40px;
  width: 120px;
  height: 120px;
  border-radius: 50%;
  background: radial-gradient(circle, rgba(34, 211, 238, 0.2), transparent 60%);
}

.feature-tag {
  text-transform: uppercase;
  letter-spacing: 0.18rem;
  font-size: 0.65rem;
  color: var(--muted);
  font-weight: 600;
}

.feature-title {
  font-size: 1.05rem;
  font-weight: 600;
  margin: 0.4rem 0 0.35rem 0;
}

.feature-body {
  color: #263243;
  font-size: 0.92rem;
  line-height: 1.45;
}

div.stButton > button {
  background: linear-gradient(120deg, var(--navy), var(--blue));
  color: #fff;
  border-radius: 12px;
  padding: 0.65rem 1.8rem;
  font-weight: 600;
  border: none;
  box-shadow: 0 14px 26px rgba(15, 23, 42, 0.18);
  transition: transform 0.2s ease, box-shadow 0.2s ease, filter 0.2s ease;
}

div.stButton > button::after {
  content: " →";
}

div.stButton > button:hover {
  transform: translateY(-2px);
  box-shadow: 0 18px 32px rgba(15, 23, 42, 0.22);
  filter: brightness(1.02);
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

  .top-nav {
    flex-direction: column;
    align-items: flex-start;
    padding: 0.8rem;
  }

  .nav-links {
    display: none;
  }

  .hero h1 {
    font-size: 2.2rem;
  }

  .feature-row {
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
status_label = "API key set" if api_key_present else "API key missing"
mode_label = "Live mode" if api_key_present else "Add API key"

st.markdown(
    f"""
<div class="top-nav fade-up">
  <div>
    <div class="logo">
      {logo_html}
    </div>
    <div class="nav-sub">Groupe</div>
  </div>
  <div class="nav-links">
    <span>Defense</span>
    <span>Public Security</span>
    <span>Civil Aviation</span>
    <span>Space</span>
    <span>Industry & Services</span>
    <span>Cybersecurity</span>
    <span>Advanced Tech</span>
  </div>
</div>

<div class="hero fade-up">
  <div>
    <div class="kicker">Domains of expertise</div>
    <h1>Thales Video Indexing</h1>
    <p>
      Operational-grade indexing that aligns speech and vision into a single
      timeline, ready for analysts and downstream AI training.
    </p>
  </div>
  <div class="card">
    <div class="panel-title">Session status</div>
    <div class="panel-value">{mode_label}</div>
    <div class="panel-sub">Configure inputs and run the pipeline below.</div>
    <div class="status-pill {status_class}">{status_label}</div>
  </div>
</div>

<div class="feature-row fade-up">
  <div class="feature-card">
    <div class="feature-tag">Step 01</div>
    <div class="feature-title">Audio extraction</div>
    <div class="feature-body">
      Automatic speech-to-text with mission context and signal quality scoring.
    </div>
  </div>
  <div class="feature-card">
    <div class="feature-tag">Step 02</div>
    <div class="feature-title">Vision scan</div>
    <div class="feature-body">
      Frame sampling with strict entity verification and timestamped detections.
    </div>
  </div>
  <div class="feature-card">
    <div class="feature-tag">Step 03</div>
    <div class="feature-title">Fusion timeline</div>
    <div class="feature-body">
      Speech and vision aligned into a single narrative for analysis and export.
    </div>
  </div>
</div>

<div class="domain-grid fade-up">
  <div class="domain-card defense">
    <div class="domain-content">
      <div class="domain-title">Defense</div>
      <div class="domain-arrow">→</div>
    </div>
  </div>
  <div class="domain-card aero">
    <div class="domain-content">
      <div class="domain-title">Aerospace</div>
      <div class="domain-arrow">→</div>
    </div>
  </div>
  <div class="domain-card cyber">
    <div class="domain-content">
      <div class="domain-title">Cyber & Digital</div>
      <div class="domain-arrow">→</div>
    </div>
  </div>
</div>
""",
    unsafe_allow_html=True,
)

st.markdown("<div class='section-title'>Run the pipeline</div>", unsafe_allow_html=True)

selected_video = None
video_upload = None

form_cols = st.columns([1.25, 0.75], gap="large")
with form_cols[0]:
    st.markdown("<div class='panel'>", unsafe_allow_html=True)
    st.subheader("Upload video")
    use_existing = st.toggle("Use an existing video from data/", value=False)

    if use_existing:
        videos = find_videos(DATA_DIR)
        if not videos:
            st.warning("No videos found in data/. Upload a video instead.")
        else:
            labels = {format_video_label(video): video for video in videos}
            selected_label = st.selectbox("Select a video", list(labels.keys()))
            selected_video = labels[selected_label]
    else:
        video_upload = st.file_uploader(
            "Video file", type=[ext.strip(".") for ext in ALLOWED_VIDEO_EXTS]
        )
        st.caption("Supported formats: mp4, mkv, avi, mov. Transcript is auto-generated.")
    st.markdown("</div>", unsafe_allow_html=True)

with form_cols[1]:
    st.markdown("<div class='panel'>", unsafe_allow_html=True)
    st.subheader("Run pipeline")
    st.caption("Click run to extract audio, transcribe, and detect entities.")
    with st.expander("Advanced settings", expanded=False):
        frame_interval = st.number_input(
            "Frame interval (seconds)", min_value=1, value=30, step=1
        )
        output_dir_input = st.text_input("Output directory", value="reports_ui")
    ready_to_run = api_key_present and bool(selected_video or video_upload)
    if not api_key_present:
        st.error("MISTRAL_API_KEY is missing. Add it in Streamlit secrets.")
    elif not (selected_video or video_upload):
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
            errors.append("Select a video from data/.")
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
    st.header("Results")

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
    st.markdown("<div class='section-title'>Search & Insights</div>", unsafe_allow_html=True)
    st.markdown("<div class='panel'>", unsafe_allow_html=True)
    query = st.text_input(
        "Search keywords",
        placeholder="e.g., drone, convoy, AAB960A",
    )
    st.markdown("</div>", unsafe_allow_html=True)

    if query:
        query_lower = query.lower().strip()
        entities = video_report_data.get("entities", {}) if video_report_data else {}

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
