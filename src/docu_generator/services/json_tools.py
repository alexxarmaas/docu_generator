from __future__ import annotations

import json


def parse_json_object(raw: str) -> dict:
    text = raw.strip()

    if text.startswith("```"):
        lines = text.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        text = "\n".join(lines).strip()

    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end < start:
        raise ValueError("La respuesta del modelo no contiene un objeto JSON.")

    return json.loads(text[start : end + 1])
