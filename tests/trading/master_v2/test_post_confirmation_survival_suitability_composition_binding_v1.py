# tests/trading/master_v2/test_post_confirmation_survival_suitability_composition_binding_v1.py
"""C4 contract/boundary tests — POST_CONFIRMATION_SURVIVAL_SUITABILITY_COMPOSITION_BINDING_V1."""

from __future__ import annotations

import ast
from dataclasses import replace
from pathlib import Path

import pytest

from trading.market_state.directional_confirmation_progress_v1 import (
    ConfirmationAssessmentStateV1,
    ConfirmationProgressReasonCodeV1,
    ConfirmationProgressStateV1,
    ConfirmationSideV1,
    initial_confirmation_progress_state_v1,
)
from trading.market_state.distinct_market_observation_acceptor_v1 import (
    ObservationAcceptanceStateV1,
    ObservationCandidateV1,
    ObservationClassification,
    commit_observation_acceptance_v1,
    evaluate_distinct_market_observation_v1,
    initial_observation_acceptance_state_v1,
)
from trading.market_state.observation_identity_v1 import (
    InstrumentObservationKeyV1,
    MarketObservationEpoch,
)
from trading.master_v2.directional_assessment_confirmation_integration_v1 import (
    DirectionalConfirmationSideStateCarrierV1,
    initial_directional_confirmation_side_state_carrier_v1,
    non_advancing_observation_acceptance_result_v1,
)
from trading.master_v2.directional_assessment_v1 import (
    DirectionalAssessmentStatus,
)
from trading.master_v2.double_play_composition_matrix_v1 import (
    CompositionSelectedSide,
    CompositionStatus,
)
from trading.master_v2.post_confirmation_survival_suitability_composition_binding_v1 import (
    COMPOSITION_REMAINS_SOLE_CONFIRMED_ADMISSIBILITY_GATE,
    POST_CONFIRMATION_SURVIVAL_SUITABILITY_COMPOSITION_BINDING_CAPABILITY_ID,
    SURVIVAL_CONFIRMED_EARLY_GATE,
    SUITABILITY_CONFIRMED_EARLY_GATE,
    PostC3DownstreamConfirmationAuthorityErrorV1,
    assert_post_c3_downstream_confirmation_non_authority_v1,
    assert_productive_c4_modules_confirmation_non_authority_v1,
    collect_forbidden_downstream_confirmation_calls_v1,
    collect_forbidden_scenario_legacy_imports_v1,
)
from trading.master_v2.suitability_binding_v1 import SuitabilityBindingStatus
from trading.master_v2.survival_assessment_v1 import SurvivalAssessmentStatus

from tests.trading.master_v2.test_integrated_offline_trading_logic_replay_v1 import (
    _default_policies,
    _replay_input,
    _run,
)

REPO_ROOT = Path(__file__).resolve().parents[3]
C4_MODULE = (
    REPO_ROOT
    / "src/trading/master_v2/post_confirmation_survival_suitability_composition_binding_v1.py"
)
REPLAY_MODULE = REPO_ROOT / "src/trading/master_v2/integrated_offline_trading_logic_replay_v1.py"
WIRING_MODULE = REPO_ROOT / "src/backtest/mv2_research_wiring_v1.py"
SURVIVAL_MODULE = REPO_ROOT / "src/trading/master_v2/survival_assessment_v1.py"
SUITABILITY_MODULE = REPO_ROOT / "src/trading/master_v2/suitability_binding_v1.py"
COMPOSITION_MODULE = REPO_ROOT / "src/trading/master_v2/double_play_composition_matrix_v1.py"


def _key() -> InstrumentObservationKeyV1:
    return InstrumentObservationKeyV1(
        venue="okx_eea",
        canonical_instrument_id="inst-eth-usdt-perp",
        venue_instrument_id="inst-eth-usdt-perp",
    )


def _session() -> str:
    return "sess-c4"


def _confirmed_side_state(
    *,
    side: ConfirmationSideV1,
    epoch: int = 1,
) -> ConfirmationProgressStateV1:
    return ConfirmationProgressStateV1(
        session_id=_session(),
        venue="okx_eea",
        instrument=_key(),
        side=side,
        assessment_state=ConfirmationAssessmentStateV1.CONFIRMED,
        latest_accepted_market_observation_epoch=MarketObservationEpoch(value=epoch),
        candidate_started_at_epoch=MarketObservationEpoch(value=1),
        distinct_confirmation_observation_count=1,
        last_processed_acceptor_result_fingerprint=None,
    )


