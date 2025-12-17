# tests/test_demo_execution_backtest_smoke.py
"""
Smoke-Tests fuer scripts/demo_execution_backtest.py (Phase 16C).

Testet:
- Import des Demo-Scripts
- Interne Funktionen (get_strategy_fn, generate_sample_data, etc.)
- main() mit Test-Argumenten (ohne echte CLI)
- ExecutionPipeline vs. Legacy-Modus
"""
import pandas as pd
import pytest


class TestDemoScriptImports:
    """Tests fuer grundlegende Imports."""

    def test_script_imports(self):
        """Script kann importiert werden."""
        from scripts import demo_execution_backtest

        assert hasattr(demo_execution_backtest, "main")
        assert hasattr(demo_execution_backtest, "parse_args")
        assert hasattr(demo_execution_backtest, "get_strategy_fn")
        assert hasattr(demo_execution_backtest, "generate_sample_data")
        assert hasattr(demo_execution_backtest, "run_backtest")

    def test_parse_args_defaults(self):
        """parse_args hat korrekte Defaults."""
        from scripts.demo_execution_backtest import parse_args

        args = parse_args([])

        assert args.symbol == "BTC/EUR"
        assert args.strategy == "ma_crossover"
        assert args.timeframe == "1h"
        assert args.bars == 200
        assert args.fee_bps == 10.0
        assert args.slippage_bps == 5.0
        assert args.use_legacy is False
        assert args.no_log_executions is False
        assert args.compare is False

    def test_parse_args_custom(self):
        """parse_args verarbeitet Custom-Argumente."""
        from scripts.demo_execution_backtest import parse_args

        args = parse_args([
            "--symbol", "ETH/EUR",
            "--strategy", "macd",
            "--timeframe", "4h",
            "--bars", "100",
            "--fee-bps", "15.0",
            "--slippage-bps", "8.0",
            "--use-legacy",
        ])

        assert args.symbol == "ETH/EUR"
        assert args.strategy == "macd"
        assert args.timeframe == "4h"
        assert args.bars == 100
        assert args.fee_bps == 15.0
        assert args.slippage_bps == 8.0
        assert args.use_legacy is True


class TestGetStrategyFn:
    """Tests fuer get_strategy_fn."""

    def test_load_ma_crossover(self):
        """ma_crossover Strategie kann geladen werden."""
        from scripts.demo_execution_backtest import get_strategy_fn

        fn = get_strategy_fn("ma_crossover")
        assert callable(fn)

    def test_load_macd(self):
        """macd Strategie kann geladen werden."""
        from scripts.demo_execution_backtest import get_strategy_fn

        fn = get_strategy_fn("macd")
        assert callable(fn)

    def test_load_momentum(self):
        """momentum Strategie kann geladen werden."""
        from scripts.demo_execution_backtest import get_strategy_fn

        fn = get_strategy_fn("momentum")
        assert callable(fn)

    def test_unknown_strategy_raises(self):
        """Unbekannte Strategie wirft ValueError."""
        from scripts.demo_execution_backtest import get_strategy_fn

        with pytest.raises(ValueError, match="Unbekannte Strategie"):
            get_strategy_fn("unknown_strategy")


class TestGetDefaultStrategyParams:
    """Tests fuer get_default_strategy_params."""

    def test_ma_crossover_params(self):
        """MA-Crossover hat Default-Parameter."""
        from scripts.demo_execution_backtest import get_default_strategy_params

        params = get_default_strategy_params("ma_crossover")

        assert "fast_period" in params
        assert "slow_period" in params
        assert "stop_pct" in params
        assert params["fast_period"] == 10
        assert params["slow_period"] == 30

    def test_macd_params(self):
        """MACD hat Default-Parameter."""
        from scripts.demo_execution_backtest import get_default_strategy_params

        params = get_default_strategy_params("macd")

        assert "fast_period" in params
        assert "slow_period" in params
        assert "signal_period" in params

    def test_unknown_strategy_returns_minimal(self):
        """Unbekannte Strategie gibt minimale Defaults."""
        from scripts.demo_execution_backtest import get_default_strategy_params

        params = get_default_strategy_params("unknown")

        assert "stop_pct" in params


