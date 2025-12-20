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


class TestArmstrongCycleStrategy:
    """Tests für ArmstrongCycleStrategy."""

    def test_import_armstrong_strategy(self):
        """Test: Armstrong-Strategie kann importiert werden."""
        from src.strategies.armstrong import ArmstrongCycleStrategy

        assert ArmstrongCycleStrategy is not None
        assert ArmstrongCycleStrategy.KEY == "armstrong_cycle"

    def test_armstrong_is_research_only(self):
        """Test: Armstrong ist als Research-Only markiert."""
        from src.strategies.armstrong import ArmstrongCycleStrategy

        assert ArmstrongCycleStrategy.IS_LIVE_READY is False
        assert ArmstrongCycleStrategy.TIER == "r_and_d"
        assert "research" in ArmstrongCycleStrategy.ALLOWED_ENVIRONMENTS
        assert "live" not in ArmstrongCycleStrategy.ALLOWED_ENVIRONMENTS

    def test_armstrong_instantiation(self):
        """Test: Armstrong-Strategie kann instanziiert werden."""
        from src.strategies.armstrong import ArmstrongCycleStrategy

        strategy = ArmstrongCycleStrategy()

        assert strategy is not None
        assert strategy.cycle_length_days == 3141  # ECM-Default
        assert strategy.event_window_days == 90
        assert "RESEARCH" in strategy.meta.description.upper()

    def test_armstrong_generate_signals_returns_flat(self):
        """Test: Armstrong generate_signals gibt Flat-Signal (Research-Stub)."""
        from src.strategies.armstrong import ArmstrongCycleStrategy

        strategy = ArmstrongCycleStrategy()

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

        # Research-Stub: Alle Signale sollten 0 (flat) sein
        assert isinstance(signals, pd.Series)
        assert len(signals) == len(data)
        assert (signals == 0).all(), "Research-Stub sollte nur Flat-Signale liefern"

    def test_armstrong_cycle_info(self):
        """Test: get_cycle_info gibt valide Informationen zurück."""
        from src.strategies.armstrong import ArmstrongCycleStrategy

        strategy = ArmstrongCycleStrategy()
        test_date = pd.Timestamp("2024-06-15")

        info = strategy.get_cycle_info(test_date)

        assert "cycle_phase" in info
        assert "is_near_turning_point" in info
        assert "next_turning_point" in info
        assert 0 <= info["cycle_phase"] <= 1
        assert isinstance(info["is_near_turning_point"], bool)

    def test_armstrong_repr_shows_research_only(self):
        """Test: __repr__ zeigt RESEARCH-ONLY an."""
        from src.strategies.armstrong import ArmstrongCycleStrategy

        strategy = ArmstrongCycleStrategy()
        repr_str = repr(strategy)

        assert "RESEARCH-ONLY" in repr_str


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

    def test_el_karoui_generate_signals_returns_flat(self):
        """Test: El-Karoui generate_signals gibt Flat-Signal (Research-Stub)."""
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

        # Research-Stub: Alle Signale sollten 0 (flat) sein
        assert isinstance(signals, pd.Series)
        assert len(signals) == len(data)
        assert (signals == 0).all(), "Research-Stub sollte nur Flat-Signale liefern"

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
        assert analysis["vol_regime"] in {"low", "medium", "high"}

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

    def test_armstrong_registered_in_registry(self):
        """Test: Armstrong ist in der Registry registriert."""
        from src.strategies.registry import get_available_strategy_keys, get_strategy_spec

        keys = get_available_strategy_keys()
        assert "armstrong_cycle" in keys

        spec = get_strategy_spec("armstrong_cycle")
        assert spec.key == "armstrong_cycle"
        assert "R&D" in spec.description or "Research" in spec.description

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

        assert "armstrong_cycle" in tiering
        assert "el_karoui_vol_model" in tiering

    def test_armstrong_has_r_and_d_tier(self):
        """Test: Armstrong hat Tier 'r_and_d'."""
        from src.experiments.strategy_profiles import load_tiering_config

        tiering = load_tiering_config()

        assert tiering["armstrong_cycle"].tier == "r_and_d"
        assert tiering["armstrong_cycle"].allow_live is False

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
@pytest.mark.skipif(not FASTAPI_AVAILABLE, reason="FastAPI not installed")
class TestAllRnDStrategiesInTiering:
    """Tests: Alle R&D-Strategien sind in der Tiering-Struktur mit korrekten Feldern."""

    # Erwartete R&D-Strategien mit ihren Kategorien
    EXPECTED_RND_STRATEGIES = {
        "armstrong_cycle": {
            "label": "Armstrong Cycle Strategy",
            "category": "cycles",
        },
        "ehlers_cycle_filter": {
            "label": "Ehlers Cycle Filter",
            "category": "cycles",
        },
        "el_karoui_vol_model": {
            "label": "El Karoui Volatility Model",
            "category": "volatility",
        },
        "bouchaud_microstructure": {
            "label": "Bouchaud Microstructure Overlay",
            "category": "microstructure",
        },
        "vol_regime_overlay": {
            "label": "Gatheral Cont Vol Overlay",
            "category": "volatility",
        },
        "meta_labeling": {
            "label": "Lopez de Prado Meta-Labeling",
            "category": "ml",
        },
    }

    def test_all_rnd_strategies_present(self):
        """Test: Alle erwarteten R&D-Strategien sind im Tiering vorhanden."""
        from src.webui.app import load_strategy_tiering

        tiering = load_strategy_tiering(include_research=True)
        r_and_d_ids = [r["id"] for r in tiering["rows"] if r["tier"] == "r_and_d"]

        for strategy_id in self.EXPECTED_RND_STRATEGIES:
            assert strategy_id in r_and_d_ids, f"R&D-Strategie '{strategy_id}' fehlt im Tiering"

    def test_all_rnd_strategies_have_r_and_d_tier(self):
        """Test: Alle R&D-Strategien haben tier='r_and_d'."""
        from src.webui.app import load_strategy_tiering

        tiering = load_strategy_tiering(include_research=True)

        for strategy_id in self.EXPECTED_RND_STRATEGIES:
            row = next((r for r in tiering["rows"] if r["id"] == strategy_id), None)
            assert row is not None, f"Strategie '{strategy_id}' nicht gefunden"
            assert row["tier"] == "r_and_d", f"Strategie '{strategy_id}' hat falschen Tier"

    def test_all_rnd_strategies_have_correct_category(self):
        """Test: Alle R&D-Strategien haben die erwartete category."""
        from src.webui.app import load_strategy_tiering

        tiering = load_strategy_tiering(include_research=True)

        for strategy_id, expected in self.EXPECTED_RND_STRATEGIES.items():
            row = next((r for r in tiering["rows"] if r["id"] == strategy_id), None)
            assert row is not None, f"Strategie '{strategy_id}' nicht gefunden"
            assert row.get("category") == expected["category"], (
                f"Strategie '{strategy_id}' hat category='{row.get('category')}', "
                f"erwartet: '{expected['category']}'"
            )

    def test_all_rnd_strategies_have_label(self):
        """Test: Alle R&D-Strategien haben ein Label."""
        from src.webui.app import load_strategy_tiering

        tiering = load_strategy_tiering(include_research=True)

        for strategy_id, expected in self.EXPECTED_RND_STRATEGIES.items():
            row = next((r for r in tiering["rows"] if r["id"] == strategy_id), None)
            assert row is not None, f"Strategie '{strategy_id}' nicht gefunden"
            assert row.get("label") == expected["label"], (
                f"Strategie '{strategy_id}' hat label='{row.get('label')}', "
                f"erwartet: '{expected['label']}'"
            )

    def test_all_rnd_strategies_have_experimental_risk_profile(self):
        """Test: Alle R&D-Strategien haben risk_profile='experimental'."""
        from src.webui.app import load_strategy_tiering

        tiering = load_strategy_tiering(include_research=True)

        for strategy_id in self.EXPECTED_RND_STRATEGIES:
            row = next((r for r in tiering["rows"] if r["id"] == strategy_id), None)
            assert row is not None, f"Strategie '{strategy_id}' nicht gefunden"
            assert row.get("risk_profile") == "experimental", (
                f"Strategie '{strategy_id}' hat risk_profile='{row.get('risk_profile')}', "
                f"erwartet: 'experimental'"
            )

    def test_all_rnd_strategies_have_research_owner(self):
        """Test: Alle R&D-Strategien haben owner='research'."""
        from src.webui.app import load_strategy_tiering

        tiering = load_strategy_tiering(include_research=True)

        for strategy_id in self.EXPECTED_RND_STRATEGIES:
            row = next((r for r in tiering["rows"] if r["id"] == strategy_id), None)
            assert row is not None, f"Strategie '{strategy_id}' nicht gefunden"
            assert row.get("owner") == "research", (
                f"Strategie '{strategy_id}' hat owner='{row.get('owner')}', "
                f"erwartet: 'research'"
            )

    def test_all_rnd_strategies_have_tags(self):
        """Test: Alle R&D-Strategien haben Tags (nicht leer)."""
        from src.webui.app import load_strategy_tiering

        tiering = load_strategy_tiering(include_research=True)

        for strategy_id in self.EXPECTED_RND_STRATEGIES:
            row = next((r for r in tiering["rows"] if r["id"] == strategy_id), None)
            assert row is not None, f"Strategie '{strategy_id}' nicht gefunden"
            tags = row.get("tags", [])
            assert isinstance(tags, list), f"Strategie '{strategy_id}' hat keine Tags-Liste"
            assert len(tags) > 0, f"Strategie '{strategy_id}' hat leere Tags"

    def test_rnd_categories_available(self):
        """Test: Alle erwarteten Kategorien sind verfügbar."""
        from src.webui.app import load_strategy_tiering

        tiering = load_strategy_tiering(include_research=True)
        category_ids = [c["id"] for c in tiering.get("categories", [])]

        expected_categories = {"cycles", "volatility", "microstructure", "ml"}
        for cat in expected_categories:
            assert cat in category_ids, f"Kategorie '{cat}' fehlt in categories"

    def test_rnd_tier_has_by_category_grouping(self):
        """Test: R&D-Tier hat by_category Gruppierung."""
        from src.webui.app import load_strategy_tiering

        tiering = load_strategy_tiering(include_research=True)

        r_and_d_tier = next(
            (t for t in tiering.get("tiers", []) if t["tier"] == "r_and_d"),
            None
        )
        assert r_and_d_tier is not None, "R&D-Tier nicht gefunden"
        assert "by_category" in r_and_d_tier, "R&D-Tier hat keine by_category Gruppierung"

        # Prüfe, dass jede Kategorie Strategien enthält
        for cat_group in r_and_d_tier["by_category"]:
            assert "category" in cat_group
            assert "label" in cat_group
            assert "strategies" in cat_group
            assert len(cat_group["strategies"]) > 0