def _invalid_side_state(*, side: ConfirmationSideV1) -> ConfirmationProgressStateV1:
    return ConfirmationProgressStateV1(
        session_id=_session(),
        venue="okx_eea",
        instrument=_key(),
        side=side,
        assessment_state=ConfirmationAssessmentStateV1.INVALID,
        latest_accepted_market_observation_epoch=MarketObservationEpoch(value=1),
        candidate_started_at_epoch=None,
        distinct_confirmation_observation_count=0,
        last_processed_acceptor_result_fingerprint=None,
    )


def _carrier_from_sides(
    *,
    bull: ConfirmationProgressStateV1,
    bear: ConfirmationProgressStateV1,
) -> DirectionalConfirmationSideStateCarrierV1:
    return DirectionalConfirmationSideStateCarrierV1(
        bull_confirmation_state=bull,
        bear_confirmation_state=bear,
    )


def _distinct_acceptor(*, event_time: float = 1_700_000_000.0, mark: float = 10.0):
    state = initial_observation_acceptance_state_v1(bound_instrument_key=_key())
    candidate = ObservationCandidateV1(
        venue=_key().venue,
        canonical_instrument_id=_key().canonical_instrument_id,
        venue_instrument_id=_key().venue_instrument_id,
        venue_event_time=event_time,
        mark_price=mark,
    )
    result = evaluate_distinct_market_observation_v1(state, candidate)
    assert result.classification is ObservationClassification.DISTINCT
    committed = commit_observation_acceptance_v1(current_state=state, result=result)
    return result, committed


def _policies_confirm_once():
    policies = _default_policies()
    return replace(
        policies,
        directional=replace(policies.directional, confirmation_epochs=1),
    )


def test_c4_capability_constants() -> None:
    assert POST_CONFIRMATION_SURVIVAL_SUITABILITY_COMPOSITION_BINDING_CAPABILITY_ID == (
        "POST_CONFIRMATION_SURVIVAL_SUITABILITY_COMPOSITION_BINDING_V1"
    )
    assert COMPOSITION_REMAINS_SOLE_CONFIRMED_ADMISSIBILITY_GATE is True
    assert SURVIVAL_CONFIRMED_EARLY_GATE is False
    assert SUITABILITY_CONFIRMED_EARLY_GATE is False
    assert_post_c3_downstream_confirmation_non_authority_v1()
    with pytest.raises(PostC3DownstreamConfirmationAuthorityErrorV1):
        assert_post_c3_downstream_confirmation_non_authority_v1(confirmation_recompute_enabled=True)


def test_a1_both_observe_no_selection() -> None:
    result = _run()
    assert result.intermediate is not None
    assert result.intermediate.bull_assessment.status is DirectionalAssessmentStatus.OBSERVE
    assert result.intermediate.bear_assessment.status is DirectionalAssessmentStatus.OBSERVE
    assert result.intermediate.composition_result.selected_side is CompositionSelectedSide.NONE
    assert result.intermediate.post_confirmation_binding_capability_id == (
        POST_CONFIRMATION_SURVIVAL_SUITABILITY_COMPOSITION_BINDING_CAPABILITY_ID
    )


def test_a2_bull_candidate_bear_observe_no_selection() -> None:
    # confirmation_epochs=2: first DISTINCT CONFIRMED-signal → CANDIDATE
    acceptor, _ = _distinct_acceptor()
    carrier = initial_directional_confirmation_side_state_carrier_v1(
        session_id=_session(),
        venue="okx_eea",
        instrument=_key(),
    )
    result = _run(
        price_path=(3500.0, 3570.0),
        directional_confirmation_progress=carrier,
        observation_acceptance_result=acceptor,
        confirmation_progress_session_id=_session(),
        confirmation_progress_venue="okx_eea",
        confirmation_progress_instrument=_key(),
    )
    assert result.intermediate is not None
    assert result.intermediate.bull_assessment.status is DirectionalAssessmentStatus.CANDIDATE
    assert result.intermediate.bear_assessment.status is DirectionalAssessmentStatus.OBSERVE
    assert result.intermediate.composition_result.selected_side is CompositionSelectedSide.NONE


