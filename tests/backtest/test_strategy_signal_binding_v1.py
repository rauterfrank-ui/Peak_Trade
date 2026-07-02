"""Contract tests for strategy signal binding v1 (STEP 29M wiring fix)."""

from __future__ import annotations

import math

import pandas as pd
import pytest

from src.backtest import mv2_research_wiring_v1 as wiring
from src.backtest.strategy_signal_binding_v1 import (
    ENGINE_SIGNAL_SOURCE_CONFIGURED_STRATEGY,
    StrategySignalBindingError,
    collect_configured_strategy_params_v1,
    compute_required_warmup_rows_v1,
    execute_configured_strategy_signal_series_v1,
    project_strategy_params_for_binding_v1,
    resolve_effective_strategy_params_v1,
)


def _bars(n: int = 80) -> pd.DataFrame:
    idx = pd.date_range("2026-06-01", periods=n, freq="1h", tz="UTC")
    close = [100.0 + 5.0 * math.sin(i / 8.0) + float(i) * 0.05 for i in range(n)]
    return pd.DataFrame(
        {
            "open": close,
            "high": [v + 0.5 for v in close],
            "low": [v - 0.5 for v in close],
            "close": close,
            "mark_price": close,
            "index_price": [v - 0.1 for v in close],
            "best_bid": [v - 0.05 for v in close],
            "best_ask": [v + 0.05 for v in close],
            "spread": [0.1 for _ in close],
            "volume": [1000.0 for _ in close],
            "open_interest": [10000.0 for _ in close],
            "funding_rate": [0.0001 for _ in close],
            "volatility_estimate": [0.2 for _ in close],
            "is_final": [True for _ in close],
            "bar_interval": ["1m" for _ in close],
        },
        index=idx,
    )


def _cfg(**strategy_params: int) -> dict:
    payload = {
        "backtest": {
            "initial_cash": 10_000.0,
            "cost_model_version": "backtest_cost_v0",
            "fee_bps": 10.0,
            "slippage_bps": 5.0,
        },
        "risk": {
            "risk_per_trade": 0.02,
            "max_position_size": 0.25,
            "min_position_value": 10.0,
            "min_stop_distance": 0.0001,
        },
        "economic_evaluation_v1": {
            "strategy_id": "ma_crossover",
            "walk_forward": {"train_bars": 8, "test_bars": 4, "step_bars": 4},
            "monte_carlo": {"runs": 4, "seed": 42},
        },
    }
    if strategy_params:
        payload["economic_evaluation_v1"]["strategy_params"] = dict(strategy_params)
    return payload


def test_resolve_effective_params_defaults_for_ma_crossover() -> None:
    effective, digest = resolve_effective_strategy_params_v1("ma_crossover", {})
    assert effective["fast_window"] == 20
    assert effective["slow_window"] == 50
    assert len(digest) == 64


def test_legacy_alias_fast_period_maps_to_fast_window() -> None:
    effective, _ = resolve_effective_strategy_params_v1(
        "ma_crossover",
        {"fast_period": 10, "slow_period": 30},
    )
    assert effective["fast_window"] == 10
    assert effective["slow_window"] == 30


def test_unknown_strategy_param_fail_closed() -> None:
    with pytest.raises(StrategySignalBindingError, match="unknown_strategy_param"):
        resolve_effective_strategy_params_v1("ma_crossover", {"not_a_param": 1})


def test_resolve_effective_params_rejects_price_col_directly() -> None:
    with pytest.raises(StrategySignalBindingError, match="unknown_strategy_param:price_col"):
        resolve_effective_strategy_params_v1(
            "ma_crossover",
            {"fast_window": 20, "slow_window": 50, "price_col": "close"},
        )


def test_project_ma_crossover_strips_price_col_for_binding() -> None:
    projected = project_strategy_params_for_binding_v1(
        "ma_crossover",
        {"fast_window": 20, "slow_window": 50, "price_col": "close"},
    )
    assert projected == {"fast_window": 20, "slow_window": 50}


def test_project_ma_crossover_rejects_unexpected_param() -> None:
    with pytest.raises(StrategySignalBindingError, match="unknown_strategy_param:unexpected_param"):
        project_strategy_params_for_binding_v1(
            "ma_crossover",
            {
                "fast_window": 20,
                "slow_window": 50,
                "price_col": "close",
                "unexpected_param": 1,
            },
        )


