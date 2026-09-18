"""Build a governed Cap 2.3 pin from one same-universe ranking member.

Does not produce, persist, or write a Cap 2.3 selection DTO.
Does not join MF runtime, rewrite MF_SINGLE_EGRESS_V1, or merge universes.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping, NoReturn

from src.ops.current_mf_member_to_pinned_cap23_n1_adapter_v1.constants_v1 import (
    ADAPTER_MAY_RERANK,
    ADAPTER_MAY_RESELECT,
    ADAPTER_MAY_WRITE_CAP23_SELECTION,
    CROSS_UNIVERSE_CANDIDATE_BORROWING,
    CROSS_UNIVERSE_FALLBACK,
    CROSS_UNIVERSE_PIN,
    CROSS_UNIVERSE_REPLACEMENT,
    CROSS_UNIVERSE_RERANKING,
    CROSS_UNIVERSE_SELECTION,
    INSTRUMENT_ID_ALONE_SUFFICIENT,
    MULTI_UNIVERSE_MERGE,
    PIN_IS_SELECTION_AUTHORITY,
)
from src.ops.single_selected_future_policy_v1.constants_v1 import ELIGIBILITY_ELIGIBLE
from src.ops.single_selected_future_policy_v1.governed_pin_v1 import (
    SCHEMA_VERSION,
    GovernedCap23InstrumentPinV1,
    lane_state_root_key,
)
from src.ops.single_selected_future_policy_v1.reason_codes_v1 import SelectionFailureCodeV1


class GovernedCap23PinAdapterError(ValueError):
    def __init__(self, code: str, detail: str = "") -> None:
        super().__init__(f"{code}:{detail}" if detail else code)
        self.failure_code = code
        self.detail = detail


def _fail(code: str, detail: str = "") -> NoReturn:
    raise GovernedCap23PinAdapterError(code, detail)


def _require_identity_field(snapshot: Mapping[str, Any], key: str) -> str:
    value = str(snapshot.get(key) or "").strip()
    if not value:
        _fail(SelectionFailureCodeV1.GOVERNED_PIN_PROVENANCE_MISMATCH.value, key)
    return value


def build_governed_cap23_pin_v1(
    *,
    canonical_instrument_id: str,
    ranking_snapshot: Mapping[str, Any],
    lane_state_root: Path | str,
    replacement_ranking_snapshot: Mapping[str, Any] | None = None,
    fallback_ranking_snapshot: Mapping[str, Any] | None = None,
    underfill_ranking_snapshot: Mapping[str, Any] | None = None,
) -> GovernedCap23InstrumentPinV1:
    """Return a non-authoritative pin bound to one full Cap 2.2 snapshot."""
    if (
        replacement_ranking_snapshot is not None
        or fallback_ranking_snapshot is not None
        or underfill_ranking_snapshot is not None
    ):
        _fail(SelectionFailureCodeV1.GOVERNED_PIN_CROSS_UNIVERSE_FORBIDDEN.value, "extra_ranking")
    if not isinstance(ranking_snapshot, Mapping):
        _fail(SelectionFailureCodeV1.GOVERNED_PIN_PROVENANCE_MISMATCH.value, "ranking_snapshot")

    instrument_id = str(canonical_instrument_id or "").strip()
    if not instrument_id:
        _fail(SelectionFailureCodeV1.GOVERNED_PIN_INSTRUMENT_NOT_IN_RANKING.value, "empty")

    universe_snapshot_id = _require_identity_field(ranking_snapshot, "universe_snapshot_id")
    ranking_snapshot_id = _require_identity_field(ranking_snapshot, "ranking_snapshot_id")
    ranking_integrity_digest = _require_identity_field(ranking_snapshot, "integrity_digest")
    lane_key = lane_state_root_key(lane_state_root)

    ranked = list(ranking_snapshot.get("ranked_candidates") or [])
    matches = [
        row
        for row in ranked
        if isinstance(row, Mapping)
        and str(row.get("canonical_instrument_id") or "").strip() == instrument_id
    ]
    if not matches:
        _fail(SelectionFailureCodeV1.GOVERNED_PIN_INSTRUMENT_NOT_IN_RANKING.value, instrument_id)
    natives = {str(row.get("venue_native_id") or "").strip() for row in matches}
    if len(matches) != 1 or len(natives) != 1 or not next(iter(natives)):
        _fail(SelectionFailureCodeV1.GOVERNED_PIN_AMBIGUOUS_NATIVE_ID.value, instrument_id)
    row = matches[0]
    if str(row.get("eligibility_status") or "") != ELIGIBILITY_ELIGIBLE:
        _fail(SelectionFailureCodeV1.GOVERNED_PIN_CANDIDATE_INELIGIBLE.value, instrument_id)
    venue_native_id = str(row.get("venue_native_id") or "").strip()

    pin = GovernedCap23InstrumentPinV1(
        canonical_instrument_id=instrument_id,
        universe_snapshot_id=universe_snapshot_id,
        ranking_snapshot_id=ranking_snapshot_id,
        ranking_integrity_digest=ranking_integrity_digest,
        lane_state_root=lane_key,
        resolved_venue_native_id=venue_native_id,
        schema_version=SCHEMA_VERSION,
        pin_is_selection_authority=PIN_IS_SELECTION_AUTHORITY,
        adapter_may_write_cap23_selection=ADAPTER_MAY_WRITE_CAP23_SELECTION,
        adapter_may_rerank=ADAPTER_MAY_RERANK,
        adapter_may_reselect=ADAPTER_MAY_RESELECT,
        cross_universe_selection=CROSS_UNIVERSE_SELECTION,
        cross_universe_pin=CROSS_UNIVERSE_PIN,
        cross_universe_replacement=CROSS_UNIVERSE_REPLACEMENT,
        cross_universe_fallback=CROSS_UNIVERSE_FALLBACK,
        cross_universe_candidate_borrowing=CROSS_UNIVERSE_CANDIDATE_BORROWING,
        cross_universe_reranking=CROSS_UNIVERSE_RERANKING,
        multi_universe_merge=MULTI_UNIVERSE_MERGE,
        instrument_id_alone_sufficient=INSTRUMENT_ID_ALONE_SUFFICIENT,
    )
    return pin
