"""Original funding/accounting -> atomic budget renewal -> original consumers."""

from dataclasses import replace
from decimal import Decimal
import json
from pathlib import Path

import pytest

from src.ops.portfolio_capital_reservation_budget_v1 import entry_execution_cost_v1 as cost
from src.ops.portfolio_capital_reservation_budget_v1.open_slot_cost_renewal_v1 import (
    FundingSettlementAssignmentV1,
    OpenSlotCostRenewalContextV1,
)
from src.ops.portfolio_capital_reservation_budget_v1.test_phase_limits_v1 import (
    load_slot_entry_budget_v1,
)
from tests.ops import test_open_slot_loss_protection_v1 as connected
from tests.ops import test_current_open_slot_cost_protection_v1 as current
from tests.ops.test_closing_execution_cost_provision_v1 import (
    install_policy,
    no_network as no_network,
)
from tests.ops.test_next_funding_cost_provision_v1 import attach_funding_probe
from tests.ops._opening_execution_cost_fixture_v1 import install_cost_probe
from tests.ops.test_n1_original_reservation_host_handoff_v1 import (
    synthetic_ports_and_isolation as synthetic_ports_and_isolation,
)

ROOT = Path(__file__).resolve().parents[2]


def policy():
    return load_slot_entry_budget_v1(
        ROOT / "docs/ops/specs/BOUNDED_MULTISLOT_TEST_ENTRY_BUDGET_V8.json"
    )


def value_for(
    world,
    lane,
    epoch,
    *,
    periods=(),
    next_horizon=None,
    fault=None,
    fee="0.0005",
    capital="1000",
    output=None,
):
    owner, rid = world["host"].owner, world["holds"][lane]
    value = current.current_sources(owner, rid, connected.observation(world, lane, epoch), fee=fee)
    sources = json.loads(value.cost_sources_json)
    funding = sources["funding"]
    original_horizon = json.loads(owner._sizing_bindings[rid].funding_cost_binding.receipt_json)[
        "upcoming_funding_time_ms"
    ]
    horizon = next_horizon or original_horizon
    funding["payload"]["data"][0].update(
        fundingTime=str(horizon), nextFundingTime=str(horizon + 17000)
    )
    funding["body_sha256"] = cost.digest(funding["payload"])
    value = replace(value, cost_sources_json=cost.canonical(sources))
    if output is None:
        output = connected.original.capital(
            world["host"], world["bounds"][lane], epoch
        ).producer_output
    if capital != "1000":
        output = replace(output, value=capital)
    assignments = []
    session = world["sessions"][lane]
    for time, event_id in periods:
        row = session.funding_events[event_id]
        assignments.append(
            FundingSettlementAssignmentV1(
                time,
                event_id,
                **{k: row[k] for k in ("amount", "currency", "instrument_id", "event_time_unix")},
            )
        )
    pages = []
    if periods:
        raw = json.loads(cost.canonical(funding))
        prior = owner._open_slot_cost_reserves.get(rid, [])
        lower = prior[-1]["upcoming_funding_time_ms"] if prior else original_horizon
        raw["endpoint"] = (
            f"/api/v5/public/funding-rate-history?instId={world['bounds'][lane].venue_native_id}&before={lower - 1}&after={horizon}&limit=400"
        )
        raw["payload"] = dict(
            code="0",
            data=[
                dict(
                    instId=world["bounds"][lane].venue_native_id,
                    instType=funding["payload"]["data"][0]["instType"],
                    fundingTime=str(time),
                    realizedRate="0.0001",
                )
                for time, _ in reversed(periods)
            ],
        )
        raw["body_sha256"] = cost.digest(raw["payload"])
        pages = [cost.FreshPretradeGetTransportResultV1(**raw)]
    if fault == "missing-payment":
        assignments = []
    elif fault == "missing-history":
        pages = []
    elif fault == "wrong-amount":
        assignments[0] = replace(assignments[0], amount="999")
    elif fault == "wrong-period":
        assignments[0] = replace(assignments[0], funding_time_ms=assignments[0].funding_time_ms + 1)
    elif fault == "wrong-event":
        assignments[0] = replace(assignments[0], event_id="not-in-accounting")
    elif fault == "wrong-currency":
        assignments[0] = replace(assignments[0], currency="USDC")
    elif fault == "missing-period":
        raw = json.loads(cost.canonical(pages[0].__dict__))
        raw["payload"]["data"].pop(0)
        pages = [cost.FreshPretradeGetTransportResultV1(**raw)]
    elif fault == "wrong-history-direction":
        pages = [replace(pages[0], endpoint=pages[0].endpoint.replace("before=", "wrong="))]
    elif fault == "foreign-history-context":
        pages = [replace(pages[0], pretrade_decision_id="other-slot")]
    elif fault == "reused-history":
        pages = [replace(pages[0], historical_reuse=True)]
    elif fault == "future-history":
        pages = [replace(pages[0], acquired_at_utc=connected.original.utc(epoch + 1))]
    elif fault == "capital-before-payment":
        output = replace(
            output, observed_at_as_of=connected.original.utc(periods[-1][0] / 1000 - 1)
        )
    elif fault == "stale-history":
        pages = [replace(pages[0], acquired_at_utc=connected.original.utc(epoch - 20))]
    elif fault == "foreign-capital":
        output = replace(output, bound_account_identity="other-account")
    elif fault == "stale-capital":
        output = replace(output, observed_at_as_of=connected.original.utc(epoch - 20))
    elif fault == "future-capital":
        output = replace(output, decision_epoch=connected.original.utc(epoch + 1))
    context = OpenSlotCostRenewalContextV1.capture_v1(
        owner=owner, capital_output=output, settlements=assignments, history_sources=pages
    )
    return replace(
        value,
        renewal_context_json="null"
        if fault == "missing-context"
        else cost.canonical(context.to_dict_v1()),
    )


