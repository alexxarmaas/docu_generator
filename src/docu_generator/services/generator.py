from __future__ import annotations

import json
import re

from docu_generator.config import read_prompt
from docu_generator.models import GuideDraft, GuideSection, ScreenEvidence
from docu_generator.services.json_tools import parse_json_object


def _split_actions(instructions: str) -> list[str]:
    text = re.sub(r"\s+", " ", instructions.strip()).strip(" .")
    if not text:
        return []

    parts = re.split(
        r"\s*(?:,|;|\by luego\b|\bdespués\b|\bdespues\b|\by después\b|\by despues\b|\by\b)\s*",
        text,
        flags=re.IGNORECASE,
    )
    actions = [part.strip(" .") for part in parts if len(part.strip(" .")) >= 3]
    return actions[:6]


def _fallback_title(action: str, index: int) -> str:
    lower = action.lower()

    if any(word in lower for word in ("entra", "accede", "abre", "inicia")):
        return "Accede a Brisia"
    if any(word in lower for word in ("elige", "selecciona", "escoge", "localiza", "busca")):
        if "albar" in lower:
            return "Selecciona el albarán"
        return "Selecciona el elemento"
    if any(word in lower for word in ("revisa", "comprueba", "verifica", "valida")):
        return "Revisa la información"
    if any(word in lower for word in ("corrige", "modifica", "edita", "cambia")):
        return "Corrige lo necesario"
    if any(word in lower for word in ("confirma", "guarda", "finaliza", "termina")):
        return "Finaliza el proceso"

    return f"Paso {index}"


def _fallback_body(action: str, index: int) -> str:
    clean = action.strip().rstrip(".")
    lower = clean.lower()

    if any(word in lower for word in ("entra", "accede", "abre", "inicia")):
        return (
            "**Qué hacer**\n\n"
            f"{clean[0].upper() + clean[1:]}.\n\n"
            "**Objetivo de este paso**\n\n"
            "Llegar a la zona de trabajo desde la que vas a gestionar el albarán."
        )

    if any(word in lower for word in ("elige", "selecciona", "escoge", "localiza", "busca")):
        return (
            "**Qué hacer**\n\n"
            f"{clean[0].upper() + clean[1:]}.\n\n"
            "> Antes de continuar, asegúrate de que has abierto el documento correcto."
        )

    if any(word in lower for word in ("revisa", "comprueba", "verifica", "valida")):
        return (
            "**Qué hacer**\n\n"
            f"{clean[0].upper() + clean[1:]}.\n\n"
            "**Durante la revisión**\n\n"
            "- Recorre la información mostrada de principio a fin.\n"
            "- Compárala con el albarán original.\n"
            "- Si algún dato no coincide, detente y revísalo antes de continuar."
        )

    if any(word in lower for word in ("corrige", "modifica", "edita", "cambia")):
        return (
            "**Qué hacer**\n\n"
            f"{clean[0].upper() + clean[1:]}.\n\n"
            "**Recomendación**\n\n"
            "Haz únicamente los cambios necesarios y vuelve a comprobar el resultado antes de seguir."
        )

    if any(word in lower for word in ("confirma", "guarda", "finaliza", "termina")):
        return (
            "**Qué hacer**\n\n"
            f"{clean[0].upper() + clean[1:]}.\n\n"
            "> Finaliza únicamente cuando hayas terminado la revisión del documento."
        )

    return (
        "**Qué hacer**\n\n"
        f"{clean[0].upper() + clean[1:]}.\n\n"
        f"Completa este paso antes de continuar con el siguiente punto de la guía."
    )


def _build_fallback_guide(
    title: str,
    instructions: str,
    evidences: list[ScreenEvidence],
) -> GuideDraft:
    actions = _split_actions(instructions)

    if not actions:
        actions = ["Accede al documento", "Selecciona el albarán", "Revisa la información"]

    sections: list[GuideSection] = []
    image_names = [evidence.image_name for evidence in evidences]

    for index, action in enumerate(actions, start=1):
        image_name = image_names[index - 1] if index - 1 < len(image_names) else None
        sections.append(
            GuideSection(
                title=_fallback_title(action, index),
                body=_fallback_body(action, index),
                image_name=image_name,
            )
        )

    if len(sections) == 1 and len(image_names) > 1:
        for extra_index, image_name in enumerate(image_names[1:], start=2):
            sections.append(
                GuideSection(
                    title=f"Continúa la revisión · Pantalla {extra_index}",
                    body=(
                        "**Qué hacer**\n\n"
                        "Continúa con la revisión siguiendo el mismo criterio del paso anterior.\n\n"
                        "> Utiliza esta captura como referencia visual para ubicarte en el proceso."
                    ),
                    image_name=image_name,
                )
            )

    introduction = (
        "Esta guía resume el flujo para completar el proceso de forma ordenada. "
        "Sigue los pasos en el orden indicado y utiliza las capturas como referencia visual."
    )

    closing_note = (
        "**Antes de terminar:** comprueba que has recorrido todos los pasos de la guía "
        "y que la información revisada coincide con el documento original."
    )

    return GuideDraft(
        title=title,
        introduction=introduction,
        sections=sections,
        closing_note=closing_note,
    )


def generate_guide(
    provider,
    profile: dict,
    title: str,
    instructions: str,
    audience: str,
    evidences: list[ScreenEvidence],
) -> GuideDraft:
    if not provider.ai_enabled:
        return _build_fallback_guide(
            title=title,
            instructions=instructions,
            evidences=evidences,
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
      "image_name": "nombre-exacto-de-la-imagen"
    }},
    {{
      "title": "...",
      "body": "...",
      "image_name": null
    }}
  ],
  "closing_note": ""
}}

Usa null, sin comillas, cuando una sección no necesite imagen.
"""
    raw = provider.complete(prompt)
    data = parse_json_object(raw)
    data["title"] = title
    return GuideDraft.model_validate(data)
