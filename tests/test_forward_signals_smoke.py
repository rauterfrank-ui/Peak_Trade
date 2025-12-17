"""
Peak_Trade Forward-Signals Smoke Tests
=======================================
Smoke-Tests für die Forward-Signal-Pipeline.

Diese Tests verwenden Mock-/Dummy-Daten, um keine echten Exchange-Calls
zu machen.
"""

from pathlib import Path

import numpy as np
import pandas as pd

from src.core.experiments import (
    RUN_TYPE_FORWARD_SIGNAL,
    log_forward_signal_run,
)
from src.core.peak_config import PeakConfig
from src.strategies.registry import create_strategy_from_config


def create_dummy_ohlcv(n_bars: int = 100) -> pd.DataFrame:
    """Erzeugt synthetische OHLCV-Daten für Tests."""
    np.random.seed(42)

    # Zeitindex (stündlich, UTC)
    idx = pd.date_range("2025-01-01", periods=n_bars, freq="1h", tz="UTC")

    # Random Walk für Close
    returns = np.random.normal(0, 0.01, n_bars)
    trend = np.sin(np.linspace(0, 4 * np.pi, n_bars)) * 0.005
    returns = returns + trend
    close_prices = 50000 * np.exp(np.cumsum(returns))

    df = pd.DataFrame(index=idx)
    df["close"] = close_prices
    df["open"] = df["close"].shift(1).fillna(50000)

    high_bump = np.random.uniform(0, 0.003, n_bars)
    low_dip = np.random.uniform(0, 0.003, n_bars)
    df["high"] = np.maximum(df["open"], df["close"]) * (1 + high_bump)
    df["low"] = np.minimum(df["open"], df["close"]) * (1 - low_dip)

    df["volume"] = np.random.uniform(100, 1000, n_bars)

    return df[["open", "high", "low", "close", "volume"]]


def create_test_config() -> PeakConfig:
    """Erstellt eine minimale Test-Config."""
    return PeakConfig(raw={
        "strategy": {
            "ma_crossover": {
                "fast_window": 5,
                "slow_window": 20,
            },
            "rsi_reversion": {
                "rsi_period": 14,
                "oversold": 30,
                "overbought": 70,
            },
        },
        "exchange": {
            "id": "kraken",
            "sandbox": True,
        },
    })


class TestForwardSignalConstants:
    """Tests für Forward-Signal-Konstanten."""

    def test_run_type_forward_signal_exists(self):
        """Test: RUN_TYPE_FORWARD_SIGNAL ist definiert."""
        assert RUN_TYPE_FORWARD_SIGNAL == "forward_signal"

    def test_run_type_in_valid_types(self):
        """Test: forward_signal ist in VALID_RUN_TYPES."""
        from src.core.experiments import VALID_RUN_TYPES
        assert RUN_TYPE_FORWARD_SIGNAL in VALID_RUN_TYPES


class TestLogForwardSignalRun:
    """Tests für log_forward_signal_run()."""

    def test_log_forward_signal_run_returns_run_id(self, tmp_path, monkeypatch):
        """Test: log_forward_signal_run gibt eine run_id zurück."""
        # Temporäres Experiments-Verzeichnis verwenden
        temp_experiments_dir = tmp_path / "experiments"
        temp_experiments_csv = temp_experiments_dir / "experiments.csv"
        monkeypatch.setattr("src.core.experiments.EXPERIMENTS_DIR", temp_experiments_dir)
        monkeypatch.setattr("src.core.experiments.EXPERIMENTS_CSV", temp_experiments_csv)

        # Log durchführen
        run_id = log_forward_signal_run(
            strategy_key="ma_crossover",
            symbol="BTC/EUR",
            timeframe="1h",
            last_timestamp=pd.Timestamp("2025-01-01T12:00:00Z"),
            last_signal=1.0,
            last_price=50000.0,
            tag="test-run",
            config_path="config.toml",
            exchange_name="kraken",
            bars_fetched=200,
        )

        assert isinstance(run_id, str)
        assert len(run_id) > 0

    def test_log_forward_signal_run_writes_csv(self, tmp_path, monkeypatch):
        """Test: log_forward_signal_run schreibt in CSV."""
        temp_experiments_dir = tmp_path / "experiments"
        temp_experiments_csv = temp_experiments_dir / "experiments.csv"
        monkeypatch.setattr("src.core.experiments.EXPERIMENTS_DIR", temp_experiments_dir)
        monkeypatch.setattr("src.core.experiments.EXPERIMENTS_CSV", temp_experiments_csv)

        run_id = log_forward_signal_run(
            strategy_key="rsi_reversion",
            symbol="ETH/EUR",
            timeframe="4h",
            last_timestamp=pd.Timestamp("2025-01-02T08:00:00Z"),
            last_signal=-1.0,
            last_price=3000.0,
        )

        # CSV sollte jetzt existieren
        assert temp_experiments_csv.exists()

        # CSV lesen und prüfen
        df = pd.read_csv(temp_experiments_csv)
        assert len(df) == 1
        assert df.iloc[0]["run_id"] == run_id
        assert df.iloc[0]["run_type"] == "forward_signal"
        assert df.iloc[0]["strategy_key"] == "rsi_reversion"
        assert df.iloc[0]["symbol"] == "ETH/EUR"