class Driver:
    def __init__(
        self,
        root,
        *,
        target="LANE_1",
        fault=None,
        fee="0.0005",
        capital="1000",
        skipped=False,
        amount="-0.03",
        finish_close=False,
        pre_renew_all=False,
    ):
        self.root, self.target, self.fault = root, target, fault
        self.fee, self.capital, self.skipped, self.amount = fee, capital, skipped, amount
        self.finish_close, self.world = finish_close, None
        self.pre_renew_all = pre_renew_all

    def nominate(self, world):
        self.membership = world["membership"]
        return world["recovery"]

    def close(self, world):
        self.world = world
        lane, owner = self.target, world["host"].owner
        rid = world["holds"][lane]
        epoch = world["kwargs"]["observed_unix"]
        horizon = json.loads(owner._sizing_bindings[rid].funding_cost_binding.receipt_json)[
            "upcoming_funding_time_ms"
        ]
        periods = [(horizon, "observed-settlement-1")]
        if self.skipped:
            periods.append((horizon + 20000, "observed-settlement-2"))
        if self.fault == "capital-before-payment":
            periods.append((int(epoch * 1000) - 1500, "recent-observed-settlement"))
        session = world["sessions"][lane]
        for time, event_id in periods:
            session.apply_funding_observation_v1(
                event_id=event_id,
                amount=self.amount,
                currency=session.contract.quote_currency,
                instrument_id=session.contract.symbol,
                event_time_unix=time / 1000,
            )
        connected.advance_position_episode_from_simulated_accounting_v1(
            episode=world["episodes"][lane],
            session=session,
            fills=tuple(world["fills"][lane]),
            source_archive_root=self.root / "renewal-funding",
            cursor_store_root=Path(world["pairs"][lane][0].lane_state_root),
            expected_scope=world["scope"],
            writer_session_id="observed-renewal-settlements",
        )
        next_horizon = int(epoch * 1000) + 23000
        if self.pre_renew_all:
            next_horizon = int(epoch * 1000) + 1800000
            for other in world["bounds"]:
                assigned = periods
                if other != lane:
                    other_rid = world["holds"][other]
                    old_time = json.loads(
                        owner._sizing_bindings[other_rid].funding_cost_binding.receipt_json
                    )["upcoming_funding_time_ms"]
                    assigned = [(old_time, "observed-other-slot-settlement")]
                    other_session = world["sessions"][other]
                    other_session.apply_funding_observation_v1(
                        event_id=assigned[0][1],
                        amount="-0.03",
                        currency=other_session.contract.quote_currency,
                        instrument_id=other_session.contract.symbol,
                        event_time_unix=old_time / 1000,
                    )
                    connected.advance_position_episode_from_simulated_accounting_v1(
                        episode=world["episodes"][other],
                        session=other_session,
                        fills=tuple(world["fills"][other]),
                        source_archive_root=self.root / "renewal-funding" / other,
                        cursor_store_root=Path(world["pairs"][other][0].lane_state_root),
                        expected_scope=world["scope"],
                        writer_session_id="other-slot-renewal",
                    )
                earlier = value_for(
                    world, other, epoch - 0.5, periods=assigned, next_horizon=next_horizon
                )
                assert (
                    owner.observe_open_slot_loss_v1(
                        slot_id=other,
                        episode=world["episodes"][other],
                        observation=earlier,
                        mark_px=world["kwargs"]["mark_px"],
                        observed_unix=epoch - 0.5,
                    )
                    is None
                )
            periods = []
        self.observation = value_for(
            world,
            lane,
            epoch,
            periods=periods,
            next_horizon=next_horizon,
            fault=self.fault,
            fee=self.fee,
            capital=self.capital,
        )
        world["kwargs"]["live_29p_injected_by_lane"] = {
            l: replace(v, open_slot_loss_observation=self.observation if l == lane else None)
            for l, v in world["kwargs"]["live_29p_injected_by_lane"].items()
        }
        world["kwargs"]["rotation_exit_requests"] = {}
        self.before = owner.budget_state_v1()
        self.before_readback = owner.local_commitment_readback_v1()
        self.sequence = owner._store.sequence
        self.results = connected.original.invoke_occupied_lane_governed_cycle_n1_consumer_v1(
            world["pairs"], **world["kwargs"]
        )
        self.after = owner.budget_state_v1()
        if self.finish_close:
            return self.results
        raise connected.Observed()


