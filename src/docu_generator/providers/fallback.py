from __future__ import annotations

from .base import Provider


class FallbackProvider(Provider):
    ai_enabled = False

    def complete(self, prompt: str, images: list[dict] | None = None) -> str:
        raise RuntimeError("El proveedor fallback no realiza llamadas a modelos.")
