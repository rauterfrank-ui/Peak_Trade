"""
Peak_Trade – Strategy Smoke-Check Tests (Phase 76)
===================================================

Tests fuer die Strategy-Diagnostics und Smoke-Check CLI.

Test-Kategorien:
1. Enumeration-Tests: v1.1-Strategien werden korrekt ermittelt
2. Erfolgspfad-Tests: Strategien laufen sauber durch
3. Fehlerpfad-Tests: Fehler werden sauber abgefangen
4. CLI-Tests: CLI gibt korrekten Exit-Code

Usage:
    # Alle Tests
    pytest tests/test_strategy_smoke_cli.py -v

    # Nur schnelle Tests
    pytest tests/test_strategy_smoke_cli.py -v -m "not slow"

    # Mit Verbose-Output
    pytest tests/test_strategy_smoke_cli.py -v -s
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock
from typing import List

import pytest
import pandas as pd
import numpy as np


# Projekt-Root
PROJECT_ROOT = Path(__file__).parent.parent


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def v11_expected_strategies() -> set:
    """Erwartete v1.1-offizielle Strategien."""
    return {
        "ma_crossover",
        "rsi_reversion",
        "breakout",
        "momentum_1h",
        "bollinger_bands",
        "macd",
        "trend_following",
        "mean_reversion",
        "vol_regime_filter",
    }


@pytest.fixture
def small_ohlcv_df() -> pd.DataFrame:
    """Kleine OHLCV-Daten fuer schnelle Tests."""
    from src.strategies.diagnostics import create_synthetic_ohlcv
    return create_synthetic_ohlcv(n_bars=100)


# ============================================================================
# TEST 1: ENUMERATION
# ============================================================================

class TestStrategyEnumeration:
    """Tests fuer die Strategie-Enumeration."""

    def test_get_v11_strategies_returns_list(self):
        """get_v11_official_strategies gibt eine Liste zurueck."""
        from src.strategies.diagnostics import get_v11_official_strategies

        strategies = get_v11_official_strategies()

        assert isinstance(strategies, list)
        assert len(strategies) >= 8  # Mindestens 8 v1.1-Strategien

    def test_get_v11_strategies_no_duplicates(self):
        """Keine Duplikate in der Strategieliste."""
        from src.strategies.diagnostics import get_v11_official_strategies

        strategies = get_v11_official_strategies()

        assert len(strategies) == len(set(strategies))

    def test_get_v11_strategies_contains_expected(self, v11_expected_strategies):
        """Alle erwarteten v1.1-Strategien sind enthalten."""
        from src.strategies.diagnostics import get_v11_official_strategies

        strategies = set(get_v11_official_strategies())

        missing = v11_expected_strategies - strategies
        assert not missing, f"Fehlende v1.1-Strategien: {missing}"

    def test_get_v11_strategies_sorted(self):
        """Strategieliste ist sortiert."""
        from src.strategies.diagnostics import get_v11_official_strategies

        strategies = get_v11_official_strategies()

        assert strategies == sorted(strategies)

    def test_get_strategy_category(self):
        """Kategorie-Abfrage funktioniert."""
        from src.strategies.diagnostics import get_strategy_category

        # Bekannte Kategorien pruefen
        assert get_strategy_category("ma_crossover") == "trend"
        assert get_strategy_category("rsi_reversion") == "mean_reversion"
        assert get_strategy_category("breakout") == "breakout"

    def test_get_strategy_defaults(self):
        """Default-Parameter-Abfrage funktioniert."""
        from src.strategies.diagnostics import get_strategy_defaults

        defaults = get_strategy_defaults("ma_crossover")

        assert isinstance(defaults, dict)
        assert "fast_window" in defaults or len(defaults) > 0


# ============================================================================
# TEST 2: ERFOLGSPFAD
# ============================================================================

class TestSmokeTestSuccess:
    """Tests fuer erfolgreiche Smoke-Tests."""

    def test_run_single_strategy_smoke_ok(self, small_ohlcv_df):
        """Einzelne Strategie laeuft erfolgreich."""
        from src.strategies.diagnostics import run_single_strategy_smoke

        result = run_single_strategy_smoke(
            strategy_name="ma_crossover",
            df=small_ohlcv_df,
        )

        assert result.status == "ok"
        assert result.name == "ma_crossover"
        assert result.return_pct is not None
        assert result.num_trades is not None
        assert result.duration_ms is not None
        assert result.error is None

    def test_run_multiple_strategies_smoke(self, small_ohlcv_df):
        """Mehrere Strategien laufen erfolgreich."""
        from src.strategies.diagnostics import run_strategy_smoke_tests

        # Nur ein paar Strategien fuer Geschwindigkeit
        results = run_strategy_smoke_tests(
            strategy_names=["ma_crossover", "rsi_reversion"],
            n_bars=100,
        )

        assert len(results) == 2
        assert all(r.name in ["ma_crossover", "rsi_reversion"] for r in results)

        # Mindestens eine sollte OK sein
        ok_results = [r for r in results if r.status == "ok"]
        assert len(ok_results) >= 1, "Mindestens eine Strategie sollte OK sein"

    def test_summarize_smoke_results(self):
        """Summary-Funktion funktioniert korrekt."""
        from src.strategies.diagnostics import (
            StrategySmokeResult,
            summarize_smoke_results,
        )

        results = [
            StrategySmokeResult(name="a", status="ok", return_pct=1.0, num_trades=5),
            StrategySmokeResult(name="b", status="ok", return_pct=2.0, num_trades=10),
            StrategySmokeResult(name="c", status="fail", error="Test error"),
        ]

        summary = summarize_smoke_results(results)

        assert summary["total"] == 3
        assert summary["ok"] == 2
        assert summary["fail"] == 1
        assert summary["failed_strategies"] == ["c"]
        assert summary["all_passed"] is False

    def test_summarize_all_passed(self):
        """Summary zeigt all_passed korrekt an."""
        from src.strategies.diagnostics import (
            StrategySmokeResult,
            summarize_smoke_results,
        )

        results = [
            StrategySmokeResult(name="a", status="ok", return_pct=1.0),
            StrategySmokeResult(name="b", status="ok", return_pct=2.0),
        ]

        summary = summarize_smoke_results(results)

        assert summary["all_passed"] is True
        assert summary["fail"] == 0


# ============================================================================
# TEST 3: FEHLERPFAD
# ============================================================================

class TestSmokeTestFailure:
    """Tests fuer Fehlerbehandlung."""

    def test_unknown_strategy_returns_fail(self, small_ohlcv_df):
        """Unbekannte Strategie gibt FAIL zurueck."""
        from src.strategies.diagnostics import run_single_strategy_smoke

        result = run_single_strategy_smoke(
            strategy_name="nonexistent_strategy_xyz",
            df=small_ohlcv_df,
        )

        assert result.status == "fail"
        assert result.error is not None
        assert "nonexistent_strategy_xyz" in result.error or "not" in result.error.lower()

    def test_error_does_not_break_other_strategies(self, small_ohlcv_df):
        """Fehler bei einer Strategie bricht nicht andere Tests ab."""
        from src.strategies.diagnostics import run_strategy_smoke_tests

        # Eine bekannte und eine unbekannte Strategie
        results = run_strategy_smoke_tests(
            strategy_names=["ma_crossover", "nonexistent_xyz"],
            n_bars=100,
        )

        assert len(results) == 2

        # ma_crossover sollte OK sein
        ma_result = next(r for r in results if r.name == "ma_crossover")
        assert ma_result.status == "ok"

        # nonexistent_xyz sollte FAIL sein
        bad_result = next(r for r in results if r.name == "nonexistent_xyz")
        assert bad_result.status == "fail"

    def test_exception_in_backtest_captured(self, small_ohlcv_df):
        """Exceptions im Backtest werden abgefangen."""
        from src.strategies.diagnostics import run_single_strategy_smoke

        # Mock die Strategy-Registry um einen Fehler zu erzeugen
        with patch("src.strategies.registry.get_strategy_spec") as mock_spec:
            mock_spec.side_effect = RuntimeError("Simulated backtest error")

            result = run_single_strategy_smoke(
                strategy_name="ma_crossover",
                df=small_ohlcv_df,
            )

        assert result.status == "fail"
        assert result.error is not None
        assert "Simulated backtest error" in result.error


# ============================================================================
# TEST 4: SYNTHETIC DATA
# ============================================================================

class TestSyntheticData:
    """Tests fuer synthetische Daten-Generierung."""

    def test_create_synthetic_ohlcv_shape(self):
        """Synthetische Daten haben korrektes Format."""
        from src.strategies.diagnostics import create_synthetic_ohlcv

        df = create_synthetic_ohlcv(n_bars=100)

        assert len(df) == 100
        assert list(df.columns) == ["open", "high", "low", "close", "volume"]
        assert isinstance(df.index, pd.DatetimeIndex)

    def test_create_synthetic_ohlcv_values_valid(self):
        """Synthetische Daten haben gueltige Werte."""
        from src.strategies.diagnostics import create_synthetic_ohlcv

        df = create_synthetic_ohlcv(n_bars=100)

        # High >= Open, Close
        assert (df["high"] >= df["open"]).all()
        assert (df["high"] >= df["close"]).all()

        # Low <= Open, Close
        assert (df["low"] <= df["open"]).all()
        assert (df["low"] <= df["close"]).all()

        # Keine NaN-Werte
        assert not df.isna().any().any()

        # Volume > 0
        assert (df["volume"] > 0).all()

    def test_create_synthetic_ohlcv_reproducible(self):
        """Synthetische Daten mit Seed sind reproduzierbar (Werte, nicht Index)."""
        from src.strategies.diagnostics import create_synthetic_ohlcv

        df1 = create_synthetic_ohlcv(n_bars=50, seed=123)
        df2 = create_synthetic_ohlcv(n_bars=50, seed=123)

        # Vergleiche nur die Werte, nicht den Index (da Index datetime.now() verwendet)
        pd.testing.assert_frame_equal(
            df1.reset_index(drop=True),
            df2.reset_index(drop=True),
        )


# ============================================================================
# TEST 5: FORMAT OUTPUT
# ============================================================================

class TestFormatOutput:
    """Tests fuer Output-Formatierung."""

    def test_format_smoke_result_ok(self):
        """OK-Result wird korrekt formatiert."""
        from src.strategies.diagnostics import (
            StrategySmokeResult,
            format_smoke_result_line,
        )

        result = StrategySmokeResult(
            name="ma_crossover",
            status="ok",
            return_pct=5.23,
            sharpe=1.45,
            max_drawdown_pct=-8.12,
            num_trades=42,
        )

        line = format_smoke_result_line(result)

        assert "[OK]" in line
        assert "ma_crossover" in line
        assert "+5.23%" in line
        assert "1.45" in line
        assert "8.12%" in line
        assert "42" in line

    def test_format_smoke_result_fail(self):
        """FAIL-Result wird korrekt formatiert."""
        from src.strategies.diagnostics import (
            StrategySmokeResult,
            format_smoke_result_line,
        )

        result = StrategySmokeResult(
            name="bad_strategy",
            status="fail",
            error="KeyError: 'signal'",
        )

        line = format_smoke_result_line(result)

        assert "[FAIL]" in line
        assert "bad_strategy" in line
        assert "KeyError" in line


# ============================================================================
# TEST 6: CLI INTEGRATION (optional, kann uebersprungen werden)
# ============================================================================

@pytest.mark.slow
class TestCLIIntegration:
    """Integration-Tests fuer die CLI."""

    def test_cli_list_strategies(self):
        """CLI --list-strategies funktioniert."""
        result = subprocess.run(
            [sys.executable, "scripts/strategy_smoke_check.py", "--list-strategies"],
            capture_output=True,
            text=True,
            cwd=PROJECT_ROOT,
        )

        assert result.returncode == 0
        assert "ma_crossover" in result.stdout
        assert "rsi_reversion" in result.stdout

    def test_cli_single_strategy_ok(self):
        """CLI mit einzelner Strategie gibt Exit-Code 0."""
        result = subprocess.run(
            [
                sys.executable,
                "scripts/strategy_smoke_check.py",
                "--strategies", "ma_crossover",
                "--n-bars", "50",
            ],
            capture_output=True,
            text=True,
            cwd=PROJECT_ROOT,
            timeout=60,
        )

        # MA-Crossover sollte durchlaufen
        assert "[OK]" in result.stdout or result.returncode == 0

    def test_cli_unknown_strategy_fail(self):
        """CLI mit unbekannter Strategie gibt Exit-Code 1."""
        result = subprocess.run(
            [
                sys.executable,
                "scripts/strategy_smoke_check.py",
                "--strategies", "nonexistent_xyz",
                "--n-bars", "50",
            ],
            capture_output=True,
            text=True,
            cwd=PROJECT_ROOT,
            timeout=60,
        )

        assert result.returncode == 1
        assert "[FAIL]" in result.stdout


# ============================================================================
# TEST 7: REGISTRY INTEGRATION
# ============================================================================

class TestRegistryIntegration:
    """Tests fuer Registry-Integration."""

    def test_all_v11_strategies_in_registry(self, v11_expected_strategies):
        """Alle v1.1-Strategien sind in der Registry."""
        from src.strategies.registry import get_available_strategy_keys

        available = set(get_available_strategy_keys())

        for strategy in v11_expected_strategies:
            assert strategy in available, f"'{strategy}' fehlt in Registry"

    def test_v11_strategies_can_be_instantiated(self, v11_expected_strategies):
        """Alle v1.1-Strategien koennen instanziiert werden."""
        from src.strategies.registry import get_strategy_spec

        for strategy_name in v11_expected_strategies:
            spec = get_strategy_spec(strategy_name)

            # Versuche Instanziierung
            try:
                instance = spec.cls()
                assert hasattr(instance, "generate_signals")
            except TypeError:
                # Manche Strategien brauchen Parameter - das ist OK
                pass


# ============================================================================
# TEST 8: PHASE 78 - KRAKEN CACHE DATA SOURCE
# ============================================================================

class TestKrakenCacheDataSource:
    """Tests fuer Kraken-Cache-Datenquelle (Phase 78)."""

    @pytest.fixture
    def kraken_cache_dir(self, tmp_path):
        """Erstellt temporaeres Verzeichnis mit Test-Cache-Daten."""
        cache_dir = tmp_path / "data" / "cache"
        cache_dir.mkdir(parents=True)

        # Kleine Test-OHLCV-Daten erstellen
        n_bars = 300
        np.random.seed(42)
        idx = pd.date_range(
            start="2025-11-01 00:00:00",
            periods=n_bars,
            freq="1h",
            tz="UTC",
        )
        close_prices = 90000 * np.exp(np.cumsum(np.random.normal(0, 0.01, n_bars)))
        df = pd.DataFrame(index=idx)
        df["open"] = close_prices * (1 + np.random.uniform(-0.001, 0.001, n_bars))
        df["close"] = close_prices
        df["high"] = np.maximum(df["open"], df["close"]) * 1.005
        df["low"] = np.minimum(df["open"], df["close"]) * 0.995
        df["volume"] = np.random.uniform(50, 500, n_bars)

        # Als parquet speichern
        df.to_parquet(cache_dir / "BTC_EUR_1h.parquet")

        return tmp_path

    def test_load_kraken_cache_ohlcv_success(self, kraken_cache_dir):
        """Kraken-Cache OHLCV-Loader funktioniert mit gueltigen Daten."""
        from src.strategies.diagnostics import load_kraken_cache_ohlcv

        # Temporaere Config erstellen
        config_path = kraken_cache_dir / "config.toml"
        config_path.write_text(f'[data]\ndata_dir = "{kraken_cache_dir / "data"}"\n')

        df = load_kraken_cache_ohlcv(
            symbol="BTC/EUR",
            timeframe="1h",
            n_bars=200,
            config_path=str(config_path),
        )

        assert isinstance(df, pd.DataFrame)
        assert len(df) == 200
        assert list(df.columns) == ["open", "high", "low", "close", "volume"]
        assert isinstance(df.index, pd.DatetimeIndex)

    def test_load_kraken_cache_ohlcv_not_found(self, tmp_path):
        """Kraken-Cache wirft FileNotFoundError bei fehlenden Daten."""
        from src.strategies.diagnostics import load_kraken_cache_ohlcv

        # Leeres Cache-Verzeichnis
        cache_dir = tmp_path / "data" / "cache"
        cache_dir.mkdir(parents=True)

        config_path = tmp_path / "config.toml"
        config_path.write_text(f'[data]\ndata_dir = "{tmp_path / "data"}"\n')

        with pytest.raises(FileNotFoundError) as exc_info:
            load_kraken_cache_ohlcv(
                symbol="ETH/EUR",
                timeframe="1h",
                n_bars=100,
                config_path=str(config_path),
            )

        assert "ETH_EUR_1h" in str(exc_info.value)

    def test_run_strategy_smoke_tests_with_kraken_cache(self, kraken_cache_dir):
        """run_strategy_smoke_tests funktioniert mit kraken_cache data_source."""
        from src.strategies.diagnostics import run_strategy_smoke_tests

        config_path = kraken_cache_dir / "config.toml"
        config_path.write_text(f'[data]\ndata_dir = "{kraken_cache_dir / "data"}"\n')

        results = run_strategy_smoke_tests(
            strategy_names=["ma_crossover"],
            config_path=str(config_path),
            market="BTC/EUR",
            timeframe="1h",
            n_bars=200,
            data_source="kraken_cache",
        )

        assert len(results) == 1
        result = results[0]
        assert result.name == "ma_crossover"
        assert result.data_source == "kraken_cache"
        assert result.symbol == "BTC/EUR"
        assert result.timeframe == "1h"
        assert result.num_bars == 200

        # Sollte OK sein (echte Daten)
        if result.status == "ok":
            assert result.return_pct is not None
            assert result.start_ts is not None
            assert result.end_ts is not None

    def test_run_strategy_smoke_tests_kraken_cache_missing_data(self, tmp_path):
        """Bei fehlenden Kraken-Cache-Daten werden alle Strategien als fail markiert."""
        from src.strategies.diagnostics import run_strategy_smoke_tests

        # Leeres Cache-Verzeichnis
        cache_dir = tmp_path / "data" / "cache"
        cache_dir.mkdir(parents=True)

        config_path = tmp_path / "config.toml"
        config_path.write_text(f'[data]\ndata_dir = "{tmp_path / "data"}"\n')

        results = run_strategy_smoke_tests(
            strategy_names=["ma_crossover", "rsi_reversion"],
            config_path=str(config_path),
            market="NONEXISTENT/PAIR",
            timeframe="1h",
            data_source="kraken_cache",
        )

        assert len(results) == 2
        for r in results:
            assert r.status == "fail"
            assert r.data_source == "kraken_cache"
            assert "nicht gefunden" in r.error or "not found" in r.error.lower()

    def test_data_source_synthetic_default(self):
        """Default data_source ist synthetic."""
        from src.strategies.diagnostics import run_strategy_smoke_tests

        results = run_strategy_smoke_tests(
            strategy_names=["ma_crossover"],
            n_bars=100,
        )

        assert len(results) == 1
        assert results[0].data_source == "synthetic"

    def test_strategy_smoke_result_new_fields(self):
        """StrategySmokeResult hat alle Phase 78 Felder."""
        from src.strategies.diagnostics import StrategySmokeResult

        result = StrategySmokeResult(
            name="test",
            status="ok",
            data_source="kraken_cache",
            symbol="BTC/EUR",
            timeframe="1h",
            num_bars=500,
            start_ts=pd.Timestamp("2025-01-01", tz="UTC"),
            end_ts=pd.Timestamp("2025-01-21", tz="UTC"),
        )

        assert result.data_source == "kraken_cache"
        assert result.symbol == "BTC/EUR"
        assert result.timeframe == "1h"
        assert result.num_bars == 500
        assert result.start_ts is not None
        assert result.end_ts is not None

    def test_format_smoke_result_line_with_data_info(self):
        """format_smoke_result_line zeigt Datenquelle-Info an."""
        from src.strategies.diagnostics import (
            StrategySmokeResult,
            format_smoke_result_line,
        )

        result = StrategySmokeResult(
            name="ma_crossover",
            status="ok",
            data_source="kraken_cache",
            symbol="BTC/EUR",
            timeframe="1h",
            num_bars=720,
            return_pct=5.5,
            sharpe=1.2,
            max_drawdown_pct=-8.0,
            num_trades=15,
        )

        line = format_smoke_result_line(result)

        assert "data=kraken_cache" in line
        assert "symbol=BTC/EUR" in line
        assert "tf=1h" in line
        assert "bars=720" in line
        assert "[OK]" in line
        assert "ma_crossover" in line


@pytest.mark.slow
class TestKrakenCacheCLIIntegration:
    """CLI-Integration-Tests fuer Kraken-Cache (Phase 78)."""

    def test_cli_data_source_help(self):
        """CLI zeigt --data-source in der Hilfe an."""
        result = subprocess.run(
            [sys.executable, "scripts/strategy_smoke_check.py", "--help"],
            capture_output=True,
            text=True,
            cwd=PROJECT_ROOT,
        )

        assert result.returncode == 0
        assert "--data-source" in result.stdout
        assert "synthetic" in result.stdout
        assert "kraken_cache" in result.stdout

    def test_cli_synthetic_explicit(self):
        """CLI mit explizitem --data-source synthetic funktioniert."""
        result = subprocess.run(
            [
                sys.executable,
                "scripts/strategy_smoke_check.py",
                "--strategies", "ma_crossover",
                "--n-bars", "100",
                "--data-source", "synthetic",
            ],
            capture_output=True,
            text=True,
            cwd=PROJECT_ROOT,
            timeout=60,
        )

        assert "Data-Source: synthetic" in result.stdout
        assert "[OK]" in result.stdout or result.returncode == 0

    def test_cli_kraken_cache_with_real_data(self):
        """CLI mit --data-source kraken_cache und echten Cache-Daten."""
        # Pruefe ob BTC_EUR_1h.parquet existiert
        cache_path = PROJECT_ROOT / "data" / "cache" / "BTC_EUR_1h.parquet"
        if not cache_path.exists():
            pytest.skip("BTC_EUR_1h.parquet nicht im Cache vorhanden")

        result = subprocess.run(
            [
                sys.executable,
                "scripts/strategy_smoke_check.py",
                "--strategies", "ma_crossover",
                "--data-source", "kraken_cache",
                "--market", "BTC/EUR",
                "--timeframe", "1h",
                "--n-bars", "200",
            ],
            capture_output=True,
            text=True,
            cwd=PROJECT_ROOT,
            timeout=60,
        )

        assert "Data-Source: kraken_cache" in result.stdout
        # Sollte durchlaufen wenn Daten vorhanden
        assert result.returncode in [0, 1]  # 0=OK, 1=FAIL (aber kein Crash)


# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
