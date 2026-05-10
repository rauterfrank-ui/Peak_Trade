"""Static visibility contract for GitHub workflow secrets references.

Parses workflow YAML files as UTF-8 text only. Never reads credential payloads,
never calls GitHub APIs, never dispatches workflows, never executes scripts,
and never touches runtime, scheduler, daemon, paper/shadow/testnet/live,
broker/exchange, or order-submission paths.

This contract freezes the current workflow `secrets.*` reference inventory as
an owner-review surface. It does not require workflow YAML changes and does
not treat the current set as a new hard failure without owner decision.
"""

from __future__ import annotations

import re
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
WORKFLOW_ROOT = REPO_ROOT / ".github" / "workflows"

SECRET_REF_RX = re.compile(r"\$\{\{\s*secrets\.([A-Za-z0-9_]+)\s*\}\}", re.I)
LOOSE_SECRETS_RX = re.compile(r"secrets\.", re.I)

KNOWN_WORKFLOWS_WITH_SECRETS_REFERENCES = frozenset(
    {
        "add-to-project.yml",
        "aiops-promptfoo-evals.yml",
        "ci-export-pack-download-verify.yml",
        "ci-operator-verify-registry.yml",
        "ci-scheduled-paper-and-export-smoke.yml",
        "ci.yml",
        "cursor_auto_automerge.yml",
        "cursor_auto_pr.yml",
        "infostream-automation.yml",
        "market_outlook_automation.yml",
        "paper_session_audit_evidence.yml",
        "paper_tests_audit_evidence.yml",
        "pr-head-sha-required-checks-liveness-guard.yml",
        "prbj-testnet-exec-events.yml",
        "prcc-aws-export-smoke.yml",
        "prcd-aws-export-write-smoke.yml",
    }
)

KNOWN_SECRET_REFERENCE_NAMES = frozenset(
    {
        "ADD_TO_PROJECT_PAT",
        "GITHUB_TOKEN",
        "KRAKEN_TESTNET_API_KEY",
        "KRAKEN_TESTNET_API_SECRET",
        "OPENAI_API_KEY",
        "PT_EXPORT_ID",
        "PT_EXPORT_PREFIX",
        "PT_EXPORT_REMOTE",
        "PT_RCLONE_CONF_B64",
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


def _secret_reference_names(text: str) -> set[str]:
    return set(m.upper() for m in SECRET_REF_RX.findall(text))


def _workflows_with_secrets_references() -> dict[str, set[str]]:
    result: dict[str, set[str]] = {}

    for workflow in _workflow_files():
        text = _workflow_text(workflow)
        names = _secret_reference_names(text)
        if names or LOOSE_SECRETS_RX.search(text):
            result[workflow.name] = names

    return result


def test_workflow_secrets_reference_visibility_contract_has_workflows_to_check() -> None:
    workflows = _workflow_files()

    assert WORKFLOW_ROOT.exists()
    assert workflows


def test_workflow_secrets_reference_visibility_contract_module_avoids_execution_hooks() -> None:
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


def test_workflow_secrets_reference_visibility_contract_classifies_current_workflow_set() -> None:
    current = frozenset(_workflows_with_secrets_references())

    assert current == KNOWN_WORKFLOWS_WITH_SECRETS_REFERENCES


def test_workflow_secrets_reference_visibility_contract_classifies_current_secret_names() -> None:
    current_names: set[str] = set()
    for names in _workflows_with_secrets_references().values():
        current_names.update(names)

    assert current_names == KNOWN_SECRET_REFERENCE_NAMES


def test_workflow_secrets_reference_visibility_contract_known_sets_stay_documentary() -> None:
    """Known sets are owner-review surfaces, not workflow-change mandates."""
    assert len(KNOWN_WORKFLOWS_WITH_SECRETS_REFERENCES) == 16
    assert len(KNOWN_SECRET_REFERENCE_NAMES) == 9


def test_workflow_secrets_reference_visibility_contract_requires_names_for_known_set() -> None:
    current = _workflows_with_secrets_references()

    missing = [
        workflow for workflow in KNOWN_WORKFLOWS_WITH_SECRETS_REFERENCES if workflow not in current
    ]

    assert not missing, f"known workflows lost secrets-reference visibility: {missing}"


def test_workflow_secrets_reference_visibility_contract_never_checks_secret_values() -> None:
    test_text = Path(__file__).read_text(encoding="utf-8").lower()

    forbidden_value_access_markers = [
        " ".join(("gh", "secret", "list")),
        " ".join(("gh", "secret", "view")),
        " ".join(("gh", "api")),
        " ".join(("secrets", "get")),
        "".join(("get_secret", "_value")),
    ]

    found = [marker for marker in forbidden_value_access_markers if marker in test_text]
    assert not found, f"contract must never access secret values: {found}"


def test_workflow_secrets_reference_visibility_contract_retains_static_local_scope() -> None:
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
