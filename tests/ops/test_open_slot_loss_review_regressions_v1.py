"""Review regressions at the original connected N1/owner boundary."""

from decimal import Decimal

import pytest

from src.ops.portfolio_capital_reservation_budget_v1.contract_v1 import (
    PortfolioCapitalBudgetError,
    PortfolioCapitalReservationBudgetOwnerV1,
)
from tests.ops import test_open_slot_loss_protection_v1 as connected
from tests.ops.test_n1_original_reservation_host_handoff_v1 import (
    synthetic_ports_and_isolation as synthetic_ports_and_isolation,
)


@pytest.mark.parametrize("fault", ["closed-owner", "storage-failed", "missing-store"])
def test_unavailable_writer_stops_original_n1_without_releasing_holds(tmp_path, monkeypatch, fault):
    original_observe = PortfolioCapitalReservationBudgetOwnerV1.observe_open_slot_loss_v1
    calls = []

    def unavailable(owner, **kwargs):
        before = owner.budget_state_v1()
        prior = owner._closed_owner, owner._storage_failed, owner._store
        calls.append(kwargs["slot_id"])
        # Inject each already-unavailable writer state immediately before
        # original N1 asks its owner for protection. Restore only for cleanup.
        if fault == "closed-owner":
            owner._closed_owner = True
        elif fault == "storage-failed":
            owner._storage_failed = True
        else:
            owner._store = None
        try:
            return original_observe(owner, **kwargs)
        finally:
            owner._closed_owner, owner._storage_failed, owner._store = prior
            assert owner.budget_state_v1() == before
            assert (
                owner.test_slot_loss_state_v1(kwargs["slot_id"])["open_position_protection"] is None
            )

    monkeypatch.setattr(
        PortfolioCapitalReservationBudgetOwnerV1, "observe_open_slot_loss_v1", unavailable
    )
    with pytest.raises(
        PortfolioCapitalBudgetError, match="OPEN_SLOT_ORIGINAL_BUDGET_WRITER_UNAVAILABLE"
    ):
        connected.run_open(tmp_path, monkeypatch)
    # N1 propagates the owner failure before another occupied slot/Core cycle.
    assert calls == ["LANE_1"]


@pytest.mark.parametrize("offset,accepted", [(Decimal("1e-20"), True), (Decimal(1), False)])
def test_original_n1_compares_float_projection_but_retains_exact_accounting_mark(
    tmp_path, monkeypatch, offset, accepted
):
    original_observation = connected.observation
    exact_marks = {}

    def supplied(world, lane, epoch, **kwargs):
        mark = Decimal(str(world["kwargs"]["mark_px"])) + offset
        exact_marks[lane] = mark
        return original_observation(world, lane, epoch, mark_px=mark)

    monkeypatch.setattr(connected, "observation", supplied)
    driver = connected.run_open(tmp_path, monkeypatch)
    try:
        result = driver.results["LANE_1"]
        protection = driver.world["host"].owner.test_slot_loss_state_v1("LANE_1")[
            "open_position_protection"
        ]
        if accepted:
            mark = exact_marks["LANE_1"]
            assert mark != Decimal(str(driver.world["kwargs"]["mark_px"]))
            assert float(mark) == float(driver.world["kwargs"]["mark_px"])
            assert result.slot_loss_protection_status == "OBSERVED_PROTECTION_ONLY"
            assert Decimal(protection["latest"]["native_mark_price"]) == mark
            assert (
                result.s7_invocation.cycle_result.replay.intermediate.entry_exit_decision.exit_class.value
                == "safety_exit"
            )
            assert result.position_management_close_intent is not None
        else:
            assert result.slot_loss_protection_status == "UNPROVEN_ORIGINAL_EXITS_RETAINED"
            assert result.slot_loss_protection_reason_codes == (
                "OPEN_SLOT_CURRENT_MARK_CYCLE_MISMATCH",
            )
            assert protection is None
            assert result.position_management_close_intent is None
        assert driver.before == driver.after
        assert all(r.governed_cycle_result.post_count == 0 for r in driver.results.values())
    finally:
        connected.cleanup(driver)
