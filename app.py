from __future__ import annotations

from uuid import uuid4

import streamlit as st
from dotenv import load_dotenv

from docu_generator.config import load_profile
from docu_generator.models import GuideBlock, GuideDraft, GuideSection, ReviewReport
from docu_generator.services.exporter import (
    build_export_zip,
    render_html,
    render_markdown,
)
from docu_generator.services.pdf_exporter import build_pdf
from docu_generator.services.project_io import dump_project, load_project

load_dotenv()

st.set_page_config(
    page_title="Docu Generator",
    page_icon="📘",
    layout="wide",
)

BLOCK_LIBRARY = {
    "text": {
        "label": "Texto",
        "icon": "📝",
        "type": "text",
    },
    "image": {
        "label": "Imagen",
        "icon": "🖼️",
        "type": "image",
    },
    "checklist": {
        "label": "Checklist",
        "icon": "☑️",
        "type": "checklist",
    },
    "tip": {
        "label": "Consejo",
        "icon": "💡",
        "type": "note",
        "variant": "tip",
        "callout_label": "Consejo",
    },
    "warning": {
        "label": "Importante",
        "icon": "⚠️",
        "type": "note",
        "variant": "warning",
        "callout_label": "Importante",
    },
    "success": {
        "label": "Resultado esperado",
        "icon": "✅",
        "type": "note",
        "variant": "success",
        "callout_label": "Resultado esperado",
    },
    "continue": {
        "label": "Antes de continuar",
        "icon": "➡️",
        "type": "note",
        "variant": "info",
        "callout_label": "Antes de continuar",
    },
    "divider": {
        "label": "Separador",
        "icon": "—",
        "type": "divider",
    },
}


def new_block(preset: str = "text") -> dict:
    config = BLOCK_LIBRARY.get(preset, BLOCK_LIBRARY["text"])

    return {
        "id": uuid4().hex,
        "type": config["type"],
        "text": "",
        "items": "",
        "image_name": None,
        "image_caption": "",
        "image_bytes": None,
        "image_mime": None,
        "label": config.get("callout_label", ""),
        "variant": config.get("variant", "info"),
    }


def clone_block(block: dict) -> dict:
    return {
        "id": uuid4().hex,
        "type": block.get("type", "text"),
        "text": block.get("text", ""),
        "items": block.get("items", ""),
        "image_name": block.get("image_name"),
        "image_caption": block.get("image_caption", ""),
        "image_bytes": block.get("image_bytes"),
        "image_mime": block.get("image_mime"),
        "label": block.get("label", ""),
        "variant": block.get("variant", "info"),
    }


def new_step() -> dict:
    return {
        "id": uuid4().hex,
        "title": "",
        "blocks": [new_block("text")],
    }


def ensure_state() -> None:
    if "steps" not in st.session_state:
        st.session_state.steps = [new_step()]
    if "guide_title" not in st.session_state:
        st.session_state.guide_title = ""
    if "guide_intro" not in st.session_state:
        st.session_state.guide_intro = ""
    if "guide_closing" not in st.session_state:
        st.session_state.guide_closing = ""


def reset_project() -> None:
    st.session_state.guide_title = ""
    st.session_state.guide_intro = ""
    st.session_state.guide_closing = ""
    st.session_state.steps = [new_step()]


def move_item(items: list, index: int, offset: int) -> None:
    target = index + offset
    if target < 0 or target >= len(items):
        return
    items[index], items[target] = items[target], items[index]


def duplicate_step(index: int) -> None:
    source = st.session_state.steps[index]
    clone = {
        "id": uuid4().hex,
        "title": source.get("title", ""),
        "blocks": [clone_block(block) for block in source.get("blocks", [])],
    }
    st.session_state.steps.insert(index + 1, clone)


def remove_step(index: int) -> None:
    if len(st.session_state.steps) == 1:
        st.session_state.steps[0] = new_step()
        return
    st.session_state.steps.pop(index)


