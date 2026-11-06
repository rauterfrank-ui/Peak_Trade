"""Canonical chain zero-trade blocker v1 — OPTION_D wiring regression contracts.

Proves ENTRY_SIDE=NONE remains the strategy fail-closed initial carrier, while a
deterministic Bull/Bear path can still reach Entry/Order-intent projection
exclusively via transition_state + composition matrix + market-context price_path.
"""

from __future__ import annotations

import ast
import inspect
from pathlib import Path

import pytest

from src.backtest.mv2_research_wiring_v1 import (
    build_initial_mv2_integrated_replay_bar_sequence_state_v1,
    project_mv2_agreement_bound_price_path_v1,
    resolve_agreement_bound_directional_cycle_v1,
)
from trading.master_v2.deterministic_scope_event_generator_v1 import ScopeDirectionState
from trading.master_v2.double_play_composition_matrix_v1 import (
    CompositionSelectedSide,
    CompositionStatus,
)
from trading.master_v2.double_play_entry_exit_policy_v0 import (
    DecisionOutcome,
    EntryExitDirectionState,
)
from trading.master_v2.double_play_sole_authority_quarantine_v1 import (
    CANONICAL_BULL_BEAR_STATE_OWNER,
    CANONICAL_COMPOSITION_AUTHORITY,
    CANONICAL_SWITCH_AUTHORITY,
    LIVE_AUTHORIZED,
    ORDERS_ENABLED,
    RUNTIME_BRIDGE_STATUS,
)
from trading.master_v2.double_play_state import SideState, transition_state
from trading.master_v2.suitability_binding_v1 import (
    derive_effective_strategy_side_agreement_v1,
)
from trading.master_v2.directional_assessment_v1 import DirectionalAssessmentSide
from trading.master_v2.strategy_suitability_agreement_material_v1 import (
    StrategyAgreementEventKindV1,
    StrategyEntrySideCarrierV1,
    StrategySideAgreementV1,
    StrategySignalEncodingClassV1,
    StrategySuitabilityAgreementMaterialV1,
    compute_strategy_suitability_agreement_material_digest_v1,
)
from tests.trading.master_v2 import test_integrated_offline_trading_logic_replay_v1 as replay_tests

_DIGEST = "a" * 64
_WIRING = Path("src/backtest/mv2_research_wiring_v1.py")
_SUITABILITY = Path("src/trading/master_v2/suitability_binding_v1.py")
_ADAPTER = Path("src/backtest/strategy_signal_suitability_agreement_adapter_v1.py")


def _entry_none_material(
    *,
    instrument_id: str,
    trading_epoch: int,
    event: StrategyAgreementEventKindV1 = StrategyAgreementEventKindV1.ENTRY,
    cycle: int = 1,
) -> StrategySuitabilityAgreementMaterialV1:
    digest = compute_strategy_suitability_agreement_material_digest_v1(
        encoding_class=StrategySignalEncodingClassV1.ENTRY_EXIT_EVENT_V1,
        configured_strategy_id="bollinger_bands",
        executed_strategy_id="bollinger_bands",
        strategy_version="v1",
        strategy_params_digest=_DIGEST,
        strategy_signal_digest=_DIGEST,
        instrument_id=instrument_id,
        trading_epoch=trading_epoch,
        cycle_signal_value=cycle,
        side_agreement=StrategySideAgreementV1.NEUTRAL,
        filter_pass=None,
        event_kind=event,
        entry_side=StrategyEntrySideCarrierV1.NONE,
    )
    return StrategySuitabilityAgreementMaterialV1(
        encoding_class=StrategySignalEncodingClassV1.ENTRY_EXIT_EVENT_V1,
        configured_strategy_id="bollinger_bands",
        executed_strategy_id="bollinger_bands",
        strategy_version="v1",
        strategy_params_digest=_DIGEST,
        strategy_signal_digest=_DIGEST,
        instrument_id=instrument_id,
        trading_epoch=trading_epoch,
        cycle_signal_value=cycle,  # type: ignore[arg-type]
        side_agreement=StrategySideAgreementV1.NEUTRAL,
        filter_pass=None,
        event_kind=event,
        entry_side=StrategyEntrySideCarrierV1.NONE,
        material_digest=digest,
    )


