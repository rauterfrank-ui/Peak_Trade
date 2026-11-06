from __future__ import annotations

from src.obs.metrics_server import ensure_metrics_server


def start_session_http() -> None:
    """Start in-process /metrics HTTP server for a session (Mode A). Port from env; fails if port in use."""
    ensure_metrics_server(port=None)
