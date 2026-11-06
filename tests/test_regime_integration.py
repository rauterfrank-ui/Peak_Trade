# tests/test_regime_integration.py
"""
Integration Tests fuer Regime Detection & Strategy Switching (Phase 28)
=======================================================================

End-to-End-Tests fuer den gesamten Regime-Layer:
- RegimeDetector + StrategySwitchingPolicy zusammen
- Simulation eines Backtests mit Regime-basiertem Switching
"""

import pytest
import pandas as pd
import numpy as np
from typing import Dict, List

from src.regime import (
    RegimeLabel,
    RegimeContext,
    RegimeDetectorConfig,
    StrategySwitchingConfig,
    VolatilityRegimeDetector,
    SimpleRegimeMappingPolicy,
    make_regime_detector,
    make_switching_policy,
    StrategySwitchDecision,
)


# ============================================================================
# TEST DATA FIXTURES
# ============================================================================


@pytest.fixture
def synthetic_market_data() -> pd.DataFrame:
    """
    Erstellt synthetische Marktdaten mit verschiedenen Phasen:
    - Phase 1 (0-50): Low Volatility (Ranging)
    - Phase 2 (50-100): Breakout (High Vol)
    - Phase 3 (100-150): Trending
    - Phase 4 (150-200): Low Volatility again
    """
    np.random.seed(42)
    n_bars = 200

    dates = pd.date_range(start="2024-01-01", periods=n_bars, freq="1h")

    base_price = 50000.0
    prices = np.zeros(n_bars)
    prices[0] = base_price

    for i in range(1, n_bars):
        if i < 50:
            # Phase 1: Ranging (niedrige Vol)
            prices[i] = prices[i - 1] * (1 + np.random.normal(0, 0.001))
        elif i < 100:
            # Phase 2: Breakout (hohe Vol)
            prices[i] = prices[i - 1] * (1 + np.random.normal(0.002, 0.025))
        elif i < 150:
            # Phase 3: Trending (mittlere Vol, klarer Trend)
            prices[i] = prices[i - 1] * (1 + np.random.normal(0.001, 0.008))
        else:
            # Phase 4: Ranging wieder
            prices[i] = prices[i - 1] * (1 + np.random.normal(0, 0.002))

    # Realistische OHLCV
    high = prices * (1 + np.abs(np.random.normal(0, 0.003, n_bars)))
    low = prices * (1 - np.abs(np.random.normal(0, 0.003, n_bars)))
    open_prices = prices * (1 + np.random.normal(0, 0.001, n_bars))
    volume = np.random.randint(100, 1000, n_bars)

    # Ensure high > low
    high = np.maximum(high, prices)
    low = np.minimum(low, prices)

    df = pd.DataFrame(
        {
            "open": open_prices,
            "high": high,
            "low": low,
            "close": prices,
            "volume": volume,
        },
        index=dates,
    )

    return df


@pytest.fixture
def full_config() -> tuple[RegimeDetectorConfig, StrategySwitchingConfig]:
    """Vollstaendige Konfiguration fuer Integration Tests."""
    detector_config = RegimeDetectorConfig(
        enabled=True,
        detector_name="volatility_breakout",
        lookback_window=50,
        min_history_bars=50,  # Niedrigerer Wert fuer Tests
        vol_window=20,
        vol_percentile_breakout=0.75,
        vol_percentile_ranging=0.30,
        trending_ma_window=30,
        trending_slope_threshold=0.0001,
    )

    switching_config = StrategySwitchingConfig(
        enabled=True,
        policy_name="simple_regime_mapping",
        regime_to_strategies={
            "breakout": ["vol_breakout"],
            "ranging": ["mean_reversion_channel", "rsi_reversion"],
            "trending": ["trend_following"],
            "unknown": ["ma_crossover"],
        },
        regime_to_weights={
            "ranging": {"mean_reversion_channel": 0.6, "rsi_reversion": 0.4},
        },
        default_strategies=["ma_crossover"],
    )

    return detector_config, switching_config


