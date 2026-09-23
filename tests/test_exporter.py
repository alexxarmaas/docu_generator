import io
import zipfile

from docu_generator.models import (
    GuideBlock,
    GuideDraft,
    GuideSection,
    ReviewReport,
)
from docu_generator.services.docx_exporter import build_docx
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
        document_type="Procedimiento",
        version="1.2",
        status="En revisión",
        author="Alejandro",
        show_cover=True,
        show_toc=True,
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
                    GuideBlock(
                        type="table",
                        items=[
                            "Campo | Valor",
                            "Proveedor | ACME",
                            "Estado | Correcto",
                        ],
                    ),
                    GuideBlock(type="pagebreak"),
                ],
            )
        ],
        closing_note="Proceso completado.",
    )


def test_export_zip_contains_all_publish_formats():
    payload = build_export_zip(
        sample_guide(),
        ReviewReport(),
        [],
        PROFILE,
    )

    with zipfile.ZipFile(io.BytesIO(payload)) as archive:
        names = set(archive.namelist())

    assert "guide.md" in names
    assert "guide.html" in names
    assert "guide.pdf" in names
    assert "guide.docx" in names
    assert "review.txt" in names


def test_markdown_contains_metadata_table_and_pagebreak():
    text = render_markdown(sample_guide(), ReviewReport())

    assert "**Tipo:** Procedimiento" in text
    assert "**Versión:** 1.2" in text
    assert "| Campo | Valor |" in text
    assert "| --- | --- |" in text
    assert "<!-- pagebreak -->" in text


def test_html_contains_publishing_components():
    html = render_html(
        sample_guide(),
        ReviewReport(),
        [],
        PROFILE,
    )

    assert "<title>Guía de prueba</title>" in html
    assert "callout-warning" in html
    assert 'class="cover"' in html
    assert 'class="toc"' in html
    assert 'class="content-block table-block"' in html
    assert 'class="page-break"' in html


def test_pdf_is_generated_locally():
    pdf = build_pdf(
        sample_guide(),
        [],
        PROFILE,
    )

    assert pdf.startswith(b"%PDF")
    assert len(pdf) > 1500


def test_docx_is_generated_and_has_document_xml():
    docx = build_docx(
        sample_guide(),
        [],
        PROFILE,
    )

    assert docx.startswith(b"PK")

    with zipfile.ZipFile(io.BytesIO(docx)) as archive:
        names = set(archive.namelist())
        document_xml = archive.read("word/document.xml")

    assert "word/document.xml" in names
    assert "Guía de prueba".encode("utf-8") in document_xml
    assert "ACME".encode("utf-8") in document_xml


def test_legacy_sections_still_render():
    guide = GuideDraft(
        title="Legacy",
        show_cover=False,
        show_toc=False,
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
