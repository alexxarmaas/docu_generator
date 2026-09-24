import type { Block, BlockType, Project, Step } from "./types";

export function uid() {
  return crypto.randomUUID().replaceAll("-", "");
}

export function createBlock(type: BlockType = "text"): Block {
  const notePreset =
    type === "note"
      ? { label: "Consejo", variant: "tip" as const }
      : { label: "", variant: "info" as const };

  return {
    id: uid(),
    type,
    text: "",
    items: "",
    image_name: null,
    image_caption: "",
    image_mime: null,
    image_base64: null,
    label: notePreset.label,
    variant: notePreset.variant,
    image_width: "large",
    align: "center",
    annotations: [],
    crop: null,
  };
}

export function createStep(title = ""): Step {
  return {
    id: uid(),
    title,
    blocks: [createBlock("text")],
  };
}

export function createProject(): Project {
  return {
    version: 4,
    title: "",
    introduction: "",
    closing_note: "",
    metadata: {
      document_type: "Guía",
      version_label: "1.0",
      status: "Borrador",
      author: "",
      updated_at: "",
      show_cover: true,
      show_toc: true,
    },
    steps: [createStep()],
  };
}

export function cloneBlock(block: Block): Block {
  return {
    ...structuredClone(block),
    id: uid(),
    annotations: block.annotations.map((annotation) => ({
      ...annotation,
      id: uid(),
    })),
  };
}

export function dataUrl(block: Block) {
  if (!block.image_base64) return "";
  return `data:${block.image_mime || "image/png"};base64,${block.image_base64}`;
}
