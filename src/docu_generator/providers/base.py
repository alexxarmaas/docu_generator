from __future__ import annotations

from abc import ABC, abstractmethod


class Provider(ABC):
    ai_enabled: bool = False

    @abstractmethod
    def complete(self, prompt: str, images: list[dict] | None = None) -> str:
        raise NotImplementedError