def run(tmp_path, monkeypatch, *, count=2, **options):
    install_policy(monkeypatch, policy())
    monkeypatch.setattr(connected.original, "policy", policy)
    attach_funding_probe(monkeypatch, funding_seconds=3600)
    install_cost_probe(monkeypatch)
    driver = Driver(tmp_path, **options)
    try:
        with pytest.raises(connected.Observed):
            connected.original.connected_close(
                tmp_path, monkeypatch, count, driver.target, rotation_driver=driver
            )
    except BaseException:
        if driver.world:
            connected.cleanup(driver)
        raise
    return driver


@pytest.mark.parametrize("count,target,skipped", [(2, "LANE_1", False), (5, "LANE_5", True)])
@pytest.mark.parametrize("amount", ["-0.03", "0", "0.04"])
def test_original_settlements_renew_one_slot_atomically_without_redebit_or_resize(
    tmp_path, monkeypatch, count, target, skipped, amount
):
    driver = run(tmp_path, monkeypatch, count=count, target=target, skipped=skipped, amount=amount)
    try:
        owner = driver.world["host"].owner
        proof = current.latest(driver, target)
        assert proof["reserve_renewal_status"] == "RENEWAL_ADMITTED", proof[
            "reserve_renewal_reasons"
        ]
        receipt = proof["reserve_renewal"]
        assert len(receipt["settlements"]) == (2 if skipped else 1)
        assert owner._store.sequence == driver.sequence + 1
        assert driver.after.active_reservation_sum == driver.before.active_reservation_sum
        after = owner.local_commitment_readback_v1()
        for a, b in zip(driver.before_readback.commitments, after.commitments):
            assert a.amount == b.amount and a.canonical_quantity == b.canonical_quantity
            if a.slot_id != target:
                assert a == b
        assert driver.after.remaining_unreserved == Decimal(1000) - after.active_commitment_sum
        assert Decimal(receipt["held_after_usdc"]) == after.active_commitment_sum
        session = driver.world["sessions"][target]
        session.mark_to_market(Decimal(proof["native_mark_price"]))
        assert (
            Decimal(proof["native_net_result"])
            == session.portfolio_state().equity - session.initial_equity
        )
        assert not proof["close_required"]
        assert driver.results[target].position_management_close_intent is None
        seq = owner._store.sequence
        assert (
            owner.observe_open_slot_loss_v1(
                slot_id=target,
                episode=driver.world["episodes"][target],
                observation=driver.observation,
                mark_px=driver.world["kwargs"]["mark_px"],
                observed_unix=driver.world["kwargs"]["observed_unix"],
            )
            is None
        )
        assert owner._store.sequence == seq
    finally:
        connected.cleanup(driver)


