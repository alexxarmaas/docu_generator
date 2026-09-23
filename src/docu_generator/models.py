from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


BlockType = Literal["text", "image", "checklist", "note", "divider"]
CalloutVariant = Literal["info", "tip", "warning", "success"]


class ScreenEvidence(BaseModel):
    image_name: str
    screen_name: str = "Pantalla"
    visible_elements: list[str] = Field(default_factory=list)
    supported_actions: list[str] = Field(default_factory=list)
    uncertainties: list[str] = Field(default_factory=list)


class GuideBlock(BaseModel):
    type: BlockType
    text: str = ""
    items: list[str] = Field(default_factory=list)
    image_name: str | None = None
    image_caption: str = ""
    label: str = ""
    variant: CalloutVariant = "info"


class GuideSection(BaseModel):
    title: str

    # New free-form block model.
    blocks: list[GuideBlock] = Field(default_factory=list)

    # Legacy fields remain supported so the old generator/pipeline keeps working.
    body: str = ""
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
