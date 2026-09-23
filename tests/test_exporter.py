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
from docu_generator.services.pdf_exporter import build_pdf


PROFILE = {
    "name": "Brisia",
    "product": "Brisia",
    "brand": {
        "primary": "#092D54",
        "accent": "#00B8A9",
    },
    "css": "body{}",
}


def sample_guide():
    return GuideDraft(
        title="Guía de prueba",
        introduction="Introducción de la guía.",
        sections=[
            GuideSection(
                title="Primer paso",
                blocks=[
                    GuideBlock(type="text", text="Comprueba la pantalla."),
                    GuideBlock(
                        type="note",
                        label="Importante",
                        variant="warning",
                        text="No confirmes todavía.",
                    ),
                    GuideBlock(
                        type="checklist",
                        items=["Cantidad correcta", "Precio correcto"],
                    ),
                ],
            )
        ],
        closing_note="Proceso completado.",
    )


def test_export_zip_contains_expected_files():
    guide = sample_guide()

    payload = build_export_zip(
        guide,
        ReviewReport(),
        [],
        PROFILE,
    )

    with zipfile.ZipFile(io.BytesIO(payload)) as archive:
        names = set(archive.namelist())

    assert "guide.md" in names
    assert "guide.html" in names
    assert "guide.pdf" in names
    assert "review.txt" in names


def test_markdown_preserves_block_order_and_callout_label():
    guide = GuideDraft(
        title="Guía",
        sections=[
            GuideSection(
                title="Revisar",
                blocks=[
                    GuideBlock(type="text", text="Primero revisa los datos."),
                    GuideBlock(
                        type="note",
                        label="Consejo",
                        variant="tip",
                        text="Hazlo con calma.",
                    ),
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
        text.index("> **Consejo:**"),
        text.index("> Hazlo con calma."),
        text.index("- [ ] Cantidad correcta"),
        text.index("---"),
        text.index("Después continúa."),
    ]

    assert positions == sorted(positions)


def test_html_contains_callout_variant():
    html = render_html(
        sample_guide(),
        ReviewReport(),
        [],
        PROFILE,
    )

    assert "<title>Guía de prueba</title>" in html
    assert "callout-warning" in html
    assert "Importante" in html


def test_pdf_is_generated_locally():
    pdf = build_pdf(
        sample_guide(),
        [],
        PROFILE,
    )

    assert pdf.startswith(b"%PDF")
    assert len(pdf) > 1000


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
    assert "Aviso antiguo" in text
