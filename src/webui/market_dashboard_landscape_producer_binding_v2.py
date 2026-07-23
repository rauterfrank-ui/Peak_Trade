"""Phase 4.1 + 4.2 + 4.3A + 4.3B read-only producer binding for Market Landscape V2.

Binds market_instrument, universe_ranking, dynamic_scope lifecycle identity,
canonical_decision evidence, and double_play display projection.
Regime / bull-bear / switch remain unbound.
Lives outside market_dashboard_landscape_v2 so that package stays free of
trading/webui producer imports (architecture guard).

Fail-closed:
- Wired slots without durable producer output → MISSING_SOURCE / INVALID
- Producer timestamps preserved; page-assembly time is observation-only
- Aged producer snapshots → STALE (never silently refreshed)
- Never fabricate OHLCV, ranking, eligibility, selected instrument, scope,
  decisions, or Double Play composition
- Never call scope initializers, trailing-scope runtime owners, switch owners,
  decision producers, compose_double_play_decision, or build_dashboard_display_snapshot
- No risk / safety / execution binding
"""

from __future__ import annotations

import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from .market_dashboard_landscape_v2.availability import Availability
from .market_dashboard_landscape_v2.projections import (
    project_canonical_decision_snapshot_v1,
    project_double_play_snapshot_v1,
    project_dynamic_scope_snapshot_v1,
    project_market_instrument_snapshot_v1,
    project_universe_ranking_snapshot_v1,
)
from .market_dashboard_landscape_v2.unavailable import (
    unavailable_canonical_decision,
    unavailable_double_play,
    unavailable_dynamic_scope,
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

# F2 consuming-surface max_allowed_staleness_seconds for Landscape Phase 4.1+.
# Declared here as the dashboard consumer policy; never invent freshness via now().
LANDSCAPE_PHASE41_MAX_AGE_SECONDS = 86_400
LANDSCAPE_PHASE42_MAX_AGE_SECONDS = LANDSCAPE_PHASE41_MAX_AGE_SECONDS
LANDSCAPE_PHASE43A_MAX_AGE_SECONDS = LANDSCAPE_PHASE41_MAX_AGE_SECONDS
LANDSCAPE_PHASE43B_MAX_AGE_SECONDS = LANDSCAPE_PHASE41_MAX_AGE_SECONDS

REASON_MARKET_CONTEXT_NOT_PERSISTED = "CANONICAL_MARKET_CONTEXT_NOT_PERSISTED_FOR_DASHBOARD"
REASON_SCOPE_NOT_PERSISTED = "CANONICAL_SCOPE_SNAPSHOT_NOT_PERSISTED_FOR_DASHBOARD"
REASON_DECISION_NOT_PERSISTED = "CANONICAL_DECISION_EVIDENCE_NOT_PERSISTED_FOR_DASHBOARD"
REASON_DOUBLE_PLAY_NOT_PERSISTED = "CANONICAL_DOUBLE_PLAY_DISPLAY_NOT_PERSISTED_FOR_DASHBOARD"
REASON_UNIVERSE_ABSENT = "UNIVERSE_SELECTION_READMODEL_ABSENT"
REASON_ARCHIVE_ROOT_UNSET = "UNIVERSE_ARCHIVE_ROOT_UNSET"
REASON_SELECTED_FORBIDDEN_SYMBOL = "SELECTED_INSTRUMENT_FORBIDDEN_BTC_USD_OR_SPOT_DUMMY"
REASON_SELECTED_NOT_IN_UNIVERSE = "SELECTED_INSTRUMENT_NOT_IN_CANONICAL_UNIVERSE"
REASON_SOURCE_CONTRADICTION = "MARKET_AND_UNIVERSE_SELECTED_INSTRUMENT_CONTRADICTION"
REASON_SELECTED_IDENTITY_PROJECTED = "SELECTED_INSTRUMENT_IDENTITY_FROM_UNIVERSE_SELECTION"
REASON_PRODUCER_TIMESTAMP_MISSING = "PRODUCER_TIMESTAMP_MISSING"
REASON_PRODUCER_TIMESTAMP_INVALID = "PRODUCER_TIMESTAMP_INVALID"
REASON_PRODUCER_DATA_STALE = "PRODUCER_DATA_EXCEEDED_LANDSCAPE_MAX_AGE"

SCOPE_PRODUCER_MODULE = "trading.master_v2.canonical_scope_initialization_v1"
SCOPE_SOURCE_KIND = "canonical_scope_snapshot"
DECISION_PRODUCER_MODULE = "trading.master_v2.canonical_trading_decision_evidence_v1"
DECISION_SOURCE_KIND = "canonical_trading_decision_evidence"
DECISION_EVIDENCE_SCHEMA_VERSION = "canonical_trading_decision_evidence_v1"
DOUBLE_PLAY_PRODUCER_MODULE = "trading.master_v2.double_play_dashboard_display"
DOUBLE_PLAY_SOURCE_KIND = "double_play_dashboard_display"
DOUBLE_PLAY_LAYER_VERSION = "v0"

PHASE_4_1_BOUND_SLOTS: tuple[str, ...] = (
    "market_instrument",
    "universe_ranking",
)
PHASE_4_2_BOUND_SLOTS: tuple[str, ...] = ("dynamic_scope",)
PHASE_4_3A_BOUND_SLOTS: tuple[str, ...] = ("canonical_decision",)
PHASE_4_3B_BOUND_SLOTS: tuple[str, ...] = ("double_play",)

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


def _enum_or_str(value: Any) -> str:
    if hasattr(value, "value"):
        return str(value.value)
    return str(value)


def _resolve_injected_aware_timestamp(
    raw: Any,
) -> tuple[datetime | None, str | None]:
    """Return (aware_utc_dt, error_reason). None+None means absent."""
    if raw is None:
        return None, None
    if isinstance(raw, datetime):
        if raw.tzinfo is None:
            return None, REASON_PRODUCER_TIMESTAMP_INVALID
        return raw.astimezone(timezone.utc), None
    if isinstance(raw, str):
        try:
            parsed = parse_producer_utc_timestamp(raw)
        except ValueError:
            return None, REASON_PRODUCER_TIMESTAMP_INVALID
        return parsed, None
    return None, REASON_PRODUCER_TIMESTAMP_INVALID


def _bind_dynamic_scope_lifecycle(
    *,
    as_of: datetime,
    git_sha: str | None,
    dynamic_scope_fields: Mapping[str, Any] | None,
) -> Any:
    """Project injected CanonicalScopeSnapshotV1-compatible lifecycle fields.

    No durable dashboard scope readmodel. Without injection → MISSING_SOURCE.
    Never runs canonical scope initialization or switch-transition owners.
    """
    if dynamic_scope_fields is None:
        return unavailable_dynamic_scope(
            availability=Availability.MISSING_SOURCE,
            generated_at=as_of,
            reason=REASON_SCOPE_NOT_PERSISTED,
        )

    if "scope_state" in dynamic_scope_fields and dynamic_scope_fields["scope_state"] is not None:
        scope_state = _enum_or_str(dynamic_scope_fields["scope_state"])
    elif (
        "lifecycle_state" in dynamic_scope_fields
        and dynamic_scope_fields["lifecycle_state"] is not None
    ):
        scope_state = _enum_or_str(dynamic_scope_fields["lifecycle_state"])
    else:
        raise KeyError(
            "dynamic_scope_fields missing required keys: ['scope_state'|'lifecycle_state']"
        )

    if (
        "current_scope_ref" in dynamic_scope_fields
        and dynamic_scope_fields["current_scope_ref"] is not None
    ):
        current_scope_ref = str(dynamic_scope_fields["current_scope_ref"])
    elif "scope_id" in dynamic_scope_fields and dynamic_scope_fields["scope_id"] is not None:
        current_scope_ref = str(dynamic_scope_fields["scope_id"])
    else:
        raise KeyError(
            "dynamic_scope_fields missing required keys: ['current_scope_ref'|'scope_id']"
        )

    next_scope_ref: str | None = None
    if "next_scope_ref" in dynamic_scope_fields:
        raw_next = dynamic_scope_fields["next_scope_ref"]
        next_scope_ref = None if raw_next is None else str(raw_next)

    generated_at_raw = dynamic_scope_fields.get("generated_at")
    producer_at, gen_error = _resolve_injected_aware_timestamp(generated_at_raw)
    if gen_error is not None:
        return unavailable_dynamic_scope(
            availability=Availability.INVALID,
            generated_at=as_of,
            reason=gen_error,
        )
    if producer_at is None:
        return unavailable_dynamic_scope(
            availability=Availability.MISSING_SOURCE,
            generated_at=as_of,
            reason=REASON_PRODUCER_TIMESTAMP_MISSING,
        )

    effective_at: datetime | None = None
    if "effective_at" in dynamic_scope_fields:
        effective_at, eff_error = _resolve_injected_aware_timestamp(
            dynamic_scope_fields.get("effective_at")
        )
        if eff_error is not None:
            return unavailable_dynamic_scope(
                availability=Availability.INVALID,
                generated_at=as_of,
                reason=eff_error,
            )

    try:
        availability, is_stale, stale_reason = classify_producer_freshness(
            producer_at=producer_at,
            as_of=as_of,
            max_age_seconds=LANDSCAPE_PHASE42_MAX_AGE_SECONDS,
        )
    except ValueError:
        return unavailable_dynamic_scope(
            availability=Availability.INVALID,
            generated_at=as_of,
            reason=REASON_PRODUCER_TIMESTAMP_INVALID,
        )

    reason_codes = tuple(str(code) for code in dynamic_scope_fields.get("reason_codes", ()) or ())
    evidence_digest = dynamic_scope_fields.get("evidence_digest")
    if evidence_digest is None:
        evidence_digest = dynamic_scope_fields.get("semantic_digest")

    return project_dynamic_scope_snapshot_v1(
        scope_state=scope_state,
        current_scope_ref=current_scope_ref,
        next_scope_ref=next_scope_ref,
        reason_codes=reason_codes,
        generated_at=producer_at,
        effective_at=effective_at,
        source_reference=(
            None
            if dynamic_scope_fields.get("source_reference") is None
            else str(dynamic_scope_fields.get("source_reference"))
        ),
        evidence_digest=None if evidence_digest is None else str(evidence_digest),
        git_sha=git_sha,
        producer_module=SCOPE_PRODUCER_MODULE,
        source_kind=SCOPE_SOURCE_KIND,
        availability=availability,
        max_age_seconds=LANDSCAPE_PHASE42_MAX_AGE_SECONDS,
        is_stale=is_stale,
        stale_reason=stale_reason,
    )


def _bind_canonical_decision(
    *,
    as_of: datetime,
    git_sha: str | None,
    canonical_decision_fields: Mapping[str, Any] | None,
) -> Any:
    """Project injected CanonicalTradingDecisionEvidenceV1-compatible fields.

    No durable dashboard decision readmodel. Without injection → MISSING_SOURCE.
    Never runs decision producers, Double Play composers, or switch owners.
    Blockers remain empty — evidence has no direct blockers field.
    """
    if canonical_decision_fields is None:
        return unavailable_canonical_decision(
            availability=Availability.MISSING_SOURCE,
            generated_at=as_of,
            reason=REASON_DECISION_NOT_PERSISTED,
        )

    required = (
        "instrument_id",
        "decision_outcome",
        "next_direction_state",
        "decision_id",
        "evidence_schema_version",
    )
    missing = [key for key in required if key not in canonical_decision_fields]
    if missing:
        raise KeyError(f"canonical_decision_fields missing required keys: {missing}")

    instrument_id = str(canonical_decision_fields["instrument_id"])
    decision_outcome = str(canonical_decision_fields["decision_outcome"])
    next_direction_state = str(canonical_decision_fields["next_direction_state"])
    decision_id = str(canonical_decision_fields["decision_id"])
    evidence_schema_version = str(canonical_decision_fields["evidence_schema_version"])

    if not instrument_id or not decision_outcome or not next_direction_state:
        return unavailable_canonical_decision(
            availability=Availability.INVALID,
            generated_at=as_of,
            reason="CANONICAL_DECISION_REQUIRED_FIELDS_EMPTY",
        )
    if not evidence_schema_version:
        return unavailable_canonical_decision(
            availability=Availability.INVALID,
            generated_at=as_of,
            reason="CANONICAL_DECISION_SCHEMA_VERSION_MISSING",
        )

    generated_at_raw = canonical_decision_fields.get("generated_at")
    producer_at, gen_error = _resolve_injected_aware_timestamp(generated_at_raw)
    if gen_error is not None:
        return unavailable_canonical_decision(
            availability=Availability.INVALID,
            generated_at=as_of,
            reason=gen_error,
        )
    if producer_at is None:
        return unavailable_canonical_decision(
            availability=Availability.MISSING_SOURCE,
            generated_at=as_of,
            reason=REASON_PRODUCER_TIMESTAMP_MISSING,
        )

    effective_at: datetime | None = None
    if "effective_at" in canonical_decision_fields:
        effective_at, eff_error = _resolve_injected_aware_timestamp(
            canonical_decision_fields.get("effective_at")
        )
        if eff_error is not None:
            return unavailable_canonical_decision(
                availability=Availability.INVALID,
                generated_at=as_of,
                reason=eff_error,
            )

    try:
        availability, is_stale, stale_reason = classify_producer_freshness(
            producer_at=producer_at,
            as_of=as_of,
            max_age_seconds=LANDSCAPE_PHASE43A_MAX_AGE_SECONDS,
        )
    except ValueError:
        return unavailable_canonical_decision(
            availability=Availability.INVALID,
            generated_at=as_of,
            reason=REASON_PRODUCER_TIMESTAMP_INVALID,
        )

    # Exact field copy — preserve injection order; never sort/enrich/reinterpret.
    raw_codes = canonical_decision_fields.get("reason_codes", ()) or ()
    reason_codes = tuple(str(code) for code in raw_codes)

    evidence_digest = canonical_decision_fields.get("semantic_digest")
    if evidence_digest is None:
        evidence_digest = canonical_decision_fields.get("evidence_digest")
    if evidence_digest is not None:
        evidence_digest = str(evidence_digest)
        if not evidence_digest:
            evidence_digest = None

    return project_canonical_decision_snapshot_v1(
        instrument_id=instrument_id,
        decision=decision_outcome,
        direction=next_direction_state,
        reason_codes=reason_codes,
        blockers=(),  # no direct blockers field on CanonicalTradingDecisionEvidenceV1
        decision_id=decision_id,
        evidence_schema_version=evidence_schema_version,
        evidence_digest=evidence_digest,
        generated_at=producer_at,
        effective_at=effective_at,
        source_reference=(
            None
            if canonical_decision_fields.get("source_reference") is None
            else str(canonical_decision_fields.get("source_reference"))
        ),
        git_sha=git_sha,
        producer_module=DECISION_PRODUCER_MODULE,
        source_kind=DECISION_SOURCE_KIND,
        availability=availability,
        max_age_seconds=LANDSCAPE_PHASE43A_MAX_AGE_SECONDS,
        is_stale=is_stale,
        stale_reason=stale_reason,
    )


def _bind_double_play_display(
    *,
    as_of: datetime,
    git_sha: str | None,
    double_play_fields: Mapping[str, Any] | None,
) -> Any:
    """Project injected DoublePlayDashboardDisplaySnapshot-compatible fields.

    No durable dashboard Double Play readmodel. Without injection → MISSING_SOURCE.
    Never calls compose_double_play_decision or build_dashboard_display_snapshot.
    Pending/Armed are not on the display snapshot — remain unbound elsewhere.
    """
    if double_play_fields is None:
        return unavailable_double_play(
            availability=Availability.MISSING_SOURCE,
            generated_at=as_of,
            reason=REASON_DOUBLE_PLAY_NOT_PERSISTED,
        )

    if "overall_status" not in double_play_fields:
        raise KeyError("double_play_fields missing required keys: ['overall_status']")
    if "panel_summaries" not in double_play_fields:
        raise KeyError("double_play_fields missing required keys: ['panel_summaries']")

    overall_status = _enum_or_str(double_play_fields["overall_status"])
    if not overall_status:
        return unavailable_double_play(
            availability=Availability.INVALID,
            generated_at=as_of,
            reason="CANONICAL_DOUBLE_PLAY_OVERALL_STATUS_EMPTY",
        )

    raw_panels = double_play_fields["panel_summaries"]
    if isinstance(raw_panels, Mapping):
        return unavailable_double_play(
            availability=Availability.INVALID,
            generated_at=as_of,
            reason="CANONICAL_DOUBLE_PLAY_PANEL_SUMMARIES_INVALID",
        )
    try:
        panel_summaries = tuple(dict(row) for row in (raw_panels or ()))
    except (TypeError, ValueError):
        return unavailable_double_play(
            availability=Availability.INVALID,
            generated_at=as_of,
            reason="CANONICAL_DOUBLE_PLAY_PANEL_SUMMARIES_INVALID",
        )

    # display_only / live_authorization: fail closed if producer asserts otherwise.
    display_only = double_play_fields.get("display_only", True)
    if display_only is not True:
        return unavailable_double_play(
            availability=Availability.INVALID,
            generated_at=as_of,
            reason="CANONICAL_DOUBLE_PLAY_DISPLAY_ONLY_REQUIRED",
        )
    live_authorization = double_play_fields.get("live_authorization", False)
    if live_authorization is not False:
        return unavailable_double_play(
            availability=Availability.INVALID,
            generated_at=as_of,
            reason="CANONICAL_DOUBLE_PLAY_LIVE_AUTHORIZATION_FORBIDDEN",
        )

    generated_at_raw = double_play_fields.get("generated_at")
    producer_at, gen_error = _resolve_injected_aware_timestamp(generated_at_raw)
    if gen_error is not None:
        return unavailable_double_play(
            availability=Availability.INVALID,
            generated_at=as_of,
            reason=gen_error,
        )
    if producer_at is None:
        return unavailable_double_play(
            availability=Availability.MISSING_SOURCE,
            generated_at=as_of,
            reason=REASON_PRODUCER_TIMESTAMP_MISSING,
        )

    effective_at: datetime | None = None
    if "effective_at" in double_play_fields:
        effective_at, eff_error = _resolve_injected_aware_timestamp(
            double_play_fields.get("effective_at")
        )
        if eff_error is not None:
            return unavailable_double_play(
                availability=Availability.INVALID,
                generated_at=as_of,
                reason=eff_error,
            )

    try:
        availability, is_stale, stale_reason = classify_producer_freshness(
            producer_at=producer_at,
            as_of=as_of,
            max_age_seconds=LANDSCAPE_PHASE43B_MAX_AGE_SECONDS,
        )
    except ValueError:
        return unavailable_double_play(
            availability=Availability.INVALID,
            generated_at=as_of,
            reason=REASON_PRODUCER_TIMESTAMP_INVALID,
        )

    # Exact field copy — never merge Decision reason codes or invent blockers.
    raw_blockers = double_play_fields.get("blockers", ()) or ()
    blockers = tuple(str(code) for code in raw_blockers)

    evidence_digest = double_play_fields.get("evidence_digest")
    if evidence_digest is not None:
        evidence_digest = str(evidence_digest)
        if not evidence_digest:
            evidence_digest = None

    return project_double_play_snapshot_v1(
        overall_status=overall_status,
        panel_summaries=panel_summaries,
        blockers=blockers,
        generated_at=producer_at,
        effective_at=effective_at,
        source_reference=(
            None
            if double_play_fields.get("source_reference") is None
            else str(double_play_fields.get("source_reference"))
        ),
        evidence_digest=evidence_digest,
        git_sha=git_sha,
        producer_module=DOUBLE_PLAY_PRODUCER_MODULE,
        source_kind=DOUBLE_PLAY_SOURCE_KIND,
        availability=availability,
        max_age_seconds=LANDSCAPE_PHASE43B_MAX_AGE_SECONDS,
        is_stale=is_stale,
        stale_reason=stale_reason,
        display_only=True,
        live_authorization=False,
    )


def bind_market_universe_slots(
    *,
    generated_at: datetime,
    archive_root: str | Path | None = None,
    git_sha: str | None = None,
    market_instrument_fields: Mapping[str, Any] | None = None,
    dynamic_scope_fields: Mapping[str, Any] | None = None,
    canonical_decision_fields: Mapping[str, Any] | None = None,
    double_play_fields: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Return Phase 4.1+4.2+4.3A+4.3B slot overrides.

    ``generated_at`` is the dashboard observation/as-of clock only. It must never
    overwrite producer provenance timestamps or fabricate freshness.

    market_instrument_fields accepts already-computed CanonicalMarketContext
    field dicts for tests and future durable loaders. Those fields must carry
    producer ``generated_at`` and/or ``effective_at``.

    dynamic_scope_fields accepts already-computed CanonicalScopeSnapshotV1-
    compatible lifecycle identity fields plus producer wall-clock timestamps.
    Without injection, dynamic_scope is MISSING_SOURCE (no durable readmodel).

    canonical_decision_fields accepts already-computed
    CanonicalTradingDecisionEvidenceV1-compatible fields plus producer
    wall-clock timestamps. Without injection, canonical_decision is
    MISSING_SOURCE (no durable readmodel).

    double_play_fields accepts already-computed
    DoublePlayDashboardDisplaySnapshot-compatible fields plus producer
    wall-clock timestamps. Without injection, double_play is MISSING_SOURCE.
    Never calls compose/build Double Play owners.
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
    scope = _bind_dynamic_scope_lifecycle(
        as_of=as_of,
        git_sha=git_sha,
        dynamic_scope_fields=dynamic_scope_fields,
    )
    decision = _bind_canonical_decision(
        as_of=as_of,
        git_sha=git_sha,
        canonical_decision_fields=canonical_decision_fields,
    )
    double_play = _bind_double_play_display(
        as_of=as_of,
        git_sha=git_sha,
        double_play_fields=double_play_fields,
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
        "dynamic_scope": scope,
        "canonical_decision": decision,
        "double_play": double_play,
    }
