"""Original Core and TESTNET writer with a mocked Demo HTTP server only."""

from dataclasses import replace
from datetime import datetime
from decimal import Decimal
import json

import pytest

from scripts.ops.inspect_btc_demo_account_v1 import pretrade_reader
from src.ops import btc_demo_lane3_v2 as demo
from src.ops.portfolio_capital_reservation_budget_v1.contract_v1 import (
    PortfolioCapitalReservationBudgetOwnerV1,
)
from src.ops.portfolio_capital_reservation_budget_v1.slot_loss_budget_v1 import (
    SlotCapitalAllocationV1,
)
from tests.ops import test_btc_demo_offline_trading_host_v1 as btc
from tests.ops import test_current_usdc_xperp_financial_admission_v1 as financial
from tests.ops.test_inspect_btc_demo_account_v1 import Response
from tests.ops.test_closing_execution_cost_provision_v1 import no_network as no_network


@pytest.fixture(params=[1, -1])
def demo_entry(tmp_path, monkeypatch, request):
    monkeypatch.setattr(financial, "ACCOUNT", btc.budget_fixture.ACCOUNT)
    instrument = btc.instrument
    monkeypatch.setattr(
        btc,
        "instrument",
        lambda **kw: dict(instrument(**kw), ctVal="1", lotSz="0.0001", minSz="0.0001"),
    )
    policy = replace(
        financial.policy(),
        allowed_slot_ids=("LANE_3",),
        aggregate_reserved_notional_limit=Decimal(25),
    )
    allocation = SlotCapitalAllocationV1(
        btc.budget_fixture.ACCOUNT,
        "explicit-offline-initial-allocation",
        (("LANE_3", Decimal(25)),),
    )
    host, candles, admission, public = btc.setup_host(
        tmp_path,
        monkeypatch,
        request.param,
        policy=policy,
        execution_environment="TESTNET",
        allocation=allocation,
    )
    try:
        entry, _ = btc.enter(host, candles, admission, request.param)
        _, args, _ = financial.prepare(
            tmp_path,
            monkeypatch,
            slot="LANE_3",
            host_context=(host.budget, None),
            slot_entry=(host.budget.bound, entry.cycle, dict(public, settleCcy="USDC")),
            fixture_transport="OKX_EEA_TESTNET_OFFLINE_FIXTURE",
        )
        injected = args["injected"]
        raw = json.loads(injected.opening_cost_observation.sources_json)
        raw.update(json.loads(injected.native_initial_margin_observation.sources_json))
        raw["funding"] = json.loads(injected.funding_cost_observation.source_json)
        payloads = {key: value["payload"] for key, value in raw.items()}
        payloads.update(positions=dict(code="0", data=[]), pending=dict(code="0", data=[]))
        epoch = entry.cycle.replay.intermediate.market_context.decision_time
        instant = datetime.fromisoformat(epoch.replace("Z", "+00:00"))

        class FrozenDatetime(datetime):
            @classmethod
            def now(cls, tz=None):
                return instant if tz is None else instant.astimezone(tz)

        monkeypatch.setattr(demo, "datetime", FrozenDatetime)

        class Opener:
            def open(self, req, timeout):
                assert req.method == "GET" and req.data is None
                assert req.get_header("X-simulated-trading") == "1"
                matches = [
                    key
                    for key, (path, query) in demo.BTC_DEMO_PRETRADE_QUERIES_V1.items()
                    if req.selector == path + ("?" + demo.urlencode(query) if query else "")
                ]
                assert len(matches) == 1
                return Response(req.full_url, payloads[matches[0]]["data"])

        monkeypatch.setattr(demo, "build_opener", lambda *handlers: Opener())
        reads = pretrade_reader("fixture-key", "fixture-secret", "fixture-phrase")
        yield host, entry, reads, financial.raw_input(args), instant, payloads
    finally:
        host.budget.owner.close()


