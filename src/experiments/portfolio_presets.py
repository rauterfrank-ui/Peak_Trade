# src/experiments/portfolio_presets.py
"""
Peak_Trade Tiered Portfolio Presets (Phase 80)
===============================================

Verknüpft Portfolio-Presets mit dem Tiering-System (core/aux/legacy).

Features:
- Helper-Funktionen zum Filtern von Strategien nach Tier
- Tiering-Validierung für Portfolio-Presets
- Laden von tiered Presets mit automatischer Compliance-Prüfung

Usage:
    from src.experiments.portfolio_presets import (
        get_strategies_by_tier,
        get_tiering_aware_strategies,
        validate_preset_tiering_compliance,
        load_tiered_preset,
    )

    # Alle Core-Strategien holen
    core_strategies = get_strategies_by_tier("core")

    # Core + Aux Strategien holen
    strategies = get_tiering_aware_strategies(include_tiers=["core", "aux"])

    # Preset-Tiering validieren
    result = validate_preset_tiering_compliance("core_balanced", allowed_tiers=["core"])
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path

from src.experiments.portfolio_recipes import (
    PortfolioRecipe,
    load_portfolio_recipes,
)
from src.experiments.strategy_profiles import (
    load_tiering_config,
)

logger = logging.getLogger(__name__)

# =============================================================================
# CONSTANTS
# =============================================================================

DEFAULT_TIERING_CONFIG = Path("config/strategy_tiering.toml")
DEFAULT_PRESETS_DIR = Path("config/portfolio_presets")
DEFAULT_RECIPES_FILE = Path("config/portfolio_recipes.toml")

VALID_TIERS = {"core", "aux", "legacy", "unclassified", "r_and_d"}


# =============================================================================
# DATA MODELS
# =============================================================================


@dataclass
class TieringComplianceResult:
    """
    Ergebnis einer Tiering-Compliance-Prüfung.

    Attributes:
        preset_name: Name des geprüften Presets
        is_compliant: Ob das Preset den Tiering-Anforderungen entspricht
        allowed_tiers: Liste der erlaubten Tiers
        strategies_checked: Liste der geprüften Strategien
        violations: Liste von Strategien, die gegen die Tiering-Regeln verstoßen
        violation_details: Details zu den Verstößen (strategy_id -> tier)
    """

    preset_name: str
    is_compliant: bool
    allowed_tiers: list[str]
    strategies_checked: list[str] = field(default_factory=list)
    violations: list[str] = field(default_factory=list)
    violation_details: dict[str, str] = field(default_factory=dict)

    def __str__(self) -> str:
        status = "✅ COMPLIANT" if self.is_compliant else "❌ NON-COMPLIANT"
        lines = [
            f"Tiering Compliance: {self.preset_name}",
            f"Status: {status}",
            f"Allowed Tiers: {', '.join(self.allowed_tiers)}",
            f"Strategies Checked: {len(self.strategies_checked)}",
        ]
        if self.violations:
            lines.append(f"Violations: {len(self.violations)}")
            for strat in self.violations:
                tier = self.violation_details.get(strat, "unknown")
                lines.append(f"  - {strat}: tier={tier}")
        return "\n".join(lines)


# =============================================================================
# TIERING HELPER FUNCTIONS
# =============================================================================


def get_strategies_by_tier(
    tier: str,
    tiering_config_path: Path = DEFAULT_TIERING_CONFIG,
) -> list[str]:
    """
    Gibt alle Strategien eines bestimmten Tiers zurück.

    Args:
        tier: Tier-Level ("core", "aux", "legacy", "unclassified")
        tiering_config_path: Pfad zur Tiering-Config

    Returns:
        Liste der Strategy-IDs mit diesem Tier

    Example:
        >>> core_strategies = get_strategies_by_tier("core")
        >>> print(core_strategies)
        ['rsi_reversion', 'ma_crossover', 'bollinger_bands']
    """
    if tier not in VALID_TIERS:
        logger.warning(f"Unknown tier: {tier}. Valid tiers: {VALID_TIERS}")
        return []

    tiering = load_tiering_config(tiering_config_path)

    return [
        strategy_id
        for strategy_id, info in tiering.items()
        if info.tier == tier
    ]


def get_tiering_aware_strategies(
    include_tiers: list[str] | None = None,
    exclude_tiers: list[str] | None = None,
    tiering_config_path: Path = DEFAULT_TIERING_CONFIG,
) -> list[str]:
    """
    Gibt Strategien basierend auf Tier-Filtern zurück.

    Args:
        include_tiers: Liste der zu inkludierenden Tiers (default: ["core"])
        exclude_tiers: Liste der zu exkludierenden Tiers (optional)
        tiering_config_path: Pfad zur Tiering-Config

    Returns:
        Liste der Strategy-IDs, die den Filtern entsprechen

    Example:
        >>> # Nur Core-Strategien
        >>> strategies = get_tiering_aware_strategies(include_tiers=["core"])

        >>> # Core + Aux, aber kein Legacy
        >>> strategies = get_tiering_aware_strategies(
        ...     include_tiers=["core", "aux"],
        ...     exclude_tiers=["legacy"]
        ... )
    """
    if include_tiers is None:
        include_tiers = ["core"]

    if exclude_tiers is None:
        exclude_tiers = []

    # Validierung
    for tier in include_tiers + exclude_tiers:
        if tier not in VALID_TIERS:
            logger.warning(f"Unknown tier: {tier}. Valid tiers: {VALID_TIERS}")

    tiering = load_tiering_config(tiering_config_path)

    include_set = set(include_tiers)
    exclude_set = set(exclude_tiers)

    result = [
        strategy_id
        for strategy_id, info in tiering.items()
        if info.tier in include_set and info.tier not in exclude_set
    ]

    logger.debug(
        f"Tiering filter: include={include_tiers}, exclude={exclude_tiers} "
        f"-> {len(result)} strategies"
    )

    return result


def get_all_tiered_strategies(
    tiering_config_path: Path = DEFAULT_TIERING_CONFIG,
) -> dict[str, list[str]]:
    """
    Gibt alle Strategien gruppiert nach Tier zurück.

    Args:
        tiering_config_path: Pfad zur Tiering-Config

    Returns:
        Dict mit tier -> list[strategy_id]

    Example:
        >>> all_tiered = get_all_tiered_strategies()
        >>> print(all_tiered["core"])
        ['rsi_reversion', 'ma_crossover', 'bollinger_bands']
    """
    tiering = load_tiering_config(tiering_config_path)

    result: dict[str, list[str]] = {
        "core": [],
        "aux": [],
        "legacy": [],
        "unclassified": [],
    }

    for strategy_id, info in tiering.items():
        tier = info.tier if info.tier in result else "unclassified"
        result[tier].append(strategy_id)

    return result


def get_strategy_tier(
    strategy_id: str,
    tiering_config_path: Path = DEFAULT_TIERING_CONFIG,
) -> str:
    """
    Gibt das Tier einer einzelnen Strategie zurück.

    Args:
        strategy_id: Strategy-ID
        tiering_config_path: Pfad zur Tiering-Config

    Returns:
        Tier-String ("core", "aux", "legacy", "unclassified")
    """
    tiering = load_tiering_config(tiering_config_path)
    info = tiering.get(strategy_id)
    return info.tier if info else "unclassified"


# =============================================================================
# PRESET VALIDATION
# =============================================================================


def validate_preset_tiering_compliance(
    preset_name: str,
    allowed_tiers: list[str],
    recipe: PortfolioRecipe | None = None,
    recipes_path: Path = DEFAULT_RECIPES_FILE,
    tiering_config_path: Path = DEFAULT_TIERING_CONFIG,
) -> TieringComplianceResult:
    """
    Validiert, ob ein Portfolio-Preset nur Strategien aus erlaubten Tiers enthält.

    Args:
        preset_name: Name des Presets
        allowed_tiers: Liste der erlaubten Tiers
        recipe: Optionales PortfolioRecipe-Objekt (wenn bereits geladen)
        recipes_path: Pfad zur Portfolio-Recipes-Datei
        tiering_config_path: Pfad zur Tiering-Config

    Returns:
        TieringComplianceResult mit Details zur Validierung

    Example:
        >>> result = validate_preset_tiering_compliance(
        ...     "core_balanced",
        ...     allowed_tiers=["core"]
        ... )
        >>> print(result.is_compliant)
        True
    """
    # Recipe laden falls nicht übergeben
    if recipe is None:
        try:
            recipes = load_portfolio_recipes(recipes_path)
            recipe = recipes.get(preset_name)
            if recipe is None:
                # Suche nach ID
                for r in recipes.values():
                    if r.id == preset_name:
                        recipe = r
                        break
        except Exception as e:
            logger.error(f"Could not load recipe {preset_name}: {e}")
            return TieringComplianceResult(
                preset_name=preset_name,
                is_compliant=False,
                allowed_tiers=allowed_tiers,
                violations=[f"Could not load recipe: {e}"],
            )

    if recipe is None:
        return TieringComplianceResult(
            preset_name=preset_name,
            is_compliant=False,
            allowed_tiers=allowed_tiers,
            violations=[f"Recipe '{preset_name}' not found"],
        )

    # Strategien aus dem Recipe extrahieren
    strategies = recipe.strategies or []

    # Tiering laden
    tiering = load_tiering_config(tiering_config_path)

    # Validierung
    violations: list[str] = []
    violation_details: dict[str, str] = {}
    allowed_set = set(allowed_tiers)

    for strategy_id in strategies:
        info = tiering.get(strategy_id)
        tier = info.tier if info else "unclassified"

        if tier not in allowed_set:
            violations.append(strategy_id)
            violation_details[strategy_id] = tier

    result = TieringComplianceResult(
        preset_name=preset_name,
        is_compliant=len(violations) == 0,
        allowed_tiers=allowed_tiers,
        strategies_checked=strategies,
        violations=violations,
        violation_details=violation_details,
    )

    if violations:
        logger.warning(f"Tiering compliance check failed for {preset_name}: {result}")
    else:
        logger.debug(f"Tiering compliance check passed for {preset_name}")

    return result


def validate_all_presets_tiering(
    presets_dir: Path = DEFAULT_PRESETS_DIR,
    tiering_config_path: Path = DEFAULT_TIERING_CONFIG,
) -> dict[str, TieringComplianceResult]:
    """
    Validiert alle Presets in einem Verzeichnis gegen ihre erwarteten Tiering-Regeln.

    Presets werden basierend auf ihrem Namen klassifiziert:
    - "core_*" -> nur core erlaubt
    - "core_aux_*" oder "core_plus_aux_*" -> core + aux erlaubt
    - andere -> alle Tiers erlaubt (außer legacy)

    Args:
        presets_dir: Verzeichnis mit Preset-TOML-Dateien
        tiering_config_path: Pfad zur Tiering-Config

    Returns:
        Dict mit preset_name -> TieringComplianceResult
    """
    results: dict[str, TieringComplianceResult] = {}

    if not presets_dir.exists():
        logger.warning(f"Presets directory not found: {presets_dir}")
        return results

    for preset_file in presets_dir.glob("*.toml"):
        preset_name = preset_file.stem

        # Bestimme erlaubte Tiers basierend auf Preset-Name
        if preset_name.startswith("core_plus_aux") or preset_name.startswith("core_aux"):
            allowed_tiers = ["core", "aux"]
        elif preset_name.startswith("core_"):
            allowed_tiers = ["core"]
        else:
            # Default: core + aux (kein legacy)
            allowed_tiers = ["core", "aux"]

        try:
            recipes = load_portfolio_recipes(preset_file)
            for recipe_key, recipe in recipes.items():
                result = validate_preset_tiering_compliance(
                    recipe_key,
                    allowed_tiers=allowed_tiers,
                    recipe=recipe,
                    tiering_config_path=tiering_config_path,
                )
                results[recipe_key] = result
        except Exception as e:
            logger.error(f"Error validating preset {preset_name}: {e}")
            results[preset_name] = TieringComplianceResult(
                preset_name=preset_name,
                is_compliant=False,
                allowed_tiers=allowed_tiers,
                violations=[str(e)],
            )

    return results


# =============================================================================
# PRESET LOADING WITH TIERING
# =============================================================================


def load_tiered_preset(
    preset_name: str,
    presets_dir: Path = DEFAULT_PRESETS_DIR,
    enforce_compliance: bool = True,
    tiering_config_path: Path = DEFAULT_TIERING_CONFIG,
) -> PortfolioRecipe:
    """
    Lädt ein Portfolio-Preset mit Tiering-Validierung.

    Args:
        preset_name: Name des Presets (ohne .toml)
        presets_dir: Verzeichnis mit Preset-Dateien
        enforce_compliance: Ob Tiering-Verstöße einen Fehler auslösen sollen
        tiering_config_path: Pfad zur Tiering-Config

    Returns:
        PortfolioRecipe-Objekt

    Raises:
        FileNotFoundError: Wenn das Preset nicht gefunden wird
        ValueError: Wenn enforce_compliance=True und Tiering-Verstöße vorliegen

    Example:
        >>> recipe = load_tiered_preset("core_balanced")
        >>> print(recipe.strategies)
        ['rsi_reversion', 'ma_crossover', 'bollinger_bands']
    """
    preset_file = presets_dir / f"{preset_name}.toml"

    if not preset_file.exists():
        raise FileNotFoundError(f"Preset file not found: {preset_file}")

    recipes = load_portfolio_recipes(preset_file)

    # Das erste Recipe aus der Datei verwenden (oder nach Name suchen)
    recipe = None
    if preset_name in recipes:
        recipe = recipes[preset_name]
    else:
        # Erstes Recipe nehmen
        recipe = next(iter(recipes.values()), None)

    if recipe is None:
        raise ValueError(f"No recipe found in preset file: {preset_file}")

    # Tiering-Compliance prüfen
    if preset_name.startswith("core_plus_aux") or preset_name.startswith("core_aux"):
        allowed_tiers = ["core", "aux"]
    elif preset_name.startswith("core_"):
        allowed_tiers = ["core"]
    else:
        allowed_tiers = ["core", "aux"]

    compliance = validate_preset_tiering_compliance(
        preset_name,
        allowed_tiers=allowed_tiers,
        recipe=recipe,
        tiering_config_path=tiering_config_path,
    )

    if not compliance.is_compliant:
        msg = f"Tiering compliance check failed for {preset_name}:\n{compliance}"
        if enforce_compliance:
            raise ValueError(msg)
        else:
            logger.warning(msg)

    return recipe


# =============================================================================
# PRESET BUILDERS
# =============================================================================


def build_core_only_preset(
    name: str = "core_only",
    description: str = "Portfolio mit nur Core-Strategien",
    weights: list[float] | None = None,
    tiering_config_path: Path = DEFAULT_TIERING_CONFIG,
) -> PortfolioRecipe:
    """
    Erstellt ein Preset mit nur Core-Strategien.

    Args:
        name: Name des Presets
        description: Beschreibung
        weights: Optionale Gewichtungen (default: gleichverteilt)
        tiering_config_path: Pfad zur Tiering-Config

    Returns:
        PortfolioRecipe-Objekt
    """
    strategies = get_strategies_by_tier("core", tiering_config_path)

    if not strategies:
        raise ValueError("No core strategies found in tiering config")

    if weights is None:
        # Gleichverteilung
        weights = [1.0 / len(strategies)] * len(strategies)

    if len(weights) != len(strategies):
        raise ValueError(
            f"weights length ({len(weights)}) must match strategies count ({len(strategies)})"
        )

    return PortfolioRecipe(
        key=name,
        id=name,
        portfolio_name=name,
        description=description,
        strategies=strategies,
        weights=weights,
        run_montecarlo=True,
        mc_num_runs=100,
        run_stress_tests=True,
        stress_scenarios=["flash_crash", "high_volatility"],
        stress_severity=0.5,
        format="both",
        risk_profile="moderate",
        tags=["core", "tiered", "phase80"],
    )


def build_core_plus_aux_preset(
    name: str = "core_plus_aux",
    description: str = "Portfolio mit Core- und Aux-Strategien",
    core_weight: float = 0.6,
    aux_weight: float = 0.4,
    tiering_config_path: Path = DEFAULT_TIERING_CONFIG,
) -> PortfolioRecipe:
    """
    Erstellt ein Preset mit Core- und Aux-Strategien.

    Args:
        name: Name des Presets
        description: Beschreibung
        core_weight: Gesamtgewicht für Core-Strategien (0.0-1.0)
        aux_weight: Gesamtgewicht für Aux-Strategien (0.0-1.0)
        tiering_config_path: Pfad zur Tiering-Config

    Returns:
        PortfolioRecipe-Objekt
    """
    core_strategies = get_strategies_by_tier("core", tiering_config_path)
    aux_strategies = get_strategies_by_tier("aux", tiering_config_path)

    if not core_strategies:
        raise ValueError("No core strategies found in tiering config")

    strategies = core_strategies + aux_strategies

    # Gewichte berechnen
    weights = []

    # Core-Strategien: gleichverteilt innerhalb core_weight
    if core_strategies:
        core_individual = core_weight / len(core_strategies)
        weights.extend([core_individual] * len(core_strategies))

    # Aux-Strategien: gleichverteilt innerhalb aux_weight
    if aux_strategies:
        aux_individual = aux_weight / len(aux_strategies)
        weights.extend([aux_individual] * len(aux_strategies))

    return PortfolioRecipe(
        key=name,
        id=name,
        portfolio_name=name,
        description=description,
        strategies=strategies,
        weights=weights,
        run_montecarlo=True,
        mc_num_runs=100,
        run_stress_tests=True,
        stress_scenarios=["flash_crash", "high_volatility", "trend_reversal"],
        stress_severity=0.6,
        format="both",
        risk_profile="aggressive",
        tags=["core", "aux", "tiered", "phase80"],
    )


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    "DEFAULT_PRESETS_DIR",
    # Constants
    "DEFAULT_TIERING_CONFIG",
    "VALID_TIERS",
    # Data Models
    "TieringComplianceResult",
    # Builders
    "build_core_only_preset",
    "build_core_plus_aux_preset",
    "get_all_tiered_strategies",
    # Tiering Helpers
    "get_strategies_by_tier",
    "get_strategy_tier",
    "get_tiering_aware_strategies",
    # Loading
    "load_tiered_preset",
    "validate_all_presets_tiering",
    # Validation
    "validate_preset_tiering_compliance",
]
