"""Explicit dashboard connection / freshness classification for O5.

Fail-closed: STALE and DISCONNECTED (and MISSING_SOURCE / DEGRADED) must never
be promoted to HEALTHY. Cached stale or disconnected payloads cannot render green.
"""

from __future__ import annotations

from typing import Any, Mapping

from src.ops.canonical_read_model_and_market_dashboard_rebuild_v1.constants_v1 import (
    CONNECTION_DEGRADED,
    CONNECTION_DISCONNECTED,
    CONNECTION_HEALTHY,
    CONNECTION_MISSING_SOURCE,
    CONNECTION_STATES,
    CONNECTION_STALE,
    DEGRADED_MAX_AGE_SECONDS,
    HEALTHY_MAX_AGE_SECONDS,
    NON_HEALTHY_RENDER_STATES,
)


class ConnectionStateContractErrorV1(ValueError):
    """Fail-closed connection-state contract violation."""


def connection_state_contract_v1() -> dict[str, Any]:
    return {
        "states": sorted(CONNECTION_STATES),
        "healthy_max_age_seconds": HEALTHY_MAX_AGE_SECONDS,
        "degraded_max_age_seconds": DEGRADED_MAX_AGE_SECONDS,
        "stale_cannot_render_healthy": True,
        "disconnected_cannot_render_healthy": True,
        "missing_source_cannot_render_healthy": True,
        "non_healthy_render_states": sorted(NON_HEALTHY_RENDER_STATES),
    }


def assert_connection_state_cannot_render_healthy_v1(state: str) -> dict[str, Any]:
    normalized = str(state or "").strip().upper()
    if normalized not in CONNECTION_STATES:
        raise ConnectionStateContractErrorV1(f"UNKNOWN_CONNECTION_STATE:{state}")
    if normalized == CONNECTION_HEALTHY:
        return {"ok": True, "state": normalized, "may_render_healthy": True}
    if normalized in NON_HEALTHY_RENDER_STATES:
        return {"ok": True, "state": normalized, "may_render_healthy": False}
    raise ConnectionStateContractErrorV1(f"UNCLASSIFIED_CONNECTION_STATE:{state}")


def classify_connection_state_v1(
    *,
    source_present: bool,
    is_stale: bool = False,
    disconnected: bool = False,
    freshness_age_seconds: float | None = None,
    healthy_max_age_seconds: float = HEALTHY_MAX_AGE_SECONDS,
    degraded_max_age_seconds: float = DEGRADED_MAX_AGE_SECONDS,
    availability: str | None = None,
) -> str:
    """Classify connection state from explicit inputs.

    Priority (fail-closed):
    1. MISSING_SOURCE when no source
    2. DISCONNECTED when transport disconnected
    3. STALE when stale flag / availability / age beyond degraded window
    4. DEGRADED when age exceeds healthy window
    5. HEALTHY otherwise
    """
    avail = str(availability or "").strip().upper()
    if not source_present or avail in {"MISSING_SOURCE", "NOT_BOUND"}:
        return CONNECTION_MISSING_SOURCE
    if disconnected:
        return CONNECTION_DISCONNECTED
    if is_stale or avail == "STALE":
        return CONNECTION_STALE
    if freshness_age_seconds is None:
        # Source present but age unknown → degraded, never invent healthy.
        return CONNECTION_DEGRADED
    age = float(freshness_age_seconds)
    if age < 0:
        # Clock skew / projection-before-event: treat as zero age, never invent healthy
        # via negative age arithmetic.
        age = 0.0
    if age > float(degraded_max_age_seconds):
        return CONNECTION_STALE
    if age > float(healthy_max_age_seconds):
        return CONNECTION_DEGRADED
    return CONNECTION_HEALTHY


def assert_no_healthy_render_for_cached_bad_state_v1(
    *,
    connection_state: str,
    render_as_healthy: bool,
) -> dict[str, Any]:
    """Prove stale/disconnected/missing cached data cannot render healthy."""
    state = classify_or_reject_v1(connection_state)
    if state in NON_HEALTHY_RENDER_STATES and render_as_healthy:
        raise ConnectionStateContractErrorV1(f"STALE_OR_DISCONNECTED_CANNOT_RENDER_HEALTHY:{state}")
    return {
        "ok": True,
        "connection_state": state,
        "render_as_healthy": bool(render_as_healthy),
        "allowed": True,
    }


def classify_or_reject_v1(raw: str) -> str:
    normalized = str(raw or "").strip().upper()
    # Bounded compatibility aliases from pre-O5 chrome.
    aliases = {
        "LIVE_DATA": CONNECTION_HEALTHY,
        "RECONNECTING": CONNECTION_DISCONNECTED,
        "AVAILABLE": CONNECTION_HEALTHY,
    }
    normalized = aliases.get(normalized, normalized)
    if normalized not in CONNECTION_STATES:
        raise ConnectionStateContractErrorV1(f"UNKNOWN_CONNECTION_STATE:{raw}")
    return normalized


def connection_chrome_from_poll_inputs_v1(
    payload: Mapping[str, Any] | None,
    *,
    availability: str | None = None,
    disconnected: bool = False,
    now_unix: float | None = None,
) -> dict[str, Any]:
    """Derive chrome fields from a poll/read-model payload (stdlib only)."""
    if payload is None:
        state = CONNECTION_MISSING_SOURCE
        return {
            "connection_state": state,
            "may_render_healthy": False,
            "freshness_age_seconds": None,
            "source_present": False,
        }

    is_stale = (
        bool(payload.get("is_stale"))
        or str(payload.get("freshness_state") or "").lower() == "stale"
    )
    age = payload.get("freshness_age_seconds")
    if age is None and now_unix is not None:
        last_event = payload.get("last_event_time_unix")
        if last_event is None:
            last_event = payload.get("last_projection_time_unix")
        if last_event is not None:
            age = float(now_unix) - float(last_event)

    state = classify_connection_state_v1(
        source_present=True,
        is_stale=is_stale,
        disconnected=disconnected,
        freshness_age_seconds=None if age is None else float(age),
        availability=availability or str(payload.get("availability") or ""),
    )
    return {
        "connection_state": state,
        "may_render_healthy": state == CONNECTION_HEALTHY,
        "freshness_age_seconds": None if age is None else float(age),
        "source_present": True,
    }
