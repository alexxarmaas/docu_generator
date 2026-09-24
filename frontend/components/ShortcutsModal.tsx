"use client";

import { Keyboard, X } from "lucide-react";

type Props = {
  open: boolean;
  onClose: () => void;
};

const SHORTCUTS = [
  ["Ctrl / ⌘ + S", "Guardar en biblioteca"],
  ["Ctrl / ⌘ + Z", "Deshacer"],
  ["Ctrl / ⌘ + Y", "Rehacer"],
  ["Ctrl / ⌘ + Shift + Z", "Rehacer"],
  ["Alt + 1", "Abrir Preview"],
  ["Alt + 2", "Abrir Revisión"],
  ["Alt + 3", "Abrir Exportación"],
  ["/", "Buscar bloque desde el inserter"],
  ["?", "Mostrar esta ayuda"],
  ["Esc", "Cerrar modal o ayuda"],
];

export default function ShortcutsModal({ open, onClose }: Props) {
  if (!open) return null;

  return (
    <div className="shortcuts-backdrop" onMouseDown={onClose}>
      <section
        className="shortcuts-modal"
        role="dialog"
        aria-modal="true"
        aria-label="Atajos de teclado"
        onMouseDown={(event) => event.stopPropagation()}
      >
        <header>
          <div className="shortcuts-title">
            <span className="shortcuts-icon">
              <Keyboard size={18} />
            </span>
            <div>
              <span className="eyebrow">Productividad</span>
              <h2>Atajos de teclado</h2>
            </div>
          </div>
          <button className="icon-button" onClick={onClose} aria-label="Cerrar">
            <X size={17} />
          </button>
        </header>

        <div className="shortcuts-list">
          {SHORTCUTS.map(([shortcut, action]) => (
            <div key={shortcut}>
              <span>{action}</span>
              <kbd>{shortcut}</kbd>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}
