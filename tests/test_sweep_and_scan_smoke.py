# tests/test_sweep_and_scan_smoke.py
"""
Smoke-Tests für Strategy-Sweeps und Market-Scans.

Testet:
- Parameter-Grid-Expansion
- log_sweep_run() Logger
- log_market_scan_result() Logger
- Analytics-Funktionen für Sweeps/Scans
"""
from __future__ import annotations

import json
import pytest
from datetime import datetime
from pathlib import Path
from typing import Dict, Any


class TestParameterGridExpansion:
    """Tests für expand_parameter_grid()."""

    def test_expand_single_param(self):
        """Einzelner Parameter wird korrekt expandiert."""
        from scripts.run_sweep import expand_parameter_grid

        grid = {"short_window": [5, 10, 20]}
        result = expand_parameter_grid(grid)

        assert len(result) == 3
        assert {"short_window": 5} in result
        assert {"short_window": 10} in result
        assert {"short_window": 20} in result

    def test_expand_two_params(self):
        """Zwei Parameter erzeugen kartesisches Produkt."""
        from scripts.run_sweep import expand_parameter_grid

        grid = {
            "short_window": [5, 10],
            "long_window": [50, 100],
        }
        result = expand_parameter_grid(grid)

        assert len(result) == 4
        assert {"short_window": 5, "long_window": 50} in result
        assert {"short_window": 5, "long_window": 100} in result
        assert {"short_window": 10, "long_window": 50} in result
        assert {"short_window": 10, "long_window": 100} in result

    def test_expand_three_params(self):
        """Drei Parameter erzeugen korrektes Produkt."""
        from scripts.run_sweep import expand_parameter_grid

        grid = {
            "a": [1, 2],
            "b": [10, 20],
            "c": ["x", "y"],
        }
        result = expand_parameter_grid(grid)

        # 2 × 2 × 2 = 8
        assert len(result) == 8

    def test_expand_empty_grid(self):
        """Leeres Grid gibt eine leere Kombination zurück."""
        from scripts.run_sweep import expand_parameter_grid

        result = expand_parameter_grid({})
        assert result == [{}]

    def test_expand_single_value_params(self):
        """Parameter mit nur einem Wert."""
        from scripts.run_sweep import expand_parameter_grid

        grid = {
            "fixed": [42],
            "variable": [1, 2, 3],
        }
        result = expand_parameter_grid(grid)

        assert len(result) == 3
        for combo in result:
            assert combo["fixed"] == 42


class TestLoadParameterGrid:
    """Tests für load_parameter_grid()."""

    def test_load_json_string(self):
        """JSON-String wird korrekt geladen."""
        from scripts.run_sweep import load_parameter_grid

        json_str = '{"short_window": [5, 10], "long_window": [50, 100]}'
        result = load_parameter_grid(json_str)

        assert result == {"short_window": [5, 10], "long_window": [50, 100]}

    def test_load_toml_file(self, tmp_path: Path):
        """TOML-Datei wird korrekt geladen."""
        from scripts.run_sweep import load_parameter_grid

        toml_content = """
[grid]
short_window = [5, 10]
long_window = [50, 100]
"""
        toml_file = tmp_path / "test_grid.toml"
        toml_file.write_text(toml_content)

        result = load_parameter_grid(str(toml_file))
        assert result == {"short_window": [5, 10], "long_window": [50, 100]}

    def test_load_invalid_raises(self):
        """Ungültige Eingabe wirft ValueError."""
        from scripts.run_sweep import load_parameter_grid

        with pytest.raises(ValueError):
            load_parameter_grid("not valid json {{{ or file")


