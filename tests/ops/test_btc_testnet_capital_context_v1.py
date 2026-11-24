"""Candidate TESTNET capital semantics, original producer and synthetic GETs."""

from decimal import Decimal

import pytest

from src.ops.btc_demo_entry_financial_inputs_v1 import build_btc_demo_capital_inputs_v1
from src.ops.full_core_live_path_composition_root_v1.current_productive_mv2_capital_context_rebind_v1 import (
    build_current_productive_account_capital_context_v1,
    build_current_productive_live_account_capital_context_v1,
)
from tests.ops.test_btc_demo_entry_reservation_v1 import demo_entry as demo_entry
from tests.ops.test_btc_testnet_net_reversal_cost_v1 import prepared
from tests.ops.test_closing_execution_cost_provision_v1 import no_network as no_network


def test_original_context_keeps_typed_equity_and_distinguishes_live_and_testnet(demo_entry):
    _, args, _ = prepared(demo_entry)
    applied = args["applied_input"]
    inputs = dict(
        instrument_id=applied.instrument_id,
        typed_account_equity=Decimal("23.75"),
        reference_price=applied.reference_price,
        protective_stop_price=applied.protective_stop_price,
        instrument_constraints=applied.instrument,
    )
    live = build_current_productive_live_account_capital_context_v1(**inputs)
    explicit_live = build_current_productive_account_capital_context_v1(
        **inputs, execution_environment="LIVE"
    )
    testnet = build_current_productive_account_capital_context_v1(
        **inputs, execution_environment="TESTNET"
    )
    assert live == explicit_live
    assert live.capital_risk_mode == "LIVE_ACCOUNT_BOUND"
    assert testnet.capital_risk_mode == "TESTNET_ACCOUNT_BOUND"
    assert testnet.config_digest != live.config_digest
    assert (
        testnet.account_equity
        == testnet.scope_capital_limit
        == testnet.total_capital_limit
        == Decimal("23.75")
    )
    with pytest.raises(RuntimeError, match="ACCOUNT_CAPITAL_ENVIRONMENT_INVALID"):
        build_current_productive_account_capital_context_v1(**inputs, execution_environment="PAPER")


def test_continuation_input_can_use_lower_free_margin_without_reallocating_25(demo_entry):
    host, entry, reads, _, instant, payloads = demo_entry
    for detail in payloads["balance"]["data"][0]["details"]:
        if detail["ccy"] == "USDC":
            detail["availEq"] = "23.75"
    before = host.budget.budget_revision_ref_v1()
    batch = host.inspect_testnet_pretrade_sources_v1(
        entry=entry, reads=reads, clock=instant.timestamp
    )
    inputs = dict(
        account=host.budget.account,
        epoch=entry.cycle.replay.intermediate.market_context.decision_time,
        now=instant.isoformat(),
        config=payloads["account"]["data"][0],
    )
    with pytest.raises(ValueError, match="DECLARED_BUDGET_UNCOVERED"):
        build_btc_demo_capital_inputs_v1(batch["sources"], **inputs)
    _, output, _, _ = build_btc_demo_capital_inputs_v1(
        batch["sources"],
        minimum_available=Decimal(0),
        **inputs,
    )
    assert Decimal(output.value) == Decimal("23.75")
    assert host.budget.budget_revision_ref_v1() == before
    assert host.budget.owner.stored_reservation_count_v1() == 0
