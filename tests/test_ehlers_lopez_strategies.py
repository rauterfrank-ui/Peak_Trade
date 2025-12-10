# tests/test_ehlers_lopez_strategies.py
"""
Tests für Ehlers & López de Prado Research-Strategien.

Diese Tests verifizieren:
1. Registry-Einträge existieren mit korrekten Metadaten
2. Strategien sind als R&D-Only markiert (nicht live-ready)
3. Instanziierung und generate_signals funktionieren
4. Safety-Constraints werden eingehalten

Phase: Research-Track Integration (Ehlers DSP + Meta-Labeling)
"""
from __future__ import annotations

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any


# =============================================================================
# EHLERS CYCLE FILTER STRATEGY TESTS
# =============================================================================


class TestEhlersCycleFilterStrategy:
    """Tests für EhlersCycleFilterStrategy."""

    def test_import_ehlers_strategy(self):
        """Test: Ehlers-Strategie kann importiert werden."""
        from src.strategies.ehlers import EhlersCycleFilterStrategy

        assert EhlersCycleFilterStrategy is not None
        assert EhlersCycleFilterStrategy.KEY == "ehlers_cycle_filter"

    def test_ehlers_is_research_only(self):
        """Test: Ehlers ist als Research-Only markiert."""
        from src.strategies.ehlers import EhlersCycleFilterStrategy

        assert EhlersCycleFilterStrategy.IS_LIVE_READY is False
        assert EhlersCycleFilterStrategy.TIER == "r_and_d"
        assert "research" in EhlersCycleFilterStrategy.ALLOWED_ENVIRONMENTS
        assert "live" not in EhlersCycleFilterStrategy.ALLOWED_ENVIRONMENTS

    def test_ehlers_instantiation_default(self):
        """Test: Ehlers-Strategie kann mit Defaults instanziiert werden."""
        from src.strategies.ehlers import EhlersCycleFilterStrategy

        strategy = EhlersCycleFilterStrategy()

        assert strategy is not None
        assert strategy.cfg.smoother_type == "super_smoother"
        assert strategy.cfg.min_cycle_length == 6
        assert strategy.cfg.max_cycle_length == 50
        # Prüfe auf Research-Hinweis (verschiedene Varianten)
        desc_upper = strategy.meta.description.upper()
        assert (
            "RESEARCH" in desc_upper or
            "NICHT FÜR LIVE" in desc_upper or
            "NOT FOR LIVE" in desc_upper
        )

    def test_ehlers_instantiation_custom(self):
        """Test: Ehlers-Strategie mit Custom-Config."""
        from src.strategies.ehlers import EhlersCycleFilterStrategy

        strategy = EhlersCycleFilterStrategy(
            smoother_type="two_pole",
            min_cycle_length=10,
            max_cycle_length=100,
            cycle_threshold=0.6,
        )

        assert strategy.cfg.smoother_type == "two_pole"
        assert strategy.cfg.min_cycle_length == 10
        assert strategy.cfg.max_cycle_length == 100
        assert strategy.cfg.cycle_threshold == 0.6

    def test_ehlers_generate_signals_returns_flat(self):
        """Test: Ehlers generate_signals gibt Flat-Signal (Research-Stub)."""
        from src.strategies.ehlers import EhlersCycleFilterStrategy

        strategy = EhlersCycleFilterStrategy()

        # Test-Daten erstellen
        dates = pd.date_range("2020-01-01", periods=150, freq="h")
        data = pd.DataFrame(
            {
                "open": np.random.randn(150).cumsum() + 100,
                "high": np.random.randn(150).cumsum() + 102,
                "low": np.random.randn(150).cumsum() + 98,
                "close": np.random.randn(150).cumsum() + 100,
                "volume": np.random.randint(1000, 10000, 150),
            },
            index=dates,
        )

        signals = strategy.generate_signals(data)

        # Research-Stub: Alle Signale sollten 0 (flat) sein
        assert isinstance(signals, pd.Series)
        assert len(signals) == len(data)
        assert (signals == 0).all(), "Research-Stub sollte nur Flat-Signale liefern"

    def test_ehlers_generate_signals_validates_input(self):
        """Test: generate_signals validiert Input korrekt."""
        from src.strategies.ehlers import EhlersCycleFilterStrategy

        strategy = EhlersCycleFilterStrategy()

        # Test ohne 'close' Spalte
        data_no_close = pd.DataFrame({"open": [100, 101, 102]})
        with pytest.raises(ValueError, match="close"):
            strategy.generate_signals(data_no_close)

        # Test mit zu wenig Daten
        data_short = pd.DataFrame({"close": [100] * 10})
        with pytest.raises(ValueError, match="mind."):
            strategy.generate_signals(data_short)

    def test_ehlers_config_dataclass(self):
        """Test: EhlersCycleFilterConfig funktioniert korrekt."""
        from src.strategies.ehlers.ehlers_cycle_filter_strategy import (
            EhlersCycleFilterConfig,
        )

        cfg = EhlersCycleFilterConfig(
            smoother_type="super_smoother",
            min_cycle_length=8,
            max_cycle_length=40,
        )

        assert cfg.smoother_type == "super_smoother"
        assert cfg.min_cycle_length == 8

        # to_dict Test
        cfg_dict = cfg.to_dict()
        assert cfg_dict["smoother_type"] == "super_smoother"
        assert cfg_dict["min_cycle_length"] == 8

    def test_ehlers_repr_shows_research_only(self):
        """Test: __repr__ zeigt RESEARCH-ONLY an."""
        from src.strategies.ehlers import EhlersCycleFilterStrategy

        strategy = EhlersCycleFilterStrategy()
        repr_str = repr(strategy)

        assert "RESEARCH-ONLY" in repr_str
        assert "EhlersCycleFilterStrategy" in repr_str


