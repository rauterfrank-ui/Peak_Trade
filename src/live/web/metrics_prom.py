from __future__ import annotations

import logging
import os
import time
from typing import Any

try:
    import prometheus_client  # type: ignore
    from prometheus_client import CONTENT_TYPE_LATEST, Counter, Gauge, Histogram  # type: ignore
    from prometheus_client.exposition import generate_latest  # type: ignore

    _PROM_AVAILABLE = True
except Exception:  # pragma: no cover
    prometheus_client = None  # type: ignore
    Counter = Histogram = Gauge = None  # type: ignore
    CONTENT_TYPE_LATEST = "text/plain; version=0.0.4; charset=utf-8"
    generate_latest = None  # type: ignore
    _PROM_AVAILABLE = False

logger = logging.getLogger(__name__)

_HTTP_REQUESTS_TOTAL = None
_HTTP_REQUEST_DURATION = None
_HTTP_IN_FLIGHT = None


def is_prometheus_available() -> bool:
    return bool(_PROM_AVAILABLE)


def _enabled() -> bool:
    return os.getenv("PEAK_TRADE_PROMETHEUS_ENABLED", "0") == "1"


def _init_metrics() -> None:
    global _HTTP_REQUESTS_TOTAL, _HTTP_REQUEST_DURATION, _HTTP_IN_FLIGHT

    if _HTTP_REQUESTS_TOTAL is not None:
        return

    # Defensive: should only be called when prometheus_client is available
    _HTTP_REQUESTS_TOTAL = Counter(
        "peak_trade_http_requests_total",
        "Total HTTP requests handled by Peak_Trade live web service.",
        labelnames=("method", "route", "status_code"),
    )
    _HTTP_REQUEST_DURATION = Histogram(
        "peak_trade_http_request_duration_seconds",
        "HTTP request latency in seconds (Peak_Trade live web service).",
        labelnames=("method", "route", "status_code"),
        buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 10),
    )
    _HTTP_IN_FLIGHT = Gauge(
        "peak_trade_http_in_flight_requests",
        "In-flight HTTP requests currently being handled.",
    )


def instrument_app(app: Any) -> None:
    """
    Adds lightweight Prometheus instrumentation via middleware.
    No-ops if prometheus is unavailable or disabled.
    """
    if not is_prometheus_available() or not _enabled():
        logger.info("Prometheus metrics disabled (prometheus_client missing or flag off).")
        return

    _init_metrics()

    @app.middleware("http")
    async def _prom_middleware(request, call_next):
        # in-flight
        try:
            _HTTP_IN_FLIGHT.inc()  # type: ignore[union-attr]
        except Exception:
            pass

        start = time.perf_counter()
        status_code = "500"
        route_label = "__unknown__"
        method = getattr(request, "method", "GET")

        try:
            response = await call_next(request)
            status_code = str(getattr(response, "status_code", 200))

            # Route template if possible (prevents cardinality explosion)
            try:
                route = request.scope.get("route")
                route_label = getattr(route, "path", None) or "__unknown__"
            except Exception:
                route_label = "__unknown__"

            return response
        finally:
            dur = time.perf_counter() - start
            try:
                _HTTP_REQUESTS_TOTAL.labels(  # type: ignore[union-attr]
                    method=method, route=route_label, status_code=status_code
                ).inc()
                _HTTP_REQUEST_DURATION.labels(  # type: ignore[union-attr]
                    method=method, route=route_label, status_code=status_code
                ).observe(dur)
            except Exception:
                pass

            try:
                _HTTP_IN_FLIGHT.dec()  # type: ignore[union-attr]
            except Exception:
                pass


def maybe_register_metrics(app: Any) -> None:
    """
    Registers /metrics endpoint only when prometheus is available AND enabled.
    """
    if not is_prometheus_available() or not _enabled():
        return

    _init_metrics()

    @app.get("/metrics", include_in_schema=False)
    def _metrics():
        from fastapi import Response

        payload = generate_latest()  # type: ignore[misc]
        return Response(content=payload, media_type=CONTENT_TYPE_LATEST)
