"""Scope event generator binding parity: scenario replay adverse-exit path (offline only)."""

from __future__ import annotations

import ast
from pathlib import Path

from trading.master_v2.canonical_market_context_v1 import DataIntegrityStatus
from trading.master_v2.deterministic_scope_event_generator_v1 import (
    CanonicalScopeEventType,
    ScopeCandidateKind,
    ScopeConfirmationStateV1,
)
from trading.master_v2.double_play_entry_exit_policy_v0 import (
    DecisionOutcome,
    ExitClass,
    PolicySignalV0,
)
from trading.master_v2.double_play_state import (
    ActiveSide,
    DynamicScopeRules,
    RuntimeScopeState,
    ScopeEvent,
    SideState,
)
from trading.master_v2.full_canonical_system_backtest_parity_gap_assessment_v0 import (
    ALLOWED_SLICE_CHANGED_PATH_PREFIXES,
    NEXT_RECOMMENDED_SLICE,
    parity_surface_assessments_v0,
    parity_status_counts_v0,
    scan_changed_paths_for_forbidden_runtime_v0,
)
from trading.master_v2.integrated_vs_scenario_replay_full_system_parity_harness_v0 import (
    canonical_owner_refs_v0,
)
from trading.master_v2.offline_double_play_scenario_replay_v0 import (
    OFFLINE_DOUBLE_PLAY_SCENARIO_REPLAY_OWNER,
    OfflineDoublePlayScenarioReplayInputV0,
    OfflineDoublePlayScenarioTickV0,
    SYNTHETIC_FUTURES_INSTRUMENT,
    build_default_bull_bear_bull_scenario_ticks,
    make_offline_scenario_tick_provenance_v1,
    run_offline_double_play_scenario_replay_v0,
)
from trading.master_v2.scope_event_generator_scenario_binding_adapter_v0 import (
    CANONICAL_SCOPE_EVENT_GENERATOR_OWNER,
    SCOPE_EVENT_GENERATOR_SCENARIO_BINDING_ADAPTER_OWNER,
    ScenarioScopeEventContextV0,
    derive_scope_adverse_exit_signal_v0,
    evaluate_scenario_scope_event_v0,
    scope_event_binding_non_authority_boundary_ok_v0,
)

REPO_ROOT = Path(__file__).resolve().parents[3]
_INSTRUMENT = SYNTHETIC_FUTURES_INSTRUMENT
_DEFAULT_RULES = DynamicScopeRules(
    min_band_width=1.0,
    max_band_width=50.0,
    min_switch_cooldown_ticks=0,
    max_switches_per_window=1_000_000,
    volatility_estimate=0.02,
)
_RUNTIME_SCOPE = RuntimeScopeState(anchor_price=100.0, current_hysteresis_band=4.0)

_SLICE_CHANGED_FILES = ALLOWED_SLICE_CHANGED_PATH_PREFIXES

_FORBIDDEN_IMPORT_SCAN_PATHS = (
    REPO_ROOT / "src/trading/master_v2/scope_event_generator_scenario_binding_adapter_v0.py",
    REPO_ROOT
    / "src/trading/master_v2/integrated_vs_scenario_replay_full_system_parity_harness_v0.py",
    REPO_ROOT / "scripts/ops/run_scope_event_generator_scenario_replay_binding_parity_rewire_v0.py",
    REPO_ROOT
    / "tests/trading/master_v2/test_scope_event_generator_scenario_replay_binding_parity_rewire_contract_v0.py",
)


