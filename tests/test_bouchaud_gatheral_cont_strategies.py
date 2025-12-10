# tests/test_bouchaud_gatheral_cont_strategies.py
"""
Tests für Bouchaud & Gatheral/Cont Research-Strategie-Skelette.

Diese Tests verifizieren:
1. Registry-Einträge existieren mit korrekten Metadaten
2. Strategien sind als R&D-Only markiert (nicht live-ready)
3. generate_signals wirft NotImplementedError (Skeleton)
4. Safety-Constraints werden eingehalten

Phase: Research-Track Integration (Bouchaud Microstructure + Gatheral/Cont Vol-Regime)
"""
from __future__ import annotations

import pytest
import pandas as pd
import numpy as np
from typing import Dict, Any


# =============================================================================
# BOUCHAUD MICROSTRUCTURE STRATEGY TESTS
# =============================================================================


class TestBouchaudMicrostructureStrategy:
    """Tests für BouchaudMicrostructureStrategy."""

    def test_import_bouchaud_strategy(self):
        """Test: Bouchaud-Strategie kann importiert werden."""
        from src.strategies.bouchaud import BouchaudMicrostructureStrategy

        assert BouchaudMicrostructureStrategy is not None
        assert BouchaudMicrostructureStrategy.KEY == "bouchaud_microstructure"

    def test_bouchaud_is_research_only(self):
        """Test: Bouchaud ist als Research-Only markiert."""
        from src.strategies.bouchaud import BouchaudMicrostructureStrategy

        assert BouchaudMicrostructureStrategy.IS_LIVE_READY is False
        assert BouchaudMicrostructureStrategy.TIER == "r_and_d"
        assert "research" in BouchaudMicrostructureStrategy.ALLOWED_ENVIRONMENTS
        assert "live" not in BouchaudMicrostructureStrategy.ALLOWED_ENVIRONMENTS
        assert "testnet" not in BouchaudMicrostructureStrategy.ALLOWED_ENVIRONMENTS
        assert "shadow" not in BouchaudMicrostructureStrategy.ALLOWED_ENVIRONMENTS

    def test_bouchaud_instantiation_default(self):
        """Test: Bouchaud-Strategie kann mit Defaults instanziiert werden."""
        from src.strategies.bouchaud import BouchaudMicrostructureStrategy

        strategy = BouchaudMicrostructureStrategy()

        assert strategy is not None
        assert strategy.cfg.use_orderbook_imbalance is True
        assert strategy.cfg.use_trade_signs is True
        assert strategy.cfg.lookback_ticks == 100
        assert strategy.cfg.min_liquidity_filter == 1000.0

    def test_bouchaud_instantiation_custom(self):
        """Test: Bouchaud-Strategie mit Custom-Config."""
        from src.strategies.bouchaud import BouchaudMicrostructureStrategy

        strategy = BouchaudMicrostructureStrategy(
            use_orderbook_imbalance=False,
            lookback_ticks=200,
            min_liquidity_filter=5000.0,
        )

        assert strategy.cfg.use_orderbook_imbalance is False
        assert strategy.cfg.lookback_ticks == 200
        assert strategy.cfg.min_liquidity_filter == 5000.0

    def test_bouchaud_generate_signals_raises_not_implemented(self):
        """Test: generate_signals wirft NotImplementedError (Skeleton)."""
        from src.strategies.bouchaud import BouchaudMicrostructureStrategy

        strategy = BouchaudMicrostructureStrategy()

        # Test-Daten erstellen
        dates = pd.date_range("2020-01-01", periods=100, freq="h")
        data = pd.DataFrame(
            {
                "close": np.random.randn(100).cumsum() + 100,
            },
            index=dates,
        )

        # Skeleton sollte NotImplementedError werfen
        with pytest.raises(NotImplementedError) as exc_info:
            strategy.generate_signals(data)

        # Prüfe, dass die Fehlermeldung informativ ist
        assert "Platzhalter-Skelett" in str(exc_info.value) or \
               "Tick-/Orderbuch-Daten" in str(exc_info.value) or \
               "RESEARCH-ONLY" in str(exc_info.value)

    def test_bouchaud_config_dataclass(self):
        """Test: BouchaudMicrostructureConfig funktioniert korrekt."""
        from src.strategies.bouchaud.bouchaud_microstructure_strategy import (
            BouchaudMicrostructureConfig,
        )

        cfg = BouchaudMicrostructureConfig(
            use_orderbook_imbalance=True,
            lookback_ticks=50,
        )

        assert cfg.use_orderbook_imbalance is True
        assert cfg.lookback_ticks == 50

        # to_dict Test
        cfg_dict = cfg.to_dict()
        assert cfg_dict["use_orderbook_imbalance"] is True
        assert cfg_dict["lookback_ticks"] == 50

    def test_bouchaud_repr_shows_skeleton(self):
        """Test: __repr__ zeigt SKELETON / NOT IMPLEMENTED an."""
        from src.strategies.bouchaud import BouchaudMicrostructureStrategy

        strategy = BouchaudMicrostructureStrategy()
        repr_str = repr(strategy)

        assert "SKELETON" in repr_str or "NOT IMPLEMENTED" in repr_str

    def test_bouchaud_metadata_contains_warning(self):
        """Test: Metadata enthält Warnung über Skeleton/Research-Only."""
        from src.strategies.bouchaud import BouchaudMicrostructureStrategy

        strategy = BouchaudMicrostructureStrategy()
        desc_upper = strategy.meta.description.upper()

        assert (
            "SKELETON" in desc_upper or
            "PLATZHALTER" in desc_upper or
            "NICHT FÜR LIVE" in desc_upper or
            "RESEARCH" in desc_upper
        )


