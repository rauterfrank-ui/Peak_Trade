"""Actual bounded N1 close/continuation consumes a test-only slot loss allowance."""

from dataclasses import replace
from copy import deepcopy
from decimal import Decimal
import json
from pathlib import Path
import shutil

import pytest

from src.ops.portfolio_capital_reservation_budget_v1.test_phase_limits_v1 import (
    load_slot_entry_budget_v1,
    parse_slot_entry_budget_v1,
)
from src.ops.portfolio_capital_reservation_budget_v1.slot_economic_source_v1 import (
    SlotCloseAccountingSourceV1,
)
from src.ops.productive_futures_accounting_runtime_binding_v1.accounting_engine_v1 import (
    ProductiveFuturesAccountingSessionV1,
)
from src.ops.portfolio_capital_reservation_budget_v1.contract_v1 import (
    PortfolioCapitalReservationBudgetOwnerV1,
    PortfolioCapitalBudgetError,
    capital_context_facts_v1,
)
from src.ops.portfolio_capital_reservation_budget_v1.durable_store_v1 import DurableBudgetStoreV1
from tests.ops import test_bounded_slot_connected_roundtrip_v1 as original

ROOT = Path(__file__).resolve().parents[2]
POLICY = ROOT / "docs/ops/specs/BOUNDED_MULTISLOT_TEST_ENTRY_BUDGET_V2.json"


def policy():
    return load_slot_entry_budget_v1(POLICY)


def test_loss_limit_is_explicit_test_phase_without_changing_old_policy():
    current = policy()
    assert current.per_slot_test_loss_limit == Decimal(25)
    assert current.to_dict_v1()["loss_limit_scope"] == "EXPLICIT_TEST_PHASE_ONLY"
    assert not current.to_dict_v1()["automatic_loss_budget_refill_allowed"]
    old = load_slot_entry_budget_v1(
        ROOT / "docs/ops/specs/BOUNDED_MULTISLOT_TEST_ENTRY_BUDGET_V1.json"
    )
    assert old.per_slot_test_loss_limit is None
    assert old.to_dict_v1()["schema"] == "entry_budget_policy.v2"
    assert "per_slot_test_loss_limit" not in old.to_dict_v1()


@pytest.mark.parametrize(
    "field,value",
    [
        ("loss_limit_scope", "PRODUCTIVE_FOREVER"),
        ("automatic_loss_budget_refill_allowed", True),
        ("per_slot_test_loss_limit", "26"),
        ("per_slot_test_loss_limit", 25),
        ("per_slot_test_loss_limit", "NaN"),
    ],
)
def test_unrequested_scope_refill_or_loss_limit_is_refused(field, value):
    data = policy().to_dict_v1()
    data[field] = value
    with pytest.raises(ValueError):
        parse_slot_entry_budget_v1(data)


def _install_test_path(monkeypatch, exhausted):
    monkeypatch.setattr(original, "policy", policy)
    worlds = []
    seed = original.connected_close
    constructor = original.PostCloseFeedbackRequestV1
    apply = ProductiveFuturesAccountingSessionV1.apply_fill

    def funding_path(session, fill):
        if (
            exhausted
            and fill.fill_id.startswith("original-close:")
            and "scripted-test-funding" not in session.funding_events
        ):
            # Explicit scripted synthetic settlement. The original kernel
            # supplies the monetary result; no product probability/forecast.
            probe = ProductiveFuturesAccountingSessionV1.from_durable_dict(
                session.to_durable_dict()
            )
            apply(probe, fill)
            target = -Decimal(25) - (probe.portfolio_state().equity - probe.initial_equity)
            session.apply_funding_observation_v1(
                event_id="scripted-test-funding",
                amount=str(target),
                currency=session.contract.quote_currency,
                instrument_id=session.contract.symbol,
                event_time_unix=fill.event_time_unix - 0.001,
            )
        return apply(session, fill)

    def capture(*args, **kwargs):
        world = seed(*args, **kwargs)
        worlds.append(world)
        return world

    def request(*args, **kwargs):
        built = constructor(*args, **kwargs)
        world = worlds[-1]
        lane = built.execution.source.quantity_handoff.lane_id
        source = built.budget_owner.reservation_monetary_source_v1(world["holds"][lane])
        index = json.loads(source.index_tickers_json)
        for row in index["data"]:
            row["ts"] = str(int((original.T0 + 121) * 1000))
        accounting = SlotCloseAccountingSourceV1.from_episode_v1(
            world["episodes"][lane],
            valuation_epoch=built.observed_at_utc,
            index_tickers_payload=index,
            pair_instruments_payload=json.loads(source.conversion_pair_instruments_json),
            fx_acquired_at_utc=built.observed_at_utc,
        )
        return replace(built, slot_accounting_source=accounting)

    monkeypatch.setattr(ProductiveFuturesAccountingSessionV1, "apply_fill", funding_path)
    monkeypatch.setattr(original, "connected_close", capture)
    monkeypatch.setattr(original, "PostCloseFeedbackRequestV1", request)
    return worlds


