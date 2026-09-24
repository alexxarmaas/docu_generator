"use client";

import {
  closestCenter,
  DndContext,
  DragEndEvent,
  PointerSensor,
  useSensor,
  useSensors,
} from "@dnd-kit/core";
import { arrayMove } from "@dnd-kit/sortable";
import {
  Archive,
  CheckCircle2,
  ChevronRight,
  Cloud,
  CloudOff,
  Download,
  Eye,
  FileDown,
  FileText,
  FolderOpen,
  Library,
  Plus,
  Redo2,
  RefreshCw,
  Save,
  Search,
  Settings2,
  Undo2,
  Upload,
} from "lucide-react";
import { ChangeEvent, useEffect, useMemo, useRef, useState } from "react";
import {
  deleteProject,
  downloadExport,
  getAutosave,
  listProjects,
  loadProject,
  normalizeProject,
  saveAutosave,
  saveProject,
  validateProject,
} from "@/lib/api";
import {
  cloneBlock,
  createProject,
  createStep,
  dataUrl,
  uid,
} from "@/lib/project";
import type {
  Block,
  Project,
  ProjectEntry,
  Step,
  ValidationIssue,
} from "@/lib/types";
import AnnotationModal from "./AnnotationModal";
import StepCard from "./StepCard";

type EditingImage = {
  stepId: string;
  blockId: string;
} | null;

type InspectorTab = "preview" | "checks" | "export";

