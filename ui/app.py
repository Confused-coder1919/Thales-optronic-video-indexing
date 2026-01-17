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

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import pandas as pd
import streamlit as st
import streamlit.components.v1 as st_components
from dotenv import load_dotenv
import yaml

from utils import ALLOWED_VIDEO_EXTS, find_videos, run_pipeline
from components.three_hero_bg.component import render_three_hero
from ui.assets.theme import css_variables

try:
    from thales.config import MISTRAL_MODEL, PIXTRAL_MODEL
except Exception:
    MISTRAL_MODEL = "mistral-large-latest"
    PIXTRAL_MODEL = "pixtral-large-latest"

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


def load_css() -> None:
    styles_path = ROOT_DIR / "ui" / "assets" / "styles.css"
    styles_css = ""
    if styles_path.exists():
        styles_css = styles_path.read_text(encoding="utf-8")
    theme_css = css_variables()
    st.markdown(f"<style>{theme_css}\n{styles_css}</style>", unsafe_allow_html=True)


def section_header(section_id: str, title: str, subtitle: str) -> None:
    st.markdown(f"<div id='{section_id}' class='section-anchor'></div>", unsafe_allow_html=True)
    st.markdown(
        f"<div class='section-header'><div class='section-title'>{title}</div>"
        f"<div class='section-subtitle'>{subtitle}</div></div>",
        unsafe_allow_html=True,
    )


def render_stepper(steps: list[dict]) -> None:
    items = []
    for step in steps:
        status = str(step.get("status", "Pending"))
        timestamp = step.get("timestamp", "—")
        status_class = status.lower().replace(" ", "-")
        items.append(
            "<div class='stepper-item {status_class}'>"
            "<div class='stepper-dot'></div>"
            "<div>"
            f"<div class='stepper-title'>{step.get('step','')}</div>"
            f"<div class='stepper-meta'>{status} - {timestamp}</div>"
            "</div>"
            "</div>".format(status_class=status_class)
        )
    html = "<div class='stepper'>" + "".join(items) + "</div>"
    st.markdown(html, unsafe_allow_html=True)


def inject_nav_script(section_ids: list[str]) -> None:
    payload = json.dumps(section_ids)
    script = f"""
    <script>
      (function () {{
        const ids = {payload};
        function init() {{
          try {{
            const doc = window.parent.document;
            const navLinks = Array.from(doc.querySelectorAll('.nav-link'));
            const sections = ids.map((id) => doc.getElementById(id)).filter(Boolean);
            if (!navLinks.length || !sections.length) {{
              return;
            }}
            const linkById = new Map();
            navLinks.forEach((link) => {{
              const target = link.getAttribute('data-target') || link.getAttribute('href');
              if (!target) return;
              const id = target.replace('#', '');
              linkById.set(id, link);
            }});
            const observer = new window.parent.IntersectionObserver(
              (entries) => {{
                entries.forEach((entry) => {{
                  if (!entry.isIntersecting) return;
                  const link = linkById.get(entry.target.id);
                  if (!link) return;
                  navLinks.forEach((item) => item.classList.remove('active'));
                  link.classList.add('active');
                }});
              }},
              {{ rootMargin: '-35% 0px -55% 0px', threshold: 0.0 }}
            );
            sections.forEach((section) => observer.observe(section));
          }} catch (err) {{
            console.log('nav observer error', err);
          }}
        }}

        if (document.readyState === 'complete') {{
          init();
        }} else {{
          window.addEventListener('load', init);
        }}
      }})();
    </script>
    """
    st_components.html(script, height=0, width=0)


st.set_page_config(page_title="Thales Video Indexing", layout="wide")
ensure_work_dir()
logo_data = load_logo_data()
if logo_data:
    logo_html = f"<img class=\"hero-logo\" src=\"data:image/svg+xml;base64,{logo_data}\" alt=\"Thales logo\" />"
else:
    logo_html = "<span class=\"logo-text\">THALES</span>"

load_css()

data_dir = DATA_DIR

