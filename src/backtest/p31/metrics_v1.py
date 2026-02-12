"""P31 — Backtest metrics v1 (equity → KPIs)."""

from __future__ import annotations

from math import sqrt
from typing import Dict, List


def compute_returns(equity: List[float]) -> List[float]:
    """
    Simple returns: r_t = equity[t]/equity[t-1] - 1
    """
    if len(equity) < 2:
        return []

    rets: List[float] = []
    prev = equity[0]
    for cur in equity[1:]:
        if prev <= 0.0:
            raise ValueError("equity contains non-positive previous value; returns undefined")
        rets.append(cur / prev - 1.0)
        prev = cur
    return rets


def max_drawdown(equity: List[float]) -> float:
    """
    Max drawdown as positive fraction: 1 - cur/peak
    """
    if len(equity) < 2:
        return 0.0

    peak = equity[0]
    if peak <= 0.0:
        raise ValueError("equity contains non-positive starting value; drawdown undefined")
    mdd = 0.0

    for cur in equity[1:]:
        if cur > peak:
            peak = cur
            if peak <= 0.0:
                raise ValueError("equity contains non-positive peak; drawdown undefined")
            continue
        # cur <= peak
        dd = 1.0 - (cur / peak)
        if dd > mdd:
            mdd = dd
    return mdd


def sharpe(returns: List[float], risk_free: float = 0.0) -> float:
    """
    Per-step Sharpe ratio with population std-dev (ddof=0).
    Returns 0.0 if insufficient data or zero variance.
    """
    n = len(returns)
    if n < 2:
        return 0.0

    excess = [r - risk_free for r in returns]
    mean = sum(excess) / n
    var = sum((x - mean) ** 2 for x in excess) / n
    if var <= 0.0:
        return 0.0
    return mean / sqrt(var)


def summary_kpis(equity: List[float], risk_free: float = 0.0) -> Dict[str, float]:
    if len(equity) < 2:
        return {
            "total_return": 0.0,
            "max_drawdown": 0.0,
            "sharpe": 0.0,
            "n_steps": float(len(equity)),
        }
    if equity[0] <= 0.0:
        raise ValueError("equity starts non-positive; total_return undefined")

    total_return = equity[-1] / equity[0] - 1.0
    mdd = max_drawdown(equity)
    rets = compute_returns(equity)
    sh = sharpe(rets, risk_free=risk_free)
    return {
        "total_return": float(total_return),
        "max_drawdown": float(mdd),
        "sharpe": float(sh),
        "n_steps": float(len(equity)),
    }
