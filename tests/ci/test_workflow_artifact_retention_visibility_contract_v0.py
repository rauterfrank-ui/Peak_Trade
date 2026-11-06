"""Static visibility contract for GitHub workflow artifact retention.

Parses workflow YAML files as UTF-8 text only. Never dispatches workflows,
never calls GitHub APIs, never executes scripts, and never touches runtime,
scheduler, daemon, paper/shadow/testnet/live, broker/exchange, or order paths.

This contract intentionally classifies current upload-artifact retention
visibility. It does not require workflow YAML changes and does not treat the
known missing-retention list as a new hard failure without owner decision.
"""

from __future__ import annotations

import re
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
WORKFLOW_ROOT = REPO_ROOT / ".github" / "workflows"

KNOWN_UPLOAD_ARTIFACT_WORKFLOWS_WITHOUT_RETENTION_DAYS = {
    "audit.yml",
    "market_outlook_automation.yml",
    "paper_session_audit_evidence.yml",
    "paper_session_telemetry_summary.yml",
    "paper_tests_audit_evidence.yml",
    "shadow_paper_smoke.yml",
}


def _workflow_files() -> list[Path]:
    return sorted(
        path
        for pattern in ("*.yml", "*.yaml")
        for path in WORKFLOW_ROOT.glob(pattern)
        if path.is_file()
    )


def _workflow_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _upload_artifact_workflows() -> list[Path]:
    return [path for path in _workflow_files() if "actions/upload-artifact" in _workflow_text(path)]


def _has_retention_days(path: Path) -> bool:
    return bool(re.search(r"retention-days\s*:", _workflow_text(path)))


def test_workflow_artifact_retention_visibility_contract_has_workflows_to_check() -> None:
    workflows = _workflow_files()

    assert WORKFLOW_ROOT.exists()
    assert workflows


def test_workflow_artifact_retention_visibility_contract_module_avoids_execution_hooks() -> None:
    test_text = Path(__file__).read_text(encoding="utf-8")
    import_lines = [
        line.strip()
        for line in test_text.splitlines()
        if line.strip().startswith(("import ", "from "))
    ]

    forbidden_import_prefixes = [
        "import os",
        "from os",
        "import subprocess",
        "from subprocess",
        "import runpy",
        "from runpy",
        "import importlib",
        "from importlib",
        "import requests",
        "from requests",
        "import httpx",
        "from httpx",
        "import urllib",
        "from urllib",
        "import socket",
        "from socket",
    ]

    found = [
        prefix
        for prefix in forbidden_import_prefixes
        if any(line.startswith(prefix) for line in import_lines)
    ]
    assert not found, f"static workflow contract must not import execution/network hooks: {found}"


def test_workflow_artifact_retention_visibility_contract_tracks_upload_artifact_surface() -> None:
    upload_workflows = _upload_artifact_workflows()

    assert upload_workflows
    assert len(upload_workflows) >= len(KNOWN_UPLOAD_ARTIFACT_WORKFLOWS_WITHOUT_RETENTION_DAYS)


def test_workflow_artifact_retention_visibility_contract_classifies_known_missing_retention_list() -> (
    None
):
    missing_retention = {
        path.name for path in _upload_artifact_workflows() if not _has_retention_days(path)
    }

    assert missing_retention == KNOWN_UPLOAD_ARTIFACT_WORKFLOWS_WITHOUT_RETENTION_DAYS


def test_workflow_artifact_retention_visibility_contract_known_missing_list_stays_documentary() -> (
    None
):
    """The known list is an owner-review surface, not an automatic YAML-change mandate."""
    assert KNOWN_UPLOAD_ARTIFACT_WORKFLOWS_WITHOUT_RETENTION_DAYS == {
        "audit.yml",
        "market_outlook_automation.yml",
        "paper_session_audit_evidence.yml",
        "paper_session_telemetry_summary.yml",
        "paper_tests_audit_evidence.yml",
        "shadow_paper_smoke.yml",
    }


def test_workflow_artifact_retention_visibility_contract_retains_existing_retention_count_floor() -> (
    None
):
    with_retention = [
        path.name for path in _upload_artifact_workflows() if _has_retention_days(path)
    ]

    assert len(with_retention) >= 36


def test_workflow_artifact_retention_visibility_contract_retains_static_local_scope() -> None:
    test_text = Path(__file__).read_text(encoding="utf-8")

    # Built dynamically so this guard does not match its own string table.
    forbidden_fragments = [
        "".join(("subprocess", ".")),
        "".join(("os", ".system")),
        "".join(("runpy", ".")),
        "".join(("importlib", ".import_module")),
        "".join(("requests", ".")),
        "".join(("httpx", ".")),
        "".join(("urllib", ".")),
        "".join(("socket", ".")),
        " ".join(("gh", "workflow", "run")),
        " ".join(("gh", "api")),
    ]

    found = [fragment for fragment in forbidden_fragments if fragment in test_text]
    assert not found, f"contract must remain static/local-only: {found}"
