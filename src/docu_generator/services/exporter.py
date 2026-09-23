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
        if section.image_name:
            lines.extend([f"![{section.title}](images/{section.image_name})", ""])

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
                "image_name": section.image_name,
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
        for image in images:
            archive.writestr(f"images/{image['name']}", image["bytes"])

    return buffer.getvalue()
