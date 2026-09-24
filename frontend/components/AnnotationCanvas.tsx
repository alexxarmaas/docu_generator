"use client";

import {
  Arrow as ArrowShape,
  Circle,
  Group,
  Image as KonvaImage,
  Layer,
  Rect,
  Stage,
  Text,
} from "react-konva";
import {
  ArrowUpRight,
  Crop as CropIcon,
  EyeOff,
  Hash,
  MousePointer2,
  Square,
  Trash2,
} from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import type { KonvaEventObject } from "konva/lib/Node";
import type { Annotation, AnnotationType, Crop } from "@/lib/types";
import { uid } from "@/lib/project";

type Tool = "select" | AnnotationType | "crop";

type Props = {
  imageUrl: string;
  annotations: Annotation[];
  crop: Crop | null;
  onAnnotationsChange: (annotations: Annotation[]) => void;
  onCropChange: (crop: Crop | null) => void;
};

const COLORS = ["#00B8A9", "#092D54", "#E24A4A", "#F2A93B"];

export default function AnnotationCanvas({
  imageUrl,
  annotations,
  crop,
  onAnnotationsChange,
  onCropChange,
}: Props) {
  const [image, setImage] = useState<HTMLImageElement | null>(null);
  const [tool, setTool] = useState<Tool>("select");
  const [color, setColor] = useState(COLORS[0]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [start, setStart] = useState<{ x: number; y: number } | null>(null);
  const [draft, setDraft] = useState<Annotation | null>(null);
  const [draftCrop, setDraftCrop] = useState<Crop | null>(null);

  useEffect(() => {
    const next = new window.Image();
    next.onload = () => setImage(next);
    next.src = imageUrl;
  }, [imageUrl]);

  const size = useMemo(() => {
    if (!image) return { width: 820, height: 500 };
    const maxWidth = 820;
    const maxHeight = 560;
    const scale = Math.min(maxWidth / image.width, maxHeight / image.height, 1);
    return {
      width: Math.max(240, Math.round(image.width * scale)),
      height: Math.max(180, Math.round(image.height * scale)),
    };
  }, [image]);

  const normalized = (stageX: number, stageY: number) => ({
    x: Math.max(0, Math.min(1, stageX / size.width)),
    y: Math.max(0, Math.min(1, stageY / size.height)),
  });

  const pointer = (event: KonvaEventObject<MouseEvent>) => {
    const position = event.target.getStage()?.getPointerPosition();
    return position ? normalized(position.x, position.y) : null;
  };

  const replaceAnnotation = (next: Annotation) => {
    onAnnotationsChange(
      annotations.map((item) => (item.id === next.id ? next : item)),
    );
  };

  const handleMouseDown = (event: KonvaEventObject<MouseEvent>) => {
    if (tool === "select") return;
    const point = pointer(event);
    if (!point) return;

    if (tool === "number") {
      const nextNumber =
        annotations.filter((item) => item.type === "number").length + 1;
      onAnnotationsChange([
        ...annotations,
        {
          id: uid(),
          type: "number",
          x: point.x,
          y: point.y,
          width: 0,
          height: 0,
          x2: point.x,
          y2: point.y,
          label: String(nextNumber),
          color,
        },
      ]);
      return;
    }

    setStart(point);

    if (tool === "crop") {
      setDraftCrop({ x: point.x, y: point.y, width: 0, height: 0 });
      return;
    }

    setDraft({
      id: uid(),
      type: tool,
      x: point.x,
      y: point.y,
      width: 0,
      height: 0,
      x2: point.x,
      y2: point.y,
      label: "",
      color,
    });
  };

  const handleMouseMove = (event: KonvaEventObject<MouseEvent>) => {
    if (!start) return;
    const point = pointer(event);
    if (!point) return;

    if (tool === "crop") {
      setDraftCrop({
        x: Math.min(start.x, point.x),
        y: Math.min(start.y, point.y),
        width: Math.abs(point.x - start.x),
        height: Math.abs(point.y - start.y),
      });
      return;
    }

    if (!draft) return;

    if (draft.type === "arrow") {
      setDraft({ ...draft, x2: point.x, y2: point.y });
    } else {
      setDraft({
        ...draft,
        x: Math.min(start.x, point.x),
        y: Math.min(start.y, point.y),
        width: Math.abs(point.x - start.x),
        height: Math.abs(point.y - start.y),
      });
    }
  };

  const handleMouseUp = () => {
    if (tool === "crop" && draftCrop) {
      if (draftCrop.width > 0.01 && draftCrop.height > 0.01) {
        onCropChange(draftCrop);
      }
      setDraftCrop(null);
    } else if (draft) {
      const meaningful =
        draft.type === "arrow"
          ? Math.abs(draft.x2 - draft.x) + Math.abs(draft.y2 - draft.y) > 0.02
          : draft.width + draft.height > 0.02;
      if (meaningful) onAnnotationsChange([...annotations, draft]);
      setDraft(null);
    }

    setStart(null);
  };

  const removeSelected = () => {
    if (!selectedId) return;
    onAnnotationsChange(annotations.filter((item) => item.id !== selectedId));
    setSelectedId(null);
  };

  const renderAnnotation = (annotation: Annotation, preview = false) => {
    const selected = annotation.id === selectedId;
    const draggable = tool === "select" && !preview;

    if (annotation.type === "arrow") {
      return (
        <ArrowShape
          key={annotation.id}
          x={annotation.x * size.width}
          y={annotation.y * size.height}
          points={[
            0,
            0,
            (annotation.x2 - annotation.x) * size.width,
            (annotation.y2 - annotation.y) * size.height,
          ]}
          stroke={annotation.color}
          fill={annotation.color}
          strokeWidth={selected ? 5 : 4}
          pointerLength={14}
          pointerWidth={12}
          draggable={draggable}
          onClick={() => setSelectedId(annotation.id)}
          onTap={() => setSelectedId(annotation.id)}
          onDragEnd={(event) => {
            const dx = event.target.x() / size.width - annotation.x;
            const dy = event.target.y() / size.height - annotation.y;
            replaceAnnotation({
              ...annotation,
              x: annotation.x + dx,
              y: annotation.y + dy,
              x2: annotation.x2 + dx,
              y2: annotation.y2 + dy,
            });
          }}
        />
      );
    }

    if (annotation.type === "number") {
      const radius = 18;
      return (
        <Group
          key={annotation.id}
          x={annotation.x * size.width}
          y={annotation.y * size.height}
          draggable={draggable}
          onClick={() => setSelectedId(annotation.id)}
          onTap={() => setSelectedId(annotation.id)}
          onDragEnd={(event) =>
            replaceAnnotation({
              ...annotation,
              x: event.target.x() / size.width,
              y: event.target.y() / size.height,
            })
          }
        >
          <Circle
            radius={radius}
            fill={annotation.color}
            stroke={selected ? "#ffffff" : annotation.color}
            strokeWidth={selected ? 3 : 1}
          />
          <Text
            text={annotation.label || "1"}
            fill="#ffffff"
            fontStyle="bold"
            fontSize={17}
            width={radius * 2}
            height={radius * 2}
            x={-radius}
            y={-radius + 7}
            align="center"
          />
        </Group>
      );
    }

    return (
      <Rect
        key={annotation.id}
        x={annotation.x * size.width}
        y={annotation.y * size.height}
        width={annotation.width * size.width}
        height={annotation.height * size.height}
        stroke={annotation.color}
        strokeWidth={selected ? 4 : 3}
        dash={annotation.type === "blur" ? [8, 5] : undefined}
        fill={annotation.type === "blur" ? "rgba(9,45,84,.20)" : undefined}
        cornerRadius={6}
        draggable={draggable}
        onClick={() => setSelectedId(annotation.id)}
        onTap={() => setSelectedId(annotation.id)}
        onDragEnd={(event) =>
          replaceAnnotation({
            ...annotation,
            x: event.target.x() / size.width,
            y: event.target.y() / size.height,
          })
        }
      />
    );
  };

  return (
    <div className="annotation-workspace">
      <div className="annotation-toolbar">
        {[
          ["select", MousePointer2, "Seleccionar"],
          ["rect", Square, "Rectángulo"],
          ["arrow", ArrowUpRight, "Flecha"],
          ["number", Hash, "Número"],
          ["blur", EyeOff, "Blur"],
          ["crop", CropIcon, "Recortar"],
        ].map(([value, Icon, label]) => (
          <button
            key={String(value)}
            className={`tool-button ${tool === value ? "active" : ""}`}
            onClick={() => setTool(value as Tool)}
            title={String(label)}
          >
            <Icon size={17} />
            <span>{String(label)}</span>
          </button>
        ))}

        <div className="tool-separator" />

        <div className="color-row">
          {COLORS.map((option) => (
            <button
              key={option}
              className={`color-swatch ${color === option ? "active" : ""}`}
              style={{ background: option }}
              onClick={() => setColor(option)}
              aria-label={`Color ${option}`}
            />
          ))}
        </div>

        <button
          className="tool-button danger"
          onClick={removeSelected}
          disabled={!selectedId}
        >
          <Trash2 size={17} />
          <span>Eliminar</span>
        </button>

        {crop && (
          <button className="tool-button" onClick={() => onCropChange(null)}>
            <CropIcon size={17} />
            <span>Quitar recorte</span>
          </button>
        )}
      </div>

      <div className="canvas-shell">
        <Stage
          width={size.width}
          height={size.height}
          onMouseDown={handleMouseDown}
          onMouseMove={handleMouseMove}
          onMouseUp={handleMouseUp}
          onClick={(event) => {
            if (event.target === event.target.getStage()) setSelectedId(null);
          }}
        >
          <Layer>
            {image && (
              <KonvaImage
                image={image}
                width={size.width}
                height={size.height}
              />
            )}

            {annotations.map((annotation) => renderAnnotation(annotation))}
            {draft && renderAnnotation(draft, true)}

            {crop && (
              <Rect
                x={crop.x * size.width}
                y={crop.y * size.height}
                width={crop.width * size.width}
                height={crop.height * size.height}
                stroke="#ffffff"
                strokeWidth={2}
                dash={[10, 6]}
              />
            )}

            {draftCrop && (
              <Rect
                x={draftCrop.x * size.width}
                y={draftCrop.y * size.height}
                width={draftCrop.width * size.width}
                height={draftCrop.height * size.height}
                stroke="#00B8A9"
                strokeWidth={3}
                dash={[10, 6]}
                fill="rgba(0,184,169,.08)"
              />
            )}
          </Layer>
        </Stage>
      </div>

      <div className="annotation-status">
        <span>{annotations.length} anotación(es)</span>
        <span>{crop ? "Recorte activo" : "Sin recorte"}</span>
        <span>
          {tool === "select"
            ? "Arrastra las anotaciones para recolocarlas."
            : "Arrastra sobre la captura para crear el elemento."}
        </span>
      </div>
    </div>
  );
}
