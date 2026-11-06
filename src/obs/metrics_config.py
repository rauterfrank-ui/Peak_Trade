from __future__ import annotations

import os


def get_metrics_port(default: int = 9111) -> int:
    # Canonical env var:
    v = os.getenv("PEAK_TRADE_METRICSD_PORT")
    # Legacy fallback (kept for backward compat; prefer canonical):
    if not v:
        v = os.getenv("PEAKTRADE_METRICS_PORT")
    if not v:
        return default
    try:
        p = int(v)
    except ValueError as e:
        raise RuntimeError(f"Invalid PEAK_TRADE_METRICSD_PORT={v!r}") from e
    if p <= 0 or p > 65535:
        raise RuntimeError(f"Invalid PEAK_TRADE_METRICSD_PORT={v!r}")
    return p
