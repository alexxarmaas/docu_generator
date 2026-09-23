from __future__ import annotations

from uuid import uuid4

import streamlit as st
from dotenv import load_dotenv

from docu_generator.config import load_profile
from docu_generator.models import GuideDraft, GuideSection, ReviewReport
from docu_generator.services.exporter import build_export_zip

load_dotenv()

st.set_page_config(
    page_title="Docu Generator",
    page_icon="📘",
    layout="wide",
)


def new_step() -> dict:
    return {
        "id": uuid4().hex,
        "title": "",
        "body": "",
        "checklist": "",
        "note": "",
        "image_name": None,
        "image_bytes": None,
        "image_mime": None,
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


def move_step(index: int, offset: int) -> None:
    target = index + offset
    if target < 0 or target >= len(st.session_state.steps):
        return
    st.session_state.steps[index], st.session_state.steps[target] = (
        st.session_state.steps[target],
        st.session_state.steps[index],
    )


def remove_step(index: int) -> None:
    if len(st.session_state.steps) == 1:
        st.session_state.steps[0] = new_step()
        return
    st.session_state.steps.pop(index)


def build_guide() -> tuple[GuideDraft, list[dict]]:
    sections: list[GuideSection] = []
    images: list[dict] = []

    for step in st.session_state.steps:
        title = step["title"].strip()
        body = step["body"].strip()
        checklist = [
            item.strip()
            for item in step["checklist"].splitlines()
            if item.strip()
        ]
        note = step["note"].strip()

        if not any((title, body, checklist, note, step["image_name"])):
            continue

        sections.append(
            GuideSection(
                title=title or "Paso sin título",
                body=body,
                checklist=checklist,
                note=note,
                image_name=step["image_name"],
            )
        )

        if step["image_name"] and step["image_bytes"] is not None:
            images.append(
                {
                    "name": step["image_name"],
                    "mime_type": step["image_mime"] or "image/png",
                    "bytes": step["image_bytes"],
                }
            )

    guide = GuideDraft(
        title=st.session_state.guide_title.strip() or "Guía sin título",
        introduction=st.session_state.guide_intro.strip(),
        sections=sections,
        closing_note=st.session_state.guide_closing.strip(),
    )
    return guide, images


ensure_state()
profile = load_profile("brisia")

st.title("Docu Generator")
st.caption("Editor local por bloques para crear guías de usuario sin depender de ninguna API.")

with st.sidebar:
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
        placeholder="Ejemplo: Comprueba los datos antes de confirmar el documento.",
    )

    st.divider()
    st.caption(f"{len(st.session_state.steps)} bloque(s) de paso")

    if st.button("＋ Añadir paso", use_container_width=True, type="primary"):
        st.session_state.steps.append(new_step())
        st.rerun()

editor_col, preview_col = st.columns([1.05, 0.95], gap="large")

with editor_col:
    st.subheader("Editor")

    for index, step in enumerate(st.session_state.steps):
        step_number = index + 1

        with st.container(border=True):
            top_left, top_actions = st.columns([4, 2])
            with top_left:
                st.markdown(f"### Paso {step_number}")
            with top_actions:
                up, down, delete = st.columns(3)
                if up.button("↑", key=f"up_{step['id']}", disabled=index == 0):
                    move_step(index, -1)
                    st.rerun()
                if down.button(
                    "↓",
                    key=f"down_{step['id']}",
                    disabled=index == len(st.session_state.steps) - 1,
                ):
                    move_step(index, 1)
                    st.rerun()
                if delete.button("✕", key=f"delete_{step['id']}"):
                    remove_step(index)
                    st.rerun()

            step["title"] = st.text_input(
                "Título del paso",
                value=step["title"],
                key=f"title_{step['id']}",
                placeholder="Ej. Selecciona el albarán",
            )

            step["body"] = st.text_area(
                "Explicación",
                value=step["body"],
                key=f"body_{step['id']}",
                height=120,
                placeholder=(
                    "Explica qué debe hacer el usuario. "
                    "Puedes utilizar Markdown para negritas, listas, etc."
                ),
            )

            upload = st.file_uploader(
                "Imagen del paso",
                type=["png", "jpg", "jpeg", "webp"],
                key=f"image_{step['id']}",
            )
            if upload is not None:
                step["image_name"] = upload.name
                step["image_bytes"] = upload.getvalue()
                step["image_mime"] = upload.type or "image/png"

            if step["image_bytes"] is not None:
                st.image(
                    step["image_bytes"],
                    caption=step["image_name"],
                    use_container_width=True,
                )
                if st.button("Quitar imagen", key=f"remove_image_{step['id']}"):
                    step["image_name"] = None
                    step["image_bytes"] = None
                    step["image_mime"] = None
                    st.rerun()

            with st.expander("Opciones del paso"):
                step["checklist"] = st.text_area(
                    "Checklist",
                    value=step["checklist"],
                    key=f"checklist_{step['id']}",
                    height=90,
                    placeholder=(
                        "Un elemento por línea\n"
                        "Cantidad correcta\n"
                        "Precio correcto\n"
                        "Proveedor correcto"
                    ),
                    help="Cada línea se exportará como un elemento de comprobación.",
                )
                step["note"] = st.text_area(
                    "Aviso / nota",
                    value=step["note"],
                    key=f"note_{step['id']}",
                    height=80,
                    placeholder="Ej. No confirmes hasta comprobar todos los datos.",
                )

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
            st.info("Añade contenido a un bloque para empezar a construir la guía.")

        image_lookup = {image["name"]: image for image in images}

        for number, section in enumerate(guide.sections, start=1):
            st.markdown(f"### {number}. {section.title}")

            if section.body:
                st.markdown(section.body)

            if section.checklist:
                st.markdown("**Qué comprobar**")
                for item in section.checklist:
                    st.checkbox(
                        item,
                        value=False,
                        disabled=True,
                        key=f"preview_check_{number}_{item}",
                    )

            if section.note:
                st.info(section.note)

            if section.image_name and section.image_name in image_lookup:
                st.image(
                    image_lookup[section.image_name]["bytes"],
                    use_container_width=True,
                )

            if number < len(guide.sections):
                st.divider()

        if guide.closing_note:
            st.info(guide.closing_note)

    if guide.sections:
        export_bytes = build_export_zip(
            guide=guide,
            review=review,
            images=images,
            profile=profile,
        )
        safe_name = "".join(
            c if c.isalnum() or c in "-_" else "-"
            for c in guide.title.lower()
        )
        st.download_button(
            "Descargar guía",
            data=export_bytes,
            file_name=f"{safe_name or 'guia'}.zip",
            mime="application/zip",
            type="primary",
            use_container_width=True,
        )