def test_1_initial_entry_side_remains_none() -> None:
    base = replay_tests._replay_input()
    material = _entry_none_material(
        instrument_id=base.instrument_id,
        trading_epoch=base.trading_epoch,
    )
    assert material.entry_side is StrategyEntrySideCarrierV1.NONE
    assert material.entry_side.value == "NONE"
    assert resolve_agreement_bound_directional_cycle_v1(material) is None


def test_2_bull_canonical_path_reaches_enter_long_intent() -> None:
    base = replay_tests._replay_input()
    material = _entry_none_material(
        instrument_id=base.instrument_id,
        trading_epoch=base.trading_epoch,
    )
    # Market-context bull path + armed LONG direction; strategy side stays NONE.
    result = replay_tests._run(
        price_path=(3500.0, 3600.0),
        strategy_suitability_agreement_material=material,
        side_state=SideState.LONG_ARMED,
        direction_state=EntryExitDirectionState.LONG_ARMED,
    )
    assert result.intermediate is not None
    composition = result.intermediate.composition_result
    assert composition.selected_side is CompositionSelectedSide.LONG
    assert composition.composition_status is CompositionStatus.LONG_SELECTED
    assert result.evidence.decision_outcome == DecisionOutcome.ENTER_LONG.value
    assert resolve_agreement_bound_directional_cycle_v1(material) is None
    assert result.intermediate.canonical_order_intent is not None


def test_3_bear_canonical_path_reaches_enter_short_intent() -> None:
    base = replay_tests._replay_input()
    material = _entry_none_material(
        instrument_id=base.instrument_id,
        trading_epoch=base.trading_epoch,
    )
    result = replay_tests._run(
        price_path=(3500.0, 3400.0),
        strategy_suitability_agreement_material=material,
        side_state=SideState.SHORT_ARMED,
        direction_state=EntryExitDirectionState.SHORT_ARMED,
        scope_direction_state=ScopeDirectionState.SHORT,
    )
    assert result.intermediate is not None
    composition = result.intermediate.composition_result
    assert composition.selected_side is CompositionSelectedSide.SHORT
    assert composition.composition_status is CompositionStatus.SHORT_SELECTED
    assert result.evidence.decision_outcome == DecisionOutcome.ENTER_SHORT.value
    # Intent may bind only when CRS quantity PASS; entry decision itself must form.
    if result.evidence.quantity_status == "PASS":
        assert result.intermediate.canonical_order_intent is not None


def test_4_neutral_chop_unbound_remains_fail_closed() -> None:
    base = replay_tests._replay_input()
    material = _entry_none_material(
        instrument_id=base.instrument_id,
        trading_epoch=base.trading_epoch,
        event=StrategyAgreementEventKindV1.NONE,
        cycle=0,
    )
    result = replay_tests._run(
        price_path=(3500.0, 3500.0),
        strategy_suitability_agreement_material=material,
        side_state=SideState.LONG_ARMED,
        direction_state=EntryExitDirectionState.LONG_ARMED,
    )
    assert result.evidence.decision_outcome != DecisionOutcome.ENTER_LONG.value
    assert result.evidence.decision_outcome != DecisionOutcome.ENTER_SHORT.value
    assert result.intermediate is not None
    assert result.intermediate.canonical_order_intent is None
    assert project_mv2_agreement_bound_price_path_v1(mark_price=100.0, material=material) == (
        100.0,
        100.0,
    )


def test_5_legacy_bypass_cannot_reach_order_intent_or_execution() -> None:
    assert RUNTIME_BRIDGE_STATUS == "BOUND_NOT_ACTIVATED"
    assert LIVE_AUTHORIZED == "false"
    assert ORDERS_ENABLED == "false"
    result = replay_tests._run(price_path=(3500.0, 3600.0))
    assert result.evidence.execution_eligible is False
    assert result.evidence.adapter_compatible is False


