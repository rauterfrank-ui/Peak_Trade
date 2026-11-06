"""Open-position marks must update equity/drawdown without simulated fills."""

from decimal import Decimal
from types import SimpleNamespace

import pytest

from src.ops.integrated_offline_economic_evidence_v1.replay_simulated_economics_bridge_v1 import (
    apply_replay_result_to_simulated_portfolio_v1,
)
from src.ops.integrated_paper_shadow_observation_session_v1.portfolio_economics_model_v1 import (
    PortfolioEconomicsModelParamsV1,
    SimulatedPortfolioEconomicsModelV1,
)
from src.ops.wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_hardening_v2.idempotent_portfolio_v2 import (
    IdempotentPortfolioV2,
)

INSTRUMENT = "ETH-USD_UM_XPERP-310404"


@pytest.mark.parametrize("host", ["model", "idempotent_v2", "replay_bridge"])
@pytest.mark.parametrize(
    "side,marks", [("BUY", ("110", "90", "100")), ("SELL", ("90", "110", "100"))]
)
def test_hold_marks_preserve_equity_identity_and_observed_drawdown(host, side, marks) -> None:
    model = SimulatedPortfolioEconomicsModelV1(
        PortfolioEconomicsModelParamsV1(initial_equity=Decimal("1000"))
    )
    model.apply_intended_action(
        instrument_id=INSTRUMENT, side=side, quantity=Decimal("2"), mark_price=Decimal("100")
    )
    wrapper = IdempotentPortfolioV2(model=model)
    initial_cash = model.state.cash
    costs = (
        model.state.cumulative_fees,
        model.state.cumulative_slippage,
        model.state.cumulative_funding,
    )
    quantity = model.state.positions[INSTRUMENT].quantity
    peak = model.state.peak_equity
    worst_drawdown = model.state.max_drawdown
    hold_result = SimpleNamespace(
        replay_pass=True,
        fail_reasons=(),
        evidence=SimpleNamespace(
            decision_outcome="hold",
            selected_side="none",
            reason_codes=(),
            execution_eligible=False,
            order_intent_effect="NONE",
        ),
        intermediate=None,
    )
    for index, mark in enumerate(marks):
        if host == "model":
            result = model.apply_intended_action(
                instrument_id=INSTRUMENT,
                side="HOLD",
                quantity=Decimal("0"),
                mark_price=Decimal(mark),
            )
            assert result is None
        elif host == "idempotent_v2":
            result = wrapper.apply_intended_action(
                instrument_id=INSTRUMENT,
                side="HOLD",
                quantity=Decimal("0"),
                mark_price=Decimal(mark),
                intent_id=f"hold-{index}",
            )
            assert result is None
        else:
            admission = apply_replay_result_to_simulated_portfolio_v1(
                model, result=hold_result, instrument_id=INSTRUMENT, mark_price=Decimal(mark)
            )
            assert admission.admitted is False
            assert admission.fill is None
            assert admission.external_submission_authorized is False
        expected_equity = initial_cash + quantity * (
            Decimal(mark) - model.state.positions[INSTRUMENT].avg_entry_price
        )
        peak = max(peak, expected_equity)
        worst_drawdown = max(worst_drawdown, (peak - expected_equity) / peak)
        metrics = model.economic_metrics()
        assert metrics.unrealized_pnl == expected_equity - initial_cash
        assert metrics.equity == expected_equity
        assert metrics.drawdown == worst_drawdown
        assert model.state.peak_equity == peak
        assert model.snapshot()["economic_metrics"]["equity"] == str(expected_equity)
        assert model.state.cash == initial_cash
        assert model.state.fill_count == 1
        assert model.completed_trade_count == 0
        assert model.state.positions[INSTRUMENT].quantity == quantity
        assert (
            model.state.cumulative_fees,
            model.state.cumulative_slippage,
            model.state.cumulative_funding,
        ) == costs
    assert worst_drawdown > 0
