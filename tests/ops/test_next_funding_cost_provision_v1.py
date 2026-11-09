"""An independent current funding source reaches the real original N1 budget."""

from dataclasses import replace
from datetime import datetime, timedelta
from decimal import Decimal
import json
from pathlib import Path

import pytest

from src.ops.portfolio_capital_reservation_budget_v1 import entry_execution_cost_v1 as cost
from src.ops.portfolio_capital_reservation_budget_v1.sizing_binding_v1 import (
    ReservationSizingBindingV1,
)
from src.ops.portfolio_capital_reservation_budget_v1.test_phase_limits_v1 import (
    load_slot_entry_budget_v1,
)
from tests.ops._wp03_supervisor_golden_harness_v1 import _run_layered_entry_supervisor_v1
from tests.ops._opening_execution_cost_fixture_v1 import install_cost_probe
from tests.ops.test_closing_execution_cost_provision_v1 import (
    install_policy,
    no_network as no_network,
)

ROOT = Path(__file__).resolve().parents[2]


def policy():
    return load_slot_entry_budget_v1(
        ROOT / "docs/ops/specs/BOUNDED_MULTISLOT_TEST_ENTRY_BUDGET_V5.json"
    )


def attach_funding_probe(
    monkeypatch,
    *,
    fault=None,
    ceiling="0.01",
    floor="-0.02",
    predicted="0.0001",
    funding_seconds=3600,
):
    from tests.ops import _opening_execution_cost_fixture_v1 as fixture

    attach = fixture.attach_costs

    def funding(kwargs, **options):
        observed = attach(kwargs, **options)
        if fault == "missing":
            return observed
        now = datetime.fromisoformat(observed.evaluated_at_utc.replace("Z", "+00:00"))
        native = kwargs["bound_instrument"].venue_native_id
        kind = next(
            r for r in kwargs["injected"].instruments_payload["data"] if r["instId"] == native
        )["instType"]
        ms = int(now.timestamp() * 1000)
        row = dict(
            instId=native,
            instType=kind,
            method="current_period",
            settState="settled",
            ts=str(ms),
            fundingRate=predicted,
            minFundingRate=floor,
            maxFundingRate=ceiling,
            fundingTime=str(ms + funding_seconds * 1000),
            nextFundingTime=str(ms + (funding_seconds + 3600) * 1000),
        )
        if fault == "foreign-instrument":
            row["instId"] = "FOREIGN-USDT-SWAP"
        elif fault == "processing":
            row["settState"] = "processing"
        elif fault == "unsupported-method":
            row["method"] = "next_period"
        elif fault == "missing-limit":
            row.pop("maxFundingRate")
        elif fault == "rate-outside-limits":
            row["fundingRate"] = "999"
        elif fault == "future-ts":
            row["ts"] = str(ms + 1000)
        elif fault == "expired-settlement":
            row["fundingTime"] = str(ms)
        elif fault == "invalid-next-time":
            row["nextFundingTime"] = row["fundingTime"]
        raw = json.loads(observed.sources_json)["book"]
        raw.update(
            endpoint="/api/v5/public/funding-rate?instId=" + native,
            payload=dict(code="0", data=[row]),
            auth_header_sent=False,
            body_sha256=cost.digest(row),
        )
        if fault == "foreign-acquisition":
            raw["pretrade_decision_id"] = "foreign"
        elif fault == "reused":
            raw["historical_reuse"] = True
        source = cost.FreshPretradeGetTransportResultV1(**raw)
        observation = cost.FundingCostObservationV1.capture_v1(
            bound_instrument=kwargs["bound_instrument"],
            decision_epoch=observed.decision_epoch,
            cycle_id=observed.cycle_id,
            source=source,
            evaluated_at_utc=observed.evaluated_at_utc,
        )
        kwargs["injected"] = replace(kwargs["injected"], funding_cost_observation=observation)
        return observed

    monkeypatch.setattr(fixture, "attach_costs", funding)


