"""Existing N1/hold/accounting/renewal/recovery consumers, simulated sources only."""

from dataclasses import replace
from decimal import Decimal, localcontext, ROUND_FLOOR
from fractions import Fraction
import json
from pathlib import Path

import pytest

from src.ops.portfolio_capital_reservation_budget_v1 import entry_execution_cost_v1 as cost
from src.ops.portfolio_capital_reservation_budget_v1 import native_cost_cover_v1 as cover
from src.ops.portfolio_capital_reservation_budget_v1.open_slot_cost_renewal_v1 import (
    OpenSlotCostRenewalContextV1,
)
from src.ops.portfolio_capital_reservation_budget_v1.test_phase_limits_v1 import (
    load_slot_entry_budget_v1,
    parse_slot_entry_budget_v1,
)
from tests.ops import test_native_initial_margin_admission_v1 as native
from tests.ops import test_open_slot_cost_reserve_renewal_v1 as renewal
from tests.ops import test_bounded_slot_connected_roundtrip_v1 as connected
from tests.ops.test_closing_execution_cost_provision_v1 import (
    install_policy,
    no_network as no_network,
)
from tests.ops._opening_execution_cost_fixture_v1 import install_cost_probe
from tests.ops.test_n1_original_reservation_host_handoff_v1 import (
    synthetic_ports_and_isolation as synthetic_ports_and_isolation,
)

ROOT = Path(__file__).resolve().parents[2]


def policy():
    return load_slot_entry_budget_v1(
        ROOT / "docs/ops/specs/BOUNDED_MULTISLOT_TEST_ENTRY_BUDGET_V10.json"
    )


def setup(monkeypatch, **options):
    install_policy(monkeypatch, policy())
    monkeypatch.setattr(connected, "policy", policy)
    captures, clock = install_cost_probe(monkeypatch)
    native.install_margin_probe(monkeypatch, clock, **options)
    return captures, clock


@pytest.mark.parametrize("short", [False, True])
def test_original_n1_quantity_and_native_costs_reach_original_hold(tmp_path, monkeypatch, short):
    captures, _ = setup(monkeypatch)
    result = native._run_layered_entry_supervisor_v1(tmp_path, short=short)
    kwargs, admitted, _state = captures[0]
    assert admitted.status == "PASS", admitted.reason_codes
    owner = kwargs["portfolio_budget_owner"]
    sizing = next(iter(owner._sizing_bindings.values()))
    margin, values = cover.original_costs_v1(sizing)
    assert all(v > 0 for v in values.values())
    assert sum(values.values()) < Fraction(1000)
    assert result.policy_result.orchestrator_result.post_count == 0
    assert margin["quantity"] == str(sizing.decision.final_quantity)
    assert not margin["native_cost_cover_proven"]  # Historical IM receipt unchanged.


def test_exact_margin_only_balance_is_rejected_by_actual_n1_without_partial_hold(
    tmp_path, monkeypatch
):
    # 6.7 USDT covers this fixture's 6.6667 IM, but not costs. USDC remains 1000.
    captures, _ = setup(monkeypatch, available="6.7")
    native._run_layered_entry_supervisor_v1(tmp_path, short=False)
    _kwargs, result, state = captures[0]
    assert result.status != "PASS"
    assert "NATIVE_COST_COVER_LOCAL_OBLIGATIONS_UNCOVERED" in result.reason_codes
    assert state["state"]["reservations"] == []


def test_five_original_holds_include_costs_in_native_aggregate(tmp_path, monkeypatch):
    captures, _ = setup(monkeypatch, available="34")
    with pytest.raises(AssertionError, match="NATIVE_COST_COVER_LOCAL_OBLIGATIONS_UNCOVERED"):
        connected.connected_close(tmp_path, monkeypatch, 5, "LANE_5")
    owner = captures[0][0]["portfolio_budget_owner"]
    try:
        assert 0 < len(owner._by_key) < 5
        assert all(r.counts_against_budget for r in owner._by_key.values())
    finally:
        owner.close()


