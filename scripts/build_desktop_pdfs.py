from __future__ import annotations

import sys
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import ListFlowable, ListItem, Paragraph, SimpleDocTemplate

ROOT = Path(__file__).resolve().parents[1]
SOURCE_DIR = ROOT / "docs" / "desktop"


def escape_markup(value: str) -> str:
    return value.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def build_pdf(source: Path, destination: Path) -> None:
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(
        name="DocTitle", parent=styles["Title"], fontName="Helvetica-Bold",
        fontSize=20, leading=25, textColor=colors.HexColor("#17324d"),
        alignment=TA_LEFT, spaceAfter=12,
    ))
    styles.add(ParagraphStyle(
        name="DocHeading", parent=styles["Heading2"], fontSize=13,
        leading=17, textColor=colors.HexColor("#17324d"),
        spaceBefore=10, spaceAfter=5,
    ))
    styles.add(ParagraphStyle(
        name="DocBody", parent=styles["BodyText"], fontSize=9,
        leading=13, spaceAfter=5,
    ))

    story = []
    paragraphs = []
    bullets = []
    numbers = []

    def flush_text():
        if paragraphs:
            story.append(Paragraph(escape_markup(" ".join(paragraphs)), styles["DocBody"]))
            paragraphs.clear()

    def flush_lists():
        if bullets:
            story.append(ListFlowable(
                [ListItem(Paragraph(escape_markup(item), styles["DocBody"])) for item in bullets],
                bulletType="bullet", leftIndent=16,
            ))
            bullets.clear()
        if numbers:
            story.append(ListFlowable(
                [ListItem(Paragraph(escape_markup(item), styles["DocBody"])) for item in numbers],
                bulletType="1", leftIndent=18,
            ))
            numbers.clear()

    for raw in source.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line:
            flush_text()
            flush_lists()
        elif line.startswith("|"):
            flush_text()
            flush_lists()
        elif line.startswith("# "):
            flush_text()
            flush_lists()
            story.append(Paragraph(escape_markup(line[2:]), styles["DocTitle"]))
        elif line.startswith("## "):
            flush_text()
            flush_lists()
            story.append(Paragraph(escape_markup(line[3:]), styles["DocHeading"]))
        elif line.startswith("- "):
            flush_text()
            numbers.clear()
            bullets.append(line[2:])
        elif line[:1].isdigit() and ". " in line[:5]:
            flush_text()
            bullets.clear()
            numbers.append(line.split(". ", 1)[1])
        else:
            paragraphs.append(line.replace("**", ""))

    flush_text()
    flush_lists()
    destination.parent.mkdir(parents=True, exist_ok=True)
    document = SimpleDocTemplate(
        str(destination), pagesize=A4, rightMargin=18 * mm,
        leftMargin=18 * mm, topMargin=17 * mm, bottomMargin=17 * mm,
        title=source.stem.replace("_", " "), author="ZTF Classifier Project",
    )

    def footer(canvas, doc):
        canvas.saveState()
        canvas.setFont("Helvetica", 8)
        canvas.setFillColor(colors.HexColor("#666666"))
        canvas.drawString(18 * mm, 10 * mm, "ZTF Classifier Windows Preview 0.1.0-preview.1")
        canvas.drawRightString(A4[0] - 18 * mm, 10 * mm, f"Page {doc.page}")
        canvas.restoreState()

    document.build(story, onFirstPage=footer, onLaterPages=footer)


def main() -> int:
    output = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "dist"
    build_pdf(SOURCE_DIR / "User_Manual.md", output / "User_Manual.pdf")
    build_pdf(SOURCE_DIR / "Quick_Start.md", output / "Quick_Start.pdf")
    print("Created User_Manual.pdf and Quick_Start.pdf")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
