from __future__ import annotations

import base64

from openai import OpenAI

from .base import Provider


class OpenAIProvider(Provider):
    ai_enabled = True

    def __init__(self, api_key: str, model: str):
        self.client = OpenAI(api_key=api_key)
        self.model = model

    def complete(self, prompt: str, images: list[dict] | None = None) -> str:
        content: list[dict] = [{"type": "input_text", "text": prompt}]

        for image in images or []:
            encoded = base64.b64encode(image["bytes"]).decode("ascii")
            data_url = f'data:{image["mime_type"]};base64,{encoded}'
            content.append(
                {
                    "type": "input_image",
                    "image_url": data_url,
                }
            )

        response = self.client.responses.create(
            model=self.model,
            input=[
                {
                    "role": "user",
                    "content": content,
                }
            ],
        )
        return response.output_text
