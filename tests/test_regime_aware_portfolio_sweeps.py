# tests/test_regime_aware_portfolio_sweeps.py
"""
Peak_Trade Regime-Aware Portfolio Sweeps Tests
==============================================
Unit-Tests für Regime-Aware Portfolio Sweep-Presets.
"""
import pytest

from src.experiments.regime_aware_portfolio_sweeps import (
    get_regime_aware_portfolio_sweeps,
    get_regime_aware_aggressive_sweeps,
    get_regime_aware_conservative_sweeps,
    get_regime_aware_volmetric_sweeps,
    get_regime_aware_combined_sweeps,
    get_regime_aware_sweep,
    list_available_regime_aware_sweeps,
)
from src.experiments.base import ParamSweep
from src.experiments.research_playground import (
    get_predefined_sweep,
    list_predefined_sweeps,
)


# ============================================================================
# BASE SWEEP TESTS
# ============================================================================


class TestRegimeAwarePortfolioSweeps:
    """Tests für Regime-Aware Portfolio Sweeps."""

    def test_get_portfolio_sweeps_coarse(self):
        """Test: Portfolio-Sweeps mit coarse Granularität."""
        sweeps = get_regime_aware_portfolio_sweeps("coarse")

        assert len(sweeps) > 0
        assert any(s.name == "risk_on_scale" for s in sweeps)
        assert any(s.name == "neutral_scale" for s in sweeps)
        assert any(s.name == "risk_off_scale" for s in sweeps)

    def test_get_portfolio_sweeps_medium(self):
        """Test: Portfolio-Sweeps mit medium Granularität."""
        sweeps = get_regime_aware_portfolio_sweeps("medium")

        assert len(sweeps) >= 4
        assert any(s.name == "mode" for s in sweeps)
        assert any(s.name == "signal_threshold" for s in sweeps)

    def test_get_portfolio_sweeps_fine(self):
        """Test: Portfolio-Sweeps mit fine Granularität."""
        sweeps = get_regime_aware_portfolio_sweeps("fine")

        assert len(sweeps) >= 4
        # Fine sollte mehr Werte haben
        risk_on_sweep = next(s for s in sweeps if s.name == "risk_on_scale")
        assert len(risk_on_sweep.values) >= 1

    def test_aggressive_sweeps(self):
        """Test: Aggressive Sweeps enthalten erwartete Parameter."""
        sweeps = get_regime_aware_aggressive_sweeps("medium")

        sweep_names = [s.name for s in sweeps]
        assert "risk_on_scale" in sweep_names
        assert "neutral_scale" in sweep_names
        assert "risk_off_scale" in sweep_names

        # Risk-On sollte 1.0 sein
        risk_on_sweep = next(s for s in sweeps if s.name == "risk_on_scale")
        assert 1.0 in risk_on_sweep.values

        # Risk-Off sollte niedrige Werte haben
        risk_off_sweep = next(s for s in sweeps if s.name == "risk_off_scale")
        assert all(v <= 0.2 for v in risk_off_sweep.values)

    def test_conservative_sweeps(self):
        """Test: Conservative Sweeps enthalten erwartete Parameter."""
        sweeps = get_regime_aware_conservative_sweeps("medium")

        sweep_names = [s.name for s in sweeps]
        assert "risk_on_scale" in sweep_names
        assert "neutral_scale" in sweep_names
        assert "risk_off_scale" in sweep_names
        assert "mode" in sweep_names

        # Risk-Off sollte 0.0 sein
        risk_off_sweep = next(s for s in sweeps if s.name == "risk_off_scale")
        assert 0.0 in risk_off_sweep.values

        # Mode sollte "filter" sein
        mode_sweep = next(s for s in sweeps if s.name == "mode")
        assert "filter" in mode_sweep.values

    def test_volmetric_sweeps(self):
        """Test: Vol-Metrik-Sweeps enthalten Vol-Parameter."""
        sweeps = get_regime_aware_volmetric_sweeps("medium")

        sweep_names = [s.name for s in sweeps]
        assert "vol_metric" in sweep_names
        assert "low_vol_threshold" in sweep_names
        assert "high_vol_threshold" in sweep_names

        # Vol-Metrik sollte mehrere Optionen haben
        vol_metric_sweep = next(s for s in sweeps if s.name == "vol_metric")
        assert len(vol_metric_sweep.values) >= 2
        assert "atr" in vol_metric_sweep.values

    def test_combined_sweeps_aggressive(self):
        """Test: Combined Sweeps kombinieren Portfolio + Vol-Regime."""
        sweeps = get_regime_aware_combined_sweeps("medium", preset="aggressive")

        sweep_names = [s.name for s in sweeps]
        # Portfolio-Parameter
        assert "risk_on_scale" in sweep_names
        assert "neutral_scale" in sweep_names
        # Vol-Regime-Parameter
        assert "low_vol_threshold" in sweep_names
        assert "high_vol_threshold" in sweep_names

    def test_combined_sweeps_volmetric(self):
        """Test: Combined Sweeps mit volmetric preset."""
        sweeps = get_regime_aware_combined_sweeps("medium", preset="volmetric")

        sweep_names = [s.name for s in sweeps]
        # Volmetric preset hat nur Vol-Parameter
        assert "vol_metric" in sweep_names

    def test_registry_access(self):
        """Test: Registry-Funktionen funktionieren."""
        available = list_available_regime_aware_sweeps()

        assert len(available) > 0
        assert "regime_aware_aggressive" in available

        # Get sweep via registry
        sweeps = get_regime_aware_sweep("regime_aware_aggressive", "medium")
        assert len(sweeps) > 0

    def test_registry_unknown_sweep(self):
        """Test: Registry wirft Fehler bei unbekanntem Sweep."""
        with pytest.raises(ValueError, match="Unbekannter Regime-Aware Portfolio-Sweep"):
            get_regime_aware_sweep("unknown_sweep", "medium")

    def test_sweep_values_valid(self):
        """Test: Alle Sweep-Werte sind valide."""
        sweeps = get_regime_aware_aggressive_sweeps("medium")

        for sweep in sweeps:
            assert len(sweep.values) > 0
            # Skalierungsfaktoren sollten zwischen 0 und 1 liegen
            if "scale" in sweep.name:
                assert all(0 <= v <= 1.0 for v in sweep.values)
            # Mode sollte nur "scale" oder "filter" sein
            if sweep.name == "mode":
                assert all(m in ["scale", "filter"] for m in sweep.values)
            # Threshold sollte zwischen 0 und 1 liegen
            if "threshold" in sweep.name:
                assert all(0 <= v <= 1.0 for v in sweep.values)