# =============================================================================
# VOL REGIME OVERLAY STRATEGY TESTS
# =============================================================================


class TestVolRegimeOverlayStrategy:
    """Tests für VolRegimeOverlayStrategy."""

    def test_import_vol_regime_overlay_strategy(self):
        """Test: VolRegimeOverlay-Strategie kann importiert werden."""
        from src.strategies.gatheral_cont import VolRegimeOverlayStrategy

        assert VolRegimeOverlayStrategy is not None
        assert VolRegimeOverlayStrategy.KEY == "vol_regime_overlay"

    def test_vol_regime_overlay_is_research_only(self):
        """Test: VolRegimeOverlay ist als Research-Only markiert."""
        from src.strategies.gatheral_cont import VolRegimeOverlayStrategy

        assert VolRegimeOverlayStrategy.IS_LIVE_READY is False
        assert VolRegimeOverlayStrategy.TIER == "r_and_d"
        assert "research" in VolRegimeOverlayStrategy.ALLOWED_ENVIRONMENTS
        assert "live" not in VolRegimeOverlayStrategy.ALLOWED_ENVIRONMENTS
        assert "testnet" not in VolRegimeOverlayStrategy.ALLOWED_ENVIRONMENTS
        assert "shadow" not in VolRegimeOverlayStrategy.ALLOWED_ENVIRONMENTS

    def test_vol_regime_overlay_instantiation_default(self):
        """Test: VolRegimeOverlay-Strategie kann mit Defaults instanziiert werden."""
        from src.strategies.gatheral_cont import VolRegimeOverlayStrategy

        strategy = VolRegimeOverlayStrategy()

        assert strategy is not None
        assert strategy.cfg.day_vol_budget == 0.02
        assert strategy.cfg.max_intraday_dd == 0.01
        assert strategy.cfg.regime_lookback_bars == 100
        assert strategy.cfg.high_vol_threshold == 0.75
        assert strategy.cfg.low_vol_threshold == 0.25

    def test_vol_regime_overlay_instantiation_custom(self):
        """Test: VolRegimeOverlay-Strategie mit Custom-Config."""
        from src.strategies.gatheral_cont import VolRegimeOverlayStrategy

        strategy = VolRegimeOverlayStrategy(
            day_vol_budget=0.03,
            max_intraday_dd=0.015,
            regime_lookback_bars=200,
            use_rough_vol=True,
        )

        assert strategy.cfg.day_vol_budget == 0.03
        assert strategy.cfg.max_intraday_dd == 0.015
        assert strategy.cfg.regime_lookback_bars == 200
        assert strategy.cfg.use_rough_vol is True

    def test_vol_regime_overlay_generate_signals_raises_not_implemented(self):
        """Test: generate_signals wirft NotImplementedError (Meta-Layer)."""
        from src.strategies.gatheral_cont import VolRegimeOverlayStrategy

        strategy = VolRegimeOverlayStrategy()

        # Test-Daten erstellen
        dates = pd.date_range("2020-01-01", periods=100, freq="h")
        data = pd.DataFrame(
            {
                "close": np.random.randn(100).cumsum() + 100,
            },
            index=dates,
        )

        # Meta-Layer sollte NotImplementedError werfen
        with pytest.raises(NotImplementedError) as exc_info:
            strategy.generate_signals(data)

        # Prüfe, dass die Fehlermeldung informativ ist
        assert "Meta-Layer" in str(exc_info.value) or \
               "kein Signal-Generator" in str(exc_info.value) or \
               "RESEARCH-ONLY" in str(exc_info.value)

    def test_vol_regime_overlay_get_regime_state_raises_not_implemented(self):
        """Test: get_regime_state wirft NotImplementedError."""
        from src.strategies.gatheral_cont import VolRegimeOverlayStrategy

        strategy = VolRegimeOverlayStrategy()
        data = pd.DataFrame({"close": [100, 101, 102]})

        with pytest.raises(NotImplementedError):
            strategy.get_regime_state(data)

    def test_vol_regime_overlay_get_position_scalar_raises_not_implemented(self):
        """Test: get_position_scalar wirft NotImplementedError."""
        from src.strategies.gatheral_cont import VolRegimeOverlayStrategy

        strategy = VolRegimeOverlayStrategy()
        data = pd.DataFrame({"close": [100, 101, 102]})

        with pytest.raises(NotImplementedError):
            strategy.get_position_scalar(data)

    def test_vol_regime_overlay_config_dataclass(self):
        """Test: VolRegimeOverlayConfig funktioniert korrekt."""
        from src.strategies.gatheral_cont.vol_regime_overlay_strategy import (
            VolRegimeOverlayConfig,
        )

        cfg = VolRegimeOverlayConfig(
            day_vol_budget=0.025,
            max_intraday_dd=0.012,
        )

        assert cfg.day_vol_budget == 0.025
        assert cfg.max_intraday_dd == 0.012

        # to_dict Test
        cfg_dict = cfg.to_dict()
        assert cfg_dict["day_vol_budget"] == 0.025
        assert cfg_dict["max_intraday_dd"] == 0.012

    def test_vol_regime_overlay_repr_shows_skeleton(self):
        """Test: __repr__ zeigt SKELETON / NOT IMPLEMENTED an."""
        from src.strategies.gatheral_cont import VolRegimeOverlayStrategy

        strategy = VolRegimeOverlayStrategy()
        repr_str = repr(strategy)

        assert "SKELETON" in repr_str or "NOT IMPLEMENTED" in repr_str

    def test_vol_regime_overlay_metadata_contains_warning(self):
        """Test: Metadata enthält Warnung über Skeleton/Research-Only."""
        from src.strategies.gatheral_cont import VolRegimeOverlayStrategy

        strategy = VolRegimeOverlayStrategy()
        desc_upper = strategy.meta.description.upper()

        assert (
            "SKELETON" in desc_upper or
            "PLATZHALTER" in desc_upper or
            "NICHT FÜR LIVE" in desc_upper or
            "META" in desc_upper
        )


