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
from pathlib import Path
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
import logging

# tomllib ist ab Python 3.11 in stdlib
try:
    import tomllib
except ImportError:
    # Fallback für Python < 3.11
    try:
        import tomli as tomllib
    except ImportError:
        raise ImportError("Benötigt Python 3.11+ (tomllib) oder 'pip install tomli'")

from .errors import ConfigError

logger = logging.getLogger(__name__)


# Projekt-Root (robust gegenüber unterschiedlichem CWD)
_PROJECT_ROOT = Path(__file__).resolve().parents[2]

# Default Config-Pfade (Primär: config/config.toml, Fallback: ./config.toml)
DEFAULT_CONFIG_PATH = _PROJECT_ROOT / "config" / "config.toml"
FALLBACK_CONFIG_PATH = _PROJECT_ROOT / "config.toml"


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
    params: Dict[str, Any]
    defaults: Dict[str, Any]
    metadata: Optional[Dict[str, Any]] = None

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

    def to_dict(self) -> Dict[str, Any]:
        """Merged Dict aller Parameter."""
        return {**self.defaults, **self.params}


class ConfigRegistry:
    """
    Zentrale Config-Verwaltung mit Registry-Support.
    """

    def __init__(self, config_path: Optional[Path] = None):
        """
        Args:
            config_path: Pfad zu config.toml (default: config/config.toml)
        """
        self.config_path = config_path or self._resolve_config_path()
        self._raw_config: Optional[Dict[str, Any]] = None

    def _resolve_config_path(self) -> Path:
        """
        Bestimmt Config-Pfad (env var > default > fallback).

        Priorität:
        1) PEAK_TRADE_CONFIG (wie in docs/REGISTRY_BACKTEST_CLI.md dokumentiert)
        2) <repo>/config/config.toml
        3) <repo>/config.toml
        """
        # Prefer PEAK_TRADE_CONFIG_PATH (used by test harness / other loaders),
        # then fall back to PEAK_TRADE_CONFIG (documented for registry/CLI).
        #
        # Rationale: in CI/test contexts, PEAK_TRADE_CONFIG may be set for other subsystems.
        # The test harness sets PEAK_TRADE_CONFIG_PATH early and expects it to win.
        env_path = os.getenv("PEAK_TRADE_CONFIG_PATH") or os.getenv("PEAK_TRADE_CONFIG")
        if env_path:
            p = Path(env_path)
            if not p.is_absolute():
                p = _PROJECT_ROOT / p
            logger.info("ConfigRegistry: using config override: %s", p)
            return p

        if DEFAULT_CONFIG_PATH.exists():
            logger.info("ConfigRegistry: using default config path: %s", DEFAULT_CONFIG_PATH)
            return DEFAULT_CONFIG_PATH
        if FALLBACK_CONFIG_PATH.exists():
            logger.warning(
                "ConfigRegistry: default missing, using fallback config path: %s",
                FALLBACK_CONFIG_PATH,
            )
            return FALLBACK_CONFIG_PATH

        # Default zurückgeben, damit Fehlermeldung den erwarteten Pfad enthält.
        logger.warning(
            "ConfigRegistry: no config found; expected default path: %s", DEFAULT_CONFIG_PATH
        )
        return DEFAULT_CONFIG_PATH

    def _warn_strategy_catalog_mismatches(self, cfg: Dict[str, Any]) -> None:
        """
        Sanity warnings for strategies.available vs. configured [strategy.*] blocks.

        - Warn if `strategies.available` contains ids without a corresponding `[strategy.<id>]` block.
        - Optionally warn if `[strategy.*]` exists but id is not listed in `strategies.available`.
        """
        strategies_section = cfg.get("strategies", {}) or {}
        available = strategies_section.get("available", []) or []
        defined = list((cfg.get("strategy", {}) or {}).keys())

        if not isinstance(available, list):
            return

        defined_set = set(defined)
        missing_blocks = [s for s in available if s not in defined_set]
        if missing_blocks:
            logger.warning(
                "ConfigRegistry: strategies.available contains ids without [strategy.<id>] blocks: %s",
                missing_blocks,
            )

        # Optional: defined but not marked available (can cause regime filtering surprises)
        available_set = set(available)
        not_listed = [s for s in defined if s not in available_set]
        if not_listed and available:
            logger.warning(
                "ConfigRegistry: [strategy.*] blocks not listed in strategies.available: %s",
                not_listed,
            )

    def _load_config(self) -> Dict[str, Any]:
        """Lädt config.toml."""
        if not self.config_path.exists():
            raise ConfigError(
                f"Configuration file not found: {self.config_path}",
                hint="Create config/config.toml (recommended) or set PEAK_TRADE_CONFIG environment variable",
                context={"config_path": str(self.config_path)},
            )

        try:
            with open(self.config_path, "rb") as f:
                cfg = tomllib.load(f)

            # Defensive fallback:
            # In CI and some test setups, PEAK_TRADE_CONFIG may be used for other config systems
            # (e.g. a root-level config without registry anchors). BacktestEngine and registry-driven
            # workflows require at least:
            #   - cfg["backtest"] (initial_cash, results_dir, ...)
            #   - cfg["strategies"] / cfg["strategy"] for registry-backed selection
            #
            # If an override config lacks required anchors, fall back to the default registry config.
            missing_registry_anchors = (
                ("backtest" not in cfg) or ("strategies" not in cfg) or ("strategy" not in cfg)
            )
            if missing_registry_anchors:
                if self.config_path != DEFAULT_CONFIG_PATH and DEFAULT_CONFIG_PATH.exists():
                    logger.warning(
                        "ConfigRegistry: config at %s lacks registry anchors; falling back to default: %s",
                        self.config_path,
                        DEFAULT_CONFIG_PATH,
                    )
                    with open(DEFAULT_CONFIG_PATH, "rb") as f:
                        cfg = tomllib.load(f)
                else:
                    logger.warning(
                        "ConfigRegistry: config at %s lacks registry anchors; callers may fail",
                        self.config_path,
                    )

            # Sanity warnings (no hard errors)
            try:
                self._warn_strategy_catalog_mismatches(cfg)
            except Exception as e:
                logger.debug("ConfigRegistry: strategy catalog sanity check failed: %s", e)
            return cfg
        except Exception as e:
            raise ConfigError(
                f"Failed to parse configuration file: {self.config_path}",
                hint="Verify TOML syntax is valid. Use a TOML validator or check for common errors (missing quotes, brackets, etc.)",
                context={"config_path": str(self.config_path)},
                cause=e,
            )

    @property
    def config(self) -> Dict[str, Any]:
        """Lazy Loading der Config (Caching)."""
        if self._raw_config is None:
            self._raw_config = self._load_config()
        return self._raw_config

    def reload(self):
        """Erzwingt Neuladen der Config."""
        self._raw_config = None

    def get_active_strategies(self) -> List[str]:
        """Liste der aktiven Strategien."""
        return self.config.get("strategies", {}).get("active", [])

    def get_available_strategies(self) -> List[str]:
        """Liste aller verfügbaren Strategien."""
        return self.config.get("strategies", {}).get("available", [])

    def list_strategies(self) -> List[str]:
        """Liste aller definierten Strategien (aus [strategy.*])."""
        return sorted(self.config.get("strategy", {}).keys())

    def get_strategy_defaults(self) -> Dict[str, Any]:
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
            ConfigError: Wenn Strategie nicht definiert
        """
        if name not in self.config.get("strategy", {}):
            available = self.list_strategies()
            available_str = ", ".join(available) if available else "none"
            raise ConfigError(
                f"Strategy '{name}' not found in configuration",
                hint=f"Available strategies: [{available_str}]. Check [strategy.{name}] section in config.toml",
                context={
                    "requested_strategy": name,
                    "available_strategies": available,
                    "config_path": str(self.config_path),
                },
            )

        defaults = self.get_strategy_defaults()
        strategy_params = self.config["strategy"][name]
        metadata = self.config.get("strategies", {}).get("metadata", {}).get(name)
        active = name in self.get_active_strategies()

        return StrategyConfig(
            name=name, active=active, params=strategy_params, defaults=defaults, metadata=metadata
        )

    def get_strategies_by_regime(self, regime: str) -> List[str]:
        """
        Filtert Strategien nach Marktregime.

        Args:
            regime: "trending", "ranging", "any"

        Returns:
            Liste von Strategie-Namen
        """
        if regime == "any":
            # "any" bedeutet: kein Regime-Filter → alle verfügbaren Strategien
            return list(self.get_available_strategies())

        result = []
        metadata_dict = self.config.get("strategies", {}).get("metadata", {})

        for name in self.get_available_strategies():
            meta = metadata_dict.get(name, {})
            if meta.get("best_market_regime") in [regime, "any"]:
                result.append(name)

        return result


_GLOBAL_REGISTRY: Optional[ConfigRegistry] = None


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


def get_config() -> Dict[str, Any]:
    """Gibt die Raw-Config zurück."""
    return get_registry().config


def get_active_strategies() -> List[str]:
    """Liste der aktiven Strategien."""
    return get_registry().get_active_strategies()


def get_strategy_config(name: str) -> StrategyConfig:
    """Lädt Strategie-Config mit Defaults-Merging."""
    return get_registry().get_strategy_config(name)


def list_strategies() -> List[str]:
    """Liste aller definierten Strategien."""
    return get_registry().list_strategies()


def get_strategies_by_regime(regime: str) -> List[str]:
    """Filtert Strategien nach Marktregime."""
    return get_registry().get_strategies_by_regime(regime)


def reset_config():
    """Reset Global Registry (für Tests)."""
    global _GLOBAL_REGISTRY
    _GLOBAL_REGISTRY = None
