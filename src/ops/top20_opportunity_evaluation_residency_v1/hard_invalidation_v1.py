"""Structural hard invalidation only (no rank/score/trading outcomes)."""

from __future__ import annotations

from typing import Any, Mapping, Optional

from src.ops.top20_opportunity_evaluation_residency_v1.constants_v1 import REASON_HARD_INVALIDATION


def hard_invalidation_reason_v1(
    *,
    record_instrument_id: str,
    universe_snapshot: Optional[Mapping[str, Any]],
    admission_universe_snapshot_id: str,
) -> Optional[str]:
    if universe_snapshot is None:
        return None
    current_universe_id = str(
        universe_snapshot.get("snapshot_id") or universe_snapshot.get("universe_snapshot_id") or ""
    )
    if current_universe_id and current_universe_id != admission_universe_snapshot_id:
        return REASON_HARD_INVALIDATION
    instruments = universe_snapshot.get("instruments") or ()
    ids = {
        str(row.get("canonical_instrument_id") or "").strip()
        for row in instruments
        if isinstance(row, Mapping)
    }
    if record_instrument_id not in ids:
        return REASON_HARD_INVALIDATION
    for row in instruments:
        if not isinstance(row, Mapping):
            continue
        if str(row.get("canonical_instrument_id") or "").strip() != record_instrument_id:
            continue
        native = str(row.get("venue_native_inst_id") or row.get("venue_native_id") or "").strip()
        if not native:
            return REASON_HARD_INVALIDATION
        break
    return None
