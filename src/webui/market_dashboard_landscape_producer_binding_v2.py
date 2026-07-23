"""Phase 4.1 read-only producer binding for Market Landscape V2.

Binds market_instrument and universe_ranking only.
Dynamic scope / regime / switch remain unbound (Phase 4.2).
Lives outside market_dashboard_landscape_v2 so that package stays free of
trading/webui producer imports (architecture guard).

Fail-closed:
- Wired slots without durable producer output → MISSING_SOURCE / INVALID
- Producer timestamps preserved; page-assembly time is observation-only
- Aged producer snapshots → STALE (never silently refreshed)
- Never fabricate OHLCV, ranking, eligibility, or selected instrument
- No decision / Double Play / risk / safety / execution / scope binding
"""

from __future__ import annotations

import os
import re
from datetime import datetime, timezone
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

# F2 consuming-surface max_allowed_staleness_seconds for Landscape Phase 4.1.
# Declared here as the dashboard consumer policy; never invent freshness via now().
LANDSCAPE_PHASE41_MAX_AGE_SECONDS = 86_400

REASON_MARKET_CONTEXT_NOT_PERSISTED = "CANONICAL_MARKET_CONTEXT_NOT_PERSISTED_FOR_DASHBOARD"
REASON_UNIVERSE_ABSENT = "UNIVERSE_SELECTION_READMODEL_ABSENT"
REASON_ARCHIVE_ROOT_UNSET = "UNIVERSE_ARCHIVE_ROOT_UNSET"
REASON_SELECTED_FORBIDDEN_SYMBOL = "SELECTED_INSTRUMENT_FORBIDDEN_BTC_USD_OR_SPOT_DUMMY"
REASON_SELECTED_NOT_IN_UNIVERSE = "SELECTED_INSTRUMENT_NOT_IN_CANONICAL_UNIVERSE"
REASON_SOURCE_CONTRADICTION = "MARKET_AND_UNIVERSE_SELECTED_INSTRUMENT_CONTRADICTION"
REASON_SELECTED_IDENTITY_PROJECTED = "SELECTED_INSTRUMENT_IDENTITY_FROM_UNIVERSE_SELECTION"
REASON_PRODUCER_TIMESTAMP_MISSING = "PRODUCER_TIMESTAMP_MISSING"
REASON_PRODUCER_TIMESTAMP_INVALID = "PRODUCER_TIMESTAMP_INVALID"
REASON_PRODUCER_DATA_STALE = "PRODUCER_DATA_EXCEEDED_LANDSCAPE_MAX_AGE"

PHASE_4_1_BOUND_SLOTS: tuple[str, ...] = (
    "market_instrument",
    "universe_ranking",
)

_ISO8601_UTC_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?(Z|\+00:00)$")


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


def parse_producer_utc_timestamp(raw: str | None) -> datetime | None:
    """Parse a producer ISO-8601 UTC timestamp.

    Returns None when absent. Raises ValueError for naive/invalid values
    (fail-closed; never silently coerce to local/now).
    """
    if raw is None:
        return None
    if not isinstance(raw, str) or not raw.strip():
        raise ValueError(REASON_PRODUCER_TIMESTAMP_INVALID)
    text = raw.strip()
    if not _ISO8601_UTC_PATTERN.match(text):
        raise ValueError(REASON_PRODUCER_TIMESTAMP_INVALID)
    normalized = text.replace("Z", "+00:00")
    parsed = datetime.fromisoformat(normalized)
    if parsed.tzinfo is None:
        raise ValueError(REASON_PRODUCER_TIMESTAMP_INVALID)
    return parsed.astimezone(timezone.utc)