@pytest.mark.parametrize(
    "fault",
    [
        "missing-context",
        "missing-history",
        "missing-payment",
        "wrong-amount",
        "wrong-period",
        "wrong-event",
        "wrong-currency",
        "missing-period",
        "wrong-history-direction",
        "foreign-history-context",
        "reused-history",
        "future-history",
        "capital-before-payment",
        "stale-history",
        "foreign-capital",
        "stale-capital",
        "future-capital",
    ],
)
def test_unproven_renewal_retains_all_holds_and_blocks_early_and_late_entry(
    tmp_path, monkeypatch, fault
):
    driver = run(tmp_path, monkeypatch, skipped=True, fault=fault)
    try:
        owner = driver.world["host"].owner
        proof = current.latest(driver)
        assert proof["reserve_renewal_status"] == "UNPROVEN_HELD_RESERVES_RETAINED", proof
        assert proof["reserve_renewal"] is None and proof["reserve_renewal_reasons"]
        if fault == "capital-before-payment":
            assert proof["reserve_renewal_reasons"] == [
                "OPEN_SLOT_RENEWAL_CAPITAL_BEFORE_ACCOUNTING"
            ]
        assert driver.before == driver.after
        result = owner.try_reserve_v1(
            slot_id="LANE_3",
            decision_id="blocked-new-entry",
            cycle_id="blocked-renewal",
            observation_id=owner.budget_state_v1().observation_id,
            amount=Decimal(1),
        )
        assert result.disposition.value == "FAIL_CLOSED"
        assert result.reason_codes == ("OPEN_SLOT_COST_RESERVE_RENEWAL_UNPROVEN",)
        from src.ops.full_core_live_path_composition_root_v1.final_order_envelope_v1 import (
            FinalOrderEnvelopeV1,
        )
        from src.ops.full_core_live_path_composition_root_v1 import (
            current_productive_entry_budget_policy_v1 as ep,
        )

        monkeypatch.setattr(ep, "load_entry_budget_policy_v1", policy)
        rid = driver.world["holds"]["LANE_2"]
        order = FinalOrderEnvelopeV1(**owner.execution_links_v1()[rid]["envelope"])
        with pytest.raises(ValueError, match="COST_RESERVE_RENEWAL_UNPROVEN"):
            owner.inspect_current_entry_budget_policy_v1(rid, order)
    finally:
        connected.cleanup(driver)


def observe(driver, value, epoch):
    world = driver.world
    return world["host"].owner.observe_open_slot_loss_v1(
        slot_id=driver.target,
        episode=world["episodes"][driver.target],
        observation=value,
        mark_px=world["kwargs"]["mark_px"],
        observed_unix=epoch,
    )


