"""29P capital-risk mode/provenance: Integrated Replay is OFFLINE_ALGEBRA only."""

from __future__ import annotations

from decimal import Decimal

import pytest

from trading.master_v2.capital_risk_sizing_historical_default_deauthorization_v1 import (
    ISOLATED_OFFLINE_REPLAY_FIXTURE_ACCOUNT_EQUITY,
    REASON_CAPITAL_RISK_CONTEXT_UNRESOLVED,
)
from trading.master_v2.capital_risk_sizing_offline_replay_binding_adapter_v0 import (
    CAPITAL_RISK_MODE_LIVE_ACCOUNT_BOUND,
    CAPITAL_RISK_MODE_OFFLINE_ALGEBRA,
    isolated_offline_replay_fixture_capital_context_v0,
)
from trading.master_v2.integrated_offline_trading_logic_replay_v1 import (
    run_integrated_offline_trading_logic_replay_v1,
)
from tests.trading.master_v2.test_master_v2_integrated_replay_safety_before_intent_restore_contract_v1 import (
    _confirmed_replay_input,
    _patch_replay_owners,
)


def test_isolated_fixture_context_is_offline_algebra_not_current_authority() -> None:
    ctx = isolated_offline_replay_fixture_capital_context_v0(instrument_id="ETH-USDT-SWAP")
    assert ctx.capital_risk_mode == CAPITAL_RISK_MODE_OFFLINE_ALGEBRA
    assert ctx.account_equity == ISOLATED_OFFLINE_REPLAY_FIXTURE_ACCOUNT_EQUITY


def test_integrated_replay_without_boundary_fail_closed_sizing_context(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _patch_replay_owners(monkeypatch)
    replay = run_integrated_offline_trading_logic_replay_v1(_confirmed_replay_input(side="LONG"))
    assert replay.capital_risk_mode == CAPITAL_RISK_MODE_OFFLINE_ALGEBRA
    assert replay.intermediate is not None
    assert replay.intermediate.capital_risk_mode == CAPITAL_RISK_MODE_OFFLINE_ALGEBRA
    assert replay.capital_risk_mode != CAPITAL_RISK_MODE_LIVE_ACCOUNT_BOUND
    assert REASON_CAPITAL_RISK_CONTEXT_UNRESOLVED in replay.evidence.reason_codes


def test_offline_algebra_is_not_live_account_bound_token() -> None:
    assert CAPITAL_RISK_MODE_OFFLINE_ALGEBRA != CAPITAL_RISK_MODE_LIVE_ACCOUNT_BOUND