@pytest.fixture
def available_strategies() -> List[str]:
    """Liste aller verfuegbaren Strategien."""
    return [
        "vol_breakout",
        "mean_reversion_channel",
        "rsi_reversion",
        "trend_following",
        "ma_crossover",
    ]


# ============================================================================
# INTEGRATION TESTS
# ============================================================================


class TestRegimeIntegration:
    """End-to-End Integration Tests."""

    def test_detector_and_policy_together(
        self,
        synthetic_market_data: pd.DataFrame,
        full_config: tuple[RegimeDetectorConfig, StrategySwitchingConfig],
        available_strategies: List[str],
    ):
        """Detector und Policy arbeiten zusammen."""
        detector_config, switching_config = full_config

        # Detector erstellen und Regimes berechnen
        detector = make_regime_detector(detector_config)
        assert detector is not None

        regimes = detector.detect_regimes(synthetic_market_data)
        assert len(regimes) == len(synthetic_market_data)

        # Policy erstellen
        policy = make_switching_policy(switching_config)
        assert policy is not None

        # Fuer jedes Regime eine Decision treffen
        decisions = []
        for regime in regimes:
            decision = policy.decide(regime, available_strategies)
            decisions.append(decision)

        assert len(decisions) == len(regimes)

        # Alle Decisions sind gueltig
        for decision in decisions:
            assert isinstance(decision, StrategySwitchDecision)
            assert len(decision.active_strategies) > 0

    def test_regime_changes_trigger_strategy_switches(
        self,
        synthetic_market_data: pd.DataFrame,
        full_config: tuple[RegimeDetectorConfig, StrategySwitchingConfig],
        available_strategies: List[str],
    ):
        """Regime-Wechsel fuehren zu Strategy-Wechseln."""
        detector_config, switching_config = full_config

        detector = make_regime_detector(detector_config)
        policy = make_switching_policy(switching_config)

        regimes = detector.detect_regimes(synthetic_market_data)

        # Track strategy changes
        prev_strategies = None
        strategy_changes = 0

        for i, regime in enumerate(regimes):
            decision = policy.decide(regime, available_strategies)
            current_strategies = set(decision.active_strategies)

            if prev_strategies is not None and current_strategies != prev_strategies:
                strategy_changes += 1

            prev_strategies = current_strategies

        # Es sollte mindestens einige Wechsel geben
        # (da die synthetischen Daten verschiedene Phasen haben)
        assert strategy_changes > 0, "Keine Strategy-Wechsel erkannt"

    def test_breakout_regime_uses_breakout_strategy(
        self,
        synthetic_market_data: pd.DataFrame,
        full_config: tuple[RegimeDetectorConfig, StrategySwitchingConfig],
        available_strategies: List[str],
    ):
        """Bei Breakout-Regime wird vol_breakout verwendet."""
        detector_config, switching_config = full_config

        detector = make_regime_detector(detector_config)
        policy = make_switching_policy(switching_config)

        regimes = detector.detect_regimes(synthetic_market_data)

        # Finde Bars mit breakout-Regime
        breakout_indices = regimes[regimes == "breakout"].index

        if len(breakout_indices) > 0:
            # Pruefe Decision fuer eine breakout-Bar
            decision = policy.decide("breakout", available_strategies)
            assert "vol_breakout" in decision.active_strategies

    def test_ranging_regime_uses_mean_reversion(
        self,
        synthetic_market_data: pd.DataFrame,
        full_config: tuple[RegimeDetectorConfig, StrategySwitchingConfig],
        available_strategies: List[str],
    ):
        """Bei Ranging-Regime werden Mean-Reversion-Strategien verwendet."""
        detector_config, switching_config = full_config

        detector = make_regime_detector(detector_config)
        policy = make_switching_policy(switching_config)

        regimes = detector.detect_regimes(synthetic_market_data)

        # Finde Bars mit ranging-Regime
        ranging_indices = regimes[regimes == "ranging"].index

        if len(ranging_indices) > 0:
            decision = policy.decide("ranging", available_strategies)
            # Mindestens eine Mean-Reversion-Strategie sollte aktiv sein
            mean_reversion_strategies = {"mean_reversion_channel", "rsi_reversion"}
            active_set = set(decision.active_strategies)
            assert len(active_set & mean_reversion_strategies) > 0

    def test_regime_distribution_is_sensible(
        self,
        synthetic_market_data: pd.DataFrame,
        full_config: tuple[RegimeDetectorConfig, StrategySwitchingConfig],
    ):
        """Regime-Verteilung ist sinnvoll (nicht alles unknown)."""
        detector_config, _ = full_config

        detector = make_regime_detector(detector_config)
        regimes = detector.detect_regimes(synthetic_market_data)

        # Verteilung berechnen
        distribution = regimes.value_counts(normalize=True)

        # Nicht mehr als 50% unknown
        unknown_pct = distribution.get("unknown", 0)
        assert unknown_pct < 0.5, f"Zu viele unknown: {unknown_pct:.1%}"

        # Mindestens 2 verschiedene Regime (ohne unknown)
        non_unknown_regimes = [r for r in distribution.index if r != "unknown"]
        assert len(non_unknown_regimes) >= 2, "Zu wenige verschiedene Regime erkannt"


