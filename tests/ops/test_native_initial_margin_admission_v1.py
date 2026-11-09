"""Original N1 quantity -> native margin -> atomic original hold -> cold read.

All GETs/fills are explicit internal simulations. No venue/account truth claim.
"""

from copy import deepcopy
from dataclasses import replace
from decimal import Decimal
from fractions import Fraction
import json
from pathlib import Path

import pytest

from src.ops.portfolio_capital_reservation_budget_v1 import native_initial_margin_v1 as margin
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
from tests.ops.test_next_funding_cost_provision_v1 import attach_funding_probe
from tests.ops.test_n1_original_reservation_host_handoff_v1 import (
    synthetic_ports_and_isolation as synthetic_ports_and_isolation,
)

ROOT = Path(__file__).resolve().parents[2]


def policy():
    return load_slot_entry_budget_v1(
        ROOT / "docs/ops/specs/BOUNDED_MULTISLOT_TEST_ENTRY_BUDGET_V9.json"
    )


def install_margin_probe(monkeypatch, clock, *, fault=None, available="1000", lever="3"):
    from tests.ops import _opening_execution_cost_fixture_v1 as fixture

    attach_funding_probe(monkeypatch)
    attach = fixture.attach_costs

    def observe(kwargs, **options):
        opening = attach(kwargs, **options)
        raw = json.loads(opening.sources_json)
        raw["account"]["payload"]["data"][0].update(acctLv="2", posMode="net_mode")
        raw["account"]["body_sha256"] = cost.digest(raw["account"]["payload"])
        opening = replace(opening, sources_json=cost.canonical(raw))
        injected = kwargs["injected"]
        clock[0] = injected.observed_at
        payload = deepcopy(injected.payload)
        payload["data"][0]["details"] = [
            r for r in payload["data"][0]["details"] if r["ccy"] != "USDT"
        ] + [dict(ccy="USDT", availEq=available)]
        kwargs["injected"] = replace(
            injected,
            opening_cost_observation=opening,
            payload=payload,
            body_sha256=cost.digest(payload),
        )
        base = raw["account"]
        balance = cost.FreshPretradeGetTransportResultV1(
            **{
                **base,
                "endpoint": "/api/v5/account/balance",
                "payload": payload,
                "body_sha256": cost.digest(payload),
                "acquired_at_utc": injected.observed_at,
            }
        )
        native = kwargs["bound_instrument"].venue_native_id
        leverage = cost.FreshPretradeGetTransportResultV1(
            **{
                **base,
                "endpoint": f"/api/v5/account/leverage-info?instId={native}&mgnMode=cross",
                "payload": dict(
                    code="0",
                    data=[dict(instId=native, mgnMode="cross", posSide="net", lever=lever)],
                ),
            }
        )
        sources = dict(balance=balance, leverage=leverage)
        if fault == "missing-native":
            payload["data"][0]["details"] = [
                r for r in payload["data"][0]["details"] if r["ccy"] != "USDT"
            ]
        elif fault == "duplicate-native":
            payload["data"][0]["details"].append(dict(ccy="USDT", availEq=available))
        elif fault == "unusable-availbal":
            payload["data"][0]["details"][-1] = dict(ccy="USDT", availBal="1000000", eq="1000000")
        elif fault == "foreign-account":
            payload["data"][0]["uid"] = "foreign-account"
        elif fault == "other-mode":
            raw["account"]["payload"]["data"][0]["acctLv"] = "3"
            opening = replace(opening, sources_json=cost.canonical(raw))
            kwargs["injected"] = replace(kwargs["injected"], opening_cost_observation=opening)
        elif fault == "hedge":
            leverage.payload["data"][0]["posSide"] = "long"
        elif fault == "wrong-instrument":
            leverage.payload["data"][0]["instId"] = "foreign"
        elif fault == "duplicate-leverage":
            leverage.payload["data"].append(deepcopy(leverage.payload["data"][0]))
        elif fault == "missing-leverage":
            leverage.payload["data"][0]["lever"] = ""
        elif fault == "no-auth":
            sources["leverage"] = replace(leverage, auth_header_sent=False)
        elif fault == "reuse":
            sources["leverage"] = replace(leverage, historical_reuse=True)
        elif fault == "stale":
            sources["leverage"] = replace(leverage, acquired_at_utc="2000-01-01T00:00:00Z")
        elif fault == "future":
            sources["leverage"] = replace(leverage, acquired_at_utc="2100-01-01T00:00:00Z")
        elif fault == "foreign-acquisition":
            sources["leverage"] = replace(leverage, pretrade_decision_id="foreign")
        elif fault == "filtered-balance":
            sources["balance"] = replace(balance, endpoint="/api/v5/account/balance?ccy=USDT")
        elif fault == "capital-parent":
            sources["balance"] = replace(balance, body_sha256="f" * 64)
        elif fault == "wrong-contract-unit":
            instruments = deepcopy(kwargs["injected"].instruments_payload)
            next(r for r in instruments["data"] if r["instId"] == native)["ctValCcy"] = "USDT"
            raw["instruments"]["payload"] = instruments
            raw["instruments"]["body_sha256"] = cost.digest(instruments)
            opening = replace(opening, sources_json=cost.canonical(raw))
            kwargs["injected"] = replace(
                kwargs["injected"],
                instruments_payload=instruments,
                opening_cost_observation=opening,
            )
        value = margin.NativeInitialMarginObservationV1.capture_v1(
            sources=sources,
            opening_observation=opening,
            evaluated_at_utc=injected.observed_at,
        )
        if fault == "entry-parent":
            value = replace(value, opening_observation_digest="0" * 64)
        if fault != "missing":
            kwargs["injected"] = replace(
                kwargs["injected"], native_initial_margin_observation=value
            )
        return opening

    monkeypatch.setattr(fixture, "attach_costs", observe)