def insert_block(step: dict, index: int, preset: str) -> None:
    step.setdefault("blocks", []).insert(index, new_block(preset))


def duplicate_block(step: dict, index: int) -> None:
    step["blocks"].insert(index + 1, clone_block(step["blocks"][index]))


def remove_block(step: dict, index: int) -> None:
    step["blocks"].pop(index)
    if not step["blocks"]:
        step["blocks"].append(new_block("text"))


def block_has_content(block: dict) -> bool:
    block_type = block.get("type", "text")

    if block_type in {"text", "note"}:
        return bool(block.get("text", "").strip())

    if block_type == "checklist":
        return any(line.strip() for line in block.get("items", "").splitlines())

    if block_type == "image":
        return bool(block.get("image_name") and block.get("image_bytes") is not None)

    if block_type == "divider":
        return True

    return False


def block_display(block: dict) -> tuple[str, str]:
    block_type = block.get("type", "text")

    if block_type == "text":
        text = block.get("text", "").strip()
        summary = text[:54] + ("..." if len(text) > 54 else "")
        return "📝", summary or "Texto"

    if block_type == "image":
        return "🖼️", block.get("image_caption") or block.get("image_name") or "Imagen"

    if block_type == "checklist":
        count = len(
            [line for line in block.get("items", "").splitlines() if line.strip()]
        )
        return "☑️", f"Checklist · {count} elemento(s)"

    if block_type == "note":
        variants = {
            "tip": "💡",
            "warning": "⚠️",
            "success": "✅",
            "info": "➡️",
        }
        return variants.get(block.get("variant"), "ℹ️"), block.get("label") or "Aviso"

    return "—", "Separador"


def render_insert_menu(step: dict, insert_index: int, key_prefix: str) -> None:
    with st.popover("＋ Insertar debajo"):
        st.caption("Bloques")
        columns = st.columns(2)

        for option_index, (preset, config) in enumerate(BLOCK_LIBRARY.items()):
            with columns[option_index % 2]:
                if st.button(
                    f"{config['icon']} {config['label']}",
                    key=f"{key_prefix}_{preset}",
                    use_container_width=True,
                ):
                    insert_block(step, insert_index, preset)
                    st.rerun()


def build_guide() -> tuple[GuideDraft, list[dict]]:
    sections: list[GuideSection] = []
    images_by_name: dict[str, dict] = {}

    for step in st.session_state.steps:
        guide_blocks: list[GuideBlock] = []

        for block in step.get("blocks", []):
            if not block_has_content(block):
                continue

            block_type = block.get("type", "text")

            if block_type == "text":
                guide_blocks.append(
                    GuideBlock(type="text", text=block.get("text", "").strip())
                )

            elif block_type == "note":
                guide_blocks.append(
                    GuideBlock(
                        type="note",
                        text=block.get("text", "").strip(),
                        label=block.get("label", "").strip(),
                        variant=block.get("variant", "info"),
                    )
                )

            elif block_type == "checklist":
                items = [
                    line.strip()
                    for line in block.get("items", "").splitlines()
                    if line.strip()
                ]
                guide_blocks.append(
                    GuideBlock(type="checklist", items=items)
                )

            elif block_type == "divider":
                guide_blocks.append(GuideBlock(type="divider"))

            elif block_type == "image":
                image_name = block.get("image_name")
                guide_blocks.append(
                    GuideBlock(
                        type="image",
                        image_name=image_name,
                        image_caption=block.get("image_caption", "").strip(),
                    )
                )

                if image_name and block.get("image_bytes") is not None:
                    images_by_name[image_name] = {
                        "name": image_name,
                        "mime_type": block.get("image_mime") or "image/png",
                        "bytes": block["image_bytes"],
                    }

        title = step.get("title", "").strip()

        if not guide_blocks and not title:
            continue

        sections.append(
            GuideSection(
                title=title or "Paso sin título",
                blocks=guide_blocks,
            )
        )

    guide = GuideDraft(
        title=st.session_state.guide_title.strip() or "Guía sin título",
        introduction=st.session_state.guide_intro.strip(),
        sections=sections,
        closing_note=st.session_state.guide_closing.strip(),
    )

    return guide, list(images_by_name.values())


