"""Original accounting -> durable slot fact -> original controlled N1 exit."""

from dataclasses import replace
from decimal import Decimal
import json
from pathlib import Path

import pytest

from src.ops.portfolio_capital_reservation_budget_v1 import entry_execution_cost_v1 as cost
from src.ops.portfolio_capital_reservation_budget_v1.test_phase_limits_v1 import (
    load_slot_entry_budget_v1,
)
from src.ops.portfolio_capital_reservation_budget_v1.sizing_binding_v1 import (
    ReservationSizingBindingV1,
)
from src.ops.exit_policy_producer_binding_v1.simulated_accounting_progress_v1 import (
    advance_position_episode_from_simulated_accounting_v1,
)
from tests.ops import test_bounded_slot_connected_roundtrip_v1 as original
from tests.ops.test_closing_execution_cost_provision_v1 import install_policy
from tests.ops.test_next_funding_cost_provision_v1 import attach_funding_probe
from tests.ops._opening_execution_cost_fixture_v1 import install_cost_probe
from tests.ops.test_n1_original_reservation_host_handoff_v1 import (
    synthetic_ports_and_isolation as synthetic_ports_and_isolation,
)

ROOT = Path(__file__).resolve().parents[2]


def policy():
    return load_slot_entry_budget_v1(
        ROOT / "docs/ops/specs/BOUNDED_MULTISLOT_TEST_ENTRY_BUDGET_V6.json"
    )


class Observed(Exception):
    pass


def observation(world, lane, epoch, *, mark_px=None):
    owner = world["host"].owner
    rid = world["holds"][lane]
    binding = ReservationSizingBindingV1.from_dict_v1(
        owner.risk_snapshot_v1()["state"]["sizing_bindings"][rid]
    )
    episode = world["episodes"][lane]
    mark_px = world["kwargs"]["mark_px"] if mark_px is None else mark_px
    native = episode.identity.venue_native_id
    kind = next(
        r
        for r in json.loads(binding.monetary_source.instruments_json)["data"]
        if r["instId"] == native
    )["instType"]
    raw = json.loads(binding.entry_cost_binding.observation_json)["sources_json"]
    source = json.loads(raw)["book"]
    payload = dict(
        code="0",
        data=[dict(instId=native, instType=kind, markPx=str(mark_px), ts=str(int(epoch * 1000)))],
    )
    source.update(
        endpoint=f"/api/v5/public/mark-price?instType={kind}&instId={native}",
        payload=payload,
        body_sha256=cost.digest(payload),
        auth_header_sent=False,
        pretrade_decision_id=cost.open_slot_mark_acquisition_id_v1(
            episode.identity, original.utc(epoch)
        ),
        acquired_at_utc=original.utc(epoch),
    )
    index = json.loads(binding.monetary_source.index_tickers_json)
    for row in index["data"]:
        row.update(idxPx="1", ts=str(int(epoch * 1000)))
    return cost.OpenSlotLossObservationV1.capture_v1(
        episode=episode,
        mark_source=cost.FreshPretradeGetTransportResultV1(**source),
        valuation_epoch=original.utc(epoch),
        index_tickers_payload=index,
        pair_instruments_payload=json.loads(
            binding.monetary_source.conversion_pair_instruments_json
        ),
        fx_acquired_at_utc=original.utc(epoch),
    )


