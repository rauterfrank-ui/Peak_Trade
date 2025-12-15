"""
Tests für OfflineRealtimeFeed v0 (IDEA-DATA-010)
================================================

Testet:
- Grundlegende Tick-Generierung
- Safety-Gate Integration
- Regime-Switching Verhalten
- GARCH Volatilitäts-Modell
"""
from __future__ import annotations

from typing import List

import numpy as np
import pandas as pd
import pytest

from src.data.feeds import (
    OfflineRealtimeFeed,
    OfflineRealtimeFeedConfig,
    RegimeConfig,
    SyntheticTick,
)
from src.data.safety import (
    DataSafetyViolationError,
    DataUsageContextKind,
)


def create_sample_ohlcv(n_bars: int = 10, start_price: float = 100.0) -> pd.DataFrame:
    """Erstellt einen einfachen OHLCV DataFrame für Tests."""
    dates = pd.date_range(
        start="2024-01-01 00:00:00",
        periods=n_bars,
        freq="1min",
        tz="UTC",
    )

    np.random.seed(42)
    prices = [start_price]
    for _ in range(n_bars - 1):
        change = np.random.normal(0, 0.001)
        prices.append(prices[-1] * (1 + change))

    ohlcv = pd.DataFrame(
        {
            "open": prices,
            "high": [p * 1.001 for p in prices],
            "low": [p * 0.999 for p in prices],
            "close": prices,
            "volume": [1000.0] * n_bars,
        },
        index=dates,
    )
    return ohlcv


def create_simple_config(
    usage_context: DataUsageContextKind = DataUsageContextKind.BACKTEST,
    n_regimes: int = 2,
    seed: int = 42,
) -> OfflineRealtimeFeedConfig:
    """Erstellt eine einfache Konfiguration für Tests."""
    regimes = [
        RegimeConfig(
            regime_id=0,
            garch_omega=0.00001,
            garch_alpha=0.1,
            garch_beta=0.85,
        ),
        RegimeConfig(
            regime_id=1,
            garch_omega=0.00005,
            garch_alpha=0.15,
            garch_beta=0.80,
        ),
    ][:n_regimes]

    if n_regimes == 1:
        transition_matrix = [[1.0]]
    elif n_regimes == 2:
        transition_matrix = [[0.95, 0.05], [0.10, 0.90]]
    else:
        raise ValueError(f"n_regimes={n_regimes} nicht unterstützt in Test-Helper")

    return OfflineRealtimeFeedConfig(
        symbol="BTC/USD",
        base_timeframe="1min",
        tick_interval_ms=1000,
        regimes=regimes,
        transition_matrix=transition_matrix,
        student_df=5.0,
        usage_context=usage_context,
        seed=seed,
    )


class TestSyntheticTick:
    """Tests für SyntheticTick Dataclass."""

    def test_tick_creation(self):
        """Tick kann erstellt werden."""
        ts = pd.Timestamp("2024-01-01 00:00:00", tz="UTC")
        tick = SyntheticTick(
            timestamp=ts,
            price=100.0,
            volume=50.0,
            regime_id=0,
            sim_run_id="test-123",
        )
        assert tick.timestamp == ts
        assert tick.price == 100.0
        assert tick.volume == 50.0
        assert tick.regime_id == 0
        assert tick.sim_run_id == "test-123"
        assert tick.is_synthetic is True

    def test_is_synthetic_always_true(self):
        """is_synthetic ist immer True, auch wenn False übergeben wird."""
        ts = pd.Timestamp("2024-01-01 00:00:00", tz="UTC")
        tick = SyntheticTick(
            timestamp=ts,
            price=100.0,
            volume=50.0,
            regime_id=0,
            sim_run_id="test-123",
            is_synthetic=False,  # Versuche False zu setzen
        )
        # Sollte trotzdem True sein
        assert tick.is_synthetic is True


