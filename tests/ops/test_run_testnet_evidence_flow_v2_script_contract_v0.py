"""Static contract tests for scripts/ops/run_testnet_evidence_flow_v2.sh.

Parses the bash driver as UTF-8 text only. Never invokes bash, testnet orchestrator,
GitHub CLI, workflows, scheduler, daemon, or runtime from this module.
"""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "scripts" / "ops" / "run_testnet_evidence_flow_v2.sh"


def _script_text() -> str:
    return SCRIPT.read_text(encoding="utf-8")


def test_run_testnet_evidence_flow_v2_contract_target_present() -> None:
    assert SCRIPT.exists()
    assert SCRIPT.is_file()


def test_run_testnet_evidence_flow_v2_contract_module_avoids_execution_hooks() -> None:
    lines = Path(__file__).read_text(encoding="utf-8").splitlines()
    stripped = [ln.strip() for ln in lines]
    banned_starts = (
        "import subprocess",
        "from subprocess ",
        "from subprocess\t",
        "import runpy",
        "from runpy ",
        "from runpy\t",
        "import importlib",
        "from importlib ",
        "from importlib\t",
        "import urllib",
        "from urllib",
        "import requests",
        "from requests",
        "import httpx",
        "from httpx",
        "import os",
        "from os ",
        "from os\t",
    )
    hits = [ln for ln in stripped if ln.startswith(banned_starts)]
    assert not hits, f"unexpected execution/network/fs-hook imports: {hits}"


def test_run_testnet_evidence_flow_v2_contract_has_strict_shell_guards() -> None:
    text = _script_text()

    assert "#!/usr/bin/env bash" in text
    assert "set -euo pipefail" in text


def test_run_testnet_evidence_flow_v2_contract_preserves_testnet_evidence_identity() -> None:
    text = _script_text().lower()

    required_markers = ("testnet", "evidence")
    missing = [marker for marker in required_markers if marker not in text]
    assert not missing, f"missing expected R-004 identity markers: {missing}"


def test_run_testnet_evidence_flow_v2_contract_has_operator_gate_vocabulary() -> None:
    text = _script_text().lower()

    gate_markers = (
        "dry",
        "allow",
        "enable",
        "enabled",
        "confirm",
        "armed",
        "abort",
        "exit 1",
        "paper",
        "testnet",
    )

    present = [marker for marker in gate_markers if marker in text]
    assert len(present) >= 3, f"expected visible operator/gate vocabulary, got: {present}"


def test_run_testnet_evidence_flow_v2_contract_preserves_output_or_evidence_surface() -> None:
    text = _script_text().lower()

    expected_markers = ("out/", "evidence")
    missing = [marker for marker in expected_markers if marker not in text]
    assert not missing, f"missing expected output/evidence markers: {missing}"


def test_run_testnet_evidence_flow_v2_contract_pins_core_python_entrypoints() -> None:
    text = _script_text()

    assert "scripts/orchestrate_testnet_runs.py" in text
    assert "scripts/ci/execution_evidence_producer.py" in text


def test_run_testnet_evidence_flow_v2_contract_pins_dispatch_chain_order() -> None:
    """PR-BG → PR-BE → PR-BI workflow filenames stay ordered for R-004 dispatch observability."""
    text = _script_text()

    workflows = (
        "prbg-execution-evidence.yml",
        "prbe-shadow-testnet-scorecard.yml",
        "prbi-live-pilot-scorecard.yml",
    )

    positions = [text.index(name) for name in workflows]
    assert positions == sorted(positions), "dispatch chain order drift"


def test_run_testnet_evidence_flow_v2_contract_documents_github_cli_dispatch_surface() -> None:
    text = _script_text()

    assert "gh workflow run" in text.lower()
    assert "gh run list" in text.lower()
    assert "gh run watch" in text.lower()
    assert "gh run download" in text.lower()
    assert "--ref main" in text


def test_run_testnet_evidence_flow_v2_contract_does_not_directly_submit_orders() -> None:
    text = _script_text().lower()

    forbidden_fragments = (
        "create_order(",
        ".create_order",
        "submit_order(",
        ".submit_order",
        "place_order(",
        ".place_order",
        "market_buy(",
        "market_sell(",
        "private_post_order",
        "futures_create_order",
        "binance.create_order",
        "exchange.create_order",
        "ccxt.",
    )

    found = [fragment for fragment in forbidden_fragments if fragment in text]
    assert not found, f"script must not directly submit trading orders: {found}"


def test_run_testnet_evidence_flow_v2_contract_does_not_use_unscoped_destructive_cleanup() -> None:
    text = _script_text().lower()

    forbidden_fragments = (
        "rm -rf /",
        'rm -rf "$repo_root"',
        "rm -rf '${repo_root}'",
        "rm -rf .git",
        "git clean -fdx",
        "git reset --hard",
    )

    found = [fragment for fragment in forbidden_fragments if fragment in text]
    assert not found, f"script contains unscoped destructive cleanup: {found}"


def test_run_testnet_evidence_flow_v2_contract_keeps_live_authority_gated_or_absent() -> None:
    text = _script_text().lower()

    sensitive_markers = (
        " live",
        "live_",
        "broker",
        "exchange",
        "order",
    )

    if not any(marker in text for marker in sensitive_markers):
        return

    guard_markers = (
        "dry",
        "testnet",
        "evidence",
        "allow",
        "enable",
        "confirm",
        "armed",
        "abort",
        "exit 1",
    )

    present_guards = [marker for marker in guard_markers if marker in text]
    assert present_guards, "sensitive authority terms require visible gate/evidence vocabulary"


def test_run_testnet_evidence_flow_v2_contract_has_no_hardcoded_secret_values() -> None:
    text = _script_text().lower()

    forbidden_secret_value_markers = (
        "aws_access_key_id=",
        "aws_secret_access_key=",
        "aws_session_token=",
        "-----begin private key-----",
        "bearer ",
        "api_key=",
        "apikey=",
        "secret_key=",
    )

    found = [marker for marker in forbidden_secret_value_markers if marker in text]
    assert not found, f"script must not hardcode secret-like values: {found}"
