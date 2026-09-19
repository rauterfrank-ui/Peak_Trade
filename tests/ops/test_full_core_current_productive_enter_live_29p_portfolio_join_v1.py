"""ENTER Live-29P join with portfolio capital reservation seam. No POST."""

from __future__ import annotations

from decimal import Decimal

import pytest

from src.ops.full_core_live_path_composition_root_v1.current_productive_enter_live_29p_join_v1 import (
    CurrentProductiveEnterLive29PJoinError,
    CurrentProductiveEnterLive29PPortfolioSlotContextV1,
    STATUS_PASS,
    join_current_productive_enter_live_29p_before_venue_plan_v1,
)
from src.ops.full_core_live_path_composition_root_v1.constants_v1 import (
    EXTERNAL_EFFECT_AUTHORIZED,
    POST_ALLOWED,
)
from src.ops.portfolio_capital_reservation_budget_v1.contract_v1 import (
    CANONICAL_RESTART_RECONSTRUCTABLE,
    MULTI_FUTURE_RUNTIME_AUTHORIZED,
    N_GT_1_ENABLED,
    PortfolioCapitalReservationBudgetOwnerV1,
    ReserveDispositionV1,
    ReservationStateV1,
)
from src.ops.single_selected_future_policy_v1.constants_v1 import MAX_POSITIONS_EFFECTIVE
from tests.ops.test_full_core_current_productive_enter_live_29p_join_v1 import (
    EPOCH,
    _balance_payload,
    _bound,
    _enter_replay,
    _host_enter_cycle,
    _injected,
)
from src.governance.capital_risk_sizing_v1 import CapitalRiskSizingOutcome


def test_legacy_path_unchanged_without_portfolio_owner() -> None:
    _cycle_a, cycle_b, _path = _host_enter_cycle()
    replay = _enter_replay(cycle_b)
    injected = _injected(payload=_balance_payload(avail_eq="100.00"))
    legacy = join_current_productive_enter_live_29p_before_venue_plan_v1(
        replay=replay,
        bound_instrument=_bound(),
        injected=injected,
        decision_epoch=EPOCH,
    )
    assert legacy.status == STATUS_PASS
    assert legacy.portfolio_reservation_id == ""
    assert legacy.replay is not None
    sizing = legacy.replay.intermediate.capital_risk_sizing_decision
    assert sizing is not None
    assert sizing.outcome is CapitalRiskSizingOutcome.PASS


def test_portfolio_owner_requires_paired_slot_context() -> None:
    _cycle_a, cycle_b, _path = _host_enter_cycle()
    replay = _enter_replay(cycle_b)
    owner = PortfolioCapitalReservationBudgetOwnerV1()
    with pytest.raises(CurrentProductiveEnterLive29PJoinError, match="PAIR_REQUIRED"):
        join_current_productive_enter_live_29p_before_venue_plan_v1(
            replay=replay,
            bound_instrument=_bound(),
            injected=_injected(payload=_balance_payload()),
            decision_epoch=EPOCH,
            portfolio_budget_owner=owner,
        )


def test_portfolio_path_reserves_before_crs_and_commits_on_pass() -> None:
    _cycle_a, cycle_b, _path = _host_enter_cycle()
    replay = _enter_replay(cycle_b)
    evidence = replay.evidence
    owner = PortfolioCapitalReservationBudgetOwnerV1()
    slot = CurrentProductiveEnterLive29PPortfolioSlotContextV1(
        slot_id="LANE_1",
        decision_id=str(evidence.decision_id),
        cycle_id="cycle-portfolio-seam-1",
    )
    result = join_current_productive_enter_live_29p_before_venue_plan_v1(
        replay=replay,
        bound_instrument=_bound(),
        injected=_injected(payload=_balance_payload(avail_eq="100.00")),
        decision_epoch=EPOCH,
        portfolio_budget_owner=owner,
        portfolio_slot=slot,
    )
    assert result.status == STATUS_PASS
    assert result.portfolio_reservation_disposition == ReserveDispositionV1.ADMITTED.value
    assert result.portfolio_reservation_id != ""
    reserved = owner.lookup_v1(
        slot_id=slot.slot_id,
        decision_id=slot.decision_id,
        cycle_id=slot.cycle_id,
        observation_id=owner.budget_state_v1().observation_id,
    )
    assert reserved is not None
    assert reserved.state is ReservationStateV1.RESERVED
    owner.commit_internal_pre_external_effect_v1(result.portfolio_reservation_id)
    committed = owner.lookup_v1(
        slot_id=slot.slot_id,
        decision_id=slot.decision_id,
        cycle_id=slot.cycle_id,
        observation_id=owner.budget_state_v1().observation_id,
    )
    assert committed is not None
    assert committed.state is ReservationStateV1.COMMITTED


def test_two_slots_contention_via_admit_seam() -> None:
    from tests.ops.test_portfolio_capital_reservation_budget_contract_v1 import (
        _admit,
        _bind,
    )

    owner = PortfolioCapitalReservationBudgetOwnerV1()
    _bind(owner)
    first = _admit(owner, slot="LANE_1", decision="dec-a", value="100.00")
    second = _admit(owner, slot="LANE_2", decision="dec-b", value="100.00")
    assert first.disposition is ReserveDispositionV1.ADMITTED
    assert second.disposition in {
        ReserveDispositionV1.DENIED,
        ReserveDispositionV1.FAIL_CLOSED,
    }
    assert owner.invariant_holds_v1()


def test_safety_pins_unchanged() -> None:
    assert int(MAX_POSITIONS_EFFECTIVE) == 1
    assert N_GT_1_ENABLED is False
    assert MULTI_FUTURE_RUNTIME_AUTHORIZED is False
    assert EXTERNAL_EFFECT_AUTHORIZED is False
    assert POST_ALLOWED is False
    assert CANONICAL_RESTART_RECONSTRUCTABLE is False


def test_restart_fail_closed_after_reservation() -> None:
    from tests.ops.test_portfolio_capital_reservation_budget_contract_v1 import (
        _admit,
        _bind,
    )

    owner = PortfolioCapitalReservationBudgetOwnerV1()
    _bind(owner)
    admitted = _admit(owner, slot="LANE_1", decision="dec-r", value="100.00")
    assert admitted.reservation is not None
    restarted = owner.restart_fail_closed_v1()
    assert restarted.disposition is ReserveDispositionV1.FAIL_CLOSED
    assert owner.active_sum_v1() == Decimal("0")