# =============================================================================
# REGISTRY TESTS
# =============================================================================


class TestStrategyRegistry:
    """Tests für Strategy-Registry mit Bouchaud & Gatheral/Cont Strategien."""

    def test_bouchaud_registered_in_registry(self):
        """Test: Bouchaud ist in der Registry registriert."""
        from src.strategies.registry import get_available_strategy_keys, get_strategy_spec

        keys = get_available_strategy_keys()
        assert "bouchaud_microstructure" in keys

        spec = get_strategy_spec("bouchaud_microstructure")
        assert spec.key == "bouchaud_microstructure"
        assert "R&D" in spec.description or "Skeleton" in spec.description or "Bouchaud" in spec.description

    def test_vol_regime_overlay_registered_in_registry(self):
        """Test: VolRegimeOverlay ist in der Registry registriert."""
        from src.strategies.registry import get_available_strategy_keys, get_strategy_spec

        keys = get_available_strategy_keys()
        assert "vol_regime_overlay" in keys

        spec = get_strategy_spec("vol_regime_overlay")
        assert spec.key == "vol_regime_overlay"
        assert "R&D" in spec.description or "Skeleton" in spec.description or "Gatheral" in spec.description


# =============================================================================
# TIERING TESTS
# =============================================================================


class TestStrategyTiering:
    """Tests für Strategy-Tiering mit neuen Skeleton-Strategien."""

    def test_tiering_config_contains_bouchaud(self):
        """Test: Tiering-Config enthält Bouchaud-Strategie."""
        from src.experiments.strategy_profiles import load_tiering_config

        tiering = load_tiering_config()

        assert "bouchaud_microstructure" in tiering
        assert tiering["bouchaud_microstructure"].tier == "r_and_d"
        assert tiering["bouchaud_microstructure"].allow_live is False

    def test_tiering_config_contains_vol_regime_overlay(self):
        """Test: Tiering-Config enthält VolRegimeOverlay-Strategie."""
        from src.experiments.strategy_profiles import load_tiering_config

        tiering = load_tiering_config()

        assert "vol_regime_overlay" in tiering
        assert tiering["vol_regime_overlay"].tier == "r_and_d"
        assert tiering["vol_regime_overlay"].allow_live is False


# =============================================================================
# API INTEGRATION TESTS
# =============================================================================


