"""P129 — Onramp CLI smoke tests."""

from __future__ import annotations

import json
import subprocess
import sys


def test_onramp_cli_default_deny_returns_json() -> None:
    """Default transport_allow=NO: flow completes, adapter denies, exit 0."""
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "src.execution.networked.onramp_cli_v1",
            "--mode",
            "shadow",
            "--intent",
            "place_order",
            "--market",
            "BTC-USD",
            "--qty",
            "0.01",
        ],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    data = json.loads(result.stdout)
    assert "meta" in data
    assert data["meta"]["transport_allow"] == "NO"
    assert data["meta"]["mode"] == "shadow"
    assert data["guards"]["rc"] == 0
    assert data["transport"]["rc"] == 0
    assert data["adapter"]["rc"] == 1
    assert "networked_send_denied" in data["adapter"]["msg"]


def test_onramp_cli_transport_allow_yes_exits_3() -> None:
    """transport_allow=YES: TransportGateError, exit 3."""
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "src.execution.networked.onramp_cli_v1",
            "--mode",
            "shadow",
            "--intent",
            "place_order",
            "--market",
            "BTC-USD",
            "--qty",
            "0.01",
            "--transport-allow",
            "YES",
        ],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 3
    data = json.loads(result.stdout)
    assert data["transport"]["rc"] == 3
    assert "TRANSPORT_GATE_DENY" in data["transport"]["msg"]


def test_onramp_cli_rejects_live_mode() -> None:
    """mode=live: guards fail, exit 1."""
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "src.execution.networked.onramp_cli_v1",
            "--mode",
            "live",
            "--intent",
            "place_order",
            "--market",
            "BTC-USD",
            "--qty",
            "0.01",
        ],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 1
    data = json.loads(result.stdout)
    assert data["guards"]["rc"] != 0
    assert "mode" in data["guards"]["msg"].lower()