# =============================================================================
# WebUI/API Tests
# =============================================================================


@pytest.mark.web
@pytest.mark.skipif(not FASTAPI_AVAILABLE, reason="FastAPI not installed")
class TestStrategyTieringAPI:
    """Tests für Strategy-Tiering API-Endpoints."""

    def test_load_strategy_tiering_excludes_research_by_default(self):
        """Test: load_strategy_tiering schließt R&D standardmäßig aus."""
        from src.webui.app import load_strategy_tiering

        tiering = load_strategy_tiering(include_research=False)

        # Prüfe, dass keine R&D-Strategien enthalten sind
        for row in tiering.get("rows", []):
            assert row["tier"] != "r_and_d", f"R&D-Strategie {row['id']} sollte gefiltert sein"

        # Prüfe auch die Tier-Gruppen
        for tier_group in tiering.get("tiers", []):
            assert tier_group["tier"] != "r_and_d", "R&D-Tier sollte gefiltert sein"

    def test_load_strategy_tiering_includes_research_when_requested(self):
        """Test: load_strategy_tiering inkludiert R&D mit Flag."""
        from src.webui.app import load_strategy_tiering

        tiering = load_strategy_tiering(include_research=True)

        # Prüfe, dass R&D-Strategien enthalten sind
        r_and_d_strategies = [r for r in tiering.get("rows", []) if r["tier"] == "r_and_d"]
        assert len(r_and_d_strategies) >= 2, "Mindestens Armstrong und El-Karoui sollten vorhanden sein"

        # Prüfe spezifische Strategien
        strategy_ids = [r["id"] for r in r_and_d_strategies]
        assert "armstrong_cycle" in strategy_ids
        assert "el_karoui_vol_model" in strategy_ids

    def test_r_and_d_strategies_have_correct_allowed_environments(self):
        """Test: R&D-Strategien haben nur offline_backtest und research als Environments."""
        from src.webui.app import load_strategy_tiering

        tiering = load_strategy_tiering(include_research=True)

        for row in tiering.get("rows", []):
            if row["tier"] == "r_and_d":
                assert "offline_backtest" in row["allowed_environments"]
                assert "research" in row["allowed_environments"]
                assert "live" not in row["allowed_environments"]
                assert "testnet" not in row["allowed_environments"]
                assert row["is_live_ready"] is False

    def test_r_and_d_strategies_in_separate_tier_group(self):
        """Test: R&D-Strategien sind in eigener Tier-Gruppe."""
        from src.webui.app import load_strategy_tiering

        tiering = load_strategy_tiering(include_research=True)

        r_and_d_tier = None
        for tier_group in tiering.get("tiers", []):
            if tier_group["tier"] == "r_and_d":
                r_and_d_tier = tier_group
                break

        assert r_and_d_tier is not None, "R&D-Tier-Gruppe sollte existieren"
        assert r_and_d_tier["label"] == "R&D / Research"
        assert len(r_and_d_tier["strategies"]) >= 2


