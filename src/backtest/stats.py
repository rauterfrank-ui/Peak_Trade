"""
Peak_Trade Backtest Statistics
================================
Performance-Metriken und Live-Trading-Validierung.

Metriken:
- Total Return, Max Drawdown
- Sharpe Ratio, Calmar Ratio
- Trade-Statistiken (Win Rate, Profit Factor)
- Live-Trading-Validierung
"""

import pandas as pd
import numpy as np
from typing import Dict, Tuple, List
from dataclasses import dataclass


@dataclass
class TradeStats:
    """Trade-Statistiken."""
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float
    avg_win: float
    avg_loss: float
    profit_factor: float


def compute_basic_stats(equity: pd.Series) -> Dict[str, float]:
    """
    Berechnet grundlegende Performance-Metriken.
    
    Args:
        equity: Equity-Kurve (Series mit DatetimeIndex)
        
    Returns:
        Dict mit 'total_return' und 'max_drawdown'
        
    Example:
        >>> equity = pd.Series([10000, 10100, 10050, 10200])
        >>> stats = compute_basic_stats(equity)
        >>> print(f"Return: {stats['total_return']:.2%}")
    """
    if len(equity) < 2:
        return {"total_return": 0.0, "max_drawdown": 0.0}
    
    # Total Return
    total_return = (equity.iloc[-1] / equity.iloc[0]) - 1
    
    # Max Drawdown
    running_max = equity.cummax()
    drawdown = (equity / running_max) - 1
    max_drawdown = drawdown.min()
    
    return {
        "total_return": float(total_return),
        "max_drawdown": float(max_drawdown)
    }


def compute_sharpe_ratio(
    equity: pd.Series,
    periods_per_year: int = 252,
    risk_free_rate: float = 0.0
) -> float:
    """
    Berechnet Sharpe Ratio.
    
    Args:
        equity: Equity-Kurve
        periods_per_year: Anzahl Perioden pro Jahr (252 für täglich, 8760 für stündlich)
        risk_free_rate: Risikofreier Zinssatz (annualisiert)
        
    Returns:
        Sharpe Ratio (annualisiert)
        
    Formula:
        Sharpe = (mean_return - risk_free) / std_return * sqrt(periods_per_year)
    """
    if len(equity) < 2:
        return 0.0
    
    # Returns berechnen
    returns = equity.pct_change().dropna()
    
    if len(returns) == 0 or returns.std() == 0:
        return 0.0
    
    # Annualisierte Metriken
    mean_return = returns.mean() * periods_per_year
    std_return = returns.std() * np.sqrt(periods_per_year)
    
    sharpe = (mean_return - risk_free_rate) / std_return
    return float(sharpe)


def compute_calmar_ratio(equity: pd.Series, periods_per_year: int = 252) -> float:
    """
    Berechnet Calmar Ratio (Return / Max Drawdown).
    
    Args:
        equity: Equity-Kurve
        periods_per_year: Anzahl Perioden pro Jahr
        
    Returns:
        Calmar Ratio
    """
    stats = compute_basic_stats(equity)
    max_dd = abs(stats['max_drawdown'])
    
    if max_dd == 0:
        return 0.0
    
    # Annualisierter Return
    total_return = stats['total_return']
    n_periods = len(equity) - 1
    years = n_periods / periods_per_year
    
    if years <= 0:
        return 0.0
    
    annual_return = (1 + total_return) ** (1 / years) - 1
    
    return float(annual_return / max_dd)


def compute_trade_stats(trades: List[Dict]) -> TradeStats:
    """
    Berechnet Trade-Statistiken.
    
    Args:
        trades: Liste von Trade-Dicts mit 'pnl'
        
    Returns:
        TradeStats-Objekt
        
    Example:
        >>> trades = [{'pnl': 100}, {'pnl': -50}, {'pnl': 75}]
        >>> stats = compute_trade_stats(trades)
        >>> print(f"Win Rate: {stats.win_rate:.1%}")
    """
    if not trades:
        return TradeStats(
            total_trades=0, winning_trades=0, losing_trades=0,
            win_rate=0.0, avg_win=0.0, avg_loss=0.0, profit_factor=0.0
        )
    
    pnls = [t['pnl'] for t in trades]
    wins = [p for p in pnls if p > 0]
    losses = [p for p in pnls if p < 0]
    
    total_trades = len(trades)
    winning_trades = len(wins)
    losing_trades = len(losses)
    
    win_rate = winning_trades / total_trades if total_trades > 0 else 0.0
    avg_win = np.mean(wins) if wins else 0.0
    avg_loss = np.mean(losses) if losses else 0.0
    
    # Profit Factor
    total_wins = sum(wins) if wins else 0.0
    total_losses = abs(sum(losses)) if losses else 0.0
    profit_factor = total_wins / total_losses if total_losses > 0 else 0.0
    
    return TradeStats(
        total_trades=total_trades,
        winning_trades=winning_trades,
        losing_trades=losing_trades,
        win_rate=win_rate,
        avg_win=avg_win,
        avg_loss=avg_loss,
        profit_factor=profit_factor
    )


def validate_for_live_trading(stats: Dict) -> Tuple[bool, List[str]]:
    """
    Validiert, ob Strategie bereit für Live-Trading ist.
    
    Args:
        stats: Dict mit Performance-Metriken
        
    Returns:
        (passed, warnings): Bool + Liste von Warnungen
        
    Kriterien:
        - Sharpe Ratio >= 1.5
        - Max Drawdown >= -15%
        - Min. 50 Trades
        - Profit Factor >= 1.3
        
    Example:
        >>> stats = {
        ...     'sharpe': 1.8,
        ...     'max_drawdown': -0.12,
        ...     'total_trades': 60,
        ...     'profit_factor': 1.5
        ... }
        >>> passed, warnings = validate_for_live_trading(stats)
        >>> if passed:
        ...     print("Strategie FREIGEGEBEN für Live-Trading")
    """
    warnings = []
    
    # Kriterium 1: Sharpe Ratio
    sharpe = stats.get('sharpe', 0)
    if sharpe < 1.5:
        warnings.append(f"Sharpe Ratio {sharpe:.2f} < 1.5 (zu riskant)")
    
    # Kriterium 2: Max Drawdown
    max_dd = stats.get('max_drawdown', 0)
    if max_dd < -0.15:
        warnings.append(f"Max Drawdown {max_dd:.1%} > -15% (zu hohe Verluste)")
    
    # Kriterium 3: Anzahl Trades
    total_trades = stats.get('total_trades', 0)
    if total_trades < 50:
        warnings.append(f"Nur {total_trades} Trades < 50 (zu wenig statistische Signifikanz)")
    
    # Kriterium 4: Profit Factor
    pf = stats.get('profit_factor', 0)
    if pf < 1.3:
        warnings.append(f"Profit Factor {pf:.2f} < 1.3 (zu niedrig)")
    
    passed = len(warnings) == 0
    return passed, warnings
