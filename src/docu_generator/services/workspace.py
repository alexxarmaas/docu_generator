from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


WORKSPACE_ROOT = Path.home() / "DocuGenerator"
PROJECTS_DIR = WORKSPACE_ROOT / "projects"
VERSIONS_DIR = WORKSPACE_ROOT / "versions"
AUTOSAVE_PATH = WORKSPACE_ROOT / "autosave.docugen.json"


@dataclass
class ProjectEntry:
    name: str
    path: Path
    modified_at: datetime
    size_bytes: int


def ensure_workspace() -> None:
    PROJECTS_DIR.mkdir(parents=True, exist_ok=True)
    VERSIONS_DIR.mkdir(parents=True, exist_ok=True)


def safe_filename(value: str) -> str:
    cleaned = re.sub(r"[^\w\- ]+", "", value, flags=re.UNICODE).strip()
    cleaned = re.sub(r"\s+", "-", cleaned)
    return cleaned[:80] or "proyecto"


def autosave(payload: bytes) -> Path:
    ensure_workspace()
    AUTOSAVE_PATH.write_bytes(payload)
    return AUTOSAVE_PATH


def load_autosave() -> bytes | None:
    if not AUTOSAVE_PATH.exists():
        return None
    return AUTOSAVE_PATH.read_bytes()


def save_project(
    title: str,
    payload: bytes,
    filename: str | None = None,
    *,
    create_version: bool = True,
) -> Path:
    ensure_workspace()
    base = safe_filename(filename or title)
    if not base.endswith(".docugen.json"):
        base = f"{base}.docugen.json"

    path = PROJECTS_DIR / base
    path.write_bytes(payload)

    if create_version:
        project_slug = base.removesuffix(".docugen.json")
        version_dir = VERSIONS_DIR / project_slug
        version_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S-%f")
        (version_dir / f"{timestamp}.docugen.json").write_bytes(payload)

    return path


def list_projects() -> list[ProjectEntry]:
    ensure_workspace()
    entries = []

    for path in PROJECTS_DIR.glob("*.docugen.json"):
        stat = path.stat()
        entries.append(
            ProjectEntry(
                name=path.name,
                path=path,
                modified_at=datetime.fromtimestamp(stat.st_mtime),
                size_bytes=stat.st_size,
            )
        )

    return sorted(entries, key=lambda entry: entry.modified_at, reverse=True)


def list_versions(name: str) -> list[ProjectEntry]:
    ensure_workspace()
    project_slug = Path(name).name.removesuffix(".docugen.json")
    version_dir = VERSIONS_DIR / project_slug
    if not version_dir.exists():
        return []

    entries = []
    for path in version_dir.glob("*.docugen.json"):
        stat = path.stat()
        entries.append(
            ProjectEntry(
                name=path.name,
                path=path,
                modified_at=datetime.fromtimestamp(stat.st_mtime),
                size_bytes=stat.st_size,
            )
        )

    return sorted(entries, key=lambda entry: entry.modified_at, reverse=True)


def load_saved_project(name: str) -> bytes:
    ensure_workspace()
    path = PROJECTS_DIR / Path(name).name
    return path.read_bytes()


def load_version(project_name: str, version_name: str) -> bytes:
    ensure_workspace()
    project_slug = Path(project_name).name.removesuffix(".docugen.json")
    path = VERSIONS_DIR / project_slug / Path(version_name).name
    return path.read_bytes()


def delete_saved_project(name: str) -> None:
    ensure_workspace()
    path = PROJECTS_DIR / Path(name).name
    if path.exists():
        path.unlink()
