from __future__ import annotations

import os
from typing import Optional

_started: bool = False


def ensure_metrics_server(port: Optional[int] = None) -> bool:
    """
    Start a Prometheus /metrics HTTP server in THIS process (idempotent).

    - Fail-open: if prometheus_client is unavailable, return False and do nothing.
    - Default port: 9111 (canonical env: PEAK_TRADE_METRICSD_PORT; legacy: PEAKTRADE_METRICS_PORT).
    - Mode B uses a dedicated metricsd; sessions must not bind. Fail-fast on port collisions.
    """
    # Mode B uses a dedicated metricsd; sessions must not bind.
    if (os.getenv("PEAKTRADE_METRICS_MODE", "") or "").strip().upper() == "B":
        return False

    global _started
    if _started:
        return True

    try:
        from prometheus_client import start_http_server  # type: ignore
    except Exception:
        return False

    if port is None:
        # Canonical port resolver (supports legacy env var fallback)
        from src.obs.metrics_config import get_metrics_port
        from src.ops.net.ports import ensure_tcp_port_free

        port = get_metrics_port(9111)
        ensure_tcp_port_free(port, context="metrics_server_inprocess")

    try:
        # Exposes /metrics on 0.0.0.0:<port> (default binding).
        start_http_server(port)
        _started = True
        return True
    except Exception:
        # Fail-open: never crash the trading/session loop due to metrics server.
        return False
