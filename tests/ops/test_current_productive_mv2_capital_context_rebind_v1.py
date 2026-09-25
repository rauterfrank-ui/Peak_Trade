"""MV2 capital_context rebind from typed 29P producer equity."""

from __future__ import annotations

from decimal import Decimal

import pytest

from src.ops.decision_config_ownership_and_consumer_closure_v1.canonical_values_v1 import (
    CANONICAL_ADVERSE_EXIT_DISTANCE,
)
from src.governance.capital_risk_sizing_v1 import InstrumentQuantityConstraintsV1
from src.ops.full_core_live_path_composition_root_v1.current_productive_mv2_capital_context_rebind_v1 import (
    CURRENT_PRODUCTIVE_MV2_CAPITAL_CONTEXT_REBIND_V1_CREATED,
    PRODUCTIVE_CAPITAL_RISK_LIMITS_FROM_TYPED_29P_EQUITY_LINEAGE_REF_V1,
    REBIND_SEAM_ID,
    build_current_productive_live_account_capital_context_v1,
    resolve_productive_capital_risk_limits_from_29p_producer_v1,
)
from trading.master_v2.capital_risk_sizing_historical_default_deauthorization_v1 import (
    ISOLATED_OFFLINE_REPLAY_FIXTURE_ACCOUNT_EQUITY,
    ISOLATED_OFFLINE_REPLAY_FIXTURE_PER_TRADE_RISK_LIMIT,
    ISOLATED_OFFLINE_REPLAY_FIXTURE_SCOPE_CAPITAL_LIMIT,
    REASON_PRODUCTIVE_CAPITAL_RISK_LIMITS_UNRESOLVED,
)
from trading.master_v2.capital_risk_sizing_offline_replay_binding_adapter_v0 import (
    CAPITAL_RISK_MODE_LIVE_ACCOUNT_BOUND,
    derive_protective_stop_price_from_adverse_exit_v0,
)


def test_created_flag_and_lineage() -> None:
    assert CURRENT_PRODUCTIVE_MV2_CAPITAL_CONTEXT_REBIND_V1_CREATED is True
    assert REBIND_SEAM_ID == "CURRENT_PRODUCTIVE_MV2_CAPITAL_CONTEXT_REBIND_SEAM_V1"
    assert "resolve_productive_capital_risk_limits_from_29p_producer_v1" in (
        PRODUCTIVE_CAPITAL_RISK_LIMITS_FROM_TYPED_29P_EQUITY_LINEAGE_REF_V1
    )


def test_limits_from_typed_equity_not_historical_fixture_literals() -> None:
    equity = Decimal("100.00")
    limits = resolve_productive_capital_risk_limits_from_29p_producer_v1(
        typed_account_equity=equity,
    )
    assert limits is not None
    assert limits.scope_capital_limit == equity
    assert limits.per_trade_risk_limit == equity
    assert limits.scope_capital_limit != ISOLATED_OFFLINE_REPLAY_FIXTURE_SCOPE_CAPITAL_LIMIT
    assert limits.per_trade_risk_limit != ISOLATED_OFFLINE_REPLAY_FIXTURE_PER_TRADE_RISK_LIMIT


def _fixture_constraints(instrument_id: str = "inst-eth-usdt-perp") -> InstrumentQuantityConstraintsV1:
    return InstrumentQuantityConstraintsV1(
        instrument_id=instrument_id,
        market_type="futures",
        contract_kind="LINEAR",
        contract_multiplier=Decimal("0.01"),
        lot_size=Decimal("1"),
        minimum_quantity=Decimal("1"),
        maximum_quantity=None,
        minimum_notional=None,
        tick_size=Decimal("0.01"),
        instrument_metadata_version="test-metadata-version-v1",
    )


def test_build_live_account_bound_context() -> None:
    mark = Decimal("1630")
    stop = derive_protective_stop_price_from_adverse_exit_v0(
        selected_side="long",
        reference_price=mark,
        adverse_exit_distance=CANONICAL_ADVERSE_EXIT_DISTANCE,
    )
    assert stop is not None
    ctx = build_current_productive_live_account_capital_context_v1(
        instrument_id="inst-eth-usdt-perp",
        typed_account_equity=Decimal("777.77"),
        reference_price=mark,
        protective_stop_price=stop,
        instrument_constraints=_fixture_constraints(),
    )
    assert ctx.capital_risk_mode == CAPITAL_RISK_MODE_LIVE_ACCOUNT_BOUND
    assert ctx.account_equity == Decimal("777.77")
    assert ctx.account_equity != ISOLATED_OFFLINE_REPLAY_FIXTURE_ACCOUNT_EQUITY
    assert ctx.scope_capital_limit == Decimal("777.77")
    assert ctx.instrument.maximum_quantity is None
    assert ctx.instrument.instrument_metadata_version == "test-metadata-version-v1"


def test_non_positive_equity_fail_closed() -> None:
    assert (
        resolve_productive_capital_risk_limits_from_29p_producer_v1(
            typed_account_equity=Decimal("0")
        )
        is None
    )
    with pytest.raises(Exception, match=REASON_PRODUCTIVE_CAPITAL_RISK_LIMITS_UNRESOLVED):
        build_current_productive_live_account_capital_context_v1(
            instrument_id="inst-eth-usdt-perp",
            typed_account_equity=Decimal("-1"),
            reference_price=Decimal("100"),
            protective_stop_price=Decimal("50"),
            instrument_constraints=_fixture_constraints(),
        )