class Driver:
    def __init__(
        self,
        root,
        *,
        target="LANE_1",
        remaining=Decimal(0),
        fault=None,
        legacy_time_exit=False,
        finish_close=False,
    ):
        self.root, self.target, self.remaining, self.fault = root, target, remaining, fault
        self.world = None
        self.legacy_time_exit = legacy_time_exit
        self.finish_close = finish_close

    def nominate(self, world):
        self.membership = world["membership"]
        return world["recovery"]

    def close(self, world):
        self.world = world
        lane = self.target
        session = world["sessions"][lane]
        mark = Decimal(str(world["kwargs"]["mark_px"]))
        session.mark_to_market(mark)
        prior = session.portfolio_state().equity - session.initial_equity
        session.apply_funding_observation_v1(
            event_id="explicit-loss-test-settlement",
            amount=str(self.remaining - Decimal(25) - prior),
            currency=session.contract.quote_currency,
            instrument_id=session.contract.symbol,
            event_time_unix=world["event"] - 1,
        )
        advance_position_episode_from_simulated_accounting_v1(
            episode=world["episodes"][lane],
            session=session,
            fills=tuple(world["fills"][lane]),
            source_archive_root=self.root / "funding-sources",
            cursor_store_root=Path(world["pairs"][lane][0].lane_state_root),
            expected_scope=world["scope"],
            writer_session_id="explicit-loss-funding",
        )
        kwargs = world["kwargs"]
        epoch = kwargs["observed_unix"]
        obs = {l: observation(world, l, epoch) for l in world["bounds"]}
        if self.fault == "missing":
            obs[lane] = None
        elif self.fault == "foreign-slot":
            obs[lane] = obs["LANE_2"]
        elif self.fault is not None:
            value = obs[lane]
            if self.fault in {
                "stale-mark",
                "future-mark",
                "foreign-mark",
                "historical-mark",
                "wrong-mark-context",
            }:
                source = json.loads(value.mark_source_json)
                if self.fault == "stale-mark":
                    source["payload"]["data"][0]["ts"] = str(int((epoch - 10) * 1000))
                elif self.fault == "future-mark":
                    source["payload"]["data"][0]["ts"] = str(int((epoch + 1) * 1000))
                elif self.fault == "foreign-mark":
                    source["payload"]["data"][0]["instId"] = "FOREIGN-USDT-SWAP"
                elif self.fault == "historical-mark":
                    source["historical_reuse"] = True
                else:
                    source["pretrade_decision_id"] = "foreign-context"
                obs[lane] = replace(value, mark_source_json=cost.canonical(source))
            elif self.fault == "missing-fx":
                obs[lane] = replace(value, index_tickers_json="null")
            elif self.fault == "future-fx":
                obs[lane] = replace(value, fx_acquired_at_utc=original.utc(epoch + 1))
            elif self.fault == "old-episode-source":
                obs[lane] = replace(value, current_source_ref=value.initial_source_ref)
            elif self.fault == "wrong-valuation":
                obs[lane] = replace(value, valuation_epoch=original.utc(epoch - 1))
        kwargs["live_29p_injected_by_lane"] = {
            l: replace(v, open_slot_loss_observation=obs[l])
            for l, v in kwargs["live_29p_injected_by_lane"].items()
        }
        if not self.legacy_time_exit:
            kwargs["rotation_exit_requests"] = {}
        self.before = world["host"].owner.budget_state_v1()
        self.results = original.invoke_occupied_lane_governed_cycle_n1_consumer_v1(
            world["pairs"], **kwargs
        )
        self.after = world["host"].owner.budget_state_v1()
        if self.finish_close:
            return self.results
        raise Observed()


def run_open(tmp_path, monkeypatch, *, count=2, **options):
    install_policy(monkeypatch, policy())
    monkeypatch.setattr(original, "policy", policy)
    attach_funding_probe(monkeypatch, funding_seconds=7200)
    install_cost_probe(monkeypatch)
    driver = Driver(tmp_path, **options)
    try:
        with pytest.raises(Observed):
            original.connected_close(
                tmp_path, monkeypatch, count, driver.target, rotation_driver=driver
            )
    except BaseException:
        if driver.world:
            cleanup(driver)
        raise
    return driver


def cleanup(driver):
    driver.world["host"].close()
    driver.world["writer"].release()


@pytest.mark.parametrize("count,target", [(2, "LANE_1"), (5, "LANE_1"), (5, "LANE_5")])
def test_original_n1_closes_only_the_exhausted_slot_and_preserves_all_holds(
    tmp_path, monkeypatch, count, target
):
    driver = run_open(tmp_path, monkeypatch, count=count, target=target)
    try:
        result = driver.results[target]
        assert result.slot_loss_protection_status == "OBSERVED_PROTECTION_ONLY", (
            result.slot_loss_protection_reason_codes
        )
        decision = result.s7_invocation.cycle_result.replay.intermediate.entry_exit_decision
        assert decision.exit_class.value == "safety_exit"
        assert result.position_management_close_intent is not None
        assert result.governed_cycle_result.position_management_execution_handoff is not None
        assert all(
            r.position_management_close_intent is None
            for l, r in driver.results.items()
            if l != target
        )
        owner = driver.world["host"].owner
        state = owner.test_slot_loss_state_v1(target)
        assert (
            state["exhausted"]
            and state["new_entry_blocker"] == "TEST_SLOT_MARK_VALUED_LOSS_ALLOWANCE_EXHAUSTED"
        )
        proof = state["open_position_protection"]["latest"]
        assert Decimal(proof["remaining_allowance_before_future_costs_usdc"]) <= 0
        assert proof["funding_or_cost_rollover_admitted"] is False
        assert proof["private_venue_cash_observed"] is False
        assert driver.before == driver.after
        assert all(v.governed_cycle_result.post_count == 0 for v in driver.results.values())
    finally:
        cleanup(driver)