# =============================================================================
# Safety Tests
# =============================================================================


@pytest.mark.web
@pytest.mark.skipif(not FASTAPI_AVAILABLE, reason="FastAPI not installed")
class TestResearchStrategySafety:
    """Tests für Safety-Constraints von Research-Strategien."""

    def test_research_strategies_not_in_standard_tiering(self):
        """Test: Research-Strategien erscheinen nicht in Standard-Tiering-Abfrage."""
        from src.webui.app import load_strategy_tiering

        # Standard-Abfrage (ohne include_research)
        tiering = load_strategy_tiering()

        strategy_ids = [r["id"] for r in tiering.get("rows", [])]
        assert "armstrong_cycle" not in strategy_ids
        assert "el_karoui_vol_model" not in strategy_ids

    def test_research_strategies_have_deployment_blocked(self):
        """Test: Research-Strategien sollten deployment_blocked haben."""
        from src.webui.app import load_strategy_tiering

        tiering = load_strategy_tiering(include_research=True)

        for row in tiering.get("rows", []):
            if row["tier"] == "r_and_d":
                # is_live_ready sollte False sein
                assert row["is_live_ready"] is False
                # allow_live sollte False sein
                assert row["allow_live"] is False

    def test_research_strategy_metadata_contains_warning(self):
        """Test: Research-Strategy-Metadata enthält Warnung."""
        from src.strategies.armstrong import ArmstrongCycleStrategy
        from src.strategies.el_karoui import ElKarouiVolModelStrategy

        armstrong = ArmstrongCycleStrategy()
        el_karoui = ElKarouiVolModelStrategy()

        # Prüfe Metadata
        assert "NICHT FÜR LIVE" in armstrong.meta.description.upper() or \
               "NOT FOR LIVE" in armstrong.meta.description.upper() or \
               "RESEARCH" in armstrong.meta.description.upper()

        assert "NICHT FÜR LIVE" in el_karoui.meta.description.upper() or \
               "NOT FOR LIVE" in el_karoui.meta.description.upper() or \
               "RESEARCH" in el_karoui.meta.description.upper()


