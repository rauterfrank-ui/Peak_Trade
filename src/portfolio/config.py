# src/portfolio/config.py
"""
Portfolio Configuration (Phase 26)
===================================

Dataclass für Portfolio-Strategie-Konfiguration.
Wird aus config.toml geladen und steuert den Portfolio-Layer.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from ..core.peak_config import PeakConfig


@dataclass
class PortfolioConfig:
    """
    Konfiguration für Portfolio-Strategien.

    Attributes:
        enabled: Aktiviert/Deaktiviert den Portfolio-Layer
        name: Name der Portfolio-Strategie (equal_weight, fixed_weights, vol_target)
        symbols: Explizites Universe (optional, sonst aus Kontext)
        fixed_weights: Feste Gewichte für FixedWeightsStrategy
        rebalance_frequency: Rebalancing-Intervall ("1D", "1W", "every_bar")
        vol_lookback: Lookback für Volatilitätsberechnung (Vol-Target-Strategie)
        vol_target: Ziel-Volatilität für Vol-Target-Strategie
        max_single_weight: Maximales Gewicht für ein einzelnes Symbol
        min_weight: Minimales Gewicht (Symbole unter diesem Wert werden ausgeschlossen)
        normalize_weights: Ob Gewichte auf Summe 1.0 normalisiert werden sollen
    """

    enabled: bool = False
    name: str = "equal_weight"
    symbols: Optional[List[str]] = None
    fixed_weights: Optional[Dict[str, float]] = None
    rebalance_frequency: str = "1D"
    vol_lookback: int = 20
    vol_target: float = 0.15  # 15% annualisierte Volatilität
    max_single_weight: float = 0.5  # Max 50% in einem Symbol
    min_weight: float = 0.01  # Min 1%
    normalize_weights: bool = True

    def __post_init__(self) -> None:
        """Validierung der Config-Werte."""
        valid_strategies = ["equal_weight", "fixed_weights", "vol_target"]
        if self.name not in valid_strategies:
            raise ValueError(
                f"Unbekannte Portfolio-Strategie: '{self.name}'. Verfügbar: {valid_strategies}"
            )

        if self.max_single_weight <= 0 or self.max_single_weight > 1.0:
            raise ValueError(
                f"max_single_weight muss in (0, 1] liegen, ist: {self.max_single_weight}"
            )

        if self.vol_lookback < 2:
            raise ValueError(f"vol_lookback muss >= 2 sein, ist: {self.vol_lookback}")

    @classmethod
    def from_peak_config(cls, cfg: PeakConfig) -> "PortfolioConfig":
        """
        Erstellt PortfolioConfig aus PeakConfig.

        Args:
            cfg: PeakConfig-Instanz (aus config.toml)

        Returns:
            PortfolioConfig-Instanz

        Example:
            >>> from src.core.peak_config import load_config
            >>> peak_cfg = load_config("config.toml")
            >>> portfolio_cfg = PortfolioConfig.from_peak_config(peak_cfg)
        """
        # Basis-Felder
        enabled = cfg.get("portfolio.enabled", False)
        name = cfg.get("portfolio.strategy_name", "equal_weight")

        # Falls name nicht gesetzt, versuche allocation_method als Fallback
        if name == "equal_weight" and cfg.get("portfolio.allocation_method"):
            allocation_method = cfg.get("portfolio.allocation_method", "equal")
            # Mapping: allocation_method → strategy_name
            if allocation_method == "equal":
                name = "equal_weight"
            elif allocation_method == "manual":
                name = "fixed_weights"
            elif allocation_method in ("risk_parity", "vol_target"):
                name = "vol_target"

        # Symbole
        symbols = cfg.get("portfolio.symbols", None)

        # Fixed Weights aus [portfolio.weights] oder [portfolio.asset_weights]
        fixed_weights = cfg.get("portfolio.weights", None)
        if fixed_weights is None:
            # Fallback: asset_weights + symbols kombinieren
            asset_weights = cfg.get("portfolio.asset_weights", None)
            if asset_weights and symbols:
                fixed_weights = dict(zip(symbols, asset_weights))

        # Rebalancing
        rebalance_freq_bars = cfg.get("portfolio.rebalance_frequency", 24)
        # Konvertiere Bars zu String-Format
        if isinstance(rebalance_freq_bars, int):
            if rebalance_freq_bars <= 1:
                rebalance_frequency = "every_bar"
            elif rebalance_freq_bars <= 24:
                rebalance_frequency = "1D"
            else:
                rebalance_frequency = "1W"
        else:
            rebalance_frequency = str(rebalance_freq_bars)

        # Volatility-Target-Parameter
        vol_lookback = cfg.get("portfolio.vol_lookback", 20)
        vol_target = cfg.get("portfolio.vol_target", 0.15)

        # Constraints
        max_single_weight = cfg.get("portfolio.max_single_weight", 0.5)
        min_weight = cfg.get("portfolio.min_weight", 0.01)
        normalize_weights = cfg.get("portfolio.normalize_weights", True)

        return cls(
            enabled=enabled,
            name=name,
            symbols=symbols,
            fixed_weights=fixed_weights,
            rebalance_frequency=rebalance_frequency,
            vol_lookback=vol_lookback,
            vol_target=vol_target,
            max_single_weight=max_single_weight,
            min_weight=min_weight,
            normalize_weights=normalize_weights,
        )

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PortfolioConfig":
        """
        Erstellt PortfolioConfig aus einem Dict.

        Args:
            data: Dict mit Config-Werten

        Returns:
            PortfolioConfig-Instanz
        """
        return cls(
            enabled=data.get("enabled", False),
            name=data.get("name", "equal_weight"),
            symbols=data.get("symbols"),
            fixed_weights=data.get("fixed_weights"),
            rebalance_frequency=data.get("rebalance_frequency", "1D"),
            vol_lookback=data.get("vol_lookback", 20),
            vol_target=data.get("vol_target", 0.15),
            max_single_weight=data.get("max_single_weight", 0.5),
            min_weight=data.get("min_weight", 0.01),
            normalize_weights=data.get("normalize_weights", True),
        )

    def to_dict(self) -> Dict[str, Any]:
        """
        Konvertiert Config zu Dict.

        Returns:
            Dict mit allen Config-Werten
        """
        return {
            "enabled": self.enabled,
            "name": self.name,
            "symbols": self.symbols,
            "fixed_weights": self.fixed_weights,
            "rebalance_frequency": self.rebalance_frequency,
            "vol_lookback": self.vol_lookback,
            "vol_target": self.vol_target,
            "max_single_weight": self.max_single_weight,
            "min_weight": self.min_weight,
            "normalize_weights": self.normalize_weights,
        }
