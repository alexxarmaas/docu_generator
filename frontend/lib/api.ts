import type { Project, ProjectEntry, ValidationIssue } from "./types";

const API = process.env.NEXT_PUBLIC_DOCU_API || "http://127.0.0.1:8000";

async function json<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const message = await response.text();
    throw new Error(message || `HTTP ${response.status}`);
  }
  return response.json() as Promise<T>;
}

export async function getAutosave(): Promise<Project | null> {
  const result = await json<{ project: Project | null }>(
    await fetch(`${API}/api/autosave`, { cache: "no-store" }),
  );
  return result.project;
}

export async function saveAutosave(project: Project) {
  await json(
    await fetch(`${API}/api/autosave`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(project),
    }),
  );
}

export async function listProjects(): Promise<ProjectEntry[]> {
  const result = await json<{ projects: ProjectEntry[] }>(
    await fetch(`${API}/api/projects`, { cache: "no-store" }),
  );
  return result.projects;
}

export async function loadProject(name: string): Promise<Project> {
  const result = await json<{ project: Project }>(
    await fetch(`${API}/api/projects/${encodeURIComponent(name)}`, {
      cache: "no-store",
    }),
  );
  return result.project;
}

export async function saveProject(project: Project, filename?: string) {
  const query = filename ? `?filename=${encodeURIComponent(filename)}` : "";
  return json<{ ok: boolean; name: string }>(
    await fetch(`${API}/api/projects${query}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(project),
    }),
  );
}

export async function deleteProject(name: string) {
  await json(
    await fetch(`${API}/api/projects/${encodeURIComponent(name)}`, {
      method: "DELETE",
    }),
  );
}

export async function validateProject(project: Project) {
  const result = await json<{ issues: ValidationIssue[] }>(
    await fetch(`${API}/api/validate`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(project),
    }),
  );
  return result.issues;
}

export async function downloadExport(
  project: Project,
  format: "pdf" | "docx" | "html" | "md" | "zip",
) {
  const response = await fetch(`${API}/api/export/${format}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(project),
  });

  if (!response.ok) {
    throw new Error(await response.text());
  }

  const blob = await response.blob();
  const disposition = response.headers.get("content-disposition") || "";
  const encoded = disposition.match(/filename\*=UTF-8''([^;]+)/)?.[1];
  const filename = encoded ? decodeURIComponent(encoded) : `guide.${format}`;

  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = filename;
  document.body.appendChild(anchor);
  anchor.click();
  anchor.remove();
  URL.revokeObjectURL(url);
}
