import base64
import json

from docu_generator.services.project_io import dump_project, load_project


def test_v2_project_roundtrip_preserves_free_blocks_image_and_callout():
    steps = [
        {
            "id": "step-id",
            "title": "Revisa el albarán",
            "blocks": [
                {
                    "id": "text-id",
                    "type": "text",
                    "text": "Comprueba los datos principales.",
                    "items": "",
                    "image_name": None,
                    "image_caption": "",
                    "image_bytes": None,
                    "image_mime": None,
                    "label": "",
                    "variant": "info",
                },
                {
                    "id": "image-id",
                    "type": "image",
                    "text": "",
                    "items": "",
                    "image_name": "imagen.png",
                    "image_caption": "Pantalla de revisión",
                    "image_bytes": b"image-bytes",
                    "image_mime": "image/png",
                    "label": "",
                    "variant": "info",
                },
                {
                    "id": "note-id",
                    "type": "note",
                    "text": "Comprueba esto antes de seguir.",
                    "items": "",
                    "image_name": None,
                    "image_caption": "",
                    "image_bytes": None,
                    "image_mime": None,
                    "label": "Antes de continuar",
                    "variant": "info",
                },
            ],
        }
    ]

    payload = dump_project(
        title="Cómo revisar un albarán",
        introduction="Introducción",
        closing_note="Cierre",
        steps=steps,
    )

    raw = json.loads(payload.decode("utf-8"))
    assert raw["version"] == 2

    restored = load_project(payload)
    step = restored["steps"][0]

    assert [block["type"] for block in step["blocks"]] == [
        "text",
        "image",
        "note",
    ]
    assert step["blocks"][1]["image_bytes"] == b"image-bytes"
    assert step["blocks"][2]["label"] == "Antes de continuar"
    assert step["blocks"][2]["variant"] == "info"


def test_v1_project_is_migrated_to_free_blocks():
    payload = {
        "version": 1,
        "title": "Proyecto antiguo",
        "introduction": "",
        "closing_note": "",
        "steps": [
            {
                "title": "Paso antiguo",
                "body": "Texto",
                "checklist": "Uno\nDos",
                "note": "Aviso",
                "image_name": "old.png",
                "image_caption": "Imagen antigua",
                "image_mime": "image/png",
                "image_base64": base64.b64encode(b"old-image").decode("ascii"),
            }
        ],
    }

    restored = load_project(
        json.dumps(payload, ensure_ascii=False).encode("utf-8")
    )

    blocks = restored["steps"][0]["blocks"]

    assert [block["type"] for block in blocks] == [
        "text",
        "image",
        "checklist",
        "note",
    ]
    assert blocks[0]["text"] == "Texto"
    assert blocks[1]["image_bytes"] == b"old-image"
    assert blocks[2]["items"] == "Uno\nDos"
    assert blocks[3]["text"] == "Aviso"
    assert blocks[3]["label"] == "Importante"
    assert blocks[3]["variant"] == "warning"
