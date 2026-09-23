import base64
import json

from docu_generator.services.project_io import dump_project, load_project


def test_v3_roundtrip_preserves_metadata_layout_and_image():
    steps = [
        {
            "id": "step-id",
            "title": "Revisa el albarán",
            "blocks": [
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
                    "image_width": "medium",
                    "align": "right",
                },
                {
                    "id": "table-id",
                    "type": "table",
                    "text": "",
                    "items": "Campo | Valor\nEstado | Correcto",
                    "image_name": None,
                    "image_caption": "",
                    "image_bytes": None,
                    "image_mime": None,
                    "label": "",
                    "variant": "info",
                    "image_width": "large",
                    "align": "center",
                },
            ],
        }
    ]

    payload = dump_project(
        title="Cómo revisar un albarán",
        introduction="Introducción",
        closing_note="Cierre",
        steps=steps,
        metadata={
            "document_type": "Procedimiento",
            "version_label": "2.1",
            "status": "Publicado",
            "author": "Alejandro",
            "show_cover": False,
            "show_toc": True,
        },
    )

    raw = json.loads(payload.decode("utf-8"))
    assert raw["version"] == 3

    restored = load_project(payload)
    step = restored["steps"][0]

    assert restored["metadata"]["document_type"] == "Procedimiento"
    assert restored["metadata"]["version_label"] == "2.1"
    assert restored["metadata"]["status"] == "Publicado"
    assert step["blocks"][0]["image_bytes"] == b"image-bytes"
    assert step["blocks"][0]["image_width"] == "medium"
    assert step["blocks"][0]["align"] == "right"
    assert step["blocks"][1]["type"] == "table"


def test_v2_project_is_migrated_with_layout_defaults():
    payload = {
        "version": 2,
        "title": "Proyecto v2",
        "steps": [
            {
                "title": "Paso",
                "blocks": [
                    {
                        "type": "note",
                        "text": "Consejo",
                        "label": "Consejo",
                        "variant": "tip",
                    }
                ],
            }
        ],
    }

    restored = load_project(
        json.dumps(payload, ensure_ascii=False).encode("utf-8")
    )

    block = restored["steps"][0]["blocks"][0]
    assert block["variant"] == "tip"
    assert block["image_width"] == "large"
    assert block["align"] == "center"
    assert restored["metadata"]["status"] == "Borrador"


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
    assert blocks[1]["image_bytes"] == b"old-image"
    assert blocks[3]["label"] == "Importante"
    assert blocks[3]["variant"] == "warning"
