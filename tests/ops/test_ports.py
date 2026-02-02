"""Tests for src/ops/net/ports (port check / fail-fast for metricsd vs session)."""

from __future__ import annotations

import socket

import pytest

from src.ops.net.ports import ensure_tcp_port_free, is_tcp_port_free, PortCheckResult


def test_is_tcp_port_free_free_port() -> None:
    """Free port returns is_free=True."""
    r = is_tcp_port_free(0, host="127.0.0.1")  # 0 = any free port from OS
    # We actually need a fixed port to assert; use a high ephemeral to avoid flakiness
    r2 = is_tcp_port_free(39281, host="127.0.0.1")
    assert r2.is_free is True
    assert "bind_ok" in r2.detail or r2.detail == "bind_ok"


def test_ensure_tcp_port_free_raises_when_bound() -> None:
    """ensure_tcp_port_free raises RuntimeError when port is already in use."""
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
        s.bind(("127.0.0.1", 0))
        _host, port = s.getsockname()
        with pytest.raises(RuntimeError, match=r"Port .* is already in use"):
            ensure_tcp_port_free(port, host="127.0.0.1", context="test")
    finally:
        s.close()
