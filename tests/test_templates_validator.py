from docu_generator.models import GuideBlock, GuideDraft, GuideSection
from docu_generator.services.templates import create_from_template, template_choices
from docu_generator.services.validator import has_blocking_errors, validate_guide


def test_templates_have_unique_ids_and_structure():
    choices = dict(template_choices())
    assert "tutorial" in choices
    assert "procedure" in choices
    assert "troubleshooting" in choices

    first = create_from_template("tutorial")
    second = create_from_template("tutorial")

    assert first["steps"]
    assert first["steps"][0]["id"] != second["steps"][0]["id"]
    assert first["steps"][0]["blocks"][0]["id"] != second["steps"][0]["blocks"][0]["id"]


def test_validator_detects_blocking_missing_image():
    guide = GuideDraft(
        title="Guía válida",
        sections=[
            GuideSection(
                title="Paso",
                blocks=[
                    GuideBlock(
                        type="image",
                        image_name="missing.png",
                        image_caption="Captura",
                    )
                ],
            )
        ],
    )

    issues = validate_guide(guide, [])

    assert has_blocking_errors(issues)
    assert any("no está disponible" in issue.message for issue in issues)


def test_validator_accepts_complete_simple_guide():
    guide = GuideDraft(
        title="Guía válida",
        sections=[
            GuideSection(
                title="Paso",
                blocks=[
                    GuideBlock(type="text", text="Haz esto."),
                    GuideBlock(
                        type="checklist",
                        items=["Dato correcto"],
                    ),
                ],
            )
        ],
    )

    issues = validate_guide(guide, [])

    assert not has_blocking_errors(issues)
