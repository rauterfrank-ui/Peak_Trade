"""Offline readiness evidence over the existing accounting session, not live proof."""

from dataclasses import replace
from decimal import Decimal
import json
from pathlib import Path
import subprocess
from unittest.mock import patch

import pytest

from src.ops.productive_futures_accounting_runtime_binding_v1.accounting_engine_v1 import (
    ProductiveFuturesAccountingSessionV1,
    AccountingEngineError,
)
from src.ops.productive_futures_accounting_runtime_binding_v1.models_v1 import (
    ContractMetadataV1,
    SimulatedFillInputV1,
)
from src.ops.productive_futures_accounting_runtime_binding_v1.single_writer_v1 import (
    ProductiveFuturesAccountingSingleWriterV1,
)
from src.ops.productive_futures_accounting_runtime_binding_v1 import persistence_v1 as storage
from src.ops.governed_productive_account_equity_authority_producer_v1.equity_verification_policy_v1 import (
    load_equity_verification_policy_v1,
    assess_equity_window_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.real_equity_replay_v1 import (
    reconcile_real_equity_window_v1,
    compare_native_display_v1,
)
from tests.ops.test_real_equity_replay_v1 import fixture

D = Decimal
ROOT = Path(__file__).resolve().parents[2]


def session(multiplier="0.1", symbol="SUI-USDC-SWAP", initial="1000"):
    contract = ContractMetadataV1(
        symbol=symbol,
        contract_size=D(multiplier),
        tick_size=D("0.01"),
        min_qty=D("1"),
        quote_currency="USDC",
        initial_margin_rate=D("0.1"),
        maintenance_margin_rate=D("0.05"),
        max_leverage=D("10"),
        contract_type="linear",
    )
    return ProductiveFuturesAccountingSessionV1(contract=contract, initial_equity=D(initial))


def fill(s, identity, side, qty, price, mark, fee="0", slip="0", time=1):
    return SimulatedFillInputV1(
        fill_id=identity,
        instrument_id=s.contract.symbol,
        side=side,
        quantity=D(qty),
        fill_price=D(price),
        mark_price=D(mark),
        fee=D(fee),
        slippage_cost=D(slip),
        notional=D(qty) * D(price) * s.contract.contract_size,
        event_time_unix=time,
    )


def persist(s, root):
    writer = ProductiveFuturesAccountingSingleWriterV1(
        state_root=root, session_id="offline-verification"
    )
    writer.acquire()
    try:
        storage.persist_accounting_bundle_atomic_v1(state_root=root, session=s, writer=writer)
    finally:
        writer.release()


@pytest.mark.parametrize(
    "symbol,multiplier,base",
    [
        ("SUI-USDC-SWAP", "0.1", "1"),
        ("ETH-USDC-SWAP", "0.01", "100"),
        ("BTC-USDC-SWAP", "1", "10000"),
    ],
)
@pytest.mark.parametrize("direction", [1, -1])
def test_long_short_open_partial_close_funding_fees_restart_without_double_count(
    tmp_path, symbol, multiplier, base, direction
):
    s = session(multiplier, symbol)
    cs = D(multiplier)
    slip = D(base) * D("0.0005")
    entry = D(base) + D(direction) * slip
    opened = fill(
        s,
        "open",
        "BUY" if direction == 1 else "SELL",
        "2",
        str(entry),
        base,
        fee="0.01",
        slip=str(2 * slip * cs),
        time=10,
    )
    result = s.apply_fill(opened)
    assert result.portfolio_state.fill_count == 1
    assert s.portfolio_state().equity == D("1000") - D("0.01") - 2 * slip * cs
    s.apply_funding_observation_v1(
        event_id="funding", amount="-0.002", currency="USDC", instrument_id=symbol
    )
    mark = D(base) + D(direction) * D(base) * D("0.1")
    s.mark_to_market(mark)
    expected_open = D(direction) * (mark - entry) * 2 * cs
    assert s.portfolio_state().equity == D("1000") + expected_open - D("0.012")
    persist(s, tmp_path)
    s = storage.load_accounting_session(tmp_path, require_present=True)
    before = s.portfolio_state().to_dict()
    assert s.apply_fill(opened).idempotent_replay
    assert s.apply_funding_observation_v1(
        event_id="funding", amount="-0.002", currency="USDC", instrument_id=symbol
    )["idempotent_replay"]
    assert s.portfolio_state().to_dict() == before
    s.apply_fill(
        fill(
            s,
            "partial",
            "SELL" if direction == 1 else "BUY",
            "1",
            str(mark),
            str(mark),
            fee="0.02",
            time=20,
        )
    )
    assert s.position.qty == 1 and s.position.fees_paid == D("0.03")
    assert s.portfolio_state().equity == D("1000") + expected_open - D("0.032")
    end = D(base) + D(direction) * D(base) * D("0.12")
    s.apply_fill(
        fill(
            s,
            "close",
            "SELL" if direction == 1 else "BUY",
            "1",
            str(end),
            str(end),
            fee="0.03",
            time=30,
        )
    )
    expected_gross = D(direction) * ((mark - entry) + (end - entry)) * cs
    assert s.position is None
    assert s.realized_pnl == expected_gross
    assert s.portfolio_state().equity == D("1000") + expected_gross - D("0.062")
    persist(s, tmp_path)
    assert (
        storage.load_accounting_session(tmp_path, require_present=True).portfolio_state().digest()
        == s.portfolio_state().digest()
    )


def test_many_cycles_and_periodic_restart_preserve_conservation_and_funding(tmp_path):
    s = session("0.01")
    for n in range(250):
        s.apply_fill(fill(s, f"open-{n}", "BUY", "1", "100", "100", fee="0.001", time=n * 2))
        s.apply_funding_observation_v1(
            event_id=f"funding-{n}",
            amount="-0.0005",
            currency="USDC",
            instrument_id=s.contract.symbol,
        )
        s.apply_fill(fill(s, f"close-{n}", "SELL", "1", "110", "110", fee="0.001", time=n * 2 + 1))
        if n % 25 == 0:
            persist(s, tmp_path)
            s = storage.load_accounting_session(tmp_path, require_present=True)
    assert s.portfolio_state().equity == D("1000") + 250 * D("0.0975")
    assert s.portfolio_state().fill_count == 500
    assert len(s.funding_events) == 250


def test_weighted_entry_is_not_rounded_to_a_tradable_tick_and_shell_cash_is_consistent():
    from src.ops.productive_futures_accounting_runtime_binding_v1.bridge_binding_v1 import (
        sync_portfolio_shell_from_accounting_v1,
    )
    from src.ops.integrated_paper_shadow_observation_session_v1.portfolio_economics_model_v1 import (
        SimulatedPortfolioEconomicsModelV1,
    )

    s = session()
    s.apply_fill(fill(s, "one", "BUY", "1", "100", "100", time=1))
    s.apply_fill(fill(s, "two", "BUY", "1", "100.01", "100.01", time=2))
    assert s.position.entry_price == D("100.005")
    assert s.portfolio_state().unrealized_pnl == D("0.001")
    s.apply_funding_observation_v1(
        event_id="f", amount="-0.0001", currency="USDC", instrument_id=s.contract.symbol
    )
    shell = SimulatedPortfolioEconomicsModelV1()
    sync_portfolio_shell_from_accounting_v1(shell, s)
    assert shell.state.cash == D("999.9999")
    assert shell.state.equity - shell.state.cash == D("0.001")
    assert shell.state.cumulative_funding == D("0.0001")


def test_failed_mark_keeps_last_consistent_position_snapshot():
    s = session()
    s.apply_fill(fill(s, "short", "SELL", "2", "100", "100"))
    before = s.to_durable_dict()
    with pytest.raises(ValueError):
        s.mark_to_market(D("1000000000"))
    assert s.to_durable_dict() == before


def test_accounting_checkpoint_reloads_idempotently_in_a_new_python_process(tmp_path):
    s = session()
    f = fill(s, "open", "BUY", "2", "100", "105", fee="0.01", time=1)
    s.apply_fill(f)
    s.apply_funding_observation_v1(
        event_id="funding", amount="-0.002", currency="USDC", instrument_id=s.contract.symbol
    )
    persist(s, tmp_path)
    source = tmp_path / "replay_input.json"
    source.write_text(json.dumps(f.to_dict()))
    code = """
import json,sys,socket
from decimal import Decimal
from pathlib import Path
from unittest.mock import patch
from src.ops.productive_futures_accounting_runtime_binding_v1.persistence_v1 import load_accounting_session
from src.ops.productive_futures_accounting_runtime_binding_v1.models_v1 import SimulatedFillInputV1
with patch.object(socket.socket,"connect",side_effect=AssertionError("network forbidden")):
    root=Path(sys.argv[1]);s=load_accounting_session(root,require_present=True)
    data=json.loads((root/"replay_input.json").read_text())
    for key in ("quantity","mark_price","fill_price","fee","slippage_cost","notional"):
        data[key]=Decimal(data[key])
    before=s.portfolio_state().digest()
    assert s.apply_fill(SimulatedFillInputV1(**data)).idempotent_replay
    assert s.apply_funding_observation_v1(event_id="funding",amount="-0.002",currency="USDC",instrument_id=s.contract.symbol)["idempotent_replay"]
    assert s.portfolio_state().digest()==before
    print(json.dumps({"digest":before,"funding_events":len(s.funding_events)}))
"""
    child = subprocess.run(
        [str(ROOT / "scripts/pt"), "-c", code, str(tmp_path)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    output = json.loads(child.stdout.splitlines()[-1])
    assert output == {"digest": s.portfolio_state().digest(), "funding_events": 1}


def test_unknown_instrument_is_rejected_even_before_first_position():
    s = session()
    f = replace(fill(s, "first", "BUY", "1", "100", "100"), instrument_id="UNKNOWN")
    with pytest.raises(AccountingEngineError, match="instrument_mismatch"):
        s.apply_fill(f)
    assert s.fill_order == [] and s.position is None


@pytest.mark.parametrize("defect", ["duplicate_conflict", "late", "instrument", "bad_fee"])
def test_invalid_fill_is_rejected_without_mutation(defect):
    s = session()
    opened = fill(s, "first", "BUY", "2", "100", "100", time=10)
    s.apply_fill(opened)
    before = s.to_durable_dict()
    bad = {
        "duplicate_conflict": replace(opened, fee=D("1")),
        "late": fill(s, "late", "SELL", "1", "100", "100", time=9),
        "instrument": replace(
            fill(s, "other", "BUY", "1", "100", "100", time=20), instrument_id="UNKNOWN"
        ),
        "bad_fee": fill(s, "bankrupt", "BUY", "1", "100", "100", fee="10000", time=20),
    }[defect]
    with pytest.raises((AccountingEngineError, ValueError)):
        s.apply_fill(bad)
    assert s.to_durable_dict() == before


def test_funding_conflict_unknown_currency_and_unknown_instrument_are_not_posted():
    s = session()
    s.apply_funding_observation_v1(
        event_id="f", amount="-0.01", currency="USDC", instrument_id=s.contract.symbol
    )
    before = s.to_durable_dict()
    for args in [
        dict(event_id="f", amount="-0.02", currency="USDC", instrument_id=s.contract.symbol),
        dict(event_id="new", amount="1", currency="EUR", instrument_id=s.contract.symbol),
        dict(event_id="new", amount="1", currency="USDC", instrument_id="UNKNOWN"),
    ]:
        with pytest.raises(AccountingEngineError):
            s.apply_funding_observation_v1(**args)
    assert s.to_durable_dict() == before


def test_corrupt_mixed_or_legacy_checkpoint_does_not_seed_default_capital(tmp_path):
    s = session(initial="0")
    persist(s, tmp_path)
    assert storage.load_accounting_session(tmp_path, require_present=True).initial_equity == 0
    state = tmp_path / storage.ACCOUNTING_STATE_FILENAME
    data = json.loads(state.read_text())
    del data["initial_equity"]
    state.write_text(json.dumps(data))
    with pytest.raises(storage.PersistenceInterruptionError):
        storage.load_accounting_session(tmp_path)
    persist(s, tmp_path)
    state.unlink()
    with pytest.raises(storage.PersistenceInterruptionError):
        storage.load_accounting_session(tmp_path)
    legacy = s.to_durable_dict()
    legacy.pop("checkpoint_version")
    with pytest.raises(AccountingEngineError, match="REQUIRES_EXPLICIT_REPLAY"):
        ProductiveFuturesAccountingSessionV1.from_durable_dict(legacy)


def test_interruption_during_publish_leaves_restart_blocked(tmp_path):
    s = session()
    persist(s, tmp_path)
    s.apply_fill(fill(s, "new", "BUY", "1", "100", "100"))
    original = storage._atomic_write_text

    def interrupted(path, text):
        if path.name == storage.PORTFOLIO_STATE_FILENAME:
            raise OSError("injected crash after accounting file")
        return original(path, text)

    with patch.object(storage, "_atomic_write_text", side_effect=interrupted):
        with pytest.raises(storage.PersistenceInterruptionError):
            persist(s, tmp_path)
    with pytest.raises(storage.PersistenceInterruptionError):
        storage.load_accounting_session(tmp_path, require_present=True)


def test_unknown_inverse_contract_not_silently_interpreted_as_linear():
    c = replace(session().contract, contract_type="inverse")
    with pytest.raises(AccountingEngineError, match="UNSUPPORTED_CONTRACT_TYPE"):
        ProductiveFuturesAccountingSessionV1(contract=c, initial_equity=D("1000"))


def test_unknown_restored_action_and_wrong_kernel_owner_are_rejected():
    s = session()
    s.apply_fill(fill(s, "one", "BUY", "1", "100", "100"))
    data = s.to_durable_dict()
    data["applied_fill_results"]["one"]["action_code"] = "UNKNOWN_EVENT"
    with pytest.raises(ValueError, match="UNKNOWN_ACTION"):
        ProductiveFuturesAccountingSessionV1.from_durable_dict(data)
    data = s.to_durable_dict()
    data["kernel_owner"] = "other-owner"
    with pytest.raises(ValueError, match="OWNER_MISMATCH"):
        ProductiveFuturesAccountingSessionV1.from_durable_dict(data)


def test_internal_comparison_rule_accepts_declared_rendering_without_runtime_authority():
    policy = load_equity_verification_policy_v1(
        ROOT / "config/ops/equity_verification_policy_v1.json"
    )
    result = reconcile_real_equity_window_v1(*fixture())
    result["initial_equity_display_comparison"] = compare_native_display_v1(
        D("725.4691081539303132"), "725.4691081539303"
    )
    assessment = assess_equity_window_v1(result, policy)
    assert assessment["status"] == "LOCAL_VERIFICATION_PASS_RUNTIME_BLOCKED"
    assert not assessment["runtime_activation_authorized"] and not assessment["capital_admitted"]
    # A nearby decimal that is not the declared rendering is not accepted.
    result["initial_equity_display_comparison"] = compare_native_display_v1(
        D("725.4691081539303132"), "725.46910815393031"
    )
    assert assess_equity_window_v1(result, policy)["blockers"]
    result["initial_equity_display_comparison"] = compare_native_display_v1(
        D("10000000000000001"), "10000000000000000"
    )
    assert (
        "UNEXPLAINED_OR_EXCESSIVE_DISPLAY_GAP:OPENING_EQUITY:USDC"
        in assess_equity_window_v1(result, policy)["blockers"]
    )


def test_unexplained_funding_residual_is_not_accepted_as_a_small_display_gap():
    policy = load_equity_verification_policy_v1(
        ROOT / "config/ops/equity_verification_policy_v1.json"
    )
    result = reconcile_real_equity_window_v1(*fixture())
    result["funding"]["currency_balances"][0]["observed_minus_replayed"] = "0.00000000000001"
    assert (
        "FUNDING_RESIDUAL_NOT_EXPLAINED_BY_COUNTERPARTS"
        in assess_equity_window_v1(result, policy)["blockers"]
    )


@pytest.mark.parametrize(
    "key,value",
    [
        ("runtime_activation_authorized", True),
        ("capital_admission_authorized", True),
        ("ledger_adjustments_allowed", True),
    ],
)
def test_local_verification_policy_cannot_enable_money(tmp_path, key, value):
    policy = json.loads((ROOT / "config/ops/equity_verification_policy_v1.json").read_text())
    policy[key] = value
    path = tmp_path / "policy.json"
    path.write_text(json.dumps(policy))
    with pytest.raises(ValueError):
        load_equity_verification_policy_v1(path)
