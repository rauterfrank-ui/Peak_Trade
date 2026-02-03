from __future__ import annotations

import socket

import pytest

from src.ops.net.ports import ensure_tcp_port_free


def _bind_ephemeral() -> tuple[socket.socket, int]:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(("127.0.0.1", 0))
    s.listen(1)
    port = s.getsockname()[1]
    return s, port


def test_ensure_tcp_port_free_raises_when_bound() -> None:
    s, port = _bind_ephemeral()
    try:
        with pytest.raises(RuntimeError):
            ensure_tcp_port_free(port, context="test")
    finally:
        s.close()