class TestGenerateSampleData:
    """Tests fuer generate_sample_data."""

    def test_basic_generation(self):
        """Sample-Daten werden korrekt generiert."""
        from scripts.demo_execution_backtest import generate_sample_data

        df = generate_sample_data(symbol="BTC/EUR", bars=50)

        assert isinstance(df, pd.DataFrame)
        assert len(df) == 50
        assert "open" in df.columns
        assert "high" in df.columns
        assert "low" in df.columns
        assert "close" in df.columns
        assert "volume" in df.columns

    def test_different_symbols(self):
        """Verschiedene Symbole haben unterschiedliche Basis-Preise."""
        from scripts.demo_execution_backtest import generate_sample_data

        btc_df = generate_sample_data(symbol="BTC/EUR", bars=10)
        eth_df = generate_sample_data(symbol="ETH/EUR", bars=10)
        ltc_df = generate_sample_data(symbol="LTC/EUR", bars=10)

        # BTC sollte hoeher sein als ETH, ETH hoeher als LTC
        assert btc_df["close"].mean() > eth_df["close"].mean()
        assert eth_df["close"].mean() > ltc_df["close"].mean()

    def test_ohlc_consistency(self):
        """OHLC-Daten sind konsistent (high >= close, low <= close)."""
        from scripts.demo_execution_backtest import generate_sample_data

        df = generate_sample_data(symbol="BTC/EUR", bars=100)

        # High >= max(open, close)
        assert (df["high"] >= df[["open", "close"]].max(axis=1)).all()

        # Low <= min(open, close)
        assert (df["low"] <= df[["open", "close"]].min(axis=1)).all()

    def test_with_start_end(self):
        """Sample-Daten mit Start/End-Datum."""
        from scripts.demo_execution_backtest import generate_sample_data

        df = generate_sample_data(
            symbol="BTC/EUR",
            start="2024-01-01",
            end="2024-01-10",
            timeframe="1d",
        )

        assert len(df) > 0
        assert df.index[0] >= pd.Timestamp("2024-01-01")
        assert df.index[-1] <= pd.Timestamp("2024-01-10")


class TestRunBacktest:
    """Tests fuer run_backtest."""

    def test_execution_pipeline_mode(self):
        """Backtest mit ExecutionPipeline funktioniert."""
        from scripts.demo_execution_backtest import (
            generate_sample_data,
            get_default_strategy_params,
            get_strategy_fn,
            run_backtest,
        )

        df = generate_sample_data(symbol="BTC/EUR", bars=100)
        strategy_fn = get_strategy_fn("ma_crossover")
        params = get_default_strategy_params("ma_crossover")

        result, engine = run_backtest(
            df=df,
            strategy_fn=strategy_fn,
            strategy_params=params,
            symbol="BTC/EUR",
            fee_bps=10.0,
            slippage_bps=5.0,
            use_execution_pipeline=True,
            log_executions=True,
        )

        assert result is not None
        assert hasattr(result, "stats")
        assert "total_return" in result.stats

        # ExecutionPipeline-spezifische Stats
        assert "total_orders" in result.stats or result.stats.get("total_trades", 0) == 0

    def test_legacy_mode(self):
        """Backtest im Legacy-Modus funktioniert."""
        from scripts.demo_execution_backtest import (
            generate_sample_data,
            get_default_strategy_params,
            get_strategy_fn,
            run_backtest,
        )

        df = generate_sample_data(symbol="BTC/EUR", bars=100)
        strategy_fn = get_strategy_fn("ma_crossover")
        params = get_default_strategy_params("ma_crossover")

        result, engine = run_backtest(
            df=df,
            strategy_fn=strategy_fn,
            strategy_params=params,
            symbol="BTC/EUR",
            fee_bps=10.0,
            slippage_bps=5.0,
            use_execution_pipeline=False,
            log_executions=False,
        )

        assert result is not None
        assert hasattr(result, "stats")
        assert "total_return" in result.stats

    def test_execution_logs_populated(self):
        """Execution-Logs werden bei log_executions=True gefuellt."""
        from scripts.demo_execution_backtest import (
            generate_sample_data,
            get_default_strategy_params,
            get_strategy_fn,
            run_backtest,
        )

        df = generate_sample_data(symbol="BTC/EUR", bars=100)
        strategy_fn = get_strategy_fn("ma_crossover")
        params = get_default_strategy_params("ma_crossover")

        result, engine = run_backtest(
            df=df,
            strategy_fn=strategy_fn,
            strategy_params=params,
            symbol="BTC/EUR",
            fee_bps=10.0,
            slippage_bps=5.0,
            use_execution_pipeline=True,
            log_executions=True,
        )

        logs = engine.get_execution_logs()
        # Logs sollten mindestens existieren (koennen leer sein bei wenig Trades)
        assert isinstance(logs, list)


