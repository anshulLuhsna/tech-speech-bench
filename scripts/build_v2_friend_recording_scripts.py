#!/usr/bin/env python3
"""Build friendly TechSpeechBench v2 recording sheets from TSV manifests.

The PDF is for participants. It intentionally hides benchmark split labels,
categories, and target terms so people can read naturally without being nudged
to over-pronounce particular words.

Example:
  /path/to/python scripts/build_v2_friend_recording_scripts.py
"""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import landscape, A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


DEFAULT_MANIFEST_DIR = Path("data/v2/recording-scripts")
DEFAULT_OUTPUT_DIR = Path("techspeechbench_v2_friend_recording_scripts")
SPEAKER_IDS = ("s01", "s02", "s03", "s04", "s05", "s06")
ROWS_PER_PAGE = 20


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build participant-facing v2 recording PDFs.")
    parser.add_argument("--manifest-dir", type=Path, default=DEFAULT_MANIFEST_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    return parser.parse_args()


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f, delimiter="\t"))

    if [*rows[0]] != ["clip_id", "utterance"]:
        raise ValueError(f"{path} must have clip_id and utterance columns")
    if len(rows) != 40:
        raise ValueError(f"{path} must contain 40 recording lines, found {len(rows)}")
    return rows


def draw_footer(canvas, doc) -> None:
    canvas.saveState()
    canvas.setFillColor(colors.HexColor("#667085"))
    canvas.setFont("Helvetica", 8)
    canvas.drawCentredString(landscape(A4)[0] / 2, 10 * mm, f"TechSpeechBench v2 recording sheet - page {doc.page}")
    canvas.restoreState()


def build_story(rows: list[dict[str, str]]) -> list:
    styles = getSampleStyleSheet()
    title = ParagraphStyle(
        "Title",
        parent=styles["Title"],
        fontName="Helvetica-Bold",
        fontSize=24,
        leading=27,
        textColor=colors.HexColor("#101828"),
        alignment=TA_CENTER,
        spaceAfter=3,
    )
    subtitle = ParagraphStyle(
        "Subtitle",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=11.5,
        leading=14,
        textColor=colors.HexColor("#475467"),
        alignment=TA_CENTER,
        spaceAfter=7,
    )
    body = ParagraphStyle(
        "Body",
        parent=styles["BodyText"],
        fontName="Helvetica",
        fontSize=8.3,
        leading=10.5,
        textColor=colors.HexColor("#344054"),
    )
    table_body = ParagraphStyle(
        "TableBody",
        parent=body,
        fontSize=8.3,
        leading=10,
        textColor=colors.HexColor("#101828"),
    )
    table_id = ParagraphStyle(
        "TableId",
        parent=table_body,
        fontName="Courier-Bold",
    )

    story = [
        Paragraph("TechSpeechBench v2", title),
        Paragraph("Quick recording sheet - 40 short clips", subtitle),
    ]
    instructions = [
        [
            Paragraph("<b>Record naturally</b><br/>Read each sentence at your normal pace. No need to spell out or over-pronounce technical words.", body),
            Paragraph("<b>One memo per line</b><br/>Use Voice Memos and make one separate recording for every row. Keep them in this order.", body),
            Paragraph("<b>No renaming needed</b><br/>Leave the default names. When done, share the original .m4a files through the Drive folder I send you.", body),
            Paragraph("<b>If you slip up</b><br/>Delete that memo and record the same line again. A quiet room is enough; no special setup needed.", body),
        ]
    ]
    info_table = Table(instructions, colWidths=[66 * mm, 66 * mm, 66 * mm, 66 * mm])
    info_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F9FAFB")),
                ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#D0D5DD")),
                ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#EAECF0")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )
    story.extend([info_table, Spacer(1, 5 * mm)])

    for page_index, page_rows in enumerate(
        (rows[:ROWS_PER_PAGE], rows[ROWS_PER_PAGE:]), start=1
    ):
        if page_index > 1:
            story.append(PageBreak())

        table_data = [["Clip", "Read this"]]
        table_data.extend(
            [
                Paragraph(row["clip_id"].split("_")[-1], table_id),
                Paragraph(row["utterance"], table_body),
            ]
            for row in page_rows
        )
        table = Table(table_data, colWidths=[22 * mm, 240 * mm], repeatRows=1)
        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#101828")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, 0), 9),
                    ("ALIGN", (0, 0), (0, -1), "CENTER"),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#EAECF0")),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F9FAFB")]),
                    ("LEFTPADDING", (0, 0), (-1, -1), 7),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 7),
                    ("TOPPADDING", (0, 0), (-1, -1), 2),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
                ]
            )
        )
        story.append(table)

    return story


def build_pdf(rows: list[dict[str, str]], output_path: Path) -> None:
    document = SimpleDocTemplate(
        str(output_path),
        pagesize=landscape(A4),
        leftMargin=18 * mm,
        rightMargin=18 * mm,
        topMargin=12 * mm,
        bottomMargin=14 * mm,
        title="TechSpeechBench v2 recording sheet",
        author="TechSpeechBench",
    )
    document.build(build_story(rows), onFirstPage=draw_footer, onLaterPages=draw_footer)


def main() -> None:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    for speaker_id in SPEAKER_IDS:
        manifest_path = args.manifest_dir / f"{speaker_id}.tsv"
        output_path = args.output_dir / f"techspeechbench_v2_{speaker_id}_recording_script.pdf"
        build_pdf(read_rows(manifest_path), output_path)
        print(f"wrote {output_path}")


if __name__ == "__main__":
    main()
