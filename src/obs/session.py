from __future__ import annotations

from src.obs.metrics_config import get_metrics_port
from src.ops.net.ports import ensure_tcp_port_free


def start_session_http() -> None:
    """Start in-process /metrics HTTP server for a session (Mode A). Port from env; fails if port in use."""
    port = get_metrics_port(9111)
    ensure_tcp_port_free(port, context="obs_session_http")
    # TODO: start HTTP server on port
