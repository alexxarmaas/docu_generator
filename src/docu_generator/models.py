from __future__ import annotations

from pydantic import BaseModel, Field


class ScreenEvidence(BaseModel):
    image_name: str
    screen_name: str = "Pantalla"
    visible_elements: list[str] = Field(default_factory=list)
    supported_actions: list[str] = Field(default_factory=list)
    uncertainties: list[str] = Field(default_factory=list)


class GuideSection(BaseModel):
    title: str
    body: str
    image_name: str | None = None
    image_caption: str = ""
    checklist: list[str] = Field(default_factory=list)
    note: str = ""


class GuideDraft(BaseModel):
    title: str
    introduction: str = ""
    sections: list[GuideSection] = Field(default_factory=list)
    closing_note: str = ""


class ReviewReport(BaseModel):
    issues: list[str] = Field(default_factory=list)
