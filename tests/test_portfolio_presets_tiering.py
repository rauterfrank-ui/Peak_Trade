# tests/test_portfolio_presets_tiering.py
"""
Tests für Phase 80: Tiered Portfolio Presets

Testet:
- Tiering-Helper-Funktionen
- Portfolio-Preset-Validierung gegen Tiering-Regeln
- Core-Presets enthalten keine Legacy-Strategien
- Core+Aux-Presets enthalten nur Core und Aux
"""

import pytest
from pathlib import Path

from src.experiments.portfolio_presets import (
    get_strategies_by_tier,
    get_tiering_aware_strategies,
    get_all_tiered_strategies,
    get_strategy_tier,
    validate_preset_tiering_compliance,
    validate_all_presets_tiering,
    load_tiered_preset,
    build_core_only_preset,
    build_core_plus_aux_preset,
    TieringComplianceResult,
    VALID_TIERS,
)
from src.experiments.portfolio_recipes import load_portfolio_recipes
from src.experiments.strategy_profiles import load_tiering_config


# =============================================================================
# FIXTURES
# =============================================================================


@pytest.fixture
def tiering_config_path():
    """Pfad zur Tiering-Config."""
    return Path("config/strategy_tiering.toml")


@pytest.fixture
def presets_dir():
    """Pfad zum Presets-Verzeichnis."""
    return Path("config/portfolio_presets")


@pytest.fixture
def tiering_config(tiering_config_path):
    """Geladene Tiering-Config."""
    return load_tiering_config(tiering_config_path)


# =============================================================================
# TESTS: TIERING HELPERS
# =============================================================================


class TestGetStrategiesByTier:
    """Tests für get_strategies_by_tier."""

    def test_get_core_strategies(self, tiering_config_path):
        """Core-Strategien werden korrekt zurückgegeben."""
        core = get_strategies_by_tier("core", tiering_config_path)

        assert isinstance(core, list)
        assert len(core) >= 1, "Es sollte mindestens eine Core-Strategie geben"

        # Bekannte Core-Strategien prüfen
        expected_core = {"rsi_reversion", "ma_crossover", "bollinger_bands"}
        assert set(core) == expected_core, f"Expected {expected_core}, got {set(core)}"

    def test_get_aux_strategies(self, tiering_config_path):
        """Aux-Strategien werden korrekt zurückgegeben."""
        aux = get_strategies_by_tier("aux", tiering_config_path)

        assert isinstance(aux, list)
        assert len(aux) >= 1, "Es sollte mindestens eine Aux-Strategie geben"

        # Einige bekannte Aux-Strategien prüfen
        assert "breakout" in aux
        assert "macd" in aux

    def test_get_legacy_strategies(self, tiering_config_path):
        """Legacy-Strategien werden korrekt zurückgegeben."""
        legacy = get_strategies_by_tier("legacy", tiering_config_path)

        assert isinstance(legacy, list)
        # Legacy sollte existieren aber nicht leer sein
        assert len(legacy) >= 1, "Es sollte mindestens eine Legacy-Strategie geben"

        # Bekannte Legacy-Strategien
        expected_legacy = {"breakout_donchian", "my_strategy", "vol_breakout"}
        assert set(legacy) == expected_legacy

    def test_invalid_tier_returns_empty(self, tiering_config_path):
        """Ungültiges Tier gibt leere Liste zurück."""
        result = get_strategies_by_tier("invalid_tier", tiering_config_path)
        assert result == []


class TestGetTieringAwareStrategies:
    """Tests für get_tiering_aware_strategies."""

    def test_default_returns_core_only(self, tiering_config_path):
        """Default gibt nur Core-Strategien zurück."""
        result = get_tiering_aware_strategies(tiering_config_path=tiering_config_path)
        core = get_strategies_by_tier("core", tiering_config_path)
        assert set(result) == set(core)

    def test_include_core_and_aux(self, tiering_config_path):
        """Core + Aux Include funktioniert."""
        result = get_tiering_aware_strategies(
            include_tiers=["core", "aux"],
            tiering_config_path=tiering_config_path,
        )

        core = get_strategies_by_tier("core", tiering_config_path)
        aux = get_strategies_by_tier("aux", tiering_config_path)

        assert set(result) == set(core) | set(aux)

    def test_exclude_legacy(self, tiering_config_path):
        """Legacy-Ausschluss funktioniert."""
        result = get_tiering_aware_strategies(
            include_tiers=["core", "aux", "legacy"],
            exclude_tiers=["legacy"],
            tiering_config_path=tiering_config_path,
        )

        legacy = get_strategies_by_tier("legacy", tiering_config_path)

        for strat in legacy:
            assert strat not in result


