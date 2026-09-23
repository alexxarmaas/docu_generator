from __future__ import annotations

import html
import io
import re

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    HRFlowable,
    Image,
    KeepTogether,
    ListFlowable,
    ListItem,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from docu_generator.models import GuideBlock, GuideDraft, GuideSection


def _hex(value: str | None, fallback: str):
    try:
        return colors.HexColor(value or fallback)
    except Exception:
        return colors.HexColor(fallback)


def _inline_markup(text: str) -> str:
    value = html.escape(text)
    value = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", value)
    value = re.sub(r"(?<!\*)\*(.+?)\*(?!\*)", r"<i>\1</i>", value)
    return value


def _section_blocks(section: GuideSection) -> list[GuideBlock]:
    if section.blocks:
        return section.blocks

    blocks: list[GuideBlock] = []

    if section.body:
        blocks.append(GuideBlock(type="text", text=section.body))
    if section.checklist:
        blocks.append(GuideBlock(type="checklist", items=section.checklist))
    if section.note:
        blocks.append(
            GuideBlock(
                type="note",
                text=section.note,
                label="Importante",
                variant="warning",
            )
        )
    if section.image_name:
        blocks.append(
            GuideBlock(
                type="image",
                image_name=section.image_name,
                image_caption=section.image_caption,
            )
        )

    return blocks


def _text_flowables(text: str, body_style: ParagraphStyle):
    flowables = []
    paragraphs = re.split(r"\n\s*\n", text.strip())

    for paragraph in paragraphs:
        if not paragraph.strip():
            continue

        lines = [line.rstrip() for line in paragraph.splitlines()]

        if all(
            not line.strip() or line.lstrip().startswith(("- ", "* "))
            for line in lines
        ):
            items = []
            for line in lines:
                clean = line.strip()
                if not clean:
                    continue
                items.append(
                    ListItem(
                        Paragraph(_inline_markup(clean[2:].strip()), body_style),
                        leftIndent=8,
                    )
                )
            if items:
                flowables.append(
                    ListFlowable(
                        items,
                        bulletType="bullet",
                        leftIndent=16,
                    )
                )
                flowables.append(Spacer(1, 3 * mm))
            continue

        joined = "<br/>".join(
            _inline_markup(line) for line in lines if line.strip()
        )
        flowables.append(Paragraph(joined, body_style))
        flowables.append(Spacer(1, 3 * mm))

    return flowables


def _image_max_width(document_width: float, size: str) -> float:
    ratios = {
        "small": 0.42,
        "medium": 0.62,
        "large": 0.84,
        "full": 1.0,
    }
    return document_width * ratios.get(size, 0.84)


def _scaled_image(
    raw: bytes,
    max_width: float,
    max_height: float,
    align: str = "center",
):
    image = Image(io.BytesIO(raw))
    scale = min(
        max_width / image.imageWidth,
        max_height / image.imageHeight,
        1.0,
    )
    image.drawWidth = image.imageWidth * scale
    image.drawHeight = image.imageHeight * scale
    image.hAlign = {
        "left": "LEFT",
        "center": "CENTER",
        "right": "RIGHT",
    }.get(align, "CENTER")
    return image


def _table_flowable(rows: list[str], width: float, primary, border):
    parsed = [
        [cell.strip() for cell in row.split("|")]
        for row in rows
        if row.strip()
    ]
    if not parsed:
        return None

    columns = max(len(row) for row in parsed)
    normalized = [
        row + [""] * (columns - len(row))
        for row in parsed
    ]
    table = Table(
        normalized,
        colWidths=[width / columns] * columns,
        repeatRows=1,
        hAlign="LEFT",
    )
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#EEF3F6")),
                ("TEXTCOLOR", (0, 0), (-1, 0), primary),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
                ("FONTSIZE", (0, 0), (-1, -1), 8.5),
                ("LEADING", (0, 0), (-1, -1), 11),
                ("GRID", (0, 0), (-1, -1), 0.45, border),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    return table


