"use client";

import { useDroppable } from "@dnd-kit/core";
import { SortableContext, verticalListSortingStrategy } from "@dnd-kit/sortable";
import {
  CheckSquare2,
  Copy,
  FileDown,
  Image as ImageIcon,
  ListPlus,
  MessageSquareText,
  Minus,
  Plus,
  Table2,
  Trash2,
  Type,
} from "lucide-react";
import type { Block, BlockType, Step } from "@/lib/types";
import SortableBlock from "./SortableBlock";

type Props = {
  step: Step;
  index: number;
  onStepChange: (step: Step) => void;
  onDelete: () => void;
  onDuplicate: () => void;
  onAnnotate: (blockId: string) => void;
};

const BLOCK_OPTIONS: Array<{
  type: BlockType;
  label: string;
  icon: typeof Type;
}> = [
  { type: "text", label: "Texto", icon: Type },
  { type: "image", label: "Imagen", icon: ImageIcon },
  { type: "checklist", label: "Checklist", icon: CheckSquare2 },
  { type: "table", label: "Tabla", icon: Table2 },
  { type: "note", label: "Aviso", icon: MessageSquareText },
  { type: "divider", label: "Separador", icon: Minus },
  { type: "pagebreak", label: "Salto", icon: FileDown },
];

export default function StepCard({
  step,
  index,
  onStepChange,
  onDelete,
  onDuplicate,
  onAnnotate,
}: Props) {
  const { setNodeRef, isOver } = useDroppable({
    id: `step:${step.id}`,
    data: { type: "step", stepId: step.id },
  });

  const patchBlock = (blockId: string, patch: Partial<Block>) => {
    onStepChange({
      ...step,
      blocks: step.blocks.map((block) =>
        block.id === blockId ? { ...block, ...patch } : block,
      ),
    });
  };

  const deleteBlock = (blockId: string) => {
    onStepChange({
      ...step,
      blocks: step.blocks.filter((block) => block.id !== blockId),
    });
  };

  const duplicateBlock = (blockId: string) => {
    const blockIndex = step.blocks.findIndex((block) => block.id === blockId);
    if (blockIndex < 0) return;

    const clone = structuredClone(step.blocks[blockIndex]);
    clone.id = crypto.randomUUID().replaceAll("-", "");
    clone.annotations = clone.annotations.map((annotation) => ({
      ...annotation,
      id: crypto.randomUUID().replaceAll("-", ""),
    }));

    const blocks = [...step.blocks];
    blocks.splice(blockIndex + 1, 0, clone);
    onStepChange({ ...step, blocks });
  };

  const addBlock = (type: BlockType) => {
    const id = crypto.randomUUID().replaceAll("-", "");
    const block: Block = {
      id,
      type,
      text: "",
      items: "",
      image_name: null,
      image_caption: "",
      image_mime: null,
      image_base64: null,
      label: type === "note" ? "Consejo" : "",
      variant: type === "note" ? "tip" : "info",
      image_width: "large",
      align: "center",
      annotations: [],
      crop: null,
    };
    onStepChange({ ...step, blocks: [...step.blocks, block] });
  };

  return (
    <section className="step-card">
      <header className="step-header">
        <div className="step-kicker">
          <span className="step-number">{String(index + 1).padStart(2, "0")}</span>
          <span>Paso</span>
        </div>

        <input
          className="step-title"
          value={step.title}
          onChange={(event) =>
            onStepChange({ ...step, title: event.target.value })
          }
          placeholder="Ponle un nombre claro a este paso…"
        />

        <div className="step-actions">
          <button className="icon-button" onClick={onDuplicate} title="Duplicar paso">
            <Copy size={16} />
          </button>
          <button
            className="icon-button danger-hover"
            onClick={onDelete}
            title="Eliminar paso"
          >
            <Trash2 size={16} />
          </button>
        </div>
      </header>

      <div
        ref={setNodeRef}
        className={`step-dropzone ${isOver ? "is-over" : ""}`}
      >
        <SortableContext
          items={step.blocks.map((block) => block.id)}
          strategy={verticalListSortingStrategy}
        >
          {step.blocks.map((block) => (
            <SortableBlock
              key={block.id}
              block={block}
              stepId={step.id}
              onUpdate={(patch) => patchBlock(block.id, patch)}
              onDelete={() => deleteBlock(block.id)}
              onDuplicate={() => duplicateBlock(block.id)}
              onAnnotate={() => onAnnotate(block.id)}
            />
          ))}
        </SortableContext>

        {step.blocks.length === 0 && (
          <div className="empty-drop">
            <ListPlus size={22} />
            <strong>Este paso está vacío</strong>
            <span>Añade un bloque o arrastra uno desde otro paso.</span>
          </div>
        )}
      </div>

      <div className="block-palette">
        <div className="block-palette-label">
          <Plus size={14} />
          Añadir
        </div>
        {BLOCK_OPTIONS.map(({ type, label, icon: Icon }) => (
          <button key={type} onClick={() => addBlock(type)} title={label}>
            <Icon size={14} />
            <span>{label}</span>
          </button>
        ))}
      </div>
    </section>
  );
}
