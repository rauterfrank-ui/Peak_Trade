"""Phase 4.1–4.5 + 4.6B read-only producer binding for Market Landscape V2.

Binds market_instrument, universe_ranking, dynamic_scope lifecycle identity,
canonical_decision evidence, double_play display projection, safety
authority KillSwitch/boundary field projection, risk/sizing/capital field
projection, execution/reconciliation field projection, and economic summary
EconomicViabilityEvidenceV1 field projection.
Regime / bull-bear / switch remain unbound.
Lives outside market_dashboard_landscape_v2 so that package stays free of
trading/webui producer imports (architecture guard).

Fail-closed:
- Wired slots without durable producer output → MISSING_SOURCE / INVALID
- Producer timestamps preserved; page-assembly time is observation-only
- Aged producer snapshots → STALE (never silently refreshed)
- Never fabricate OHLCV, ranking, eligibility, selected instrument, scope,
  decisions, Double Play composition, Safety/KillSwitch state, risk/sizing/
  capital quantities, execution/reconciliation status, or economic metrics
- Never call scope initializers, trailing-scope runtime owners, switch owners,
  decision producers, compose_double_play_decision, or build_dashboard_display_snapshot
- Never instantiate KillSwitch, call trigger/recover, evaluate_offline_killswitch_boundary_v0,
  or any bind_* Safety evaluator; no live state-file autoload
- Never call capital/risk/sizing evaluators, order-intent builders,
  or offline reconciliation evaluators; no order/execution mutation imports
- Never discover/select EconomicViabilityEvidenceV1 instances (no filesystem,
  registry, latest-file, or environment selector)
- Never bind promotion_economic_gate_v1 or infer lifecycle labels
"""

from __future__ import annotations

import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from .market_dashboard_landscape_v2.availability import Availability
from .market_dashboard_landscape_v2.projections import (
    project_canonical_decision_snapshot_v1,
    project_double_play_snapshot_v1,
    project_dynamic_scope_snapshot_v1,
    project_regime_bull_bear_switch_snapshot_v1,
    project_economic_summary_snapshot_v1,
    project_execution_reconciliation_snapshot_v1,
    project_market_instrument_snapshot_v1,
    project_risk_sizing_capital_snapshot_v1,
    project_safety_authority_snapshot_v1,
    project_universe_ranking_snapshot_v1,
)
from .market_dashboard_landscape_v2.unavailable import (
    unavailable_canonical_decision,
    unavailable_double_play,
    unavailable_dynamic_scope,
    unavailable_regime_bull_bear_switch,
    unavailable_economic_summary,
    unavailable_execution_reconciliation,
    unavailable_market_instrument,
    unavailable_risk_sizing_capital,
    unavailable_safety_authority,
    unavailable_universe_ranking,
)
from .workflow_dashboard_archive_root_v1 import (
    ENV_ARCHIVE_ROOT,
    WorkflowDashboardArchiveRootError,
    resolve_workflow_dashboard_archive_root,
)
from .workflow_dashboard_readmodel_v1.universe_selection_contract_v1 import (
    FORBIDDEN_SELECTED_SYMBOLS,
)
from .workflow_dashboard_readmodel_v1.universe_selection_reader_v1 import (
    try_load_universe_selection_for_dashboard,
)

# F2 consuming-surface max_allowed_staleness_seconds for Landscape Phase 4.1+.
# Declared here as the dashboard consumer policy; never invent freshness via now().
LANDSCAPE_PHASE41_MAX_AGE_SECONDS = 86_400
LANDSCAPE_PHASE42_MAX_AGE_SECONDS = LANDSCAPE_PHASE41_MAX_AGE_SECONDS
LANDSCAPE_PHASE42B_MAX_AGE_SECONDS = LANDSCAPE_PHASE41_MAX_AGE_SECONDS
LANDSCAPE_PHASE43A_MAX_AGE_SECONDS = LANDSCAPE_PHASE41_MAX_AGE_SECONDS
LANDSCAPE_PHASE43B_MAX_AGE_SECONDS = LANDSCAPE_PHASE41_MAX_AGE_SECONDS
LANDSCAPE_PHASE44A_MAX_AGE_SECONDS = LANDSCAPE_PHASE41_MAX_AGE_SECONDS
LANDSCAPE_PHASE44B_MAX_AGE_SECONDS = LANDSCAPE_PHASE41_MAX_AGE_SECONDS
LANDSCAPE_PHASE45_MAX_AGE_SECONDS = LANDSCAPE_PHASE41_MAX_AGE_SECONDS
LANDSCAPE_PHASE46B_MAX_AGE_SECONDS = LANDSCAPE_PHASE41_MAX_AGE_SECONDS

