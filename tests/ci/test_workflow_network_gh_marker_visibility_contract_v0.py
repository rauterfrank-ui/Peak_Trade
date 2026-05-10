"""Static visibility contract for workflow curl/wget/gh markers.

Parses workflow YAML files as UTF-8 text only. Never dispatches workflows,
never calls GitHub APIs, never executes scripts, and never touches runtime,
scheduler, daemon, paper/shadow/testnet/live, broker/exchange, or order paths.

This contract freezes the current workflow network/GitHub-CLI marker inventory
as an owner-review surface. It does not require workflow YAML changes and does
not treat the current set as a new hard failure without owner decision.
"""

from __future__ import annotations

import re
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
WORKFLOW_ROOT = REPO_ROOT / ".github" / "workflows"

KNOWN_WORKFLOWS_WITH_NETWORK_OR_GH_MARKERS = frozenset(
    {
        "aiops-trend-ledger-from-seed.yml",
        "ci-operator-verify-registry.yml",
        "ci-scheduled-paper-and-export-smoke.yml",
        "policy_critic.yml",
        "prbd-live-readiness-scorecard.yml",
        "prbe-shadow-testnet-scorecard.yml",
        "prbg-execution-evidence.yml",
        "prbi-live-pilot-scorecard.yml",
        "prk-prj-status-report.yml",
    }
)

_CURL_RX = re.compile(r"\bcurl\b", re.I)
_WGET_RX = re.compile(r"\bwget\b", re.I)
_GH_RX = re.compile(r"\bgh\s+")


def _workflow_files() -> list[Path]:
    return sorted(
        path
        for pattern in ("*.yml", "*.yaml")
        for path in WORKFLOW_ROOT.glob(pattern)
        if path.is_file()
    )


def _workflow_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _network_or_gh_signals(path: Path) -> set[str]:
    text = _workflow_text(path)
    signals: set[str] = set()

    if _CURL_RX.search(text):
        signals.add("curl")
    if _WGET_RX.search(text):
        signals.add("wget")
    if _GH_RX.search(text):
        signals.add("gh")

    return signals


def _workflows_with_network_or_gh_markers() -> dict[str, set[str]]:
    result: dict[str, set[str]] = {}

    for workflow in _workflow_files():
        signals = _network_or_gh_signals(workflow)
        if signals:
            result[workflow.name] = signals

    return result


def test_workflow_network_gh_marker_visibility_contract_has_workflows_to_check() -> None:
    workflows = _workflow_files()

    assert WORKFLOW_ROOT.exists()
    assert workflows


def test_workflow_network_gh_marker_visibility_contract_module_avoids_execution_hooks() -> None:
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


def test_workflow_network_gh_marker_visibility_contract_classifies_current_set() -> None:
    current = frozenset(_workflows_with_network_or_gh_markers())

    assert current == KNOWN_WORKFLOWS_WITH_NETWORK_OR_GH_MARKERS


def test_workflow_network_gh_marker_visibility_contract_known_set_stays_documentary() -> None:
    """The known set is an owner-review surface, not a workflow-change mandate."""
    assert len(KNOWN_WORKFLOWS_WITH_NETWORK_OR_GH_MARKERS) == 9


def test_workflow_network_gh_marker_visibility_contract_requires_signals_for_known_set() -> None:
    current = _workflows_with_network_or_gh_markers()

    missing_signals = [
        workflow
        for workflow in KNOWN_WORKFLOWS_WITH_NETWORK_OR_GH_MARKERS
        if not current.get(workflow)
    ]

    assert not missing_signals, f"known workflows lost network/GH marker signals: {missing_signals}"


def test_workflow_network_gh_marker_visibility_contract_records_signal_vocabulary() -> None:
    current = _workflows_with_network_or_gh_markers()
    all_signals = set().union(*current.values()) if current else set()

    assert all_signals <= {"curl", "wget", "gh"}
    assert all_signals


def test_workflow_network_gh_marker_visibility_contract_retains_static_local_scope() -> None:
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
