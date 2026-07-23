"""Phase 4.1 read-only producer binding for Market Landscape V2.

Binds market_instrument and universe_ranking only.
Dynamic scope / regime / switch remain unbound (Phase 4.2).
Lives outside market_dashboard_landscape_v2 so that package stays free of
trading/webui producer imports (architecture guard).

Fail-closed:
- Wired slots without durable producer output → MISSING_SOURCE / INVALID
- Never fabricate OHLCV, ranking, eligibility, or selected instrument
- No decision / Double Play / risk / safety / execution / scope binding
"""

from __future__ import annotations

import os
from datetime import datetime
from pathlib import Path
from typing import Any, Mapping

from .market_dashboard_landscape_v2.availability import Availability
from .market_dashboard_landscape_v2.projections import (
    project_market_instrument_snapshot_v1,
    project_universe_ranking_snapshot_v1,
)
from .market_dashboard_landscape_v2.unavailable import (
    unavailable_market_instrument,
    unavailable_universe_ranking,
)
from .workflow_dashboard_readmodel_v1.universe_selection_contract_v1 import (
    FORBIDDEN_SELECTED_SYMBOLS,
)
from .workflow_dashboard_readmodel_v1.universe_selection_reader_v1 import (
    try_load_universe_selection_for_dashboard,
)

# Reuse the existing workflow-dashboard archive env — no second archive owner.
ENV_ARCHIVE_ROOT = "PEAK_TRADE_WORKFLOW_DASHBOARD_V1_ARCHIVE_ROOT"

REASON_MARKET_CONTEXT_NOT_PERSISTED = "CANONICAL_MARKET_CONTEXT_NOT_PERSISTED_FOR_DASHBOARD"
REASON_UNIVERSE_ABSENT = "UNIVERSE_SELECTION_READMODEL_ABSENT"
REASON_ARCHIVE_ROOT_UNSET = "UNIVERSE_ARCHIVE_ROOT_UNSET"
REASON_SELECTED_FORBIDDEN_SYMBOL = "SELECTED_INSTRUMENT_FORBIDDEN_BTC_USD_OR_SPOT_DUMMY"
REASON_SELECTED_NOT_IN_UNIVERSE = "SELECTED_INSTRUMENT_NOT_IN_CANONICAL_UNIVERSE"
REASON_SOURCE_CONTRADICTION = "MARKET_AND_UNIVERSE_SELECTED_INSTRUMENT_CONTRADICTION"
REASON_SELECTED_IDENTITY_PROJECTED = "SELECTED_INSTRUMENT_IDENTITY_FROM_UNIVERSE_SELECTION"

PHASE_4_1_BOUND_SLOTS: tuple[str, ...] = (
    "market_instrument",
    "universe_ranking",
)


def resolve_landscape_archive_root(
    archive_root: str | Path | None = None,
) -> Path | None:
    """Resolve durable archive root for universe_selection readmodel load."""
    if archive_root is not None:
        raw = str(archive_root).strip()
        if not raw:
            return None
        path = Path(raw).expanduser()
        try:
            path = path.resolve(strict=True)
        except OSError:
            return None
        return path if path.is_dir() else None
    env_raw = (os.getenv(ENV_ARCHIVE_ROOT) or "").strip()
    if not env_raw:
        return None
    path = Path(env_raw).expanduser()
    try:
        path = path.resolve(strict=True)
    except OSError:
        return None
    return path if path.is_dir() else None


def _row_dict(row: Any) -> dict[str, Any]:
    return {
        "row_id": row.row_id,
        "symbol": row.symbol,
        "rank": row.rank,
        "exchange": row.exchange,
        "display_score": row.display_score,
        "notes": row.notes,
    }


def _bind_universe_ranking(
    *,
    generated_at: datetime,
    archive_root: Path | None,
    git_sha: str | None,
) -> Any:
    if archive_root is None:
        return unavailable_universe_ranking(
            availability=Availability.MISSING_SOURCE,
            generated_at=generated_at,
            reason=REASON_ARCHIVE_ROOT_UNSET,
        )
    slice_v1 = try_load_universe_selection_for_dashboard(archive_root)
    if slice_v1.load_errors:
        return unavailable_universe_ranking(
            availability=Availability.INVALID,
            generated_at=generated_at,
            reason=str(slice_v1.load_errors[0]),
        )
    if not slice_v1.loaded:
        return unavailable_universe_ranking(
            availability=Availability.MISSING_SOURCE,
            generated_at=generated_at,
            reason=REASON_UNIVERSE_ABSENT,
        )

    ranking_rows = [_row_dict(row) for row in slice_v1.ranking]
    universe_rows = [_row_dict(row) for row in slice_v1.universe]
    selected_id = None
    if slice_v1.selected_future is not None:
        selected_id = slice_v1.selected_future.symbol

    if selected_id is not None and selected_id in FORBIDDEN_SELECTED_SYMBOLS:
        return unavailable_universe_ranking(
            availability=Availability.INVALID,
            generated_at=generated_at,
            reason=REASON_SELECTED_FORBIDDEN_SYMBOL,
        )

    if selected_id is not None and universe_rows:
        membership = {str(row["symbol"]) for row in universe_rows}
        if selected_id not in membership:
            return unavailable_universe_ranking(
                availability=Availability.INVALID,
                generated_at=generated_at,
                reason=REASON_SELECTED_NOT_IN_UNIVERSE,
            )

    reason_codes = ["UNIVERSE_SELECTION_READMODEL_PROJECTED"]
    if not ranking_rows:
        reason_codes.append("TOP20_RANKING_NOT_PRESENT_IN_READMODEL")
    if not universe_rows:
        reason_codes.append("UNIVERSE_MEMBERSHIP_NOT_PRESENT_IN_READMODEL")
    if selected_id is None:
        reason_codes.append("SELECTED_FUTURE_NOT_PRESENT_IN_READMODEL")

    if not ranking_rows and not universe_rows and selected_id is None:
        return unavailable_universe_ranking(
            availability=Availability.MISSING_SOURCE,
            generated_at=generated_at,
            reason=REASON_UNIVERSE_ABSENT,
        )

    return project_universe_ranking_snapshot_v1(
        ranking=ranking_rows,
        universe=universe_rows,
        selected_instrument_id=selected_id,
        reason_codes=tuple(reason_codes),
        generated_at=generated_at,
        effective_at=generated_at,
        source_reference=str(archive_root / "readmodels" / "universe_selection_readmodel.v1.json"),
        git_sha=git_sha,
    )


