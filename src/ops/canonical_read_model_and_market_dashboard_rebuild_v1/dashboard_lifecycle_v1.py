"""Read-only dashboard lifecycle contract for O5."""

from __future__ import annotations

from typing import Any, Mapping

from src.ops.canonical_read_model_and_market_dashboard_rebuild_v1.constants_v1 import (
    CANONICAL_MARKET_ROUTE,
    CANONICAL_OHLCV_API,
    DASHBOARD_TRANSPORT,
    LIFECYCLE_COMPONENTS,
    READ_MODEL_SCHEMA_NAME,
)


def dashboard_lifecycle_contract_v1() -> dict[str, Any]:
    return {
        "components": list(LIFECYCLE_COMPONENTS),
        "transport": DASHBOARD_TRANSPORT,
        "canonical_market_route": CANONICAL_MARKET_ROUTE,
        "canonical_ohlcv_api": CANONICAL_OHLCV_API,
        "websocket_required": False,
        "sse_required": False,
        "trading_authority": False,
        "orders_allowed": False,
        "runtime_mutation_allowed": False,
        "risk_authority": False,
        "read_model_schema": READ_MODEL_SCHEMA_NAME,
        "independent_component_status_required": True,
        "supervisor_binding": "O2_DASHBOARD_ONLY_SCAFFOLD_COMPATIBLE",
    }


def materialize_dashboard_lifecycle_status_v1(
    *,
    backend_alive: bool,
    frontend_armed: bool,
    poll_transport_ok: bool,
    read_model_present: bool,
    health_endpoint_ok: bool,
    connection_state: str,
) -> dict[str, Any]:
    """Explicit per-component status; never invents trading authority."""
    components = {
        "DASHBOARD_BACKEND": "RUNNING" if backend_alive else "STOPPED",
        "DASHBOARD_FRONTEND": "ARMED" if frontend_armed else "DISARMED",
        "STREAM_OR_POLL_TRANSPORT": "OK" if poll_transport_ok else "DISCONNECTED",
        "READ_MODEL_STORE": "PRESENT" if read_model_present else "MISSING_SOURCE",
        "HEALTH_ENDPOINT": "OK" if health_endpoint_ok else "DEGRADED",
    }
    overall = "HEALTHY"
    if not read_model_present:
        overall = "MISSING_SOURCE"
    elif not poll_transport_ok or connection_state == "DISCONNECTED":
        overall = "DISCONNECTED"
    elif connection_state in {"STALE", "DEGRADED"}:
        overall = connection_state
    elif not backend_alive or not health_endpoint_ok:
        overall = "DEGRADED"
    elif not frontend_armed:
        overall = "DEGRADED"

    return {
        "schema": "o5_dashboard_lifecycle_status_v1",
        "components": components,
        "overall_connection_state": overall,
        "trading_authority": False,
        "orders": False,
        "runtime_mutation": False,
        "risk_authority": False,
        "write_methods": [],
    }


def assert_dashboard_has_no_trading_authority_v1(
    lifecycle: Mapping[str, Any],
) -> dict[str, Any]:
    forbidden_true = (
        "trading_authority",
        "orders",
        "runtime_mutation",
        "risk_authority",
        "orders_allowed",
        "runtime_mutation_allowed",
    )
    for key in forbidden_true:
        if lifecycle.get(key) is True:
            raise ValueError(f"DASHBOARD_TRADING_OR_MUTATION_AUTHORITY_LEAK:{key}")
    if lifecycle.get("write_methods"):
        raise ValueError("DASHBOARD_WRITE_METHODS_FORBIDDEN")
    return {"ok": True, "trading_authority": False, "orders": False}
