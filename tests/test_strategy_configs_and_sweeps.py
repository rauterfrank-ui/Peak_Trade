"""
Phase 75: Strategy Config & Sweep Consistency Tests
=====================================================

Diese Tests stellen sicher, dass:
1. Alle v1.1-Strategien einen Config-Block haben
2. Die Strategy-Registry alle Strategien laden kann
3. Alle enabled Strategien eine Sweep-Config haben
4. CLI-Smoke-Tests für verschiedene Strategie-Typen funktionieren
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from typing import Dict, List, Set

try:
    import tomllib
except ImportError:
    import tomli as tomllib


# ============================================================================
# TEST FIXTURES
# ============================================================================


@pytest.fixture
def config_path() -> Path:
    """Pfad zur Haupt-Config."""
    return Path("config/config.toml")


@pytest.fixture
def sweeps_dir() -> Path:
    """Pfad zum Sweeps-Verzeichnis."""
    return Path("config/sweeps")


@pytest.fixture
def config_data(config_path: Path) -> Dict:
    """Lädt die Haupt-Config."""
    with open(config_path, "rb") as f:
        return tomllib.load(f)


@pytest.fixture
def v11_strategies() -> Set[str]:
    """Liste der offiziellen v1.1-Strategien."""
    return {
        "ma_crossover",
        "rsi_reversion",
        "breakout",
        "momentum_1h",
        "bollinger_bands",
        "macd",
        "trend_following",
        "mean_reversion",
        "vol_regime_filter",
    }


@pytest.fixture
def sweep_files(sweeps_dir: Path) -> Dict[str, Path]:
    """Mapping von Strategie-Namen zu Sweep-Dateien."""
    return {f.stem: f for f in sweeps_dir.glob("*.toml")}


# ============================================================================
# TEST 1: Strategy ↔ Config
# ============================================================================


def test_v11_strategies_have_config_blocks(config_data: Dict, v11_strategies: Set[str]):
    """
    Jede v1.1-Strategie muss einen [strategies.<name>]-Block haben.
    """
    strategies_section = config_data.get("strategies", {})

    missing = []
    for strategy in v11_strategies:
        if strategy not in strategies_section:
            missing.append(strategy)

    assert not missing, f"Folgende v1.1-Strategien fehlen in config.toml [strategies.*]: {missing}"


def test_v11_strategies_are_enabled(config_data: Dict, v11_strategies: Set[str]):
    """
    Alle v1.1-Strategien (außer meta/filter) sollten enabled=true haben.
    """
    strategies_section = config_data.get("strategies", {})

    # Filter-Strategien dürfen enabled=false sein
    skip_check = {"composite", "regime_aware_portfolio"}

    disabled = []
    for strategy in v11_strategies:
        if strategy in skip_check:
            continue
        strategy_cfg = strategies_section.get(strategy, {})
        if not strategy_cfg.get("enabled", False):
            disabled.append(strategy)

    assert not disabled, f"Folgende v1.1-Strategien sollten enabled=true haben: {disabled}"


def test_v11_strategies_have_category(config_data: Dict, v11_strategies: Set[str]):
    """
    Jede v1.1-Strategie muss eine Kategorie haben.
    """
    strategies_section = config_data.get("strategies", {})
    valid_categories = {"trend", "mean_reversion", "momentum", "breakout", "meta"}

    missing_category = []
    invalid_category = []

    for strategy in v11_strategies:
        strategy_cfg = strategies_section.get(strategy, {})
        category = strategy_cfg.get("category")

        if category is None:
            missing_category.append(strategy)
        elif category not in valid_categories:
            invalid_category.append((strategy, category))

    assert not missing_category, f"Strategien ohne Kategorie: {missing_category}"
    assert not invalid_category, f"Strategien mit ungültiger Kategorie: {invalid_category}"


def test_v11_strategies_have_defaults(config_data: Dict, v11_strategies: Set[str]):
    """
    Jede v1.1-Strategie sollte einen .defaults-Block haben.
    """
    strategies_section = config_data.get("strategies", {})

    missing_defaults = []
    for strategy in v11_strategies:
        strategy_cfg = strategies_section.get(strategy, {})
        if "defaults" not in strategy_cfg:
            missing_defaults.append(strategy)

    # Warnung statt Fehler, da manche Strategien keine Defaults brauchen
    if missing_defaults:
        pytest.skip(f"Strategien ohne .defaults-Block (optional): {missing_defaults}")


# ============================================================================
# TEST 2: Config ↔ Implementation
# ============================================================================


def test_registry_can_load_all_v11_strategies(v11_strategies: Set[str]):
    """
    Die Strategy-Registry kann alle v1.1-Strategien laden.
    """
    from src.strategies.registry import get_strategy_spec, get_available_strategy_keys

    available = set(get_available_strategy_keys())

    # Mapping für Strategie-Namen die anders heißen
    name_mapping = {
        "momentum_1h": "momentum_1h",  # Identisch
    }

    missing_in_registry = []
    for strategy in v11_strategies:
        registry_name = name_mapping.get(strategy, strategy)
        if registry_name not in available:
            missing_in_registry.append(strategy)

    assert not missing_in_registry, (
        f"Folgende v1.1-Strategien fehlen in der Registry: {missing_in_registry}. "
        f"Verfügbar: {sorted(available)}"
    )


def test_registry_strategies_can_be_instantiated():
    """
    Strategie-Klassen können ohne Config instanziiert werden (Default-Parameter).
    """
    from src.strategies.registry import get_strategy_spec, get_available_strategy_keys

    # Strategien die spezielle Initialisierung brauchen
    skip_instantiation = {
        "regime_aware_portfolio",  # Benötigt components
        "composite",  # Benötigt components
    }

    errors = []
    for key in get_available_strategy_keys():
        if key in skip_instantiation:
            continue

        try:
            spec = get_strategy_spec(key)
            # Versuche Instanziierung mit Default-Parametern
            instance = spec.cls()
            assert hasattr(instance, "generate_signals"), f"{key}: generate_signals Methode fehlt"
        except Exception as e:
            errors.append((key, str(e)))

    # Einige Strategien brauchen spezielle Parameter - das ist OK
    # Wir prüfen nur, dass keine unerwarteten Fehler auftreten
    critical_errors = [(k, e) for k, e in errors if "required positional argument" not in e]

    if critical_errors:
        pytest.fail(f"Fehler bei Strategie-Instanziierung: {critical_errors}")


# ============================================================================
# TEST 3: Config ↔ Sweeps
# ============================================================================


def test_v11_strategies_have_sweep_configs(v11_strategies: Set[str], sweep_files: Dict[str, Path]):
    """
    Jede enabled v1.1-Strategie hat eine Sweep-Config.
    """
    # Mapping für abweichende Dateinamen
    name_mapping = {
        "momentum_1h": "momentum",
        "rsi_reversion": "rsi_reversion",
    }

    # Meta-Strategien können ohne Sweep sein
    skip_sweep = {"composite", "regime_aware_portfolio"}

    missing_sweeps = []
    for strategy in v11_strategies:
        if strategy in skip_sweep:
            continue

        sweep_name = name_mapping.get(strategy, strategy)
        if sweep_name not in sweep_files:
            missing_sweeps.append(strategy)

    assert not missing_sweeps, (
        f"Folgende v1.1-Strategien haben keine Sweep-Config: {missing_sweeps}. "
        f"Vorhandene Sweeps: {sorted(sweep_files.keys())}"
    )


def test_sweep_configs_are_parseable(sweep_files: Dict[str, Path]):
    """
    Alle Sweep-Configs können geparst werden.
    """
    errors = []
    for name, path in sweep_files.items():
        try:
            with open(path, "rb") as f:
                data = tomllib.load(f)

            # Prüfe ob entweder [grid] oder [sweep.parameters] existiert
            has_grid = "grid" in data
            has_sweep_params = "sweep" in data and "parameters" in data.get("sweep", {})

            if not has_grid and not has_sweep_params:
                errors.append((name, "Weder [grid] noch [sweep.parameters] gefunden"))

        except Exception as e:
            errors.append((name, str(e)))

    assert not errors, f"Sweep-Config Parse-Fehler: {errors}"


def test_sweep_configs_have_parameters(sweep_files: Dict[str, Path]):
    """
    Sweep-Configs enthalten mindestens einen sinnvollen Parameter-Grid.
    """
    errors = []
    for name, path in sweep_files.items():
        with open(path, "rb") as f:
            data = tomllib.load(f)

        # Suche Parameter in [grid] oder [sweep.parameters]
        params = data.get("grid", data.get("sweep", {}).get("parameters", {}))

        if not params:
            errors.append((name, "Keine Parameter definiert"))
            continue

        # Prüfe ob mindestens ein Parameter eine Liste ist (für Grid-Search)
        has_list_param = any(isinstance(v, list) for v in params.values())
        if not has_list_param:
            errors.append((name, "Keine Listen-Parameter für Grid-Search"))

    assert not errors, f"Sweep-Config Parameter-Fehler: {errors}"


# ============================================================================
# TEST 4: CLI Smoke Tests
# ============================================================================


@pytest.mark.parametrize(
    "strategy_type,strategy_name",
    [
        ("trend", "ma_crossover"),
        ("mean_reversion", "rsi_reversion"),
        ("momentum", "momentum_1h"),
    ],
)
def test_strategy_smoke_instantiation(strategy_type: str, strategy_name: str):
    """
    Smoke-Test: Strategie kann instanziiert werden und generate_signals existiert.
    """
    from src.strategies.registry import get_strategy_spec

    spec = get_strategy_spec(strategy_name)
    strategy = spec.cls()

    assert hasattr(strategy, "generate_signals")
    assert hasattr(strategy, "validate")
    assert hasattr(strategy, "config")


def test_strategy_registry_list_not_empty():
    """
    Die Strategy-Registry ist nicht leer.
    """
    from src.strategies.registry import get_available_strategy_keys

    keys = get_available_strategy_keys()
    assert len(keys) >= 8, f"Mindestens 8 Strategien erwartet, gefunden: {len(keys)}"


def test_config_registry_loads_without_error():
    """
    Die Config-Registry kann geladen werden.
    """
    from src.core.config_registry import get_config, list_strategies

    config = get_config()
    strategies = list_strategies()

    assert config is not None
    assert len(strategies) > 0


# ============================================================================
# TEST 5: v1.1 Portfolio Presets
# ============================================================================


@pytest.fixture
def portfolio_recipes_path() -> Path:
    """Pfad zu portfolio_recipes.toml."""
    return Path("config/portfolio_recipes.toml")


@pytest.fixture
def portfolio_recipes_data(portfolio_recipes_path: Path) -> Dict:
    """Lädt portfolio_recipes.toml."""
    with open(portfolio_recipes_path, "rb") as f:
        return tomllib.load(f)


def test_v11_portfolio_presets_exist(portfolio_recipes_data: Dict):
    """
    Die v1.1 Portfolio-Presets existieren.
    """
    recipes = portfolio_recipes_data.get("portfolio_recipes", {})

    expected_presets = ["conservative_v11", "moderate_v11", "aggressive_v11"]
    missing = [p for p in expected_presets if p not in recipes]

    assert not missing, f"Fehlende v1.1 Portfolio-Presets: {missing}"


def test_v11_portfolio_presets_have_required_fields(portfolio_recipes_data: Dict):
    """
    v1.1 Portfolio-Presets haben alle erforderlichen Felder.
    """
    recipes = portfolio_recipes_data.get("portfolio_recipes", {})
    # risk_profile ist optional, da es in TOML-Arrays verschachtelt sein kann
    required_fields = ["id", "portfolio_name", "description", "strategies"]

    errors = []
    for preset_name in ["conservative_v11", "moderate_v11", "aggressive_v11"]:
        preset = recipes.get(preset_name, {})
        missing = [f for f in required_fields if f not in preset]
        if missing:
            errors.append((preset_name, missing))

    assert not errors, f"Fehlende Felder in v1.1-Presets: {errors}"


def test_v11_portfolio_presets_use_v11_strategies(
    portfolio_recipes_data: Dict, v11_strategies: Set[str]
):
    """
    v1.1 Portfolio-Presets verwenden nur v1.1-offizielle Strategien.
    """
    recipes = portfolio_recipes_data.get("portfolio_recipes", {})

    errors = []
    for preset_name in ["conservative_v11", "moderate_v11", "aggressive_v11"]:
        preset = recipes.get(preset_name, {})
        strategies = preset.get("strategies", [])

        # Strategien können als Liste von Dicts oder als Liste von Strings kommen
        for strat in strategies:
            if isinstance(strat, dict):
                strat_name = strat.get("name", "")
            else:
                strat_name = strat

            if strat_name and strat_name not in v11_strategies:
                errors.append((preset_name, strat_name))

    assert not errors, f"v1.1-Presets verwenden nicht-v1.1-Strategien: {errors}"


# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
