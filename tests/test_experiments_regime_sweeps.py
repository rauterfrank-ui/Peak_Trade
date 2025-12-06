# tests/test_experiments_regime_sweeps.py
"""
Tests für src/experiments/regime_sweeps.py (Phase 29)
====================================================

Testet die vordefinierten Parameter-Sweeps für Regime-Detection
und Strategy-Switching.
"""
import pytest
from typing import List

from src.experiments.base import ParamSweep
from src.experiments.regime_sweeps import (
    get_volatility_detector_sweeps,
    get_range_compression_detector_sweeps,
    get_regime_detector_sweeps,
    get_all_regime_detector_sweeps,
    get_strategy_switching_sweeps,
    get_regime_mapping_variants,
    get_weight_variants,
    get_combined_regime_strategy_sweeps,
    list_available_regime_sweeps,
    REGIME_SWEEP_REGISTRY,
)


# ============================================================================
# VOLATILITY DETECTOR SWEEPS TESTS
# ============================================================================

class TestVolatilityDetectorSweeps:
    """Tests für VolatilityRegimeDetector Sweeps."""

    def test_coarse_granularity(self):
        """Coarse Granularität gibt wenige Parameter."""
        sweeps = get_volatility_detector_sweeps("coarse")

        assert len(sweeps) >= 3
        names = [s.name for s in sweeps]
        assert any("vol_window" in n for n in names)
        assert any("vol_percentile_breakout" in n for n in names)

    def test_medium_granularity(self):
        """Medium Granularität gibt mehr Parameter."""
        sweeps = get_volatility_detector_sweeps("medium")

        assert len(sweeps) >= 4

    def test_fine_granularity(self):
        """Fine Granularität gibt viele Parameter."""
        sweeps = get_volatility_detector_sweeps("fine")

        assert len(sweeps) >= 5

    def test_custom_prefix(self):
        """Custom Prefix wird verwendet."""
        sweeps = get_volatility_detector_sweeps("coarse", prefix="custom_")

        names = [s.name for s in sweeps]
        assert all(n.startswith("custom_") for n in names)

    def test_percentile_values_valid(self):
        """Perzentil-Werte sind zwischen 0 und 1."""
        sweeps = get_volatility_detector_sweeps("fine")

        for sweep in sweeps:
            if "percentile" in sweep.name:
                assert all(0 <= v <= 1 for v in sweep.values)


# ============================================================================
# RANGE COMPRESSION DETECTOR SWEEPS TESTS
# ============================================================================

class TestRangeCompressionDetectorSweeps:
    """Tests für RangeCompressionRegimeDetector Sweeps."""

    def test_has_compression_parameters(self):
        """Enthält Kompression-Parameter."""
        sweeps = get_range_compression_detector_sweeps("medium")

        names = [s.name for s in sweeps]
        assert any("range_compression_window" in n for n in names)
        assert any("compression_threshold" in n for n in names)

    def test_compression_threshold_valid(self):
        """Compression-Threshold ist sinnvoll."""
        sweeps = get_range_compression_detector_sweeps("fine")

        threshold = next(s for s in sweeps if "compression_threshold" in s.name)
        assert all(0 < v < 1 for v in threshold.values)


# ============================================================================
# GET REGIME DETECTOR SWEEPS TESTS
# ============================================================================

class TestGetRegimeDetectorSweeps:
    """Tests für get_regime_detector_sweeps()."""

    def test_volatility_detector(self):
        """Volatility Detector funktioniert."""
        sweeps = get_regime_detector_sweeps("volatility_breakout", "medium")

        assert isinstance(sweeps, list)
        assert len(sweeps) > 0

    def test_range_compression_detector(self):
        """Range Compression Detector funktioniert."""
        sweeps = get_regime_detector_sweeps("range_compression", "medium")

        assert isinstance(sweeps, list)
        assert len(sweeps) > 0

    def test_alias_names(self):
        """Alias-Namen funktionieren."""
        # volatility -> volatility_breakout
        sweeps1 = get_regime_detector_sweeps("vol", "medium")
        sweeps2 = get_regime_detector_sweeps("volatility_breakout", "medium")

        assert len(sweeps1) == len(sweeps2)

    def test_unknown_detector_raises(self):
        """Unbekannter Detector wirft ValueError."""
        with pytest.raises(ValueError, match="Unbekannter Regime-Detector"):
            get_regime_detector_sweeps("unknown_detector", "medium")


# ============================================================================
# GET ALL REGIME DETECTOR SWEEPS TESTS
# ============================================================================

class TestGetAllRegimeDetectorSweeps:
    """Tests für get_all_regime_detector_sweeps()."""

    def test_returns_dict(self):
        """Gibt Dictionary zurück."""
        all_sweeps = get_all_regime_detector_sweeps("medium")

        assert isinstance(all_sweeps, dict)
        assert "volatility_breakout" in all_sweeps
        assert "range_compression" in all_sweeps

    def test_all_values_are_lists(self):
        """Alle Werte sind Listen von ParamSweeps."""
        all_sweeps = get_all_regime_detector_sweeps("medium")

        for name, sweeps in all_sweeps.items():
            assert isinstance(sweeps, list)
            assert all(isinstance(s, ParamSweep) for s in sweeps)


# ============================================================================
# STRATEGY SWITCHING SWEEPS TESTS
# ============================================================================

