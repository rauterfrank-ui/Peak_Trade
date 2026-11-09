"""Observed fees/book costs reach actual N1 reservation, envelope and readback."""

from dataclasses import replace
from datetime import datetime, timedelta
from decimal import Decimal
import json
from pathlib import Path
import socket

import pytest

from src.ops.portfolio_capital_reservation_budget_v1.sizing_binding_v1 import (
    ReservationSizingBindingV1,
)
from src.ops.portfolio_capital_reservation_budget_v1.test_phase_limits_v1 import (
    load_slot_entry_budget_v1,
)
from src.ops.portfolio_capital_reservation_budget_v1 import entry_execution_cost_v1 as cost
from tests.ops._opening_execution_cost_fixture_v1 import install_cost_probe
from tests.ops._wp03_supervisor_golden_harness_v1 import _run_layered_entry_supervisor_v1


@pytest.fixture(autouse=True)
def forbid_network(monkeypatch):
    def forbidden(*args, **kwargs):
        pytest.fail("Opening cost tests use explicit synthetic ports only")

    monkeypatch.setattr(socket.socket, "connect", forbidden)


@pytest.mark.parametrize("short", [False, True])
def test_actual_n1_retains_original_quantity_and_reserves_observed_opening_fee(
    tmp_path, monkeypatch, short
):
    captures, _ = install_cost_probe(monkeypatch)
    run = _run_layered_entry_supervisor_v1(tmp_path, short=short)
    sequence = run.policy_result.orchestrator_result
    envelope = sequence.cycle_records[-1].final_order_envelope
    assert envelope is not None and len(captures) == 1
    kwargs, result, snapshot = captures[0]
    assert result.status == "PASS", result.reason_codes
    raw = next(iter(snapshot["state"]["sizing_bindings"].values()))
    binding = ReservationSizingBindingV1.from_dict_v1(raw)
    assert raw["schema"] == "reservation_sizing_binding.v4"
    receipt = binding.entry_cost_binding.validate_v1(
        monetary_source=binding.monetary_source,
        applied_input=binding.applied_input,
        decision=binding.decision,
    )
    qty = Decimal(envelope.quantity)
    price = Decimal(receipt["book_vwap"])
    multiplier = binding.applied_input.instrument.contract_multiplier
    reference = Decimal(binding.monetary_source.native_reference_price)
    fx = binding.applied_input.reference_price / reference
    expected_fee = price * qty * multiplier * Decimal("0.0005") * fx
    assert Decimal(receipt["fee_usdc"]) == expected_fee > 0
    assert Decimal(receipt["adverse_entry_cost_usdc"]) == Decimal("0.01") * qty * multiplier * fx
    assert receipt["quantity"] == str(binding.decision.final_quantity)
    assert qty == binding.decision.final_quantity
    assert envelope.side == ("sell" if short else "buy")
    assert receipt["future_close_fees_and_funding"] == "NOT_INCLUDED"
    owner = kwargs["portfolio_budget_owner"]
    state = owner.budget_state_v1()
    assert state.reserved_opening_fees == expected_fee
    assert (
        state.active_reservation_sum
        == binding.decision.canonical_position_sizing.resulting_notional
    )
    assert sequence.post_count == 0 and not sequence.permit_created


@pytest.mark.parametrize(
    "fault",
    [
        "missing-book",
        "wrong-group",
        "top-level-fees",
        "wrong-family",
        "wrong-account",
        "no-auth",
        "reused-get",
        "foreign-acquisition",
        "future-book",
        "stale-book",
        "insufficient-depth",
        "crossed-book",
    ],
)
def test_bad_cost_sources_deny_actual_n1_without_any_hold(tmp_path, monkeypatch, fault):
    captures, _ = install_cost_probe(monkeypatch, fault=fault)
    run = _run_layered_entry_supervisor_v1(tmp_path, short=False)
    kwargs, result, snapshot = captures[0]
    assert result.status != "PASS"
    assert "ENTRY_COST_NOT_ADMITTED_NO_RESERVATION" in result.reason_codes
    assert snapshot["state"]["reservations"] == []
    assert not run.policy_result.orchestrator_result.cycle_records[-1].final_order_envelope


def test_fee_cost_changes_real_admission_and_rebate_does_not_mint_capital(tmp_path, monkeypatch):
    with monkeypatch.context() as patch:
        captures, _ = install_cost_probe(patch, taker="-2")
        run = _run_layered_entry_supervisor_v1(tmp_path / "expensive", short=False)
        assert "ENTRY_COST_CAPITAL_WITH_FEES_EXCEEDED" in captures[0][1].reason_codes
        assert captures[0][2]["state"]["reservations"] == []
        assert not run.policy_result.orchestrator_result.cycle_records[-1].final_order_envelope
    with monkeypatch.context() as patch:
        captures, _ = install_cost_probe(patch, taker="0.0003")
        run = _run_layered_entry_supervisor_v1(tmp_path / "rebate", short=False)
        binding = ReservationSizingBindingV1.from_dict_v1(
            next(iter(captures[0][2]["state"]["sizing_bindings"].values()))
        )
        receipt = json.loads(binding.entry_cost_binding.receipt_json)
        assert receipt["charged_rate"] == "0" and Decimal(receipt["fee_usdc"]) == 0
        assert (
            run.policy_result.orchestrator_result.cycle_records[-1].final_order_envelope is not None
        )


