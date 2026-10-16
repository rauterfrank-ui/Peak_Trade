# tests/test_research_strategies.py
"""
Tests für Research-Strategien (Armstrong & El-Karoui).

Diese Tests verifizieren:
1. Registry-Einträge existieren mit korrekten Metadaten
2. Strategien sind als R&D-Only markiert (nicht live-ready)
3. API-Endpoint filtert Research-Strategien korrekt
4. Safety-Constraints werden eingehalten

Phase: Research-Track Integration
"""

from __future__ import annotations

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any

# Check if FastAPI is available for web-related tests
try:
    import fastapi

    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False

# =============================================================================
# Strategy Import Tests
# =============================================================================


class TestElKarouiVolModelStrategy:
    """Tests für ElKarouiVolModelStrategy."""

    def test_import_el_karoui_strategy(self):
        """Test: El-Karoui-Strategie kann importiert werden."""
        from src.strategies.el_karoui import ElKarouiVolModelStrategy

        assert ElKarouiVolModelStrategy is not None
        assert ElKarouiVolModelStrategy.KEY == "el_karoui_vol_model"

    def test_el_karoui_is_research_only(self):
        """Test: El-Karoui ist als Research-Only markiert."""
        from src.strategies.el_karoui import ElKarouiVolModelStrategy

        assert ElKarouiVolModelStrategy.IS_LIVE_READY is False
        assert ElKarouiVolModelStrategy.TIER == "r_and_d"
        assert "research" in ElKarouiVolModelStrategy.ALLOWED_ENVIRONMENTS
        assert "live" not in ElKarouiVolModelStrategy.ALLOWED_ENVIRONMENTS

    def test_el_karoui_instantiation(self):
        """Test: El-Karoui-Strategie kann instanziiert werden."""
        from src.strategies.el_karoui import ElKarouiVolModelStrategy

        strategy = ElKarouiVolModelStrategy()

        assert strategy is not None
        assert strategy.vol_window == 20
        assert 0 < strategy.vol_threshold_low < 1
        assert 0 < strategy.vol_threshold_high < 1
        assert "RESEARCH" in strategy.meta.description.upper()

    def test_el_karoui_generate_signals_regime_based(self):
        """Test: El-Karoui mappt Vol-Regime-Serie auf 0/1-Signale (kein Flat-Stub)."""
        from src.strategies.el_karoui import ElKarouiVolModelStrategy

        strategy = ElKarouiVolModelStrategy()

        # Test-Daten erstellen
        dates = pd.date_range("2020-01-01", periods=100, freq="D")
        data = pd.DataFrame(
            {
                "open": np.random.randn(100).cumsum() + 100,
                "high": np.random.randn(100).cumsum() + 102,
                "low": np.random.randn(100).cumsum() + 98,
                "close": np.random.randn(100).cumsum() + 100,
                "volume": np.random.randint(1000, 10000, 100),
            },
            index=dates,
        )

        signals = strategy.generate_signals(data)

        assert isinstance(signals, pd.Series)
        assert len(signals) == len(data)
        assert set(signals.unique()).issubset({0, 1})
        assert signals.attrs.get("is_research_stub") is False

    def test_el_karoui_vol_analysis(self):
        """Test: get_vol_analysis gibt valide Analyse zurück."""
        from src.strategies.el_karoui import ElKarouiVolModelStrategy

        strategy = ElKarouiVolModelStrategy()

        # Test-Daten erstellen
        dates = pd.date_range("2020-01-01", periods=100, freq="D")
        data = pd.DataFrame(
            {
                "close": np.random.randn(100).cumsum() + 100,
            },
            index=dates,
        )

        analysis = strategy.get_vol_analysis(data)

        assert "current_vol" in analysis
        assert "vol_regime" in analysis
        assert "vol_percentile" in analysis
        assert analysis["vol_regime"] in {"low", "normal", "high"}

    def test_el_karoui_repr_shows_research_only(self):
        """Test: __repr__ zeigt RESEARCH-ONLY an."""
        from src.strategies.el_karoui import ElKarouiVolModelStrategy

        strategy = ElKarouiVolModelStrategy()
        repr_str = repr(strategy)

        assert "RESEARCH-ONLY" in repr_str


# =============================================================================
# Registry Tests
# =============================================================================


class TestStrategyRegistry:
    """Tests für Strategy-Registry mit Research-Strategien."""

    def test_el_karoui_registered_in_registry(self):
        """Test: El-Karoui ist in der Registry registriert."""
        from src.strategies.registry import get_available_strategy_keys, get_strategy_spec

        keys = get_available_strategy_keys()
        assert "el_karoui_vol_model" in keys

        spec = get_strategy_spec("el_karoui_vol_model")
        assert spec.key == "el_karoui_vol_model"
        assert "R&D" in spec.description or "Research" in spec.description


# =============================================================================
# Tiering Tests
# =============================================================================


class TestStrategyTiering:
    """Tests für Strategy-Tiering mit R&D Tier."""

    def test_tiering_config_exists(self):
        """Test: Tiering-Config existiert und enthält Research-Strategien."""
        from src.experiments.strategy_profiles import load_tiering_config

        tiering = load_tiering_config()

        assert "el_karoui_vol_model" in tiering

    def test_el_karoui_has_r_and_d_tier(self):
        """Test: El-Karoui hat Tier 'r_and_d'."""
        from src.experiments.strategy_profiles import load_tiering_config

        tiering = load_tiering_config()

        assert tiering["el_karoui_vol_model"].tier == "r_and_d"
        assert tiering["el_karoui_vol_model"].allow_live is False

    def test_tier_types_includes_r_and_d(self):
        """Test: TIER_TYPES inkludiert 'r_and_d'."""
        from src.experiments.strategy_profiles import TIER_TYPES

        # Literal-Typ prüfen (indirekt via get_args)
        from typing import get_args

        allowed_tiers = get_args(TIER_TYPES)
        assert "r_and_d" in allowed_tiers

    def test_tier_labels_includes_r_and_d(self):
        """Test: TIER_LABELS hat Label für 'r_and_d'."""
        from src.experiments.strategy_profiles import TIER_LABELS

        assert "r_and_d" in TIER_LABELS
        assert "Research" in TIER_LABELS["r_and_d"]


@pytest.mark.web
class TestResearchStrategyMetadataOnly:
    """Presentation WebUI retired — strategy metadata checks remain offline."""

    def test_research_strategy_metadata_contains_warning(self):
        from src.strategies.el_karoui import ElKarouiVolModelStrategy

        el_karoui = ElKarouiVolModelStrategy()
        assert (
            "NICHT FÜR LIVE" in el_karoui.meta.description.upper()
            or "NOT FOR LIVE" in el_karoui.meta.description.upper()
            or "RESEARCH" in el_karoui.meta.description.upper()
        )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
