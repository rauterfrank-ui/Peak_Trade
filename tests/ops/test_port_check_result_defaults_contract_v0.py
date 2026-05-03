"""Contract tests for PortCheckResult default field values (v0).

No sockets, subprocess, env toggles, or calls to is_tcp_port_free /
ensure_tcp_port_free.
"""

from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from src.ops.net.ports import PortCheckResult


def test_port_check_result_defaults_contract_v0() -> None:
    r = PortCheckResult(port=49152)
    assert r.port == 49152
    assert r.host == "127.0.0.1"
    assert r.is_free is True
    assert r.detail == ""


def test_port_check_result_explicit_host_preserved_contract_v0() -> None:
    r = PortCheckResult(port=443, host="0.0.0.0", is_free=False, detail="busy")
    assert r.port == 443
    assert r.host == "0.0.0.0"
    assert r.is_free is False
    assert r.detail == "busy"


def test_port_check_result_frozen_contract_v0() -> None:
    r = PortCheckResult(port=1)
    with pytest.raises(FrozenInstanceError):
        r.host = "::1"  # type: ignore[misc]
