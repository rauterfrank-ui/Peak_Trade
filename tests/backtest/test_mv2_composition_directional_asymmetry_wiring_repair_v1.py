"""OBL_B05 composition directional asymmetry wiring repair v1 contracts."""

from __future__ import annotations

import ast
import inspect
from pathlib import Path

import pytest

from src.backtest.mv2_research_wiring_v1 import (
    MV2_AGREEMENT_BOUND_RELATIVE_IMPULSE_V1,
    build_initial_mv2_integrated_replay_bar_sequence_state_v1,
    project_directional_confirmation_state_from_assessments_v1,
    project_mv2_agreement_bound_price_path_v1,
    project_mv2_integrated_replay_bar_sequence_state_from_intermediate_v1,
    resolve_agreement_bound_directional_cycle_v1,
)
from trading.master_v2.directional_assessment_v1 import (
    DirectionalAssessmentSide,
    DirectionalAssessmentStatus,
    DirectionalAssessmentV1,
    DirectionalConfirmationStateV1,
    ScopeEventRefV1,
    compute_signal_strength,
    with_computed_directional_assessment_digest,
)
from trading.master_v2.double_play_composition_matrix_v1 import (
    CompositionStatus,
)
from trading.master_v2.integrated_offline_trading_logic_replay_v1 import (
    _directional_input_for_side,
)
from trading.master_v2.strategy_suitability_agreement_material_v1 import (
    StrategyAgreementEventKindV1,
    StrategySideAgreementV1,
    StrategySignalEncodingClassV1,
    StrategySuitabilityAgreementMaterialV1,
    compute_strategy_suitability_agreement_material_digest_v1,
)
from tests.trading.master_v2.test_double_play_composition_matrix_v1 import (
    test_5_both_sides_candidate_observe,
    test_7_long_only_admissible,
    test_8_short_only_admissible,
)

_WIRING = Path("src/backtest/mv2_research_wiring_v1.py")
_REPLAY = Path("src/trading/master_v2/integrated_offline_trading_logic_replay_v1.py")
_DIGEST = "a" * 64


def _material(
    *,
    encoding: StrategySignalEncodingClassV1,
    cycle: int,
    side: StrategySideAgreementV1 = StrategySideAgreementV1.NEUTRAL,
    event: StrategyAgreementEventKindV1 | None = None,
) -> StrategySuitabilityAgreementMaterialV1:
    digest = compute_strategy_suitability_agreement_material_digest_v1(
        encoding_class=encoding,
        configured_strategy_id="bollinger_bands",
        executed_strategy_id="bollinger_bands",
        strategy_version="v1",
        strategy_params_digest=_DIGEST,
        strategy_signal_digest=_DIGEST,
        instrument_id="okx:linear_perpetual:1INCH:USDT:USDT:perp",
        trading_epoch=10,
        cycle_signal_value=cycle,
        side_agreement=side,
        filter_pass=None,
        event_kind=event,
    )
    return StrategySuitabilityAgreementMaterialV1(
        encoding_class=encoding,
        configured_strategy_id="bollinger_bands",
        executed_strategy_id="bollinger_bands",
        strategy_version="v1",
        strategy_params_digest=_DIGEST,
        strategy_signal_digest=_DIGEST,
        instrument_id="okx:linear_perpetual:1INCH:USDT:USDT:perp",
        trading_epoch=10,
        cycle_signal_value=cycle,  # type: ignore[arg-type]
        side_agreement=side,
        filter_pass=None,
        event_kind=event,
        material_digest=digest,
    )


