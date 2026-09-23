from __future__ import annotations

import os

from .fallback import FallbackProvider
from .openai_provider import OpenAIProvider


def build_provider(model: str):
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if api_key:
        return OpenAIProvider(api_key=api_key, model=model)
    return FallbackProvider()
