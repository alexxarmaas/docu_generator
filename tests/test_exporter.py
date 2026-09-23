import io
import zipfile

from docu_generator.models import GuideDraft, GuideSection, ReviewReport
from docu_generator.services.exporter import (
    build_export_zip,
    render_html,
    render_markdown,
)


def test_export_zip_contains_expected_files():
    guide = GuideDraft(
        title="Guía de prueba",
        introduction="Introducción",
        sections=[
            GuideSection(
                title="Primer paso",
                body="Comprueba la pantalla.",
                image_name="screen.png",
                image_caption="Pantalla de revisión",
                checklist=["Cantidad correcta", "Precio correcto"],
                note="No confirmes todavía.",
            )
        ],
    )
    review = ReviewReport()
    images = [
        {
            "name": "screen.png",
            "mime_type": "image/png",
            "bytes": b"fake-image",
        }
    ]
    profile = {
        "name": "Brisia",
        "product": "Brisia",
        "css": "body{}",
    }

    payload = build_export_zip(guide, review, images, profile)

    with zipfile.ZipFile(io.BytesIO(payload)) as archive:
        names = set(archive.namelist())

    assert "guide.md" in names
    assert "guide.html" in names
    assert "review.txt" in names
    assert "images/screen.png" in names


def test_markdown_contains_checklist_note_and_caption():
    guide = GuideDraft(
        title="Guía",
        sections=[
            GuideSection(
                title="Revisar",
                body="Comprueba los datos.",
                image_name="screen.png",
                image_caption="Vista de revisión",
                checklist=["Cantidad correcta", "Precio correcto"],
                note="Revisa antes de continuar.",
            )
        ],
    )

    text = render_markdown(guide, ReviewReport())

    assert "- [ ] Cantidad correcta" in text
    assert "- [ ] Precio correcto" in text
    assert "> Revisa antes de continuar." in text
    assert "*Vista de revisión*" in text


def test_html_can_be_downloaded_standalone():
    guide = GuideDraft(
        title="Guía",
        sections=[GuideSection(title="Paso", body="Contenido")],
    )
    html = render_html(
        guide,
        ReviewReport(),
        [],
        {"name": "Brisia", "product": "Brisia", "css": ""},
    )

    assert "<title>Guía</title>" in html
    assert "Contenido" in html