def _positional_ls_material(cycle: int) -> StrategySuitabilityAgreementMaterialV1:
    digest = compute_strategy_suitability_agreement_material_digest_v1(
        encoding_class=StrategySignalEncodingClassV1.POSITIONAL_LS_STATE_V1,
        configured_strategy_id="rsi_reversion",
        executed_strategy_id="rsi_reversion",
        strategy_version="v1",
        strategy_params_digest=_DIGEST,
        strategy_signal_digest=_DIGEST,
        instrument_id="okx:linear_perpetual:ETH:USDT:USDT:perp",
        trading_epoch=10,
        cycle_signal_value=cycle,
        side_agreement=StrategySideAgreementV1.NEUTRAL,
        filter_pass=None,
        event_kind=None,
    )
    return StrategySuitabilityAgreementMaterialV1(
        encoding_class=StrategySignalEncodingClassV1.POSITIONAL_LS_STATE_V1,
        configured_strategy_id="rsi_reversion",
        executed_strategy_id="rsi_reversion",
        strategy_version="v1",
        strategy_params_digest=_DIGEST,
        strategy_signal_digest=_DIGEST,
        instrument_id="okx:linear_perpetual:ETH:USDT:USDT:perp",
        trading_epoch=10,
        cycle_signal_value=cycle,  # type: ignore[arg-type]
        side_agreement=StrategySideAgreementV1.NEUTRAL,
        filter_pass=None,
        event_kind=None,
        material_digest=digest,
    )


def test_no_absolute_mark_plus_5_in_research_wiring() -> None:
    source = _WIRING.read_text(encoding="utf-8")
    assert "mark_price + 5.0" not in source
    assert "mark_price+5" not in source
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
            right = node.right
            if isinstance(right, ast.Constant) and right.value == 5.0:
                pytest.fail("absolute +5.0 impulse remains in mv2_research_wiring_v1")


def test_scale_invariance_relative_impulse() -> None:
    material = _positional_ls_material(1)
    cheap = project_mv2_agreement_bound_price_path_v1(mark_price=0.25, material=material)
    rich = project_mv2_agreement_bound_price_path_v1(mark_price=3500.0, material=material)
    cheap_ret = (cheap[1] - cheap[0]) / cheap[0]
    rich_ret = (rich[1] - rich[0]) / rich[0]
    assert cheap_ret == pytest.approx(MV2_AGREEMENT_BOUND_RELATIVE_IMPULSE_V1)
    assert rich_ret == pytest.approx(MV2_AGREEMENT_BOUND_RELATIVE_IMPULSE_V1)
    assert cheap_ret == pytest.approx(rich_ret)


def test_neutral_entry_exit_fail_closed_flat_path() -> None:
    material = _material(
        encoding=StrategySignalEncodingClassV1.ENTRY_EXIT_EVENT_V1,
        cycle=1,
        side=StrategySideAgreementV1.NEUTRAL,
        event=StrategyAgreementEventKindV1.ENTRY,
    )
    assert resolve_agreement_bound_directional_cycle_v1(material) is None
    # Unbound prior → flat fail-closed (no invented strategy asymmetry).
    path = project_mv2_agreement_bound_price_path_v1(mark_price=100.0, material=material)
    assert path == (100.0, 100.0)
    assert material.entry_side.value == "NONE"
    # Bound prior → market-context path; direction remains MV2-owned.
    market = project_mv2_agreement_bound_price_path_v1(
        mark_price=102.0,
        material=material,
        prior_mark_price=100.0,
    )
    assert market == (100.0, 102.0)


def test_directional_asymmetry_long_material_not_both_candidates() -> None:
    material = _positional_ls_material(1)
    path = project_mv2_agreement_bound_price_path_v1(mark_price=100.0, material=material)
    bull = compute_signal_strength(
        price_path=path, side=DirectionalAssessmentSide.LONG, reference_price=100.0
    )
    bear = compute_signal_strength(
        price_path=path, side=DirectionalAssessmentSide.SHORT, reference_price=100.0
    )
    assert bull > 0.0
    assert bear < 0.0
    assert bull != pytest.approx(bear)


def test_directional_asymmetry_short_material_mirrored() -> None:
    material = _positional_ls_material(-1)
    path = project_mv2_agreement_bound_price_path_v1(mark_price=100.0, material=material)
    bull = compute_signal_strength(
        price_path=path, side=DirectionalAssessmentSide.LONG, reference_price=100.0
    )
    bear = compute_signal_strength(
        price_path=path, side=DirectionalAssessmentSide.SHORT, reference_price=100.0
    )
    assert bear > 0.0
    assert bull < 0.0


