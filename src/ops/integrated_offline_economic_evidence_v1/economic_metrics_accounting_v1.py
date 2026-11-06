"""Build integrated offline economic metrics accounting from simulated portfolio state."""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from src.ops.integrated_offline_economic_evidence_v1.current_integrated_offline_economic_policy_v1 import (
    TRADE_COUNT_SEMANTIC_COMPLETED_POSITION_ROUND_TRIP,
)
from src.ops.integrated_paper_shadow_observation_session_v1.portfolio_economics_model_v1 import (
    SimulatedPortfolioEconomicsModelV1,
)


def build_qualification_accounting_from_portfolio_v1(
    portfolio: SimulatedPortfolioEconomicsModelV1,
) -> dict[str, Any]:
    """Authoritative qualification fields; trade_count = completed round trips only."""
    state = portfolio.state
    completed = portfolio.completed_trade_count
    realized_legs = portfolio.realized_leg_count
    return {
        "trade_count": completed,
        "completed_trade_count": completed,
        "trade_count_semantic": TRADE_COUNT_SEMANTIC_COMPLETED_POSITION_ROUND_TRIP,
        "entry_count": portfolio.entry_count,
        "fill_count": state.fill_count,
        "realized_leg_count": realized_legs,
        "win_leg_count": portfolio.win_leg_count,
        "loss_leg_count": portfolio.loss_leg_count,
        "winning_completed_trades": portfolio.winning_completed_trades,
        "losing_completed_trades": portfolio.losing_completed_trades,
    }


def expectancy_per_completed_trade_v1(
    *,
    portfolio: SimulatedPortfolioEconomicsModelV1,
    net_pnl: Decimal | str,
) -> str:
    completed = portfolio.completed_trade_count
    if completed == 0:
        return "0"
    net = Decimal(str(net_pnl))
    return str(net / completed)


def net_pnl_from_portfolio_state_v1(portfolio: SimulatedPortfolioEconomicsModelV1) -> str:
    state = portfolio.state
    return str(
        state.realized_pnl
        + state.unrealized_pnl
        - state.cumulative_fees
        - state.cumulative_slippage
    )


def merge_qualification_metrics_into_doc_v1(
    *,
    portfolio: SimulatedPortfolioEconomicsModelV1,
    metrics_doc: dict[str, Any],
) -> dict[str, Any]:
    """Inject qualification accounting fields; trade_count = completed round trips."""
    accounting = build_qualification_accounting_from_portfolio_v1(portfolio)
    net_pnl = net_pnl_from_portfolio_state_v1(portfolio)
    merged = dict(metrics_doc)
    merged.update(accounting)
    merged["expectancy"] = expectancy_per_completed_trade_v1(
        portfolio=portfolio,
        net_pnl=net_pnl,
    )
    exposure = sum(
        (p.quantity * p.avg_entry_price).copy_abs() for p in portfolio.state.positions.values()
    )
    merged["exposure"] = str(exposure)
    return merged
