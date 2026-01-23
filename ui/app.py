import os
import time
from typing import Optional

import requests
import streamlit as st

API_BASE = (
    st.secrets.get("ENTITY_INDEXING_API_BASE", None)
    if hasattr(st, "secrets")
    else None
)
API_BASE = API_BASE or os.getenv("ENTITY_INDEXING_API_BASE", "http://localhost:8000")

st.set_page_config(page_title="Entity Indexing", layout="wide")

st.sidebar.title("Entity Indexing")
page = st.sidebar.selectbox(
    "Navigate",
    ["Home", "Videos Library", "Upload", "Video Details", "Unified Entity Search"],
)


def api_get(path: str):
    res = requests.get(f"{API_BASE}{path}")
    res.raise_for_status()
    return res.json()


def api_post_video(video_file, voice_file, interval_sec: int):
    files = {"video_file": video_file}
    if voice_file is not None:
        files["voice_file"] = voice_file
    data = {"interval_sec": str(interval_sec)}
    res = requests.post(f"{API_BASE}/api/videos", files=files, data=data)
    res.raise_for_status()
    return res.json()


if page == "Home":
    st.title("Entity Indexing")
    st.caption("Unified intelligence layer across your video archive.")
    try:
        videos = api_get("/api/videos")
    except Exception:
        videos = []
    total = len(videos)
    completed = len([v for v in videos if v.get("status") == "completed"])
    processing = len([v for v in videos if v.get("status") == "processing"])

    col1, col2, col3 = st.columns(3)
    col1.metric("Total Videos", total)
    col2.metric("Processing", processing)
    col3.metric("Completed", completed)

    st.markdown("---")
    st.subheader("Quick Start")
    st.write("Upload a video and generate a full entity indexing report with timeline insights.")

elif page == "Videos Library":
    st.title("Videos Library")
    try:
        videos = api_get("/api/videos")
    except Exception:
        videos = []
    if not videos:
        st.info("No videos found.")
    else:
        st.dataframe(videos, use_container_width=True)

elif page == "Upload":
    st.title("Upload")
    st.caption("Create a new entity indexing job.")

    video_file = st.file_uploader("Video file", type=["mp4", "mkv", "mov", "avi"])
    voice_file = st.file_uploader("Optional voice description (.txt)", type=["txt"])
    interval_sec = st.number_input("Frame interval (seconds)", min_value=1, value=5)

    if st.button("Start Processing", type="primary"):
        if not video_file:
            st.error("Please upload a video file.")
        else:
            try:
                result = api_post_video(video_file, voice_file, interval_sec)
                st.success(f"Job created: {result['video_id']}")
                st.write("Go to Video Details to monitor progress.")
            except Exception as exc:
                st.error(f"Upload failed: {exc}")

elif page == "Video Details":
    st.title("Video Details")
    try:
        videos = api_get("/api/videos")
    except Exception:
        videos = []

    video_id: Optional[str] = None
    if videos:
        video_id = st.selectbox("Select video", [v["video_id"] for v in videos])
    else:
        video_id = st.text_input("Video ID")

    if video_id:
        try:
            detail = api_get(f"/api/videos/{video_id}")
            status = api_get(f"/api/videos/{video_id}/status")
        except Exception as exc:
            st.error(f"Failed to load video: {exc}")
            st.stop()

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Status", status.get("status"))
        col2.metric("Progress", f"{int(status.get('progress', 0) * 100)}%")
        col3.metric("Frames", detail.get("frames_analyzed") or "-")
        col4.metric("Entities", detail.get("unique_entities") or "-")

        st.subheader("Processing Stage")
        st.write(status.get("current_stage") or "-")
        st.progress(status.get("progress", 0.0))

        auto_refresh = st.checkbox("Auto refresh", value=True)
        if auto_refresh and status.get("status") not in {"completed", "failed"}:
            time.sleep(1.5)
            st.experimental_rerun()

        if detail.get("report_available"):
            st.subheader("Report Summary")
            report = detail.get("report") or {}
            st.json(report)

            st.subheader("Frames")
            page_num = st.number_input("Page", min_value=1, value=1)
            page_size = st.number_input("Page size", min_value=1, max_value=50, value=12)
            frames = api_get(
                f"/api/videos/{video_id}/frames?page={int(page_num)}&page_size={int(page_size)}"
            )
            cols = st.columns(3)
            for idx, frame in enumerate(frames.get("frames", [])):
                with cols[idx % 3]:
                    st.image(f"{API_BASE}{frame['url']}", use_column_width=True)
                    st.caption(f"{frame['timestamp_sec']}s")

elif page == "Unified Entity Search":
    st.title("Unified Entity Search")
    q = st.text_input("Query (comma-separated entities)")
    similarity = st.slider("Similarity threshold", min_value=0.0, max_value=1.0, value=0.7)
    min_presence = st.slider("Minimum presence", min_value=0.0, max_value=1.0, value=0.0)
    min_frames = st.number_input("Minimum frames", min_value=0, value=0)

    if st.button("Search", type="primary") and q:
        try:
            params = (
                f"?q={q}&similarity={similarity}&min_presence={min_presence}&min_frames={min_frames}"
            )
            results = api_get(f"/api/search{params}")
        except Exception as exc:
            st.error(f"Search failed: {exc}")
            st.stop()

        st.subheader("Summary")
        st.write(results)
