"use client";

import dynamic from "next/dynamic";

const EditorWorkspace = dynamic(() => import("./EditorWorkspace"), {
  ssr: false,
  loading: () => (
    <main className="client-loading">
      <div className="client-loading-card">
        <div className="brand-mark">DG</div>
        <div>
          <strong>Docu Generator</strong>
          <span>Preparando editor local…</span>
        </div>
      </div>
    </main>
  ),
});

export default function ClientOnlyEditor() {
  return <EditorWorkspace />;
}