class TestStrategySwitchingSweeps:
    """Tests für Strategy-Switching Sweeps."""

    def test_has_weight_parameters(self):
        """Enthält Weight-Parameter."""
        sweeps = get_strategy_switching_sweeps("medium")

        names = [s.name for s in sweeps]
        assert any("primary_weight" in n for n in names)

    def test_weight_values_valid(self):
        """Weight-Werte sind zwischen 0 und 1."""
        sweeps = get_strategy_switching_sweeps("fine")

        for sweep in sweeps:
            if "weight" in sweep.name:
                assert all(0 <= v <= 1 for v in sweep.values)


# ============================================================================
# REGIME MAPPING VARIANTS TESTS
# ============================================================================

class TestRegimeMappingVariants:
    """Tests für Regime-Mapping-Varianten."""

    def test_returns_list(self):
        """Gibt Liste zurück."""
        variants = get_regime_mapping_variants()

        assert isinstance(variants, list)
        assert len(variants) > 0

    def test_all_variants_have_regime_keys(self):
        """Alle Varianten haben Regime-Keys."""
        variants = get_regime_mapping_variants()

        required_regimes = {"breakout", "ranging", "trending", "unknown"}

        for variant in variants:
            assert isinstance(variant, dict)
            assert required_regimes.issubset(variant.keys())

    def test_all_values_are_lists(self):
        """Alle Strategie-Werte sind Listen."""
        variants = get_regime_mapping_variants()

        for variant in variants:
            for regime, strategies in variant.items():
                assert isinstance(strategies, list)
                assert len(strategies) > 0


# ============================================================================
# WEIGHT VARIANTS TESTS
# ============================================================================

class TestWeightVariants:
    """Tests für Weight-Varianten."""

    def test_returns_list(self):
        """Gibt Liste zurück."""
        variants = get_weight_variants()

        assert isinstance(variants, list)
        assert len(variants) > 0

    def test_weights_sum_to_one(self):
        """Gewichte summieren zu ~1.0."""
        variants = get_weight_variants()

        for variant in variants:
            for regime, weights in variant.items():
                total = sum(weights.values())
                assert abs(total - 1.0) < 0.01, f"Weights for {regime}: {total}"


# ============================================================================
# COMBINED SWEEPS TESTS
# ============================================================================

class TestCombinedSweeps:
    """Tests für kombinierte Sweeps."""

    def test_combines_strategy_and_regime(self):
        """Kombiniert Strategie- und Regime-Sweeps."""
        sweeps = get_combined_regime_strategy_sweeps(
            "vol_breakout",
            "volatility_breakout",
            "medium",
        )

        names = [s.name for s in sweeps]

        # Sollte Strategy-Parameter enthalten
        assert any("atr" in n.lower() for n in names)

        # Sollte Regime-Parameter enthalten
        assert any("regime" in n.lower() for n in names)

    def test_no_duplicate_names(self):
        """Keine doppelten Parameter-Namen."""
        sweeps = get_combined_regime_strategy_sweeps(
            "ma_crossover",
            "volatility_breakout",
            "medium",
        )

        names = [s.name for s in sweeps]
        assert len(names) == len(set(names))


# ============================================================================
# REGISTRY TESTS
# ============================================================================

class TestRegimeSweepRegistry:
    """Tests für REGIME_SWEEP_REGISTRY."""

    def test_registry_not_empty(self):
        """Registry ist nicht leer."""
        assert len(REGIME_SWEEP_REGISTRY) > 0

    def test_all_entries_callable(self):
        """Alle Registry-Einträge sind aufrufbar."""
        for name, func in REGIME_SWEEP_REGISTRY.items():
            sweeps = func("coarse")
            assert isinstance(sweeps, list)

    def test_list_available_regime_sweeps(self):
        """list_available_regime_sweeps() gibt Liste zurück."""
        names = list_available_regime_sweeps()

        assert isinstance(names, list)
        assert len(names) > 0
        assert "volatility_breakout" in names


# ============================================================================
# VALIDATION TESTS
# ============================================================================

class TestRegimeSweepValidation:
    """Tests für Sweep-Validierung."""

    @pytest.mark.parametrize("regime_type", list(REGIME_SWEEP_REGISTRY.keys()))
    def test_all_regime_types_have_valid_sweeps(self, regime_type):
        """Alle Regime-Typen haben gültige Sweeps."""
        for granularity in ["coarse", "medium", "fine"]:
            sweeps = REGIME_SWEEP_REGISTRY[regime_type](granularity)

            assert isinstance(sweeps, list)
            assert len(sweeps) > 0
            for sweep in sweeps:
                assert isinstance(sweep, ParamSweep)
                assert sweep.name
                assert len(sweep.values) > 0

    @pytest.mark.parametrize("regime_type", list(REGIME_SWEEP_REGISTRY.keys()))
    def test_granularity_ordering(self, regime_type):
        """Fine hat mehr oder gleich viele Werte wie Coarse."""
        coarse = REGIME_SWEEP_REGISTRY[regime_type]("coarse")
        fine = REGIME_SWEEP_REGISTRY[regime_type]("fine")

        coarse_count = sum(len(s.values) for s in coarse)
        fine_count = sum(len(s.values) for s in fine)

        assert coarse_count <= fine_count