@pytest.mark.parametrize("short", [False, True])
def test_original_n1_keeps_side_aware_funding_allowance_and_original_quantity(
    tmp_path, monkeypatch, short
):
    live = install_policy(monkeypatch, policy())
    attach_funding_probe(monkeypatch)
    captures, _ = install_cost_probe(monkeypatch)
    run = _run_layered_entry_supervisor_v1(tmp_path, short=short)
    kwargs, result, snapshot = captures[0]
    assert result.status == "PASS", result.reason_codes
    raw = next(iter(snapshot["state"]["sizing_bindings"].values()))
    assert raw["schema"] == "reservation_sizing_binding.v6"
    binding = ReservationSizingBindingV1.from_dict_v1(raw)
    receipt = binding.funding_cost_binding.validate_v1(
        entry_binding=binding.entry_cost_binding,
        close_binding=binding.close_cost_binding,
        monetary_source=binding.monetary_source,
        applied_input=binding.applied_input,
        decision=binding.decision,
    )
    rate = Decimal("0.02") if short else Decimal("0.01")
    assert (
        Decimal(receipt["funding_allowance_usdc"])
        == Decimal(receipt["exposure_basis_usdc"]) * rate
        > 0
    )
    assert receipt["adverse_rate_allowance"] == str(rate)
    assert (
        receipt["actual_funding_payment"] is False
        and receipt["future_credit_funds_reservation"] is False
    )
    envelope = run.policy_result.orchestrator_result.cycle_records[-1].final_order_envelope
    assert (
        Decimal(envelope.quantity)
        == binding.decision.final_quantity
        == Decimal(receipt["quantity"])
    )
    state, facts, readback = live[0]
    assert state.reserved_funding_costs == Decimal(receipt["funding_allowance_usdc"])
    held = (
        state.active_reservation_sum
        + state.reserved_opening_fees
        + state.reserved_closing_costs
        + state.reserved_funding_costs
    )
    assert state.remaining_unreserved == state.canonical_available_capital - held
    assert readback.active_commitment_sum == facts["already_committed_capital"] == held
    assert run.policy_result.orchestrator_result.post_count == 0


@pytest.mark.parametrize(
    "fault",
    [
        "missing",
        "foreign-instrument",
        "processing",
        "unsupported-method",
        "missing-limit",
        "rate-outside-limits",
        "future-ts",
        "expired-settlement",
        "invalid-next-time",
        "foreign-acquisition",
        "reused",
    ],
)
def test_missing_or_unbound_funding_source_blocks_real_n1_without_hold(
    tmp_path, monkeypatch, fault
):
    install_policy(monkeypatch, policy())
    attach_funding_probe(monkeypatch, fault=fault)
    captures, _ = install_cost_probe(monkeypatch)
    run = _run_layered_entry_supervisor_v1(tmp_path, short=False)
    assert "FUNDING_COST_NOT_ADMITTED_NO_RESERVATION" in captures[0][1].reason_codes
    assert not captures[0][2]["state"]["reservations"]
    assert run.policy_result.orchestrator_result.cycle_records[-1].final_order_envelope is None


def test_favorable_forecast_is_not_capital_credit_and_high_adverse_limit_denies(
    tmp_path, monkeypatch
):
    with monkeypatch.context() as patch:
        live = install_policy(patch, policy())
        attach_funding_probe(patch, predicted="-0.005")
        captures, _ = install_cost_probe(patch)
        _run_layered_entry_supervisor_v1(tmp_path / "credit", short=False)
        assert captures[0][1].status == "PASS"
        assert live[0][0].reserved_funding_costs > 0
    with monkeypatch.context() as patch:
        install_policy(patch, policy())
        attach_funding_probe(patch, ceiling="2")
        captures, _ = install_cost_probe(patch)
        run = _run_layered_entry_supervisor_v1(tmp_path / "high", short=False)
        assert "TEST_SLOT_REMAINING_LOSS_BUDGET_EXCEEDED" in captures[0][1].reason_codes
        assert not captures[0][2]["state"]["reservations"]
        assert run.policy_result.orchestrator_result.cycle_records[-1].final_order_envelope is None


def test_original_replay_keeps_funding_proof_and_rejects_missing_or_changed_source(
    tmp_path, monkeypatch
):
    from src.ops.full_core_live_path_composition_root_v1 import (
        current_productive_enter_live_29p_join_v1 as join,
    )

    install_policy(monkeypatch, policy())
    attach_funding_probe(monkeypatch)
    install_cost_probe(monkeypatch)
    original = join.admit_sized_slot_reservation_v1
    observed = []

    def replay(owner, **kwargs):
        result = original(owner, **kwargs)
        assert result.reservation is not None
        rid = str(result.reservation.reservation_id)
        before = owner.budget_state_v1(), owner._store.sequence
        arguments = dict(
            request=kwargs["sizing_input"],
            opening_cost_observation=kwargs["opening_cost_observation"],
            funding_cost_observation=kwargs["funding_cost_observation"],
        )
        duplicate = owner.replay_sized_reservation_v1(rid, **arguments)
        assert duplicate.disposition.value == "IDEMPOTENT_REPLAY"
        assert duplicate.sizing_decision.final_quantity == result.sizing_decision.final_quantity
        for value in [None, replace(arguments["funding_cost_observation"], cycle_id="foreign")]:
            denied = owner.replay_sized_reservation_v1(
                rid, **{**arguments, "funding_cost_observation": value}
            )
            assert "FUNDING_COST_REPLAY_CONTEXT_CHANGED_OR_MISSING" in denied.reason_codes
        assert before == (owner.budget_state_v1(), owner._store.sequence)
        observed.append(True)
        return result

    monkeypatch.setattr(join, "admit_sized_slot_reservation_v1", replay)
    _run_layered_entry_supervisor_v1(tmp_path, short=False)
    assert observed == [True]