ensure_mistral_api_key()
api_key_present = bool(os.getenv("MISTRAL_API_KEY"))
returncode_preview = st.session_state.get("returncode")
run_params_preview = st.session_state.get("run_params", {})
run_finished_preview = st.session_state.get("run_finished_at") or "—"
run_started_preview = st.session_state.get("run_started_at") or "—"
output_preview = run_params_preview.get("output_dir", "reports_ui")
frame_interval_preview = run_params_preview.get("frame_interval")
frame_interval_label = (
    f"{frame_interval_preview}s"
    if frame_interval_preview not in (None, "—")
    else "—"
)
discovery_preview = "On" if run_params_preview.get("discovery_mode") else "Off"
is_running = bool(st.session_state.get("is_running"))

if not api_key_present:
    status_kind = "blocked"
    status_label = "API key required"
    status_body = "Add MISTRAL_API_KEY in Streamlit secrets to enable the pipeline."
elif is_running:
    status_kind = "running"
    status_label = "Pipeline running"
    status_body = "Processing the latest upload. Live status appears below."
elif returncode_preview is None:
    status_kind = "ready"
    status_label = "Ready to run"
    status_body = "Upload a video to start the intelligence workflow."
elif returncode_preview == 0:
    status_kind = "ready"
    status_label = "Last run succeeded"
    status_body = "Review outputs or launch another run."
else:
    status_kind = "failed"
    status_label = "Last run failed"
    status_body = "Check the logs for troubleshooting details."

st.markdown("<section id='hero' class='hero'>", unsafe_allow_html=True)
st.markdown("<div class='hero-bg'>", unsafe_allow_html=True)
render_three_hero(height=360)
st.markdown("</div>", unsafe_allow_html=True)
st.markdown("<div class='hero-inner'>", unsafe_allow_html=True)

hero_cols = st.columns([1.3, 0.9], gap="large")
with hero_cols[0]:
    st.markdown(
        f"""
<div class="hero-brand">{logo_html}<span>Thales Optronic</span></div>
<div class="hero-kicker">Single-video intelligence pipeline</div>
<h1 class="hero-title">Thales Video Indexing</h1>
<div class="hero-subtitle">
  Upload one video and let the system extract audio, transcribe speech, extract entities,
  verify with vision, and fuse everything into a single timeline.
</div>
<div class="hero-cta">
  <a class="cta-btn cta-primary" href="#run">Run pipeline</a>
  <a class="cta-btn cta-secondary" href="#quickstart">Quick start</a>
  <a class="cta-btn cta-ghost" href="#results">View results</a>
</div>
<div class="hero-tags">
  <span class="hero-tag">Upload video only</span>
  <span class="hero-tag">Auto audio extraction</span>
  <span class="hero-tag">STT + vision fusion</span>
</div>
""",
        unsafe_allow_html=True,
    )

with hero_cols[1]:
    st.markdown(
        f"""
<div class="panel">
  <div class="panel-title">Pipeline readiness</div>
  <div class="status-pill {status_kind}">{status_label}</div>
  <p class="panel-note">{status_body}</p>
  <div class="hero-meta">
    <div class="meta-row"><span>Last run</span><strong>{run_finished_preview}</strong></div>
    <div class="meta-row"><span>Started</span><strong>{run_started_preview}</strong></div>
    <div class="meta-row"><span>Frame interval</span><strong>{frame_interval_label}</strong></div>
    <div class="meta-row"><span>Discovery mode</span><strong>{discovery_preview}</strong></div>
    <div class="meta-row"><span>Output dir</span><strong>{output_preview}</strong></div>
  </div>
</div>
""",
        unsafe_allow_html=True,
    )

st.markdown("</div></section>", unsafe_allow_html=True)

nav_links = [
    ("hero", "Hero"),
    ("quickstart", "Quick start"),
    ("run", "Upload & Run"),
    ("timeline", "Timeline"),
    ("results", "Results"),
    ("insights", "Insights"),
    ("transcript", "Transcript"),
    ("analysis", "Outputs"),
    ("downloads", "Downloads"),
    ("faq", "FAQ"),
]

nav_html = ["<div class='nav-bar'><div class='nav-shell'>"]
nav_html.append("<span class='nav-label'>Navigate</span>")
for section_id, label in nav_links:
    nav_html.append(
        f"<a class='nav-link' href='#{section_id}' data-target='{section_id}'>{label}</a>"
    )
nav_html.append("</div></div>")
st.markdown("".join(nav_html), unsafe_allow_html=True)
inject_nav_script([section_id for section_id, _label in nav_links])

