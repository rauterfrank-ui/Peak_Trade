"""
Tests für src/backtest/walkforward.py
=====================================

Testet Walk-Forward-Backtesting-Funktionalität.
"""
import sys
from pathlib import Path

# Projekt-Root zum Path hinzufügen
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

from src.backtest.walkforward import (
    WalkForwardConfig,
    WalkForwardResult,
    split_train_test_windows,
    run_walkforward_for_config,
    run_walkforward_for_top_n_from_sweep,
)
from src.strategies.ma_crossover import generate_signals as ma_signals


# =============================================================================
# TEST FIXTURES
# =============================================================================


def create_test_data(n_bars: int = 500, seed: int = 42, freq: str = "1d") -> pd.DataFrame:
    """
    Erstellt deterministische Test-Daten für Walk-Forward-Tests.

    Args:
        n_bars: Anzahl der Bars (bei freq='1d' entspricht dies Tagen)
        seed: Random Seed für Reproduzierbarkeit
        freq: Frequenz der Bars ('1d' für täglich, '1h' für stündlich)

    Returns:
        DataFrame mit OHLCV-Daten und DatetimeIndex

    Note:
        Mit n_bars=500 und freq='1d' ergibt sich ein Zeitraum von ca. 500 Tagen,
        ausreichend für Walk-Forward-Tests mit train_window=90d + test_window=30d.
    """
    np.random.seed(seed)

    # Start-Zeitpunkt
    start = datetime(2020, 1, 1)
    dates = pd.date_range(start, periods=n_bars, freq=freq)

    # Preis-Simulation mit Trend und Oszillation
    base_price = 50000
    trend = np.linspace(0, 5000, n_bars)
    cycle = np.sin(np.linspace(0, 6 * np.pi, n_bars)) * 2000
    noise = np.random.randn(n_bars).cumsum() * 200

    close_prices = base_price + trend + cycle + noise

    # OHLC generieren
    df = pd.DataFrame({
        'open': close_prices * (1 + np.random.randn(n_bars) * 0.002),
        'high': close_prices * (1 + abs(np.random.randn(n_bars)) * 0.003),
        'low': close_prices * (1 - abs(np.random.randn(n_bars)) * 0.003),
        'close': close_prices,
        'volume': np.random.randint(10, 100, n_bars)
    }, index=dates)

    return df


# =============================================================================
# TESTS FOR split_train_test_windows
# =============================================================================