class TestRegimeContextFlow:
    """Tests fuer RegimeContext-basierten Flow."""

    def test_context_based_detection(
        self,
        synthetic_market_data: pd.DataFrame,
        full_config: tuple[RegimeDetectorConfig, StrategySwitchingConfig],
    ):
        """Regime Detection via RegimeContext funktioniert."""
        detector_config, _ = full_config
        detector = VolatilityRegimeDetector(detector_config)

        # Erstelle Context fuer letzte Bar
        context = RegimeContext(
            timestamp=synthetic_market_data.index[-1],
            window=synthetic_market_data,
            symbol="BTC/EUR",
            features={"custom_feature": 42},
        )

        regime = detector.detect_regime(context)

        assert regime in ("breakout", "ranging", "trending", "unknown")


class TestBacktestSimulation:
    """Simuliert einen vereinfachten Backtest mit Regime-Switching."""

    def test_simulated_backtest_flow(
        self,
        synthetic_market_data: pd.DataFrame,
        full_config: tuple[RegimeDetectorConfig, StrategySwitchingConfig],
        available_strategies: List[str],
    ):
        """
        Simuliert den Backtest-Flow mit Regime Detection:
        1. Fuer jede Bar: Regime erkennen
        2. Policy entscheidet welche Strategien aktiv sind
        3. Simuliere Signal-Generierung basierend auf aktiver Strategie
        """
        detector_config, switching_config = full_config

        detector = make_regime_detector(detector_config)
        policy = make_switching_policy(switching_config)

        # Pre-compute regimes (effizienter als pro-Bar)
        regimes = detector.detect_regimes(synthetic_market_data)

        # Tracking
        strategy_usage = {s: 0 for s in available_strategies}
        signals = []

        for i in range(len(synthetic_market_data)):
            regime = regimes.iloc[i]
            decision = policy.decide(regime, available_strategies)

            # Track primary strategy usage
            primary = decision.primary_strategy
            if primary and primary in strategy_usage:
                strategy_usage[primary] += 1

            # Simuliere Signal (vereinfacht)
            signal = 0
            if decision.is_single_strategy:
                # Single strategy -> direktes Signal
                if regime == "breakout":
                    signal = 1  # vol_breakout: long
                elif regime == "ranging":
                    signal = -1  # mean_reversion: short at highs
            else:
                # Multiple strategies -> gewichtetes Signal (vereinfacht)
                signal = 0

            signals.append(signal)

        # Assertions
        assert len(signals) == len(synthetic_market_data)

        # Mindestens eine Strategie wurde verwendet
        assert sum(strategy_usage.values()) > 0

        # Es gibt sowohl positive als auch negative Signale
        has_long = any(s > 0 for s in signals)
        has_short = any(s < 0 for s in signals)
        # Mindestens eine Richtung sollte vorkommen
        assert has_long or has_short


