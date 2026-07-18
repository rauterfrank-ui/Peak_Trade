"""Survival/suitability binding parity: scenario replay canonical owners (offline only)."""

from __future__ import annotations

import ast
from dataclasses import replace
from pathlib import Path

from trading.master_v2.double_play_composition import (
    DoublePlayCompositionInput,
    DoublePlayCompositionStatus,
    RequestedSide,
)
from trading.master_v2.double_play_composition_matrix_v1 import CompositionStatus
from trading.master_v2.double_play_composition_scenario_matrix_adapter_v0 import (
    compose_double_play_scenario_via_canonical_matrix_v0,
)
from trading.master_v2.double_play_state import SideState, TransitionDecision
from trading.master_v2.double_play_suitability import (
    SuitabilityClass,
    SuitabilityProjectionDecision,
    project_strategy_suitability,
)
from trading.master_v2.double_play_survival import (
    SurvivalEnvelopeDecision,
    SurvivalEnvelopeStatus,
    evaluate_survival_envelope,
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
    evaluate_scenario_matrix_for_side_state_v0,
)
from trading.master_v2.offline_double_play_scenario_replay_v0 import (
    OFFLINE_DOUBLE_PLAY_SCENARIO_REPLAY_OWNER,
    SYNTHETIC_FUTURES_INSTRUMENT,
    _survival_envelope,
    _suitability_input,
    build_default_bull_bear_bull_scenario_ticks,
    run_offline_double_play_scenario_replay_v0,
    OfflineDoublePlayScenarioReplayInputV0,
)
from trading.master_v2.survival_assessment_v1 import (
    SurvivalAssessmentStatus,
    SurvivalHardFailReason,
    SurvivalMetricInputsV1,
)
from trading.master_v2.survival_suitability_scenario_binding_adapter_v0 import (
    CANONICAL_SUITABILITY_BINDING_OWNER,
    CANONICAL_SURVIVAL_ASSESSMENT_OWNER,
    SURVIVAL_SUITABILITY_SCENARIO_BINDING_ADAPTER_OWNER,
    ScenarioSurvivalSuitabilityOverridesV0,
    apply_canonical_survival_suitability_pre_matrix_gates_v0,
    canonical_survival_blocks_entry_v0,
    canonical_suitability_blocks_entry_v0,
    evaluate_scenario_survival_suitability_v0,
    legacy_envelope_would_block_but_canonical_passes_v0,
)
from trading.master_v2.suitability_binding_v1 import (
    SuitabilityBindingStatus,
    SuitabilityRegimeStatus,
    SuitabilityStrategyRegistryV1,
)

REPO_ROOT = Path(__file__).resolve().parents[3]
_INSTRUMENT = SYNTHETIC_FUTURES_INSTRUMENT
_EPOCH = 61
_CONTEXT = "survival-suitability-binding-parity-v0"

_SLICE_CHANGED_FILES = ALLOWED_SLICE_CHANGED_PATH_PREFIXES