@pytest.mark.parametrize("available", ["25", "2500"])
def test_original_demo_entry_reserves_costs_and_reopens_same_testnet_journal(demo_entry, available):
    host, entry, reads, movement, instant, payloads = demo_entry
    for detail in payloads["balance"]["data"][0]["details"]:
        if detail["ccy"] == "USDC":
            for key in ("availEq", "availBal", "cashBal", "eq"):
                if key in detail:
                    detail[key] = available
    result, checksum = host.reserve_testnet_entry_v1(
        entry=entry,
        reads=reads,
        movement_input=movement,
        clock=instant.timestamp,
    )
    assert result.disposition.value == "ADMITTED"
    owner = host.budget.owner
    before = owner.local_commitment_readback_v1()
    (held,) = before.commitments
    assert held.canonical_quantity == "0.0003"
    assert before.active_commitment_sum <= Decimal(25)
    assert min(held.opening_fee_reserve, held.closing_cost_reserve, held.funding_cost_reserve) > 0
    assert held.execution_phase == "NO_EXECUTION_LINK"
    rid = result.reservation.reservation_id
    state = owner.risk_snapshot_v1()["state"]
    assert state["execution_environment"] == "TESTNET"
    assert "offline_testnet_source_digest" not in state["sizing_bindings"][rid]
    saved = state["sizing_bindings"][rid]
    from src.ops.governed_productive_monetary_normalization_v1.sizing_source_v1 import (
        SizingMonetarySourceV1,
    )

    money = SizingMonetarySourceV1.from_dict_v1(saved["monetary_source"])
    context, identity, _ = money.rebuild_v1()
    assert identity.quote_currency == context.native_reference_price.currency == "USD"
    assert identity.settle_currency == context.reference_price.currency == "USDC"
    assert context.contract_settlement_rule.account_identity == host.budget.account
    assert context.usdt_usdc_edge is None
    from src.ops.governed_productive_monetary_normalization_v1.contracts_v1 import (
        MonetaryNormalizationError,
    )

    with pytest.raises(MonetaryNormalizationError, match="XPERP_PAYOFF_IS_NOT_MARKET_FX"):
        replace(money, index_tickers_json='{"data": []}').rebuild_v1()
    with pytest.raises(MonetaryNormalizationError, match="XPERP_QUOTED_PRICE_UNIT_MISMATCH"):
        context.contract_settlement_rule.cash_multiplier_v1("USDC")
    assert saved["entry_cost_binding"]["receipt"]["quote_currency"] == "USD"
    margin = saved["native_initial_margin_binding"]["receipt"]
    assert margin["quoted_price_currency"] == "USD"
    assert margin["settlement_currency"] == "USDC"
    source = (
        demo._demo_lane_root(host.budget.root) / "entry-reservation-sources" / (checksum + ".json")
    )
    packet = json.loads(source.read_bytes())
    assert set(packet["original_bodies_hex"]) == set(demo.BTC_DEMO_PRETRADE_QUERIES_V1)
    assert all(
        secret not in source.read_text()
        for secret in ("fixture-key", "fixture-secret", "fixture-phrase")
    )
    assert owner.slot_capital_basis_v1("LANE_3").initial_usdc == Decimal(25)
    with pytest.raises(ValueError, match="EXISTING_OBLIGATION"):
        host.reserve_testnet_entry_v1(
            entry=entry,
            reads=reads,
            movement_input=movement,
            clock=instant.timestamp,
        )
    assert owner.local_commitment_readback_v1().commitments == before.commitments
    root = owner.durable_scope_identity_v1()["root"]
    owner.close()
    from src.ops.btc_demo_budget_owner_v3 import BtcDemoBudgetOwnerV3

    reopened = BtcDemoBudgetOwnerV3(
        durable_root=root,
        durable_account_identity=host.budget.account,
        durable_mode="recover",
        durable_lane_bindings={"LANE_3": host.budget.bound},
    )
    try:
        after = reopened.local_commitment_readback_v1()
        assert after.commitments == before.commitments
        assert reopened.slot_capital_basis_v1("LANE_3").initial_usdc == Decimal(25)
    finally:
        reopened.close()


def test_demo_entry_rejects_nonflat_inventory_before_reserving(demo_entry):
    host, entry, reads, movement, instant, payloads = demo_entry
    payloads["positions"]["data"] = [{"instId": demo._NATIVE, "pos": "0.0001", "posSide": "net"}]
    before = host.budget.budget_revision_ref_v1()
    with pytest.raises(ValueError, match="REQUIRES_FLAT_INVENTORY"):
        host.reserve_testnet_entry_v1(
            entry=entry,
            reads=reads,
            movement_input=movement,
            clock=instant.timestamp,
        )
    assert host.budget.budget_revision_ref_v1() == before
    assert host.budget.owner.active_sum_v1() == 0


@pytest.mark.parametrize("fault", ["body-payload-divergence", "expired-after-read"])
def test_demo_originals_are_checked_before_any_budget_mutation(demo_entry, fault):
    from copy import deepcopy
    from src.ops.btc_demo_entry_reservation_v1 import reserve_btc_demo_entry_v1

    host, entry, reads, movement, instant, _ = demo_entry
    batch = host.inspect_testnet_pretrade_sources_v1(
        entry=entry,
        reads=reads,
        clock=instant.timestamp,
    )
    if fault == "body-payload-divergence":
        source = batch["sources"]["book"]
        payload = deepcopy(source.payload)
        payload["data"][0]["asks"][0][0] = "1"
        batch["sources"]["book"] = replace(source, payload=payload)
    before = host.budget.budget_revision_ref_v1()
    with pytest.raises(ValueError, match="SOURCE_MISMATCH|ACQUISITION_STALE"):
        reserve_btc_demo_entry_v1(
            host,
            cycle=entry.cycle,
            batch=batch,
            movement_input=movement,
            clock=lambda: instant.timestamp() + (16 if fault == "expired-after-read" else 0),
        )
    assert host.budget.budget_revision_ref_v1() == before
    assert host.budget.owner.active_sum_v1() == 0


