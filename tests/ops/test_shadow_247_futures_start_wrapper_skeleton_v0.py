"""Static/offline guards for Shadow 247 Futures default-off start-wrapper skeleton v0."""

from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "scripts" / "ops" / "shadow_247_futures_start_wrapper_skeleton_v0.py"
SRC_TEXT = SCRIPT.read_text(encoding="utf-8")


def test_shadow_247_futures_wrapper_skeleton_script_exists() -> None:
    assert SCRIPT.is_file(), "expected skeleton under scripts/ops/"


@pytest.mark.parametrize(
    "forbidden_snippet",
    [
        "ccxt",
        "requests",
        "aiohttp",
        "websocket",
        "binance",
        "subprocess",
        "os.system",
        "Popen",
        "urllib.request",
        "socket",
    ],
)
def test_shadow_247_futures_wrapper_skeleton_source_has_no_blocked_substrings(
    forbidden_snippet: str,
) -> None:
    assert forbidden_snippet not in SRC_TEXT.lower()


@pytest.mark.parametrize(
    "marker",
    [
        "BOUNDARY_NO_LIVE",
        "BOUNDARY_NO_TESTNET_UNLESS_APPROVED",
        "BOUNDARY_NO_BROKER",
        "BOUNDARY_NO_PRIVATE_EXCHANGE",
        "BOUNDARY_NO_ORDER_SUBMISSION",
        "BOUNDARY_NO_NETWORK",
        "BOUNDARY_FUTURES_PERP_SCOPE",
        "/tmp/peak_trade",
        "NO_ORDER_SUBMISSION",
    ],
)
def test_shadow_247_futures_wrapper_skeleton_has_boundary_constants(marker: str) -> None:
    assert marker in SRC_TEXT


def test_shadow_247_futures_wrapper_skeleton_import_has_no_side_effects(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("PYTHONINSPECT", raising=False)

    spec = importlib.util.spec_from_file_location(
        "_skel_under_test_shadow_247",
        SCRIPT,
    )
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    assert hasattr(mod, "main")
    assert mod.EXIT_FAIL_CLOSED_DEFAULT == 64


def test_shadow_247_futures_wrapper_skeleton_default_returns_64(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(REPO_ROOT)
    proc = subprocess.run(
        [sys.executable, str(SCRIPT)],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
        timeout=10,
    )
    assert proc.returncode == 64
    combo = proc.stderr + proc.stdout
    assert "FAIL-CLOSED" in combo or "fail-closed" in combo.lower() or "SKELETON" in combo
    assert "RUN_STARTED=false" in combo


def test_shadow_247_futures_wrapper_skeleton_correct_token_still_returns_64(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(REPO_ROOT)
    token = "I_EXPLICITLY_CONFIRM_SHADOW_247_FUTURES_START_WRAPPER_BEYOND_DEFAULT_OFF_SKELETON_V0"
    proc = subprocess.run(
        [sys.executable, str(SCRIPT), "--confirm-token", token],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
        timeout=10,
    )
    assert proc.returncode == 64


def test_shadow_247_futures_wrapper_skeleton_evidence_root_invalid_returns_64(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(REPO_ROOT)
    proc = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--evidence-root",
            "/var/tmp/forbidden_peak_trade_fake",
        ],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
        timeout=10,
    )
    assert proc.returncode == 64
    assert "peak_trade" in (proc.stderr + proc.stdout)


def test_shadow_247_futures_wrapper_skeleton_evidence_root_valid_prefix_still_returns_64(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(REPO_ROOT)
    proc = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--evidence-root",
            "/tmp/peak_trade_shadow_247_skeleton_probe",
        ],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
        timeout=10,
    )
    assert proc.returncode == 64


def test_shadow_247_futures_wrapper_skeleton_future_token_marker_in_source_only() -> None:
    marker = "I_EXPLICITLY_CONFIRM_SHADOW_247_FUTURES_START_WRAPPER_BEYOND_DEFAULT_OFF_SKELETON_V0"
    assert marker in SRC_TEXT
    assert "FUTURE_OPERATOR_CONFIRMATION_TOKEN_V0" in SRC_TEXT


def test_shadow_247_futures_wrapper_skeleton_machine_lines_include_flags() -> None:
    monkeypatch_locals = subprocess.run(
        [sys.executable, str(SCRIPT), "--inspect"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
        timeout=10,
    )
    combo = monkeypatch_locals.stdout + monkeypatch_locals.stderr
    assert monkeypatch_locals.returncode == 64
    assert "BOUNDARY_NO_LIVE" in combo
    assert "RUN_STARTED=false" in combo
    assert "SCHEDULER_STARTED=false" in combo
