"""Supply the now-required shared reservation owner to standalone join tests.

No fabricated capital or policy override: observations remain caller-supplied,
and the actual outer Operations policy is loaded by the production join.
"""

from src.ops.full_core_live_path_composition_root_v1.current_productive_enter_live_29p_join_v1 import (
    CurrentProductiveEnterLive29PPortfolioSlotContextV1,
    join_current_productive_enter_live_29p_before_venue_plan_v1,
)
from src.ops.portfolio_capital_reservation_budget_v1.contract_v1 import (
    PortfolioCapitalReservationBudgetOwnerV1,
)


def join_with_portfolio_fixture_v1(**kwargs):
    if "portfolio_budget_owner" not in kwargs and "portfolio_slot" not in kwargs:
        evidence = getattr(kwargs.get("replay"), "evidence", None)
        kwargs["portfolio_budget_owner"] = PortfolioCapitalReservationBudgetOwnerV1()
        kwargs["portfolio_slot"] = CurrentProductiveEnterLive29PPortfolioSlotContextV1(
            slot_id="LANE_1",
            decision_id=str(getattr(evidence, "decision_id", "fixture-unbound")),
            cycle_id="standalone-outer-budget-test",
        )
    return join_current_productive_enter_live_29p_before_venue_plan_v1(**kwargs)