REASON_MARKET_CONTEXT_NOT_PERSISTED = "CANONICAL_MARKET_CONTEXT_NOT_PERSISTED_FOR_DASHBOARD"
REASON_SCOPE_NOT_PERSISTED = "CANONICAL_SCOPE_SNAPSHOT_NOT_PERSISTED_FOR_DASHBOARD"
REASON_REGIME_BULL_BEAR_SWITCH_NOT_PERSISTED = (
    "CANONICAL_REGIME_BULL_BEAR_SWITCH_NOT_PERSISTED_FOR_DASHBOARD"
)
REASON_REGIME_SIDE_SWITCH_CONTRADICTION = "REGIME_BULL_BEAR_SWITCH_FIELD_CONTRADICTION"
REASON_DECISION_NOT_PERSISTED = "CANONICAL_DECISION_EVIDENCE_NOT_PERSISTED_FOR_DASHBOARD"
REASON_DOUBLE_PLAY_NOT_PERSISTED = "CANONICAL_DOUBLE_PLAY_DISPLAY_NOT_PERSISTED_FOR_DASHBOARD"
REASON_SAFETY_NOT_PERSISTED = "CANONICAL_SAFETY_AUTHORITY_NOT_PERSISTED_FOR_DASHBOARD"
REASON_RISK_SIZING_NOT_PERSISTED = "CANONICAL_RISK_SIZING_CAPITAL_NOT_PERSISTED_FOR_DASHBOARD"
REASON_EXECUTION_NOT_PERSISTED = "CANONICAL_EXECUTION_RECONCILIATION_NOT_PERSISTED_FOR_DASHBOARD"
REASON_ECONOMIC_NOT_PERSISTED = "CANONICAL_ECONOMIC_EVIDENCE_NOT_PERSISTED_FOR_DASHBOARD"
REASON_SCHEMA_MISMATCH = "SCHEMA_MISMATCH"
REASON_INVALID_PROVENANCE = "INVALID_PROVENANCE"
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
REGIME_BULL_BEAR_SWITCH_PRODUCER_MODULE = "trading.master_v2.double_play_state"
REGIME_BULL_BEAR_SWITCH_SOURCE_KIND = "regime_bull_bear_switch_projection"
REGIME_OWNER_MODULE = "trading.master_v2.suitability_binding_v1"
BULL_BEAR_OWNER_MODULE = "trading.master_v2.double_play_state"
SWITCH_OWNER_MODULE = "trading.master_v2.double_play_state"
SWITCH_EVIDENCE_MODULE = "trading.master_v2.integrated_offline_trading_logic_replay_v1"
KNOWN_SIDE_STATES = frozenset(
    {
        "neutral_observe",
        "long_armed",
        "long_active",
        "long_blocked",
        "short_armed",
        "short_active",
        "short_blocked",
        "switch_long_to_short_pending",
        "switch_short_to_long_pending",
        "chop_guard_block",
        "kill_all",
    }
)
KNOWN_REGIME_STATUSES = frozenset({"known", "unknown"})
DECISION_PRODUCER_MODULE = "trading.master_v2.canonical_trading_decision_evidence_v1"
DECISION_SOURCE_KIND = "canonical_trading_decision_evidence"
DECISION_EVIDENCE_SCHEMA_VERSION = "canonical_trading_decision_evidence_v1"
DOUBLE_PLAY_PRODUCER_MODULE = "trading.master_v2.double_play_dashboard_display"
DOUBLE_PLAY_SOURCE_KIND = "double_play_dashboard_display"
DOUBLE_PLAY_LAYER_VERSION = "v0"
SAFETY_AUTHORITY_OWNER_MODULE = "src.risk_layer.kill_switch"
SAFETY_EVIDENCE_PRODUCER_MODULE = (
    "trading.master_v2.killswitch_boundary_offline_replay_binding_adapter_v0"
)
SAFETY_SOURCE_KIND = "killswitch_boundary_offline_replay_boundary"
ECONOMIC_PRODUCER_MODULE = "backtest.economic_viability_evidence_v1"
ECONOMIC_SOURCE_KIND = "economic_viability_evidence_v1"
ECONOMIC_CONTRACT_SCHEMA_VERSION = "v1"
RISK_SIZING_PRODUCER_MODULE = (
    "trading.master_v2.capital_risk_sizing_offline_replay_binding_adapter_v0"
)
RISK_SIZING_SOURCE_KIND = "capital_risk_sizing_offline_replay_binding"
RISK_SIZING_AUTHORITY_OWNER = "src.governance.capital_risk_sizing_v1"
EXECUTION_PRODUCER_MODULE = (
    "trading.master_v2.canonical_order_intent_offline_replay_binding_adapter_v0"
)
EXECUTION_SOURCE_KIND = "canonical_order_intent_offline_replay_binding"
EXECUTION_AUTHORITY_OWNER = "src.governance.canonical_order_intent_v1"
LANDSCAPE_PROJECTION_SCHEMA_VERSION = "v1"

PHASE_4_1_BOUND_SLOTS: tuple[str, ...] = (
    "market_instrument",
    "universe_ranking",
)
PHASE_4_2_BOUND_SLOTS: tuple[str, ...] = ("dynamic_scope",)
PHASE_4_2B_BOUND_SLOTS: tuple[str, ...] = ("regime_bull_bear_switch",)
PHASE_4_3A_BOUND_SLOTS: tuple[str, ...] = ("canonical_decision",)
PHASE_4_3B_BOUND_SLOTS: tuple[str, ...] = ("double_play",)
PHASE_4_4A_BOUND_SLOTS: tuple[str, ...] = ("safety_authority",)
PHASE_4_4B_BOUND_SLOTS: tuple[str, ...] = ("risk_sizing_capital",)
PHASE_4_5_BOUND_SLOTS: tuple[str, ...] = ("execution_reconciliation",)
PHASE_4_6B_BOUND_SLOTS: tuple[str, ...] = ("economic_summary",)

_ISO8601_UTC_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?(Z|\+00:00)$")


