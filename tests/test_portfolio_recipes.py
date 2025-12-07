# tests/test_portfolio_recipes.py
"""
Tests für Portfolio Recipes & Presets
=======================================

Tests für:
- PortfolioRecipe Dataclass
- load_portfolio_recipes
- get_portfolio_recipe
- Validierung
"""
from __future__ import annotations

from pathlib import Path

import pytest

from src.experiments.portfolio_recipes import (
    PortfolioRecipe,
    get_portfolio_recipe,
    load_portfolio_recipes,
)

# =============================================================================
# FIXTURES
# =============================================================================


@pytest.fixture
def sample_recipe_toml(tmp_path: Path) -> Path:
    """Erstellt eine temporäre TOML-Datei mit Sample-Rezepten."""
    toml_content = """
[portfolio_recipes.rsi_reversion_balanced]
id = "rsi_reversion_balanced"
portfolio_name = "RSI Reversion Balanced v1"
description = "3x RSI-Reversion Top-Konfigurationen mit moderaten Gewichten."
sweep_name = "rsi_reversion_basic"
top_n = 3
weights = [0.4, 0.3, 0.3]
run_montecarlo = true
mc_num_runs = 1000
run_stress_tests = true
stress_scenarios = ["single_crash_bar", "vol_spike"]
stress_severity = 0.2
format = "both"
risk_profile = "moderate"
tags = ["rsi", "reversion", "balanced"]

[portfolio_recipes.ma_crossover_equal]
id = "ma_crossover_equal"
portfolio_name = "MA Crossover Equal Weight"
description = "5x MA Crossover mit Equal-Weight."
sweep_name = "ma_crossover_basic"
top_n = 5
weights = [0.2, 0.2, 0.2, 0.2, 0.2]
run_montecarlo = false
run_stress_tests = false
format = "md"
"""
    recipe_file = tmp_path / "portfolio_recipes.toml"
    recipe_file.write_text(toml_content)
    return recipe_file


@pytest.fixture
def invalid_recipe_toml(tmp_path: Path) -> Path:
    """Erstellt eine temporäre TOML-Datei mit ungültigen Rezepten."""
    toml_content = """
[portfolio_recipes.invalid_weights_length]
id = "invalid_weights_length"
portfolio_name = "Invalid Weights Length"
sweep_name = "test_sweep"
top_n = 3
weights = [0.5, 0.5]  # Falsche Länge!

[portfolio_recipes.invalid_mc_config]
id = "invalid_mc_config"
portfolio_name = "Invalid MC Config"
sweep_name = "test_sweep"
top_n = 2
weights = [0.5, 0.5]
run_montecarlo = false
mc_num_runs = 1000  # Sollte nicht gesetzt sein wenn run_montecarlo = false

[portfolio_recipes.invalid_stress_config]
id = "invalid_stress_config"
portfolio_name = "Invalid Stress Config"
sweep_name = "test_sweep"
top_n = 2
weights = [0.5, 0.5]
run_stress_tests = false
stress_scenarios = ["single_crash_bar"]  # Sollte nicht gesetzt sein
"""
    recipe_file = tmp_path / "invalid_recipes.toml"
    recipe_file.write_text(toml_content)
    return recipe_file


# =============================================================================
# DATACLASS TESTS
# =============================================================================


def test_portfolio_recipe_creation():
    """Testet Erstellung einer gültigen PortfolioRecipe."""
    recipe = PortfolioRecipe(
        key="test_recipe",
        id="test_recipe",
        portfolio_name="Test Portfolio",
        description="Test Description",
        sweep_name="test_sweep",
        top_n=3,
        weights=[0.4, 0.3, 0.3],
    )

    assert recipe.key == "test_recipe"
    assert recipe.id == "test_recipe"
    assert recipe.portfolio_name == "Test Portfolio"
    assert recipe.top_n == 3
    assert len(recipe.weights) == 3


