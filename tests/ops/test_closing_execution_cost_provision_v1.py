"""Current source-bound close-cost provision reaches the real N1 budget owner."""

from dataclasses import replace
from decimal import Decimal
import json
from pathlib import Path
import socket

import pytest

from src.ops.portfolio_capital_reservation_budget_v1.contract_v1 import (
    PortfolioCapitalReservationBudgetOwnerV1 as Owner,
    capital_context_facts_v1,
)
from src.ops.portfolio_capital_reservation_budget_v1.sizing_binding_v1 import (
    ReservationSizingBindingV1,
)
from src.ops.portfolio_capital_reservation_budget_v1.test_phase_limits_v1 import (
    load_slot_entry_budget_v1,
)
from src.ops.portfolio_capital_reservation_budget_v1 import entry_execution_cost_v1 as cost
from tests.ops._opening_execution_cost_fixture_v1 import install_cost_probe
from tests.ops._wp03_supervisor_golden_harness_v1 import _run_layered_entry_supervisor_v1

ROOT = Path(__file__).resolve().parents[2]


def policy():
    return load_slot_entry_budget_v1(
        ROOT / "docs/ops/specs/BOUNDED_MULTISLOT_TEST_ENTRY_BUDGET_V4.json"
    )


@pytest.fixture(autouse=True)
def no_network(monkeypatch):
    def denied(*args, **kwargs):
        pytest.fail("Only explicit synthetic source ports are used")

    monkeypatch.setattr(socket.socket, "connect", denied)


def install_policy(monkeypatch, selected_policy=None):
    live = []
    selected_policy = selected_policy or policy()
    original = Owner.__init__

    def create(self, **kwargs):
        kwargs["entry_budget_policy"] = selected_policy
        return original(self, **kwargs)

    monkeypatch.setattr(Owner, "__init__", create)
    from src.ops.portfolio_capital_reservation_budget_v1.host_v1 import PortfolioBudgetHostV1

    host_init = PortfolioBudgetHostV1.__init__

    def simulated_host(self, **kwargs):
        kwargs["execution_environment"] = "INTERNAL_SIMULATED_EXECUTION"
        kwargs["entry_budget_policy"] = selected_policy
        return host_init(self, **kwargs)

    monkeypatch.setattr(PortfolioBudgetHostV1, "__init__", simulated_host)
    bind = Owner.bind_execution_plan_v1

    def observe_plan(self, rid, envelope, **kwargs):
        result = bind(self, rid, envelope, **kwargs)
        live.append(
            (
                self.budget_state_v1(),
                capital_context_facts_v1(self, slot_id="LANE_1"),
                self.local_commitment_readback_v1(),
            )
        )
        return result

    monkeypatch.setattr(Owner, "bind_execution_plan_v1", observe_plan)
    return live


