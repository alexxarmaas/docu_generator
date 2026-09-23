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
        instructions="Explica cómo revisar un documento.",
    )
    guide = pipeline.generate_guide(
        title="Cómo revisar un documento",
        instructions="Explica cómo revisar un documento.",
        audience="Usuario",
        evidences=evidences,
    )
    review = pipeline.review_guide(guide, evidences)

    assert len(evidences) == 2
    assert len(guide.sections) == 2
    assert guide.sections[0].image_name == "listado.png"
    assert guide.sections[1].image_name == "revision.png"
    assert review.issues == []
