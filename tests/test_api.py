from fastapi.testclient import TestClient

from docu_generator.api import app


client = TestClient(app)


def _project():
    return {
        "version": 4,
        "title": "Guía API",
        "introduction": "Introducción",
        "closing_note": "",
        "metadata": {
            "document_type": "Guía",
            "version_label": "1.0",
            "status": "Borrador",
            "author": "",
            "updated_at": "",
            "show_cover": False,
            "show_toc": False,
        },
        "steps": [
            {
                "id": "step1",
                "title": "Primer paso",
                "blocks": [
                    {
                        "id": "block1",
                        "type": "text",
                        "text": "Haz esto.",
                        "items": "",
                        "image_name": None,
                        "image_caption": "",
                        "image_mime": None,
                        "image_base64": None,
                        "label": "",
                        "variant": "info",
                        "image_width": "large",
                        "align": "center",
                        "annotations": [],
                        "crop": None,
                    }
                ],
            }
        ],
    }


def test_health_endpoint():
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["ok"] is True


def test_validate_endpoint_accepts_portable_project():
    response = client.post("/api/validate", json=_project())

    assert response.status_code == 200
    assert response.json()["issues"] == []


def test_pdf_export_endpoint_uses_existing_publish_engine():
    response = client.post("/api/export/pdf", json=_project())

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert response.content.startswith(b"%PDF")
