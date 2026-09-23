from __future__ import annotations

import base64
import json
from uuid import uuid4


PROJECT_VERSION = 1


def dump_project(
    title: str,
    introduction: str,
    closing_note: str,
    steps: list[dict],
) -> bytes:
    payload_steps = []

    for step in steps:
        image_data = None
        if step.get("image_bytes") is not None:
            image_data = base64.b64encode(step["image_bytes"]).decode("ascii")

        payload_steps.append(
            {
                "title": step.get("title", ""),
                "body": step.get("body", ""),
                "checklist": step.get("checklist", ""),
                "note": step.get("note", ""),
                "image_name": step.get("image_name"),
                "image_caption": step.get("image_caption", ""),
                "image_mime": step.get("image_mime"),
                "image_base64": image_data,
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


def load_project(raw: bytes) -> dict:
    payload = json.loads(raw.decode("utf-8"))

    if payload.get("version") != PROJECT_VERSION:
        raise ValueError(
            f"Versión de proyecto no compatible: {payload.get('version')}"
        )

    steps = []
    for item in payload.get("steps", []):
        image_bytes = None
        image_base64 = item.get("image_base64")
        if image_base64:
            image_bytes = base64.b64decode(image_base64)

        steps.append(
            {
                "id": uuid4().hex,
                "title": item.get("title", ""),
                "body": item.get("body", ""),
                "checklist": item.get("checklist", ""),
                "note": item.get("note", ""),
                "image_name": item.get("image_name"),
                "image_caption": item.get("image_caption", ""),
                "image_bytes": image_bytes,
                "image_mime": item.get("image_mime"),
            }
        )

    return {
        "title": payload.get("title", ""),
        "introduction": payload.get("introduction", ""),
        "closing_note": payload.get("closing_note", ""),
        "steps": steps,
    }
