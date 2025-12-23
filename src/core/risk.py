# src/core/risk.py
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Optional, List, Dict
import pandas as pd
import numpy as np
import logging

logger = logging.getLogger(__name__)


class BaseRiskManager(ABC):
    """
    Basisklasse für Risk Management.

    Contract:
    - reset() wird zu Beginn eines Backtests aufgerufen
    - adjust_target_position() wird vor jeder Trade-Eröffnung aufgerufen
      und kann die Ziel-Position reduzieren oder auf 0 setzen
    """

    @abstractmethod
    def reset(self, start_equity: Optional[float] = None) -> None:
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
        timestamp: Optional[Any] = None,
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

    def reset(self, start_equity: Optional[float] = None) -> None:
        pass  # Nichts zu tun

    def adjust_target_position(
        self,
        target_units: float,
        price: float,
        equity: float,
        timestamp: Optional[Any] = None,
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

    def reset(self, start_equity: Optional[float] = None) -> None:
        """Setzt Peak-Equity und Trading-Status zurück."""
        self.peak_equity = start_equity if start_equity else 0.0
        self.trading_stopped = False

    def adjust_target_position(
        self,
        target_units: float,
        price: float,
        equity: float,
        timestamp: Optional[Any] = None,
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

    def reset(self, start_equity: Optional[float] = None) -> None:
        """Setzt Trading-Status zurück."""
        self.trading_stopped = False

    def adjust_target_position(
        self,
        target_units: float,
        price: float,
        equity: float,
        timestamp: Optional[Any] = None,
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


@dataclass
class PortfolioVaRStressRiskManager(BaseRiskManager):
    """
    Advanced Risk Manager: Portfolio-Level VaR/CVaR + Stress-Testing.

    Features:
    - Portfolio Exposure Limits (Gross/Net)
    - Position Weight Limits
    - VaR/CVaR Limits (Historical)
    - Rolling-Window für Returns-Berechnung
    - Circuit Breaker bei HARD Breaches

    Attributes:
        alpha: VaR/CVaR Konfidenzniveau (z.B. 0.05 = 95% VaR)
        window: Rolling-Window für Returns (z.B. 252 = 1 Jahr)
        max_gross_exposure: Max Gross Exposure als Fraction of Equity (z.B. 1.5)
        max_net_exposure: Max Abs(Net Exposure) als Fraction of Equity (z.B. 1.0)
        max_position_weight: Max Weight einer Position (z.B. 0.35)
        max_var: Max VaR als Fraction of Equity (z.B. 0.08)
        max_cvar: Max CVaR als Fraction of Equity (z.B. 0.12)

    Example:
        >>> manager = PortfolioVaRStressRiskManager(
        ...     alpha=0.05,
        ...     window=252,
        ...     max_gross_exposure=1.5,
        ...     max_var=0.08
        ... )
    """

    alpha: float = 0.05
    window: int = 252
    max_gross_exposure: Optional[float] = None
    max_net_exposure: Optional[float] = None
    max_position_weight: Optional[float] = None
    max_var: Optional[float] = None
    max_cvar: Optional[float] = None

    def __post_init__(self) -> None:
        # Tracking-Strukturen
        self.returns_history: List[float] = []
        self.trading_stopped: bool = False
        self.breach_count: int = 0

        # Lazy-Import für Risk-Layer (vermeidet zirkuläre Imports)
        from ..risk import RiskLimitsV2, RiskEnforcer

        self.limits = RiskLimitsV2(
            max_gross_exposure=self.max_gross_exposure,
            max_net_exposure=self.max_net_exposure,
            max_position_weight=self.max_position_weight,
            max_var=self.max_var,
            max_cvar=self.max_cvar,
            alpha=self.alpha,
            window=self.window,
        )
        self.enforcer = RiskEnforcer()

    def reset(self, start_equity: Optional[float] = None) -> None:
        """Setzt Risk-Manager für neuen Backtest zurück."""
        self.returns_history.clear()
        self.trading_stopped = False
        self.breach_count = 0

    def adjust_target_position(
        self,
        target_units: float,
        price: float,
        equity: float,
        timestamp: Optional[Any] = None,
        **kwargs: Any,
    ) -> float:
        """
        Passt Ziel-Position basierend auf VaR/Exposure-Limits an.

        Args:
            target_units: Vorgeschlagene Position
            price: Aktueller Preis
            equity: Aktuelle Equity
            timestamp: Optional Zeitstempel
            **kwargs: Zusätzliche Daten:
                - positions: List[PositionSnapshot] (optional)
                - last_return: float (letzter Return für History)

        Returns:
            Angepasste Position (0.0 bei HALT)
        """
        # Wenn bereits gestoppt, blockiere alle Trades
        if self.trading_stopped:
            return 0.0

        # Update Returns-History
        if "last_return" in kwargs:
            self._update_returns_history(kwargs["last_return"])

        # Erstelle Portfolio-Snapshot
        from ..risk import PositionSnapshot, PortfolioSnapshot

        positions = kwargs.get("positions", [])
        if not isinstance(positions, list):
            positions = []

        # Füge geplante Position hinzu (wenn target_units != 0)
        if target_units != 0:
            symbol = kwargs.get("symbol", "UNKNOWN")
            planned_pos = PositionSnapshot(
                symbol=symbol,
                units=target_units,
                price=price,
                timestamp=timestamp,
            )
            positions = positions + [planned_pos]

        snapshot = PortfolioSnapshot(
            equity=equity,
            positions=positions,
            timestamp=timestamp,
        )

        # Returns für VaR-Berechnung (Rolling Window)
        returns_series = self._get_returns_series()

        # Evaluiere Limits
        decision = self.enforcer.evaluate_portfolio(
            snapshot=snapshot,
            returns=returns_series if len(returns_series) > 0 else None,
            limits=self.limits,
            alpha=self.alpha,
        )

        # Entscheidung verarbeiten
        if not decision.allowed:
            self.trading_stopped = True
            self.breach_count += len(decision.breaches)

            if logger.isEnabledFor(logging.WARNING):
                logger.warning(f"⚠️  RISK HALT at {timestamp}: {decision.get_breach_summary()}")

            return 0.0

        # Warnings loggen (aber erlauben)
        if decision.breaches:
            self.breach_count += len(decision.breaches)
            if logger.isEnabledFor(logging.INFO):
                logger.info(f"Risk warnings: {len(decision.breaches)} breaches (allowed)")

        return target_units

    def _update_returns_history(self, last_return: float) -> None:
        """Aktualisiert Returns-History (Rolling Window)."""
        self.returns_history.append(last_return)

        # Beschränke auf Window
        if len(self.returns_history) > self.window:
            self.returns_history = self.returns_history[-self.window :]

    def _get_returns_series(self) -> pd.Series:
        """Gibt Returns-History als Series zurück."""
        if not self.returns_history:
            return pd.Series(dtype=float)
        return pd.Series(self.returns_history)

    def __repr__(self) -> str:
        return (
            f"<PortfolioVaRStressRiskManager("
            f"alpha={self.alpha:.2f}, "
            f"window={self.window}, "
            f"max_var={self.max_var}, "
            f"max_gross={self.max_gross_exposure})>"
        )


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
    type = "noop"                     # oder "max_drawdown", "equity_floor", "portfolio_var_stress"
    max_drawdown = 0.25               # für type="max_drawdown"
    equity_floor = 5000.0             # für type="equity_floor"

    # Für type="portfolio_var_stress":
    alpha = 0.05
    window = 252
    [risk.limits]
    max_gross_exposure = 1.5
    max_net_exposure = 1.0
    max_position_weight = 0.35
    max_var = 0.08
    max_cvar = 0.12

    Example:
        >>> from src.core.peak_config import load_config
        >>> cfg = load_config()
        >>> risk_mgr = build_risk_manager_from_config(cfg)
    """

    # Config-Zugriff: Unterstützt PeakConfig und Dict
    if hasattr(cfg, "get"):
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

    if type_value == "portfolio_var_stress":
        # VaR-Layer v1 Config
        alpha = float(get_fn(f"{section}.alpha", 0.05))
        window = int(get_fn(f"{section}.window", 252))

        # Limits (optional)
        max_gross = get_fn(f"{section}.limits.max_gross_exposure", None)
        max_net = get_fn(f"{section}.limits.max_net_exposure", None)
        max_pos_weight = get_fn(f"{section}.limits.max_position_weight", None)
        max_var = get_fn(f"{section}.limits.max_var", None)
        max_cvar = get_fn(f"{section}.limits.max_cvar", None)

        # Konvertiere zu float wenn vorhanden
        if max_gross is not None:
            max_gross = float(max_gross)
        if max_net is not None:
            max_net = float(max_net)
        if max_pos_weight is not None:
            max_pos_weight = float(max_pos_weight)
        if max_var is not None:
            max_var = float(max_var)
        if max_cvar is not None:
            max_cvar = float(max_cvar)

        return PortfolioVaRStressRiskManager(
            alpha=alpha,
            window=window,
            max_gross_exposure=max_gross,
            max_net_exposure=max_net,
            max_position_weight=max_pos_weight,
            max_var=max_var,
            max_cvar=max_cvar,
        )

    # Fallback / Default
    return NoopRiskManager()
