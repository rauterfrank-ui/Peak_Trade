"""Regression: MV2 legacy-bar cost application + research shared portfolio equity."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from typing import Any, Mapping

import pandas as pd
import pytest

from src.backtest.backtest_engine_position_feedback_adapter_v1 import (
    finalize_legacy_realistic_bar_loop_v1,
    init_legacy_realistic_bar_loop_state_v1,
    step_legacy_realistic_bar_v1,
)
from src.backtest.cost_config_v0 import resolve_effective_backtest_cost_config
from src.backtest.engine import (
    BacktestEngine,
    Trade,
    _compute_roundtrip_fee_slippage_components_v0,
    _emit_legacy_trade_accounting_fields_v0,
)
from src.backtest import mv2_research_wiring_v1 as wiring
from src.backtest.strategy_signal_binding_v1 import ENGINE_SIGNAL_SOURCE_MV2_REPLAY

_REPO = Path(__file__).resolve().parents[2]
_PORT = (
    _REPO
    / "docs/evidence/canonical_economic_reevaluation_post_5348_v1"
    / "shared_portfolio_equity_research_v1.py"
)


def _load_portfolio_mod():
    spec = importlib.util.spec_from_file_location("shared_portfolio_equity_research_v1", _PORT)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


def _cfg(*, fee_bps: float = 10.0, slippage_bps: float = 5.0) -> Mapping[str, Any]:
    return {
        "backtest": {
            "initial_cash": 10_000.0,
            "cost_model_version": "backtest_cost_v0",
            "fee_bps": fee_bps,
            "slippage_bps": slippage_bps,
        },
        "risk": {
            "risk_per_trade": 0.004,
            "max_position_size": 0.25,
            "min_position_value": 10.0,
            "min_stop_distance": 0.0001,
        },
        "economic_evaluation_v1": {
            "strategy_params": {
                "fast_window": 2,
                "slow_window": 3,
            },
        },
    }


def _bars(n: int, closes: list[float] | None = None) -> pd.DataFrame:
    closes = closes or [100.0 + i for i in range(n)]
    idx = pd.date_range("2024-01-01", periods=n, freq="1h", tz="UTC")
    return pd.DataFrame(
        {
            "open": closes,
            "high": [c + 1.0 for c in closes],
            "low": [c - 1.0 for c in closes],
            "close": closes,
            "volume": [1000.0] * n,
            "mark_price": closes,
            "index_price": closes,
            "best_bid": [c - 0.05 for c in closes],
            "best_ask": [c + 0.05 for c in closes],
            "spread": [0.1] * n,
            "open_interest": [10000.0] * n,
            "funding_rate": [0.0001] * n,
            "volatility_estimate": [0.2] * n,
            "is_final": [True] * n,
            "bar_interval": ["1h"] * n,
        },
        index=idx,
    )


def _run_roundtrip(
    *,
    signals: list[int],
    closes: list[float],
    fee_bps: float,
    slip_bps: float,
    explicit_zero: bool = False,
):
    cfg = dict(_cfg(fee_bps=fee_bps, slippage_bps=slip_bps))
    engine = BacktestEngine(
        use_execution_pipeline=True,
        risk_limits=wiring.build_mv2_research_risk_limits_v1(cfg),
    )
    engine.config = cfg
    cost = resolve_effective_backtest_cost_config(
        cfg, explicit_zero_cost_non_economic=explicit_zero
    )
    state = init_legacy_realistic_bar_loop_state_v1(engine, strategy_params={"stop_pct": 0.5})
    bars = _bars(len(closes), closes=closes)
    for i, signal in enumerate(signals):
        state = step_legacy_realistic_bar_v1(
            engine,
            state,
            bar=bars.iloc[i],
            signal=signal,
            symbol="inst-eth-usdt-perp",
            effective_cost=cost,
            honor_mapped_short_entry=True,
        )
    result = finalize_legacy_realistic_bar_loop_v1(
        engine,
        state,
        df=bars,
        effective_cost=cost,
        symbol="inst-eth-usdt-perp",
    )
    return result, cost


def test_long_roundtrip_applies_fees_and_slippage() -> None:
    result, cost = _run_roundtrip(
        signals=[0, 1, 0, -1],
        closes=[100.0, 100.0, 100.0, 110.0],
        fee_bps=10.0,
        slip_bps=5.0,
    )
    assert result.trades is not None and not result.trades.empty
    trade = result.trades.iloc[0]
    assert float(trade["size"]) > 0.0
    assert float(trade["entry_cost"]) > 0.0
    assert float(trade["exit_cost"]) > 0.0
    assert float(trade["fee_total"]) > 0.0
    assert float(trade["slippage_total"]) > 0.0
    assert float(trade["gross_pnl"]) > float(trade["pnl"])
    assert float(trade["gross_pnl"]) - float(trade["fee_total"]) - float(
        trade["slippage_total"]
    ) == pytest.approx(float(trade["pnl"]), abs=1e-9)
    assert float(trade["entry_price"]) == pytest.approx(100.0)
    assert float(trade["exit_price"]) == pytest.approx(110.0)
    entry_fee, exit_fee, entry_slip, exit_slip = _compute_roundtrip_fee_slippage_components_v0(
        size=float(trade["size"]),
        entry_price=float(trade["entry_price"]),
        exit_price=float(trade["exit_price"]),
        effective_cost=cost,
    )
    assert float(trade["fee_total"]) == pytest.approx(entry_fee + exit_fee)
    assert float(trade["slippage_total"]) == pytest.approx(entry_slip + exit_slip)


def test_short_roundtrip_applies_fees_and_slippage() -> None:
    result, _cost = _run_roundtrip(
        signals=[0, -1, 0, 1],
        closes=[100.0, 100.0, 100.0, 90.0],
        fee_bps=10.0,
        slip_bps=5.0,
    )
    trade = result.trades.iloc[0]
    assert float(trade["size"]) < 0.0
    assert float(trade["gross_pnl"]) > 0.0
    assert float(trade["pnl"]) < float(trade["gross_pnl"])
    assert float(trade["fee_total"]) + float(trade["slippage_total"]) == pytest.approx(
        float(trade["gross_pnl"]) - float(trade["pnl"]), abs=1e-9
    )


def test_zero_cost_configuration_keeps_gross_equals_net() -> None:
    result, _cost = _run_roundtrip(
        signals=[0, 1, 0, -1],
        closes=[100.0, 100.0, 100.0, 110.0],
        fee_bps=0.0,
        slip_bps=0.0,
        explicit_zero=True,
    )
    trade = result.trades.iloc[0]
    assert float(trade["entry_cost"]) == pytest.approx(0.0)
    assert float(trade["exit_cost"]) == pytest.approx(0.0)
    assert float(trade["fee_total"]) == pytest.approx(0.0)
    assert float(trade["slippage_total"]) == pytest.approx(0.0)
    assert float(trade["pnl"]) == pytest.approx(float(trade["gross_pnl"]))


def test_no_double_cost_application_on_emit() -> None:
    cfg = _cfg(fee_bps=10.0, slippage_bps=5.0)
    cost = resolve_effective_backtest_cost_config(cfg)
    trade = Trade(
        entry_time=pd.Timestamp("2024-01-01T00:00:00Z"),
        entry_price=100.0,
        size=10.0,
        stop_price=50.0,
    )
    trade.exit_time = pd.Timestamp("2024-01-01T01:00:00Z")
    trade.exit_price = 110.0
    trade.pnl = 100.0
    _emit_legacy_trade_accounting_fields_v0(
        trade, side="long", effective_cost=cost, legacy_path_cost_application=True
    )
    net_once = float(trade.pnl)
    _emit_legacy_trade_accounting_fields_v0(
        trade, side="long", effective_cost=cost, legacy_path_cost_application=True
    )
    assert float(trade.pnl) == pytest.approx(net_once)
    assert float(trade.gross_pnl) - float(trade.fee_total) - float(
        trade.slippage_total
    ) == pytest.approx(float(trade.pnl))


def test_shared_portfolio_equity_single_initial_capital_and_drawdown() -> None:
    mod = _load_portfolio_mod()
    idx = pd.date_range("2024-01-01", periods=5, freq="1h", tz="UTC")
    a = pd.Series([10_000.0, 11_000.0, 9_000.0, 9_500.0, 10_500.0], index=idx)
    b = pd.Series([10_000.0, 10_500.0, 8_500.0, 9_000.0, 10_000.0], index=idx)
    equity = mod.build_equal_weight_portfolio_equity({"A": a, "B": b}, initial_capital=10_000.0)
    assert float(equity.iloc[0]) == pytest.approx(10_000.0)
    metrics = mod.portfolio_metrics_from_equity(equity, initial_capital=10_000.0)
    assert metrics["net_return"] == pytest.approx(float(equity.iloc[-1]) / 10_000.0 - 1.0)
    assert metrics["max_drawdown"] < 0.0
    assert "hourly_portfolio" in metrics["sharpe_definition"]
    recon = mod.reconcile_portfolio_equity_to_scaled_net_pnl(
        initial_capital=10_000.0,
        final_equity=float(equity.iloc[-1]),
        sleeve_net_pnls=[500.0, 0.0],
        n_instruments=2,
        sleeve_initial_cash=10_000.0,
    )
    assert recon == "PASS"


def test_overlapping_trades_peak_exposure_scaled_to_shared_capital() -> None:
    mod = _load_portfolio_mod()
    trades = [
        {
            "entry_time": "2024-01-01T00:00:00Z",
            "exit_time": "2024-01-01T03:00:00Z",
            "size": 1.0,
            "entry_price": 10_000.0,
        },
        {
            "entry_time": "2024-01-01T01:00:00Z",
            "exit_time": "2024-01-01T04:00:00Z",
            "size": 1.0,
            "entry_price": 10_000.0,
        },
    ]
    out = mod.peak_gross_exposure_from_scaled_trades(
        trades,
        n_instruments=2,
        initial_capital=10_000.0,
        sleeve_initial_cash=10_000.0,
    )
    assert out["peak_gross_exposure"] == pytest.approx(10_000.0)
    assert out["scale"] == pytest.approx(0.5)


def test_mv2_wiring_costs_applied_end_to_end(monkeypatch: pytest.MonkeyPatch) -> None:
    signals = [0, 1, 0, -1]
    call_idx = {"i": 0}

    def _forced_signal(_evidence: object) -> int:
        idx = call_idx["i"]
        call_idx["i"] += 1
        return signals[min(idx, len(signals) - 1)]

    monkeypatch.setattr(
        wiring,
        "map_decision_evidence_to_position_signal_v1",
        _forced_signal,
    )
    result = wiring.run_mv2_research_backtest_wiring_v1(
        bars=_bars(4, closes=[100.0, 100.0, 100.0, 110.0]),
        strategy_id="ma_crossover",
        cfg=_cfg(fee_bps=10.0, slippage_bps=5.0),
        backtest_engine_signal_source=ENGINE_SIGNAL_SOURCE_MV2_REPLAY,
    )
    trades = result.backtest_result.trades
    assert trades is not None and not trades.empty
    trade = trades.iloc[0]
    assert float(trade["fee_total"]) > 0.0
    assert float(trade["slippage_total"]) > 0.0
    assert result.backtest_result.metadata.get("legacy_path_cost_application") is True