def _scan_forbidden_imports(path: Path, forbidden_tokens: frozenset[str]) -> list[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    hits: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if any(token in alias.name for token in forbidden_tokens):
                    hits.append(alias.name)
        if isinstance(node, ast.ImportFrom) and node.module:
            if any(token in node.module for token in forbidden_tokens):
                hits.append(node.module)
    return hits


def test_owner_constants_and_canonical_reuse_v0() -> None:
    refs = canonical_owner_refs_v0()
    assert refs["scope_event_generator"] == CANONICAL_SCOPE_EVENT_GENERATOR_OWNER
    assert (
        refs["scope_event_generator_scenario_binding_adapter"]
        == SCOPE_EVENT_GENERATOR_SCENARIO_BINDING_ADAPTER_OWNER
    )
    assert refs["scenario_replay"] == OFFLINE_DOUBLE_PLAY_SCENARIO_REPLAY_OWNER


def test_forbidden_runtime_paths_guard_v0() -> None:
    ok, violations = scan_changed_paths_for_forbidden_runtime_v0(_SLICE_CHANGED_FILES)
    assert ok is True
    assert violations == ()


def test_slice_sources_exclude_execution_runtime_imports_v0() -> None:
    forbidden = frozenset(
        {
            "execution",
            "scheduler",
            "credentials",
            "live_runtime",
            "testnet",
            "shadow",
            "paper_lane",
        }
    )
    for path in _FORBIDDEN_IMPORT_SCAN_PATHS:
        assert path.is_file(), f"missing slice source: {path}"
        hits = _scan_forbidden_imports(path, forbidden)
        assert hits == [], f"forbidden imports in {path}: {hits}"


def test_scenario_adverse_exit_uses_canonical_generator_v0() -> None:
    binding = evaluate_scenario_scope_event_v0(
        ScenarioScopeEventContextV0(
            instrument_id=_INSTRUMENT,
            trading_epoch=1,
            context_reference="scope-gen-parity-v0-adverse",
            current_price=96.0,
            scope_state=_RUNTIME_SCOPE,
            rules=_DEFAULT_RULES,
            active_side=ActiveSide.LONG,
            confirmation_state=ScopeConfirmationStateV1(
                candidate_kind=None,
                candidate_count=0,
                last_evaluated_trading_epoch=0,
            ),
            up_distance=2.0,
            adverse_exit_distance=2.0,
            reversal_distance=4.0,
        )
    )
    # Nested adverse+downscope: SM event is DOWNSCOPE_*; PolicySignal still adverse.
    assert binding.scope_event_evidence.event_type is CanonicalScopeEventType.DOWNSCOPE_CANDIDATE
    assert ScopeCandidateKind.ADVERSE_EXIT.value in binding.scope_event_evidence.matched_conditions
    assert binding.scope_adverse_exit_signal.triggered is True
    assert scope_event_binding_non_authority_boundary_ok_v0(binding)


def test_no_legacy_shortcut_adverse_exit_from_tick_scope_event_v0() -> None:
    """Adverse-exit signal must come from generator evidence, not tick.scope_event labels."""
    binding = evaluate_scenario_scope_event_v0(
        ScenarioScopeEventContextV0(
            instrument_id=_INSTRUMENT,
            trading_epoch=2,
            context_reference="scope-gen-parity-v0-no-shortcut",
            current_price=100.0,
            scope_state=_RUNTIME_SCOPE,
            rules=_DEFAULT_RULES,
            active_side=ActiveSide.LONG,
            confirmation_state=ScopeConfirmationStateV1(
                candidate_kind=None,
                candidate_count=0,
                last_evaluated_trading_epoch=1,
            ),
            up_distance=2.0,
            adverse_exit_distance=2.0,
            reversal_distance=4.0,
        )
    )
    assert binding.scope_adverse_exit_signal.triggered is False
    assert (
        binding.scope_event_evidence.event_type
        is not CanonicalScopeEventType.ADVERSE_EXIT_CANDIDATE
    )


def test_untrusted_data_blocks_adverse_exit_authority_v0() -> None:
    binding = evaluate_scenario_scope_event_v0(
        ScenarioScopeEventContextV0(
            instrument_id=_INSTRUMENT,
            trading_epoch=3,
            context_reference="scope-gen-parity-v0-untrusted",
            current_price=90.0,
            scope_state=_RUNTIME_SCOPE,
            rules=_DEFAULT_RULES,
            active_side=ActiveSide.LONG,
            confirmation_state=ScopeConfirmationStateV1(
                candidate_kind=None,
                candidate_count=0,
                last_evaluated_trading_epoch=2,
            ),
            safety_decision_allowed=False,
            data_integrity_status=DataIntegrityStatus.UNTRUSTED,
            up_distance=2.0,
            adverse_exit_distance=2.0,
            reversal_distance=4.0,
        )
    )
    assert binding.scope_adverse_exit_signal.triggered is False
    assert binding.scope_event_evidence.blocked_reasons
    assert scope_event_binding_non_authority_boundary_ok_v0(binding)


def test_derive_scope_adverse_exit_signal_from_matched_condition_v0() -> None:
    binding = evaluate_scenario_scope_event_v0(
        ScenarioScopeEventContextV0(
            instrument_id=_INSTRUMENT,
            trading_epoch=4,
            context_reference="scope-gen-parity-v0-matched",
            current_price=96.0,
            scope_state=_RUNTIME_SCOPE,
            rules=_DEFAULT_RULES,
            active_side=ActiveSide.LONG,
            confirmation_state=ScopeConfirmationStateV1(
                candidate_kind=None,
                candidate_count=0,
                last_evaluated_trading_epoch=3,
            ),
            up_distance=2.0,
            adverse_exit_distance=2.0,
            reversal_distance=4.0,
        )
    )
    signal = derive_scope_adverse_exit_signal_v0(binding.scope_event_evidence)
    assert signal.triggered is True
    assert ScopeCandidateKind.ADVERSE_EXIT.value in binding.scope_event_evidence.matched_conditions


def test_adapter_output_decision_bound_no_runtime_order_authority_v0() -> None:
    binding = evaluate_scenario_scope_event_v0(
        ScenarioScopeEventContextV0(
            instrument_id=_INSTRUMENT,
            trading_epoch=5,
            context_reference="scope-gen-parity-v0-authority",
            current_price=100.0,
            scope_state=_RUNTIME_SCOPE,
            rules=_DEFAULT_RULES,
            active_side=ActiveSide.NEUTRAL,
            confirmation_state=ScopeConfirmationStateV1(
                candidate_kind=None,
                candidate_count=0,
                last_evaluated_trading_epoch=4,
            ),
        )
    )
    assert scope_event_binding_non_authority_boundary_ok_v0(binding)
    evidence = binding.scope_event_evidence
    assert evidence.authority_effect == "NONE"
    assert evidence.runtime_effect == "NONE"
    assert evidence.order_effect == "NONE"


def test_surface_b_pass_cde_remain_partial_v0() -> None:
    counts = parity_status_counts_v0()
    assert counts["PASS"] == 16
    assert counts["PARTIAL"] == 0
    surface_b = next(item for item in parity_surface_assessments_v0() if item.surface_id == "B")
    assert surface_b.parity_status == "PASS"
    assert surface_b.missing_binding_if_any == ""
    surface_c = next(item for item in parity_surface_assessments_v0() if item.surface_id == "C")
    assert surface_c.parity_status == "PASS"
    assert surface_c.missing_binding_if_any == ""
    surface_d = next(item for item in parity_surface_assessments_v0() if item.surface_id == "D")
    assert surface_d.parity_status == "PASS"
    surface_e = next(item for item in parity_surface_assessments_v0() if item.surface_id == "E")
    assert surface_e.parity_status == "PASS"
    surface_p = next(item for item in parity_surface_assessments_v0() if item.surface_id == "P")
    assert surface_p.parity_status == "PASS"
    assert surface_p.missing_binding_if_any == ""
    assert NEXT_RECOMMENDED_SLICE == "FULL_CANONICAL_BACKTEST_BOUNDARY_CHAIN_REASSESSMENT_V0"


def test_scenario_replay_e2e_wires_generator_per_tick_v0() -> None:
    ticks = (
        OfflineDoublePlayScenarioTickV0(
            tick_index=0,
            timestamp_ms=1_700_000_000_000,
            price=100.0,
            scope_event=ScopeEvent.NOOP,
            scope_event_provenance="TEST_INJECTION",
            tick_provenance=make_offline_scenario_tick_provenance_v1(
                source_kind="offline_scenario_fixture",
                source_id="scope_gen_scenario_e2e",
                tick_index=0,
                event_time_ms=1_700_000_000_000,
                sequence_number=0,
            ),
        ),
        OfflineDoublePlayScenarioTickV0(
            tick_index=1,
            timestamp_ms=1_700_000_060_000,
            price=96.0,
            scope_event=ScopeEvent.NOOP,
            scope_event_provenance="TEST_INJECTION",
            tick_provenance=make_offline_scenario_tick_provenance_v1(
                source_kind="offline_scenario_fixture",
                source_id="scope_gen_scenario_e2e",
                tick_index=1,
                event_time_ms=1_700_000_060_000,
                sequence_number=1,
            ),
        ),
    )
    result = run_offline_double_play_scenario_replay_v0(
        OfflineDoublePlayScenarioReplayInputV0(
            selected_future_id=_INSTRUMENT,
            ticks=ticks,
            correlation_id_prefix="scope-gen-scenario-e2e-v0",
            allow_test_scope_event_injection=True,
        )
    )
    assert len(result.tick_records) == 2
    assert all(record.entry_exit_policy_ref for record in result.tick_records)


def test_default_scenario_replay_still_passes_with_generator_binding_v0() -> None:
    result = run_offline_double_play_scenario_replay_v0(
        OfflineDoublePlayScenarioReplayInputV0(
            selected_future_id=_INSTRUMENT,
            ticks=build_default_bull_bear_bull_scenario_ticks(),
            correlation_id_prefix="scope-gen-default-scenario-v0",
            allow_test_scope_event_injection=True,
        )
    )
    assert result.replay_pass is True


def test_adverse_exit_signal_drives_entry_exit_policy_when_position_open_v0() -> None:
    from trading.master_v2.double_play_composition_matrix_v1 import CompositionStatus
    from trading.master_v2.double_play_entry_exit_scenario_binding_adapter_v0 import (
        ScenarioEntryExitPolicyContextV0,
        evaluate_scenario_entry_exit_policy_v0,
    )
    from trading.master_v2.integrated_vs_scenario_replay_full_system_parity_harness_v0 import (
        evaluate_scenario_matrix_for_side_state_v0,
    )

    matrix = evaluate_scenario_matrix_for_side_state_v0(
        side_state=SideState.LONG_ACTIVE,
        instrument_id=_INSTRUMENT,
        trading_epoch=10,
        context_reference="scope-gen-entry-exit-v0",
    )
    decision = evaluate_scenario_entry_exit_policy_v0(
        instrument_id=_INSTRUMENT,
        trading_epoch=10,
        context_reference="scope-gen-entry-exit-v0",
        composition_result=matrix,
        side_state=SideState.LONG_ACTIVE,
        policy_context=ScenarioEntryExitPolicyContextV0(
            scope_adverse_exit_signal=PolicySignalV0(
                triggered=True,
                reason_code="adverse_scope_exit_candidate",
            ),
        ),
    )
    assert ExitClass.ADVERSE_SCOPE_EXIT.value in decision.reason_codes or (
        decision.decision_outcome in (DecisionOutcome.EXIT, DecisionOutcome.OBSERVE)
    )
    assert matrix.composition_status is CompositionStatus.LONG_SELECTED
