from __future__ import annotations

from pathlib import Path

import yaml


def _find_project_root() -> Path:
    candidates = [
        Path(__file__).resolve().parents[2],
        Path.cwd(),
        *Path.cwd().parents,
    ]

    for candidate in candidates:
        if (candidate / "profiles").exists() and (candidate / "prompts").exists():
            return candidate

    return Path(__file__).resolve().parents[2]


PROJECT_ROOT = _find_project_root()


def load_profile(name: str) -> dict:
    profile_dir = PROJECT_ROOT / "profiles" / name
    config_path = profile_dir / "profile.yaml"
    css_path = profile_dir / "style.css"

    if not config_path.exists():
        raise FileNotFoundError(
            f"No existe el perfil: {name}. "
            f"Ruta esperada: {config_path}. "
            "Comprueba que has actualizado el repositorio con git pull."
        )

    with config_path.open("r", encoding="utf-8") as handle:
        profile = yaml.safe_load(handle) or {}

    profile["slug"] = name
    profile["css"] = css_path.read_text(encoding="utf-8") if css_path.exists() else ""
    return profile


def read_prompt(name: str) -> str:
    path = PROJECT_ROOT / "prompts" / f"{name}.md"
    if not path.exists():
        raise FileNotFoundError(
            f"No existe el prompt: {name}. Ruta esperada: {path}"
        )
    return path.read_text(encoding="utf-8")
