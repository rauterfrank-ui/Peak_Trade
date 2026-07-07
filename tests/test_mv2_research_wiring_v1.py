"""MV2 research wiring v1: canonical order intent backtest state-file integration."""

from __future__ import annotations

import json
from pathlib import Path

from src.backtest.mv2_research_wiring_v1 import (
    CanonicalOrderIntentBacktestStateFileBindingConfigV1,
    CapitalRiskSizingBacktestStateFileBindingConfigV1,
    run_mv2_research_backtest_wiring_v1,
)
from src.governance.canonical_order_intent_v1 import (
    CONTRACT_VERSION as CANONICAL_ORDER_INTENT_CONTRACT_VERSION,
)
from src.governance.capital_risk_sizing_v1 import (
    CONTRACT_VERSION as CAPITAL_RISK_SIZING_CONTRACT_VERSION,
)
from trading.master_v2.canonical_order_intent_boundary_backtest_state_file_binding_adapter_v0 import (
    CANONICAL_ORDER_INTENT_BOUNDARY_BACKTEST_STATE_FILE_SCHEMA_VERSION,
    compute_backtest_state_file_digest_from_payload_v0,
)
from trading.master_v2.capital_risk_sizing_boundary_backtest_state_file_binding_adapter_v0 import (
    CAPITAL_RISK_SIZING_BOUNDARY_BACKTEST_STATE_FILE_SCHEMA_VERSION,
    compute_backtest_state_file_digest_from_payload_v0 as sizing_digest,
)
from tests.backtest.test_mv2_research_wiring_v1 import _bars, _cfg


def _sizing_payload() -> dict[str, object]:
    base = {
        "schema_version": CAPITAL_RISK_SIZING_BOUNDARY_BACKTEST_STATE_FILE_SCHEMA_VERSION,
        "instrument_id": "inst-eth-usdt-perp",
        "reference_price": "3500",
        "protective_stop_price": "3400",
        "account_equity": "10000",
        "scope_capital_limit": "500",
        "per_trade_risk_limit": "25",
        "total_capital_limit": "500",
        "daily_loss_remaining_budget": "25",
        "current_reconciled_exposure": "0",
        "lot_size": "0.01",
        "minimum_quantity": "0.01",
        "maximum_quantity": "100",
        "minimum_notional": "5",
        "tick_size": "0.01",
        "capital_risk_sizing_owner_digest_ref": CAPITAL_RISK_SIZING_CONTRACT_VERSION,
    }
    return {**base, "state_file_digest_ref": sizing_digest(base)}


def _order_intent_payload() -> dict[str, object]:
    base = {
        "schema_version": CANONICAL_ORDER_INTENT_BOUNDARY_BACKTEST_STATE_FILE_SCHEMA_VERSION,
        "instrument_id": "inst-eth-usdt-perp",
        "reference_price": "3500",
        "protective_stop_price": "3400",
        "account_equity": "10000",
        "scope_capital_limit": "500",
        "per_trade_risk_limit": "25",
        "total_capital_limit": "500",
        "daily_loss_remaining_budget": "25",
        "current_reconciled_exposure": "0",
        "lot_size": "0.01",
        "minimum_quantity": "0.01",
        "maximum_quantity": "100",
        "minimum_notional": "5",
        "tick_size": "0.01",
        "canonical_order_intent_owner_digest_ref": CANONICAL_ORDER_INTENT_CONTRACT_VERSION,
    }
    return {
        **base,
        "state_file_digest_ref": compute_backtest_state_file_digest_from_payload_v0(base),
    }


def test_mv2_wiring_reuses_existing_backtest_matrix_v0() -> None:
    from tests.backtest import test_mv2_research_wiring_v1 as core

    core.test_matrix_23_end_to_end_returns_signal_series()


def test_mv2_wiring_canonical_order_intent_chain_v0(tmp_path: Path) -> None:
    sizing_payload = _sizing_payload()
    sizing_path = tmp_path / "capital_risk_sizing_backtest_state.json"
    sizing_path.write_text(json.dumps(sizing_payload, indent=2), encoding="utf-8")

    intent_payload = _order_intent_payload()
    intent_path = tmp_path / "canonical_order_intent_backtest_state.json"
    intent_path.write_text(json.dumps(intent_payload, indent=2), encoding="utf-8")

    result = run_mv2_research_backtest_wiring_v1(
        _bars(n=6),
        strategy_id="ma_crossover",
        cfg=_cfg(),
        explicit_zero_cost_non_economic=True,
        capital_risk_sizing_state_file_binding=CapitalRiskSizingBacktestStateFileBindingConfigV1(
            state_file_path=sizing_path,
            expected_state_file_digest_ref=str(sizing_payload["state_file_digest_ref"]),
        ),
        canonical_order_intent_state_file_binding=CanonicalOrderIntentBacktestStateFileBindingConfigV1(
            state_file_path=intent_path,
            expected_state_file_digest_ref=str(intent_payload["state_file_digest_ref"]),
        ),
    )
    assert all(
        o.capital_risk_sizing_backtest_state_file_evidence is not None for o in result.bar_outcomes
    )
    assert all(
        o.canonical_order_intent_backtest_state_file_evidence is not None
        for o in result.bar_outcomes
    )
