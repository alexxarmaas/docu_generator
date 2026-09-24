"use client";

import {
  CheckSquare2,
  FileDown,
  Image as ImageIcon,
  Lightbulb,
  Minus,
  Search,
  ShieldAlert,
  Sparkles,
  Table2,
  Type,
} from "lucide-react";
import { KeyboardEvent, useMemo, useRef, useState } from "react";
import type { Block, BlockType } from "@/lib/types";

type InsertPreset = {
  type: BlockType;
  label?: string;
  variant?: Block["variant"];
};

type Props = {
  onInsert: (preset: InsertPreset) => void;
};

const COMMANDS: Array<{
  id: string;
  title: string;
  description: string;
  keywords: string;
  icon: typeof Type;
  preset: InsertPreset;
}> = [
  {
    id: "text",
    title: "Texto",
    description: "Explicación o instrucciones",
    keywords: "texto parrafo explicación instrucciones",
    icon: Type,
    preset: { type: "text" },
  },
  {
    id: "image",
    title: "Imagen",
    description: "Captura con anotaciones",
    keywords: "imagen captura screenshot foto",
    icon: ImageIcon,
    preset: { type: "image" },
  },
  {
    id: "checklist",
    title: "Checklist",
    description: "Lista de comprobaciones",
    keywords: "checklist lista comprobaciones tareas",
    icon: CheckSquare2,
    preset: { type: "checklist" },
  },
  {
    id: "table",
    title: "Tabla",
    description: "Datos estructurados en filas",
    keywords: "tabla datos filas columnas",
    icon: Table2,
    preset: { type: "table" },
  },
  {
    id: "tip",
    title: "Consejo",
    description: "Recomendación útil",
    keywords: "consejo tip recomendación ayuda",
    icon: Lightbulb,
    preset: { type: "note", label: "Consejo", variant: "tip" },
  },
  {
    id: "warning",
    title: "Importante",
    description: "Aviso o precaución",
    keywords: "importante advertencia warning atención aviso",
    icon: ShieldAlert,
    preset: { type: "note", label: "Importante", variant: "warning" },
  },
  {
    id: "success",
    title: "Resultado esperado",
    description: "Cómo debe quedar al terminar",
    keywords: "resultado éxito correcto esperado",
    icon: Sparkles,
    preset: {
      type: "note",
      label: "Resultado esperado",
      variant: "success",
    },
  },
  {
    id: "divider",
    title: "Separador",
    description: "Divide visualmente contenido",
    keywords: "separador linea divisor",
    icon: Minus,
    preset: { type: "divider" },
  },
  {
    id: "pagebreak",
    title: "Salto de página",
    description: "Nueva página al exportar",
    keywords: "salto pagina pdf exportar",
    icon: FileDown,
    preset: { type: "pagebreak" },
  },
];

export default function BlockCommandInput({ onInsert }: Props) {
  const [value, setValue] = useState("");
  const [open, setOpen] = useState(false);
  const [activeIndex, setActiveIndex] = useState(0);
  const inputRef = useRef<HTMLInputElement>(null);

  const query = value.startsWith("/") ? value.slice(1).trim().toLowerCase() : "";

  const commands = useMemo(() => {
    if (!query) return COMMANDS;
    return COMMANDS.filter((command) =>
      `${command.title} ${command.description} ${command.keywords}`
        .toLowerCase()
        .includes(query),
    );
  }, [query]);

  const choose = (index: number) => {
    const command = commands[index];
    if (!command) return;
    onInsert(command.preset);
    setValue("");
    setOpen(false);
    setActiveIndex(0);
    window.setTimeout(() => inputRef.current?.focus(), 0);
  };

  const onKeyDown = (event: KeyboardEvent<HTMLInputElement>) => {
    if (!open && event.key === "/") {
      setOpen(true);
      setActiveIndex(0);
      return;
    }

    if (!open) return;

    if (event.key === "ArrowDown") {
      event.preventDefault();
      setActiveIndex((index) =>
        commands.length ? (index + 1) % commands.length : 0,
      );
    } else if (event.key === "ArrowUp") {
      event.preventDefault();
      setActiveIndex((index) =>
        commands.length
          ? (index - 1 + commands.length) % commands.length
          : 0,
      );
    } else if (event.key === "Enter") {
      event.preventDefault();
      choose(activeIndex);
    } else if (event.key === "Escape") {
      event.preventDefault();
      setOpen(false);
      setValue("");
    }
  };

  return (
    <div className="slash-command">
      <div className="slash-input-shell">
        <span className="slash-plus">+</span>
        <input
          ref={inputRef}
          value={value}
          onChange={(event) => {
            const next = event.target.value;
            setValue(next);
            setOpen(next.startsWith("/"));
            setActiveIndex(0);
          }}
          onFocus={() => {
            if (value.startsWith("/")) setOpen(true);
          }}
          onKeyDown={onKeyDown}
          placeholder="Añadir bloque… escribe / para buscar"
          aria-label="Añadir bloque"
        />
        <kbd>/</kbd>
      </div>

      {open && (
        <div className="slash-menu">
          <div className="slash-menu-header">
            <Search size={13} />
            <span>{query ? `Resultados para “${query}”` : "Insertar bloque"}</span>
          </div>

          <div className="slash-menu-list">
            {commands.length === 0 && (
              <div className="slash-empty">No hay bloques que coincidan.</div>
            )}

            {commands.map((command, index) => {
              const Icon = command.icon;
              return (
                <button
                  type="button"
                  key={command.id}
                  className={index === activeIndex ? "active" : ""}
                  onMouseEnter={() => setActiveIndex(index)}
                  onMouseDown={(event) => event.preventDefault()}
                  onClick={() => choose(index)}
                >
                  <span className="slash-command-icon">
                    <Icon size={15} />
                  </span>
                  <span>
                    <strong>{command.title}</strong>
                    <small>{command.description}</small>
                  </span>
                </button>
              );
            })}
          </div>

          <div className="slash-menu-footer">
            <span><kbd>↑</kbd><kbd>↓</kbd> navegar</span>
            <span><kbd>Enter</kbd> insertar</span>
            <span><kbd>Esc</kbd> cerrar</span>
          </div>
        </div>
      )}
    </div>
  );
}
