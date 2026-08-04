"""Reuse-before-new owner registry for Market Dashboard Landscape V2.

Maps dashboard projection slots to existing canonical producer modules.
This package is a consumer boundary only — it does not own trading truth.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping


@dataclass(frozen=True)
class CanonicalOwnerRefV1:
    """Pointer to an existing sole-authority producer (path + role)."""

    slot: str
    owner_module: str
    owner_symbol: str
    authority_class: str
    reuse_status: str  # REUSED | PROJECTION_ONLY | NOT_BOUND
    notes: str


# Phase-0 inventory (read-only): existing immutable contracts preferred over new truth.
CANONICAL_OWNER_REGISTRY_V1: tuple[CanonicalOwnerRefV1, ...] = (
    CanonicalOwnerRefV1(
        slot="market_instrument",
        owner_module="trading.master_v2.canonical_market_context_v1",
        owner_symbol="CanonicalMarketContextV1",
        authority_class="market_context",
        reuse_status="REUSED",
        notes=(
            "Phase 4.1: identity may also project from universe_selection "
            "selected_future when CanonicalMarketContext is not persisted for dashboard; "
            "OHLCV binds separately via okx_selected_instrument_ohlcv_readmodel.v1 "
            "(not this identity slot)."
        ),
    ),
    CanonicalOwnerRefV1(
        slot="universe_ranking",
        owner_module="webui.workflow_dashboard_readmodel_v1.universe_selection_contract_v1",
        owner_symbol="universe_selection_readmodel.v1",
        authority_class="universe_projection",
        reuse_status="REUSED",
        notes="Phase 4.1: Landscape binds verify-before-trust universe_selection_readmodel.v1.",
    ),
    CanonicalOwnerRefV1(
        slot="dynamic_scope",
        owner_module="trading.master_v2.canonical_scope_initialization_v1",
        owner_symbol="CanonicalScopeLifecycleState",
        authority_class="dynamic_scope",
        reuse_status="REUSED",
        notes=(
            "Phase 4.2 + CAPABILITY_PRESENTATION_DYNAMIC_SCOPE_PROJECTION_"
            "MATERIALIZER_AUTOBIND_V1: Landscape projects "
            "CanonicalScopeSnapshotV1 lifecycle identity only "
            "(scope_state/current_scope_ref[/next_scope_ref]); no scope "
            "initializer or transition calls; no invented next_scope_ref. "
            "Durable auto-bind via non-authoritative "
            "dynamic_scope_presentation_projection.v1 under archive root "
            "(materialized from durable dynamic_scope_state_v1.json); "
            "injection remains test-compatible; AUTHORITY_EFFECT=NONE. "
            "Regime/Bull-Bear/Switch bind via separate slot "
            "regime_bull_bear_switch."
        ),
    ),
    CanonicalOwnerRefV1(
        slot="regime_bull_bear_switch",
        owner_module="trading.master_v2.double_play_state",
        owner_symbol="SideState+transition_state/TransitionDecision",
        authority_class="regime_bull_bear_switch",
        reuse_status="REUSED",
        notes=(
            "Phase 4.2B + CAPABILITY_PRESENTATION_BULL_BEAR_REGIME_PROJECTION_"
            "MATERIALIZER_V1: Regime fields project from "
            "suitability_binding_v1 (regime_id/regime_status). Bull/Bear "
            "projects SideState exactly. Switch projects "
            "StateSwitchEvidenceV1 / TransitionDecision fields "
            "(previous/next side, scope_event_type, transition_allowed, "
            "transition_reason_code). No transition_state calls; no "
            "SideState derivation; contradictory side fields fail closed. "
            "Durable auto-bind via non-authoritative "
            "bull_bear_regime_presentation_projection.v1 under archive root; "
            "injection remains test-compatible; AUTHORITY_EFFECT=NONE."
        ),
    ),
    CanonicalOwnerRefV1(
        slot="canonical_decision",
        owner_module="trading.master_v2.canonical_trading_decision_evidence_v1",
        owner_symbol="CanonicalTradingDecisionEvidenceV1",
        authority_class="decision",
        reuse_status="REUSED",
        notes=(
            "Phase 4.3A + CAPABILITY_PRESENTATION_CANONICAL_DECISION_AUTOBIND_V1: "
            "Landscape projects CanonicalTradingDecisionEvidenceV1 "
            "field-for-field (decision_outcome/next_direction_state/reason_codes/"
            "decision_id); blockers remain empty (no direct evidence field); "
            "no recomputation; Double Play is a separate Phase 4.3B slot. "
            "Durable auto-bind via non-authoritative "
            "canonical_decision_presentation_projection.v1 under archive root; "
            "injection remains test-compatible; AUTHORITY_EFFECT=NONE."
        ),
    ),
    CanonicalOwnerRefV1(
        slot="double_play",
        owner_module="trading.master_v2.double_play_dashboard_display",
        owner_symbol="DoublePlayDashboardDisplaySnapshot",
        authority_class="double_play",
        reuse_status="REUSED",
        notes=(
            "Phase 4.3B + CAPABILITY_PRESENTATION_DOUBLE_PLAY_AUTOBIND_V1: "
            "Landscape projects DoublePlayDashboardDisplaySnapshot "
            "field-for-field (overall_status/panel_summaries/blockers); "
            "display_only=True; live_authorization=False; no compose/build calls; "
            "pending/armed remain unbound (not on display snapshot). "
            "Durable auto-bind via non-authoritative "
            "double_play_presentation_projection.v1 under archive root; "
            "injection remains test-compatible; AUTHORITY_EFFECT=NONE."
        ),
    ),
    CanonicalOwnerRefV1(
        slot="risk_sizing_capital",
        owner_module="trading.master_v2.capital_risk_sizing_offline_replay_binding_adapter_v0",
        owner_symbol="capital_risk_sizing_offline_replay_binding",
        authority_class="risk_sizing",
        reuse_status="REUSED",
        notes=(
            "Phase 4.4B + CAPABILITY_PRESENTATION_RISK_SIZING_CAPITAL_"
            "PROJECTION_MATERIALIZER_AUTOBIND_V1: Landscape projects "
            "Risk/Sizing/Capital fields field-for-field "
            "(risk_status/sizing_status/capital_status/quantity/reason_codes); "
            "authority owner remains src.governance.capital_risk_sizing_v1; "
            "offline replay adapter is non-authority wiring/parity only; "
            "dashboard AUTHORITY_EFFECT=NONE; durable auto-bind via "
            "non-authoritative risk_sizing_capital_presentation_projection.v1 "
            "under archive root; injection remains test-compatible; without "
            "injection/projection MISSING_SOURCE; never call capital/risk/"
            "sizing evaluators or invent quantity."
        ),
    ),
    CanonicalOwnerRefV1(
        slot="safety_authority",
        owner_module="src.risk_layer.kill_switch",
        owner_symbol="KillSwitch",
        authority_class="safety_veto",
        reuse_status="REUSED",
        notes=(
            "Phase 4.4A + CAPABILITY_PRESENTATION_SAFETY_AUTHORITY_"
            "PROJECTION_MATERIALIZER_AUTOBIND_V1: Landscape projects "
            "KillSwitch/boundary fields field-for-field "
            "(kill_switch_state/veto_active/reason_codes); "
            "authority owner remains src.risk_layer.kill_switch; "
            "projection/evidence source "
            "trading.master_v2.killswitch_boundary_offline_replay_binding_adapter_v0 "
            "is non-authority wiring/parity only; dashboard AUTHORITY_EFFECT=NONE; "
            "durable auto-bind via non-authoritative "
            "safety_authority_presentation_projection.v1 persisted at "
            "readmodels/safety_authority.v1.json under archive root; "
            "explicit injection remains priority over archive autobind; "
            "without injection/projection MISSING_SOURCE; "
            "no trigger/recover; no offline evaluator; "
            "no productive KillSwitch state-file autoload "
            "(never live data/kill_switch/state.json)."
        ),
    ),
    CanonicalOwnerRefV1(
        slot="execution_reconciliation",
        owner_module="trading.master_v2.canonical_order_intent_offline_replay_binding_adapter_v0",
        owner_symbol="canonical_order_intent_offline_replay_binding",
        authority_class="execution_intent",
        reuse_status="REUSED",
        notes=(
            "Phase 4.5 + CAPABILITY_PRESENTATION_EXECUTION_RECONCILIATION_"
            "PROJECTION_MATERIALIZER_AUTOBIND_V1: Landscape projects "
            "Execution/Reconciliation fields field-for-field "
            "(execution_status/reconciliation_status/order_intent_ref/reason_codes); "
            "authority owner remains src.governance.canonical_order_intent_v1; "
            "offline replay adapter is non-authority wiring/parity only; "
            "dashboard AUTHORITY_EFFECT=NONE; durable auto-bind via "
            "non-authoritative execution_reconciliation_presentation_projection.v1 "
            "under archive root; injection remains test-compatible; without "
            "injection/projection MISSING_SOURCE; reconciliation_status may be "
            "absent (partial) and must not be invented; never import "
            "order/execution mutation APIs or call build_canonical_order_intent_v1 "
            "/ evaluate_offline_reconciliation_*."
        ),
    ),
    CanonicalOwnerRefV1(
        slot="economic_summary",
        owner_module="backtest.economic_viability_evidence_v1",
        owner_symbol="EconomicViabilityEvidenceV1",
        authority_class="economic_evidence",
        reuse_status="REUSED",
        notes=(
            "Phase 4.6B + CAPABILITY_PRESENTATION_ECONOMIC_SUMMARY_"
            "PROJECTION_MATERIALIZER_AUTOBIND_V1: Landscape projects "
            "EconomicViabilityEvidenceV1 field-for-field "
            "(economic_viability_status=status enum value; "
            "economic_validity_proven/policy_threshold_status/metrics/digests); "
            "AUTHORITY_EFFECT=NONE; durable auto-bind via non-authoritative "
            "economic_summary_presentation_projection.v1 under archive root; "
            "explicit injection only remains priority over archive autobind; "
            "without injection/projection MISSING_SOURCE; "
            "no filesystem/registry/latest selector; "
            "promotion_economic_gate_v1 remains a separate owner; lifecycle "
            "labels ABSENT (not inferred)."
        ),
    ),
    CanonicalOwnerRefV1(
        slot="autonomy_stage",
        owner_module="NONE",
        owner_symbol="NONE",
        authority_class="autonomy",
        reuse_status="NOT_BOUND",
        notes=(
            "Phase 4.7B OPTION_D closeout: autonomy_stage remains NOT_BOUND; "
            "no canonical productive Autonomy State aggregate required; "
            "sole owner/producer/contract=NONE; Autonomy stages 0–7 are "
            "docs-only informative review vocabulary (not productive "
            "operational state); AUTHORITY_EFFECT=NONE; runtime bridge status "
            "(BOUND_NOT_ACTIVATED / CANONICAL_RUNTIME_ENTRYPOINT_STATUS) is a "
            "separate fact and NON_SOURCE for autonomy_stage; "
            "RuntimeBridgePreActivationGate, promotion_economic_gate_v1, "
            "KillSwitch, scheduler/worker, and WorkflowDashboardReadModelV1 "
            "MUST NOT be named as autonomy_stage owner/source; "
            "cross-source synthesis into Autonomy state unauthorized; "
            "dashboard cannot own or infer Autonomy state; "
            "binding/producer/contract/adapter/injection authorized=false."
        ),
    ),
    CanonicalOwnerRefV1(
        slot="diagnostics_summary",
        owner_module="UNRESOLVED",
        owner_symbol="UNRESOLVED",
        authority_class="diagnostics",
        reuse_status="NOT_BOUND",
        notes=(
            "Phase 4.6C OPTION_A_KEEP_NOT_BOUND ratified: diagnostics_summary "
            "remains NOT_BOUND; sole owner UNRESOLVED; implementation authorized="
            "false; typed injection authorized=false; consumer-contract redesign "
            "required before any future binding; WorkflowDashboardReadModelV1 is "
            "NON_SOURCE/PROJECTION_ONLY and MUST NOT be named as diagnostics "
            "owner/source; summary is unresolved/presenter-oriented semantics "
            "until a separate redesign is ratified; OPTION_B_NEW_DOMAIN_NEUTRAL_"
            "DIAGNOSTICS_EVIDENCE rejected; OPTION_D_SOURCE_HEALTH_ONLY rejected; "
            "OPTION_C_MULTIPLE_DOMAIN_SPECIFIC_DIAGNOSTICS deferred to a separate "
            "operator-authorized redesign phase (not this PR)."
        ),
    ),
    CanonicalOwnerRefV1(
        slot="source_health",
        owner_module="webui.market_dashboard_landscape_v2.source_health",
        owner_symbol="DashboardSourceHealthSnapshotV1",
        authority_class="dashboard_aggregation",
        reuse_status="REUSED",
        notes="Aggregation-only; never invents per-slot truth.",
    ),
)


def owner_registry_by_slot() -> Mapping[str, CanonicalOwnerRefV1]:
    return {entry.slot: entry for entry in CANONICAL_OWNER_REGISTRY_V1}


REQUIRED_PROJECTION_SLOTS: tuple[str, ...] = tuple(
    entry.slot for entry in CANONICAL_OWNER_REGISTRY_V1
)
