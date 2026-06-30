# src/strategies/registry.py
"""
Strategy-Registry für Peak_Trade.

Zentrale Registry aller verfügbaren Strategien mit einheitlichem Zugriff.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, Mapping, Optional, Tuple, Type

from .base import BaseStrategy
from .ma_crossover import MACrossoverStrategy
from .rsi_reversion import RsiReversionStrategy
from .breakout_donchian import DonchianBreakoutStrategy
from .momentum import MomentumStrategy
from .bollinger import BollingerBandsStrategy
from .macd import MACDStrategy
from .trend_following import TrendFollowingStrategy
from .mean_reversion import MeanReversionStrategy
from .my_strategy import MyStrategy

# Phase 40: Strategy Library Erweiterungen
from .breakout import BreakoutStrategy
from .vol_regime_filter import VolRegimeFilter
from .composite import CompositeStrategy
from .regime_aware_portfolio import RegimeAwarePortfolioStrategy

# Research-Track: Armstrong & El-Karoui Strategien (R&D-Only)
from .armstrong import ArmstrongCycleStrategy
from .el_karoui import ElKarouiVolatilityStrategy, ElKarouiVolModelStrategy

# Research-Track: Ehlers & López de Prado Strategien (R&D-Only)
from .ehlers import EhlersCycleFilterStrategy
from .lopez_de_prado import MetaLabelingStrategy

# Research-Track: Bouchaud (OHLCV-Proxy) & Gatheral/Cont (Skeleton)
from .bouchaud import BouchaudMicrostructureStrategy
from .gatheral_cont import VolRegimeOverlayStrategy


@dataclass(frozen=True)
class StrategySpec:
    """
    Spezifikation einer registrierten Strategie.

    Attributes:
        key: Eindeutiger Kurzname (z.B. "ma_crossover")
        cls: Strategieklasse (muss von BaseStrategy erben)
        config_section: TOML-Section für Config (z.B. "strategy.ma_crossover")
        description: Optionale Beschreibung
        is_live_ready: Ob Strategie für Live-Trading freigegeben ist (Default: True)
        tier: Strategie-Tier ("production" oder "r_and_d", Default: "production")
        allowed_environments: Liste erlaubter Environments (Default: ["backtest", "paper", "live"])
    """

    key: str
    cls: Type[BaseStrategy]
    config_section: str
    description: str = ""
    is_live_ready: bool = True
    tier: str = "production"
    allowed_environments: tuple[str, ...] = (
        "backtest",
        "offline_backtest",
        "paper",
        "live",
        "research",
    )


# Zentrale Registry aller verfügbaren Strategien
_STRATEGY_REGISTRY: Dict[str, StrategySpec] = {
    "ma_crossover": StrategySpec(
        key="ma_crossover",
        cls=MACrossoverStrategy,
        config_section="strategy.ma_crossover",
        description="Moving Average Crossover (Trend-Following)",
        allowed_environments=("backtest", "offline_backtest", "paper", "testnet", "live"),
    ),
    "rsi_reversion": StrategySpec(
        key="rsi_reversion",
        cls=RsiReversionStrategy,
        config_section="strategy.rsi_reversion",
        description="RSI Mean-Reversion (Oversold/Overbought)",
    ),
    "breakout_donchian": StrategySpec(
        key="breakout_donchian",
        cls=DonchianBreakoutStrategy,
        config_section="strategy.breakout_donchian",
        description="Donchian Channel Breakout (Trend-Following)",
    ),
    "momentum_1h": StrategySpec(
        key="momentum_1h",
        cls=MomentumStrategy,
        config_section="strategy.momentum_1h",
        description="Momentum-basierte Trend-Following-Strategie",
    ),
    "bollinger_bands": StrategySpec(
        key="bollinger_bands",
        cls=BollingerBandsStrategy,
        config_section="strategy.bollinger_bands",
        description="Bollinger Bands Mean-Reversion",
    ),
    "macd": StrategySpec(
        key="macd",
        cls=MACDStrategy,
        config_section="strategy.macd",
        description="MACD Trend-Following",
    ),
    "trend_following": StrategySpec(
        key="trend_following",
        cls=TrendFollowingStrategy,
        config_section="strategy.trend_following",
        description="ADX-basierte Trend-Following-Strategie (Phase 18)",
    ),
    "mean_reversion": StrategySpec(
        key="mean_reversion",
        cls=MeanReversionStrategy,
        config_section="strategy.mean_reversion",
        description="Z-Score Mean-Reversion-Strategie (Phase 18)",
    ),
    "my_strategy": StrategySpec(
        key="my_strategy",
        cls=MyStrategy,
        config_section="strategy.my_strategy",
        description="ATR-basierte Volatility-Breakout-Strategie",
    ),
    # Phase 40: Strategy Library Erweiterungen
    "breakout": StrategySpec(
        key="breakout",
        cls=BreakoutStrategy,
        config_section="strategy.breakout",
        description="Breakout/Momentum-Strategie mit SL/TP (Phase 40)",
    ),
    "vol_regime_filter": StrategySpec(
        key="vol_regime_filter",
        cls=VolRegimeFilter,
        config_section="strategy.vol_regime_filter",
        description="Volatilitäts-Regime-Filter (Phase 40)",
    ),
    "composite": StrategySpec(
        key="composite",
        cls=CompositeStrategy,
        config_section="strategy.composite",
        description="Multi-Strategy Composite (Phase 40)",
    ),
    "regime_aware_portfolio": StrategySpec(
        key="regime_aware_portfolio",
        cls=RegimeAwarePortfolioStrategy,
        config_section="portfolio.regime_aware_breakout_rsi",
        description="Regime-Aware Portfolio Strategy (Breakout + RSI + Vol-Regime)",
    ),
    # ==========================================================================
    # Research-Track: R&D-Only Strategien (NICHT FÜR LIVE-TRADING)
    # ==========================================================================
    "armstrong_cycle": StrategySpec(
        key="armstrong_cycle",
        cls=ArmstrongCycleStrategy,
        config_section="strategy.armstrong_cycle",
        description="Armstrong ECM Cycle Strategy (R&D-Only, nicht für Live)",
        is_live_ready=True,  # Armstrong ist live-ready
        tier="production",
        allowed_environments=("backtest", "paper", "live"),
    ),
    "el_karoui_vol_model": StrategySpec(
        key="el_karoui_vol_model",
        cls=ElKarouiVolModelStrategy,
        config_section="strategy.el_karoui_vol_model",
        description="El Karoui Stochastic Vol Model (R&D-Only, nicht für Live)",
        is_live_ready=True,  # El Karoui ist live-ready
        tier="production",
        allowed_environments=("backtest", "paper", "live"),
    ),
    "ehlers_cycle_filter": StrategySpec(
        key="ehlers_cycle_filter",
        cls=EhlersCycleFilterStrategy,
        config_section="strategy.ehlers_cycle_filter",
        description="Ehlers DSP Cycle Filter (R&D-Only, Intraday-Signalqualität)",
        is_live_ready=False,  # NICHT live-ready
        tier="r_and_d",
        allowed_environments=("backtest", "offline_backtest", "research"),
    ),
    "meta_labeling": StrategySpec(
        key="meta_labeling",
        cls=MetaLabelingStrategy,
        config_section="strategy.meta_labeling",
        description="Meta-Labeling nach López de Prado (R&D-Only, ML-Layer)",
        is_live_ready=False,  # NICHT live-ready
        tier="r_and_d",
        allowed_environments=("backtest", "offline_backtest", "research"),
    ),
    # Research-Strategien (teilweise OHLCV-Proxy-Slices)
    "bouchaud_microstructure": StrategySpec(
        key="bouchaud_microstructure",
        cls=BouchaudMicrostructureStrategy,
        config_section="strategy.bouchaud_microstructure",
        description="Bouchaud Microstructure (R&D, OHLCV-Proxy-Signale)",
        is_live_ready=False,  # NICHT live-ready
        tier="r_and_d",
        allowed_environments=("backtest", "offline_backtest", "research"),
    ),
    "vol_regime_overlay": StrategySpec(
        key="vol_regime_overlay",
        cls=VolRegimeOverlayStrategy,
        config_section="strategy.vol_regime_overlay",
        description="Gatheral & Cont Vol-Regime-Overlay (R&D, realized-vol/Quantil-Proxy)",
        is_live_ready=False,  # NICHT live-ready
        tier="r_and_d",
        allowed_environments=("backtest", "offline_backtest", "research"),
    ),
}

REGISTRY_SCHEMA_VERSION = "strategy_registry_v1"
REGISTRY_POLICY_VERSION = "strategy_registry_policy_v1"
STRATEGY_VERSION_DEFAULT = "v1"
PARAMETER_SCHEMA_VERSION_DEFAULT = "v1"
ALIAS_POLICY_VERSION = "strategy_alias_v1"
ALIAS_REASON_CODE = "LEGACY_ALIAS_RESOLVED"

_LOADER_MODULE_REFS: Dict[str, str] = {
    "ma_crossover": "ma_crossover",
    "momentum_1h": "momentum",
    "rsi_strategy": "rsi",
    "bollinger_bands": "bollinger",
    "macd": "macd",
    "ecm_cycle": "ecm",
    "trend_following": "trend_following",
    "mean_reversion": "mean_reversion",
    "my_strategy": "my_strategy",
    "vol_breakout": "vol_breakout",
    "mean_reversion_channel": "mean_reversion_channel",
    "rsi_reversion": "rsi_reversion",
    "breakout": "breakout",
    "breakout_donchian": "breakout_donchian",
    "vol_regime_filter": "vol_regime_filter",
    "composite": "composite",
    "regime_aware_portfolio": "regime_aware_portfolio",
    "armstrong_cycle": "armstrong.armstrong_cycle_strategy",
    "el_karoui_vol_model": "el_karoui.el_karoui_vol_model_strategy",
    "ehlers_cycle_filter": "ehlers.ehlers_cycle_filter_strategy",
    "meta_labeling": "lopez_de_prado.meta_labeling_strategy",
    "bouchaud_microstructure": "bouchaud.bouchaud_microstructure_strategy",
    "vol_regime_overlay": "gatheral_cont.vol_regime_overlay_strategy",
}

_FUNCTIONAL_ONLY_STRATEGY_IDS: frozenset[str] = frozenset(
    {"vol_breakout", "mean_reversion_channel", "ecm_cycle", "rsi_strategy"}
)


class DeprecationStatus(str, Enum):
    ACTIVE = "ACTIVE"
    DEPRECATED_ALIAS = "DEPRECATED_ALIAS"
    DEPRECATED_STRATEGY = "DEPRECATED_STRATEGY"
    REMOVED = "REMOVED"


class StrategyRegistryError(ValueError):
    """Fail-closed strategy registry resolution error."""


@dataclass(frozen=True)
class StrategyAliasV1:
    legacy_key: str
    canonical_strategy_id: str
    alias_policy_version: str = ALIAS_POLICY_VERSION
    deprecation_status: DeprecationStatus = DeprecationStatus.DEPRECATED_ALIAS
    deprecation_message: str = ""
    removal_not_before_version: str = "strategy_registry_v2"
    source_ref: str = "src/strategies/registry.py"
    semantic_digest: str = ""


@dataclass(frozen=True)
class StrategyRegistryEntryV1:
    strategy_id: str
    strategy_version: str
    canonical_name: str
    factory_or_builder_ref: str
    capability_tags: Tuple[str, ...]
    supported_sides: Tuple[str, ...]
    supported_regimes: Tuple[str, ...]
    futures_compatible: bool
    spot_compatible: bool
    parameter_schema_version: str
    implementation_ref: str
    implementation_digest: str
    registration_source: str
    deprecation_status: DeprecationStatus
    replacement_strategy_id: Optional[str]
    alias_set: Tuple[str, ...]
    semantic_digest: str
    loader_module_ref: str


@dataclass(frozen=True)
class StrategyResolutionV1:
    original_key: str
    canonical_strategy_id: str
    strategy_version: str
    alias_applied: bool
    alias_policy_version: Optional[str]
    reason_code: str
    deprecation_status: DeprecationStatus


@dataclass(frozen=True)
class StrategyRegistrySnapshotV1:
    registry_schema_version: str
    registry_policy_version: str
    entries: Tuple[StrategyRegistryEntryV1, ...]
    aliases: Tuple[StrategyAliasV1, ...]
    deprecated_keys: Tuple[str, ...]
    strategy_ids_sorted: Tuple[str, ...]
    input_digest: str
    semantic_digest: str


def _stable_digest(payload: Mapping[str, Any]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


_LEGACY_ALIASES: Dict[str, StrategyAliasV1] = {
    "el_karoui_vol_v1": StrategyAliasV1(
        legacy_key="el_karoui_vol_v1",
        canonical_strategy_id="el_karoui_vol_model",
        deprecation_message="Use el_karoui_vol_model instead of el_karoui_vol_v1",
        semantic_digest=_stable_digest(
            {
                "legacy_key": "el_karoui_vol_v1",
                "canonical_strategy_id": "el_karoui_vol_model",
            }
        ),
    ),
}


def _normalize_strategy_key(raw_key: Optional[str]) -> str:
    if raw_key is None:
        raise StrategyRegistryError("strategy id must not be None")
    if not isinstance(raw_key, str):
        raise StrategyRegistryError("strategy id must be a string")
    if raw_key != raw_key.strip():
        raise StrategyRegistryError(f"strategy id whitespace ambiguity rejected: {raw_key!r}")
    normalized = raw_key.strip()
    if not normalized:
        raise StrategyRegistryError("strategy id must not be empty")
    return normalized


def _entry_capability_tags(spec: StrategySpec) -> Tuple[str, ...]:
    tags = ["futures", spec.tier]
    if spec.is_live_ready:
        tags.append("live_ready")
    return tuple(sorted(tags))


def _implementation_ref_for(strategy_id: str, spec: Optional[StrategySpec]) -> str:
    if spec is not None:
        return f"{spec.cls.__module__}.{spec.cls.__name__}"
    loader = _LOADER_MODULE_REFS[strategy_id]
    return f"src.strategies.{loader}"


def _build_canonical_entry(
    strategy_id: str, spec: Optional[StrategySpec]
) -> StrategyRegistryEntryV1:
    loader_ref = _LOADER_MODULE_REFS[strategy_id]
    if spec is not None:
        factory_ref = f"oop:{spec.cls.__module__}.{spec.cls.__name__}"
        capability_tags = _entry_capability_tags(spec)
    else:
        factory_ref = f"functional:src.strategies.{loader_ref}.generate_signals"
        capability_tags = ("futures", "functional")

    implementation_ref = _implementation_ref_for(strategy_id, spec)
    payload = {
        "strategy_id": strategy_id,
        "strategy_version": STRATEGY_VERSION_DEFAULT,
        "factory_or_builder_ref": factory_ref,
        "implementation_ref": implementation_ref,
        "loader_module_ref": loader_ref,
    }
    alias_set = tuple(
        sorted(
            alias.legacy_key
            for alias in _LEGACY_ALIASES.values()
            if alias.canonical_strategy_id == strategy_id
        )
    )
    return StrategyRegistryEntryV1(
        strategy_id=strategy_id,
        strategy_version=STRATEGY_VERSION_DEFAULT,
        canonical_name=strategy_id,
        factory_or_builder_ref=factory_ref,
        capability_tags=capability_tags,
        supported_sides=("long", "short"),
        supported_regimes=("*",),
        futures_compatible=True,
        spot_compatible=False,
        parameter_schema_version=PARAMETER_SCHEMA_VERSION_DEFAULT,
        implementation_ref=implementation_ref,
        implementation_digest=_stable_digest({"implementation_ref": implementation_ref}),
        registration_source="src/strategies/registry.py",
        deprecation_status=DeprecationStatus.ACTIVE,
        replacement_strategy_id=None,
        alias_set=alias_set,
        semantic_digest=_stable_digest(payload),
        loader_module_ref=loader_ref,
    )


def _all_canonical_strategy_ids() -> Tuple[str, ...]:
    ids = set(_STRATEGY_REGISTRY.keys()) | set(_FUNCTIONAL_ONLY_STRATEGY_IDS)
    return tuple(sorted(ids))


_CANONICAL_ENTRIES: Tuple[StrategyRegistryEntryV1, ...] = tuple(
    _build_canonical_entry(strategy_id, _STRATEGY_REGISTRY.get(strategy_id))
    for strategy_id in _all_canonical_strategy_ids()
)
_CANONICAL_ENTRY_BY_ID: Dict[str, StrategyRegistryEntryV1] = {
    entry.strategy_id: entry for entry in _CANONICAL_ENTRIES
}


def _validate_registry_invariants() -> None:
    if len(_CANONICAL_ENTRY_BY_ID) != len(_CANONICAL_ENTRIES):
        raise StrategyRegistryError("duplicate strategy_id in canonical registry")
    canonical_ids = set(_CANONICAL_ENTRY_BY_ID)
    for alias in _LEGACY_ALIASES.values():
        if alias.legacy_key in canonical_ids:
            raise StrategyRegistryError(f"alias/canonical collision: {alias.legacy_key}")
        if alias.canonical_strategy_id not in canonical_ids:
            raise StrategyRegistryError(f"alias target unknown: {alias.canonical_strategy_id}")
        if alias.canonical_strategy_id in _LEGACY_ALIASES:
            raise StrategyRegistryError(f"alias chain forbidden: {alias.legacy_key}")


_validate_registry_invariants()


def resolve_strategy_id(raw_key: Optional[str]) -> StrategyResolutionV1:
    normalized = _normalize_strategy_key(raw_key)
    if normalized in _CANONICAL_ENTRY_BY_ID:
        entry = _CANONICAL_ENTRY_BY_ID[normalized]
        return StrategyResolutionV1(
            original_key=raw_key if isinstance(raw_key, str) else normalized,
            canonical_strategy_id=entry.strategy_id,
            strategy_version=entry.strategy_version,
            alias_applied=False,
            alias_policy_version=None,
            reason_code="CANONICAL_ID",
            deprecation_status=entry.deprecation_status,
        )
    alias = _LEGACY_ALIASES.get(normalized)
    if alias is None:
        raise StrategyRegistryError(f"unknown strategy id: {normalized!r}")
    entry = _CANONICAL_ENTRY_BY_ID[alias.canonical_strategy_id]
    return StrategyResolutionV1(
        original_key=raw_key if isinstance(raw_key, str) else normalized,
        canonical_strategy_id=entry.strategy_id,
        strategy_version=entry.strategy_version,
        alias_applied=True,
        alias_policy_version=alias.alias_policy_version,
        reason_code=ALIAS_REASON_CODE,
        deprecation_status=alias.deprecation_status,
    )


def get_loader_module_ref(strategy_id: str) -> str:
    resolution = resolve_strategy_id(strategy_id)
    return _CANONICAL_ENTRY_BY_ID[resolution.canonical_strategy_id].loader_module_ref


def get_loader_module_map() -> Dict[str, str]:
    return {entry.strategy_id: entry.loader_module_ref for entry in _CANONICAL_ENTRIES}


def get_strategy_registry_entry(strategy_id: str) -> StrategyRegistryEntryV1:
    resolution = resolve_strategy_id(strategy_id)
    return _CANONICAL_ENTRY_BY_ID[resolution.canonical_strategy_id]


def build_registry_snapshot() -> StrategyRegistrySnapshotV1:
    entries = tuple(sorted(_CANONICAL_ENTRIES, key=lambda e: e.strategy_id))
    aliases = tuple(sorted(_LEGACY_ALIASES.values(), key=lambda a: a.legacy_key))
    deprecated_keys = tuple(sorted(a.legacy_key for a in aliases))
    strategy_ids_sorted = tuple(e.strategy_id for e in entries)
    input_payload = {
        "entries": [e.semantic_digest for e in entries],
        "aliases": [a.semantic_digest for a in aliases],
        "registry_schema_version": REGISTRY_SCHEMA_VERSION,
        "registry_policy_version": REGISTRY_POLICY_VERSION,
    }
    input_digest = _stable_digest(input_payload)
    semantic_digest = _stable_digest(
        {
            "input_digest": input_digest,
            "strategy_ids_sorted": list(strategy_ids_sorted),
            "deprecated_keys": list(deprecated_keys),
        }
    )
    return StrategyRegistrySnapshotV1(
        registry_schema_version=REGISTRY_SCHEMA_VERSION,
        registry_policy_version=REGISTRY_POLICY_VERSION,
        entries=entries,
        aliases=aliases,
        deprecated_keys=deprecated_keys,
        strategy_ids_sorted=strategy_ids_sorted,
        input_digest=input_digest,
        semantic_digest=semantic_digest,
    )


def serialize_registry_snapshot(snapshot: StrategyRegistrySnapshotV1) -> str:
    return json.dumps(
        {
            "registry_schema_version": snapshot.registry_schema_version,
            "registry_policy_version": snapshot.registry_policy_version,
            "strategy_ids_sorted": list(snapshot.strategy_ids_sorted),
            "deprecated_keys": list(snapshot.deprecated_keys),
            "input_digest": snapshot.input_digest,
            "semantic_digest": snapshot.semantic_digest,
            "entries": [
                {
                    "strategy_id": e.strategy_id,
                    "strategy_version": e.strategy_version,
                    "semantic_digest": e.semantic_digest,
                }
                for e in snapshot.entries
            ],
            "aliases": [
                {
                    "legacy_key": a.legacy_key,
                    "canonical_strategy_id": a.canonical_strategy_id,
                }
                for a in snapshot.aliases
            ],
        },
        sort_keys=True,
        separators=(",", ":"),
    )


def get_available_strategy_keys() -> list[str]:
    """
    Gibt Liste aller registrierten Strategie-Keys zurück.

    Returns:
        Liste von Strategie-Keys (z.B. ["ma_crossover", "rsi_reversion", ...])

    Example:
        >>> keys = get_available_strategy_keys()
        >>> print(keys)
        ['ma_crossover', 'rsi_reversion', 'breakout_donchian']
    """
    return list(_all_canonical_strategy_ids())


def get_strategy_spec(key: str) -> StrategySpec:
    """
    Holt die StrategySpec für einen gegebenen Key.

    Args:
        key: Strategie-Key (z.B. "ma_crossover")

    Returns:
        StrategySpec-Objekt

    Raises:
        KeyError: Wenn key nicht in Registry

    Example:
        >>> spec = get_strategy_spec("ma_crossover")
        >>> print(spec.cls)
        <class 'MACrossoverStrategy'>
    """
    try:
        resolution = resolve_strategy_id(key)
    except StrategyRegistryError as exc:
        available = ", ".join(get_available_strategy_keys())
        raise KeyError(
            f"Strategie '{key}' nicht in Registry. Verfügbare Strategien: {available}"
        ) from exc
    canonical = resolution.canonical_strategy_id
    if canonical not in _STRATEGY_REGISTRY:
        available = ", ".join(get_available_strategy_keys())
        raise KeyError(f"Strategie '{key}' nicht in Registry. Verfügbare Strategien: {available}")
    return _STRATEGY_REGISTRY[canonical]


def create_strategy_from_config(
    key: str,
    cfg: Any,
) -> BaseStrategy:
    """
    Erstellt eine Strategie-Instanz aus der Registry basierend auf Config.

    Args:
        key: Strategie-Key (z.B. "ma_crossover")
        cfg: Config-Objekt (PeakConfig oder kompatibel)

    Returns:
        Instanz der Strategie (BaseStrategy)

    Raises:
        KeyError: Wenn key nicht in Registry
        ValueError: Wenn Strategie in aktuellem Environment nicht erlaubt

    Example:
        >>> from src.core.peak_config import load_config
        >>> cfg = load_config()
        >>> strategy = create_strategy_from_config("ma_crossover", cfg)
        >>> print(strategy)
        <MACrossoverStrategy(fast_window=20, slow_window=50, ...)>
    """
    try:
        resolution = resolve_strategy_id(key)
    except StrategyRegistryError as exc:
        available = ", ".join(get_available_strategy_keys())
        raise KeyError(
            f"Strategie '{key}' nicht in Registry. Verfügbare Strategien: {available}"
        ) from exc
    canonical_key = resolution.canonical_strategy_id
    spec = get_strategy_spec(canonical_key)

    # ==========================================================================
    # GATE-SYSTEM: 3-stufige Prüfung für R&D-Strategien
    # ==========================================================================

    # Environment-Mode ermitteln (mit mehreren Fallbacks)
    env_mode = cfg.get("environment.mode")
    if not env_mode:
        # Fallback 1: env.mode
        env_mode = cfg.get("env.mode")
    if not env_mode:
        # Fallback 2: runtime.environment
        env_mode = cfg.get("runtime.environment")
    if not env_mode:
        # Fallback 3: environment.runtime_environment
        env_mode = cfg.get("environment.runtime_environment")
    if not env_mode:
        # Default: backtest
        env_mode = "backtest"

    # Gate A: IS_LIVE_READY Check (Hard-Gate für Live-Mode)
    if env_mode == "live" and not spec.is_live_ready:
        raise ValueError(
            f"Strategy '{key}' cannot be used in LIVE mode (IS_LIVE_READY=False). "
            f"This strategy is R&D-only and not validated for live trading."
        )

    # Gate B: TIER Check (R&D-Strategien brauchen allow_r_and_d_strategies Flag)
    if spec.tier == "r_and_d":
        allow_rnd = cfg.get("research.allow_r_and_d_strategies", False)
        if not allow_rnd:
            raise ValueError(
                f"Strategy '{key}' is R&D-only (TIER=r_and_d) and requires "
                f"'research.allow_r_and_d_strategies = true' in config."
            )

    # Gate C: ALLOWED_ENVIRONMENTS Check
    if env_mode not in spec.allowed_environments:
        allowed_str = ", ".join(spec.allowed_environments)
        raise ValueError(
            f"Strategy '{key}' not allowed in environment '{env_mode}'. "
            f"Allowed environments: {allowed_str}"
        )

    # Strategie-Instanz via from_config() erstellen
    strategy = spec.cls.from_config(cfg, section=spec.config_section)

    return strategy


def list_strategies(verbose: bool = False) -> None:
    """
    Gibt Liste aller verfügbaren Strategien aus (CLI-Helper).

    Args:
        verbose: Wenn True, zeigt auch Beschreibungen

    Example:
        >>> list_strategies(verbose=True)
        Available Strategies:
        - ma_crossover: Moving Average Crossover (Trend-Following)
        - rsi_reversion: RSI Mean-Reversion (Oversold/Overbought)
        - breakout_donchian: Donchian Channel Breakout (Trend-Following)
    """
    print("Available Strategies:")
    for key in sorted(get_available_strategy_keys()):
        spec = _STRATEGY_REGISTRY[key]
        if verbose and spec.description:
            print(f"  - {key}: {spec.description}")
        else:
            print(f"  - {key}")


def register_strategy(
    key: str,
    cls: Type[BaseStrategy],
    config_section: str,
    description: str = "",
) -> None:
    """
    Registriert eine neue Strategie zur Laufzeit.

    Args:
        key: Eindeutiger Strategie-Key
        cls: Strategieklasse
        config_section: TOML-Section
        description: Optionale Beschreibung

    Raises:
        ValueError: Wenn key bereits existiert

    Example:
        >>> class MyStrategy(BaseStrategy):
        ...     pass
        >>> register_strategy("my_strat", MyStrategy, "strategy.my_strat")
    """
    if key in _STRATEGY_REGISTRY:
        raise ValueError(f"Strategie '{key}' ist bereits registriert")

    _STRATEGY_REGISTRY[key] = StrategySpec(
        key=key,
        cls=cls,
        config_section=config_section,
        description=description,
    )
