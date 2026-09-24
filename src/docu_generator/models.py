from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


BlockType = Literal[
    "text",
    "image",
    "checklist",
    "note",
    "divider",
    "table",
    "pagebreak",
]
CalloutVariant = Literal["info", "tip", "warning", "success"]
ImageWidth = Literal["small", "medium", "large", "full"]
Alignment = Literal["left", "center", "right"]
DocumentStatus = Literal["Borrador", "En revisión", "Publicado", "Archivado"]
AnnotationType = Literal["rect", "arrow", "number", "blur"]


class ImageCrop(BaseModel):
    x: float = 0
    y: float = 0
    width: float = 1
    height: float = 1


class ImageAnnotation(BaseModel):
    id: str
    type: AnnotationType
    x: float = 0
    y: float = 0
    width: float = 0
    height: float = 0
    x2: float = 0
    y2: float = 0
    label: str = ""
    color: str = "#00B8A9"


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
    image_width: ImageWidth = "large"
    align: Alignment = "center"
    annotations: list[ImageAnnotation] = Field(default_factory=list)
    crop: ImageCrop | None = None


class GuideSection(BaseModel):
    title: str
    blocks: list[GuideBlock] = Field(default_factory=list)

    # Legacy fields remain supported for the old AI/fallback pipeline.
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

    document_type: str = "Guía"
    version: str = "1.0"
    status: DocumentStatus = "Borrador"
    author: str = ""
    updated_at: str = ""
    show_cover: bool = True
    show_toc: bool = True


class ReviewReport(BaseModel):
    issues: list[str] = Field(default_factory=list)