def test_funding_boundary_expires_entry_authority_without_releasing_original_hold(
    tmp_path, monkeypatch
):
    from src.ops.portfolio_capital_reservation_budget_v1.contract_v1 import (
        PortfolioCapitalReservationBudgetOwnerV1 as Owner,
    )

    install_policy(monkeypatch, policy())
    attach_funding_probe(monkeypatch, funding_seconds=1)
    _, clock = install_cost_probe(monkeypatch)
    bind = Owner.bind_execution_plan_v1
    checked = []

    def expire(self, rid, envelope, **kwargs):
        result = bind(self, rid, envelope, **kwargs)
        self.inspect_current_entry_budget_policy_v1(rid, envelope)
        before = self.budget_state_v1(), self._store.sequence
        initial = clock[0]
        clock[0] = (
            datetime.fromisoformat(initial.replace("Z", "+00:00")) + timedelta(seconds=2)
        ).isoformat()
        try:
            with pytest.raises(
                ValueError, match="FUNDING_COST_NEXT_SETTLEMENT_BOUND_EXPIRED_OR_INVALID"
            ):
                self.inspect_current_entry_budget_policy_v1(rid, envelope)
        finally:
            clock[0] = initial
        assert before == (self.budget_state_v1(), self._store.sequence)
        checked.append(True)
        return result

    monkeypatch.setattr(Owner, "bind_execution_plan_v1", expire)
    _run_layered_entry_supervisor_v1(tmp_path, short=False)
    assert checked == [True]


def test_previous_close_policy_does_not_silently_require_or_encode_funding():
    old = load_slot_entry_budget_v1(
        ROOT / "docs/ops/specs/BOUNDED_MULTISLOT_TEST_ENTRY_BUDGET_V4.json"
    )
    assert old.to_dict_v1()["schema"] == "entry_budget_policy.v5"
    assert "require_next_funding_costs" not in old.to_dict_v1()
    assert policy().require_next_funding_costs


@pytest.mark.parametrize(
    "field,value",
    [
        ("funding_allowance_usdc", "0"),
        ("slot_id", "LANE_2"),
        ("quantity", "999"),
        ("upcoming_funding_time_ms", 1),
    ],
)
def test_rehashed_receipt_cannot_replace_original_funding_source(
    tmp_path, monkeypatch, field, value
):
    install_policy(monkeypatch, policy())
    attach_funding_probe(monkeypatch)
    captures, _ = install_cost_probe(monkeypatch)
    _run_layered_entry_supervisor_v1(tmp_path, short=False)
    raw = next(iter(captures[0][2]["state"]["sizing_bindings"].values()))
    receipt = raw["funding_cost_binding"]["receipt"]
    receipt[field] = value
    receipt["digest"] = cost.digest({k: v for k, v in receipt.items() if k != "digest"})
    binding = ReservationSizingBindingV1.from_dict_v1(raw)
    with pytest.raises(ValueError, match="FUNDING_COST_SOURCE_OR_PROVISION_MISMATCH"):
        binding.validate_v1(
            amount=binding.decision.canonical_position_sizing.resulting_notional,
            decision_id=binding.applied_input.decision_id,
        )


@pytest.mark.parametrize("replacement", [False, True], ids=["keep", "replace"])
def test_original_five_slot_close_and_cold_read_retain_foreign_funding_reserves(
    tmp_path, monkeypatch, replacement
):
    from tests.ops import test_test_phase_slot_loss_budget_v1 as loss
    from tests.ops import test_bounded_slot_connected_roundtrip_v1 as connected
    from src.ops.portfolio_capital_reservation_budget_v1.contract_v1 import (
        PortfolioCapitalReservationBudgetOwnerV1 as Owner,
    )
    from src.ops.portfolio_capital_reservation_budget_v1.durable_store_v1 import (
        DurableBudgetStoreV1,
    )
    from src.ops.single_selected_future_runtime_binding_v1.models_v1 import BoundInstrumentV1

    worlds = loss._install_test_path(monkeypatch, exhausted=True)
    monkeypatch.setattr(connected, "policy", policy)
    # The roundtrip's close is after one hour. This source's explicit next
    # settlement is later; this test does not model settlement or rollover.
    attach_funding_probe(monkeypatch, funding_seconds=7200)
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
        provision = cost.reserved_funding_cost_v1(bound)
        assert provision > 0
        if reservation["slot_id"] == "LANE_5":
            assert reservation["state"] == "RELEASED"
        else:
            assert reservation["state"] == "COMMITTED"
            held += provision
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
        assert state.reserved_funding_costs == held > 0
        assert owner.test_slot_loss_state_v1("LANE_5")["exhausted"]
        assert owner.local_commitment_readback_v1().active_commitment_sum == (
            state.active_reservation_sum
            + state.reserved_opening_fees
            + state.reserved_closing_costs
            + held
        )
    finally:
        owner.close()