# =============================================================================
# META-LABELING STRATEGY TESTS
# =============================================================================


class TestMetaLabelingStrategy:
    """Tests für MetaLabelingStrategy."""

    def test_import_meta_labeling_strategy(self):
        """Test: MetaLabeling-Strategie kann importiert werden."""
        from src.strategies.lopez_de_prado import MetaLabelingStrategy

        assert MetaLabelingStrategy is not None
        assert MetaLabelingStrategy.KEY == "meta_labeling"

    def test_meta_labeling_is_research_only(self):
        """Test: MetaLabeling ist als Research-Only markiert."""
        from src.strategies.lopez_de_prado import MetaLabelingStrategy

        assert MetaLabelingStrategy.IS_LIVE_READY is False
        assert MetaLabelingStrategy.TIER == "r_and_d"
        assert "research" in MetaLabelingStrategy.ALLOWED_ENVIRONMENTS
        assert "live" not in MetaLabelingStrategy.ALLOWED_ENVIRONMENTS

    def test_meta_labeling_instantiation_default(self):
        """Test: MetaLabeling-Strategie kann mit Defaults instanziiert werden."""
        from src.strategies.lopez_de_prado import MetaLabelingStrategy

        strategy = MetaLabelingStrategy()

        assert strategy is not None
        assert strategy.cfg.base_strategy_id == "rsi_reversion"
        assert strategy.cfg.take_profit == 0.02
        assert strategy.cfg.stop_loss == 0.01
        assert strategy.cfg.vertical_barrier_bars == 20
        # Prüfe auf Research-Hinweis (verschiedene Varianten)
        desc_upper = strategy.meta.description.upper()
        assert (
            "RESEARCH" in desc_upper or
            "NICHT FÜR LIVE" in desc_upper or
            "NOT FOR LIVE" in desc_upper
        )

    def test_meta_labeling_instantiation_custom(self):
        """Test: MetaLabeling-Strategie mit Custom-Config."""
        from src.strategies.lopez_de_prado import MetaLabelingStrategy

        strategy = MetaLabelingStrategy(
            base_strategy_id="ma_crossover",
            take_profit=0.03,
            stop_loss=0.015,
            vertical_barrier_bars=30,
            min_confidence=0.7,
        )

        assert strategy.cfg.base_strategy_id == "ma_crossover"
        assert strategy.cfg.take_profit == 0.03
        assert strategy.cfg.stop_loss == 0.015
        assert strategy.cfg.vertical_barrier_bars == 30
        assert strategy.cfg.min_confidence == 0.7

    def test_meta_labeling_generate_signals_returns_flat(self):
        """Test: MetaLabeling generate_signals gibt Flat-Signal (Research-Stub)."""
        from src.strategies.lopez_de_prado import MetaLabelingStrategy

        strategy = MetaLabelingStrategy()

        # Test-Daten erstellen
        dates = pd.date_range("2020-01-01", periods=100, freq="h")
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

        # Research-Stub: Alle Signale sollten 0 (flat) sein
        assert isinstance(signals, pd.Series)
        assert len(signals) == len(data)
        assert (signals == 0).all(), "Research-Stub sollte nur Flat-Signale liefern"

    def test_meta_labeling_generate_signals_validates_input(self):
        """Test: generate_signals validiert Input korrekt."""
        from src.strategies.lopez_de_prado import MetaLabelingStrategy

        strategy = MetaLabelingStrategy()

        # Test ohne 'close' Spalte
        data_no_close = pd.DataFrame({"open": [100, 101, 102]})
        with pytest.raises(ValueError, match="close"):
            strategy.generate_signals(data_no_close)

    def test_meta_labeling_config_dataclass(self):
        """Test: MetaLabelingConfig funktioniert korrekt."""
        from src.strategies.lopez_de_prado.meta_labeling_strategy import (
            MetaLabelingConfig,
        )

        cfg = MetaLabelingConfig(
            base_strategy_id="breakout",
            take_profit=0.025,
            stop_loss=0.012,
        )

        assert cfg.base_strategy_id == "breakout"
        assert cfg.take_profit == 0.025

        # to_dict Test
        cfg_dict = cfg.to_dict()
        assert cfg_dict["base_strategy_id"] == "breakout"
        assert cfg_dict["take_profit"] == 0.025

    def test_meta_labeling_repr_shows_research_only(self):
        """Test: __repr__ zeigt RESEARCH-ONLY an."""
        from src.strategies.lopez_de_prado import MetaLabelingStrategy

        strategy = MetaLabelingStrategy()
        repr_str = repr(strategy)

        assert "RESEARCH-ONLY" in repr_str
        assert "MetaLabelingStrategy" in repr_str