class TestRegimeConfig:
    """Tests für RegimeConfig."""

    def test_valid_config(self):
        """Gültige Konfiguration wird akzeptiert."""
        config = RegimeConfig(
            regime_id=0,
            garch_omega=0.00001,
            garch_alpha=0.1,
            garch_beta=0.85,
        )
        assert config.regime_id == 0
        assert config.garch_omega == 0.00001

    def test_negative_omega_raises(self):
        """Negatives omega wird abgelehnt."""
        with pytest.raises(ValueError, match="garch_omega"):
            RegimeConfig(
                regime_id=0,
                garch_omega=-0.001,
                garch_alpha=0.1,
                garch_beta=0.85,
            )

    def test_alpha_out_of_range_raises(self):
        """Alpha außerhalb [0, 1] wird abgelehnt."""
        with pytest.raises(ValueError, match="garch_alpha"):
            RegimeConfig(
                regime_id=0,
                garch_omega=0.00001,
                garch_alpha=1.5,
                garch_beta=0.85,
            )

    def test_beta_out_of_range_raises(self):
        """Beta außerhalb [0, 1] wird abgelehnt."""
        with pytest.raises(ValueError, match="garch_beta"):
            RegimeConfig(
                regime_id=0,
                garch_omega=0.00001,
                garch_alpha=0.1,
                garch_beta=-0.1,
            )


class TestOfflineRealtimeFeedConfig:
    """Tests für OfflineRealtimeFeedConfig."""

    def test_valid_config(self):
        """Gültige Konfiguration wird akzeptiert."""
        config = create_simple_config()
        assert config.symbol == "BTC/USD"
        assert len(config.regimes) == 2

    def test_empty_regimes_raises(self):
        """Leere Regime-Liste wird abgelehnt."""
        with pytest.raises(ValueError, match="Mindestens ein Regime"):
            OfflineRealtimeFeedConfig(
                symbol="BTC/USD",
                base_timeframe="1min",
                tick_interval_ms=1000,
                regimes=[],
                transition_matrix=[],
                student_df=5.0,
                usage_context=DataUsageContextKind.BACKTEST,
            )

    def test_invalid_transition_matrix_size(self):
        """Falsche Transition-Matrix-Größe wird abgelehnt."""
        regimes = [
            RegimeConfig(regime_id=0, garch_omega=0.00001, garch_alpha=0.1, garch_beta=0.85),
        ]
        with pytest.raises(ValueError, match="transition_matrix"):
            OfflineRealtimeFeedConfig(
                symbol="BTC/USD",
                base_timeframe="1min",
                tick_interval_ms=1000,
                regimes=regimes,
                transition_matrix=[[0.5, 0.5]],  # 1 Regime, aber 2 Spalten
                student_df=5.0,
                usage_context=DataUsageContextKind.BACKTEST,
            )

    def test_transition_matrix_row_sum_validation(self):
        """Transition-Matrix Zeilen müssen sich zu 1 summieren."""
        regimes = [
            RegimeConfig(regime_id=0, garch_omega=0.00001, garch_alpha=0.1, garch_beta=0.85),
        ]
        with pytest.raises(ValueError, match="summiert sich"):
            OfflineRealtimeFeedConfig(
                symbol="BTC/USD",
                base_timeframe="1min",
                tick_interval_ms=1000,
                regimes=regimes,
                transition_matrix=[[0.5]],  # Summe != 1
                student_df=5.0,
                usage_context=DataUsageContextKind.BACKTEST,
            )

    def test_student_df_validation(self):
        """student_df > 2 erforderlich."""
        regimes = [
            RegimeConfig(regime_id=0, garch_omega=0.00001, garch_alpha=0.1, garch_beta=0.85),
        ]
        with pytest.raises(ValueError, match="student_df"):
            OfflineRealtimeFeedConfig(
                symbol="BTC/USD",
                base_timeframe="1min",
                tick_interval_ms=1000,
                regimes=regimes,
                transition_matrix=[[1.0]],
                student_df=2.0,  # Muss > 2 sein
                usage_context=DataUsageContextKind.BACKTEST,
            )


