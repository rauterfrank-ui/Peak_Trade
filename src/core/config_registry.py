"""
Peak_Trade Config Registry (Standalone)
========================================
Strategien-Registry ohne Pydantic - nur Standard-Library + toml.

Verwendung:
    from src.core.config_registry import (
        get_config,
        get_active_strategies,
        get_strategy_config
    )
"""

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

# tomllib ist ab Python 3.11 in stdlib
try:
    import tomllib
except ImportError:
    # Fallback für Python < 3.11
    try:
        import tomli as tomllib
    except ImportError:
        raise ImportError(
            "Benötigt Python 3.11+ (tomllib) oder 'pip install tomli'"
        )


# Default Config-Pfad (relativ zum Projekt-Root)
DEFAULT_CONFIG_PATH = Path("config.toml")


@dataclass
class StrategyConfig:
    """
    Merged Strategie-Config: Defaults + Strategie-spezifische Parameter.

    Attributes:
        name: Strategie-Name
        active: Ist in strategies.active?
        params: Strategie-spezifische Parameter
        defaults: Default-Parameter
        metadata: Optional Metadata-Dict
    """
    name: str
    active: bool
    params: dict[str, Any]
    defaults: dict[str, Any]
    metadata: dict[str, Any] | None = None

    def get(self, key: str, default: Any = None) -> Any:
        """
        Holt Parameter mit Fallback-Logik:
        1. Strategie-spezifische Parameter
        2. Defaults
        3. Übergebener default-Wert
        """
        if key in self.params:
            return self.params[key]
        if key in self.defaults:
            return self.defaults[key]
        return default

    def to_dict(self) -> dict[str, Any]:
        """Merged Dict aller Parameter."""
        return {**self.defaults, **self.params}


class ConfigRegistry:
    """
    Zentrale Config-Verwaltung mit Registry-Support.
    """

    def __init__(self, config_path: Path | None = None):
        """
        Args:
            config_path: Pfad zu config.toml (default: config/config.toml)
        """
        self.config_path = config_path or self._resolve_config_path()
        self._raw_config: dict[str, Any] | None = None

    def _resolve_config_path(self) -> Path:
        """Bestimmt Config-Pfad (env var > default)."""
        env_path = os.getenv("PEAK_TRADE_CONFIG")
        if env_path:
            return Path(env_path)
        return DEFAULT_CONFIG_PATH

    def _load_config(self) -> dict[str, Any]:
        """Lädt config.toml."""
        if not self.config_path.exists():
            raise FileNotFoundError(
                f"Config nicht gefunden: {self.config_path}"
            )

        with open(self.config_path, "rb") as f:
            return tomllib.load(f)

    @property
    def config(self) -> dict[str, Any]:
        """Lazy Loading der Config (Caching)."""
        if self._raw_config is None:
            self._raw_config = self._load_config()
        return self._raw_config

    def reload(self):
        """Erzwingt Neuladen der Config."""
        self._raw_config = None

    def get_active_strategies(self) -> list[str]:
        """Liste der aktiven Strategien."""
        return self.config.get("strategies", {}).get("active", [])

    def get_available_strategies(self) -> list[str]:
        """Liste aller verfügbaren Strategien."""
        return self.config.get("strategies", {}).get("available", [])

    def list_strategies(self) -> list[str]:
        """Liste aller definierten Strategien (aus [strategy.*])."""
        return sorted(self.config.get("strategy", {}).keys())

    def get_strategy_defaults(self) -> dict[str, Any]:
        """Holt Strategie-Defaults."""
        return self.config.get("strategies", {}).get("defaults", {})

    def get_strategy_config(self, name: str) -> StrategyConfig:
        """
        Lädt Strategie-Config mit Defaults-Merging.

        Args:
            name: Strategie-Name

        Returns:
            StrategyConfig mit merged Parameters

        Raises:
            KeyError: Wenn Strategie nicht definiert
        """
        if name not in self.config.get("strategy", {}):
            available = ", ".join(self.list_strategies()) or "keine"
            raise KeyError(
                f"Strategie '{name}' nicht in config.toml definiert. "
                f"Verfügbare: {available}"
            )

        defaults = self.get_strategy_defaults()
        strategy_params = self.config["strategy"][name]
        metadata = (
            self.config.get("strategies", {})
            .get("metadata", {})
            .get(name)
        )
        active = name in self.get_active_strategies()

        return StrategyConfig(
            name=name,
            active=active,
            params=strategy_params,
            defaults=defaults,
            metadata=metadata
        )

    def get_strategies_by_regime(self, regime: str) -> list[str]:
        """
        Filtert Strategien nach Marktregime.

        Args:
            regime: "trending", "ranging", "any"

        Returns:
            Liste von Strategie-Namen
        """
        result = []
        metadata_dict = self.config.get("strategies", {}).get("metadata", {})

        for name in self.get_available_strategies():
            meta = metadata_dict.get(name, {})
            if meta.get("best_market_regime") in [regime, "any"]:
                result.append(name)

        return result


_GLOBAL_REGISTRY: ConfigRegistry | None = None


def get_registry(force_reload: bool = False) -> ConfigRegistry:
    """
    Gibt globale ConfigRegistry-Instanz zurück (Singleton).

    Args:
        force_reload: Config neu laden?

    Returns:
        ConfigRegistry-Instanz
    """
    global _GLOBAL_REGISTRY

    if _GLOBAL_REGISTRY is None:
        _GLOBAL_REGISTRY = ConfigRegistry()
    elif force_reload:
        _GLOBAL_REGISTRY.reload()

    return _GLOBAL_REGISTRY


def get_config() -> dict[str, Any]:
    """Gibt die Raw-Config zurück."""
    return get_registry().config


def get_active_strategies() -> list[str]:
    """Liste der aktiven Strategien."""
    return get_registry().get_active_strategies()


def get_strategy_config(name: str) -> StrategyConfig:
    """Lädt Strategie-Config mit Defaults-Merging."""
    return get_registry().get_strategy_config(name)


def list_strategies() -> list[str]:
    """Liste aller definierten Strategien."""
    return get_registry().list_strategies()


def get_strategies_by_regime(regime: str) -> list[str]:
    """Filtert Strategien nach Marktregime."""
    return get_registry().get_strategies_by_regime(regime)


def reset_config():
    """Reset Global Registry (für Tests)."""
    global _GLOBAL_REGISTRY
    _GLOBAL_REGISTRY = None