export default function EditorWorkspace() {
  const [project, setProject] = useState<Project>(() => createProject());
  const [past, setPast] = useState<Project[]>([]);
  const [future, setFuture] = useState<Project[]>([]);
  const [hydrated, setHydrated] = useState(false);
  const [apiOnline, setApiOnline] = useState(false);
  const [autosaveState, setAutosaveState] = useState<
    "idle" | "saving" | "saved" | "error"
  >("idle");
  const [projects, setProjects] = useState<ProjectEntry[]>([]);
  const [currentProject, setCurrentProject] = useState("");
  const [issues, setIssues] = useState<ValidationIssue[]>([]);
  const [editingImage, setEditingImage] = useState<EditingImage>(null);
  const [busyExport, setBusyExport] = useState<string | null>(null);
  const [inspectorTab, setInspectorTab] = useState<InspectorTab>("preview");
  const [projectSearch, setProjectSearch] = useState("");
  const autosaveTimer = useRef<ReturnType<typeof setTimeout> | null>(null);

  const sensors = useSensors(
    useSensor(PointerSensor, {
      activationConstraint: { distance: 6 },
    }),
  );

  const refreshProjects = async () => {
    try {
      const entries = await listProjects();
      setProjects(entries);
      setApiOnline(true);
    } catch {
      setApiOnline(false);
    }
  };

  useEffect(() => {
    void (async () => {
      try {
        const [autosaved] = await Promise.all([getAutosave(), refreshProjects()]);
        if (autosaved) setProject(autosaved);
        setApiOnline(true);
      } catch {
        setApiOnline(false);
      } finally {
        setHydrated(true);
      }
    })();
  }, []);

  useEffect(() => {
    if (!hydrated) return;
    if (autosaveTimer.current) clearTimeout(autosaveTimer.current);

    setAutosaveState("saving");
    autosaveTimer.current = setTimeout(() => {
      void saveAutosave(project)
        .then(() => {
          setAutosaveState("saved");
          setApiOnline(true);
        })
        .catch(() => {
          setAutosaveState("error");
          setApiOnline(false);
        });
    }, 700);

    return () => {
      if (autosaveTimer.current) clearTimeout(autosaveTimer.current);
    };
  }, [project, hydrated]);

  const commit = (next: Project | ((current: Project) => Project)) => {
    setProject((current) => {
      const value = typeof next === "function" ? next(current) : next;
      if (JSON.stringify(value) === JSON.stringify(current)) return current;
      setPast((items) => [...items.slice(-49), structuredClone(current)]);
      setFuture([]);
      return value;
    });
  };

  const undo = () => {
    if (!past.length) return;
    const previous = past[past.length - 1];
    setFuture((items) => [structuredClone(project), ...items].slice(0, 50));
    setPast((items) => items.slice(0, -1));
    setProject(previous);
  };

  const redo = () => {
    if (!future.length) return;
    const next = future[0];
    setPast((items) => [...items.slice(-49), structuredClone(project)]);
    setFuture((items) => items.slice(1));
    setProject(next);
  };

  const updateStep = (stepId: string, step: Step) => {
    commit((current) => ({
      ...current,
      steps: current.steps.map((item) => (item.id === stepId ? step : item)),
    }));
  };

  const addStep = () => {
    commit((current) => ({
      ...current,
      steps: [...current.steps, createStep()],
    }));
  };

  const deleteStep = (stepId: string) => {
    commit((current) => ({
      ...current,
      steps:
        current.steps.length === 1
          ? [createStep()]
          : current.steps.filter((step) => step.id !== stepId),
    }));
  };

  const duplicateStep = (stepId: string) => {
    commit((current) => {
      const index = current.steps.findIndex((step) => step.id === stepId);
      if (index < 0) return current;
      const source = current.steps[index];
      const clone: Step = {
        id: uid(),
        title: source.title,
        blocks: source.blocks.map(cloneBlock),
      };
      const steps = [...current.steps];
      steps.splice(index + 1, 0, clone);
      return { ...current, steps };
    });
  };

  const findBlock = (blockId: string) => {
    for (let stepIndex = 0; stepIndex < project.steps.length; stepIndex += 1) {
      const blockIndex = project.steps[stepIndex].blocks.findIndex(
        (block) => block.id === blockId,
      );
      if (blockIndex >= 0) return { stepIndex, blockIndex };
    }
    return null;
  };

  const onDragEnd = ({ active, over }: DragEndEvent) => {
    if (!over || active.id === over.id) return;

    const source = findBlock(String(active.id));
    if (!source) return;

    const overId = String(over.id);
    let targetStepIndex = -1;
    let targetBlockIndex = -1;

    if (overId.startsWith("step:")) {
      const targetStepId = overId.slice(5);
      targetStepIndex = project.steps.findIndex(
        (step) => step.id === targetStepId,
      );
    } else {
      const target = findBlock(overId);
      if (!target) return;
      targetStepIndex = target.stepIndex;
      targetBlockIndex = target.blockIndex;
    }

    if (targetStepIndex < 0) return;

    commit((current) => {
      const steps = structuredClone(current.steps);
      const sourceStep = steps[source.stepIndex];

      if (
        source.stepIndex === targetStepIndex &&
        targetBlockIndex >= 0
      ) {
        sourceStep.blocks = arrayMove(
          sourceStep.blocks,
          source.blockIndex,
          targetBlockIndex,
        );
        return { ...current, steps };
      }

      const [moved] = sourceStep.blocks.splice(source.blockIndex, 1);
      const targetStep = steps[targetStepIndex];

      if (targetBlockIndex < 0) {
        targetStep.blocks.push(moved);
      } else {
        const adjustedIndex =
          source.stepIndex === targetStepIndex &&
          source.blockIndex < targetBlockIndex
            ? targetBlockIndex - 1
            : targetBlockIndex;
        targetStep.blocks.splice(adjustedIndex, 0, moved);
      }

      return { ...current, steps };
    });
  };

  const editingBlock = useMemo(() => {
    if (!editingImage) return null;
    return (
      project.steps
        .find((step) => step.id === editingImage.stepId)
        ?.blocks.find((block) => block.id === editingImage.blockId) || null
    );
  }, [editingImage, project]);

  const filteredProjects = useMemo(() => {
    const query = projectSearch.trim().toLowerCase();
    if (!query) return projects;
    return projects.filter((entry) =>
      entry.name.toLowerCase().includes(query),
    );
  }, [projectSearch, projects]);

  const updateEditingImage = (
    annotations: Block["annotations"],
    crop: Block["crop"],
  ) => {
    if (!editingImage) return;
    commit((current) => ({
      ...current,
      steps: current.steps.map((step) =>
        step.id !== editingImage.stepId
          ? step
          : {
              ...step,
              blocks: step.blocks.map((block) =>
                block.id === editingImage.blockId
                  ? { ...block, annotations, crop }
                  : block,
              ),
            },
      ),
    }));
    setEditingImage(null);
  };

  const saveToLibrary = async () => {
    try {
      const next: Project = {
        ...project,
        metadata: {
          ...project.metadata,
          updated_at: new Date().toLocaleString("es-ES"),
        },
      };
      const result = await saveProject(next, currentProject || undefined);
      setProject(next);
      setCurrentProject(result.name);
      await refreshProjects();
    } catch (error) {
      window.alert(`No se pudo guardar: ${String(error)}`);
    }
  };

  const publish = async () => {
    const next: Project = {
      ...project,
      metadata: {
        ...project.metadata,
        status: "Publicado",
        updated_at: new Date().toLocaleString("es-ES"),
      },
    };
    setProject(next);
    try {
      const result = await saveProject(next, currentProject || undefined);
      setCurrentProject(result.name);
      await refreshProjects();
    } catch (error) {
      window.alert(`No se pudo publicar: ${String(error)}`);
    }
  };

  const openProject = async (name: string) => {
    try {
      const loaded = await loadProject(name);
      setProject(loaded);
      setPast([]);
      setFuture([]);
      setCurrentProject(name);
      setIssues([]);
    } catch (error) {
      window.alert(`No se pudo abrir: ${String(error)}`);
    }
  };

  const removeProject = async (name: string) => {
    if (!window.confirm("¿Eliminar este proyecto de la biblioteca local?")) return;
    await deleteProject(name);
    if (currentProject === name) setCurrentProject("");
    await refreshProjects();
  };

  const validate = async () => {
    try {
      const result = await validateProject(project);
      setIssues(result);
      setInspectorTab("checks");
    } catch (error) {
      window.alert(`No se pudo validar: ${String(error)}`);
    }
  };

  const exportAs = async (
    format: "pdf" | "docx" | "html" | "md" | "zip",
  ) => {
    setBusyExport(format);
    try {
      await downloadExport(project, format);
    } catch (error) {
      window.alert(`No se pudo exportar: ${String(error)}`);
    } finally {
      setBusyExport(null);
    }
  };

  const exportEditable = () => {
    const blob = new Blob([JSON.stringify(project, null, 2)], {
      type: "application/json",
    });
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = `${slug(project.title || "proyecto")}.docugen.json`;
    anchor.click();
    URL.revokeObjectURL(url);
  };

  const importEditable = (event: ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = () => {
      void (async () => {
        try {
          const imported = JSON.parse(String(reader.result));
          const normalized = await normalizeProject(imported);
          setProject(normalized);
          setPast([]);
          setFuture([]);
          setCurrentProject("");
          setIssues([]);
        } catch (error) {
          window.alert(`No se pudo importar: ${String(error)}`);
        }
      })();
    };
    reader.readAsText(file);
    event.target.value = "";
  };

  const blocking = issues.some((issue) => issue.level === "error");

  const autosaveText =
    autosaveState === "saving"
      ? "Guardando…"
      : autosaveState === "saved"
        ? "Guardado"
        : autosaveState === "error"
          ? "Error al guardar"
          : "Listo";

  return (
    <div className="app-shell">
      <header className="app-bar">
        <div className="app-brand">
          <div className="brand-mark">DG</div>
          <div className="brand-copy">
            <strong>Docu Generator</strong>
            <span>Brisia</span>
          </div>
          <ChevronRight size={15} className="breadcrumb-chevron" />
          <span className="document-breadcrumb">
            {project.title || "Documento sin título"}
          </span>
        </div>

        <div className="app-bar-center">
          <div className="history-controls">
            <button
              className="toolbar-icon"
              onClick={undo}
              disabled={!past.length}
              title="Deshacer"
            >
              <Undo2 size={16} />
            </button>
            <button
              className="toolbar-icon"
              onClick={redo}
              disabled={!future.length}
              title="Rehacer"
            >
              <Redo2 size={16} />
            </button>
          </div>

          <div
            className={`save-state ${autosaveState === "error" ? "error" : ""}`}
          >
            {apiOnline ? <Cloud size={14} /> : <CloudOff size={14} />}
            <span>{autosaveText}</span>
          </div>
        </div>

        <div className="app-actions">
          <button className="button ghost" onClick={() => void validate()}>
            <CheckCircle2 size={16} />
            Validar
          </button>
          <button className="button secondary" onClick={() => void saveToLibrary()}>
            <Save size={16} />
            Guardar
          </button>
          <button className="button primary" onClick={() => void publish()}>
            <Archive size={16} />
            Publicar
          </button>
        </div>
      </header>

      <div className="workspace">
        <aside className="sidebar">
          <div className="sidebar-scroll">
            <section className="sidebar-section library-section">
              <div className="section-title-row">
                <div>
                  <Library size={15} />
                  <strong>Biblioteca</strong>
                </div>
                <button
                  className="toolbar-icon"
                  onClick={() => void refreshProjects()}
                  title="Actualizar"
                >
                  <RefreshCw size={14} />
                </button>
              </div>

              <div className="sidebar-search">
                <Search size={14} />
                <input
                  value={projectSearch}
                  onChange={(event) => setProjectSearch(event.target.value)}
                  placeholder="Buscar proyecto…"
                />
              </div>

              <div className="project-list">
                {filteredProjects.length === 0 && (
                  <div className="empty-small">
                    {projects.length === 0
                      ? "Todavía no hay proyectos guardados."
                      : "No hay coincidencias."}
                  </div>
                )}

                {filteredProjects.map((entry) => (
                  <div
                    key={entry.name}
                    className={`project-item ${currentProject === entry.name ? "active" : ""}`}
                  >
                    <button onClick={() => void openProject(entry.name)}>
                      <FolderOpen size={15} />
                      <span>{entry.name.replace(".docugen.json", "")}</span>
                    </button>
                    <button
                      className="project-delete"
                      onClick={() => void removeProject(entry.name)}
                      aria-label="Eliminar"
                      title="Eliminar proyecto"
                    >
                      ×
                    </button>
                  </div>
                ))}
              </div>

              <div className="quick-project-actions">
                <button
                  onClick={() => {
                    setProject(createProject());
                    setPast([]);
                    setFuture([]);
                    setCurrentProject("");
                    setIssues([]);
                  }}
                >
                  <Plus size={14} />
                  Nuevo
                </button>

                <label>
                  <Upload size={14} />
                  Importar
                  <input
                    type="file"
                    accept=".json"
                    hidden
                    onChange={importEditable}
                  />
                </label>
              </div>
            </section>

            <details className="settings-card" open>
              <summary>
                <span>
                  <Settings2 size={15} />
                  Documento
                </span>
              </summary>
              <div className="settings-card-body">
                <label>
                  Tipo
                  <input
                    className="field"
                    value={project.metadata.document_type}
                    onChange={(event) =>
                      commit({
                        ...project,
                        metadata: {
                          ...project.metadata,
                          document_type: event.target.value,
                        },
                      })
                    }
                  />
                </label>

                <div className="field-grid">
                  <label>
                    Versión
                    <input
                      className="field"
                      value={project.metadata.version_label}
                      onChange={(event) =>
                        commit({
                          ...project,
                          metadata: {
                            ...project.metadata,
                            version_label: event.target.value,
                          },
                        })
                      }
                    />
                  </label>

                  <label>
                    Estado
                    <select
                      className="field"
                      value={project.metadata.status}
                      onChange={(event) =>
                        commit({
                          ...project,
                          metadata: {
                            ...project.metadata,
                            status: event.target
                              .value as Project["metadata"]["status"],
                          },
                        })
                      }
                    >
                      <option>Borrador</option>
                      <option>En revisión</option>
                      <option>Publicado</option>
                      <option>Archivado</option>
                    </select>
                  </label>
                </div>

                <label>
                  Autor
                  <input
                    className="field"
                    value={project.metadata.author}
                    onChange={(event) =>
                      commit({
                        ...project,
                        metadata: {
                          ...project.metadata,
                          author: event.target.value,
                        },
                      })
                    }
                    placeholder="Nombre del autor"
                  />
                </label>

                <div className="toggle-stack">
                  <label>
                    <span>
                      <strong>Portada</strong>
                      <small>Añadir portada al documento</small>
                    </span>
                    <input
                      type="checkbox"
                      checked={project.metadata.show_cover}
                      onChange={(event) =>
                        commit({
                          ...project,
                          metadata: {
                            ...project.metadata,
                            show_cover: event.target.checked,
                          },
                        })
                      }
                    />
                  </label>
                  <label>
                    <span>
                      <strong>Índice</strong>
                      <small>Generar índice de pasos</small>
                    </span>
                    <input
                      type="checkbox"
                      checked={project.metadata.show_toc}
                      onChange={(event) =>
                        commit({
                          ...project,
                          metadata: {
                            ...project.metadata,
                            show_toc: event.target.checked,
                          },
                        })
                      }
                    />
                  </label>
                </div>
              </div>
            </details>

            <div className="sidebar-footer-actions">
              <button className="sidebar-link" onClick={exportEditable}>
                <Download size={14} />
                Descargar proyecto editable
              </button>
            </div>
          </div>
        </aside>

        <section className="main-column">
          <div className="editor-header">
            <span className="editor-kicker">GUÍA DE USUARIO</span>
            <input
              className="document-title-input"
              value={project.title}
              onChange={(event) =>
                commit({ ...project, title: event.target.value })
              }
              placeholder="Escribe el título de la guía…"
            />

            <div className="document-meta-line">
              <span>{project.metadata.document_type}</span>
              <span>v{project.metadata.version_label}</span>
              <span className={`status-pill status-${project.metadata.status.toLowerCase().replace(" ", "-")}`}>
                {project.metadata.status}
              </span>
              {project.metadata.author && <span>{project.metadata.author}</span>}
            </div>

            <textarea
              className="intro-editor"
              value={project.introduction}
              onChange={(event) =>
                commit({ ...project, introduction: event.target.value })
              }
              placeholder="Añade una breve introducción para explicar qué aprenderá el usuario…"
              rows={3}
            />
          </div>

          <DndContext
            sensors={sensors}
            collisionDetection={closestCenter}
            onDragEnd={onDragEnd}
          >
            <div className="steps-stack">
              {project.steps.map((step, index) => (
                <StepCard
                  key={step.id}
                  step={step}
                  index={index}
                  onStepChange={(next) => updateStep(step.id, next)}
                  onDelete={() => deleteStep(step.id)}
                  onDuplicate={() => duplicateStep(step.id)}
                  onAnnotate={(blockId) =>
                    setEditingImage({ stepId: step.id, blockId })
                  }
                />
              ))}
            </div>
          </DndContext>

          <button className="add-step" onClick={addStep}>
            <Plus size={17} />
            <span>Añadir paso</span>
          </button>

          <div className="closing-card">
            <span>Nota final</span>
            <textarea
              value={project.closing_note}
              onChange={(event) =>
                commit({ ...project, closing_note: event.target.value })
              }
              placeholder="Añade un cierre, recordatorio o siguiente paso…"
              rows={3}
            />
          </div>
        </section>

        <aside className="inspector">
          <div className="inspector-tabs">
            <button
              className={inspectorTab === "preview" ? "active" : ""}
              onClick={() => setInspectorTab("preview")}
            >
              <Eye size={15} />
              Preview
            </button>
            <button
              className={inspectorTab === "checks" ? "active" : ""}
              onClick={() => setInspectorTab("checks")}
            >
              <CheckCircle2 size={15} />
              Revisar
              {issues.length > 0 && (
                <span className="tab-count">{issues.length}</span>
              )}
            </button>
            <button
              className={inspectorTab === "export" ? "active" : ""}
              onClick={() => setInspectorTab("export")}
            >
              <FileDown size={15} />
              Exportar
            </button>
          </div>

          <div className="inspector-body">
            {inspectorTab === "preview" && (
              <DocumentPreview project={project} />
            )}

            {inspectorTab === "checks" && (
              <div className="checks-panel">
                <div className="panel-heading">
                  <div>
                    <span className="eyebrow">Control de calidad</span>
                    <h3>Revisión del documento</h3>
                  </div>
                  <button className="button secondary compact" onClick={() => void validate()}>
                    Revisar
                  </button>
                </div>

                {issues.length === 0 ? (
                  <div className="empty-checks">
                    <CheckCircle2 size={28} />
                    <strong>Sin problemas detectados</strong>
                    <span>
                      Pulsa “Revisar” para comprobar la guía antes de exportarla.
                    </span>
                  </div>
                ) : (
                  <div className="validation-panel">
                    {issues.map((issue, index) => (
                      <div className={`issue ${issue.level}`} key={index}>
                        <span className="issue-dot" />
                        <span>{issue.message}</span>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}

            {inspectorTab === "export" && (
              <div className="export-workspace">
                <div className="panel-heading">
                  <div>
                    <span className="eyebrow">Publicación</span>
                    <h3>Exportar documento</h3>
                  </div>
                </div>

                {blocking && (
                  <div className="export-warning">
                    Hay errores de validación que debes corregir antes de exportar.
                  </div>
                )}

                <ExportCard
                  title="PDF"
                  description="Documento final listo para entregar o imprimir."
                  primary
                  disabled={blocking || busyExport !== null || !apiOnline}
                  busy={busyExport === "pdf"}
                  onClick={() => void exportAs("pdf")}
                />
                <ExportCard
                  title="Word / DOCX"
                  description="Documento editable para Word o LibreOffice."
                  disabled={blocking || busyExport !== null || !apiOnline}
                  busy={busyExport === "docx"}
                  onClick={() => void exportAs("docx")}
                />
                <ExportCard
                  title="HTML"
                  description="Archivo autónomo para abrir en navegador."
                  disabled={blocking || busyExport !== null || !apiOnline}
                  busy={busyExport === "html"}
                  onClick={() => void exportAs("html")}
                />
                <ExportCard
                  title="Markdown"
                  description="Versión ligera para repositorios o wikis."
                  disabled={blocking || busyExport !== null || !apiOnline}
                  busy={busyExport === "md"}
                  onClick={() => void exportAs("md")}
                />
                <ExportCard
                  title="ZIP completo"
                  description="Incluye todos los formatos e imágenes."
                  disabled={blocking || busyExport !== null || !apiOnline}
                  busy={busyExport === "zip"}
                  onClick={() => void exportAs("zip")}
                />

                {!apiOnline && (
                  <div className="backend-notice">
                    <CloudOff size={16} />
                    Backend local desconectado. Comprueba que FastAPI esté activo.
                  </div>
                )}
              </div>
            )}
          </div>
        </aside>
      </div>

      {editingBlock?.image_base64 && (
        <AnnotationModal
          open={Boolean(editingImage)}
          imageUrl={dataUrl(editingBlock)}
          annotations={editingBlock.annotations}
          crop={editingBlock.crop}
          onClose={() => setEditingImage(null)}
          onSave={updateEditingImage}
        />
      )}
    </div>
  );
}

function DocumentPreview({ project }: { project: Project }) {
  return (
    <div className="preview-workspace">
      <div className="preview-toolbar">
        <div>
          <span className="eyebrow">Vista final</span>
          <strong>{project.metadata.status}</strong>
        </div>
        <span className="preview-zoom">A4</span>
      </div>

      <div className="paper-preview">
        {project.metadata.show_cover && (
          <div className="preview-cover">
            <span>BRISIA</span>
            <h2>{project.title || "Guía sin título"}</h2>
            <p>
              {project.metadata.document_type} · v
              {project.metadata.version_label}
            </p>
          </div>
        )}

        <div className="preview-body">
          {!project.metadata.show_cover && (
            <h2>{project.title || "Guía sin título"}</h2>
          )}

          {project.introduction && <p>{project.introduction}</p>}

          {project.metadata.show_toc && project.steps.length > 0 && (
            <div className="preview-toc">
              <strong>Contenido</strong>
              {project.steps.map((step, index) => (
                <span key={step.id}>
                  {index + 1}. {step.title || "Paso sin título"}
                </span>
              ))}
            </div>
          )}

          {project.steps.map((step, index) => (
            <div className="preview-step" key={step.id}>
              <h3>
                <span>{index + 1}</span>
                {step.title || "Paso sin título"}
              </h3>
              {step.blocks.map((block) => (
                <PreviewBlock block={block} key={block.id} />
              ))}
            </div>
          ))}

          {project.closing_note && (
            <div className="preview-callout success">
              {project.closing_note}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function ExportCard({
  title,
  description,
  primary = false,
  disabled,
  busy,
  onClick,
}: {
  title: string;
  description: string;
  primary?: boolean;
  disabled: boolean;
  busy: boolean;
  onClick: () => void;
}) {
  return (
    <button
      className={`export-card ${primary ? "primary" : ""}`}
      disabled={disabled}
      onClick={onClick}
    >
      <div className="export-card-icon">
        <FileText size={18} />
      </div>
      <div>
        <strong>{busy ? "Generando…" : title}</strong>
        <span>{description}</span>
      </div>
      <Download size={16} className="export-card-download" />
    </button>
  );
}

function PreviewBlock({ block }: { block: Block }) {
  if (block.type === "text" && block.text) {
    return <p className="preview-text">{block.text}</p>;
  }

  if (block.type === "note" && block.text) {
    return (
      <div className={`preview-callout ${block.variant}`}>
        {block.label && <strong>{block.label}</strong>}
        <span>{block.text}</span>
      </div>
    );
  }

  if (block.type === "checklist" && block.items.trim()) {
    return (
      <ul className="preview-checklist">
        {block.items
          .split("\n")
          .filter(Boolean)
          .map((item, index) => (
            <li key={index}>☐ {item}</li>
          ))}
      </ul>
    );
  }

  if (block.type === "table" && block.items.trim()) {
    const rows = block.items
      .split("\n")
      .filter(Boolean)
      .map((row) => row.split("|").map((cell) => cell.trim()));

    return (
      <div className="preview-table-wrap">
        <table className="preview-table">
          <tbody>
            {rows.map((row, rowIndex) => (
              <tr key={rowIndex}>
                {row.map((cell, cellIndex) =>
                  rowIndex === 0 ? (
                    <th key={cellIndex}>{cell}</th>
                  ) : (
                    <td key={cellIndex}>{cell}</td>
                  ),
                )}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    );
  }

  if (block.type === "image" && block.image_base64) {
    return (
      <figure className={`preview-image ${block.image_width} ${block.align}`}>
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img src={dataUrl(block)} alt={block.image_caption || "Captura"} />
        {(block.annotations.length > 0 || block.crop) && (
          <span className="preview-annotation-note">
            Edición visual aplicada en exportación
          </span>
        )}
        {block.image_caption && <figcaption>{block.image_caption}</figcaption>}
      </figure>
    );
  }

  if (block.type === "divider") return <hr className="preview-divider" />;

  if (block.type === "pagebreak") {
    return <div className="preview-pagebreak">salto de página</div>;
  }

  return null;
}

function slug(value: string) {
  return (
    value
      .toLowerCase()
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "")
      .replace(/[^a-z0-9]+/g, "-")
      .replace(/^-|-$/g, "") || "proyecto"
  );
}
