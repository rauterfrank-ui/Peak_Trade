"""Fresh cost facts reach the existing original per-slot safety consumer."""

from dataclasses import replace
from decimal import Decimal
import json
from pathlib import Path

import pytest

from src.ops.portfolio_capital_reservation_budget_v1 import entry_execution_cost_v1 as cost
from src.ops.portfolio_capital_reservation_budget_v1.test_phase_limits_v1 import (
    load_slot_entry_budget_v1,
    parse_slot_entry_budget_v1,
)
from tests.ops import test_open_slot_loss_protection_v1 as connected
from tests.ops.test_n1_original_reservation_host_handoff_v1 import (
    synthetic_ports_and_isolation as synthetic_ports_and_isolation,
)

ROOT = Path(__file__).resolve().parents[2]


def policy():
    return load_slot_entry_budget_v1(
        ROOT / "docs/ops/specs/BOUNDED_MULTISLOT_TEST_ENTRY_BUDGET_V7.json"
    )


def current_sources(
    owner, rid, value, *, fee="0.0005", ceiling="0.01", floor="-0.02", spread="0.001", fault=None
):
    if fault == "missing":
        return value
    sizing = owner._sizing_bindings[rid]
    sources = json.loads(json.loads(sizing.entry_cost_binding.observation_json)["sources_json"])
    sources["funding"] = json.loads(
        json.loads(sizing.funding_cost_binding.observation_json)["source_json"]
    )
    mark_source = json.loads(value.mark_source_json)
    ms = mark_source["payload"]["data"][0]["ts"]
    for name, source in sources.items():
        source.update(
            acquired_at_utc=value.valuation_epoch,
            pretrade_decision_id=mark_source["pretrade_decision_id"],
        )
        for row in source["payload"]["data"]:
            if "ts" in row:
                row["ts"] = ms
        if name == "fees":
            for group in source["payload"]["data"][0]["feeGroup"]:
                group.update(maker="0.0001", taker=str(-Decimal(fee)))
    price = Decimal(mark_source["payload"]["data"][0]["markPx"])
    quantity = sizing.decision.final_quantity
    book = sources["book"]["payload"]["data"][0]
    book.update(
        bids=[[str(price * (1 - Decimal(spread))), str(quantity)]],
        asks=[[str(price * (1 + Decimal(spread))), str(quantity)]],
    )
    row = sources["funding"]["payload"]["data"][0]
    row.update(minFundingRate=floor, maxFundingRate=ceiling, fundingRate="0")
    if fault == "foreign-account":
        sources["account"]["payload"]["data"][0]["uid"] = "other-account"
    elif fault == "stale-book":
        book["ts"] = str(int(ms) - 10000)
    elif fault == "future-book":
        book["ts"] = str(int(ms) + 1000)
    elif fault == "foreign-context":
        sources["fees"]["pretrade_decision_id"] = "other-slot-cycle"
    elif fault == "foreign-fee-group":
        sources["fees"]["payload"]["data"][0]["feeGroup"][0]["groupId"] = "foreign"
    elif fault == "missing-fees":
        del sources["fees"]
    elif fault == "insufficient-depth":
        book["bids"][0][1] = "0.0001"
    elif fault == "processing":
        row["settState"] = "processing"
    elif fault == "different-settlement":
        row["fundingTime"] = str(int(row["fundingTime"]) + 1000)
    elif fault == "public-with-auth":
        sources["funding"]["auth_header_sent"] = True
    elif fault == "reused-fees":
        sources["fees"]["historical_reuse"] = True
    elif fault == "future-acquisition":
        sources["fees"]["acquired_at_utc"] = connected.original.utc(int(ms) / 1000 + 1)
    for source in sources.values():
        source["body_sha256"] = cost.digest(source["payload"])
    return replace(value, cost_sources_json=cost.canonical(sources))


def run_current(
    tmp_path, monkeypatch, *, target="LANE_1", count=2, remaining=Decimal(1), **options
):
    original_observation = connected.observation

    def supplied(world, lane, epoch, **kwargs):
        value = original_observation(world, lane, epoch, **kwargs)
        return current_sources(
            world["host"].owner, world["holds"][lane], value, **(options if lane == target else {})
        )

    monkeypatch.setattr(connected, "policy", policy)
    monkeypatch.setattr(connected, "observation", supplied)
    return connected.run_open(
        tmp_path, monkeypatch, count=count, target=target, remaining=remaining
    )