def test_same_period_repricing_and_another_settlement_use_the_current_owned_reserve(
    tmp_path, monkeypatch
):
    driver = run(tmp_path, monkeypatch, count=5, target="LANE_5")
    try:
        world, lane = driver.world, driver.target
        owner, rid = world["host"].owner, world["holds"][lane]
        epoch = world["kwargs"]["observed_unix"] + 1
        first = current.latest(driver, lane)["reserve_renewal"]
        value = value_for(
            world, lane, epoch, next_horizon=first["upcoming_funding_time_ms"], fee="0.02"
        )
        observe(driver, value, epoch)
        second = current.latest(driver, lane)["reserve_renewal"]
        assert second["previous_reserve_ref"] == first["digest"] and not second["settlements"]
        assert Decimal(second["close_provision_usdc"]) > Decimal(first["close_provision_usdc"])
        assert (
            Decimal(second["held_after_usdc"])
            == owner.local_commitment_readback_v1().active_commitment_sum
        )
        time = second["upcoming_funding_time_ms"]
        epoch = time / 1000 + 1
        session = world["sessions"][lane]
        session.apply_funding_observation_v1(
            event_id="second-rollover-original-payment",
            amount="-0.07",
            currency=session.contract.quote_currency,
            instrument_id=session.contract.symbol,
            event_time_unix=time / 1000,
        )
        connected.advance_position_episode_from_simulated_accounting_v1(
            episode=world["episodes"][lane],
            session=session,
            fills=tuple(world["fills"][lane]),
            source_archive_root=tmp_path / "second-period-sources",
            cursor_store_root=Path(world["pairs"][lane][0].lane_state_root),
            expected_scope=world["scope"],
            writer_session_id="second-period",
        )
        value = value_for(
            world,
            lane,
            epoch,
            periods=[(time, "second-rollover-original-payment")],
            next_horizon=int(epoch * 1000) + 11000,
        )
        observe(driver, value, epoch)
        third = current.latest(driver, lane)["reserve_renewal"]
        assert third["previous_reserve_ref"] == second["digest"]
        assert len(third["settlements"]) == 1 and third["settlements"][0]["amount"] == "-0.07"
        assert len(owner._open_slot_cost_reserves[rid]) == 3
        assert owner.active_slot_sum_v1(lane) == next(
            v.amount for v in driver.before_readback.commitments if v.slot_id == lane
        )
        root = world["host"].root / "owner"
        world["host"].close()
        from tests.ops.test_test_phase_slot_loss_budget_v1 import _cold_owner
        from src.ops.portfolio_capital_reservation_budget_v1.durable_store_v1 import (
            DurableBudgetStoreV1,
        )

        store = DurableBudgetStoreV1(root, account_identity="acct-1", mode="recover")
        raw = store.load()
        store.close()
        cold = _cold_owner(root, raw, selected_policy=policy())
        try:
            assert len(cold._open_slot_cost_reserves[rid]) == 3
            assert not cold.budget_state_v1().admitted and cold.budget_state_v1().recovery_required
            assert cold.local_commitment_readback_v1().active_commitment_sum == Decimal(
                third["held_after_usdc"]
            )
        finally:
            cold.close()
    finally:
        connected.cleanup(driver)


