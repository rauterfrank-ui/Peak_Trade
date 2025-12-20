# src/strategies/registry.py
"""
Strategy-Registry für Peak_Trade.

Zentrale Registry aller verfügbaren Strategien mit einheitlichem Zugriff.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional, Type

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

# Research-Track: Bouchaud & Gatheral/Cont Strategien (R&D-Only, Skeleton)
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
    allowed_environments: tuple[str, ...] = ("backtest", "offline_backtest", "paper", "live", "research")


# Zentrale Registry aller verfügbaren Strategien
_STRATEGY_REGISTRY: Dict[str, StrategySpec] = {
    "ma_crossover": StrategySpec(
        key="ma_crossover",
        cls=MACrossoverStrategy,
        config_section="strategy.ma_crossover",
        description="Moving Average Crossover (Trend-Following)",
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
    # Alias für Backwards Compatibility
    "el_karoui_vol_v1": StrategySpec(
        key="el_karoui_vol_v1",
        cls=ElKarouiVolModelStrategy,
        config_section="strategy.el_karoui_vol_model",
        description="El Karoui Vol Model (Alias für el_karoui_vol_model, R&D-Only)",
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
    # Skeleton-Strategien (Platzhalter für zukünftige Research)
    "bouchaud_microstructure": StrategySpec(
        key="bouchaud_microstructure",
        cls=BouchaudMicrostructureStrategy,
        config_section="strategy.bouchaud_microstructure",
        description="Bouchaud Microstructure (R&D-Skeleton, Tick-/Orderbuch-basiert)",
        is_live_ready=False,  # NICHT live-ready
        tier="r_and_d",
        allowed_environments=("backtest", "offline_backtest", "research"),
    ),
    "vol_regime_overlay": StrategySpec(
        key="vol_regime_overlay",
        cls=VolRegimeOverlayStrategy,
        config_section="strategy.vol_regime_overlay",
        description="Gatheral & Cont Vol-Regime-Overlay (R&D-Skeleton, Meta-Layer)",
        is_live_ready=False,  # NICHT live-ready
        tier="r_and_d",
        allowed_environments=("backtest", "offline_backtest", "research"),
    ),
}


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
    return list(_STRATEGY_REGISTRY.keys())


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
    if key not in _STRATEGY_REGISTRY:
        available = ", ".join(get_available_strategy_keys())
        raise KeyError(
            f"Strategie '{key}' nicht in Registry. "
            f"Verfügbare Strategien: {available}"
        )
    return _STRATEGY_REGISTRY[key]


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
    spec = get_strategy_spec(key)

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
