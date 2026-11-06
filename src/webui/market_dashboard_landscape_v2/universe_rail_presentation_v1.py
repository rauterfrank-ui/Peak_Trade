"""Universe / TOP-20 / Selection rail presentation (S01 consumer only).

Reads UniverseRankingSnapshotV1 fields only. Never sorts, ranks, selects, or
eligibility-evaluates. RENDER_ORDER_SOURCE=READMODEL_ONLY.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Any, Mapping

from .availability import Availability
from .contracts import UniverseRankingSnapshotV1

MAX_RANKING_ROWS_CONTRACT = 20

_AVAILABILITY_LABELS: Mapping[Availability, str] = {
    Availability.AVAILABLE: "AVAILABLE",
    Availability.NOT_BOUND: "NOT_BOUND",
    Availability.MISSING_SOURCE: "MISSING_SOURCE",
    Availability.STALE: "STALE",
    Availability.INVALID: "INVALID",
}


def _format_decimal_display_v1(value: Any) -> str:
    decimal_value = Decimal(str(value))
    if decimal_value == decimal_value.to_integral_value():
        return format(decimal_value.to_integral_value(), "f")
    plain = format(decimal_value.normalize(), "f")
    if plain in {"-0", "-0.0"}:
        return "0"
    return plain


REASON_TOP20_ABSENT = "TOP20_RANKING_NOT_PRESENT_IN_READMODEL"
REASON_SELECTED_ABSENT = "SELECTED_FUTURE_NOT_PRESENT_IN_READMODEL"


def _score_display(row: Mapping[str, Any]) -> str:
    raw = row.get("display_score")
    if raw is None or raw == "":
        return "—"
    try:
        return _format_decimal_display_v1(raw)
    except (TypeError, ValueError):
        return "—"


def _ranking_board_display_state(
    snap: UniverseRankingSnapshotV1,
) -> str:
    if snap.availability is Availability.INVALID:
        return "INVALID"
    if snap.availability is Availability.MISSING_SOURCE:
        return "MISSING"
    if snap.availability is Availability.NOT_BOUND:
        return "MISSING"
    rows = snap.ranking
    codes = set(snap.reason_codes)
    if not rows:
        if REASON_TOP20_ABSENT in codes:
            return "MISSING"
        return "MISSING"
    if REASON_TOP20_ABSENT in codes or len(rows) < MAX_RANKING_ROWS_CONTRACT:
        return "PARTIAL"
    return "FULL"


def _selected_future_display_state(snap: UniverseRankingSnapshotV1) -> str:
    if snap.availability not in (Availability.AVAILABLE, Availability.STALE):
        return "MISSING"
    if snap.selected_instrument_id is None:
        return "MISSING"
    if REASON_SELECTED_ABSENT in snap.reason_codes:
        return "PARTIAL"
    return "AVAILABLE"


def _build_ranking_board_rows(
    snap: UniverseRankingSnapshotV1,
) -> tuple[dict[str, Any], ...]:
    """Preserve readmodel row order; never sort by score or rank."""
    selected = snap.selected_instrument_id
    out: list[dict[str, Any]] = []
    for index, row in enumerate(snap.ranking):
        symbol = str(row.get("symbol") or "")
        rank_raw = row.get("rank")
        rank = (
            int(rank_raw) if isinstance(rank_raw, int) and not isinstance(rank_raw, bool) else None
        )
        out.append(
            {
                "row_order_index": index,
                "rank": rank,
                "symbol": symbol,
                "display_score": row.get("display_score"),
                "display_score_label": _score_display(row),
                "is_selected": bool(selected and symbol == selected),
                "exchange": row.get("exchange"),
            }
        )
    return tuple(out)


def _selected_score_from_ranking_rows(
    snap: UniverseRankingSnapshotV1,
) -> str:
    selected = snap.selected_instrument_id
    if not selected:
        return "—"
    for row in snap.ranking:
        if str(row.get("symbol") or "") == selected:
            return _score_display(row)
    return "—"


@dataclass(frozen=True)
class UniverseRailPresentationV1:
    """Template-ready universe rail context."""

    watchlist_availability: str
    watchlist_label: str
    membership_in_universe_label: str
    rank_label: str
    selected_instrument_id: str | None
    selection_reason_availability: str
    selection_reason_label: str
    source_run_id: str | None
    session_availability: str
    session_label: str
    ranking_board_display_state: str
    ranking_board_row_count: int
    ranking_board_rows: tuple[dict[str, Any], ...]
    selected_future_display_state: str
    selected_future_instrument: str
    selected_future_rank: str
    selected_future_score: str
    selected_future_selection_reason: str
    provenance_availability: str
    provenance_freshness_label: str
    provenance_producer_generated_at: str | None
    provenance_reason_codes: tuple[str, ...]
    universe_membership_row_count: int

    def to_template_dict(self) -> dict[str, Any]:
        return {
            "watchlist_availability": self.watchlist_availability,
            "watchlist_label": self.watchlist_label,
            "membership_label": self.membership_in_universe_label,
            "membership_in_universe_label": self.membership_in_universe_label,
            "rank_label": self.rank_label,
            "selected_instrument_id": self.selected_instrument_id,
            "selection_reason_availability": self.selection_reason_availability,
            "selection_reason_label": self.selection_reason_label,
            "source_run_id": self.source_run_id,
            "session_availability": self.session_availability,
            "session_label": self.session_label,
            "ranking_board": {
                "display_state": self.ranking_board_display_state,
                "row_count": self.ranking_board_row_count,
                "expected_max_rows": MAX_RANKING_ROWS_CONTRACT,
                "rows": list(self.ranking_board_rows),
            },
            "selected_future": {
                "display_state": self.selected_future_display_state,
                "instrument_id": self.selected_future_instrument,
                "rank_display": self.selected_future_rank,
                "score_display": self.selected_future_score,
                "selection_reason_display": self.selected_future_selection_reason,
            },
            "provenance": {
                "source_run_id": self.source_run_id or "—",
                "availability": self.provenance_availability,
                "freshness_label": self.provenance_freshness_label,
                "producer_generated_at": self.provenance_producer_generated_at or "—",
                "reason_codes": list(self.provenance_reason_codes),
            },
            "universe_membership_row_count": self.universe_membership_row_count,
        }


def build_universe_rail_presentation_v1(
    snap: UniverseRankingSnapshotV1,
) -> UniverseRailPresentationV1:
    """Build fail-closed universe rail presentation from projected S01 snapshot."""
    availability = snap.availability
    ranking_rows = _build_ranking_board_rows(snap)
    universe_rows = [dict(row) for row in snap.universe]
    selected_id = snap.selected_instrument_id

    membership_label = _AVAILABILITY_LABELS[availability]
    watchlist_label = _AVAILABILITY_LABELS[availability]
    ranking_label = _AVAILABILITY_LABELS[availability]
    selection_reason_label = _AVAILABILITY_LABELS[availability]
    source_run_id = snap.source_run_id

    if availability in (Availability.AVAILABLE, Availability.STALE):
        if universe_rows:
            watchlist_label = str(len(universe_rows))
        else:
            watchlist_label = "NOT_AVAILABLE"
        selected_rank = snap.selected_rank
        if selected_rank is not None:
            ranking_label = f"#{selected_rank}"
        elif selected_id is not None:
            ranking_label = "NOT_AVAILABLE"
        elif not ranking_rows:
            ranking_label = "NOT_AVAILABLE"
        reason = snap.selection_reason
        if isinstance(reason, str) and reason.strip():
            selection_reason_label = reason.strip()
        else:
            selection_reason_label = "—"
        if selected_id and universe_rows:
            membership = {str(row.get("symbol")) for row in universe_rows}
            membership_label = "IN_UNIVERSE" if selected_id in membership else "NOT_IN_UNIVERSE"
        elif selected_id is None:
            membership_label = "NOT_AVAILABLE"
        elif not universe_rows:
            membership_label = "NOT_AVAILABLE"

    board_state = _ranking_board_display_state(snap)
    selected_state = _selected_future_display_state(snap)

    if selected_state == "MISSING":
        selected_instrument = _AVAILABILITY_LABELS.get(availability, "MISSING_SOURCE")
        selected_rank_disp = _AVAILABILITY_LABELS.get(availability, "MISSING_SOURCE")
        selected_score_disp = "—"
        selected_reason_disp = _AVAILABILITY_LABELS.get(availability, "MISSING_SOURCE")
    else:
        selected_instrument = selected_id or "—"
        if snap.selected_rank is not None:
            selected_rank_disp = f"#{snap.selected_rank}"
        else:
            selected_rank_disp = "NOT_AVAILABLE"
        selected_score_disp = _selected_score_from_ranking_rows(snap)
        if isinstance(snap.selection_reason, str) and snap.selection_reason.strip():
            selected_reason_disp = snap.selection_reason.strip()
        else:
            selected_reason_disp = "—"

    freshness_label = _AVAILABILITY_LABELS[availability]
    if snap.freshness.is_stale and snap.freshness.stale_reason:
        freshness_label = f"STALE ({snap.freshness.stale_reason})"

    producer_at = snap.provenance.generated_at.isoformat().replace("+00:00", "Z")

    session_availability = (
        availability.value
        if source_run_id
        else (
            Availability.MISSING_SOURCE.value
            if availability in (Availability.AVAILABLE, Availability.STALE)
            else availability.value
        )
    )
    session_label = (
        source_run_id
        if source_run_id
        else (
            "—"
            if availability in (Availability.AVAILABLE, Availability.STALE)
            else _AVAILABILITY_LABELS[availability]
        )
    )

    return UniverseRailPresentationV1(
        watchlist_availability=availability.value,
        watchlist_label=watchlist_label,
        membership_in_universe_label=membership_label,
        rank_label=ranking_label,
        selected_instrument_id=selected_id,
        selection_reason_availability=availability.value,
        selection_reason_label=selection_reason_label,
        source_run_id=source_run_id,
        session_availability=session_availability,
        session_label=session_label,
        ranking_board_display_state=board_state,
        ranking_board_row_count=len(ranking_rows),
        ranking_board_rows=ranking_rows,
        selected_future_display_state=selected_state,
        selected_future_instrument=str(selected_instrument),
        selected_future_rank=str(selected_rank_disp),
        selected_future_score=str(selected_score_disp),
        selected_future_selection_reason=str(selected_reason_disp),
        provenance_availability=availability.value,
        provenance_freshness_label=freshness_label,
        provenance_producer_generated_at=producer_at,
        provenance_reason_codes=snap.reason_codes,
        universe_membership_row_count=len(universe_rows),
    )