@pytest.mark.parametrize("fault", [None, "cost", "missing-reserve", "missing-state", "payment"])
def test_five_holds_and_renewal_survive_cold_read_or_reject_semantic_tampering(
    tmp_path, monkeypatch, fault
):
    from tests.ops.test_test_phase_slot_loss_budget_v1 import _cold_owner
    from src.ops.portfolio_capital_reservation_budget_v1.durable_store_v1 import (
        DurableBudgetStoreV1,
    )
    from src.ops.portfolio_capital_reservation_budget_v1.contract_v1 import (
        PortfolioCapitalBudgetError,
    )

    driver = run(tmp_path, monkeypatch, count=5, target="LANE_5", skipped=True)
    world = driver.world
    owner, rid = world["host"].owner, world["holds"]["LANE_5"]
    expected = owner.local_commitment_readback_v1().active_commitment_sum
    root = world["host"].root / "owner"
    world["host"].close()
    store = DurableBudgetStoreV1(root, account_identity="acct-1", mode="recover")
    try:
        raw = store.load()
        if fault == "missing-state":
            del raw["open_slot_cost_reserves"]
        elif fault == "missing-reserve":
            raw["open_slot_cost_reserves"] = {}
        elif fault:
            receipt = raw["open_slot_cost_reserves"][rid][0]
            if fault == "cost":
                receipt["close_provision_usdc"] = "0"
            else:
                receipt["settlements"][0]["amount"] = "0"
            receipt["digest"] = cost.digest({k: v for k, v in receipt.items() if k != "digest"})
        if fault:
            store.save(raw)
    finally:
        store.close()
    cold = None
    try:
        if fault:
            with pytest.raises(PortfolioCapitalBudgetError, match="SEMANTIC_RESTORE_UNPROVEN"):
                _cold_owner(root, raw, selected_policy=policy())
        else:
            cold = _cold_owner(root, raw, selected_policy=policy())
            assert cold.budget_state_v1().recovery_required and not cold.budget_state_v1().admitted
            assert cold.local_commitment_readback_v1().active_commitment_sum == expected
            assert all(cold.active_slot_sum_v1(f"LANE_{i}") > 0 for i in range(1, 6))
            assert (
                cold.test_slot_loss_state_v1("LANE_5")["open_position_protection"]["latest"][
                    "reserve_renewal_status"
                ]
                == "RENEWAL_ADMITTED"
            )
    finally:
        if cold:
            cold.close()
        connected.cleanup(driver)


@pytest.mark.parametrize("committed", [False, True])
def test_unknown_renewal_commit_requires_original_cold_recovery(tmp_path, monkeypatch, committed):
    from tests.ops.test_test_phase_slot_loss_budget_v1 import _cold_owner
    from src.ops.portfolio_capital_reservation_budget_v1.durable_store_v1 import (
        DurableBudgetStoreV1,
    )
    from src.ops.portfolio_capital_reservation_budget_v1.contract_v1 import (
        PortfolioCapitalBudgetError,
    )

    driver = run(tmp_path, monkeypatch, count=5, target="LANE_5")
    world, lane = driver.world, driver.target
    owner, rid = world["host"].owner, world["holds"][lane]
    epoch = world["kwargs"]["observed_unix"] + 1
    first = current.latest(driver, lane)["reserve_renewal"]
    value = value_for(
        world, lane, epoch, next_horizon=first["upcoming_funding_time_ms"], fee="0.02"
    )
    save = owner._store.save

    def uncertain(state):
        if committed:
            save(state)
        raise OSError("explicit interrupted renewal acknowledgement")

    monkeypatch.setattr(owner._store, "save", uncertain)
    with pytest.raises(PortfolioCapitalBudgetError, match="COMMIT_UNPROVEN_REOPEN_REQUIRED"):
        observe(driver, value, epoch)
    assert owner.budget_state_v1().recovery_required and not owner.budget_state_v1().admitted
    assert owner.active_sum_v1() == driver.before.active_reservation_sum
    with pytest.raises(PortfolioCapitalBudgetError, match="WRITER_UNAVAILABLE"):
        observe(driver, value, epoch)
    root = world["host"].root / "owner"
    world["host"].close()
    store = DurableBudgetStoreV1(root, account_identity="acct-1", mode="recover")
    raw = store.load()
    store.close()
    cold = _cold_owner(root, raw, selected_policy=policy())
    try:
        assert len(cold._open_slot_cost_reserves[rid]) == (2 if committed else 1)
        assert cold.budget_state_v1().recovery_required and not cold.budget_state_v1().admitted
        assert cold.active_sum_v1() == driver.before.active_reservation_sum
        assert all(cold.active_slot_sum_v1(f"LANE_{i}") > 0 for i in range(1, 6))
    finally:
        cold.close()
        connected.cleanup(driver)


