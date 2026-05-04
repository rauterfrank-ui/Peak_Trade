"""In-memory contract for ``WorkflowScript`` DTO (v0).

No HTTP client, router wiring, filesystem, subprocess, env, or network.

Prod definition: ``src.webui.ops_workflows_router.WorkflowScript``.
"""

from __future__ import annotations

from dataclasses import asdict

import pytest

pytest.importorskip("fastapi")

from src.webui.ops_workflows_router import WorkflowScript


def _minimal() -> WorkflowScript:
    return WorkflowScript(
        id="merge_flow",
        title="Merge Flow",
        description="Does merges.",
        script_path="scripts/merge.sh",
        commands=["./scripts/merge.sh"],
        docs_refs=["docs/ops/README.md"],
    )


def test_workflow_script_import_and_required_fields_contract_v0() -> None:
    wf = _minimal()
    assert wf.id == "merge_flow"
    assert wf.title == "Merge Flow"
    assert wf.description == "Does merges."
    assert wf.script_path == "scripts/merge.sh"
    assert wf.commands == ["./scripts/merge.sh"]
    assert wf.docs_refs == ["docs/ops/README.md"]


def test_workflow_script_default_optional_fields_contract_v0() -> None:
    wf = _minimal()
    assert wf.exists is False
    assert wf.size_bytes is None
    assert wf.last_modified is None


def test_workflow_script_explicit_optional_fields_contract_v0() -> None:
    wf = WorkflowScript(
        id="x",
        title="t",
        description="d",
        script_path="p.sh",
        commands=["run"],
        docs_refs=["docs/a.md"],
        exists=True,
        size_bytes=128,
        last_modified="2026-05-03T12:00:00Z",
    )
    assert wf.exists is True
    assert wf.size_bytes == 128
    assert wf.last_modified == "2026-05-03T12:00:00Z"


def test_workflow_script_asdict_shape_contract_v0() -> None:
    wf = _minimal()
    d = asdict(wf)
    assert d == {
        "id": "merge_flow",
        "title": "Merge Flow",
        "description": "Does merges.",
        "script_path": "scripts/merge.sh",
        "commands": ["./scripts/merge.sh"],
        "docs_refs": ["docs/ops/README.md"],
        "exists": False,
        "size_bytes": None,
        "last_modified": None,
    }