def run(tmp_path, monkeypatch, **options):
    install_policy(monkeypatch, policy())
    captures, clock = install_cost_probe(monkeypatch)
    install_margin_probe(monkeypatch, clock, **options)
    result = _run_layered_entry_supervisor_v1(tmp_path, short=False)
    assert len(captures) == 1
    return result, captures[0], clock


@pytest.mark.parametrize("short", [False, True])
def test_original_n1_quantity_uses_native_cash_not_valuation_fx(tmp_path, monkeypatch, short):
    live = install_policy(monkeypatch, policy())
    captures, clock = install_cost_probe(monkeypatch)
    install_margin_probe(monkeypatch, clock)
    run = _run_layered_entry_supervisor_v1(tmp_path, short=short)
    kwargs, result, state = captures[0]
    assert result.status == "PASS", result.reason_codes
    raw = next(iter(state["state"]["sizing_bindings"].values()))
    assert raw["schema"] == "reservation_sizing_binding.v7"
    binding = ReservationSizingBindingV1.from_dict_v1(raw)
    binding.validate_v1(
        amount=binding.decision.canonical_position_sizing.resulting_notional,
        decision_id=binding.applied_input.decision_id,
    )
    receipt = raw["native_initial_margin_binding"]["receipt"]
    envelope = run.policy_result.orchestrator_result.cycle_records[-1].final_order_envelope
    assert envelope.quantity == receipt["quantity"]
    assert receipt["settlement_currency"] == "USDT"
    assert receipt["observed_leverage"] == "3"
    assert receipt["side"] == ("SHORT" if short else "LONG")
    required = Fraction(int(receipt["required_numerator"]), int(receipt["required_denominator"]))
    notional = Fraction(int(receipt["notional_numerator"]), int(receipt["notional_denominator"]))
    assert required * 3 == notional > 0
    assert live and run.policy_result.orchestrator_result.post_count == 0
    # The native margin check creates no second USDC debit or credit.
    budget, _, readback = live[0]
    assert readback.venue_margin_coverage == "UNPROVEN_NO_MARGIN_CREDIT"
    assert (
        budget.active_reservation_sum
        == binding.decision.canonical_position_sizing.resulting_notional
    )
    assert not receipt["liquidation_cover_proven"] and not receipt["native_cost_cover_proven"]


@pytest.mark.parametrize(
    "fault",
    [
        "missing",
        "missing-native",
        "duplicate-native",
        "unusable-availbal",
        "foreign-account",
        "other-mode",
        "hedge",
        "wrong-instrument",
        "duplicate-leverage",
        "missing-leverage",
        "no-auth",
        "reuse",
        "stale",
        "future",
        "foreign-acquisition",
        "filtered-balance",
        "capital-parent",
        "wrong-contract-unit",
        "entry-parent",
    ],
)
def test_unbound_sources_block_actual_entry_without_hold(tmp_path, monkeypatch, fault):
    _run, (_kwargs, result, state), _clock = run(tmp_path, monkeypatch, fault=fault)
    assert result.status != "PASS"
    assert any("NATIVE_INITIAL_MARGIN" in r for r in result.reason_codes), result.reason_codes
    assert state["state"]["reservations"] == []