def test_execute_ma_crossover_step29m_canonical_config_with_price_col() -> None:
    cfg = _cfg(fast_window=20, slow_window=50)
    cfg["economic_evaluation_v1"]["strategy_params"]["price_col"] = "close"
    result = execute_configured_strategy_signal_series_v1(
        _bars(120),
        strategy_id="ma_crossover",
        cfg=cfg,
    )
    assert result.provenance.strategy_execution_status.value == "EXECUTED"
    assert result.provenance.configured_strategy_params == {
        "fast_window": 20,
        "slow_window": 50,
        "price_col": "close",
    }
    assert result.provenance.effective_strategy_params == {
        "fast_window": 20,
        "slow_window": 50,
    }
    assert result.provenance.strategy_nonzero_signal_count >= 0


def test_execute_ma_crossover_rejects_unexpected_param_with_price_col() -> None:
    cfg = _cfg(fast_window=20, slow_window=50)
    cfg["economic_evaluation_v1"]["strategy_params"]["price_col"] = "close"
    cfg["economic_evaluation_v1"]["strategy_params"]["unexpected_param"] = 1
    with pytest.raises(StrategySignalBindingError, match="unknown_strategy_param:unexpected_param"):
        execute_configured_strategy_signal_series_v1(
            _bars(),
            strategy_id="ma_crossover",
            cfg=cfg,
        )


def test_resolve_breakout_donchian_preserves_price_col_directly() -> None:
    effective, _ = resolve_effective_strategy_params_v1(
        "breakout_donchian",
        {"lookback": 20, "price_col": "close"},
    )
    assert effective["price_col"] == "close"
    assert effective["lookback"] == 20


def test_execute_ma_crossover_produces_nonzero_signals_on_trending_fixture() -> None:
    result = execute_configured_strategy_signal_series_v1(
        _bars(),
        strategy_id="ma_crossover",
        cfg=_cfg(),
    )
    assert result.provenance.strategy_execution_status.value == "EXECUTED"
    assert result.provenance.engine_signal_source == ENGINE_SIGNAL_SOURCE_CONFIGURED_STRATEGY
    assert result.provenance.strategy_nonzero_signal_count > 0
    assert result.provenance.strategy_signal_digest == result.provenance.engine_signal_digest


def test_mv2_wiring_uses_strategy_signals_not_flat_replay() -> None:
    result = wiring.run_mv2_research_backtest_wiring_v1(
        _bars(),
        strategy_id="ma_crossover",
        cfg=_cfg(),
    )
    assert result.strategy_signal_provenance.strategy_nonzero_signal_count > 0
    assert (result.signals != 0).any()
    assert (
        result.strategy_signal_provenance.engine_signal_digest
        == result.strategy_signal_provenance.strategy_signal_digest
    )
    assert result.mv2_replay_signals is not None
    assert len(result.mv2_replay_signals) == len(_bars())


def test_mv2_wiring_engine_trades_when_strategy_has_entries() -> None:
    result = wiring.run_mv2_research_backtest_wiring_v1(
        _bars(120),
        strategy_id="ma_crossover",
        cfg=_cfg(),
    )
    assert result.backtest_result.stats.get("total_trades", 0) >= 0
    assert result.strategy_signal_provenance.configured_strategy_id == "ma_crossover"


def test_collect_configured_params_from_evaluation_section() -> None:
    cfg = _cfg(fast_window=15, slow_window=40)
    params = collect_configured_strategy_params_v1(cfg, "ma_crossover")
    assert params["fast_window"] == 15
    assert params["slow_window"] == 40


def test_signal_contract_rejects_duplicate_timestamps() -> None:
    from src.backtest.strategy_signal_binding_v1 import validate_strategy_signal_contract_v1

    idx = pd.DatetimeIndex(
        ["2026-06-01 00:00:00+00:00", "2026-06-01 00:00:00+00:00"],
        tz="UTC",
    )
    signals = pd.Series([0, 1], index=idx)
    with pytest.raises(StrategySignalBindingError, match="duplicate_timestamps"):
        validate_strategy_signal_contract_v1(
            signals,
            bars_index=idx,
            strategy_id="ma_crossover",
            strategy_params_digest="abc",
        )


def test_resolve_effective_params_defaults_for_macd() -> None:
    effective, digest = resolve_effective_strategy_params_v1("macd", {})
    assert effective["fast_ema"] == 12
    assert effective["slow_ema"] == 26
    assert effective["signal_ema"] == 9
    assert len(digest) == 64


def test_macd_unknown_strategy_param_fail_closed() -> None:
    with pytest.raises(StrategySignalBindingError, match="unknown_strategy_param"):
        resolve_effective_strategy_params_v1("macd", {"fast_window": 12})


def test_macd_required_warmup_rows() -> None:
    effective, _ = resolve_effective_strategy_params_v1("macd", {})
    assert compute_required_warmup_rows_v1("macd", effective) == 34


