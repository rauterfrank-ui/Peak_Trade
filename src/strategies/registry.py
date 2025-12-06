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