_FORBIDDEN_IMPORT_SCAN_PATHS = (
    REPO_ROOT / "src/trading/master_v2/survival_suitability_scenario_binding_adapter_v0.py",
    REPO_ROOT / "src/trading/master_v2/double_play_composition_scenario_matrix_adapter_v0.py",
    REPO_ROOT
    / "src/trading/master_v2/integrated_vs_scenario_replay_full_system_parity_harness_v0.py",
    REPO_ROOT / "scripts/ops/run_survival_suitability_scenario_replay_binding_parity_rewire_v0.py",
    REPO_ROOT
    / "tests/trading/master_v2/test_survival_suitability_scenario_replay_binding_parity_rewire_contract_v0.py",
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


def _transition() -> TransitionDecision:
    return TransitionDecision(
        allowed=True,
        reason_code="TEST",
        live_authorization_granted=False,
    )


def _legacy_survival_ok() -> SurvivalEnvelopeDecision:
    return evaluate_survival_envelope(_survival_envelope())


def _legacy_survival_blocked() -> SurvivalEnvelopeDecision:
    ok = _legacy_survival_ok()
    return replace(
        ok,
        status=SurvivalEnvelopeStatus.BLOCKED,
        pre_authorization_eligible=False,
    )


def _legacy_suitability_both_pools() -> SuitabilityProjectionDecision:
    return project_strategy_suitability(_suitability_input())


def _legacy_suitability_blocked_pools() -> SuitabilityProjectionDecision:
    base = _legacy_suitability_both_pools()
    proj = replace(
        base.projection,
        suitability_class=SuitabilityClass.DISABLED_FOR_CANDIDATE,
        eligible_for_long_bull_pool=False,
        eligible_for_short_bear_pool=False,
    )
    return replace(
        base,
        projection=proj,
        can_enter_long_bull_pool=False,
        can_enter_short_bear_pool=False,
    )


def _composition_input(
    *,
    side: SideState,
    requested: RequestedSide,
    survival: SurvivalEnvelopeDecision | None = None,
    suitability: SuitabilityProjectionDecision | None = None,
) -> DoublePlayCompositionInput:
    return DoublePlayCompositionInput(
        transition=_transition(),
        resulting_side_state=side,
        survival=survival or _legacy_survival_ok(),
        suitability=suitability or _legacy_suitability_both_pools(),
        requested_side=requested,
    )


def test_owner_constants_and_canonical_reuse_v0() -> None:
    refs = canonical_owner_refs_v0()
    assert refs["survival_suitability_scenario_binding_adapter"] == (
        SURVIVAL_SUITABILITY_SCENARIO_BINDING_ADAPTER_OWNER
    )
    assert refs["scenario_replay"] == OFFLINE_DOUBLE_PLAY_SCENARIO_REPLAY_OWNER
    assert CANONICAL_SURVIVAL_ASSESSMENT_OWNER.endswith("survival_assessment_v1")
    assert CANONICAL_SUITABILITY_BINDING_OWNER.endswith("suitability_binding_v1")


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


def test_1_survival_hard_fail_blocks_composition_v0() -> None:
    overrides = ScenarioSurvivalSuitabilityOverridesV0(
        bull_survival_status=SurvivalAssessmentStatus.FAIL,
        bull_explicit_hard_fail_reasons=(SurvivalHardFailReason.EXPLICIT_HARD_FAIL,),
    )
    evaluation = evaluate_scenario_survival_suitability_v0(
        instrument_id=_INSTRUMENT,
        trading_epoch=_EPOCH,
        side_st=SideState.LONG_ACTIVE,
        overrides=overrides,
    )
    assert canonical_survival_blocks_entry_v0(evaluation.bull_survival)
    decision = apply_canonical_survival_suitability_pre_matrix_gates_v0(
        _composition_input(side=SideState.LONG_ACTIVE, requested=RequestedSide.LONG_BULL),
        evaluation,
    )
    assert decision is not None
    assert decision.status is DoublePlayCompositionStatus.BLOCKED


def test_2_survival_required_unknown_blocks_composition_v0() -> None:
    unknown_metrics = SurvivalMetricInputsV1(
        data_completeness_complete=None,
        volatility_survival_ratio=0.8,
        sequence_survival_ratio=0.8,
        drawdown_survival_ratio=0.8,
        liquidation_buffer_ratio=0.2,
    )
    overrides = ScenarioSurvivalSuitabilityOverridesV0(
        bull_metric_inputs=unknown_metrics,
        bear_metric_inputs=unknown_metrics,
    )
    evaluation = evaluate_scenario_survival_suitability_v0(
        instrument_id=_INSTRUMENT,
        trading_epoch=_EPOCH,
        side_st=SideState.LONG_ACTIVE,
        overrides=overrides,
    )
    assert evaluation.bull_survival.status is SurvivalAssessmentStatus.BLOCKED
    decision = apply_canonical_survival_suitability_pre_matrix_gates_v0(
        _composition_input(side=SideState.LONG_ACTIVE, requested=RequestedSide.LONG_BULL),
        evaluation,
    )
    assert decision is not None
    assert decision.status is DoublePlayCompositionStatus.BLOCKED


def test_3_suitability_fail_blocks_composition_v0() -> None:
    overrides = ScenarioSurvivalSuitabilityOverridesV0(
        bull_suitability_status=SuitabilityBindingStatus.FAIL,
    )
    evaluation = evaluate_scenario_survival_suitability_v0(
        instrument_id=_INSTRUMENT,
        trading_epoch=_EPOCH,
        side_st=SideState.LONG_ACTIVE,
        overrides=overrides,
    )
    assert canonical_suitability_blocks_entry_v0(evaluation.bull_suitability)
    decision = apply_canonical_survival_suitability_pre_matrix_gates_v0(
        _composition_input(side=SideState.LONG_ACTIVE, requested=RequestedSide.LONG_BULL),
        evaluation,
    )
    assert decision is not None
    assert decision.status is DoublePlayCompositionStatus.BLOCKED


def test_4_suitability_unknown_blocks_composition_v0() -> None:
    overrides = ScenarioSurvivalSuitabilityOverridesV0(
        regime_status=SuitabilityRegimeStatus.UNKNOWN,
    )
    evaluation = evaluate_scenario_survival_suitability_v0(
        instrument_id=_INSTRUMENT,
        trading_epoch=_EPOCH,
        side_st=SideState.LONG_ACTIVE,
        overrides=overrides,
    )
    assert evaluation.bull_suitability.status is SuitabilityBindingStatus.BLOCKED
    decision = apply_canonical_survival_suitability_pre_matrix_gates_v0(
        _composition_input(side=SideState.LONG_ACTIVE, requested=RequestedSide.LONG_BULL),
        evaluation,
    )
    assert decision is not None
    assert decision.status is DoublePlayCompositionStatus.BLOCKED


def test_4b_suitability_no_eligible_strategy_blocks_v0() -> None:
    overrides = ScenarioSurvivalSuitabilityOverridesV0(
        strategy_registry=SuitabilityStrategyRegistryV1(entries=()),
    )
    evaluation = evaluate_scenario_survival_suitability_v0(
        instrument_id=_INSTRUMENT,
        trading_epoch=_EPOCH,
        side_st=SideState.LONG_ACTIVE,
        overrides=overrides,
    )
    assert evaluation.bull_suitability.status in (
        SuitabilityBindingStatus.FAIL,
        SuitabilityBindingStatus.BLOCKED,
    )
    decision = apply_canonical_survival_suitability_pre_matrix_gates_v0(
        _composition_input(side=SideState.LONG_ACTIVE, requested=RequestedSide.LONG_BULL),
        evaluation,
    )
    assert decision is not None
    assert decision.status is DoublePlayCompositionStatus.BLOCKED


def test_5_survival_pass_suitability_pass_proceeds_v0() -> None:
    evaluation = evaluate_scenario_survival_suitability_v0(
        instrument_id=_INSTRUMENT,
        trading_epoch=_EPOCH,
        side_st=SideState.LONG_ACTIVE,
    )
    assert evaluation.bull_survival.status is SurvivalAssessmentStatus.PASS
    assert evaluation.bull_suitability.status is SuitabilityBindingStatus.PASS
    decision = apply_canonical_survival_suitability_pre_matrix_gates_v0(
        _composition_input(side=SideState.LONG_ACTIVE, requested=RequestedSide.LONG_BULL),
        evaluation,
    )
    assert decision is None
    matrix = evaluate_scenario_matrix_for_side_state_v0(
        side_state=SideState.LONG_ACTIVE,
        instrument_id=_INSTRUMENT,
        trading_epoch=_EPOCH,
        context_reference=_CONTEXT,
    )
    assert matrix.composition_status is CompositionStatus.LONG_SELECTED
    adapter = compose_double_play_scenario_via_canonical_matrix_v0(
        _composition_input(side=SideState.LONG_ACTIVE, requested=RequestedSide.LONG_BULL),
        instrument_id=_INSTRUMENT,
        trading_epoch=_EPOCH,
        context_reference=_CONTEXT,
    )
    assert adapter.status is DoublePlayCompositionStatus.ELIGIBLE_MODEL_ONLY


def test_6_legacy_envelope_mismatch_does_not_override_canonical_v0() -> None:
    evaluation = evaluate_scenario_survival_suitability_v0(
        instrument_id=_INSTRUMENT,
        trading_epoch=_EPOCH,
        side_st=SideState.LONG_ACTIVE,
    )
    assert legacy_envelope_would_block_but_canonical_passes_v0(
        legacy_survival_blocked=True,
        legacy_suitability_blocked=True,
        evaluation=evaluation,
        requested_side=RequestedSide.LONG_BULL,
    )
    adapter = compose_double_play_scenario_via_canonical_matrix_v0(
        _composition_input(
            side=SideState.LONG_ACTIVE,
            requested=RequestedSide.LONG_BULL,
            survival=_legacy_survival_blocked(),
            suitability=_legacy_suitability_blocked_pools(),
        ),
        instrument_id=_INSTRUMENT,
        trading_epoch=_EPOCH,
        context_reference=_CONTEXT,
    )
    assert adapter.status is DoublePlayCompositionStatus.ELIGIBLE_MODEL_ONLY


def test_scenario_replay_e2e_survival_suitability_binding_v0() -> None:
    result = run_offline_double_play_scenario_replay_v0(
        OfflineDoublePlayScenarioReplayInputV0(
            selected_future_id=_INSTRUMENT,
            ticks=build_default_bull_bear_bull_scenario_ticks(),
            source_revision="survival-suitability-binding-parity-v0",
        allow_test_scope_event_injection=True,)
    )
    assert result.replay_pass, result.fail_reasons
    assert result.summary.orders_total == 0


def test_gap_assessment_surface_e_pass_v0() -> None:
    surface_e = next(item for item in parity_surface_assessments_v0() if item.surface_id == "E")
    assert surface_e.parity_status == "PASS"
    assert surface_e.missing_binding_if_any == ""
    assert "evaluate_scenario_survival_suitability_v0" in surface_e.current_scenario_replay_binding
    assert "evaluate_survival_assessment_v1" in surface_e.current_scenario_replay_binding
    assert "evaluate_suitability_binding_v1" in surface_e.current_scenario_replay_binding


def test_gap_assessment_surface_c_d_still_pass_v0() -> None:
    surface_c = next(item for item in parity_surface_assessments_v0() if item.surface_id == "C")
    surface_d = next(item for item in parity_surface_assessments_v0() if item.surface_id == "D")
    assert surface_c.parity_status == "PASS"
    assert surface_d.parity_status == "PASS"


def test_gap_assessment_surface_p_unchanged_partial_v0() -> None:
    surface_p = next(item for item in parity_surface_assessments_v0() if item.surface_id == "P")
    assert surface_p.parity_status == "PASS"
    assert surface_p.missing_binding_if_any == ""


def test_gap_assessment_status_distribution_v0() -> None:
    counts = parity_status_counts_v0()
    assert counts["PASS"] == 16
    assert counts["PARTIAL"] == 0
    assert counts["GAP"] == 0


def test_next_recommended_slice_points_to_surface_p_v0() -> None:
    assert NEXT_RECOMMENDED_SLICE == "FULL_CANONICAL_BACKTEST_BOUNDARY_CHAIN_REASSESSMENT_V0"


def test_flat_before_opposite_side_contracts_still_pass_v0() -> None:
    from tests.trading.master_v2 import (
        test_flat_before_opposite_side_scenario_replay_binding_parity_rewire_contract_v0 as pr4970,
    )

    pr4970.test_4_reconciled_flat_opposite_entry_via_canonical_policy_only_v0()
    pr4970.test_gap_assessment_surface_d_pass_v0()


def test_reversal_preparation_contracts_still_pass_v0() -> None:
    from tests.trading.master_v2 import (
        test_reversal_preparation_scenario_replay_binding_parity_rewire_contract_v0 as pr4969,
    )

    pr4969.test_scenario_reversal_preparation_exit_via_canonical_policy_v0()
    pr4969.test_surface_c_pass_dep_unchanged_partial_v0()
