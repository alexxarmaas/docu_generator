from __future__ import annotations

import base64
import json
from uuid import uuid4


PROJECT_VERSION = 3


DEFAULT_METADATA = {
    "document_type": "Guía",
    "version_label": "1.0",
    "status": "Borrador",
    "author": "",
    "show_cover": True,
    "show_toc": True,
}


def _encode_image(raw: bytes | None) -> str | None:
    if raw is None:
        return None
    return base64.b64encode(raw).decode("ascii")


def _decode_image(raw: str | None) -> bytes | None:
    if not raw:
        return None
    return base64.b64decode(raw)


def _normalize_block(block: dict) -> dict:
    return {
        "id": uuid4().hex,
        "type": block.get("type", "text"),
        "text": block.get("text", ""),
        "items": block.get("items", ""),
        "image_name": block.get("image_name"),
        "image_caption": block.get("image_caption", ""),
        "image_bytes": _decode_image(block.get("image_base64")),
        "image_mime": block.get("image_mime"),
        "label": block.get("label", ""),
        "variant": block.get("variant", "info"),
        "image_width": block.get("image_width", "large"),
        "align": block.get("align", "center"),
    }


def dump_project(
    title: str,
    introduction: str,
    closing_note: str,
    steps: list[dict],
    metadata: dict | None = None,
) -> bytes:
    payload_steps = []

    for step in steps:
        payload_blocks = []

        for block in step.get("blocks", []):
            payload_blocks.append(
                {
                    "type": block.get("type", "text"),
                    "text": block.get("text", ""),
                    "items": block.get("items", ""),
                    "image_name": block.get("image_name"),
                    "image_caption": block.get("image_caption", ""),
                    "image_mime": block.get("image_mime"),
                    "image_base64": _encode_image(block.get("image_bytes")),
                    "label": block.get("label", ""),
                    "variant": block.get("variant", "info"),
                    "image_width": block.get("image_width", "large"),
                    "align": block.get("align", "center"),
                }
            )

        payload_steps.append(
            {
                "title": step.get("title", ""),
                "blocks": payload_blocks,
            }
        )

    merged_metadata = dict(DEFAULT_METADATA)
    if metadata:
        merged_metadata.update(metadata)

    payload = {
        "version": PROJECT_VERSION,
        "title": title,
        "introduction": introduction,
        "closing_note": closing_note,
        "metadata": merged_metadata,
        "steps": payload_steps,
    }

    return json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")


def _load_v3(payload: dict) -> list[dict]:
    steps = []

    for item in payload.get("steps", []):
        blocks = [_normalize_block(block) for block in item.get("blocks", [])]
        steps.append(
            {
                "id": uuid4().hex,
                "title": item.get("title", ""),
                "blocks": blocks,
            }
        )

    return steps


def _load_v2(payload: dict) -> list[dict]:
    steps = []

    for item in payload.get("steps", []):
        blocks = [_normalize_block(block) for block in item.get("blocks", [])]
        steps.append(
            {
                "id": uuid4().hex,
                "title": item.get("title", ""),
                "blocks": blocks,
            }
        )

    return steps


def _legacy_block(
    block_type: str,
    *,
    text: str = "",
    items: str = "",
    image_name: str | None = None,
    image_caption: str = "",
    image_bytes: bytes | None = None,
    image_mime: str | None = None,
    label: str = "",
    variant: str = "info",
) -> dict:
    return {
        "id": uuid4().hex,
        "type": block_type,
        "text": text,
        "items": items,
        "image_name": image_name,
        "image_caption": image_caption,
        "image_bytes": image_bytes,
        "image_mime": image_mime,
        "label": label,
        "variant": variant,
        "image_width": "large",
        "align": "center",
    }


def _load_v1(payload: dict) -> list[dict]:
    """Migrate the original fixed-field editor format to free blocks."""
    steps = []

    for item in payload.get("steps", []):
        blocks = []

        if item.get("body"):
            blocks.append(
                _legacy_block("text", text=item.get("body", ""))
            )

        image_bytes = _decode_image(item.get("image_base64"))
        if item.get("image_name") or image_bytes is not None:
            blocks.append(
                _legacy_block(
                    "image",
                    image_name=item.get("image_name"),
                    image_caption=item.get("image_caption", ""),
                    image_bytes=image_bytes,
                    image_mime=item.get("image_mime"),
                )
            )

        if item.get("checklist"):
            blocks.append(
                _legacy_block(
                    "checklist",
                    items=item.get("checklist", ""),
                )
            )

        if item.get("note"):
            blocks.append(
                _legacy_block(
                    "note",
                    text=item.get("note", ""),
                    label="Importante",
                    variant="warning",
                )
            )

        steps.append(
            {
                "id": uuid4().hex,
                "title": item.get("title", ""),
                "blocks": blocks,
            }
        )

    return steps


def load_project(raw: bytes) -> dict:
    payload = json.loads(raw.decode("utf-8"))
    version = payload.get("version", 1)

    if version == 3:
        steps = _load_v3(payload)
    elif version == 2:
        steps = _load_v2(payload)
    elif version == 1:
        steps = _load_v1(payload)
    else:
        raise ValueError(f"Versión de proyecto no compatible: {version}")

    metadata = dict(DEFAULT_METADATA)
    metadata.update(payload.get("metadata") or {})

    return {
        "title": payload.get("title", ""),
        "introduction": payload.get("introduction", ""),
        "closing_note": payload.get("closing_note", ""),
        "metadata": metadata,
        "steps": steps,
    }
