"""29P capital-risk mode/provenance: Integrated Replay is OFFLINE_ALGEBRA only."""

from __future__ import annotations

from decimal import Decimal

import pytest

from trading.master_v2.capital_risk_sizing_offline_replay_binding_adapter_v0 import (
    CAPITAL_RISK_MODE_LIVE_ACCOUNT_BOUND,
    CAPITAL_RISK_MODE_OFFLINE_ALGEBRA,
    default_offline_replay_capital_context_v0,
)
from trading.master_v2.integrated_offline_trading_logic_replay_v1 import (
    run_integrated_offline_trading_logic_replay_v1,
)
from tests.trading.master_v2.test_master_v2_integrated_replay_safety_before_intent_restore_contract_v1 import (
    _confirmed_replay_input,
    _patch_replay_owners,
)


def test_default_offline_context_is_offline_algebra_with_unchanged_numeric_defaults() -> None:
    ctx = default_offline_replay_capital_context_v0(instrument_id="ETH-USDT-SWAP")
    assert ctx.capital_risk_mode == CAPITAL_RISK_MODE_OFFLINE_ALGEBRA
    assert ctx.account_equity == Decimal("10000")
    assert ctx.scope_capital_limit == Decimal("500")
    assert ctx.per_trade_risk_limit == Decimal("25")
    assert ctx.total_capital_limit == Decimal("500")
    assert ctx.daily_loss_remaining_budget == Decimal("25")
    assert ctx.reference_price == Decimal("3500")
    assert ctx.protective_stop_price == Decimal("3400")


def test_integrated_replay_emits_offline_algebra_mode(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _patch_replay_owners(monkeypatch)
    replay = run_integrated_offline_trading_logic_replay_v1(_confirmed_replay_input(side="LONG"))
    assert replay.capital_risk_mode == CAPITAL_RISK_MODE_OFFLINE_ALGEBRA
    assert replay.intermediate is not None
    assert replay.intermediate.capital_risk_mode == CAPITAL_RISK_MODE_OFFLINE_ALGEBRA
    assert replay.capital_risk_mode != CAPITAL_RISK_MODE_LIVE_ACCOUNT_BOUND


def test_offline_algebra_is_not_live_account_bound_token() -> None:
    assert CAPITAL_RISK_MODE_OFFLINE_ALGEBRA != CAPITAL_RISK_MODE_LIVE_ACCOUNT_BOUND
