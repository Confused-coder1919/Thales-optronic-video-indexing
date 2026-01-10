import base64
import json
import os
import re
import sys
import time
from pathlib import Path

import pandas as pd
import streamlit as st
from dotenv import load_dotenv

from utils import ALLOWED_VIDEO_EXTS, find_pairs, run_pipeline

ROOT_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT_DIR / "data"
WORK_DIR = ROOT_DIR / "ui" / "work"
LOGO_SVG_PATH = ROOT_DIR / "ui" / "assets" / "thales-logo.svg"
TIMESTAMP_RE = re.compile(r"\(\d{2}:\d{2}\)")

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


def format_pair_label(pair: dict) -> str:
    voice_name = Path(pair["voice_path"]).name
    video_name = Path(pair["video_path"]).name
    return f"{pair['pair_id']}: {voice_name} + {video_name}"


def ensure_work_dir():
    WORK_DIR.mkdir(parents=True, exist_ok=True)


def validate_transcript(text_bytes: bytes) -> tuple[bool, bool]:
    try:
        text = text_bytes.decode("utf-8", errors="ignore")
    except Exception:
        return False, False
    if not text.strip():
        return False, False
    has_timestamps = bool(TIMESTAMP_RE.search(text))
    return True, has_timestamps


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
  --navy: #1b2a6d;
  --navy-dark: #121c4a;
  --blue: #2d5bda;
  --bg: #f8fbff;
  --card: #ffffff;
  --muted: #5c6b7a;
  --border: rgba(15, 23, 42, 0.12);
  --shadow: 0 18px 40px rgba(12, 22, 66, 0.08);
}

html, body, [class*="css"] {
  font-family: "Sora", sans-serif;
  color: var(--navy-dark);
}