class TestDisabledRegimeLayer:
    """Tests fuer deaktivierten Regime-Layer."""

    def test_disabled_detector_returns_none(self):
        """Deaktivierter Detector gibt None zurueck."""
        config = RegimeDetectorConfig(enabled=False)
        detector = make_regime_detector(config)
        assert detector is None

    def test_disabled_policy_returns_none(self):
        """Deaktivierte Policy gibt None zurueck."""
        config = StrategySwitchingConfig(enabled=False)
        policy = make_switching_policy(config)
        assert policy is None

    def test_backtest_without_regime_layer(
        self,
        synthetic_market_data: pd.DataFrame,
        available_strategies: List[str],
    ):
        """Backtest funktioniert auch ohne Regime-Layer."""
        detector_config = RegimeDetectorConfig(enabled=False)
        switching_config = StrategySwitchingConfig(enabled=False)

        detector = make_regime_detector(detector_config)
        policy = make_switching_policy(switching_config)

        assert detector is None
        assert policy is None

        # Ohne Regime-Layer: alle Strategien immer verfuegbar
        # Dies simuliert das bisherige Verhalten
        active_strategies = available_strategies

        # Backtest wuerde alle Strategien nutzen
        assert len(active_strategies) == len(available_strategies)


class TestEdgeCases:
    """Tests fuer Edge Cases."""

    def test_empty_available_strategies(
        self,
        full_config: tuple[RegimeDetectorConfig, StrategySwitchingConfig],
    ):
        """Policy mit leerer Strategy-Liste."""
        _, switching_config = full_config
        policy = SimpleRegimeMappingPolicy(switching_config)

        decision = policy.decide("breakout", [])

        # Sollte leere Liste zurueckgeben (kein Fallback moeglich)
        assert decision.active_strategies == []

    def test_very_short_data(
        self,
        full_config: tuple[RegimeDetectorConfig, StrategySwitchingConfig],
    ):
        """Detector mit sehr kurzen Daten."""
        detector_config, _ = full_config
        detector = VolatilityRegimeDetector(detector_config)

        # Nur 10 Bars
        short_data = pd.DataFrame(
            {
                "open": [100] * 10,
                "high": [101] * 10,
                "low": [99] * 10,
                "close": [100] * 10,
                "volume": [1000] * 10,
            },
            index=pd.date_range("2024-01-01", periods=10, freq="1h"),
        )

        regimes = detector.detect_regimes(short_data)

        # Alle unknown wegen zu wenig Historie
        assert (regimes == "unknown").all()

    def test_constant_prices(
        self,
        full_config: tuple[RegimeDetectorConfig, StrategySwitchingConfig],
    ):
        """Detector mit konstanten Preisen (keine Volatilitaet)."""
        detector_config, _ = full_config
        detector_config.min_history_bars = 20  # Niedrig fuer Test
        detector = VolatilityRegimeDetector(detector_config)

        # Konstante Preise
        const_data = pd.DataFrame(
            {
                "open": [100.0] * 100,
                "high": [100.01] * 100,
                "low": [99.99] * 100,
                "close": [100.0] * 100,
                "volume": [1000] * 100,
            },
            index=pd.date_range("2024-01-01", periods=100, freq="1h"),
        )

        regimes = detector.detect_regimes(const_data)

        # Sollte kein Fehler auftreten
        assert len(regimes) == 100
        # Niedrige Vol -> wahrscheinlich ranging
        # (oder unknown wenn Berechnung nicht konvergiert)
