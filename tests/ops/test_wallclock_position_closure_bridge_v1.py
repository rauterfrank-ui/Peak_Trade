"""Position closure: productive wallclock bridge mutates portfolio on simulated fill."""

from __future__ import annotations

from decimal import Decimal

from src.ops.integrated_paper_shadow_observation_session_v1.portfolio_economics_model_v1 import (
    PortfolioEconomicsModelParamsV1,
)


def test_hardened_bridge_cycle_fill_mutates_portfolio_state_hash() -> None:
    from src.ops.wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_hardening_v2.hardening_cycle_bridge_v2 import (
        HardenedBridgeSessionStateV2,
        run_hardened_bridge_cycle_v2,
    )
    from src.ops.wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_hardening_v2.idempotent_portfolio_v2 import (
        IdempotentPortfolioV2,
    )

    params = PortfolioEconomicsModelParamsV1(
        fee_rate_bps=Decimal("2.0"),
        slippage_bps=Decimal("1.0"),
        initial_equity=Decimal("100000"),
    )
    state = HardenedBridgeSessionStateV2(portfolio=IdempotentPortfolioV2.from_params(params))
    for i, mid in enumerate((3500.0, 3510.0, 3520.0)):
        run_hardened_bridge_cycle_v2(
            state,
            mid_price=mid,
            event_ts_unix=1_700_000_100.0 + i,
            session_id="position-closure-probe",
        )
    cycle = run_hardened_bridge_cycle_v2(
        state,
        mid_price=3550.0,
        event_ts_unix=1_700_000_200.0,
        session_id="position-closure-probe",
        forced_actionable={"intended_side": "BUY", "intended_quantity": "0.14"},
    )
    assert cycle.get("fill") is not None
    assert cycle.get("portfolio_state_before_hash") != cycle.get("portfolio_state_after_hash")