class TestStrategyTieringAPI:
    """Tests für API-Integration der Skeleton-Strategien."""

    def test_load_strategy_tiering_includes_skeletons_with_flag(self):
        """Test: API inkludiert Skeleton-Strategien mit include_research=True."""
        from src.webui.app import load_strategy_tiering

        tiering = load_strategy_tiering(include_research=True)

        strategy_ids = [r["id"] for r in tiering.get("rows", [])]
        assert "bouchaud_microstructure" in strategy_ids
        assert "vol_regime_overlay" in strategy_ids

    def test_load_strategy_tiering_excludes_skeletons_without_flag(self):
        """Test: API exkludiert Skeleton-Strategien ohne include_research Flag."""
        from src.webui.app import load_strategy_tiering

        tiering = load_strategy_tiering(include_research=False)

        strategy_ids = [r["id"] for r in tiering.get("rows", [])]
        assert "bouchaud_microstructure" not in strategy_ids
        assert "vol_regime_overlay" not in strategy_ids

    def test_skeleton_strategies_have_correct_allowed_environments(self):
        """Test: Skeleton-Strategien haben korrekte allowed_environments."""
        from src.webui.app import load_strategy_tiering

        tiering = load_strategy_tiering(include_research=True)

        for row in tiering.get("rows", []):
            if row["id"] in ["bouchaud_microstructure", "vol_regime_overlay"]:
                assert "offline_backtest" in row["allowed_environments"]
                assert "research" in row["allowed_environments"]
                assert "live" not in row["allowed_environments"]
                assert "testnet" not in row["allowed_environments"]


# =============================================================================
# SAFETY TESTS
# =============================================================================


class TestResearchStrategySafety:
    """Tests für Safety-Constraints der Skeleton-Strategien."""

    def test_all_skeleton_strategies_have_is_live_ready_false(self):
        """Test: Alle Skeleton-Strategien haben IS_LIVE_READY=False."""
        from src.strategies.bouchaud import BouchaudMicrostructureStrategy
        from src.strategies.gatheral_cont import VolRegimeOverlayStrategy

        assert BouchaudMicrostructureStrategy.IS_LIVE_READY is False
        assert VolRegimeOverlayStrategy.IS_LIVE_READY is False

    def test_all_skeleton_strategies_have_r_and_d_tier(self):
        """Test: Alle Skeleton-Strategien haben TIER='r_and_d'."""
        from src.strategies.bouchaud import BouchaudMicrostructureStrategy
        from src.strategies.gatheral_cont import VolRegimeOverlayStrategy

        assert BouchaudMicrostructureStrategy.TIER == "r_and_d"
        assert VolRegimeOverlayStrategy.TIER == "r_and_d"

    def test_skeleton_strategies_only_allow_research_environments(self):
        """Test: Skeleton-Strategien erlauben nur Research-Environments."""
        from src.strategies.bouchaud import BouchaudMicrostructureStrategy
        from src.strategies.gatheral_cont import VolRegimeOverlayStrategy

        allowed_envs_bouchaud = set(BouchaudMicrostructureStrategy.ALLOWED_ENVIRONMENTS)
        allowed_envs_vol = set(VolRegimeOverlayStrategy.ALLOWED_ENVIRONMENTS)

        # Nur offline_backtest und research erlaubt
        expected = {"offline_backtest", "research"}
        assert allowed_envs_bouchaud == expected
        assert allowed_envs_vol == expected


# =============================================================================
# FASTAPI INTEGRATION TESTS
# =============================================================================


class TestFastAPIEndpoints:
    """Integration-Tests für FastAPI-Endpoints mit Skeleton-Strategien."""

    @pytest.fixture
    def client(self):
        """FastAPI TestClient."""
        try:
            from fastapi.testclient import TestClient
            from src.webui.app import app

            return TestClient(app)
        except ImportError:
            pytest.skip("fastapi.testclient nicht verfügbar")

    def test_api_includes_bouchaud_with_research_flag(self, client):
        """Test: API inkludiert Bouchaud mit include_research=true."""
        response = client.get("/api/strategy_tiering?include_research=true")
        assert response.status_code == 200

        data = response.json()
        all_strategy_ids = []
        for tier_group in data.get("tiers", []):
            for s in tier_group.get("strategies", []):
                all_strategy_ids.append(s["id"])

        assert "bouchaud_microstructure" in all_strategy_ids

    def test_api_includes_vol_regime_overlay_with_research_flag(self, client):
        """Test: API inkludiert VolRegimeOverlay mit include_research=true."""
        response = client.get("/api/strategy_tiering?include_research=true")
        assert response.status_code == 200

        data = response.json()
        all_strategy_ids = []
        for tier_group in data.get("tiers", []):
            for s in tier_group.get("strategies", []):
                all_strategy_ids.append(s["id"])

        assert "vol_regime_overlay" in all_strategy_ids


# =============================================================================
# RUN TESTS
# =============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])