def latest(driver, lane="LANE_1"):
    return driver.world["host"].owner.test_slot_loss_state_v1(lane)["open_position_protection"][
        "latest"
    ]


@pytest.mark.parametrize("count,target", [(2, "LANE_1"), (5, "LANE_5")])
@pytest.mark.parametrize("change", [dict(fee="0.1"), dict(ceiling="0.2"), dict(spread="0.1")])
def test_higher_current_cost_reaches_only_its_original_n1_safety_exit(
    tmp_path, monkeypatch, count, target, change
):
    driver = run_current(tmp_path, monkeypatch, count=count, target=target, **change)
    try:
        proof = latest(driver, target)
        receipt = proof["current_cost_provision"]
        assert proof["current_cost_status"] == "OBSERVED_PROTECTION_ONLY", proof[
            "current_cost_reasons"
        ]
        assert proof["reason"] == "TEST_SLOT_CURRENT_COST_PROVISIONS_UNCOVERED"
        assert not proof["actual_loss_allowance_exhausted"]
        assert Decimal(proof["remaining_allowance_before_future_costs_usdc"]) == 1
        assert Decimal(receipt["total_future_cost_provision_usdc"]) > 1
        assert Decimal(receipt["quantity"]) == driver.world["sessions"][target].position.qty
        result = driver.results[target]
        assert (
            result.s7_invocation.cycle_result.replay.intermediate.entry_exit_decision.exit_class.value
            == "safety_exit"
        )
        assert result.position_management_close_intent is not None
        assert all(
            v.position_management_close_intent is None
            for lane, v in driver.results.items()
            if lane != target
        )
        assert driver.before == driver.after
        assert all(v.governed_cycle_result.post_count == 0 for v in driver.results.values())
    finally:
        connected.cleanup(driver)


@pytest.mark.parametrize(
    "fault",
    [
        "missing",
        "foreign-account",
        "stale-book",
        "future-book",
        "foreign-context",
        "foreign-fee-group",
        "missing-fees",
        "insufficient-depth",
        "processing",
        "different-settlement",
        "public-with-auth",
        "reused-fees",
        "future-acquisition",
    ],
)
def test_unproven_current_cost_keeps_original_protection_and_all_holds(
    tmp_path, monkeypatch, fault
):
    driver = run_current(tmp_path, monkeypatch, fault=fault)
    try:
        proof = latest(driver)
        assert proof["current_cost_status"] == "UNPROVEN_ORIGINAL_PROTECTION_RETAINED"
        assert proof["current_cost_provision"] is None and proof["current_cost_reasons"]
        assert not proof["close_required"] and not proof["actual_loss_allowance_exhausted"]
        assert driver.results["LANE_1"].position_management_close_intent is None
        assert driver.before == driver.after
    finally:
        connected.cleanup(driver)


def test_missing_cost_does_not_mask_observed_exhaustion(tmp_path, monkeypatch):
    driver = run_current(tmp_path, monkeypatch, remaining=Decimal(0), fault="missing")
    try:
        proof = latest(driver)
        assert proof["actual_loss_allowance_exhausted"] and proof["close_required"]
        assert driver.results["LANE_1"].position_management_close_intent is not None
        assert proof["current_cost_status"] == "UNPROVEN_ORIGINAL_PROTECTION_RETAINED"
        assert driver.before == driver.after
    finally:
        connected.cleanup(driver)


