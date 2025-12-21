"""
BacktestEngine: Generische Engine für Position-basierte Backtests.
"""

from typing import Any, Dict, Optional, Tuple
import numpy as np
import pandas as pd
from .results import BacktestResult


class BacktestEngine:
    """
    Führt Backtests mit Zielpositionen (target_positions) durch.
    Berücksichtigt Kommission und Slippage.
    """

    def __init__(
        self,
        commission_perc: float = 0.0005,
        slippage_perc: float = 0.0002,
    ) -> None:
        """
        Args:
            commission_perc: Prozentuale Kommission auf Notional (z.B. 0.0005 = 5bp)
            slippage_perc: Prozentuale Slippage pro Trade
        """
        self.commission_perc = float(commission_perc)
        self.slippage_perc = float(slippage_perc)

    def run_with_positions(
        self,
        df: pd.DataFrame,
        target_positions: pd.Series,
        initial_capital: float = 100_000.0,
        price_col: str = "close",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> BacktestResult:
        """
        Führt Backtest mit gegebenen Zielpositionen durch.

        Args:
            df: Marktdaten (muss price_col enthalten)
            target_positions: Zielposition in Units (Stückzahl)
            initial_capital: Startkapital
            price_col: Spaltenname für Preis
            metadata: Zusätzliche Metadaten

        Returns:
            BacktestResult mit Equity-Curve, Trades, Stats etc.
        """
        # Validierung
        if price_col not in df.columns:
            raise ValueError(f"Spalte '{price_col}' nicht in DataFrame gefunden.")

        # Daten vorbereiten
        df = df.sort_index().copy()
        price = df[price_col].astype(float)

        # Target-Positions alignen
        target_positions = target_positions.sort_index()
        target_positions = target_positions.reindex(df.index).ffill().fillna(0.0).astype(float)

        # Initialisierung
        position = 0.0
        cash = float(initial_capital)
        equity_records = []
        trade_records = []

        # Zeitschleife
        for t, p in price.items():
            tp = target_positions.loc[t]
            order = tp - position

            # Trade ausführen
            if order != 0.0:
                # Slippage
                slip = self.slippage_perc * p * np.sign(order)
                exec_price = p + slip

                # Notional & Kommission
                notional_exec = order * exec_price
                commission = abs(notional_exec) * self.commission_perc

                # Cash-Update
                cash -= notional_exec
                cash -= commission

                # Position-Update
                position = tp

                # Trade-Record
                trade_records.append(
                    {
                        "time": t,
                        "order_size": order,
                        "position_after": position,
                        "price": p,
                        "exec_price": exec_price,
                        "notional": notional_exec,
                        "commission": commission,
                        "cash_after": cash,
                    }
                )

            # Equity berechnen
            equity = cash + position * p
            equity_records.append(
                {
                    "time": t,
                    "equity": equity,
                    "cash": cash,
                    "position": position,
                    "price": p,
                }
            )

        # DataFrames erstellen
        equity_df = pd.DataFrame(equity_records).set_index("time")
        equity_curve = equity_df["equity"]

        trades_df = pd.DataFrame(trade_records)
        if not trades_df.empty:
            trades_df = trades_df.set_index("time")

        # Stats berechnen
        stats, drawdown_curve, daily_returns = self._compute_stats(equity_curve)

        # Result zurückgeben
        return BacktestResult(
            equity_curve=equity_curve,
            trades=trades_df,
            stats=stats,
            drawdown_curve=drawdown_curve,
            daily_returns=daily_returns,
            metadata=metadata or {},
        )

    def run_realistic(
        self,
        df: pd.DataFrame,
        strategy_name: str,
        params: Dict[str, Any],
        filters=None,
        risk_modules=None,
        initial_capital: float = 100_000.0,
        price_col: str = "close",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> BacktestResult:
        """
        Führt Backtest mit einer benannten Strategie durch.

        Args:
            df: Marktdaten
            strategy_name: Name der registrierten Strategie
            params: Strategie-Parameter
            filters: Optional, Liste von Filter-Objekten
            risk_modules: Optional, Liste von Risk-Module-Objekten
            initial_capital: Startkapital
            price_col: Spaltenname für Preis
            metadata: Zusätzliche Metadaten

        Returns:
            BacktestResult
        """
        # Strategie laden
        from src.strategies.registry import get_strategy

        StrategyCls = get_strategy(strategy_name)
        strategy = StrategyCls()

        # Signale generieren
        signals = strategy.generate_signals(df, params)

        # Filter anwenden
        if filters is not None:
            for flt in filters:
                signals = flt.apply(df, signals)

        # Risk-Module anwenden
        target_positions = signals
        if risk_modules is not None:
            for rm in risk_modules:
                target_positions = rm.apply(
                    df=df,
                    signals=target_positions,
                    prices=df[price_col],
                    initial_capital=initial_capital,
                )

        # Metadata ergänzen
        meta = metadata or {}
        meta["strategy"] = strategy_name
        meta["params"] = params
        if risk_modules:
            meta["risk_modules"] = [type(rm).__name__ for rm in risk_modules]

        # Backtest ausführen
        return self.run_with_positions(
            df=df,
            target_positions=target_positions,
            initial_capital=initial_capital,
            price_col=price_col,
            metadata=meta,
        )

    def _compute_stats(
        self, equity_curve: pd.Series
    ) -> Tuple[Dict[str, Any], pd.Series, pd.Series]:
        """
        Berechnet Kennzahlen aus Equity-Curve.

        Args:
            equity_curve: Zeitreihe des Portfoliowerts

        Returns:
            Tuple (stats_dict, drawdown_curve, daily_returns)
        """
        equity_curve = equity_curve.astype(float)

        # Validierung
        if equity_curve.empty or equity_curve.iloc[0] <= 0:
            return {}, pd.Series(dtype=float), pd.Series(dtype=float)

        # Returns
        returns = equity_curve.pct_change().dropna()

        # Daily-Returns (falls DatetimeIndex)
        if isinstance(equity_curve.index, pd.DatetimeIndex):
            daily_equity = equity_curve.resample("1D").last().dropna()
            daily_returns = daily_equity.pct_change().dropna()
        else:
            daily_returns = returns.copy()

        # Basisgrößen
        n_bars = len(equity_curve) - 1
        total_return = equity_curve.iloc[-1] / equity_curve.iloc[0] - 1.0

        # Annualisierung (252 Handelstage)
        if len(daily_returns) > 1:
            avg_daily_ret = daily_returns.mean()
            vol_daily = daily_returns.std(ddof=1)
            cagr = (1.0 + avg_daily_ret) ** 252 - 1.0
            ann_vol = vol_daily * np.sqrt(252)
            sharpe = cagr / ann_vol if ann_vol > 0 else np.nan
        else:
            cagr = np.nan
            ann_vol = np.nan
            sharpe = np.nan

        # Drawdown
        running_max = equity_curve.cummax()
        drawdown = equity_curve / running_max - 1.0
        max_drawdown = drawdown.min() if not drawdown.empty else 0.0

        # Max-Drawdown-Dauer
        if not drawdown.empty:
            dd_end_idx = drawdown.idxmin()
            mask = equity_curve.index <= dd_end_idx
            pre_dd = equity_curve[mask]
            prev_peak_idx = pre_dd.idxmax()
            max_dd_duration = pre_dd.index.get_loc(dd_end_idx) - pre_dd.index.get_loc(prev_peak_idx)
        else:
            max_dd_duration = 0

        # Stats-Dict
        stats = {
            "total_return": total_return,
            "cagr": cagr,
            "ann_vol": ann_vol,
            "sharpe": sharpe,
            "max_drawdown": max_drawdown,
            "max_drawdown_duration_bars": max_dd_duration,
            "n_bars": n_bars,
            "start_equity": equity_curve.iloc[0],
            "end_equity": equity_curve.iloc[-1],
        }

        return stats, drawdown, daily_returns
