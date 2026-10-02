"""Cap2.2 VALID snapshot admission adjudication (no economic re-scoring)."""

from __future__ import annotations

from typing import Any, Mapping, Optional, Sequence

from src.ops.productive_futures_ranking_producer_v1.constants_v1 import SNAPSHOT_STATE_VALID
from src.ops.single_selected_future_policy_v1.constants_v1 import ELIGIBILITY_ELIGIBLE
from src.ops.top20_opportunity_evaluation_residency_v1.constants_v1 import REASON_INVALID_CAP22


class ResidencyAdmissionError(ValueError):
    def __init__(self, code: str, detail: str = "") -> None:
        super().__init__(f"{code}:{detail}" if detail else code)
        self.failure_code = code


def validate_cap22_integrity_v1(snapshot: Mapping[str, Any]) -> tuple[str, ...]:
    failures: list[str] = []
    if str(snapshot.get("snapshot_state") or "") != SNAPSHOT_STATE_VALID:
        failures.append(REASON_INVALID_CAP22)
    digest = str(snapshot.get("integrity_digest") or "").strip()
    if not digest:
        failures.append(REASON_INVALID_CAP22)
    else:
        from src.ops.productive_futures_ranking_producer_v1.models_v1 import (
            ProductiveFuturesRankingSnapshotV1,
        )

        try:
            dto = ProductiveFuturesRankingSnapshotV1.from_dict(snapshot)
            if dto.compute_integrity_digest() != digest:
                failures.append(REASON_INVALID_CAP22)
        except Exception:  # noqa: BLE001
            failures.append(REASON_INVALID_CAP22)
    if not str(snapshot.get("ranking_snapshot_id") or "").strip():
        failures.append(REASON_INVALID_CAP22)
    if not str(snapshot.get("universe_snapshot_id") or "").strip():
        failures.append(REASON_INVALID_CAP22)
    return tuple(failures)


def eligible_top20_candidates_v1(
    snapshot: Mapping[str, Any],
) -> tuple[tuple[str, int, Mapping[str, Any]], ...]:
    """Return (canonical_id, rank, row) for each VALID Top20 eligible row."""
    failures = validate_cap22_integrity_v1(snapshot)
    if failures:
        raise ResidencyAdmissionError(failures[0], "snapshot")
    rows: list[tuple[str, int, Mapping[str, Any]]] = []
    for raw in snapshot.get("ranked_candidates") or ():
        if not isinstance(raw, Mapping):
            continue
        if str(raw.get("eligibility_status") or "") != ELIGIBILITY_ELIGIBLE:
            continue
        rank = int(raw.get("rank") or 0)
        if rank < 1 or rank > 20:
            continue
        canonical = str(raw.get("canonical_instrument_id") or "").strip()
        if not canonical:
            continue
        rows.append((canonical, rank, dict(raw)))
    return tuple(rows)


def current_rank_observation_for_instrument_v1(
    snapshot: Mapping[str, Any],
    *,
    canonical_instrument_id: str,
    observed_at_unix: float,
) -> tuple[Optional[int], bool]:
    """Latest Cap2.2 truth only — never fabricates membership."""
    instrument = str(canonical_instrument_id or "").strip()
    for raw in snapshot.get("ranked_candidates") or ():
        if not isinstance(raw, Mapping):
            continue
        if str(raw.get("canonical_instrument_id") or "").strip() != instrument:
            continue
        rank = int(raw.get("rank") or 0)
        in_top20 = (
            1 <= rank <= 20 and str(raw.get("eligibility_status") or "") == ELIGIBILITY_ELIGIBLE
        )
        return rank if in_top20 else rank, in_top20
    return None, False


def admission_events_from_valid_snapshot_v1(
    snapshot: Mapping[str, Any],
    *,
    already_admitted: Sequence[tuple[str, str]],
) -> tuple[tuple[str, int, Mapping[str, Any]], ...]:
    """FIRST_VALID_TOP20 candidates not already in non-terminal residency."""
    active_keys = {tuple(row) for row in already_admitted}
    universe_id = str(snapshot.get("universe_snapshot_id") or "")
    events: list[tuple[str, int, Mapping[str, Any]]] = []
    for canonical, rank, row in eligible_top20_candidates_v1(snapshot):
        key = (universe_id, canonical)
        if key in active_keys:
            continue
        events.append((canonical, rank, row))
    return tuple(events)
