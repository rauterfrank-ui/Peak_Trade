"""Portfolio capital reservation budget contract v1.

No venue calls. No orders. N=1 pins stay unchanged.
"""

from __future__ import annotations

import inspect
import random
import threading
from decimal import Decimal
from pathlib import Path

from src.governance.capital_risk_sizing_v1 import (
    CapitalRiskSizingInputV1,
    CapitalRiskSizingOutcome,
    InstrumentQuantityConstraintsV1,
    evaluate_capital_risk_sizing_v1,
)
from src.ops.full_core_live_path_composition_root_v1.constants_v1 import (
    EXTERNAL_EFFECT_AUTHORIZED,
    POST_ALLOWED,
    REAL_VENUE_POST_ALLOWED,
)
from src.ops.full_core_live_path_composition_root_v1.execution_admission_contract_v1 import (
    FreshPretradeGetStatusV1,
    LiveAccountBoundStatusV1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.current_productive_29p_risk_capital_model_v1 import (
    CurrentProductive29PRiskCapitalOutputV1,
    CurrentProductiveUsdcFreeMarginObservationV1,
    produce_current_productive_29p_risk_capital_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.current_productive_available_for_sizing_producer_v1 import (
    CurrentProductiveAccountEligibilityFactV1,
    CurrentProductiveP01ReductionFactV1,
)
from src.ops.portfolio_capital_reservation_budget_v1.contract_v1 import (
    CANONICAL_RESTART_RECONSTRUCTABLE,
    MAX_POSITIONS_EFFECTIVE,
    MULTI_FUTURE_RUNTIME_AUTHORIZED,
    N_GT_1_ENABLED,
    PORTFOLIO_BUDGET_OWNER,
    RESERVATION_OWNER,
    SIZING_OWNER,
    VENUE_FILL_INTEGRATED,
    PortfolioCapitalBudgetError,
    PortfolioCapitalReservationBudgetOwnerV1,
    ReleaseReasonV1,
    ReservationStateV1,
    ReserveDispositionV1,
    SlotId,
    admit_sized_slot_reservation_v1,
    observation_identity_v1,
)
from src.ops.single_selected_future_policy_v1.constants_v1 import (
    MAX_POSITIONS_EFFECTIVE as POLICY_MAX_POSITIONS,
    MULTI_FUTURE_RUNTIME_AUTHORIZED as POLICY_MULTI_FUTURE,
)

DIGEST = "a" * 64
EPOCH = "2026-09-15T12:03:00Z"
ACCOUNT = "acct-1"
INSTRUMENT = "ETH-USD-PERP"
TRUSTED = FreshPretradeGetStatusV1.TRUSTED_PRESENT.value
BOUND = LiveAccountBoundStatusV1.TRUSTED_PRESENT.value
JOIN_PATH = (
    Path(__file__).resolve().parents[2]
    / "src/ops/full_core_live_path_composition_root_v1/current_productive_enter_live_29p_join_v1.py"
)


def _obs(
    *, value: str = "100.00", epoch: str = EPOCH
) -> CurrentProductiveUsdcFreeMarginObservationV1:
    return CurrentProductiveUsdcFreeMarginObservationV1(
        fact_id="CURRENT_PRODUCTIVE_USDC_FREE_MARGIN_OBSERVATION",
        surface="details[ccy=USDC].availEq",
        value=value,
        settlement_currency="USDC",
        selected_ccy="USDC",
        bound_account_identity=ACCOUNT,
        bound_venue_identity="okx",
        bound_td_mode="cross",
        decision_epoch=epoch,
        observed_at_as_of=epoch,
        age_seconds="1",
        freshness_max_age="5",
        provenance_digest=DIGEST,
        already_net_of_in_use="true",
        account_level_avail_eq_used="false",
        fallback_chain_used="false",
    )


def _p01(epoch: str = EPOCH) -> CurrentProductiveP01ReductionFactV1:
    return CurrentProductiveP01ReductionFactV1(
        fact_id="CURRENT_PRODUCTIVE_P01_GOVERNED_REDUCTION",
        applicability_state="DOES_NOT_APPLY",
        value="",
        settlement_currency="USDC",
        bound_account_identity=ACCOUNT,
        bound_venue_identity="okx",
        bound_td_mode="cross",
        decision_epoch=epoch,
        observed_at_as_of=epoch,
        age_seconds="1",
        freshness_max_age="5",
        provenance_digest=DIGEST,
        source_class="GOVERNED_CONDITIONAL",
    )


def _eligibility(epoch: str = EPOCH) -> CurrentProductiveAccountEligibilityFactV1:
    return CurrentProductiveAccountEligibilityFactV1(
        fact_id="CURRENT_PRODUCTIVE_U01_ACCOUNT_ELIGIBILITY",
        account_mode="FUTURES_MODE",
        bound_account_identity=ACCOUNT,
        bound_venue_identity="okx",
        bound_td_mode="cross",
        decision_epoch=epoch,
        provenance_digest=DIGEST,
    )


def _produce(
    *, value: str = "100.00", epoch: str = EPOCH
) -> CurrentProductive29PRiskCapitalOutputV1:
    output = produce_current_productive_29p_risk_capital_v1(
        observation=_obs(value=value, epoch=epoch),
        p01=_p01(epoch),
        eligibility=_eligibility(epoch),
    )
    assert output.produced == "true", output.reason_codes
    return output


def _bind(
    owner: PortfolioCapitalReservationBudgetOwnerV1,
    *,
    value: str = "100.00",
    epoch: str = EPOCH,
) -> str:
    output = _produce(value=value, epoch=epoch)
    bound = owner.bind_canonical_producer_output_v1(output)
    assert bound.disposition in {
        ReserveDispositionV1.ADMITTED,
        ReserveDispositionV1.IDEMPOTENT_REPLAY,
    }
    return observation_identity_v1(output)


def _sizing_input(**overrides: object) -> CapitalRiskSizingInputV1:
    instrument = InstrumentQuantityConstraintsV1(
        instrument_id=INSTRUMENT,
        market_type="futures",
        contract_kind="LINEAR",
        contract_multiplier=Decimal("1"),
        lot_size=Decimal("0.01"),
        minimum_quantity=Decimal("0.01"),
        maximum_quantity=Decimal("100"),
        minimum_notional=Decimal("5"),
        tick_size=Decimal("0.01"),
        instrument_metadata_version="portfolio_budget_contract_test_v1",
    )
    base: dict[str, object] = {
        "decision_id": "decision-001",
        "instrument_id": INSTRUMENT,
        "selected_side": "LONG",
        "reference_price": Decimal("100"),
        "protective_stop_price": Decimal("50"),
        "stop_distance": None,
        "account_equity": Decimal("100"),
        "scope_capital_limit": Decimal("1000"),
        "per_trade_risk_limit": Decimal("1000"),
        "total_capital_limit": Decimal("1000"),
        "daily_loss_remaining_budget": Decimal("1000"),
        "current_reconciled_exposure": Decimal("0"),
        "maximum_positions": 1,
        "current_open_positions_count": 0,
        "current_open_side": None,
        "configured_quantity_cap": None,
        "leverage_ceiling": None,
        "reconciliation_status": "RECONCILED",
        "policy_version": "capital_risk_sizing_policy_v1",
        "config_digest": "cfg_digest_test",
        "input_digest": DIGEST,
        "instrument": instrument,
        "decision_outcome": "enter_long",
    }
    base.update(overrides)
    return CapitalRiskSizingInputV1(**base)  # type: ignore[arg-type]


def _admit(
    owner: PortfolioCapitalReservationBudgetOwnerV1,
    *,
    slot: str,
    decision: str,
    epoch: str = EPOCH,
    value: str = "100.00",
    sizing: CapitalRiskSizingInputV1 | None = None,
):
    return admit_sized_slot_reservation_v1(
        owner,
        observation=_obs(value=value, epoch=epoch),
        p01=_p01(epoch),
        eligibility=_eligibility(epoch),
        slot_id=SlotId(slot),
        decision_id=decision,
        cycle_id="cycle-1",
        instrument_id=INSTRUMENT,
        account_identity=ACCOUNT,
        sizing_input=sizing or _sizing_input(),
        fresh_pretrade_get_status=TRUSTED,
        live_account_bound_status=BOUND,
        fresh_evidence_fetched=True,
        fresh_evidence_validated=True,
    )


def test_a_second_slot_over_remainder_is_denied() -> None:
    owner = PortfolioCapitalReservationBudgetOwnerV1()
    observation_id = _bind(owner)
    first = owner.try_reserve_v1(
        slot_id=SlotId("LANE_1"),
        decision_id="d1",
        cycle_id="c1",
        observation_id=observation_id,
        amount=Decimal("60"),
    )
    second = owner.try_reserve_v1(
        slot_id=SlotId("LANE_2"),
        decision_id="d2",
        cycle_id="c1",
        observation_id=observation_id,
        amount=Decimal("50"),
    )
    assert first.disposition is ReserveDispositionV1.ADMITTED
    assert first.mutated is True
    assert second.disposition is ReserveDispositionV1.DENIED
    assert second.mutated is False
    assert second.reservation is None
    assert owner.active_sum_v1() == Decimal("60")
    assert owner.stored_reservation_count_v1() == 1
    assert owner.invariant_holds_v1()


def test_b_two_slots_fit_and_leave_remainder() -> None:
    owner = PortfolioCapitalReservationBudgetOwnerV1()
    observation_id = _bind(owner)
    first = owner.try_reserve_v1(
        slot_id="LANE_1",
        decision_id="d1",
        cycle_id="c1",
        observation_id=observation_id,
        amount=Decimal("40"),
    )
    second = owner.try_reserve_v1(
        slot_id="LANE_2",
        decision_id="d2",
        cycle_id="c1",
        observation_id=observation_id,
        amount=Decimal("50"),
    )
    assert first.disposition is ReserveDispositionV1.ADMITTED
    assert second.disposition is ReserveDispositionV1.ADMITTED
    state = owner.budget_state_v1()
    assert state.active_reservation_sum == Decimal("90")
    assert state.remaining_unreserved == Decimal("10")
    assert state.canonical_available_capital == Decimal("100.00")


def test_c_concurrent_requests_cannot_both_take_the_same_remainder() -> None:
    owner = PortfolioCapitalReservationBudgetOwnerV1()
    observation_id = _bind(owner)
    barrier = threading.Barrier(8)
    results: list[object] = []
    lock = threading.Lock()

    def _worker(index: int) -> None:
        barrier.wait()
        result = owner.try_reserve_v1(
            slot_id=SlotId(f"LANE_{index}"),
            decision_id=f"d{index}",
            cycle_id="c-concurrent",
            observation_id=observation_id,
            amount=Decimal("30"),
        )
        with lock:
            results.append(result)

    threads = [threading.Thread(target=_worker, args=(index,)) for index in range(1, 9)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    admitted = [item for item in results if item.disposition is ReserveDispositionV1.ADMITTED]
    assert len(admitted) == 3
    assert owner.active_sum_v1() == Decimal("90")
    assert owner.active_sum_v1() <= owner.admitted_budget_v1()


def test_d_duplicate_replay_does_not_double_count() -> None:
    owner = PortfolioCapitalReservationBudgetOwnerV1()
    observation_id = _bind(owner)
    first = owner.try_reserve_v1(
        slot_id="LANE_1",
        decision_id="d1",
        cycle_id="c1",
        observation_id=observation_id,
        amount=Decimal("40"),
    )
    replay = owner.try_reserve_v1(
        slot_id="LANE_1",
        decision_id="d1",
        cycle_id="c1",
        observation_id=observation_id,
        amount=Decimal("40"),
    )
    mismatch = owner.try_reserve_v1(
        slot_id="LANE_1",
        decision_id="d1",
        cycle_id="c1",
        observation_id=observation_id,
        amount=Decimal("41"),
    )
    assert first.reservation is not None
    assert replay.disposition is ReserveDispositionV1.IDEMPOTENT_REPLAY
    assert replay.mutated is False
    assert replay.reservation is not None
    assert replay.reservation.reservation_id == first.reservation.reservation_id
    assert mismatch.disposition is ReserveDispositionV1.FAIL_CLOSED
    assert mismatch.mutated is False
    assert owner.active_sum_v1() == Decimal("40")
    released = owner.release_v1(
        str(first.reservation.reservation_id),
        reason=ReleaseReasonV1.EXPLICIT_CANCEL_BEFORE_EXTERNAL_EFFECT,
    )
    assert released.reservation is not None
    replay_after = owner.try_reserve_v1(
        slot_id="LANE_1",
        decision_id="d1",
        cycle_id="c1",
        observation_id=observation_id,
        amount=Decimal("40"),
    )
    assert replay_after.disposition is ReserveDispositionV1.IDEMPOTENT_REPLAY
    assert replay_after.reservation is not None
    assert replay_after.reservation.state is ReservationStateV1.RELEASED
    assert owner.active_sum_v1() == Decimal("0")


def test_e_release_returns_capital() -> None:
    owner = PortfolioCapitalReservationBudgetOwnerV1()
    observation_id = _bind(owner)
    first = owner.try_reserve_v1(
        slot_id="LANE_1",
        decision_id="d1",
        cycle_id="c1",
        observation_id=observation_id,
        amount=Decimal("60"),
    )
    assert first.reservation is not None
    released = owner.release_v1(
        str(first.reservation.reservation_id),
        reason=ReleaseReasonV1.EXPLICIT_CANCEL_BEFORE_EXTERNAL_EFFECT,
    )
    assert released.reservation is not None
    assert released.reservation.state is ReservationStateV1.RELEASED
    assert owner.active_sum_v1() == Decimal("0")
    second = owner.try_reserve_v1(
        slot_id="LANE_2",
        decision_id="d2",
        cycle_id="c1",
        observation_id=observation_id,
        amount=Decimal("60"),
    )
    assert second.disposition is ReserveDispositionV1.ADMITTED
    assert owner.active_sum_v1() == Decimal("60")


def test_f_new_epoch_does_not_keep_old_reservation() -> None:
    owner = PortfolioCapitalReservationBudgetOwnerV1()
    old_id = _bind(owner, value="100.00", epoch=EPOCH)
    held = owner.try_reserve_v1(
        slot_id="LANE_1",
        decision_id="d1",
        cycle_id="c1",
        observation_id=old_id,
        amount=Decimal("40"),
    )
    assert held.reservation is not None
    new_id = _bind(owner, value="80.00", epoch="2026-09-15T12:04:00Z")
    assert new_id != old_id
    stored = owner.lookup_v1(
        slot_id="LANE_1",
        decision_id="d1",
        cycle_id="c1",
        observation_id=old_id,
    )
    assert stored is not None
    assert stored.state is ReservationStateV1.EXPIRED
    assert owner.active_sum_v1() == Decimal("0")
    stale = owner.try_reserve_v1(
        slot_id="LANE_2",
        decision_id="d2",
        cycle_id="c1",
        observation_id=old_id,
        amount=Decimal("10"),
    )
    assert stale.disposition is ReserveDispositionV1.FAIL_CLOSED
    assert stale.mutated is False
    fresh = owner.try_reserve_v1(
        slot_id="LANE_2",
        decision_id="d2",
        cycle_id="c1",
        observation_id=new_id,
        amount=Decimal("80"),
    )
    assert fresh.disposition is ReserveDispositionV1.ADMITTED
    assert owner.active_sum_v1() == Decimal("80")
    assert owner.admitted_budget_v1() == Decimal("80.00")


def test_g_failed_pre_external_effect_releases() -> None:
    owner = PortfolioCapitalReservationBudgetOwnerV1()
    observation_id = _bind(owner)
    reserved = owner.try_reserve_v1(
        slot_id="LANE_1",
        decision_id="d1",
        cycle_id="c1",
        observation_id=observation_id,
        amount=Decimal("25"),
    )
    assert reserved.reservation is not None
    committed = owner.commit_internal_pre_external_effect_v1(
        str(reserved.reservation.reservation_id)
    )
    assert committed.reservation is not None
    assert committed.reservation.state is ReservationStateV1.COMMITTED
    assert committed.reservation.venue_fill_integrated is False
    assert VENUE_FILL_INTEGRATED is False
    failed = owner.fail_pre_external_effect_v1(str(reserved.reservation.reservation_id))
    assert failed.reservation is not None
    assert failed.reservation.state is ReservationStateV1.RELEASED
    assert owner.active_sum_v1() == Decimal("0")
    plan = owner.try_reserve_v1(
        slot_id="LANE_2",
        decision_id="d2",
        cycle_id="c1",
        observation_id=observation_id,
        amount=Decimal("25"),
    )
    assert plan.reservation is not None
    closed = owner.release_plan_failure_v1(str(plan.reservation.reservation_id))
    assert closed.reservation is not None
    assert owner.active_sum_v1() == Decimal("0")


def test_h_five_slots_cannot_exceed_budget() -> None:
    owner = PortfolioCapitalReservationBudgetOwnerV1()
    observation_id = _bind(owner, value="100")
    admitted = 0
    for index in range(1, 6):
        result = owner.try_reserve_v1(
            slot_id=SlotId(f"LANE_{index}"),
            decision_id=f"d{index}",
            cycle_id="c1",
            observation_id=observation_id,
            amount=Decimal("30"),
        )
        if result.disposition is ReserveDispositionV1.ADMITTED:
            admitted += 1
        assert owner.active_sum_v1() <= owner.admitted_budget_v1()
    assert admitted == 3
    assert owner.active_sum_v1() == Decimal("90")
    exact = PortfolioCapitalReservationBudgetOwnerV1()
    exact_id = _bind(exact, value="100")
    for index in range(1, 6):
        result = exact.try_reserve_v1(
            slot_id=f"LANE_{index}",
            decision_id=f"e{index}",
            cycle_id="c2",
            observation_id=exact_id,
            amount=Decimal("20"),
        )
        assert result.disposition is ReserveDispositionV1.ADMITTED
    assert exact.active_sum_v1() == Decimal("100")
    overflow = exact.try_reserve_v1(
        slot_id="LANE_1",
        decision_id="extra",
        cycle_id="c2",
        observation_id=exact_id,
        amount=Decimal("0.01"),
    )
    assert overflow.disposition is ReserveDispositionV1.DENIED
    assert exact.active_sum_v1() == Decimal("100")


def test_i_missing_or_invalid_capital_fact_fails_closed() -> None:
    owner = PortfolioCapitalReservationBudgetOwnerV1()
    missing = produce_current_productive_29p_risk_capital_v1(
        observation=None,
        p01=None,
        eligibility=None,
    )
    bound = owner.bind_canonical_producer_output_v1(missing)
    assert bound.disposition is ReserveDispositionV1.FAIL_CLOSED
    assert bound.mutated is False
    raw = owner.bind_canonical_producer_output_v1({"availEq": "100"})
    assert raw.disposition is ReserveDispositionV1.FAIL_CLOSED
    unbound = owner.try_reserve_v1(
        slot_id="LANE_1",
        decision_id="d1",
        cycle_id="c1",
        observation_id="f" * 64,
        amount=Decimal("1"),
    )
    assert unbound.disposition is ReserveDispositionV1.FAIL_CLOSED
    assert owner.active_sum_v1() == Decimal("0")
    seam = admit_sized_slot_reservation_v1(
        owner,
        observation=None,
        p01=None,
        eligibility=None,
        slot_id="LANE_1",
        decision_id="d1",
        cycle_id="c1",
        instrument_id=INSTRUMENT,
        account_identity=ACCOUNT,
        sizing_input=_sizing_input(),
        fresh_pretrade_get_status=TRUSTED,
        live_account_bound_status=BOUND,
        fresh_evidence_fetched=False,
        fresh_evidence_validated=False,
    )
    assert seam.disposition is ReserveDispositionV1.FAIL_CLOSED
    assert seam.reservation is None
    assert owner.stored_reservation_count_v1() == 0


def test_j_existing_n1_sizing_path_is_unchanged() -> None:
    output = _produce()
    equity = Decimal(output.value)
    sizing_input = _sizing_input(account_equity=equity)
    direct = evaluate_capital_risk_sizing_v1(sizing_input)
    owner = PortfolioCapitalReservationBudgetOwnerV1()
    seam = _admit(owner, slot="LANE_1", decision="decision-001", sizing=sizing_input)
    assert direct.outcome is CapitalRiskSizingOutcome.PASS
    assert seam.sizing_decision is not None
    assert seam.sizing_decision.canonical_position_sizing is not None
    assert seam.sizing_decision.outcome is direct.outcome
    assert seam.sizing_decision.final_quantity == direct.final_quantity
    assert seam.reservation is not None
    assert (
        seam.reservation.amount == seam.sizing_decision.canonical_position_sizing.resulting_notional
    )
    assert seam.sizing_owner == SIZING_OWNER
    assert evaluate_capital_risk_sizing_v1.__module__ == SIZING_OWNER
    join_source = JOIN_PATH.read_text(encoding="utf-8")
    assert "admit_sized_slot_reservation_v1" in join_source
    assert "portfolio_capital_reservation_budget_v1" in join_source
    assert "bind_capital_risk_sizing_offline_replay_evidence_v0" in join_source
    assert POLICY_MAX_POSITIONS == 1
    assert POLICY_MULTI_FUTURE is False
    assert MAX_POSITIONS_EFFECTIVE == 1
    assert MULTI_FUTURE_RUNTIME_AUTHORIZED is False
    assert N_GT_1_ENABLED is False
    assert EXTERNAL_EFFECT_AUTHORIZED is False
    assert POST_ALLOWED is False
    assert REAL_VENUE_POST_ALLOWED is False


def test_requested_is_transient_inside_the_atomic_reserve() -> None:
    owner = PortfolioCapitalReservationBudgetOwnerV1()
    observation_id = _bind(owner)
    result = owner.try_reserve_v1(
        slot_id="LANE_1",
        decision_id="d1",
        cycle_id="c1",
        observation_id=observation_id,
        amount=Decimal("10"),
    )
    assert result.reservation is not None
    assert result.reservation.state is ReservationStateV1.RESERVED
    assert result.reservation.transition_trace == (
        ReservationStateV1.REQUESTED.value,
        ReservationStateV1.RESERVED.value,
    )


def test_restart_without_canonical_state_fails_closed() -> None:
    owner = PortfolioCapitalReservationBudgetOwnerV1()
    observation_id = _bind(owner)
    reserved = owner.try_reserve_v1(
        slot_id="LANE_1",
        decision_id="d1",
        cycle_id="c1",
        observation_id=observation_id,
        amount=Decimal("10"),
    )
    assert reserved.reservation is not None
    restarted = owner.restart_fail_closed_v1()
    assert restarted.disposition is ReserveDispositionV1.FAIL_CLOSED
    assert owner.active_sum_v1() == Decimal("0")
    assert owner.budget_state_v1().canonical_restart_reconstructable is False
    assert CANONICAL_RESTART_RECONSTRUCTABLE is False
    blocked = owner.try_reserve_v1(
        slot_id="LANE_1",
        decision_id="d1",
        cycle_id="c1",
        observation_id=observation_id,
        amount=Decimal("10"),
    )
    assert blocked.disposition is ReserveDispositionV1.FAIL_CLOSED
    try:
        owner.reject_unproven_restore_v1({"reservations": ["stale"]})
    except PortfolioCapitalBudgetError as exc:
        assert "UNPROVEN_RESTART_RESTORE_FORBIDDEN" in str(exc)
    else:
        raise AssertionError("unproven restore must fail closed")
    fresh_id = _bind(owner, value="100.00", epoch="2026-09-15T13:00:00Z")
    assert fresh_id != observation_id
    assert owner.active_sum_v1() == Decimal("0")


def test_property_active_sum_never_exceeds_admitted_budget() -> None:
    owner = PortfolioCapitalReservationBudgetOwnerV1()
    observation_id = _bind(owner, value="100")
    rng = random.Random(19)
    live: list[str] = []
    for step in range(200):
        roll = rng.randrange(4)
        if roll == 0 and live:
            reservation_id = live.pop(rng.randrange(len(live)))
            owner.release_v1(reservation_id, reason=ReleaseReasonV1.ABANDONED)
        elif roll == 1 and live:
            owner.commit_internal_pre_external_effect_v1(live[rng.randrange(len(live))])
        else:
            amount = Decimal(rng.choice(["1", "10", "25", "40", "60", "100"]))
            result = owner.try_reserve_v1(
                slot_id=f"LANE_{(step % 5) + 1}",
                decision_id=f"prop-{step}",
                cycle_id="property",
                observation_id=observation_id,
                amount=amount,
            )
            if (
                result.disposition is ReserveDispositionV1.ADMITTED
                and result.reservation is not None
            ):
                live.append(str(result.reservation.reservation_id))
                assert result.reservation.state is not ReservationStateV1.REQUESTED
        assert owner.active_sum_v1() <= owner.admitted_budget_v1()
        assert owner.invariant_holds_v1()


def test_sizing_deny_does_not_reserve() -> None:
    owner = PortfolioCapitalReservationBudgetOwnerV1()
    denied = _admit(
        owner,
        slot="LANE_1",
        decision="blocked",
        sizing=_sizing_input(maximum_positions=0),
    )
    assert denied.disposition is ReserveDispositionV1.DENIED
    assert denied.reservation is None
    assert owner.active_sum_v1() == Decimal("0")
    assert PORTFOLIO_BUDGET_OWNER == RESERVATION_OWNER
    assert "evaluate_capital_slot_ratchet" not in inspect.getsource(
        PortfolioCapitalReservationBudgetOwnerV1
    )


def test_unknown_cancel_fails_closed() -> None:
    owner = PortfolioCapitalReservationBudgetOwnerV1()
    observation_id = _bind(owner)
    reserved = owner.try_reserve_v1(
        slot_id="LANE_1",
        decision_id="d1",
        cycle_id="c1",
        observation_id=observation_id,
        amount=Decimal("15"),
    )
    assert reserved.reservation is not None
    unknown = owner.cancel_before_external_effect_v1("b" * 64)
    assert unknown.disposition is ReserveDispositionV1.FAIL_CLOSED
    cancelled = owner.cancel_before_external_effect_v1(str(reserved.reservation.reservation_id))
    assert cancelled.reservation is not None
    assert cancelled.reservation.state is ReservationStateV1.RELEASED
    assert owner.active_sum_v1() == Decimal("0")