class TestBasicConstruction:
    """Tests für grundlegende Konstruktion."""

    def test_from_ohlcv_factory(self):
        """from_ohlcv Factory-Methode funktioniert."""
        ohlcv = create_sample_ohlcv(n_bars=10)
        config = create_simple_config()

        feed = OfflineRealtimeFeed.from_ohlcv(ohlcv, config)

        assert feed is not None
        assert feed.config == config
        assert feed.sim_run_id is not None
        assert len(feed.sim_run_id) > 0

    def test_constructor_direct(self):
        """Direkter Konstruktor funktioniert."""
        ohlcv = create_sample_ohlcv(n_bars=10)
        config = create_simple_config()

        feed = OfflineRealtimeFeed(ohlcv, config)

        assert feed is not None

    def test_generates_ticks(self):
        """Feed generiert Ticks."""
        ohlcv = create_sample_ohlcv(n_bars=5)
        config = create_simple_config()

        feed = OfflineRealtimeFeed.from_ohlcv(ohlcv, config)

        ticks: List[SyntheticTick] = []
        for tick in feed:
            ticks.append(tick)
            if len(ticks) >= 10:
                break

        assert len(ticks) == 10
        assert all(tick.is_synthetic is True for tick in ticks)

    def test_all_ticks_have_is_synthetic_true(self):
        """Alle Ticks haben is_synthetic=True."""
        ohlcv = create_sample_ohlcv(n_bars=3)
        config = create_simple_config()

        feed = OfflineRealtimeFeed.from_ohlcv(ohlcv, config)

        for tick in feed:
            assert tick.is_synthetic is True, "Jeder Tick MUSS is_synthetic=True haben!"

    def test_timestamps_strictly_increasing(self):
        """Timestamps sind streng aufsteigend."""
        ohlcv = create_sample_ohlcv(n_bars=5)
        config = create_simple_config()

        feed = OfflineRealtimeFeed.from_ohlcv(ohlcv, config)

        ticks = list(feed)
        for i in range(1, len(ticks)):
            assert ticks[i].timestamp > ticks[i - 1].timestamp, (
                f"Timestamp nicht streng aufsteigend bei Index {i}: "
                f"{ticks[i - 1].timestamp} >= {ticks[i].timestamp}"
            )


class TestSafetyGateIntegration:
    """Tests für Safety-Gate Integration."""

    def test_backtest_context_allowed(self):
        """BACKTEST Kontext ist erlaubt."""
        ohlcv = create_sample_ohlcv(n_bars=5)
        config = create_simple_config(usage_context=DataUsageContextKind.BACKTEST)

        # Sollte keine Exception werfen
        feed = OfflineRealtimeFeed.from_ohlcv(ohlcv, config)
        assert feed is not None

    def test_research_context_allowed(self):
        """RESEARCH Kontext ist erlaubt."""
        ohlcv = create_sample_ohlcv(n_bars=5)
        config = create_simple_config(usage_context=DataUsageContextKind.RESEARCH)

        # Sollte keine Exception werfen
        feed = OfflineRealtimeFeed.from_ohlcv(ohlcv, config)
        assert feed is not None

    def test_paper_trade_context_allowed(self):
        """PAPER_TRADE Kontext ist erlaubt."""
        ohlcv = create_sample_ohlcv(n_bars=5)
        config = create_simple_config(usage_context=DataUsageContextKind.PAPER_TRADE)

        # Sollte keine Exception werfen
        feed = OfflineRealtimeFeed.from_ohlcv(ohlcv, config)
        assert feed is not None

    def test_live_trade_context_blocked(self):
        """LIVE_TRADE Kontext ist VERBOTEN - wirft Exception."""
        ohlcv = create_sample_ohlcv(n_bars=5)
        config = create_simple_config(usage_context=DataUsageContextKind.LIVE_TRADE)

        with pytest.raises(DataSafetyViolationError) as exc_info:
            OfflineRealtimeFeed.from_ohlcv(ohlcv, config)

        error = exc_info.value
        assert error.result.allowed is False
        # Prüfe, dass die Fehlermeldung informativ ist
        assert "LIVE_TRADE" in str(error) or "live" in str(error).lower()


