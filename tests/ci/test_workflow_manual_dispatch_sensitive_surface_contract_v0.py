"""Static visibility contract for manual-dispatch workflows with sensitive surfaces.

Parses workflow YAML files as UTF-8 text only. Never dispatches workflows,
never calls GitHub APIs, never executes scripts, and never touches runtime,
scheduler, daemon, paper/shadow/testnet/live, broker/exchange, or order paths.

This contract freezes the current manual-dispatch + sensitive-surface inventory
as an owner-review surface. It does not require workflow YAML changes and does
not treat the current set as a new hard failure without owner decision.
"""

from __future__ import annotations

import re
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
WORKFLOW_ROOT = REPO_ROOT / ".github" / "workflows"

KNOWN_MANUAL_DISPATCH_WORKFLOWS_WITH_SENSITIVE_SURFACES = frozenset(
    {
        "aiops-promptfoo-evals.yml",
        "aiops-trend-ledger-from-seed.yml",
        "audit.yml",
        "ci-export-pack-download-verify.yml",
        "ci-operator-verify-registry.yml",
        "ci-scheduled-paper-and-export-smoke.yml",
        "ci.yml",
        "class-a-shadow-paper-scheduled-probe-v1.yml",
        "cursor_auto_automerge.yml",
        "cursor_auto_pr.yml",
        "docs-token-policy-gate.yml",
        "evidence_pack_gate.yml",
        "full_audit_weekly.yml",
        "infostream-automation.yml",
        "knowledge_extras_chromadb.yml",
        "l4_critic_replay_determinism.yml",
        "market_outlook_automation.yml",
        "offline_suites.yml",
        "ops_doctor_dashboard.yml",
        "ops_doctor_pages.yml",
        "paper_session_audit_evidence.yml",
        "paper_session_telemetry_summary.yml",
        "paper_tests_audit_evidence.yml",
        "prbc-stability-gate.yml",
        "prbd-live-readiness-scorecard.yml",
        "prbe-shadow-testnet-scorecard.yml",
        "prbg-execution-evidence.yml",
        "prbi-live-pilot-scorecard.yml",
        "prbj-testnet-exec-events.yml",
        "prcc-aws-export-smoke.yml",
        "prcd-aws-export-write-smoke.yml",
        "prj-scheduled-shadow-paper-features-smoke.yml",
        "prk-prj-status-report.yml",
        "pro-prk-nightly-selfcheck.yml",
        "quarto_smoke.yml",
        "real-market-forward-evidence-smoke.yml",
        "replay_compare_report.yml",
        "shadow_paper_smoke.yml",
        "test-health-automation.yml",
        "test_health.yml",
        "var_report_regression_gate.yml",
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


def _has_workflow_dispatch(text: str) -> bool:
    return bool(re.search(r"^\s*workflow_dispatch\s*:", text, re.MULTILINE))


def _sensitive_signals(text: str) -> set[str]:
    signals: set[str] = set()

    if re.search(r"secrets\.", text, re.IGNORECASE):
        signals.add("secrets")
    if re.search(r":\s*write\b", text):
        signals.add("write_permissions")
    if "actions/upload-artifact" in text:
        signals.add("upload_artifact")
    if "actions/download-artifact" in text:
        signals.add("download_artifact")
    if re.search(r"GITHUB_TOKEN", text, re.IGNORECASE):
        signals.add("github_token")
    if re.search(r"\bgh\s+", text):
        signals.add("gh")
    if re.search(r"\b(curl|wget)\b", text, re.IGNORECASE):
        signals.add("curl_wget")

    return signals


def _manual_dispatch_workflows_with_sensitive_surfaces() -> dict[str, set[str]]:
    result: dict[str, set[str]] = {}

    for workflow in _workflow_files():
        text = _workflow_text(workflow)
        signals = _sensitive_signals(text)
        if _has_workflow_dispatch(text) and signals:
            result[workflow.name] = signals

    return result


def test_manual_dispatch_sensitive_surface_contract_has_workflows_to_check() -> None:
    workflows = _workflow_files()

    assert WORKFLOW_ROOT.exists()
    assert workflows


def test_manual_dispatch_sensitive_surface_contract_module_avoids_execution_hooks() -> None:
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


def test_manual_dispatch_sensitive_surface_contract_classifies_current_set() -> None:
    current = frozenset(_manual_dispatch_workflows_with_sensitive_surfaces())

    assert current == KNOWN_MANUAL_DISPATCH_WORKFLOWS_WITH_SENSITIVE_SURFACES


def test_manual_dispatch_sensitive_surface_contract_known_set_stays_documentary() -> None:
    """The known set is an owner-review surface, not a workflow-change mandate."""
    assert len(KNOWN_MANUAL_DISPATCH_WORKFLOWS_WITH_SENSITIVE_SURFACES) == 42


def test_manual_dispatch_sensitive_surface_contract_requires_signals_for_known_set() -> None:
    current = _manual_dispatch_workflows_with_sensitive_surfaces()

    missing_signals = [
        workflow
        for workflow in KNOWN_MANUAL_DISPATCH_WORKFLOWS_WITH_SENSITIVE_SURFACES
        if not current.get(workflow)
    ]

    assert not missing_signals, (
        f"known manual-dispatch workflows lost sensitive-surface signals: {missing_signals}"
    )


def test_manual_dispatch_sensitive_surface_contract_retains_static_local_scope() -> None:
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