def test_current_observation_replay_is_idempotent_and_started_close_stays_bound(
    tmp_path, monkeypatch
):
    driver = run_current(tmp_path, monkeypatch, fee="0.1")
    try:
        world = driver.world
        owner = world["host"].owner
        lane = "LANE_1"
        proof = latest(driver)
        original_request = owner.pending_open_slot_loss_exit_v1(lane)
        original_sequence = owner._store.sequence
        value = cost.OpenSlotLossObservationV1.from_dict_v1(proof["observation"])
        request = owner.observe_open_slot_loss_v1(
            slot_id=lane,
            episode=world["episodes"][lane],
            observation=value,
            mark_px=world["kwargs"]["mark_px"],
            observed_unix=world["kwargs"]["observed_unix"],
        )
        assert (
            request.proof_digest == original_request.proof_digest
            and owner._store.sequence == original_sequence
        )
        epoch = world["kwargs"]["observed_unix"] + 1
        value = connected.observation(world, lane, epoch)
        value = current_sources(
            owner, world["holds"][lane], value, fee="0", floor="0", ceiling="0", spread="0.00001"
        )
        request = owner.observe_open_slot_loss_v1(
            slot_id=lane,
            episode=world["episodes"][lane],
            observation=value,
            mark_px=world["kwargs"]["mark_px"],
            observed_unix=epoch,
        )
        assert not latest(driver)["close_required"]
        assert latest(driver)["current_cost_status"] == "OBSERVED_PROTECTION_ONLY"
        assert request.proof_digest == original_request.proof_digest
        assert driver.before == owner.budget_state_v1()
    finally:
        connected.cleanup(driver)


def test_current_cost_exit_reaches_original_close_fill_flat_and_reconciliation(
    tmp_path, monkeypatch
):
    from tests.ops.test_closing_execution_cost_provision_v1 import install_policy
    from tests.ops.test_next_funding_cost_provision_v1 import attach_funding_probe
    from tests.ops._opening_execution_cost_fixture_v1 import install_cost_probe

    install_policy(monkeypatch, policy())
    monkeypatch.setattr(connected.original, "policy", policy)
    attach_funding_probe(monkeypatch, funding_seconds=7200)
    install_cost_probe(monkeypatch)
    original_observation = connected.observation

    def supplied(world, lane, epoch, **kwargs):
        value = original_observation(world, lane, epoch, **kwargs)
        return current_sources(
            world["host"].owner,
            world["holds"][lane],
            value,
            fee="0.1" if lane == "LANE_5" else "0.0005",
        )

    monkeypatch.setattr(connected, "observation", supplied)
    driver = connected.Driver(tmp_path, target="LANE_5", remaining=Decimal(1), finish_close=True)
    try:
        world = connected.original.connected_close(
            tmp_path,
            monkeypatch,
            5,
            "LANE_5",
            rotation_driver=driver,
            expected_exit_class="safety_exit",
        )
        proof = latest(driver, "LANE_5")
        assert proof["reason"] == "TEST_SLOT_CURRENT_COST_PROVISIONS_UNCOVERED"
        assert world["sessions"]["LANE_5"].position is None
        assert len(world["fills"]["LANE_5"]) == 2
        assert all(
            s.position is not None for lane, s in world["sessions"].items() if lane != "LANE_5"
        )
        # Flat and a fresh recovery do not release another owner's hold. The
        # original economic-close/capital-release transaction remains required.
        assert all(world["host"].owner.active_slot_sum_v1(f"LANE_{i}") > 0 for i in range(1, 6))
        assert world["host"].owner.budget_state_v1().admitted
    finally:
        if driver.world:
            connected.cleanup(driver)


def test_new_policy_is_explicit_and_old_observation_encoding_is_preserved():
    old = load_slot_entry_budget_v1(
        ROOT / "docs/ops/specs/BOUNDED_MULTISLOT_TEST_ENTRY_BUDGET_V6.json"
    )
    assert (
        not old.refresh_open_slot_cost_protection
        and old.to_dict_v1()["schema"] == "entry_budget_policy.v7"
    )
    assert policy().refresh_open_slot_cost_protection
    assert parse_slot_entry_budget_v1(policy().to_dict_v1()) == policy()
    raw = policy().to_dict_v1()
    raw["enforce_open_slot_loss_protection"] = False
    with pytest.raises(ValueError):
        parse_slot_entry_budget_v1(raw)
    legacy = cost.OpenSlotLossObservationV1("identity", "initial", "current", "mark", "epoch")
    assert "cost_sources_json" not in legacy.to_dict_v1()
    assert cost.OpenSlotLossObservationV1.from_dict_v1(legacy.to_dict_v1()) == legacy