def with_native_balance(sizing, available):
    retained = sizing.native_initial_margin_binding
    observation = json.loads(retained.observation_json)
    sources = json.loads(observation["sources_json"])
    parent = json.loads(retained.original_margin_json)
    currency = json.loads(retained.receipt_json)["settlement_currency"]
    next(r for r in sources["balance"]["payload"]["data"][0]["details"] if r["ccy"] == currency)[
        "availEq"
    ] = str(available)
    sources["balance"]["body_sha256"] = cost.digest(sources["balance"]["payload"])
    parent["provenance_digest"] = sources["balance"]["body_sha256"]
    observation["sources_json"] = cost.canonical(sources)
    binding = native.margin.bind_native_initial_margin_v1(
        native.margin.NativeInitialMarginObservationV1.from_dict_v1(observation),
        original_margin=native.margin.CurrentProductiveUsdcFreeMarginObservationV1(**parent),
        entry_binding=sizing.entry_cost_binding,
        monetary_source=sizing.monetary_source,
        applied_input=sizing.applied_input,
        decision=sizing.decision,
    )
    return replace(sizing, native_initial_margin_binding=binding)


def test_exact_native_cost_boundary_cannot_round_an_insufficient_balance_up(tmp_path, monkeypatch):
    captures, _ = setup(monkeypatch)
    native._run_layered_entry_supervisor_v1(tmp_path, short=False)
    owner = captures[0][0]["portfolio_budget_owner"]
    rid, sizing = next(iter(owner._sizing_bindings.items()))
    _margin, values = cover.original_costs_v1(sizing)
    required = sum(values.values())
    with localcontext() as context:
        context.prec, context.rounding = 50, ROUND_FLOOR
        below = Decimal(required.numerator) / Decimal(required.denominator)
        if Fraction(below) == required:
            below = context.next_minus(below)
        above = context.next_plus(below)
    assert Fraction(below) < required <= Fraction(above)
    for value, allowed in ((below, False), (above, True)):
        candidate = with_native_balance(sizing, value)
        with owner._lock:
            if allowed:
                native.margin.require_native_margin_locked_v1(
                    owner, candidate, exclude_reservation_id=rid
                )
            else:
                with pytest.raises(
                    ValueError, match="NATIVE_COST_COVER_LOCAL_OBLIGATIONS_UNCOVERED"
                ):
                    native.margin.require_native_margin_locked_v1(
                        owner, candidate, exclude_reservation_id=rid
                    )


def test_original_financial_replay_and_late_consumer_also_use_new_policy(tmp_path, monkeypatch):
    monkeypatch.setattr(native, "policy", policy)
    native.test_original_financial_replay_and_late_consumer_preserve_the_margin_parent(
        tmp_path, monkeypatch
    )


@pytest.mark.parametrize("field", ["require_native_initial_margin", "require_native_cost_cover"])
def test_new_policy_cannot_omit_or_disable_required_semantics(field):
    original = policy().to_dict_v1()
    for value in (False, None, "true"):
        with pytest.raises(ValueError):
            parse_slot_entry_budget_v1({**original, field: value})
    old = native.policy().to_dict_v1()
    assert old["schema"] == "entry_budget_policy.v10" and "require_native_cost_cover" not in old


def renewal_sources(monkeypatch, *, available="1000", fault=None):
    original = renewal.value_for

    def value_for(world, lane, epoch, **kwargs):
        value = original(world, lane, epoch, **kwargs)
        context = OpenSlotCostRenewalContextV1.from_dict_v1(json.loads(value.renewal_context_json))
        if fault == "missing":
            return value
        owner, rid = world["host"].owner, world["holds"][lane]
        sources = json.loads(
            json.loads(owner._sizing_bindings[rid].native_initial_margin_binding.observation_json)[
                "sources_json"
            ]
        )
        raw = sources["balance"]
        raw["payload"]["data"][0]["uid"] = owner._account_identity
        raw["payload"]["data"][0]["details"] = [
            dict(ccy="USDC", availEq="1000"),
            dict(ccy="USDT", availEq=available),
        ]
        current = json.loads(value.cost_sources_json)
        raw.update(
            acquired_at_utc=value.valuation_epoch,
            pretrade_decision_id=current["account"]["pretrade_decision_id"],
        )
        if fault == "foreign-account":
            raw["payload"]["data"][0]["uid"] = "other"
        elif fault == "missing-native":
            raw["payload"]["data"][0]["details"].pop()
        elif fault == "duplicate-native":
            raw["payload"]["data"][0]["details"].append(dict(ccy="USDT", availEq="999999"))
        elif fault == "availbal":
            raw["payload"]["data"][0]["details"][-1] = dict(ccy="USDT", availBal="999999")
        elif fault == "filtered":
            raw["endpoint"] += "?ccy=USDT"
        elif fault == "foreign-context":
            raw["pretrade_decision_id"] = "other"
        elif fault == "reused":
            raw["historical_reuse"] = True
        elif fault == "public":
            raw["auth_header_sent"] = False
        elif fault == "stale":
            raw["acquired_at_utc"] = "2000-01-01T00:00:00Z"
        elif fault == "capital-exceeds-source":
            raw["payload"]["data"][0]["details"][0]["availEq"] = "999"
        raw["body_sha256"] = cost.digest(raw["payload"])
        context = replace(context, native_balance_source_json=cost.canonical(raw))
        return replace(value, renewal_context_json=cost.canonical(context.to_dict_v1()))

    monkeypatch.setattr(renewal, "value_for", value_for)


