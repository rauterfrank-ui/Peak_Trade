"""Cap-2.4 runtime binding witness epoch resolution (non-protected surface)."""

from __future__ import annotations

from datetime import datetime, timezone

from src.ops.single_selected_future_policy_v1.models_v1 import (
    SingleSelectedFutureSelectionV1,
)


class Cap24RuntimeBindingWitnessEpochError(ValueError):
    def __init__(self, reason_code: str) -> None:
        self.reason_code = reason_code
        super().__init__(reason_code)


def _parse_rfc3339_utc_v1(value: str) -> datetime | None:
    text = str(value or "").strip()
    if not text:
        return None
    for fmt in ("%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%dT%H:%M:%S.%fZ"):
        try:
            return datetime.strptime(text, fmt).replace(tzinfo=timezone.utc)
        except ValueError:
            continue
    return None


def resolve_cap24_runtime_binding_witness_epoch_v1(
    *,
    selection: SingleSelectedFutureSelectionV1,
    decision_epoch: str,
) -> str:
    """Witness time for Cap-2.4 runtime binding gate (valid_from..valid_until).

    ``decision_epoch`` is often captured before Cap24 ranking publishes
    ``selection.valid_from`` (ranking.event_time). The gate must witness post-publication
    handoff time, not pre-ranking decision capture.
    """

    decision = str(decision_epoch or "").strip()
    if not decision:
        raise Cap24RuntimeBindingWitnessEpochError("BINDING_EPOCH_MALFORMED")
    valid_from = _parse_rfc3339_utc_v1(selection.valid_from)
    valid_until = _parse_rfc3339_utc_v1(selection.valid_until)
    decision_dt = _parse_rfc3339_utc_v1(decision)
    if valid_from is None or valid_until is None or decision_dt is None:
        raise Cap24RuntimeBindingWitnessEpochError("SELECTION_VALIDITY_MALFORMED")

    def _in_window(dt: datetime) -> bool:
        return valid_from <= dt <= valid_until

    if _in_window(decision_dt):
        return decision
    wall_dt = _parse_rfc3339_utc_v1(selection.selected_at_wall_time)
    if wall_dt is not None and _in_window(wall_dt):
        return wall_dt.strftime("%Y-%m-%dT%H:%M:%SZ")
    return decision