@pytest.mark.parametrize("change", [dict(fee="0.1"), dict(floor="-0.2")])
def test_natural_short_uses_ask_close_and_lower_funding_bound_at_original_s7(
    tmp_path, monkeypatch, change
):
    from tests.ops import test_open_slot_loss_short_protection_v1 as short

    original_observation = short.observation

    def supplied(world, lane, epoch, **kwargs):
        value = original_observation(world, lane, epoch, **kwargs)
        return current_sources(world["host"].owner, world["holds"][lane], value, **change)

    monkeypatch.setattr(short, "policy", policy)
    monkeypatch.setattr(short, "observation", supplied)
    proof = short._run_original_short_loss_probe(tmp_path, monkeypatch, remaining=Decimal(1))[0]
    assert proof["current_cost_status"] == "OBSERVED_PROTECTION_ONLY", proof["current_cost_reasons"]
    assert proof["reason"] == "TEST_SLOT_CURRENT_COST_PROVISIONS_UNCOVERED"
    assert not proof["actual_loss_allowance_exhausted"]
    receipt = proof["current_cost_provision"]
    assert receipt["position_side"] == "SHORT" and receipt["closing_order_side"] == "BUY"
    assert Decimal(receipt["current_close_book_vwap"]) > Decimal(receipt["native_mark_price"])
    assert Decimal(receipt["adverse_funding_rate"]) == -Decimal(change.get("floor", "-0.02"))


@pytest.mark.parametrize("tamper", [None, "cost", "source"])
def test_cost_trigger_and_five_holds_survive_cold_read_or_reject_tampering(
    tmp_path, monkeypatch, tamper
):
    from tests.ops.test_test_phase_slot_loss_budget_v1 import _cold_owner, _write_reviewed_state
    from src.ops.portfolio_capital_reservation_budget_v1.durable_store_v1 import (
        DurableBudgetStoreV1,
    )
    from src.ops.portfolio_capital_reservation_budget_v1.contract_v1 import (
        PortfolioCapitalBudgetError,
    )

    driver = run_current(tmp_path, monkeypatch, count=5, target="LANE_5", fee="0.1")
    world = driver.world
    root = world["host"].root / "owner"
    world["host"].close()
    store = DurableBudgetStoreV1(root, account_identity="acct-1", mode="recover")
    try:
        raw = store.load()
    finally:
        store.close()
    owner = None
    try:
        if tamper:
            proof = raw["open_slot_protection"]["LANE_5"]["latest"]
            if tamper == "cost":
                proof["current_cost_provision"]["total_future_cost_provision_usdc"] = "0"
                receipt = proof["current_cost_provision"]
                receipt["digest"] = cost.digest({k: v for k, v in receipt.items() if k != "digest"})
            else:
                sources = json.loads(proof["observation"]["cost_sources_json"])
                sources["fees"]["payload"]["data"][0]["feeGroup"][0]["taker"] = "-0.9"
                proof["observation"]["cost_sources_json"] = cost.canonical(sources)
            proof["digest"] = cost.digest({k: v for k, v in proof.items() if k != "digest"})
            clone = tmp_path / "tampered-cost-owner"
            _write_reviewed_state(clone, raw)
            with pytest.raises(PortfolioCapitalBudgetError, match="SEMANTIC_RESTORE_UNPROVEN"):
                _cold_owner(clone, raw, selected_policy=policy())
        else:
            owner = _cold_owner(root, raw, selected_policy=policy())
            assert not owner.budget_state_v1().admitted
            assert all(owner.active_slot_sum_v1(f"LANE_{i}") > 0 for i in range(1, 6))
            request = owner.pending_open_slot_loss_exit_v1("LANE_5")
            assert request.validate_v1(
                episode=world["episodes"]["LANE_5"],
                bound=world["bounds"]["LANE_5"],
                observed_unix=world["kwargs"]["observed_unix"] + 1,
            )
            state = owner.budget_state_v1()
            assert state.reserved_funding_costs == driver.after.reserved_funding_costs
            assert state.reserved_closing_costs == driver.after.reserved_closing_costs
    finally:
        if owner:
            owner.close()
        connected.cleanup(driver)