@pytest.mark.parametrize("exhausted", [False, True], ids=["positive-result", "exactly-25-consumed"])
@pytest.mark.parametrize("replacement", [False, True], ids=["keep", "replace"])
def test_original_natural_slot_cycle_records_result_and_consumes_loss_gate(
    tmp_path, monkeypatch, exhausted, replacement
):
    _install_test_path(monkeypatch, exhausted)
    original.roundtrip(
        tmp_path, monkeypatch, 2, "LANE_1", replacement, expected_loss_exhausted=exhausted
    )


@pytest.fixture(scope="module")
def exhausted_five_slot_state(tmp_path_factory):
    root = tmp_path_factory.mktemp("five-slot-test-loss")
    with pytest.MonkeyPatch.context() as patch:
        worlds = _install_test_path(patch, exhausted=True)
        original.roundtrip(root, patch, 5, "LANE_5", False, expected_loss_exhausted=True)
        store = DurableBudgetStoreV1(
            worlds[0]["host"].root / "owner", account_identity="acct-1", mode="recover"
        )
        try:
            return store.load(), worlds[0]
        finally:
            store.close()


def _write_reviewed_state(root, raw):
    # Rehash through the original writer: these tests reach semantic recovery,
    # rather than merely failing the SQLite history checksum.
    store = DurableBudgetStoreV1(root, account_identity="acct-1", mode="create")
    try:
        store.save(raw)
    finally:
        store.close()


def _cold_owner(root, raw, *, selected_policy=None):
    from src.ops.single_selected_future_runtime_binding_v1.models_v1 import BoundInstrumentV1

    return PortfolioCapitalReservationBudgetOwnerV1(
        durable_root=root,
        durable_account_identity="acct-1",
        durable_mode="recover",
        durable_lane_bindings={
            lane: BoundInstrumentV1(**row["bound"]) for lane, row in raw["lane_bindings"].items()
        },
        entry_budget_policy=selected_policy,
    )


def test_five_slot_cold_read_retains_loss_and_cannot_silently_end_test_phase(
    tmp_path, exhausted_five_slot_state
):
    raw, _world = exhausted_five_slot_state
    _write_reviewed_state(tmp_path / "owner", raw)
    owner = _cold_owner(tmp_path / "owner", raw)
    try:
        state = owner.test_slot_loss_state_v1("LANE_5")
        assert state["exhausted"] and state["remaining_loss_allowance_usdc"] == "0"
        assert len(state["records"]) == 1
        assert owner.entry_budget_policy_v1() == policy()
        assert not owner.budget_state_v1().admitted
        assert owner.active_slot_sum_v1("LANE_5") == 0
        assert all(owner.active_slot_sum_v1(f"LANE_{i}") > 0 for i in range(1, 5))
    finally:
        owner.close()
    old = load_slot_entry_budget_v1(
        ROOT / "docs/ops/specs/BOUNDED_MULTISLOT_TEST_ENTRY_BUDGET_V1.json"
    )
    with pytest.raises(PortfolioCapitalBudgetError, match="SEMANTIC_RESTORE_UNPROVEN"):
        _cold_owner(tmp_path / "owner", raw, selected_policy=old)