def test_a3_bull_confirmed_survival_suitability_pass_long_selected() -> None:
    acceptor, _ = _distinct_acceptor()
    carrier = initial_directional_confirmation_side_state_carrier_v1(
        session_id=_session(),
        venue="okx_eea",
        instrument=_key(),
    )
    result = _run(
        policies=_policies_confirm_once(),
        price_path=(3500.0, 3570.0),
        directional_confirmation_progress=carrier,
        observation_acceptance_result=acceptor,
        confirmation_progress_session_id=_session(),
        confirmation_progress_venue="okx_eea",
        confirmation_progress_instrument=_key(),
    )
    assert result.intermediate is not None
    assert result.intermediate.bull_assessment.status is DirectionalAssessmentStatus.CONFIRMED
    assert result.intermediate.bear_assessment.status is DirectionalAssessmentStatus.OBSERVE
    assert result.intermediate.bull_survival.status is SurvivalAssessmentStatus.PASS
    assert result.intermediate.bull_suitability.status is SuitabilityBindingStatus.PASS
    assert (
        result.intermediate.composition_result.composition_status is CompositionStatus.LONG_SELECTED
    )
    assert result.intermediate.composition_result.selected_side is CompositionSelectedSide.LONG


def test_a4_bear_confirmed_survival_suitability_pass_short_selected() -> None:
    acceptor, _ = _distinct_acceptor()
    carrier = initial_directional_confirmation_side_state_carrier_v1(
        session_id=_session(),
        venue="okx_eea",
        instrument=_key(),
    )
    result = _run(
        policies=_policies_confirm_once(),
        price_path=(3500.0, 3430.0),
        directional_confirmation_progress=carrier,
        observation_acceptance_result=acceptor,
        confirmation_progress_session_id=_session(),
        confirmation_progress_venue="okx_eea",
        confirmation_progress_instrument=_key(),
    )
    assert result.intermediate is not None
    assert result.intermediate.bear_assessment.status is DirectionalAssessmentStatus.CONFIRMED
    assert result.intermediate.bull_assessment.status is DirectionalAssessmentStatus.OBSERVE
    assert (
        result.intermediate.composition_result.composition_status
        is CompositionStatus.SHORT_SELECTED
    )
    assert result.intermediate.composition_result.selected_side is CompositionSelectedSide.SHORT


def test_a5_both_confirmed_chop_guard_block() -> None:
    carrier = _carrier_from_sides(
        bull=_confirmed_side_state(side=ConfirmationSideV1.LONG),
        bear=_confirmed_side_state(side=ConfirmationSideV1.SHORT),
    )
    acceptor = non_advancing_observation_acceptance_result_v1(
        bound_instrument_key=_key(),
        market_observation_epoch=MarketObservationEpoch(value=1),
    )
    result = _run(
        price_path=(3500.0, 3500.0),
        directional_confirmation_progress=carrier,
        observation_acceptance_result=acceptor,
        confirmation_progress_session_id=_session(),
        confirmation_progress_venue="okx_eea",
        confirmation_progress_instrument=_key(),
    )
    assert result.intermediate is not None
    assert result.intermediate.bull_assessment.status is DirectionalAssessmentStatus.CONFIRMED
    assert result.intermediate.bear_assessment.status is DirectionalAssessmentStatus.CONFIRMED
    assert (
        result.intermediate.composition_result.composition_status
        is CompositionStatus.CHOP_GUARD_BLOCK
    )
    assert result.intermediate.composition_result.selected_side is CompositionSelectedSide.NONE


def test_a6_bull_invalid_bear_confirmed_short_selectable() -> None:
    carrier = _carrier_from_sides(
        bull=_invalid_side_state(side=ConfirmationSideV1.LONG),
        bear=_confirmed_side_state(side=ConfirmationSideV1.SHORT),
    )
    acceptor = non_advancing_observation_acceptance_result_v1(
        bound_instrument_key=_key(),
        market_observation_epoch=MarketObservationEpoch(value=1),
    )
    result = _run(
        price_path=(3500.0, 3430.0),
        directional_confirmation_progress=carrier,
        observation_acceptance_result=acceptor,
        confirmation_progress_session_id=_session(),
        confirmation_progress_venue="okx_eea",
        confirmation_progress_instrument=_key(),
    )
    assert result.intermediate is not None
    assert result.intermediate.bull_assessment.status is DirectionalAssessmentStatus.INVALID
    assert result.intermediate.bear_assessment.status is DirectionalAssessmentStatus.CONFIRMED
    assert (
        result.intermediate.composition_result.composition_status
        is CompositionStatus.SHORT_SELECTED
    )