class TestSplitTrainTestWindows:
    """Tests für split_train_test_windows()."""

    def test_split_windows_basic(self):
        """Grundlegender Test: Fenster werden korrekt aufgeteilt."""
        start = pd.Timestamp("2020-01-01")
        end = pd.Timestamp("2020-12-31")
        config = WalkForwardConfig(train_window="180d", test_window="30d")

        windows = split_train_test_windows(start, end, config)

        # Sollte mehrere Fenster erzeugen
        assert len(windows) > 0

        # Prüfe erstes Fenster
        train_start, train_end, test_start, test_end = windows[0]
        assert train_start == start
        assert train_end == train_start + pd.Timedelta("180d")
        assert test_start == train_end
        assert test_end == test_start + pd.Timedelta("30d")

    def test_split_windows_no_overlap(self):
        """Fenster sollten lückenlos und ohne Überlappung aufeinander folgen (anchored mode)."""
        start = pd.Timestamp("2020-01-01")
        end = pd.Timestamp("2020-12-31")
        # step_size=None -> anchored mode: Fenster folgen lückenlos
        config = WalkForwardConfig(train_window="90d", test_window="30d")

        windows = split_train_test_windows(start, end, config)

        # Prüfe, dass Fenster lückenlos aufeinander folgen (anchored mode)
        for i in range(len(windows) - 1):
            _, _, _, test_end_current = windows[i]
            train_start_next, _, _, _ = windows[i + 1]

            # Anchored mode: nächstes Train-Fenster startet exakt am Ende des aktuellen Test-Fensters
            assert train_start_next == test_end_current, (
                f"Fenster {i} -> {i+1}: train_start_next ({train_start_next}) "
                f"sollte == test_end_current ({test_end_current}) sein"
            )

    def test_split_windows_last_incomplete_discarded(self):
        """Unvollständige Fenster am Ende werden verworfen."""
        start = pd.Timestamp("2020-01-01")
        end = pd.Timestamp("2020-06-15")  # Zu kurz für vollständiges Fenster nach erstem
        config = WalkForwardConfig(train_window="90d", test_window="30d")

        windows = split_train_test_windows(start, end, config)

        # Prüfe, dass alle Fenster vollständig sind
        for train_start, train_end, test_start, test_end in windows:
            # Train-Fenster muss vollständig sein
            assert train_end <= end
            # Test-Fenster muss vollständig sein
            assert test_end <= end

    def test_split_windows_count(self):
        """Anzahl der Fenster sollte korrekt sein (anchored mode)."""
        start = pd.Timestamp("2020-01-01")
        end = pd.Timestamp("2020-12-31")  # 365 Tage
        # Anchored mode: train+test = 90d+30d = 120d pro Fenster (lückenlos)
        config = WalkForwardConfig(train_window="90d", test_window="30d")

        windows = split_train_test_windows(start, end, config)

        # Erwartete Anzahl (anchored): 365 / 120 = ca. 3 vollständige Fenster
        assert len(windows) >= 2
        assert len(windows) <= 4

    def test_split_windows_custom_step_size(self):
        """Custom step_size wird korrekt verwendet (rolling mode)."""
        start = pd.Timestamp("2020-01-01")
        end = pd.Timestamp("2020-12-31")
        # step_size definiert den Abstand zwischen aufeinanderfolgenden train_start-Zeitpunkten
        config = WalkForwardConfig(
            train_window="90d",
            test_window="30d",
            step_size="60d"  # Rolling: train_start verschiebt sich um 60d
        )

        windows = split_train_test_windows(start, end, config)

        # Mit step_size=60d sollten mehr Fenster entstehen als im anchored mode
        # (weil Fenster sich überlappen können)
        assert len(windows) > 0

        # Prüfe, dass train_start um step_size verschoben wird
        if len(windows) > 1:
            train_start_first, _, _, _ = windows[0]
            train_start_second, _, _, _ = windows[1]
            step = train_start_second - train_start_first
            # Schritt sollte exakt step_size sein
            assert step == pd.Timedelta("60d"), (
                f"step zwischen train_starts sollte 60d sein, ist aber {step}"
            )

    def test_split_windows_too_short_raises(self):
        """Zu kurzer Zeitraum sollte ValueError werfen."""
        start = pd.Timestamp("2020-01-01")
        end = pd.Timestamp("2020-02-01")  # Nur 31 Tage
        config = WalkForwardConfig(train_window="90d", test_window="30d")  # Benötigt 120 Tage

        with pytest.raises(ValueError, match=".*zu kurz.*"):
            split_train_test_windows(start, end, config)

    def test_split_windows_invalid_window_raises(self):
        """Ungültige Fenster-Dauer sollte ValueError werfen."""
        start = pd.Timestamp("2020-01-01")
        end = pd.Timestamp("2020-12-31")
        config = WalkForwardConfig(train_window="invalid", test_window="30d")

        with pytest.raises(ValueError, match=".*Ungültige Fenster-Dauer.*"):
            split_train_test_windows(start, end, config)


# =============================================================================
# TESTS FOR run_walkforward_for_config
# =============================================================================


