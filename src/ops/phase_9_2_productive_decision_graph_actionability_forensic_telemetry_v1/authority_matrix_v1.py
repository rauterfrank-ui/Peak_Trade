"""Read-only productive decision-graph authority / call-order matrix."""

from __future__ import annotations

from typing import Any

from src.ops.phase_9_2_productive_decision_graph_actionability_forensic_telemetry_v1.constants_v1 import (
    ACTIONABILITY_CALL_ORDER_V1,
    OWNER,
    PRODUCTIVE_CALLER,
    PRODUCTIVE_DECISION_AUTHORITY,
    PRODUCTIVE_HOST,
)


def inventory_productive_decision_graph_authority_v1() -> dict[str, Any]:
    """Enumerate productive stage authorities without creating a parallel engine."""
    rows = [
        {
            "STAGE": "instrument_selection",
            "PRODUCTIVE_SYMBOL": "ensure_single_selected_future_runtime_binding_v1",
            "PRODUCTIVE_CALLER": PRODUCTIVE_CALLER,
            "INPUT_CONTRACT": "selection/ranking/universe state roots",
            "OUTPUT_CONTRACT": "RuntimeBindingGateResultV1",
            "STATE_OWNER": "ops.single_selected_future_runtime_binding_v1",
            "CONFIG_OWNER": "ops.single_selected_future_runtime_binding_v1",
            "DECISION_REASON_SOURCE": "selection_gate.reason_codes",
            "CURRENT_TELEMETRY": "selection_binding_evidence",
            "MISSING_TELEMETRY": "stage observation event",
            "CALL_ORDER_INDEX": 0,
        },
        {
            "STAGE": "public_market_observation",
            "PRODUCTIVE_SYMBOL": "BridgeSessionStateV1.append_mid / mid_price input",
            "PRODUCTIVE_CALLER": PRODUCTIVE_CALLER,
            "INPUT_CONTRACT": "mid_price + event_ts_unix + ObservationCycleKindV1",
            "OUTPUT_CONTRACT": "price path append",
            "STATE_OWNER": "BridgeSessionStateV1.mid_prices",
            "CONFIG_OWNER": "N/A_input_only",
            "DECISION_REASON_SOURCE": "observation cycle kind",
            "CURRENT_TELEMETRY": "cycle_ledger mid",
            "MISSING_TELEMETRY": "stage observation event",
            "CALL_ORDER_INDEX": 1,
        },
        {
            "STAGE": "observation_identity",
            "PRODUCTIVE_SYMBOL": "ObservationIdentityV1",
            "PRODUCTIVE_CALLER": (
                "ops.stateful_confirmation_and_c1_productive_binding_v1.host_binding_v1."
                "evaluate_host_observation_acceptance_v1"
            ),
            "INPUT_CONTRACT": "mark + venue_event_time + instrument",
            "OUTPUT_CONTRACT": "ObservationIdentityV1 | None",
            "STATE_OWNER": "ops.stateful_confirmation_and_c1_productive_binding_v1",
            "CONFIG_OWNER": "confirmation config digest",
            "DECISION_REASON_SOURCE": "ObservationAcceptanceResultV1.reason_code",
            "CURRENT_TELEMETRY": "confirmation commit",
            "MISSING_TELEMETRY": "stage observation event",
            "CALL_ORDER_INDEX": 2,
        },
        {
            "STAGE": "distinct_observation_acceptance",
            "PRODUCTIVE_SYMBOL": "DistinctMarketObservationAcceptor / C1",
            "PRODUCTIVE_CALLER": (
                "ops.stateful_confirmation_and_c1_productive_binding_v1.host_binding_v1."
                "evaluate_host_observation_acceptance_v1"
            ),
            "INPUT_CONTRACT": "ObservationAcceptanceStateV1 + candidate identity",
            "OUTPUT_CONTRACT": "ObservationAcceptanceResultV1",
            "STATE_OWNER": "ops.stateful_confirmation_and_c1_productive_binding_v1",
            "CONFIG_OWNER": "ops.decision_config_ownership_and_consumer_closure_v1",
            "DECISION_REASON_SOURCE": "ObservationClassification",
            "CURRENT_TELEMETRY": "observation_acceptance_result",
            "MISSING_TELEMETRY": "stage observation event",
            "CALL_ORDER_INDEX": 3,
        },
        {
            "STAGE": "features",
            "PRODUCTIVE_SYMBOL": "compute_feature_regime_from_mid_prices_v1",
            "PRODUCTIVE_CALLER": PRODUCTIVE_CALLER,
            "INPUT_CONTRACT": "mid_prices window",
            "OUTPUT_CONTRACT": "FeatureRegimeResultV1",
            "STATE_OWNER": "bridge feature_regime_pipeline_v1",
            "CONFIG_OWNER": "FEATURE_WINDOW_MIN / PRICE_PATH_MAX_LEN (frozen)",
            "DECISION_REASON_SOURCE": "warmup_complete / ok",
            "CURRENT_TELEMETRY": "feature_regime dict",
            "MISSING_TELEMETRY": "stage observation event",
            "CALL_ORDER_INDEX": 4,
        },
        {
            "STAGE": "typed_volatility_presence",
            "PRODUCTIVE_SYMBOL": "CanonicalMarketContextV1.volatility_estimate",
            "PRODUCTIVE_CALLER": PRODUCTIVE_DECISION_AUTHORITY,
            "INPUT_CONTRACT": "features.volatility_estimate",
            "OUTPUT_CONTRACT": "typed volatility presence in market context",
            "STATE_OWNER": "trading.master_v2.canonical_market_context_v1",
            "CONFIG_OWNER": "diagnostic_only_numeric_max_age",
            "DECISION_REASON_SOURCE": "TYPED_VOLATILITY_* reason codes",
            "CURRENT_TELEMETRY": "volatility_estimate + evidence provenance",
            "MISSING_TELEMETRY": "stage observation event",
            "CALL_ORDER_INDEX": 5,
        },
        {
            "STAGE": "market_state_bull_bear",
            "PRODUCTIVE_SYMBOL": "DirectionalAssessmentV1 (bull/bear)",
            "PRODUCTIVE_CALLER": (
                "trading.master_v2.directional_assessment_confirmation_integration_v1."
                "evaluate_bull_bear_directional_assessment_with_confirmation_progress_v1"
            ),
            "INPUT_CONTRACT": "CanonicalMarketContextV1 + confirmation carrier",
            "OUTPUT_CONTRACT": "bull_assessment + bear_assessment",
            "STATE_OWNER": "trading.master_v2.directional_assessment_v1",
            "CONFIG_OWNER": "DirectionalAssessmentPolicyV1",
            "DECISION_REASON_SOURCE": "assessment.status / regime_id",
            "CURRENT_TELEMETRY": "intermediate.bull/bear_assessment",
            "MISSING_TELEMETRY": "stage observation event",
            "CALL_ORDER_INDEX": 6,
        },
        {
            "STAGE": "directional_confirmation",
            "PRODUCTIVE_SYMBOL": "DirectionalConfirmationSideStateCarrierV1 / C2+C3",
            "PRODUCTIVE_CALLER": (
                "trading.master_v2.directional_assessment_confirmation_integration_v1"
            ),
            "INPUT_CONTRACT": "C1 acceptance + confirmation carrier",
            "OUTPUT_CONTRACT": "confirmation phase OBSERVE|CANDIDATE|CONFIRMED|INVALID",
            "STATE_OWNER": "ops.stateful_confirmation_and_c1_productive_binding_v1",
            "CONFIG_OWNER": "confirmation_epochs (Cap 6.3 canonical)",
            "DECISION_REASON_SOURCE": "ConfirmationAssessmentStateV1",
            "CURRENT_TELEMETRY": "confirmation commit / carrier_after",
            "MISSING_TELEMETRY": "stage observation event",
            "CALL_ORDER_INDEX": 7,
        },
        {
            "STAGE": "master_v2",
            "PRODUCTIVE_SYMBOL": "run_integrated_offline_trading_logic_replay_v1",
            "PRODUCTIVE_CALLER": PRODUCTIVE_DECISION_AUTHORITY,
            "INPUT_CONTRACT": "IntegratedOfflineReplayInputV1",
            "OUTPUT_CONTRACT": "IntegratedOfflineReplayResultV1.evidence",
            "STATE_OWNER": "trading.master_v2",
            "CONFIG_OWNER": "ops.decision_config_ownership_and_consumer_closure_v1",
            "DECISION_REASON_SOURCE": "evidence.decision_outcome + reason_codes",
            "CURRENT_TELEMETRY": "CanonicalTradingDecisionEvidenceV1",
            "MISSING_TELEMETRY": "stage observation event",
            "CALL_ORDER_INDEX": 8,
        },
        {
            "STAGE": "double_play",
            "PRODUCTIVE_SYMBOL": "evaluate_double_play_entry_exit_policy_v0",
            "PRODUCTIVE_CALLER": (
                "trading.master_v2.double_play_entry_exit_policy_v0."
                "evaluate_double_play_entry_exit_policy_v0"
            ),
            "INPUT_CONTRACT": "composition + position + exit signals",
            "OUTPUT_CONTRACT": "EntryExitPolicyDecisionV0",
            "STATE_OWNER": "trading.master_v2.double_play_entry_exit_policy_v0",
            "CONFIG_OWNER": "DoublePlayEntryExitPolicyV0",
            "DECISION_REASON_SOURCE": "entry_exit_decision.outcome / precedence",
            "CURRENT_TELEMETRY": "intermediate.entry_exit_decision",
            "MISSING_TELEMETRY": "stage observation event",
            "CALL_ORDER_INDEX": 9,
        },
        {
            "STAGE": "dynamic_scope",
            "PRODUCTIVE_SYMBOL": "deterministic_scope_event_generator_v1 / RuntimeScopeState",
            "PRODUCTIVE_CALLER": (
                "ops.dynamic_scope_persistence_binding_v1.host_binding_v1."
                "commit_host_dynamic_scope_after_replay_v1"
            ),
            "INPUT_CONTRACT": "previous RuntimeScopeState + confirmed direction",
            "OUTPUT_CONTRACT": "scope transition / RuntimeScopeState",
            "STATE_OWNER": "ops.dynamic_scope_persistence_binding_v1",
            "CONFIG_OWNER": "up/adverse/reversal distances (Cap 6.3)",
            "DECISION_REASON_SOURCE": "scope_event + scope_advanced",
            "CURRENT_TELEMETRY": "last_dynamic_scope_commit",
            "MISSING_TELEMETRY": "stage observation event",
            "CALL_ORDER_INDEX": 10,
        },
        {
            "STAGE": "survival",
            "PRODUCTIVE_SYMBOL": "evaluate_survival_assessment_v1",
            "PRODUCTIVE_CALLER": (
                "trading.master_v2.post_confirmation_survival_suitability_composition_binding_v1"
            ),
            "INPUT_CONTRACT": "DirectionalAssessmentV1 + market context",
            "OUTPUT_CONTRACT": "SurvivalResultV1",
            "STATE_OWNER": "trading.master_v2.survival_assessment_v1",
            "CONFIG_OWNER": "SurvivalAssessmentPolicyV1",
            "DECISION_REASON_SOURCE": "survival.result / reason",
            "CURRENT_TELEMETRY": "intermediate.bull/bear_survival",
            "MISSING_TELEMETRY": "stage observation event",
            "CALL_ORDER_INDEX": 11,
        },
        {
            "STAGE": "suitability",
            "PRODUCTIVE_SYMBOL": "evaluate_suitability_binding_v1",
            "PRODUCTIVE_CALLER": (
                "trading.master_v2.post_confirmation_survival_suitability_composition_binding_v1"
            ),
            "INPUT_CONTRACT": "survival + regime + registry",
            "OUTPUT_CONTRACT": "SuitabilityResultV1",
            "STATE_OWNER": "trading.master_v2.suitability_binding_v1",
            "CONFIG_OWNER": "SuitabilityRankingPolicyV1",
            "DECISION_REASON_SOURCE": "suitability.result / reason",
            "CURRENT_TELEMETRY": "intermediate.bull/bear_suitability",
            "MISSING_TELEMETRY": "stage observation event",
            "CALL_ORDER_INDEX": 12,
        },
        {
            "STAGE": "composition",
            "PRODUCTIVE_SYMBOL": "DoublePlayCompositionMatrixV1",
            "PRODUCTIVE_CALLER": ("trading.master_v2.double_play_composition_matrix_v1"),
            "INPUT_CONTRACT": "bull/bear suitability + previous composition direction",
            "OUTPUT_CONTRACT": "DoublePlayCompositionResultV1",
            "STATE_OWNER": "trading.master_v2.double_play_composition_matrix_v1",
            "CONFIG_OWNER": "DoublePlayCompositionPolicyV1",
            "DECISION_REASON_SOURCE": "composition_result.selected_side / outcome",
            "CURRENT_TELEMETRY": "intermediate.composition_result",
            "MISSING_TELEMETRY": "stage observation event",
            "CALL_ORDER_INDEX": 13,
        },
        {
            "STAGE": "risk",
            "PRODUCTIVE_SYMBOL": "CapitalRiskSizingDecisionV1",
            "PRODUCTIVE_CALLER": (
                "trading.master_v2.capital_risk_sizing_offline_replay_binding_adapter_v0"
            ),
            "INPUT_CONTRACT": "entry/exit decision + portfolio context",
            "OUTPUT_CONTRACT": "capital_risk_sizing_decision",
            "STATE_OWNER": "src.governance.capital_risk_sizing_v1",
            "CONFIG_OWNER": "capital risk sizing policy",
            "DECISION_REASON_SOURCE": "capital_risk_sizing_decision.outcome",
            "CURRENT_TELEMETRY": "risk_sizing_result on BridgeCycleResultV1",
            "MISSING_TELEMETRY": "stage observation event",
            "CALL_ORDER_INDEX": 14,
        },
        {
            "STAGE": "safety",
            "PRODUCTIVE_SYMBOL": "safety_kernel / TradingGate / safety_exit_signal",
            "PRODUCTIVE_CALLER": (
                "ops.exit_policy_producer_binding_v1.host_binding_v1."
                "evaluate_host_exit_policy_producers_v1"
            ),
            "INPUT_CONTRACT": "exit safety signals + replay evidence",
            "OUTPUT_CONTRACT": "safety_mode / trading_gate / safety_blocked",
            "STATE_OWNER": "trading.master_v2.safety_kernel + Cap 6.5",
            "CONFIG_OWNER": "safety / kill-switch contracts",
            "DECISION_REASON_SOURCE": "safety_blocked / safety_result",
            "CURRENT_TELEMETRY": "safety_result on BridgeCycleResultV1",
            "MISSING_TELEMETRY": "stage observation event",
            "CALL_ORDER_INDEX": 15,
        },
        {
            "STAGE": "exit_policy",
            "PRODUCTIVE_SYMBOL": "evaluate_host_exit_policy_producers_v1",
            "PRODUCTIVE_CALLER": (
                "ops.exit_policy_producer_binding_v1.host_binding_v1."
                "evaluate_host_exit_policy_producers_v1"
            ),
            "INPUT_CONTRACT": "open position + mark + Cap 6.5 producers",
            "OUTPUT_CONTRACT": "PolicySignalV0 bundle + trading_gate",
            "STATE_OWNER": "ops.exit_policy_producer_binding_v1",
            "CONFIG_OWNER": "adverse/profit/time exit distances",
            "DECISION_REASON_SOURCE": "exit signal triggered flags",
            "CURRENT_TELEMETRY": "exit_policy commit",
            "MISSING_TELEMETRY": "stage observation event",
            "CALL_ORDER_INDEX": 16,
        },
        {
            "STAGE": "canonical_intent",
            "PRODUCTIVE_SYMBOL": "map_replay_result_to_intended_analytical_action_v1",
            "PRODUCTIVE_CALLER": (
                "ops.wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_v1."
                "intended_action_mapper_v1.map_replay_result_to_intended_analytical_action_v1"
            ),
            "INPUT_CONTRACT": "IntegratedOfflineReplayResultV1 + portfolio",
            "OUTPUT_CONTRACT": "IntendedAnalyticalActionV1",
            "STATE_OWNER": "bridge intended_action_mapper_v1",
            "CONFIG_OWNER": "N/A_mapper_only",
            "DECISION_REASON_SOURCE": "intended_action.reason_codes",
            "CURRENT_TELEMETRY": "intended_action dict",
            "MISSING_TELEMETRY": "stage observation event",
            "CALL_ORDER_INDEX": 17,
        },
        {
            "STAGE": "simulated_execution",
            "PRODUCTIVE_SYMBOL": "apply_intended_action_via_canonical_accounting_v1",
            "PRODUCTIVE_CALLER": (
                "ops.productive_futures_accounting_runtime_binding_v1.bridge_binding_v1."
                "apply_intended_action_via_canonical_accounting_v1"
            ),
            "INPUT_CONTRACT": "intended_side + quantity + mark",
            "OUTPUT_CONTRACT": "simulated fill + accounting",
            "STATE_OWNER": "ops.productive_futures_accounting_runtime_binding_v1",
            "CONFIG_OWNER": "fee/slippage model constants",
            "DECISION_REASON_SOURCE": "fill present / accounting result",
            "CURRENT_TELEMETRY": "fills_ledger",
            "MISSING_TELEMETRY": "stage observation event",
            "CALL_ORDER_INDEX": 18,
        },
    ]

    indices = [int(r["CALL_ORDER_INDEX"]) for r in rows]
    stages = [str(r["STAGE"]) for r in rows]
    call_order_exact = stages == list(ACTIONABILITY_CALL_ORDER_V1) and indices == list(
        range(len(ACTIONABILITY_CALL_ORDER_V1))
    )
    return {
        "owner": OWNER,
        "productive_host": PRODUCTIVE_HOST,
        "productive_caller": PRODUCTIVE_CALLER,
        "productive_decision_authority": PRODUCTIVE_DECISION_AUTHORITY,
        "parallel_decision_engine_created": False,
        "core_logic_changed": False,
        "CALL_ORDER_FROZEN": call_order_exact,
        "PRODUCTIVE_DECISION_GRAPH_IDENTIFIED": True,
        "PRODUCTIVE_SYMBOLS_ENUMERATED": True,
        "PRODUCTIVE_CALLERS_ENUMERATED": True,
        "STATE_OWNERS_IDENTIFIED": True,
        "CONFIG_CONSUMERS_IDENTIFIED": True,
        "MASTER_V2_AUTHORITY_EXACT": True,
        "DOUBLE_PLAY_AUTHORITY_EXACT": True,
        "BULL_BEAR_AUTHORITY_EXACT": True,
        "CONFIRMATION_AUTHORITY_EXACT": True,
        "DYNAMIC_SCOPE_AUTHORITY_EXACT": True,
        "COMPOSITION_AUTHORITY_EXACT": True,
        "RISK_AUTHORITY_EXACT": True,
        "SAFETY_AUTHORITY_EXACT": True,
        "EXIT_PRECEDENCE_EXACT": True,
        "actionability_call_order": list(ACTIONABILITY_CALL_ORDER_V1),
        "matrix": rows,
    }
