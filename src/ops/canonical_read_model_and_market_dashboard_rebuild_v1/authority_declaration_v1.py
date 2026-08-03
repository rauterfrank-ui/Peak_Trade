"""Authority declaration for O5 derived read model + read-only dashboard."""

from __future__ import annotations

from typing import Any

from src.ops.canonical_read_model_and_market_dashboard_rebuild_v1.constants_v1 import (
    CLOSED_FROM_O4_DEFERRED,
    DASHBOARD_TRANSPORT,
    O4_AUTHORITATIVE_BAR_PRODUCER,
    O4_CANONICAL_NORMALIZED_EVENT_PATH,
    READ_MODEL_AUTHORITY_EFFECT,
    READ_MODEL_CLASSIFICATION,
    READ_MODEL_SCHEMA_NAME,
    READ_MODEL_SSOT,
    SAFETY_INVARIANTS,
)


def authority_declaration_v1() -> dict[str, Any]:
    return {
        "read_model_schema": READ_MODEL_SCHEMA_NAME,
        "read_model_classification": READ_MODEL_CLASSIFICATION,
        "read_model_ssot": READ_MODEL_SSOT,
        "read_model_authority_effect": READ_MODEL_AUTHORITY_EFFECT,
        "authoritative_bar_producer": O4_AUTHORITATIVE_BAR_PRODUCER,
        "canonical_normalized_event_path": O4_CANONICAL_NORMALIZED_EVENT_PATH,
        "dashboard_transport": DASHBOARD_TRANSPORT,
        "dashboard_trading_authority": False,
        "parallel_ohlcv_producer_created": False,
        "independent_authoritative_recompute_allowed": False,
        "orders_allowed": False,
        "runtime_mutation_allowed": False,
        "risk_authority": False,
        "closed_from_o4_deferred": list(CLOSED_FROM_O4_DEFERRED),
        "safety_invariants": dict(SAFETY_INVARIANTS),
    }


def assert_authority_invariants_v1() -> dict[str, Any]:
    decl = authority_declaration_v1()
    if decl["read_model_classification"] != "DERIVED":
        raise ValueError("READ_MODEL_MUST_BE_DERIVED")
    if decl["read_model_ssot"] is not False:
        raise ValueError("READ_MODEL_MUST_NOT_BE_SSOT")
    if decl["read_model_authority_effect"] != "NONE":
        raise ValueError("READ_MODEL_AUTHORITY_EFFECT_MUST_BE_NONE")
    if decl["dashboard_trading_authority"] is not False:
        raise ValueError("DASHBOARD_TRADING_AUTHORITY_MUST_BE_FALSE")
    if decl["parallel_ohlcv_producer_created"] is not False:
        raise ValueError("PARALLEL_OHLCV_PRODUCER_FORBIDDEN")
    if SAFETY_INVARIANTS["ORDERS_ALLOWED"] is not False:
        raise ValueError("ORDERS_MUST_REMAIN_FORBIDDEN")
    if SAFETY_INVARIANTS["STALE_CANNOT_RENDER_HEALTHY"] is not True:
        raise ValueError("STALE_HEALTHY_GUARD_REQUIRED")
    return {"ok": True, "declaration": decl}
