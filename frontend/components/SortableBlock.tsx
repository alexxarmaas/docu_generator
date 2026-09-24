"use client";

import { CSS } from "@dnd-kit/utilities";
import { useSortable } from "@dnd-kit/sortable";
import {
  ArrowDown,
  ArrowUp,
  CheckSquare2,
  Copy,
  FileDown,
  GripVertical,
  Image as ImageIcon,
  MessageSquareText,
  MoreHorizontal,
  PencilRuler,
  Plus,
  Table2,
  Trash2,
  Type,
} from "lucide-react";
import { useEffect, useRef, useState } from "react";
import type { Block } from "@/lib/types";
import AnnotatedImagePreview from "./AnnotatedImagePreview";
import BlockCommandInput from "./BlockCommandInput";

type InsertPreset = {
  type: Block["type"];
  label?: string;
  variant?: Block["variant"];
  text?: string;
};

type Props = {
  block: Block;
  stepId: string;
  canMoveUp: boolean;
  canMoveDown: boolean;
  onUpdate: (patch: Partial<Block>) => void;
  onDelete: () => void;
  onDuplicate: () => void;
  onMoveUp: () => void;
  onMoveDown: () => void;
  onInsertAfter: (preset: InsertPreset) => void;
  onAnnotate: () => void;
};

