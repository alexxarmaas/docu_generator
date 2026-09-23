from __future__ import annotations

from datetime import datetime
from uuid import uuid4

import streamlit as st
from dotenv import load_dotenv

from docu_generator.config import load_profile
from docu_generator.models import GuideBlock, GuideDraft, GuideSection, ReviewReport
from docu_generator.services.docx_exporter import build_docx
from docu_generator.services.exporter import (
    build_export_zip,
    render_html,
    render_markdown,
)
from docu_generator.services.pdf_exporter import build_pdf
from docu_generator.services.project_io import dump_project, load_project
from docu_generator.services.templates import create_from_template, template_choices
from docu_generator.services.validator import has_blocking_errors, validate_guide
from docu_generator.services.workspace import (
    WORKSPACE_ROOT,
    autosave,
    delete_saved_project,
    list_projects,
    list_versions,
    load_autosave,
    load_saved_project,
    load_version,
    save_project,
)

load_dotenv()

st.set_page_config(
    page_title="Docu Generator",
    page_icon="📘",
    layout="wide",
)

BLOCK_LIBRARY = {
    "text": {"label": "Texto", "icon": "📝", "type": "text"},
    "image": {"label": "Imagen", "icon": "🖼️", "type": "image"},
    "checklist": {"label": "Checklist", "icon": "☑️", "type": "checklist"},
    "table": {"label": "Tabla", "icon": "▦", "type": "table"},
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
    "divider": {"label": "Separador", "icon": "—", "type": "divider"},
    "pagebreak": {
        "label": "Salto de página",
        "icon": "↧",
        "type": "pagebreak",
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
        "image_width": "large",
        "align": "center",
    }


def clone_block(block: dict) -> dict:
    clone = dict(block)
    clone["id"] = uuid4().hex
    return clone


def new_step() -> dict:
    return {
        "id": uuid4().hex,
        "title": "",
        "blocks": [new_block("text")],
    }


def metadata_from_state() -> dict:
    return {
        "document_type": st.session_state.get("doc_type", "Guía"),
        "version_label": st.session_state.get("doc_version", "1.0"),
        "status": st.session_state.get("doc_status", "Borrador"),
        "author": st.session_state.get("doc_author", ""),
        "show_cover": st.session_state.get("show_cover", True),
        "show_toc": st.session_state.get("show_toc", True),
    }


def project_payload() -> bytes:
    return dump_project(
        title=st.session_state.get("guide_title", ""),
        introduction=st.session_state.get("guide_intro", ""),
        closing_note=st.session_state.get("guide_closing", ""),
        steps=st.session_state.get("steps", []),
        metadata=metadata_from_state(),
    )


def apply_project(project: dict, *, clear_history: bool = False) -> None:
    metadata = project.get("metadata", {})
    st.session_state.guide_title = project.get("title", "")
    st.session_state.guide_intro = project.get("introduction", "")
    st.session_state.guide_closing = project.get("closing_note", "")
    st.session_state.steps = project.get("steps") or [new_step()]
    st.session_state.doc_type = metadata.get("document_type", "Guía")
    st.session_state.doc_version = metadata.get("version_label", "1.0")
    st.session_state.doc_status = metadata.get("status", "Borrador")
    st.session_state.doc_author = metadata.get("author", "")
    st.session_state.show_cover = metadata.get("show_cover", True)
    st.session_state.show_toc = metadata.get("show_toc", True)

    if clear_history:
        st.session_state.undo_stack = []
        st.session_state.redo_stack = []
        st.session_state.last_snapshot = None


def ensure_state() -> None:
    defaults = {
        "guide_title": "",
        "guide_intro": "",
        "guide_closing": "",
        "steps": [new_step()],
        "doc_type": "Guía",
        "doc_version": "1.0",
        "doc_status": "Borrador",
        "doc_author": "",
        "show_cover": True,
        "show_toc": True,
        "current_project_name": "",
        "last_saved_at": "",
        "undo_stack": [],
        "redo_stack": [],
        "last_snapshot": None,
        "skip_history_once": False,
        "history_restoring": False,
        "editor_initialized": False,
    }

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

    if not st.session_state.editor_initialized:
        raw = load_autosave()
        if raw:
            try:
                apply_project(load_project(raw), clear_history=True)
                st.session_state.autosave_restored = True
            except Exception:
                st.session_state.autosave_restored = False

        st.session_state.editor_initialized = True
        st.session_state.last_snapshot = project_payload()


def prepare_mutation() -> None:
    current = project_payload()
    stack = st.session_state.undo_stack
    if not stack or stack[-1] != current:
        stack.append(current)
    if len(stack) > 60:
        del stack[:-60]
    st.session_state.redo_stack = []
    st.session_state.skip_history_once = True


def undo() -> None:
    if not st.session_state.undo_stack:
        return
    current = project_payload()
    previous = st.session_state.undo_stack.pop()
    st.session_state.redo_stack.append(current)
    apply_project(load_project(previous))
    st.session_state.history_restoring = True
    st.rerun()


def redo() -> None:
    if not st.session_state.redo_stack:
        return
    current = project_payload()
    next_state = st.session_state.redo_stack.pop()
    st.session_state.undo_stack.append(current)
    apply_project(load_project(next_state))
    st.session_state.history_restoring = True
    st.rerun()


def track_history_and_autosave() -> None:
    current = project_payload()

    if st.session_state.history_restoring:
        st.session_state.last_snapshot = current
        st.session_state.history_restoring = False
    elif st.session_state.skip_history_once:
        st.session_state.last_snapshot = current
        st.session_state.skip_history_once = False
    elif st.session_state.last_snapshot is None:
        st.session_state.last_snapshot = current
    elif current != st.session_state.last_snapshot:
        previous = st.session_state.last_snapshot
        stack = st.session_state.undo_stack
        if not stack or stack[-1] != previous:
            stack.append(previous)
        if len(stack) > 60:
            del stack[:-60]
        st.session_state.redo_stack = []
        st.session_state.last_snapshot = current

    try:
        autosave(current)
        st.session_state.autosave_ok = True
    except Exception:
        st.session_state.autosave_ok = False


def create_new_project(template_id: str) -> None:
    template = create_from_template(template_id)
    prepare_mutation()
    st.session_state.guide_title = ""
    st.session_state.guide_intro = template["introduction"]
    st.session_state.guide_closing = template["closing_note"]
    st.session_state.steps = template["steps"]
    st.session_state.doc_type = template["document_type"]
    st.session_state.doc_version = "1.0"
    st.session_state.doc_status = "Borrador"
    st.session_state.current_project_name = ""
    st.session_state.last_saved_at = ""
    st.rerun()


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


def transfer_block(
    source_step_index: int,
    block_index: int,
    target_step_index: int,
    *,
    copy: bool,
) -> None:
    source_step = st.session_state.steps[source_step_index]
    target_step = st.session_state.steps[target_step_index]
    block = source_step["blocks"][block_index]
    target_step["blocks"].append(clone_block(block) if copy else block)

    if not copy:
        source_step["blocks"].pop(block_index)
        if not source_step["blocks"]:
            source_step["blocks"].append(new_block("text"))


def block_has_content(block: dict) -> bool:
    block_type = block.get("type", "text")

    if block_type in {"text", "note"}:
        return bool(block.get("text", "").strip())
    if block_type in {"checklist", "table"}:
        return any(line.strip() for line in block.get("items", "").splitlines())
    if block_type == "image":
        return bool(block.get("image_name") and block.get("image_bytes") is not None)
    if block_type in {"divider", "pagebreak"}:
        return True
    return False


def block_display(block: dict) -> tuple[str, str]:
    block_type = block.get("type", "text")

    if block_type == "text":
        text = block.get("text", "").strip()
        return "📝", (text[:54] + ("..." if len(text) > 54 else "")) or "Texto"
    if block_type == "image":
        return "🖼️", block.get("image_caption") or block.get("image_name") or "Imagen"
    if block_type == "checklist":
        count = len([x for x in block.get("items", "").splitlines() if x.strip()])
        return "☑️", f"Checklist · {count} elemento(s)"
    if block_type == "table":
        count = len([x for x in block.get("items", "").splitlines() if x.strip()])
        return "▦", f"Tabla · {count} fila(s)"
    if block_type == "note":
        variants = {"tip": "💡", "warning": "⚠️", "success": "✅", "info": "➡️"}
        return variants.get(block.get("variant"), "ℹ️"), block.get("label") or "Aviso"
    if block_type == "pagebreak":
        return "↧", "Salto de página"
    return "—", "Separador"


def render_insert_menu(step: dict, insert_index: int, key_prefix: str) -> None:
    with st.popover("＋ Insertar debajo"):
        columns = st.columns(2)
        for option_index, (preset, config) in enumerate(BLOCK_LIBRARY.items()):
            with columns[option_index % 2]:
                if st.button(
                    f"{config['icon']} {config['label']}",
                    key=f"{key_prefix}_{preset}",
                    use_container_width=True,
                ):
                    prepare_mutation()
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
            elif block_type in {"checklist", "table"}:
                items = [
                    line.strip()
                    for line in block.get("items", "").splitlines()
                    if line.strip()
                ]
                guide_blocks.append(GuideBlock(type=block_type, items=items))
            elif block_type in {"divider", "pagebreak"}:
                guide_blocks.append(GuideBlock(type=block_type))
            elif block_type == "image":
                image_name = block.get("image_name")
                guide_blocks.append(
                    GuideBlock(
                        type="image",
                        image_name=image_name,
                        image_caption=block.get("image_caption", "").strip(),
                        image_width=block.get("image_width", "large"),
                        align=block.get("align", "center"),
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
        document_type=st.session_state.doc_type,
        version=st.session_state.doc_version.strip() or "1.0",
        status=st.session_state.doc_status,
        author=st.session_state.doc_author.strip(),
        updated_at=st.session_state.last_saved_at,
        show_cover=st.session_state.show_cover,
        show_toc=st.session_state.show_toc,
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
        message = f"**{block.label}**\n\n{block.text}" if block.label else block.text
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
    elif block.type == "pagebreak":
        st.caption("──────── salto de página ────────")
    elif block.type == "table":
        rows = [[cell.strip() for cell in row.split("|")] for row in block.items]
        if rows:
            st.table(rows)
    elif block.type == "image" and block.image_name in image_lookup:
        widths = {"small": 280, "medium": 440, "large": 650, "full": None}
        kwargs = {}
        width = widths.get(block.image_width)
        if width:
            kwargs["width"] = width
        else:
            kwargs["use_container_width"] = True
        st.image(
            image_lookup[block.image_name]["bytes"],
            caption=block.image_caption or None,
            **kwargs,
        )


def render_block_editor(
    step: dict,
    block: dict,
    block_index: int,
    step_index: int,
) -> None:
    icon, display = block_display(block)

    with st.expander(
        f"{icon} {block_index + 1}. {display}",
        expanded=not block_has_content(block),
    ):
        actions = st.columns([1, 1, 1, 1, 4])

        if actions[0].button("↑", key=f"bup_{block['id']}", disabled=block_index == 0):
            prepare_mutation()
            move_item(step["blocks"], block_index, -1)
            st.rerun()

        if actions[1].button(
            "↓",
            key=f"bdown_{block['id']}",
            disabled=block_index == len(step["blocks"]) - 1,
        ):
            prepare_mutation()
            move_item(step["blocks"], block_index, 1)
            st.rerun()

        if actions[2].button("⧉", key=f"bdup_{block['id']}", help="Duplicar"):
            prepare_mutation()
            duplicate_block(step, block_index)
            st.rerun()

        if actions[3].button("✕", key=f"bdel_{block['id']}", help="Eliminar"):
            prepare_mutation()
            remove_block(step, block_index)
            st.rerun()

        block_type = block.get("type", "text")

        if block_type == "text":
            block["text"] = st.text_area(
                "Texto",
                value=block.get("text", ""),
                key=f"text_{block['id']}",
                height=130,
                placeholder="Escribe la explicación. Puedes utilizar Markdown.",
            )

        elif block_type == "note":
            meta_a, meta_b = st.columns([1.2, 1])
            block["label"] = meta_a.text_input(
                "Etiqueta",
                value=block.get("label", ""),
                key=f"label_{block['id']}",
            )
            variants = ["info", "tip", "warning", "success"]
            labels = {
                "info": "Información",
                "tip": "Consejo",
                "warning": "Advertencia",
                "success": "Resultado",
            }
            current = block.get("variant", "info")
            if current not in variants:
                current = "info"
            block["variant"] = meta_b.selectbox(
                "Estilo",
                variants,
                index=variants.index(current),
                format_func=lambda value: labels[value],
                key=f"variant_{block['id']}",
            )
            block["text"] = st.text_area(
                "Contenido",
                value=block.get("text", ""),
                key=f"note_{block['id']}",
                height=100,
            )

        elif block_type == "checklist":
            block["items"] = st.text_area(
                "Elementos",
                value=block.get("items", ""),
                key=f"check_{block['id']}",
                height=120,
                placeholder="Un elemento por línea",
            )

        elif block_type == "table":
            block["items"] = st.text_area(
                "Filas",
                value=block.get("items", ""),
                key=f"table_{block['id']}",
                height=140,
                placeholder=(
                    "Campo | Descripción | Ejemplo\n"
                    "Proveedor | Proveedor del documento | ACME S.L.\n"
                    "Fecha | Fecha del albarán | 23/09/2026"
                ),
                help="Una fila por línea y columnas separadas con |",
            )

        elif block_type == "divider":
            st.caption("Inserta una línea separadora.")

        elif block_type == "pagebreak":
            st.caption("Fuerza una nueva página en PDF/DOCX y en impresión HTML.")

        elif block_type == "image":
            upload = st.file_uploader(
                "Imagen",
                type=["png", "jpg", "jpeg", "webp"],
                key=f"image_{block['id']}",
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
                    key=f"caption_{block['id']}",
                )
                img_a, img_b = st.columns(2)
                widths = ["small", "medium", "large", "full"]
                current_width = block.get("image_width", "large")
                if current_width not in widths:
                    current_width = "large"
                block["image_width"] = img_a.selectbox(
                    "Tamaño",
                    widths,
                    index=widths.index(current_width),
                    format_func=lambda value: {
                        "small": "Pequeña",
                        "medium": "Mediana",
                        "large": "Grande",
                        "full": "Ancho completo",
                    }[value],
                    key=f"width_{block['id']}",
                )
                aligns = ["left", "center", "right"]
                current_align = block.get("align", "center")
                if current_align not in aligns:
                    current_align = "center"
                block["align"] = img_b.selectbox(
                    "Alineación",
                    aligns,
                    index=aligns.index(current_align),
                    format_func=lambda value: {
                        "left": "Izquierda",
                        "center": "Centro",
                        "right": "Derecha",
                    }[value],
                    key=f"align_{block['id']}",
                )

                if st.button("Quitar imagen", key=f"rmimg_{block['id']}"):
                    prepare_mutation()
                    block["image_name"] = None
                    block["image_caption"] = ""
                    block["image_bytes"] = None
                    block["image_mime"] = None
                    st.rerun()

        if len(st.session_state.steps) > 1:
            st.divider()
            targets = [
                (index, f"Paso {index + 1}: {candidate.get('title') or 'Sin título'}")
                for index, candidate in enumerate(st.session_state.steps)
                if index != step_index
            ]
            target_index = st.selectbox(
                "Enviar bloque a",
                [item[0] for item in targets],
                format_func=lambda value: next(
                    label for index, label in targets if index == value
                ),
                key=f"target_{block['id']}",
            )
            move_col, copy_col = st.columns(2)
            if move_col.button("Mover", key=f"move_{block['id']}", use_container_width=True):
                prepare_mutation()
                transfer_block(step_index, block_index, target_index, copy=False)
                st.rerun()
            if copy_col.button("Copiar", key=f"copy_{block['id']}", use_container_width=True):
                prepare_mutation()
                transfer_block(step_index, block_index, target_index, copy=True)
                st.rerun()

    render_insert_menu(
        step,
        block_index + 1,
        key_prefix=f"insert_{block['id']}",
    )


ensure_state()
profile = load_profile("brisia")

st.title("Docu Generator")
st.caption("Workspace local para crear, versionar y publicar documentación de producto.")

with st.sidebar:
    st.header("Edición")
    undo_col, redo_col = st.columns(2)
    if undo_col.button(
        "↶ Deshacer",
        use_container_width=True,
        disabled=not st.session_state.undo_stack,
    ):
        undo()
    if redo_col.button(
        "↷ Rehacer",
        use_container_width=True,
        disabled=not st.session_state.redo_stack,
    ):
        redo()

    autosave_label = "Autosave ✓" if st.session_state.get("autosave_ok", True) else "Autosave con error"
    st.caption(f"{autosave_label} · {WORKSPACE_ROOT}")

    with st.expander("Biblioteca local", expanded=True):
        projects = list_projects()
        if projects:
            selected_project = st.selectbox(
                "Proyectos",
                [entry.name for entry in projects],
                format_func=lambda name: name.removesuffix(".docugen.json"),
            )
            open_col, del_col = st.columns(2)
            if open_col.button("Abrir", use_container_width=True):
                project = load_project(load_saved_project(selected_project))
                apply_project(project, clear_history=True)
                st.session_state.current_project_name = selected_project
                st.session_state.last_snapshot = project_payload()
                st.rerun()
            if del_col.button("Eliminar", use_container_width=True):
                delete_saved_project(selected_project)
                st.rerun()

            versions = list_versions(selected_project)
            if versions:
                selected_version = st.selectbox(
                    "Versiones guardadas",
                    [entry.name for entry in versions[:20]],
                    format_func=lambda name: name.replace(".docugen.json", ""),
                )
                if st.button("Restaurar versión", use_container_width=True):
                    apply_project(
                        load_project(
                            load_version(selected_project, selected_version)
                        )
                    )
                    st.session_state.history_restoring = True
                    st.rerun()
        else:
            st.caption("Todavía no hay proyectos guardados.")

        if st.button("Guardar en biblioteca", use_container_width=True, type="primary"):
            st.session_state.last_saved_at = datetime.now().strftime("%d/%m/%Y %H:%M")
            payload = project_payload()
            base_name = (
                st.session_state.current_project_name.removesuffix(".docugen.json")
                if st.session_state.current_project_name
                else st.session_state.guide_title
            )
            path = save_project(
                st.session_state.guide_title or "proyecto",
                payload,
                filename=base_name,
            )
            st.session_state.current_project_name = path.name
            st.session_state.last_snapshot = payload
            st.success("Proyecto guardado y versionado.")

    with st.expander("Importar / crear"):
        project_upload = st.file_uploader(
            "Importar .docugen.json",
            type=["json"],
        )
        if st.button(
            "Abrir archivo importado",
            use_container_width=True,
            disabled=project_upload is None,
        ):
            try:
                apply_project(
                    load_project(project_upload.getvalue()),
                    clear_history=True,
                )
                st.session_state.current_project_name = ""
                st.session_state.last_snapshot = project_payload()
                st.rerun()
            except Exception as exc:
                st.error(f"No se pudo abrir: {exc}")

        choices = template_choices()
        template_id = st.selectbox(
            "Plantilla",
            [item[0] for item in choices],
            format_func=lambda value: next(
                label for key, label in choices if key == value
            ),
        )
        if st.button("Nueva desde plantilla", use_container_width=True):
            create_new_project(template_id)

    with st.expander("Documento", expanded=True):
        st.text_input("Título", key="guide_title")
        st.text_area("Introducción", key="guide_intro", height=90)
        st.text_area("Cierre", key="guide_closing", height=80)

    with st.expander("Publicación"):
        st.text_input("Tipo", key="doc_type")
        meta_a, meta_b = st.columns(2)
        meta_a.text_input("Versión", key="doc_version")
        meta_b.selectbox(
            "Estado",
            ["Borrador", "En revisión", "Publicado", "Archivado"],
            key="doc_status",
        )
        st.text_input("Autor", key="doc_author")
        st.checkbox("Portada", key="show_cover")
        st.checkbox("Índice", key="show_toc")
        if st.session_state.last_saved_at:
            st.caption(f"Último guardado: {st.session_state.last_saved_at}")

        if st.button("Publicar versión", use_container_width=True):
            st.session_state.doc_status = "Publicado"
            st.session_state.last_saved_at = datetime.now().strftime("%d/%m/%Y %H:%M")
            payload = project_payload()
            base_name = (
                st.session_state.current_project_name.removesuffix(".docugen.json")
                if st.session_state.current_project_name
                else st.session_state.guide_title
            )
            path = save_project(
                st.session_state.guide_title or "proyecto",
                payload,
                filename=base_name,
            )
            st.session_state.current_project_name = path.name
            st.session_state.last_snapshot = payload
            st.success(f"Versión {st.session_state.doc_version} publicada y archivada.")

    if st.button("＋ Añadir paso", use_container_width=True):
        prepare_mutation()
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
                    key=f"sup_{step['id']}",
                    disabled=step_index == 0,
                ):
                    prepare_mutation()
                    move_item(st.session_state.steps, step_index, -1)
                    st.rerun()

                if down.button(
                    "↓",
                    key=f"sdown_{step['id']}",
                    disabled=step_index == len(st.session_state.steps) - 1,
                ):
                    prepare_mutation()
                    move_item(st.session_state.steps, step_index, 1)
                    st.rerun()

                if duplicate.button("⧉", key=f"sdup_{step['id']}"):
                    prepare_mutation()
                    duplicate_step(step_index)
                    st.rerun()

                if delete.button("✕", key=f"sdel_{step['id']}"):
                    prepare_mutation()
                    remove_step(step_index)
                    st.rerun()

            step["title"] = st.text_input(
                "Título del paso",
                value=step.get("title", ""),
                key=f"stitle_{step['id']}",
            )

            for block_index, block in enumerate(step.get("blocks", [])):
                render_block_editor(step, block, block_index, step_index)

            with st.popover("＋ Añadir bloque al final", use_container_width=True):
                columns = st.columns(2)
                for option_index, (preset, config) in enumerate(BLOCK_LIBRARY.items()):
                    with columns[option_index % 2]:
                        if st.button(
                            f"{config['icon']} {config['label']}",
                            key=f"end_{step['id']}_{preset}",
                            use_container_width=True,
                        ):
                            prepare_mutation()
                            insert_block(step, len(step["blocks"]), preset)
                            st.rerun()

guide, images = build_guide()
review = ReviewReport()
validation_issues = validate_guide(guide, images)
blocking_errors = has_blocking_errors(validation_issues)

with preview_col:
    st.subheader("Vista previa")
    st.caption(
        f"{guide.document_type} · v{guide.version} · {guide.status}"
        + (f" · {guide.author}" if guide.author else "")
    )

    with st.container(border=True):
        st.caption("BRISIA · DOCUMENTACIÓN")
        st.markdown(f"# {guide.title}")

        if guide.introduction:
            st.markdown(guide.introduction)

        if guide.show_toc and guide.sections:
            with st.expander("Contenido", expanded=False):
                for index, section in enumerate(guide.sections, start=1):
                    st.write(f"{index}. {section.title}")

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
            st.success(guide.closing_note)

    with st.expander(
        f"Validación · {len(validation_issues)} aviso(s)",
        expanded=blocking_errors,
    ):
        if not validation_issues:
            st.success("Documento listo para exportar.")
        for issue in validation_issues:
            if issue.level == "error":
                st.error(issue.message)
            elif issue.level == "warning":
                st.warning(issue.message)
            else:
                st.info(issue.message)

    st.markdown("#### Guardar y exportar")

    safe_name = "".join(
        c if c.isalnum() or c in "-_" else "-"
        for c in guide.title.lower()
    ).strip("-") or "guia"

    project_bytes = project_payload()
    st.download_button(
        "Proyecto editable",
        data=project_bytes,
        file_name=f"{safe_name}.docugen.json",
        mime="application/json",
        use_container_width=True,
    )

    if guide.sections:
        html_text = render_html(guide, review, images, profile)
        markdown_text = render_markdown(guide, review)
        pdf_bytes = build_pdf(guide, images, profile)
        docx_bytes = build_docx(guide, images, profile)
        zip_bytes = build_export_zip(guide, review, images, profile)

        first, second = st.columns(2)
        first.download_button(
            "PDF",
            data=pdf_bytes,
            file_name=f"{safe_name}.pdf",
            mime="application/pdf",
            type="primary",
            use_container_width=True,
            disabled=blocking_errors,
        )
        second.download_button(
            "Word / DOCX",
            data=docx_bytes,
            file_name=f"{safe_name}.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            use_container_width=True,
            disabled=blocking_errors,
        )

        third, fourth = st.columns(2)
        third.download_button(
            "HTML",
            data=html_text.encode("utf-8"),
            file_name=f"{safe_name}.html",
            mime="text/html",
            use_container_width=True,
            disabled=blocking_errors,
        )
        fourth.download_button(
            "Markdown",
            data=markdown_text.encode("utf-8"),
            file_name=f"{safe_name}.md",
            mime="text/markdown",
            use_container_width=True,
            disabled=blocking_errors,
        )

        st.download_button(
            "ZIP completo",
            data=zip_bytes,
            file_name=f"{safe_name}.zip",
            mime="application/zip",
            use_container_width=True,
            disabled=blocking_errors,
        )

track_history_and_autosave()
