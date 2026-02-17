"""P113: Execution Router CLI smoke (mocks only)."""

from __future__ import annotations

import json
import subprocess
import sys


def test_cli_place_order_shadow() -> None:
    out = subprocess.run(
        [
            sys.executable,
            "-m",
            "src.execution.router.cli_v1",
            "--mode",
            "shadow",
            "--intent",
            "place_order",
            "--qty",
            "0.01",
        ],
        capture_output=True,
        text=True,
        cwd=".",
    )
    assert out.returncode == 0
    data = json.loads(out.stdout)
    assert data["meta"]["ok"] is True
    assert data["meta"]["mode"] == "shadow"
    assert data["meta"]["dry_run"] is True
    assert data["result"]["ok"] is True
    assert data["result"]["adapter"] == "mock"
    assert data["result"]["order_id"]


def test_cli_rejects_dry_run_no() -> None:
    """dry-run must be YES (mocks-only guard)."""
    out = subprocess.run(
        [
            sys.executable,
            "-m",
            "src.execution.router.cli_v1",
            "--mode",
            "shadow",
            "--dry-run",
            "NO",
            "--intent",
            "place_order",
            "--adapter",
            "mock",
            "--market",
            "BTC-USD",
            "--side",
            "buy",
            "--qty",
            "0.01",
        ],
        capture_output=True,
        text=True,
        cwd=".",
    )
    assert out.returncode == 3
    assert "ROUTER_CLI_GUARD_FAIL" in out.stdout or "ROUTER_CLI_GUARD_FAIL" in out.stderr


def test_cli_cancel_all_paper() -> None:
    out = subprocess.run(
        [
            sys.executable,
            "-m",
            "src.execution.router.cli_v1",
            "--mode",
            "paper",
            "--intent",
            "cancel_all",
        ],
        capture_output=True,
        text=True,
        cwd=".",
    )
    assert out.returncode == 0
    data = json.loads(out.stdout)
    assert data["meta"]["ok"] is True
    assert data["result"]["canceled"] >= 0
