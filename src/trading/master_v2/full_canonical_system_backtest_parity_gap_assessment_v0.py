"""
Offline-only gap assessment registry: Integrated Offline Replay vs Scenario Replay
vs Backtest vs Runtime decision parity surfaces (v0).

Assessment-only. No runtime authority, no economic evaluation, no trading semantic change.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal, Mapping, Sequence, Tuple

FULL_CANONICAL_SYSTEM_BACKTEST_PARITY_GAP_ASSESSMENT_LAYER_VERSION = "v0"
FULL_CANONICAL_SYSTEM_BACKTEST_PARITY_GAP_ASSESSMENT_OWNER = (
    "trading.master_v2.full_canonical_system_backtest_parity_gap_assessment_v0"
)

ParityStatus = Literal["PASS", "PARTIAL", "GAP", "NOT_APPLICABLE"]
MatrixStatus = Literal[
    "PASS",
    "GAP",
    "NOT_APPLICABLE_BOUNDARY_ONLY",
    "BLOCKED",
    "UNKNOWN",
]

NEXT_RECOMMENDED_SLICE = "FULL_CANONICAL_BACKTEST_BOUNDARY_CHAIN_REASSESSMENT_V0"

ALLOWED_SLICE_CHANGED_PATH_PREFIXES: Tuple[str, ...] = (
    "src/trading/master_v2/full_canonical_system_backtest_parity_gap_assessment_v0.py",
    "scripts/ops/run_full_canonical_system_backtest_parity_gap_assessment_v0.py",
    "scripts/ops/run_safety_kernel_offline_replay_binding_parity_rewire_v0.py",
    "scripts/ops/run_reconciliation_unknown_outcome_offline_replay_binding_parity_rewire_v0.py",
    "scripts/ops/run_killswitch_boundary_offline_replay_binding_parity_rewire_v0.py",
    "tests/trading/master_v2/test_full_canonical_system_backtest_parity_gap_assessment_contract_v0.py",
    "tests/trading/master_v2/test_safety_kernel_offline_replay_binding_parity_rewire_contract_v0.py",
    "tests/trading/master_v2/test_reconciliation_unknown_outcome_offline_replay_binding_parity_rewire_contract_v0.py",
    "tests/trading/master_v2/test_killswitch_boundary_offline_replay_binding_parity_rewire_contract_v0.py",
    "src/trading/master_v2/reconciliation_unknown_outcome_offline_replay_binding_adapter_v0.py",
    "src/trading/master_v2/killswitch_boundary_offline_replay_binding_adapter_v0.py",
    "src/trading/master_v2/killswitch_boundary_backtest_state_file_binding_adapter_v0.py",
    "src/trading/master_v2/reconciliation_boundary_backtest_state_file_binding_adapter_v0.py",
    "src/backtest/mv2_research_wiring_v1.py",
    "scripts/ops/run_backtest_killswitch_state_file_wiring_v0.py",
    "scripts/ops/run_backtest_killswitch_boundary_wiring_v0.py",
    "scripts/ops/run_backtest_reconciliation_state_file_wiring_v0.py",
    "scripts/ops/run_backtest_reconciliation_unknown_outcome_wiring_v0.py",
    "tests/trading/master_v2/test_killswitch_boundary_backtest_state_file_binding_contract_v0.py",
    "tests/test_backtest_killswitch_boundary_wiring_v0.py",
    "tests/trading/master_v2/test_reconciliation_boundary_backtest_state_file_binding_contract_v0.py",
    "tests/test_backtest_reconciliation_unknown_outcome_wiring_v0.py",
    "src/trading/master_v2/capital_risk_sizing_boundary_backtest_state_file_binding_adapter_v0.py",
    "scripts/ops/run_backtest_capital_risk_sizing_wiring_v0.py",
    "tests/trading/master_v2/test_capital_risk_sizing_boundary_backtest_state_file_binding_contract_v0.py",
    "src/trading/master_v2/canonical_order_intent_boundary_backtest_state_file_binding_adapter_v0.py",
    "scripts/ops/run_backtest_canonical_order_intent_wiring_v0.py",
    "tests/test_backtest_canonical_order_intent_wiring_v0.py",
    "src/trading/master_v2/safety_kernel_boundary_backtest_state_file_binding_adapter_v0.py",
    "scripts/ops/run_backtest_safety_kernel_wiring_v0.py",
    "tests/test_backtest_safety_kernel_wiring_v0.py",
    "src/trading/master_v2/promotion_gate_boundary_offline_replay_binding_adapter_v0.py",
    "src/trading/master_v2/promotion_gate_boundary_backtest_state_file_binding_adapter_v0.py",
    "scripts/ops/run_backtest_promotion_gate_boundary_wiring_v0.py",
    "tests/trading/master_v2/test_promotion_gate_boundary_backtest_state_file_binding_contract_v0.py",
    "tests/trading/master_v2/test_promotion_gate_boundary_offline_replay_binding_parity_rewire_contract_v0.py",
    "tests/test_backtest_promotion_gate_boundary_wiring_v0.py",
    "src/trading/master_v2/ai_observability_boundary_offline_replay_binding_adapter_v0.py",
    "src/trading/master_v2/ai_observability_boundary_backtest_state_file_binding_adapter_v0.py",
    "src/trading/master_v2/feedback_learning_boundary_offline_replay_binding_adapter_v0.py",
    "src/trading/master_v2/feedback_learning_boundary_backtest_state_file_binding_adapter_v0.py",
    "scripts/ops/run_backtest_ai_observability_feedback_boundary_wiring_v0.py",
    "tests/trading/master_v2/test_ai_observability_boundary_backtest_state_file_binding_contract_v0.py",
    "tests/trading/master_v2/test_ai_observability_boundary_offline_replay_binding_parity_rewire_contract_v0.py",
    "tests/trading/master_v2/test_feedback_learning_boundary_backtest_state_file_binding_contract_v0.py",
    "tests/trading/master_v2/test_feedback_learning_boundary_offline_replay_binding_parity_rewire_contract_v0.py",
    "tests/test_backtest_ai_observability_feedback_boundary_wiring_v0.py",
    "src/trading/master_v2/bull_bear_state_switch_scenario_binding_adapter_v0.py",
    "src/trading/master_v2/scope_event_generator_scenario_binding_adapter_v0.py",
    "src/trading/master_v2/reversal_preparation_scenario_binding_adapter_v0.py",
    "scripts/ops/run_bull_bear_state_switch_scenario_replay_binding_parity_rewire_v0.py",
    "scripts/ops/run_scope_event_generator_scenario_replay_binding_parity_rewire_v0.py",
    "scripts/ops/run_reversal_preparation_scenario_replay_binding_parity_rewire_v0.py",
    "tests/trading/master_v2/test_bull_bear_state_switch_scenario_replay_binding_parity_rewire_contract_v0.py",
    "tests/trading/master_v2/test_scope_event_generator_scenario_replay_binding_parity_rewire_contract_v0.py",
    "tests/trading/master_v2/test_reversal_preparation_scenario_replay_binding_parity_rewire_contract_v0.py",
    "src/trading/master_v2/flat_before_opposite_side_scenario_binding_adapter_v0.py",
    "scripts/ops/run_flat_before_opposite_side_scenario_replay_binding_parity_rewire_v0.py",
    "tests/trading/master_v2/test_flat_before_opposite_side_scenario_replay_binding_parity_rewire_contract_v0.py",
    "docs/research/FULL_CANONICAL_SYSTEM_BACKTEST_PARITY_GAP_ASSESSMENT_V0.md",
    "scripts/ops/run_integrated_vs_scenario_replay_full_system_4_way_parity_rewire_v0.py",
    "scripts/ops/run_surface_p_full_bar_sequence_4_way_parity_completion_v0.py",
    "src/trading/master_v2/integrated_vs_scenario_replay_full_system_parity_harness_v0.py",
    "tests/trading/master_v2/test_integrated_vs_scenario_replay_full_system_parity_contract_suite_v0.py",
    "tests/trading/master_v2/test_surface_p_full_bar_sequence_4_way_parity_completion_contract_v0.py",
    "src/trading/master_v2/surface_p_offline_complete_runtime_bridge_bound_not_activated_contract_v0.py",
    "scripts/ops/run_surface_p_offline_complete_runtime_bridge_bound_not_activated_contract_v0.py",
    "tests/trading/master_v2/test_surface_p_offline_complete_runtime_bridge_bound_not_activated_contract_v0.py",
    "src/trading/master_v2/surface_p_final_flags_fail_closed_contract_v0.py",
    "scripts/ops/run_surface_p_final_flags_fail_closed_contract_v0.py",
    "tests/trading/master_v2/test_surface_p_final_flags_fail_closed_contract_v0.py",
    "src/trading/master_v2/surface_p_semantic_parity_gap_assessment_v0.py",
    "scripts/ops/run_surface_p_semantic_parity_gap_assessment_v0.py",
    "tests/trading/master_v2/test_surface_p_semantic_parity_gap_assessment_contract_v0.py",
    "src/trading/master_v2/next_full_canonical_parity_surface_after_surface_p_assessment_v0.py",
    "scripts/ops/run_next_full_canonical_parity_surface_after_surface_p_assessment_v0.py",
    "tests/trading/master_v2/test_next_full_canonical_parity_surface_after_surface_p_assessment_contract_v0.py",
    "src/trading/master_v2/runtime_bridge_pre_activation_gate_assessment_v0.py",
    "scripts/ops/run_runtime_bridge_pre_activation_gate_assessment_v0.py",
    "tests/trading/master_v2/test_runtime_bridge_pre_activation_gate_assessment_contract_v0.py",
    "src/trading/master_v2/surface_p_required_proof_input_binding_v0.py",
    "tests/research/test_surface_p_proof_input_gap_assessment_binding_v0.py",
    "src/trading/master_v2/runtime_bridge_boundary_gap_assessment_v0.py",
    "scripts/ops/run_runtime_bridge_boundary_gap_assessment_v0.py",
    "tests/trading/master_v2/test_runtime_bridge_boundary_gap_assessment_contract_v0.py",
)

FORBIDDEN_CHANGED_PATH_PREFIXES: Tuple[str, ...] = (
    "src/execution/",
    "src/live/",
    "src/runtime/",
    "src/scheduler/",
    "src/governance/",
    "src/risk/",
    "credentials",
    "secrets",
)


@dataclass(frozen=True)
class ParitySurfaceAssessmentV0:
    surface_id: str
    surface_name: str
    canonical_owner_files: Tuple[str, ...]
    current_integrated_offline_replay_binding: str
    current_scenario_replay_binding: str
    current_backtest_binding: str
    current_runtime_semantics_reference: str
    parity_status: ParityStatus
    evidence_refs: Tuple[str, ...]
    missing_binding_if_any: str
    recommended_next_slice: str
    forbidden_runtime_authority_confirmed: bool = True


def _parity_surface_assessments_base_v0() -> Tuple[ParitySurfaceAssessmentV0, ...]:
    return (
        ParitySurfaceAssessmentV0(
            surface_id="A",
            surface_name="Bull/Bear State Switch",
            canonical_owner_files=(
                "src/trading/master_v2/double_play_state.py",
                "src/trading/master_v2/directional_assessment_v1.py",
            ),
            current_integrated_offline_replay_binding=(
                "integrated_offline_trading_logic_replay_v1.run_integrated_offline_trading_logic_replay_v1"
                " -> deterministic_scope_event_generator_v1 -> transition_state()"
            ),
            current_scenario_replay_binding=(
                "offline_double_play_scenario_replay_v0.run_offline_double_play_scenario_replay_v0"
                " -> evaluate_scenario_state_switch_v0() per tick"
            ),
            current_backtest_binding=(
                "backtest/mv2_research_wiring_v1.run_mv2_research_backtest_wiring_v1"
                " -> integrated replay (indirect)"
            ),
            current_runtime_semantics_reference=(
                "canonical_core_runtime_integration_bridge_v0 (BOUND_NOT_ACTIVATED);"
                " legacy_runtime_entrypoint_guard_v0"
            ),
            parity_status="PASS",
            evidence_refs=(
                "tests/trading/master_v2/test_offline_master_v2_double_play_scenario_replay_binding_contract_v0.py",
                "tests/trading/master_v2/test_integrated_offline_trading_logic_replay_v1.py",
                "tests/trading/master_v2/test_integrated_vs_scenario_replay_full_system_parity_contract_suite_v0.py",
                "tests/trading/master_v2/test_bull_bear_state_switch_scenario_replay_binding_parity_rewire_contract_v0.py",
            ),
            missing_binding_if_any="",
            recommended_next_slice=NEXT_RECOMMENDED_SLICE,
        ),
        ParitySurfaceAssessmentV0(
            surface_id="B",
            surface_name="Scope adverse exit",
            canonical_owner_files=(
                "src/trading/master_v2/deterministic_scope_event_generator_v1.py",
                "src/trading/master_v2/double_play_entry_exit_policy_v0.py",
            ),
            current_integrated_offline_replay_binding=(
                "integrated_offline_trading_logic_replay_v1 -> generate_deterministic_scope_event()"
                " + scope_adverse_exit_signal -> evaluate_double_play_entry_exit_policy_v0()"
            ),
            current_scenario_replay_binding=(
                "offline_double_play_scenario_replay_v0 -> evaluate_scenario_scope_event_v0()"
                " -> generate_deterministic_scope_event()"
                " + scope_adverse_exit_signal -> evaluate_scenario_entry_exit_policy_v0()"
            ),
            current_backtest_binding=(
                "mv2_research_wiring_v1 adverse_exit_distance=60.0 -> integrated replay"
            ),
            current_runtime_semantics_reference=(
                "canonical_core_runtime_integration_bridge_v0 passes scope params to integrated replay"
            ),
            parity_status="PASS",
            evidence_refs=(
                "tests/trading/master_v2/test_deterministic_scope_event_generator_v1.py",
                "tests/trading/master_v2/test_double_play_entry_exit_policy_v0.py",
                "tests/trading/master_v2/test_scope_event_generator_scenario_replay_binding_parity_rewire_contract_v0.py",
            ),
            missing_binding_if_any="",
            recommended_next_slice=NEXT_RECOMMENDED_SLICE,
        ),
        ParitySurfaceAssessmentV0(
            surface_id="C",
            surface_name="Reversal preparation",
            canonical_owner_files=(
                "src/trading/master_v2/double_play_composition_matrix_v1.py",
                "src/trading/master_v2/double_play_entry_exit_policy_v0.py",
            ),
            current_integrated_offline_replay_binding=(
                "integrated_offline_trading_logic_replay_v1 -> composition matrix"
                " + evaluate_double_play_entry_exit_policy_v0()"
            ),
            current_scenario_replay_binding=(
                "offline_double_play_scenario_replay_v0"
                " -> evaluate_scenario_reversal_preparation_entry_exit_v0()"
                " -> evaluate_double_play_entry_exit_policy_v0()"
                " (REVERSAL_PREPARATION_EXIT)"
            ),
            current_backtest_binding="Integrated replay (default PositionManagementContext.FLAT)",
            current_runtime_semantics_reference=(
                "canonical_core_runtime_integration_bridge_v0 -> integrated replay"
            ),
            parity_status="PASS",
            evidence_refs=(
                "tests/trading/master_v2/test_integrated_vs_scenario_replay_full_system_parity_contract_suite_v0.py::test_5_reversal_preparation_boundary_parity_v0",
                "tests/trading/master_v2/test_double_play_composition_matrix_v1.py",
                "tests/trading/master_v2/test_double_play_entry_exit_policy_v0.py",
                "tests/trading/master_v2/test_reversal_preparation_scenario_replay_binding_parity_rewire_contract_v0.py",
            ),
            missing_binding_if_any="",
            recommended_next_slice=NEXT_RECOMMENDED_SLICE,
        ),
        ParitySurfaceAssessmentV0(
            surface_id="D",
            surface_name="Flat-before-opposite-side invariant",
            canonical_owner_files=(
                "src/trading/master_v2/double_play_state.py",
                "src/trading/master_v2/double_play_entry_exit_policy_v0.py",
            ),
            current_integrated_offline_replay_binding=(
                "transition_state() SWITCH_*_PENDING pipeline"
                " + evaluate_double_play_entry_exit_policy_v0() flat/flip gates"
            ),
            current_scenario_replay_binding=(
                "offline_double_play_scenario_replay_v0"
                " -> evaluate_scenario_flat_before_opposite_side_entry_exit_v0()"
                " -> evaluate_double_play_entry_exit_policy_v0()"
                " flat/flip gates per tick"
            ),
            current_backtest_binding=(
                "Integrated replay defaults venue_flat=True, ExistingPositionSide.NONE"
            ),
            current_runtime_semantics_reference=(
                "double_play_state.transition_state (DOUBLE_PLAY_BULL_BEAR_REFERENCE_V0)"
            ),
            parity_status="PASS",
            evidence_refs=(
                "tests/trading/master_v2/test_double_play_entry_exit_policy_v0.py",
                "tests/trading/master_v2/test_offline_master_v2_double_play_scenario_replay_binding_contract_v0.py",
                "tests/trading/master_v2/test_flat_before_opposite_side_scenario_replay_binding_parity_rewire_contract_v0.py",
                "src/trading/master_v2/survival_suitability_scenario_binding_adapter_v0.py",
                "src/trading/master_v2/double_play_composition_scenario_matrix_adapter_v0.py",
                "src/trading/master_v2/offline_double_play_scenario_replay_v0.py",
                "scripts/ops/run_survival_suitability_scenario_replay_binding_parity_rewire_v0.py",
                "tests/trading/master_v2/test_survival_suitability_scenario_replay_binding_parity_rewire_contract_v0.py",
            ),
            missing_binding_if_any="",
            recommended_next_slice=NEXT_RECOMMENDED_SLICE,
        ),
        ParitySurfaceAssessmentV0(
            surface_id="E",
            surface_name="Survival and Suitability",
            canonical_owner_files=(
                "src/trading/master_v2/survival_assessment_v1.py",
                "src/trading/master_v2/suitability_binding_v1.py",
                "src/trading/master_v2/double_play_survival.py",
                "src/trading/master_v2/double_play_suitability.py",
            ),
            current_integrated_offline_replay_binding=(
                "integrated_offline_trading_logic_replay_v1 ->"
                " evaluate_survival_assessment_v1() + evaluate_suitability_binding_v1()"
            ),
            current_scenario_replay_binding=(
                "offline_double_play_scenario_replay_v0 ->"
                " evaluate_scenario_survival_suitability_v0()"
                " -> evaluate_survival_assessment_v1() + evaluate_suitability_binding_v1()"
            ),
            current_backtest_binding="Integrated v1 path via mv2_research_wiring_v1",
            current_runtime_semantics_reference=(
                "canonical_core_runtime_integration_bridge_v0 v1 policies"
            ),
            parity_status="PASS",
            evidence_refs=(
                "tests/trading/master_v2/test_double_play_composition_scenario_matrix_parity_contract_v0.py",
                "tests/trading/master_v2/test_directional_assessment_v1.py",
                "tests/trading/master_v2/test_survival_suitability_scenario_replay_binding_parity_rewire_contract_v0.py",
            ),
            missing_binding_if_any="",
            recommended_next_slice=NEXT_RECOMMENDED_SLICE,
        ),
        ParitySurfaceAssessmentV0(
            surface_id="F",
            surface_name="Double Play composition",
            canonical_owner_files=(
                "src/trading/master_v2/double_play_composition_matrix_v1.py",
                "src/trading/master_v2/double_play_composition_scenario_matrix_adapter_v0.py",
            ),
            current_integrated_offline_replay_binding=(
                "integrated_offline_trading_logic_replay_v1 ->"
                " evaluate_double_play_composition_matrix_v1()"
            ),
            current_scenario_replay_binding=(
                "offline_double_play_scenario_replay_v0 ->"
                " compose_double_play_scenario_via_canonical_matrix_v0()"
            ),
            current_backtest_binding="Integrated replay",
            current_runtime_semantics_reference=(
                "evaluate_double_play_authority_boundary_v0"
                " CANONICAL_DOUBLE_PLAY_OFFLINE_AUTHORITY_OWNER"
            ),
            parity_status="PASS",
            evidence_refs=(
                "tests/trading/master_v2/test_integrated_vs_scenario_replay_full_system_parity_contract_suite_v0.py",
                "tests/trading/master_v2/test_double_play_composition_scenario_matrix_parity_contract_v0.py",
                "src/trading/master_v2/integrated_vs_scenario_replay_full_system_parity_harness_v0.py",
            ),
            missing_binding_if_any="",
            recommended_next_slice=NEXT_RECOMMENDED_SLICE,
        ),
        ParitySurfaceAssessmentV0(
            surface_id="G",
            surface_name="Entry / Position / Exit Policy",
            canonical_owner_files=("src/trading/master_v2/double_play_entry_exit_policy_v0.py",),
            current_integrated_offline_replay_binding=(
                "integrated_offline_trading_logic_replay_v1 ->"
                " evaluate_double_play_entry_exit_policy_v0()"
            ),
            current_scenario_replay_binding=(
                "offline_double_play_scenario_replay_v0 ->"
                " evaluate_scenario_entry_exit_policy_v0() per tick"
            ),
            current_backtest_binding="Integrated replay",
            current_runtime_semantics_reference=(
                "canonical_core_runtime_integration_bridge_v0 -> integrated replay evidence"
            ),
            parity_status="PASS",
            evidence_refs=(
                "tests/trading/master_v2/test_double_play_entry_exit_policy_v0.py",
                "tests/trading/master_v2/test_integrated_offline_trading_logic_replay_v1.py",
                "tests/trading/master_v2/test_scenario_replay_double_play_entry_exit_policy_binding_parity_rewire_contract_v0.py",
            ),
            missing_binding_if_any="",
            recommended_next_slice=NEXT_RECOMMENDED_SLICE,
        ),
        ParitySurfaceAssessmentV0(
            surface_id="H",
            surface_name="Capital / Risk / Sizing",
            canonical_owner_files=(
                "src/governance/capital_risk_sizing_v1.py",
                "src/trading/master_v2/double_play_capital_slot.py",
            ),
            current_integrated_offline_replay_binding=(
                "integrated_offline_trading_logic_replay_v1 ->"
                " bind_capital_risk_sizing_offline_replay_evidence_v0()"
            ),
            current_scenario_replay_binding=(
                "offline_double_play_scenario_replay_v0 ->"
                " evaluate_scenario_capital_risk_sizing_v0() per tick"
            ),
            current_backtest_binding=(
                "backtest/mv2_research_wiring_v1.run_mv2_research_backtest_wiring_v1"
                " -> bind_capital_risk_sizing_boundary_backtest_state_file_evidence_v0()"
                " via capital_risk_sizing_boundary_backtest_state_file_binding_adapter_v0"
            ),
            current_runtime_semantics_reference=(
                "canonical_core_runtime_integration_intent_pipeline_bridge_v0"
                " Slice B BOUND_NOT_ACTIVATED"
            ),
            parity_status="PASS",
            evidence_refs=(
                "tests/governance/test_capital_risk_sizing_v1.py",
                "tests/trading/master_v2/test_offline_master_v2_double_play_scenario_replay_binding_contract_v0.py",
                "tests/trading/master_v2/test_capital_risk_sizing_offline_replay_binding_parity_rewire_contract_v0.py",
                "tests/trading/master_v2/test_capital_risk_sizing_boundary_backtest_state_file_binding_contract_v0.py",
            ),
            missing_binding_if_any="",
            recommended_next_slice=NEXT_RECOMMENDED_SLICE,
        ),
        ParitySurfaceAssessmentV0(
            surface_id="I",
            surface_name="Canonical Order Intent boundary",
            canonical_owner_files=(
                "src/governance/canonical_order_intent_v1.py",
                "src/governance/runbook_progress_registry_v1.py",
            ),
            current_integrated_offline_replay_binding=(
                "integrated_offline_trading_logic_replay_v1 ->"
                " bind_canonical_order_intent_offline_replay_evidence_v0()"
            ),
            current_scenario_replay_binding=(
                "offline_double_play_scenario_replay_v0 ->"
                " evaluate_scenario_canonical_order_intent_v0() per tick"
            ),
            current_backtest_binding=(
                "backtest/mv2_research_wiring_v1.run_mv2_research_backtest_wiring_v1 ->"
                " bind_canonical_order_intent_boundary_backtest_state_file_evidence_v0()"
                " via canonical_order_intent_boundary_backtest_state_file_binding_adapter_v0"
            ),
            current_runtime_semantics_reference=(
                "canonical_core_runtime_integration_intent_pipeline_bridge_v0"
                " build_canonical_order_intent_v1 BOUND_NOT_ACTIVATED"
            ),
            parity_status="PASS",
            evidence_refs=(
                "tests/governance/test_canonical_order_intent_v1.py",
                "tests/governance/test_intent_compatibility_firewall_v1.py",
                "tests/trading/master_v2/test_canonical_order_intent_offline_replay_binding_parity_rewire_contract_v0.py",
                "tests/test_backtest_canonical_order_intent_wiring_v0.py",
            ),
            missing_binding_if_any="",
            recommended_next_slice=NEXT_RECOMMENDED_SLICE,
        ),
        ParitySurfaceAssessmentV0(
            surface_id="J",
            surface_name="Safety Kernel semantics",
            canonical_owner_files=(
                "src/meta/learning_loop/runtime_eligibility_v1.py",
                "src/meta/learning_loop/killswitch_writer_fencing_and_independent_read_paths_v1.py",
                "src/trading/master_v2/safety_kernel_offline_replay_binding_adapter_v0.py",
            ),
            current_integrated_offline_replay_binding=(
                "integrated_offline_trading_logic_replay_v1 ->"
                " bind_safety_kernel_offline_replay_evidence_v0()"
            ),
            current_scenario_replay_binding=(
                "offline_double_play_scenario_replay_v0 ->"
                " evaluate_scenario_safety_kernel_v0() per tick"
            ),
            current_backtest_binding=(
                "backtest/mv2_research_wiring_v1.run_mv2_research_backtest_wiring_v1 ->"
                " bind_safety_kernel_boundary_backtest_state_file_evidence_v0()"
                " via safety_kernel_boundary_backtest_state_file_binding_adapter_v0"
            ),
            current_runtime_semantics_reference=(
                "docs/ops/specs/FUTURES_MASTER_V2_RUNTIME_GOVERNANCE_BOUNDARY_CONTRACT_V0.md"
            ),
            parity_status="PASS",
            evidence_refs=(
                "tests/meta/test_killswitch_writer_fencing_and_independent_read_paths_v1.py",
                "tests/meta/test_runtime_eligibility_v1.py",
                "tests/trading/master_v2/test_safety_kernel_offline_replay_binding_parity_rewire_contract_v0.py",
                "tests/test_backtest_safety_kernel_wiring_v0.py",
            ),
            missing_binding_if_any="",
            recommended_next_slice=NEXT_RECOMMENDED_SLICE,
        ),
        ParitySurfaceAssessmentV0(
            surface_id="K",
            surface_name="KillSwitch boundary semantics",
            canonical_owner_files=(
                "src/meta/learning_loop/killswitch_writer_fencing_and_independent_read_paths_v1.py",
                "src/risk_layer/kill_switch/core.py",
                "src/trading/master_v2/killswitch_boundary_offline_replay_binding_adapter_v0.py",
            ),
            current_integrated_offline_replay_binding=(
                "integrated_offline_trading_logic_replay_v1 ->"
                " bind_killswitch_boundary_offline_replay_evidence_v0()"
            ),
            current_scenario_replay_binding=(
                "offline_double_play_scenario_replay_v0 ->"
                " evaluate_scenario_killswitch_boundary_v0() per tick"
            ),
            current_backtest_binding=(
                "backtest/mv2_research_wiring_v1.run_mv2_research_backtest_wiring_v1"
                " -> bind_killswitch_boundary_backtest_state_file_evidence_v0()"
                " via killswitch_boundary_backtest_state_file_binding_adapter_v0"
            ),
            current_runtime_semantics_reference=(
                "src/ops/gates/risk_gate.py; FUTURES_RISK_SAFETY_KILLSWITCH_CONTRACT_V0"
            ),
            parity_status="PASS",
            evidence_refs=(
                "tests/trading/master_v2/test_offline_master_v2_double_play_scenario_replay_binding_contract_v0.py::test_killswitch_blocks_activation",
                "tests/trading/master_v2/test_killswitch_boundary_offline_replay_binding_parity_rewire_contract_v0.py",
                "tests/trading/master_v2/test_killswitch_boundary_backtest_state_file_binding_contract_v0.py",
                "tests/test_backtest_killswitch_boundary_wiring_v0.py",
            ),
            missing_binding_if_any="",
            recommended_next_slice=NEXT_RECOMMENDED_SLICE,
        ),
        ParitySurfaceAssessmentV0(
            surface_id="L",
            surface_name="Reconciliation and Unknown Outcome semantics",
            canonical_owner_files=(
                "src/trading/master_v2/double_play_entry_exit_policy_v0.py",
                "src/trading/master_v2/reconciliation_unknown_outcome_offline_replay_binding_adapter_v0.py",
                "src/meta/learning_loop/runtime_state_reconciliation_v1.py",
            ),
            current_integrated_offline_replay_binding=(
                "integrated_offline_trading_logic_replay_v1 ->"
                " bind_reconciliation_unknown_outcome_offline_replay_evidence_v0()"
            ),
            current_scenario_replay_binding=(
                "offline_double_play_scenario_replay_v0 ->"
                " evaluate_scenario_reconciliation_unknown_outcome_v0() per tick"
            ),
            current_backtest_binding=(
                "backtest/mv2_research_wiring_v1.run_mv2_research_backtest_wiring_v1"
                " -> bind_reconciliation_boundary_backtest_state_file_evidence_v0()"
                " via reconciliation_boundary_backtest_state_file_binding_adapter_v0"
            ),
            current_runtime_semantics_reference="src/ops/recon/reconcile.py",
            parity_status="PASS",
            evidence_refs=(
                "tests/trading/master_v2/test_double_play_entry_exit_policy_v0.py",
                "tests/trading/master_v2/test_reconciliation_unknown_outcome_offline_replay_binding_parity_rewire_contract_v0.py",
                "tests/trading/master_v2/test_reconciliation_boundary_backtest_state_file_binding_contract_v0.py",
                "tests/test_backtest_reconciliation_unknown_outcome_wiring_v0.py",
            ),
            missing_binding_if_any="",
            recommended_next_slice=NEXT_RECOMMENDED_SLICE,
        ),
        ParitySurfaceAssessmentV0(
            surface_id="M",
            surface_name="Promotion Gate boundary",
            canonical_owner_files=(
                "src/governance/promotion_loop/promotion_economic_gate_v1.py",
                "src/trading/master_v2/promotion_gate_boundary_offline_replay_binding_adapter_v0.py",
                "docs/ops/specs/MASTER_V2_PROMOTION_STATE_MACHINE_V1.md",
            ),
            current_integrated_offline_replay_binding=(
                "bind_promotion_gate_boundary_offline_replay_evidence_v0()"
                " via promotion_gate_boundary_offline_replay_binding_adapter_v0"
            ),
            current_scenario_replay_binding=(
                "bind_promotion_gate_boundary_offline_replay_evidence_v0()"
                " (offline candidate eligibility representation only)"
            ),
            current_backtest_binding=(
                "backtest/mv2_research_wiring_v1.run_mv2_research_backtest_wiring_v1"
                " -> bind_promotion_gate_boundary_backtest_state_file_evidence_v0()"
                " via promotion_gate_boundary_backtest_state_file_binding_adapter_v0"
            ),
            current_runtime_semantics_reference=(
                "governance/promotion_loop/safety.py global_promotion_lock;"
                " promotion_economic_gate_v1 (non-authorizing candidate eligibility only)"
            ),
            parity_status="PASS",
            evidence_refs=(
                "tests/governance/test_promotion_economic_gate_v1.py",
                "tests/ops/test_step29n_promotion_economic_gate_binding_fail_closed_contract_v0.py",
                "tests/trading/master_v2/test_promotion_gate_boundary_offline_replay_binding_parity_rewire_contract_v0.py",
                "tests/trading/master_v2/test_promotion_gate_boundary_backtest_state_file_binding_contract_v0.py",
                "tests/test_backtest_promotion_gate_boundary_wiring_v0.py",
            ),
            missing_binding_if_any="",
            recommended_next_slice=NEXT_RECOMMENDED_SLICE,
        ),
        ParitySurfaceAssessmentV0(
            surface_id="N",
            surface_name="AI / Observability / Explainability boundary",
            canonical_owner_files=(
                "src/trading/master_v2/canonical_trading_decision_evidence_v1.py",
                "src/trading/master_v2/double_play_dashboard_display.py",
                "src/trading/master_v2/decision_packet_v1.py",
            ),
            current_integrated_offline_replay_binding=(
                "bind_ai_observability_boundary_offline_replay_evidence_v0()"
                " via ai_observability_boundary_offline_replay_binding_adapter_v0"
            ),
            current_scenario_replay_binding=(
                "bind_ai_observability_boundary_offline_replay_evidence_v0()"
                " (read-only explainability envelope from decision evidence)"
            ),
            current_backtest_binding=(
                "backtest/mv2_research_wiring_v1.run_mv2_research_backtest_wiring_v1"
                " -> bind_ai_observability_boundary_backtest_state_file_evidence_v0()"
                " via ai_observability_boundary_backtest_state_file_binding_adapter_v0"
            ),
            current_runtime_semantics_reference=(
                "docs/ops/specs/MASTER_V2_DECISION_AUTHORITY_MAP_V1.md;"
                " docs/governance/ai/AI_LAYER_CANONICAL_SPEC_V1.md (advisory only)"
            ),
            parity_status="PASS",
            evidence_refs=(
                "tests/trading/master_v2/test_offline_master_v2_double_play_scenario_replay_binding_contract_v0.py",
                "tests/trading/master_v2/test_integrated_offline_trading_logic_replay_v1.py",
                "tests/trading/master_v2/test_ai_observability_boundary_backtest_state_file_binding_contract_v0.py",
                "tests/trading/master_v2/test_ai_observability_boundary_offline_replay_binding_parity_rewire_contract_v0.py",
                "tests/test_backtest_ai_observability_feedback_boundary_wiring_v0.py",
            ),
            missing_binding_if_any="",
            recommended_next_slice=NEXT_RECOMMENDED_SLICE,
        ),
        ParitySurfaceAssessmentV0(
            surface_id="O",
            surface_name="Feedback / Learning boundary",
            canonical_owner_files=(
                "src/meta/learning_loop/runtime_observation_feedback_v1.py",
                "src/meta/learning_loop/deploy_inactive_v1.py",
            ),
            current_integrated_offline_replay_binding=(
                "bind_feedback_learning_boundary_offline_replay_evidence_v0()"
                " via feedback_learning_boundary_offline_replay_binding_adapter_v0"
                " (observe-only; no learning effects)"
            ),
            current_scenario_replay_binding=(
                "bind_feedback_learning_boundary_offline_replay_evidence_v0()"
                " (observe-only; no learning effects)"
            ),
            current_backtest_binding=(
                "backtest/mv2_research_wiring_v1.run_mv2_research_backtest_wiring_v1"
                " -> bind_feedback_learning_boundary_backtest_state_file_evidence_v0()"
                " via feedback_learning_boundary_backtest_state_file_binding_adapter_v0"
            ),
            current_runtime_semantics_reference=(
                "docs/ops/specs/MASTER_V2_LEARNING_AI_AUTONOMY_INVENTORY_V1.md"
                " (deploy-inactive; no strategy mutation)"
            ),
            parity_status="PASS",
            evidence_refs=(
                "docs/governance/authority_conflict_matrix_v1.md",
                "tests/trading/master_v2/test_feedback_learning_boundary_backtest_state_file_binding_contract_v0.py",
                "tests/trading/master_v2/test_feedback_learning_boundary_offline_replay_binding_parity_rewire_contract_v0.py",
                "tests/test_backtest_ai_observability_feedback_boundary_wiring_v0.py",
            ),
            missing_binding_if_any="",
            recommended_next_slice=NEXT_RECOMMENDED_SLICE,
        ),
        ParitySurfaceAssessmentV0(
            surface_id="P",
            surface_name=("Backtest / Offline Replay / Scenario Replay / Runtime decision parity"),
            canonical_owner_files=(
                "src/trading/master_v2/integrated_vs_scenario_replay_full_system_parity_harness_v0.py",
                "src/trading/master_v2/evaluate_double_play_authority_boundary_v0.py",
            ),
            current_integrated_offline_replay_binding=(
                "run_integrated_offline_trading_logic_replay_v1()"
            ),
            current_scenario_replay_binding=(
                "run_offline_double_play_scenario_replay_v0() + matrix adapter"
            ),
            current_backtest_binding=(
                "evaluate_surface_p_four_way_parity_v0() ->"
                " bind_backtest_bar_four_way_parity_lane_v0() via"
                " integrated_vs_scenario_replay_full_system_parity_harness_v0"
            ),
            current_runtime_semantics_reference=(
                "canonical_core_runtime_integration_bridge_v0 +"
                " canonical_core_runtime_integration_intent_pipeline_bridge_v0"
                " both BOUND_NOT_ACTIVATED; runtime reference lane bound offline"
            ),
            parity_status="PARTIAL",
            evidence_refs=(
                "tests/trading/master_v2/test_integrated_vs_scenario_replay_full_system_parity_contract_suite_v0.py",
                "tests/trading/master_v2/test_surface_p_full_bar_sequence_4_way_parity_completion_contract_v0.py",
                "scripts/ops/run_integrated_vs_scenario_replay_full_system_parity_contract_suite_v0.py",
                "scripts/ops/run_integrated_vs_scenario_replay_full_system_4_way_parity_rewire_v0.py",
                "scripts/ops/run_surface_p_full_bar_sequence_4_way_parity_completion_v0.py",
                "docs/governance/authority_conflict_matrix_v1.md",
            ),
            missing_binding_if_any=(
                "Runtime bridge activation remains BOUND_NOT_ACTIVATED by policy;"
                " full bar-sequence 4-way parity fixture coverage complete offline"
                " (entry/exit, capital/intent, blocked paths); runtime bridge activation"
                " still policy-blocked"
            ),
            recommended_next_slice=NEXT_RECOMMENDED_SLICE,
        ),
    )


def parity_surface_assessments_v0() -> Tuple[ParitySurfaceAssessmentV0, ...]:
    """Return gap assessments with Surface P promoted to PASS when offline proof input is satisfied."""
    from trading.master_v2.surface_p_required_proof_input_binding_v0 import (
        evaluate_surface_p_required_proof_input_binding_v0,
    )

    base = _parity_surface_assessments_base_v0()
    repo_root = Path(__file__).resolve().parents[3]
    binding = evaluate_surface_p_required_proof_input_binding_v0(repo_root)
    if not binding.satisfied:
        return base

    updated: list[ParitySurfaceAssessmentV0] = []
    for item in base:
        if item.surface_id != "P":
            updated.append(item)
            continue
        updated.append(
            ParitySurfaceAssessmentV0(
                surface_id=item.surface_id,
                surface_name=item.surface_name,
                canonical_owner_files=item.canonical_owner_files,
                current_integrated_offline_replay_binding=item.current_integrated_offline_replay_binding,
                current_scenario_replay_binding=item.current_scenario_replay_binding,
                current_backtest_binding=item.current_backtest_binding,
                current_runtime_semantics_reference=item.current_runtime_semantics_reference,
                parity_status="PASS",
                evidence_refs=item.evidence_refs,
                missing_binding_if_any="",
                recommended_next_slice=item.recommended_next_slice,
                forbidden_runtime_authority_confirmed=item.forbidden_runtime_authority_confirmed,
            )
        )
    return tuple(updated)


def normalize_matrix_status_v0(parity_status: ParityStatus) -> MatrixStatus:
    if parity_status == "PASS":
        return "PASS"
    if parity_status in ("PARTIAL", "GAP"):
        return "GAP"
    if parity_status == "NOT_APPLICABLE":
        return "NOT_APPLICABLE_BOUNDARY_ONLY"
    return "UNKNOWN"


def get_surface_p_required_proof_input_binding_v0(
    repo_root: Path | None = None,
) -> Mapping[str, Any]:
    """Expose Surface P required proof-input binding in gap assessment; fail-closed only."""
    from trading.master_v2.surface_p_required_proof_input_binding_v0 import (
        BINDING_SLICE_ID,
        SURFACE_P_PROOF_INPUT_ID,
        SURFACE_P_REQUIRED_PROOF_INPUT_BINDING_OWNER,
        SURFACE_P_SURFACE_ID,
        evaluate_surface_p_required_proof_input_binding_v0,
    )

    root = repo_root or Path(__file__).resolve().parents[3]
    binding = evaluate_surface_p_required_proof_input_binding_v0(root)
    binding_status = (
        "BOUND_FROM_REPAIRED_SOURCE_EVIDENCE"
        if binding.satisfied and binding.binding_status == "VERIFIED"
        else "MISSING_REQUIRED_PROOF_INPUT_SURFACE_P"
    )
    return {
        "surface_id": SURFACE_P_SURFACE_ID,
        "required_proof_input_id": SURFACE_P_PROOF_INPUT_ID,
        "required_proof_input_binding_status": binding_status,
        "binding_owner": SURFACE_P_REQUIRED_PROOF_INPUT_BINDING_OWNER,
        "binding_slice_id": BINDING_SLICE_ID,
        "accepted_source_status": binding.registry_parity_status,
        "partial_reason_required": "RUNTIME_BRIDGE_BOUND_NOT_ACTIVATED",
        "proof_input_satisfied": binding.satisfied,
        "owner_evidence_refs_present": binding.owner_evidence_refs_present,
        "offline_four_way_fixtures_complete": binding.offline_four_way_fixtures_complete,
        "semantic_binding_confirmations_complete": binding.semantic_binding_confirmations_complete,
        "surface_p_offline_parity_complete": binding.surface_p_offline_parity_complete,
        "runtime_bridge_bound_not_activated": binding.runtime_bridge_bound_not_activated,
        "full_canonical_chain_wired": binding.full_canonical_chain_wired,
        "backtest_runtime_decision_parity_pass": binding.backtest_runtime_decision_parity_pass,
        "system_economic_evidence_admissible": binding.system_economic_evidence_admissible,
        "runtime_rewire_admissible": False,
        "claim_promotion_allowed": False,
        "runtime_authority_effect": "NONE",
        "order_authority_effect": "NONE",
        "safety_semantics_changed": False,
        "economic_claim_changed": False,
        "no_runtime_authority_confirmed": True,
        "no_economic_claim_confirmed": True,
        "detail": binding.detail,
        "fail_closed_reasons": list(binding.fail_closed_reasons),
    }


def parity_gap_records_v0() -> Tuple[Mapping[str, Any], ...]:
    from trading.master_v2.surface_p_offline_complete_runtime_bridge_bound_not_activated_contract_v0 import (
        surface_p_offline_parity_complete_runtime_activation_pending_v0,
    )

    records: list[Mapping[str, Any]] = []
    for item in parity_surface_assessments_v0():
        if (
            item.surface_id == "P"
            and surface_p_offline_parity_complete_runtime_activation_pending_v0()
        ):
            continue
        matrix_status = normalize_matrix_status_v0(item.parity_status)
        if matrix_status != "GAP":
            continue
        records.append(
            {
                "surface_id": item.surface_id,
                "surface_name": item.surface_name,
                "matrix_status": matrix_status,
                "parity_status": item.parity_status,
                "owner": list(item.canonical_owner_files),
                "current_path": {
                    "integrated_offline_replay": item.current_integrated_offline_replay_binding,
                    "scenario_replay": item.current_scenario_replay_binding,
                    "backtest": item.current_backtest_binding,
                    "runtime_reference": item.current_runtime_semantics_reference,
                },
                "canonical_expected_path": (
                    "Unified canonical decision-chain binding across Integrated Offline Replay,"
                    " Scenario Replay, Backtest wiring, and documented Runtime reference"
                ),
                "missing_binding": item.missing_binding_if_any,
                "forbidden_mutation_risk": (
                    "Trading logic, Master V2 semantics, Double Play semantics,"
                    " risk/sizing math, Safety Kernel/runtime authority, execution behavior"
                ),
                "narrow_reuse_first_remediation": item.recommended_next_slice,
                "evidence_refs": list(item.evidence_refs),
            }
        )
    return tuple(records)


def render_parity_gap_matrix_json_v0() -> str:
    from trading.master_v2.surface_p_final_flags_fail_closed_contract_v0 import (
        evaluate_current_head_surface_p_final_flags_fail_closed_contract_v0,
        surface_p_final_flags_result_to_dict_v0,
    )
    from trading.master_v2.surface_p_offline_complete_runtime_bridge_bound_not_activated_contract_v0 import (
        evaluate_surface_p_offline_complete_runtime_bridge_bound_not_activated_contract_v0,
        surface_p_semantic_status_to_dict_v0,
    )

    surface_p_semantic = (
        evaluate_surface_p_offline_complete_runtime_bridge_bound_not_activated_contract_v0()
    )
    surface_p_proof_input_binding = get_surface_p_required_proof_input_binding_v0()
    final_flags = evaluate_current_head_surface_p_final_flags_fail_closed_contract_v0()
    surfaces = []
    for item in parity_surface_assessments_v0():
        surface_entry: dict[str, Any] = {
            "surface_id": item.surface_id,
            "surface_name": item.surface_name,
            "parity_status": item.parity_status,
            "matrix_status": normalize_matrix_status_v0(item.parity_status),
            "canonical_owner_files": list(item.canonical_owner_files),
            "missing_binding": item.missing_binding_if_any or None,
            "recommended_next_slice": item.recommended_next_slice,
            "forbidden_runtime_authority_confirmed": item.forbidden_runtime_authority_confirmed,
        }
        if item.surface_id == "P":
            surface_entry["surface_p_semantic"] = dict(
                surface_p_semantic_status_to_dict_v0(surface_p_semantic)
            )
            surface_entry["surface_p_required_proof_input_binding"] = dict(
                surface_p_proof_input_binding
            )
            if surface_p_semantic.surface_p_overall_status == "PARTIAL_RUNTIME_ACTIVATION_PENDING":
                surface_entry["matrix_status"] = "PARTIAL_RUNTIME_ACTIVATION_PENDING"
        surfaces.append(surface_entry)
    counts = parity_status_counts_v0()
    gap_records = parity_gap_records_v0()
    payload = {
        "assessment_version": FULL_CANONICAL_SYSTEM_BACKTEST_PARITY_GAP_ASSESSMENT_LAYER_VERSION,
        "assessment_owner": FULL_CANONICAL_SYSTEM_BACKTEST_PARITY_GAP_ASSESSMENT_OWNER,
        "next_recommended_slice": NEXT_RECOMMENDED_SLICE,
        "summary": {
            "parity_surfaces_assessed": len(surfaces),
            "pass_surfaces": counts["PASS"],
            "partial_surfaces": counts["PARTIAL"],
            "gap_surfaces": counts["GAP"],
            "not_applicable_surfaces": counts["NOT_APPLICABLE"],
            "matrix_gap_count": len(gap_records),
            "full_canonical_chain_wired": final_flags.full_canonical_chain_wired,
            "backtest_runtime_decision_parity_pass": (
                final_flags.backtest_runtime_decision_parity_pass
            ),
            "system_economic_evidence_admissible": (
                final_flags.system_economic_evidence_admissible
            ),
        },
        "surfaces": surfaces,
        "gap_records": list(gap_records),
        "surface_p_semantic": dict(surface_p_semantic_status_to_dict_v0(surface_p_semantic)),
        "surface_p_required_proof_input_binding": dict(surface_p_proof_input_binding),
        "final_flags": dict(surface_p_final_flags_result_to_dict_v0(final_flags)),
    }
    return json.dumps(payload, indent=2, sort_keys=True) + "\n"


def parity_status_counts_v0() -> Mapping[str, int]:
    assessments = parity_surface_assessments_v0()
    counts = {"PASS": 0, "PARTIAL": 0, "GAP": 0, "NOT_APPLICABLE": 0}
    for item in assessments:
        counts[item.parity_status] += 1
    return counts


def render_parity_gap_matrix_markdown_v0() -> str:
    from trading.master_v2.surface_p_final_flags_fail_closed_contract_v0 import (
        evaluate_current_head_surface_p_final_flags_fail_closed_contract_v0,
    )

    final_flags = evaluate_current_head_surface_p_final_flags_fail_closed_contract_v0()
    lines = [
        "# Full Canonical System Backtest Parity Gap Matrix v0",
        "",
        "Assessment-only. No runtime authority. No economic evaluation.",
        "",
        f"NEXT_RECOMMENDED_SLICE={NEXT_RECOMMENDED_SLICE}",
        "",
        "| ID | Surface | Status | Canonical Owner(s) | Missing Binding |",
        "|----|---------|--------|------------------|-----------------|",
    ]
    for item in parity_surface_assessments_v0():
        owners = ", ".join(f"`{p}`" for p in item.canonical_owner_files[:2])
        if len(item.canonical_owner_files) > 2:
            owners += ", ..."
        missing = item.missing_binding_if_any or "—"
        lines.append(
            f"| {item.surface_id} | {item.surface_name} | {item.parity_status}"
            f" | {owners} | {missing} |"
        )
    counts = parity_status_counts_v0()
    lines.extend(
        [
            "",
            "## Summary",
            "",
            f"PARITY_SURFACES_ASSESSED={len(parity_surface_assessments_v0())}",
            f"PASS_SURFACES={counts['PASS']}",
            f"PARTIAL_SURFACES={counts['PARTIAL']}",
            f"GAP_SURFACES={counts['GAP']}",
            f"NOT_APPLICABLE_SURFACES={counts['NOT_APPLICABLE']}",
            "",
            f"FULL_CANONICAL_CHAIN_WIRED={str(final_flags.full_canonical_chain_wired).lower()}",
            (
                "BACKTEST_RUNTIME_DECISION_PARITY_PASS="
                f"{str(final_flags.backtest_runtime_decision_parity_pass).lower()}"
            ),
            (
                "SYSTEM_ECONOMIC_EVIDENCE_ADMISSIBLE="
                f"{str(final_flags.system_economic_evidence_admissible).lower()}"
            ),
        ]
    )
    return "\n".join(lines) + "\n"


def scan_changed_paths_for_forbidden_runtime_v0(
    changed_paths: Sequence[str],
) -> Tuple[bool, Tuple[str, ...]]:
    violations: list[str] = []
    for path in changed_paths:
        normalized = path.replace("\\", "/")
        if any(normalized.startswith(prefix) for prefix in FORBIDDEN_CHANGED_PATH_PREFIXES):
            if normalized not in ALLOWED_SLICE_CHANGED_PATH_PREFIXES:
                violations.append(normalized)
    return (len(violations) == 0, tuple(violations))