@pytest.mark.parametrize(
    "field,value",
    [
        ("available", "0"),
        ("available", "NaN"),
        ("available", "-1"),
        ("lever", "0"),
        ("lever", "Infinity"),
        ("lever", "-1"),
    ],
)
def test_native_shortfall_or_invalid_numbers_cannot_borrow_usdc_fx_credit(
    tmp_path, monkeypatch, field, value
):
    _run, (_kwargs, result, state), _clock = run(tmp_path, monkeypatch, **{field: value})
    assert result.status != "PASS" and state["state"]["reservations"] == []


def test_old_policy_is_not_upgraded():
    old = load_slot_entry_budget_v1(
        ROOT / "docs/ops/specs/BOUNDED_MULTISLOT_TEST_ENTRY_BUDGET_V8.json"
    )
    assert old.to_dict_v1()["schema"] == "entry_budget_policy.v9"
    assert old.require_native_initial_margin is False
    assert "require_native_initial_margin" not in old.to_dict_v1()
    assert policy().to_dict_v1()["schema"] == "entry_budget_policy.v10"


def test_collector_reuses_original_balance_and_only_requests_bound_leverage(tmp_path, monkeypatch):
    _run, (_kwargs, _result, state), clock = run(tmp_path, monkeypatch)
    raw = next(iter(state["state"]["sizing_bindings"].values()))
    original = raw["native_initial_margin_binding"]["observation"]
    opening = cost.EntryExecutionCostObservationV1.from_dict_v1(
        raw["entry_cost_binding"]["observation"]
    )
    sources = json.loads(original["sources_json"])
    calls = []

    class Port:
        def get(self, **kwargs):
            assert kwargs == dict(
                endpoint=sources["leverage"]["endpoint"],
                auth_required=True,
                pretrade_decision_id=opening.acquisition_decision_id,
                get_cache_policy="DYNAMIC_REFRESH_REQUIRED",
            )
            calls.append(kwargs)
            return cost.FreshPretradeGetTransportResultV1(**sources["leverage"])

    collected = margin.collect_native_initial_margin_observation_v1(
        transport=Port(),
        opening_observation=opening,
        balance_source=cost.FreshPretradeGetTransportResultV1(**sources["balance"]),
    )
    assert len(calls) == 1 and collected.to_dict_v1() == original
    assert collected.evaluated_at_utc == clock[0]


def test_repeating_margin_cannot_round_down_an_insufficient_native_balance(tmp_path, monkeypatch):
    from decimal import localcontext, ROUND_FLOOR

    _run, (_kwargs, _result, state), _clock = run(tmp_path, monkeypatch)
    raw = next(iter(state["state"]["sizing_bindings"].values()))
    binding = ReservationSizingBindingV1.from_dict_v1(raw)
    retained = binding.native_initial_margin_binding
    observed = json.loads(retained.observation_json)
    sources = json.loads(observed["sources_json"])
    receipt = json.loads(retained.receipt_json)
    notional = Fraction(int(receipt["notional_numerator"]), int(receipt["notional_denominator"]))
    divisor = next(p for p in (3, 7, 11, 13, 17, 19) if notional.numerator % p)
    required = notional / divisor
    assert required.denominator % divisor == 0
    with localcontext() as ctx:
        ctx.prec, ctx.rounding = 28, ROUND_FLOOR
        below = Decimal(required.numerator) / Decimal(required.denominator)
        above = ctx.next_plus(below)
    parent = json.loads(retained.original_margin_json)
    sources["leverage"]["payload"]["data"][0]["lever"] = str(divisor)
    arguments = dict(
        entry_binding=binding.entry_cost_binding,
        monetary_source=binding.monetary_source,
        applied_input=binding.applied_input,
        decision=binding.decision,
    )
    for available, allowed in ((below, False), (above, True)):
        row = next(
            r for r in sources["balance"]["payload"]["data"][0]["details"] if r["ccy"] == "USDT"
        )
        row["availEq"] = str(available)
        sources["balance"]["body_sha256"] = cost.digest(sources["balance"]["payload"])
        parent["provenance_digest"] = sources["balance"]["body_sha256"]
        observation = margin.NativeInitialMarginObservationV1.from_dict_v1(
            {
                **observed,
                "sources_json": cost.canonical(sources),
            }
        )
        if allowed:
            margin.assess_native_initial_margin_v1(
                observation,
                original_margin=margin.CurrentProductiveUsdcFreeMarginObservationV1(**parent),
                **arguments,
            )
        else:
            with pytest.raises(ValueError, match="NATIVE_INITIAL_MARGIN_INSUFFICIENT"):
                margin.assess_native_initial_margin_v1(
                    observation,
                    original_margin=margin.CurrentProductiveUsdcFreeMarginObservationV1(**parent),
                    **arguments,
                )