def render_preview_block(
    block: GuideBlock,
    image_lookup: dict[str, dict],
    key_prefix: str,
) -> None:
    if block.type == "text":
        st.markdown(block.text)

    elif block.type == "note":
        message = block.text
        if block.label:
            message = f"**{block.label}**\n\n{message}"

        if block.variant == "warning":
            st.warning(message)
        elif block.variant in {"tip", "success"}:
            st.success(message)
        else:
            st.info(message)

    elif block.type == "checklist":
        for item_index, item in enumerate(block.items):
            st.checkbox(
                item,
                value=False,
                disabled=True,
                key=f"{key_prefix}_check_{item_index}",
            )

    elif block.type == "divider":
        st.divider()

    elif block.type == "image" and block.image_name in image_lookup:
        st.image(
            image_lookup[block.image_name]["bytes"],
            caption=block.image_caption or None,
            use_container_width=True,
        )


def render_block_editor(step: dict, block: dict, block_index: int) -> None:
    icon, display = block_display(block)
    expanded = not block_has_content(block)

    with st.expander(
        f"{icon} {block_index + 1}. {display}",
        expanded=expanded,
    ):
        actions = st.columns([1, 1, 1, 1, 4])

        if actions[0].button(
            "↑",
            key=f"block_up_{block['id']}",
            disabled=block_index == 0,
            help="Mover bloque arriba",
        ):
            move_item(step["blocks"], block_index, -1)
            st.rerun()

        if actions[1].button(
            "↓",
            key=f"block_down_{block['id']}",
            disabled=block_index == len(step["blocks"]) - 1,
            help="Mover bloque abajo",
        ):
            move_item(step["blocks"], block_index, 1)
            st.rerun()

        if actions[2].button(
            "⧉",
            key=f"block_duplicate_{block['id']}",
            help="Duplicar bloque",
        ):
            duplicate_block(step, block_index)
            st.rerun()

        if actions[3].button(
            "✕",
            key=f"block_delete_{block['id']}",
            help="Eliminar bloque",
        ):
            remove_block(step, block_index)
            st.rerun()

        block_type = block.get("type", "text")

        if block_type == "text":
            block["text"] = st.text_area(
                "Texto",
                value=block.get("text", ""),
                key=f"block_text_{block['id']}",
                height=130,
                placeholder="Escribe la explicación. Puedes utilizar Markdown.",
            )

        elif block_type == "note":
            meta_a, meta_b = st.columns([1.2, 1])

            block["label"] = meta_a.text_input(
                "Etiqueta",
                value=block.get("label", ""),
                key=f"block_label_{block['id']}",
                placeholder="Ej. Importante",
            )

            variant_options = ["info", "tip", "warning", "success"]
            variant_labels = {
                "info": "Información",
                "tip": "Consejo",
                "warning": "Advertencia",
                "success": "Correcto / resultado",
            }
            current_variant = block.get("variant", "info")
            if current_variant not in variant_options:
                current_variant = "info"

            block["variant"] = meta_b.selectbox(
                "Estilo",
                variant_options,
                index=variant_options.index(current_variant),
                format_func=lambda value: variant_labels[value],
                key=f"block_variant_{block['id']}",
            )

            block["text"] = st.text_area(
                "Contenido",
                value=block.get("text", ""),
                key=f"block_note_{block['id']}",
                height=100,
                placeholder="Escribe el contenido del aviso.",
            )

        elif block_type == "checklist":
            block["items"] = st.text_area(
                "Elementos",
                value=block.get("items", ""),
                key=f"block_checklist_{block['id']}",
                height=120,
                placeholder=(
                    "Un elemento por línea\n"
                    "Proveedor correcto\n"
                    "Fecha correcta\n"
                    "Importes correctos"
                ),
            )

        elif block_type == "divider":
            st.caption("Este bloque inserta una línea separadora.")

        elif block_type == "image":
            upload = st.file_uploader(
                "Imagen",
                type=["png", "jpg", "jpeg", "webp"],
                key=f"block_image_{block['id']}",
            )

            if upload is not None:
                stored_name = f"{block['id'][:8]}_{upload.name}"
                block["image_name"] = stored_name
                block["image_bytes"] = upload.getvalue()
                block["image_mime"] = upload.type or "image/png"

            if block.get("image_bytes") is not None:
                st.image(
                    block["image_bytes"],
                    caption=block.get("image_caption") or "Vista previa",
                    use_container_width=True,
                )

                block["image_caption"] = st.text_input(
                    "Pie de imagen",
                    value=block.get("image_caption", ""),
                    key=f"block_caption_{block['id']}",
                    placeholder="Ej. Listado principal de albaranes",
                )

                if st.button(
                    "Quitar imagen",
                    key=f"block_remove_image_{block['id']}",
                ):
                    block["image_name"] = None
                    block["image_caption"] = ""
                    block["image_bytes"] = None
                    block["image_mime"] = None
                    st.rerun()

    render_insert_menu(
        step,
        block_index + 1,
        key_prefix=f"insert_after_{block['id']}",
    )


