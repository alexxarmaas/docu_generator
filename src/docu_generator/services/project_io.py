from __future__ import annotations

import base64
import json
from uuid import uuid4


PROJECT_VERSION = 2


def _encode_image(raw: bytes | None) -> str | None:
    if raw is None:
        return None
    return base64.b64encode(raw).decode("ascii")


def _decode_image(raw: str | None) -> bytes | None:
    if not raw:
        return None
    return base64.b64decode(raw)


def dump_project(
    title: str,
    introduction: str,
    closing_note: str,
    steps: list[dict],
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
                }
            )

        payload_steps.append(
            {
                "title": step.get("title", ""),
                "blocks": payload_blocks,
            }
        )

    payload = {
        "version": PROJECT_VERSION,
        "title": title,
        "introduction": introduction,
        "closing_note": closing_note,
        "steps": payload_steps,
    }

    return json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")


def _load_v2(payload: dict) -> list[dict]:
    steps = []

    for item in payload.get("steps", []):
        blocks = []

        for block in item.get("blocks", []):
            blocks.append(
                {
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
                }
            )

        steps.append(
            {
                "id": uuid4().hex,
                "title": item.get("title", ""),
                "blocks": blocks,
            }
        )

    return steps


def _load_v1(payload: dict) -> list[dict]:
    """Migrate the original fixed-field editor format to free blocks."""
    steps = []

    for item in payload.get("steps", []):
        blocks = []

        if item.get("body"):
            blocks.append(
                {
                    "id": uuid4().hex,
                    "type": "text",
                    "text": item.get("body", ""),
                    "items": "",
                    "image_name": None,
                    "image_caption": "",
                    "image_bytes": None,
                    "image_mime": None,
                    "label": "",
                    "variant": "info",
                }
            )

        image_bytes = _decode_image(item.get("image_base64"))

        if item.get("image_name") or image_bytes is not None:
            blocks.append(
                {
                    "id": uuid4().hex,
                    "type": "image",
                    "text": "",
                    "items": "",
                    "image_name": item.get("image_name"),
                    "image_caption": item.get("image_caption", ""),
                    "image_bytes": image_bytes,
                    "image_mime": item.get("image_mime"),
                    "label": "",
                    "variant": "info",
                }
            )

        if item.get("checklist"):
            blocks.append(
                {
                    "id": uuid4().hex,
                    "type": "checklist",
                    "text": "",
                    "items": item.get("checklist", ""),
                    "image_name": None,
                    "image_caption": "",
                    "image_bytes": None,
                    "image_mime": None,
                    "label": "",
                    "variant": "info",
                }
            )

        if item.get("note"):
            blocks.append(
                {
                    "id": uuid4().hex,
                    "type": "note",
                    "text": item.get("note", ""),
                    "items": "",
                    "image_name": None,
                    "image_caption": "",
                    "image_bytes": None,
                    "image_mime": None,
                    "label": "Importante",
                    "variant": "warning",
                }
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

    if version == 2:
        steps = _load_v2(payload)
    elif version == 1:
        steps = _load_v1(payload)
    else:
        raise ValueError(f"Versión de proyecto no compatible: {version}")

    return {
        "title": payload.get("title", ""),
        "introduction": payload.get("introduction", ""),
        "closing_note": payload.get("closing_note", ""),
        "steps": steps,
    }
