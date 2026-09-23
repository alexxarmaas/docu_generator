from __future__ import annotations

from dataclasses import dataclass

from docu_generator.models import GuideDraft


@dataclass
class ValidationIssue:
    level: str
    message: str


def validate_guide(guide: GuideDraft, images: list[dict]) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    image_names = {image["name"] for image in images}

    if not guide.title.strip() or guide.title == "Guía sin título":
        issues.append(ValidationIssue("error", "La guía no tiene un título definitivo."))

    if not guide.sections:
        issues.append(ValidationIssue("error", "La guía no contiene pasos."))

    for section_index, section in enumerate(guide.sections, start=1):
        if not section.title.strip() or section.title == "Paso sin título":
            issues.append(
                ValidationIssue(
                    "warning",
                    f"El paso {section_index} no tiene un título definitivo.",
                )
            )

        if not section.blocks:
            issues.append(
                ValidationIssue(
                    "warning",
                    f"El paso {section_index} no contiene bloques.",
                )
            )

        for block_index, block in enumerate(section.blocks, start=1):
            prefix = f"Paso {section_index}, bloque {block_index}"

            if block.type == "image":
                if not block.image_name:
                    issues.append(
                        ValidationIssue("warning", f"{prefix}: imagen vacía.")
                    )
                elif block.image_name not in image_names:
                    issues.append(
                        ValidationIssue(
                            "error",
                            f"{prefix}: la imagen referenciada no está disponible.",
                        )
                    )
                if block.image_name and not block.image_caption.strip():
                    issues.append(
                        ValidationIssue(
                            "info",
                            f"{prefix}: la imagen no tiene pie de foto.",
                        )
                    )

            elif block.type == "checklist" and not block.items:
                issues.append(
                    ValidationIssue("warning", f"{prefix}: checklist vacío.")
                )

            elif block.type == "note" and not block.text.strip():
                issues.append(
                    ValidationIssue("warning", f"{prefix}: callout vacío.")
                )

            elif block.type == "text" and not block.text.strip():
                issues.append(
                    ValidationIssue("info", f"{prefix}: bloque de texto vacío.")
                )

            elif block.type == "table":
                rows = [row for row in block.items if row.strip()]
                if len(rows) < 2:
                    issues.append(
                        ValidationIssue(
                            "warning",
                            f"{prefix}: la tabla debería tener cabecera y al menos una fila.",
                        )
                    )

    return issues


def has_blocking_errors(issues: list[ValidationIssue]) -> bool:
    return any(issue.level == "error" for issue in issues)
