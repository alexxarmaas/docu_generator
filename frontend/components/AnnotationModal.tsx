"use client";

import dynamic from "next/dynamic";
import { X } from "lucide-react";
import { useEffect, useState } from "react";
import type { Annotation, Crop } from "@/lib/types";

const AnnotationCanvas = dynamic(() => import("./AnnotationCanvas"), {
  ssr: false,
});

type Props = {
  open: boolean;
  imageUrl: string;
  annotations: Annotation[];
  crop: Crop | null;
  onClose: () => void;
  onSave: (annotations: Annotation[], crop: Crop | null) => void;
};

export default function AnnotationModal({
  open,
  imageUrl,
  annotations,
  crop,
  onClose,
  onSave,
}: Props) {
  const [draftAnnotations, setDraftAnnotations] = useState<Annotation[]>(annotations);
  const [draftCrop, setDraftCrop] = useState<Crop | null>(crop);

  useEffect(() => {
    if (open) {
      setDraftAnnotations(structuredClone(annotations));
      setDraftCrop(crop ? { ...crop } : null);
    }
  }, [open, annotations, crop]);

  if (!open) return null;

  return (
    <div className="modal-backdrop" role="dialog" aria-modal="true">
      <div className="annotation-modal">
        <div className="modal-header">
          <div>
            <span className="eyebrow">Editor visual</span>
            <h2>Anotar captura</h2>
          </div>
          <button className="icon-button" onClick={onClose} aria-label="Cerrar">
            <X size={18} />
          </button>
        </div>

        <AnnotationCanvas
          imageUrl={imageUrl}
          annotations={draftAnnotations}
          crop={draftCrop}
          onAnnotationsChange={setDraftAnnotations}
          onCropChange={setDraftCrop}
        />

        <div className="modal-footer">
          <span className="muted">
            Las anotaciones siguen siendo editables y se renderizan al exportar.
          </span>
          <div className="modal-actions">
            <button className="button secondary" onClick={onClose}>
              Cancelar
            </button>
            <button
              className="button primary"
              onClick={() => onSave(draftAnnotations, draftCrop)}
            >
              Guardar anotaciones
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
