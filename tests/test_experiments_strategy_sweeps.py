# tests/test_experiments_strategy_sweeps.py
"""
Tests für src/experiments/strategy_sweeps.py (Phase 29)
======================================================

Testet die vordefinierten Parameter-Sweeps für alle Strategien.
"""

import pytest
from typing import List

from src.experiments.base import ParamSweep
from src.experiments.strategy_sweeps import (
    get_ma_crossover_sweeps,
    get_bollinger_sweeps,
    get_macd_sweeps,
    get_momentum_sweeps,
    get_trend_following_sweeps,
    get_vol_breakout_sweeps,
    get_mean_reversion_sweeps,
    get_rsi_reversion_sweeps,
    get_donchian_sweeps,
    get_strategy_sweeps,
    list_available_strategies,
    get_all_strategy_sweeps,
    STRATEGY_SWEEP_REGISTRY,
)


# ============================================================================
# MA CROSSOVER SWEEPS TESTS
# ============================================================================


class TestMACrossoverSweeps:
    """Tests für MA Crossover Sweeps."""

    def test_coarse_granularity(self):
        """Coarse Granularität gibt wenige Werte."""
        sweeps = get_ma_crossover_sweeps("coarse")

        assert len(sweeps) == 2
        assert any(s.name == "fast_period" for s in sweeps)
        assert any(s.name == "slow_period" for s in sweeps)

        fast = next(s for s in sweeps if s.name == "fast_period")
        assert len(fast.values) == 3

    def test_medium_granularity(self):
        """Medium Granularität gibt mittlere Anzahl."""
        sweeps = get_ma_crossover_sweeps("medium")

        fast = next(s for s in sweeps if s.name == "fast_period")
        assert len(fast.values) == 5

    def test_fine_granularity(self):
        """Fine Granularität gibt viele Werte."""
        sweeps = get_ma_crossover_sweeps("fine")

        fast = next(s for s in sweeps if s.name == "fast_period")
        assert len(fast.values) > 5

    def test_include_ma_type(self):
        """include_ma_type fügt MA-Typ hinzu."""
        sweeps = get_ma_crossover_sweeps("coarse", include_ma_type=True)

        assert any(s.name == "ma_type" for s in sweeps)
        ma_type = next(s for s in sweeps if s.name == "ma_type")
        assert "sma" in ma_type.values
        assert "ema" in ma_type.values


# ============================================================================
# BOLLINGER SWEEPS TESTS
# ============================================================================


class TestBollingerSweeps:
    """Tests für Bollinger Sweeps."""

    def test_has_period(self):
        """Enthält period Parameter."""
        sweeps = get_bollinger_sweeps("medium")

        assert any(s.name == "period" for s in sweeps)

    def test_has_num_std(self):
        """Enthält num_std Parameter."""
        sweeps = get_bollinger_sweeps("medium")

        assert any(s.name == "num_std" for s in sweeps)
        num_std = next(s for s in sweeps if s.name == "num_std")
        assert all(0.5 <= v <= 4.0 for v in num_std.values)


# ============================================================================
# MACD SWEEPS TESTS
# ============================================================================


