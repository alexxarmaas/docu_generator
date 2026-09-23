from __future__ import annotations

import os

import streamlit as st
from dotenv import load_dotenv

from docu_generator.config import load_profile
from docu_generator.pipeline import DocumentationPipeline
from docu_generator.providers import build_provider
from docu_generator.services.exporter import build_export_zip

load_dotenv()

st.set_page_config(
    page_title="Docu Generator",
    page_icon="📘",
    layout="wide",
)

st.title("Docu Generator")
st.caption("Capturas + contexto → guía de usuario lista para revisar y compartir.")

with st.sidebar:
    st.header("Configuración")
    profile_name = st.selectbox("Perfil", ["brisia"], index=0)
    audience = st.selectbox(
        "Audiencia",
        ["Usuario", "Usuario avanzado", "Técnico"],
        index=0,
    )
    model_name = os.getenv("DOCU_MODEL", "gpt-5.6-luna")
    provider = build_provider(model=model_name)
    if provider.ai_enabled:
        st.success(f"IA activa · {model_name}")
    else:
        st.info("Modo fallback · añade OPENAI_API_KEY para activar análisis visual")

profile = load_profile(profile_name)

title = st.text_input(
    "Título de la guía",
    placeholder="Cómo revisar un albarán en Brisia",
)

instructions = st.text_area(
    "¿Qué quieres explicar?",
    height=130,
    placeholder=(
        "Explica cómo revisar las líneas detectadas antes de confirmar el documento. "
        "Destaca cantidades, precios y descuentos."
    ),
)

uploaded_files = st.file_uploader(
    "Capturas de pantalla",
    type=["png", "jpg", "jpeg", "webp"],
    accept_multiple_files=True,
    help="El orden de subida se utilizará como orden narrativo inicial.",
)

if uploaded_files:
    st.subheader("Capturas")
    columns = st.columns(min(3, len(uploaded_files)))
    for index, uploaded in enumerate(uploaded_files):
        with columns[index % len(columns)]:
            st.image(uploaded, caption=f"{index + 1}. {uploaded.name}", use_container_width=True)

generate = st.button(
    "Generar guía",
    type="primary",
    disabled=not (title.strip() and instructions.strip() and uploaded_files),
)

if generate:
    images = [
        {
            "name": f.name,
            "mime_type": f.type or "image/png",
            "bytes": f.getvalue(),
        }
        for f in uploaded_files
    ]

    pipeline = DocumentationPipeline(provider=provider, profile=profile)

    with st.status("Generando documentación...", expanded=True) as status:
        st.write("Analizando capturas…")
        evidences = pipeline.analyze_images(images, instructions=instructions)

        st.write("Redactando la guía…")
        guide = pipeline.generate_guide(
            title=title,
            instructions=instructions,
            audience=audience,
            evidences=evidences,
        )

        st.write("Revisando coherencia…")
        review = pipeline.review_guide(guide=guide, evidences=evidences)

        status.update(label="Guía generada", state="complete", expanded=False)

    st.session_state["guide"] = guide
    st.session_state["review"] = review
    st.session_state["evidences"] = evidences
    st.session_state["images"] = images

if "guide" in st.session_state:
    guide = st.session_state["guide"]
    review = st.session_state["review"]
    evidences = st.session_state["evidences"]
    images = st.session_state["images"]

    st.divider()
    st.header(guide.title)
    if guide.introduction:
        st.markdown(guide.introduction)

    image_lookup = {image["name"]: image for image in images}

    for number, section in enumerate(guide.sections, start=1):
        st.subheader(f"{number}. {section.title}")
        st.markdown(section.body)
        if section.image_name and section.image_name in image_lookup:
            st.image(
                image_lookup[section.image_name]["bytes"],
                caption=section.image_name,
                use_container_width=True,
            )

    if review.issues:
        with st.expander(f"Revisión · {len(review.issues)} aviso(s)", expanded=True):
            for issue in review.issues:
                st.warning(issue)
    else:
        st.success("Revisión superada: no se han detectado incoherencias evidentes.")

    with st.expander("Evidencia detectada"):
        for evidence in evidences:
            st.markdown(f"**{evidence.image_name} · {evidence.screen_name}**")
            if evidence.visible_elements:
                st.write("Elementos:", ", ".join(evidence.visible_elements))
            if evidence.supported_actions:
                st.write("Acciones:", ", ".join(evidence.supported_actions))
            if evidence.uncertainties:
                st.write("Incertidumbres:", ", ".join(evidence.uncertainties))

    export_bytes = build_export_zip(
        guide=guide,
        review=review,
        images=images,
        profile=profile,
    )
    safe_name = "".join(c if c.isalnum() or c in "-_" else "-" for c in guide.title.lower())
    st.download_button(
        "Descargar paquete",
        data=export_bytes,
        file_name=f"{safe_name or 'guia'}.zip",
        mime="application/zip",
        type="primary",
    )
