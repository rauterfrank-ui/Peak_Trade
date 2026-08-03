"""Versioned derived market-dashboard read model projector (O5).

Consumes O4 authoritative envelopes / derived OHLCV projection. Does not
recompute bars independently and does not create a parallel OHLCV producer.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Mapping, Sequence

from src.ops.canonical_public_md_and_ohlcv_transport_reconciliation_v1.constants_v1 import (
    AUTHORITATIVE_BAR_PRODUCER,
    CLASS_DERIVED,
    DASHBOARD_TRANSPORT as O4_DASHBOARD_TRANSPORT,
)
from src.ops.canonical_public_md_and_ohlcv_transport_reconciliation_v1.dashboard_ohlcv_projection_v1 import (
    project_authoritative_envelopes_to_dashboard_ohlcv_v1,
)
from src.ops.canonical_read_model_and_market_dashboard_rebuild_v1.connection_state_v1 import (
    classify_connection_state_v1,
)
from src.ops.canonical_read_model_and_market_dashboard_rebuild_v1.constants_v1 import (
    CANONICAL_MARKET_ROUTE,
    CANONICAL_OHLCV_API,
    CONNECTION_MISSING_SOURCE,
    DASHBOARD_TRANSPORT,
    O4_AUTHORITATIVE_BAR_PRODUCER,
    O4_CANONICAL_NORMALIZED_EVENT_PATH,
    READ_MODEL_AUTHORITY_EFFECT,
    READ_MODEL_CLASSIFICATION,
    READ_MODEL_RELATIVE_PATH,
    READ_MODEL_SCHEMA_NAME,
    READ_MODEL_SSOT,
)


def _iso_from_unix(epoch: float | None) -> str | None:
    if epoch is None:
        return None
    return datetime.fromtimestamp(float(epoch), tz=timezone.utc).isoformat().replace("+00:00", "Z")


def read_model_path_contract_v1() -> dict[str, Any]:
    return {
        "schema_name": READ_MODEL_SCHEMA_NAME,
        "relative_path": READ_MODEL_RELATIVE_PATH,
        "classification": READ_MODEL_CLASSIFICATION,
        "ssot": READ_MODEL_SSOT,
        "authority_effect": READ_MODEL_AUTHORITY_EFFECT,
        "dashboard_transport": DASHBOARD_TRANSPORT,
        "canonical_market_route": CANONICAL_MARKET_ROUTE,
        "canonical_ohlcv_api": CANONICAL_OHLCV_API,
        "authoritative_bar_producer": O4_AUTHORITATIVE_BAR_PRODUCER,
        "canonical_normalized_event_path": O4_CANONICAL_NORMALIZED_EVENT_PATH,
        "parallel_ohlcv_producer_allowed": False,
        "independent_authoritative_recompute_allowed": False,
    }


def project_o4_envelopes_to_canonical_dashboard_read_model_v1(
    envelopes: Sequence[Mapping[str, Any]],
    *,
    selection_bundle_id: str,
    projection_time_unix: float,
    disconnected: bool = False,
    is_stale: bool = False,
) -> dict[str, Any]:
    """Project O4 envelopes into the versioned O5 derived read model."""
    if DASHBOARD_TRANSPORT != O4_DASHBOARD_TRANSPORT:
        raise ValueError("DASHBOARD_TRANSPORT_DRIFT")
    if not envelopes:
        return build_missing_source_read_model_v1(
            selection_bundle_id=selection_bundle_id,
            projection_time_unix=projection_time_unix,
            reason="NO_ENVELOPES",
        )

    ohlcv = project_authoritative_envelopes_to_dashboard_ohlcv_v1(
        envelopes,
        selection_bundle_id=selection_bundle_id,
        transport=DASHBOARD_TRANSPORT,
    )
    instrument = str(ohlcv.get("instrument_id") or "")
    interval = str(ohlcv.get("interval") or "")
    session_ids = {str(e.get("session_id") or "") for e in envelopes}
    repo_shas = {str(e.get("repository_sha") or "") for e in envelopes}
    config_digests = {str(e.get("config_digest") or "") for e in envelopes}
    if len(session_ids) != 1 or "" in session_ids:
        raise ValueError("SESSION_ID_CROSS_CONTAMINATION_OR_MISSING")
    if len(repo_shas) != 1 or "" in repo_shas:
        raise ValueError("REPOSITORY_SHA_CROSS_CONTAMINATION_OR_MISSING")
    if len(config_digests) != 1 or "" in config_digests:
        raise ValueError("CONFIG_DIGEST_CROSS_CONTAMINATION_OR_MISSING")

    last_event_time = max(float(e["event_time"]) for e in envelopes)
    freshness_age = float(projection_time_unix) - last_event_time
    connection_state = classify_connection_state_v1(
        source_present=True,
        is_stale=is_stale,
        disconnected=disconnected,
        freshness_age_seconds=freshness_age,
    )

    return {
        "schema_name": READ_MODEL_SCHEMA_NAME,
        "schema_version": 1,
        "authority_classification": CLASS_DERIVED,
        "read_model_classification": READ_MODEL_CLASSIFICATION,
        "read_model_ssot": READ_MODEL_SSOT,
        "read_model_authority_effect": READ_MODEL_AUTHORITY_EFFECT,
        "authoritative_bar_producer": AUTHORITATIVE_BAR_PRODUCER,
        "canonical_normalized_event_path": O4_CANONICAL_NORMALIZED_EVENT_PATH,
        "dashboard_transport": DASHBOARD_TRANSPORT,
        "canonical_market_route": CANONICAL_MARKET_ROUTE,
        "canonical_ohlcv_api": CANONICAL_OHLCV_API,
        "independent_authoritative_recompute": False,
        "parallel_ohlcv_producer": False,
        "relative_path": READ_MODEL_RELATIVE_PATH,
        "selection_bundle_id": selection_bundle_id,
        "source_session_id": next(iter(session_ids)),
        "repository_sha": next(iter(repo_shas)),
        "config_digest": next(iter(config_digests)),
        "instrument": instrument,
        "instrument_id": instrument,
        "interval": interval,
        "venue": ohlcv.get("venue"),
        "last_event_time_unix": last_event_time,
        "last_event_time": _iso_from_unix(last_event_time),
        "last_projection_time_unix": float(projection_time_unix),
        "last_projection_time": _iso_from_unix(projection_time_unix),
        "freshness_age_seconds": freshness_age,
        "connection_state": connection_state,
        "is_stale": bool(is_stale) or connection_state == "STALE",
        "bar_count": ohlcv.get("bar_count"),
        "bars": ohlcv.get("bars"),
        "ohlcv_projection": ohlcv,
        "trading_authority": False,
        "orders": False,
        "runtime_mutation": False,
        "risk_authority": False,
        "write_methods": [],
    }


def build_missing_source_read_model_v1(
    *,
    selection_bundle_id: str,
    projection_time_unix: float,
    reason: str = "MISSING_SOURCE",
) -> dict[str, Any]:
    """Expected MISSING_SOURCE semantics — explicit, never fabricated healthy."""
    return {
        "schema_name": READ_MODEL_SCHEMA_NAME,
        "schema_version": 1,
        "authority_classification": CLASS_DERIVED,
        "read_model_classification": READ_MODEL_CLASSIFICATION,
        "read_model_ssot": READ_MODEL_SSOT,
        "read_model_authority_effect": READ_MODEL_AUTHORITY_EFFECT,
        "authoritative_bar_producer": AUTHORITATIVE_BAR_PRODUCER,
        "dashboard_transport": DASHBOARD_TRANSPORT,
        "selection_bundle_id": selection_bundle_id,
        "source_session_id": None,
        "repository_sha": None,
        "config_digest": None,
        "instrument": None,
        "instrument_id": None,
        "interval": None,
        "venue": None,
        "last_event_time_unix": None,
        "last_event_time": None,
        "last_projection_time_unix": float(projection_time_unix),
        "last_projection_time": _iso_from_unix(projection_time_unix),
        "freshness_age_seconds": None,
        "connection_state": CONNECTION_MISSING_SOURCE,
        "is_stale": False,
        "bar_count": 0,
        "bars": [],
        "ohlcv_projection": None,
        "missing_source_reason": reason,
        "trading_authority": False,
        "orders": False,
        "runtime_mutation": False,
        "risk_authority": False,
        "write_methods": [],
        "may_render_healthy": False,
    }


def bind_dashboard_backend_to_read_model_v1(
    read_model: Mapping[str, Any],
) -> dict[str, Any]:
    """Exclusive backend binding declaration — read model only, no trading authority."""
    if str(read_model.get("schema_name") or "") != READ_MODEL_SCHEMA_NAME:
        raise ValueError("DASHBOARD_BACKEND_REQUIRES_CANONICAL_O5_READ_MODEL")
    if read_model.get("read_model_classification") != READ_MODEL_CLASSIFICATION:
        raise ValueError("READ_MODEL_MUST_BE_DERIVED")
    if read_model.get("trading_authority") or read_model.get("orders"):
        raise ValueError("DASHBOARD_TRADING_AUTHORITY_FORBIDDEN")
    return {
        "bound": True,
        "exclusive_to_canonical_read_model": True,
        "schema_name": READ_MODEL_SCHEMA_NAME,
        "connection_state": read_model.get("connection_state"),
        "source_session_id": read_model.get("source_session_id"),
        "repository_sha": read_model.get("repository_sha"),
        "config_digest": read_model.get("config_digest"),
        "instrument": read_model.get("instrument") or read_model.get("instrument_id"),
        "interval": read_model.get("interval"),
        "last_event_time": read_model.get("last_event_time"),
        "last_projection_time": read_model.get("last_projection_time"),
        "freshness_age_seconds": read_model.get("freshness_age_seconds"),
        "dashboard_transport": DASHBOARD_TRANSPORT,
        "trading_authority": False,
        "orders": False,
        "runtime_mutation": False,
        "risk_authority": False,
    }
