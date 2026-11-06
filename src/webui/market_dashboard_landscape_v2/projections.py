"""Pure field-projection adapters — no decision/risk/sizing recomputation."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Mapping, Sequence

from .availability import Availability
from .contracts import (
    SCHEMA_FAMILY,
    SCHEMA_VERSION,
    CanonicalDecisionSnapshotV1,
    DoublePlaySnapshotV1,
    DynamicScopeSnapshotV1,
    EconomicSummarySnapshotV1,
    ExecutionReconciliationSnapshotV1,
    MarketInstrumentSnapshotV1,
    RegimeBullBearSwitchSnapshotV1,
    RiskSizingCapitalSnapshotV1,
    SafetyAuthoritySnapshotV1,
    UniverseRankingSnapshotV1,
)
from .provenance import FreshnessV1, SnapshotProvenanceV1


def project_market_instrument_snapshot_v1(
    *,
    instrument_id: str,
    venue: str | None,
    market_type: str | None,
    mark_price: float | None,
    reason_codes: Sequence[str],
    generated_at: datetime,
    effective_at: datetime | None,
    source_reference: str | None,
    evidence_digest: str | None = None,
    git_sha: str | None = None,
    producer_module: str = "trading.master_v2.canonical_market_context_v1",
    source_kind: str = "canonical_market_context",
    availability: Availability = Availability.AVAILABLE,
    max_age_seconds: int | None = None,
    is_stale: bool = False,
    stale_reason: str | None = None,
) -> MarketInstrumentSnapshotV1:
    """Project already-computed market identity fields into a Landscape snapshot.

    Forbidden: inventing instrument/venue/mark_price, fabricating OHLCV, or
    deriving futures/spot eligibility from symbol heuristics.
    market_type and mark_price may remain None when the producer did not supply them.
    generated_at/effective_at must be producer timestamps — never page-assembly time.
    """
    if not instrument_id:
        raise ValueError("instrument_id required for AVAILABLE/STALE projection")
    if availability not in (Availability.AVAILABLE, Availability.STALE):
        raise ValueError("project_market_instrument only emits AVAILABLE or STALE")
    if availability is Availability.AVAILABLE and is_stale:
        raise ValueError("AVAILABLE cannot be stale")
    if availability is Availability.STALE and not is_stale:
        raise ValueError("STALE requires is_stale=True")
    schema_id = f"{SCHEMA_FAMILY}.market_instrument.{SCHEMA_VERSION}"
    provenance = SnapshotProvenanceV1(
        schema_id=schema_id,
        schema_version=SCHEMA_VERSION,
        producer_module=producer_module,
        generated_at=generated_at,
        effective_at=effective_at,
        source_kind=source_kind,
        source_reference=source_reference,
        evidence_digest=evidence_digest,
        git_sha=git_sha,
        availability=availability,
    )
    freshness = FreshnessV1(
        observed_at=generated_at,
        max_age_seconds=max_age_seconds,
        is_stale=is_stale,
        stale_reason=stale_reason,
    )
    return MarketInstrumentSnapshotV1(
        schema_id=schema_id,
        schema_version=SCHEMA_VERSION,
        provenance=provenance,
        freshness=freshness,
        availability=availability,
        instrument_id=instrument_id,
        venue=venue,
        market_type=market_type,
        mark_price=None if mark_price is None else float(mark_price),
        reason_codes=tuple(str(code) for code in reason_codes),
    )


def project_universe_ranking_snapshot_v1(
    *,
    ranking: Sequence[Mapping[str, Any]],
    selected_instrument_id: str | None,
    reason_codes: Sequence[str],
    generated_at: datetime,
    effective_at: datetime | None,
    source_reference: str | None,
    universe: Sequence[Mapping[str, Any]] = (),
    evidence_digest: str | None = None,
    git_sha: str | None = None,
    producer_module: str = ("webui.workflow_dashboard_readmodel_v1.universe_selection_contract_v1"),
    availability: Availability = Availability.AVAILABLE,
    max_age_seconds: int | None = None,
    is_stale: bool = False,
    stale_reason: str | None = None,
    source_run_id: str | None = None,
    selection_reason: str | None = None,
    selected_rank: int | None = None,
) -> UniverseRankingSnapshotV1:
    """Project an existing universe_selection ranking into Landscape form.

    Forbidden: recomputing ranks, inventing selected instruments, or enriching
    rows with decision/risk/sizing semantics.
    generated_at/effective_at must be producer timestamps — never page-assembly time.
    Optional source_run_id / selection_reason / selected_rank are exact producer
    fields only — never synthesized.
    """
    ranking_rows = tuple(dict(row) for row in ranking)
    universe_rows = tuple(dict(row) for row in universe)
    if not ranking_rows and not universe_rows and not selected_instrument_id:
        raise ValueError(
            "ranking, universe, or selected_instrument_id required for AVAILABLE/STALE"
        )
    if availability not in (Availability.AVAILABLE, Availability.STALE):
        raise ValueError("project_universe_ranking only emits AVAILABLE or STALE")
    if availability is Availability.AVAILABLE and is_stale:
        raise ValueError("AVAILABLE cannot be stale")
    if availability is Availability.STALE and not is_stale:
        raise ValueError("STALE requires is_stale=True")
    schema_id = f"{SCHEMA_FAMILY}.universe_ranking.{SCHEMA_VERSION}"
    provenance = SnapshotProvenanceV1(
        schema_id=schema_id,
        schema_version=SCHEMA_VERSION,
        producer_module=producer_module,
        generated_at=generated_at,
        effective_at=effective_at,
        source_kind="universe_selection_readmodel",
        source_reference=source_reference,
        evidence_digest=evidence_digest,
        git_sha=git_sha,
        availability=availability,
    )
    freshness = FreshnessV1(
        observed_at=generated_at,
        max_age_seconds=max_age_seconds,
        is_stale=is_stale,
        stale_reason=stale_reason,
    )
    return UniverseRankingSnapshotV1(
        schema_id=schema_id,
        schema_version=SCHEMA_VERSION,
        provenance=provenance,
        freshness=freshness,
        availability=availability,
        ranking=ranking_rows,
        universe=universe_rows,
        selected_instrument_id=selected_instrument_id,
        reason_codes=tuple(str(code) for code in reason_codes),
        source_run_id=source_run_id,
        selection_reason=selection_reason,
        selected_rank=selected_rank,
    )


def project_dynamic_scope_snapshot_v1(
    *,
    scope_state: str,
    current_scope_ref: str,
    reason_codes: Sequence[str],
    generated_at: datetime,
    effective_at: datetime | None,
    source_reference: str | None,
    next_scope_ref: str | None = None,
    evidence_digest: str | None = None,
    git_sha: str | None = None,
    producer_module: str = "trading.master_v2.canonical_scope_initialization_v1",
    source_kind: str = "canonical_scope_snapshot",
    availability: Availability = Availability.AVAILABLE,
    max_age_seconds: int | None = None,
    is_stale: bool = False,
    stale_reason: str | None = None,
) -> DynamicScopeSnapshotV1:
    """Project already-computed canonical scope lifecycle identity fields.

    Forbidden: inventing lifecycle state/refs, deriving regime/bull-bear/switch,
    calling scope initializers or switch-transition owners, or using page-assembly
    time as producer freshness.
    generated_at/effective_at must be producer timestamps — never page-assembly time.
    """
    if not scope_state:
        raise ValueError("scope_state required for AVAILABLE/STALE projection")
    if not current_scope_ref:
        raise ValueError("current_scope_ref required for AVAILABLE/STALE projection")
    if availability not in (Availability.AVAILABLE, Availability.STALE):
        raise ValueError("project_dynamic_scope only emits AVAILABLE or STALE")
    if availability is Availability.AVAILABLE and is_stale:
        raise ValueError("AVAILABLE cannot be stale")
    if availability is Availability.STALE and not is_stale:
        raise ValueError("STALE requires is_stale=True")
    schema_id = f"{SCHEMA_FAMILY}.dynamic_scope.{SCHEMA_VERSION}"
    provenance = SnapshotProvenanceV1(
        schema_id=schema_id,
        schema_version=SCHEMA_VERSION,
        producer_module=producer_module,
        generated_at=generated_at,
        effective_at=effective_at,
        source_kind=source_kind,
        source_reference=source_reference,
        evidence_digest=evidence_digest,
        git_sha=git_sha,
        availability=availability,
    )
    freshness = FreshnessV1(
        observed_at=generated_at,
        max_age_seconds=max_age_seconds,
        is_stale=is_stale,
        stale_reason=stale_reason,
    )
    return DynamicScopeSnapshotV1(
        schema_id=schema_id,
        schema_version=SCHEMA_VERSION,
        provenance=provenance,
        freshness=freshness,
        availability=availability,
        scope_state=str(scope_state),
        current_scope_ref=str(current_scope_ref),
        next_scope_ref=None if next_scope_ref is None else str(next_scope_ref),
        reason_codes=tuple(str(code) for code in reason_codes),
    )


def project_regime_bull_bear_switch_snapshot_v1(
    *,
    regime_id: str,
    regime_status: str,
    side_state: str,
    previous_side_state: str,
    next_side_state: str,
    scope_event_type: str,
    transition_allowed: bool,
    transition_reason_code: str,
    reason_codes: Sequence[str],
    generated_at: datetime,
    effective_at: datetime | None,
    source_reference: str | None,
    evidence_digest: str | None = None,
    git_sha: str | None = None,
    producer_module: str = "trading.master_v2.double_play_state",
    source_kind: str = "regime_bull_bear_switch_projection",
    availability: Availability = Availability.AVAILABLE,
    max_age_seconds: int | None = None,
    is_stale: bool = False,
    stale_reason: str | None = None,
) -> RegimeBullBearSwitchSnapshotV1:
    """Project already-computed Regime / SideState / Switch evidence fields.

    Forbidden: calling transition_state, deriving SideState/ActiveSide, inventing
    regime_id, or synthesizing across contradictory producers.
    generated_at/effective_at must be producer timestamps — never page-assembly time.
    """
    if not regime_id or not regime_status or not side_state:
        raise ValueError("regime_id, regime_status, and side_state required")
    if not previous_side_state or not next_side_state or not scope_event_type:
        raise ValueError("switch identity fields required for AVAILABLE/STALE")
    if not transition_reason_code:
        raise ValueError("transition_reason_code required for AVAILABLE/STALE")
    if not isinstance(transition_allowed, bool):
        raise TypeError("transition_allowed must be bool")
    if availability not in (Availability.AVAILABLE, Availability.STALE):
        raise ValueError("project_regime_bull_bear_switch only emits AVAILABLE or STALE")
    if availability is Availability.AVAILABLE and is_stale:
        raise ValueError("AVAILABLE cannot be stale")
    if availability is Availability.STALE and not is_stale:
        raise ValueError("STALE requires is_stale=True")
    schema_id = f"{SCHEMA_FAMILY}.regime_bull_bear_switch.{SCHEMA_VERSION}"
    provenance = SnapshotProvenanceV1(
        schema_id=schema_id,
        schema_version=SCHEMA_VERSION,
        producer_module=producer_module,
        generated_at=generated_at,
        effective_at=effective_at,
        source_kind=source_kind,
        source_reference=source_reference,
        evidence_digest=evidence_digest,
        git_sha=git_sha,
        availability=availability,
    )
    freshness = FreshnessV1(
        observed_at=generated_at,
        max_age_seconds=max_age_seconds,
        is_stale=is_stale,
        stale_reason=stale_reason,
    )
    return RegimeBullBearSwitchSnapshotV1(
        schema_id=schema_id,
        schema_version=SCHEMA_VERSION,
        provenance=provenance,
        freshness=freshness,
        availability=availability,
        regime_id=str(regime_id),
        regime_status=str(regime_status),
        side_state=str(side_state),
        previous_side_state=str(previous_side_state),
        next_side_state=str(next_side_state),
        scope_event_type=str(scope_event_type),
        transition_allowed=bool(transition_allowed),
        transition_reason_code=str(transition_reason_code),
        reason_codes=tuple(str(code) for code in reason_codes),
    )


def project_canonical_decision_snapshot_v1(
    *,
    instrument_id: str,
    decision: str,
    direction: str,
    reason_codes: Sequence[str],
    blockers: Sequence[str],
    decision_id: str | None,
    evidence_schema_version: str,
    evidence_digest: str | None,
    generated_at: datetime,
    effective_at: datetime | None,
    source_reference: str | None,
    git_sha: str | None = None,
    producer_module: str = "trading.master_v2.canonical_trading_decision_evidence_v1",
    source_kind: str = "canonical_trading_decision_evidence",
    availability: Availability = Availability.AVAILABLE,
    max_age_seconds: int | None = None,
    is_stale: bool = False,
    stale_reason: str | None = None,
) -> CanonicalDecisionSnapshotV1:
    """Project already-computed decision evidence fields into a Landscape snapshot.

    Forbidden: inventing decision/direction, synthesizing reason codes, or
    deriving blockers from non-evidence sources.
    generated_at/effective_at must be producer timestamps — never page-assembly time.
    Blockers must remain empty when the canonical evidence has no blockers field.
    """
    if not instrument_id or not decision or not direction:
        raise ValueError("instrument_id, decision, and direction are required for AVAILABLE/STALE")
    if not evidence_schema_version:
        raise ValueError("evidence_schema_version required")
    if availability not in (Availability.AVAILABLE, Availability.STALE):
        raise ValueError("project_canonical_decision only emits AVAILABLE or STALE")
    if availability is Availability.AVAILABLE and is_stale:
        raise ValueError("AVAILABLE cannot be stale")
    if availability is Availability.STALE and not is_stale:
        raise ValueError("STALE requires is_stale=True")
    codes = tuple(str(code) for code in reason_codes)
    block = tuple(str(code) for code in blockers)
    schema_id = f"{SCHEMA_FAMILY}.canonical_decision.{SCHEMA_VERSION}"
    provenance = SnapshotProvenanceV1(
        schema_id=schema_id,
        schema_version=SCHEMA_VERSION,
        producer_module=producer_module,
        generated_at=generated_at,
        effective_at=effective_at,
        source_kind=source_kind,
        source_reference=source_reference,
        evidence_digest=evidence_digest,
        git_sha=git_sha,
        availability=availability,
    )
    freshness = FreshnessV1(
        observed_at=generated_at,
        max_age_seconds=max_age_seconds,
        is_stale=is_stale,
        stale_reason=stale_reason,
    )
    return CanonicalDecisionSnapshotV1(
        schema_id=schema_id,
        schema_version=SCHEMA_VERSION,
        provenance=provenance,
        freshness=freshness,
        availability=availability,
        instrument_id=instrument_id,
        decision=decision,
        direction=direction,
        reason_codes=codes,
        blockers=block,
        decision_id=decision_id,
        evidence_schema_version=evidence_schema_version,
    )


def project_double_play_snapshot_v1(
    *,
    overall_status: str,
    panel_summaries: Sequence[Mapping[str, Any]],
    blockers: Sequence[str],
    generated_at: datetime,
    source_reference: str | None,
    evidence_digest: str | None = None,
    git_sha: str | None = None,
    producer_module: str = "trading.master_v2.double_play_dashboard_display",
    source_kind: str = "double_play_dashboard_display",
    effective_at: datetime | None = None,
    availability: Availability = Availability.AVAILABLE,
    max_age_seconds: int | None = None,
    is_stale: bool = False,
    stale_reason: str | None = None,
    display_only: bool = True,
    live_authorization: bool = False,
) -> DoublePlaySnapshotV1:
    """Project an existing Double Play display snapshot into Landscape form.

    Forbidden: calling compose_double_play_decision / build_dashboard_display_snapshot,
    inventing overall_status/panels/blockers, or granting live_authorization.
    generated_at/effective_at must be producer timestamps — never page-assembly time.
    """
    if not overall_status:
        raise ValueError("overall_status required for AVAILABLE/STALE")
    if availability not in (Availability.AVAILABLE, Availability.STALE):
        raise ValueError("project_double_play only emits AVAILABLE or STALE")
    if availability is Availability.AVAILABLE and is_stale:
        raise ValueError("AVAILABLE cannot be stale")
    if availability is Availability.STALE and not is_stale:
        raise ValueError("STALE requires is_stale=True")
    if live_authorization is not False:
        raise ValueError("live_authorization must remain False")
    if availability in (Availability.AVAILABLE, Availability.STALE) and not display_only:
        raise ValueError("AVAILABLE/STALE DoublePlaySnapshot must be display_only=True")
    schema_id = f"{SCHEMA_FAMILY}.double_play.{SCHEMA_VERSION}"
    provenance = SnapshotProvenanceV1(
        schema_id=schema_id,
        schema_version=SCHEMA_VERSION,
        producer_module=producer_module,
        generated_at=generated_at,
        effective_at=generated_at if effective_at is None else effective_at,
        source_kind=source_kind,
        source_reference=source_reference,
        evidence_digest=evidence_digest,
        git_sha=git_sha,
        availability=availability,
    )
    freshness = FreshnessV1(
        observed_at=generated_at,
        max_age_seconds=max_age_seconds,
        is_stale=is_stale,
        stale_reason=stale_reason,
    )
    return DoublePlaySnapshotV1(
        schema_id=schema_id,
        schema_version=SCHEMA_VERSION,
        provenance=provenance,
        freshness=freshness,
        availability=availability,
        overall_status=str(overall_status),
        panel_summaries=tuple(dict(row) for row in panel_summaries),
        blockers=tuple(str(code) for code in blockers),
        display_only=True,
        live_authorization=False,
    )


def project_safety_authority_snapshot_v1(
    *,
    kill_switch_state: str,
    veto_active: bool,
    reason_codes: Sequence[str],
    generated_at: datetime,
    source_reference: str | None,
    evidence_digest: str | None = None,
    git_sha: str | None = None,
    producer_module: str = "trading.master_v2.killswitch_boundary_offline_replay_binding_adapter_v0",
    source_kind: str = "killswitch_boundary_offline_replay_boundary",
    effective_at: datetime | None = None,
    availability: Availability = Availability.AVAILABLE,
    max_age_seconds: int | None = None,
    is_stale: bool = False,
    stale_reason: str | None = None,
) -> SafetyAuthoritySnapshotV1:
    """Project already-computed KillSwitch / boundary fields into Landscape form.

    Forbidden: instantiating KillSwitch, calling trigger/recover, calling
    evaluate_offline_killswitch_boundary_v0 or any bind_* evaluator, inventing
    healthy/default safety state, or deriving veto from Risk/Capital/Sizing.
    generated_at/effective_at must be producer timestamps — never page-assembly time.
    """
    if not kill_switch_state:
        raise ValueError("kill_switch_state required for AVAILABLE/STALE")
    if not isinstance(veto_active, bool):
        raise TypeError("veto_active must be bool")
    if availability not in (Availability.AVAILABLE, Availability.STALE):
        raise ValueError("project_safety_authority only emits AVAILABLE or STALE")
    if availability is Availability.AVAILABLE and is_stale:
        raise ValueError("AVAILABLE cannot be stale")
    if availability is Availability.STALE and not is_stale:
        raise ValueError("STALE requires is_stale=True")
    schema_id = f"{SCHEMA_FAMILY}.safety_authority.{SCHEMA_VERSION}"
    provenance = SnapshotProvenanceV1(
        schema_id=schema_id,
        schema_version=SCHEMA_VERSION,
        producer_module=producer_module,
        generated_at=generated_at,
        effective_at=generated_at if effective_at is None else effective_at,
        source_kind=source_kind,
        source_reference=source_reference,
        evidence_digest=evidence_digest,
        git_sha=git_sha,
        availability=availability,
    )
    freshness = FreshnessV1(
        observed_at=generated_at,
        max_age_seconds=max_age_seconds,
        is_stale=is_stale,
        stale_reason=stale_reason,
    )
    return SafetyAuthoritySnapshotV1(
        schema_id=schema_id,
        schema_version=SCHEMA_VERSION,
        provenance=provenance,
        freshness=freshness,
        availability=availability,
        kill_switch_state=str(kill_switch_state),
        veto_active=veto_active,
        reason_codes=tuple(str(code) for code in reason_codes),
    )


def project_economic_summary_snapshot_v1(
    *,
    economic_viability_status: str,
    economic_validity_proven: bool,
    profitability_claim_allowed: bool,
    policy_threshold_status: str,
    policy_version: str,
    authority_effect: str,
    runtime_effect: bool,
    order_effect: bool,
    reason_codes: Sequence[str],
    profit_factor: Mapping[str, Any],
    net_return: Mapping[str, Any],
    max_drawdown: Mapping[str, Any],
    sharpe: Mapping[str, Any],
    trade_count: Mapping[str, Any],
    funding_drag: Mapping[str, Any],
    contract_version: str,
    owner: str,
    strategy_id: str,
    strategy_version: str,
    config_digest: str,
    implementation_digest: str,
    data_digest: str,
    manifest_digest: str,
    wiring_chain_digest: str,
    policy_digest: str,
    generated_at: datetime,
    source_reference: str | None,
    evidence_ref: str | None = None,
    evidence_digest: str | None = None,
    git_sha: str | None = None,
    producer_module: str = "backtest.economic_viability_evidence_v1",
    source_kind: str = "economic_viability_evidence_v1",
    effective_at: datetime | None = None,
    availability: Availability = Availability.AVAILABLE,
    max_age_seconds: int | None = None,
    is_stale: bool = False,
    stale_reason: str | None = None,
) -> EconomicSummarySnapshotV1:
    """Project already-selected EconomicViabilityEvidenceV1 fields field-for-field.

    Forbidden: recomputing metrics, synthesizing PASS/FAIL, mapping promotion
    gate status, inferring lifecycle labels, or selecting among evidence instances.
    generated_at/effective_at must be producer timestamps — never page-assembly time.
    """
    if not economic_viability_status:
        raise ValueError("economic_viability_status required for AVAILABLE/STALE")
    if not isinstance(economic_validity_proven, bool):
        raise TypeError("economic_validity_proven must be bool")
    if not isinstance(profitability_claim_allowed, bool):
        raise TypeError("profitability_claim_allowed must be bool")
    if not isinstance(runtime_effect, bool):
        raise TypeError("runtime_effect must be bool")
    if not isinstance(order_effect, bool):
        raise TypeError("order_effect must be bool")
    if availability not in (Availability.AVAILABLE, Availability.STALE):
        raise ValueError("project_economic_summary only emits AVAILABLE or STALE")
    if availability is Availability.AVAILABLE and is_stale:
        raise ValueError("AVAILABLE cannot be stale")
    if availability is Availability.STALE and not is_stale:
        raise ValueError("STALE requires is_stale=True")
    schema_id = f"{SCHEMA_FAMILY}.economic_summary.{SCHEMA_VERSION}"
    provenance = SnapshotProvenanceV1(
        schema_id=schema_id,
        schema_version=SCHEMA_VERSION,
        producer_module=producer_module,
        generated_at=generated_at,
        effective_at=generated_at if effective_at is None else effective_at,
        source_kind=source_kind,
        source_reference=source_reference,
        evidence_digest=evidence_digest,
        git_sha=git_sha,
        availability=availability,
    )
    freshness = FreshnessV1(
        observed_at=generated_at,
        max_age_seconds=max_age_seconds,
        is_stale=is_stale,
        stale_reason=stale_reason,
    )
    return EconomicSummarySnapshotV1(
        schema_id=schema_id,
        schema_version=SCHEMA_VERSION,
        provenance=provenance,
        freshness=freshness,
        availability=availability,
        economic_viability_status=str(economic_viability_status),
        economic_validity_proven=economic_validity_proven,
        profitability_claim_allowed=profitability_claim_allowed,
        policy_threshold_status=str(policy_threshold_status),
        policy_version=str(policy_version),
        authority_effect=str(authority_effect),
        runtime_effect=runtime_effect,
        order_effect=order_effect,
        reason_codes=tuple(str(code) for code in reason_codes),
        profit_factor=dict(profit_factor),
        net_return=dict(net_return),
        max_drawdown=dict(max_drawdown),
        sharpe=dict(sharpe),
        trade_count=dict(trade_count),
        funding_drag=dict(funding_drag),
        evidence_ref=None if evidence_ref is None else str(evidence_ref),
        contract_version=str(contract_version),
        owner=str(owner),
        strategy_id=str(strategy_id),
        strategy_version=str(strategy_version),
        config_digest=str(config_digest),
        implementation_digest=str(implementation_digest),
        data_digest=str(data_digest),
        manifest_digest=str(manifest_digest),
        wiring_chain_digest=str(wiring_chain_digest),
        policy_digest=str(policy_digest),
    )


def project_risk_sizing_capital_snapshot_v1(
    *,
    risk_status: str,
    sizing_status: str,
    capital_status: str,
    reason_codes: Sequence[str],
    generated_at: datetime,
    source_reference: str | None,
    quantity: float | None = None,
    evidence_digest: str | None = None,
    git_sha: str | None = None,
    producer_module: str = (
        "trading.master_v2.capital_risk_sizing_offline_replay_binding_adapter_v0"
    ),
    source_kind: str = "capital_risk_sizing_offline_replay_binding",
    effective_at: datetime | None = None,
    availability: Availability = Availability.AVAILABLE,
    max_age_seconds: int | None = None,
    is_stale: bool = False,
    stale_reason: str | None = None,
) -> RiskSizingCapitalSnapshotV1:
    """Project already-selected Risk/Sizing/Capital fields field-for-field.

    Forbidden: evaluating capital_risk_sizing_v1, inventing quantity/limits,
    merging unrelated sources, or labeling dashboard projection as authority.
    quantity is retained only when AVAILABLE (contract forbids quantity on
    non-AVAILABLE availability, including STALE).
    """
    if not risk_status:
        raise ValueError("risk_status required for AVAILABLE/STALE")
    if not sizing_status:
        raise ValueError("sizing_status required for AVAILABLE/STALE")
    if not capital_status:
        raise ValueError("capital_status required for AVAILABLE/STALE")
    if availability not in (Availability.AVAILABLE, Availability.STALE):
        raise ValueError("project_risk_sizing_capital only emits AVAILABLE or STALE")
    if availability is Availability.AVAILABLE and is_stale:
        raise ValueError("AVAILABLE cannot be stale")
    if availability is Availability.STALE and not is_stale:
        raise ValueError("STALE requires is_stale=True")
    if availability is not Availability.AVAILABLE:
        quantity = None
    schema_id = f"{SCHEMA_FAMILY}.risk_sizing_capital.{SCHEMA_VERSION}"
    provenance = SnapshotProvenanceV1(
        schema_id=schema_id,
        schema_version=SCHEMA_VERSION,
        producer_module=producer_module,
        generated_at=generated_at,
        effective_at=generated_at if effective_at is None else effective_at,
        source_kind=source_kind,
        source_reference=source_reference,
        evidence_digest=evidence_digest,
        git_sha=git_sha,
        availability=availability,
    )
    freshness = FreshnessV1(
        observed_at=generated_at,
        max_age_seconds=max_age_seconds,
        is_stale=is_stale,
        stale_reason=stale_reason,
    )
    return RiskSizingCapitalSnapshotV1(
        schema_id=schema_id,
        schema_version=SCHEMA_VERSION,
        provenance=provenance,
        freshness=freshness,
        availability=availability,
        risk_status=str(risk_status),
        sizing_status=str(sizing_status),
        capital_status=str(capital_status),
        reason_codes=tuple(str(code) for code in reason_codes),
        quantity=None if quantity is None else float(quantity),
    )


def project_execution_reconciliation_snapshot_v1(
    *,
    execution_status: str,
    reason_codes: Sequence[str],
    generated_at: datetime,
    source_reference: str | None,
    reconciliation_status: str | None = None,
    order_intent_ref: str | None = None,
    evidence_digest: str | None = None,
    git_sha: str | None = None,
    producer_module: str = (
        "trading.master_v2.canonical_order_intent_offline_replay_binding_adapter_v0"
    ),
    source_kind: str = "canonical_order_intent_offline_replay_binding",
    effective_at: datetime | None = None,
    availability: Availability = Availability.AVAILABLE,
    max_age_seconds: int | None = None,
    is_stale: bool = False,
    stale_reason: str | None = None,
) -> ExecutionReconciliationSnapshotV1:
    """Project already-selected Execution/Reconciliation fields field-for-field.

    Forbidden: building order intents, calling execution/order APIs, mutating
    reconciliation, or inventing pipeline/health status. reconciliation_status
    and order_intent_ref may remain None when the injected producer omitted them
    (partial source — never fabricated).
    """
    if not execution_status:
        raise ValueError("execution_status required for AVAILABLE/STALE")
    if availability not in (Availability.AVAILABLE, Availability.STALE):
        raise ValueError("project_execution_reconciliation only emits AVAILABLE or STALE")
    if availability is Availability.AVAILABLE and is_stale:
        raise ValueError("AVAILABLE cannot be stale")
    if availability is Availability.STALE and not is_stale:
        raise ValueError("STALE requires is_stale=True")
    schema_id = f"{SCHEMA_FAMILY}.execution_reconciliation.{SCHEMA_VERSION}"
    provenance = SnapshotProvenanceV1(
        schema_id=schema_id,
        schema_version=SCHEMA_VERSION,
        producer_module=producer_module,
        generated_at=generated_at,
        effective_at=generated_at if effective_at is None else effective_at,
        source_kind=source_kind,
        source_reference=source_reference,
        evidence_digest=evidence_digest,
        git_sha=git_sha,
        availability=availability,
    )
    freshness = FreshnessV1(
        observed_at=generated_at,
        max_age_seconds=max_age_seconds,
        is_stale=is_stale,
        stale_reason=stale_reason,
    )
    return ExecutionReconciliationSnapshotV1(
        schema_id=schema_id,
        schema_version=SCHEMA_VERSION,
        provenance=provenance,
        freshness=freshness,
        availability=availability,
        execution_status=str(execution_status),
        reconciliation_status=(
            None if reconciliation_status is None else str(reconciliation_status)
        ),
        order_intent_ref=None if order_intent_ref is None else str(order_intent_ref),
        reason_codes=tuple(str(code) for code in reason_codes),
    )
