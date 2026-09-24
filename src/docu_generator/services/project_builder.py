from __future__ import annotations

from docu_generator.models import (
    GuideBlock,
    GuideDraft,
    GuideSection,
    ImageAnnotation,
    ImageCrop,
)
from docu_generator.services.image_renderer import render_annotated_image
from docu_generator.services.project_io import load_project


def build_document(raw: bytes) -> tuple[GuideDraft, list[dict]]:
    project = load_project(raw)
    metadata = project["metadata"]
    sections: list[GuideSection] = []
    images_by_name: dict[str, dict] = {}

    for step in project["steps"]:
        guide_blocks: list[GuideBlock] = []

        for block in step.get("blocks", []):
            block_type = block.get("type", "text")
            annotations = [
                ImageAnnotation.model_validate(item)
                for item in block.get("annotations") or []
            ]
            crop = (
                ImageCrop.model_validate(block["crop"])
                if block.get("crop")
                else None
            )

            if block_type == "text":
                text = block.get("text", "").strip()
                if text:
                    guide_blocks.append(GuideBlock(type="text", text=text))

            elif block_type == "note":
                text = block.get("text", "").strip()
                if text:
                    guide_blocks.append(
                        GuideBlock(
                            type="note",
                            text=text,
                            label=block.get("label", "").strip(),
                            variant=block.get("variant", "info"),
                        )
                    )

            elif block_type in {"checklist", "table"}:
                items = [
                    line.strip()
                    for line in block.get("items", "").splitlines()
                    if line.strip()
                ]
                if items:
                    guide_blocks.append(
                        GuideBlock(type=block_type, items=items)
                    )

            elif block_type in {"divider", "pagebreak"}:
                guide_blocks.append(GuideBlock(type=block_type))

            elif block_type == "image":
                image_name = block.get("image_name")
                image_bytes = block.get("image_bytes")
                if image_name:
                    guide_blocks.append(
                        GuideBlock(
                            type="image",
                            image_name=image_name,
                            image_caption=block.get("image_caption", "").strip(),
                            image_width=block.get("image_width", "large"),
                            align=block.get("align", "center"),
                            annotations=annotations,
                            crop=crop,
                        )
                    )

                if image_name and image_bytes is not None:
                    rendered = image_bytes
                    mime = block.get("image_mime") or "image/png"

                    if annotations or crop is not None:
                        rendered = render_annotated_image(
                            image_bytes,
                            annotations,
                            crop,
                        )
                        mime = "image/png"

                    images_by_name[image_name] = {
                        "name": image_name,
                        "mime_type": mime,
                        "bytes": rendered,
                    }

        title = step.get("title", "").strip()
        if guide_blocks or title:
            sections.append(
                GuideSection(
                    title=title or "Paso sin título",
                    blocks=guide_blocks,
                )
            )

    guide = GuideDraft(
        title=project["title"].strip() or "Guía sin título",
        introduction=project["introduction"].strip(),
        closing_note=project["closing_note"].strip(),
        sections=sections,
        document_type=metadata.get("document_type", "Guía"),
        version=metadata.get("version_label", "1.0"),
        status=metadata.get("status", "Borrador"),
        author=metadata.get("author", ""),
        updated_at=metadata.get("updated_at", ""),
        show_cover=metadata.get("show_cover", True),
        show_toc=metadata.get("show_toc", True),
    )

    return guide, list(images_by_name.values())
