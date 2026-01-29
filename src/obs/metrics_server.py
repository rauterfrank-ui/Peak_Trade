from __future__ import annotations

import os
from typing import Optional

_started: bool = False


def ensure_metrics_server(port: Optional[int] = None) -> bool:
    """
    Start a Prometheus /metrics HTTP server in THIS process (idempotent).

    - Fail-open: if prometheus_client is unavailable, return False and do nothing.
    - Default port: 9111 (override via PEAKTRADE_METRICS_PORT).
    """
    global _started
    if _started:
        return True

    try:
        from prometheus_client import start_http_server  # type: ignore
    except Exception:
        return False

    if port is None:
        raw = os.getenv("PEAKTRADE_METRICS_PORT", "").strip()
        port = int(raw) if raw else 9111

    try:
        # Exposes /metrics on 0.0.0.0:<port> (default binding).
        start_http_server(port)
        _started = True
        return True
    except Exception:
        # Fail-open: never crash the trading/session loop due to metrics server.
        return False