def renew(tmp_path, monkeypatch, *, count=2, **options):
    setup(monkeypatch)
    renewal_sources(monkeypatch, **options)
    driver = renewal.Driver(tmp_path, target=f"LANE_{count}")
    try:
        with pytest.raises(renewal.connected.Observed):
            connected.connected_close(
                tmp_path, monkeypatch, count, driver.target, rotation_driver=driver
            )
        return driver
    except BaseException:
        if driver.world:
            renewal.connected.cleanup(driver)
        raise


@pytest.mark.parametrize("count", [2, 5])
def test_original_renewal_covers_all_native_holds_and_survives_cold_read(
    tmp_path, monkeypatch, count
):
    from tests.ops.test_test_phase_slot_loss_budget_v1 import _cold_owner

    driver = renew(tmp_path, monkeypatch, count=count)
    owner = driver.world["host"].owner
    try:
        proof = renewal.current.latest(driver, driver.target)
        assert proof["reserve_renewal_status"] == "RENEWAL_ADMITTED", proof[
            "reserve_renewal_reasons"
        ]
        receipt = proof["reserve_renewal"]
        native_cover = receipt["native_cost_cover"]
        assert receipt["schema"] == "open_slot_cost_reserve_renewal.v2"
        assert native_cover["covered"] and not native_cover["liquidation_cover_proven"]
        assert cover._unpack(native_cover["required_by_currency"]["USDT"]) > 6 * count
        assert owner._store.sequence == driver.sequence + 1
        assert driver.before.active_reservation_sum == driver.after.active_reservation_sum
        raw = owner.risk_snapshot_v1()["state"]
        root = driver.world["host"].root / "owner"
        renewal.connected.cleanup(driver)
        cold = _cold_owner(root, raw, selected_policy=policy())
        try:
            assert cold.budget_state_v1().recovery_required and not cold.budget_state_v1().admitted
            assert len(cold._open_slot_cost_reserves[driver.world["holds"][driver.target]]) == 1
        finally:
            cold.close()
    finally:
        renewal.connected.cleanup(driver)


@pytest.mark.parametrize(
    "fault",
    [
        "missing",
        "foreign-account",
        "missing-native",
        "duplicate-native",
        "availbal",
        "filtered",
        "foreign-context",
        "reused",
        "public",
        "stale",
        "capital-exceeds-source",
    ],
)
def test_unproven_native_renewal_keeps_original_holds_and_blocks_new_entry(
    tmp_path, monkeypatch, fault
):
    driver = renew(tmp_path, monkeypatch, fault=fault)
    try:
        proof = renewal.current.latest(driver, driver.target)
        assert proof["reserve_renewal_status"] == "UNPROVEN_HELD_RESERVES_RETAINED", proof
        assert proof["reserve_renewal"] is None and proof["reserve_renewal_reasons"]
        assert driver.before == driver.after
        owner = driver.world["host"].owner
        result = owner.try_reserve_v1(
            slot_id="LANE_3",
            decision_id="new",
            cycle_id="new",
            observation_id=owner.budget_state_v1().observation_id,
            amount=Decimal(1),
        )
        assert result.reason_codes == ("OPEN_SLOT_COST_RESERVE_RENEWAL_UNPROVEN",)
    finally:
        renewal.connected.cleanup(driver)


def test_native_shortfall_uses_original_safety_exit_without_releasing_foreign_holds(
    tmp_path, monkeypatch
):
    driver = renew(tmp_path, monkeypatch, count=5, available="1")
    try:
        proof = renewal.current.latest(driver, driver.target)
        assert (
            proof["reserve_renewal_status"] == "INSUFFICIENT_NATIVE_CAPITAL_HELD_RESERVES_RETAINED"
        ), proof
        assert proof["reason"] == "TEST_SLOT_RENEWED_NATIVE_CAPITAL_UNCOVERED"
        assert proof["reserve_renewal"] is None and proof["close_required"]
        assert driver.before == driver.after
        assert driver.results[driver.target].position_management_close_intent is not None
        assert all(
            v.position_management_close_intent is None
            for k, v in driver.results.items()
            if k != driver.target
        )
        assert all(v.governed_cycle_result.post_count == 0 for v in driver.results.values())
    finally:
        renewal.connected.cleanup(driver)


