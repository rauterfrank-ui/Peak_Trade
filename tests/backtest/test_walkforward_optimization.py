from __future__ import annotations

from typing import Any

import pandas as pd
import pytest

from src.backtest.result import BacktestResult
from src.backtest.walkforward import WalkForwardConfig, run_walkforward_for_config


def _mk_df(n: int = 30) -> pd.DataFrame:
    idx = pd.date_range("2025-01-01", periods=n, freq="h")
    return pd.DataFrame(
        {"open": 1, "high": 1, "low": 1, "close": 1, "volume": 1},
        index=idx,
    )


def _mk_result(df: pd.DataFrame, stats: dict[str, float]) -> BacktestResult:
    # Minimal BacktestResult for walkforward pipeline.
    equity = pd.Series(10000.0, index=df.index, dtype=float)
    drawdown = pd.Series(0.0, index=df.index, dtype=float)
    return BacktestResult(
        equity_curve=equity,
        drawdown=drawdown,
        trades=None,
        stats={
            **stats,
            "total_trades": 0,
            "win_rate": 0.0,
            "profit_factor": 0.0,
            "blocked_trades": 0,
        },
        metadata={},
    )


def test_walkforward_optimization_uses_train_only_and_applies_best_to_test(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Any
) -> None:
    from src.backtest.engine import BacktestEngine

    df = _mk_df(40)
    cfg = WalkForwardConfig(
        train_window="10h",
        test_window="5h",
        output_dir=tmp_path,
    )

    calls: list[tuple[int, dict[str, Any]]] = []

    def _stub_run_realistic(
        self,
        *,
        df: pd.DataFrame,
        strategy_signal_fn: Any,
        strategy_params: dict[str, Any],
        symbol: str | None = None,
    ) -> BacktestResult:
        # Record slice length + params for assertions
        calls.append((len(df), dict(strategy_params)))

        # Score on train depends on 'p'
        p = int(strategy_params.get("p", 0))
        sharpe = 2.0 if p == 2 else 1.0
        max_dd = -0.1 if p == 2 else -0.2
        total_ret = 0.10 if p == 2 else 0.05
        return _mk_result(df, {"sharpe": sharpe, "max_drawdown": max_dd, "total_return": total_ret})

    monkeypatch.setattr(BacktestEngine, "run_realistic", _stub_run_realistic, raising=True)

    result = run_walkforward_for_config(
        config_id="cfg1",
        wf_config=cfg,
        df=df,
        strategy_name="dummy",
        strategy_signal_fn=lambda _df, _p: None,
        strategy_params={"base": 1},
        param_grid={"p": [1, 2]},
        optimization_metric="sharpe",
    )

    # Expect optimization per window:
    # - 2 train runs (p=1, p=2) with len(train_df)
    # - 1 test run (best p=2) with len(test_df)
    assert any(p.get("p") == 2 for _l, p in calls)
    # Find a test call by length == test_window bars (5h -> 5 rows)
    test_calls = [(l, p) for (l, p) in calls if l == 5]
    assert test_calls, "expected at least one test call with test window length"
    assert test_calls[0][1]["p"] == 2

    # Boundary disjointness: train window length 10, test window length 5
    train_calls = [(l, p) for (l, p) in calls if l == 10]
    assert train_calls, "expected train calls with train window length"

    # Artifacts should be written when param_grid is provided
    artifact = tmp_path / "cfg1_walkforward_optimization.json"
    assert artifact.exists()

    assert len(result.windows) > 0
    assert result.windows[0].best_params is not None
    assert result.windows[0].best_params["p"] == 2


def test_walkforward_optimization_empty_grid_raises(tmp_path: Any) -> None:
    df = _mk_df(30)
    cfg = WalkForwardConfig(train_window="10h", test_window="5h", output_dir=tmp_path)

    with pytest.raises(ValueError, match="param_grid darf nicht leer"):
        run_walkforward_for_config(
            config_id="cfg_empty",
            wf_config=cfg,
            df=df,
            strategy_name="dummy",
            strategy_signal_fn=lambda _df, _p: None,
            strategy_params={"base": 1},
            param_grid={},
        )


def test_walkforward_optimization_invalid_params_skip_and_if_none_valid_raises(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Any
) -> None:
    from src.backtest.engine import BacktestEngine

    df = _mk_df(30)
    cfg = WalkForwardConfig(train_window="10h", test_window="5h", output_dir=tmp_path)

    def _stub_run_realistic(
        self,
        *,
        df: pd.DataFrame,
        strategy_signal_fn: Any,
        strategy_params: dict[str, Any],
        symbol: str | None = None,
    ) -> BacktestResult:
        if strategy_params.get("p") == 1:
            raise ValueError("invalid params")
        return _mk_result(df, {"sharpe": 1.0, "max_drawdown": -0.1, "total_return": 0.05})

    monkeypatch.setattr(BacktestEngine, "run_realistic", _stub_run_realistic, raising=True)

    # one invalid, one valid -> should work
    _ = run_walkforward_for_config(
        config_id="cfg_skip",
        wf_config=cfg,
        df=df,
        strategy_name="dummy",
        strategy_signal_fn=lambda _df, _p: None,
        strategy_params={"base": 1},
        param_grid=[{"p": 1}, {"p": 2}],
    )

    # all invalid -> raises
    with pytest.raises(ValueError, match="Keine gültigen Parameter-Kandidaten"):
        run_walkforward_for_config(
            config_id="cfg_all_bad",
            wf_config=cfg,
            df=df,
            strategy_name="dummy",
            strategy_signal_fn=lambda _df, _p: None,
            strategy_params={"base": 1},
            param_grid=[{"p": 1}],
        )
