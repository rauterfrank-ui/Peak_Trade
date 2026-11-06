"""
VaR Core – offline, deterministic foundation (Phase C1).

Single-asset Value-at-Risk with explicit inputs/outputs/units.
Methods: historical, parametric_normal.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Optional

import numpy as np

Method = Literal["historical", "parametric_normal"]

try:
    from scipy.stats import norm as scipy_norm

    _SCIPY_AVAILABLE = True
except ImportError:
    scipy_norm = None
    _SCIPY_AVAILABLE = False

try:
    from statistics import NormalDist

    _NORMALDIST_AVAILABLE = True
except ImportError:
    NormalDist = None
    _NORMALDIST_AVAILABLE = False


def _normal_ppf(p: float) -> float:
    """(1-alpha) quantile of N(0,1). Deterministic."""
    if _SCIPY_AVAILABLE:
        return float(scipy_norm.ppf(p))
    if _NORMALDIST_AVAILABLE:
        return NormalDist().inv_cdf(p)
    raise ImportError("VaR parametric_normal requires scipy or Python 3.8+ statistics.NormalDist")


@dataclass(frozen=True)
class VaRResult:
    method: Method
    alpha: float  # e.g. 0.99
    horizon: int  # in bars/periods
    var: float  # VaR as positive loss number
    sample_size: int


def compute_var(
    returns: np.ndarray,
    *,
    alpha: float = 0.99,
    horizon: int = 1,
    method: Method = "historical",
) -> VaRResult:
    """
    Compute Value-at-Risk (VaR) on a 1D returns series.

    Conventions:
    - `returns` are arithmetic returns per period.
    - VaR is returned as a positive loss magnitude (e.g. 0.02 = 2% loss).
    - `horizon` scales returns by sqrt(horizon) for parametric_normal,
      and by aggregation for historical (simple sqrt scaling here as baseline).
    """
    r = np.asarray(returns, dtype=float)
    r = r[np.isfinite(r)]
    if r.ndim != 1:
        raise ValueError("returns must be 1D")
    if len(r) < 30:
        raise ValueError("returns too short for VaR (need >=30 finite samples)")
    if not (0.5 < alpha < 1.0):
        raise ValueError("alpha must be in (0.5, 1.0)")
    if horizon < 1:
        raise ValueError("horizon must be >=1")

    if method == "historical":
        q = np.quantile(r, 1.0 - alpha)
        var = max(0.0, -q) * np.sqrt(horizon)
        return VaRResult(
            method=method, alpha=alpha, horizon=horizon, var=float(var), sample_size=len(r)
        )

    if method == "parametric_normal":
        mu = float(np.mean(r))
        sigma = float(np.std(r, ddof=1))
        if sigma <= 0.0:
            return VaRResult(
                method=method, alpha=alpha, horizon=horizon, var=0.0, sample_size=len(r)
            )
        z = _normal_ppf(1.0 - alpha)
        var = max(0.0, -(mu + z * sigma)) * np.sqrt(horizon)
        return VaRResult(
            method=method, alpha=alpha, horizon=horizon, var=float(var), sample_size=len(r)
        )

    raise ValueError(f"unknown method: {method}")