# =============================================================================
# REGISTRY TESTS
# =============================================================================


class TestStrategyRegistry:
    """Tests für Strategy-Registry mit Ehlers & López de Prado Strategien."""

    def test_ehlers_registered_in_registry(self):
        """Test: Ehlers ist in der Registry registriert."""
        from src.strategies.registry import get_available_strategy_keys, get_strategy_spec

        keys = get_available_strategy_keys()
        assert "ehlers_cycle_filter" in keys

        spec = get_strategy_spec("ehlers_cycle_filter")
        assert spec.key == "ehlers_cycle_filter"
        assert "R&D" in spec.description or "Research" in spec.description

    def test_meta_labeling_registered_in_registry(self):
        """Test: MetaLabeling ist in der Registry registriert."""
        from src.strategies.registry import get_available_strategy_keys, get_strategy_spec

        keys = get_available_strategy_keys()
        assert "meta_labeling" in keys

        spec = get_strategy_spec("meta_labeling")
        assert spec.key == "meta_labeling"
        assert "R&D" in spec.description or "López" in spec.description or "ML" in spec.description


# =============================================================================
# TIERING TESTS
# =============================================================================


class TestStrategyTiering:
    """Tests für Strategy-Tiering mit neuen R&D-Strategien."""

    def test_tiering_config_contains_ehlers(self):
        """Test: Tiering-Config enthält Ehlers-Strategie."""
        from src.experiments.strategy_profiles import load_tiering_config

        tiering = load_tiering_config()

        assert "ehlers_cycle_filter" in tiering
        assert tiering["ehlers_cycle_filter"].tier == "r_and_d"
        assert tiering["ehlers_cycle_filter"].allow_live is False

    def test_tiering_config_contains_meta_labeling(self):
        """Test: Tiering-Config enthält MetaLabeling-Strategie."""
        from src.experiments.strategy_profiles import load_tiering_config

        tiering = load_tiering_config()

        assert "meta_labeling" in tiering
        assert tiering["meta_labeling"].tier == "r_and_d"
        assert tiering["meta_labeling"].allow_live is False