class TestGetAllTieredStrategies:
    """Tests für get_all_tiered_strategies."""

    def test_returns_all_tiers(self, tiering_config_path):
        """Alle Tiers werden zurückgegeben."""
        result = get_all_tiered_strategies(tiering_config_path)

        assert "core" in result
        assert "aux" in result
        assert "legacy" in result
        assert "unclassified" in result

    def test_no_overlap_between_tiers(self, tiering_config_path):
        """Keine Strategie ist in mehreren Tiers."""
        result = get_all_tiered_strategies(tiering_config_path)

        all_strategies = []
        for tier_strategies in result.values():
            all_strategies.extend(tier_strategies)

        # Keine Duplikate
        assert len(all_strategies) == len(set(all_strategies))


class TestGetStrategyTier:
    """Tests für get_strategy_tier."""

    def test_known_core_strategy(self, tiering_config_path):
        """Bekannte Core-Strategie wird korrekt erkannt."""
        tier = get_strategy_tier("rsi_reversion", tiering_config_path)
        assert tier == "core"

    def test_known_legacy_strategy(self, tiering_config_path):
        """Bekannte Legacy-Strategie wird korrekt erkannt."""
        tier = get_strategy_tier("breakout_donchian", tiering_config_path)
        assert tier == "legacy"

    def test_unknown_strategy_returns_unclassified(self, tiering_config_path):
        """Unbekannte Strategie gibt 'unclassified' zurück."""
        tier = get_strategy_tier("nonexistent_strategy", tiering_config_path)
        assert tier == "unclassified"


# =============================================================================
# TESTS: PRESET VALIDATION
# =============================================================================


class TestValidatePresetTieringCompliance:
    """Tests für validate_preset_tiering_compliance."""

    def test_core_balanced_is_compliant(self, presets_dir, tiering_config_path):
        """core_balanced enthält nur Core-Strategien."""
        preset_file = presets_dir / "core_balanced.toml"
        if not preset_file.exists():
            pytest.skip("core_balanced.toml not found")

        recipes = load_portfolio_recipes(preset_file)
        recipe = recipes.get("core_balanced")

        result = validate_preset_tiering_compliance(
            "core_balanced",
            allowed_tiers=["core"],
            recipe=recipe,
            tiering_config_path=tiering_config_path,
        )

        assert result.is_compliant, f"core_balanced should be compliant: {result}"
        assert len(result.violations) == 0

    def test_core_trend_meanreversion_is_compliant(self, presets_dir, tiering_config_path):
        """core_trend_meanreversion enthält nur Core-Strategien."""
        preset_file = presets_dir / "core_trend_meanreversion.toml"
        if not preset_file.exists():
            pytest.skip("core_trend_meanreversion.toml not found")

        recipes = load_portfolio_recipes(preset_file)
        recipe = recipes.get("core_trend_meanreversion")

        result = validate_preset_tiering_compliance(
            "core_trend_meanreversion",
            allowed_tiers=["core"],
            recipe=recipe,
            tiering_config_path=tiering_config_path,
        )

        assert result.is_compliant, f"core_trend_meanreversion should be compliant: {result}"

    def test_core_plus_aux_aggro_is_compliant(self, presets_dir, tiering_config_path):
        """core_plus_aux_aggro enthält nur Core und Aux."""
        preset_file = presets_dir / "core_plus_aux_aggro.toml"
        if not preset_file.exists():
            pytest.skip("core_plus_aux_aggro.toml not found")

        recipes = load_portfolio_recipes(preset_file)
        recipe = recipes.get("core_plus_aux_aggro")

        result = validate_preset_tiering_compliance(
            "core_plus_aux_aggro",
            allowed_tiers=["core", "aux"],
            recipe=recipe,
            tiering_config_path=tiering_config_path,
        )

        assert result.is_compliant, f"core_plus_aux_aggro should be compliant: {result}"

    def test_detects_legacy_violation(self, tiering_config_path):
        """Erkennt Legacy-Strategien als Verstoß."""
        from src.experiments.portfolio_recipes import PortfolioRecipe

        # Erstelle ein Fake-Recipe mit Legacy-Strategie
        fake_recipe = PortfolioRecipe(
            key="test_with_legacy",
            id="test_with_legacy",
            portfolio_name="Test With Legacy",
            description="Test",
            strategies=["rsi_reversion", "breakout_donchian"],  # Legacy!
            weights=[0.5, 0.5],
        )

        result = validate_preset_tiering_compliance(
            "test_with_legacy",
            allowed_tiers=["core"],
            recipe=fake_recipe,
            tiering_config_path=tiering_config_path,
        )

        assert not result.is_compliant
        assert "breakout_donchian" in result.violations
        assert result.violation_details["breakout_donchian"] == "legacy"


