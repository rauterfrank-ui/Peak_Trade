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

import logging
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

import numpy as np
import pandas as pd

from ..core.config_registry import (
    get_active_strategies,
    get_config,
    get_strategy_config,
)
from ..core.peak_config import load_config
from ..core.position_sizing import BasePositionSizer
from ..core.regime import (
    build_regime_config_from_config,
    label_combined_regime,
    label_trend_regime,
    label_vol_regime,
    summarize_regime_distribution,
)
from ..core.risk import BaseRiskManager
from ..execution.pipeline import ExecutionPipeline, ExecutionPipelineConfig, SignalEvent

# Order-Layer Imports (Phase 16)
from ..orders.base import OrderExecutionResult
from ..orders.paper import PaperMarketContext
from ..risk import (
    PositionRequest,
    PositionSizer,
    PositionSizerConfig,
    RiskLimits,
    RiskLimitsConfig,
    calc_position_size,
)
from ..strategies import load_strategy
from . import stats as stats_mod
from .result import BacktestResult

logger = logging.getLogger(__name__)


@dataclass
class Trade:
    """Einzelner Trade mit allen Details."""
    entry_time: datetime
    entry_price: float
    size: float
    stop_price: float
    exit_time: datetime | None = None
    exit_price: float | None = None
    pnl: float | None = None
    pnl_pct: float | None = None
    exit_reason: str = ""


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
        position_sizer: PositionSizer | None = None,
        risk_limits: RiskLimits | None = None,
        core_position_sizer: BasePositionSizer | None = None,
        risk_manager: BaseRiskManager | None = None,
        use_execution_pipeline: bool = True,
        log_executions: bool = False,
        # Backward-compatibility alias
        use_order_layer: bool | None = None,
    ):
        """
        Initialisiert Backtest-Engine mit Risk-Layer.

        Args:
            position_sizer: PositionSizer-Instanz (default: Default-Config)
            risk_limits: RiskLimits-Instanz (default: Default-Config)
            core_position_sizer: Optional BasePositionSizer für signal-to-units conversion
            risk_manager: Optional BaseRiskManager für Drawdown/Equity-Floor Management
            use_execution_pipeline: Wenn True, wird die ExecutionPipeline verwendet.
                            Dies aktiviert die Order-basierte Simulation mit OrderRequest/OrderFill.
                            Default: True (neuer Modus mit ExecutionPipeline)
            log_executions: Wenn True, werden Execution-Summaries gesammelt und in
                           _execution_logs gespeichert. Default: False
            use_order_layer: DEPRECATED - Alias fuer use_execution_pipeline (backward compat)
        """
        self.config = get_config()

        # Risk-Layer initialisieren
        self.position_sizer = position_sizer or PositionSizer(PositionSizerConfig())
        self.risk_limits = risk_limits or RiskLimits(RiskLimitsConfig())

        # Core Position Sizer (optional, für neue OOP-API)
        self.core_position_sizer = core_position_sizer

        # Risk Manager (optional, für neue OOP-API)
        self.risk_manager = risk_manager

        # ExecutionPipeline Flag (Phase 16B)
        # Backward-compat: use_order_layer überschreibt use_execution_pipeline
        if use_order_layer is not None:
            logger.warning(
                "use_order_layer ist deprecated, nutze use_execution_pipeline stattdessen"
            )
            self.use_execution_pipeline = use_order_layer
        else:
            self.use_execution_pipeline = use_execution_pipeline

        # Alias für backward compat
        self.use_order_layer = self.use_execution_pipeline

        # Execution Logging Flag (Phase 16B)
        self.log_executions = log_executions

        # Tracking-Strukturen
        self.equity_curve: list[float] = []
        self.daily_returns_pct: dict[pd.Timestamp, list[float]] = {}

        # ExecutionPipeline Tracking (Phase 16B)
        self.execution_results: list[OrderExecutionResult] = []
        self._execution_logs: list[dict[str, Any]] = []

        # ExecutionPipeline-Instanz (wird bei Bedarf erstellt)
        self.execution_pipeline: ExecutionPipeline | None = None

        # DataFrame-Referenz für Regime-Berechnung
        self.data: pd.DataFrame | None = None

    def _register_trade_pnl(self, trade_dt: pd.Timestamp, pnl_pct: float) -> None:
        """
        Registriert Trade-PnL für Daily-Loss-Tracking.

        Args:
            trade_dt: Zeitstempel des Trades
            pnl_pct: PnL in Prozent (z.B. -1.5 für -1.5%)
        """
        day = trade_dt.normalize()
        self.daily_returns_pct.setdefault(day, []).append(pnl_pct)

    def _get_today_returns(self, current_dt: pd.Timestamp) -> list[float]:
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

    def _init_execution_pipeline(
        self,
        symbol: str,
        initial_price: float,
        fee_bps: float = 0.0,
        slippage_bps: float = 0.0,
    ) -> ExecutionPipeline:
        """
        Initialisiert die ExecutionPipeline fuer den Backtest.

        Args:
            symbol: Trading-Symbol (z.B. "BTC/EUR")
            initial_price: Startpreis fuer den Marktkontext
            fee_bps: Fees in Basispunkten
            slippage_bps: Slippage in Basispunkten

        Returns:
            Initialisierte ExecutionPipeline
        """
        market_ctx = PaperMarketContext(
            prices={symbol: initial_price},
            fee_bps=fee_bps,
            slippage_bps=slippage_bps,
            base_currency="EUR",
        )

        pipeline_config = ExecutionPipelineConfig(
            log_executions=self.log_executions,
            generate_client_ids=True,
            default_order_type="market",
        )

        self.execution_pipeline = ExecutionPipeline.for_paper(market_ctx, pipeline_config)
        return self.execution_pipeline

    def _log_execution_summary(
        self,
        run_id: str,
        symbol: str,
        summary: dict[str, Any],
    ) -> None:
        """
        Speichert Execution-Summary in _execution_logs.

        Args:
            run_id: Eindeutige Run-ID
            symbol: Trading-Symbol
            summary: Summary-Dict von ExecutionPipeline.get_execution_summary()
        """
        log_entry = {
            "run_id": run_id,
            "symbol": symbol,
            "timestamp": datetime.now().isoformat(),
            **summary,
        }
        self._execution_logs.append(log_entry)

        if self.log_executions:
            logger.info(
                f"[EXECUTION LOG] {run_id}/{symbol}: "
                f"{summary.get('total_orders', 0)} orders, "
                f"{summary.get('filled_orders', 0)} filled, "
                f"notional={summary.get('total_notional', 0):.2f}"
            )

    def get_execution_logs(self) -> list[dict[str, Any]]:
        """
        Gibt alle gesammelten Execution-Logs zurueck.

        Returns:
            Liste von Execution-Log-Eintraegen
        """
        return self._execution_logs.copy()

    def clear_execution_logs(self) -> None:
        """Loescht alle Execution-Logs."""
        self._execution_logs.clear()

    def run_realistic(
        self,
        df: pd.DataFrame,
        strategy_signal_fn: Callable,
        strategy_params: dict,
        symbol: str = "BTC/EUR",
        fee_bps: float = 0.0,
        slippage_bps: float = 0.0,
    ) -> BacktestResult:
        """
        Realistischer Backtest mit vollständigem Risk-Management.

        Workflow (Legacy, use_execution_pipeline=False):
        1. Signale generieren via strategy_signal_fn
        2. Bar-für-Bar durchlaufen
        3. Stop-Loss-Checks
        4. Risk-Limit-Checks vor jedem Trade
        5. Position-Sizing via PositionSizer
        6. Trade-Execution mit PnL-Tracking

        Workflow (ExecutionPipeline, use_execution_pipeline=True):
        1. Signale generieren via strategy_signal_fn
        2. ExecutionPipeline mit PaperOrderExecutor initialisieren
        3. Signal-Wechsel erkennen und Orders via Pipeline ausfuehren
        4. PnL und Equity aus Fills berechnen

        Args:
            df: OHLCV-DataFrame (DatetimeIndex, Spalten: open, high, low, close, volume)
            strategy_signal_fn: Funktion(df, params) -> pd.Series mit Signalen (1=Buy, -1=Sell, 0=Hold)
            strategy_params: Parameter-Dict für Strategie (inkl. stop_pct)
            symbol: Trading-Symbol (default: "BTC/EUR") - nur bei ExecutionPipeline verwendet
            fee_bps: Fees in Basispunkten (default: 0.0) - nur bei ExecutionPipeline verwendet
            slippage_bps: Slippage in Basispunkten (default: 0.0) - nur bei ExecutionPipeline verwendet

        Returns:
            BacktestResult mit Equity-Curve, Trades, Stats

        Example:
            >>> from src.strategies.ma_crossover import generate_signals
            >>>
            >>> # Mit ExecutionPipeline (Default)
            >>> engine = BacktestEngine(use_execution_pipeline=True)
            >>> result = engine.run_realistic(
            ...     df=df,
            ...     strategy_signal_fn=generate_signals,
            ...     strategy_params={'fast_period': 10, 'slow_period': 30},
            ...     symbol="BTC/EUR",
            ...     fee_bps=10.0,
            ... )
            >>>
            >>> # Legacy-Modus (ohne ExecutionPipeline)
            >>> engine = BacktestEngine(use_execution_pipeline=False)
            >>> result = engine.run_realistic(
            ...     df=df,
            ...     strategy_signal_fn=generate_signals,
            ...     strategy_params={'fast_period': 10, 'slow_period': 30, 'stop_pct': 0.02}
            ... )
        """
        # Dispatch: ExecutionPipeline oder Legacy-Pfad
        if self.use_execution_pipeline:
            return self._run_with_execution_pipeline(
                df=df,
                strategy_signal_fn=strategy_signal_fn,
                strategy_params=strategy_params,
                symbol=symbol,
                fee_bps=fee_bps,
                slippage_bps=slippage_bps,
            )

        # Legacy-Pfad (ohne ExecutionPipeline)
        # Init
        equity = self.config["backtest"]["initial_cash"]
        self.equity_curve = [equity]
        self.daily_returns_pct = {}
        trades: list[Trade] = []
        blocked_trades = 0

        # DataFrame speichern für spätere Regime-Berechnung
        self.data = df

        current_trade: Trade | None = None
        stop_pct = strategy_params.get("stop_pct", 0.02)

        # Risk Manager initialisieren
        if self.risk_manager is not None:
            self.risk_manager.reset(start_equity=equity)

        # Signale generieren
        signals = strategy_signal_fn(df, strategy_params)

        # Bar-für-Bar-Loop
        for i in range(len(df)):
            bar = df.iloc[i]
            signal = signals.iloc[i]
            trade_dt = bar.name  # Timestamp

            # 1. STOP-LOSS CHECK (höchste Priorität!)
            if current_trade is not None and bar["low"] <= current_trade.stop_price:
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
                abs(entry_price - stop_price)

                # Position Sizing
                # If core_position_sizer is set, use it to convert signal to target units
                if self.core_position_sizer is not None:
                    # New OOP API: get_target_position returns units directly
                    target_units = self.core_position_sizer.get_target_position(
                        signal=int(signal),
                        price=entry_price,
                        equity=equity
                    )

                    # Risk Manager: Adjust target position (kann auf 0 reduzieren)
                    if self.risk_manager is not None:
                        target_units = self.risk_manager.adjust_target_position(
                            target_units=target_units,
                            price=entry_price,
                            equity=equity,
                            timestamp=trade_dt
                        )

                    # Calculate position value and size
                    position_value = abs(target_units) * entry_price
                    position_size = abs(target_units)

                    # Simple validation
                    rejected = False
                    reason = ""

                    # Check if RiskManager blocked trade (target_units = 0)
                    if target_units == 0:
                        rejected = True
                        reason = "Risk Manager stopped trading (Drawdown/Equity-Floor reached)"

                    # Check minimum position value
                    min_pos_val = self.config["risk"].get("min_position_value", 50.0)
                    if position_value < min_pos_val:
                        rejected = True
                        reason = f"Position value {position_value:.2f} < minimum {min_pos_val:.2f}"

                    # Check maximum position size
                    max_pos_pct = self.config["risk"].get("max_position_size", 0.25)
                    if position_value > equity * max_pos_pct:
                        rejected = True
                        reason = f"Position {position_value:.2f} > max {equity * max_pos_pct:.2f}"

                    if rejected:
                        logger.debug(f"Core Position Sizing blockiert Trade: {reason}")
                        blocked_trades += 1
                    else:
                        proposed_position_value = position_value

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
                                size=position_size,
                                stop_price=stop_price,
                            )
                        else:
                            # Risk-Limits haben Trade blockiert
                            blocked_trades += 1
                else:
                    # Old API: use legacy PositionSizer from risk module
                    req = PositionRequest(
                        equity=equity,
                        entry_price=entry_price,
                        stop_price=stop_price,
                        risk_per_trade=self.config["risk"]["risk_per_trade"],
                    )

                    pos_result = calc_position_size(
                        req,
                        max_position_pct=self.config["risk"]["max_position_size"],
                        min_position_value=self.config["risk"]["min_position_value"],
                        min_stop_distance=self.config["risk"]["min_stop_distance"],
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
        equity_series = pd.Series(self.equity_curve, index=[df.index[0], *list(df.index)])

        # Drawdown berechnen
        drawdown_series = stats_mod.compute_drawdown(equity_series)

        # Basic Stats (inkl. CAGR, Sharpe)
        basic_stats = stats_mod.compute_basic_stats(equity_series)

        # Trade Stats
        from .stats import compute_trade_stats
        trade_stats = compute_trade_stats([t.__dict__ for t in trades])

        stats = {
            **basic_stats,
            "total_trades": trade_stats.total_trades,
            "win_rate": trade_stats.win_rate,
            "profit_factor": trade_stats.profit_factor,
            "blocked_trades": blocked_trades,
        }

        # Trades als DataFrame für neuen BacktestResult
        if trades:
            trades_df = pd.DataFrame([t.__dict__ for t in trades])
        else:
            trades_df = None

        # Regime-Infos berechnen (optional, falls Config verfügbar)
        regime_meta: dict[str, Any] = {}
        try:
            peak_cfg = load_config("config.toml")
            regime_cfg = build_regime_config_from_config(peak_cfg)

            # Regime-Labels berechnen
            trend_labels = label_trend_regime(self.data, regime_cfg)
            vol_labels = label_vol_regime(self.data, regime_cfg)
            combined_labels = label_combined_regime(trend_labels, vol_labels)

            # Verteilung berechnen
            dist = summarize_regime_distribution(combined_labels)

            regime_meta = {
                "regime_distribution": dist,
                "regime_config": regime_cfg.to_dict(),
            }

            logger.debug(f"Regime-Verteilung: {dist}")
        except Exception as e:
            logger.debug(f"Regime-Berechnung fehlgeschlagen: {e}")
            # Kein Fehler werfen, einfach ohne Regime-Infos fortfahren

        logger.info(
            f"Backtest abgeschlossen: {len(trades)} Trades, {blocked_trades} blockiert"
        )

        # Metadata zusammenführen
        metadata = {
            "mode": "realistic_with_risk_management",
            "strategy_name": "",
            "blocked_trades": blocked_trades,
        }
        metadata.update(regime_meta)

        return BacktestResult(
            equity_curve=equity_series,
            drawdown=drawdown_series,
            trades=trades_df,
            stats=stats,
            metadata=metadata,
        )

    def run_vectorized(
        self, df: pd.DataFrame, strategy_signal_fn: Callable, strategy_params: dict
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
        position = signals.replace({-1: 0}).ffill().fillna(0)
        strategy_returns = position.shift(1) * returns

        # Equity berechnen
        equity = self.config["backtest"]["initial_cash"] * (1 + strategy_returns.cumsum())

        # Drawdown berechnen
        drawdown_series = stats_mod.compute_drawdown(equity)

        # Stats berechnen
        basic_stats = stats_mod.compute_basic_stats(equity)

        stats = {
            **basic_stats,
            "total_trades": 0,  # Nicht verfügbar im vectorized mode
            "win_rate": 0.0,
            "profit_factor": 0.0,
        }

        return BacktestResult(
            equity_curve=equity,
            drawdown=drawdown_series,
            trades=None,  # Keine echten Trades
            stats=stats,
            metadata={
                "mode": "vectorized (WARNING: NO RISK MANAGEMENT!)",
                "strategy_name": "",
            },
        )

    def run_with_order_layer(
        self,
        df: pd.DataFrame,
        strategy_signal_fn: Callable,
        strategy_params: dict,
        symbol: str = "BTC/EUR",
        fee_bps: float = 0.0,
        slippage_bps: float = 0.0,
    ) -> BacktestResult:
        """
        DEPRECATED: Verwende run_realistic() mit use_execution_pipeline=True.

        Diese Methode bleibt fuer Backward-Kompatibilitaet erhalten und
        delegiert an _run_with_execution_pipeline().
        """
        logger.warning(
            "run_with_order_layer() ist deprecated. "
            "Nutze run_realistic() mit use_execution_pipeline=True stattdessen."
        )
        return self._run_with_execution_pipeline(
            df=df,
            strategy_signal_fn=strategy_signal_fn,
            strategy_params=strategy_params,
            symbol=symbol,
            fee_bps=fee_bps,
            slippage_bps=slippage_bps,
        )

    def _run_with_execution_pipeline(
        self,
        df: pd.DataFrame,
        strategy_signal_fn: Callable,
        strategy_params: dict,
        symbol: str = "BTC/EUR",
        fee_bps: float = 0.0,
        slippage_bps: float = 0.0,
    ) -> BacktestResult:
        """
        Interner Backtest mit ExecutionPipeline.

        Verwendet die ExecutionPipeline aus Phase 16 fuer die Simulation.
        Alle Trades werden als OrderRequest/OrderFill abgewickelt.

        Workflow:
        1. Signale generieren via strategy_signal_fn
        2. ExecutionPipeline mit PaperOrderExecutor initialisieren
        3. Signal-Wechsel erkennen und Orders generieren
        4. Orders ueber Pipeline ausfuehren
        5. PnL und Equity aus Fills berechnen
        6. Optional: Execution-Summary loggen

        Args:
            df: OHLCV-DataFrame (DatetimeIndex, Spalten: open, high, low, close, volume)
            strategy_signal_fn: Funktion(df, params) -> pd.Series mit Signalen (1=Buy, -1=Sell, 0=Hold)
            strategy_params: Parameter-Dict fuer Strategie
            symbol: Trading-Symbol (default: "BTC/EUR")
            fee_bps: Fees in Basispunkten (default: 0.0)
            slippage_bps: Slippage in Basispunkten (default: 0.0)

        Returns:
            BacktestResult mit Equity-Curve, Trades (als OrderFills), Stats
        """
        import uuid
        run_id = f"backtest_{uuid.uuid4().hex[:8]}"

        # Init
        initial_equity = self.config["backtest"]["initial_cash"]
        equity = initial_equity
        self.equity_curve = [equity]
        self.execution_results = []

        # DataFrame speichern
        self.data = df

        # Signale generieren
        signals = strategy_signal_fn(df, strategy_params)

        # ExecutionPipeline initialisieren
        initial_price = float(df.iloc[0]["close"])
        pipeline = self._init_execution_pipeline(
            symbol=symbol,
            initial_price=initial_price,
            fee_bps=fee_bps,
            slippage_bps=slippage_bps,
        )

        # Referenz auf Marktkontext fuer Preis-Updates
        market_ctx = pipeline.executor.context

        # Tracking-Variablen
        current_position = 0.0  # Aktuelle Position (positiv=Long, negativ=Short)
        previous_signal = 0
        trades_data: list[dict[str, Any]] = []
        entry_price = 0.0
        entry_time = None

        # Position-Sizing Parameter
        self.config["risk"].get("risk_per_trade", 0.02)
        max_position_pct = self.config["risk"].get("max_position_size", 0.25)

        # Bar-fuer-Bar-Loop
        for i in range(len(df)):
            bar = df.iloc[i]
            # Verwende .iloc[0] wenn Series, sonst direkt int()
            sig_val = signals.iloc[i]
            signal = int(sig_val.iloc[0]) if hasattr(sig_val, 'iloc') else int(sig_val)
            bar_time = bar.name
            close_price = float(bar["close"])

            # Preis in Marktkontext aktualisieren
            market_ctx.set_price(symbol, close_price)

            # Position-Sizing: Berechne gewuenschte Positionsgroesse
            position_value = equity * max_position_pct
            position_size = position_value / close_price if close_price > 0 else 0.0

            # SignalEvent erstellen
            event = SignalEvent(
                timestamp=bar_time.to_pydatetime() if hasattr(bar_time, "to_pydatetime") else bar_time,
                symbol=symbol,
                signal=signal,
                price=close_price,
                previous_signal=previous_signal,
                metadata={"bar_index": i, "strategy_params": strategy_params},
            )

            # Orders generieren basierend auf Signal-Wechsel
            orders = pipeline.signal_to_orders(
                event=event,
                position_size=position_size,
                current_position=current_position,
            )

            # Orders ausfuehren
            if orders:
                results = pipeline.execute_orders(orders)
                self.execution_results.extend(results)

                # Position und Equity aktualisieren
                for result in results:
                    if result.is_filled and result.fill:
                        fill = result.fill
                        fill.quantity * fill.price
                        fee = fill.fee or 0.0

                        if fill.side == "buy":
                            # Kauf: Cash reduzieren, Position erhoehen
                            if current_position <= 0:
                                # Neuer Long-Entry
                                entry_price = fill.price
                                entry_time = fill.timestamp

                            # Position schliessen (bei Short) oder neue Long-Position
                            if current_position < 0:
                                # Short schliessen
                                pnl = abs(current_position) * (entry_price - fill.price) - fee
                                trades_data.append({
                                    "entry_time": entry_time,
                                    "entry_price": entry_price,
                                    "exit_time": fill.timestamp,
                                    "exit_price": fill.price,
                                    "size": abs(current_position),
                                    "side": "short",
                                    "pnl": pnl,
                                    "pnl_pct": (pnl / (entry_price * abs(current_position))) * 100 if entry_price > 0 else 0,
                                    "fee": fee,
                                    "exit_reason": "signal",
                                })
                                equity += pnl
                                current_position = 0.0

                            current_position += fill.quantity
                            equity -= fee  # Fee abziehen

                        else:  # sell
                            if current_position > 0:
                                # Long schliessen
                                pnl = current_position * (fill.price - entry_price) - fee
                                trades_data.append({
                                    "entry_time": entry_time,
                                    "entry_price": entry_price,
                                    "exit_time": fill.timestamp,
                                    "exit_price": fill.price,
                                    "size": current_position,
                                    "side": "long",
                                    "pnl": pnl,
                                    "pnl_pct": (pnl / (entry_price * current_position)) * 100 if entry_price > 0 else 0,
                                    "fee": fee,
                                    "exit_reason": "signal",
                                })
                                equity += pnl
                                current_position = 0.0
                            elif current_position <= 0:
                                # Short-Entry
                                entry_price = fill.price
                                entry_time = fill.timestamp
                                current_position -= fill.quantity
                                equity -= fee

            # Equity-Curve aktualisieren (Mark-to-Market)
            if current_position > 0:
                current_position * close_price
                unrealized_pnl = current_position * (close_price - entry_price)
                current_equity = equity + unrealized_pnl
            elif current_position < 0:
                unrealized_pnl = abs(current_position) * (entry_price - close_price)
                current_equity = equity + unrealized_pnl
            else:
                current_equity = equity

            self.equity_curve.append(current_equity)
            previous_signal = signal

        # Offene Position am Ende schliessen
        if current_position != 0:
            last_bar = df.iloc[-1]
            close_price = float(last_bar["close"])

            if current_position > 0:
                # Long schliessen
                pnl = current_position * (close_price - entry_price)
                trades_data.append({
                    "entry_time": entry_time,
                    "entry_price": entry_price,
                    "exit_time": last_bar.name,
                    "exit_price": close_price,
                    "size": current_position,
                    "side": "long",
                    "pnl": pnl,
                    "pnl_pct": (pnl / (entry_price * current_position)) * 100 if entry_price > 0 else 0,
                    "fee": 0.0,
                    "exit_reason": "end_of_data",
                })
                equity += pnl
            else:
                # Short schliessen
                pnl = abs(current_position) * (entry_price - close_price)
                trades_data.append({
                    "entry_time": entry_time,
                    "entry_price": entry_price,
                    "exit_time": last_bar.name,
                    "exit_price": close_price,
                    "size": abs(current_position),
                    "side": "short",
                    "pnl": pnl,
                    "pnl_pct": (pnl / (entry_price * abs(current_position))) * 100 if entry_price > 0 else 0,
                    "fee": 0.0,
                    "exit_reason": "end_of_data",
                })
                equity += pnl

        # Stats berechnen
        equity_series = pd.Series(self.equity_curve, index=[df.index[0], *list(df.index)])
        drawdown_series = stats_mod.compute_drawdown(equity_series)
        basic_stats = stats_mod.compute_basic_stats(equity_series)

        # Trade-Stats
        from .stats import compute_trade_stats
        trade_stats = compute_trade_stats(trades_data) if trades_data else None

        # Execution-Summary
        exec_summary = pipeline.get_execution_summary()

        stats = {
            **basic_stats,
            "total_trades": len(trades_data),
            "win_rate": trade_stats.win_rate if trade_stats else 0.0,
            "profit_factor": trade_stats.profit_factor if trade_stats else 0.0,
            "total_orders": exec_summary["total_orders"],
            "filled_orders": exec_summary["filled_orders"],
            "rejected_orders": exec_summary["rejected_orders"],
            "total_fees": exec_summary["total_fees"],
        }

        # Trades-DataFrame
        trades_df = pd.DataFrame(trades_data) if trades_data else None

        logger.info(
            f"ExecutionPipeline Backtest abgeschlossen: {len(trades_data)} Trades, "
            f"{exec_summary['total_orders']} Orders, {exec_summary['total_fees']:.2f} Fees"
        )

        # Execution-Logging (Phase 16B)
        if self.log_executions:
            self._log_execution_summary(
                run_id=run_id,
                symbol=symbol,
                summary=exec_summary,
            )

        return BacktestResult(
            equity_curve=equity_series,
            drawdown=drawdown_series,
            trades=trades_df,
            stats=stats,
            metadata={
                "mode": "execution_pipeline_backtest",
                "strategy_name": "",
                "symbol": symbol,
                "fee_bps": fee_bps,
                "slippage_bps": slippage_bps,
                "execution_summary": exec_summary,
                "run_id": run_id,
            },
        )


# ============================================================================
# REGISTRY-BASIERTE ENTRY-POINTS
# ============================================================================

def run_single_strategy_from_registry(
    df: pd.DataFrame,
    strategy_name: str,
    custom_params: dict[str, Any] | None = None,
    position_sizer: PositionSizer | None = None,
    risk_limits: RiskLimits | None = None,
    core_position_sizer: BasePositionSizer | None = None,
    risk_manager: BaseRiskManager | None = None,
) -> BacktestResult:
    """
    Führt Backtest für EINE Strategie aus der Registry aus.

    Workflow:
    1. Lädt Strategie-Config aus Registry (mit Defaults-Merging)
    2. Override mit custom_params (falls angegeben)
    3. Lädt Strategie-Funktion via load_strategy()
    4. Führt run_realistic() aus

    Args:
        df: OHLCV-DataFrame
        strategy_name: Name der Strategie (muss in config.toml definiert sein)
        custom_params: Optional Params die Config überschreiben
        position_sizer: Optional custom PositionSizer
        risk_limits: Optional custom RiskLimits

    Returns:
        BacktestResult mit strategy_name gesetzt

    Raises:
        KeyError: Wenn Strategie nicht in Registry
        ValueError: Wenn Strategie-Funktion fehlerhaft

    Example:
        >>> from src.backtest.engine import run_single_strategy_from_registry
        >>>
        >>> result = run_single_strategy_from_registry(
        ...     df=df,
        ...     strategy_name="ma_crossover",
        ...     custom_params={"fast_period": 20}  # überschreibt Config
        ... )
        >>> print(f"{result.strategy_name}: Sharpe={result.stats['sharpe']:.2f}")
    """
    # 1. Config aus Registry laden
    strategy_cfg = get_strategy_config(strategy_name)

    # 2. Merged Params (Defaults + Strategy-Specific)
    params = strategy_cfg.to_dict()

    # 3. Custom Params überschreiben
    if custom_params:
        params.update(custom_params)

    # 4. Strategie-Funktion laden
    try:
        strategy_fn = load_strategy(strategy_name)
    except Exception as e:
        raise ValueError(
            f"Konnte Strategie '{strategy_name}' nicht laden: {e}"
        )

    # 5. Engine initialisieren
    engine = BacktestEngine(
        position_sizer=position_sizer,
        risk_limits=risk_limits,
        core_position_sizer=core_position_sizer,
        risk_manager=risk_manager,
    )

    # 6. Backtest ausführen
    logger.info(f"Starte Backtest für Strategie '{strategy_name}'")
    logger.debug(f"Merged Params: {params}")

    result = engine.run_realistic(
        df=df,
        strategy_signal_fn=strategy_fn,
        strategy_params=params,
    )

    # 7. Strategy-Name setzen
    result.strategy_name = strategy_name

    logger.info(
        f"Backtest '{strategy_name}' abgeschlossen: "
        f"Return={result.stats['total_return']:.2%}, "
        f"Sharpe={result.stats['sharpe']:.2f}, "
        f"Trades={result.stats['total_trades']}"
    )

    return result


@dataclass
class PortfolioResult:
    """
    Multi-Strategy Portfolio-Backtest-Ergebnis.

    Attributes:
        combined_equity: Kombinierte Equity-Curve aller Strategien
        strategy_results: Dict[strategy_name → BacktestResult]
        portfolio_stats: Aggregierte Portfolio-Stats
        allocation: Dict[strategy_name → Kapital-Allocation in %]
    """
    combined_equity: pd.Series
    strategy_results: dict[str, BacktestResult]
    portfolio_stats: dict[str, float]
    allocation: dict[str, float]


def run_portfolio_from_config(
    df: pd.DataFrame,
    cfg: dict[str, Any] | None = None,
    portfolio_name: str = "default",
    strategy_filter: list[str] | None = None,
    regime_filter: str | None = None,
    position_sizer: PositionSizer | None = None,
    risk_limits: RiskLimits | None = None,
    core_position_sizer: BasePositionSizer | None = None,
    risk_manager: BaseRiskManager | None = None,
) -> PortfolioResult:
    """
    Führt Portfolio-Backtest mit mehreren Strategien aus.

    Workflow:
    1. Lädt aktive Strategien aus Registry
    2. Optional: Filtert nach regime_filter oder strategy_filter
    3. Bestimmt Capital Allocation (equal/risk_parity/sharpe_weighted/manual)
    4. Führt Backtests für jede Strategie parallel aus
    5. Kombiniert Equity-Curves basierend auf Allocation
    6. Berechnet Portfolio-Stats

    Args:
        df: OHLCV-DataFrame
        cfg: Optional Config-Dict (default: lädt aus config.toml)
        portfolio_name: Portfolio-Name (default: "default")
        strategy_filter: Optional Liste von Strategie-Namen (überschreibt active)
        regime_filter: Optional Marktregime-Filter ("trending", "ranging", "any")
        position_sizer: Optional custom PositionSizer für alle Strategien
        risk_limits: Optional custom RiskLimits für alle Strategien

    Returns:
        PortfolioResult mit kombinierter Equity und Individual-Results

    Example:
        >>> from src.backtest.engine import run_portfolio_from_config
        >>>
        >>> # Alle aktiven Strategien
        >>> result = run_portfolio_from_config(df)
        >>>
        >>> # Nur Trending-Strategien
        >>> result = run_portfolio_from_config(df, regime_filter="trending")
        >>>
        >>> # Custom Strategie-Liste
        >>> result = run_portfolio_from_config(
        ...     df,
        ...     strategy_filter=["ma_crossover", "momentum_1h"]
        ... )
    """
    # 1. Config laden
    if cfg is None:
        cfg = get_config()

    portfolio_cfg = cfg.get("portfolio", {})

    if not portfolio_cfg.get("enabled", False):
        raise ValueError(
            "Portfolio-Mode ist deaktiviert. "
            "Setze portfolio.enabled=true in config.toml"
        )

    # 2. Strategien bestimmen
    if strategy_filter:
        strategies = strategy_filter
    elif regime_filter:
        from ..core.config_registry import get_strategies_by_regime
        strategies = get_strategies_by_regime(regime_filter)
        if not strategies:
            raise ValueError(
                f"Keine Strategien für Regime '{regime_filter}' gefunden"
            )
    else:
        strategies = get_active_strategies()

    if not strategies:
        raise ValueError("Keine Strategien zum Backtesten ausgewählt")

    # 3. Max Strategies Limit prüfen
    max_strategies = portfolio_cfg.get("max_strategies_active", 3)
    if len(strategies) > max_strategies:
        logger.warning(
            f"Portfolio limitiert auf {max_strategies} Strategien, "
            f"aber {len(strategies)} wurden ausgewählt. "
            f"Nutze erste {max_strategies}."
        )
        strategies = strategies[:max_strategies]

    logger.info(
        f"Starte Portfolio-Backtest mit {len(strategies)} Strategien: "
        f"{', '.join(strategies)}"
    )

    # 4. Capital Allocation bestimmen
    total_capital = portfolio_cfg.get("total_capital", cfg["backtest"]["initial_cash"])
    allocation_method = portfolio_cfg.get("allocation_method", "equal")

    allocation = _calculate_allocation(
        strategies=strategies,
        method=allocation_method,
        manual_weights=portfolio_cfg.get("weights", {}),
        total_capital=total_capital,
    )

    logger.info(f"Capital Allocation ({allocation_method}): {allocation}")

    # 5. Backtests für jede Strategie ausführen
    strategy_results: dict[str, BacktestResult] = {}

    for strategy_name in strategies:
        # Capital für diese Strategie
        strategy_capital = allocation[strategy_name] * total_capital

        # Backtest mit angepasstem Initial Capital
        # WICHTIG: Wir müssen initial_cash temporär überschreiben
        original_cash = cfg["backtest"]["initial_cash"]
        cfg["backtest"]["initial_cash"] = strategy_capital

        try:
            result = run_single_strategy_from_registry(
                df=df,
                strategy_name=strategy_name,
                position_sizer=position_sizer,
                risk_limits=risk_limits,
                core_position_sizer=core_position_sizer,
                risk_manager=risk_manager,
            )
            strategy_results[strategy_name] = result
        except Exception as e:
            logger.error(
                f"Fehler beim Backtest von '{strategy_name}': {e}"
            )
            # Bei Fehler: Dummy-Result mit 0 Equity
            strategy_results[strategy_name] = _create_dummy_result(
                strategy_name, df, strategy_capital
            )
        finally:
            # Initial Cash zurücksetzen
            cfg["backtest"]["initial_cash"] = original_cash

    # 6. Equity-Curves kombinieren
    combined_equity = _combine_equity_curves(
        strategy_results=strategy_results,
        allocation=allocation,
    )

    # 7. Portfolio-Stats berechnen
    from .stats import compute_basic_stats, compute_sharpe_ratio

    portfolio_stats = {
        **compute_basic_stats(combined_equity),
        "sharpe": compute_sharpe_ratio(combined_equity),
        "num_strategies": len(strategies),
        "allocation_method": allocation_method,
    }

    # Individual Stats hinzufügen
    for name, result in strategy_results.items():
        portfolio_stats[f"{name}_return"] = result.stats["total_return"]
        portfolio_stats[f"{name}_sharpe"] = result.stats["sharpe"]
        portfolio_stats[f"{name}_trades"] = result.stats["total_trades"]

    logger.info(
        f"Portfolio-Backtest abgeschlossen: "
        f"Return={portfolio_stats['total_return']:.2%}, "
        f"Sharpe={portfolio_stats['sharpe']:.2f}"
    )

    return PortfolioResult(
        combined_equity=combined_equity,
        strategy_results=strategy_results,
        portfolio_stats=portfolio_stats,
        allocation=allocation,
    )


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def _calculate_allocation(
    strategies: list[str],
    method: str,
    manual_weights: dict[str, float],
    total_capital: float,
) -> dict[str, float]:
    """
    Berechnet Capital Allocation für Portfolio.

    Methods:
    - "equal": Gleichverteilung (1/N)
    - "manual": Nutzt portfolio.weights aus Config
    - "risk_parity": NOTE: Siehe docs/TECH_DEBT_BACKLOG.md (gleiches Risk-Level pro Strategie)
    - "sharpe_weighted": NOTE: Siehe docs/TECH_DEBT_BACKLOG.md (basierend auf historischer Sharpe)

    Args:
        strategies: Liste von Strategie-Namen
        method: Allocation-Methode
        manual_weights: Dict mit manuellen Weights
        total_capital: Gesamt-Kapital

    Returns:
        Dict[strategy_name → fraction] (Summe = 1.0)
    """
    n = len(strategies)

    if method == "equal":
        return {name: 1.0 / n for name in strategies}

    elif method == "manual":
        # Nutze manual_weights, fallback auf equal
        allocation = {}
        for name in strategies:
            weight = manual_weights.get(name)
            if weight is None:
                logger.warning(
                    f"Kein Weight für '{name}' in portfolio.weights, "
                    f"nutze equal weight"
                )
                weight = 1.0 / n
            allocation[name] = weight

        # Normalisieren (Summe = 1.0)
        total = sum(allocation.values())
        if abs(total - 1.0) > 0.01:
            logger.warning(
                f"Weights summieren zu {total:.3f} statt 1.0, "
                f"normalisiere..."
            )
            allocation = {k: v / total for k, v in allocation.items()}

        return allocation

    elif method == "risk_parity":
        # TODO: Implementierung basierend auf Volatility/Sharpe
        logger.warning(
            "risk_parity noch nicht implementiert, nutze equal weight"
        )
        return {name: 1.0 / n for name in strategies}

    elif method == "sharpe_weighted":
        # TODO: Benötigt historische Backtests
        logger.warning(
            "sharpe_weighted noch nicht implementiert, nutze equal weight"
        )
        return {name: 1.0 / n for name in strategies}

    else:
        raise ValueError(
            f"Unbekannte Allocation-Methode: '{method}'. "
            f"Verfügbar: equal, manual, risk_parity, sharpe_weighted"
        )


def _combine_equity_curves(
    strategy_results: dict[str, BacktestResult],
    allocation: dict[str, float],
) -> pd.Series:
    """
    Kombiniert Equity-Curves mehrerer Strategien basierend auf Allocation.

    Args:
        strategy_results: Dict[strategy_name → BacktestResult]
        allocation: Dict[strategy_name → fraction]

    Returns:
        Kombinierte Equity-Curve (pd.Series)
    """
    if not strategy_results:
        raise ValueError("Keine Strategy-Results zum Kombinieren")

    # Alle Equity-Curves sammeln
    equity_curves = {}
    for name, result in strategy_results.items():
        weight = allocation[name]
        equity_curves[name] = result.equity_curve * weight

    # Kombinieren (Summe)
    combined = sum(equity_curves.values())

    return combined


def _create_dummy_result(
    strategy_name: str,
    df: pd.DataFrame,
    initial_capital: float,
) -> BacktestResult:
    """
    Erstellt Dummy-BacktestResult bei Fehler.

    Args:
        strategy_name: Name der Strategie
        df: OHLCV-DataFrame
        initial_capital: Startkapital

    Returns:
        BacktestResult mit flat Equity
    """
    equity = pd.Series(
        initial_capital,
        index=[df.index[0], *list(df.index)],
    )

    return BacktestResult(
        equity_curve=equity,
        trades=[],
        stats={
            "total_return": 0.0,
            "sharpe": 0.0,
            "max_drawdown": 0.0,
            "total_trades": 0,
            "win_rate": 0.0,
            "profit_factor": 0.0,
        },
        mode="error_dummy",
        strategy_name=strategy_name,
        blocked_trades=0,
    )


# ============================================================================
# PORTFOLIO STRATEGY LAYER INTEGRATION (Phase 26)
# ============================================================================

@dataclass
class PortfolioStrategyResult:
    """
    Ergebnis eines Portfolio-Strategy-Layer-Backtests (Phase 26).

    Unterschied zu PortfolioResult:
    - PortfolioResult: Multi-Strategy (verschiedene Strategien)
    - PortfolioStrategyResult: Multi-Asset mit Portfolio-Gewichtung

    Attributes:
        combined_equity: Kombinierte Equity-Curve des Portfolios
        symbol_equities: Equity pro Symbol
        target_weights_history: Historie der Zielgewichte über Zeit
        actual_weights_history: Historie der tatsächlichen Gewichte
        portfolio_stats: Aggregierte Portfolio-Statistiken
        trades_per_symbol: Trades pro Symbol
        portfolio_strategy_name: Name der verwendeten Portfolio-Strategie
        metadata: Zusätzliche Informationen
    """
    combined_equity: pd.Series
    symbol_equities: dict[str, pd.Series]
    target_weights_history: pd.DataFrame
    actual_weights_history: pd.DataFrame
    portfolio_stats: dict[str, float]
    trades_per_symbol: dict[str, pd.DataFrame]
    portfolio_strategy_name: str
    metadata: dict[str, Any] = field(default_factory=dict)


def run_portfolio_strategy_backtest(
    data_dict: dict[str, pd.DataFrame],
    strategy_signal_fn: Callable,
    strategy_params: dict[str, Any],
    portfolio_config: Any | None = None,
    initial_capital: float = 10000.0,
    fee_bps: float = 0.0,
    slippage_bps: float = 0.0,
    rebalance_interval: int = 1,
) -> PortfolioStrategyResult:
    """
    Führt Portfolio-Backtest mit Portfolio-Strategy-Layer aus (Phase 26).

    Diese Funktion kombiniert:
    1. Single-Strategie-Signale für mehrere Symbole
    2. Portfolio-Strategie für Gewichtung (Equal-Weight, Fixed, Vol-Target)
    3. Backtest mit Rebalancing

    Workflow:
    1. Für jedes Symbol: Signale generieren
    2. Portfolio-Kontext aufbauen
    3. Portfolio-Strategie: Zielgewichte berechnen
    4. Positionen anpassen (Rebalancing)
    5. PnL und Equity tracken

    Args:
        data_dict: Dict[symbol -> OHLCV-DataFrame]
        strategy_signal_fn: Signal-Generator-Funktion
        strategy_params: Parameter für Signal-Generator
        portfolio_config: Optional PortfolioConfig (default: aus config.toml)
        initial_capital: Startkapital
        fee_bps: Gebühren in Basispunkten
        slippage_bps: Slippage in Basispunkten
        rebalance_interval: Rebalancing alle N Bars

    Returns:
        PortfolioStrategyResult mit kombinierten Ergebnissen

    Example:
        >>> from src.portfolio import PortfolioConfig
        >>> from src.strategies.ma_crossover import generate_signals
        >>>
        >>> # Daten für mehrere Symbole laden
        >>> data = {
        ...     "BTC/EUR": btc_df,
        ...     "ETH/EUR": eth_df,
        ... }
        >>>
        >>> # Mit Equal-Weight
        >>> config = PortfolioConfig(enabled=True, name="equal_weight")
        >>> result = run_portfolio_strategy_backtest(
        ...     data_dict=data,
        ...     strategy_signal_fn=generate_signals,
        ...     strategy_params={"fast_window": 20, "slow_window": 50},
        ...     portfolio_config=config,
        ... )

    Note:
        WICHTIG: Nur für Research/Backtest/Shadow, NICHT für Live-Trading!
    """
    from ..core.peak_config import load_config
    from ..portfolio import (
        PortfolioConfig,
        PortfolioContext,
        make_portfolio_strategy,
    )

    # 1. Portfolio-Config laden
    if portfolio_config is None:
        try:
            peak_cfg = load_config("config.toml")
            portfolio_config = PortfolioConfig.from_peak_config(peak_cfg)
        except Exception as e:
            logger.warning(f"Konnte PortfolioConfig nicht laden: {e}, nutze Defaults")
            portfolio_config = PortfolioConfig(enabled=True, name="equal_weight")

    # 2. Portfolio-Strategie erstellen
    portfolio_strategy = make_portfolio_strategy(portfolio_config)

    if portfolio_strategy is None:
        raise ValueError(
            "Portfolio-Layer ist deaktiviert. "
            "Setze portfolio.enabled=true in config.toml"
        )

    logger.info(
        f"Portfolio-Strategy-Backtest mit {portfolio_strategy.name} gestartet"
    )

    # 3. Daten validieren und synchronisieren
    symbols = list(data_dict.keys())
    if not symbols:
        raise ValueError("data_dict ist leer")

    # Gemeinsamen Index finden (Intersection)
    common_index = data_dict[symbols[0]].index
    for symbol in symbols[1:]:
        common_index = common_index.intersection(data_dict[symbol].index)

    if len(common_index) == 0:
        raise ValueError("Keine gemeinsamen Zeitstempel in den Daten")

    logger.info(f"Portfolio mit {len(symbols)} Symbolen, {len(common_index)} Bars")

    # 4. Signale für alle Symbole generieren
    signals_dict: dict[str, pd.Series] = {}
    for symbol, df in data_dict.items():
        df_aligned = df.loc[common_index]
        signals = strategy_signal_fn(df_aligned, strategy_params)
        signals_dict[symbol] = signals.loc[common_index]

    # 5. Backtest-Loop initialisieren
    equity = initial_capital
    cash = initial_capital
    positions: dict[str, float] = {s: 0.0 for s in symbols}  # Stückzahl

    # Tracking
    equity_curve = [equity]
    symbol_equity_curves: dict[str, list[float]] = {s: [0.0] for s in symbols}
    target_weights_list: list[dict[str, float]] = []
    actual_weights_list: list[dict[str, float]] = []
    all_trades: dict[str, list[dict]] = {s: [] for s in symbols}

    # Entry-Tracking für PnL
    entry_prices: dict[str, float] = {}
    entry_times: dict[str, pd.Timestamp] = {}

    # 6. Bar-für-Bar-Loop
    prev_target_weights: dict[str, float] = {}

    for bar_idx, timestamp in enumerate(common_index):
        # Aktuelle Preise
        prices = {s: float(data_dict[s].loc[timestamp, "close"]) for s in symbols}

        # Aktuelle Signale
        current_signals = {s: float(signals_dict[s].loc[timestamp]) for s in symbols}

        # Portfolio-Wert berechnen (Mark-to-Market)
        portfolio_value = cash
        for symbol in symbols:
            pos_value = positions[symbol] * prices[symbol]
            portfolio_value += pos_value
            symbol_equity_curves[symbol].append(pos_value)

        equity = portfolio_value
        equity_curve.append(equity)

        # Aktuelle Gewichte berechnen
        actual_weights = {}
        for symbol in symbols:
            pos_value = positions[symbol] * prices[symbol]
            actual_weights[symbol] = pos_value / equity if equity > 0 else 0.0
        actual_weights_list.append(actual_weights)

        # Returns berechnen für Vol-Target (wenn nötig)
        returns_history = None
        if bar_idx >= portfolio_config.vol_lookback and portfolio_config.name == "vol_target":
            returns_dict = {}
            for symbol in symbols:
                symbol_prices = data_dict[symbol].loc[common_index[:bar_idx+1], "close"]
                returns_dict[symbol] = symbol_prices.pct_change().dropna()
            returns_history = pd.DataFrame(returns_dict)

        # Portfolio-Context erstellen
        context = PortfolioContext(
            timestamp=timestamp,
            symbols=symbols,
            prices=prices,
            current_positions=positions.copy(),
            strategy_signals=current_signals,
            returns_history=returns_history,
            equity=equity,
        )

        # Zielgewichte berechnen
        target_weights = portfolio_strategy.generate_target_weights(context)
        target_weights_list.append(target_weights)

        # Rebalancing-Check
        should_rebalance = (bar_idx % rebalance_interval == 0)
        weights_changed = (target_weights != prev_target_weights)

        if should_rebalance or weights_changed:
            # Positionen anpassen
            for symbol in symbols:
                target_weight = target_weights.get(symbol, 0.0)
                target_value = equity * target_weight
                target_position = target_value / prices[symbol] if prices[symbol] > 0 else 0.0

                current_position = positions[symbol]
                delta = target_position - current_position

                if abs(delta) > 0.0001:  # Mindest-Trade-Größe
                    trade_value = abs(delta) * prices[symbol]
                    fee = trade_value * fee_bps / 10000

                    if delta > 0:
                        # Kaufen
                        cost = delta * prices[symbol] * (1 + slippage_bps / 10000) + fee
                        if cost <= cash:
                            positions[symbol] += delta
                            cash -= cost

                            # Trade tracken
                            if current_position <= 0:
                                entry_prices[symbol] = prices[symbol]
                                entry_times[symbol] = timestamp
                    else:
                        # Verkaufen
                        proceeds = abs(delta) * prices[symbol] * (1 - slippage_bps / 10000) - fee
                        positions[symbol] += delta  # delta ist negativ
                        cash += proceeds

                        # Trade abschließen wenn Position geschlossen
                        if positions[symbol] <= 0 and symbol in entry_prices:
                            pnl = (prices[symbol] - entry_prices[symbol]) * abs(current_position)
                            all_trades[symbol].append({
                                "entry_time": entry_times.get(symbol),
                                "entry_price": entry_prices.get(symbol),
                                "exit_time": timestamp,
                                "exit_price": prices[symbol],
                                "size": abs(current_position),
                                "pnl": pnl,
                                "pnl_pct": (pnl / (entry_prices[symbol] * abs(current_position))) * 100 if entry_prices.get(symbol) else 0,
                            })
                            entry_prices.pop(symbol, None)
                            entry_times.pop(symbol, None)

        prev_target_weights = target_weights.copy()

    # 7. Offene Positionen am Ende schließen
    last_timestamp = common_index[-1]
    for symbol in symbols:
        if positions[symbol] > 0 and symbol in entry_prices:
            last_price = float(data_dict[symbol].loc[last_timestamp, "close"])
            pnl = (last_price - entry_prices[symbol]) * positions[symbol]
            all_trades[symbol].append({
                "entry_time": entry_times.get(symbol),
                "entry_price": entry_prices.get(symbol),
                "exit_time": last_timestamp,
                "exit_price": last_price,
                "size": positions[symbol],
                "pnl": pnl,
                "pnl_pct": (pnl / (entry_prices[symbol] * positions[symbol])) * 100 if entry_prices.get(symbol) else 0,
                "exit_reason": "end_of_data",
            })

    # 8. Ergebnisse aufbereiten
    equity_series = pd.Series(equity_curve, index=[common_index[0], *list(common_index)])

    # Symbol Equities als Series
    symbol_equities = {
        s: pd.Series(symbol_equity_curves[s], index=[common_index[0], *list(common_index)])
        for s in symbols
    }

    # Weights als DataFrames
    target_weights_df = pd.DataFrame(target_weights_list, index=common_index)
    actual_weights_df = pd.DataFrame(actual_weights_list, index=common_index)

    # Trades als DataFrames
    trades_per_symbol = {
        s: pd.DataFrame(all_trades[s]) if all_trades[s] else pd.DataFrame()
        for s in symbols
    }

    # Portfolio-Stats berechnen
    portfolio_stats = stats_mod.compute_basic_stats(equity_series)
    portfolio_stats["sharpe"] = compute_sharpe_ratio(equity_series)
    portfolio_stats["total_trades"] = sum(len(t) for t in all_trades.values())
    portfolio_stats["num_symbols"] = len(symbols)
    portfolio_stats["rebalance_interval"] = rebalance_interval

    # Win-Rate berechnen
    all_pnls = []
    for trades in all_trades.values():
        all_pnls.extend([t["pnl"] for t in trades])

    if all_pnls:
        wins = sum(1 for p in all_pnls if p > 0)
        portfolio_stats["win_rate"] = wins / len(all_pnls)
    else:
        portfolio_stats["win_rate"] = 0.0

    logger.info(
        f"Portfolio-Strategy-Backtest abgeschlossen: "
        f"Return={portfolio_stats['total_return']:.2%}, "
        f"Sharpe={portfolio_stats['sharpe']:.2f}, "
        f"Trades={portfolio_stats['total_trades']}"
    )

    return PortfolioStrategyResult(
        combined_equity=equity_series,
        symbol_equities=symbol_equities,
        target_weights_history=target_weights_df,
        actual_weights_history=actual_weights_df,
        portfolio_stats=portfolio_stats,
        trades_per_symbol=trades_per_symbol,
        portfolio_strategy_name=portfolio_config.name,
        metadata={
            "symbols": symbols,
            "initial_capital": initial_capital,
            "fee_bps": fee_bps,
            "slippage_bps": slippage_bps,
            "portfolio_config": portfolio_config.to_dict(),
        },
    )


def compute_sharpe_ratio(equity_series: pd.Series, risk_free_rate: float = 0.0) -> float:
    """
    Berechnet die Sharpe Ratio für eine Equity-Curve.

    Args:
        equity_series: Equity-Zeitreihe
        risk_free_rate: Risikofreier Zinssatz (annualisiert)

    Returns:
        Annualisierte Sharpe Ratio
    """
    if len(equity_series) < 2:
        return 0.0

    returns = equity_series.pct_change().dropna()

    if returns.std() == 0:
        return 0.0

    # Annualisierung (Annahme: Daily/Hourly Data)
    annualization = np.sqrt(252)  # Für tägliche Daten

    excess_returns = returns.mean() - risk_free_rate / 252
    sharpe = (excess_returns / returns.std()) * annualization

    return float(sharpe)
