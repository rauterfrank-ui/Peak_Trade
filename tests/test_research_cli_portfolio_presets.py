# tests/test_research_cli_portfolio_presets.py
"""
Tests für Portfolio-Preset-Integration in run_portfolio_robustness.py
======================================================================

Testet die Merge-Logik: Preset + CLI-Argumente
"""

from __future__ import annotations

import argparse

# Importiere run_portfolio_robustness
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import scripts.run_portfolio_robustness as portfolio_script

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
"""
    recipe_file = tmp_path / "portfolio_recipes.toml"
    recipe_file.write_text(toml_content)
    return recipe_file


@pytest.fixture
def mock_args_with_preset(sample_recipe_toml: Path) -> argparse.Namespace:
    """Erstellt Mock-Args mit Preset."""
    return argparse.Namespace(
        portfolio_preset="rsi_reversion_balanced",
        recipes_config=str(sample_recipe_toml),
        sweep_name=None,
        config="config/config.toml",
        top_n=None,
        portfolio_name=None,
        weights=None,
        run_montecarlo=False,
        mc_num_runs=1000,
        mc_method="simple",
        mc_block_size=20,
        mc_seed=42,
        run_stress_tests=False,
        stress_scenarios=["single_crash_bar", "vol_spike"],
        stress_severity=0.2,
        stress_window=5,
        stress_position="middle",
        stress_seed=42,
        output_dir=None,
        format=None,
        use_dummy_data=True,
        dummy_bars=500,
        verbose=False,
    )


@pytest.fixture
def mock_args_with_preset_and_overrides(sample_recipe_toml: Path) -> argparse.Namespace:
    """Erstellt Mock-Args mit Preset + Overrides."""
    return argparse.Namespace(
        portfolio_preset="rsi_reversion_balanced",
        recipes_config=str(sample_recipe_toml),
        sweep_name="rsi_reversion_basic",  # Override
        config="config/config.toml",
        top_n=5,  # Override
        portfolio_name="custom_portfolio",  # Override
        weights=[0.2, 0.2, 0.2, 0.2, 0.2],  # Override
        run_montecarlo=True,
        mc_num_runs=2000,  # Override
        mc_method="simple",
        mc_block_size=20,
        mc_seed=42,
        run_stress_tests=True,
        stress_scenarios=["single_crash_bar"],  # Override
        stress_severity=0.3,  # Override
        stress_window=5,
        stress_position="middle",
        stress_seed=42,
        output_dir=None,
        format="md",  # Override
        use_dummy_data=True,
        dummy_bars=500,
        verbose=False,
    )


# =============================================================================
# TESTS
# =============================================================================


@patch("scripts.run_portfolio_robustness.load_top_n_configs_for_sweep")
@patch("scripts.run_portfolio_robustness.run_portfolio_robustness")
@patch("scripts.run_portfolio_robustness.build_portfolio_robustness_report")
def test_run_from_args_with_preset(
    mock_report,
    mock_run_robustness,
    mock_load_topn,
    mock_args_with_preset,
    sample_recipe_toml: Path,
):
    """Testet run_from_args mit Preset: Preset-Werte werden geladen."""
    # Mock Setup
    mock_load_topn.return_value = [
        {"config_id": "config_1", "rank": 1},
        {"config_id": "config_2", "rank": 2},
        {"config_id": "config_3", "rank": 3},
    ]
    mock_run_robustness.return_value = MagicMock()
    mock_report.return_value = {"md": Path("test.md"), "html": Path("test.html")}

    # Führe aus
    exit_code = portfolio_script.run_from_args(mock_args_with_preset)

    # Prüfe dass Preset-Werte verwendet wurden
    assert exit_code == 0
    assert mock_load_topn.called
    call_kwargs = mock_load_topn.call_args[1]
    assert call_kwargs["sweep_name"] == "rsi_reversion_basic"  # Aus Preset
    assert call_kwargs["n"] == 3  # Aus Preset

    # Prüfe dass run_portfolio_robustness mit richtigen Parametern aufgerufen wurde
    assert mock_run_robustness.called
    config = mock_run_robustness.call_args[0][0]
    assert config.portfolio.name == "RSI Reversion Balanced v1"  # Aus Preset
    assert config.num_mc_runs == 1000  # Aus Preset
    assert config.run_stress_tests is True  # Aus Preset


@patch("scripts.run_portfolio_robustness.load_top_n_configs_for_sweep")
@patch("scripts.run_portfolio_robustness.run_portfolio_robustness")
@patch("scripts.run_portfolio_robustness.build_portfolio_robustness_report")
def test_run_from_args_with_preset_and_overrides(
    mock_report,
    mock_run_robustness,
    mock_load_topn,
    mock_args_with_preset_and_overrides,
    sample_recipe_toml: Path,
):
    """Testet run_from_args mit Preset + Overrides: CLI-Argumente überschreiben Preset."""
    # Mock Setup
    mock_load_topn.return_value = [
        {"config_id": f"config_{i + 1}", "rank": i + 1} for i in range(5)
    ]
    mock_run_robustness.return_value = MagicMock()
    mock_report.return_value = {"md": Path("test.md")}

    # Führe aus
    exit_code = portfolio_script.run_from_args(mock_args_with_preset_and_overrides)

    # Prüfe dass Overrides verwendet wurden
    assert exit_code == 0
    assert mock_load_topn.called
    call_kwargs = mock_load_topn.call_args[1]
    assert call_kwargs["n"] == 5  # Override, nicht Preset (3)

    # Prüfe dass run_portfolio_robustness mit Override-Parametern aufgerufen wurde
    assert mock_run_robustness.called
    config = mock_run_robustness.call_args[0][0]
    assert config.portfolio.name == "custom_portfolio"  # Override, nicht Preset
    assert config.num_mc_runs == 2000  # Override, nicht Preset (1000)
    assert config.stress_severity == 0.3  # Override, nicht Preset (0.2)

    # Prüfe dass Report mit Override-Format erstellt wurde
    assert mock_report.called
    report_format = mock_report.call_args[1]["format"]
    assert report_format == "md"  # Override, nicht Preset ("both")


@patch("scripts.run_portfolio_robustness.get_portfolio_recipe")
def test_run_from_args_preset_not_found(mock_get_recipe, mock_args_with_preset):
    """Testet Fehlerbehandlung: Preset nicht gefunden."""
    mock_get_recipe.side_effect = KeyError("Recipe not found")

    exit_code = portfolio_script.run_from_args(mock_args_with_preset)

    assert exit_code == 1


def test_build_parser_has_preset_args():
    """Testet dass build_parser --portfolio-preset und --recipes-config enthält."""
    parser = portfolio_script.build_parser()

    # Parse mit Preset
    args = parser.parse_args(
        [
            "--portfolio-preset",
            "test_preset",
            "--recipes-config",
            "custom_recipes.toml",
            "--sweep-name",
            "test_sweep",
            "--config",
            "config/config.toml",
            "--portfolio-name",
            "test_portfolio",
        ]
    )

    assert args.portfolio_preset == "test_preset"
    assert args.recipes_config == "custom_recipes.toml"


# =============================================================================
# PHASE 53: TESTS FÜR NEUE RECIPES MIT DIREKTEN STRATEGIENAMEN
# =============================================================================


@pytest.fixture
def phase53_recipe_toml(tmp_path: Path) -> Path:
    """Erstellt eine temporäre TOML-Datei mit Phase-53-Rezepten (direkte Strategienamen)."""
    toml_content = """
