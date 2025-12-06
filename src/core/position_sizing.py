# src/core/position_sizing.py
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Literal


class BasePositionSizer(ABC):
    """
    Basisklasse für Position Sizing.

    Contract:
    - Input: diskretes Signal (-1, 0, 1), aktueller Preis, aktuelle Equity
    - Output: Ziel-Positionsgröße in Units (z.B. BTC, ETH, Stücke).
    """

    @abstractmethod
    def get_target_position(self, signal: int, price: float, equity: float) -> float:
        """
        Berechne die Ziel-Positionsgröße (Units) für das gegebene Signal.

        Args:
            signal: Diskretes Signal (-1=short, 0=flat, 1=long)
            price: Aktueller Preis des Assets
            equity: Aktuelle Equity/Kapital

        Returns:
            Ziel-Positionsgröße in Units (positiv=long, negativ=short, 0=flat)
        """
        raise NotImplementedError


class NoopPositionSizer(BasePositionSizer):
    """
    Default: nutzt das Signal direkt als Units (Kompatibilität mit altem Verhalten).

    - signal =  1 -> +1 Unit
    - signal = -1 -> -1 Unit
    - signal =  0 ->  0 Units
    """

    def get_target_position(self, signal: int, price: float, equity: float) -> float:
        return float(signal)

    def __repr__(self) -> str:
        return "<NoopPositionSizer()>"


@dataclass
class FixedSizeSizer(BasePositionSizer):
    """
    Fester Positionsumfang in Units pro vollem Signal.

    Beispiel:
    - units = 0.01  → 0.01 BTC pro vollem Long/Short-Signal
    """

    units: float = 1.0

    def get_target_position(self, signal: int, price: float, equity: float) -> float:
        return float(signal) * float(self.units)

    def __repr__(self) -> str:
        return f"<FixedSizeSizer(units={self.units})>"


@dataclass
class FixedFractionSizer(BasePositionSizer):
    """
    Investiert einen festen Anteil der aktuellen Equity pro vollem Signal.

    Beispiel:
    - fraction = 0.1 → 10% der Equity
    - Units = (Equity * fraction) / price
    """

    fraction: float = 0.1  # 10%

    def get_target_position(self, signal: int, price: float, equity: float) -> float:
        if signal == 0:
            return 0.0
        if price <= 0:
            return 0.0

        notional = max(equity, 0.0) * float(self.fraction)
        units = notional / price
        return float(signal) * units

    def __repr__(self) -> str:
        return f"<FixedFractionSizer(fraction={self.fraction:.1%})>"


def build_position_sizer_from_config(
    cfg: Any,
    section: str = "position_sizing",
) -> BasePositionSizer:
    """
    Fabrik-Funktion, die aus der Config einen passenden PositionSizer baut.

    Args:
        cfg: Config-Objekt (PeakConfig oder kompatibles Dict-Interface)
        section: Config-Section für Position Sizing

    Returns:
        BasePositionSizer-Instanz

    Erwartete Struktur in config.toml:

    [position_sizing]
    type = "noop"            # oder "fixed_size", "fixed_fraction"
    units = 1.0              # nur für type="fixed_size"
    fraction = 0.1           # nur für type="fixed_fraction"

    Example:
        >>> from src.core.peak_config import load_config
        >>> cfg = load_config()
        >>> sizer = build_position_sizer_from_config(cfg)
    """

    # Config-Zugriff: Unterstützt PeakConfig und Dict
    if hasattr(cfg, 'get'):
        get_fn = cfg.get
    elif isinstance(cfg, dict):
        # Fallback für plain dict
        def get_fn(path, default=None):
            keys = path.split(".")
            node = cfg
            for key in keys:
                if isinstance(node, dict) and key in node:
                    node = node[key]
                else:
                    return default
            return node
    else:
        raise TypeError(f"Unsupported config type: {type(cfg)}")

    type_value: str = str(get_fn(f"{section}.type", "noop")).lower()

    if type_value == "fixed_size":
        units = float(get_fn(f"{section}.units", 1.0))
        return FixedSizeSizer(units=units)

    if type_value == "fixed_fraction":
        fraction = float(get_fn(f"{section}.fraction", 0.1))
        return FixedFractionSizer(fraction=fraction)

    # Fallback / Default
    return NoopPositionSizer()
