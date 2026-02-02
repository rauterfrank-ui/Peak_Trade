from __future__ import annotations

import socket
from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class PortCheckResult:
    port: int
    host: str = "127.0.0.1"
    is_free: bool = True
    detail: str = ""


def is_tcp_port_free(port: int, host: str = "127.0.0.1") -> PortCheckResult:
    """
    Checks if a TCP port can be bound on (host, port).
    Deterministic, no external deps, works on macOS/Linux.
    """
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((host, port))
        return PortCheckResult(port=port, host=host, is_free=True, detail="bind_ok")
    except OSError as e:
        return PortCheckResult(port=port, host=host, is_free=False, detail=f"bind_failed: {e}")
    finally:
        try:
            s.close()
        except Exception:
            pass


def ensure_tcp_port_free(port: int, *, host: str = "127.0.0.1", context: str = "") -> None:
    r = is_tcp_port_free(port, host=host)
    if not r.is_free:
        ctx = f" context={context}" if context else ""
        raise RuntimeError(f"Port {host}:{port} is already in use ({r.detail}).{ctx}")
