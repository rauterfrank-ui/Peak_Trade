"""Operator header display view model (read-only, futures-only boundaries)."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def build_operator_header_display_v1(
    *,
    source: str,
    futures_ohlcv: dict[str, Any] | None = None,
    economic_vm: dict[str, Any] | None = None,
    ai_activity_state: str,
) -> dict[str, Any]:
    """Build the compact operator header VM (authority boundaries are hard-coded false)."""
    ohlcv = futures_ohlcv if isinstance(futures_ohlcv, dict) else {}
    economic = economic_vm if isinstance(economic_vm, dict) else {}

    data_source = str(ohlcv.get("source") or "").strip() or "unavailable"
    freshness = str(ohlcv.get("generated_at_iso") or "").strip() or "unavailable"
    stale = bool(ohlcv.get("stale") is True)

    return {
        "section_visible": True,
        "read_only": True,
        "view_only": True,
        "futures_only": True,
        "bitcoin_excluded": True,
        "spot_allowed": False,
        "synthetic_allowed": False,
        "source": str(source),
        "data_source": data_source,
        "data_freshness": freshness,
        "stale": stale,
        "economic_gate_status": str(economic.get("economic_status") or "unavailable"),
        "economic_gate_pass": bool(economic.get("gates_pass") is True),
        "runtime_authority": "NONE",
        "orders_allowed": False,
        "live_allowed": False,
        "promotion_allowed": False,
        "ai_activity_state": ai_activity_state,
        "snapshot_timestamp": _utc_now_iso(),
    }


__all__ = ["build_operator_header_display_v1"]
