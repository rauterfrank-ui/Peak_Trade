"""Static visibility contract for GitHub workflow write permissions.

Parses workflow YAML files as UTF-8 text only. Never dispatches workflows,
never calls GitHub APIs, never executes scripts, and never touches runtime,
scheduler, daemon, paper/shadow/testnet/live, broker/exchange, or order paths.

This contract freezes the current workflow `*: write` permission inventory as an
owner-review surface. It does not require workflow YAML changes and does not
treat the current set as a new hard failure without owner decision.
"""

from __future__ import annotations

import re
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
WORKFLOW_ROOT = REPO_ROOT / ".github" / "workflows"

KNOWN_WORKFLOWS_WITH_WRITE_PERMISSIONS = frozenset(
    {
        "ci-scheduled-paper-and-export-smoke.yml",
        "cursor_auto_automerge.yml",
        "cursor_auto_pr.yml",
        "infostream-automation.yml",
        "ops_doctor_pages.yml",
        "paper_session_audit_evidence.yml",
        "policy_critic.yml",
        "weekly_core_audit.yml",
    }
)


def _workflow_files() -> list[Path]:
    return sorted(
        path
        for pattern in ("*.yml", "*.yaml")
        for path in WORKFLOW_ROOT.glob(pattern)
        if path.is_file()
    )


def _workflow_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _workflow_write_permission_lines(path: Path) -> list[str]:
    lines = []
    write_pat = re.compile(r":\s*write\b")
    for line in _workflow_text(path).splitlines():
        if write_pat.search(line):
            lines.append(line.strip())
    return lines


def _permission_line_key(line: str) -> str:
    normalized = line.strip()
    if normalized.startswith("#"):
        normalized = normalized[1:].strip()
    return normalized.split(":", 1)[0].strip()


def _workflows_with_write_permissions() -> dict[str, list[str]]:
    return {
        workflow.name: lines
        for workflow in _workflow_files()
        if (lines := _workflow_write_permission_lines(workflow))
    }


def test_workflow_write_permissions_visibility_contract_has_workflows_to_check() -> None:
    workflows = _workflow_files()

    assert WORKFLOW_ROOT.exists()
    assert workflows


def test_workflow_write_permissions_visibility_contract_module_avoids_execution_hooks() -> None:
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


def test_workflow_write_permissions_visibility_contract_classifies_current_set() -> None:
    current = frozenset(_workflows_with_write_permissions())

    assert current == KNOWN_WORKFLOWS_WITH_WRITE_PERMISSIONS


def test_workflow_write_permissions_visibility_contract_known_set_stays_documentary() -> None:
    """The known set is an owner-review surface, not a workflow-change mandate."""
    assert len(KNOWN_WORKFLOWS_WITH_WRITE_PERMISSIONS) == 8


def test_workflow_write_permissions_visibility_contract_requires_lines_for_known_set() -> None:
    current = _workflows_with_write_permissions()

    missing_lines = [
        workflow for workflow in KNOWN_WORKFLOWS_WITH_WRITE_PERMISSIONS if not current.get(workflow)
    ]

    assert not missing_lines, f"known workflows lost write-permission lines: {missing_lines}"


def test_workflow_write_permissions_visibility_contract_keeps_lines_scoped_to_permissions_vocabulary() -> (
    None
):
    current = _workflows_with_write_permissions()

    unexpected_lines = []
    allowed_permission_names = {
        "actions",
        "attestations",
        "checks",
        "contents",
        "deployments",
        "discussions",
        "id-token",
        "issues",
        "models",
        "packages",
        "pages",
        "pull-requests",
        "security-events",
        "statuses",
    }

    for workflow, lines in current.items():
        for line in lines:
            key = _permission_line_key(line)
            if key not in allowed_permission_names:
                unexpected_lines.append(f"{workflow}: {line}")

    assert not unexpected_lines, f"unexpected write-permission line shape: {unexpected_lines}"


def test_workflow_write_permissions_visibility_contract_retains_static_local_scope() -> None:
    test_text = Path(__file__).read_text(encoding="utf-8")

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


def test_cybersecurity_visibility_r001_derived_evidence_owner_crosslink_v0() -> None:
    """R-001 mapped-by-derived-evidence owner crosslink for Cybersecurity Visibility Chain."""
    ci_audit_text = (REPO_ROOT / "docs" / "ops" / "CI_AUDIT_KNOWN_ISSUES.md").read_text(
        encoding="utf-8"
    )
    ci_collapsed = ci_audit_text.lower()
    truth_map_text = (
        REPO_ROOT / "docs" / "ops" / "registry" / "DOCS_TRUTH_MAP.md"
    ).read_text(encoding="utf-8")
    truth_collapsed = truth_map_text.lower()
    module_name = Path(__file__).name

    assert "R-001" in ci_audit_text
    assert module_name in ci_audit_text
    assert "DERIVED-CYBER-R-001-001" in ci_audit_text
    assert "mapped-by-derived-evidence" in ci_collapsed
    assert "INPUT_JSONL_PROVIDED=false" in ci_audit_text
    assert "DEFINITIVE_R001_R002_R007_MAPPING_BLOCKED=true" in ci_audit_text
    assert "non-authorizing" in ci_collapsed

    assert module_name in truth_map_text
    assert "mapped-by-derived-evidence" in truth_collapsed
    assert "DERIVED_ONLY_MAPPING_WAVE1_BATCH_CLOSURE_V0=true" in truth_map_text
    assert "non-authorizing" in truth_collapsed