def test_explicit_policy_requires_cost_sources_but_old_policy_is_unchanged():
    root = Path(__file__).resolve().parents[2] / "docs/ops/specs"
    new = load_slot_entry_budget_v1(root / "BOUNDED_MULTISLOT_TEST_ENTRY_BUDGET_V3.json")
    old = load_slot_entry_budget_v1(root / "BOUNDED_MULTISLOT_TEST_ENTRY_BUDGET_V2.json")
    assert new.require_opening_execution_costs and new.per_slot_test_loss_limit == Decimal(25)
    assert old.to_dict_v1()["schema"] == "entry_budget_policy.v3"
    assert "require_opening_execution_costs" not in old.to_dict_v1()
    assert not old.require_opening_execution_costs


def test_real_financial_replay_preserves_costs_and_late_consumer_rejects_expiry(
    tmp_path, monkeypatch
):
    from src.ops.full_core_live_path_composition_root_v1 import (
        current_productive_enter_live_29p_join_v1 as join,
    )
    from src.ops.portfolio_capital_reservation_budget_v1.contract_v1 import (
        PortfolioCapitalReservationBudgetOwnerV1 as Owner,
    )

    captures, clock = install_cost_probe(monkeypatch)
    admit = join.admit_sized_slot_reservation_v1
    bind = Owner.bind_execution_plan_v1
    proof = []

    def inspect_admit(owner, **kwargs):
        result = admit(owner, **kwargs)
        if result.reservation is not None:
            rid = str(result.reservation.reservation_id)
            before = owner._store.sequence
            replay = owner.replay_sized_reservation_v1(
                rid,
                request=kwargs["sizing_input"],
                opening_cost_observation=kwargs["opening_cost_observation"],
            )
            assert replay.disposition.value == "IDEMPOTENT_REPLAY"
            for observation in (
                None,
                replace(kwargs["opening_cost_observation"], cycle_id="foreign-cycle"),
            ):
                blocked = owner.replay_sized_reservation_v1(
                    rid, request=kwargs["sizing_input"], opening_cost_observation=observation
                )
                assert "ENTRY_COST_REPLAY_CONTEXT_CHANGED_OR_MISSING" in blocked.reason_codes
            assert owner._store.sequence == before
            proof.append("original financial replay")
        return result

    def inspect_plan(owner, rid, envelope, **kwargs):
        result = bind(owner, rid, envelope, **kwargs)
        state = owner.budget_state_v1()
        owner.inspect_current_entry_budget_policy_v1(rid, envelope)
        original_clock = clock[0]
        clock[0] = (
            datetime.fromisoformat(original_clock.replace("Z", "+00:00")) + timedelta(seconds=61)
        ).isoformat()
        try:
            with pytest.raises(ValueError, match="ACQUISITION_STALE"):
                owner.inspect_current_entry_budget_policy_v1(rid, envelope)
        finally:
            clock[0] = original_clock
        assert owner.budget_state_v1() == state
        proof.append("late current financial consumer")
        return result

    monkeypatch.setattr(join, "admit_sized_slot_reservation_v1", inspect_admit)
    monkeypatch.setattr(Owner, "bind_execution_plan_v1", inspect_plan)
    run = _run_layered_entry_supervisor_v1(tmp_path, short=False)
    assert run.policy_result.orchestrator_result.cycle_records[-1].final_order_envelope is not None
    assert proof == ["original financial replay", "late current financial consumer"]


@pytest.mark.parametrize("replacement", [False, True], ids=["keep", "replace"])
def test_five_slot_original_close_and_cold_read_preserve_foreign_fee_holds(
    tmp_path, monkeypatch, replacement
):
    from tests.ops import test_test_phase_slot_loss_budget_v1 as loss
    from tests.ops import test_bounded_slot_connected_roundtrip_v1 as original
    from src.ops.portfolio_capital_reservation_budget_v1.durable_store_v1 import (
        DurableBudgetStoreV1,
    )

    worlds = loss._install_test_path(monkeypatch, exhausted=True)
    root = Path(__file__).resolve().parents[2] / "docs/ops/specs"
    monkeypatch.setattr(
        original,
        "policy",
        lambda: load_slot_entry_budget_v1(root / "BOUNDED_MULTISLOT_TEST_ENTRY_BUDGET_V3.json"),
    )
    install_cost_probe(monkeypatch)
    original.roundtrip(
        tmp_path, monkeypatch, 5, "LANE_5", replacement, expected_loss_exhausted=True
    )
    store = DurableBudgetStoreV1(
        worlds[0]["host"].root / "owner", account_identity="acct-1", mode="recover"
    )
    try:
        raw = store.load()
    finally:
        store.close()
    assert raw["entry_budget_policy"]["require_opening_execution_costs"]
    held_fees = []
    for row in raw["reservations"]:
        binding = ReservationSizingBindingV1.from_dict_v1(
            raw["sizing_bindings"][row["reservation_id"]]
        )
        if row["slot_id"] != "LANE_5":
            assert row["state"] == "COMMITTED"
            held_fees.append(cost.reserved_opening_fee_v1(binding))
        else:
            assert row["state"] == "RELEASED"
    assert len(held_fees) == 4 and all(fee > 0 for fee in held_fees)
    assert raw["test_slot_economics"]["LANE_5"]["exhausted"]
