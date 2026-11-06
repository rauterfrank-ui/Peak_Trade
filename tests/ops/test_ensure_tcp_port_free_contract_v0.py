"""Deterministic contract tests for ``ensure_tcp_port_free`` (v0).

No real sockets, subprocess, env toggles, or calls to the real
``is_tcp_port_free`` bind path — the probe is monkeypatched.
"""

from __future__ import annotations

import pytest

import src.ops.net.ports as ports
from src.ops.net.ports import PortCheckResult


def test_ensure_tcp_port_free_success_no_raise_and_forwards_host_port_contract_v0(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: list[tuple[int, str]] = []

    def fake_is_tcp_port_free(port: int, host: str = "127.0.0.1") -> PortCheckResult:
        captured.append((port, host))
        return PortCheckResult(port=port, host=host, is_free=True, detail="bind_ok")

    monkeypatch.setattr(ports, "is_tcp_port_free", fake_is_tcp_port_free)

    ports.ensure_tcp_port_free(18080, host="0.0.0.0")
    assert captured == [(18080, "0.0.0.0")]


def test_ensure_tcp_port_free_default_host_forwarded_contract_v0(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: list[tuple[int, str]] = []

    def fake_is_tcp_port_free(port: int, host: str = "127.0.0.1") -> PortCheckResult:
        captured.append((port, host))
        return PortCheckResult(port=port, host=host, is_free=True, detail="bind_ok")

    monkeypatch.setattr(ports, "is_tcp_port_free", fake_is_tcp_port_free)

    ports.ensure_tcp_port_free(19090)
    assert captured == [(19090, "127.0.0.1")]


def test_ensure_tcp_port_free_occupied_raises_runtime_error_with_detail_and_context_contract_v0(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_is_tcp_port_free(port: int, host: str = "127.0.0.1") -> PortCheckResult:
        return PortCheckResult(
            port=port,
            host=host,
            is_free=False,
            detail="bind_failed: synthetic busy",
        )

    monkeypatch.setattr(ports, "is_tcp_port_free", fake_is_tcp_port_free)

    with pytest.raises(RuntimeError) as exc_info:
        ports.ensure_tcp_port_free(443, host="10.0.0.1", context="preflight")

    msg = str(exc_info.value)
    assert "10.0.0.1:443" in msg
    assert "bind_failed: synthetic busy" in msg
    assert msg.endswith(" context=preflight")


def test_ensure_tcp_port_free_occupied_no_context_suffix_contract_v0(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_is_tcp_port_free(port: int, host: str = "127.0.0.1") -> PortCheckResult:
        return PortCheckResult(
            port=port,
            host=host,
            is_free=False,
            detail="busy",
        )

    monkeypatch.setattr(ports, "is_tcp_port_free", fake_is_tcp_port_free)

    with pytest.raises(RuntimeError) as exc_info:
        ports.ensure_tcp_port_free(8080, host="127.0.0.1")

    msg = str(exc_info.value)
    assert "127.0.0.1:8080" in msg
    assert "(busy)." in msg
    assert "context=" not in msg
