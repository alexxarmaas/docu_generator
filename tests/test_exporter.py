import io
import zipfile

from docu_generator.models import (
    GuideBlock,
    GuideDraft,
    GuideSection,
    ReviewReport,
)
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
                blocks=[
                    GuideBlock(type="text", text="Comprueba la pantalla."),
                    GuideBlock(
                        type="image",
                        image_name="screen.png",
                        image_caption="Pantalla de revisión",
                    ),
                    GuideBlock(
                        type="checklist",
                        items=["Cantidad correcta", "Precio correcto"],
                    ),
                    GuideBlock(
                        type="note",
                        text="No confirmes todavía.",
                    ),
                ],
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


def test_markdown_preserves_block_order():
    guide = GuideDraft(
        title="Guía",
        sections=[
            GuideSection(
                title="Revisar",
                blocks=[
                    GuideBlock(type="text", text="Primero revisa los datos."),
                    GuideBlock(
                        type="image",
                        image_name="screen.png",
                        image_caption="Vista de revisión",
                    ),
                    GuideBlock(type="note", text="No continúes todavía."),
                    GuideBlock(
                        type="checklist",
                        items=["Cantidad correcta", "Precio correcto"],
                    ),
                    GuideBlock(type="divider"),
                    GuideBlock(type="text", text="Después continúa."),
                ],
            )
        ],
    )

    text = render_markdown(guide, ReviewReport())

    positions = [
        text.index("Primero revisa los datos."),
        text.index("![Vista de revisión]"),
        text.index("> No continúes todavía."),
        text.index("- [ ] Cantidad correcta"),
        text.index("---"),
        text.index("Después continúa."),
    ]

    assert positions == sorted(positions)
    assert "*Vista de revisión*" in text


def test_html_can_be_downloaded_standalone():
    guide = GuideDraft(
        title="Guía",
        sections=[
            GuideSection(
                title="Paso",
                blocks=[
                    GuideBlock(type="text", text="Contenido"),
                    GuideBlock(type="note", text="Aviso"),
                ],
            )
        ],
    )
    html = render_html(
        guide,
        ReviewReport(),
        [],
        {"name": "Brisia", "product": "Brisia", "css": ""},
    )

    assert "<title>Guía</title>" in html
    assert "Contenido" in html
    assert "Aviso" in html


def test_legacy_sections_still_render():
    guide = GuideDraft(
        title="Legacy",
        sections=[
            GuideSection(
                title="Paso antiguo",
                body="Texto antiguo",
                checklist=["Uno"],
                note="Aviso antiguo",
            )
        ],
    )

    text = render_markdown(guide, ReviewReport())

    assert "Texto antiguo" in text
    assert "- [ ] Uno" in text
    assert "> Aviso antiguo" in text