# =============================================================================
# FastAPI Integration Tests (requires TestClient)
# =============================================================================


@pytest.mark.web
@pytest.mark.skipif(not FASTAPI_AVAILABLE, reason="FastAPI not installed")
class TestStrategyTieringAPIEndpoints:
    """Integration-Tests für FastAPI-Endpoints."""

    @pytest.fixture
    def client(self):
        """FastAPI TestClient."""
        from fastapi.testclient import TestClient
        from src.webui.app import app

        return TestClient(app)

    def test_api_strategy_tiering_excludes_research_by_default(self, client):
        """Test: API /api/strategy_tiering schließt R&D standardmäßig aus."""
        response = client.get("/api/strategy_tiering")
        assert response.status_code == 200

        data = response.json()
        assert data["include_research"] is False

        # Prüfe, dass kein R&D-Tier in tiers ist
        tier_names = [t["tier"] for t in data.get("tiers", [])]
        assert "r_and_d" not in tier_names

    def test_api_strategy_tiering_includes_research_with_flag(self, client):
        """Test: API /api/strategy_tiering inkludiert R&D mit Flag."""
        response = client.get("/api/strategy_tiering?include_research=true")
        assert response.status_code == 200

        data = response.json()
        assert data["include_research"] is True
        assert data["research_notice"] is not None

        # Prüfe, dass R&D-Tier in tiers ist
        tier_names = [t["tier"] for t in data.get("tiers", [])]
        assert "r_and_d" in tier_names

        # Prüfe R&D-Strategien
        r_and_d_tier = next(t for t in data["tiers"] if t["tier"] == "r_and_d")
        strategy_ids = [s["id"] for s in r_and_d_tier["strategies"]]
        assert "armstrong_cycle" in strategy_ids
        assert "el_karoui_vol_model" in strategy_ids

    def test_api_strategy_tiering_detail_blocks_research_without_flag(self, client):
        """Test: API /api/strategy_tiering/{id} blockiert R&D ohne Flag."""
        response = client.get("/api/strategy_tiering/armstrong_cycle")
        assert response.status_code == 404

    def test_api_strategy_tiering_detail_allows_research_with_flag(self, client):
        """Test: API /api/strategy_tiering/{id} erlaubt R&D mit Flag."""
        response = client.get("/api/strategy_tiering/armstrong_cycle?include_research=true")
        assert response.status_code == 200

        data = response.json()
        assert data["id"] == "armstrong_cycle"
        assert data["tier"] == "r_and_d"
        assert data["deployment_blocked"] is True
        assert "deployment_notice" in data


# =============================================================================
# Run Tests
# =============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