class TestLogSweepRun:
    """Tests für log_sweep_run() Logger."""

    def test_log_sweep_run_returns_run_id(self, tmp_path: Path, monkeypatch):
        """log_sweep_run gibt eine run_id zurück."""
        from src.core.experiments import log_sweep_run, EXPERIMENTS_DIR, EXPERIMENTS_CSV

        # Experiments-Verzeichnis auf tmp_path umleiten
        test_experiments_dir = tmp_path / "experiments"
        test_experiments_csv = test_experiments_dir / "experiments.csv"
        monkeypatch.setattr("src.core.experiments.EXPERIMENTS_DIR", test_experiments_dir)
        monkeypatch.setattr("src.core.experiments.EXPERIMENTS_CSV", test_experiments_csv)

        run_id = log_sweep_run(
            strategy_key="ma_crossover",
            symbol="BTC/EUR",
            timeframe="1h",
            params={"short_window": 10, "long_window": 50},
            stats={"total_return": 0.15, "sharpe": 1.2, "max_drawdown": -0.08},
            sweep_name="test_sweep",
            tag="test",
        )

        assert run_id is not None
        assert len(run_id) > 0

    def test_log_sweep_run_creates_csv(self, tmp_path: Path, monkeypatch):
        """log_sweep_run erstellt CSV-Datei."""
        from src.core.experiments import log_sweep_run

        test_experiments_dir = tmp_path / "experiments"
        test_experiments_csv = test_experiments_dir / "experiments.csv"
        monkeypatch.setattr("src.core.experiments.EXPERIMENTS_DIR", test_experiments_dir)
        monkeypatch.setattr("src.core.experiments.EXPERIMENTS_CSV", test_experiments_csv)

        log_sweep_run(
            strategy_key="ma_crossover",
            symbol="BTC/EUR",
            timeframe="1h",
            params={"short_window": 10},
            stats={"total_return": 0.1},
        )

        assert test_experiments_csv.exists()
        content = test_experiments_csv.read_text()
        assert "sweep" in content
        assert "ma_crossover" in content

    def test_log_sweep_run_stores_params(self, tmp_path: Path, monkeypatch):
        """log_sweep_run speichert Parameter in params_json."""
        import pandas as pd
        from src.core.experiments import log_sweep_run

        test_experiments_dir = tmp_path / "experiments"
        test_experiments_csv = test_experiments_dir / "experiments.csv"
        monkeypatch.setattr("src.core.experiments.EXPERIMENTS_DIR", test_experiments_dir)
        monkeypatch.setattr("src.core.experiments.EXPERIMENTS_CSV", test_experiments_csv)

        params = {"short_window": 10, "long_window": 50}
        log_sweep_run(
            strategy_key="ma_crossover",
            symbol="BTC/EUR",
            timeframe="1h",
            params=params,
            stats={"total_return": 0.1},
        )

        df = pd.read_csv(test_experiments_csv)
        params_json = df.iloc[0]["params_json"]
        loaded_params = json.loads(params_json)
        assert loaded_params == params


class TestLogMarketScanResult:
    """Tests für log_market_scan_result() Logger."""

    def test_log_market_scan_forward_mode(self, tmp_path: Path, monkeypatch):
        """log_market_scan_result für Forward-Mode."""
        from src.core.experiments import log_market_scan_result

        test_experiments_dir = tmp_path / "experiments"
        test_experiments_csv = test_experiments_dir / "experiments.csv"
        monkeypatch.setattr("src.core.experiments.EXPERIMENTS_DIR", test_experiments_dir)
        monkeypatch.setattr("src.core.experiments.EXPERIMENTS_CSV", test_experiments_csv)

        run_id = log_market_scan_result(
            strategy_key="ma_crossover",
            symbol="BTC/EUR",
            timeframe="1h",
            mode="forward",
            signal=1.0,
            scan_name="morning_scan",
            tag="daily",
        )

        assert run_id is not None
        assert test_experiments_csv.exists()

        content = test_experiments_csv.read_text()
        assert "market_scan" in content
        assert "BTC/EUR" in content

    def test_log_market_scan_backtest_lite_mode(self, tmp_path: Path, monkeypatch):
        """log_market_scan_result für Backtest-Lite-Mode."""
        from src.core.experiments import log_market_scan_result

        test_experiments_dir = tmp_path / "experiments"
        test_experiments_csv = test_experiments_dir / "experiments.csv"
        monkeypatch.setattr("src.core.experiments.EXPERIMENTS_DIR", test_experiments_dir)
        monkeypatch.setattr("src.core.experiments.EXPERIMENTS_CSV", test_experiments_csv)

        run_id = log_market_scan_result(
            strategy_key="rsi_reversion",
            symbol="ETH/EUR",
            timeframe="4h",
            mode="backtest-lite",
            stats={"total_return": 0.08, "sharpe": 0.9, "max_drawdown": -0.05},
            scan_name="weekly_scan",
        )

        assert run_id is not None

    def test_log_market_scan_stores_signal_in_stats(self, tmp_path: Path, monkeypatch):
        """Signal wird in stats_json gespeichert."""
        import pandas as pd
        from src.core.experiments import log_market_scan_result

        test_experiments_dir = tmp_path / "experiments"
        test_experiments_csv = test_experiments_dir / "experiments.csv"
        monkeypatch.setattr("src.core.experiments.EXPERIMENTS_DIR", test_experiments_dir)
        monkeypatch.setattr("src.core.experiments.EXPERIMENTS_CSV", test_experiments_csv)

        log_market_scan_result(
            strategy_key="ma_crossover",
            symbol="BTC/EUR",
            timeframe="1h",
            mode="forward",
            signal=-1.0,
        )

        df = pd.read_csv(test_experiments_csv)
        stats_json = df.iloc[0]["stats_json"]
        stats = json.loads(stats_json)
        assert stats.get("last_signal") == -1.0


