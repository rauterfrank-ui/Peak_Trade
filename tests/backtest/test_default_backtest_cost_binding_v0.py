"""RUNBOOK STEP 29J — default backtest economic realism cost binding tests."""

from __future__ import annotations

import copy
import math
from typing import Any, Dict

import numpy as np
import pandas as pd
import pytest

from src.backtest.cost_config_v0 import (
    BacktestCostConfigError,
    EffectiveBacktestCostConfigV0,
    REASON_EXPLICIT_ZERO_COST,
    compute_cost_config_digest,
    resolve_effective_backtest_cost_config,
)
from src.backtest.engine import BacktestEngine


def _minimal_cfg() -> Dict[str, Any]:
    return {
        "backtest": {
            "initial_cash": 10_000.0,
            "cost_model_version": "backtest_cost_v0",
            "fee_bps": 10.0,
            "slippage_bps": 5.0,
        },
        "risk": {
            "risk_per_trade": 0.02,
            "max_position_size": 0.25,
        },
    }


def _ohlcv(n: int = 80) -> pd.DataFrame:
    np.random.seed(7)
    idx = pd.date_range("2024-01-01", periods=n, freq="1h", tz="UTC")
    close = 100.0 + np.cumsum(np.random.normal(0, 0.2, n))
    df = pd.DataFrame(
        {
            "open": close,
            "high": close + 0.5,
            "low": close - 0.5,
            "close": close,
            "volume": np.full(n, 100.0),
        },
        index=idx,
    )
    return df


def _signal_fn(df: pd.DataFrame, params: dict) -> pd.Series:
    fast = int(params.get("fast_period", 3))
    slow = int(params.get("slow_period", 8))
    ma_fast = df["close"].rolling(fast).mean()
    ma_slow = df["close"].rolling(slow).mean()
    sig = pd.Series(0, index=df.index)
    sig[ma_fast > ma_slow] = 1
    sig[ma_fast < ma_slow] = -1
    return sig.fillna(0)


class TestCostConfigResolver:
    def test_standard_config_binding_non_zero(self) -> None:
        cfg = resolve_effective_backtest_cost_config(_minimal_cfg())
        assert cfg.taker_fee_bps == 10.0
        assert cfg.entry_slippage_bps == 5.0
        assert cfg.zero_cost_explicitly_requested is False
        assert cfg.config_digest

    def test_missing_backtest_section_fail_closed(self) -> None:
        with pytest.raises(BacktestCostConfigError):
            resolve_effective_backtest_cost_config({})

    def test_missing_fee_key_fail_closed(self) -> None:
        cfg = _minimal_cfg()
        del cfg["backtest"]["fee_bps"]
        with pytest.raises(BacktestCostConfigError):
            resolve_effective_backtest_cost_config(cfg)

    def test_missing_slippage_key_fail_closed(self) -> None:
        cfg = _minimal_cfg()
        del cfg["backtest"]["slippage_bps"]
        with pytest.raises(BacktestCostConfigError):
            resolve_effective_backtest_cost_config(cfg)

    def test_none_fee_fail_closed(self) -> None:
        cfg = _minimal_cfg()
        cfg["backtest"]["fee_bps"] = None
        with pytest.raises(BacktestCostConfigError):
            resolve_effective_backtest_cost_config(cfg)

    def test_none_slippage_fail_closed(self) -> None:
        cfg = _minimal_cfg()
        cfg["backtest"]["slippage_bps"] = None
        with pytest.raises(BacktestCostConfigError):
            resolve_effective_backtest_cost_config(cfg)

    def test_negative_fee_fail_closed(self) -> None:
        cfg = _minimal_cfg()
        cfg["backtest"]["fee_bps"] = -1.0
        with pytest.raises(BacktestCostConfigError):
            resolve_effective_backtest_cost_config(cfg)

    def test_negative_slippage_fail_closed(self) -> None:
        cfg = _minimal_cfg()
        cfg["backtest"]["slippage_bps"] = -1.0
        with pytest.raises(BacktestCostConfigError):
            resolve_effective_backtest_cost_config(cfg)

    @pytest.mark.parametrize("bad", [float("nan"), float("inf")])
    def test_non_finite_fail_closed(self, bad: float) -> None:
        cfg = _minimal_cfg()
        cfg["backtest"]["fee_bps"] = bad
        with pytest.raises(BacktestCostConfigError):
            resolve_effective_backtest_cost_config(cfg)

    def test_cli_override_applied_and_provenance(self) -> None:
        cfg = resolve_effective_backtest_cost_config(_minimal_cfg(), cli_fee_bps=15.0)
        assert cfg.taker_fee_bps == 15.0
        assert cfg.override_source == "explicit_cli_override"
        assert cfg.override_digest
        assert len(cfg.override_provenance) == 1

    def test_cli_slippage_override(self) -> None:
        cfg = resolve_effective_backtest_cost_config(_minimal_cfg(), cli_slippage_bps=8.0)
        assert cfg.entry_slippage_bps == 8.0

    def test_cli_beats_config(self) -> None:
        base = resolve_effective_backtest_cost_config(_minimal_cfg())
        over = resolve_effective_backtest_cost_config(_minimal_cfg(), cli_fee_bps=20.0)
        assert over.taker_fee_bps == 20.0
        assert over.taker_fee_bps != base.taker_fee_bps

    def test_run_config_override(self) -> None:
        cfg = resolve_effective_backtest_cost_config(
            _minimal_cfg(), run_config_fee_bps=12.0, run_config_slippage_bps=6.0
        )
        assert cfg.taker_fee_bps == 12.0
        assert cfg.entry_slippage_bps == 6.0

    def test_cli_beats_run_config(self) -> None:
        cfg = resolve_effective_backtest_cost_config(
            _minimal_cfg(),
            run_config_fee_bps=12.0,
            cli_fee_bps=18.0,
        )
        assert cfg.taker_fee_bps == 18.0

    def test_explicit_zero_cost_non_economic(self) -> None:
        cfg = resolve_effective_backtest_cost_config(
            _minimal_cfg(), explicit_zero_cost_non_economic=True
        )
        assert cfg.taker_fee_bps == 0.0
        assert cfg.entry_slippage_bps == 0.0
        assert cfg.economic_interpretation_allowed is False
        assert REASON_EXPLICIT_ZERO_COST in cfg.reason_codes

    def test_implicit_zero_cost_forbidden(self) -> None:
        cfg = _minimal_cfg()
        cfg["backtest"]["fee_bps"] = 0.0
        cfg["backtest"]["slippage_bps"] = 0.0
        with pytest.raises(BacktestCostConfigError):
            resolve_effective_backtest_cost_config(cfg)

    def test_config_digest_changes_with_cost(self) -> None:
        a = resolve_effective_backtest_cost_config(_minimal_cfg())
        b_cfg = _minimal_cfg()
        b_cfg["backtest"]["fee_bps"] = 11.0
        b = resolve_effective_backtest_cost_config(b_cfg)
        assert a.config_digest != b.config_digest

    def test_override_digest_changes_with_override(self) -> None:
        a = resolve_effective_backtest_cost_config(_minimal_cfg(), cli_fee_bps=11.0)
        b = resolve_effective_backtest_cost_config(_minimal_cfg(), cli_fee_bps=12.0)
        assert a.override_digest != b.override_digest

    def test_funding_status_not_bound(self) -> None:
        cfg = resolve_effective_backtest_cost_config(_minimal_cfg())
        assert cfg.funding_model_version == "NOT_BOUND"


