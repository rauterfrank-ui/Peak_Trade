"""Outer budget policy: no E2E capital/profile channel into Double Play."""

from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from decimal import Decimal
import json
from pathlib import Path

import pytest

from src.ops.full_core_live_path_composition_root_v1.current_productive_entry_budget_policy_v1 import (
    EntryBudgetPolicyV1,
    EntryBudgetPolicyError,
    load_entry_budget_policy_v1,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_enter_live_29p_join_v1 import (
    CurrentProductiveEnterLive29PPortfolioSlotContextV1 as Slot,
    join_current_productive_enter_live_29p_before_venue_plan_v1 as join,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_venue_plan_v1 import (
    try_bind_current_productive_venue_plan_v1,
)
from src.ops.full_core_live_path_composition_root_v1.final_order_envelope_v1 import (
    bind_final_order_envelope_from_venue_plan_v1,
)
from src.ops.portfolio_capital_reservation_budget_v1.contract_v1 import (
    PortfolioCapitalReservationBudgetOwnerV1 as Owner,
    ReserveDispositionV1 as D,
)
from tests.ops.test_full_core_current_productive_enter_live_29p_join_v1 import (
    EPOCH,
    _host_enter_cycle,
    _enter_replay,
    _bound,
    _injected,
    _balance_payload,
)
from tests.ops.test_portfolio_capital_reservation_budget_contract_v1 import _bind


def _join(owner, replay, policy=None, cycle="outer-budget"):
    return join(
        replay=replay,
        bound_instrument=_bound(),
        decision_epoch=EPOCH,
        injected=_injected(payload=_balance_payload(avail_eq="1000.00")),
        portfolio_budget_owner=owner,
        portfolio_slot=Slot(
            slot_id="LANE_1", decision_id=str(replay.evidence.decision_id), cycle_id=cycle
        ),
        entry_budget_policy=policy,
    )


def test_default_policy_is_outer_notional_limit_with_no_automatic_increase():
    policy = load_entry_budget_policy_v1()
    assert policy.per_entry_notional_limit == policy.aggregate_reserved_notional_limit == 25
    assert policy.currency == "USDC"
    assert policy.automatic_increase_allowed is False
    assert policy.expiry == "UNTIL_EXPLICIT_POLICY_CHANGE"
    repo = Path(__file__).resolve().parents[2]
    assert not any(
        "current_productive_entry_budget_policy_v1" in p.read_text()
        for p in (repo / "src/trading").rglob("*.py")
    )


def test_actual_join_caps_sizing_and_reserve_keeps_equity_and_never_reruns_dp(monkeypatch):
    _, cycle, _ = _host_enter_cycle()
    replay = _enter_replay(cycle)
    assert replay is cycle.replay
    original = replay.evidence

    def forbidden_dp_call(*args, **kwargs):
        raise AssertionError("The outer budget must never rerun a DP decision")

    monkeypatch.setattr(
        "trading.master_v2.double_play_entry_exit_policy_v0.evaluate_double_play_entry_exit_policy_v0",
        forbidden_dp_call,
    )
    monkeypatch.setattr(
        "src.ops.full_core_live_path_composition_root_v1.current_productive_master_v2_runtime_cycle_v1.run_integrated_offline_trading_logic_replay_v1",
        forbidden_dp_call,
    )
    owner = Owner()
    result = _join(owner, replay)
    assert result.status == "PASS", result.reason_codes
    sized = result.replay.intermediate.capital_risk_sizing_decision
    assert result.producer_output_value == "1000.00"
    assert owner.admitted_budget_v1() == 1000
    assert sized.scope_capital_envelope.available_capital == 1000
    assert sized.scope_capital_envelope.per_order_cap == 25
    assert sized.scope_capital_envelope.total_capital_limit == 25
    assert 0 < sized.canonical_position_sizing.resulting_notional <= 25
    assert owner.active_sum_v1() == sized.canonical_position_sizing.resulting_notional
    for key in (
        "decision_id",
        "selected_side",
        "decision_outcome",
        "scope_event_ref",
        "state_switch_ref",
        "entry_exit_policy_ref",
    ):
        assert getattr(result.replay.evidence, key) == getattr(original, key)
    assert replay.evidence is original
    assert result.entry_budget_policy_digest == load_entry_budget_policy_v1().digest_v1()
    status, reasons, plan = try_bind_current_productive_venue_plan_v1(
        replay=result.replay,
        bound_instrument=_bound(),
        session_id="outer-budget",
        run_id="outer-budget",
        composed_epoch=EPOCH,
        execution_mode="LIVE",
    )
    assert status.value == "PASS", reasons
    envelope = bind_final_order_envelope_from_venue_plan_v1(
        plan, admission_ref="offline", provenance_ref="outer-budget-proof", creation_epoch=EPOCH
    )
    assert Decimal(envelope.quantity) == sized.final_quantity
    assert result.post_count == "0" and result.permit_created == "false"


def test_below_venue_minimum_does_not_inflate_order_or_reserve():
    _, cycle, _ = _host_enter_cycle()
    owner = Owner()
    result = _join(
        owner, _enter_replay(cycle), EntryBudgetPolicyV1("too-small", 1, Decimal(1), Decimal(1))
    )
    assert result.status == "FAIL"
    assert owner.active_sum_v1() == 0
    assert owner.stored_reservation_count_v1() == 0
    assert result.post_count == "0"


def test_aggregate_ceiling_is_atomic_under_parallel_reserve_requests():
    owner = Owner()
    observation = _bind(owner, value="1000")
    with ThreadPoolExecutor(max_workers=8) as pool:
        results = list(
            pool.map(
                lambda n: owner.try_reserve_v1(
                    slot_id="LANE_1",
                    decision_id=f"parallel-{n}",
                    cycle_id="offline",
                    observation_id=observation,
                    amount=Decimal(10),
                    max_active_sum=Decimal(25),
                ),
                range(8),
            )
        )
    assert sum(r.disposition is D.ADMITTED for r in results) == 2
    assert owner.active_sum_v1() == 20
    assert owner.admitted_budget_v1() == 1000


def test_policy_revision_or_limit_change_cannot_resize_an_existing_hold():
    _, cycle, _ = _host_enter_cycle()
    owner = Owner()
    replay = _enter_replay(cycle)
    first = _join(owner, replay)
    before = owner.active_sum_v1()
    again = _join(owner, replay)
    assert again.status == "PASS"
    assert (
        again.replay.intermediate.capital_risk_sizing_decision
        == first.replay.intermediate.capital_risk_sizing_decision
    )
    changed = _join(
        owner,
        replay,
        replace(load_entry_budget_policy_v1(), revision=2, per_entry_notional_limit=Decimal(20)),
    )
    assert changed.status == "FAIL"
    assert changed.first_blocker == "RESERVATION_SIZING_CONTEXT_CHANGED"
    assert owner.active_sum_v1() == before


@pytest.mark.parametrize(
    "change", ["missing", "zero", "nan", "currency", "auto", "number", "unknown"]
)
def test_invalid_or_missing_policy_has_no_default_equity_or_unbounded_fallback(tmp_path, change):
    path = tmp_path / "policy.json"
    if change != "missing":
        payload = load_entry_budget_policy_v1().to_dict_v1()
        if change == "zero":
            payload["per_entry_notional_limit"] = "0"
        if change == "nan":
            payload["per_entry_notional_limit"] = "NaN"
        if change == "currency":
            payload["currency"] = "EUR"
        if change == "auto":
            payload["automatic_increase_allowed"] = True
        if change == "number":
            payload["per_entry_notional_limit"] = 25
        if change == "unknown":
            payload["invented"] = True
        path.write_text(json.dumps(payload))
    with pytest.raises(EntryBudgetPolicyError):
        load_entry_budget_policy_v1(path)


def test_hold_and_position_management_do_not_consume_entry_budget():
    _, cycle, _ = _host_enter_cycle()
    original = _enter_replay(cycle)
    for outcome, side in (("hold", "long"), ("reduce", "long"), ("exit", "long")):
        replay = replace(
            original,
            evidence=replace(original.evidence, decision_outcome=outcome, selected_side=side),
        )
        result = join(replay=replay, bound_instrument=_bound(), decision_epoch=EPOCH)
        assert result.get_count == 0
        assert result.replay is replay
        assert result.portfolio_reservation_id == ""
        assert result.entry_budget_policy_digest == ""
        if outcome in {"reduce", "exit"}:
            assert result.status == "NOT_CALLED_POSITION_MANAGEMENT"


def test_missing_policy_blocks_the_actual_join_without_fallback(tmp_path, monkeypatch):
    _, cycle, _ = _host_enter_cycle()
    owner = Owner()
    monkeypatch.setattr(
        "src.ops.full_core_live_path_composition_root_v1.current_productive_entry_budget_policy_v1.POLICY_PATH",
        tmp_path / "missing-policy.json",
    )
    result = _join(owner, _enter_replay(cycle))
    assert result.first_blocker == "ENTRY_BUDGET_POLICY_UNAVAILABLE_OR_INVALID"
    assert result.get_count == 0
    assert owner.active_sum_v1() == 0
    assert not owner.budget_state_v1().admitted


def test_outer_policy_identity_and_sizing_survive_durable_owner_recovery(tmp_path):
    from tests.ops.test_durable_portfolio_budget_recovery_v1 import _owner, _auto
    from tests.ops.test_portfolio_capital_reservation_budget_contract_v1 import (
        _produce,
        _sizing_input,
        _admit,
    )
    from src.ops.full_core_live_path_composition_root_v1.current_productive_mv2_capital_context_rebind_v1 import (
        build_current_productive_live_account_capital_context_v1,
    )

    request = _sizing_input(account_equity=Decimal(1000))
    source = build_current_productive_live_account_capital_context_v1(
        instrument_id=request.instrument_id,
        typed_account_equity=Decimal(1000),
        reference_price=request.reference_price,
        protective_stop_price=request.protective_stop_price,
        instrument_constraints=request.instrument,
    )
    constrained = load_entry_budget_policy_v1().constrain_entry_context_v1(source)
    request = replace(
        request,
        scope_capital_limit=constrained.scope_capital_limit,
        total_capital_limit=constrained.total_capital_limit,
        config_digest=constrained.config_digest,
    )
    owner = _owner(tmp_path)
    assert (
        _auto(
            owner, tmp_path, output=_produce(value="1000", epoch="2026-11-03T12:00:00Z")
        ).disposition
        is D.ADMITTED
    )
    first = _admit(owner, slot="LANE_1", decision=request.decision_id, value="1000", sizing=request)
    assert first.disposition is D.ADMITTED
    assert first.reservation.amount == 25
    owner.close()
    owner = _owner(tmp_path, "recover")
    try:
        assert (
            _auto(
                owner, tmp_path, output=_produce(value="1000", epoch="2026-11-03T12:00:00Z")
            ).disposition
            is D.ADMITTED
        )
        again = _admit(
            owner, slot="LANE_1", decision=request.decision_id, value="1000", sizing=request
        )
        assert again.disposition is D.IDEMPOTENT_REPLAY
        assert again.sizing_decision == first.sizing_decision
        assert again.sizing_decision.quantity_provenance.config_digest == constrained.config_digest
        assert owner.admitted_budget_v1() == 1000
        assert owner.active_sum_v1() == 25
    finally:
        owner.close()
