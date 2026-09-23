from docu_generator.services.project_io import dump_project, load_project


def test_project_roundtrip_preserves_text_and_image():
    steps = [
        {
            "id": "ignored",
            "title": "Selecciona el albarán",
            "body": "Abre el documento que quieras revisar.",
            "checklist": "Proveedor correcto\nFecha correcta",
            "note": "No continúes si el documento no corresponde.",
            "image_name": "listado.png",
            "image_caption": "Listado de albaranes",
            "image_bytes": b"image-bytes",
            "image_mime": "image/png",
        }
    ]

    payload = dump_project(
        title="Cómo revisar un albarán",
        introduction="Introducción",
        closing_note="Cierre",
        steps=steps,
    )

    restored = load_project(payload)

    assert restored["title"] == "Cómo revisar un albarán"
    assert restored["introduction"] == "Introducción"
    assert restored["closing_note"] == "Cierre"
    assert len(restored["steps"]) == 1

    step = restored["steps"][0]
    assert step["title"] == "Selecciona el albarán"
    assert step["image_name"] == "listado.png"
    assert step["image_caption"] == "Listado de albaranes"
    assert step["image_bytes"] == b"image-bytes"
    assert step["image_mime"] == "image/png"
