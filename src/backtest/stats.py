"""
Peak_Trade Backtest Statistics
================================
Performance-Metriken und Live-Trading-Validierung.

Metriken:
- Total Return, Max Drawdown
- Sharpe Ratio, Sortino Ratio, Calmar Ratio
- Ulcer Index, Recovery Factor
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


def compute_drawdown(equity: pd.Series) -> pd.Series:
    """
    Berechnet den prozentualen Drawdown basierend auf der Equity-Curve.

    Args:
        equity: Equity-Kurve (Series mit DatetimeIndex)

    Returns:
        pd.Series im Bereich [-1, 0], wobei 0 = kein Drawdown.

    Example:
        >>> equity = pd.Series([10000, 10100, 9500, 10200])
        >>> dd = compute_drawdown(equity)
        >>> print(f"Max DD: {dd.min():.2%}")
    """
    equity = equity.astype(float)
    running_max = equity.cummax()
    dd = (equity - running_max) / running_max.replace(0.0, np.nan)
    return dd.fillna(0.0)


def compute_basic_stats(equity: pd.Series) -> Dict[str, float]:
    """
    Berechnet grundlegende Performance-Metriken inkl. CAGR.

    Args:
        equity: Equity-Kurve (Series mit DatetimeIndex)

    Returns:
        Dict mit 'total_return', 'max_drawdown', 'cagr', 'sharpe'

    Example:
        >>> equity = pd.Series([10000, 10100, 10050, 10200])
        >>> stats = compute_basic_stats(equity)
        >>> print(f"Return: {stats['total_return']:.2%}")
    """
    if len(equity) < 2:
        return {
            "total_return": 0.0,
            "max_drawdown": 0.0,
            "cagr": 0.0,
            "sharpe": 0.0,
        }

    equity = equity.astype(float)

    # Total Return
    start = float(equity.iloc[0])
    end = float(equity.iloc[-1])
    total_return = (end - start) / start if start != 0 else 0.0

    # Max Drawdown
    dd = compute_drawdown(equity)
    max_drawdown = float(dd.min()) if not dd.empty else 0.0

    # CAGR & Sharpe (wenn DatetimeIndex vorhanden)
    if isinstance(equity.index, pd.DatetimeIndex) and len(equity) > 1:
        returns = equity.pct_change().dropna()
        mean_ret = returns.mean()
        std_ret = returns.std(ddof=1)

        # Einfache Annualisierung (365 Tage)
        annual_factor = 365.0
        cagr = (1.0 + mean_ret) ** annual_factor - 1.0 if mean_ret is not None else 0.0
        sharpe = (mean_ret * np.sqrt(annual_factor) / std_ret) if std_ret not in (0, None) else 0.0
    else:
        cagr = 0.0
        sharpe = 0.0

    return {
        "total_return": float(total_return),
        "max_drawdown": float(max_drawdown),
        "cagr": float(cagr),
        "sharpe": float(sharpe),
    }


def compute_sharpe_ratio(
    equity: pd.Series, periods_per_year: int = 252, risk_free_rate: float = 0.0
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
    max_dd = abs(stats["max_drawdown"])

    if max_dd == 0:
        return 0.0

    # Annualisierter Return
    total_return = stats["total_return"]
    n_periods = len(equity) - 1
    years = n_periods / periods_per_year

    if years <= 0:
        return 0.0

    annual_return = (1 + total_return) ** (1 / years) - 1

    return float(annual_return / max_dd)


def compute_ulcer_index(equity: pd.Series) -> float:
    """
    Berechnet den Ulcer Index (RMS der Drawdowns).

    Der Ulcer Index misst die "Stress"-Tiefe von Drawdowns: Wurzel aus dem
    Mittel der quadrierten prozentualen Drawdowns. Niedrigere Werte = weniger
    anhaltende Drawdowns. Einheit: Dezimal (z.B. 0.05 = 5% RMS-Drawdown).

    Formula:
        dd_t = (equity_t - running_max_t) / running_max_t
        Ulcer Index = sqrt(mean(dd_t^2))

    Args:
        equity: Equity-Kurve (Series mit DatetimeIndex optional)

    Returns:
        Ulcer Index >= 0 (0 = keine Drawdowns)
    """
    if len(equity) < 2:
        return 0.0
    dd = compute_drawdown(equity.astype(float))
    sq = (dd**2).replace([np.inf, -np.inf], np.nan).dropna()
    if len(sq) == 0:
        return 0.0
    return float(np.sqrt(sq.mean()))


def compute_recovery_factor(equity: pd.Series) -> float:
    """
    Berechnet den Recovery Factor (Total Return / |Max Drawdown|).

    Misst, wie viel Return pro Einheit Max Drawdown erzielt wurde.
    Höhere Werte = bessere Risiko-Adjustierung. Bei keinem Drawdown wird 0
    zurückgegeben (keine Division durch null).

    Formula:
        Recovery Factor = total_return / |max_drawdown|  (max_drawdown < 0)

    Args:
        equity: Equity-Kurve

    Returns:
        Recovery Factor >= 0 (0 wenn max_drawdown == 0)
    """
    if len(equity) < 2:
        return 0.0
    basic = compute_basic_stats(equity.astype(float))
    total_return = basic["total_return"]
    max_dd = basic["max_drawdown"]
    abs_dd = abs(max_dd)
    if abs_dd == 0:
        return 0.0
    return float(total_return / abs_dd)


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
            total_trades=0,
            winning_trades=0,
            losing_trades=0,
            win_rate=0.0,
            avg_win=0.0,
            avg_loss=0.0,
            profit_factor=0.0,
        )

    pnls = [t["pnl"] for t in trades]
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
        profit_factor=profit_factor,
    )


def compute_backtest_stats(
    trades: List[Dict],
    equity_curve: pd.Series,
    *,
    periods_per_year: int = 8760,
    risk_free_rate: float = 0.0,
) -> Dict[str, float]:
    """
    Zentrale Funktion zur Berechnung aller Backtest-Metriken.

    Kombiniert Equity-basierte Stats und Trade-Stats in einem einzigen Dict.
    Dies ist die Haupt-API für Stats-Berechnung im gesamten Framework.

    Args:
        trades: Liste von Trade-Dicts mit mindestens 'pnl' Key
        equity_curve: Equity-Series mit DatetimeIndex
        periods_per_year: Anzahl Perioden pro Jahr für Annualisierung
            - 8760 für stündliche Daten (365 * 24)
            - 252 für tägliche Daten
            - 52 für wöchentliche Daten
        risk_free_rate: Risikofreier Zinssatz (annualisiert, default: 0)

    Returns:
        Dict mit allen Standard-Metriken:
        {
            "total_return": float,      # Gesamt-Return (z.B. 0.15 = 15%)
            "cagr": float,              # Compound Annual Growth Rate
            "max_drawdown": float,      # Max Drawdown (z.B. -0.10 = -10%)
            "sharpe": float,            # Sharpe Ratio (annualisiert)
            "sortino": float,           # Sortino Ratio (annualisiert)
            "calmar": float,            # Calmar Ratio (Return / MaxDD)
            "ulcer_index": float,       # Ulcer Index (RMS Drawdown)
            "recovery_factor": float,   # Recovery Factor (Return / |MaxDD|)
            "total_trades": int,        # Anzahl Trades
            "winning_trades": int,      # Anzahl Gewinn-Trades
            "losing_trades": int,       # Anzahl Verlust-Trades
            "win_rate": float,          # Win-Rate (z.B. 0.55 = 55%)
            "profit_factor": float,     # Gross Profits / Gross Losses
            "avg_win": float,           # Durchschnittlicher Gewinn pro Trade
            "avg_loss": float,          # Durchschnittlicher Verlust pro Trade
            "expectancy": float,        # Erwartungswert pro Trade
        }

    Example:
        >>> from src.backtest.stats import compute_backtest_stats
        >>>
        >>> trades = [{'pnl': 100}, {'pnl': -50}, {'pnl': 75}]
        >>> equity = pd.Series([10000, 10100, 10050, 10125])
        >>>
        >>> stats = compute_backtest_stats(trades, equity)
        >>> print(f"Return: {stats['total_return']:.2%}")
        >>> print(f"Sharpe: {stats['sharpe']:.2f}")
    """
    # 1. Basic Equity Stats
    basic = compute_basic_stats(equity_curve)

    # 2. Trade Stats
    trade_stats = compute_trade_stats(trades)

    # 3. Sharpe mit korrekten Parametern
    sharpe = compute_sharpe_ratio(
        equity_curve, periods_per_year=periods_per_year, risk_free_rate=risk_free_rate
    )

    # 4. Sortino Ratio (nur Downside-Volatilität)
    sortino = _compute_sortino_ratio(
        equity_curve, periods_per_year=periods_per_year, risk_free_rate=risk_free_rate
    )

    # 5. Calmar Ratio
    calmar = compute_calmar_ratio(equity_curve, periods_per_year=periods_per_year)

    # 6. Ulcer Index & Recovery Factor
    ulcer_index = compute_ulcer_index(equity_curve)
    recovery_factor = compute_recovery_factor(equity_curve)

    # 7. Expectancy (durchschnittlicher Gewinn pro Trade)
    if trade_stats.total_trades > 0:
        total_pnl = sum(t.get("pnl", 0) for t in trades)
        expectancy = total_pnl / trade_stats.total_trades
    else:
        expectancy = 0.0

    return {
        # Equity-basierte Metriken
        "total_return": basic["total_return"],
        "cagr": basic["cagr"],
        "max_drawdown": basic["max_drawdown"],
        "sharpe": sharpe,
        "sortino": sortino,
        "calmar": calmar,
        "ulcer_index": ulcer_index,
        "recovery_factor": recovery_factor,
        # Trade-basierte Metriken
        "total_trades": trade_stats.total_trades,
        "winning_trades": trade_stats.winning_trades,
        "losing_trades": trade_stats.losing_trades,
        "win_rate": trade_stats.win_rate,
        "profit_factor": trade_stats.profit_factor,
        "avg_win": trade_stats.avg_win,
        "avg_loss": trade_stats.avg_loss,
        "expectancy": expectancy,
    }


def _compute_sortino_ratio(
    equity: pd.Series,
    periods_per_year: int = 252,
    risk_free_rate: float = 0.0,
) -> float:
    """
    Berechnet Sortino Ratio (nur Downside-Volatilität).

    Args:
        equity: Equity-Kurve
        periods_per_year: Anzahl Perioden pro Jahr
        risk_free_rate: Risikofreier Zinssatz (annualisiert)

    Returns:
        Sortino Ratio (annualisiert)
    """
    if len(equity) < 2:
        return 0.0

    returns = equity.pct_change().dropna()

    if len(returns) == 0:
        return 0.0

    # Nur negative Returns für Downside-Volatilität
    downside_returns = returns[returns < 0]

    if len(downside_returns) == 0:
        # Keine negativen Returns = perfekte Strategie
        return float("inf") if returns.mean() > 0 else 0.0

    downside_std = downside_returns.std()

    if downside_std == 0:
        return 0.0

    # Annualisierte Metriken
    mean_return = returns.mean() * periods_per_year
    downside_std_annual = downside_std * np.sqrt(periods_per_year)

    sortino = (mean_return - risk_free_rate) / downside_std_annual
    return float(sortino)


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
    sharpe = stats.get("sharpe", 0)
    if sharpe < 1.5:
        warnings.append(f"Sharpe Ratio {sharpe:.2f} < 1.5 (zu riskant)")

    # Kriterium 2: Max Drawdown
    max_dd = stats.get("max_drawdown", 0)
    if max_dd < -0.15:
        warnings.append(f"Max Drawdown {max_dd:.1%} > -15% (zu hohe Verluste)")

    # Kriterium 3: Anzahl Trades
    total_trades = stats.get("total_trades", 0)
    if total_trades < 50:
        warnings.append(f"Nur {total_trades} Trades < 50 (zu wenig statistische Signifikanz)")

    # Kriterium 4: Profit Factor
    pf = stats.get("profit_factor", 0)
    if pf < 1.3:
        warnings.append(f"Profit Factor {pf:.2f} < 1.3 (zu niedrig)")

    passed = len(warnings) == 0
    return passed, warnings
