"""
BacktestResult: Standardisiertes Ergebnisobjekt für Backtests.
"""
from dataclasses import dataclass
from typing import Any, Dict
import pandas as pd


@dataclass
class BacktestResult:
    """
    Enthält alle Ergebnisse eines Backtests.
    
    Attributes:
        equity_curve: Zeitreihe des Portfoliowerts
        trades: DataFrame mit allen ausgeführten Trades
        stats: Dict mit Kennzahlen (CAGR, Sharpe, MaxDD etc.)
        drawdown_curve: Zeitreihe der relativen Drawdowns
        daily_returns: Tagesrenditen (resampled)
        metadata: Zusätzliche Infos (Strategy-Name, Params etc.)
    """
    equity_curve: pd.Series
    trades: pd.DataFrame
    stats: Dict[str, Any]
    drawdown_curve: pd.Series
    daily_returns: pd.Series
    metadata: Dict[str, Any]