@pytest.mark.parametrize("short", [False, True])
def test_actual_n1_reserves_own_close_costs_in_same_original_owner(tmp_path, monkeypatch, short):
    live = install_policy(monkeypatch)
    captures, _ = install_cost_probe(monkeypatch)
    run = _run_layered_entry_supervisor_v1(tmp_path, short=short)
    kwargs, result, snapshot = captures[0]
    assert result.status == "PASS", result.reason_codes
    raw = next(iter(snapshot["state"]["sizing_bindings"].values()))
    assert raw["schema"] == "reservation_sizing_binding.v5"
    binding = ReservationSizingBindingV1.from_dict_v1(raw)
    binding.validate_v1(
        amount=binding.decision.canonical_position_sizing.resulting_notional,
        decision_id=binding.applied_input.decision_id,
    )
    receipt = binding.close_cost_binding.validate_v1(
        entry_binding=binding.entry_cost_binding,
        monetary_source=binding.monetary_source,
        applied_input=binding.applied_input,
        decision=binding.decision,
    )
    assert receipt["position_side"] == ("SHORT" if short else "LONG")
    assert receipt["closing_order_side"] == ("BUY" if short else "SELL")
    assert (
        receipt["future_execution_or_fee_guaranteed"] is False
        and receipt["funding_included"] is False
    )
    envelope = run.policy_result.orchestrator_result.cycle_records[-1].final_order_envelope
    assert (
        Decimal(envelope.quantity)
        == binding.decision.final_quantity
        == Decimal(receipt["quantity"])
    )
    source = binding.monetary_source
    ref, stop = Decimal(source.native_reference_price), Decimal(source.native_protective_stop_price)
    price = Decimal(receipt["current_close_book_vwap"])
    assert price == ref + (Decimal("0.01") if short else -Decimal("0.01"))
    expected_fee = (
        max(ref, stop, price)
        * binding.applied_input.instrument.contract_multiplier
        * binding.decision.final_quantity
        * Decimal("0.0005")
        * (binding.applied_input.reference_price / ref)
    )
    assert Decimal(receipt["fee_allowance_usdc"]) == expected_fee > 0
    state, facts, readback = live[0]
    assert state.reserved_closing_costs == Decimal(receipt["reserved_close_cost_usdc"]) > 0
    held = state.active_reservation_sum + state.reserved_opening_fees + state.reserved_closing_costs
    # Match atomic admission and its actual capital consumer: subtract the
    # aggregate obligation once, avoiding chained Decimal rounding differences.
    assert state.remaining_unreserved == state.canonical_available_capital - held
    assert (
        facts["already_committed_capital"]
        == state.active_reservation_sum + state.reserved_opening_fees + state.reserved_closing_costs
    )
    assert readback.active_commitment_sum == facts["already_committed_capital"]
    assert run.policy_result.orchestrator_result.post_count == 0


def test_legacy_cost_policy_keeps_its_exact_schema():
    old = load_slot_entry_budget_v1(
        ROOT / "docs/ops/specs/BOUNDED_MULTISLOT_TEST_ENTRY_BUDGET_V3.json"
    )
    assert old.to_dict_v1()["schema"] == "entry_budget_policy.v4"
    assert "require_closing_execution_costs" not in old.to_dict_v1()
    assert policy().require_closing_execution_costs


@pytest.mark.parametrize("short", [False, True])
def test_unexecutable_opposite_book_denies_real_entry_without_partial_hold(
    tmp_path, monkeypatch, short
):
    from tests.ops import _opening_execution_cost_fixture_v1 as fixture

    install_policy(monkeypatch)
    attach = fixture.attach_costs

    def insufficient_close(kwargs, **options):
        observed = attach(kwargs, **options)
        sources = json.loads(observed.sources_json)
        book = sources["book"]["payload"]
        book["data"][0]["asks" if short else "bids"][0][1] = "0.00000001"
        sources["book"]["body_sha256"] = cost.digest(book)
        observed = replace(observed, sources_json=cost.canonical(sources))
        kwargs["injected"] = replace(kwargs["injected"], opening_cost_observation=observed)
        return observed

    monkeypatch.setattr(fixture, "attach_costs", insufficient_close)
    captures, _ = install_cost_probe(monkeypatch)
    run = _run_layered_entry_supervisor_v1(tmp_path, short=short)
    assert "CLOSE_COST_NOT_ADMITTED_NO_RESERVATION" in captures[0][1].reason_codes
    assert not captures[0][2]["state"]["reservations"]
    assert run.policy_result.orchestrator_result.cycle_records[-1].final_order_envelope is None


def test_close_costs_change_actual_slot_loss_admission_without_changing_quantity(
    tmp_path, monkeypatch
):
    from src.ops.full_core_live_path_composition_root_v1 import (
        current_productive_enter_live_29p_join_v1 as join,
    )

    admit = join.admit_sized_slot_reservation_v1
    sized = []

    def observe_admit(*args, **kwargs):
        result = admit(*args, **kwargs)
        sized.append(result)
        return result

    with monkeypatch.context() as patch:
        patch.setattr(join, "admit_sized_slot_reservation_v1", observe_admit)
        install_policy(patch, replace(policy(), require_closing_execution_costs=False, revision=3))
        captures, _ = install_cost_probe(patch, taker="-0.7")
        _run_layered_entry_supervisor_v1(tmp_path / "old", short=False)
        assert captures[0][1].status == "PASS"
        old_quantity = sized[-1].sizing_decision.final_quantity
    with monkeypatch.context() as patch:
        patch.setattr(join, "admit_sized_slot_reservation_v1", observe_admit)
        install_policy(patch)
        captures, _ = install_cost_probe(patch, taker="-0.7")
        run = _run_layered_entry_supervisor_v1(tmp_path / "new", short=False)
        assert "TEST_SLOT_REMAINING_LOSS_BUDGET_EXCEEDED" in captures[0][1].reason_codes
        assert sized[-1].sizing_decision.final_quantity == old_quantity
        assert not captures[0][2]["state"]["reservations"]
        assert run.policy_result.orchestrator_result.cycle_records[-1].final_order_envelope is None