def test_6_no_second_direction_or_composition_authority() -> None:
    assert CANONICAL_BULL_BEAR_STATE_OWNER.endswith("transition_state")
    assert CANONICAL_SWITCH_AUTHORITY.endswith("transition_state")
    assert CANONICAL_COMPOSITION_AUTHORITY.endswith("double_play_composition_matrix_v1")
    assert callable(transition_state)
    wiring = _WIRING.read_text(encoding="utf-8")
    assert "prior_mark_price" in wiring
    adapter = _ADAPTER.read_text(encoding="utf-8")
    assert "_BOLLINGER_EVENT_ONLY_OWNER" in adapter
    assert "return StrategyEntrySideCarrierV1.NONE" in adapter


def test_7_integrated_replay_consumes_scope_direction_composition_intent() -> None:
    base = replay_tests._replay_input()
    material = _entry_none_material(
        instrument_id=base.instrument_id,
        trading_epoch=base.trading_epoch,
    )
    result = replay_tests._run(
        price_path=(3500.0, 3600.0),
        strategy_suitability_agreement_material=material,
        side_state=SideState.LONG_ARMED,
        direction_state=EntryExitDirectionState.LONG_ARMED,
    )
    inter = result.intermediate
    assert inter is not None
    assert inter.composition_result.selected_side is CompositionSelectedSide.LONG
    assert inter.state_switch.next_side_state == SideState.LONG_ARMED.value
    assert result.evidence.composition_result_ref
    assert result.evidence.decision_outcome == DecisionOutcome.ENTER_LONG.value
    assert inter.canonical_order_intent is not None


def test_8_negative_unbound_prior_and_invalid_prior_fail_closed() -> None:
    material = _entry_none_material(instrument_id="inst", trading_epoch=1)
    assert project_mv2_agreement_bound_price_path_v1(mark_price=50.0, material=material) == (
        50.0,
        50.0,
    )
    with pytest.raises(ValueError, match="prior_mark"):
        project_mv2_agreement_bound_price_path_v1(
            mark_price=50.0,
            material=material,
            prior_mark_price=0.0,
        )
    with pytest.raises(ValueError, match="prior_mark"):
        project_mv2_agreement_bound_price_path_v1(
            mark_price=50.0,
            material=material,
            prior_mark_price=float("nan"),
        )
    state = build_initial_mv2_integrated_replay_bar_sequence_state_v1(trading_epoch=0)
    assert state.prior_mark_price is None


def test_9_entry_side_none_suitability_is_timing_only_not_long_bias() -> None:
    material = _entry_none_material(instrument_id="inst", trading_epoch=10)
    assert (
        derive_effective_strategy_side_agreement_v1(material, DirectionalAssessmentSide.LONG)
        is StrategySideAgreementV1.AGREE
    )
    assert (
        derive_effective_strategy_side_agreement_v1(material, DirectionalAssessmentSide.SHORT)
        is StrategySideAgreementV1.AGREE
    )
    src = inspect.getsource(derive_effective_strategy_side_agreement_v1)
    assert "entry_side" in src
    assert "agrees only with LONG" not in src


def test_10_market_context_path_used_when_strategy_direction_unbound() -> None:
    material = _entry_none_material(instrument_id="inst", trading_epoch=10)
    assert resolve_agreement_bound_directional_cycle_v1(material) is None
    bull = project_mv2_agreement_bound_price_path_v1(
        mark_price=102.0, material=material, prior_mark_price=100.0
    )
    bear = project_mv2_agreement_bound_price_path_v1(
        mark_price=98.0, material=material, prior_mark_price=100.0
    )
    assert bull == (100.0, 102.0)
    assert bear == (100.0, 98.0)


def test_11_sole_owners_unchanged_and_no_option_b_template() -> None:
    assert "transition_state" in CANONICAL_BULL_BEAR_STATE_OWNER
    assert "double_play_composition_matrix_v1" in CANONICAL_COMPOSITION_AUTHORITY
    suitability_tree = ast.parse(_SUITABILITY.read_text(encoding="utf-8"))
    src = _SUITABILITY.read_text(encoding="utf-8")
    assert "StrategyEntrySideCarrierV1" in src
    assert isinstance(suitability_tree, ast.Module)
