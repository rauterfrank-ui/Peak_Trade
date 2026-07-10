"""Contract tests for ehlers_cycle_filter/v1 offline baseline materialization v0."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pytest

from src.backtest.engine import BacktestEngine
from src.backtest.step29m_macd_v1_economic_evaluation_admissibility_contract_v1 import (
    compute_evaluation_config_digest_v1,
)
from src.research.step29m_ehlers_cycle_filter_v1_offline_economic_baseline_materialization_v0 import (
    IMPLEMENTATION_SURFACE_PATHS,
    compute_step29m_ehlers_implementation_digest_v0,
    materialize_legacy_backtest_accounting_reconciliation_v0,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
EVAL_CONFIG = (
    REPO_ROOT
    / "config/ops/step29m_okx_inst_eth_usdt_perp_ehlers_cycle_filter_v1_economic_evaluation_v1.json"
)
PRIOR_IMPLEMENTATION_DIGEST = "a153ea4fc624ed3e00fbcd38006c361b05ddeab473344c5181efa79372962702"


def test_implementation_digest_changes_after_defect_repair_surfaces() -> None:
    digest = compute_step29m_ehlers_implementation_digest_v0(REPO_ROOT)
    assert digest != PRIOR_IMPLEMENTATION_DIGEST
    assert len(digest) == 64


def test_config_and_strategy_params_digests_unchanged_on_main_config() -> None:
    cfg = json.loads(EVAL_CONFIG.read_text(encoding="utf-8"))
    assert (
        compute_evaluation_config_digest_v1(cfg)
        == "c4db0a42b95156192d8c1fcf486aa3d616ae2f0b5dafa26b9e0d7d9a29c204a6"
    )
    assert cfg["offline_evaluation_sizing_contract_v1"]["strategy_params_digest"] == (
        "49f8b07e7de872e66f74dd27b5e97a3ae3aaee414e25d3b08cba2674c40cc5b9"
    )


def test_materializer_uses_canonical_accounting_owner_fields() -> None:
    index = pd.date_range("2024-01-01", periods=3, freq="1h", tz="UTC")
    closes = [100.0, 101.0, 105.0]
    df = pd.DataFrame(
        {
            "open": closes,
            "high": [c + 1.0 for c in closes],
            "low": [c - 1.0 for c in closes],
            "close": closes,
            "volume": [1000.0] * len(closes),
        },
        index=index,
    )

    def strategy_fn(_df: pd.DataFrame, _params: dict) -> pd.Series:
        signals = pd.Series(0, index=_df.index, dtype=int)
        signals.iloc[1] = 1
        return signals

    engine = BacktestEngine(use_execution_pipeline=False)
    engine.config = {
        "backtest": {"initial_cash": 10_000.0, "fee_bps": 0.0, "slippage_bps": 0.0},
        "risk": {
            "risk_per_trade": 0.01,
            "max_position_size": 0.25,
            "min_position_value": 50.0,
            "min_stop_distance": 0.001,
        },
    }
    result = engine.run_realistic(
        df=df,
        strategy_signal_fn=strategy_fn,
        strategy_params={"stop_pct": 0.5},
        fee_bps=0.0,
        slippage_bps=0.0,
        explicit_zero_cost_non_economic=True,
    )
    payload = materialize_legacy_backtest_accounting_reconciliation_v0(
        result,
        initial_cash=10_000.0,
    )
    assert payload["schema_version"] == "cross_sectional_single_slot_accounting_reconciliation.v0"
    assert payload["accounting_reconciliation_pass"] is True
    assert payload["failure_class"] is None


def test_implementation_surface_paths_exist() -> None:
    for rel in IMPLEMENTATION_SURFACE_PATHS:
        assert (REPO_ROOT / rel).is_file()
