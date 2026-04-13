"""
Christoffersen Independence + Conditional Coverage Tests (validation layer).

Thin wrappers around the canonical stdlib implementation in
``src.risk_layer.var_backtest.christoffersen_tests`` (Phase 8B), mirroring the
pattern used for Kupiec in ``kupiec_pof.py``.

Legacy API (``ChristoffersenIndependenceResult``, ``independence_test``, …)
is preserved for ``suite_runner`` and existing call sites.

References:
-----------
- Christoffersen, P. F. (1998). Evaluating Interval Forecasts.
  International Economic Review, 39(4), 841-862.
"""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from src.risk_layer.var_backtest.christoffersen_tests import (
    christoffersen_lr_cc as _canonical_christoffersen_lr_cc,
    christoffersen_lr_ind as _canonical_christoffersen_lr_ind,
)


@dataclass
class ChristoffersenIndependenceResult:
    """Result of Independence Test (legacy shape for suite reports)."""

    is_valid: bool
    p_value: float
    lr_statistic: float


@dataclass
class ChristoffersenConditionalCoverageResult:
    """Result of Conditional Coverage Test (legacy shape for suite reports)."""

    is_valid: bool
    p_value: float
    lr_cc_statistic: float


def independence_test(
    breaches_bool: pd.Series,
    significance: float = 0.05,
) -> ChristoffersenIndependenceResult:
    """
    Christoffersen independence test (LR-IND) on a breach indicator series.

    Delegates to :func:`christoffersen_lr_ind` with the same breach convention
    as the suite runner (True = loss exceeds VaR).
    """
    seq = [bool(x) for x in breaches_bool.tolist()]
    n = len(seq)
    if n < 2:
        return ChristoffersenIndependenceResult(
            is_valid=False,
            p_value=1.0,
            lr_statistic=0.0,
        )

    r = _canonical_christoffersen_lr_ind(seq, p_threshold=significance)
    return ChristoffersenIndependenceResult(
        is_valid=(r.verdict == "PASS"),
        p_value=float(r.p_value),
        lr_statistic=float(r.lr_ind),
    )


def conditional_coverage_test(
    breaches: int,
    observations: int,
    breaches_bool: pd.Series,
    confidence_level: float = 0.95,
    significance: float = 0.05,
) -> ChristoffersenConditionalCoverageResult:
    """
    Christoffersen conditional coverage test (LR-CC).

    ``alpha`` for the joint test is the expected exceedance rate ``1 - confidence_level``
    (e.g. 95%% VaR → 5%% tail).

    Delegates to :func:`christoffersen_lr_cc`.
    """
    seq = [bool(x) for x in breaches_bool.tolist()]
    if len(seq) != observations:
        raise ValueError(
            f"breaches_bool length ({len(seq)}) must match observations ({observations})"
        )
    if sum(seq) != breaches:
        raise ValueError(f"breaches_bool sum ({sum(seq)}) must match breaches ({breaches})")

    n = len(seq)
    if n < 2:
        return ChristoffersenConditionalCoverageResult(
            is_valid=False,
            p_value=1.0,
            lr_cc_statistic=0.0,
        )

    alpha_exceedance = 1.0 - confidence_level
    if not 0 < alpha_exceedance < 1:
        raise ValueError(
            f"Invalid implied exceedance rate {alpha_exceedance} from confidence_level={confidence_level}"
        )

    r = _canonical_christoffersen_lr_cc(
        seq,
        alpha_exceedance,
        p_threshold=significance,
    )
    return ChristoffersenConditionalCoverageResult(
        is_valid=(r.verdict == "PASS"),
        p_value=float(r.p_value),
        lr_cc_statistic=float(r.lr_cc),
    )
