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
    """

    key: str
    cls: Type[BaseStrategy]
    config_section: str
    description: str = ""


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
    ),
    "el_karoui_vol_model": StrategySpec(
        key="el_karoui_vol_model",
        cls=ElKarouiVolModelStrategy,
        config_section="strategy.el_karoui_vol_model",
        description="El Karoui Stochastic Vol Model (R&D-Only, nicht für Live)",
    ),
    "ehlers_cycle_filter": StrategySpec(
        key="ehlers_cycle_filter",
        cls=EhlersCycleFilterStrategy,
        config_section="strategy.ehlers_cycle_filter",
        description="Ehlers DSP Cycle Filter (R&D-Only, Intraday-Signalqualität)",
    ),
    "meta_labeling": StrategySpec(
        key="meta_labeling",
        cls=MetaLabelingStrategy,
        config_section="strategy.meta_labeling",
        description="Meta-Labeling nach López de Prado (R&D-Only, ML-Layer)",
    ),
    # Skeleton-Strategien (Platzhalter für zukünftige Research)
    "bouchaud_microstructure": StrategySpec(
        key="bouchaud_microstructure",
        cls=BouchaudMicrostructureStrategy,
        config_section="strategy.bouchaud_microstructure",
        description="Bouchaud Microstructure (R&D-Skeleton, Tick-/Orderbuch-basiert)",
    ),
    "vol_regime_overlay": StrategySpec(
        key="vol_regime_overlay",
        cls=VolRegimeOverlayStrategy,
        config_section="strategy.vol_regime_overlay",
        description="Gatheral & Cont Vol-Regime-Overlay (R&D-Skeleton, Meta-Layer)",
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

    Example:
        >>> from src.core.peak_config import load_config
        >>> cfg = load_config()
        >>> strategy = create_strategy_from_config("ma_crossover", cfg)
        >>> print(strategy)
        <MACrossoverStrategy(fast_window=20, slow_window=50, ...)>
    """
    spec = get_strategy_spec(key)

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
