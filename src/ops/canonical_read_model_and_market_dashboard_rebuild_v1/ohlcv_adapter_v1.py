"""Adapt existing DERIVED OHLCV materializer payloads into the O5 read-model chrome.

Does not create a parallel OHLCV producer. Preserves HTTP_JSON_POLL and the
GET /market surface while stamping O5 connection / freshness identity fields.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Mapping

from src.ops.canonical_read_model_and_market_dashboard_rebuild_v1.connection_state_v1 import (
    classify_connection_state_v1,
)
from src.ops.canonical_read_model_and_market_dashboard_rebuild_v1.constants_v1 import (
    CANONICAL_MARKET_ROUTE,
    CANONICAL_OHLCV_API,
    CONNECTION_MISSING_SOURCE,
    DASHBOARD_TRANSPORT,
    O4_AUTHORITATIVE_BAR_PRODUCER,
    READ_MODEL_AUTHORITY_EFFECT,
    READ_MODEL_CLASSIFICATION,
    READ_MODEL_RELATIVE_PATH,
    READ_MODEL_SCHEMA_NAME,
    READ_MODEL_SSOT,
)


def _parse_iso_to_unix(value: Any) -> float | None:
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        return datetime.fromisoformat(text).timestamp()
    except ValueError:
        return None


def _iso_from_unix(epoch: float | None) -> str | None:
    if epoch is None:
        return None
    return datetime.fromtimestamp(float(epoch), tz=timezone.utc).isoformat().replace("+00:00", "Z")


def adapt_derived_ohlcv_payload_to_o5_read_model_v1(
    ohlcv: Mapping[str, Any] | None,
    *,
    projection_time_unix: float,
    availability: str | None = None,
    disconnected: bool = False,
) -> dict[str, Any]:
    """Stamp O5 identity + connection chrome onto an existing DERIVED OHLCV payload."""
    if ohlcv is None:
        return {
            "schema_name": READ_MODEL_SCHEMA_NAME,
            "schema_version": 1,
            "read_model_classification": READ_MODEL_CLASSIFICATION,
            "read_model_ssot": READ_MODEL_SSOT,
            "read_model_authority_effect": READ_MODEL_AUTHORITY_EFFECT,
            "authoritative_bar_producer": O4_AUTHORITATIVE_BAR_PRODUCER,
            "dashboard_transport": DASHBOARD_TRANSPORT,
            "canonical_market_route": CANONICAL_MARKET_ROUTE,
            "canonical_ohlcv_api": CANONICAL_OHLCV_API,
            "relative_path": READ_MODEL_RELATIVE_PATH,
            "source_session_id": None,
            "repository_sha": None,
            "config_digest": None,
            "instrument": None,
            "interval": None,
            "last_event_time": None,
            "last_event_time_unix": None,
            "last_projection_time": _iso_from_unix(projection_time_unix),
            "last_projection_time_unix": float(projection_time_unix),
            "freshness_age_seconds": None,
            "connection_state": CONNECTION_MISSING_SOURCE,
            "is_stale": False,
            "trading_authority": False,
            "orders": False,
            "runtime_mutation": False,
            "risk_authority": False,
            "write_methods": [],
            "source_payload_schema": None,
        }

    last_event_unix = (
        _parse_iso_to_unix(ohlcv.get("last_timestamp"))
        or _parse_iso_to_unix(ohlcv.get("captured_at"))
        or _parse_iso_to_unix(ohlcv.get("effective_at"))
    )
    freshness_age = (
        None if last_event_unix is None else float(projection_time_unix) - float(last_event_unix)
    )
    is_stale = (
        bool(ohlcv.get("is_stale")) or str(ohlcv.get("freshness_state") or "").lower() == "stale"
    )
    freshness_state = str(ohlcv.get("freshness_state") or "").lower()
    if disconnected:
        connection_state = "DISCONNECTED"
    elif is_stale:
        connection_state = "STALE"
    elif freshness_state == "fresh":
        # Honor materializer freshness; do not re-age candle tips as STALE.
        connection_state = "HEALTHY"
    else:
        connection_state = classify_connection_state_v1(
            source_present=True,
            is_stale=False,
            disconnected=False,
            freshness_age_seconds=freshness_age,
            availability=availability,
        )
    return {
        "schema_name": READ_MODEL_SCHEMA_NAME,
        "schema_version": 1,
        "read_model_classification": READ_MODEL_CLASSIFICATION,
        "read_model_ssot": READ_MODEL_SSOT,
        "read_model_authority_effect": READ_MODEL_AUTHORITY_EFFECT,
        "authoritative_bar_producer": ohlcv.get("authoritative_bar_producer")
        or O4_AUTHORITATIVE_BAR_PRODUCER,
        "authority_classification": ohlcv.get("authority_classification") or "DERIVED",
        "dashboard_transport": DASHBOARD_TRANSPORT,
        "canonical_market_route": CANONICAL_MARKET_ROUTE,
        "canonical_ohlcv_api": CANONICAL_OHLCV_API,
        "relative_path": READ_MODEL_RELATIVE_PATH,
        "independent_authoritative_recompute": False,
        "parallel_ohlcv_producer": False,
        "source_session_id": ohlcv.get("session_id") or ohlcv.get("source_session_id"),
        "repository_sha": ohlcv.get("repository_sha") or ohlcv.get("git_sha"),
        "config_digest": ohlcv.get("config_digest"),
        "instrument": ohlcv.get("instrument_id") or ohlcv.get("instrument"),
        "interval": ohlcv.get("interval"),
        "venue": ohlcv.get("venue"),
        "last_event_time_unix": last_event_unix,
        "last_event_time": _iso_from_unix(last_event_unix)
        if last_event_unix is not None
        else (ohlcv.get("last_timestamp") or ohlcv.get("captured_at")),
        "last_projection_time_unix": float(projection_time_unix),
        "last_projection_time": _iso_from_unix(projection_time_unix),
        "freshness_age_seconds": freshness_age,
        "connection_state": connection_state,
        "is_stale": bool(is_stale) or connection_state == "STALE",
        "bar_count": ohlcv.get("bar_count"),
        "trading_authority": False,
        "orders": False,
        "runtime_mutation": False,
        "risk_authority": False,
        "write_methods": [],
        "source_payload_schema": ohlcv.get("schema_name"),
        "selection_bundle_id": ohlcv.get("selection_bundle_id"),
    }
