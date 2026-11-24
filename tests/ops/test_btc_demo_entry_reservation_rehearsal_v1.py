"""Actual Slot 3 decision and isolated internal USDC budget, no venue calls."""

from dataclasses import replace
from decimal import Decimal
from datetime import datetime

import pytest

from src.ops.portfolio_capital_reservation_budget_v1.contract_v1 import (
    PortfolioCapitalReservationBudgetOwnerV1,
)
from src.ops.full_core_live_path_composition_root_v1 import (
    productive_read_only_get_transport_v1 as wire,
)
from src.ops.okx_eea_private_account_state_runtime_v1.k1_source_v1 import (
    open_k1_account_observation_source_v1,
)
from tests.ops.test_k1_account_observation_source_v1 import InjectedOpener, _FakeKeychainBackend
from tests.ops import test_btc_demo_offline_trading_host_v1 as btc
from tests.ops import test_current_usdc_xperp_financial_admission_v1 as financial
from tests.ops.test_closing_execution_cost_provision_v1 import no_network as no_network


@pytest.fixture
def scenario(tmp_path, monkeypatch, request):
    direction = request.param
    monkeypatch.setattr(btc.budget_fixture, "ACCOUNT", financial.ACCOUNT)
    original_instrument = btc.instrument

    def demo_instrument(**kwargs):
        return dict(original_instrument(**kwargs), ctVal="1", lotSz="0.0001", minSz="0.0001")

    monkeypatch.setattr(btc, "instrument", demo_instrument)
    demo, candles, admission, public = btc.setup_host(tmp_path, monkeypatch, direction)
    try:
        entry, _ = btc.enter(demo, candles, admission, direction)
        private = dict(public, settleCcy="USDC")
        epoch = entry.cycle.replay.intermediate.market_context.decision_time
        timestamp = datetime.fromisoformat(epoch.replace("Z", "+00:00")).timestamp()
        monkeypatch.setattr(wire, "utc_now_iso_v1", lambda: epoch)
        opener = InjectedOpener(account=financial.ACCOUNT)
        monkeypatch.setattr(wire, "build_opener", lambda *handlers: opener)
        with open_k1_account_observation_source_v1(
            expected_account_identity=financial.ACCOUNT,
            session_id="lane3-offline",
            max_request_count=40,
            account_inventory_guard=True,
            inventory_inst_type="FUTURES",
            clock=lambda: timestamp,
            k1_lookup_backend=_FakeKeychainBackend(),
        ) as source:
            sim = financial.PortfolioBudgetHostV1(
                root=tmp_path / "sim",
                private_rest_fetch=source,
                repository_sha="offline-synthetic",
                session_id="lane3-offline",
                expected_account_identity=financial.ACCOUNT,
                durable_mode="create",
                clock=lambda: timestamp,
                execution_environment="INTERNAL_SIMULATED_EXECUTION",
                entry_budget_policy=replace(
                    financial.policy(),
                    allowed_slot_ids=("LANE_3",),
                    aggregate_reserved_notional_limit=Decimal("25"),
                ),
            )
            try:
                recovery = sim.observe_v1({"LANE_3": demo.budget.bound})
                _, kwargs, clock = financial.prepare(
                    tmp_path,
                    monkeypatch,
                    slot="LANE_3",
                    slot_entry=(demo.budget.bound, entry.cycle, private),
                    host_context=(sim, recovery),
                )
                monkeypatch.setattr(
                    financial.pretrade_acquisition_v1, "utc_now_iso_v1", lambda: clock[0]
                )
                injected = replace(
                    kwargs["injected"],
                    acquisition_decision_id=epoch,
                    acquisition_cycle_id=entry.cycle.cycle_id,
                    pretrade_acquired_at_utc=(epoch,),
                )
                yield demo, sim, entry, injected, recovery
            finally:
                sim.close()
    finally:
        demo.budget.owner.close()