@pytest.mark.parametrize("remaining,close", [(Decimal("1"), False), (Decimal("0.01"), True)])
def test_original_cost_provisions_trigger_before_zero_without_inventing_a_percentage(
    tmp_path, monkeypatch, remaining, close
):
    driver = run_open(tmp_path, monkeypatch, remaining=remaining)
    try:
        result = driver.results["LANE_1"]
        proof = driver.world["host"].owner.test_slot_loss_state_v1("LANE_1")[
            "open_position_protection"
        ]["latest"]
        assert Decimal(proof["remaining_allowance_before_future_costs_usdc"]) == remaining
        assert proof["actual_loss_allowance_exhausted"] is False
        assert proof["close_required"] is close
        assert (result.position_management_close_intent is not None) is close
        assert driver.before == driver.after
    finally:
        cleanup(driver)


@pytest.mark.parametrize(
    "fault",
    [
        "missing",
        "foreign-slot",
        "stale-mark",
        "future-mark",
        "foreign-mark",
        "historical-mark",
        "wrong-mark-context",
        "missing-fx",
        "future-fx",
        "old-episode-source",
        "wrong-valuation",
    ],
)
def test_unproven_source_does_not_invent_a_loss_or_release_any_hold(tmp_path, monkeypatch, fault):
    driver = run_open(tmp_path, monkeypatch, fault=fault)
    try:
        result = driver.results["LANE_1"]
        assert result.slot_loss_protection_status == "UNPROVEN_ORIGINAL_EXITS_RETAINED"
        assert result.slot_loss_protection_reason_codes
        assert result.position_management_close_intent is None
        assert (
            driver.world["host"].owner.test_slot_loss_state_v1("LANE_1")["open_position_protection"]
            is None
        )
        assert driver.before == driver.after
    finally:
        cleanup(driver)


def test_missing_loss_source_preserves_original_time_exit(tmp_path, monkeypatch):
    driver = run_open(tmp_path, monkeypatch, fault="missing", legacy_time_exit=True)
    try:
        result = driver.results["LANE_1"]
        assert result.slot_loss_protection_status == "UNPROVEN_ORIGINAL_EXITS_RETAINED"
        assert (
            result.s7_invocation.cycle_result.replay.intermediate.entry_exit_decision.exit_class.value
            == "time_exit"
        )
        assert result.position_management_close_intent is not None
        assert driver.before == driver.after
    finally:
        cleanup(driver)


def test_started_cost_close_survives_a_better_mark_and_observation_replay(tmp_path, monkeypatch):
    driver = run_open(tmp_path, monkeypatch, remaining=Decimal("0.01"))
    try:
        world = driver.world
        owner = world["host"].owner
        episode = world["episodes"]["LANE_1"]
        epoch = world["kwargs"]["observed_unix"] + 1
        before = owner.test_slot_loss_state_v1("LANE_1")["open_position_protection"][
            "pending_close"
        ]
        mark = world["kwargs"]["mark_px"] * 2
        value = observation(world, "LANE_1", epoch, mark_px=mark)
        request = owner.observe_open_slot_loss_v1(
            slot_id="LANE_1", episode=episode, observation=value, mark_px=mark, observed_unix=epoch
        )
        state = owner.test_slot_loss_state_v1("LANE_1")
        assert state["open_position_protection"]["latest"]["close_required"] is False
        assert state["open_position_protection"]["pending_close"] == before
        assert request.validate_v1(
            episode=episode, bound=world["bounds"]["LANE_1"], observed_unix=epoch
        )
        seq = owner._store.sequence
        assert (
            owner.observe_open_slot_loss_v1(
                slot_id="LANE_1",
                episode=episode,
                observation=value,
                mark_px=mark,
                observed_unix=epoch,
            )
            == request
        )
        assert owner._store.sequence == seq
        with pytest.raises(ValueError, match="TIME_OR_REPLAY_CONFLICT"):
            owner.observe_open_slot_loss_v1(
                slot_id="LANE_1",
                episode=episode,
                observation=observation(world, "LANE_1", epoch - 1),
                mark_px=world["kwargs"]["mark_px"],
                observed_unix=epoch - 1,
            )
    finally:
        cleanup(driver)