def test_a7_confirmed_survival_fail_no_long_selection() -> None:
    acceptor, _ = _distinct_acceptor()
    carrier = initial_directional_confirmation_side_state_carrier_v1(
        session_id=_session(),
        venue="okx_eea",
        instrument=_key(),
    )
    policies = _policies_confirm_once()
    policies = replace(
        policies,
        survival=replace(policies.survival, min_net_edge=999.0),
    )
    result = _run(
        policies=policies,
        price_path=(3500.0, 3570.0),
        directional_confirmation_progress=carrier,
        observation_acceptance_result=acceptor,
        confirmation_progress_session_id=_session(),
        confirmation_progress_venue="okx_eea",
        confirmation_progress_instrument=_key(),
    )
    assert result.intermediate is not None
    assert result.intermediate.bull_assessment.status is DirectionalAssessmentStatus.CONFIRMED
    assert result.intermediate.bull_survival.status is SurvivalAssessmentStatus.FAIL
    assert result.intermediate.composition_result.selected_side is not CompositionSelectedSide.LONG


def test_a8_confirmed_suitability_fail_no_long_selection() -> None:
    acceptor, _ = _distinct_acceptor()
    carrier = initial_directional_confirmation_side_state_carrier_v1(
        session_id=_session(),
        venue="okx_eea",
        instrument=_key(),
    )
    result = _run(
        policies=_policies_confirm_once(),
        price_path=(3500.0, 3570.0),
        strategy_registry=replace(_replay_input().strategy_registry, entries=()),
        directional_confirmation_progress=carrier,
        observation_acceptance_result=acceptor,
        confirmation_progress_session_id=_session(),
        confirmation_progress_venue="okx_eea",
        confirmation_progress_instrument=_key(),
    )
    assert result.intermediate is not None
    assert result.intermediate.bull_assessment.status is DirectionalAssessmentStatus.CONFIRMED
    assert result.intermediate.bull_suitability.status in {
        SuitabilityBindingStatus.FAIL,
        SuitabilityBindingStatus.BLOCKED,
    }
    assert result.intermediate.composition_result.selected_side is not CompositionSelectedSide.LONG


def test_a9_confirmed_hold_stable_preserves_status_and_reason_codes() -> None:
    carrier = _carrier_from_sides(
        bull=_confirmed_side_state(side=ConfirmationSideV1.LONG, epoch=1),
        bear=initial_confirmation_progress_state_v1(
            session_id=_session(),
            venue="okx_eea",
            instrument=_key(),
            side=ConfirmationSideV1.SHORT,
            initial_market_observation_epoch=MarketObservationEpoch(value=1),
        ),
    )
    from trading.market_state.observation_identity_v1 import ObservationIdentityV1

    seeded = ObservationAcceptanceStateV1(
        last_accepted_observation_identity=ObservationIdentityV1(
            venue=_key().venue,
            canonical_instrument_id=_key().canonical_instrument_id,
            venue_instrument_id=_key().venue_instrument_id,
            venue_event_time=1_700_000_000.0,
            mark_price=10.0,
        ),
        market_observation_epoch=MarketObservationEpoch(value=1),
        bound_instrument_key=_key(),
        last_accepted_transport=None,
    )
    candidate = ObservationCandidateV1(
        venue=_key().venue,
        canonical_instrument_id=_key().canonical_instrument_id,
        venue_instrument_id=_key().venue_instrument_id,
        venue_event_time=1_700_000_001.0,
        mark_price=11.0,
    )
    acceptor = evaluate_distinct_market_observation_v1(seeded, candidate)
    assert acceptor.classification is ObservationClassification.DISTINCT
    result = _run(
        policies=_policies_confirm_once(),
        price_path=(3500.0, 3570.0),
        directional_confirmation_progress=carrier,
        observation_acceptance_result=acceptor,
        confirmation_progress_session_id=_session(),
        confirmation_progress_venue="okx_eea",
        confirmation_progress_instrument=_key(),
    )
    assert result.intermediate is not None
    assert result.intermediate.bull_assessment.status is DirectionalAssessmentStatus.CONFIRMED
    assert ConfirmationProgressReasonCodeV1.ACCEPTED_DISTINCT_HOLD_CONFIRMED.value in (
        result.intermediate.bull_assessment.reason_codes
    )
    assert "c3_confirmation_progress" in result.intermediate.bull_assessment.reason_codes