section_header(
    "quickstart",
    "Quick start",
    "Get a full analysis in three steps.",
)
st.markdown(
    """
<div class="quickstart-grid">
  <div class="feature-card">
    <h4>1) Add API key</h4>
    <p>Set <code>MISTRAL_API_KEY</code> in Streamlit secrets to enable analysis.</p>
  </div>
  <div class="feature-card">
    <h4>2) Upload & run</h4>
    <p>Upload a video and click Run pipeline. Audio + vision analysis runs automatically.</p>
  </div>
  <div class="feature-card">
    <h4>3) Review outputs</h4>
    <p>Explore scene summaries, entities, keyword timeline, and exports.</p>
  </div>
</div>
""",
    unsafe_allow_html=True,
)

section_header(
    "run",
    "Upload & Run",
    "Upload a single video and launch the full pipeline in one click.",
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
        discovery_mode = st.checkbox("Discovery mode (vision-first proposals)", value=False)
        st.caption("Discovery mode proposes entities from sampled frames before verification.")
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
if "is_running" not in st.session_state:
    st.session_state["is_running"] = False

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
        env_overrides["THALES_DISCOVERY_MODE"] = "1" if discovery_mode else "0"

        out_dir = Path(output_dir_input)
        if not out_dir.is_absolute():
            out_dir = ROOT_DIR / out_dir

            st.session_state["is_running"] = True

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

            st.session_state["is_running"] = False

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
                "discovery_mode": bool(discovery_mode),
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

section_header(
    "timeline",
    "Pipeline timeline",
    "Status and configuration for the most recent run.",
)
timeline_cols = st.columns([1.2, 1], gap="large")
with timeline_cols[0]:
    st.markdown("<div class='panel'>", unsafe_allow_html=True)
    st.subheader("Run progress")
    steps = build_pipeline_steps(
        logs_text,
        produced_files,
        export_csv_enabled,
        returncode,
        step_times,
    )
    render_stepper(steps)
    st.markdown("</div>", unsafe_allow_html=True)
with timeline_cols[1]:
    st.markdown("<div class='panel'>", unsafe_allow_html=True)
    st.subheader("Run metadata")
    frame_interval_value = run_params.get("frame_interval")
    frame_label = (
        f"{frame_interval_value}s" if frame_interval_value not in (None, "—") else "—"
    )
    meta_rows = [
        ("Start", run_started_at or "—"),
        ("Finish", run_finished_at or "—"),
        ("Last log update", st.session_state.get("last_log_at", "—")),
        ("Frame interval", frame_label),
        ("Discovery mode", "On" if run_params.get("discovery_mode") else "Off"),
        ("Output dir", run_params.get("output_dir", "—")),
    ]
    if run_params.get("video_name"):
        meta_rows.append(("Video file", run_params.get("video_name")))
    meta_html = "".join(
        f"<div class='meta-row'><span>{label}</span><strong>{value}</strong></div>"
        for label, value in meta_rows
    )
    st.markdown(meta_html, unsafe_allow_html=True)
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

section_header(
    "results",
    "Results",
    "Key metrics and entity overview from the latest run.",
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

        vision_only_rows = []
        for row in rows:
            meta = entities.get(row["entity"], {})
            if meta.get("source") == "vision" and meta.get("discovered_only") is True:
                vision_only_rows.append(row)

        if vision_only_rows:
            st.subheader("Vision-only entities")
            st.caption("Entities proposed by discovery mode that were not found in speech.")
            st.dataframe(pd.DataFrame(vision_only_rows), use_container_width=True)
else:
    st.info("Run the pipeline to populate results and metrics.")

section_header(
    "insights",
    "Insights",
    "Scene summaries, frame verification, and entity timelines.",
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
                        .mark_bar(color="#0f766e")
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

section_header(
    "transcript",
    "Transcript & Search",
    "Transcript context, keyword search, and entity matches.",
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

if summary_data or video_report_data or voice_segments:
    st.subheader("Search transcript & entities")
    st.caption("Filter transcript text and cross-check matches against vision detections.")

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
                        .mark_bar(color="#0f766e")
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
                            .mark_bar(color="#0f766e")
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

section_header(
    "analysis",
    "Analysis outputs",
    "Detailed artifacts produced by the pipeline.",
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

section_header(
    "downloads",
    "Download reports",
    "Export the intelligence outputs for sharing or archive.",
)
if summary_path or video_report_path:
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

section_header(
    "faq",
    "FAQ",
    "Common questions about this project.",
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