def _market_from_universe_selected(
    *,
    generated_at: datetime,
    archive_root: Path,
    git_sha: str | None,
    universe_snap: Any,
) -> Any:
    """Project selected-instrument identity from universe selection only.

    Does not invent market_type or mark_price. OHLCV remains unbound.
    """
    if universe_snap.availability is not Availability.AVAILABLE:
        return unavailable_market_instrument(
            availability=Availability.MISSING_SOURCE,
            generated_at=generated_at,
            reason=REASON_MARKET_CONTEXT_NOT_PERSISTED,
        )
    selected = universe_snap.selected_instrument_id
    if not selected:
        return unavailable_market_instrument(
            availability=Availability.MISSING_SOURCE,
            generated_at=generated_at,
            reason=REASON_MARKET_CONTEXT_NOT_PERSISTED,
        )
    venue = None
    for row in (*universe_snap.universe, *universe_snap.ranking):
        if row.get("symbol") == selected and row.get("exchange"):
            venue = str(row["exchange"])
            break
    return project_market_instrument_snapshot_v1(
        instrument_id=str(selected),
        venue=venue,
        market_type=None,
        mark_price=None,
        reason_codes=(REASON_SELECTED_IDENTITY_PROJECTED,),
        generated_at=generated_at,
        effective_at=generated_at,
        source_reference=str(archive_root / "readmodels" / "universe_selection_readmodel.v1.json"),
        git_sha=git_sha,
        producer_module=("webui.workflow_dashboard_readmodel_v1.universe_selection_contract_v1"),
        source_kind="universe_selection_selected_instrument",
    )


def bind_market_universe_slots(
    *,
    generated_at: datetime,
    archive_root: str | Path | None = None,
    git_sha: str | None = None,
    market_instrument_fields: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Return Phase 4.1 slot overrides (market_instrument + universe_ranking).

    market_instrument_fields accepts already-computed CanonicalMarketContext
    field dicts for tests and future durable loaders. Absent producer fields
    may still bind identity from universe selected_future when present.
    Never invent mark price, OHLCV, ranking, or eligibility.
    """
    if generated_at.tzinfo is None:
        raise ValueError("generated_at must be timezone-aware")
    root = resolve_landscape_archive_root(archive_root)

    universe = _bind_universe_ranking(
        generated_at=generated_at,
        archive_root=root,
        git_sha=git_sha,
    )

    if market_instrument_fields is not None:
        required = ("instrument_id",)
        missing = [key for key in required if key not in market_instrument_fields]
        if missing:
            raise KeyError(f"market_instrument_fields missing required keys: {missing}")
        market = project_market_instrument_snapshot_v1(
            instrument_id=str(market_instrument_fields["instrument_id"]),
            venue=(
                None
                if market_instrument_fields.get("venue") is None
                else str(market_instrument_fields["venue"])
            ),
            market_type=(
                None
                if market_instrument_fields.get("market_type") is None
                else str(market_instrument_fields["market_type"])
            ),
            mark_price=(
                None
                if market_instrument_fields.get("mark_price") is None
                else float(market_instrument_fields["mark_price"])
            ),
            reason_codes=tuple(
                str(code) for code in market_instrument_fields.get("reason_codes", ())
            ),
            generated_at=generated_at,
            effective_at=market_instrument_fields.get("effective_at", generated_at),
            source_reference=market_instrument_fields.get("source_reference"),
            evidence_digest=market_instrument_fields.get("evidence_digest"),
            git_sha=git_sha,
            producer_module=str(
                market_instrument_fields.get(
                    "producer_module",
                    "trading.master_v2.canonical_market_context_v1",
                )
            ),
        )
        selected = getattr(universe, "selected_instrument_id", None)
        if (
            universe.availability is Availability.AVAILABLE
            and selected
            and market.instrument_id != selected
        ):
            market = unavailable_market_instrument(
                availability=Availability.INVALID,
                generated_at=generated_at,
                reason=REASON_SOURCE_CONTRADICTION,
            )
            universe = unavailable_universe_ranking(
                availability=Availability.INVALID,
                generated_at=generated_at,
                reason=REASON_SOURCE_CONTRADICTION,
            )
    elif root is not None:
        market = _market_from_universe_selected(
            generated_at=generated_at,
            archive_root=root,
            git_sha=git_sha,
            universe_snap=universe,
        )
    else:
        market = unavailable_market_instrument(
            availability=Availability.MISSING_SOURCE,
            generated_at=generated_at,
            reason=REASON_MARKET_CONTEXT_NOT_PERSISTED,
        )

    return {
        "market_instrument": market,
        "universe_ranking": universe,
    }
