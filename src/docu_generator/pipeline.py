from __future__ import annotations

from docu_generator.services.analyzer import analyze_images
from docu_generator.services.generator import generate_guide
from docu_generator.services.reviewer import review_guide


class DocumentationPipeline:
    def __init__(self, provider, profile: dict):
        self.provider = provider
        self.profile = profile

    def analyze_images(self, images: list[dict], instructions: str):
        return analyze_images(
            provider=self.provider,
            images=images,
            instructions=instructions,
        )

    def generate_guide(self, title: str, instructions: str, audience: str, evidences):
        return generate_guide(
            provider=self.provider,
            profile=self.profile,
            title=title,
            instructions=instructions,
            audience=audience,
            evidences=evidences,
        )

    def review_guide(self, guide, evidences):
        return review_guide(
            provider=self.provider,
            guide=guide,
            evidences=evidences,
        )