class TestEngineCostBinding:
    def test_standard_engine_path_uses_config_not_zero(self) -> None:
        engine = BacktestEngine()
        engine.config = _minimal_cfg()
        result = engine.run_realistic(
            df=_ohlcv(),
            strategy_signal_fn=_signal_fn,
            strategy_params={"fast_period": 3, "slow_period": 8},
        )
        meta = result.metadata
        assert meta["fee_bps"] == 10.0
        assert meta["slippage_bps"] == 5.0
        assert meta["config_digest"]
        assert "effective_cost_config" in meta

    def test_explicit_zero_cost_test_mode(self) -> None:
        engine = BacktestEngine()
        engine.config = _minimal_cfg()
        result = engine.run_realistic(
            df=_ohlcv(),
            strategy_signal_fn=_signal_fn,
            strategy_params={"fast_period": 3, "slow_period": 8},
            explicit_zero_cost_non_economic=True,
        )
        assert result.metadata["fee_bps"] == 0.0
        assert result.metadata["economic_interpretation_allowed"] is False

    def test_result_metadata_contains_cost_fields(self) -> None:
        engine = BacktestEngine()
        engine.config = _minimal_cfg()
        result = engine.run_realistic(
            df=_ohlcv(),
            strategy_signal_fn=_signal_fn,
            strategy_params={"fast_period": 3, "slow_period": 8},
        )
        assert "gross_return" in result.stats
        assert "net_return" in result.stats
        assert "fee_drag" in result.stats
        assert "slippage_impact" in result.stats
        assert result.stats["funding_drag_or_status"] == "NOT_BOUND"

    def test_reproducibility_same_input_same_net(self) -> None:
        df = _ohlcv()
        params = {"fast_period": 3, "slow_period": 8}

        def _run() -> float:
            engine = BacktestEngine()
            engine.config = _minimal_cfg()
            res = engine.run_realistic(df=df, strategy_signal_fn=_signal_fn, strategy_params=params)
            return float(res.stats["net_return"])

        assert math.isclose(_run(), _run(), rel_tol=0.0, abs_tol=0.0)

    def test_higher_fees_lower_or_equal_return(self) -> None:
        df = _ohlcv(120)
        params = {"fast_period": 3, "slow_period": 8}
        low = resolve_effective_backtest_cost_config(_minimal_cfg())
        high_cfg = copy.deepcopy(_minimal_cfg())
        high_cfg["backtest"]["fee_bps"] = 50.0
        high_cfg["backtest"]["slippage_bps"] = 25.0
        high = resolve_effective_backtest_cost_config(high_cfg)

        engine = BacktestEngine()
        engine.config = _minimal_cfg()
        r_low = engine.run_realistic(
            df=df, strategy_signal_fn=_signal_fn, strategy_params=params, cost_config=low
        )
        r_high = engine.run_realistic(
            df=df, strategy_signal_fn=_signal_fn, strategy_params=params, cost_config=high
        )
        assert r_high.stats["net_return"] <= r_low.stats["net_return"]

    def test_long_short_symmetry_cost_binding(self) -> None:
        """Fees/slippage bound symmetrically for maker/taker and entry/exit."""
        cfg = resolve_effective_backtest_cost_config(_minimal_cfg())
        assert cfg.maker_fee_bps == cfg.taker_fee_bps
        assert cfg.entry_slippage_bps == cfg.exit_slippage_bps


class TestRunBacktestCliBinding:
    def test_cli_module_exposes_cost_flags(self) -> None:
        from scripts import run_backtest as rb

        with open(rb.__file__, encoding="utf-8") as f:
            text = f.read()
        assert "--fee-bps" in text
        assert "--slippage-bps" in text
        assert "--explicit-zero-cost-non-economic" in text