@pytest.mark.parametrize(
    "field,value",
    [
        ("reserved_close_cost_usdc", "0"),
        ("slot_id", "LANE_2"),
        ("quantity", "999"),
        ("closing_order_side", "BUY"),
    ],
)
def test_rebound_close_receipt_cannot_change_original_reserve(tmp_path, monkeypatch, field, value):
    install_policy(monkeypatch)
    captures, _ = install_cost_probe(monkeypatch)
    _run_layered_entry_supervisor_v1(tmp_path, short=False)
    raw = next(iter(captures[0][2]["state"]["sizing_bindings"].values()))
    receipt = raw["close_cost_binding"]["receipt"]
    receipt[field] = value
    receipt["digest"] = cost.digest({k: v for k, v in receipt.items() if k != "digest"})
    binding = ReservationSizingBindingV1.from_dict_v1(raw)
    with pytest.raises(ValueError, match="CLOSE_COST_SOURCE_OR_PROVISION_MISMATCH"):
        binding.validate_v1(
            amount=binding.decision.canonical_position_sizing.resulting_notional,
            decision_id=binding.applied_input.decision_id,
        )


@pytest.mark.parametrize("replacement", [False, True], ids=["keep", "replace"])
def test_real_five_slot_close_and_cold_read_keep_foreign_close_cost_reserves(
    tmp_path, monkeypatch, replacement
):
    from tests.ops import test_test_phase_slot_loss_budget_v1 as loss
    from tests.ops import test_bounded_slot_connected_roundtrip_v1 as connected
    from src.ops.portfolio_capital_reservation_budget_v1.durable_store_v1 import (
        DurableBudgetStoreV1,
    )
    from src.ops.single_selected_future_runtime_binding_v1.models_v1 import BoundInstrumentV1

    worlds = loss._install_test_path(monkeypatch, exhausted=True)
    monkeypatch.setattr(connected, "policy", policy)
    install_cost_probe(monkeypatch)
    connected.roundtrip(
        tmp_path, monkeypatch, 5, "LANE_5", replacement, expected_loss_exhausted=True
    )
    root = worlds[0]["host"].root / "owner"
    store = DurableBudgetStoreV1(root, account_identity="acct-1", mode="recover")
    try:
        raw = store.load()
    finally:
        store.close()
    held = Decimal(0)
    for reservation in raw["reservations"]:
        bound = ReservationSizingBindingV1.from_dict_v1(
            raw["sizing_bindings"][reservation["reservation_id"]]
        )
        value = cost.reserved_closing_cost_v1(bound)
        assert value > 0
        if reservation["slot_id"] == "LANE_5":
            assert reservation["state"] == "RELEASED"
        else:
            assert reservation["state"] == "COMMITTED"
            held += value
    bindings = {
        lane: BoundInstrumentV1(**value["bound"]) for lane, value in raw["lane_bindings"].items()
    }
    owner = Owner(
        durable_root=root,
        durable_account_identity="acct-1",
        durable_mode="recover",
        durable_lane_bindings=bindings,
        entry_budget_policy=policy(),
    )
    try:
        state = owner.budget_state_v1()
        assert state.recovery_required and not state.admitted
        assert state.reserved_closing_costs == held > 0
        assert owner.test_slot_loss_state_v1("LANE_5")["exhausted"]
        assert (
            owner.local_commitment_readback_v1().active_commitment_sum
            == state.active_reservation_sum + state.reserved_opening_fees + held
        )
    finally:
        owner.close()