def test_portfolio_recipe_validation_success():
    """Testet erfolgreiche Validierung."""
    recipe = PortfolioRecipe(
        key="test",
        id="test",
        portfolio_name="Test",
        description=None,
        sweep_name="test_sweep",
        top_n=3,
        weights=[0.4, 0.3, 0.3],
        run_montecarlo=True,
        mc_num_runs=1000,
        run_stress_tests=True,
        stress_scenarios=["single_crash_bar"],
        stress_severity=0.2,
    )

    # Sollte keine Exception werfen
    recipe.validate()


def test_portfolio_recipe_validation_top_n_zero():
    """Testet Validierung: top_n <= 0."""
    recipe = PortfolioRecipe(
        key="test",
        id="test",
        portfolio_name="Test",
        description=None,
        sweep_name="test_sweep",
        top_n=0,
        weights=[],
    )

    with pytest.raises(ValueError, match="top_n must be > 0"):
        recipe.validate()


def test_portfolio_recipe_validation_weights_length_mismatch():
    """Testet Validierung: weights Länge stimmt nicht mit top_n überein."""
    recipe = PortfolioRecipe(
        key="test",
        id="test",
        portfolio_name="Test",
        description=None,
        sweep_name="test_sweep",
        top_n=3,
        weights=[0.5, 0.5],  # Falsche Länge!
    )

    with pytest.raises(ValueError, match="weights length.*must match top_n"):
        recipe.validate()


def test_portfolio_recipe_validation_negative_weights():
    """Testet Validierung: negative Gewichte."""
    recipe = PortfolioRecipe(
        key="test",
        id="test",
        portfolio_name="Test",
        description=None,
        sweep_name="test_sweep",
        top_n=2,
        weights=[0.5, -0.5],  # Negativ!
    )

    with pytest.raises(ValueError, match="weights must be non-negative"):
        recipe.validate()


def test_portfolio_recipe_validation_mc_num_runs_without_flag():
    """Testet Validierung: mc_num_runs gesetzt, aber run_montecarlo = False."""
    recipe = PortfolioRecipe(
        key="test",
        id="test",
        portfolio_name="Test",
        description=None,
        sweep_name="test_sweep",
        top_n=2,
        weights=[0.5, 0.5],
        run_montecarlo=False,
        mc_num_runs=1000,  # Sollte nicht gesetzt sein
    )

    with pytest.raises(ValueError, match="mc_num_runs is set but run_montecarlo is False"):
        recipe.validate()


def test_portfolio_recipe_validation_stress_without_flag():
    """Testet Validierung: stress_* gesetzt, aber run_stress_tests = False."""
    recipe = PortfolioRecipe(
        key="test",
        id="test",
        portfolio_name="Test",
        description=None,
        sweep_name="test_sweep",
        top_n=2,
        weights=[0.5, 0.5],
        run_stress_tests=False,
        stress_scenarios=["single_crash_bar"],  # Sollte nicht gesetzt sein
    )

    with pytest.raises(ValueError, match="stress_\\* fields are set but run_stress_tests is False"):
        recipe.validate()


def test_portfolio_recipe_validation_invalid_format():
    """Testet Validierung: ungültiges Format."""
    recipe = PortfolioRecipe(
        key="test",
        id="test",
        portfolio_name="Test",
        description=None,
        sweep_name="test_sweep",
        top_n=2,
        weights=[0.5, 0.5],
        format="invalid",  # Ungültig!
    )

    with pytest.raises(ValueError, match="format must be one of"):
        recipe.validate()


def test_portfolio_recipe_validation_invalid_stress_severity():
    """Testet Validierung: stress_severity außerhalb [0, 1]."""
    recipe = PortfolioRecipe(
        key="test",
        id="test",
        portfolio_name="Test",
        description=None,
        sweep_name="test_sweep",
        top_n=2,
        weights=[0.5, 0.5],
        run_stress_tests=True,
        stress_severity=1.5,  # Außerhalb [0, 1]!
    )

    with pytest.raises(ValueError, match="stress_severity must be between 0.0 and 1.0"):
        recipe.validate()


# =============================================================================
# LOADER TESTS
# =============================================================================