class TestRegimeSwitching:
    """Tests für Regime-Switching Verhalten."""

    def test_regime_ids_in_valid_range(self):
        """Regime-IDs sind im gültigen Bereich."""
        ohlcv = create_sample_ohlcv(n_bars=10)
        config = create_simple_config(n_regimes=2)

        feed = OfflineRealtimeFeed.from_ohlcv(ohlcv, config)

        for tick in feed:
            assert tick.regime_id in (0, 1), f"Ungültige regime_id: {tick.regime_id}"

    def test_multiple_regimes_occur(self):
        """Bei nicht-trivialer Transition-Matrix treten mehrere Regimes auf."""
        ohlcv = create_sample_ohlcv(n_bars=100)
        config = OfflineRealtimeFeedConfig(
            symbol="BTC/USD",
            base_timeframe="1min",
            tick_interval_ms=100,  # Mehr Ticks pro Kerze
            regimes=[
                RegimeConfig(regime_id=0, garch_omega=0.00001, garch_alpha=0.1, garch_beta=0.85),
                RegimeConfig(regime_id=1, garch_omega=0.00005, garch_alpha=0.15, garch_beta=0.80),
            ],
            transition_matrix=[[0.90, 0.10], [0.10, 0.90]],  # Häufigere Wechsel
            student_df=5.0,
            usage_context=DataUsageContextKind.BACKTEST,
            seed=42,
        )

        feed = OfflineRealtimeFeed.from_ohlcv(ohlcv, config)

        # Sammle alle Ticks (begrenzt auf 5000)
        ticks: List[SyntheticTick] = []
        for tick in feed:
            ticks.append(tick)
            if len(ticks) >= 5000:
                break

        regime_ids = {tick.regime_id for tick in ticks}

        # Bei 5000 Ticks und 10% Übergangswahrscheinlichkeit sollten beide Regimes vorkommen
        assert len(regime_ids) >= 2, (
            f"Erwartet mindestens 2 verschiedene Regimes, gefunden: {regime_ids}"
        )


class TestVolatilityModel:
    """Tests für das Volatilitäts-Modell."""

    def test_prices_are_positive(self):
        """Preise bleiben positiv."""
        ohlcv = create_sample_ohlcv(n_bars=20, start_price=100.0)
        config = create_simple_config()

        feed = OfflineRealtimeFeed.from_ohlcv(ohlcv, config)

        for tick in feed:
            assert tick.price > 0, f"Preis muss positiv sein: {tick.price}"

    def test_volume_is_positive(self):
        """Volume ist positiv."""
        ohlcv = create_sample_ohlcv(n_bars=10)
        config = create_simple_config()

        feed = OfflineRealtimeFeed.from_ohlcv(ohlcv, config)

        for tick in feed:
            assert tick.volume >= 0, f"Volume muss >= 0 sein: {tick.volume}"

    def test_reproducibility_with_seed(self):
        """Gleicher Seed produziert gleiche Sequenz."""
        ohlcv = create_sample_ohlcv(n_bars=10)
        config1 = create_simple_config(seed=12345)
        config2 = create_simple_config(seed=12345)

        feed1 = OfflineRealtimeFeed.from_ohlcv(ohlcv, config1)
        feed2 = OfflineRealtimeFeed.from_ohlcv(ohlcv, config2)

        ticks1 = [next(feed1) for _ in range(50)]
        ticks2 = [next(feed2) for _ in range(50)]

        for t1, t2 in zip(ticks1, ticks2):
            assert t1.price == t2.price, "Preise sollten identisch sein bei gleichem Seed"
            assert t1.regime_id == t2.regime_id, "Regimes sollten identisch sein"


