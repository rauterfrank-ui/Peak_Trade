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
            "OHLCV remains unbound."
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
            "Phase 4.2: Landscape projects CanonicalScopeSnapshotV1 lifecycle "
            "identity only (scope_state/current_scope_ref); Regime/Switch/"
            "RuntimeScopeState/transition_state remain unbound."
        ),
    ),
    CanonicalOwnerRefV1(
        slot="canonical_decision",
        owner_module="trading.master_v2.canonical_trading_decision_evidence_v1",
        owner_symbol="CanonicalTradingDecisionEvidenceV1",
        authority_class="decision",
        reuse_status="REUSED",
        notes=(
            "Phase 4.3A: Landscape projects CanonicalTradingDecisionEvidenceV1 "
            "field-for-field (decision_outcome/next_direction_state/reason_codes/"
            "decision_id); blockers remain empty (no direct evidence field); "
            "no recomputation; Double Play is a separate Phase 4.3B slot."
        ),
    ),
    CanonicalOwnerRefV1(
        slot="double_play",
        owner_module="trading.master_v2.double_play_dashboard_display",
        owner_symbol="DoublePlayDashboardDisplaySnapshot",
        authority_class="double_play",
        reuse_status="REUSED",
        notes=(
            "Phase 4.3B: Landscape projects DoublePlayDashboardDisplaySnapshot "
            "field-for-field (overall_status/panel_summaries/blockers); "
            "display_only=True; live_authorization=False; no compose/build calls; "
            "pending/armed remain unbound (not on display snapshot)."
        ),
    ),
    CanonicalOwnerRefV1(
        slot="risk_sizing_capital",
        owner_module="trading.master_v2.capital_risk_sizing_offline_replay_binding_adapter_v0",
        owner_symbol="capital_risk_sizing_offline_replay_binding",
        authority_class="risk_sizing",
        reuse_status="NOT_BOUND",
        notes="No Landscape projection binding yet; NOT_BOUND until PR5.",
    ),
    CanonicalOwnerRefV1(
        slot="safety_authority",
        owner_module="src.risk_layer.kill_switch",
        owner_symbol="KillSwitch",
        authority_class="safety_veto",
        reuse_status="REUSED",
        notes=(
            "Phase 4.4A: Landscape projects injected KillSwitch/boundary fields "
            "field-for-field (kill_switch_state/veto_active/reason_codes); "
            "authority owner remains src.risk_layer.kill_switch; "
            "projection/evidence source "
            "trading.master_v2.killswitch_boundary_offline_replay_binding_adapter_v0 "
            "is non-authority wiring/parity only; dashboard AUTHORITY_EFFECT=NONE; "
            "no trigger/recover; no offline evaluator; no live state-file autoload."
        ),
    ),
    CanonicalOwnerRefV1(
        slot="execution_reconciliation",
        owner_module="trading.master_v2.canonical_order_intent_offline_replay_binding_adapter_v0",
        owner_symbol="canonical_order_intent_offline_replay_binding",
        authority_class="execution_intent",
        reuse_status="NOT_BOUND",
        notes="Order/execution APIs must never be imported by Landscape UI.",
    ),
    CanonicalOwnerRefV1(
        slot="economic_summary",
        owner_module="backtest.economic_viability_evidence_v1",
        owner_symbol="EconomicViabilityEvidenceV1",
        authority_class="economic_evidence",
        reuse_status="REUSED",
        notes=(
            "Phase 4.6B: Landscape projects injected EconomicViabilityEvidenceV1 "
            "field-for-field (economic_viability_status=status enum value; "
            "economic_validity_proven/policy_threshold_status/metrics/digests); "
            "AUTHORITY_EFFECT=NONE; explicit injection only; without injection "
            "MISSING_SOURCE; no filesystem/registry/latest selector; "
            "promotion_economic_gate_v1 remains a separate owner; lifecycle "
            "labels ABSENT (not inferred)."
        ),
    ),
    CanonicalOwnerRefV1(
        slot="autonomy_stage",
        owner_module="trading.master_v2.runtime_bridge_pre_activation_gate_v0",
        owner_symbol="BOUND_NOT_ACTIVATED",
        authority_class="runtime_status",
        reuse_status="NOT_BOUND",
        notes="Runtime BOUND_NOT_ACTIVATED is intentional; display-only later.",
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