class TestAnalyticsSweepFunctions:
    """Tests für Analytics-Funktionen für Sweeps."""

    def test_filter_sweeps(self):
        """filter_sweeps filtert nur Sweep-Runs."""
        import pandas as pd
        from src.analytics.experiments_analysis import filter_sweeps

        df = pd.DataFrame({
            "run_type": ["sweep", "backtest", "sweep", "market_scan"],
            "strategy_key": ["ma", "ma", "rsi", "ma"],
        })

        result = filter_sweeps(df)
        assert len(result) == 2
        assert all(result["run_type"] == "sweep")

    def test_filter_sweeps_empty(self):
        """filter_sweeps mit leerem DataFrame."""
        import pandas as pd
        from src.analytics.experiments_analysis import filter_sweeps

        df = pd.DataFrame({"run_type": ["backtest", "market_scan"]})
        result = filter_sweeps(df)
        assert len(result) == 0


class TestAnalyticsMarketScanFunctions:
    """Tests für Analytics-Funktionen für Market-Scans."""

    def test_filter_market_scans(self):
        """filter_market_scans filtert nur Market-Scan-Runs."""
        import pandas as pd
        from src.analytics.experiments_analysis import filter_market_scans

        df = pd.DataFrame({
            "run_type": ["market_scan", "backtest", "market_scan", "sweep"],
            "symbol": ["BTC/EUR", "BTC/EUR", "ETH/EUR", "BTC/EUR"],
        })

        result = filter_market_scans(df)
        assert len(result) == 2
        assert all(result["run_type"] == "market_scan")

    def test_summarize_market_scans(self):
        """summarize_market_scans aggregiert korrekt."""
        import pandas as pd
        from src.analytics.experiments_analysis import summarize_market_scans

        df = pd.DataFrame({
            "run_type": ["market_scan", "market_scan", "market_scan"],
            "scan_name": ["daily", "daily", "daily"],
            "strategy_key": ["ma", "ma", "ma"],
            "symbol": ["BTC/EUR", "ETH/EUR", "LTC/EUR"],
            "stats_json": [
                '{"last_signal": 1.0}',
                '{"last_signal": -1.0}',
                '{"last_signal": 0.0}',
            ],
        })

        summaries = summarize_market_scans(df)
        assert len(summaries) == 1
        summary = summaries[0]
        assert summary.scan_name == "daily"
        assert summary.run_count == 3
        assert summary.long_signals == 1
        assert summary.short_signals == 1
        assert summary.flat_signals == 1


class TestSweepSummary:
    """Tests für SweepSummary Dataclass."""

    def test_sweep_summary_creation(self):
        """SweepSummary kann erstellt werden."""
        from src.analytics.experiments_analysis import SweepSummary

        summary = SweepSummary(
            sweep_name="ma_grid",
            strategy_key="ma_crossover",
            run_count=16,
            best_sharpe=1.5,
            best_return=0.25,
            best_params={"short_window": 10, "long_window": 100},
            best_run_id="abc-123",
        )

        assert summary.sweep_name == "ma_grid"
        assert summary.run_count == 16
        assert summary.best_sharpe == 1.5


class TestMarketScanSummary:
    """Tests für MarketScanSummary Dataclass."""

    def test_market_scan_summary_creation(self):
        """MarketScanSummary kann erstellt werden."""
        from src.analytics.experiments_analysis import MarketScanSummary

        summary = MarketScanSummary(
            scan_name="morning_scan",
            strategy_key="ma_crossover",
            run_count=5,
            long_signals=2,
            short_signals=1,
            flat_signals=2,
            top_symbol="BTC/EUR",
            top_signal=1.0,
        )

        assert summary.scan_name == "morning_scan"
        assert summary.run_count == 5
        assert summary.long_signals == 2


class TestSweepScriptDryRun:
    """Tests für run_sweep.py Script im Dry-Run-Modus."""

    def test_sweep_dry_run_exit_code(self):
        """Dry-Run beendet mit Exit-Code 0."""
        from scripts.run_sweep import main

        exit_code = main([
            "--strategy", "ma_crossover",
            "--symbol", "BTC/EUR",
            "--grid", '{"short_window": [5, 10]}',
            "--dry-run",
        ])

        assert exit_code == 0


class TestMarketScanScriptDryRun:
    """Tests für run_market_scan.py Script im Dry-Run-Modus."""

    def test_market_scan_dry_run_exit_code(self):
        """Dry-Run beendet mit Exit-Code 0."""
        from scripts.run_market_scan import main

        exit_code = main([
            "--strategy", "ma_crossover",
            "--symbols", "BTC/EUR,ETH/EUR",
            "--mode", "backtest-lite",
            "--dry-run",
        ])

        assert exit_code == 0