def resolve_landscape_archive_root(
    archive_root: str | Path | None = None,
) -> Path | None:
    """Resolve durable archive root for universe_selection readmodel load.

    Delegates to the sole Workflow Dashboard archive-root contract owner.
    Does not create directories. A missing default directory remains None so
    consumers keep fail-closed MISSING_SOURCE / ARCHIVE_ROOT_UNSET semantics.
    """
    try:
        return resolve_workflow_dashboard_archive_root(
            explicit=archive_root,
            require_existing_directory=True,
        )
    except WorkflowDashboardArchiveRootError:
        # Explicit empty/invalid injection stays fail-closed as unset for binder.
        return None


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
    # Canonical OKX intake may persist market_snapshot.captured_at as null while
    # still providing universe generated_at + exchange. Prefer captured_at when
    # present; otherwise consume the readmodel generated_at (never invent now()).
    producer_ts_raw = slice_v1.market_snapshot.captured_at
    if producer_ts_raw is None or (
        isinstance(producer_ts_raw, str) and not producer_ts_raw.strip()
    ):
        producer_ts_raw = slice_v1.generated_at
    try:
        producer_at = parse_producer_utc_timestamp(producer_ts_raw)
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

    market_type = None
    for row in (*universe_snap.universe, *universe_snap.ranking):
        if row.get("symbol") == selected and row.get("market_type"):
            market_type = str(row["market_type"])
            break

    return project_market_instrument_snapshot_v1(
        instrument_id=str(selected),
        venue=venue,
        market_type=market_type,
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


def load_bound_okx_ohlcv_readmodel_v1(
    *,
    archive_root: str | Path | None = None,
    selected_instrument_id: str | None,
    selected_venue: str | None,
) -> dict[str, Any] | None:
    """Read-only load of materialized OKX OHLCV; no network; identity fail-closed."""
    if not selected_instrument_id:
        return None
    root = resolve_landscape_archive_root(archive_root)
    if root is None:
        return None
    from src.ops.okx_selected_instrument_ohlcv_readmodel_v1 import load_ohlcv_readmodel_v1

    try:
        data = load_ohlcv_readmodel_v1(root)
    except Exception:  # noqa: BLE001
        return None
    if not data:
        return None
    if str(data.get("instrument_id") or "") != str(selected_instrument_id):
        return None
    if selected_venue and str(data.get("venue") or "").lower() not in {
        str(selected_venue).lower(),
        "okx",
        "okx_europe_eea",
    }:
        return None
    if str(data.get("venue") or "").lower() not in {"okx", "okx_europe_eea"}:
        return None
    return dict(data)


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


def _bind_regime_bull_bear_switch(
    *,
    as_of: datetime,
    git_sha: str | None,
    regime_bull_bear_switch_fields: Mapping[str, Any] | None,
) -> Any:
    """Project injected Regime / SideState / Switch evidence fields.

    No durable dashboard readmodel. Without injection → MISSING_SOURCE.
    Never calls transition_state, suitability evaluators, or invents SideState.
    """
    if regime_bull_bear_switch_fields is None:
        return unavailable_regime_bull_bear_switch(
            availability=Availability.MISSING_SOURCE,
            generated_at=as_of,
            reason=REASON_REGIME_BULL_BEAR_SWITCH_NOT_PERSISTED,
        )

    schema_version = regime_bull_bear_switch_fields.get("schema_version")
    if schema_version is not None and str(schema_version) != LANDSCAPE_PROJECTION_SCHEMA_VERSION:
        return unavailable_regime_bull_bear_switch(
            availability=Availability.INVALID,
            generated_at=as_of,
            reason=REASON_SCHEMA_MISMATCH,
        )

    required = (
        "regime_id",
        "regime_status",
        "side_state",
        "previous_side_state",
        "next_side_state",
        "scope_event_type",
        "transition_allowed",
        "transition_reason_code",
    )
    missing = [key for key in required if key not in regime_bull_bear_switch_fields]
    if missing:
        raise KeyError(f"regime_bull_bear_switch_fields missing required keys: {missing}")

    regime_id = _enum_or_str(regime_bull_bear_switch_fields["regime_id"]).strip()
    regime_status = _enum_or_str(regime_bull_bear_switch_fields["regime_status"]).strip()
    side_state = _enum_or_str(regime_bull_bear_switch_fields["side_state"]).strip()
    previous_side_state = _enum_or_str(
        regime_bull_bear_switch_fields["previous_side_state"]
    ).strip()
    next_side_state = _enum_or_str(regime_bull_bear_switch_fields["next_side_state"]).strip()
    scope_event_type = _enum_or_str(regime_bull_bear_switch_fields["scope_event_type"]).strip()
    transition_reason_code = _enum_or_str(
        regime_bull_bear_switch_fields["transition_reason_code"]
    ).strip()
    transition_allowed_raw = regime_bull_bear_switch_fields["transition_allowed"]

    if (
        not regime_id
        or not regime_status
        or not side_state
        or not previous_side_state
        or not next_side_state
        or not scope_event_type
        or not transition_reason_code
    ):
        return unavailable_regime_bull_bear_switch(
            availability=Availability.INVALID,
            generated_at=as_of,
            reason=REASON_INVALID_PROVENANCE,
        )
    if not isinstance(transition_allowed_raw, bool):
        return unavailable_regime_bull_bear_switch(
            availability=Availability.INVALID,
            generated_at=as_of,
            reason=REASON_INVALID_PROVENANCE,
        )
    if regime_status not in KNOWN_REGIME_STATUSES:
        return unavailable_regime_bull_bear_switch(
            availability=Availability.INVALID,
            generated_at=as_of,
            reason=REASON_SCHEMA_MISMATCH,
        )
    if side_state not in KNOWN_SIDE_STATES:
        return unavailable_regime_bull_bear_switch(
            availability=Availability.INVALID,
            generated_at=as_of,
            reason=REASON_SCHEMA_MISMATCH,
        )
    if previous_side_state not in KNOWN_SIDE_STATES or next_side_state not in KNOWN_SIDE_STATES:
        return unavailable_regime_bull_bear_switch(
            availability=Availability.INVALID,
            generated_at=as_of,
            reason=REASON_SCHEMA_MISMATCH,
        )
    # Fail-closed: current bull/bear side must match switch next_side_state.
    if side_state != next_side_state:
        return unavailable_regime_bull_bear_switch(
            availability=Availability.INVALID,
            generated_at=as_of,
            reason=REASON_REGIME_SIDE_SWITCH_CONTRADICTION,
        )

    generated_at_raw = regime_bull_bear_switch_fields.get("generated_at")
    producer_at, gen_error = _resolve_injected_aware_timestamp(generated_at_raw)
    if gen_error is not None:
        return unavailable_regime_bull_bear_switch(
            availability=Availability.INVALID,
            generated_at=as_of,
            reason=gen_error,
        )
    if producer_at is None:
        return unavailable_regime_bull_bear_switch(
            availability=Availability.MISSING_SOURCE,
            generated_at=as_of,
            reason=REASON_PRODUCER_TIMESTAMP_MISSING,
        )

    effective_at: datetime | None = None
    if "effective_at" in regime_bull_bear_switch_fields:
        effective_at, eff_error = _resolve_injected_aware_timestamp(
            regime_bull_bear_switch_fields.get("effective_at")
        )
        if eff_error is not None:
            return unavailable_regime_bull_bear_switch(
                availability=Availability.INVALID,
                generated_at=as_of,
                reason=eff_error,
            )

    try:
        availability, is_stale, stale_reason = classify_producer_freshness(
            producer_at=producer_at,
            as_of=as_of,
            max_age_seconds=LANDSCAPE_PHASE42B_MAX_AGE_SECONDS,
        )
    except ValueError:
        return unavailable_regime_bull_bear_switch(
            availability=Availability.INVALID,
            generated_at=as_of,
            reason=REASON_PRODUCER_TIMESTAMP_INVALID,
        )

    raw_codes = regime_bull_bear_switch_fields.get("reason_codes", ()) or ()
    reason_codes = tuple(str(code) for code in raw_codes)

    evidence_digest = regime_bull_bear_switch_fields.get("evidence_digest")
    if evidence_digest is None:
        evidence_digest = regime_bull_bear_switch_fields.get("semantic_digest")
    if evidence_digest is not None:
        evidence_digest = str(evidence_digest)
        if not evidence_digest:
            evidence_digest = None

    producer_module = str(
        regime_bull_bear_switch_fields.get(
            "producer_module", REGIME_BULL_BEAR_SWITCH_PRODUCER_MODULE
        )
    )
    source_kind = str(
        regime_bull_bear_switch_fields.get("source_kind", REGIME_BULL_BEAR_SWITCH_SOURCE_KIND)
    )

    return project_regime_bull_bear_switch_snapshot_v1(
        regime_id=regime_id,
        regime_status=regime_status,
        side_state=side_state,
        previous_side_state=previous_side_state,
        next_side_state=next_side_state,
        scope_event_type=scope_event_type,
        transition_allowed=bool(transition_allowed_raw),
        transition_reason_code=transition_reason_code,
        reason_codes=reason_codes,
        generated_at=producer_at,
        effective_at=effective_at,
        source_reference=(
            None
            if regime_bull_bear_switch_fields.get("source_reference") is None
            else str(regime_bull_bear_switch_fields.get("source_reference"))
        ),
        evidence_digest=evidence_digest,
        git_sha=git_sha,
        producer_module=producer_module,
        source_kind=source_kind,
        availability=availability,
        max_age_seconds=LANDSCAPE_PHASE42B_MAX_AGE_SECONDS,
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


def _bind_safety_authority(
    *,
    as_of: datetime,
    git_sha: str | None,
    safety_authority_fields: Mapping[str, Any] | None,
) -> Any:
    """Project injected KillSwitch / boundary-compatible Safety fields.

    No durable dashboard Safety readmodel. Without injection → MISSING_SOURCE.
    Never instantiates KillSwitch, never calls trigger/recover, never calls
    evaluate_offline_killswitch_boundary_v0 or bind_* Safety evaluators, and
    never auto-loads a live state file.
    """
    if safety_authority_fields is None:
        return unavailable_safety_authority(
            availability=Availability.MISSING_SOURCE,
            generated_at=as_of,
            reason=REASON_SAFETY_NOT_PERSISTED,
        )

    if "kill_switch_state" not in safety_authority_fields:
        raise KeyError("safety_authority_fields missing required keys: ['kill_switch_state']")
    if "veto_active" not in safety_authority_fields:
        raise KeyError("safety_authority_fields missing required keys: ['veto_active']")

    kill_switch_state = _enum_or_str(safety_authority_fields["kill_switch_state"])
    if not kill_switch_state:
        return unavailable_safety_authority(
            availability=Availability.INVALID,
            generated_at=as_of,
            reason="CANONICAL_SAFETY_KILL_SWITCH_STATE_EMPTY",
        )

    veto_raw = safety_authority_fields["veto_active"]
    if not isinstance(veto_raw, bool):
        return unavailable_safety_authority(
            availability=Availability.INVALID,
            generated_at=as_of,
            reason="CANONICAL_SAFETY_VETO_ACTIVE_INVALID",
        )
    veto_active = veto_raw

    generated_at_raw = safety_authority_fields.get("generated_at")
    producer_at, gen_error = _resolve_injected_aware_timestamp(generated_at_raw)
    if gen_error is not None:
        return unavailable_safety_authority(
            availability=Availability.INVALID,
            generated_at=as_of,
            reason=gen_error,
        )
    if producer_at is None:
        return unavailable_safety_authority(
            availability=Availability.MISSING_SOURCE,
            generated_at=as_of,
            reason=REASON_PRODUCER_TIMESTAMP_MISSING,
        )

    effective_at: datetime | None = None
    if "effective_at" in safety_authority_fields:
        effective_at, eff_error = _resolve_injected_aware_timestamp(
            safety_authority_fields.get("effective_at")
        )
        if eff_error is not None:
            return unavailable_safety_authority(
                availability=Availability.INVALID,
                generated_at=as_of,
                reason=eff_error,
            )
    elif "saved_at" in safety_authority_fields:
        # Persistence field alias — exact copy of saved_at as effective_at.
        effective_at, saved_error = _resolve_injected_aware_timestamp(
            safety_authority_fields.get("saved_at")
        )
        if saved_error is not None:
            return unavailable_safety_authority(
                availability=Availability.INVALID,
                generated_at=as_of,
                reason=saved_error,
            )

    try:
        availability, is_stale, stale_reason = classify_producer_freshness(
            producer_at=producer_at,
            as_of=as_of,
            max_age_seconds=LANDSCAPE_PHASE44A_MAX_AGE_SECONDS,
        )
    except ValueError:
        return unavailable_safety_authority(
            availability=Availability.INVALID,
            generated_at=as_of,
            reason=REASON_PRODUCER_TIMESTAMP_INVALID,
        )

    # Exact field copy — never merge Risk/Capital/Sizing reasons or invent veto.
    raw_reasons = safety_authority_fields.get("reason_codes", ()) or ()
    reason_codes = tuple(str(code) for code in raw_reasons)

    evidence_digest = safety_authority_fields.get("evidence_digest")
    if evidence_digest is None:
        evidence_digest = safety_authority_fields.get("semantic_digest")
    if evidence_digest is not None:
        evidence_digest = str(evidence_digest)
        if not evidence_digest:
            evidence_digest = None

    source_reference = safety_authority_fields.get("source_reference")
    if source_reference is None:
        source_reference = safety_authority_fields.get("killswitch_owner_ref")
    if source_reference is not None:
        source_reference = str(source_reference)

    producer_module = str(
        safety_authority_fields.get("producer_module", SAFETY_EVIDENCE_PRODUCER_MODULE)
    )
    source_kind = str(safety_authority_fields.get("source_kind", SAFETY_SOURCE_KIND))

    return project_safety_authority_snapshot_v1(
        kill_switch_state=kill_switch_state,
        veto_active=veto_active,
        reason_codes=reason_codes,
        generated_at=producer_at,
        effective_at=effective_at,
        source_reference=source_reference,
        evidence_digest=evidence_digest,
        git_sha=git_sha,
        producer_module=producer_module,
        source_kind=source_kind,
        availability=availability,
        max_age_seconds=LANDSCAPE_PHASE44A_MAX_AGE_SECONDS,
        is_stale=is_stale,
        stale_reason=stale_reason,
    )


def _metric_mapping(raw: Any) -> dict[str, Any]:
    """Copy MetricFieldV1.to_dict() shape or an already-projected mapping."""
    if hasattr(raw, "to_dict") and callable(raw.to_dict):
        return dict(raw.to_dict())
    if isinstance(raw, Mapping):
        return dict(raw)
    raise TypeError("metric fields must be MetricFieldV1 or Mapping")


def economic_viability_evidence_fields_from_v1(
    evidence: Any,
    *,
    generated_at: datetime,
    source_reference: str | None = None,
) -> dict[str, Any]:
    """Extract direct EconomicViabilityEvidenceV1 fields for injection.

    Does not recompute metrics, apply thresholds, or invent lifecycle/promotion.
    ``generated_at`` is supplied by the upstream injector (not fabricated here).
    """
    from src.backtest.economic_viability_evidence_v1 import EconomicViabilityEvidenceV1

    if not isinstance(evidence, EconomicViabilityEvidenceV1):
        raise TypeError("evidence must be EconomicViabilityEvidenceV1")
    status = evidence.status
    status_value = status.value if hasattr(status, "value") else str(status)
    return {
        "status": status_value,
        "economic_validity_proven": evidence.economic_validity_proven,
        "profitability_claim_allowed": evidence.profitability_claim_allowed,
        "policy_threshold_status": evidence.policy_threshold_status,
        "policy_version": evidence.policy_version,
        "authority_effect": evidence.authority_effect,
        "runtime_effect": evidence.runtime_effect,
        "order_effect": evidence.order_effect,
        "reason_codes": tuple(evidence.reason_codes),
        "profit_factor": _metric_mapping(evidence.profit_factor),
        "net_return": _metric_mapping(evidence.net_return),
        "max_drawdown": _metric_mapping(evidence.max_drawdown),
        "sharpe": _metric_mapping(evidence.sharpe),
        "trade_count": _metric_mapping(evidence.trade_count),
        "funding_drag": _metric_mapping(evidence.funding_drag),
        "contract_version": evidence.contract_version,
        "owner": evidence.owner,
        "strategy_id": evidence.strategy_id,
        "strategy_version": evidence.strategy_version,
        "config_digest": evidence.config_digest,
        "implementation_digest": evidence.implementation_digest,
        "data_digest": evidence.data_digest,
        "manifest_digest": evidence.manifest_digest,
        "wiring_chain_digest": evidence.wiring_chain_digest,
        "policy_digest": evidence.policy_digest,
        "generated_at": generated_at,
        "source_reference": source_reference,
        "evidence_digest": evidence.manifest_digest,
    }


def project_economic_viability_evidence_v1(
    evidence: Any,
    *,
    generated_at: datetime,
    as_of: datetime | None = None,
    git_sha: str | None = None,
    source_reference: str | None = None,
) -> Any:
    """Pure field-for-field projection of one injected EconomicViabilityEvidenceV1.

    No I/O, no selector, no promotion/lifecycle inference, no metric recomputation.
    """
    fields = economic_viability_evidence_fields_from_v1(
        evidence,
        generated_at=generated_at,
        source_reference=source_reference,
    )
    stamp = generated_at if as_of is None else as_of
    if stamp.tzinfo is None:
        raise ValueError("as_of/generated_at must be timezone-aware")
    return _bind_economic_summary(
        as_of=stamp.astimezone(timezone.utc),
        git_sha=git_sha,
        economic_viability_evidence_fields=fields,
    )


def _bind_economic_summary(
    *,
    as_of: datetime,
    git_sha: str | None,
    economic_viability_evidence_fields: Mapping[str, Any] | None,
) -> Any:
    """Project injected EconomicViabilityEvidenceV1-compatible fields.

    No durable dashboard economic readmodel. Without injection → MISSING_SOURCE.
    Never discovers evidence files, never binds promotion_economic_gate_v1,
    and never infers DEVELOPMENT/HOLDOUT/SEALED from paths.
    """
    if economic_viability_evidence_fields is None:
        return unavailable_economic_summary(
            availability=Availability.MISSING_SOURCE,
            generated_at=as_of,
            reason=REASON_ECONOMIC_NOT_PERSISTED,
        )

    required = (
        "status",
        "economic_validity_proven",
        "profitability_claim_allowed",
        "policy_threshold_status",
        "policy_version",
        "authority_effect",
        "runtime_effect",
        "order_effect",
        "profit_factor",
        "net_return",
        "max_drawdown",
        "sharpe",
        "trade_count",
        "funding_drag",
        "contract_version",
        "owner",
        "strategy_id",
        "strategy_version",
        "config_digest",
        "implementation_digest",
        "data_digest",
        "manifest_digest",
        "wiring_chain_digest",
        "policy_digest",
    )
    missing = [key for key in required if key not in economic_viability_evidence_fields]
    if missing:
        raise KeyError(f"economic_viability_evidence_fields missing required keys: {missing}")

    status_raw = economic_viability_evidence_fields["status"]
    economic_viability_status = (
        status_raw.value if hasattr(status_raw, "value") else str(status_raw)
    )
    if not economic_viability_status:
        return unavailable_economic_summary(
            availability=Availability.INVALID,
            generated_at=as_of,
            reason="CANONICAL_ECONOMIC_STATUS_EMPTY",
        )

    economic_validity_proven = economic_viability_evidence_fields["economic_validity_proven"]
    profitability_claim_allowed = economic_viability_evidence_fields["profitability_claim_allowed"]
    runtime_effect = economic_viability_evidence_fields["runtime_effect"]
    order_effect = economic_viability_evidence_fields["order_effect"]
    if not isinstance(economic_validity_proven, bool):
        return unavailable_economic_summary(
            availability=Availability.INVALID,
            generated_at=as_of,
            reason="CANONICAL_ECONOMIC_VALIDITY_PROVEN_INVALID",
        )
    if not isinstance(profitability_claim_allowed, bool):
        return unavailable_economic_summary(
            availability=Availability.INVALID,
            generated_at=as_of,
            reason="CANONICAL_ECONOMIC_PROFITABILITY_CLAIM_INVALID",
        )
    if not isinstance(runtime_effect, bool) or not isinstance(order_effect, bool):
        return unavailable_economic_summary(
            availability=Availability.INVALID,
            generated_at=as_of,
            reason="CANONICAL_ECONOMIC_EFFECT_FLAGS_INVALID",
        )

    generated_at_raw = economic_viability_evidence_fields.get("generated_at")
    producer_at, gen_error = _resolve_injected_aware_timestamp(generated_at_raw)
    if gen_error is not None:
        return unavailable_economic_summary(
            availability=Availability.INVALID,
            generated_at=as_of,
            reason=gen_error,
        )
    if producer_at is None:
        return unavailable_economic_summary(
            availability=Availability.MISSING_SOURCE,
            generated_at=as_of,
            reason=REASON_PRODUCER_TIMESTAMP_MISSING,
        )

    effective_at: datetime | None = None
    if "effective_at" in economic_viability_evidence_fields:
        effective_at, eff_error = _resolve_injected_aware_timestamp(
            economic_viability_evidence_fields.get("effective_at")
        )
        if eff_error is not None:
            return unavailable_economic_summary(
                availability=Availability.INVALID,
                generated_at=as_of,
                reason=eff_error,
            )

    try:
        availability, is_stale, stale_reason = classify_producer_freshness(
            producer_at=producer_at,
            as_of=as_of,
            max_age_seconds=LANDSCAPE_PHASE46B_MAX_AGE_SECONDS,
        )
    except ValueError:
        return unavailable_economic_summary(
            availability=Availability.INVALID,
            generated_at=as_of,
            reason=REASON_PRODUCER_TIMESTAMP_INVALID,
        )

    raw_reasons = economic_viability_evidence_fields.get("reason_codes", ()) or ()
    reason_codes = tuple(str(code) for code in raw_reasons)

    evidence_digest = economic_viability_evidence_fields.get("evidence_digest")
    if evidence_digest is None:
        evidence_digest = economic_viability_evidence_fields.get("manifest_digest")
    if evidence_digest is not None:
        evidence_digest = str(evidence_digest)
        if not evidence_digest:
            evidence_digest = None

    source_reference = economic_viability_evidence_fields.get("source_reference")
    if source_reference is not None:
        source_reference = str(source_reference)

    evidence_ref = economic_viability_evidence_fields.get("evidence_ref")
    if evidence_ref is not None:
        evidence_ref = str(evidence_ref)

    producer_module = str(
        economic_viability_evidence_fields.get("producer_module", ECONOMIC_PRODUCER_MODULE)
    )
    source_kind = str(economic_viability_evidence_fields.get("source_kind", ECONOMIC_SOURCE_KIND))

    return project_economic_summary_snapshot_v1(
        economic_viability_status=economic_viability_status,
        economic_validity_proven=economic_validity_proven,
        profitability_claim_allowed=profitability_claim_allowed,
        policy_threshold_status=str(economic_viability_evidence_fields["policy_threshold_status"]),
        policy_version=str(economic_viability_evidence_fields["policy_version"]),
        authority_effect=str(economic_viability_evidence_fields["authority_effect"]),
        runtime_effect=runtime_effect,
        order_effect=order_effect,
        reason_codes=reason_codes,
        profit_factor=_metric_mapping(economic_viability_evidence_fields["profit_factor"]),
        net_return=_metric_mapping(economic_viability_evidence_fields["net_return"]),
        max_drawdown=_metric_mapping(economic_viability_evidence_fields["max_drawdown"]),
        sharpe=_metric_mapping(economic_viability_evidence_fields["sharpe"]),
        trade_count=_metric_mapping(economic_viability_evidence_fields["trade_count"]),
        funding_drag=_metric_mapping(economic_viability_evidence_fields["funding_drag"]),
        contract_version=str(economic_viability_evidence_fields["contract_version"]),
        owner=str(economic_viability_evidence_fields["owner"]),
        strategy_id=str(economic_viability_evidence_fields["strategy_id"]),
        strategy_version=str(economic_viability_evidence_fields["strategy_version"]),
        config_digest=str(economic_viability_evidence_fields["config_digest"]),
        implementation_digest=str(economic_viability_evidence_fields["implementation_digest"]),
        data_digest=str(economic_viability_evidence_fields["data_digest"]),
        manifest_digest=str(economic_viability_evidence_fields["manifest_digest"]),
        wiring_chain_digest=str(economic_viability_evidence_fields["wiring_chain_digest"]),
        policy_digest=str(economic_viability_evidence_fields["policy_digest"]),
        generated_at=producer_at,
        effective_at=effective_at,
        source_reference=source_reference,
        evidence_ref=evidence_ref,
        evidence_digest=evidence_digest,
        git_sha=git_sha,
        producer_module=producer_module,
        source_kind=source_kind,
        availability=availability,
        max_age_seconds=LANDSCAPE_PHASE46B_MAX_AGE_SECONDS,
        is_stale=is_stale,
        stale_reason=stale_reason,
    )


def _optional_injected_str(raw: Any) -> str | None:
    if raw is None:
        return None
    text = _enum_or_str(raw).strip()
    return text or None


def _bind_risk_sizing_capital(
    *,
    as_of: datetime,
    git_sha: str | None,
    risk_sizing_capital_fields: Mapping[str, Any] | None,
) -> Any:
    """Project injected Risk/Sizing/Capital fields.

    No durable dashboard Risk readmodel. Without injection → MISSING_SOURCE.
    Never calls capital/risk/sizing evaluators or invents quantity/limits.
    """
    if risk_sizing_capital_fields is None:
        return unavailable_risk_sizing_capital(
            availability=Availability.MISSING_SOURCE,
            generated_at=as_of,
            reason=REASON_RISK_SIZING_NOT_PERSISTED,
        )

    schema_version = risk_sizing_capital_fields.get("schema_version")
    if schema_version is not None and str(schema_version) != LANDSCAPE_PROJECTION_SCHEMA_VERSION:
        return unavailable_risk_sizing_capital(
            availability=Availability.INVALID,
            generated_at=as_of,
            reason=REASON_SCHEMA_MISMATCH,
        )

    for key in ("risk_status", "sizing_status", "capital_status"):
        if key not in risk_sizing_capital_fields:
            raise KeyError(f"risk_sizing_capital_fields missing required keys: ['{key}']")

    risk_status = _enum_or_str(risk_sizing_capital_fields["risk_status"]).strip()
    sizing_status = _enum_or_str(risk_sizing_capital_fields["sizing_status"]).strip()
    capital_status = _enum_or_str(risk_sizing_capital_fields["capital_status"]).strip()
    if not risk_status or not sizing_status or not capital_status:
        return unavailable_risk_sizing_capital(
            availability=Availability.INVALID,
            generated_at=as_of,
            reason=REASON_INVALID_PROVENANCE,
        )

    generated_at_raw = risk_sizing_capital_fields.get("generated_at")
    producer_at, gen_error = _resolve_injected_aware_timestamp(generated_at_raw)
    if gen_error is not None:
        return unavailable_risk_sizing_capital(
            availability=Availability.INVALID,
            generated_at=as_of,
            reason=gen_error,
        )
    if producer_at is None:
        return unavailable_risk_sizing_capital(
            availability=Availability.MISSING_SOURCE,
            generated_at=as_of,
            reason=REASON_PRODUCER_TIMESTAMP_MISSING,
        )

    effective_at: datetime | None = None
    if "effective_at" in risk_sizing_capital_fields:
        effective_at, eff_error = _resolve_injected_aware_timestamp(
            risk_sizing_capital_fields.get("effective_at")
        )
        if eff_error is not None:
            return unavailable_risk_sizing_capital(
                availability=Availability.INVALID,
                generated_at=as_of,
                reason=eff_error,
            )

    try:
        availability, is_stale, stale_reason = classify_producer_freshness(
            producer_at=producer_at,
            as_of=as_of,
            max_age_seconds=LANDSCAPE_PHASE44B_MAX_AGE_SECONDS,
        )
    except ValueError:
        return unavailable_risk_sizing_capital(
            availability=Availability.INVALID,
            generated_at=as_of,
            reason=REASON_PRODUCER_TIMESTAMP_INVALID,
        )

    quantity: float | None = None
    if (
        "quantity" in risk_sizing_capital_fields
        and risk_sizing_capital_fields["quantity"] is not None
    ):
        try:
            quantity = float(risk_sizing_capital_fields["quantity"])
        except (TypeError, ValueError):
            return unavailable_risk_sizing_capital(
                availability=Availability.INVALID,
                generated_at=as_of,
                reason=REASON_INVALID_PROVENANCE,
            )
        if quantity != quantity or quantity in (float("inf"), float("-inf")):
            return unavailable_risk_sizing_capital(
                availability=Availability.INVALID,
                generated_at=as_of,
                reason=REASON_INVALID_PROVENANCE,
            )
        if availability is not Availability.AVAILABLE:
            quantity = None

    raw_reasons = risk_sizing_capital_fields.get("reason_codes", ()) or ()
    reason_codes = tuple(str(code) for code in raw_reasons)

    evidence_digest = risk_sizing_capital_fields.get("evidence_digest")
    if evidence_digest is None:
        evidence_digest = risk_sizing_capital_fields.get("risk_sizing_ref")
    if evidence_digest is not None:
        evidence_digest = str(evidence_digest) or None

    source_reference = risk_sizing_capital_fields.get("source_reference")
    if source_reference is not None:
        source_reference = str(source_reference)

    producer_module = str(
        risk_sizing_capital_fields.get("producer_module", RISK_SIZING_PRODUCER_MODULE)
    )
    source_kind = str(risk_sizing_capital_fields.get("source_kind", RISK_SIZING_SOURCE_KIND))

    return project_risk_sizing_capital_snapshot_v1(
        risk_status=risk_status,
        sizing_status=sizing_status,
        capital_status=capital_status,
        reason_codes=reason_codes,
        quantity=quantity,
        generated_at=producer_at,
        effective_at=effective_at,
        source_reference=source_reference,
        evidence_digest=evidence_digest,
        git_sha=git_sha,
        producer_module=producer_module,
        source_kind=source_kind,
        availability=availability,
        max_age_seconds=LANDSCAPE_PHASE44B_MAX_AGE_SECONDS,
        is_stale=is_stale,
        stale_reason=stale_reason,
    )


def _bind_execution_reconciliation(
    *,
    as_of: datetime,
    git_sha: str | None,
    execution_reconciliation_fields: Mapping[str, Any] | None,
) -> Any:
    """Project injected Execution/Reconciliation fields.

    No durable dashboard Execution readmodel. Without injection → MISSING_SOURCE.
    Never builds order intents, never calls execution/order APIs, never mutates
    reconciliation. reconciliation_status / order_intent_ref may be absent.
    """
    if execution_reconciliation_fields is None:
        return unavailable_execution_reconciliation(
            availability=Availability.MISSING_SOURCE,
            generated_at=as_of,
            reason=REASON_EXECUTION_NOT_PERSISTED,
        )

    schema_version = execution_reconciliation_fields.get("schema_version")
    if schema_version is not None and str(schema_version) != LANDSCAPE_PROJECTION_SCHEMA_VERSION:
        return unavailable_execution_reconciliation(
            availability=Availability.INVALID,
            generated_at=as_of,
            reason=REASON_SCHEMA_MISMATCH,
        )

    if "execution_status" not in execution_reconciliation_fields:
        raise KeyError(
            "execution_reconciliation_fields missing required keys: ['execution_status']"
        )

    execution_status = _enum_or_str(execution_reconciliation_fields["execution_status"]).strip()
    if not execution_status:
        return unavailable_execution_reconciliation(
            availability=Availability.INVALID,
            generated_at=as_of,
            reason=REASON_INVALID_PROVENANCE,
        )

    generated_at_raw = execution_reconciliation_fields.get("generated_at")
    producer_at, gen_error = _resolve_injected_aware_timestamp(generated_at_raw)
    if gen_error is not None:
        return unavailable_execution_reconciliation(
            availability=Availability.INVALID,
            generated_at=as_of,
            reason=gen_error,
        )
    if producer_at is None:
        return unavailable_execution_reconciliation(
            availability=Availability.MISSING_SOURCE,
            generated_at=as_of,
            reason=REASON_PRODUCER_TIMESTAMP_MISSING,
        )

    effective_at: datetime | None = None
    if "effective_at" in execution_reconciliation_fields:
        effective_at, eff_error = _resolve_injected_aware_timestamp(
            execution_reconciliation_fields.get("effective_at")
        )
        if eff_error is not None:
            return unavailable_execution_reconciliation(
                availability=Availability.INVALID,
                generated_at=as_of,
                reason=eff_error,
            )

    try:
        availability, is_stale, stale_reason = classify_producer_freshness(
            producer_at=producer_at,
            as_of=as_of,
            max_age_seconds=LANDSCAPE_PHASE45_MAX_AGE_SECONDS,
        )
    except ValueError:
        return unavailable_execution_reconciliation(
            availability=Availability.INVALID,
            generated_at=as_of,
            reason=REASON_PRODUCER_TIMESTAMP_INVALID,
        )

    reconciliation_status = _optional_injected_str(
        execution_reconciliation_fields.get("reconciliation_status")
    )
    order_intent_ref = _optional_injected_str(
        execution_reconciliation_fields.get("order_intent_ref")
    )

    raw_reasons = execution_reconciliation_fields.get("reason_codes", ()) or ()
    reason_codes = tuple(str(code) for code in raw_reasons)

    evidence_digest = execution_reconciliation_fields.get("evidence_digest")
    if evidence_digest is None:
        evidence_digest = execution_reconciliation_fields.get("semantic_digest")
    if evidence_digest is not None:
        evidence_digest = str(evidence_digest) or None

    source_reference = execution_reconciliation_fields.get("source_reference")
    if source_reference is not None:
        source_reference = str(source_reference)

    producer_module = str(
        execution_reconciliation_fields.get("producer_module", EXECUTION_PRODUCER_MODULE)
    )
    source_kind = str(execution_reconciliation_fields.get("source_kind", EXECUTION_SOURCE_KIND))

    return project_execution_reconciliation_snapshot_v1(
        execution_status=execution_status,
        reconciliation_status=reconciliation_status,
        order_intent_ref=order_intent_ref,
        reason_codes=reason_codes,
        generated_at=producer_at,
        effective_at=effective_at,
        source_reference=source_reference,
        evidence_digest=evidence_digest,
        git_sha=git_sha,
        producer_module=producer_module,
        source_kind=source_kind,
        availability=availability,
        max_age_seconds=LANDSCAPE_PHASE45_MAX_AGE_SECONDS,
        is_stale=is_stale,
        stale_reason=stale_reason,
    )


def bind_market_universe_slots(
    *,
    generated_at: datetime,
    archive_root: str | Path | None = None,
    git_sha: str | None = None,
    market_instrument_fields: Mapping[str, Any] | None = None,
    dynamic_scope_fields: Mapping[str, Any] | None = None,
    regime_bull_bear_switch_fields: Mapping[str, Any] | None = None,
    canonical_decision_fields: Mapping[str, Any] | None = None,
    double_play_fields: Mapping[str, Any] | None = None,
    safety_authority_fields: Mapping[str, Any] | None = None,
    risk_sizing_capital_fields: Mapping[str, Any] | None = None,
    execution_reconciliation_fields: Mapping[str, Any] | None = None,
    economic_viability_evidence_fields: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Return Phase 4.1–4.5 + 4.6B slot overrides.

    ``generated_at`` is the dashboard observation/as-of clock only. It must never
    overwrite producer provenance timestamps or fabricate freshness.

    market_instrument_fields accepts already-computed CanonicalMarketContext
    field dicts for tests and future durable loaders. Those fields must carry
    producer ``generated_at`` and/or ``effective_at``.

    dynamic_scope_fields accepts already-computed CanonicalScopeSnapshotV1-
    compatible lifecycle identity fields plus producer wall-clock timestamps.
    Without injection, dynamic_scope is MISSING_SOURCE (no durable readmodel).

    regime_bull_bear_switch_fields accepts already-computed Regime /
    SideState / StateSwitchEvidenceV1-compatible fields plus producer
    wall-clock timestamps. Without injection, regime_bull_bear_switch is
    MISSING_SOURCE. Never calls transition_state or invents SideState.

    canonical_decision_fields accepts already-computed
    CanonicalTradingDecisionEvidenceV1-compatible fields plus producer
    wall-clock timestamps. Without injection, canonical_decision is
    MISSING_SOURCE (no durable readmodel).

    double_play_fields accepts already-computed
    DoublePlayDashboardDisplaySnapshot-compatible fields plus producer
    wall-clock timestamps. Without injection, double_play is MISSING_SOURCE.
    Never calls compose/build Double Play owners.

    safety_authority_fields accepts already-computed KillSwitch / boundary-
    compatible fields (kill_switch_state, veto_active, reason_codes) plus
    producer wall-clock timestamps. Without injection, safety_authority is
    MISSING_SOURCE. Never calls KillSwitch.trigger/recover or offline evaluators.

    risk_sizing_capital_fields accepts already-selected Risk/Sizing/Capital
    display fields (risk_status/sizing_status/capital_status[/quantity]) plus
    producer wall-clock timestamps. Without injection, risk_sizing_capital is
    MISSING_SOURCE. Never calls capital/risk/sizing evaluators.

    execution_reconciliation_fields accepts already-selected Execution/
    Reconciliation display fields (execution_status[/reconciliation_status]/
    order_intent_ref]) plus producer wall-clock timestamps. Without injection,
    execution_reconciliation is MISSING_SOURCE. Never builds intents or calls
    execution/order/reconciliation mutation APIs.

    economic_viability_evidence_fields accepts already-selected
    EconomicViabilityEvidenceV1-compatible fields plus producer wall-clock
    timestamps. Without injection, economic_summary is MISSING_SOURCE.
    Never discovers evidence artifacts or binds promotion_economic_gate_v1.
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
    regime_bbs = _bind_regime_bull_bear_switch(
        as_of=as_of,
        git_sha=git_sha,
        regime_bull_bear_switch_fields=regime_bull_bear_switch_fields,
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
    safety = _bind_safety_authority(
        as_of=as_of,
        git_sha=git_sha,
        safety_authority_fields=safety_authority_fields,
    )
    risk = _bind_risk_sizing_capital(
        as_of=as_of,
        git_sha=git_sha,
        risk_sizing_capital_fields=risk_sizing_capital_fields,
    )
    execution = _bind_execution_reconciliation(
        as_of=as_of,
        git_sha=git_sha,
        execution_reconciliation_fields=execution_reconciliation_fields,
    )
    economic = _bind_economic_summary(
        as_of=as_of,
        git_sha=git_sha,
        economic_viability_evidence_fields=economic_viability_evidence_fields,
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
        "regime_bull_bear_switch": regime_bbs,
        "canonical_decision": decision,
        "double_play": double_play,
        "risk_sizing_capital": risk,
        "safety_authority": safety,
        "execution_reconciliation": execution,
        "economic_summary": economic,
    }
