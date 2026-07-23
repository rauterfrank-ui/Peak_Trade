"""Unavailable / unbound snapshot factories — no silent defaults."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Callable

from .availability import Availability
from .contracts import (
    SCHEMA_FAMILY,
    SCHEMA_VERSION,
    AutonomyStageSnapshotV1,
    CanonicalDecisionSnapshotV1,
    DiagnosticsSummarySnapshotV1,
    DoublePlaySnapshotV1,
    DynamicScopeSnapshotV1,
    EconomicSummarySnapshotV1,
    ExecutionReconciliationSnapshotV1,
    MarketInstrumentSnapshotV1,
    RiskSizingCapitalSnapshotV1,
    SafetyAuthoritySnapshotV1,
    UniverseRankingSnapshotV1,
)
from .owner_registry import owner_registry_by_slot
from .provenance import FreshnessV1, SnapshotProvenanceV1

_UNAVAILABLE_STATES = frozenset(
    {
        Availability.NOT_BOUND,
        Availability.MISSING_SOURCE,
        Availability.STALE,
        Availability.INVALID,
    }
)


def _utc_now_for_tests(generated_at: datetime | None) -> datetime:
    if generated_at is None:
        raise ValueError("generated_at must be supplied explicitly (no silent clock default)")
    return generated_at


def build_unavailable_provenance(
    *,
    slot: str,
    availability: Availability,
    generated_at: datetime,
    reason: str,
    source_reference: str | None = None,
    evidence_digest: str | None = None,
    git_sha: str | None = None,
) -> SnapshotProvenanceV1:
    if availability not in _UNAVAILABLE_STATES:
        raise ValueError(
            f"unavailable provenance requires non-AVAILABLE state, got {availability.value}"
        )
    if not reason or not str(reason).strip():
        raise ValueError("reason required for unavailable provenance")
    owners = owner_registry_by_slot()
    if slot not in owners:
        raise ValueError(f"unknown projection slot={slot!r}")
    owner = owners[slot]
    return SnapshotProvenanceV1(
        schema_id=f"{SCHEMA_FAMILY}.{slot}.{SCHEMA_VERSION}",
        schema_version=SCHEMA_VERSION,
        producer_module=owner.owner_module,
        generated_at=_utc_now_for_tests(generated_at),
        effective_at=None,
        source_kind=f"unavailable:{availability.value}",
        source_reference=source_reference or reason,
        evidence_digest=evidence_digest,
        git_sha=git_sha,
        availability=availability,
    )


def build_unavailable_freshness(
    *,
    observed_at: datetime,
    availability: Availability,
    stale_reason: str | None = None,
) -> FreshnessV1:
    if availability is Availability.STALE:
        if not stale_reason:
            raise ValueError("stale_reason required for STALE")
        return FreshnessV1(
            observed_at=observed_at,
            max_age_seconds=None,
            is_stale=True,
            stale_reason=stale_reason,
        )
    return FreshnessV1(
        observed_at=observed_at,
        max_age_seconds=None,
        is_stale=False,
        stale_reason=None,
    )


def unavailable_market_instrument(
    *,
    availability: Availability,
    generated_at: datetime,
    reason: str,
) -> MarketInstrumentSnapshotV1:
    provenance = build_unavailable_provenance(
        slot="market_instrument",
        availability=availability,
        generated_at=generated_at,
        reason=reason,
    )
    return MarketInstrumentSnapshotV1(
        schema_id=provenance.schema_id,
        schema_version=SCHEMA_VERSION,
        provenance=provenance,
        freshness=build_unavailable_freshness(
            observed_at=generated_at,
            availability=availability,
            stale_reason=reason if availability is Availability.STALE else None,
        ),
        availability=availability,
        instrument_id=None,
        venue=None,
        market_type=None,
        mark_price=None,
        reason_codes=(reason,),
    )


def unavailable_universe_ranking(
    *,
    availability: Availability,
    generated_at: datetime,
    reason: str,
) -> UniverseRankingSnapshotV1:
    provenance = build_unavailable_provenance(
        slot="universe_ranking",
        availability=availability,
        generated_at=generated_at,
        reason=reason,
    )
    return UniverseRankingSnapshotV1(
        schema_id=provenance.schema_id,
        schema_version=SCHEMA_VERSION,
        provenance=provenance,
        freshness=build_unavailable_freshness(
            observed_at=generated_at,
            availability=availability,
            stale_reason=reason if availability is Availability.STALE else None,
        ),
        availability=availability,
        ranking=(),
        universe=(),
        selected_instrument_id=None,
        reason_codes=(reason,),
    )


def unavailable_dynamic_scope(
    *,
    availability: Availability,
    generated_at: datetime,
    reason: str,
) -> DynamicScopeSnapshotV1:
    provenance = build_unavailable_provenance(
        slot="dynamic_scope",
        availability=availability,
        generated_at=generated_at,
        reason=reason,
    )
    return DynamicScopeSnapshotV1(
        schema_id=provenance.schema_id,
        schema_version=SCHEMA_VERSION,
        provenance=provenance,
        freshness=build_unavailable_freshness(
            observed_at=generated_at,
            availability=availability,
            stale_reason=reason if availability is Availability.STALE else None,
        ),
        availability=availability,
        scope_state=None,
        current_scope_ref=None,
        next_scope_ref=None,
        reason_codes=(reason,),
    )


def unavailable_canonical_decision(
    *,
    availability: Availability,
    generated_at: datetime,
    reason: str,
) -> CanonicalDecisionSnapshotV1:
    provenance = build_unavailable_provenance(
        slot="canonical_decision",
        availability=availability,
        generated_at=generated_at,
        reason=reason,
    )
    return CanonicalDecisionSnapshotV1(
        schema_id=provenance.schema_id,
        schema_version=SCHEMA_VERSION,
        provenance=provenance,
        freshness=build_unavailable_freshness(
            observed_at=generated_at,
            availability=availability,
            stale_reason=reason if availability is Availability.STALE else None,
        ),
        availability=availability,
        instrument_id=None,
        decision=None,
        direction=None,
        reason_codes=(reason,),
        blockers=(reason,),
        decision_id=None,
        evidence_schema_version=None,
    )


def unavailable_double_play(
    *,
    availability: Availability,
    generated_at: datetime,
    reason: str,
) -> DoublePlaySnapshotV1:
    provenance = build_unavailable_provenance(
        slot="double_play",
        availability=availability,
        generated_at=generated_at,
        reason=reason,
    )
    return DoublePlaySnapshotV1(
        schema_id=provenance.schema_id,
        schema_version=SCHEMA_VERSION,
        provenance=provenance,
        freshness=build_unavailable_freshness(
            observed_at=generated_at,
            availability=availability,
            stale_reason=reason if availability is Availability.STALE else None,
        ),
        availability=availability,
        overall_status=None,
        panel_summaries=(),
        blockers=(reason,),
        display_only=True,
        live_authorization=False,
    )


def unavailable_risk_sizing_capital(
    *,
    availability: Availability,
    generated_at: datetime,
    reason: str,
) -> RiskSizingCapitalSnapshotV1:
    provenance = build_unavailable_provenance(
        slot="risk_sizing_capital",
        availability=availability,
        generated_at=generated_at,
        reason=reason,
    )
    return RiskSizingCapitalSnapshotV1(
        schema_id=provenance.schema_id,
        schema_version=SCHEMA_VERSION,
        provenance=provenance,
        freshness=build_unavailable_freshness(
            observed_at=generated_at,
            availability=availability,
            stale_reason=reason if availability is Availability.STALE else None,
        ),
        availability=availability,
        risk_status=None,
        sizing_status=None,
        capital_status=None,
        reason_codes=(reason,),
        quantity=None,
    )


def unavailable_safety_authority(
    *,
    availability: Availability,
    generated_at: datetime,
    reason: str,
) -> SafetyAuthoritySnapshotV1:
    provenance = build_unavailable_provenance(
        slot="safety_authority",
        availability=availability,
        generated_at=generated_at,
        reason=reason,
    )
    return SafetyAuthoritySnapshotV1(
        schema_id=provenance.schema_id,
        schema_version=SCHEMA_VERSION,
        provenance=provenance,
        freshness=build_unavailable_freshness(
            observed_at=generated_at,
            availability=availability,
            stale_reason=reason if availability is Availability.STALE else None,
        ),
        availability=availability,
        kill_switch_state=None,
        veto_active=None,
        reason_codes=(reason,),
    )


def unavailable_execution_reconciliation(
    *,
    availability: Availability,
    generated_at: datetime,
    reason: str,
) -> ExecutionReconciliationSnapshotV1:
    provenance = build_unavailable_provenance(
        slot="execution_reconciliation",
        availability=availability,
        generated_at=generated_at,
        reason=reason,
    )
    return ExecutionReconciliationSnapshotV1(
        schema_id=provenance.schema_id,
        schema_version=SCHEMA_VERSION,
        provenance=provenance,
        freshness=build_unavailable_freshness(
            observed_at=generated_at,
            availability=availability,
            stale_reason=reason if availability is Availability.STALE else None,
        ),
        availability=availability,
        execution_status=None,
        reconciliation_status=None,
        order_intent_ref=None,
        reason_codes=(reason,),
    )


def unavailable_economic_summary(
    *,
    availability: Availability,
    generated_at: datetime,
    reason: str,
) -> EconomicSummarySnapshotV1:
    provenance = build_unavailable_provenance(
        slot="economic_summary",
        availability=availability,
        generated_at=generated_at,
        reason=reason,
    )
    return EconomicSummarySnapshotV1(
        schema_id=provenance.schema_id,
        schema_version=SCHEMA_VERSION,
        provenance=provenance,
        freshness=build_unavailable_freshness(
            observed_at=generated_at,
            availability=availability,
            stale_reason=reason if availability is Availability.STALE else None,
        ),
        availability=availability,
        economic_viability_status=None,
        economic_validity_proven=None,
        profitability_claim_allowed=None,
        policy_threshold_status=None,
        policy_version=None,
        authority_effect=None,
        runtime_effect=None,
        order_effect=None,
        reason_codes=(reason,),
        profit_factor=None,
        net_return=None,
        max_drawdown=None,
        sharpe=None,
        trade_count=None,
        funding_drag=None,
        evidence_ref=None,
        contract_version=None,
        owner=None,
        strategy_id=None,
        strategy_version=None,
        config_digest=None,
        implementation_digest=None,
        data_digest=None,
        manifest_digest=None,
        wiring_chain_digest=None,
        policy_digest=None,
    )


def unavailable_autonomy_stage(
    *,
    availability: Availability,
    generated_at: datetime,
    reason: str,
) -> AutonomyStageSnapshotV1:
    provenance = build_unavailable_provenance(
        slot="autonomy_stage",
        availability=availability,
        generated_at=generated_at,
        reason=reason,
    )
    return AutonomyStageSnapshotV1(
        schema_id=provenance.schema_id,
        schema_version=SCHEMA_VERSION,
        provenance=provenance,
        freshness=build_unavailable_freshness(
            observed_at=generated_at,
            availability=availability,
            stale_reason=reason if availability is Availability.STALE else None,
        ),
        availability=availability,
        autonomy_stage=None,
        runtime_bridge_status=None,
        reason_codes=(reason,),
    )


def unavailable_diagnostics_summary(
    *,
    availability: Availability,
    generated_at: datetime,
    reason: str,
) -> DiagnosticsSummarySnapshotV1:
    provenance = build_unavailable_provenance(
        slot="diagnostics_summary",
        availability=availability,
        generated_at=generated_at,
        reason=reason,
    )
    return DiagnosticsSummarySnapshotV1(
        schema_id=provenance.schema_id,
        schema_version=SCHEMA_VERSION,
        provenance=provenance,
        freshness=build_unavailable_freshness(
            observed_at=generated_at,
            availability=availability,
            stale_reason=reason if availability is Availability.STALE else None,
        ),
        availability=availability,
        diagnostic_codes=(),
        summary=None,
        reason_codes=(reason,),
    )


UNAVAILABLE_BUILDERS: dict[str, Callable[..., object]] = {
    "market_instrument": unavailable_market_instrument,
    "universe_ranking": unavailable_universe_ranking,
    "dynamic_scope": unavailable_dynamic_scope,
    "canonical_decision": unavailable_canonical_decision,
    "double_play": unavailable_double_play,
    "risk_sizing_capital": unavailable_risk_sizing_capital,
    "safety_authority": unavailable_safety_authority,
    "execution_reconciliation": unavailable_execution_reconciliation,
    "economic_summary": unavailable_economic_summary,
    "autonomy_stage": unavailable_autonomy_stage,
    "diagnostics_summary": unavailable_diagnostics_summary,
}


def default_not_bound_bundle(*, generated_at: datetime | None = None) -> dict[str, object]:
    """Explicit NOT_BOUND bundle for all unbound Landscape slots.

    generated_at is mandatory via keyword; no wall-clock silent default.
    """
    if generated_at is None:
        raise ValueError("generated_at required (no silent datetime.now default)")
    if generated_at.tzinfo is None:
        raise ValueError("generated_at must be timezone-aware")
    # Normalize intent: accept any tz-aware; factories enforce UTC via provenance.
    stamp = generated_at.astimezone(timezone.utc)
    reason = "LANDSCAPE_V2_SLOT_NOT_BOUND"
    return {
        slot: builder(
            availability=Availability.NOT_BOUND,
            generated_at=stamp,
            reason=reason,
        )
        for slot, builder in UNAVAILABLE_BUILDERS.items()
    }
