"""Candidate original TESTNET host: synthetic observations, no transport or orders."""

from dataclasses import replace
from decimal import Decimal

import pytest

from src.ops.portfolio_capital_reservation_budget_v1.host_v1 import PortfolioBudgetHostV1
from src.ops.portfolio_capital_reservation_budget_v1.slot_loss_budget_v1 import (
    SlotCapitalAllocationV1,
)
from tests.ops.test_btc_demo_budget_reconciliation_host_v1 import ACCOUNT, BINDINGS, NOW, capital
from tests.ops.test_current_usdc_xperp_financial_admission_v1 import policy as financial_policy
from tests.ops.test_portfolio_budget_host_v1 import _fetch
from tests.ops.test_closing_execution_cost_provision_v1 import no_network as no_network


def policy():
    return replace(
        financial_policy(),
        allowed_slot_ids=("LANE_3",),
        aggregate_reserved_notional_limit=Decimal(25),
    )


def host(root, *, create=True, entry_policy=None):
    return PortfolioBudgetHostV1(
        root=root,
        private_rest_fetch=_fetch(uid=ACCOUNT),
        repository_sha="explicit-offline-candidate",
        session_id="testnet-original-host",
        expected_account_identity=ACCOUNT,
        durable_mode="create" if create else "recover",
        clock=NOW.timestamp,
        execution_environment="TESTNET",
        entry_budget_policy=entry_policy or policy(),
        slot_capital_allocation=SlotCapitalAllocationV1(
            ACCOUNT, "explicit-test-allocation", (("LANE_3", Decimal(25)),)
        )
        if create
        else None,
    )


def test_original_host_reopens_testnet_and_retains_the_once_funded_allocation(tmp_path):
    root = tmp_path / "budget-owner"
    original = host(root)
    try:
        ctx = original.observe_v1(BINDINGS)
        assert original.owner.execution_environment_v1() == "TESTNET"
        ctx.recover_v1(original.owner, capital())
        allocation = original.owner.risk_snapshot_v1()["state"]["slot_capital_allocation"]
        assert allocation["funding"] is not None
        assert original.owner.slot_capital_basis_v1("LANE_3").initial_usdc == Decimal(25)
    finally:
        original.close()
    reopened = host(root, create=False)
    try:
        ctx = reopened.observe_v1(BINDINGS)
        assert reopened.owner.budget_state_v1().recovery_required
        ctx.recover_v1(reopened.owner, capital())
        assert reopened.owner.budget_state_v1().admitted
        assert reopened.owner.risk_snapshot_v1()["state"]["slot_capital_allocation"] == allocation
    finally:
        reopened.close()


@pytest.mark.parametrize("fault", ["slot", "instrument"])
def test_testnet_scope_refuses_another_lane_or_native_before_journal_creation(tmp_path, fault):
    candidate = host(tmp_path / "budget-owner")
    bindings = (
        {"LANE_2": BINDINGS["LANE_3"]}
        if fault == "slot"
        else {"LANE_3": replace(BINDINGS["LANE_3"], venue_native_id="ETH-USDT-SWAP")}
    )
    try:
        with pytest.raises(ValueError, match="BTC_TESTNET_BOUND_LANE_AND_INSTRUMENT_REQUIRED"):
            candidate.observe_v1(bindings)
        assert candidate.owner is None
        assert not (candidate.root / "owner").exists()
    finally:
        candidate.close()


@pytest.mark.parametrize("fault", ["budget", "settlement", "loss"])
def test_testnet_policy_refuses_a_different_budget_or_missing_cash_guards(tmp_path, fault):
    settings = {
        "budget": dict(
            per_entry_notional_limit=Decimal(26),
            per_slot_reserved_notional_limit=Decimal(26),
            aggregate_reserved_notional_limit=Decimal(26),
        ),
        "settlement": dict(require_usdc_settlement=False),
        "loss": dict(per_slot_test_loss_limit=Decimal(24)),
    }[fault]
    reason = (
        "TEST_PHASE_SLOT_LOSS_LIMIT_MUST_BE_25_USDC"
        if fault == "loss"
        else "BTC_TESTNET_BOUNDED_POLICY_REQUIRED"
    )
    with pytest.raises(ValueError, match=reason):
        host(tmp_path / "budget-owner", entry_policy=replace(policy(), **settings))
    assert not (tmp_path / "budget-owner").exists()


def test_testnet_cannot_bootstrap_from_a_live_allocation(tmp_path):
    from src.ops.portfolio_capital_reservation_budget_v1.contract_v1 import (
        PortfolioCapitalReservationBudgetOwnerV1,
        PortfolioCapitalBudgetError,
    )

    with pytest.raises(PortfolioCapitalBudgetError, match="TESTNET_LIVE_ALLOCATION_FORBIDDEN"):
        PortfolioCapitalReservationBudgetOwnerV1(
            durable_root=tmp_path / "owner",
            durable_account_identity=ACCOUNT,
            durable_mode="create",
            durable_lane_bindings=BINDINGS,
            execution_environment="TESTNET",
            live_slot_capital_allocation=SlotCapitalAllocationV1(
                ACCOUNT, "explicit-live-fixture", (("LANE_3", Decimal(25)),)
            ),
        )
    assert not (tmp_path / "owner").exists()
