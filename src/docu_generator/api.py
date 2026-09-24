from __future__ import annotations

import json
from urllib.parse import quote

from fastapi import Body, FastAPI, HTTPException, Query, Response
from fastapi.middleware.cors import CORSMiddleware

from docu_generator.config import load_profile
from docu_generator.models import ReviewReport
from docu_generator.services.docx_exporter import build_docx
from docu_generator.services.exporter import build_export_zip, render_html, render_markdown
from docu_generator.services.pdf_exporter import build_pdf
from docu_generator.services.project_builder import build_document
from docu_generator.services.project_io import normalize_project
from docu_generator.services.validator import validate_guide
from docu_generator.services.workspace import (
    autosave,
    delete_saved_project,
    list_projects,
    list_versions,
    load_autosave,
    load_saved_project,
    load_version,
    save_project,
)


app = FastAPI(
    title="Docu Generator API",
    version="0.4.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3001",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _payload_bytes(payload: dict) -> bytes:
    return json.dumps(payload, ensure_ascii=False).encode("utf-8")


def _portable_payload(raw: bytes) -> dict:
    return json.loads(normalize_project(raw).decode("utf-8"))


def _entry(entry) -> dict:
    return {
        "name": entry.name,
        "modified_at": entry.modified_at.isoformat(),
        "size_bytes": entry.size_bytes,
    }


@app.get("/api/health")
def health():
    return {"ok": True, "version": app.version}


@app.get("/api/profile")
def profile():
    data = load_profile("brisia")
    return {
        "name": data.get("name"),
        "product": data.get("product"),
        "brand": data.get("brand", {}),
    }


@app.get("/api/autosave")
def get_autosave():
    raw = load_autosave()
    return {"project": _portable_payload(raw) if raw else None}


@app.post("/api/autosave")
def put_autosave(payload: dict = Body(...)):
    raw = normalize_project(_payload_bytes(payload))
    autosave(raw)
    return {"ok": True}


@app.get("/api/projects")
def projects():
    return {"projects": [_entry(item) for item in list_projects()]}


@app.get("/api/projects/{name}")
def project(name: str):
    try:
        return {"project": _portable_payload(load_saved_project(name))}
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado") from exc


@app.post("/api/projects")
def save(
    payload: dict = Body(...),
    filename: str | None = Query(default=None),
):
    raw = normalize_project(_payload_bytes(payload))
    portable = json.loads(raw.decode("utf-8"))
    title = portable.get("title") or "proyecto"
    path = save_project(title, raw, filename=filename)
    return {"ok": True, "name": path.name}


@app.delete("/api/projects/{name}")
def delete_project(name: str):
    delete_saved_project(name)
    return {"ok": True}


@app.get("/api/projects/{name}/versions")
def versions(name: str):
    return {"versions": [_entry(item) for item in list_versions(name)]}


@app.get("/api/projects/{name}/versions/{version_name}")
def version(name: str, version_name: str):
    try:
        raw = load_version(name, version_name)
        return {"project": _portable_payload(raw)}
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Versión no encontrada") from exc


@app.post("/api/validate")
def validate(payload: dict = Body(...)):
    guide, images = build_document(_payload_bytes(payload))
    issues = validate_guide(guide, images)
    return {
        "issues": [
            {"level": issue.level, "message": issue.message}
            for issue in issues
        ]
    }


@app.post("/api/export/{format_name}")
def export_document(format_name: str, payload: dict = Body(...)):
    guide, images = build_document(_payload_bytes(payload))
    profile_data = load_profile("brisia")
    review = ReviewReport()

    safe_title = "".join(
        character if character.isalnum() or character in "-_" else "-"
        for character in guide.title.lower()
    ).strip("-") or "guia"

    if format_name == "pdf":
        data = build_pdf(guide, images, profile_data)
        mime = "application/pdf"
        filename = f"{safe_title}.pdf"
    elif format_name == "docx":
        data = build_docx(guide, images, profile_data)
        mime = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        filename = f"{safe_title}.docx"
    elif format_name == "html":
        data = render_html(guide, review, images, profile_data).encode("utf-8")
        mime = "text/html; charset=utf-8"
        filename = f"{safe_title}.html"
    elif format_name == "md":
        data = render_markdown(guide, review).encode("utf-8")
        mime = "text/markdown; charset=utf-8"
        filename = f"{safe_title}.md"
    elif format_name == "zip":
        data = build_export_zip(guide, review, images, profile_data)
        mime = "application/zip"
        filename = f"{safe_title}.zip"
    else:
        raise HTTPException(status_code=404, detail="Formato no soportado")

    return Response(
        content=data,
        media_type=mime,
        headers={
            "Content-Disposition": (
                f"attachment; filename*=UTF-8''{quote(filename)}"
            )
        },
    )