@pytest.mark.parametrize("scenario", [1, -1], indirect=True)
def test_slot3_reservation_survives_cold_read(scenario):
    demo, sim, entry, injected, recovery = scenario
    head = demo.budget.budget_revision_ref_v1()
    hold = demo.rehearse_entry_reservation_v1(entry=entry, injected=injected, recovery=recovery)
    assert hold.instrument_id == demo.budget.bound.instrument_id
    assert hold.venue_native_id == btc.demo._NATIVE
    assert hold.amount_basis == "CANONICAL_SIZING_RESULTING_NOTIONAL"
    units = Decimal(hold.canonical_quantity)
    assert units > 0 and units % Decimal("0.0001") == 0
    binding = sim.owner.risk_snapshot_v1()["state"]["sizing_bindings"][hold.reservation_id]
    margin = binding["native_initial_margin_binding"]["receipt"]
    assert margin["settlement_currency"] == "USDC"
    assert margin["side"].lower() == entry.cycle.decision_outcome.removeprefix("enter_")
    assert all(
        x > 0
        for x in (hold.opening_fee_reserve, hold.closing_cost_reserve, hold.funding_cost_reserve)
    )
    assert Decimal(0) < hold.amount <= Decimal("25")
    total = sim.owner.local_commitment_readback_v1().active_commitment_sum
    assert (
        total
        == hold.amount
        + hold.opening_fee_reserve
        + hold.closing_cost_reserve
        + hold.funding_cost_reserve
    )
    assert total <= Decimal("25")
    assert units == Decimal("0.0003")
    opening = binding["entry_cost_binding"]["receipt"]
    mark = Decimal(str(entry.cycle.replay.intermediate.market_context.mark_price))
    sign = 1 if margin["side"] == "LONG" else -1
    price_sum = (mark + sign * Decimal("0.1")) * Decimal("0.0001") + (
        mark + sign * Decimal("0.2")
    ) * Decimal("0.0002")
    assert Decimal(opening["book_vwap"]) == price_sum / units
    assert hold.opening_fee_reserve == price_sum * Decimal("0.0005")
    with pytest.raises(ValueError, match="FRESH_FLAT_ENTRY_REQUIRED"):
        demo.rehearse_entry_reservation_v1(entry=entry, injected=injected, recovery=recovery)
    assert sim.owner.local_commitment_readback_v1().commitments == (hold,)
    root = sim.owner.durable_scope_identity_v1()["root"]
    sim.close()
    owner = PortfolioCapitalReservationBudgetOwnerV1(
        durable_root=root,
        durable_account_identity=recovery.account,
        durable_mode="recover",
        durable_lane_bindings={"LANE_3": demo.budget.bound},
        entry_budget_policy=sim.entry_budget_policy,
    )
    try:
        readback = owner.local_commitment_readback_v1()
        assert readback.commitments == (hold,) and readback.active_commitment_sum == total
        assert (
            demo.budget.budget_revision_ref_v1() == head and demo.budget.owner.active_sum_v1() == 0
        )
    finally:
        owner.close()


