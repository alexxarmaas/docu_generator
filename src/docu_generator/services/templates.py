from __future__ import annotations

from copy import deepcopy
from uuid import uuid4


def _block(block_type: str, **kwargs) -> dict:
    return {
        "id": uuid4().hex,
        "type": block_type,
        "text": kwargs.get("text", ""),
        "items": kwargs.get("items", ""),
        "image_name": None,
        "image_caption": "",
        "image_bytes": None,
        "image_mime": None,
        "label": kwargs.get("label", ""),
        "variant": kwargs.get("variant", "info"),
        "image_width": kwargs.get("image_width", "large"),
        "align": kwargs.get("align", "center"),
    }


def _step(title: str, blocks: list[dict]) -> dict:
    return {
        "id": uuid4().hex,
        "title": title,
        "blocks": blocks,
    }


TEMPLATES = {
    "blank": {
        "name": "En blanco",
        "document_type": "Guía",
        "introduction": "",
        "closing_note": "",
        "steps": [
            _step("", [_block("text")]),
        ],
    },
    "tutorial": {
        "name": "Tutorial paso a paso",
        "document_type": "Tutorial",
        "introduction": "Sigue estos pasos para completar el proceso de principio a fin.",
        "closing_note": "Comprueba el resultado final antes de dar el proceso por terminado.",
        "steps": [
            _step(
                "Accede a la funcionalidad",
                [
                    _block("text", text="Explica cómo llegar a la pantalla inicial."),
                    _block("image"),
                ],
            ),
            _step(
                "Realiza la acción principal",
                [
                    _block("text", text="Describe la acción que debe realizar el usuario."),
                    _block("image"),
                    _block(
                        "note",
                        label="Consejo",
                        variant="tip",
                        text="Añade aquí una recomendación útil.",
                    ),
                ],
            ),
            _step(
                "Comprueba el resultado",
                [
                    _block(
                        "checklist",
                        items="Resultado correcto\nDatos revisados",
                    ),
                    _block(
                        "note",
                        label="Resultado esperado",
                        variant="success",
                        text="Describe cómo debe quedar el proceso cuando termina correctamente.",
                    ),
                ],
            ),
        ],
    },
    "procedure": {
        "name": "Procedimiento operativo",
        "document_type": "Procedimiento",
        "introduction": "Este procedimiento describe la secuencia recomendada para completar la tarea de forma consistente.",
        "closing_note": "Registra o comunica cualquier incidencia detectada durante el procedimiento.",
        "steps": [
            _step(
                "Antes de empezar",
                [
                    _block(
                        "checklist",
                        items="Acceso disponible\nInformación necesaria preparada",
                    ),
                    _block(
                        "note",
                        label="Antes de continuar",
                        variant="info",
                        text="Verifica los requisitos previos antes de empezar.",
                    ),
                ],
            ),
            _step(
                "Ejecuta el procedimiento",
                [
                    _block("text"),
                    _block("image"),
                    _block(
                        "note",
                        label="Importante",
                        variant="warning",
                        text="Añade aquí cualquier condición que pueda afectar al resultado.",
                    ),
                ],
            ),
            _step(
                "Validación final",
                [
                    _block("checklist"),
                    _block(
                        "note",
                        label="Resultado esperado",
                        variant="success",
                    ),
                ],
            ),
        ],
    },
    "troubleshooting": {
        "name": "Resolución de problemas",
        "document_type": "Troubleshooting",
        "introduction": "Utiliza esta guía para identificar el problema, aplicar las comprobaciones recomendadas y validar la solución.",
        "closing_note": "Si el problema persiste después de completar las comprobaciones, escala la incidencia con la información recopilada.",
        "steps": [
            _step(
                "Identifica el síntoma",
                [
                    _block("text", text="Describe el error o comportamiento observado."),
                    _block("image"),
                ],
            ),
            _step(
                "Comprueba las causas habituales",
                [
                    _block("checklist"),
                    _block(
                        "note",
                        label="Importante",
                        variant="warning",
                        text="No realices cambios destructivos sin una copia o validación previa.",
                    ),
                ],
            ),
            _step(
                "Aplica la solución",
                [
                    _block("text"),
                    _block("image"),
                    _block(
                        "note",
                        label="Resultado esperado",
                        variant="success",
                    ),
                ],
            ),
        ],
    },
    "quickstart": {
        "name": "Primeros pasos",
        "document_type": "Primeros pasos",
        "introduction": "Esta guía resume las acciones esenciales para empezar a utilizar la funcionalidad.",
        "closing_note": "A partir de aquí puedes continuar con las funciones avanzadas.",
        "steps": [
            _step("Acceso", [_block("text"), _block("image")]),
            _step("Configuración inicial", [_block("text"), _block("checklist")]),
            _step(
                "Primera operación",
                [
                    _block("text"),
                    _block("image"),
                    _block(
                        "note",
                        label="Consejo",
                        variant="tip",
                    ),
                ],
            ),
        ],
    },
}


def template_choices() -> list[tuple[str, str]]:
    return [(key, value["name"]) for key, value in TEMPLATES.items()]


def create_from_template(template_id: str) -> dict:
    template = deepcopy(TEMPLATES.get(template_id, TEMPLATES["blank"]))

    # Refresh IDs on every instantiation.
    for step in template["steps"]:
        step["id"] = uuid4().hex
        for block in step["blocks"]:
            block["id"] = uuid4().hex

    return template