.stApp {
  background:
    radial-gradient(900px 500px at -10% -20%, rgba(45, 91, 218, 0.12), transparent 60%),
    radial-gradient(700px 500px at 110% 10%, rgba(18, 28, 74, 0.12), transparent 55%),
    linear-gradient(180deg, #f7f9fc 0%, #f3f6fb 60%, #fbfcfe 100%);
}

section[data-testid="stSidebar"] {
  display: none;
}

.block-container {
  padding-top: 1.5rem;
  max-width: 1240px;
}

.top-nav {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1.5rem;
  padding: 0.6rem 0 1rem 0;
  border-bottom: 1px solid var(--border);
}

.logo {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.logo-img {
  height: 26px;
}

.logo-text {
  font-weight: 700;
  letter-spacing: 0.35rem;
  color: var(--navy);
  font-size: 1.3rem;
}

.nav-links {
  display: flex;
  flex-wrap: wrap;
  gap: 1.4rem;
  font-weight: 600;
  font-size: 0.9rem;
  color: var(--navy);
  justify-content: center;
  flex: 1;
}

.nav-sub {
  margin-top: 0.25rem;
  font-size: 0.8rem;
  color: var(--muted);
}

.hero {
  display: grid;
  grid-template-columns: minmax(0, 1.3fr) minmax(0, 0.8fr);
  gap: 2rem;
  align-items: center;
  margin: 2rem 0 1.6rem 0;
}

.kicker {
  text-transform: uppercase;
  letter-spacing: 0.2rem;
  font-size: 0.72rem;
  color: var(--muted);
  font-weight: 600;
}

.hero h1 {
  font-size: 2.6rem;
  line-height: 1.08;
  margin: 0.4rem 0 0.7rem 0;
}

.hero p {
  color: var(--muted);
  font-size: 1.05rem;
  max-width: 44ch;
}

.card {
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: 18px;
  padding: 1.2rem 1.3rem;
  box-shadow: var(--shadow);
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
  background: rgba(15, 118, 110, 0.12);
}

.status-pill.warn {
  color: #a64217;
  background: rgba(194, 65, 12, 0.12);
}

.domain-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: 1.5rem;
  margin: 1.8rem 0 2rem 0;
}

.domain-card {
  position: relative;
  border-radius: 22px;
  min-height: 210px;
  overflow: hidden;
  display: flex;
  align-items: flex-end;
  box-shadow: var(--shadow);
  background-size: cover;
  background-position: center;
}

.domain-card::before {
  content: "";
  position: absolute;
  inset: 0;
  background: linear-gradient(120deg, rgba(12, 22, 64, 0.2), rgba(12, 22, 64, 0.78));
}

.domain-card .domain-content {
  position: relative;
  z-index: 1;
  margin: 1.2rem;
  padding: 1rem 1.2rem;
  border-radius: 18px;
  background: rgba(17, 25, 60, 0.72);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: calc(100% - 2.4rem);
}

.domain-card .domain-title {
  font-size: 1.1rem;
  font-weight: 600;
}

.domain-card .domain-arrow {
  width: 38px;
  height: 38px;
  border-radius: 50%;
  background: #8ee6ff;
  color: var(--navy);
  display: grid;
  place-items: center;
  font-weight: 700;
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
  margin: 2rem 0 1rem 0;
}

.panel {
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: 18px;
  padding: 1.2rem 1.4rem;
  box-shadow: var(--shadow);
}

.panel label, .panel .stMarkdown {
  color: var(--navy-dark);
}

div.stButton > button {
  background: var(--navy);
  color: #fff;
  border-radius: 10px;
  padding: 0.6rem 1.6rem;
  font-weight: 600;
  border: none;
  box-shadow: 0 10px 20px rgba(18, 28, 74, 0.2);
}

div.stButton > button::after {
  content: " →";
}

div.stButton > button:hover {
  background: var(--navy-dark);
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
  }

  .top-nav {
    flex-direction: column;
    align-items: flex-start;
  }

  .nav-links {
    gap: 0.8rem;
    font-size: 0.85rem;
  }
}
</style>
""",
    unsafe_allow_html=True,
)

selected_pair_id = None
data_dir = DATA_DIR
upload_run_dir = None

ensure_mistral_api_key()
api_key_present = bool(os.getenv("MISTRAL_API_KEY"))
if "demo_mode" not in st.session_state:
    st.session_state["demo_mode"] = not api_key_present
demo_mode_active = st.session_state["demo_mode"]
status_class = "ok" if api_key_present else "warn"
status_label = "API key set" if api_key_present else "API key missing"
mode_label = "Demo mode" if demo_mode_active else "Live mode"

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

form_cols = st.columns([1.2, 0.8], gap="large")
with form_cols[0]:
    st.markdown("<div class='panel'>", unsafe_allow_html=True)
    input_mode = st.radio("Mode", ["Upload files", "Use existing data"], horizontal=True)
    if input_mode == "Upload files":
        voice_upload = st.file_uploader(
            "Transcript file (voice_*.txt)", type=["txt"]
        )
        video_upload = st.file_uploader(
            "Video file", type=[ext.strip(".") for ext in ALLOWED_VIDEO_EXTS]
        )
        pair_number = st.number_input(
            "Pair number", min_value=1, value=1, step=1
        )
    else:
        voice_upload = None
        video_upload = None
        pair_number = 1
        pairs = find_pairs(DATA_DIR)
        if not pairs:
            st.warning("No matching pairs found in data/.")
        else:
            labels = {format_pair_label(pair): pair for pair in pairs}
            selected_label = st.selectbox("Select pair", list(labels.keys()))
            selected_pair = labels[selected_label]
            selected_pair_id = selected_pair["pair_id"]
            st.session_state["voice_path"] = selected_pair["voice_path"]
    st.markdown("</div>", unsafe_allow_html=True)

with form_cols[1]:
    st.markdown("<div class='panel'>", unsafe_allow_html=True)
    frame_interval = st.number_input(
        "Frame interval (seconds)", min_value=1, value=30, step=1
    )
    output_dir_input = st.text_input("Output directory", value="reports_ui")
    demo_mode = st.checkbox("Demo mode", key="demo_mode")
    st.caption("Demo mode skips external API calls.")
    run_button = st.button("Run pipeline", type="primary")
    st.markdown("</div>", unsafe_allow_html=True)

log_placeholder = st.empty()

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
    warnings = []

    if not api_key_present and not demo_mode:
        errors.append("MISTRAL_API_KEY is missing. Enable demo mode or set the API key.")

    if input_mode == "Upload files":
        if voice_upload is None or video_upload is None:
            errors.append("Upload both the transcript and video files.")
        else:
            voice_bytes = voice_upload.getvalue()
            is_valid, has_timestamps = validate_transcript(voice_bytes)
            if not is_valid:
                errors.append("Transcript file is empty or invalid.")
            elif not has_timestamps:
                warnings.append(
                    "Transcript has no timestamps. Provide (MM:SS) markers for best results."
                )

            video_ext = Path(video_upload.name).suffix.lower()
            if video_ext not in ALLOWED_VIDEO_EXTS:
                errors.append(
                    f"Video extension {video_ext} is not supported. "
                    f"Allowed: {', '.join(ALLOWED_VIDEO_EXTS)}"
                )

            if not errors:
                timestamp = int(time.time())
                upload_run_dir = WORK_DIR / f"run_{timestamp}_pair_{int(pair_number)}"
                upload_run_dir.mkdir(parents=True, exist_ok=True)

                voice_path = upload_run_dir / f"voice_{int(pair_number)}.txt"
                video_path = upload_run_dir / f"video_{int(pair_number)}{video_ext}"

                voice_path.write_bytes(voice_bytes)
                video_path.write_bytes(video_upload.getvalue())

                data_dir = upload_run_dir
                selected_pair_id = None
                st.session_state["voice_path"] = str(voice_path)
    else:
        pairs = find_pairs(DATA_DIR)
        if not pairs:
            errors.append("No valid pairs found in data/.")
        elif selected_pair_id is None:
            errors.append("Select a voice/video pair.")
        else:
            selected = next(
                (p for p in pairs if p["pair_id"] == str(selected_pair_id)), None
            )
            if selected:
                transcript_path = Path(selected["voice_path"])
                transcript_bytes = transcript_path.read_bytes()
                is_valid, has_timestamps = validate_transcript(transcript_bytes)
                if not is_valid:
                    errors.append("Selected transcript file is empty.")
                elif not has_timestamps:
                    warnings.append(
                        "Selected transcript has no timestamps. Provide (MM:SS) markers."
                    )
            else:
                errors.append("Selected pair could not be resolved.")

    for warn in warnings:
        st.warning(warn)

    if errors:
        for err in errors:
            st.error(err)
    else:
        demo_value = "1" if demo_mode else "0"
        env_overrides = {
            "THALES_DEMO_MODE": demo_value,
        }
        mistral_key = os.getenv("MISTRAL_API_KEY")
        if mistral_key:
            env_overrides["MISTRAL_API_KEY"] = mistral_key

        out_dir = Path(output_dir_input)
        if not out_dir.is_absolute():
            out_dir = ROOT_DIR / out_dir

        def on_log(_line, logs_text):
            st.session_state["logs"] = logs_text
            log_placeholder.code(logs_text)

        returncode, logs_text, produced_files = run_pipeline(
            sys.executable,
            data_dir,
            int(frame_interval),
            out_dir,
            env_overrides,
            selected_pair_id=selected_pair_id,
            log_callback=on_log,
        )

        st.session_state["logs"] = logs_text
        st.session_state["produced_files"] = produced_files
        st.session_state["returncode"] = returncode

        outputs_found = bool(
            produced_files.get("summary_report") or produced_files.get("video_report")
        )

        if returncode != 0:
            st.error("Pipeline failed. Check the logs below for details.")
            st.session_state["show_logs_expanded"] = True
        elif outputs_found:
            st.success("Pipeline completed successfully.")
            st.session_state["show_logs_expanded"] = False
        else:
            st.warning(
                "Pipeline finished but no output files were found. "
                "Check the logs below for details."
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
