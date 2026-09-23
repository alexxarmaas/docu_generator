from pathlib import Path

import docu_generator.services.workspace as workspace


def test_workspace_autosave_project_and_versions(tmp_path, monkeypatch):
    projects = tmp_path / "projects"
    versions = tmp_path / "versions"
    autosave_path = tmp_path / "autosave.docugen.json"

    monkeypatch.setattr(workspace, "WORKSPACE_ROOT", tmp_path)
    monkeypatch.setattr(workspace, "PROJECTS_DIR", projects)
    monkeypatch.setattr(workspace, "VERSIONS_DIR", versions)
    monkeypatch.setattr(workspace, "AUTOSAVE_PATH", autosave_path)

    payload = b'{"version": 3}'

    workspace.autosave(payload)
    assert workspace.load_autosave() == payload

    saved = workspace.save_project(
        "Mi guía",
        payload,
        filename="mi-guia",
    )

    assert saved.exists()
    assert workspace.load_saved_project(saved.name) == payload

    entries = workspace.list_projects()
    assert len(entries) == 1
    assert entries[0].name == saved.name

    history = workspace.list_versions(saved.name)
    assert len(history) == 1
    assert workspace.load_version(saved.name, history[0].name) == payload

    workspace.delete_saved_project(saved.name)
    assert workspace.list_projects() == []