@pytest.mark.parametrize("scenario", [1], indirect=True)
@pytest.mark.parametrize(
    "fault,reason",
    [
        ("other-cycle", "PRIVATE_LINEAR_DECISION_INPUTS_REQUIRED"),
        ("public-index", "PRIVATE_LINEAR_DECISION_INPUTS_REQUIRED"),
        ("missing-funding", "FUNDING"),
        ("stale", "ACQUISITION_STALE"),
        ("changed-scope", "DECISION_SCOPE_MISMATCH"),
        ("wrong-account", "ISOLATED_SLOT_ACCOUNT_REQUIRED"),
        ("pending", "FRESH_FLAT_ENTRY_REQUIRED"),
        ("swap", "ISOLATED_SLOT_ACCOUNT_REQUIRED"),
    ],
)
def test_rejected_handoff_creates_no_obligation(scenario, monkeypatch, fault, reason):
    demo, sim, entry, injected, recovery = scenario
    if fault == "other-cycle":
        injected = replace(injected, acquisition_cycle_id="other:LANE_3")
    elif fault == "public-index":
        injected = replace(
            injected, index_tickers_payload={"data": [{"instId": "USDC-USD", "idxPx": "1"}]}
        )
    elif fault == "missing-funding":
        injected = replace(injected, funding_cost_observation=None)
    elif fault == "stale":
        monkeypatch.setattr(
            financial.pretrade_acquisition_v1, "utc_now_iso_v1", lambda: "2026-11-24T08:10:00Z"
        )
    elif fault == "changed-scope":
        replay = entry.cycle.replay
        mid = replay.intermediate
        event = mid.scope_event
        wrong = replace(event, semantic_binding=replace(event.semantic_binding, up_distance=1))
        entry = replace(
            entry,
            cycle=replace(
                entry.cycle, replay=replace(replay, intermediate=replace(mid, scope_event=wrong))
            ),
        )
    elif fault == "wrong-account":
        injected = replace(injected, expected_account_identity="other")
    elif fault == "pending":
        recovery = replace(recovery, pending_orders=True)
    elif fault == "swap":
        recovery = replace(
            recovery, observed=replace(recovery.observed, source_id="host-private-rest-swap")
        )
    before = demo.budget.budget_revision_ref_v1()
    with pytest.raises(ValueError, match=reason):
        demo.rehearse_entry_reservation_v1(entry=entry, injected=injected, recovery=recovery)
    assert sim.owner.local_commitment_readback_v1().commitments == ()
    assert demo.budget.budget_revision_ref_v1() == before


def test_bounded_policy_rejects_testnet_host_before_opening_store(tmp_path):
    with pytest.raises(ValueError, match="SLOT_TEST_BUDGET_REQUIRES_SIMULATED_HOST"):
        financial.PortfolioBudgetHostV1(
            root=tmp_path / "testnet",
            private_rest_fetch=None,
            repository_sha="offline",
            session_id="offline",
            expected_account_identity=financial.ACCOUNT,
            execution_environment="TESTNET",
            durable_mode="create",
            entry_budget_policy=financial.policy(),
        )
    assert not (tmp_path / "testnet").exists()


@pytest.mark.parametrize("scenario", [1], indirect=True)
@pytest.mark.parametrize(
    "missing", ["replay", "injected", "portfolio_slot", "host_budget_recovery"]
)
def test_reservation_only_denies_incomplete_entry_before_acquisition(scenario, missing):
    from src.ops.full_core_live_path_composition_root_v1.current_productive_enter_live_29p_join_v1 import (
        CurrentProductiveEnterLive29PPortfolioSlotContextV1,
        join_current_productive_enter_live_29p_before_venue_plan_v1,
    )

    demo, sim, entry, injected, recovery = scenario
    before = sim.owner.risk_snapshot_v1()["durable_head"]
    cycle = entry.cycle
    inputs = dict(
        replay=cycle.replay,
        bound_instrument=demo.budget.bound,
        decision_epoch=cycle.replay.intermediate.market_context.decision_time,
        injected=injected,
        portfolio_budget_owner=sim.owner,
        portfolio_slot=CurrentProductiveEnterLive29PPortfolioSlotContextV1(
            "LANE_3", cycle.replay.evidence.decision_id, cycle.cycle_id
        ),
        host_budget_recovery=recovery,
        reservation_only=True,
    )
    inputs[missing] = None
    result = join_current_productive_enter_live_29p_before_venue_plan_v1(**inputs)
    assert result.first_blocker == "RESERVATION_ONLY_ORIGINAL_ENTER_CONTEXT_REQUIRED"
    assert result.venue_plan_authorized is False and result.replay is None
    assert result.get_count == 0 and sim.owner.risk_snapshot_v1()["durable_head"] == before