def test_cold_owner_preserves_loss_close_and_all_five_original_holds(tmp_path, monkeypatch):
    from tests.ops.test_test_phase_slot_loss_budget_v1 import _cold_owner
    from src.ops.portfolio_capital_reservation_budget_v1.durable_store_v1 import (
        DurableBudgetStoreV1,
    )

    driver = run_open(tmp_path, monkeypatch, count=5, target="LANE_5")
    world = driver.world
    root = world["host"].root / "owner"
    held = driver.after
    world["host"].close()
    store = DurableBudgetStoreV1(root, account_identity="acct-1", mode="recover")
    try:
        raw = store.load()
    finally:
        store.close()
    owner = None
    try:
        owner = _cold_owner(root, raw, selected_policy=policy())
        state = owner.budget_state_v1()
        assert state.recovery_required and not state.admitted
        assert state.active_reservation_sum == held.active_reservation_sum
        assert state.reserved_closing_costs == held.reserved_closing_costs
        assert state.reserved_funding_costs == held.reserved_funding_costs
        assert owner.test_slot_loss_state_v1("LANE_5")["exhausted"]
        request = owner.pending_open_slot_loss_exit_v1("LANE_5")
        assert request.validate_v1(
            episode=world["episodes"]["LANE_5"],
            bound=world["bounds"]["LANE_5"],
            observed_unix=world["kwargs"]["observed_unix"] + 1,
        )
        assert all(owner.active_slot_sum_v1(f"LANE_{i}") > 0 for i in range(1, 6))
    finally:
        if owner is not None:
            owner.close()
        cleanup(driver)


def test_original_loss_close_fill_flat_reconciliation_and_no_refill_survive_cold_restart(
    tmp_path, monkeypatch
):
    from tests.ops.test_test_phase_slot_loss_budget_v1 import _install_test_path

    _install_test_path(monkeypatch, exhausted=False)
    install_policy(monkeypatch, policy())
    monkeypatch.setattr(original, "policy", policy)
    attach_funding_probe(monkeypatch, funding_seconds=7200)
    install_cost_probe(monkeypatch)
    driver = Driver(tmp_path, target="LANE_5", finish_close=True)
    original.roundtrip(
        tmp_path,
        monkeypatch,
        5,
        "LANE_5",
        False,
        expected_loss_exhausted=True,
        rotation_driver=driver,
        expected_exit_class="safety_exit",
    )
    state = driver.world["host"].owner.test_slot_loss_state_v1("LANE_5")
    assert state["exhausted"] and len(state["records"]) == 1
    assert driver.world["sessions"]["LANE_5"].position is None
    assert state["open_position_protection"]["exhaustion"]["actual_loss_allowance_exhausted"]