def classify_producer_freshness(
    *,
    producer_at: datetime,
    as_of: datetime,
    max_age_seconds: int = LANDSCAPE_PHASE41_MAX_AGE_SECONDS,
) -> tuple[Availability, bool, str | None]:
    """Compare producer timestamp to observation clock; never refresh producer time."""
    if as_of.tzinfo is None or producer_at.tzinfo is None:
        raise ValueError(REASON_PRODUCER_TIMESTAMP_INVALID)
    age = (as_of.astimezone(timezone.utc) - producer_at.astimezone(timezone.utc)).total_seconds()
    if age < 0:
        # Future producer timestamps are invalid for this consumer surface.
        raise ValueError(REASON_PRODUCER_TIMESTAMP_INVALID)
    if age > max_age_seconds:
        return Availability.STALE, True, REASON_PRODUCER_DATA_STALE
    return Availability.AVAILABLE, False, None


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
    as_of: datetime,
    archive_root: Path | None,
    git_sha: str | None,
) -> tuple[Any, Any | None]:
    """Return (universe_snapshot, loaded_slice_or_none)."""
    if archive_root is None:
        return (
            unavailable_universe_ranking(
                availability=Availability.MISSING_SOURCE,
                generated_at=as_of,
                reason=REASON_ARCHIVE_ROOT_UNSET,
            ),
            None,
        )
    slice_v1 = try_load_universe_selection_for_dashboard(archive_root)
    if slice_v1.load_errors:
        return (
            unavailable_universe_ranking(
                availability=Availability.INVALID,
                generated_at=as_of,
                reason=str(slice_v1.load_errors[0]),
            ),
            None,
        )
    if not slice_v1.loaded:
        return (
            unavailable_universe_ranking(
                availability=Availability.MISSING_SOURCE,
                generated_at=as_of,
                reason=REASON_UNIVERSE_ABSENT,
            ),
            None,
        )

    try:
        producer_at = parse_producer_utc_timestamp(slice_v1.generated_at)
    except ValueError:
        return (
            unavailable_universe_ranking(
                availability=Availability.INVALID,
                generated_at=as_of,
                reason=REASON_PRODUCER_TIMESTAMP_INVALID,
            ),
            slice_v1,
        )
    if producer_at is None:
        return (
            unavailable_universe_ranking(
                availability=Availability.MISSING_SOURCE,
                generated_at=as_of,
                reason=REASON_PRODUCER_TIMESTAMP_MISSING,
            ),
            slice_v1,
        )

    ranking_rows = [_row_dict(row) for row in slice_v1.ranking]
    universe_rows = [_row_dict(row) for row in slice_v1.universe]
    selected_id = None
    if slice_v1.selected_future is not None:
        selected_id = slice_v1.selected_future.symbol

    if selected_id is not None and selected_id in FORBIDDEN_SELECTED_SYMBOLS:
        return (
            unavailable_universe_ranking(
                availability=Availability.INVALID,
                generated_at=as_of,
                reason=REASON_SELECTED_FORBIDDEN_SYMBOL,
            ),
            slice_v1,
        )

    if selected_id is not None and universe_rows:
        membership = {str(row["symbol"]) for row in universe_rows}
        if selected_id not in membership:
            return (
                unavailable_universe_ranking(
                    availability=Availability.INVALID,
                    generated_at=as_of,
                    reason=REASON_SELECTED_NOT_IN_UNIVERSE,
                ),
                slice_v1,
            )

    reason_codes = ["UNIVERSE_SELECTION_READMODEL_PROJECTED"]
    if not ranking_rows:
        reason_codes.append("TOP20_RANKING_NOT_PRESENT_IN_READMODEL")
    if not universe_rows:
        reason_codes.append("UNIVERSE_MEMBERSHIP_NOT_PRESENT_IN_READMODEL")
    if selected_id is None:
        reason_codes.append("SELECTED_FUTURE_NOT_PRESENT_IN_READMODEL")

    if not ranking_rows and not universe_rows and selected_id is None:
        return (
            unavailable_universe_ranking(
                availability=Availability.MISSING_SOURCE,
                generated_at=as_of,
                reason=REASON_UNIVERSE_ABSENT,
            ),
            slice_v1,
        )

    try:
        availability, is_stale, stale_reason = classify_producer_freshness(
            producer_at=producer_at,
            as_of=as_of,
        )
    except ValueError:
        return (
            unavailable_universe_ranking(
                availability=Availability.INVALID,
                generated_at=as_of,
                reason=REASON_PRODUCER_TIMESTAMP_INVALID,
            ),
            slice_v1,
        )
    if is_stale and stale_reason:
        reason_codes.append(stale_reason)

    return (
        project_universe_ranking_snapshot_v1(
            ranking=ranking_rows,
            universe=universe_rows,
            selected_instrument_id=selected_id,
            reason_codes=tuple(reason_codes),
            generated_at=producer_at,
            effective_at=producer_at,
            source_reference=str(
                archive_root / "readmodels" / "universe_selection_readmodel.v1.json"
            ),
            git_sha=git_sha,
            availability=availability,
            max_age_seconds=LANDSCAPE_PHASE41_MAX_AGE_SECONDS,
            is_stale=is_stale,
            stale_reason=stale_reason,
        ),
        slice_v1,
    )