class TestValidateAllPresetsTiering:
    """Tests für validate_all_presets_tiering."""

    def test_all_presets_pass_validation(self, presets_dir, tiering_config_path):
        """Alle Presets im Verzeichnis bestehen ihre Validierung."""
        if not presets_dir.exists():
            pytest.skip("Presets directory not found")

        results = validate_all_presets_tiering(presets_dir, tiering_config_path)

        for preset_name, result in results.items():
            assert result.is_compliant, f"Preset {preset_name} failed validation: {result}"


# =============================================================================
# TESTS: CORE PRESETS CONTAIN NO LEGACY
# =============================================================================


class TestCorePresetsNoLegacy:
    """Kritischer Test: Core-Presets dürfen keine Legacy-Strategien enthalten."""

    def test_core_balanced_no_legacy(self, presets_dir, tiering_config_path):
        """core_balanced enthält keine Legacy-Strategien."""
        preset_file = presets_dir / "core_balanced.toml"
        if not preset_file.exists():
            pytest.skip("core_balanced.toml not found")

        recipes = load_portfolio_recipes(preset_file)
        recipe = recipes.get("core_balanced")

        legacy_strategies = set(get_strategies_by_tier("legacy", tiering_config_path))
        preset_strategies = set(recipe.strategies or [])

        intersection = legacy_strategies & preset_strategies
        assert len(intersection) == 0, f"Found legacy strategies in core_balanced: {intersection}"

    def test_core_trend_meanreversion_no_legacy(self, presets_dir, tiering_config_path):
        """core_trend_meanreversion enthält keine Legacy-Strategien."""
        preset_file = presets_dir / "core_trend_meanreversion.toml"
        if not preset_file.exists():
            pytest.skip("core_trend_meanreversion.toml not found")

        recipes = load_portfolio_recipes(preset_file)
        recipe = recipes.get("core_trend_meanreversion")

        legacy_strategies = set(get_strategies_by_tier("legacy", tiering_config_path))
        preset_strategies = set(recipe.strategies or [])

        intersection = legacy_strategies & preset_strategies
        assert len(intersection) == 0, f"Found legacy in core_trend_meanreversion: {intersection}"

    def test_core_plus_aux_aggro_no_legacy(self, presets_dir, tiering_config_path):
        """core_plus_aux_aggro enthält keine Legacy-Strategien."""
        preset_file = presets_dir / "core_plus_aux_aggro.toml"
        if not preset_file.exists():
            pytest.skip("core_plus_aux_aggro.toml not found")

        recipes = load_portfolio_recipes(preset_file)
        recipe = recipes.get("core_plus_aux_aggro")

        legacy_strategies = set(get_strategies_by_tier("legacy", tiering_config_path))
        preset_strategies = set(recipe.strategies or [])

        intersection = legacy_strategies & preset_strategies
        assert len(intersection) == 0, f"Found legacy in core_plus_aux_aggro: {intersection}"


# =============================================================================
# TESTS: PRESET LOADING
# =============================================================================


class TestLoadTieredPreset:
    """Tests für load_tiered_preset."""

    def test_load_core_balanced(self, presets_dir, tiering_config_path):
        """core_balanced kann geladen werden."""
        if not (presets_dir / "core_balanced.toml").exists():
            pytest.skip("core_balanced.toml not found")

        recipe = load_tiered_preset(
            "core_balanced",
            presets_dir=presets_dir,
            tiering_config_path=tiering_config_path,
        )

        assert recipe is not None
        assert recipe.id == "core_balanced"
        assert len(recipe.strategies) == 3

    def test_load_nonexistent_raises(self, presets_dir):
        """Nicht existierendes Preset wirft Fehler."""
        with pytest.raises(FileNotFoundError):
            load_tiered_preset("nonexistent_preset", presets_dir=presets_dir)


# =============================================================================
# TESTS: PRESET BUILDERS
# =============================================================================