def test_integrated_directional_input_does_not_mirror_shared_path() -> None:
    source = inspect.getsource(_directional_input_for_side)
    assert "mirror_price_path_for_short" not in source
    replay_src = _REPLAY.read_text(encoding="utf-8")
    assert "def _directional_input_for_side" in replay_src
    # Shared path only; SHORT orientation via compute_signal_strength.
    assert "price_path=inp.price_path" in source


def _assessment(
    *,
    side: DirectionalAssessmentSide,
    status: DirectionalAssessmentStatus,
    signal_strength: float,
) -> DirectionalAssessmentV1:
    ref = ScopeEventRefV1(
        scope_event_id="scope-1",
        semantic_digest=_DIGEST,
        event_type="upscope_candidate",
        trading_epoch=9,
    )
    raw = DirectionalAssessmentV1(
        assessment_id="a",
        side=side,
        instrument_id="inst-eth-usdt-perp",
        trading_epoch=10,
        status=status,
        signal_strength=signal_strength,
        confidence=min(1.0, max(0.0, signal_strength / 0.01)),
        feature_refs=("feat-momentum-v1",),
        scope_event_ref=ref,
        survival_preconditions=("survival_precondition_ref_only",),
        hard_block_reasons=(),
        reason_codes=("signal_meets_candidate_threshold",),
        valid_until_epoch=13,
        semantic_digest="",
    )
    return with_computed_directional_assessment_digest(raw)


def test_confirmation_provenance_from_da_not_scope_count() -> None:
    previous = DirectionalConfirmationStateV1(
        candidate_count=1,
        last_evaluated_trading_epoch=9,
        last_signal_strength=0.02,
    )
    bull = _assessment(
        side=DirectionalAssessmentSide.LONG,
        status=DirectionalAssessmentStatus.CANDIDATE,
        signal_strength=0.02,
    )
    bear = _assessment(
        side=DirectionalAssessmentSide.SHORT,
        status=DirectionalAssessmentStatus.OBSERVE,
        signal_strength=-0.02,
    )
    with pytest.raises(RuntimeError, match="LEGACY_LOSSY_CROSS_SIDE_PROJECTOR_AUTHORITY_FORBIDDEN"):
        project_directional_confirmation_state_from_assessments_v1(
            bull_assessment=bull,
            bear_assessment=bear,
            previous=previous,
            next_trading_epoch=11,
            candidate_signal_threshold=0.005,
        )

    wiring_src = _WIRING.read_text(encoding="utf-8")
    assert "project_directional_confirmation_state_from_assessments_v1" in wiring_src
    assert "LEGACY_LOSSY_CROSS_SIDE_PROJECTOR_AUTHORITY_FORBIDDEN" in wiring_src
    proj_src = inspect.getsource(
        project_mv2_integrated_replay_bar_sequence_state_from_intermediate_v1
    )
    assert "directional_confirmation_progress_after" in proj_src
    assert "project_directional_confirmation_state_from_assessments_v1" not in proj_src
    assert "scope_confirmation.candidate_count" not in proj_src
    assert (
        "last_signal_strength=previous.directional_confirmation_state.last_signal_strength"
        not in proj_src
    )


def test_initial_confirmation_state_not_synthetic() -> None:
    state = build_initial_mv2_integrated_replay_bar_sequence_state_v1(trading_epoch=0)
    assert state.directional_confirmation_state.candidate_count == 0
    assert state.directional_confirmation_state.last_signal_strength == 0.0


def test_composition_policy_fixtures_unchanged() -> None:
    test_5_both_sides_candidate_observe()
    test_7_long_only_admissible()
    test_8_short_only_admissible()


def test_projection_helper_exported_for_contracts() -> None:
    assert callable(project_mv2_integrated_replay_bar_sequence_state_from_intermediate_v1)
    assert CompositionStatus.OBSERVE.value == "observe"
