"""Resolve DDO N_BARS horizon decision_event from same-cycle capture (optional).

Observation-only. Does not alter cycle decisions. Explicit injection wins.
"""

from __future__ import annotations

from typing import Any, Final, Mapping

from src.learning.deterministic_decision_outcome_v0.capture_v0 import DdoCaptureBindingV0
from src.learning.deterministic_decision_outcome_v0.common_v0 import SCHEMA_NAME_DECISION_EVENT
from src.learning.deterministic_decision_outcome_v0.double_play_input_evidence_v1 import (
    PRODUCER_ID as DOUBLE_PLAY_PRODUCER_ID,
)

BINDING_ID: Final[str] = (
    "peak_trade.ops.wallclock_bridge.ddo_n_bars_horizon_upstream_from_cycle_capture_v1"
)
EXTERNAL_EFFECT_AUTHORIZED: Final[bool] = False


def _correlation_matches(record: Mapping[str, Any], correlation_id: str) -> bool:
    corr = record.get("correlation_id")
    return isinstance(corr, str) and corr == correlation_id


def _seam_rank(record: Mapping[str, Any]) -> int:
    if record.get("producer_id") == DOUBLE_PLAY_PRODUCER_ID:
        return 0
    return 1


def resolve_decision_event_from_capture_binding_v1(
    binding: DdoCaptureBindingV0 | None,
    *,
    correlation_id: str,
    cycle_id: str | None = None,
) -> dict[str, Any] | None:
    """Pick the best decision_event row for this correlation from in-memory capture."""
    if binding is None or not binding.enabled:
        return None
    candidates: list[dict[str, Any]] = []
    for record in binding.captured_records:
        if record.get("schema_name") != SCHEMA_NAME_DECISION_EVENT:
            continue
        if not _correlation_matches(record, correlation_id):
            continue
        candidates.append(dict(record))
    if not candidates:
        return None
    if cycle_id:
        cycle_matches = [row for row in candidates if row.get("cycle_id") == cycle_id]
        if cycle_matches:
            candidates = cycle_matches
    candidates.sort(key=_seam_rank)
    return candidates[0]


def maybe_bind_ddo_n_bars_horizon_decision_from_cycle_capture_v1(
    state: Any,
    *,
    correlation_id: str,
    cycle_id: str | None = None,
) -> dict[str, Any] | None:
    """Fill ``ddo_n_bars_horizon_decision_event`` when not explicitly injected."""
    existing = getattr(state, "ddo_n_bars_horizon_decision_event", None)
    if existing is not None:
        return None
    binding = getattr(state, "ddo_capture_binding", None)
    if not isinstance(binding, DdoCaptureBindingV0):
        return None
    resolved = resolve_decision_event_from_capture_binding_v1(
        binding, correlation_id=correlation_id, cycle_id=cycle_id
    )
    if resolved is None:
        return None
    state.ddo_n_bars_horizon_decision_event = resolved
    return {
        "ok": True,
        "binding_id": BINDING_ID,
        "decision_event_ref": resolved.get("record_id"),
        "source": "cycle_capture_binding",
        "external_effect_authorized": EXTERNAL_EFFECT_AUTHORIZED,
    }