def test_original_financial_replay_and_late_consumer_preserve_the_margin_parent(
    tmp_path, monkeypatch
):
    from datetime import datetime, timedelta
    from src.ops.full_core_live_path_composition_root_v1 import (
        current_productive_enter_live_29p_join_v1 as join,
    )
    from src.ops.portfolio_capital_reservation_budget_v1.contract_v1 import (
        PortfolioCapitalReservationBudgetOwnerV1 as Owner,
    )

    install_policy(monkeypatch, policy())
    captures, clock = install_cost_probe(monkeypatch)
    install_margin_probe(monkeypatch, clock)
    admit, bind = join.admit_sized_slot_reservation_v1, Owner.bind_execution_plan_v1
    proofs = []

    def observe_admit(owner, **kwargs):
        result = admit(owner, **kwargs)
        assert result.reservation is not None
        rid = str(result.reservation.reservation_id)
        arguments = dict(
            request=kwargs["sizing_input"],
            opening_cost_observation=kwargs["opening_cost_observation"],
            funding_cost_observation=kwargs["funding_cost_observation"],
            native_initial_margin_observation=kwargs["native_initial_margin_observation"],
        )
        before = owner.budget_state_v1(), owner._store.sequence
        duplicate = owner.replay_sized_reservation_v1(rid, **arguments)
        assert duplicate.disposition.value == "IDEMPOTENT_REPLAY"
        for value in [
            None,
            replace(
                arguments["native_initial_margin_observation"], opening_observation_digest="f" * 64
            ),
        ]:
            blocked = owner.replay_sized_reservation_v1(
                rid, **{**arguments, "native_initial_margin_observation": value}
            )
            assert blocked.disposition.value == "FAIL_CLOSED"
            assert "NATIVE_INITIAL_MARGIN_REPLAY_CONTEXT_CHANGED_OR_MISSING" in blocked.reason_codes
        assert before == (owner.budget_state_v1(), owner._store.sequence)
        proofs.append("original financial replay")
        return result

    def observe_plan(owner, rid, envelope, **kwargs):
        result = bind(owner, rid, envelope, **kwargs)
        before = owner.budget_state_v1(), owner._store.sequence
        owner.inspect_current_entry_budget_policy_v1(rid, envelope)
        original_clock = clock[0]
        clock[0] = (
            datetime.fromisoformat(original_clock.replace("Z", "+00:00")) + timedelta(seconds=6)
        ).isoformat()
        try:
            with pytest.raises(ValueError, match="ACQUISITION_STALE"):
                owner.inspect_current_entry_budget_policy_v1(rid, envelope)
        finally:
            clock[0] = original_clock
        assert before == (owner.budget_state_v1(), owner._store.sequence)
        proofs.append("late entry consumer")
        return result

    monkeypatch.setattr(join, "admit_sized_slot_reservation_v1", observe_admit)
    monkeypatch.setattr(Owner, "bind_execution_plan_v1", observe_plan)
    _run_layered_entry_supervisor_v1(tmp_path, short=False)
    assert captures[0][1].status == "PASS"
    assert proofs == ["original financial replay", "late entry consumer"]


class StopAfterFills(Exception):
    pass


