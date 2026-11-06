"""Phase-8.1 / S1 policy checklist (read-only, fail-closed, non-activating).

Each row is the S1 policy binding for the current single-future runtime.
Multi-future numeric expansion remains unauthorized and is not required
to close S1. Name collision with later S2–S6 work is not S1 proof.
"""

from __future__ import annotations

from src.ops.canonical_r6_phase_8_1_policy_precondition_v1.models_v1 import (
    PolicyChecklistRowV1,
    PolicyItemStatus,
    R6Phase81PolicyError,
)

_CP = PolicyItemStatus.CLOSED_PROVEN
_NRS = PolicyItemStatus.NOT_REQUIRED_AT_THIS_STAGE

REQUIRED_ITEM_IDS = (
    "active_set_top_n_semantics",
    "promotion_demotion_semantics",
    "hysteresis",
    "cooldown",
    "open_position_treatment",
    "global_risk_caps",
    "per_instrument_risk_caps",
    "portfolio_concentration",
    "correlation_handling",
    "component_portfolio_var_ownership",
    "state_isolation_per_instrument",
    "deterministic_intent_arbitration",
    "exactly_one_global_execution_writer",
    "exactly_one_global_accounting_writer",
    "per_instrument_reconciliation",
    "restart_recovery_semantics",
    "kill_switch_semantics",
    "stale_unknown_handling",
    "fail_closed_behavior",
    "evidence_experiment_identity",
    "promotion_demotion_evidence_requirements",
    "no_silent_g13_bypass",
    "no_automatic_stage_progression",
)


def _row(
    item_id: str,
    *,
    status: PolicyItemStatus,
    current_binding: str,
    owner: str,
    mf_expansion: str,
) -> PolicyChecklistRowV1:
    return PolicyChecklistRowV1(
        item_id=item_id,
        status=status,
        current_binding=current_binding,
        owner=owner,
        mf_expansion=mf_expansion,
    )