class TestMainFunction:
    """Tests fuer main()."""

    def test_main_default_args(self, capsys):
        """main() mit Default-Argumenten funktioniert."""
        from scripts.demo_execution_backtest import main

        result = main(["--bars", "50"])  # Weniger Bars fuer schnelleren Test

        assert result is not None
        assert hasattr(result, "stats")

        # Output pruefen
        captured = capsys.readouterr()
        assert "Peak_Trade Demo" in captured.out
        assert "BTC/EUR" in captured.out
        assert "execution_pipeline_backtest" in captured.out

    def test_main_legacy_mode(self, capsys):
        """main() im Legacy-Modus."""
        from scripts.demo_execution_backtest import main

        result = main(["--bars", "50", "--use-legacy"])

        assert result is not None

        captured = capsys.readouterr()
        assert "realistic_legacy" in captured.out

    def test_main_compare_mode(self, capsys):
        """main() im Vergleichsmodus."""
        from scripts.demo_execution_backtest import main

        result = main(["--bars", "50", "--compare"])

        assert result is not None

        captured = capsys.readouterr()
        assert "VERGLEICH" in captured.out
        assert "ExecutionPipeline" in captured.out
        assert "Legacy" in captured.out

    def test_main_with_strategy(self, capsys):
        """main() mit verschiedenen Strategien."""
        from scripts.demo_execution_backtest import main

        # MACD
        result = main(["--bars", "50", "--strategy", "macd"])
        assert result is not None

        captured = capsys.readouterr()
        assert "macd" in captured.out

    def test_main_verbose(self, capsys):
        """main() mit verbose Flag zeigt Sample-Trades."""
        from scripts.demo_execution_backtest import main

        result = main(["--bars", "100", "--verbose"])

        assert result is not None

        captured = capsys.readouterr()
        assert "Sample-Trades" in captured.out

    def test_main_unknown_strategy(self, capsys):
        """main() mit unbekannter Strategie gibt Fehler aus."""
        from scripts.demo_execution_backtest import main

        result = main(["--strategy", "unknown_xyz"])

        assert result is None

        captured = capsys.readouterr()
        assert "Fehler" in captured.out or "Unbekannte Strategie" in captured.out


class TestEdgeCases:
    """Edge-Case Tests."""

    def test_minimal_bars(self):
        """Backtest mit minimalen Bars."""
        from scripts.demo_execution_backtest import (
            generate_sample_data,
            get_default_strategy_params,
            get_strategy_fn,
            run_backtest,
        )

        # Sehr wenige Bars (koennte zu keinen Trades fuehren)
        df = generate_sample_data(symbol="BTC/EUR", bars=35)
        strategy_fn = get_strategy_fn("ma_crossover")
        params = get_default_strategy_params("ma_crossover")

        result, engine = run_backtest(
            df=df,
            strategy_fn=strategy_fn,
            strategy_params=params,
            symbol="BTC/EUR",
            fee_bps=10.0,
            slippage_bps=5.0,
            use_execution_pipeline=True,
            log_executions=True,
        )

        # Sollte nicht crashen, auch wenn keine Trades
        assert result is not None
        assert "total_return" in result.stats

    def test_zero_fees_slippage(self):
        """Backtest ohne Fees und Slippage."""
        from scripts.demo_execution_backtest import (
            generate_sample_data,
            get_default_strategy_params,
            get_strategy_fn,
            run_backtest,
        )

        df = generate_sample_data(symbol="BTC/EUR", bars=100)
        strategy_fn = get_strategy_fn("ma_crossover")
        params = get_default_strategy_params("ma_crossover")

        result, engine = run_backtest(
            df=df,
            strategy_fn=strategy_fn,
            strategy_params=params,
            symbol="BTC/EUR",
            fee_bps=0.0,
            slippage_bps=0.0,
            use_execution_pipeline=True,
            log_executions=False,
        )

        assert result is not None
        # Total fees sollte 0 sein
        assert result.stats.get("total_fees", 0) == 0
