from __future__ import annotations

from typing import Optional


def ensure_metrics_server(port: Optional[int] = None) -> bool:
    """
    Prometheus in-process /metrics HTTP server (CURRENT runtime detached).

    Callers may still invoke this hook; it never binds a port or starts a listener.
    """
    del port
    return False