# ============================================================================
# PREDEFINED SWEEP TESTS
# ============================================================================


class TestPredefinedRegimeAwareSweeps:
    """Tests für vordefinierte Regime-Aware Sweeps in Research Playground."""

    def test_predefined_sweeps_registered(self):
        """Test: Vordefinierte Sweeps sind registriert."""
        all_sweeps = list_predefined_sweeps()

        assert "regime_aware_portfolio_aggressive" in all_sweeps
        assert "regime_aware_portfolio_conservative" in all_sweeps
        assert "regime_aware_portfolio_volmetric" in all_sweeps

    def test_aggressive_sweep_config(self):
        """Test: Aggressive Sweep-Config ist valide."""
        sweep = get_predefined_sweep("regime_aware_portfolio_aggressive")

        assert sweep.strategy_name == "regime_aware_portfolio"
        assert "risk_on_scale" in sweep.param_grid
        assert "neutral_scale" in sweep.param_grid
        assert "risk_off_scale" in sweep.param_grid
        assert sweep.base_params["components"] == ["breakout", "rsi_reversion"]

    def test_conservative_sweep_config(self):
        """Test: Conservative Sweep-Config ist valide."""
        sweep = get_predefined_sweep("regime_aware_portfolio_conservative")

        assert sweep.strategy_name == "regime_aware_portfolio"
        assert "mode" in sweep.param_grid
        assert sweep.base_params["components"] == ["breakout", "ma_crossover"]
        assert sweep.base_params["base_weights"]["breakout"] == 0.5

    def test_volmetric_sweep_config(self):
        """Test: Volmetric Sweep-Config ist valide."""
        sweep = get_predefined_sweep("regime_aware_portfolio_volmetric")

        assert sweep.strategy_name == "regime_aware_portfolio"
        assert "vol_metric" in sweep.param_grid
        assert sweep.base_params["risk_on_scale"] == 1.0
        assert sweep.base_params["neutral_scale"] == 0.5

    def test_sweep_generate_combinations(self):
        """Test: Sweep generiert Parameter-Kombinationen."""
        sweep = get_predefined_sweep("regime_aware_portfolio_aggressive")

        combinations = sweep.generate_param_combinations()

        assert len(combinations) > 0
        # Jede Kombination sollte alle erwarteten Parameter haben
        for combo in combinations[:5]:  # Prüfe erste 5
            assert "risk_on_scale" in combo
            assert "neutral_scale" in combo
            assert "risk_off_scale" in combo

    def test_sweep_to_experiment_config(self):
        """Test: Sweep kann zu ExperimentConfig konvertiert werden."""
        sweep = get_predefined_sweep("regime_aware_portfolio_conservative")

        exp_config = sweep.to_experiment_config(
            start_date="2024-01-01",
            end_date="2024-12-01"
        )

        assert exp_config.strategy_name == "regime_aware_portfolio"
        assert len(exp_config.param_sweeps) > 0
        assert exp_config.start_date == "2024-01-01"
        assert exp_config.end_date == "2024-12-01"








