"""Static visibility contract for manual-dispatch workflows with sensitive surfaces.

Parses workflow YAML files as UTF-8 text only. Never dispatches workflows,
never calls GitHub APIs, never executes scripts, and never touches runtime,
scheduler, daemon, paper/shadow/testnet/live, broker/exchange, or order paths.

This contract freezes the current manual-dispatch + sensitive-surface inventory
as an owner-review surface. It does not require workflow YAML changes and does
not treat the current set as a new hard failure without owner decision.

Follow-up (workflow_dispatch_input_metadata_visibility_v1): best-effort
``required`` / ``type`` / ``default`` fields under each ``workflow_dispatch`` input
key (indent-heuristic only). Missing or unrecognized metadata stays ``None``.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any


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


_SENSITIVE_INPUT_NAME_MARKERS: tuple[str, ...] = (
    "token",
    "secret",
    "password",
    "key",
    "credential",
    "auth",
    "live",
    "testnet",
    "broker",
    "exchange",
    "order",
    "deploy",
    "publish",
)


def _extract_workflow_dispatch_input_keys(text: str) -> list[str]:
    """Best-effort keys under ``workflow_dispatch`` → ``inputs`` (indent-heuristic).

    GitHub Actions-shaped YAML only; avoids PyYAML. Multiple ``workflow_dispatch``
    blocks in one file are merged in document order.
    """
    lines = text.splitlines()
    collected: list[str] = []
    i = 0
    while i < len(lines):
        m_dispatch = re.match(r"^(\s*)workflow_dispatch\s*:", lines[i])
        if not m_dispatch:
            i += 1
            continue
        indent_d = len(m_dispatch.group(1))
        i += 1
        inputs_indent: int | None = None
        child_indent: int | None = None
        while i < len(lines):
            raw = lines[i]
            if not raw.strip():
                i += 1
                continue
            indent = len(raw) - len(raw.lstrip(" \t"))
            if raw.strip().startswith("#"):
                i += 1
                continue
            if indent <= indent_d:
                break
            if inputs_indent is None:
                if re.match(r"^\s*inputs\s*:", raw):
                    inputs_indent = indent
                i += 1
                continue
            if indent <= inputs_indent:
                break
            m_key = re.match(r"^\s*([A-Za-z0-9_-]+)\s*:\s*(?:#.*)?$", raw)
            if m_key:
                if child_indent is None:
                    child_indent = indent
                elif indent < child_indent:
                    break
                if indent == child_indent:
                    collected.append(m_key.group(1))
            i += 1
    return collected


def _strip_yaml_scalar_quotes(value: str) -> str:
    if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
        return value[1:-1]
    return value


def _consume_input_metadata_lines(
    lines: list[str], start: int, input_key_indent: int
) -> tuple[dict[str, Any], int]:
    """Parse nested lines under one ``inputs.<name>:`` key until next sibling input."""
    required: bool | None = None
    typ: str | None = None
    default: str | None = None
    j = start
    while j < len(lines):
        raw = lines[j]
        if not raw.strip():
            j += 1
            continue
        indent = len(raw) - len(raw.lstrip(" \t"))
        if raw.strip().startswith("#"):
            j += 1
            continue
        if indent <= input_key_indent:
            break
        stripped = raw.strip()
        m_req = re.match(r"^required\s*:\s*(true|false)\s*$", stripped, re.I)
        if m_req:
            required = m_req.group(1).lower() == "true"
            j += 1
            continue
        m_type = re.match(r"^type\s*:\s*(.+?)\s*$", stripped)
        if m_type:
            typ = _strip_yaml_scalar_quotes(m_type.group(1).strip())
            j += 1
            continue
        m_def = re.match(r"^default\s*:\s*(.*)$", stripped)
        if m_def:
            default = _strip_yaml_scalar_quotes(m_def.group(1).strip())
            j += 1
            continue
        j += 1
    return {"required": required, "type": typ, "default": default}, j


def _extract_workflow_dispatch_inputs_metadata(text: str) -> dict[str, dict[str, Any]]:
    """Best-effort metadata map per input key (merged across dispatch blocks in order)."""
    lines = text.splitlines()
    result: dict[str, dict[str, Any]] = {}
    i = 0
    while i < len(lines):
        m_dispatch = re.match(r"^(\s*)workflow_dispatch\s*:", lines[i])
        if not m_dispatch:
            i += 1
            continue
        indent_d = len(m_dispatch.group(1))
        i += 1
        inputs_indent: int | None = None
        child_indent: int | None = None
        while i < len(lines):
            raw = lines[i]
            if not raw.strip():
                i += 1
                continue
            indent = len(raw) - len(raw.lstrip(" \t"))
            if raw.strip().startswith("#"):
                i += 1
                continue
            if indent <= indent_d:
                break
            if inputs_indent is None:
                if re.match(r"^\s*inputs\s*:", raw):
                    inputs_indent = indent
                i += 1
                continue
            if indent <= inputs_indent:
                break
            m_key = re.match(r"^\s*([A-Za-z0-9_-]+)\s*:\s*(?:#.*)?$", raw)
            if m_key:
                if child_indent is None:
                    child_indent = indent
                elif indent < child_indent:
                    break
                if indent == child_indent:
                    key = m_key.group(1)
                    meta, j = _consume_input_metadata_lines(lines, i + 1, child_indent)
                    result[key] = meta
                    i = j
                    continue
            i += 1
    return result


def _inputs_metadata_for_inventory(text: str, keys: list[str]) -> dict[str, dict[str, Any]]:
    raw_meta = _extract_workflow_dispatch_inputs_metadata(text)
    return {
        k: dict(raw_meta[k]) if k in raw_meta else {"required": None, "type": None, "default": None}
        for k in keys
    }


def _input_keys_flagged_for_sensitive_name_markers(keys: list[str]) -> list[str]:
    flagged: list[str] = []
    for key in keys:
        lowered = key.lower()
        if any(marker in lowered for marker in _SENSITIVE_INPUT_NAME_MARKERS):
            flagged.append(key)
    return sorted(flagged)


def _workflow_dispatch_inputs_inventory_v1() -> dict[str, dict[str, Any]]:
    inventory: dict[str, dict[str, Any]] = {}

    for workflow in _workflow_files():
        text = _workflow_text(workflow)
        if not _has_workflow_dispatch(text):
            continue
        keys = sorted(set(_extract_workflow_dispatch_input_keys(text)))
        inventory[workflow.name] = {
            "workflow_dispatch_present": True,
            "input_keys": keys,
            "sensitive_input_name_markers": _input_keys_flagged_for_sensitive_name_markers(keys),
            "defines_inputs_block": bool(keys),
            "inputs_metadata": _inputs_metadata_for_inventory(text, keys),
        }

    return inventory


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


def test_workflow_dispatch_inputs_visibility_followup_v1_inventory_shape() -> None:
    inventory = _workflow_dispatch_inputs_inventory_v1()

    assert inventory
    for filename, row in inventory.items():
        assert filename.endswith((".yml", ".yaml"))
        assert row["workflow_dispatch_present"] is True
        assert isinstance(row["input_keys"], list)
        assert isinstance(row["sensitive_input_name_markers"], list)
        assert isinstance(row["defines_inputs_block"], bool)
        assert isinstance(row["inputs_metadata"], dict)
        assert list(row["inputs_metadata"]) == sorted(row["inputs_metadata"])
        for in_key, meta in row["inputs_metadata"].items():
            assert in_key in row["input_keys"]
            assert set(meta.keys()) == {"required", "type", "default"}
            assert meta["required"] is None or isinstance(meta["required"], bool)
            assert meta["type"] is None or isinstance(meta["type"], str)
            assert meta["default"] is None or isinstance(meta["default"], str)


def test_workflow_dispatch_inputs_visibility_followup_v1_some_workflows_define_inputs() -> None:
    inventory = _workflow_dispatch_inputs_inventory_v1()
    assert any(row["defines_inputs_block"] for row in inventory.values())


def test_workflow_dispatch_inputs_visibility_followup_v1_prcd_write_smoke_lists_confirm_token() -> (
    None
):
    inventory = _workflow_dispatch_inputs_inventory_v1()
    row = inventory.get("prcd-aws-export-write-smoke.yml")
    assert row is not None
    assert "confirm_token" in row["input_keys"]
    assert "confirm_token" in row["sensitive_input_name_markers"]


def test_workflow_dispatch_inputs_visibility_followup_v1_weekly_audit_lists_note_input() -> None:
    inventory = _workflow_dispatch_inputs_inventory_v1()
    row = inventory.get("weekly_core_audit.yml")
    assert row is not None
    assert "note" in row["input_keys"]


_SYNTHETIC_DISPATCH_INPUT_METADATA = (
    "on:\n"
    "  workflow_dispatch:\n"
    "    inputs:\n"
    "      alpha:\n"
    "        description: sample\n"
    "        required: true\n"
    "        type: string\n"
    "        default: 'hello'\n"
    "      beta:\n"
    "        required: false\n"
    '        default: ""\n'
)


def test_workflow_dispatch_input_metadata_visibility_v1_parser_synthetic_snippet() -> None:
    meta = _extract_workflow_dispatch_inputs_metadata(_SYNTHETIC_DISPATCH_INPUT_METADATA)
    assert meta["alpha"]["required"] is True
    assert meta["alpha"]["type"] == "string"
    assert meta["alpha"]["default"] == "hello"
    assert meta["beta"]["required"] is False
    assert meta["beta"]["type"] is None
    assert meta["beta"]["default"] == ""


def test_workflow_dispatch_input_metadata_visibility_v1_inventory_sorted_deterministic() -> None:
    first = _workflow_dispatch_inputs_inventory_v1()
    second = _workflow_dispatch_inputs_inventory_v1()
    assert first == second


def test_workflow_dispatch_input_metadata_visibility_v1_prcd_confirm_token_metadata_smoke() -> None:
    inventory = _workflow_dispatch_inputs_inventory_v1()
    row = inventory.get("prcd-aws-export-write-smoke.yml")
    assert row is not None
    meta = row["inputs_metadata"]["confirm_token"]
    assert meta["required"] is True
    assert meta["default"] == ""
    assert meta["type"] is None


def test_workflow_dispatch_input_metadata_visibility_v1_weekly_note_metadata_smoke() -> None:
    inventory = _workflow_dispatch_inputs_inventory_v1()
    row = inventory.get("weekly_core_audit.yml")
    assert row is not None
    meta = row["inputs_metadata"]["note"]
    assert meta["required"] is False
    assert meta["default"] == "weekly core audit"
    assert meta["type"] is None
