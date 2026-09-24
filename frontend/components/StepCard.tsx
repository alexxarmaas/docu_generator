"use client";

import { useDroppable } from "@dnd-kit/core";
import { SortableContext, verticalListSortingStrategy } from "@dnd-kit/sortable";
import {
  Copy,
  ListPlus,
  Trash2,
} from "lucide-react";
import type { Block, Step } from "@/lib/types";
import BlockCommandInput from "./BlockCommandInput";
import SortableBlock from "./SortableBlock";

type Props = {
  step: Step;
  index: number;
  onStepChange: (step: Step) => void;
  onDelete: () => void;
  onDuplicate: () => void;
  onAnnotate: (blockId: string) => void;
};

type InsertPreset = {
  type: Block["type"];
  label?: string;
  variant?: Block["variant"];
  text?: string;
};

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

  const moveBlock = (blockId: string, offset: number) => {
    const blockIndex = step.blocks.findIndex((block) => block.id === blockId);
    const targetIndex = blockIndex + offset;

    if (
      blockIndex < 0 ||
      targetIndex < 0 ||
      targetIndex >= step.blocks.length
    ) {
      return;
    }

    const blocks = [...step.blocks];
    [blocks[blockIndex], blocks[targetIndex]] = [
      blocks[targetIndex],
      blocks[blockIndex],
    ];
    onStepChange({ ...step, blocks });
  };

  const addBlock = (preset: InsertPreset, index = step.blocks.length) => {
    const id = crypto.randomUUID().replaceAll("-", "");
    const block: Block = {
      id,
      type: preset.type,
      text: preset.text || "",
      items: "",
      image_name: null,
      image_caption: "",
      image_mime: null,
      image_base64: null,
      label: preset.label || (preset.type === "note" ? "Consejo" : ""),
      variant: preset.variant || (preset.type === "note" ? "tip" : "info"),
      image_width: "large",
      align: "center",
      annotations: [],
      crop: null,
    };

    const blocks = [...step.blocks];
    blocks.splice(index, 0, block);
    onStepChange({ ...step, blocks });
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
          {step.blocks.map((block, blockIndex) => (
            <SortableBlock
              key={block.id}
              block={block}
              stepId={step.id}
              canMoveUp={blockIndex > 0}
              canMoveDown={blockIndex < step.blocks.length - 1}
              onUpdate={(patch) => patchBlock(block.id, patch)}
              onDelete={() => deleteBlock(block.id)}
              onDuplicate={() => duplicateBlock(block.id)}
              onMoveUp={() => moveBlock(block.id, -1)}
              onMoveDown={() => moveBlock(block.id, 1)}
              onInsertAfter={(preset) => addBlock(preset, blockIndex + 1)}
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

      <BlockCommandInput onInsert={(preset) => addBlock(preset)} />
    </section>
  );
}