S1_CHECKLIST: tuple[PolicyChecklistRowV1, ...] = (
    _row(
        "active_set_top_n_semantics",
        status=_CP,
        current_binding="active_set_size=1; TOP_N_ACTIVE_SET_AUTHORITY=false; Top-20 is ranking candidate context only",
        owner="ops.single_selected_future_policy_v1 + ops.productive_futures_ranking_producer_v1",
        mf_expansion="N>1_unratified_NOT_REQUIRED_AT_S1",
    ),
    _row(
        "promotion_demotion_semantics",
        status=_CP,
        current_binding="UQ7 manual_only; G14 non-authoritative until promotion; no MF activeset promo",
        owner="UQ7 + G14 + Cap2.3 replacement_pending is instrument replacement not learning promo",
        mf_expansion="activeset_promo_BLOCKED_BY_SEPARATE_OWNER_GO_S6",
    ),
    _row(
        "hysteresis",
        status=_CP,
        current_binding="Cap2.3 DEFAULT_HYSTERESIS_RANK_IMPROVEMENT=1 applies only to N=1 replacement",
        owner="ops.single_selected_future_policy_v1",
        mf_expansion="MF_hysteresis_numerics_unratified_NOT_REQUIRED_AT_S1",
    ),
    _row(
        "cooldown",
        status=_CP,
        current_binding="Cap2.3 DEFAULT_MIN_HOLDING_PERIOD_SECONDS=3600 applies only to N=1 holding",
        owner="ops.single_selected_future_policy_v1",
        mf_expansion="MF_cooldown_numerics_unratified_NOT_REQUIRED_AT_S1",
    ),
    _row(
        "open_position_treatment",
        status=_CP,
        current_binding="Cap2.3 REPLACEMENT_PENDING; no second concurrent instrument",
        owner="ops.single_selected_future_policy_v1",
        mf_expansion="MF_open_position_matrix_unratified_NOT_REQUIRED_AT_S1",
    ),
    _row(
        "global_risk_caps",
        status=_CP,
        current_binding="single-future risk owners remain in force; MF global budget unratified and unused",
        owner="canonical risk/safety path + MAX_POSITIONS_EFFECTIVE=1",
        mf_expansion="MF_global_budget_NOT_REQUIRED_AT_S1",
    ),
    _row(
        "per_instrument_risk_caps",
        status=_CP,
        current_binding="the single selected future is the only in-scope instrument",
        owner="ops.single_selected_future_runtime_binding_v1",
        mf_expansion="per_instrument_MF_caps_NOT_REQUIRED_AT_S1",
    ),
    _row(
        "portfolio_concentration",
        status=_CP,
        current_binding="N=1 implies 100% concentration; MF concentration limits unused",
        owner="PHASE1_MAX_OPEN_POSITIONS=1",
        mf_expansion="MF_concentration_limits_NOT_REQUIRED_AT_S1",
    ),
    _row(
        "correlation_handling",
        status=_NRS,
        current_binding="no concurrent multi-instrument set; correlation policy not an S1 unlock input",
        owner="S2_I85_I74",
        mf_expansion="S2_portfolio_risk_contracts",
    ),
    _row(
        "component_portfolio_var_ownership",
        status=_NRS,
        current_binding="I85/I74 deferred; not S1 policy-frame; must not be treated as present VaR authority",
        owner="I85 + I74 + R7",
        mf_expansion="S2_then_R7",
    ),
    _row(
        "state_isolation_per_instrument",
        status=_CP,
        current_binding="single selected future runtime context; no second instrument state writer",
        owner="ops.single_selected_future_runtime_binding_v1",
        mf_expansion="per_instrument_context_graph_is_S3",
    ),
    _row(
        "deterministic_intent_arbitration",
        status=_CP,
        current_binding="N=1 makes arbitration trivial; no competing instrument intents authorized",
        owner="Cap7.2 simulated execution + Cap2.4 binding",
        mf_expansion="MF_arbitration_is_S3",
    ),
    _row(
        "exactly_one_global_execution_writer",
        status=_CP,
        current_binding="canonical simulated execution port; no second execution writer authorized",
        owner="ops.single_future_stateful_no_order_runtime_activation_v1",
        mf_expansion="must_preserve_single_exec_writer_at_S3",
    ),
    _row(
        "exactly_one_global_accounting_writer",
        status=_CP,
        current_binding="productive_futures_accounting_portfolio_writer_v1 is the accounting writer",
        owner="ops.productive_futures_accounting_runtime_binding_v1",
        mf_expansion="must_preserve_single_accounting_writer_at_S3",
    ),
    _row(
        "per_instrument_reconciliation",
        status=_CP,
        current_binding="Cap1.1 productive recon; PHASE1_MAX_OPEN_POSITIONS=1",
        owner="ops.productive_reconciliation_runtime_binding_v1",
        mf_expansion="per_instrument_MF_recon_is_S3_S4",
    ),
    _row(
        "restart_recovery_semantics",
        status=_CP,
        current_binding="Cap6.4 decision-path restart proven for single-future no-order scope",
        owner="ops.full_decision_path_atomic_restart_closure_v1 + Cap2.3 restart",
        mf_expansion="MF_restart_matrix_is_S3",
    ),
    _row(
        "kill_switch_semantics",
        status=_CP,
        current_binding="MF kill path not authorized; live kill I29 remains later; no G13 bypass via kill",
        owner="I29 + Cap11 kill evidence (testnet/live later)",
        mf_expansion="MF_kill_interactions_are_S2_S5",
    ),
    _row(
        "stale_unknown_handling",
        status=_CP,
        current_binding="Cap2.3 fail-closed on stale ranking / unknown eligibility; SELECTED_DEGRADED/NO_SELECTION",
        owner="ops.single_selected_future_policy_v1",
        mf_expansion="MF_stale_matrix_NOT_REQUIRED_AT_S1",
    ),
    _row(
        "fail_closed_behavior",
        status=_CP,
        current_binding="AUTHORIZED=false; MAX_POSITIONS_EFFECTIVE=1; orders/live/testnet/canary false",
        owner="Master §2.2 + Cap2.3/2.4/7.2 constants",
        mf_expansion="must_remain_fail_closed_until_S5_GO",
    ),
    _row(
        "evidence_experiment_identity",
        status=_CP,
        current_binding="Package-N SHA256 join CLOSED_PROVEN; MD5-12 not canonical; no MF identity plane",
        owner="EG-I82-JOIN + I17 named-lane (distinct from MF)",
        mf_expansion="MF_session_identity_is_S4_S5",
    ),
    _row(
        "promotion_demotion_evidence_requirements",
        status=_CP,
        current_binding="UQ7 evidence classes required; I17 PROMOTION_PASS=false; I67/I79 cannot substitute",
        owner="UQ7 + R4/R5 non-substitution",
        mf_expansion="MF_activeset_promo_evidence_is_S6",
    ),
    _row(
        "no_silent_g13_bypass",
        status=_CP,
        current_binding="G13=INTENTIONAL_SAFETY_BARRIER; MULTI_FUTURE_RUNTIME_AUTHORIZED=false",
        owner="Master G13 + Cap2.3/2.4/7.2 constants",
        mf_expansion="RB-G13 remains until staged evidence + per-stage GO",
    ),
    _row(
        "no_automatic_stage_progression",
        status=_CP,
        current_binding="UQ5 ratified: no stage authorizes the next automatically",
        owner="UQ5 / U-MF-S1",
        mf_expansion="PER_STAGE_GO required",
    ),
)


def require_item(item_id: str) -> PolicyChecklistRowV1:
    for row in S1_CHECKLIST:
        if row.item_id == item_id:
            return row
    raise R6Phase81PolicyError(f"unknown_s1_item:{item_id}")