export default function SortableBlock({
  block,
  stepId,
  canMoveUp,
  canMoveDown,
  onUpdate,
  onDelete,
  onDuplicate,
  onMoveUp,
  onMoveDown,
  onInsertAfter,
  onAnnotate,
}: Props) {
  const [menuOpen, setMenuOpen] = useState(false);
  const [insertOpen, setInsertOpen] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);

  const {
    attributes,
    listeners,
    setNodeRef,
    transform,
    transition,
    isDragging,
  } = useSortable({
    id: block.id,
    data: { type: "block", blockId: block.id, stepId },
  });

  useEffect(() => {
    if (!menuOpen) return;

    const close = (event: MouseEvent) => {
      if (!menuRef.current?.contains(event.target as Node)) {
        setMenuOpen(false);
        setInsertOpen(false);
      }
    };

    window.addEventListener("mousedown", close);
    return () => window.removeEventListener("mousedown", close);
  }, [menuOpen]);

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
    opacity: isDragging ? 0.28 : 1,
  };

  const loadImage = (file: File | undefined) => {
    if (!file) return;
    const reader = new FileReader();
    reader.onload = () => {
      const value = String(reader.result || "");
      const [, base64 = ""] = value.split(",", 2);
      onUpdate({
        image_name: `${block.id.slice(0, 8)}_${file.name}`,
        image_caption: block.image_caption,
        image_mime: file.type || "image/png",
        image_base64: base64,
        annotations: [],
        crop: null,
      });
    };
    reader.readAsDataURL(file);
  };

  const Icon = iconForBlock(block);

  return (
    <article
      ref={setNodeRef}
      style={style}
      className={`block-card block-${block.type} ${isDragging ? "is-dragging" : ""}`}
      onContextMenu={(event) => {
        event.preventDefault();
        setMenuOpen(true);
      }}
    >
      <div className="block-head">
        <button
          className="drag-handle"
          {...attributes}
          {...listeners}
          aria-label="Arrastrar bloque"
          title="Arrastrar bloque"
        >
          <GripVertical size={16} />
        </button>

        <div className="block-label">
          <span className="block-icon">
            <Icon size={14} />
          </span>
          <span>{labelForBlock(block)}</span>
        </div>

        <div className="block-actions" ref={menuRef}>
          <button
            onClick={() => setMenuOpen((value) => !value)}
            title="Más acciones"
            aria-expanded={menuOpen}
          >
            <MoreHorizontal size={15} />
          </button>

          {menuOpen && (
            <div className="block-context-menu">
              <button
                onClick={() => {
                  onMoveUp();
                  setMenuOpen(false);
                }}
                disabled={!canMoveUp}
              >
                <ArrowUp size={14} />
                Mover arriba
              </button>
              <button
                onClick={() => {
                  onMoveDown();
                  setMenuOpen(false);
                }}
                disabled={!canMoveDown}
              >
                <ArrowDown size={14} />
                Mover abajo
              </button>
              <button
                onClick={() => {
                  onDuplicate();
                  setMenuOpen(false);
                }}
              >
                <Copy size={14} />
                Duplicar
              </button>
              <button onClick={() => setInsertOpen((value) => !value)}>
                <Plus size={14} />
                Insertar debajo
              </button>

              {insertOpen && (
                <div className="context-insert">
                  <BlockCommandInput
                    onInsert={(preset) => {
                      onInsertAfter(preset);
                      setMenuOpen(false);
                      setInsertOpen(false);
                    }}
                  />
                </div>
              )}

              <div className="context-separator" />
              <button
                className="danger"
                onClick={() => {
                  onDelete();
                  setMenuOpen(false);
                }}
              >
                <Trash2 size={14} />
                Eliminar bloque
              </button>
            </div>
          )}
        </div>
      </div>

      <div className="block-content">
        {block.type === "text" && (
          <textarea
            className="field textarea editor-field"
            value={block.text}
            onChange={(event) => onUpdate({ text: event.target.value })}
            placeholder="Escribe una explicación clara para el usuario…"
            rows={5}
          />
        )}

        {block.type === "note" && (
          <>
            <div className="field-grid">
              <input
                className="field"
                value={block.label}
                onChange={(event) => onUpdate({ label: event.target.value })}
                placeholder="Etiqueta"
              />
              <select
                className="field"
                value={block.variant}
                onChange={(event) =>
                  onUpdate({
                    variant: event.target.value as Block["variant"],
                  })
                }
              >
                <option value="info">Información</option>
                <option value="tip">Consejo</option>
                <option value="warning">Importante</option>
                <option value="success">Resultado esperado</option>
              </select>
            </div>
            <textarea
              className="field textarea editor-field"
              value={block.text}
              onChange={(event) => onUpdate({ text: event.target.value })}
              placeholder="Escribe el contenido del aviso…"
              rows={4}
            />
          </>
        )}

        {block.type === "checklist" && (
          <textarea
            className="field textarea editor-field"
            value={block.items}
            onChange={(event) => onUpdate({ items: event.target.value })}
            placeholder={"Un elemento por línea\nCantidad correcta\nPrecio correcto"}
            rows={5}
          />
        )}

        {block.type === "table" && (
          <textarea
            className="field textarea mono editor-field"
            value={block.items}
            onChange={(event) => onUpdate({ items: event.target.value })}
            placeholder={"Campo | Valor\nProveedor | ACME\nEstado | Correcto"}
            rows={6}
          />
        )}

        {block.type === "image" && (
          <div className="image-editor">
            {!block.image_base64 ? (
              <label className="image-drop">
                <span className="image-drop-icon">
                  <ImageIcon size={22} />
                </span>
                <strong>Añadir captura</strong>
                <span>Arrastra o selecciona PNG, JPG o WebP</span>
                <input
                  type="file"
                  accept="image/png,image/jpeg,image/webp"
                  onChange={(event) => loadImage(event.target.files?.[0])}
                  hidden
                />
              </label>
            ) : (
              <>
                <div className="image-preview-shell">
                  <AnnotatedImagePreview block={block} />
                  {(block.annotations.length > 0 || block.crop) && (
                    <span className="annotation-badge">
                      {block.annotations.length} anotación(es)
                      {block.crop ? " · recorte" : ""}
                    </span>
                  )}
                </div>

                <div className="image-toolbar">
                  <button className="button secondary compact" onClick={onAnnotate}>
                    <PencilRuler size={15} />
                    Anotar
                  </button>
                  <label className="button ghost compact">
                    Reemplazar
                    <input
                      type="file"
                      accept="image/png,image/jpeg,image/webp"
                      onChange={(event) => loadImage(event.target.files?.[0])}
                      hidden
                    />
                  </label>

                  <div className="image-toolbar-spacer" />

                  <select
                    className="mini-select"
                    value={block.image_width}
                    onChange={(event) =>
                      onUpdate({
                        image_width: event.target.value as Block["image_width"],
                      })
                    }
                    aria-label="Tamaño de imagen"
                  >
                    <option value="small">S</option>
                    <option value="medium">M</option>
                    <option value="large">L</option>
                    <option value="full">Full</option>
                  </select>
                  <select
                    className="mini-select"
                    value={block.align}
                    onChange={(event) =>
                      onUpdate({ align: event.target.value as Block["align"] })
                    }
                    aria-label="Alineación de imagen"
                  >
                    <option value="left">Izq.</option>
                    <option value="center">Centro</option>
                    <option value="right">Der.</option>
                  </select>
                </div>

                <input
                  className="field image-caption-field"
                  value={block.image_caption}
                  onChange={(event) =>
                    onUpdate({ image_caption: event.target.value })
                  }
                  placeholder="Añade un pie de imagen opcional…"
                />
              </>
            )}
          </div>
        )}

        {block.type === "divider" && (
          <div className="divider-editor">
            <span />
            <small>Separador</small>
            <span />
          </div>
        )}

        {block.type === "pagebreak" && (
          <div className="pagebreak-block">
            <FileDown size={15} />
            Nueva página al exportar
          </div>
        )}
      </div>
    </article>
  );
}

function iconForBlock(block: Block) {
  if (block.type === "text") return Type;
  if (block.type === "image") return ImageIcon;
  if (block.type === "checklist") return CheckSquare2;
  if (block.type === "table") return Table2;
  if (block.type === "divider") return GripVertical;
  if (block.type === "pagebreak") return FileDown;
  return MessageSquareText;
}

function labelForBlock(block: Block) {
  if (block.type === "text") return "Texto";
  if (block.type === "image") return "Imagen";
  if (block.type === "checklist") return "Checklist";
  if (block.type === "table") return "Tabla";
  if (block.type === "divider") return "Separador";
  if (block.type === "pagebreak") return "Salto de página";
  if (block.variant === "tip") return "Consejo";
  if (block.variant === "warning") return "Importante";
  if (block.variant === "success") return "Resultado esperado";
  return "Información";
}