class TestForwardSignalGeneration:
    """Tests für die Signal-Generierung."""

    def test_strategy_generates_signals(self):
        """Test: Strategie generiert Signale aus OHLCV-Daten."""
        cfg = create_test_config()
        df = create_dummy_ohlcv(100)

        strategy = create_strategy_from_config("ma_crossover", cfg)
        signals = strategy.generate_signals(df)

        assert signals is not None
        assert len(signals) == len(df)
        assert signals.index.equals(df.index)

    def test_extract_last_signal(self):
        """Test: Letztes Signal kann extrahiert werden."""
        cfg = create_test_config()
        df = create_dummy_ohlcv(100)

        strategy = create_strategy_from_config("ma_crossover", cfg)
        signals = strategy.generate_signals(df)

        last_ts = signals.index[-1]
        last_signal = float(signals.iloc[-1])
        last_price = float(df["close"].iloc[-1])

        assert isinstance(last_ts, pd.Timestamp)
        assert isinstance(last_signal, float)
        assert isinstance(last_price, float)
        assert last_signal in [-1.0, 0.0, 1.0] or np.isnan(last_signal) or abs(last_signal) <= 1.0

    def test_multiple_strategies_produce_signals(self):
        """Test: Verschiedene Strategien produzieren Signale."""
        cfg = create_test_config()
        df = create_dummy_ohlcv(100)

        for strategy_key in ["ma_crossover", "rsi_reversion"]:
            strategy = create_strategy_from_config(strategy_key, cfg)
            signals = strategy.generate_signals(df)

            assert signals is not None
            assert len(signals) > 0


class TestForwardSignalScript:
    """Tests für das run_forward_signals.py Script."""

    def test_format_signal_long(self):
        """Test: format_signal für Long-Signal."""
        # Import aus dem Script
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
        from run_forward_signals import format_signal

        assert format_signal(1.0) == "+1 (LONG)"
        assert format_signal(0.5) == "+0 (LONG)"

    def test_format_signal_short(self):
        """Test: format_signal für Short-Signal."""
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
        from run_forward_signals import format_signal

        assert format_signal(-1.0) == "-1 (SHORT)"
        assert format_signal(-0.5) == "-0 (SHORT)"

    def test_format_signal_flat(self):
        """Test: format_signal für Flat-Signal."""
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
        from run_forward_signals import format_signal

        assert format_signal(0.0) == "0 (FLAT)"


class TestEndToEndForwardSignal:
    """End-to-End Test für den Forward-Signal-Flow."""

    def test_full_forward_signal_flow(self, tmp_path, monkeypatch):
        """Test: Kompletter Forward-Signal-Flow mit Mock-Exchange."""
        # Temporäres Experiments-Verzeichnis
        temp_experiments_dir = tmp_path / "experiments"
        temp_experiments_csv = temp_experiments_dir / "experiments.csv"
        monkeypatch.setattr("src.core.experiments.EXPERIMENTS_DIR", temp_experiments_dir)
        monkeypatch.setattr("src.core.experiments.EXPERIMENTS_CSV", temp_experiments_csv)

        # 1. Config
        cfg = create_test_config()

        # 2. Dummy OHLCV-Daten (simuliert Exchange-Client)
        df = create_dummy_ohlcv(200)

        # 3. Strategie
        strategy = create_strategy_from_config("ma_crossover", cfg)

        # 4. Signale generieren
        signals = strategy.generate_signals(df)
        assert signals is not None

        # 5. Letztes Signal extrahieren
        last_ts = signals.index[-1]
        last_signal = float(signals.iloc[-1])
        last_price = float(df["close"].iloc[-1])

        # 6. In Registry loggen
        run_id = log_forward_signal_run(
            strategy_key="ma_crossover",
            symbol="BTC/EUR",
            timeframe="1h",
            last_timestamp=last_ts,
            last_signal=last_signal,
            last_price=last_price,
            tag="e2e-test",
            config_path="config.toml",
            exchange_name="mock",
            bars_fetched=len(df),
        )

        # 7. Prüfungen
        assert isinstance(run_id, str)
        assert temp_experiments_csv.exists()

        # Registry-Eintrag prüfen
        df_exp = pd.read_csv(temp_experiments_csv)
        assert len(df_exp) == 1
        assert df_exp.iloc[0]["run_type"] == "forward_signal"
        assert df_exp.iloc[0]["strategy_key"] == "ma_crossover"
        assert df_exp.iloc[0]["symbol"] == "BTC/EUR"
