from docu_generator.config import load_profile
from docu_generator.pipeline import DocumentationPipeline
from docu_generator.providers.fallback import FallbackProvider


def test_fallback_pipeline_builds_a_reviewable_guide():
    profile = load_profile("brisia")
    pipeline = DocumentationPipeline(
        provider=FallbackProvider(),
        profile=profile,
    )
    images = [
        {
            "name": "listado.png",
            "mime_type": "image/png",
            "bytes": b"fake-image",
        },
        {
            "name": "revision.png",
            "mime_type": "image/png",
            "bytes": b"fake-image",
        },
    ]

    evidences = pipeline.analyze_images(
        images,
        instructions="Entras, eliges el albarán que quieres y lo revisas paso a paso.",
    )
    guide = pipeline.generate_guide(
        title="Cómo revisar un albarán",
        instructions="Entras, eliges el albarán que quieres y lo revisas paso a paso.",
        audience="Usuario",
        evidences=evidences,
    )
    review = pipeline.review_guide(guide, evidences)

    assert len(evidences) == 2
    assert len(guide.sections) >= 3
    assert guide.sections[0].title == "Accede a Brisia"
    assert guide.sections[1].title == "Selecciona el albarán"
    assert "**Qué hacer**" in guide.sections[0].body
    assert "Borrador generado" not in guide.introduction
    assert guide.closing_note
    assert review.issues == []
