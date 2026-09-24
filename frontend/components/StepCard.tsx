"use client";

import { useDroppable } from "@dnd-kit/core";
import { SortableContext, verticalListSortingStrategy } from "@dnd-kit/sortable";
import { Copy, Plus, Trash2 } from "lucide-react";
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

const BLOCK_OPTIONS: Array<[BlockType, string]> = [
  ["text", "Texto"],
  ["image", "Imagen"],
  ["checklist", "Checklist"],
  ["table", "Tabla"],
  ["note", "Aviso"],
  ["divider", "Separador"],
  ["pagebreak", "Salto de página"],
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
    const index = step.blocks.findIndex((block) => block.id === blockId);
    if (index < 0) return;
    const source = step.blocks[index];
    const clone = structuredClone(source);
    clone.id = crypto.randomUUID().replaceAll("-", "");
    clone.annotations = clone.annotations.map((annotation) => ({
      ...annotation,
      id: crypto.randomUUID().replaceAll("-", ""),
    }));
    const blocks = [...step.blocks];
    blocks.splice(index + 1, 0, clone);
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
        <div className="step-number">{index + 1}</div>
        <input
          className="step-title"
          value={step.title}
          onChange={(event) =>
            onStepChange({ ...step, title: event.target.value })
          }
          placeholder="Título del paso"
        />
        <button className="icon-button" onClick={onDuplicate} title="Duplicar paso">
          <Copy size={16} />
        </button>
        <button className="icon-button" onClick={onDelete} title="Eliminar paso">
          <Trash2 size={16} />
        </button>
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
          <div className="empty-drop">Arrastra un bloque aquí</div>
        )}
      </div>

      <div className="add-block-row">
        <Plus size={15} />
        {BLOCK_OPTIONS.map(([type, label]) => (
          <button key={type} onClick={() => addBlock(type)}>
            {label}
          </button>
        ))}
      </div>
    </section>
  );
}