# =============================================================================
# RESEARCH MODULE TESTS
# =============================================================================


class TestResearchModules:
    """Tests für Research-Utility-Module."""

    def test_triple_barrier_import(self):
        """Test: Triple-Barrier-Modul kann importiert werden."""
        from src.research.ml.labeling.triple_barrier import (
            compute_triple_barrier_labels,
        )

        assert compute_triple_barrier_labels is not None

    def test_triple_barrier_returns_series(self):
        """Test: compute_triple_barrier_labels gibt Series zurück."""
        from src.research.ml.labeling.triple_barrier import (
            compute_triple_barrier_labels,
        )

        prices = pd.Series([100, 101, 102, 99, 98, 103])
        signals = pd.Series([1, 0, 0, 0, 0, 0])

        labels = compute_triple_barrier_labels(prices, signals, 0.02, 0.01, 5)

        assert isinstance(labels, pd.Series)
        assert len(labels) == len(prices)

    def test_meta_labeling_module_import(self):
        """Test: Meta-Labeling-Modul kann importiert werden."""
        from src.research.ml.meta.meta_labeling import (
            apply_meta_model,
            MetaModelSpec,
        )

        assert apply_meta_model is not None
        assert MetaModelSpec is not None

    def test_meta_model_spec_dataclass(self):
        """Test: MetaModelSpec funktioniert korrekt."""
        from src.research.ml.meta.meta_labeling import MetaModelSpec

        spec = MetaModelSpec(
            model_type="xgboost",
            min_confidence=0.6,
        )

        assert spec.model_type == "xgboost"
        assert spec.min_confidence == 0.6

    def test_apply_meta_model_returns_series(self):
        """Test: apply_meta_model gibt Series zurück."""
        from src.research.ml.meta.meta_labeling import apply_meta_model, MetaModelSpec

        signals = pd.Series([1, -1, 1, 0, -1])
        features = pd.DataFrame({"volatility": [0.1, 0.2, 0.15, 0.1, 0.25]})
        spec = MetaModelSpec(model_type="random_forest", min_confidence=0.6)

        result = apply_meta_model(signals, features, spec)

        assert isinstance(result, pd.Series)
        assert len(result) == len(signals)


# =============================================================================
# API INTEGRATION TESTS
# =============================================================================


class TestStrategyTieringAPI:
    """Tests für API-Integration der neuen Strategien."""

    def test_load_strategy_tiering_includes_new_strategies_with_flag(self):
        """Test: API inkludiert neue Strategien mit include_research=True."""
        from src.webui.app import load_strategy_tiering

        tiering = load_strategy_tiering(include_research=True)

        strategy_ids = [r["id"] for r in tiering.get("rows", [])]
        assert "ehlers_cycle_filter" in strategy_ids
        assert "meta_labeling" in strategy_ids

    def test_load_strategy_tiering_excludes_new_strategies_without_flag(self):
        """Test: API exkludiert neue Strategien ohne include_research Flag."""
        from src.webui.app import load_strategy_tiering

        tiering = load_strategy_tiering(include_research=False)

        strategy_ids = [r["id"] for r in tiering.get("rows", [])]
        assert "ehlers_cycle_filter" not in strategy_ids
        assert "meta_labeling" not in strategy_ids

    def test_new_strategies_have_correct_allowed_environments(self):
        """Test: Neue Strategien haben korrekte allowed_environments."""
        from src.webui.app import load_strategy_tiering

        tiering = load_strategy_tiering(include_research=True)

        for row in tiering.get("rows", []):
            if row["id"] in ["ehlers_cycle_filter", "meta_labeling"]:
                assert "offline_backtest" in row["allowed_environments"]
                assert "research" in row["allowed_environments"]
                assert "live" not in row["allowed_environments"]
                assert "testnet" not in row["allowed_environments"]


