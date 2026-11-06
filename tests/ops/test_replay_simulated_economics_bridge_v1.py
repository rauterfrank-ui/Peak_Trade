"""GHV-aligned offline replay → simulated economics bridge contracts."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from types import SimpleNamespace

import pytest

from src.ops.integrated_offline_economic_evidence_v1.productive_offline_economic_completion_v1 import (
    invoke_current_authoritative_replay_v1,
)
from src.ops.integrated_offline_economic_evidence_v1.productive_replay_baseline_v1 import (
    build_productive_replay_baseline_input_v1,
)
from src.ops.integrated_offline_economic_evidence_v1.replay_simulated_economics_bridge_v1 import (
    apply_replay_result_to_simulated_portfolio_v1,
)
from src.ops.integrated_paper_shadow_observation_session_v1.portfolio_economics_model_v1 import (
    SimulatedPortfolioEconomicsModelV1,
)
from trading.master_v2.canonical_order_intent_offline_replay_binding_adapter_v0 import (
    ORDER_INTENT_EFFECT_BOUND_OFFLINE,
)


@dataclass
class _FakeIntent:
    quantity: Decimal
    intent_action: str = "ENTER_SHORT"
    execution_eligible: bool = False
    submission_authorized: bool = False


def _enter_short_result(*, qty: Decimal = Decimal("0.5"), execution_eligible: bool = False):
    evidence = SimpleNamespace(
        decision_outcome="enter_short",
        selected_side="short",
        execution_eligible=execution_eligible,
        order_intent_effect=ORDER_INTENT_EFFECT_BOUND_OFFLINE,
        reason_codes=("entry_short_eligible",),
    )
    intermediate = SimpleNamespace(canonical_order_intent=_FakeIntent(quantity=qty))
    return SimpleNamespace(
        replay_pass=True,
        fail_reasons=(),
        evidence=evidence,
        intermediate=intermediate,
    )


def test_bridge_rejects_execution_eligible_true() -> None:
    result = _enter_short_result(execution_eligible=True)
    portfolio = SimulatedPortfolioEconomicsModelV1()
    with pytest.raises(ValueError, match="EXECUTION_ELIGIBLE_MUST_REMAIN_FALSE"):
        apply_replay_result_to_simulated_portfolio_v1(
            portfolio,
            result=result,  # type: ignore[arg-type]
            instrument_id="ETH-USD_UM_XPERP-310404",
            mark_price=Decimal("3000"),
        )


def test_ghv_current_preflight_enter_short_admits_simulated_fill_with_crs_qty() -> None:
    portfolio = SimulatedPortfolioEconomicsModelV1()
    result = _enter_short_result(qty=Decimal("0.25"))
    admission = apply_replay_result_to_simulated_portfolio_v1(
        portfolio,
        result=result,  # type: ignore[arg-type]
        instrument_id="ETH-USD_UM_XPERP-310404",
        mark_price=Decimal("3000"),
    )
    assert admission.admitted is True
    assert admission.intended_side == "SELL"
    assert admission.intended_quantity == Decimal("0.25")
    assert admission.execution_eligible is False
    assert admission.external_submission_authorized is False
    assert admission.canonical_order_intent_present is True
    assert portfolio.state.fill_count == 1
    assert portfolio.state.cumulative_fees > 0
    assert portfolio.state.cumulative_slippage > 0
    pos = portfolio.state.positions["ETH-USD_UM_XPERP-310404"]
    assert pos.quantity < 0


def test_productive_baseline_replay_keeps_execution_ineligible_and_bridge_holds() -> None:
    replay_input = build_productive_replay_baseline_input_v1()
    result = invoke_current_authoritative_replay_v1(replay_input=replay_input)
    assert result.replay_pass is True
    assert result.evidence.execution_eligible is False
    portfolio = SimulatedPortfolioEconomicsModelV1()
    admission = apply_replay_result_to_simulated_portfolio_v1(
        portfolio,
        result=result,
        instrument_id=replay_input.instrument_id,
        mark_price=Decimal(str(replay_input.current_price)),
    )
    assert admission.external_submission_authorized is False
    if admission.admitted:
        assert portfolio.state.fill_count >= 1
    else:
        assert portfolio.state.fill_count == 0