def _market_from_universe_selected(
    *,
    as_of: datetime,
    archive_root: Path,
    git_sha: str | None,
    universe_snap: Any,
    slice_v1: Any | None,
) -> Any:
    """Project selected-instrument identity from universe selection only.

    Uses market_snapshot.captured_at as the market producer timestamp.
    Does not invent market_type or mark_price. OHLCV remains unbound.
    """
    if universe_snap.availability not in (Availability.AVAILABLE, Availability.STALE):
        return unavailable_market_instrument(
            availability=Availability.MISSING_SOURCE,
            generated_at=as_of,
            reason=REASON_MARKET_CONTEXT_NOT_PERSISTED,
        )
    selected = universe_snap.selected_instrument_id
    if not selected:
        return unavailable_market_instrument(
            availability=Availability.MISSING_SOURCE,
            generated_at=as_of,
            reason=REASON_MARKET_CONTEXT_NOT_PERSISTED,
        )
    if slice_v1 is None or slice_v1.market_snapshot is None:
        return unavailable_market_instrument(
            availability=Availability.MISSING_SOURCE,
            generated_at=as_of,
            reason=REASON_PRODUCER_TIMESTAMP_MISSING,
        )
    try:
        producer_at = parse_producer_utc_timestamp(slice_v1.market_snapshot.captured_at)
    except ValueError:
        return unavailable_market_instrument(
            availability=Availability.INVALID,
            generated_at=as_of,
            reason=REASON_PRODUCER_TIMESTAMP_INVALID,
        )
    if producer_at is None:
        return unavailable_market_instrument(
            availability=Availability.MISSING_SOURCE,
            generated_at=as_of,
            reason=REASON_PRODUCER_TIMESTAMP_MISSING,
        )

    venue = None
    for row in (*universe_snap.universe, *universe_snap.ranking):
        if row.get("symbol") == selected and row.get("exchange"):
            venue = str(row["exchange"])
            break
    if venue is None and slice_v1.market_snapshot.exchange:
        venue = str(slice_v1.market_snapshot.exchange)

    try:
        availability, is_stale, stale_reason = classify_producer_freshness(
            producer_at=producer_at,
            as_of=as_of,
        )
    except ValueError:
        return unavailable_market_instrument(
            availability=Availability.INVALID,
            generated_at=as_of,
            reason=REASON_PRODUCER_TIMESTAMP_INVALID,
        )
    reason_codes = [REASON_SELECTED_IDENTITY_PROJECTED]
    if stale_reason:
        reason_codes.append(stale_reason)

    return project_market_instrument_snapshot_v1(
        instrument_id=str(selected),
        venue=venue,
        market_type=None,
        mark_price=None,
        reason_codes=tuple(reason_codes),
        generated_at=producer_at,
        effective_at=producer_at,
        source_reference=str(archive_root / "readmodels" / "universe_selection_readmodel.v1.json"),
        git_sha=git_sha,
        producer_module=("webui.workflow_dashboard_readmodel_v1.universe_selection_contract_v1"),
        source_kind="universe_selection_selected_instrument",
        availability=availability,
        max_age_seconds=LANDSCAPE_PHASE41_MAX_AGE_SECONDS,
        is_stale=is_stale,
        stale_reason=stale_reason,
    )