def test_new_renewal_replaces_native_future_costs_and_original_entry_gate_consumes_them(
    tmp_path, monkeypatch
):
    driver = renew(tmp_path, monkeypatch, count=2)
    try:
        world, lane = driver.world, driver.target
        owner, rid = world["host"].owner, world["holds"][lane]
        first = renewal.current.latest(driver, lane)["reserve_renewal"]
        epoch = world["kwargs"]["observed_unix"] + 1
        value = renewal.value_for(
            world, lane, epoch, next_horizon=first["upcoming_funding_time_ms"], fee="0.02"
        )
        renewal.observe(driver, value, epoch)
        second = renewal.current.latest(driver, lane)["reserve_renewal"]
        assert second is not None
        assert second["previous_reserve_ref"] == first["digest"]
        before = cover._unpack(first["native_cost_cover"]["target_costs"]["closing"])
        after = cover._unpack(second["native_cost_cover"]["target_costs"]["closing"])
        assert after > before and len(owner._open_slot_cost_reserves[rid]) == 2
        total_before = cover._unpack(first["native_cost_cover"]["required_by_currency"]["USDT"])
        total_after = cover._unpack(second["native_cost_cover"]["required_by_currency"]["USDT"])
        assert total_after - total_before == after - before
        # A different original candidate now sees the renewed obligation, not
        # the old entry receipt. The original IM-only comparison still passes.
        other = world["holds"]["LANE_1"]
        midpoint = (
            Decimal(total_before.numerator) / Decimal(total_before.denominator)
            + Decimal(total_after.numerator) / Decimal(total_after.denominator)
        ) / 2
        candidate = with_native_balance(owner._sizing_bindings[other], midpoint)
        with (
            owner._lock,
            pytest.raises(ValueError, match="NATIVE_COST_COVER_LOCAL_OBLIGATIONS_UNCOVERED"),
        ):
            native.margin.require_native_margin_locked_v1(
                owner, candidate, exclude_reservation_id=other
            )
    finally:
        renewal.connected.cleanup(driver)


@pytest.mark.parametrize("fault", ["cost", "total", "balance"])
def test_rehashed_native_renewal_summary_cannot_replace_original_sources_on_cold_read(
    tmp_path, monkeypatch, fault
):
    from tests.ops.test_test_phase_slot_loss_budget_v1 import _cold_owner
    from src.ops.portfolio_capital_reservation_budget_v1.durable_store_v1 import (
        DurableBudgetStoreV1,
    )
    from src.ops.portfolio_capital_reservation_budget_v1.contract_v1 import (
        PortfolioCapitalBudgetError,
    )

    driver = renew(tmp_path, monkeypatch)
    world = driver.world
    root, rid = world["host"].root / "owner", world["holds"][driver.target]
    renewal.connected.cleanup(driver)
    store = DurableBudgetStoreV1(root, account_identity="acct-1", mode="recover")
    try:
        raw = store.load()
        receipt = raw["open_slot_cost_reserves"][rid][0]
        native_cover = receipt["native_cost_cover"]
        if fault == "cost":
            native_cover["target_costs"]["closing"] = dict(numerator="0", denominator="1")
        elif fault == "total":
            native_cover["required_by_currency"]["USDT"] = dict(numerator="0", denominator="1")
        else:
            native_cover["available_by_currency"]["USDT"] = "999999999"
        native_cover["digest"] = cost.digest(
            {k: v for k, v in native_cover.items() if k != "digest"}
        )
        receipt["digest"] = cost.digest({k: v for k, v in receipt.items() if k != "digest"})
        store.save(raw)
    finally:
        store.close()
    with pytest.raises(PortfolioCapitalBudgetError, match="SEMANTIC_RESTORE_UNPROVEN"):
        _cold_owner(root, raw, selected_policy=policy())


@pytest.mark.parametrize("committed", [False, True])
def test_original_uncertain_commit_fence_also_retains_native_cost_reserves(
    tmp_path, monkeypatch, committed
):
    def run_under_new_policy(root, mp, *, count=2, target=None):
        assert target == f"LANE_{count}"
        return renew(root, mp, count=count)

    monkeypatch.setattr(renewal, "policy", policy)
    monkeypatch.setattr(renewal, "run", run_under_new_policy)
    renewal.test_unknown_renewal_commit_requires_original_cold_recovery(
        tmp_path, monkeypatch, committed
    )
