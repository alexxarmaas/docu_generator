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
    ListFlowable,
    ListItem,
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
                item_text = clean[2:].strip()
                items.append(
                    ListItem(
                        Paragraph(_inline_markup(item_text), body_style),
                        leftIndent=8,
                    )
                )

            if items:
                flowables.append(
                    ListFlowable(
                        items,
                        bulletType="bullet",
                        leftIndent=16,
                        bulletFontName="Helvetica",
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


def _scaled_image(raw: bytes, max_width: float, max_height: float):
    image = Image(io.BytesIO(raw))
    scale = min(
        max_width / image.imageWidth,
        max_height / image.imageHeight,
        1.0,
    )
    image.drawWidth = image.imageWidth * scale
    image.drawHeight = image.imageHeight * scale
    image.hAlign = "CENTER"
    return image


def build_pdf(
    guide: GuideDraft,
    images: list[dict],
    profile: dict,
) -> bytes:
    buffer = io.BytesIO()

    primary = _hex(
        profile.get("brand", {}).get("primary"),
        "#092D54",
    )
    accent = _hex(
        profile.get("brand", {}).get("accent"),
        "#00B8A9",
    )
    text_color = colors.HexColor("#16324A")
    muted = colors.HexColor("#667A8A")

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=18 * mm,
        rightMargin=18 * mm,
        topMargin=18 * mm,
        bottomMargin=18 * mm,
        title=guide.title,
        author=profile.get("name", "Docu Generator"),
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
    story.append(
        Paragraph(
            f"{html.escape(str(product_name)).upper()} - GUIA DE USUARIO",
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
            color=colors.HexColor("#DDE5EB"),
            spaceAfter=5 * mm,
        )
    )

    callout_backgrounds = {
        "info": colors.HexColor("#EEF6FC"),
        "tip": colors.HexColor("#F0FBFA"),
        "warning": colors.HexColor("#FFF8E8"),
        "success": colors.HexColor("#EEF9F1"),
    }

    for section_index, section in enumerate(guide.sections, start=1):
        story.append(
            Paragraph(
                f"{section_index}. {_inline_markup(section.title)}",
                step_style,
            )
        )

        for block in _section_blocks(section):
            if block.type == "text" and block.text:
                story.extend(_text_flowables(block.text, body_style))

            elif block.type == "checklist" and block.items:
                checklist_items = []
                for item in block.items:
                    checklist_items.append(
                        ListItem(
                            Paragraph(
                                f"[ ] {_inline_markup(item)}",
                                body_style,
                            ),
                            leftIndent=6,
                        )
                    )

                story.append(
                    ListFlowable(
                        checklist_items,
                        bulletType="bullet",
                        leftIndent=14,
                        bulletColor=accent,
                    )
                )
                story.append(Spacer(1, 4 * mm))

            elif block.type == "note" and block.text:
                label = block.label or "Nota"
                callout_content = [
                    Paragraph(
                        html.escape(label),
                        callout_label_style,
                    ),
                    Paragraph(
                        "<br/>".join(
                            _inline_markup(line)
                            for line in block.text.splitlines()
                            if line.strip()
                        ),
                        callout_body_style,
                    ),
                ]
                table = Table(
                    [[callout_content]],
                    colWidths=[doc.width],
                    hAlign="LEFT",
                )
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
                            ("BOX", (0, 0), (-1, -1), 0.5, accent),
                            ("LEFTPADDING", (0, 0), (-1, -1), 10),
                            ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                            ("TOPPADDING", (0, 0), (-1, -1), 8),
                            ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                        ]
                    )
                )
                story.append(table)
                story.append(Spacer(1, 4 * mm))

            elif block.type == "image" and block.image_name:
                image_data = image_lookup.get(block.image_name)
                if image_data:
                    try:
                        story.append(
                            _scaled_image(
                                image_data["bytes"],
                                max_width=doc.width,
                                max_height=120 * mm,
                            )
                        )
                        if block.image_caption:
                            story.append(
                                Paragraph(
                                    html.escape(block.image_caption),
                                    caption_style,
                                )
                            )
                        else:
                            story.append(Spacer(1, 3 * mm))
                    except Exception:
                        story.append(
                            Paragraph(
                                "No se pudo renderizar esta imagen en el PDF.",
                                caption_style,
                            )
                        )

            elif block.type == "divider":
                story.append(
                    HRFlowable(
                        width="100%",
                        thickness=0.6,
                        color=colors.HexColor("#DDE5EB"),
                        spaceBefore=1 * mm,
                        spaceAfter=4 * mm,
                    )
                )

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
        canvas.setStrokeColor(colors.HexColor("#DDE5EB"))
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
            f"Generado con Docu Generator - {profile.get('name', 'Perfil')}",
        )
        canvas.drawRightString(
            A4[0] - document.rightMargin,
            7 * mm,
            f"Pagina {document.page}",
        )
        canvas.restoreState()

    doc.build(
        story,
        onFirstPage=_footer,
        onLaterPages=_footer,
    )

    return buffer.getvalue()