class TestRunWalkforwardForConfig:
    """Tests für run_walkforward_for_config()."""

    def test_run_walkforward_basic(self):
        """Grundlegender Test: Walk-Forward läuft durch."""
        # 500 Tage Daten (2020-01-01 bis 2021-05-15)
        # Mit train=90d + test=30d = 120d pro Fenster -> ca. 4 Fenster möglich
        df = create_test_data(n_bars=500)
        config = WalkForwardConfig(
            train_window="90d",
            test_window="30d",
        )

        # Einfache Strategie-Parameter
        strategy_params = {
            "fast_period": 10,
            "slow_period": 30,
            "stop_pct": 0.02,
        }

        result = run_walkforward_for_config(
            config_id="test_config_1",
            wf_config=config,
            df=df,
            strategy_name="ma_crossover",
            strategy_params=strategy_params,
            strategy_signal_fn=ma_signals,
        )

        # Prüfe Ergebnis-Struktur
        assert isinstance(result, WalkForwardResult)
        assert result.config_id == "test_config_1"
        assert result.strategy_name == "ma_crossover"
        assert len(result.windows) > 0

    def test_run_walkforward_creates_windows(self):
        """Es sollten mehrere Fenster-Ergebnisse erzeugt werden."""
        # 500 Tage Daten, train=60d + test=30d = 90d pro Fenster -> ca. 5 Fenster
        # test_window=30d weil BacktestEngine mind. 30 Bars benötigt (slow_period=30)
        df = create_test_data(n_bars=500)
        config = WalkForwardConfig(
            train_window="60d",
            test_window="30d",
        )

        strategy_params = {
            "fast_period": 10,
            "slow_period": 30,
            "stop_pct": 0.02,
        }

        result = run_walkforward_for_config(
            config_id="test_config_2",
            wf_config=config,
            df=df,
            strategy_name="ma_crossover",
            strategy_params=strategy_params,
            strategy_signal_fn=ma_signals,
        )

        # Sollte mehrere Fenster haben (500d / 90d = ~5 Fenster)
        assert len(result.windows) >= 2

        # Prüfe Fenster-Struktur
        for window in result.windows:
            assert window.window_index >= 0
            assert window.train_start < window.train_end
            assert window.test_start < window.test_end
            assert window.train_end <= window.test_start
            assert window.test_result is not None
            assert isinstance(window.metrics, dict)

    def test_run_walkforward_aggregate_metrics(self):
        """Aggregierte Metriken sollten berechnet werden."""
        # 500 Tage Daten, train=90d + test=30d = 120d pro Fenster -> ca. 4 Fenster
        df = create_test_data(n_bars=500)
        config = WalkForwardConfig(
            train_window="90d",
            test_window="30d",
        )

        strategy_params = {
            "fast_period": 10,
            "slow_period": 30,
            "stop_pct": 0.02,
        }

        result = run_walkforward_for_config(
            config_id="test_config_3",
            wf_config=config,
            df=df,
            strategy_name="ma_crossover",
            strategy_params=strategy_params,
            strategy_signal_fn=ma_signals,
        )

        # Prüfe aggregierte Metriken
        assert isinstance(result.aggregate_metrics, dict)
        assert len(result.aggregate_metrics) > 0

        # Erwartete Metriken
        assert "avg_sharpe" in result.aggregate_metrics
        assert "avg_return" in result.aggregate_metrics
        assert "total_windows" in result.aggregate_metrics
        assert "win_rate_windows" in result.aggregate_metrics

        # Prüfe Werte
        assert result.aggregate_metrics["total_windows"] == len(result.windows)
        assert 0.0 <= result.aggregate_metrics["win_rate_windows"] <= 1.0

    def test_run_walkforward_with_date_range(self):
        """Funktioniert mit explizitem Start-/Enddatum."""
        # 500 Tage Daten: 2020-01-01 bis 2021-05-15
        # Zeitraum 2020-02-01 bis 2020-08-01 liegt innerhalb (ca. 180 Tage)
        # Mit train=60d + test=30d = 90d pro Fenster -> ca. 2 Fenster möglich
        # test_window=30d weil BacktestEngine mind. 30 Bars benötigt (slow_period=30)
        df = create_test_data(n_bars=500)
        config = WalkForwardConfig(
            train_window="60d",
            test_window="30d",
            start_date=pd.Timestamp("2020-02-01"),
            end_date=pd.Timestamp("2020-08-01"),
        )

        strategy_params = {
            "fast_period": 10,
            "slow_period": 30,
            "stop_pct": 0.02,
        }

        result = run_walkforward_for_config(
            config_id="test_config_4",
            wf_config=config,
            df=df,
            strategy_name="ma_crossover",
            strategy_params=strategy_params,
            strategy_signal_fn=ma_signals,
        )

        # Prüfe, dass mindestens ein Fenster erstellt wurde
        assert len(result.windows) >= 1

        # Prüfe, dass Zeitraum eingehalten wurde
        first_window = result.windows[0]
        assert first_window.train_start >= config.start_date
        last_window = result.windows[-1]
        assert last_window.test_end <= config.end_date

    def test_run_walkforward_missing_data_raises(self):
        """Fehlende Daten sollten ValueError werfen."""
        config = WalkForwardConfig(
            train_window="90d",
            test_window="30d",
        )

        with pytest.raises(ValueError, match=".*DataFrame muss übergeben werden.*"):
            run_walkforward_for_config(
                config_id="test_config_5",
                wf_config=config,
                df=None,
                strategy_name="ma_crossover",
                strategy_params={"fast_period": 10, "slow_period": 30},
            )

    def test_run_walkforward_empty_dataframe_raises(self):
        """Leerer DataFrame sollte ValueError werfen."""
        df = pd.DataFrame()
        config = WalkForwardConfig(
            train_window="90d",
            test_window="30d",
        )

        with pytest.raises(ValueError, match=".*darf nicht leer sein.*"):
            run_walkforward_for_config(
                config_id="test_config_6",
                wf_config=config,
                df=df,
                strategy_name="ma_crossover",
                strategy_params={"fast_period": 10, "slow_period": 30},
            )

    def test_run_walkforward_invalid_datetime_index_raises(self):
        """DataFrame ohne DatetimeIndex sollte ValueError werfen."""
        df = pd.DataFrame({
            'open': [100, 101, 102],
            'high': [101, 102, 103],
            'low': [99, 100, 101],
            'close': [100, 101, 102],
            'volume': [10, 11, 12],
        })
        # Kein DatetimeIndex
        config = WalkForwardConfig(
            train_window="90d",
            test_window="30d",
        )

        with pytest.raises(ValueError, match=".*DatetimeIndex.*"):
            run_walkforward_for_config(
                config_id="test_config_7",
                wf_config=config,
                df=df,
                strategy_name="ma_crossover",
                strategy_params={"fast_period": 10, "slow_period": 30},
            )

    def test_run_walkforward_window_metrics_populated(self):
        """Fenster-Metriken sollten befüllt sein."""
        # 500 Tage Daten, train=90d + test=30d = 120d pro Fenster -> ca. 4 Fenster
        df = create_test_data(n_bars=500)
        config = WalkForwardConfig(
            train_window="90d",
            test_window="30d",
        )

        strategy_params = {
            "fast_period": 10,
            "slow_period": 30,
            "stop_pct": 0.02,
        }

        result = run_walkforward_for_config(
            config_id="test_config_8",
            wf_config=config,
            df=df,
            strategy_name="ma_crossover",
            strategy_params=strategy_params,
            strategy_signal_fn=ma_signals,
        )

        # Prüfe, dass Fenster-Metriken vorhanden sind
        for window in result.windows:
            assert len(window.metrics) > 0
            # Mindestens einige Standard-Metriken sollten vorhanden sein
            assert "sharpe" in window.metrics or "total_return" in window.metrics


# =============================================================================
# INTEGRATION TESTS (Optional)
# =============================================================================


class TestWalkforwardTopNIntegration:
    """Integration-Tests für run_walkforward_for_top_n_from_sweep()."""

    @pytest.mark.skip(reason="Benötigt Sweep-Ergebnisse - nur manuell ausführen")
    def test_run_walkforward_for_top_n_basic(self):
        """
        Integrationstest: Walk-Forward für Top-N aus Sweep.

        HINWEIS: Dieser Test benötigt existierende Sweep-Ergebnisse.
        Führe zuerst einen Sweep aus:
            python scripts/run_strategy_sweep.py --sweep-name rsi_reversion_basic --max-runs 10
        """
        df = create_test_data(n_bars=1000)
        config = WalkForwardConfig(
            train_window="180d",
            test_window="30d",
        )

        # Dieser Test würde echte Sweep-Ergebnisse benötigen
        # Für automatische Tests: Mock oder Fixture erstellen
        results = run_walkforward_for_top_n_from_sweep(
            sweep_name="rsi_reversion_basic",
            wf_config=config,
            top_n=3,
            df=df,
        )

        assert len(results) > 0
        assert all(isinstance(r, WalkForwardResult) for r in results)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