def test_c19_downstream_modules_forbid_confirmation_authority_calls() -> None:
    for path in (SURVIVAL_MODULE, SUITABILITY_MODULE, COMPOSITION_MODULE):
        forbidden = collect_forbidden_downstream_confirmation_calls_v1(
            path.read_text(encoding="utf-8")
        )
        assert not forbidden, path.name
        legacy = collect_forbidden_scenario_legacy_imports_v1(path.read_text(encoding="utf-8"))
        assert not legacy, path.name


def test_c20_productive_replay_does_not_call_legacy_da_evaluator() -> None:
    source = REPLAY_MODULE.read_text(encoding="utf-8")
    tree = ast.parse(source)
    call_names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Name):
                call_names.add(func.id)
            elif isinstance(func, ast.Attribute):
                call_names.add(func.attr)
    assert "evaluate_directional_assessment_v1" not in call_names
    assert "evaluate_bull_bear_directional_assessment_with_confirmation_progress_v1" in call_names
    assert "assert_post_c3_downstream_confirmation_non_authority_v1" in call_names
    assert "assert_c4_c3_assessment_identity_binding_v1" in call_names


def test_c21_research_wiring_no_scenario_status_stub_in_productive_path() -> None:
    source = WIRING_MODULE.read_text(encoding="utf-8")
    legacy = collect_forbidden_scenario_legacy_imports_v1(source)
    assert not legacy
    assert "accept_mv2_research_bar_market_observation_v1" in source
    assert "evaluate_distinct_market_observation_v1" in source
    tree = ast.parse(source)
    call_names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Name):
                call_names.add(func.id)
            elif isinstance(func, ast.Attribute):
                call_names.add(func.attr)
    assert "evaluate_directional_assessment_v1" not in call_names
    # Lossy projector must not be invoked (definition may exist and raise).
    proj_calls = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and (
            (
                isinstance(node.func, ast.Name)
                and node.func.id == ("project_directional_confirmation_state_from_assessments_v1")
            )
            or (
                isinstance(node.func, ast.Attribute)
                and node.func.attr == "project_directional_confirmation_state_from_assessments_v1"
            )
        )
    ]
    assert not proj_calls


def test_c22_lossy_projector_raises() -> None:
    from src.backtest.mv2_research_wiring_v1 import (
        project_directional_confirmation_state_from_assessments_v1,
    )
    from trading.master_v2.directional_assessment_v1 import DirectionalConfirmationStateV1

    with pytest.raises(RuntimeError, match="LEGACY_LOSSY_CROSS_SIDE_PROJECTOR"):
        project_directional_confirmation_state_from_assessments_v1(
            bull_assessment=None,  # type: ignore[arg-type]
            bear_assessment=None,  # type: ignore[arg-type]
            previous=DirectionalConfirmationStateV1(0, -1, 0.0),
            next_trading_epoch=1,
            candidate_signal_threshold=0.005,
        )


def test_c23_static_productive_c4_guard_pass() -> None:
    assert_productive_c4_modules_confirmation_non_authority_v1(repo_root=REPO_ROOT)


def test_c24_no_cross_side_projection_in_orchestrator_binding() -> None:
    result = _run(
        policies=_policies_confirm_once(),
        price_path=(3500.0, 3570.0),
        directional_confirmation_progress=initial_directional_confirmation_side_state_carrier_v1(
            session_id=_session(),
            venue="okx_eea",
            instrument=_key(),
        ),
        observation_acceptance_result=_distinct_acceptor()[0],
        confirmation_progress_session_id=_session(),
        confirmation_progress_venue="okx_eea",
        confirmation_progress_instrument=_key(),
    )
    assert result.intermediate is not None
    bull = result.intermediate.bull_assessment
    bear = result.intermediate.bear_assessment
    assert bull.side.value == "long"
    assert bear.side.value == "short"
    assert bull.assessment_id != bear.assessment_id
    assert (
        result.intermediate.bull_survival.directional_assessment_ref.assessment_id
        == bull.assessment_id
    )
    assert (
        result.intermediate.bear_survival.directional_assessment_ref.assessment_id
        == bear.assessment_id
    )


def test_c4_owner_module_documents_capability() -> None:
    source = C4_MODULE.read_text(encoding="utf-8")
    assert "POST_CONFIRMATION_SURVIVAL_SUITABILITY_COMPOSITION_BINDING_V1" in source
    assert "COMPOSITION_REMAINS_SOLE_CONFIRMED_ADMISSIBILITY_GATE" in source
    replay_src = REPLAY_MODULE.read_text(encoding="utf-8")
    assert "POST_CONFIRMATION_SURVIVAL_SUITABILITY_COMPOSITION_BINDING_V1" in replay_src