class TestResetAndIteration:
    """Tests für Reset und Iteration."""

    def test_reset_restarts_iteration(self):
        """reset() startet Iteration neu."""
        ohlcv = create_sample_ohlcv(n_bars=5)
        config = create_simple_config()

        feed = OfflineRealtimeFeed.from_ohlcv(ohlcv, config)

        first_ticks = [next(feed) for _ in range(10)]
        feed.reset()
        second_ticks = [next(feed) for _ in range(10)]

        # Nach Reset sollte dieselbe Sequenz kommen (gleicher Seed im Vol-Model)
        for t1, t2 in zip(first_ticks, second_ticks):
            assert t1.timestamp == t2.timestamp

    def test_total_ticks_property(self):
        """total_ticks gibt korrekte Anzahl zurück."""
        ohlcv = create_sample_ohlcv(n_bars=5)
        config = create_simple_config()

        feed = OfflineRealtimeFeed.from_ohlcv(ohlcv, config)

        # 5 Kerzen * 60 Ticks/Kerze (1min / 1000ms)
        expected = 5 * 60
        assert feed.total_ticks == expected

    def test_remaining_ticks_decreases(self):
        """remaining_ticks nimmt ab beim Iterieren."""
        ohlcv = create_sample_ohlcv(n_bars=3)
        config = create_simple_config()

        feed = OfflineRealtimeFeed.from_ohlcv(ohlcv, config)

        initial_remaining = feed.remaining_ticks
        next(feed)
        assert feed.remaining_ticks == initial_remaining - 1


class TestEdgeCases:
    """Tests für Randfälle."""

    def test_single_candle(self):
        """Funktioniert mit nur einer Kerze."""
        ohlcv = create_sample_ohlcv(n_bars=1)
        config = create_simple_config()

        feed = OfflineRealtimeFeed.from_ohlcv(ohlcv, config)
        ticks = list(feed)

        assert len(ticks) == 60  # 1min / 1s = 60 Ticks
        assert all(t.is_synthetic for t in ticks)

    def test_empty_ohlcv_raises(self):
        """Leerer OHLCV DataFrame wird abgelehnt."""
        ohlcv = pd.DataFrame(
            columns=["open", "high", "low", "close", "volume"],
            index=pd.DatetimeIndex([], tz="UTC"),
        )
        config = create_simple_config()

        with pytest.raises(ValueError, match="leer"):
            OfflineRealtimeFeed.from_ohlcv(ohlcv, config)

    def test_missing_columns_raises(self):
        """Fehlende OHLCV-Spalten werden abgelehnt."""
        dates = pd.date_range("2024-01-01", periods=5, freq="1min", tz="UTC")
        ohlcv = pd.DataFrame(
            {"open": [100.0] * 5, "close": [100.0] * 5},  # high, low, volume fehlen
            index=dates,
        )
        config = create_simple_config()

        with pytest.raises(ValueError, match="Fehlende"):
            OfflineRealtimeFeed.from_ohlcv(ohlcv, config)

    def test_sim_run_id_is_unique(self):
        """Jede Feed-Instanz hat eine eindeutige sim_run_id."""
        ohlcv = create_sample_ohlcv(n_bars=5)
        config = create_simple_config()

        feed1 = OfflineRealtimeFeed.from_ohlcv(ohlcv, config)
        feed2 = OfflineRealtimeFeed.from_ohlcv(ohlcv, config)

        assert feed1.sim_run_id != feed2.sim_run_id

    def test_tick_sim_run_id_matches_feed(self):
        """Alle Ticks haben die sim_run_id des Feeds."""
        ohlcv = create_sample_ohlcv(n_bars=3)
        config = create_simple_config()

        feed = OfflineRealtimeFeed.from_ohlcv(ohlcv, config)
        expected_id = feed.sim_run_id

        for tick in feed:
            assert tick.sim_run_id == expected_id