[portfolio_recipes.rsi_reversion_conservative]
id = "rsi_reversion_conservative"
portfolio_name = "RSI Reversion Conservative"
description = "Konservatives RSI-Reversion-Portfolio"
strategies = ["rsi_reversion_btc_conservative", "rsi_reversion_eth_conservative"]
weights = [0.6, 0.4]
run_montecarlo = true
mc_num_runs = 2000
run_stress_tests = true
stress_scenarios = ["single_crash_bar", "vol_spike"]
stress_severity = 0.2
format = "both"
risk_profile = "conservative"
tags = ["rsi", "reversion", "conservative"]

[portfolio_recipes.multi_style_moderate]
id = "multi_style_moderate"
portfolio_name = "Multi-Style Moderate"
description = "Mixed-Style Portfolio"
strategies = [
  "rsi_reversion_btc_moderate",
  "rsi_reversion_eth_moderate",
  "ma_trend_btc_moderate",
  "trend_following_eth_moderate",
]
weights = [0.25, 0.25, 0.25, 0.25]
run_montecarlo = true
mc_num_runs = 3000
run_stress_tests = true
stress_scenarios = ["single_crash_bar", "vol_spike"]
stress_severity = 0.25
format = "both"
risk_profile = "moderate"
tags = ["multi-style", "moderate"]
"""
    recipe_file = tmp_path / "phase53_recipes.toml"
    recipe_file.write_text(toml_content)
    return recipe_file


@pytest.fixture
def mock_args_phase53_preset(phase53_recipe_toml: Path) -> argparse.Namespace:
    """Erstellt Mock-Args mit Phase-53-Preset (direkte Strategienamen)."""
    return argparse.Namespace(
        portfolio_preset="rsi_reversion_conservative",
        recipes_config=str(phase53_recipe_toml),
        sweep_name=None,
        config="config/config.toml",
        top_n=None,
        portfolio_name=None,
        weights=None,
        run_montecarlo=False,
        mc_num_runs=1000,
        mc_method="simple",
        mc_block_size=20,
        mc_seed=42,
        run_stress_tests=False,
        stress_scenarios=["single_crash_bar", "vol_spike"],
        stress_severity=0.2,
        stress_window=5,
        stress_position="middle",
        stress_seed=42,
        output_dir=None,
        format=None,
        use_dummy_data=True,
        dummy_bars=500,
        verbose=False,
    )


def test_phase53_recipe_loading(phase53_recipe_toml: Path):
    """Testet, dass Phase-53-Rezepte mit direkten Strategienamen geladen werden können."""
    from src.experiments.portfolio_recipes import load_portfolio_recipes

    recipes = load_portfolio_recipes(phase53_recipe_toml)

    assert len(recipes) == 2
    assert "rsi_reversion_conservative" in recipes
    assert "multi_style_moderate" in recipes

    # Prüfe erstes Rezept
    recipe1 = recipes["rsi_reversion_conservative"]
    assert recipe1.strategies is not None
    assert len(recipe1.strategies) == 2
    assert recipe1.strategies == [
        "rsi_reversion_btc_conservative",
        "rsi_reversion_eth_conservative",
    ]
    assert recipe1.weights == [0.6, 0.4]
    assert recipe1.risk_profile == "conservative"

    # Prüfe zweites Rezept
    recipe2 = recipes["multi_style_moderate"]
    assert recipe2.strategies is not None
    assert len(recipe2.strategies) == 4
    assert recipe2.risk_profile == "moderate"


@patch("scripts.run_portfolio_robustness.load_top_n_configs_for_sweep")
@patch("scripts.run_portfolio_robustness.run_portfolio_robustness")
@patch("scripts.run_portfolio_robustness.build_portfolio_robustness_report")
def test_phase53_preset_smoke_test(
    mock_report,
    mock_run_robustness,
    mock_load_topn,
    mock_args_phase53_preset,
    phase53_recipe_toml: Path,
):
    """Smoke-Test: Phase-53-Preset kann geladen werden (auch wenn run_from_args später angepasst werden muss)."""
    from src.experiments.portfolio_recipes import get_portfolio_recipe

    # Teste dass Rezept geladen werden kann
    recipe = get_portfolio_recipe(phase53_recipe_toml, "rsi_reversion_conservative")

    assert recipe.portfolio_name == "RSI Reversion Conservative"
    assert recipe.strategies is not None
    assert len(recipe.strategies) == 2
    assert recipe.risk_profile == "conservative"
    assert "conservative" in recipe.description.lower() or recipe.risk_profile == "conservative"


def test_phase53_all_new_recipes_exist():
    """Testet, dass alle neuen Phase-53-Rezepte in der Haupt-Config-Datei existieren."""
    from pathlib import Path
    from src.experiments.portfolio_recipes import load_portfolio_recipes

    recipes_path = Path("config/portfolio_recipes.toml")
    if not recipes_path.exists():
        pytest.skip("config/portfolio_recipes.toml nicht gefunden")

    recipes = load_portfolio_recipes(recipes_path)

    # Prüfe dass alle neuen Rezepte vorhanden sind
    expected_recipes = [
        "rsi_reversion_conservative",
        "rsi_reversion_moderate",
        "rsi_reversion_aggressive",
        "multi_style_moderate",
        "multi_style_aggressive",
    ]

    for recipe_key in expected_recipes:
        assert recipe_key in recipes, f"Rezept {recipe_key} nicht gefunden"
        recipe = recipes[recipe_key]
        assert recipe.strategies is not None, f"Rezept {recipe_key} hat keine strategies"
        assert len(recipe.strategies) == len(recipe.weights), (
            f"Rezept {recipe_key}: weights Länge stimmt nicht"
        )
        assert recipe.risk_profile in ["conservative", "moderate", "aggressive"], (
            f"Rezept {recipe_key}: ungültiges risk_profile"
        )
