"use client";

import { CSS } from "@dnd-kit/utilities";
import { useSortable } from "@dnd-kit/sortable";
import {
  Copy,
  GripVertical,
  Image as ImageIcon,
  PencilRuler,
  Trash2,
} from "lucide-react";
import type { Block } from "@/lib/types";
import { dataUrl } from "@/lib/project";

type Props = {
  block: Block;
  stepId: string;
  onUpdate: (patch: Partial<Block>) => void;
  onDelete: () => void;
  onDuplicate: () => void;
  onAnnotate: () => void;
};

export default function SortableBlock({
  block,
  stepId,
  onUpdate,
  onDelete,
  onDuplicate,
  onAnnotate,
}: Props) {
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

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
    opacity: isDragging ? 0.45 : 1,
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

  const imageUrl = dataUrl(block);

  return (
    <article ref={setNodeRef} style={style} className="block-card">
      <div className="block-head">
        <button
          className="drag-handle"
          {...attributes}
          {...listeners}
          aria-label="Arrastrar bloque"
          title="Arrastrar bloque"
        >
          <GripVertical size={17} />
        </button>
        <span className="block-type">{labelForBlock(block)}</span>
        <div className="block-actions">
          <button onClick={onDuplicate} title="Duplicar">
            <Copy size={15} />
          </button>
          <button onClick={onDelete} title="Eliminar">
            <Trash2 size={15} />
          </button>
        </div>
      </div>

      {block.type === "text" && (
        <textarea
          className="field textarea"
          value={block.text}
          onChange={(event) => onUpdate({ text: event.target.value })}
          placeholder="Escribe la explicación…"
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
            className="field textarea"
            value={block.text}
            onChange={(event) => onUpdate({ text: event.target.value })}
            placeholder="Contenido del aviso…"
            rows={4}
          />
        </>
      )}

      {block.type === "checklist" && (
        <textarea
          className="field textarea"
          value={block.items}
          onChange={(event) => onUpdate({ items: event.target.value })}
          placeholder={"Un elemento por línea\nCantidad correcta\nPrecio correcto"}
          rows={5}
        />
      )}

      {block.type === "table" && (
        <textarea
          className="field textarea mono"
          value={block.items}
          onChange={(event) => onUpdate({ items: event.target.value })}
          placeholder={"Campo | Valor\nProveedor | ACME\nEstado | Correcto"}
          rows={6}
        />
      )}

      {block.type === "image" && (
        <div className="image-editor">
          {!imageUrl ? (
            <label className="image-drop">
              <ImageIcon size={24} />
              <strong>Añadir captura</strong>
              <span>PNG, JPG, JPEG o WebP</span>
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
                {/* eslint-disable-next-line @next/next/no-img-element */}
                <img src={imageUrl} alt={block.image_caption || "Captura"} />
                {(block.annotations.length > 0 || block.crop) && (
                  <span className="annotation-badge">
                    {block.annotations.length} anot. {block.crop ? "· recorte" : ""}
                  </span>
                )}
              </div>

              <div className="image-buttons">
                <button className="button secondary" onClick={onAnnotate}>
                  <PencilRuler size={16} />
                  Anotar captura
                </button>
                <label className="button ghost">
                  Reemplazar
                  <input
                    type="file"
                    accept="image/png,image/jpeg,image/webp"
                    onChange={(event) => loadImage(event.target.files?.[0])}
                    hidden
                  />
                </label>
              </div>

              <input
                className="field"
                value={block.image_caption}
                onChange={(event) =>
                  onUpdate({ image_caption: event.target.value })
                }
                placeholder="Pie de imagen"
              />

              <div className="field-grid">
                <select
                  className="field"
                  value={block.image_width}
                  onChange={(event) =>
                    onUpdate({
                      image_width: event.target.value as Block["image_width"],
                    })
                  }
                >
                  <option value="small">Pequeña</option>
                  <option value="medium">Mediana</option>
                  <option value="large">Grande</option>
                  <option value="full">Ancho completo</option>
                </select>
                <select
                  className="field"
                  value={block.align}
                  onChange={(event) =>
                    onUpdate({ align: event.target.value as Block["align"] })
                  }
                >
                  <option value="left">Izquierda</option>
                  <option value="center">Centro</option>
                  <option value="right">Derecha</option>
                </select>
              </div>
            </>
          )}
        </div>
      )}

      {block.type === "divider" && <hr className="preview-divider" />}

      {block.type === "pagebreak" && (
        <div className="pagebreak-block">SALTO DE PÁGINA</div>
      )}
    </article>
  );
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
  if (block.variant === "success") return "Resultado";
  return "Información";
}