@pytest.mark.parametrize(
    "fault",
    [
        "missing-state",
        "reset-summary",
        "record-omitted",
        "duplicate-record",
        "foreign-slot",
        "forged-net",
        "missing-sealed-source",
        "future-fx",
        "fx-before-capture",
        "stale-fx",
        "missing-fx",
        "wrong-account",
        "wrong-pair",
        "before-close-known",
    ],
)
def test_cold_recovery_rejects_reset_or_unproven_economics(
    tmp_path, exhausted_five_slot_state, fault
):
    base, world = exhausted_five_slot_state
    raw = deepcopy(base)
    state = raw["test_slot_economics"]["LANE_5"]
    record = state["records"][0]
    source = record["source"]
    if fault == "missing-state":
        del raw["test_slot_economics"]
    elif fault == "reset-summary":
        state.update(net_result_usdc="0", exhausted=False)
    elif fault == "record-omitted":
        # Missing source can be pending after a legitimate interrupted handoff,
        # but must never regain Entry authority (tested separately below).
        state.update(records=[], net_result_usdc="0", exhausted=False)
    elif fault == "duplicate-record":
        state["records"].append(deepcopy(record))
    elif fault == "foreign-slot":
        raw["test_slot_economics"]["LANE_1"] = state
    elif fault == "forged-net":
        record["net_result_usdc"] = "0"
    elif fault == "missing-sealed-source":
        source["state_root"] = str(tmp_path / "missing-original-episode")
    elif fault == "wrong-account":
        identity = json.loads(source["identity_json"])
        identity["account_scope"]["account_identity"] = "foreign-account"
        source["identity_json"] = json.dumps(identity)
    elif fault == "missing-fx":
        source["index_tickers_json"] = "null"
    elif fault == "wrong-pair":
        pair = json.loads(source["pair_instruments_json"])
        pair["data"][0].update(baseCcy="EUR", ctValCcy="EUR")
        source["pair_instruments_json"] = json.dumps(pair)
    elif fault == "before-close-known":
        source["valuation_epoch"] = original.utc(original.T0 + 62.5)
    else:
        index = json.loads(source["index_tickers_json"])
        event = original.T0 + {"future-fx": 122, "stale-fx": 0, "fx-before-capture": 121}[fault]
        index["data"][0]["ts"] = str(int(event * 1000))
        source["index_tickers_json"] = json.dumps(index)
        if fault == "fx-before-capture":
            source["fx_acquired_at_utc"] = original.utc(original.T0 + 120)
    _write_reviewed_state(tmp_path / "owner", raw)
    if fault == "record-omitted":
        shutil.copytree(world["host"].root / "reconciliation", tmp_path / "reconciliation")
        host = original.PortfolioBudgetHostV1(
            root=tmp_path,
            private_rest_fetch=world["host"].fetch,
            repository_sha=original.sources.REPO_SHA,
            session_id="cold-missing-economics",
            expected_account_identity="acct-1",
            clock=lambda: original.T0 + 602,
            execution_environment="INTERNAL_SIMULATED_EXECUTION",
            entry_budget_policy=policy(),
        )
        try:
            recovery = host.observe_v1(world["bounds"])
            assert host.owner.test_slot_loss_state_v1("LANE_5")["new_entry_blocker"] == (
                "TEST_SLOT_CLOSED_ECONOMICS_NOT_RECONCILED"
            )
            # Fresh capital alone cannot repair missing original economics.
            recovery.recover_v1(
                host.owner, original._produce(value="1000", epoch=original.utc(original.T0 + 602))
            )
            with pytest.raises(
                PortfolioCapitalBudgetError, match="CLOSED_ECONOMICS_NOT_RECONCILED"
            ):
                capital_context_facts_v1(host.owner, slot_id="LANE_5")
            assert all(host.owner.active_slot_sum_v1(f"LANE_{i}") > 0 for i in range(1, 5))
        finally:
            host.close()
    else:
        with pytest.raises(PortfolioCapitalBudgetError, match="SEMANTIC_RESTORE_UNPROVEN"):
            _cold_owner(tmp_path / "owner", raw)