def build_pdf(
    guide: GuideDraft,
    images: list[dict],
    profile: dict,
) -> bytes:
    buffer = io.BytesIO()

    primary = _hex(profile.get("brand", {}).get("primary"), "#092D54")
    accent = _hex(profile.get("brand", {}).get("accent"), "#00B8A9")
    text_color = colors.HexColor("#16324A")
    muted = colors.HexColor("#667A8A")
    border = colors.HexColor("#DDE5EB")

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=18 * mm,
        rightMargin=18 * mm,
        topMargin=18 * mm,
        bottomMargin=18 * mm,
        title=guide.title,
        author=guide.author or profile.get("name", "Docu Generator"),
    )

    styles = getSampleStyleSheet()

    eyebrow_style = ParagraphStyle(
        "Eyebrow",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=8,
        leading=10,
        textColor=accent,
        spaceAfter=3 * mm,
    )
    cover_title_style = ParagraphStyle(
        "CoverTitle",
        parent=styles["Title"],
        fontName="Helvetica-Bold",
        fontSize=30,
        leading=36,
        textColor=primary,
        alignment=TA_CENTER,
        spaceAfter=7 * mm,
    )
    cover_meta_style = ParagraphStyle(
        "CoverMeta",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=11,
        leading=17,
        textColor=muted,
        alignment=TA_CENTER,
    )
    title_style = ParagraphStyle(
        "GuideTitle",
        parent=styles["Title"],
        fontName="Helvetica-Bold",
        fontSize=24,
        leading=28,
        textColor=primary,
        alignment=TA_LEFT,
        spaceAfter=5 * mm,
    )
    intro_style = ParagraphStyle(
        "Intro",
        parent=styles["BodyText"],
        fontName="Helvetica",
        fontSize=10.5,
        leading=16,
        textColor=muted,
        spaceAfter=8 * mm,
    )
    step_style = ParagraphStyle(
        "Step",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=15,
        leading=19,
        textColor=primary,
        spaceBefore=4 * mm,
        spaceAfter=5 * mm,
    )
    toc_style = ParagraphStyle(
        "TOC",
        parent=styles["BodyText"],
        fontName="Helvetica",
        fontSize=10.5,
        leading=16,
        textColor=text_color,
        leftIndent=4 * mm,
        spaceAfter=2 * mm,
    )
    body_style = ParagraphStyle(
        "Body",
        parent=styles["BodyText"],
        fontName="Helvetica",
        fontSize=10,
        leading=15,
        textColor=text_color,
    )
    caption_style = ParagraphStyle(
        "Caption",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8,
        leading=10,
        textColor=muted,
        alignment=TA_CENTER,
        spaceBefore=2 * mm,
        spaceAfter=3 * mm,
    )
    callout_label_style = ParagraphStyle(
        "CalloutLabel",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=9,
        leading=11,
        textColor=primary,
        spaceAfter=1.5 * mm,
    )
    callout_body_style = ParagraphStyle(
        "CalloutBody",
        parent=body_style,
        fontSize=9.5,
        leading=14,
    )
    closing_style = ParagraphStyle(
        "Closing",
        parent=body_style,
        textColor=primary,
    )

    image_lookup = {image["name"]: image for image in images}
    story = []
    product_name = profile.get("product") or profile.get("name") or "Producto"

    if guide.show_cover:
        story.append(Spacer(1, 28 * mm))
        story.append(
            Paragraph(
                html.escape(str(product_name)).upper(),
                ParagraphStyle(
                    "CoverProduct",
                    parent=eyebrow_style,
                    alignment=TA_CENTER,
                    fontSize=10,
                ),
            )
        )
        story.append(Spacer(1, 7 * mm))
        story.append(Paragraph(_inline_markup(guide.title), cover_title_style))
        story.append(
            Paragraph(
                "<br/>".join(
                    [
                        html.escape(guide.document_type),
                        f"Versión {html.escape(guide.version)}",
                        html.escape(guide.status),
                    ]
                ),
                cover_meta_style,
            )
        )

        if guide.author:
            story.append(Spacer(1, 8 * mm))
            story.append(
                Paragraph(
                    f"Autor: {html.escape(guide.author)}",
                    cover_meta_style,
                )
            )

        if guide.updated_at:
            story.append(
                Paragraph(
                    f"Actualizado: {html.escape(guide.updated_at)}",
                    cover_meta_style,
                )
            )

        story.append(PageBreak())

    if guide.show_toc and guide.sections:
        story.append(Paragraph("Contenido", title_style))
        for index, section in enumerate(guide.sections, start=1):
            story.append(
                Paragraph(
                    f"<b>{index}.</b> {_inline_markup(section.title)}",
                    toc_style,
                )
            )
        story.append(PageBreak())

    story.append(
        Paragraph(
            f"{html.escape(str(product_name)).upper()} - {html.escape(guide.document_type).upper()}",
            eyebrow_style,
        )
    )
    story.append(Paragraph(_inline_markup(guide.title), title_style))

    if guide.introduction:
        story.append(
            Paragraph(
                "<br/>".join(
                    _inline_markup(line)
                    for line in guide.introduction.splitlines()
                    if line.strip()
                ),
                intro_style,
            )
        )

    story.append(
        HRFlowable(
            width="100%",
            thickness=0.7,
            color=border,
            spaceAfter=5 * mm,
        )
    )

    callout_backgrounds = {
        "info": colors.HexColor("#EEF6FC"),
        "tip": colors.HexColor("#F0FBFA"),
        "warning": colors.HexColor("#FFF8E8"),
        "success": colors.HexColor("#EEF9F1"),
    }
    callout_borders = {
        "info": colors.HexColor("#4A90C2"),
        "tip": accent,
        "warning": colors.HexColor("#E2A72E"),
        "success": colors.HexColor("#48A868"),
    }

    for section_index, section in enumerate(guide.sections, start=1):
        section_story = [
            Paragraph(
                f"{section_index}. {_inline_markup(section.title)}",
                step_style,
            )
        ]

        for block in _section_blocks(section):
            if block.type == "pagebreak":
                if section_story:
                    story.append(KeepTogether(section_story))
                    section_story = []
                story.append(PageBreak())
                continue

            if block.type == "text" and block.text:
                section_story.extend(_text_flowables(block.text, body_style))

            elif block.type == "checklist" and block.items:
                checklist_items = [
                    ListItem(
                        Paragraph(f"[ ] {_inline_markup(item)}", body_style),
                        leftIndent=6,
                    )
                    for item in block.items
                ]
                section_story.append(
                    ListFlowable(
                        checklist_items,
                        bulletType="bullet",
                        leftIndent=14,
                        bulletColor=accent,
                    )
                )
                section_story.append(Spacer(1, 4 * mm))

            elif block.type == "note" and block.text:
                label = block.label or "Nota"
                callout_content = [
                    Paragraph(html.escape(label), callout_label_style),
                    Paragraph(
                        "<br/>".join(
                            _inline_markup(line)
                            for line in block.text.splitlines()
                            if line.strip()
                        ),
                        callout_body_style,
                    ),
                ]
                table = Table([[callout_content]], colWidths=[doc.width])
                table.setStyle(
                    TableStyle(
                        [
                            (
                                "BACKGROUND",
                                (0, 0),
                                (-1, -1),
                                callout_backgrounds.get(
                                    block.variant,
                                    callout_backgrounds["info"],
                                ),
                            ),
                            (
                                "BOX",
                                (0, 0),
                                (-1, -1),
                                0.6,
                                callout_borders.get(block.variant, accent),
                            ),
                            ("LEFTPADDING", (0, 0), (-1, -1), 10),
                            ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                            ("TOPPADDING", (0, 0), (-1, -1), 8),
                            ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                        ]
                    )
                )
                section_story.append(table)
                section_story.append(Spacer(1, 4 * mm))

            elif block.type == "image" and block.image_name:
                image_data = image_lookup.get(block.image_name)
                if image_data:
                    try:
                        section_story.append(
                            _scaled_image(
                                image_data["bytes"],
                                max_width=_image_max_width(
                                    doc.width,
                                    block.image_width,
                                ),
                                max_height=95 * mm,
                                align=block.align,
                            )
                        )
                        if block.image_caption:
                            caption = Paragraph(
                                html.escape(block.image_caption),
                                caption_style,
                            )
                            section_story.append(caption)
                        else:
                            section_story.append(Spacer(1, 3 * mm))
                    except Exception:
                        section_story.append(
                            Paragraph(
                                "No se pudo renderizar esta imagen en el PDF.",
                                caption_style,
                            )
                        )

            elif block.type == "divider":
                section_story.append(
                    HRFlowable(
                        width="100%",
                        thickness=0.6,
                        color=border,
                        spaceBefore=1 * mm,
                        spaceAfter=4 * mm,
                    )
                )

            elif block.type == "table":
                table = _table_flowable(
                    block.items,
                    doc.width,
                    primary,
                    border,
                )
                if table is not None:
                    section_story.append(table)
                    section_story.append(Spacer(1, 4 * mm))

        if section_story:
            story.append(KeepTogether(section_story))

        if section_index < len(guide.sections):
            story.append(Spacer(1, 3 * mm))

    if guide.closing_note:
        story.append(
            HRFlowable(
                width="100%",
                thickness=0.8,
                color=accent,
                spaceBefore=4 * mm,
                spaceAfter=4 * mm,
            )
        )
        story.append(
            Paragraph(
                "<br/>".join(
                    _inline_markup(line)
                    for line in guide.closing_note.splitlines()
                    if line.strip()
                ),
                closing_style,
            )
        )

    def _footer(canvas, document):
        canvas.saveState()
        canvas.setStrokeColor(border)
        canvas.setLineWidth(0.4)
        canvas.line(
            document.leftMargin,
            11 * mm,
            A4[0] - document.rightMargin,
            11 * mm,
        )
        canvas.setFillColor(muted)
        canvas.setFont("Helvetica", 7.5)
        canvas.drawString(
            document.leftMargin,
            7 * mm,
            f"{product_name} · {guide.document_type} · v{guide.version}",
        )
        canvas.drawRightString(
            A4[0] - document.rightMargin,
            7 * mm,
            f"Página {document.page}",
        )
        canvas.restoreState()

    doc.build(
        story,
        onFirstPage=_footer,
        onLaterPages=_footer,
    )

    return buffer.getvalue()
