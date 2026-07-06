"""
Offline-only gap assessment registry: Integrated Offline Replay vs Scenario Replay
vs Backtest vs Runtime decision parity surfaces (v0).

Assessment-only. No runtime authority, no economic evaluation, no trading semantic change.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Mapping, Sequence, Tuple

FULL_CANONICAL_SYSTEM_BACKTEST_PARITY_GAP_ASSESSMENT_LAYER_VERSION = "v0"
FULL_CANONICAL_SYSTEM_BACKTEST_PARITY_GAP_ASSESSMENT_OWNER = (
    "trading.master_v2.full_canonical_system_backtest_parity_gap_assessment_v0"
)

ParityStatus = Literal["PASS", "PARTIAL", "GAP", "NOT_APPLICABLE"]

NEXT_RECOMMENDED_SLICE = "CANONICAL_ORDER_INTENT_OFFLINE_REPLAY_BINDING_PARITY_REWIRE_V0"

ALLOWED_SLICE_CHANGED_PATH_PREFIXES: Tuple[str, ...] = (
    "src/trading/master_v2/full_canonical_system_backtest_parity_gap_assessment_v0.py",
    "scripts/ops/run_full_canonical_system_backtest_parity_gap_assessment_v0.py",
    "tests/trading/master_v2/test_full_canonical_system_backtest_parity_gap_assessment_contract_v0.py",
    "docs/research/FULL_CANONICAL_SYSTEM_BACKTEST_PARITY_GAP_ASSESSMENT_V0.md",
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


def parity_surface_assessments_v0() -> Tuple[ParitySurfaceAssessmentV0, ...]:
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
                " -> injected ScopeEvent ticks -> transition_state()"
            ),
            current_backtest_binding=(
                "backtest/mv2_research_wiring_v1.run_mv2_research_backtest_wiring_v1"
                " -> integrated replay (indirect)"
            ),
            current_runtime_semantics_reference=(
                "canonical_core_runtime_integration_bridge_v0 (BOUND_NOT_ACTIVATED);"
                " legacy_runtime_entrypoint_guard_v0"
            ),
            parity_status="PARTIAL",
            evidence_refs=(
                "tests/trading/master_v2/test_offline_master_v2_double_play_scenario_replay_binding_contract_v0.py",
                "tests/trading/master_v2/test_integrated_offline_trading_logic_replay_v1.py",
                "tests/trading/master_v2/test_integrated_vs_scenario_replay_full_system_parity_contract_suite_v0.py",
            ),
            missing_binding_if_any=(
                "End-to-end state-switch parity Integrated tick vs Scenario tick"
                " (not only composition matrix alignment)"
            ),
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
                "offline_double_play_scenario_replay_v0: ScopeEvent on ticks only;"
                " no full generator + entry-exit chain per tick"
            ),
            current_backtest_binding=(
                "mv2_research_wiring_v1 adverse_exit_distance=60.0 -> integrated replay"
            ),
            current_runtime_semantics_reference=(
                "canonical_core_runtime_integration_bridge_v0 passes scope params to integrated replay"
            ),
            parity_status="PARTIAL",
            evidence_refs=(
                "tests/trading/master_v2/test_deterministic_scope_event_generator_v1.py",
                "tests/trading/master_v2/test_double_play_entry_exit_policy_v0.py",
            ),
            missing_binding_if_any=(
                "Scenario replay binding to deterministic_scope_event_generator_v1"
                " + entry-exit adverse-exit path"
            ),
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
                "double_play_composition_scenario_matrix_adapter_v0"
                " -> evaluate_scenario_matrix_composition_v0()"
            ),
            current_backtest_binding="Integrated replay (default PositionManagementContext.FLAT)",
            current_runtime_semantics_reference=(
                "canonical_core_runtime_integration_bridge_v0 -> integrated replay"
            ),
            parity_status="PARTIAL",
            evidence_refs=(
                "tests/trading/master_v2/test_integrated_vs_scenario_replay_full_system_parity_contract_suite_v0.py::test_5_reversal_preparation_boundary_parity_v0",
                "tests/trading/master_v2/test_double_play_composition_matrix_v1.py",
                "tests/trading/master_v2/test_double_play_entry_exit_policy_v0.py",
            ),
            missing_binding_if_any=(
                "Scenario tick -> entry-exit REVERSAL_PREPARATION_EXIT policy evaluation"
            ),
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
                "offline_double_play_scenario_replay_v0 -> transition_state() only;"
                " entry-exit policy not per tick"
            ),
            current_backtest_binding=(
                "Integrated replay defaults venue_flat=True, ExistingPositionSide.NONE"
            ),
            current_runtime_semantics_reference=(
                "double_play_state.transition_state (DOUBLE_PLAY_BULL_BEAR_REFERENCE_V0)"
            ),
            parity_status="PARTIAL",
            evidence_refs=(
                "tests/trading/master_v2/test_double_play_entry_exit_policy_v0.py",
                "tests/trading/master_v2/test_offline_master_v2_double_play_scenario_replay_binding_contract_v0.py",
            ),
            missing_binding_if_any=(
                "Scenario replay -> evaluate_double_play_entry_exit_policy_v0()"
                " for flat-before-opposite-side invariant"
            ),
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
                "offline_double_play_scenario_replay_v0 -> evaluate_survival_envelope()"
                " + project_strategy_suitability() -> matrix adapter stubs"
            ),
            current_backtest_binding="Integrated v1 path via mv2_research_wiring_v1",
            current_runtime_semantics_reference=(
                "canonical_core_runtime_integration_bridge_v0 v1 policies"
            ),
            parity_status="PARTIAL",
            evidence_refs=(
                "tests/trading/master_v2/test_double_play_composition_scenario_matrix_parity_contract_v0.py",
                "tests/trading/master_v2/test_directional_assessment_v1.py",
            ),
            missing_binding_if_any=(
                "Scenario direct binding to survival_assessment_v1 / suitability_binding_v1"
                " instead of legacy envelope projection"
            ),
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
                "No evaluate_capital_risk_sizing_v1 wiring in mv2_research_wiring_v1"
            ),
            current_runtime_semantics_reference=(
                "canonical_core_runtime_integration_intent_pipeline_bridge_v0"
                " Slice B BOUND_NOT_ACTIVATED"
            ),
            parity_status="PARTIAL",
            evidence_refs=(
                "tests/governance/test_capital_risk_sizing_v1.py",
                "tests/trading/master_v2/test_offline_master_v2_double_play_scenario_replay_binding_contract_v0.py",
                "tests/trading/master_v2/test_capital_risk_sizing_offline_replay_binding_parity_rewire_contract_v0.py",
            ),
            missing_binding_if_any=("Backtest mv2_research_wiring_v1 unified sizing chain parity"),
            recommended_next_slice=NEXT_RECOMMENDED_SLICE,
        ),
        ParitySurfaceAssessmentV0(
            surface_id="I",
            surface_name="Canonical Order Intent boundary",
            canonical_owner_files=(
                "src/governance/canonical_order_intent_v1.py",
                "src/governance/runbook_progress_registry_v1.py",
            ),
            current_integrated_offline_replay_binding="NOT_BOUND (explicit no order effects)",
            current_scenario_replay_binding=(
                "NOT_BOUND (execution_intent_digest, zero-order boundary)"
            ),
            current_backtest_binding="NOT_BOUND",
            current_runtime_semantics_reference=(
                "canonical_core_runtime_integration_intent_pipeline_bridge_v0"
                " build_canonical_order_intent_v1 BOUND_NOT_ACTIVATED"
            ),
            parity_status="NOT_APPLICABLE",
            evidence_refs=(
                "tests/governance/test_canonical_order_intent_v1.py",
                "tests/governance/test_intent_compatibility_firewall_v1.py",
            ),
            missing_binding_if_any=(
                "Runtime bridge Slice B activation (out of offline assessment scope)"
            ),
            recommended_next_slice=NEXT_RECOMMENDED_SLICE,
        ),
        ParitySurfaceAssessmentV0(
            surface_id="J",
            surface_name="Safety Kernel semantics",
            canonical_owner_files=(
                "src/meta/learning_loop/runtime_eligibility_v1.py",
                "src/meta/learning_loop/killswitch_writer_fencing_and_independent_read_paths_v1.py",
            ),
            current_integrated_offline_replay_binding=(
                "SafetyMode + safety_exit_signal in entry-exit input (no kernel read)"
            ),
            current_scenario_replay_binding=(
                "evaluate_master_v2_local_flow_v1 SafetyKillSwitchHandoffV1;"
                " tick.safety_decision_allowed"
            ),
            current_backtest_binding="Default SafetyMode.NORMAL in integrated input",
            current_runtime_semantics_reference=(
                "docs/ops/specs/FUTURES_MASTER_V2_RUNTIME_GOVERNANCE_BOUNDARY_CONTRACT_V0.md"
            ),
            parity_status="PARTIAL",
            evidence_refs=(
                "tests/meta/test_killswitch_writer_fencing_and_independent_read_paths_v1.py",
                "tests/meta/test_runtime_eligibility_v1.py",
            ),
            missing_binding_if_any=(
                "Unified safety-kernel semantics across Integrated / Scenario / Runtime"
            ),
            recommended_next_slice=NEXT_RECOMMENDED_SLICE,
        ),
        ParitySurfaceAssessmentV0(
            surface_id="K",
            surface_name="KillSwitch boundary semantics",
            canonical_owner_files=(
                "src/meta/learning_loop/killswitch_writer_fencing_and_independent_read_paths_v1.py",
                "src/risk_layer/kill_switch/core.py",
            ),
            current_integrated_offline_replay_binding=(
                "safety_exit_signal + SafetyMode in entry-exit (no KillSwitch state machine)"
            ),
            current_scenario_replay_binding=(
                "ScopeEvent.KILL_ALL_REQUIRED, SideState.KILL_ALL, SafetyKillSwitchHandoffV1"
            ),
            current_backtest_binding="No KillSwitch state file",
            current_runtime_semantics_reference=(
                "src/ops/gates/risk_gate.py; FUTURES_RISK_SAFETY_KILLSWITCH_CONTRACT_V0"
            ),
            parity_status="PARTIAL",
            evidence_refs=(
                "tests/trading/master_v2/test_offline_master_v2_double_play_scenario_replay_binding_contract_v0.py::test_killswitch_blocks_activation",
                "tests/ops/test_bounded_futures_testnet_risk_killswitch_lifecycle_integration_contract_v0.py",
            ),
            missing_binding_if_any=(
                "Integrated replay explicit KillSwitch state-machine or kernel-read binding"
            ),
            recommended_next_slice=NEXT_RECOMMENDED_SLICE,
        ),
        ParitySurfaceAssessmentV0(
            surface_id="L",
            surface_name="Reconciliation and Unknown Outcome semantics",
            canonical_owner_files=(
                "src/trading/master_v2/double_play_entry_exit_policy_v0.py",
                "src/governance/capital_risk_sizing_v1.py",
                "src/meta/learning_loop/runtime_state_reconciliation_v1.py",
            ),
            current_integrated_offline_replay_binding=(
                "reconciliation_state + PositionState.SUBMISSION_UNKNOWN in entry-exit input"
            ),
            current_scenario_replay_binding="NOT bound per tick",
            current_backtest_binding="Default ReconciliationState.RECONCILED",
            current_runtime_semantics_reference="src/ops/recon/reconcile.py",
            parity_status="PARTIAL",
            evidence_refs=(
                "tests/trading/master_v2/test_double_play_entry_exit_policy_v0.py",
                "tests/governance/test_canonical_order_intent_v1.py",
            ),
            missing_binding_if_any=(
                "Scenario replay reconciliation/unknown-outcome fixtures + parity tests"
            ),
            recommended_next_slice=NEXT_RECOMMENDED_SLICE,
        ),
        ParitySurfaceAssessmentV0(
            surface_id="M",
            surface_name="Promotion Gate boundary",
            canonical_owner_files=(
                "src/governance/promotion_loop/promotion_economic_gate_v1.py",
                "docs/ops/specs/MASTER_V2_PROMOTION_STATE_MACHINE_V1.md",
            ),
            current_integrated_offline_replay_binding="NOT_APPLICABLE (non-authorizing offline)",
            current_scenario_replay_binding="NOT_APPLICABLE",
            current_backtest_binding=(
                "Indirect research-fleet bindings; not promotion gate itself"
            ),
            current_runtime_semantics_reference=(
                "governance/promotion_loop/safety.py global_promotion_lock"
            ),
            parity_status="NOT_APPLICABLE",
            evidence_refs=(
                "tests/trading/master_v2/test_offline_governance_tick_harness_v0.py",
                "docs/governance/authority_conflict_matrix_v1.md",
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
                "CanonicalTradingDecisionEvidenceV1 with decision_precedence_trace, reason_codes"
            ),
            current_scenario_replay_binding=(
                "build_dashboard_display_snapshot() + evaluate_master_v2_local_flow_v1 snapshot/digest"
            ),
            current_backtest_binding="Evidence digest in mv2_research_wiring chain",
            current_runtime_semantics_reference=(
                "docs/ops/specs/MASTER_V2_DECISION_AUTHORITY_MAP_V1.md"
            ),
            parity_status="PARTIAL",
            evidence_refs=(
                "tests/trading/master_v2/test_offline_master_v2_double_play_scenario_replay_binding_contract_v0.py",
                "tests/trading/master_v2/test_integrated_offline_trading_logic_replay_v1.py",
            ),
            missing_binding_if_any=(
                "Common explainability envelope across Integrated vs Scenario"
                " (harness extracts different field sets)"
            ),
            recommended_next_slice=NEXT_RECOMMENDED_SLICE,
        ),
        ParitySurfaceAssessmentV0(
            surface_id="O",
            surface_name="Feedback / Learning boundary",
            canonical_owner_files=(
                "src/meta/learning_loop/runtime_observation_feedback_v1.py",
                "src/meta/learning_loop/deploy_inactive_v1.py",
            ),
            current_integrated_offline_replay_binding="NONE (explicit no learning effects)",
            current_scenario_replay_binding="NONE",
            current_backtest_binding="Research metrics in mv2_research_wiring; not feedback loop",
            current_runtime_semantics_reference=(
                "docs/ops/specs/MASTER_V2_LEARNING_AI_AUTONOMY_INVENTORY_V1.md"
            ),
            parity_status="NOT_APPLICABLE",
            evidence_refs=("docs/governance/authority_conflict_matrix_v1.md",),
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
            current_backtest_binding=("run_mv2_research_backtest_wiring_v1() -> integrated only"),
            current_runtime_semantics_reference=(
                "canonical_core_runtime_integration_bridge_v0 +"
                " canonical_core_runtime_integration_intent_pipeline_bridge_v0"
                " both BOUND_NOT_ACTIVATED"
            ),
            parity_status="PARTIAL",
            evidence_refs=(
                "tests/trading/master_v2/test_integrated_vs_scenario_replay_full_system_parity_contract_suite_v0.py",
                "scripts/ops/run_integrated_vs_scenario_replay_full_system_parity_contract_suite_v0.py",
                "docs/governance/authority_conflict_matrix_v1.md",
            ),
            missing_binding_if_any=(
                "Full 4-way parity suite including backtest bar wiring,"
                " runtime bridge activation, entry-exit/capital/intent surfaces"
            ),
            recommended_next_slice=NEXT_RECOMMENDED_SLICE,
        ),
    )


def parity_status_counts_v0() -> Mapping[str, int]:
    assessments = parity_surface_assessments_v0()
    counts = {"PASS": 0, "PARTIAL": 0, "GAP": 0, "NOT_APPLICABLE": 0}
    for item in assessments:
        counts[item.parity_status] += 1
    return counts


def render_parity_gap_matrix_markdown_v0() -> str:
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
            "FULL_CANONICAL_CHAIN_WIRED=false",
            "BACKTEST_RUNTIME_DECISION_PARITY_PASS=false",
            "SYSTEM_ECONOMIC_EVIDENCE_ADMISSIBLE=false",
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
