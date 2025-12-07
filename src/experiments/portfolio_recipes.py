# src/experiments/portfolio_recipes.py
"""
Peak_Trade Portfolio Recipes & Presets
=======================================

Lädt und validiert vordefinierte Portfolio-Konfigurationen aus TOML-Dateien.

Usage:
    from src.experiments.portfolio_recipes import (
        load_portfolio_recipes,
        get_portfolio_recipe,
        PortfolioRecipe,
    )

    # Alle Rezepte laden
    recipes = load_portfolio_recipes(Path("config/portfolio_recipes.toml"))

    # Einzelnes Rezept laden
    recipe = get_portfolio_recipe(Path("config/portfolio_recipes.toml"), "rsi_reversion_balanced")
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path

try:
    # Python 3.11+
    import tomllib  # type: ignore[attr-defined]
except ModuleNotFoundError:  # pragma: no cover
    # Für Python 3.9/3.10: pip install tomli
    import tomli as tomllib  # type: ignore[assignment]

logger = logging.getLogger(__name__)


@dataclass
class PortfolioRecipe:
    """
    Ein Portfolio-Rezept (Preset) aus der TOML-Konfiguration.

    Attributes:
        key: Tabellen-Key in TOML (z.B. "rsi_reversion_balanced")
        id: ID des Rezepts (kann identisch zu key sein)
        portfolio_name: Name des Portfolios (für Reports)
        description: Kurze Beschreibung
        sweep_name: Name des Sweeps als Basis
        top_n: Anzahl Top-Konfigurationen
        weights: Liste von Gewichten (Länge = top_n)
        run_montecarlo: Ob Monte-Carlo ausgeführt werden soll
        mc_num_runs: Anzahl Monte-Carlo-Runs
        run_stress_tests: Ob Stress-Tests ausgeführt werden sollen
        stress_scenarios: Liste von Stress-Szenarien
        stress_severity: Severity für Stress-Tests
        format: Output-Format ("md", "html", "both")
        risk_profile: Informatives Risiko-Profil (optional)
        tags: Liste von Tags (optional)
    """

    key: str
    id: str
    portfolio_name: str
    description: str | None
    sweep_name: str
    top_n: int
    weights: list[float]

    run_montecarlo: bool = False
    mc_num_runs: int | None = None

    run_stress_tests: bool = False
    stress_scenarios: list[str] = field(default_factory=list)
    stress_severity: float | None = None

    format: str = "both"

    risk_profile: str | None = None
    tags: list[str] = field(default_factory=list)

    def validate(self) -> None:
        """
        Validiert das Rezept.

        Raises:
            ValueError: Bei Validierungsfehlern
        """
        # 1) top_n / weights Länge
        if self.top_n <= 0:
            raise ValueError(f"top_n must be > 0 for recipe {self.id!r}")

        if len(self.weights) != self.top_n:
            raise ValueError(
                f"weights length ({len(self.weights)}) must match top_n ({self.top_n}) "
                f"for recipe {self.id!r}"
            )

        # 2) Gewichte sollten sinnvoll sein (nicht negativ, Summe sollte ~1.0 sein)
        if any(w < 0 for w in self.weights):
            raise ValueError(f"weights must be non-negative for recipe {self.id!r}")

        weight_sum = sum(self.weights)
        if abs(weight_sum - 1.0) > 0.01:  # Toleranz für Rundungsfehler
            logger.warning(
                f"weights sum to {weight_sum:.3f} (expected ~1.0) for recipe {self.id!r}"
            )

        # 3) einfache Checks MC / Stress
        if not self.run_montecarlo and self.mc_num_runs is not None:
            raise ValueError(
                f"mc_num_runs is set but run_montecarlo is False for recipe {self.id!r}"
            )

        if not self.run_stress_tests and (
            self.stress_scenarios or self.stress_severity is not None
        ):
            raise ValueError(
                f"stress_* fields are set but run_stress_tests is False for recipe {self.id!r}"
            )

        # 4) Format-Validierung
        if self.format not in ["md", "html", "both"]:
            raise ValueError(
                f"format must be one of 'md', 'html', 'both', got {self.format!r} "
                f"for recipe {self.id!r}"
            )

        # 5) stress_severity sollte zwischen 0 und 1 sein
        if self.stress_severity is not None:
            if not (0.0 <= self.stress_severity <= 1.0):
                raise ValueError(
                    f"stress_severity must be between 0.0 and 1.0, got {self.stress_severity} "
                    f"for recipe {self.id!r}"
                )


def load_portfolio_recipes(path: Path) -> dict[str, PortfolioRecipe]:
    """
    Lädt alle Portfolio-Recipes aus der angegebenen TOML-Datei.

    Args:
        path: Pfad zur TOML-Datei

    Returns:
        Dict {recipe_key -> PortfolioRecipe}

    Raises:
        FileNotFoundError: Wenn die Datei nicht existiert
        ValueError: Bei Validierungsfehlern
    """
    if not path.exists():
        raise FileNotFoundError(f"Portfolio recipes file not found: {path}")

    try:
        with open(path, "rb") as f:
            data = tomllib.load(f)
    except Exception as e:
        raise ValueError(f"Error loading portfolio recipes from {path}: {e}") from e

    recipes_section = data.get("portfolio_recipes", {})
    if not isinstance(recipes_section, dict):
        raise ValueError(
            f"Expected 'portfolio_recipes' to be a table in {path}, got {type(recipes_section)}"
        )

    recipes: dict[str, PortfolioRecipe] = {}

    for recipe_key, recipe_data in recipes_section.items():
        if not isinstance(recipe_data, dict):
            logger.warning(f"Skipping invalid recipe entry {recipe_key!r} (not a table)")
            continue

        # ID aus recipe_data oder default auf key
        recipe_id = recipe_data.get("id", recipe_key)

        # Erstelle PortfolioRecipe
        try:
            recipe = PortfolioRecipe(
                key=recipe_key,
                id=recipe_id,
                portfolio_name=recipe_data.get("portfolio_name", recipe_id),
                description=recipe_data.get("description"),
                sweep_name=recipe_data.get("sweep_name", ""),
                top_n=recipe_data.get("top_n", 3),
                weights=recipe_data.get("weights", []),
                run_montecarlo=recipe_data.get("run_montecarlo", False),
                mc_num_runs=recipe_data.get("mc_num_runs"),
                run_stress_tests=recipe_data.get("run_stress_tests", False),
                stress_scenarios=recipe_data.get("stress_scenarios", []),
                stress_severity=recipe_data.get("stress_severity"),
                format=recipe_data.get("format", "both"),
                risk_profile=recipe_data.get("risk_profile"),
                tags=recipe_data.get("tags", []),
            )

            # Validiere
            recipe.validate()

            recipes[recipe_key] = recipe
            logger.debug(f"Loaded recipe: {recipe_key} -> {recipe.portfolio_name}")

        except Exception as e:
            logger.error(f"Error loading recipe {recipe_key!r}: {e}")
            raise

    logger.info(f"Loaded {len(recipes)} portfolio recipe(s) from {path}")
    return recipes


def get_portfolio_recipe(path: Path, recipe_id: str) -> PortfolioRecipe:
    """
    Lädt eine einzelne Recipe-Definition aus der Datei.

    Args:
        path: Pfad zur TOML-Datei
        recipe_id: Recipe-ID (kann sowohl Tabellen-Key als auch Feld 'id' sein)

    Returns:
        PortfolioRecipe

    Raises:
        KeyError: Wenn das Rezept nicht gefunden wird
        FileNotFoundError: Wenn die Datei nicht existiert
        ValueError: Bei Validierungsfehlern
    """
    recipes = load_portfolio_recipes(path)

    # Suche nach recipe_id im Key
    if recipe_id in recipes:
        return recipes[recipe_id]

    # Suche nach recipe_id im Feld 'id'
    for recipe in recipes.values():
        if recipe.id == recipe_id:
            return recipe

    # Nicht gefunden
    available = list(recipes.keys())
    raise KeyError(
        f"Portfolio recipe '{recipe_id}' not found in {path}. "
        f"Available recipes: {', '.join(available)}"
    )

