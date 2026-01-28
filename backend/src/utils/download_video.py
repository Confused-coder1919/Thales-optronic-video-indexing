from __future__ import annotations

import os
import time
from pathlib import Path
from typing import Optional, Tuple


def download_video_from_url(
    url: str,
    dest_dir: Path,
    cookie_file: Optional[Path] = None,
    cookies_from_browser: Optional[str] = None,
    user_agent: Optional[str] = None,
) -> Tuple[Path, str]:
    """
    Download a video from a URL (YouTube, etc.) using yt-dlp.
    Returns (file_path, filename).
    """
    try:
        from yt_dlp import YoutubeDL
    except Exception as exc:  # pragma: no cover
        raise RuntimeError("yt-dlp is required for URL downloads") from exc

    dest_dir.mkdir(parents=True, exist_ok=True)
    output_template = str(dest_dir / "%(title).200s.%(ext)s")

    user_agent = user_agent or os.getenv(
        "ENTITY_INDEXING_YTDLP_USER_AGENT",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    )
    cookie_file = cookie_file or (
        Path(os.getenv("ENTITY_INDEXING_YTDLP_COOKIES"))
        if os.getenv("ENTITY_INDEXING_YTDLP_COOKIES")
        else None
    )
    cookies_from_browser = cookies_from_browser or os.getenv(
        "ENTITY_INDEXING_YTDLP_COOKIES_FROM_BROWSER"
    )

    ydl_opts = {
        "outtmpl": output_template,
        "format": "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
        "merge_output_format": "mp4",
        "noplaylist": True,
        "quiet": True,
        "no_warnings": True,
        "user_agent": user_agent,
        "http_headers": {
            "User-Agent": user_agent,
            "Accept-Language": "en-US,en;q=0.9",
        },
        "geo_bypass": True,
    }
    if cookie_file:
        ydl_opts["cookiefile"] = str(cookie_file)
    if cookies_from_browser:
        # Example: "chrome", "chrome:Profile 1", "firefox"
        ydl_opts["cookiesfrombrowser"] = cookies_from_browser

    before = {p.resolve() for p in dest_dir.glob("*")}
    with YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        filename = info.get("title") or "downloaded_video"

    # Find the newest file in dest_dir (yt-dlp may change ext after merge).
    candidates = [p for p in dest_dir.glob("*") if p.resolve() not in before]
    if not candidates:
        # Fallback: pick the newest file by mtime
        candidates = list(dest_dir.glob("*"))
    if not candidates:
        raise RuntimeError("No file downloaded from URL.")

    latest = max(candidates, key=lambda p: p.stat().st_mtime if p.exists() else time.time())
    return latest, latest.name


def probe_video_url(
    url: str,
    cookie_file: Optional[Path] = None,
    cookies_from_browser: Optional[str] = None,
    user_agent: Optional[str] = None,
) -> dict:
    """
    Probe a video URL with yt-dlp without downloading.
    Returns a lightweight info dict (title, duration).
    """
    try:
        from yt_dlp import YoutubeDL
    except Exception as exc:  # pragma: no cover
        raise RuntimeError("yt-dlp is required for URL downloads") from exc

    user_agent = user_agent or os.getenv(
        "ENTITY_INDEXING_YTDLP_USER_AGENT",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    )
    cookie_file = cookie_file or (
        Path(os.getenv("ENTITY_INDEXING_YTDLP_COOKIES"))
        if os.getenv("ENTITY_INDEXING_YTDLP_COOKIES")
        else None
    )
    cookies_from_browser = cookies_from_browser or os.getenv(
        "ENTITY_INDEXING_YTDLP_COOKIES_FROM_BROWSER"
    )

    ydl_opts = {
        "quiet": True,
        "no_warnings": True,
        "skip_download": True,
        "user_agent": user_agent,
        "http_headers": {
            "User-Agent": user_agent,
            "Accept-Language": "en-US,en;q=0.9",
        },
        "geo_bypass": True,
    }
    if cookie_file:
        ydl_opts["cookiefile"] = str(cookie_file)
    if cookies_from_browser:
        ydl_opts["cookiesfrombrowser"] = cookies_from_browser

    with YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
    return {
        "title": info.get("title"),
        "duration_sec": info.get("duration"),
    }
