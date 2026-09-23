import io
import zipfile

from docu_generator.models import GuideDraft, GuideSection, ReviewReport
from docu_generator.services.exporter import build_export_zip


def test_export_zip_contains_expected_files():
    guide = GuideDraft(
        title="Guía de prueba",
        introduction="Introducción",
        sections=[
            GuideSection(
                title="Primer paso",
                body="Comprueba la pantalla.",
                image_name="screen.png",
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
