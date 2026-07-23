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
        notes="Immutable decision evidence projected field-for-field; no recomputation.",
    ),
    CanonicalOwnerRefV1(
        slot="double_play",
        owner_module="trading.master_v2.double_play_dashboard_display",
        owner_symbol="DoublePlayDashboardDisplaySnapshot",
        authority_class="double_play",
        reuse_status="REUSED",
        notes="Existing DP display snapshot; Landscape wraps with Availability/provenance.",
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
        owner_module="trading.master_v2.killswitch_boundary_offline_replay_binding_adapter_v0",
        owner_symbol="killswitch_boundary_offline_replay_binding",
        authority_class="safety_veto",
        reuse_status="NOT_BOUND",
        notes="Safety remains independent veto; Landscape unbound until PR5.",
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
        owner_symbol="economic_viability_evidence",
        authority_class="economic_evidence",
        reuse_status="NOT_BOUND",
        notes="Promotion-only economic evidence; Landscape unbound until PR6.",
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
        owner_module="webui.workflow_dashboard_readmodel_v1.types",
        owner_symbol="WorkflowDashboardReadModelV1",
        authority_class="diagnostics",
        reuse_status="PROJECTION_ONLY",
        notes="Observability diagnostics reused as reference; no second owner.",
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
