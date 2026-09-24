"use client";

import { useMemo, useState } from "react";
import type { CSSProperties } from "react";
import type { Annotation, Block, Crop } from "@/lib/types";
import { dataUrl } from "@/lib/project";

type Props = {
  block: Block;
  className?: string;
};

type Dimensions = {
  width: number;
  height: number;
};

const FULL_CROP: Crop = {
  x: 0,
  y: 0,
  width: 1,
  height: 1,
};

export default function AnnotatedImagePreview({ block, className = "" }: Props) {
  const [dimensions, setDimensions] = useState<Dimensions | null>(null);
  const crop = block.crop || FULL_CROP;
  const source = dataUrl(block);

  const aspectRatio = useMemo(() => {
    if (!dimensions) return undefined;
    return (dimensions.width * crop.width) / (dimensions.height * crop.height);
  }, [crop.height, crop.width, dimensions]);

  if (!source) return null;

  const imageStyle: CSSProperties = {
    position: "absolute",
    width: `${100 / crop.width}%`,
    maxWidth: "none",
    height: "auto",
    left: `${-(crop.x / crop.width) * 100}%`,
    top: `${-(crop.y / crop.height) * 100}%`,
  };

  return (
    <div
      className={`annotated-preview ${className}`}
      style={aspectRatio ? { aspectRatio } : undefined}
    >
      {/* eslint-disable-next-line @next/next/no-img-element */}
      <img
        src={source}
        alt={block.image_caption || "Captura"}
        style={imageStyle}
        onLoad={(event) => {
          setDimensions({
            width: event.currentTarget.naturalWidth,
            height: event.currentTarget.naturalHeight,
          });
        }}
      />

      <svg
        className="annotation-svg"
        viewBox="0 0 100 100"
        preserveAspectRatio="none"
        aria-hidden="true"
      >
        <defs>
          <marker
            id={`arrow-${block.id}`}
            markerWidth="7"
            markerHeight="7"
            refX="5.2"
            refY="3.5"
            orient="auto"
            markerUnits="strokeWidth"
          >
            <path d="M0,0 L0,7 L6,3.5 z" fill="context-stroke" />
          </marker>
        </defs>

        {block.annotations
          .filter((annotation) => annotation.type === "arrow")
          .map((annotation) => {
            const start = mapPoint(annotation.x, annotation.y, crop);
            const end = mapPoint(annotation.x2, annotation.y2, crop);
            return (
              <line
                key={annotation.id}
                x1={start.x}
                y1={start.y}
                x2={end.x}
                y2={end.y}
                stroke={annotation.color}
                strokeWidth="1.4"
                vectorEffect="non-scaling-stroke"
                markerEnd={`url(#arrow-${block.id})`}
              />
            );
          })}
      </svg>

      {block.annotations
        .filter((annotation) => annotation.type !== "arrow")
        .map((annotation) => (
          <OverlayAnnotation
            key={annotation.id}
            annotation={annotation}
            crop={crop}
          />
        ))}
    </div>
  );
}

function OverlayAnnotation({
  annotation,
  crop,
}: {
  annotation: Annotation;
  crop: Crop;
}) {
  const point = mapPoint(annotation.x, annotation.y, crop);

  if (annotation.type === "number") {
    return (
      <span
        className="live-number"
        style={{
          left: `${point.x}%`,
          top: `${point.y}%`,
          background: annotation.color,
        }}
      >
        {annotation.label || "1"}
      </span>
    );
  }

  const width = (annotation.width / crop.width) * 100;
  const height = (annotation.height / crop.height) * 100;

  if (annotation.type === "blur") {
    return (
      <span
        className="live-blur"
        style={{
          left: `${point.x}%`,
          top: `${point.y}%`,
          width: `${width}%`,
          height: `${height}%`,
          borderColor: annotation.color,
        }}
      />
    );
  }

  return (
    <span
      className="live-rect"
      style={{
        left: `${point.x}%`,
        top: `${point.y}%`,
        width: `${width}%`,
        height: `${height}%`,
        borderColor: annotation.color,
      }}
    />
  );
}

function mapPoint(x: number, y: number, crop: Crop) {
  return {
    x: ((x - crop.x) / crop.width) * 100,
    y: ((y - crop.y) / crop.height) * 100,
  };
}