def bind_market_universe_slots(
    *,
    generated_at: datetime,
    archive_root: str | Path | None = None,
    git_sha: str | None = None,
    market_instrument_fields: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Return Phase 4.1 slot overrides (market_instrument + universe_ranking).

    ``generated_at`` is the dashboard observation/as-of clock only. It must never
    overwrite producer provenance timestamps or fabricate freshness.

    market_instrument_fields accepts already-computed CanonicalMarketContext
    field dicts for tests and future durable loaders. Those fields must carry
    producer ``generated_at`` and/or ``effective_at``.
    """
    if generated_at.tzinfo is None:
        raise ValueError("generated_at must be timezone-aware")
    as_of = generated_at.astimezone(timezone.utc)
    root = resolve_landscape_archive_root(archive_root)

    universe, slice_v1 = _bind_universe_ranking(
        as_of=as_of,
        archive_root=root,
        git_sha=git_sha,
    )

    if market_instrument_fields is not None:
        required = ("instrument_id",)
        missing = [key for key in required if key not in market_instrument_fields]
        if missing:
            raise KeyError(f"market_instrument_fields missing required keys: {missing}")

        raw_producer = market_instrument_fields.get("effective_at")
        if raw_producer is None:
            raw_producer = market_instrument_fields.get("generated_at")

        producer_at: datetime | None
        parse_error: str | None = None
        if isinstance(raw_producer, datetime):
            if raw_producer.tzinfo is None:
                producer_at = None
                parse_error = REASON_PRODUCER_TIMESTAMP_INVALID
            else:
                producer_at = raw_producer.astimezone(timezone.utc)
        elif isinstance(raw_producer, str) or raw_producer is None:
            try:
                producer_at = parse_producer_utc_timestamp(
                    None if raw_producer is None else str(raw_producer)
                )
            except ValueError:
                producer_at = None
                parse_error = REASON_PRODUCER_TIMESTAMP_INVALID
        else:
            producer_at = None
            parse_error = REASON_PRODUCER_TIMESTAMP_INVALID

        if parse_error is not None:
            market = unavailable_market_instrument(
                availability=Availability.INVALID,
                generated_at=as_of,
                reason=parse_error,
            )
        elif producer_at is None:
            market = unavailable_market_instrument(
                availability=Availability.MISSING_SOURCE,
                generated_at=as_of,
                reason=REASON_PRODUCER_TIMESTAMP_MISSING,
            )
        else:
            try:
                availability, is_stale, stale_reason = classify_producer_freshness(
                    producer_at=producer_at,
                    as_of=as_of,
                )
            except ValueError:
                market = unavailable_market_instrument(
                    availability=Availability.INVALID,
                    generated_at=as_of,
                    reason=REASON_PRODUCER_TIMESTAMP_INVALID,
                )
            else:
                reason_codes = [
                    str(code) for code in market_instrument_fields.get("reason_codes", ())
                ]
                if stale_reason:
                    reason_codes.append(stale_reason)
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
                    reason_codes=tuple(reason_codes),
                    generated_at=producer_at,
                    effective_at=producer_at,
                    source_reference=market_instrument_fields.get("source_reference"),
                    evidence_digest=market_instrument_fields.get("evidence_digest"),
                    git_sha=git_sha,
                    producer_module=str(
                        market_instrument_fields.get(
                            "producer_module",
                            "trading.master_v2.canonical_market_context_v1",
                        )
                    ),
                    availability=availability,
                    max_age_seconds=LANDSCAPE_PHASE41_MAX_AGE_SECONDS,
                    is_stale=is_stale,
                    stale_reason=stale_reason,
                )

        selected = getattr(universe, "selected_instrument_id", None)
        if (
            universe.availability in (Availability.AVAILABLE, Availability.STALE)
            and selected
            and getattr(market, "instrument_id", None) is not None
            and market.instrument_id != selected
            and market.availability in (Availability.AVAILABLE, Availability.STALE)
        ):
            market = unavailable_market_instrument(
                availability=Availability.INVALID,
                generated_at=as_of,
                reason=REASON_SOURCE_CONTRADICTION,
            )
            universe = unavailable_universe_ranking(
                availability=Availability.INVALID,
                generated_at=as_of,
                reason=REASON_SOURCE_CONTRADICTION,
            )
    elif root is not None:
        market = _market_from_universe_selected(
            as_of=as_of,
            archive_root=root,
            git_sha=git_sha,
            universe_snap=universe,
            slice_v1=slice_v1,
        )
    else:
        market = unavailable_market_instrument(
            availability=Availability.MISSING_SOURCE,
            generated_at=as_of,
            reason=REASON_MARKET_CONTEXT_NOT_PERSISTED,
        )

    return {
        "market_instrument": market,
        "universe_ranking": universe,
    }