def test_breakout_donchian_required_warmup_rows_default() -> None:
    effective, _ = resolve_effective_strategy_params_v1("breakout_donchian", {})
    assert compute_required_warmup_rows_v1("breakout_donchian", effective) == 20


def test_breakout_donchian_warmup_missing_lookback_fail_closed() -> None:
    with pytest.raises(StrategySignalBindingError, match="breakout_donchian_lookback_missing"):
        compute_required_warmup_rows_v1("breakout_donchian", {})


def test_breakout_donchian_warmup_invalid_lookback_fail_closed() -> None:
    with pytest.raises(StrategySignalBindingError, match="lookback_not_integer"):
        compute_required_warmup_rows_v1("breakout_donchian", {"lookback": 2.5})


def test_execute_macd_produces_long_and_short_signals() -> None:
    result = execute_configured_strategy_signal_series_v1(
        _bars(120),
        strategy_id="macd",
        cfg={
            "economic_evaluation_v1": {
                "strategy_id": "macd",
                "strategy_params": {"fast_ema": 12, "slow_ema": 26, "signal_ema": 9},
            }
        },
    )
    assert result.provenance.strategy_execution_status.value == "EXECUTED"
    assert result.provenance.engine_signal_source == ENGINE_SIGNAL_SOURCE_CONFIGURED_STRATEGY
    assert result.provenance.strategy_nonzero_signal_count > 0
    assert (result.signals == 1).any()
    assert (result.signals == -1).any()


def test_execute_breakout_donchian_produces_signals() -> None:
    result = execute_configured_strategy_signal_series_v1(
        _bars(120),
        strategy_id="breakout_donchian",
        cfg={
            "economic_evaluation_v1": {
                "strategy_id": "breakout_donchian",
                "strategy_params": {"lookback": 20, "price_col": "close"},
            }
        },
    )
    assert result.provenance.strategy_execution_status.value == "EXECUTED"
    assert result.provenance.engine_signal_source == ENGINE_SIGNAL_SOURCE_CONFIGURED_STRATEGY
    assert result.provenance.strategy_nonzero_signal_count >= 0


def test_signal_contract_rejects_unknown_values() -> None:
    from src.backtest.strategy_signal_binding_v1 import validate_strategy_signal_contract_v1

    idx = pd.date_range("2026-06-01", periods=4, freq="1h", tz="UTC")
    signals = pd.Series([0, 2, 0, 0], index=idx)
    with pytest.raises(StrategySignalBindingError, match="unknown_signal_encoding"):
        validate_strategy_signal_contract_v1(
            signals,
            bars_index=idx,
            strategy_id="ma_crossover",
            strategy_params_digest="abc",
        )


def test_signal_contract_rejects_index_mismatch() -> None:
    from src.backtest.strategy_signal_binding_v1 import validate_strategy_signal_contract_v1

    bars_idx = pd.date_range("2026-06-01", periods=4, freq="1h", tz="UTC")
    signal_idx = pd.date_range("2026-06-02", periods=4, freq="1h", tz="UTC")
    signals = pd.Series([0, 0, 0, 0], index=signal_idx)
    with pytest.raises(StrategySignalBindingError, match="index_mismatch"):
        validate_strategy_signal_contract_v1(
            signals,
            bars_index=bars_idx,
            strategy_id="ma_crossover",
            strategy_params_digest="abc",
        )


def test_economic_evidence_persists_strategy_signal_binding() -> None:
    from src.backtest import economic_viability_evidence_v1 as ev

    bars = _bars(20)
    result = ev.build_economic_viability_evidence_v1(
        bars=bars,
        data_admissibility=ev.DataAdmissibilityV1(
            source_kind=ev.DataSourceKind.SYNTHETIC_CONTRACT_FIXTURE,
            instrument_id=wiring.MV2_REQUIRED_INSTRUMENT_ID,
            data_digest=ev.compute_bars_data_digest(bars),
            data_ref="tests/backtest/test_strategy_signal_binding_v1.py::_bars",
        ),
        strategy_id="ma_crossover",
        cfg=_cfg(fast_window=2, slow_window=3),
    )
    binding = result.strategy_signal_binding
    assert binding["configured_strategy_id"] == "ma_crossover"
    assert binding["executed_strategy_id"] == "ma_crossover"
    assert binding["engine_signal_source"] == ENGINE_SIGNAL_SOURCE_CONFIGURED_STRATEGY
    assert binding["strategy_signal_digest"] == binding["engine_signal_digest"]
    assert "mv2_replay_signal_digest" in binding
    assert "configured_strategy_signal_bound" in result.reason_codes
