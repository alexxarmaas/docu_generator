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
        {block.annotations
          .filter((annotation) => annotation.type === "arrow")
          .map((annotation) => {
            const start = mapPoint(annotation.x, annotation.y, crop);
            const end = mapPoint(annotation.x2, annotation.y2, crop);
            const head = arrowHead(start.x, start.y, end.x, end.y);
            return (
              <g key={annotation.id}>
                <line
                  x1={start.x}
                  y1={start.y}
                  x2={end.x}
                  y2={end.y}
                  stroke={annotation.color}
                  strokeWidth="1.4"
                  vectorEffect="non-scaling-stroke"
                />
                <polygon
                  points={head}
                  fill={annotation.color}
                />
              </g>
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

function arrowHead(x1: number, y1: number, x2: number, y2: number) {
  const angle = Math.atan2(y2 - y1, x2 - x1);
  const size = 3.2;
  const spread = Math.PI / 6;

  const leftX = x2 - size * Math.cos(angle - spread);
  const leftY = y2 - size * Math.sin(angle - spread);
  const rightX = x2 - size * Math.cos(angle + spread);
  const rightY = y2 - size * Math.sin(angle + spread);

  return `${x2},${y2} ${leftX},${leftY} ${rightX},${rightY}`;
}

function mapPoint(x: number, y: number, crop: Crop) {
  return {
    x: ((x - crop.x) / crop.width) * 100,
    y: ((y - crop.y) / crop.height) * 100,
  };
}