class TestMACDSweeps:
    """Tests für MACD Sweeps."""

    def test_has_all_parameters(self):
        """Enthält fast, slow und signal."""
        sweeps = get_macd_sweeps("medium")

        names = [s.name for s in sweeps]
        assert "fast_period" in names
        assert "slow_period" in names
        assert "signal_period" in names

    def test_fast_generally_less_than_slow(self):
        """Fast-Werte sind typischerweise kleiner als Slow-Werte."""
        sweeps = get_macd_sweeps("medium")

        fast = next(s for s in sweeps if s.name == "fast_period")
        slow = next(s for s in sweeps if s.name == "slow_period")

        # Der Median der Fast-Werte sollte kleiner sein als der Median der Slow-Werte
        fast_median = sorted(fast.values)[len(fast.values) // 2]
        slow_median = sorted(slow.values)[len(slow.values) // 2]
        assert fast_median < slow_median


# ============================================================================
# MOMENTUM SWEEPS TESTS
# ============================================================================


class TestMomentumSweeps:
    """Tests für Momentum Sweeps."""

    def test_has_lookback(self):
        """Enthält lookback Parameter."""
        sweeps = get_momentum_sweeps("medium")

        assert any(s.name == "lookback" for s in sweeps)

    def test_has_threshold(self):
        """Enthält threshold Parameter."""
        sweeps = get_momentum_sweeps("medium")

        assert any(s.name == "threshold" for s in sweeps)


# ============================================================================
# TREND FOLLOWING SWEEPS TESTS
# ============================================================================


class TestTrendFollowingSweeps:
    """Tests für Trend Following Sweeps."""

    def test_has_adx_parameters(self):
        """Enthält ADX-Parameter."""
        sweeps = get_trend_following_sweeps("medium")

        names = [s.name for s in sweeps]
        assert "adx_period" in names
        assert "adx_threshold" in names
        assert "exit_threshold" in names

    def test_include_ma_filter(self):
        """include_ma_filter fügt MA-Parameter hinzu."""
        sweeps = get_trend_following_sweeps("coarse", include_ma_filter=True)

        names = [s.name for s in sweeps]
        assert "ma_period" in names
        assert "use_ma_filter" in names


# ============================================================================
# VOL BREAKOUT SWEEPS TESTS
# ============================================================================


class TestVolBreakoutSweeps:
    """Tests für Vol Breakout Sweeps."""

    def test_has_atr_parameters(self):
        """Enthält ATR-Parameter."""
        sweeps = get_vol_breakout_sweeps("medium")

        names = [s.name for s in sweeps]
        assert "atr_period" in names
        assert "atr_multiplier" in names


# ============================================================================
# MEAN REVERSION SWEEPS TESTS
# ============================================================================


class TestMeanReversionSweeps:
    """Tests für Mean Reversion Sweeps."""

    def test_has_z_score_parameters(self):
        """Enthält Z-Score-Parameter."""
        sweeps = get_mean_reversion_sweeps("medium")

        names = [s.name for s in sweeps]
        assert "entry_z_score" in names
        assert "exit_z_score" in names

    def test_entry_generally_greater_than_exit(self):
        """Entry Z-Score ist typischerweise größer als Exit."""
        sweeps = get_mean_reversion_sweeps("medium")

        entry = next(s for s in sweeps if s.name == "entry_z_score")
        exit_sweep = next(s for s in sweeps if s.name == "exit_z_score")

        # Der Median des Entry Z-Score sollte größer sein als der Median des Exit Z-Score
        entry_median = sorted(entry.values)[len(entry.values) // 2]
        exit_median = sorted(exit_sweep.values)[len(exit_sweep.values) // 2]
        assert entry_median > exit_median


# ============================================================================
# RSI REVERSION SWEEPS TESTS
# ============================================================================


class TestRSIReversionSweeps:
    """Tests für RSI Reversion Sweeps."""

    def test_has_rsi_parameters(self):
        """Enthält RSI-Parameter."""
        sweeps = get_rsi_reversion_sweeps("medium")

        names = [s.name for s in sweeps]
        assert "rsi_period" in names
        assert "oversold_level" in names
        assert "overbought_level" in names

    def test_oversold_less_than_overbought(self):
        """Oversold ist kleiner als Overbought."""
        sweeps = get_rsi_reversion_sweeps("fine")

        oversold = next(s for s in sweeps if s.name == "oversold_level")
        overbought = next(s for s in sweeps if s.name == "overbought_level")

        assert max(oversold.values) < min(overbought.values)


# ============================================================================
# DONCHIAN SWEEPS TESTS
# ============================================================================


class TestDonchianSweeps:
    """Tests für Donchian Sweeps."""

    def test_has_entry_exit_periods(self):
        """Enthält Entry und Exit Perioden."""
        sweeps = get_donchian_sweeps("medium")

        names = [s.name for s in sweeps]
        assert "entry_period" in names
        assert "exit_period" in names


# ============================================================================
# GET STRATEGY SWEEPS TESTS
# ============================================================================


class TestGetStrategySweeps:
    """Tests für get_strategy_sweeps()."""

    def test_known_strategy(self):
        """Bekannte Strategie gibt Sweeps zurück."""
        sweeps = get_strategy_sweeps("ma_crossover", "medium")

        assert isinstance(sweeps, list)
        assert all(isinstance(s, ParamSweep) for s in sweeps)

    def test_unknown_strategy_raises(self):
        """Unbekannte Strategie wirft ValueError."""
        with pytest.raises(ValueError, match="Unbekannte Strategie"):
            get_strategy_sweeps("unknown_strategy", "medium")

    def test_alias_names(self):
        """Alias-Namen funktionieren."""
        # ma -> ma_crossover
        sweeps1 = get_strategy_sweeps("ma", "medium")
        sweeps2 = get_strategy_sweeps("ma_crossover", "medium")

        assert len(sweeps1) == len(sweeps2)

        # bb -> bollinger
        sweeps3 = get_strategy_sweeps("bb", "medium")
        sweeps4 = get_strategy_sweeps("bollinger", "medium")

        assert len(sweeps3) == len(sweeps4)

    def test_case_insensitive(self):
        """Namen sind case-insensitive."""
        sweeps1 = get_strategy_sweeps("MA_CROSSOVER", "medium")
        sweeps2 = get_strategy_sweeps("ma_crossover", "medium")

        assert len(sweeps1) == len(sweeps2)


# ============================================================================
# REGISTRY TESTS
# ============================================================================


class TestStrategyRegistry:
    """Tests für STRATEGY_SWEEP_REGISTRY."""

    def test_registry_not_empty(self):
        """Registry ist nicht leer."""
        assert len(STRATEGY_SWEEP_REGISTRY) > 0

    def test_all_strategies_callable(self):
        """Alle Registry-Einträge sind aufrufbar."""
        for name, func in STRATEGY_SWEEP_REGISTRY.items():
            sweeps = func("coarse")
            assert isinstance(sweeps, list)

    def test_list_available_strategies(self):
        """list_available_strategies() gibt Liste zurück."""
        strategies = list_available_strategies()

        assert isinstance(strategies, list)
        assert len(strategies) > 0
        assert "ma_crossover" in strategies

    def test_get_all_strategy_sweeps(self):
        """get_all_strategy_sweeps() gibt Dict zurück."""
        all_sweeps = get_all_strategy_sweeps("coarse")

        assert isinstance(all_sweeps, dict)
        assert "ma_crossover" in all_sweeps
        assert isinstance(all_sweeps["ma_crossover"], list)


# ============================================================================
# PARAM SWEEP VALIDATION TESTS
# ============================================================================


class TestSweepValidation:
    """Tests für Sweep-Validierung."""

    @pytest.mark.parametrize("strategy", list(STRATEGY_SWEEP_REGISTRY.keys()))
    def test_all_strategies_have_valid_sweeps(self, strategy):
        """Alle Strategien haben gültige Sweeps für alle Granularitäten."""
        for granularity in ["coarse", "medium", "fine"]:
            sweeps = STRATEGY_SWEEP_REGISTRY[strategy](granularity)

            assert isinstance(sweeps, list)
            assert len(sweeps) > 0
            for sweep in sweeps:
                assert isinstance(sweep, ParamSweep)
                assert sweep.name
                assert len(sweep.values) > 0

    @pytest.mark.parametrize("strategy", list(STRATEGY_SWEEP_REGISTRY.keys()))
    def test_granularity_ordering(self, strategy):
        """Fine hat mehr Werte als Coarse."""
        coarse = STRATEGY_SWEEP_REGISTRY[strategy]("coarse")
        medium = STRATEGY_SWEEP_REGISTRY[strategy]("medium")
        fine = STRATEGY_SWEEP_REGISTRY[strategy]("fine")

        coarse_count = sum(len(s.values) for s in coarse)
        medium_count = sum(len(s.values) for s in medium)
        fine_count = sum(len(s.values) for s in fine)

        assert coarse_count <= medium_count <= fine_count