ensure_state()
profile = load_profile("brisia")

st.title("Docu Generator")
st.caption("Editor local por bloques para crear guías de usuario sin depender de ninguna API.")

with st.sidebar:
    st.header("Proyecto")

    project_upload = st.file_uploader(
        "Abrir proyecto",
        type=["json"],
        help="Compatible con proyectos Docu Generator v1 y v2.",
    )

    load_col, new_col = st.columns(2)

    if load_col.button(
        "Abrir",
        use_container_width=True,
        disabled=project_upload is None,
    ):
        try:
            project = load_project(project_upload.getvalue())
            st.session_state.guide_title = project["title"]
            st.session_state.guide_intro = project["introduction"]
            st.session_state.guide_closing = project["closing_note"]
            st.session_state.steps = project["steps"] or [new_step()]
            st.rerun()
        except Exception as exc:
            st.error(f"No se pudo abrir el proyecto: {exc}")

    if new_col.button("Nuevo", use_container_width=True):
        reset_project()
        st.rerun()

    st.divider()
    st.header("Guía")

    st.text_input(
        "Título",
        key="guide_title",
        placeholder="Cómo revisar un albarán",
    )

    st.text_area(
        "Introducción",
        key="guide_intro",
        height=110,
        placeholder="Explica brevemente qué aprenderá el usuario.",
    )

    st.text_area(
        "Cierre",
        key="guide_closing",
        height=90,
        placeholder="Ej. Comprueba los datos antes de confirmar el documento.",
    )

    st.divider()
    st.caption(f"{len(st.session_state.steps)} paso(s)")

    if st.button("＋ Añadir paso", use_container_width=True, type="primary"):
        st.session_state.steps.append(new_step())
        st.rerun()

editor_col, preview_col = st.columns([1.08, 0.92], gap="large")