def test_stale_budget_revision_cannot_overwrite_a_newer_transaction(tmp_path, monkeypatch):
    driver = run(tmp_path, monkeypatch)
    try:
        owner, lane = driver.world["host"].owner, driver.target
        epoch = driver.world["kwargs"]["observed_unix"] + 1
        first = current.latest(driver, lane)["reserve_renewal"]
        value = value_for(
            driver.world, lane, epoch, next_horizon=first["upcoming_funding_time_ms"], fee="0.02"
        )
        owner._store.save(owner._durable_payload_locked())
        before = owner.budget_state_v1(), owner._store.sequence, owner.test_slot_loss_state_v1(lane)
        with pytest.raises(ValueError, match="BUDGET_EPOCH_CHANGED"):
            observe(driver, value, epoch)
        assert before == (
            owner.budget_state_v1(),
            owner._store.sequence,
            owner.test_slot_loss_state_v1(lane),
        )
    finally:
        connected.cleanup(driver)


def test_expired_holds_block_entries_after_restart_even_without_a_new_observation(
    tmp_path, monkeypatch
):
    driver = run(tmp_path, monkeypatch)
    try:
        owner = driver.world["host"].owner
        horizon = current.latest(driver)["reserve_renewal"]["upcoming_funding_time_ms"]
        monkeypatch.setattr(cost, "utc_now_iso_v1", lambda: connected.original.utc(horizon / 1000))
        result = owner.try_reserve_v1(
            slot_id="LANE_3",
            decision_id="expired-cost-entry",
            cycle_id="expired-period",
            observation_id=owner.budget_state_v1().observation_id,
            amount=Decimal(1),
        )
        assert result.reason_codes == ("OPEN_SLOT_COST_RESERVES_EXPIRED_RENEWAL_REQUIRED",)
    finally:
        connected.cleanup(driver)


def test_natural_short_settlement_and_ask_cost_reach_original_s7(tmp_path, monkeypatch):
    from tests.ops import test_open_slot_loss_short_protection_v1 as short
    from src.ops.portfolio_capital_reservation_budget_v1.contract_v1 import (
        PortfolioCapitalReservationBudgetOwnerV1 as Owner,
    )
    from src.ops.exit_policy_producer_binding_v1.simulated_accounting_progress_v1 import _source
    from src.ops.portfolio_capital_reservation_budget_v1.slot_economic_source_v1 import _fill
    from src.ops.productive_futures_accounting_runtime_binding_v1.accounting_engine_v1 import (
        ProductiveFuturesAccountingSessionV1,
    )
    from src.ops.single_selected_future_runtime_binding_v1.models_v1 import BoundInstrumentV1

    bind = Owner.bind_execution_plan_v1
    cursor = []

    def capture(owner, rid, order, **kwargs):
        cursor.append(kwargs["core_cursor_root"])
        return bind(owner, rid, order, **kwargs)

    def supplied(world, lane, epoch, **kwargs):
        owner, rid = world["host"].owner, world["holds"][lane]
        episode = world["episodes"][lane]
        payload, _ = _source(episode.entry_source_ref, episode.identity)
        session = ProductiveFuturesAccountingSessionV1.from_durable_dict(
            payload["accounting_checkpoint"]
        )
        horizon = json.loads(owner._sizing_bindings[rid].funding_cost_binding.receipt_json)[
            "upcoming_funding_time_ms"
        ]
        session.apply_funding_observation_v1(
            event_id="short-original-period-payment",
            amount="-0.03",
            currency=session.contract.quote_currency,
            instrument_id=session.contract.symbol,
            event_time_unix=horizon / 1000,
        )
        connected.advance_position_episode_from_simulated_accounting_v1(
            episode=episode,
            session=session,
            fills=tuple(_fill(v) for v in payload["fills"]),
            source_archive_root=tmp_path / "short-renewal-sources",
            cursor_store_root=Path(cursor[-1]),
            expected_scope=episode.identity.account_scope,
            writer_session_id="short-renewal",
        )
        world["sessions"] = {lane: session}
        world["bounds"] = {lane: BoundInstrumentV1(**owner._reservation_bindings[rid]["bound"])}
        from tests.ops.test_portfolio_capital_reservation_budget_contract_v1 import (
            _obs,
            _p01,
            _eligibility,
        )
        from src.ops.governed_productive_account_equity_authority_producer_v1.current_productive_29p_risk_capital_model_v1 import (
            produce_current_productive_29p_risk_capital_v1,
        )

        stamp = connected.original.utc(epoch)
        output = produce_current_productive_29p_risk_capital_v1(
            observation=replace(
                _obs(value="1000", epoch=stamp), bound_account_identity=owner._account_identity
            ),
            p01=replace(_p01(stamp), bound_account_identity=owner._account_identity),
            eligibility=replace(
                _eligibility(stamp), bound_account_identity=owner._account_identity
            ),
        )
        assert output.produced == "true", output.reason_codes
        return value_for(
            world,
            lane,
            epoch,
            periods=[(horizon, "short-original-period-payment")],
            next_horizon=int(epoch * 1000) + 23000,
            fee="10",
            output=output,
        )

    monkeypatch.setattr(Owner, "bind_execution_plan_v1", capture)
    monkeypatch.setattr(short, "policy", policy)
    monkeypatch.setattr(
        short,
        "attach_funding_probe",
        lambda mp, **kwargs: attach_funding_probe(mp, funding_seconds=1),
    )
    monkeypatch.setattr(short, "observation", supplied)
    proof = short._run_original_short_loss_probe(tmp_path, monkeypatch, remaining=Decimal(1))[0]
    assert (
        proof["reserve_renewal_status"] == "INSUFFICIENT_LOSS_ALLOWANCE_HELD_RESERVES_RETAINED"
    ), proof
    assert proof["current_cost_provision"]["closing_order_side"] == "BUY"
    assert Decimal(proof["current_cost_provision"]["adverse_funding_rate"]) == Decimal("0.02")