@pytest.mark.parametrize(
    "fault",
    [
        "missing-state",
        "missing-close-latch",
        "missing-exhaustion-latch",
        "rehashed-amount",
        "rehashed-quantity",
    ],
)
def test_semantic_cold_read_rejects_missing_or_rehashed_loss_protection(
    tmp_path, monkeypatch, fault
):
    from tests.ops.test_test_phase_slot_loss_budget_v1 import _cold_owner, _write_reviewed_state
    from src.ops.portfolio_capital_reservation_budget_v1.durable_store_v1 import (
        DurableBudgetStoreV1,
    )
    from src.ops.portfolio_capital_reservation_budget_v1.contract_v1 import (
        PortfolioCapitalBudgetError,
    )

    driver = run_open(tmp_path, monkeypatch)
    try:
        root = driver.world["host"].root / "owner"
        driver.world["host"].close()
        store = DurableBudgetStoreV1(root, account_identity="acct-1", mode="recover")
        try:
            raw = store.load()
        finally:
            store.close()
        if fault == "missing-state":
            del raw["open_slot_protection"]
        elif fault == "missing-close-latch":
            raw["open_slot_protection"]["LANE_1"]["pending_close"] = None
        elif fault == "missing-exhaustion-latch":
            raw["open_slot_protection"]["LANE_1"]["exhaustion"] = None
        else:
            proof = raw["open_slot_protection"]["LANE_1"]["latest"]
            proof[
                "remaining_allowance_before_future_costs_usdc"
                if fault == "rehashed-amount"
                else "quantity"
            ] = "999"
            proof["digest"] = cost.digest({k: v for k, v in proof.items() if k != "digest"})
        clone = tmp_path / "rehash-owner"
        _write_reviewed_state(clone, raw)
        with pytest.raises(PortfolioCapitalBudgetError, match="SEMANTIC_RESTORE_UNPROVEN"):
            _cold_owner(clone, raw, selected_policy=policy())
    finally:
        cleanup(driver)


def test_original_late_entry_budget_reader_consumes_the_slot_loss_latch(tmp_path, monkeypatch):
    from src.ops.full_core_live_path_composition_root_v1 import (
        current_productive_entry_budget_policy_v1 as entry_policy,
    )

    # Explicit simulated multi-slot limits at this reader. The operative
    # configuration's aggregate 25-USDC limit is neither replaced nor weakened.
    simulated = replace(
        entry_policy.load_entry_budget_policy_v1(), aggregate_reserved_notional_limit=Decimal(125)
    )
    monkeypatch.setattr(entry_policy, "load_entry_budget_policy_v1", lambda: simulated)
    driver = run_open(tmp_path, monkeypatch)
    try:
        owner = driver.world["host"].owner
        rid = driver.world["holds"]["LANE_1"]
        from src.ops.full_core_live_path_composition_root_v1.final_order_envelope_v1 import (
            FinalOrderEnvelopeV1,
        )

        order = FinalOrderEnvelopeV1(**owner.execution_links_v1()[rid]["envelope"])
        before = owner.budget_state_v1(), owner._store.sequence
        with pytest.raises(
            ValueError, match="CURRENT_ENTRY_BUDGET:TEST_SLOT_MARK_VALUED_LOSS_ALLOWANCE_EXHAUSTED"
        ):
            owner.inspect_current_entry_budget_policy_v1(rid, order)
        assert before == (owner.budget_state_v1(), owner._store.sequence)
    finally:
        cleanup(driver)


def test_failed_guard_persistence_fences_the_original_owner_without_releasing_holds(
    tmp_path, monkeypatch
):
    from src.ops.portfolio_capital_reservation_budget_v1.contract_v1 import (
        PortfolioCapitalBudgetError,
    )

    driver = run_open(tmp_path, monkeypatch)
    try:
        world = driver.world
        owner = world["host"].owner
        epoch = world["kwargs"]["observed_unix"] + 1
        held = owner.budget_state_v1().active_reservation_sum

        def fail(*args, **kwargs):
            raise OSError("explicit failed guard commit")

        monkeypatch.setattr(owner._store, "save", fail)
        with pytest.raises(PortfolioCapitalBudgetError, match="COMMIT_UNPROVEN_REOPEN_REQUIRED"):
            owner.observe_open_slot_loss_v1(
                slot_id="LANE_1",
                episode=world["episodes"]["LANE_1"],
                observation=observation(world, "LANE_1", epoch),
                mark_px=world["kwargs"]["mark_px"],
                observed_unix=epoch,
            )
        state = owner.budget_state_v1()
        assert state.active_reservation_sum == held
        assert not state.admitted and state.recovery_required
    finally:
        cleanup(driver)


def test_previous_policy_is_not_silently_upgraded_to_open_loss_protection():
    old = load_slot_entry_budget_v1(
        ROOT / "docs/ops/specs/BOUNDED_MULTISLOT_TEST_ENTRY_BUDGET_V5.json"
    )
    assert old.to_dict_v1()["schema"] == "entry_budget_policy.v6"
    assert "enforce_open_slot_loss_protection" not in old.to_dict_v1()
    assert policy().enforce_open_slot_loss_protection
