"""
Peak_Trade Backtest Engine mit Risk-Layer Integration
=======================================================
Bar-für-Bar-Backtest mit vollständigem Risk-Management.

Features:
- Position Sizing via PositionSizer
- Risk Limits via RiskLimits (Drawdown, Daily Loss, Position Size)
- Stop-Loss-Management
- Trade-Tracking mit PnL-Berechnung
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass
from datetime import datetime
import logging

from ..core import get_config
from ..risk import (
    PositionSizer,
    PositionSizerConfig,
    RiskLimits,
    RiskLimitsConfig,
    PositionRequest,
    calc_position_size,
)

logger = logging.getLogger(__name__)


@dataclass
class Trade:
    """Einzelner Trade mit allen Details."""
    entry_time: datetime
    entry_price: float
    size: float
    stop_price: float
    exit_time: Optional[datetime] = None
    exit_price: Optional[float] = None
    pnl: Optional[float] = None
    pnl_pct: Optional[float] = None
    exit_reason: str = ""


@dataclass
class BacktestResult:
    """Backtest-Ergebnis mit Stats und Trades."""
    equity_curve: pd.Series
    trades: List[Trade]
    stats: Dict[str, float]
    mode: str
    strategy_name: str = ""
    blocked_trades: int = 0  # Anzahl blockierter Trades durch Risk-Limits


class BacktestEngine:
    """
    Backtest-Engine mit vollständiger Risk-Layer-Integration.

    Usage:
        >>> from src.risk import PositionSizer, PositionSizerConfig, RiskLimits, RiskLimitsConfig
        >>>
        >>> # Optional: Custom Risk-Config
        >>> position_sizer = PositionSizer(PositionSizerConfig(risk_pct=1.0))
        >>> risk_limits = RiskLimits(RiskLimitsConfig(max_drawdown_pct=20.0))
        >>>
        >>> engine = BacktestEngine(position_sizer=position_sizer, risk_limits=risk_limits)
        >>> result = engine.run_realistic(df, strategy_signal_fn, strategy_params)
        >>> print(f"Sharpe: {result.stats['sharpe']:.2f}")
    """

    def __init__(
        self,
        position_sizer: Optional[PositionSizer] = None,
        risk_limits: Optional[RiskLimits] = None,
    ):
        """
        Initialisiert Backtest-Engine mit Risk-Layer.

        Args:
            position_sizer: PositionSizer-Instanz (default: Default-Config)
            risk_limits: RiskLimits-Instanz (default: Default-Config)
        """
        self.config = get_config()

        # Risk-Layer initialisieren
        self.position_sizer = position_sizer or PositionSizer(PositionSizerConfig())
        self.risk_limits = risk_limits or RiskLimits(RiskLimitsConfig())

        # Tracking-Strukturen
        self.equity_curve: List[float] = []
        self.daily_returns_pct: Dict[pd.Timestamp, List[float]] = {}

    def _register_trade_pnl(self, trade_dt: pd.Timestamp, pnl_pct: float) -> None:
        """
        Registriert Trade-PnL für Daily-Loss-Tracking.

        Args:
            trade_dt: Zeitstempel des Trades
            pnl_pct: PnL in Prozent (z.B. -1.5 für -1.5%)
        """
        day = trade_dt.normalize()
        self.daily_returns_pct.setdefault(day, []).append(pnl_pct)

    def _get_today_returns(self, current_dt: pd.Timestamp) -> List[float]:
        """
        Holt alle Returns des aktuellen Tages.

        Args:
            current_dt: Aktueller Zeitstempel

        Returns:
            Liste von Returns (in %) für den Tag
        """
        day = current_dt.normalize()
        return self.daily_returns_pct.get(day, [])

    def _check_risk_limits(
        self,
        current_capital: float,
        proposed_position_value: float,
        current_dt: pd.Timestamp,
    ) -> bool:
        """
        Prüft alle Risk-Limits vor Trade-Eröffnung.

        Args:
            current_capital: Aktuelles Eigenkapital
            proposed_position_value: Geplanter Positionswert
            current_dt: Zeitstempel

        Returns:
            True = Trade erlaubt, False = Trade blockiert
        """
        # 1. Equity-Curve für Drawdown-Check
        equity_curve = self.equity_curve if self.equity_curve else [current_capital]

        # 2. Heutige Returns für Daily-Loss-Check
        returns_today = self._get_today_returns(current_dt)

        # 3. Kombinierter Check
        ok = self.risk_limits.check_all(
            equity_curve=equity_curve,
            returns_today_pct=returns_today,
            new_position_nominal=proposed_position_value,
            capital=current_capital,
        )

        if not ok:
            logger.debug(
                f"Trade blockiert bei {current_dt}: "
                f"Equity={current_capital:.2f}, Position={proposed_position_value:.2f}"
            )

        return ok

    def run_realistic(
        self,
        df: pd.DataFrame,
        strategy_signal_fn: Callable,
        strategy_params: Dict,
    ) -> BacktestResult:
        """
        Realistischer Backtest mit vollständigem Risk-Management.

        Workflow:
        1. Signale generieren via strategy_signal_fn
        2. Bar-für-Bar durchlaufen
        3. Stop-Loss-Checks
        4. Risk-Limit-Checks vor jedem Trade
        5. Position-Sizing via PositionSizer
        6. Trade-Execution mit PnL-Tracking

        Args:
            df: OHLCV-DataFrame (DatetimeIndex, Spalten: open, high, low, close, volume)
            strategy_signal_fn: Funktion(df, params) -> pd.Series mit Signalen (1=Buy, -1=Sell, 0=Hold)
            strategy_params: Parameter-Dict für Strategie (inkl. stop_pct)

        Returns:
            BacktestResult mit Equity-Curve, Trades, Stats

        Example:
            >>> from src.strategies.ma_crossover import generate_signals
            >>>
            >>> engine = BacktestEngine()
            >>> result = engine.run_realistic(
            ...     df=df,
            ...     strategy_signal_fn=generate_signals,
            ...     strategy_params={'fast_period': 10, 'slow_period': 30, 'stop_pct': 0.02}
            ... )
        """
        # Init
        equity = self.config.backtest.initial_cash
        self.equity_curve = [equity]
        self.daily_returns_pct = {}
        trades: List[Trade] = []
        blocked_trades = 0

        current_trade: Optional[Trade] = None
        stop_pct = strategy_params.get("stop_pct", 0.02)

        # Signale generieren
        signals = strategy_signal_fn(df, strategy_params)

        # Bar-für-Bar-Loop
        for i in range(len(df)):
            bar = df.iloc[i]
            signal = signals.iloc[i]
            trade_dt = bar.name  # Timestamp

            # 1. STOP-LOSS CHECK (höchste Priorität!)
            if current_trade is not None:
                if bar["low"] <= current_trade.stop_price:
                    # Stop wurde getroffen
                    current_trade.exit_time = trade_dt
                    current_trade.exit_price = current_trade.stop_price
                    current_trade.pnl = current_trade.size * (
                        current_trade.exit_price - current_trade.entry_price
                    )
                    current_trade.pnl_pct = (
                        (current_trade.exit_price - current_trade.entry_price)
                        / current_trade.entry_price
                        * 100.0
                    )
                    current_trade.exit_reason = "stop_loss"

                    equity += current_trade.pnl
                    trades.append(current_trade)

                    # Daily Returns registrieren
                    self._register_trade_pnl(trade_dt, current_trade.pnl_pct)

                    current_trade = None

            # 2. SIGNAL HANDLING
            if signal == 1 and current_trade is None:
                # LONG ENTRY
                entry_price = bar["close"]
                stop_price = entry_price * (1 - stop_pct)
                stop_distance = abs(entry_price - stop_price)

                # Position Sizing
                req = PositionRequest(
                    equity=equity,
                    entry_price=entry_price,
                    stop_price=stop_price,
                    risk_per_trade=self.config.risk.risk_per_trade,
                )

                pos_result = calc_position_size(
                    req,
                    max_position_pct=self.config.risk.max_position_size,
                    min_position_value=self.config.risk.min_position_value,
                    min_stop_distance=self.config.risk.min_stop_distance,
                )

                if pos_result.rejected:
                    # Position-Sizing hat Trade blockiert
                    logger.debug(f"Position Sizing blockiert Trade: {pos_result.reason}")
                    blocked_trades += 1
                else:
                    proposed_position_value = pos_result.value

                    # Risk-Limits-Check
                    risk_ok = self._check_risk_limits(
                        current_capital=equity,
                        proposed_position_value=proposed_position_value,
                        current_dt=trade_dt,
                    )

                    if risk_ok:
                        # Trade eröffnen
                        current_trade = Trade(
                            entry_time=trade_dt,
                            entry_price=entry_price,
                            size=pos_result.size,
                            stop_price=stop_price,
                        )
                    else:
                        # Risk-Limits haben Trade blockiert
                        blocked_trades += 1

            elif signal == -1 and current_trade is not None:
                # EXIT
                current_trade.exit_time = trade_dt
                current_trade.exit_price = bar["close"]
                current_trade.pnl = current_trade.size * (
                    current_trade.exit_price - current_trade.entry_price
                )
                current_trade.pnl_pct = (
                    (current_trade.exit_price - current_trade.entry_price)
                    / current_trade.entry_price
                    * 100.0
                )
                current_trade.exit_reason = "signal"

                equity += current_trade.pnl
                trades.append(current_trade)

                # Daily Returns registrieren
                self._register_trade_pnl(trade_dt, current_trade.pnl_pct)

                current_trade = None

            # Equity-Curve aktualisieren
            self.equity_curve.append(equity)

        # Offene Position am Ende schließen
        if current_trade is not None:
            last_bar = df.iloc[-1]
            current_trade.exit_time = last_bar.name
            current_trade.exit_price = last_bar["close"]
            current_trade.pnl = current_trade.size * (
                current_trade.exit_price - current_trade.entry_price
            )
            current_trade.pnl_pct = (
                (current_trade.exit_price - current_trade.entry_price)
                / current_trade.entry_price
                * 100.0
            )
            current_trade.exit_reason = "end_of_data"

            equity += current_trade.pnl
            trades.append(current_trade)

            # Daily Returns registrieren
            self._register_trade_pnl(last_bar.name, current_trade.pnl_pct)

        # Stats berechnen
        from .stats import compute_basic_stats, compute_sharpe_ratio, compute_trade_stats

        equity_series = pd.Series(self.equity_curve, index=[df.index[0]] + list(df.index))
        basic_stats = compute_basic_stats(equity_series)
        sharpe = compute_sharpe_ratio(equity_series)
        trade_stats = compute_trade_stats([t.__dict__ for t in trades])

        stats = {
            **basic_stats,
            "sharpe": sharpe,
            "total_trades": trade_stats.total_trades,
            "win_rate": trade_stats.win_rate,
            "profit_factor": trade_stats.profit_factor,
        }

        logger.info(
            f"Backtest abgeschlossen: {len(trades)} Trades, {blocked_trades} blockiert"
        )

        return BacktestResult(
            equity_curve=equity_series,
            trades=trades,
            stats=stats,
            mode="realistic_with_risk_management",
            strategy_name="",
            blocked_trades=blocked_trades,
        )

    def run_vectorized(
        self, df: pd.DataFrame, strategy_signal_fn: Callable, strategy_params: Dict
    ) -> BacktestResult:
        """
        Vectorized Backtest: Schnell, aber OHNE Risk-Management.

        ⚠️ WARNUNG: NICHT für Live-Trading-Entscheidungen verwenden!

        - Kein Position Sizing (immer 100% investiert)
        - Kein Stop-Loss
        - Keine Risk-Limits
        - Synthetische PnL-Berechnung

        Use Case: Schnelle Parameter-Tests, erste Experimente

        Args:
            df: OHLCV-DataFrame
            strategy_signal_fn: Funktion die Signale generiert
            strategy_params: Parameter für Strategie

        Returns:
            BacktestResult (mit WARNING in mode)
        """
        signals = strategy_signal_fn(df, strategy_params)

        # Einfache Return-Berechnung
        returns = df["close"].pct_change()

        # Signal-basierte Returns (nur bei Position)
        position = signals.replace({-1: 0}).fillna(method="ffill").fillna(0)
        strategy_returns = position.shift(1) * returns

        # Equity berechnen
        equity = self.config.backtest.initial_cash * (1 + strategy_returns.cumsum())

        # Dummy-Stats
        from .stats import compute_basic_stats, compute_sharpe_ratio

        basic_stats = compute_basic_stats(equity)
        sharpe = compute_sharpe_ratio(equity)

        stats = {
            **basic_stats,
            "sharpe": sharpe,
            "total_trades": 0,  # Nicht verfügbar im vectorized mode
            "win_rate": 0.0,
            "profit_factor": 0.0,
        }

        return BacktestResult(
            equity_curve=equity,
            trades=[],  # Keine echten Trades
            stats=stats,
            mode="vectorized (WARNING: NO RISK MANAGEMENT!)",
            strategy_name="",
        )
