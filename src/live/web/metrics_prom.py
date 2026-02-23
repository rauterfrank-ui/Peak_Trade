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
_HTTP_REQUESTS_TOTAL_LABELED = None
_HTTP_REQUEST_DURATION_LABELED = None
_HTTP_IN_FLIGHT_LABELED = None
_CONST_LABELS = None


def is_prometheus_available() -> bool:
    return bool(_PROM_AVAILABLE)


def _enabled() -> bool:
    # Hard-disabled: ignore PEAK_TRADE_PROMETHEUS_ENABLED; never enable export.
    return False


def _init_metrics() -> None:
    global _HTTP_REQUESTS_TOTAL
    global _HTTP_REQUEST_DURATION
    global _HTTP_IN_FLIGHT
    global _HTTP_REQUESTS_TOTAL_LABELED
    global _HTTP_REQUEST_DURATION_LABELED
    global _HTTP_IN_FLIGHT_LABELED
    global _CONST_LABELS

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

    # Labeled variants (best-practice stable labels for Grafana filtering / multi-stack views)
    # NOTE: These labels are constant per process, but we include them as labels to allow
    # cross-stack dashboards to filter/group safely (no unbounded cardinality).
    _CONST_LABELS = {
        "service": os.getenv("PEAK_TRADE_SERVICE", "peak_trade_web"),
        "env": os.getenv("PEAK_TRADE_ENV", "local"),
        "stack": os.getenv("PEAK_TRADE_STACK", "mini"),
    }

    _HTTP_REQUESTS_TOTAL_LABELED = Counter(
        "peak_trade_http_requests_total_labeled",
        "Total HTTP requests handled by Peak_Trade live web service (const labels: service/env/stack).",
        labelnames=("service", "env", "stack", "method", "route", "status_code"),
    )
    _HTTP_REQUEST_DURATION_LABELED = Histogram(
        "peak_trade_http_request_duration_seconds_labeled",
        "HTTP request latency in seconds (Peak_Trade live web service) (const labels: service/env/stack).",
        labelnames=("service", "env", "stack", "method", "route", "status_code"),
        buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 10),
    )
    _HTTP_IN_FLIGHT_LABELED = Gauge(
        "peak_trade_http_in_flight_requests_labeled",
        "In-flight HTTP requests currently being handled (const labels: service/env/stack).",
        labelnames=("service", "env", "stack"),
    )


def instrument_app(app: Any) -> None:
    """
    Adds lightweight Prometheus instrumentation via middleware.
    No-ops if prometheus is unavailable or disabled.
    """
    if not is_prometheus_available():
        logger.info("Prometheus metrics disabled (prometheus_client missing).")
        return

    if not _enabled():
        logger.info(
            "Prometheus metrics disabled (PEAK_TRADE_PROMETHEUS_ENABLED=%r).",
            os.getenv("PEAK_TRADE_PROMETHEUS_ENABLED", "0"),
        )
        return

    _init_metrics()

    @app.middleware("http")
    async def _prom_middleware(request, call_next):
        # Avoid self-scrape noise: do not count /metrics in HTTP stats
        if getattr(request, "url", None) and request.url.path == "/metrics":
            return await call_next(request)

        # in-flight
        try:
            _HTTP_IN_FLIGHT.inc()  # type: ignore[union-attr]
            _HTTP_IN_FLIGHT_LABELED.labels(**_CONST_LABELS).inc()  # type: ignore[union-attr,arg-type]
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
                _HTTP_REQUESTS_TOTAL_LABELED.labels(  # type: ignore[union-attr]
                    **_CONST_LABELS, method=method, route=route_label, status_code=status_code
                ).inc()
                _HTTP_REQUEST_DURATION_LABELED.labels(  # type: ignore[union-attr]
                    **_CONST_LABELS, method=method, route=route_label, status_code=status_code
                ).observe(dur)
            except Exception:
                pass

            try:
                _HTTP_IN_FLIGHT.dec()  # type: ignore[union-attr]
                _HTTP_IN_FLIGHT_LABELED.labels(**_CONST_LABELS).dec()  # type: ignore[union-attr,arg-type]
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
