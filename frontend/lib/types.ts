export type BlockType =
  | "text"
  | "image"
  | "checklist"
  | "note"
  | "divider"
  | "table"
  | "pagebreak";

export type AnnotationType = "rect" | "arrow" | "number" | "blur";

export type Annotation = {
  id: string;
  type: AnnotationType;
  x: number;
  y: number;
  width: number;
  height: number;
  x2: number;
  y2: number;
  label: string;
  color: string;
};

export type Crop = {
  x: number;
  y: number;
  width: number;
  height: number;
};

export type Block = {
  id: string;
  type: BlockType;
  text: string;
  items: string;
  image_name: string | null;
  image_caption: string;
  image_mime: string | null;
  image_base64: string | null;
  label: string;
  variant: "info" | "tip" | "warning" | "success";
  image_width: "small" | "medium" | "large" | "full";
  align: "left" | "center" | "right";
  annotations: Annotation[];
  crop: Crop | null;
};

export type Step = {
  id: string;
  title: string;
  blocks: Block[];
};

export type ProjectMetadata = {
  document_type: string;
  version_label: string;
  status: "Borrador" | "En revisión" | "Publicado" | "Archivado";
  author: string;
  updated_at: string;
  show_cover: boolean;
  show_toc: boolean;
};

export type Project = {
  version: 4;
  title: string;
  introduction: string;
  closing_note: string;
  metadata: ProjectMetadata;
  steps: Step[];
};

export type ValidationIssue = {
  level: "error" | "warning" | "info";
  message: string;
};

export type ProjectEntry = {
  name: string;
  modified_at: string;
  size_bytes: number;
};
