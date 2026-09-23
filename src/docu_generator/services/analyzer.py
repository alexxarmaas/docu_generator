from __future__ import annotations

from docu_generator.config import read_prompt
from docu_generator.models import ScreenEvidence
from docu_generator.services.json_tools import parse_json_object


def analyze_images(provider, images: list[dict], instructions: str) -> list[ScreenEvidence]:
    if not provider.ai_enabled:
        return [
            ScreenEvidence(
                image_name=image["name"],
                screen_name=f"Captura {index}",
                visible_elements=[],
                supported_actions=[],
                uncertainties=[
                    "Modo fallback: la captura no ha sido interpretada visualmente."
                ],
            )
            for index, image in enumerate(images, start=1)
        ]

    prompt_template = read_prompt("image_analysis")
    evidences: list[ScreenEvidence] = []

    for image in images:
        prompt = (
            f"{prompt_template}\n\n"
            f"OBJETIVO GENERAL DE LA GUÍA:\n{instructions}\n\n"
            f"NOMBRE DEL ARCHIVO: {image['name']}\n"
            "Devuelve únicamente JSON válido."
        )
        raw = provider.complete(prompt, images=[image])
        data = parse_json_object(raw)
        data["image_name"] = image["name"]
        evidences.append(ScreenEvidence.model_validate(data))

    return evidences