def test_native_usd_mark_requires_an_explicit_valuation_before_reservation(demo_entry):
    from src.ops.btc_demo_entry_financial_inputs_v1 import build_btc_demo_sizing_inputs_v1

    host, entry, _, _, instant, payloads = demo_entry
    revision = host.budget.budget_revision_ref_v1()
    with pytest.raises(ValueError, match="NATIVE_PRICE_UNIT_REQUIRES_EXPLICIT_VALUATION"):
        build_btc_demo_sizing_inputs_v1(
            entry.cycle,
            host.budget.bound,
            payloads["instruments"],
            Decimal(25),
            instant.isoformat(),
            host.budget.owner.entry_budget_policy_v1(),
            "a" * 64,
            capital_risk_mode="TESTNET_ACCOUNT_BOUND",
            native_price_currency="USD",
        )
    assert host.budget.budget_revision_ref_v1() == revision
    assert host.budget.owner.active_sum_v1() == 0


@pytest.mark.parametrize("fault", ["settle", "quote", "underlying", "account"])
def test_contract_cash_binding_rejects_incompatible_originals_without_hold(demo_entry, fault):
    host, entry, reads, movement, instant, payloads = demo_entry
    row = payloads["instruments"]["data"][0]
    if fault == "settle":
        row["settleCcy"] = "USD"
    elif fault == "quote":
        row["quoteCcy"] = "USDC"
    elif fault == "underlying":
        row["uly"] = "ETH-USD"
    else:
        payloads["account"]["data"][0]["settleCcy"] = "USD"
    revision = host.budget.budget_revision_ref_v1()
    with pytest.raises(ValueError, match="ACCOUNT_USDC_SETTLEMENT_SOURCE_REQUIRED"):
        host.reserve_testnet_entry_v1(
            entry=entry, reads=reads, movement_input=movement, clock=instant.timestamp
        )
    assert host.budget.budget_revision_ref_v1() == revision
    assert host.budget.owner.active_sum_v1() == 0


def test_v3_journal_reopens_with_same_environment_and_rejects_generic_owner(demo_entry):
    from src.ops.btc_demo_budget_owner_v3 import BtcDemoBudgetOwnerV3, CONTRACT
    from src.ops.portfolio_capital_reservation_budget_v1.contract_v1 import (
        PortfolioCapitalBudgetError,
    )

    host, _, _, _, _, _ = demo_entry
    owner = host.budget.owner
    root = owner.durable_scope_identity_v1()["root"]
    head = owner._store.head
    snapshot = owner.risk_snapshot_v1()["state"]
    assert snapshot["testnet_owner_contract"] == CONTRACT
    assert snapshot["execution_environment"] == "TESTNET"
    owner.close()
    with pytest.raises(PortfolioCapitalBudgetError):
        PortfolioCapitalReservationBudgetOwnerV1(
            durable_root=root,
            durable_account_identity=host.budget.account,
            durable_mode="recover",
            durable_lane_bindings={"LANE_3": host.budget.bound},
        )
    reopened = BtcDemoBudgetOwnerV3(
        durable_root=root,
        durable_account_identity=host.budget.account,
        durable_mode="recover",
        durable_lane_bindings={"LANE_3": host.budget.bound},
    )
    try:
        assert reopened._store.head == head
        assert reopened.execution_environment_v1() == "TESTNET"
        assert reopened.slot_capital_basis_v1("LANE_3").initial_usdc == Decimal(25)
        refused = reopened.try_reserve_v1()
        assert refused.disposition.value == "FAIL_CLOSED"
        assert refused.reason_codes == ("BTC_DEMO_V3_ORIGINAL_ENTRY_SOURCES_REQUIRED",)
        assert reopened._store.head == head
    finally:
        reopened.close()


def test_v3_cannot_reinterpret_a_generic_journal_as_demo(tmp_path):
    from src.ops.btc_demo_budget_owner_v3 import BtcDemoBudgetOwnerV3

    host, _ = btc.budget_fixture.owner_host(tmp_path)
    root = host.owner.durable_scope_identity_v1()["root"]
    head = host.owner._store.head
    host.owner.close()
    with pytest.raises(ValueError, match="V3_JOURNAL_ENVIRONMENT"):
        BtcDemoBudgetOwnerV3(
            durable_root=root,
            durable_account_identity=host.account,
            durable_mode="recover",
            durable_lane_bindings={"LANE_3": host.bound},
        )
    restored = PortfolioCapitalReservationBudgetOwnerV1(
        durable_root=root,
        durable_account_identity=host.account,
        durable_mode="recover",
        durable_lane_bindings={"LANE_3": host.bound},
    )
    try:
        assert restored._store.head == head
    finally:
        restored.close()