def test_renewed_holds_reach_original_close_release_and_next_natural_entry(tmp_path, monkeypatch):
    from tests.ops.test_test_phase_slot_loss_budget_v1 import _install_test_path

    _install_test_path(monkeypatch, exhausted=False)
    install_policy(monkeypatch, policy())
    monkeypatch.setattr(connected.original, "policy", policy)
    attach_funding_probe(monkeypatch, funding_seconds=3600)
    install_cost_probe(monkeypatch)
    driver = Driver(tmp_path, target="LANE_5", fee="10", finish_close=True, pre_renew_all=True)
    connected.original.roundtrip(
        tmp_path,
        monkeypatch,
        5,
        "LANE_5",
        False,
        rotation_driver=driver,
        expected_exit_class="safety_exit",
    )
    assert all(driver.world["host"].owner.active_slot_sum_v1(f"LANE_{i}") > 0 for i in range(1, 6))


@pytest.mark.parametrize(
    "options,status",
    [
        (dict(capital="1"), "INSUFFICIENT_CAPITAL_HELD_RESERVES_RETAINED"),
        (dict(fee="10"), "INSUFFICIENT_LOSS_ALLOWANCE_HELD_RESERVES_RETAINED"),
    ],
)
def test_proven_insufficient_cover_reaches_original_target_safety_exit(
    tmp_path, monkeypatch, options, status
):
    driver = run(tmp_path, monkeypatch, count=5, target="LANE_5", **options)
    try:
        proof = current.latest(driver, "LANE_5")
        assert proof["reserve_renewal_status"] == status, proof
        assert proof["close_required"] and driver.before == driver.after
        assert (
            driver.results[
                "LANE_5"
            ].s7_invocation.cycle_result.replay.intermediate.entry_exit_decision.exit_class.value
            == "safety_exit"
        )
        assert driver.results["LANE_5"].position_management_close_intent is not None
        assert all(
            v.position_management_close_intent is None
            for k, v in driver.results.items()
            if k != "LANE_5"
        )
    finally:
        connected.cleanup(driver)
