from __future__ import annotations

from pathlib import Path
from typing import Dict


def generate_pdf(report: Dict, output_path: Path) -> bool:
    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.pdfgen import canvas
    except Exception:
        return False

    output_path.parent.mkdir(parents=True, exist_ok=True)
    c = canvas.Canvas(str(output_path), pagesize=letter)
    width, height = letter
    y = height - 40

    c.setFont("Helvetica-Bold", 16)
    c.drawString(40, y, "Entity Indexing Report")
    y -= 30

    c.setFont("Helvetica", 10)
    c.drawString(40, y, f"Duration: {report.get('duration_sec', 0)} sec")
    y -= 14
    c.drawString(40, y, f"Interval: {report.get('interval_sec', 0)} sec")
    y -= 14
    c.drawString(40, y, f"Frames analyzed: {report.get('frames_analyzed', 0)}")
    y -= 20

    c.setFont("Helvetica-Bold", 12)
    c.drawString(40, y, "Entities")
    y -= 16
    c.setFont("Helvetica", 10)

    entities = report.get("entities", {})
    for label, data in entities.items():
        if y < 80:
            c.showPage()
            y = height - 40
        presence = data.get("presence", 0)
        count = data.get("count", 0)
        c.drawString(40, y, f"- {label}: {count} frames ({presence:.2%})")
        y -= 12

    c.showPage()
    c.save()
    return True
