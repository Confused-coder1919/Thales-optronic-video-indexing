from __future__ import annotations

import os
import time
from urllib.parse import urlparse

import requests
from urllib.parse import urlparse
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

    parsed_url = urlparse(url)
    hostname = parsed_url.hostname or ""
    is_youtube = "youtube.com" in hostname or "youtu.be" in hostname
    origin = f"{parsed_url.scheme}://{hostname}/" if parsed_url.scheme and hostname else None

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
        "retries": 3,
        "fragment_retries": 3,
        "socket_timeout": 15,
        "concurrent_fragment_downloads": 1,
        "http_headers": {
            "User-Agent": user_agent,
            "Accept-Language": "en-US,en;q=0.9",
        },
        "geo_bypass": True,
    }
    if origin:
        ydl_opts["http_headers"]["Referer"] = origin
    if is_youtube:
        ydl_opts["http_headers"]["Referer"] = "https://www.youtube.com/"
        ydl_opts["extractor_args"] = {
            "youtube": {"player_client": ["android", "web"]}
        }
    if cookie_file:
        ydl_opts["cookiefile"] = str(cookie_file)
    if cookies_from_browser:
        # Example: "chrome", "chrome:Profile 1", "firefox"
        ydl_opts["cookiesfrombrowser"] = cookies_from_browser

    before = {p.resolve() for p in dest_dir.glob("*")}
    try:
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = info.get("title") or "downloaded_video"
    except Exception as exc:
        direct = _try_direct_download(url, dest_dir, ydl_opts["http_headers"])
        if direct:
            return direct, direct.name
        raise RuntimeError(f"unable to download video data: {exc}") from exc

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

    parsed_url = urlparse(url)
    hostname = parsed_url.hostname or ""
    is_youtube = "youtube.com" in hostname or "youtu.be" in hostname
    origin = f"{parsed_url.scheme}://{hostname}/" if parsed_url.scheme and hostname else None

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
        "retries": 3,
        "socket_timeout": 15,
        "http_headers": {
            "User-Agent": user_agent,
            "Accept-Language": "en-US,en;q=0.9",
        },
        "geo_bypass": True,
    }
    if origin:
        ydl_opts["http_headers"]["Referer"] = origin
    if is_youtube:
        ydl_opts["http_headers"]["Referer"] = "https://www.youtube.com/"
        ydl_opts["extractor_args"] = {
            "youtube": {"player_client": ["android", "web"]}
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


def _looks_like_direct(url: str) -> bool:
    ext = Path(urlparse(url).path).suffix.lower()
    return ext in {".mp4", ".mov", ".mkv", ".avi", ".webm"}


def _try_direct_download(url: str, dest_dir: Path, headers: dict) -> Optional[Path]:
    if not _looks_like_direct(url):
        return None
    dest_dir.mkdir(parents=True, exist_ok=True)
    filename = Path(urlparse(url).path).name or f"download_{int(time.time())}.mp4"
    dest_path = dest_dir / filename
    try:
        with requests.get(url, headers=headers, stream=True, timeout=20) as resp:
            if resp.status_code >= 400:
                return None
            content_type = (resp.headers.get("Content-Type") or "").lower()
            if "text/html" in content_type:
                return None
            with open(dest_path, "wb") as handle:
                for chunk in resp.iter_content(chunk_size=1024 * 1024):
                    if chunk:
                        handle.write(chunk)
    except Exception:
        return None
    return dest_path if dest_path.exists() else None
