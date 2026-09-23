from __future__ import annotations

import json

from docu_generator.config import read_prompt
from docu_generator.models import GuideDraft, GuideSection, ScreenEvidence
from docu_generator.services.json_tools import parse_json_object


def generate_guide(
    provider,
    profile: dict,
    title: str,
    instructions: str,
    audience: str,
    evidences: list[ScreenEvidence],
) -> GuideDraft:
    if not provider.ai_enabled:
        sections = []
        for index, evidence in enumerate(evidences, start=1):
            sections.append(
                GuideSection(
                    title=evidence.screen_name,
                    body=(
                        f"Paso {index}. Revisa esta pantalla siguiendo el objetivo indicado: "
                        f"{instructions}"
                    ),
                    image_name=evidence.image_name,
                )
            )
        return GuideDraft(
            title=title,
            introduction=(
                "Borrador generado en modo fallback. Activa la IA para interpretar "
                "las capturas y producir instrucciones específicas."
            ),
            sections=sections,
        )

    system_prompt = read_prompt("system")
    guide_prompt = read_prompt("guide_generation")
    evidence_json = json.dumps(
        [evidence.model_dump() for evidence in evidences],
        ensure_ascii=False,
        indent=2,
    )

    prompt = f"""
{system_prompt}

{guide_prompt}

PERFIL:
{json.dumps(profile.get("instructions", []), ensure_ascii=False)}

TÍTULO:
{title}

AUDIENCIA:
{audience}

OBJETIVO DEL USUARIO:
{instructions}

EVIDENCIA DISPONIBLE:
{evidence_json}

Devuelve únicamente un objeto JSON con esta forma:
{{
  "title": "...",
  "introduction": "...",
  "sections": [
    {{
      "title": "...",
      "body": "...",
      "image_name": "nombre-exacto-de-la-imagen-o-null"
    }}
  ],
  "closing_note": ""
}}
"""
    raw = provider.complete(prompt)
    data = parse_json_object(raw)
    data["title"] = title
    return GuideDraft.model_validate(data)