class TestBuildCoreOnlyPreset:
    """Tests für build_core_only_preset."""

    def test_builds_valid_preset(self, tiering_config_path):
        """Erstellt ein gültiges Core-Only-Preset."""
        recipe = build_core_only_preset(tiering_config_path=tiering_config_path)

        assert recipe is not None
        assert len(recipe.strategies) >= 1
        assert len(recipe.weights) == len(recipe.strategies)

        # Alle Strategien müssen Core sein
        for strat in recipe.strategies:
            tier = get_strategy_tier(strat, tiering_config_path)
            assert tier == "core", f"{strat} should be core, got {tier}"

    def test_weights_sum_to_one(self, tiering_config_path):
        """Gewichte summieren sich zu 1."""
        recipe = build_core_only_preset(tiering_config_path=tiering_config_path)
        assert abs(sum(recipe.weights) - 1.0) < 0.01


class TestBuildCorePlusAuxPreset:
    """Tests für build_core_plus_aux_preset."""

    def test_builds_valid_preset(self, tiering_config_path):
        """Erstellt ein gültiges Core+Aux-Preset."""
        recipe = build_core_plus_aux_preset(tiering_config_path=tiering_config_path)

        assert recipe is not None
        assert len(recipe.strategies) >= 1

        # Alle Strategien müssen Core oder Aux sein
        for strat in recipe.strategies:
            tier = get_strategy_tier(strat, tiering_config_path)
            assert tier in ["core", "aux"], f"{strat} should be core or aux, got {tier}"

    def test_no_legacy_strategies(self, tiering_config_path):
        """Keine Legacy-Strategien im Preset."""
        recipe = build_core_plus_aux_preset(tiering_config_path=tiering_config_path)

        legacy = set(get_strategies_by_tier("legacy", tiering_config_path))
        preset_strategies = set(recipe.strategies)

        intersection = legacy & preset_strategies
        assert len(intersection) == 0, f"Found legacy strategies: {intersection}"

    def test_weights_sum_to_one(self, tiering_config_path):
        """Gewichte summieren sich zu 1."""
        recipe = build_core_plus_aux_preset(tiering_config_path=tiering_config_path)
        assert abs(sum(recipe.weights) - 1.0) < 0.01


# =============================================================================
# TESTS: TIERING CONFIG ROBUSTNESS
# =============================================================================


class TestTieringConfigRobustness:
    """Tests für die Robustheit der Tiering-Config."""

    def test_config_loads_successfully(self, tiering_config_path):
        """Tiering-Config kann geladen werden."""
        config = load_tiering_config(tiering_config_path)
        assert config is not None
        assert len(config) > 0

    def test_all_tiers_are_valid(self, tiering_config):
        """Alle Tiers in der Config sind gültig."""
        for strategy_id, info in tiering_config.items():
            assert info.tier in VALID_TIERS, f"Invalid tier for {strategy_id}: {info.tier}"

    def test_no_duplicate_strategies(self, tiering_config):
        """Keine doppelten Strategy-IDs."""
        strategy_ids = list(tiering_config.keys())
        assert len(strategy_ids) == len(set(strategy_ids))

    def test_core_strategies_have_recommended_config(self, tiering_config):
        """Core-Strategien haben eine empfohlene Config."""
        for strategy_id, info in tiering_config.items():
            if info.tier == "core":
                assert info.recommended_config_id is not None, (
                    f"Core strategy {strategy_id} should have recommended_config_id"
                )


# =============================================================================
# INTEGRATION TESTS
# =============================================================================


class TestTieringIntegration:
    """Integration Tests für das Tiering-System."""

    def test_full_tiering_workflow(self, tiering_config_path, presets_dir):
        """Vollständiger Tiering-Workflow funktioniert."""
        # 1. Tiering laden
        all_tiered = get_all_tiered_strategies(tiering_config_path)
        assert len(all_tiered["core"]) >= 1

        # 2. Core-Preset laden
        if (presets_dir / "core_balanced.toml").exists():
            recipe = load_tiered_preset(
                "core_balanced",
                presets_dir=presets_dir,
                tiering_config_path=tiering_config_path,
            )

            # 3. Validieren
            result = validate_preset_tiering_compliance(
                "core_balanced",
                allowed_tiers=["core"],
                recipe=recipe,
                tiering_config_path=tiering_config_path,
            )

            assert result.is_compliant

    def test_tiering_aware_filtering_is_consistent(self, tiering_config_path):
        """Tiering-Filter sind konsistent."""
        # Core only
        core_only = get_tiering_aware_strategies(
            include_tiers=["core"],
            tiering_config_path=tiering_config_path,
        )

        # Core via get_strategies_by_tier
        core_direct = get_strategies_by_tier("core", tiering_config_path)

        assert set(core_only) == set(core_direct)
