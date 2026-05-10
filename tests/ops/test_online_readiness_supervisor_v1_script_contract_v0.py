"""Static contract tests for scripts/ops/online_readiness_supervisor_v1.sh.

Parses the supervisor bash driver as UTF-8 text only. Never starts/stops
supervisors, schedulers, daemons, runtime, paper/shadow/testnet/live,
broker/exchange, order-submission paths, workflows, or network I/O.
"""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "scripts" / "ops" / "online_readiness_supervisor_v1.sh"


def _script_text() -> str:
    return SCRIPT.read_text(encoding="utf-8")


def test_online_readiness_supervisor_v1_contract_target_present() -> None:
    assert SCRIPT.exists()
    assert SCRIPT.is_file()


def test_online_readiness_supervisor_v1_contract_module_avoids_execution_hooks() -> None:
    lines = Path(__file__).read_text(encoding="utf-8").splitlines()
    stripped = [ln.strip() for ln in lines]
    banned_starts = (
        "import os",
        "from os ",
        "from os\t",
        "import subprocess",
        "from subprocess ",
        "from subprocess\t",
        "import runpy",
        "from runpy ",
        "from runpy\t",
        "import importlib",
        "from importlib ",
        "from importlib\t",
        "import requests",
        "from requests",
        "import httpx",
        "from httpx",
        "import urllib",
        "from urllib",
        "import socket",
        "from socket ",
        "from socket\t",
    )
    hits = [ln for ln in stripped if ln.startswith(banned_starts)]
    assert not hits, f"unexpected execution/network-hook imports: {hits}"


def test_online_readiness_supervisor_v1_contract_has_strict_shell_guards() -> None:
    text = _script_text()

    assert "#!/usr/bin/env bash" in text
    assert "set -euo pipefail" in text


def test_online_readiness_supervisor_v1_contract_requires_explicit_enable_flag() -> None:
    text = _script_text()

    required_markers = ("SUPERVISOR_ENABLE", "YES")
    missing = [marker for marker in required_markers if marker not in text]
    assert not missing, f"missing explicit supervisor enable markers: {missing}"


def test_online_readiness_supervisor_v1_contract_constrains_modes_to_paper_or_shadow() -> None:
    text = _script_text().lower()

    required_markers = ("paper", "shadow")
    missing = [marker for marker in required_markers if marker not in text]
    assert not missing, f"missing expected non-live mode markers: {missing}"

    forbidden_mode_markers = (
        "mode=live",
        'mode="live"',
        "mode='live'",
        "live)",
    )

    found = [marker for marker in forbidden_mode_markers if marker in text]
    assert not found, f"supervisor contract must not expose live as a mode: {found}"


def test_online_readiness_supervisor_v1_contract_requires_explicit_paper_allowance() -> None:
    text = _script_text()

    required_markers = ("SUPERVISOR_ALLOW_PAPER", "paper")
    missing = [marker for marker in required_markers if marker not in text]
    assert not missing, f"missing explicit paper allowance markers: {missing}"


def test_online_readiness_supervisor_v1_contract_preserves_interval_and_iteration_controls() -> (
    None
):
    text = _script_text()

    required_markers = ("INTERVAL", "ITERATIONS")
    missing = [marker for marker in required_markers if marker not in text]
    assert not missing, f"missing supervisor loop control markers: {missing}"


def test_online_readiness_supervisor_v1_contract_preserves_output_and_log_surface() -> None:
    text = _script_text()

    required_markers = ("OUT_DIR", "P78_SUPERVISOR.ndjson", "supervisor_meta.json")
    missing = [marker for marker in required_markers if marker not in text]
    assert not missing, f"missing supervisor output/log markers: {missing}"


def test_online_readiness_supervisor_v1_contract_preserves_tick_observability_surface() -> None:
    text = _script_text()

    required_markers = ("tick", "P78_TICK")
    missing = [marker for marker in required_markers if marker not in text]
    assert not missing, f"missing tick observability markers: {missing}"


def test_online_readiness_supervisor_v1_contract_preserves_gate_selection_surface() -> None:
    text = _script_text()

    expected_markers = (
        "CHECK_MODE",
        "p86",
        "p76",
        "p86_gate_v1.sh",
        "online_readiness_go_no_go_v1.sh",
    )

    missing = [marker for marker in expected_markers if marker not in text]
    assert not missing, f"missing gate selection markers: {missing}"


def test_online_readiness_supervisor_v1_contract_does_not_directly_submit_orders() -> None:
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
    assert not found, f"supervisor must not directly submit trading orders: {found}"


def test_online_readiness_supervisor_v1_contract_does_not_dispatch_workflows_directly() -> None:
    text = _script_text().lower()

    forbidden_fragments = (
        "gh workflow run",
        "gh run rerun",
        "workflow_dispatch",
    )

    found = [fragment for fragment in forbidden_fragments if fragment in text]
    assert not found, f"supervisor must not directly dispatch workflows: {found}"


def test_online_readiness_supervisor_v1_contract_does_not_use_unscoped_destructive_cleanup() -> (
    None
):
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
    assert not found, f"supervisor contains unscoped destructive cleanup: {found}"


def test_online_readiness_supervisor_v1_contract_keeps_live_authority_absent_or_gated() -> None:
    text = _script_text().lower()

    sensitive_markers = (
        " live",
        "live_",
        "broker",
        "exchange",
        "order",
        "testnet",
    )

    if not any(marker in text for marker in sensitive_markers):
        return

    guard_markers = (
        "paper",
        "shadow",
        "supervisor_enable",
        "supervisor_allow_paper",
        "check_mode",
        "abort",
        "exit 1",
    )

    present_guards = [marker for marker in guard_markers if marker in text]
    assert present_guards, "sensitive authority terms require visible gate/mode vocabulary"


def test_online_readiness_supervisor_v1_contract_has_no_hardcoded_secret_values() -> None:
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
        "password=",
    )

    found = [marker for marker in forbidden_secret_value_markers if marker in text]
    assert not found, f"supervisor must not hardcode secret-like values: {found}"
