"""Cybersecurity baseline visibility: action refs + top-level permissions.

Parses workflow YAML files as UTF-8 text only. Never dispatches workflows,
never calls GitHub APIs, never executes scripts, and never touches runtime,
scheduler, daemon, paper/shadow/testnet/live, broker/exchange, or order paths.

Fail-closed:
- every `uses:` must be pinned (has `@…`)
- no floating mutable action refs (`@main` / `@master` / `@latest` / `@head`)

Visibility (frozen inventories — update deliberately with docs when changing):
- workflows missing top-level `permissions:`
- SHA-pin count remains documented (currently zero; tag pins accepted)
"""

from __future__ import annotations

import re
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
WORKFLOW_ROOT = REPO_ROOT / ".github" / "workflows"
SECURITY_NOTES = REPO_ROOT / "SECURITY_NOTES.md"
CI_GHA_AUDIT_INDEX = (
    REPO_ROOT / "docs" / "ops" / "CI_GITHUB_ACTIONS_PERMISSIONS_SECRETS_ARTIFACTS_AUDIT_INDEX_V0.md"
)

USES_REF_RX = re.compile(r"^\s*uses:\s*([^\s#]+)", re.MULTILINE)
FLOATING_REF_RX = re.compile(r"@(?:main|master|latest|head)\s*$", re.IGNORECASE)
SHA_PIN_RX = re.compile(r"@[0-9a-f]{40}$", re.IGNORECASE)
TOP_LEVEL_PERMISSIONS_RX = re.compile(r"^permissions\s*:", re.MULTILINE)

# Frozen 2026-07-23 inventory — add/remove only with deliberate baseline docs update.
KNOWN_WORKFLOWS_MISSING_TOP_LEVEL_PERMISSIONS = frozenset(
    {
        "add-to-project.yml",
        "ai-model-cards-validate.yml",
        "aiops-promptfoo-evals.yml",
        "audit.yml",
        "ci-export-pack-download-verify.yml",
        "ci-operator-verify-registry.yml",
        "ci-pr-merge-state-signal.yml",
        "ci-workflow-dispatch-guard.yml",
        "ci.yml",
        "ci_recon_audit_gate_smoke.yml",
        "deps_sync_guard.yml",
        "docs-token-policy-gate.yml",
        "docs_diff_guard_policy_gate.yml",
        "docs_reference_targets_fullscan_schedule.yml",
        "docs_reference_targets_gate.yml",
        "docs_reference_targets_trend.yml",
        "events_schema_smoke.yml",
        "evidence_pack_gate.yml",
        "full_audit_weekly.yml",
        "guard-reports-ignored.yml",
        "infostream-automation.yml",
        "knowledge_extras_chromadb.yml",
        "l4_critic_replay_determinism.yml",
        "lint.yml",
        "market_outlook_automation.yml",
        "master_v2_dry_smoke.yml",
        "mcp_smoke_preflight.yml",
        "merge_log_hygiene.yml",
        "offline_suites.yml",
        "optional-deps-gate.yml",
        "quarto_smoke.yml",
        "replay_compare_report.yml",
        "required-checks-hygiene-gate.yml",
        "test-health-automation.yml",
        "test_health.yml",
        "truth_gates_pr.yml",
        "typecheck-mypy.yml",
        "typecheck-pyright.yml",
        "var_report_regression_gate.yml",
    }
)

EXPECTED_SHA_PIN_COUNT = 0


def _workflow_files() -> list[Path]:
    return sorted(
        path
        for pattern in ("*.yml", "*.yaml")
        for path in WORKFLOW_ROOT.glob(pattern)
        if path.is_file()
    )


def _workflow_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _uses_refs(text: str) -> list[str]:
    return [m.group(1).strip() for m in USES_REF_RX.finditer(text)]


def _workflows_missing_top_level_permissions() -> set[str]:
    missing: set[str] = set()
    for path in _workflow_files():
        if not TOP_LEVEL_PERMISSIONS_RX.search(_workflow_text(path)):
            missing.add(path.name)
    return missing


def test_cybersecurity_baseline_contract_has_workflows_to_check() -> None:
    workflows = _workflow_files()
    assert WORKFLOW_ROOT.exists()
    assert workflows


def test_cybersecurity_baseline_contract_module_avoids_execution_hooks() -> None:
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
    assert not found, f"static baseline contract must not import execution/network hooks: {found}"


def test_cybersecurity_baseline_action_refs_are_pinned_and_not_floating() -> None:
    floating: list[tuple[str, str]] = []
    unpinned: list[tuple[str, str]] = []
    sha_pins = 0

    for path in _workflow_files():
        for ref in _uses_refs(_workflow_text(path)):
            if "@" not in ref:
                unpinned.append((path.name, ref))
                continue
            if FLOATING_REF_RX.search(ref):
                floating.append((path.name, ref))
            if SHA_PIN_RX.search(ref):
                sha_pins += 1

    assert not unpinned, f"unpinned uses: refs are forbidden: {unpinned}"
    assert not floating, f"floating mutable uses: refs are forbidden: {floating}"
    assert sha_pins == EXPECTED_SHA_PIN_COUNT, (
        f"SHA-pin count drift: expected {EXPECTED_SHA_PIN_COUNT}, got {sha_pins}. "
        "Update EXPECTED_SHA_PIN_COUNT and SECURITY_NOTES / CI GHA audit index deliberately."
    )


def test_cybersecurity_baseline_missing_top_level_permissions_inventory_frozen() -> None:
    actual = _workflows_missing_top_level_permissions()
    assert actual == set(KNOWN_WORKFLOWS_MISSING_TOP_LEVEL_PERMISSIONS), (
        "top-level permissions inventory drifted; update frozen set with deliberate docs refresh. "
        f"added={sorted(actual - set(KNOWN_WORKFLOWS_MISSING_TOP_LEVEL_PERMISSIONS))} "
        f"removed={sorted(set(KNOWN_WORKFLOWS_MISSING_TOP_LEVEL_PERMISSIONS) - actual)}"
    )


def test_cybersecurity_baseline_docs_anchors_present() -> None:
    notes = SECURITY_NOTES.read_text(encoding="utf-8")
    index = CI_GHA_AUDIT_INDEX.read_text(encoding="utf-8")

    assert "PEAK_TRADE_CYBERSECURITY_BASELINE_REFRESH_V1" in notes
    assert "RR-CB-001" in notes
    assert "Action pinning posture" in index
    assert (
        "test_cybersecurity_baseline_action_ref_and_permissions_visibility_contract_v0.py" in index
    )
    assert "PEAK_TRADE_CYBERSECURITY_BASELINE_REFRESH_V1" in index
