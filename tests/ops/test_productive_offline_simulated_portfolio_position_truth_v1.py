"""Focused tests for productive offline simulated portfolio position truth wiring."""

from __future__ import annotations

from decimal import Decimal

from src.backtest.mv2_research_wiring_v1 import (
    build_initial_mv2_integrated_replay_bar_sequence_state_v1,
)
from src.ops.integrated_offline_economic_evidence_v1.productive_offline_replay_portfolio_truth_wiring_v1 import (
    apply_pending_portfolio_observation_to_sequence_state_v1,
    attach_pending_portfolio_observation_to_replay_input_v1,
    capture_portfolio_observation_after_epoch_v1,
)
from src.ops.integrated_offline_economic_evidence_v1.productive_offline_simulated_portfolio_position_truth_v1 import (
    capture_productive_offline_simulated_portfolio_position_observation_v1,
    overlay_portfolio_observation_on_capital_context_v0,
)
from src.ops.integrated_paper_shadow_observation_session_v1.portfolio_economics_model_v1 import (
    PortfolioEconomicsModelParamsV1,
    SimulatedPortfolioEconomicsModelV1,
)
from src.trading.master_v2.canonical_core_runtime_integration_intent_pipeline_bridge_v0 import (
    CanonicalCoreRuntimeCapitalContextV0,
)
from src.ops.integrated_offline_economic_evidence_v1.productive_offline_economic_completion_v1 import (
    build_productive_replay_baseline_input_v1,
)
from src.trading.master_v2.double_play_composition_matrix_v1 import (
    DOUBLE_PLAY_COMPOSITION_MATRIX_POLICY_VERSION,
    evaluate_double_play_composition_matrix_v1,
)
from src.trading.master_v2.double_play_entry_exit_policy_v0 import (
    PositionState,
    ExistingPositionSide,
)
from src.governance.capital_risk_sizing_v1 import InstrumentQuantityConstraintsV1

INSTRUMENT = "ETH-USD_UM_XPERP-310404"


def _portfolio() -> SimulatedPortfolioEconomicsModelV1:
    return SimulatedPortfolioEconomicsModelV1(params=PortfolioEconomicsModelParamsV1())


def test_a_flat_portfolio_observation_is_flat() -> None:
    port = _portfolio()
    obs = capture_productive_offline_simulated_portfolio_position_observation_v1(
        portfolio=port,
        instrument_id=INSTRUMENT,
        mark_price=Decimal("3000"),
        feedback_source_bar_epoch=1,
    )
    assert obs.reconciled_open_position_quantity == 0
    assert obs.position_state is PositionState.FLAT_RECONCILED


def test_b_long_fill_next_epoch_observation() -> None:
    port = _portfolio()
    port.apply_intended_action(
        instrument_id=INSTRUMENT,
        side="BUY",
        quantity=Decimal("2"),
        mark_price=Decimal("3000"),
    )
    obs = capture_portfolio_observation_after_epoch_v1(
        portfolio=port,
        instrument_id=INSTRUMENT,
        mark_price=Decimal("3010"),
        trading_epoch=5,
    )
    seq = apply_pending_portfolio_observation_to_sequence_state_v1(
        build_initial_mv2_integrated_replay_bar_sequence_state_v1(trading_epoch=0),
        obs,
    )
    assert seq.position_state is PositionState.OPEN_FULL
    assert seq.existing_position_side is ExistingPositionSide.LONG
    assert obs.reconciled_open_position_quantity == Decimal("2")
    assert obs.current_reconciled_exposure == Decimal("2") * Decimal("3010")


def test_c_short_fill_observation() -> None:
    port = _portfolio()
    port.apply_intended_action(
        instrument_id=INSTRUMENT,
        side="SELL",
        quantity=Decimal("3"),
        mark_price=Decimal("2000"),
    )
    obs = capture_portfolio_observation_after_epoch_v1(
        portfolio=port,
        instrument_id=INSTRUMENT,
        mark_price=Decimal("2000"),
        trading_epoch=2,
    )
    assert obs.existing_position_side is ExistingPositionSide.SHORT
    assert obs.reconciled_open_position_quantity == Decimal("3")


def test_d_partial_reduction_updates_quantity() -> None:
    port = _portfolio()
    port.apply_intended_action(
        instrument_id=INSTRUMENT,
        side="BUY",
        quantity=Decimal("4"),
        mark_price=Decimal("1000"),
    )
    port.apply_intended_action(
        instrument_id=INSTRUMENT,
        side="SELL",
        quantity=Decimal("1.5"),
        mark_price=Decimal("1010"),
    )
    obs = capture_portfolio_observation_after_epoch_v1(
        portfolio=port,
        instrument_id=INSTRUMENT,
        mark_price=Decimal("1010"),
        trading_epoch=9,
    )
    assert obs.reconciled_open_position_quantity == Decimal("2.5")


def test_e_flat_after_full_close() -> None:
    port = _portfolio()
    port.apply_intended_action(
        instrument_id=INSTRUMENT,
        side="BUY",
        quantity=Decimal("1"),
        mark_price=Decimal("1000"),
    )
    port.apply_intended_action(
        instrument_id=INSTRUMENT,
        side="SELL",
        quantity=Decimal("1"),
        mark_price=Decimal("1000"),
    )
    obs = capture_portfolio_observation_after_epoch_v1(
        portfolio=port,
        instrument_id=INSTRUMENT,
        mark_price=Decimal("1000"),
        trading_epoch=3,
    )
    assert obs.reconciled_open_position_quantity == 0