def test_load_portfolio_recipes_success(sample_recipe_toml: Path):
    """Testet erfolgreiches Laden von Portfolio-Recipes."""
    recipes = load_portfolio_recipes(sample_recipe_toml)

    assert len(recipes) == 2
    assert "rsi_reversion_balanced" in recipes
    assert "ma_crossover_equal" in recipes

    # Prüfe erstes Rezept
    recipe1 = recipes["rsi_reversion_balanced"]
    assert recipe1.id == "rsi_reversion_balanced"
    assert recipe1.portfolio_name == "RSI Reversion Balanced v1"
    assert recipe1.sweep_name == "rsi_reversion_basic"
    assert recipe1.top_n == 3
    assert recipe1.weights == [0.4, 0.3, 0.3]
    assert recipe1.run_montecarlo is True
    assert recipe1.mc_num_runs == 1000
    assert recipe1.run_stress_tests is True
    assert recipe1.stress_scenarios == ["single_crash_bar", "vol_spike"]
    assert recipe1.stress_severity == 0.2
    assert recipe1.format == "both"
    assert recipe1.risk_profile == "moderate"
    assert "rsi" in recipe1.tags

    # Prüfe zweites Rezept
    recipe2 = recipes["ma_crossover_equal"]
    assert recipe2.id == "ma_crossover_equal"
    assert recipe2.top_n == 5
    assert recipe2.run_montecarlo is False
    assert recipe2.run_stress_tests is False


def test_load_portfolio_recipes_file_not_found(tmp_path: Path):
    """Testet Fehlerbehandlung: Datei nicht gefunden."""
    missing_file = tmp_path / "missing.toml"

    with pytest.raises(FileNotFoundError):
        load_portfolio_recipes(missing_file)


def test_load_portfolio_recipes_invalid_toml(tmp_path: Path):
    """Testet Fehlerbehandlung: ungültige TOML."""
    invalid_file = tmp_path / "invalid.toml"
    invalid_file.write_text("invalid toml content {")

    with pytest.raises(ValueError, match="Error loading portfolio recipes"):
        load_portfolio_recipes(invalid_file)


def test_load_portfolio_recipes_missing_section(tmp_path: Path):
    """Testet Fehlerbehandlung: fehlende portfolio_recipes-Sektion."""
    invalid_file = tmp_path / "no_section.toml"
    invalid_file.write_text("[other_section]\nkey = 'value'")

    recipes = load_portfolio_recipes(invalid_file)
    assert len(recipes) == 0


def test_load_portfolio_recipes_validation_errors(invalid_recipe_toml: Path):
    """Testet, dass Validierungsfehler beim Laden geworfen werden."""
    with pytest.raises(ValueError, match="weights length"):
        load_portfolio_recipes(invalid_recipe_toml)


def test_get_portfolio_recipe_by_key(sample_recipe_toml: Path):
    """Testet get_portfolio_recipe: Zugriff per Tabellen-Key."""
    recipe = get_portfolio_recipe(sample_recipe_toml, "rsi_reversion_balanced")

    assert recipe.key == "rsi_reversion_balanced"
    assert recipe.id == "rsi_reversion_balanced"
    assert recipe.portfolio_name == "RSI Reversion Balanced v1"


def test_get_portfolio_recipe_by_id(sample_recipe_toml: Path):
    """Testet get_portfolio_recipe: Zugriff per Feld 'id'."""
    # id kann von key abweichen (hier nicht, aber testen wir trotzdem)
    recipe = get_portfolio_recipe(sample_recipe_toml, "rsi_reversion_balanced")

    assert recipe.id == "rsi_reversion_balanced"


def test_get_portfolio_recipe_not_found(sample_recipe_toml: Path):
    """Testet Fehlerbehandlung: Rezept nicht gefunden."""
    with pytest.raises(KeyError, match="not found"):
        get_portfolio_recipe(sample_recipe_toml, "nonexistent_recipe")


def test_get_portfolio_recipe_file_not_found(tmp_path: Path):
    """Testet Fehlerbehandlung: Datei nicht gefunden."""
    missing_file = tmp_path / "missing.toml"

    with pytest.raises(FileNotFoundError):
        get_portfolio_recipe(missing_file, "any_recipe")

