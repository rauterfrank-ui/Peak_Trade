"""Derived dashboard OHLCV projection from the authoritative bar producer.

Preserves HTTP_JSON_POLL as the dashboard transport. Does not grant the
dashboard independent authoritative bar ownership or recomputation rights.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Mapping, Sequence

from src.ops.canonical_public_md_and_ohlcv_transport_reconciliation_v1.constants_v1 import (
    AUTHORITATIVE_BAR_PRODUCER,
    CLASS_DERIVED,
    DASHBOARD_TRANSPORT,
)


def _iso_from_epoch(epoch: float) -> str:
    return datetime.fromtimestamp(float(epoch), tz=timezone.utc).isoformat().replace("+00:00", "Z")


def project_authoritative_envelopes_to_dashboard_ohlcv_v1(
    envelopes: Sequence[Mapping[str, Any]],
    *,
    selection_bundle_id: str,
    transport: str = DASHBOARD_TRANSPORT,
) -> dict[str, Any]:
    """Project canonical envelopes into the dashboard OHLCV readmodel shape.

    Classification is always DERIVED. Transport must remain HTTP_JSON_POLL.
    """
    if transport != DASHBOARD_TRANSPORT:
        raise ValueError(f"UNSUPPORTED_DASHBOARD_TRANSPORT:{transport}")

    bars: list[dict[str, Any]] = []
    for env in envelopes:
        finalized = str(env.get("finalization_state") or "") in {
            "FINALIZED_BAR",
            "CORRECTED_BAR",
        }
        bars.append(
            {
                "ts": _iso_from_epoch(float(env["bar_open_time"])),
                "open": str(env["open"]),
                "high": str(env["high"]),
                "low": str(env["low"]),
                "close": str(env["close"]),
                "volume": str(env.get("volume", 0.0)),
                "volume_ccy": None,
                "confirm": finalized,
                "provider_ts_ms": str(int(float(env["event_time"]) * 1000.0)),
                "quality_state": env.get("quality_state"),
                "finalization_state": env.get("finalization_state"),
                "revision": env.get("revision"),
                "transport_lag": env.get("transport_lag"),
                "session_id": env.get("session_id"),
                "repository_sha": env.get("repository_sha"),
                "config_digest": env.get("config_digest"),
            }
        )
    bars.sort(key=lambda b: b["ts"])
    instrument = ""
    venue = ""
    interval = ""
    if envelopes:
        instrument = str(envelopes[0].get("canonical_instrument_id") or "")
        venue = str(envelopes[0].get("venue") or "")
        interval = str(envelopes[0].get("interval") or "")
        for env in envelopes[1:]:
            if env.get("canonical_instrument_id") != instrument:
                raise ValueError("INSTRUMENT_CROSS_CONTAMINATION")
            if env.get("interval") != interval:
                raise ValueError("INTERVAL_CROSS_CONTAMINATION")

    return {
        "schema_name": "okx_selected_instrument_ohlcv_readmodel.v1",
        "authority_classification": CLASS_DERIVED,
        "authoritative_bar_producer": AUTHORITATIVE_BAR_PRODUCER,
        "dashboard_transport": DASHBOARD_TRANSPORT,
        "independent_authoritative_recompute": False,
        "selection_bundle_id": selection_bundle_id,
        "instrument_id": instrument,
        "venue": venue,
        "interval": interval,
        "bar_count": len(bars),
        "bars": bars,
        "source": "canonical_public_md_bar_producer_projection_v1",
    }


def dashboard_ohlcv_authority_declaration_v1() -> dict[str, Any]:
    return {
        "authority_classification": CLASS_DERIVED,
        "authoritative_bar_producer": AUTHORITATIVE_BAR_PRODUCER,
        "dashboard_transport": DASHBOARD_TRANSPORT,
        "independent_authoritative_recompute_allowed": False,
        "ui_rebuild_deferred_to_o5": True,
        "supervisor_binding_deferred_to_o5": True,
    }
