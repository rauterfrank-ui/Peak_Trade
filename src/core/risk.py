# src/core/risk.py
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any


class BaseRiskManager(ABC):
    """
    Basisklasse für Risk Management.

    Contract:
    - reset() wird zu Beginn eines Backtests aufgerufen
    - adjust_target_position() wird vor jeder Trade-Eröffnung aufgerufen
      und kann die Ziel-Position reduzieren oder auf 0 setzen
    """

    @abstractmethod
    def reset(self, start_equity: float | None = None) -> None:
        """
        Setzt den RiskManager für einen neuen Backtest zurück.

        Args:
            start_equity: Start-Kapital für den Backtest
        """
        raise NotImplementedError

    @abstractmethod
    def adjust_target_position(
        self,
        target_units: float,
        price: float,
        equity: float,
        timestamp: Any | None = None,
    ) -> float:
        """
        Passt die Ziel-Position basierend auf Risk-Limits an.

        Args:
            target_units: Von Strategie + PositionSizer vorgeschlagene Units
            price: Aktueller Preis
            equity: Aktuelle Equity
            timestamp: Optionaler Zeitstempel

        Returns:
            Angepasste Ziel-Position in Units (kann 0 sein wenn Risk-Limit erreicht)
        """
        raise NotImplementedError


class NoopRiskManager(BaseRiskManager):
    """
    Default RiskManager: Keine Anpassungen, gibt target_units unverändert zurück.

    Use Case: Minimales Risk-Management oder wenn andere Mechanismen genutzt werden.
    """

    def reset(self, start_equity: float | None = None) -> None:
        pass  # Nichts zu tun

    def adjust_target_position(
        self,
        target_units: float,
        price: float,
        equity: float,
        timestamp: Any | None = None,
    ) -> float:
        return target_units

    def __repr__(self) -> str:
        return "<NoopRiskManager()>"


@dataclass
class MaxDrawdownRiskManager(BaseRiskManager):
    """
    Stoppt Trading bei Erreichen eines maximalen Drawdowns.

    Beispiel:
    - max_drawdown = 0.25 (25%)
    - Start-Equity = 10.000 €
    - Peak-Equity erreicht 12.000 €
    - Bei Equity <= 9.000 € (25% unter Peak) wird Trading gestoppt

    Attributes:
        max_drawdown: Maximaler Drawdown als Dezimalzahl (0.25 = 25%)
    """

    max_drawdown: float = 0.25

    def __post_init__(self) -> None:
        self.peak_equity: float = 0.0
        self.trading_stopped: bool = False

    def reset(self, start_equity: float | None = None) -> None:
        """Setzt Peak-Equity und Trading-Status zurück."""
        self.peak_equity = start_equity if start_equity else 0.0
        self.trading_stopped = False

    def adjust_target_position(
        self,
        target_units: float,
        price: float,
        equity: float,
        timestamp: Any | None = None,
    ) -> float:
        """
        Prüft Drawdown und stoppt Trading bei Überschreitung.

        Args:
            target_units: Vorgeschlagene Position
            price: Aktueller Preis
            equity: Aktuelle Equity
            timestamp: Optional (für Logging)

        Returns:
            0.0 wenn Trading gestoppt, sonst target_units
        """
        # Peak-Equity aktualisieren
        if equity > self.peak_equity:
            self.peak_equity = equity

        # Drawdown berechnen
        if self.peak_equity > 0:
            current_drawdown = (self.peak_equity - equity) / self.peak_equity
        else:
            current_drawdown = 0.0

        # Prüfen ob Drawdown-Limit erreicht
        if current_drawdown >= self.max_drawdown:
            if not self.trading_stopped:
                self.trading_stopped = True
                # Optional: Logging
                # print(f"⚠️ MAX DRAWDOWN ERREICHT: {current_drawdown:.1%} >= {self.max_drawdown:.1%}")
                # print(f"   Trading gestoppt bei Equity={equity:.2f}, Peak={self.peak_equity:.2f}")
            return 0.0

        # Normaler Fall: keine Anpassung
        return target_units

    def __repr__(self) -> str:
        return f"<MaxDrawdownRiskManager(max_drawdown={self.max_drawdown:.1%})>"


@dataclass
class EquityFloorRiskManager(BaseRiskManager):
    """
    Stoppt Trading wenn Equity unter einen absoluten Floor fällt.

    Beispiel:
    - equity_floor = 5.000 €
    - Sobald Equity <= 5.000 € wird Trading gestoppt

    Attributes:
        equity_floor: Minimale Equity (absoluter Wert)
    """

    equity_floor: float = 5000.0

    def __post_init__(self) -> None:
        self.trading_stopped: bool = False

    def reset(self, start_equity: float | None = None) -> None:
        """Setzt Trading-Status zurück."""
        self.trading_stopped = False

    def adjust_target_position(
        self,
        target_units: float,
        price: float,
        equity: float,
        timestamp: Any | None = None,
    ) -> float:
        """
        Prüft Equity-Floor und stoppt Trading bei Unterschreitung.

        Args:
            target_units: Vorgeschlagene Position
            price: Aktueller Preis
            equity: Aktuelle Equity
            timestamp: Optional (für Logging)

        Returns:
            0.0 wenn Trading gestoppt, sonst target_units
        """
        # Prüfen ob Equity-Floor unterschritten
        if equity <= self.equity_floor:
            if not self.trading_stopped:
                self.trading_stopped = True
                # Optional: Logging
                # print(f"⚠️ EQUITY FLOOR ERREICHT: {equity:.2f} <= {self.equity_floor:.2f}")
                # print(f"   Trading gestoppt")
            return 0.0

        # Normaler Fall: keine Anpassung
        return target_units

    def __repr__(self) -> str:
        return f"<EquityFloorRiskManager(equity_floor={self.equity_floor:,.2f})>"


def build_risk_manager_from_config(
    cfg: Any,
    section: str = "risk",
) -> BaseRiskManager:
    """
    Fabrik-Funktion, die aus der Config einen passenden RiskManager baut.

    Args:
        cfg: Config-Objekt (PeakConfig oder kompatibles Dict-Interface)
        section: Config-Section für Risk Management

    Returns:
        BaseRiskManager-Instanz

    Erwartete Struktur in config.toml:

    [risk]
    type = "noop"               # oder "max_drawdown", "equity_floor"
    max_drawdown = 0.25         # nur für type="max_drawdown"
    equity_floor = 5000.0       # nur für type="equity_floor"

    Example:
        >>> from src.core.peak_config import load_config
        >>> cfg = load_config()
        >>> risk_mgr = build_risk_manager_from_config(cfg)
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

    if type_value == "max_drawdown":
        max_dd = float(get_fn(f"{section}.max_drawdown", 0.25))
        return MaxDrawdownRiskManager(max_drawdown=max_dd)

    if type_value == "equity_floor":
        floor = float(get_fn(f"{section}.equity_floor", 5000.0))
        return EquityFloorRiskManager(equity_floor=floor)

    # Fallback / Default
    return NoopRiskManager()
