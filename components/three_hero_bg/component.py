from __future__ import annotations

from pathlib import Path

import streamlit.components.v1 as components


def render_three_hero(height: int = 320, key: str = "three-hero") -> None:
    """Render the lightweight Three.js hero background."""
    html_path = Path(__file__).with_name("index.html")
    html = html_path.read_text(encoding="utf-8")
    components.html(html, height=height, scrolling=False, key=key)
