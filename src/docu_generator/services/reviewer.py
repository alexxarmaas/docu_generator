from __future__ import annotations

import json

from docu_generator.config import read_prompt
from docu_generator.models import GuideDraft, ReviewReport, ScreenEvidence
from docu_generator.services.json_tools import parse_json_object


def review_guide(provider, guide: GuideDraft, evidences: list[ScreenEvidence]) -> ReviewReport:
    issues: list[str] = []
    known_images = {item.image_name for item in evidences}

    if not guide.sections:
        issues.append("La guía no contiene secciones.")

    for section in guide.sections:
        if section.image_name and section.image_name not in known_images:
            issues.append(
                f"La sección «{section.title}» referencia una imagen inexistente: "
                f"{section.image_name}."
            )

    if not provider.ai_enabled:
        return ReviewReport(issues=issues)

    prompt = f"""
{read_prompt("review")}

EVIDENCIA:
{json.dumps([item.model_dump() for item in evidences], ensure_ascii=False, indent=2)}

GUÍA:
{json.dumps(guide.model_dump(), ensure_ascii=False, indent=2)}

Devuelve únicamente:
{{
  "issues": ["...", "..."]
}}

Si no detectas problemas respaldados por la evidencia, devuelve una lista vacía.
"""
    try:
        data = parse_json_object(provider.complete(prompt))
        model_report = ReviewReport.model_validate(data)
        issues.extend(model_report.issues)
    except Exception as exc:
        issues.append(f"No se pudo completar la revisión con IA: {exc}")

    return ReviewReport(issues=list(dict.fromkeys(issues)))