def test_f_no_lookahead_pending_not_applied_same_epoch_capture() -> None:
    port = _portfolio()
    obs_before = capture_portfolio_observation_after_epoch_v1(
        portfolio=port,
        instrument_id=INSTRUMENT,
        mark_price=Decimal("1000"),
        trading_epoch=0,
    )
    port.apply_intended_action(
        instrument_id=INSTRUMENT,
        side="BUY",
        quantity=Decimal("1"),
        mark_price=Decimal("1000"),
    )
    obs_after = capture_portfolio_observation_after_epoch_v1(
        portfolio=port,
        instrument_id=INSTRUMENT,
        mark_price=Decimal("1000"),
        trading_epoch=0,
    )
    assert obs_before.reconciled_open_position_quantity == 0
    assert obs_after.reconciled_open_position_quantity == Decimal("1")


def test_g_open_portfolio_prevents_flat_mv2_on_next_apply() -> None:
    port = _portfolio()
    port.apply_intended_action(
        instrument_id=INSTRUMENT,
        side="SELL",
        quantity=Decimal("2"),
        mark_price=Decimal("1500"),
    )
    pending = capture_portfolio_observation_after_epoch_v1(
        portfolio=port,
        instrument_id=INSTRUMENT,
        mark_price=Decimal("1500"),
        trading_epoch=1,
    )
    seq = apply_pending_portfolio_observation_to_sequence_state_v1(
        build_initial_mv2_integrated_replay_bar_sequence_state_v1(trading_epoch=0),
        pending,
    )
    assert seq.position_state is not PositionState.FLAT_RECONCILED
    assert seq.existing_position_side is ExistingPositionSide.SHORT


def test_h_double_play_composition_owner_unchanged() -> None:
    assert (
        DOUBLE_PLAY_COMPOSITION_MATRIX_POLICY_VERSION == "double_play_composition_matrix_policy_v1"
    )
    assert evaluate_double_play_composition_matrix_v1.__module__.endswith(
        "double_play_composition_matrix_v1"
    )


def test_i_ledger_reconciliation_unchanged_import() -> None:
    from src.ops.integrated_paper_shadow_observation_session_v1.simulated_economics_round_trip_ledger_v1 import (
        reconcile_ledger_against_portfolio_v1,
    )

    assert callable(reconcile_ledger_against_portfolio_v1)


def test_j_no_fill_flat_observation_no_sequence_mutation() -> None:
    port = _portfolio()
    obs = capture_portfolio_observation_after_epoch_v1(
        portfolio=port,
        instrument_id=INSTRUMENT,
        mark_price=Decimal("1000"),
        trading_epoch=0,
    )
    seq0 = build_initial_mv2_integrated_replay_bar_sequence_state_v1(trading_epoch=0)
    seq1 = apply_pending_portfolio_observation_to_sequence_state_v1(seq0, obs)
    assert seq1.position_state == seq0.position_state


def test_crs_overlay_binds_open_qty_and_exposure() -> None:
    inst = InstrumentQuantityConstraintsV1(
        instrument_id=INSTRUMENT,
        market_type="futures",
        contract_kind="LINEAR",
        contract_multiplier=Decimal("1"),
        lot_size=Decimal("0.01"),
        minimum_quantity=Decimal("0.01"),
        maximum_quantity=None,
        minimum_notional=Decimal("5"),
        tick_size=Decimal("0.01"),
        instrument_metadata_version="test",
    )
    base = CanonicalCoreRuntimeCapitalContextV0(
        reference_price=Decimal("2000"),
        protective_stop_price=Decimal("2100"),
        account_equity=Decimal("100000"),
        scope_capital_limit=Decimal("10000"),
        per_trade_risk_limit=Decimal("500"),
        total_capital_limit=Decimal("50000"),
        daily_loss_remaining_budget=Decimal("1000"),
        current_reconciled_exposure=Decimal("0"),
        instrument=inst,
    )
    port = _portfolio()
    port.apply_intended_action(
        instrument_id=INSTRUMENT,
        side="SELL",
        quantity=Decimal("2.5"),
        mark_price=Decimal("2000"),
    )
    obs = capture_portfolio_observation_after_epoch_v1(
        portfolio=port,
        instrument_id=INSTRUMENT,
        mark_price=Decimal("2000"),
        trading_epoch=4,
    )
    ctx = overlay_portfolio_observation_on_capital_context_v0(base, obs)
    assert ctx.reconciled_open_position_quantity == Decimal("2.5")
    assert ctx.current_reconciled_exposure == Decimal("5000")
    assert ctx.current_open_side == "SHORT"
    assert ctx.current_open_positions_count == 1


def test_replay_input_attachment_carries_observation() -> None:
    from src.ops.integrated_offline_economic_evidence_v1.productive_offline_simulated_portfolio_position_truth_v1 import (
        ProductiveOfflineSimulatedPortfolioPositionObservationV1,
    )
    from src.trading.master_v2.double_play_composition_matrix_v1 import (
        PositionManagementContext,
    )

    template = build_productive_replay_baseline_input_v1(trading_epoch=0, current_price=3000.0)
    obs = ProductiveOfflineSimulatedPortfolioPositionObservationV1(
        feedback_source_bar_epoch=1,
        instrument_id=INSTRUMENT,
        signed_quantity=Decimal("-1"),
        reconciled_open_position_quantity=Decimal("1"),
        current_reconciled_exposure=Decimal("3000"),
        existing_position_side=ExistingPositionSide.SHORT,
        position_state=PositionState.OPEN_FULL,
        position_management_context=PositionManagementContext.SHORT_POSITION,
        venue_flat=False,
        current_open_positions_count=1,
        current_open_side="SHORT",
    )
    out = attach_pending_portfolio_observation_to_replay_input_v1(template, obs)
    assert out.productive_offline_simulated_portfolio_position_observation_v1 is obs