def five_world(tmp_path, monkeypatch):
    from tests.ops import test_bounded_slot_connected_roundtrip_v1 as connected

    install_policy(monkeypatch, policy())
    monkeypatch.setattr(connected, "policy", policy)
    captures, clock = install_cost_probe(monkeypatch)
    install_margin_probe(monkeypatch, clock)

    class Driver:
        world = None

        def nominate(self, world):
            self.membership = world["membership"]
            return world["recovery"]

        def close(self, world):
            self.world = world
            raise StopAfterFills()

    driver = Driver()
    try:
        with pytest.raises(StopAfterFills):
            connected.connected_close(tmp_path, monkeypatch, 5, "LANE_5", rotation_driver=driver)
        assert len(captures) == 5
        return driver.world
    except BaseException:
        if driver.world:
            driver.world["host"].close()
            driver.world["writer"].release()
        raise


@pytest.mark.parametrize("fault", [None, "missing", "receipt", "parent"])
def test_five_filled_original_holds_survive_cold_read_or_reject_rehashed_tampering(
    tmp_path, monkeypatch, fault
):
    from src.ops.portfolio_capital_reservation_budget_v1.contract_v1 import (
        PortfolioCapitalBudgetError,
    )
    from src.ops.portfolio_capital_reservation_budget_v1.durable_store_v1 import (
        DurableBudgetStoreV1,
    )
    from tests.ops.test_test_phase_slot_loss_budget_v1 import _cold_owner

    world = five_world(tmp_path, monkeypatch)
    host = world["host"]
    before = host.owner.local_commitment_readback_v1().active_commitment_sum
    root = host.root / "owner"
    host.close()
    world["writer"].release()
    store = DurableBudgetStoreV1(root, account_identity="acct-1", mode="recover")
    try:
        raw = store.load()
        assert len(raw["sizing_bindings"]) == 5
        row = next(iter(raw["sizing_bindings"].values()))
        if fault == "missing":
            del row["native_initial_margin_binding"]
            row["schema"] = "reservation_sizing_binding.v6"
        elif fault:
            value = row["native_initial_margin_binding"]
            if fault == "receipt":
                value["receipt"]["required_numerator"] = "0"
            else:
                value["original_margin"]["already_net_of_in_use"] = "false"
                value["receipt"]["original_capital_observation_digest"] = cost.digest(
                    value["original_margin"]
                )
            value["receipt"]["digest"] = cost.digest(
                {k: v for k, v in value["receipt"].items() if k != "digest"}
            )
        if fault:
            store.save(raw)
    finally:
        store.close()
    if fault:
        with pytest.raises(PortfolioCapitalBudgetError, match="SEMANTIC_RESTORE_UNPROVEN"):
            _cold_owner(root, raw, selected_policy=policy())
    else:
        cold = _cold_owner(root, raw, selected_policy=policy())
        try:
            assert cold.local_commitment_readback_v1().active_commitment_sum == before
            assert cold.budget_state_v1().recovery_required and not cold.budget_state_v1().admitted
            assert len(cold.risk_snapshot_v1()["state"]["sizing_bindings"]) == 5
        finally:
            cold.close()


def test_five_slot_atomic_admission_counts_every_native_obligation(tmp_path, monkeypatch):
    from src.ops.full_core_live_path_composition_root_v1 import (
        current_productive_enter_live_29p_join_v1 as join,
    )

    install_policy(monkeypatch, policy())
    captures, clock = install_cost_probe(monkeypatch)
    install_margin_probe(monkeypatch, clock, available="25")
    original = join.admit_sized_slot_reservation_v1
    results = []

    def admit(owner, **kwargs):
        value = original(owner, **kwargs)
        results.append(value)
        return value

    monkeypatch.setattr(join, "admit_sized_slot_reservation_v1", admit)
    from tests.ops import test_bounded_slot_connected_roundtrip_v1 as connected

    monkeypatch.setattr(connected, "policy", policy)
    with pytest.raises(AssertionError, match="NATIVE_INITIAL_MARGIN_LOCAL_OBLIGATIONS_UNCOVERED"):
        connected.connected_close(tmp_path, monkeypatch, 5, "LANE_5")
    assert any(
        "NATIVE_INITIAL_MARGIN_LOCAL_OBLIGATIONS_UNCOVERED" in r.reason_codes for r in results
    )
    # Each source admits its own order; only the original locked aggregate
    # blocks the excess slot. No partial reservation is added for denied slots.
    owner = captures[0][0]["portfolio_budget_owner"]
    active = [r for r in owner._by_key.values() if r.counts_against_budget]
    assert 0 < len(active) < 5
    owner.close()