# =============================================================================
# SAFETY TESTS
# =============================================================================


class TestResearchStrategySafety:
    """Tests für Safety-Constraints der neuen Research-Strategien."""

    def test_ehlers_metadata_contains_warning(self):
        """Test: Ehlers-Metadata enthält Warnung."""
        from src.strategies.ehlers import EhlersCycleFilterStrategy

        strategy = EhlersCycleFilterStrategy()

        assert (
            "NICHT FÜR LIVE" in strategy.meta.description.upper()
            or "NOT FOR LIVE" in strategy.meta.description.upper()
            or "RESEARCH" in strategy.meta.description.upper()
        )

    def test_meta_labeling_metadata_contains_warning(self):
        """Test: MetaLabeling-Metadata enthält Warnung."""
        from src.strategies.lopez_de_prado import MetaLabelingStrategy

        strategy = MetaLabelingStrategy()

        assert (
            "NICHT FÜR LIVE" in strategy.meta.description.upper()
            or "NOT FOR LIVE" in strategy.meta.description.upper()
            or "RESEARCH" in strategy.meta.description.upper()
        )

    def test_all_new_strategies_have_is_live_ready_false(self):
        """Test: Alle neuen Strategien haben IS_LIVE_READY=False."""
        from src.strategies.ehlers import EhlersCycleFilterStrategy
        from src.strategies.lopez_de_prado import MetaLabelingStrategy

        assert EhlersCycleFilterStrategy.IS_LIVE_READY is False
        assert MetaLabelingStrategy.IS_LIVE_READY is False

    def test_all_new_strategies_have_r_and_d_tier(self):
        """Test: Alle neuen Strategien haben TIER='r_and_d'."""
        from src.strategies.ehlers import EhlersCycleFilterStrategy
        from src.strategies.lopez_de_prado import MetaLabelingStrategy

        assert EhlersCycleFilterStrategy.TIER == "r_and_d"
        assert MetaLabelingStrategy.TIER == "r_and_d"


# =============================================================================
# FASTAPI INTEGRATION TESTS
# =============================================================================


class TestFastAPIEndpoints:
    """Integration-Tests für FastAPI-Endpoints mit neuen Strategien."""

    @pytest.fixture
    def client(self):
        """FastAPI TestClient."""
        try:
            from fastapi.testclient import TestClient
            from src.webui.app import app

            return TestClient(app)
        except ImportError:
            pytest.skip("fastapi.testclient nicht verfügbar")

    def test_api_includes_ehlers_with_research_flag(self, client):
        """Test: API inkludiert Ehlers mit include_research=true."""
        response = client.get("/api/strategy_tiering?include_research=true")
        assert response.status_code == 200

        data = response.json()
        all_strategy_ids = []
        for tier_group in data.get("tiers", []):
            for s in tier_group.get("strategies", []):
                all_strategy_ids.append(s["id"])

        assert "ehlers_cycle_filter" in all_strategy_ids

    def test_api_includes_meta_labeling_with_research_flag(self, client):
        """Test: API inkludiert MetaLabeling mit include_research=true."""
        response = client.get("/api/strategy_tiering?include_research=true")
        assert response.status_code == 200

        data = response.json()
        all_strategy_ids = []
        for tier_group in data.get("tiers", []):
            for s in tier_group.get("strategies", []):
                all_strategy_ids.append(s["id"])

        assert "meta_labeling" in all_strategy_ids


# =============================================================================
# RUN TESTS
# =============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])



