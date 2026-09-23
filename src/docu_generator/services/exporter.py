from __future__ import annotations

import base64
import io
import zipfile

import markdown
from jinja2 import Template

from docu_generator.config import PROJECT_ROOT
from docu_generator.models import GuideBlock, GuideDraft, GuideSection, ReviewReport
from docu_generator.services.pdf_exporter import build_pdf


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


def render_markdown(guide: GuideDraft, review: ReviewReport) -> str:
    lines = [f"# {guide.title}", ""]

    if guide.introduction:
        lines.extend([guide.introduction, ""])

    for index, section in enumerate(guide.sections, start=1):
        lines.extend([f"## {index}. {section.title}", ""])

        for block in _section_blocks(section):
            if block.type == "text" and block.text:
                lines.extend([block.text, ""])

            elif block.type == "checklist" and block.items:
                lines.extend([f"- [ ] {item}" for item in block.items])
                lines.append("")

            elif block.type == "note" and block.text:
                label = block.label or "Nota"
                lines.append(f"> **{label}:**")
                lines.extend(
                    f"> {line}" if line else ">"
                    for line in block.text.splitlines()
                )
                lines.append("")

            elif block.type == "image" and block.image_name:
                alt = block.image_caption or section.title
                lines.extend([f"![{alt}](images/{block.image_name})", ""])
                if block.image_caption:
                    lines.extend([f"*{block.image_caption}*", ""])

            elif block.type == "divider":
                lines.extend(["---", ""])

    if guide.closing_note:
        lines.extend(["---", "", guide.closing_note, ""])

    if review.issues:
        lines.extend(["## Notas de revisión", ""])
        lines.extend([f"- {issue}" for issue in review.issues])
        lines.append("")

    return "\n".join(lines).strip() + "\n"


def render_html(
    guide: GuideDraft,
    review: ReviewReport,
    images: list[dict],
    profile: dict,
) -> str:
    template_path = PROJECT_ROOT / "templates" / "guide.html"
    template = Template(template_path.read_text(encoding="utf-8"))

    image_lookup = {}
    for image in images:
        encoded = base64.b64encode(image["bytes"]).decode("ascii")
        image_lookup[image["name"]] = (
            f'data:{image["mime_type"]};base64,{encoded}'
        )

    sections = []

    for section in guide.sections:
        rendered_blocks = []

        for block in _section_blocks(section):
            rendered_blocks.append(
                {
                    "type": block.type,
                    "text_html": (
                        markdown.markdown(block.text)
                        if block.type in {"text", "note"} and block.text
                        else ""
                    ),
                    "items": block.items,
                    "image_name": block.image_name,
                    "image_caption": block.image_caption,
                    "image_src": image_lookup.get(block.image_name or ""),
                    "label": block.label,
                    "variant": block.variant,
                }
            )

        sections.append(
            {
                "title": section.title,
                "blocks": rendered_blocks,
            }
        )

    return template.render(
        guide=guide,
        sections=sections,
        review=review,
        profile=profile,
        css=profile.get("css", ""),
        intro_html=markdown.markdown(guide.introduction),
        closing_html=markdown.markdown(guide.closing_note),
    )


def build_export_zip(
    guide: GuideDraft,
    review: ReviewReport,
    images: list[dict],
    profile: dict,
) -> bytes:
    markdown_text = render_markdown(guide, review)
    html_text = render_html(guide, review, images, profile)
    pdf_bytes = build_pdf(guide, images, profile)

    buffer = io.BytesIO()

    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("guide.md", markdown_text)
        archive.writestr("guide.html", html_text)
        archive.writestr("guide.pdf", pdf_bytes)
        archive.writestr(
            "review.txt",
            "\n".join(review.issues) if review.issues else "Sin avisos de revisión.\n",
        )

        written_images: set[str] = set()

        for image in images:
            if image["name"] in written_images:
                continue

            archive.writestr(f"images/{image['name']}", image["bytes"])
            written_images.add(image["name"])

    return buffer.getvalue()
