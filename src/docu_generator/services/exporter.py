from __future__ import annotations

import base64
import io
import zipfile

import markdown
from jinja2 import Template

from docu_generator.config import PROJECT_ROOT
from docu_generator.models import GuideDraft, ReviewReport


def render_markdown(guide: GuideDraft, review: ReviewReport) -> str:
    lines = [f"# {guide.title}", ""]

    if guide.introduction:
        lines.extend([guide.introduction, ""])

    for index, section in enumerate(guide.sections, start=1):
        lines.extend([f"## {index}. {section.title}", "", section.body, ""])

        if section.checklist:
            lines.extend(["### Qué comprobar", ""])
            lines.extend([f"- [ ] {item}" for item in section.checklist])
            lines.append("")

        if section.note:
            lines.extend([f"> {section.note}", ""])

        if section.image_name:
            alt = section.image_caption or section.title
            lines.extend([f"![{alt}](images/{section.image_name})", ""])
            if section.image_caption:
                lines.extend([f"*{section.image_caption}*", ""])

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
        sections.append(
            {
                "title": section.title,
                "body_html": markdown.markdown(section.body),
                "checklist": section.checklist,
                "note": section.note,
                "image_name": section.image_name,
                "image_caption": section.image_caption,
                "image_src": image_lookup.get(section.image_name or ""),
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

    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("guide.md", markdown_text)
        archive.writestr("guide.html", html_text)
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
