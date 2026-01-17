from __future__ import annotations

from typing import Dict

THEME: Dict[str, str] = {
    "accent": "#0f766e",
    "accent_strong": "#0b5c57",
    "accent_soft": "rgba(15, 118, 110, 0.18)",
    "accent_glow": "rgba(15, 118, 110, 0.28)",
    "bg_top": "#f6f7fb",
    "bg_mid": "#edf1f7",
    "bg_bottom": "#e5ebf3",
    "text": "#0b1220",
    "text_soft": "#243047",
    "text_muted": "#465268",
    "glass": "rgba(255, 255, 255, 0.72)",
    "glass_strong": "rgba(255, 255, 255, 0.86)",
    "border": "rgba(12, 18, 32, 0.12)",
    "border_soft": "rgba(12, 18, 32, 0.08)",
    "shadow_strong": "0 28px 70px rgba(12, 18, 32, 0.18)",
    "shadow_soft": "0 16px 32px rgba(12, 18, 32, 0.12)",
    "shadow_glow": "0 0 0 1px rgba(255, 255, 255, 0.4)",
}


def css_variables(theme: Dict[str, str] | None = None) -> str:
    """Return CSS variable declarations for the design system."""
    theme = theme or THEME
    return f"""
    :root {{
      --accent: {theme["accent"]};
      --accent-strong: {theme["accent_strong"]};
      --accent-soft: {theme["accent_soft"]};
      --accent-glow: {theme["accent_glow"]};
      --bg-top: {theme["bg_top"]};
      --bg-mid: {theme["bg_mid"]};
      --bg-bottom: {theme["bg_bottom"]};
      --text: {theme["text"]};
      --text-soft: {theme["text_soft"]};
      --text-muted: {theme["text_muted"]};
      --glass: {theme["glass"]};
      --glass-strong: {theme["glass_strong"]};
      --border: {theme["border"]};
      --border-soft: {theme["border_soft"]};
      --shadow-strong: {theme["shadow_strong"]};
      --shadow-soft: {theme["shadow_soft"]};
      --shadow-glow: {theme["shadow_glow"]};
      --radius-s: 12px;
      --radius-m: 18px;
      --radius-l: 24px;
      --radius-xl: 32px;
      --space-1: 4px;
      --space-2: 8px;
      --space-3: 12px;
      --space-4: 16px;
      --space-5: 24px;
      --space-6: 32px;
      --space-7: 48px;
      --space-8: 64px;
      --font-body: "Sora", sans-serif;
      --font-display: "Fraunces", serif;
      --font-mono: "IBM Plex Mono", monospace;
    }}
    """
