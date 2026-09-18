"""Optional governed instrument pin for Cap 2.3 N=1 selection.

Non-authoritative constraint only. Does not create, persist, or replace
SingleSelectedFutureSelectionV1. Default Cap 2.3 path remains unpinned.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Optional, Sequence

from src.ops.single_selected_future_policy_v1.constants_v1 import ELIGIBILITY_ELIGIBLE
from src.ops.single_selected_future_policy_v1.reason_codes_v1 import SelectionFailureCodeV1

SCHEMA_VERSION = "governed_cap23_instrument_pin.v1"

PIN_IS_SELECTION_AUTHORITY = False
ADAPTER_MAY_WRITE_CAP23_SELECTION = False
ADAPTER_MAY_RERANK = False
ADAPTER_MAY_RESELECT = False
CROSS_UNIVERSE_SELECTION = False
CROSS_UNIVERSE_PIN = False
CROSS_UNIVERSE_REPLACEMENT = False
CROSS_UNIVERSE_FALLBACK = False
CROSS_UNIVERSE_CANDIDATE_BORROWING = False
CROSS_UNIVERSE_RERANKING = False
MULTI_UNIVERSE_MERGE = False
INSTRUMENT_ID_ALONE_SUFFICIENT = False


def lane_state_root_key(path: Path | str) -> str:
    return str(Path(path).expanduser().resolve())


@dataclass(frozen=True)
class GovernedCap23InstrumentPinV1:
    """Immutable Cap 2.3 candidate constraint. Not a selection DTO."""

    canonical_instrument_id: str
    universe_snapshot_id: str
    ranking_snapshot_id: str
    ranking_integrity_digest: str
    lane_state_root: str
    resolved_venue_native_id: str
    schema_version: str = SCHEMA_VERSION
    pin_is_selection_authority: bool = PIN_IS_SELECTION_AUTHORITY
    adapter_may_write_cap23_selection: bool = ADAPTER_MAY_WRITE_CAP23_SELECTION
    adapter_may_rerank: bool = ADAPTER_MAY_RERANK
    adapter_may_reselect: bool = ADAPTER_MAY_RESELECT
    cross_universe_selection: bool = CROSS_UNIVERSE_SELECTION
    cross_universe_pin: bool = CROSS_UNIVERSE_PIN
    cross_universe_replacement: bool = CROSS_UNIVERSE_REPLACEMENT
    cross_universe_fallback: bool = CROSS_UNIVERSE_FALLBACK
    cross_universe_candidate_borrowing: bool = CROSS_UNIVERSE_CANDIDATE_BORROWING
    cross_universe_reranking: bool = CROSS_UNIVERSE_RERANKING
    multi_universe_merge: bool = MULTI_UNIVERSE_MERGE
    instrument_id_alone_sufficient: bool = INSTRUMENT_ID_ALONE_SUFFICIENT

    def to_dict(self) -> dict[str, Any]:
        return {
            "adapter_may_rerank": bool(self.adapter_may_rerank),
            "adapter_may_reselect": bool(self.adapter_may_reselect),
            "adapter_may_write_cap23_selection": bool(self.adapter_may_write_cap23_selection),
            "canonical_instrument_id": self.canonical_instrument_id,
            "cross_universe_candidate_borrowing": bool(self.cross_universe_candidate_borrowing),
            "cross_universe_fallback": bool(self.cross_universe_fallback),
            "cross_universe_pin": bool(self.cross_universe_pin),
            "cross_universe_replacement": bool(self.cross_universe_replacement),
            "cross_universe_reranking": bool(self.cross_universe_reranking),
            "cross_universe_selection": bool(self.cross_universe_selection),
            "instrument_id_alone_sufficient": bool(self.instrument_id_alone_sufficient),
            "lane_state_root": self.lane_state_root,
            "multi_universe_merge": bool(self.multi_universe_merge),
            "pin_is_selection_authority": bool(self.pin_is_selection_authority),
            "ranking_integrity_digest": self.ranking_integrity_digest,
            "ranking_snapshot_id": self.ranking_snapshot_id,
            "resolved_venue_native_id": self.resolved_venue_native_id,
            "schema_version": self.schema_version,
            "universe_snapshot_id": self.universe_snapshot_id,
        }


def pin_authority_failure_codes(pin: GovernedCap23InstrumentPinV1) -> tuple[str, ...]:
    codes: list[str] = []
    if (
        pin.pin_is_selection_authority
        or pin.adapter_may_write_cap23_selection
        or pin.adapter_may_rerank
        or pin.adapter_may_reselect
        or pin.instrument_id_alone_sufficient
    ):
        codes.append(SelectionFailureCodeV1.GOVERNED_PIN_SELECTION_AUTHORITY_CLAIM_FORBIDDEN.value)
    if (
        pin.cross_universe_selection
        or pin.cross_universe_pin
        or pin.cross_universe_replacement
        or pin.cross_universe_fallback
        or pin.cross_universe_candidate_borrowing
        or pin.cross_universe_reranking
        or pin.multi_universe_merge
    ):
        codes.append(SelectionFailureCodeV1.GOVERNED_PIN_CROSS_UNIVERSE_FORBIDDEN.value)
    if pin.schema_version != SCHEMA_VERSION:
        codes.append(SelectionFailureCodeV1.GOVERNED_PIN_SCHEMA_MISMATCH.value)
    return tuple(sorted(set(codes)))


def resolve_governed_pin_candidate_v1(
    pin: GovernedCap23InstrumentPinV1,
    *,
    universe_snapshot_id: str,
    ranking_snapshot_id: str,
    ranking_integrity_digest: str,
    ranked_candidates: Sequence[Mapping[str, Any]],
    lane_state_root: Path | str | None,
) -> tuple[Optional[dict[str, Any]], tuple[str, ...]]:
    """Resolve one full-snapshot candidate. Never merges other rankings."""
    authority_codes = pin_authority_failure_codes(pin)
    if authority_codes:
        return None, authority_codes
    if lane_state_root is None or not str(lane_state_root).strip():
        return None, (SelectionFailureCodeV1.GOVERNED_PIN_MISSING_LANE_BINDING.value,)
    if lane_state_root_key(lane_state_root) != lane_state_root_key(pin.lane_state_root):
        return None, (SelectionFailureCodeV1.GOVERNED_PIN_LANE_STATE_ROOT_MISMATCH.value,)

    expected_universe = str(universe_snapshot_id or "").strip()
    expected_ranking = str(ranking_snapshot_id or "").strip()
    expected_digest = str(ranking_integrity_digest or "").strip()
    pin_universe = str(pin.universe_snapshot_id or "").strip()
    pin_ranking = str(pin.ranking_snapshot_id or "").strip()
    pin_digest = str(pin.ranking_integrity_digest or "").strip()
    if not expected_universe or not pin_universe or pin_universe != expected_universe:
        return None, (SelectionFailureCodeV1.GOVERNED_PIN_UNIVERSE_MISMATCH.value,)
    if (
        not expected_ranking
        or not expected_digest
        or not pin_ranking
        or not pin_digest
        or pin_ranking != expected_ranking
        or pin_digest != expected_digest
    ):
        return None, (SelectionFailureCodeV1.GOVERNED_PIN_PROVENANCE_MISMATCH.value,)

    instrument_id = str(pin.canonical_instrument_id or "").strip()
    if not instrument_id:
        return None, (SelectionFailureCodeV1.GOVERNED_PIN_INSTRUMENT_NOT_IN_RANKING.value,)

    matches = [
        dict(row)
        for row in ranked_candidates
        if str(row.get("canonical_instrument_id") or "").strip() == instrument_id
    ]
    if not matches:
        return None, (SelectionFailureCodeV1.GOVERNED_PIN_INSTRUMENT_NOT_IN_RANKING.value,)
    natives = {str(row.get("venue_native_id") or "").strip() for row in matches}
    if len(matches) != 1 or len(natives) != 1 or not next(iter(natives)):
        return None, (SelectionFailureCodeV1.GOVERNED_PIN_AMBIGUOUS_NATIVE_ID.value,)
    row = matches[0]
    native = str(row.get("venue_native_id") or "").strip()
    if native != str(pin.resolved_venue_native_id or "").strip():
        return None, (SelectionFailureCodeV1.GOVERNED_PIN_VENUE_NATIVE_MISMATCH.value,)
    if str(row.get("eligibility_status") or "") != ELIGIBILITY_ELIGIBLE:
        return None, (SelectionFailureCodeV1.GOVERNED_PIN_CANDIDATE_INELIGIBLE.value,)
    return row, ()
