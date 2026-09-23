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
from docu_generator.services.project_io import dump_project, load_project

load_dotenv()

st.set_page_config(
    page_title="Docu Generator",
    page_icon="📘",
    layout="wide",
)

BLOCK_LABELS = {
    "text": "Texto",
    "image": "Imagen",
    "checklist": "Checklist",
    "note": "Aviso",
    "divider": "Separador",
}


def new_block(block_type: str = "text") -> dict:
    return {
        "id": uuid4().hex,
        "type": block_type,
        "text": "",
        "items": "",
        "image_name": None,
        "image_caption": "",
        "image_bytes": None,
        "image_mime": None,
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


def add_block(step: dict, block_type: str) -> None:
    step.setdefault("blocks", []).append(new_block(block_type))


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
                    GuideBlock(type="note", text=block.get("text", "").strip())
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


def render_preview_block(block: GuideBlock, image_lookup: dict[str, dict], key_prefix: str) -> None:
    if block.type == "text":
        st.markdown(block.text)

    elif block.type == "note":
        st.info(block.text)

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
    block_type = block.get("type", "text")
    label = BLOCK_LABELS.get(block_type, block_type)

    with st.container(border=True):
        header, actions = st.columns([3.4, 2.6])

        with header:
            st.caption(f"{block_index + 1}. {label}")

        with actions:
            up, down, duplicate, delete = st.columns(4)

            if up.button(
                "↑",
                key=f"block_up_{block['id']}",
                disabled=block_index == 0,
                help="Mover bloque arriba",
            ):
                move_item(step["blocks"], block_index, -1)
                st.rerun()

            if down.button(
                "↓",
                key=f"block_down_{block['id']}",
                disabled=block_index == len(step["blocks"]) - 1,
                help="Mover bloque abajo",
            ):
                move_item(step["blocks"], block_index, 1)
                st.rerun()

            if duplicate.button(
                "⧉",
                key=f"block_duplicate_{block['id']}",
                help="Duplicar bloque",
            ):
                duplicate_block(step, block_index)
                st.rerun()

            if delete.button(
                "✕",
                key=f"block_delete_{block['id']}",
                help="Eliminar bloque",
            ):
                remove_block(step, block_index)
                st.rerun()

        if block_type == "text":
            block["text"] = st.text_area(
                "Texto",
                value=block.get("text", ""),
                key=f"block_text_{block['id']}",
                height=120,
                placeholder="Escribe la explicación. Puedes utilizar Markdown.",
                label_visibility="collapsed",
            )

        elif block_type == "note":
            block["text"] = st.text_area(
                "Aviso",
                value=block.get("text", ""),
                key=f"block_note_{block['id']}",
                height=90,
                placeholder="Ej. No confirmes hasta comprobar todos los datos.",
                label_visibility="collapsed",
            )

        elif block_type == "checklist":
            block["items"] = st.text_area(
                "Checklist",
                value=block.get("items", ""),
                key=f"block_checklist_{block['id']}",
                height=110,
                placeholder=(
                    "Un elemento por línea\n"
                    "Proveedor correcto\n"
                    "Fecha correcta\n"
                    "Importes correctos"
                ),
                label_visibility="collapsed",
            )

        elif block_type == "divider":
            st.caption("Este bloque insertará una línea separadora.")

        elif block_type == "image":
            upload = st.file_uploader(
                "Imagen",
                type=["png", "jpg", "jpeg", "webp"],
                key=f"block_image_{block['id']}",
                label_visibility="collapsed",
            )

            if upload is not None:
                stored_name = f"{block['id'][:8]}_{upload.name}"
                block["image_name"] = stored_name
                block["image_bytes"] = upload.getvalue()
                block["image_mime"] = upload.type or "image/png"

            if block.get("image_bytes") is not None:
                st.image(
                    block["image_bytes"],
                    caption=block.get("image_caption") or "Vista previa de imagen",
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

            st.caption("Contenido")

            for block_index, block in enumerate(step.get("blocks", [])):
                render_block_editor(step, block, block_index)

            st.caption("Añadir bloque")
            add_text, add_image, add_check, add_note, add_divider = st.columns(5)

            if add_text.button("＋ Texto", key=f"add_text_{step['id']}", use_container_width=True):
                add_block(step, "text")
                st.rerun()

            if add_image.button("＋ Imagen", key=f"add_image_{step['id']}", use_container_width=True):
                add_block(step, "image")
                st.rerun()

            if add_check.button("＋ Lista", key=f"add_check_{step['id']}", use_container_width=True):
                add_block(step, "checklist")
                st.rerun()

            if add_note.button("＋ Aviso", key=f"add_note_{step['id']}", use_container_width=True):
                add_block(step, "note")
                st.rerun()

            if add_divider.button("＋ Línea", key=f"add_divider_{step['id']}", use_container_width=True):
                add_block(step, "divider")
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
        zip_bytes = build_export_zip(
            guide=guide,
            review=review,
            images=images,
            profile=profile,
        )

        export_b.download_button(
            "HTML",
            data=html_text.encode("utf-8"),
            file_name=f"{safe_name}.html",
            mime="text/html",
            use_container_width=True,
        )

        export_c, export_d = st.columns(2)

        export_c.download_button(
            "Markdown",
            data=markdown_text.encode("utf-8"),
            file_name=f"{safe_name}.md",
            mime="text/markdown",
            use_container_width=True,
        )

        export_d.download_button(
            "ZIP completo",
            data=zip_bytes,
            file_name=f"{safe_name}.zip",
            mime="application/zip",
            type="primary",
            use_container_width=True,
        )