with editor_col:
    st.subheader("Editor")

    for step_index, step in enumerate(st.session_state.steps):
        with st.container(border=True):
            title_col, actions_col = st.columns([3.5, 2.5])

            with title_col:
                st.markdown(f"## Paso {step_index + 1}")

            with actions_col:
                up, down, duplicate, delete = st.columns(4)

                if up.button(
                    "↑",
                    key=f"step_up_{step['id']}",
                    disabled=step_index == 0,
                    help="Mover paso arriba",
                ):
                    move_item(st.session_state.steps, step_index, -1)
                    st.rerun()

                if down.button(
                    "↓",
                    key=f"step_down_{step['id']}",
                    disabled=step_index == len(st.session_state.steps) - 1,
                    help="Mover paso abajo",
                ):
                    move_item(st.session_state.steps, step_index, 1)
                    st.rerun()

                if duplicate.button(
                    "⧉",
                    key=f"step_duplicate_{step['id']}",
                    help="Duplicar paso",
                ):
                    duplicate_step(step_index)
                    st.rerun()

                if delete.button(
                    "✕",
                    key=f"step_delete_{step['id']}",
                    help="Eliminar paso",
                ):
                    remove_step(step_index)
                    st.rerun()

            step["title"] = st.text_input(
                "Título del paso",
                value=step.get("title", ""),
                key=f"step_title_{step['id']}",
                placeholder="Ej. Revisa las líneas del albarán",
            )

            for block_index, block in enumerate(step.get("blocks", [])):
                render_block_editor(step, block, block_index)

            with st.popover("＋ Añadir bloque al final", use_container_width=True):
                st.caption("Biblioteca de bloques")
                columns = st.columns(2)

                for option_index, (preset, config) in enumerate(BLOCK_LIBRARY.items()):
                    with columns[option_index % 2]:
                        if st.button(
                            f"{config['icon']} {config['label']}",
                            key=f"add_end_{step['id']}_{preset}",
                            use_container_width=True,
                        ):
                            insert_block(step, len(step["blocks"]), preset)
                            st.rerun()

    if st.button("＋ Añadir otro paso", use_container_width=True):
        st.session_state.steps.append(new_step())
        st.rerun()

guide, images = build_guide()
review = ReviewReport()

with preview_col:
    st.subheader("Vista previa")

    with st.container(border=True):
        st.caption("BRISIA · GUÍA DE USUARIO")
        st.markdown(f"# {guide.title}")

        if guide.introduction:
            st.markdown(guide.introduction)

        if not guide.sections:
            st.info("Añade contenido para empezar a construir la guía.")

        image_lookup = {image["name"]: image for image in images}

        for section_index, section in enumerate(guide.sections, start=1):
            st.markdown(f"### {section_index}. {section.title}")

            for block_index, block in enumerate(section.blocks):
                render_preview_block(
                    block,
                    image_lookup,
                    key_prefix=f"preview_{section_index}_{block_index}",
                )

            if section_index < len(guide.sections):
                st.markdown("---")

        if guide.closing_note:
            st.info(guide.closing_note)

    st.markdown("#### Guardar y exportar")

    safe_name = "".join(
        c if c.isalnum() or c in "-_" else "-"
        for c in guide.title.lower()
    ).strip("-") or "guia"

    project_bytes = dump_project(
        title=st.session_state.guide_title,
        introduction=st.session_state.guide_intro,
        closing_note=st.session_state.guide_closing,
        steps=st.session_state.steps,
    )

    export_a, export_b = st.columns(2)

    export_a.download_button(
        "Guardar proyecto",
        data=project_bytes,
        file_name=f"{safe_name}.docugen.json",
        mime="application/json",
        use_container_width=True,
    )

    if guide.sections:
        html_text = render_html(guide, review, images, profile)
        markdown_text = render_markdown(guide, review)
        pdf_bytes = build_pdf(guide, images, profile)
        zip_bytes = build_export_zip(
            guide=guide,
            review=review,
            images=images,
            profile=profile,
        )

        export_b.download_button(
            "PDF",
            data=pdf_bytes,
            file_name=f"{safe_name}.pdf",
            mime="application/pdf",
            type="primary",
            use_container_width=True,
        )

        export_c, export_d = st.columns(2)

        export_c.download_button(
            "HTML",
            data=html_text.encode("utf-8"),
            file_name=f"{safe_name}.html",
            mime="text/html",
            use_container_width=True,
        )

        export_d.download_button(
            "Markdown",
            data=markdown_text.encode("utf-8"),
            file_name=f"{safe_name}.md",
            mime="text/markdown",
            use_container_width=True,
        )

        st.download_button(
            "ZIP completo",
            data=zip_bytes,
            file_name=f"{safe_name}.zip",
            mime="application/zip",
            use_container_width=True,
        )
