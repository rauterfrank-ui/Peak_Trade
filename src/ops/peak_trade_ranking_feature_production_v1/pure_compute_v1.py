"""Pure B03-ratified volatility and amplitude computation (shared parity seam)."""

from __future__ import annotations

import math
from decimal import Decimal, InvalidOperation

from src.ops.peak_trade_ranking_feature_production_v1.constants_v1 import (
    LOG_RETURN_COUNT,
    MARK_COUNT,
)
from src.ops.peak_trade_ranking_feature_production_v1.reason_codes_v1 import (
    RankingFeatureProductionReasonCodeV1,
)


class RankingFeaturePureComputeError(ValueError):
    """Deterministic pure-compute failure with stable reason code."""

    def __init__(self, code: RankingFeatureProductionReasonCodeV1, detail: str = "") -> None:
        super().__init__(f"{code.value}:{detail}" if detail else code.value)
        self.code = code.value
        self.reason_code = code
        self.detail = detail


def _parse_positive_decimal(raw: str) -> Decimal:
    text = str(raw).strip()
    if not text or text.lower() in {"nan", "inf", "+inf", "-inf", "none", "null"}:
        raise RankingFeaturePureComputeError(
            RankingFeatureProductionReasonCodeV1.NONPOSITIVE_MARK_PRICE,
            text,
        )
    try:
        value = Decimal(text)
    except (InvalidOperation, ValueError, ArithmeticError) as exc:
        raise RankingFeaturePureComputeError(
            RankingFeatureProductionReasonCodeV1.NONPOSITIVE_MARK_PRICE,
            text,
        ) from exc
    if not value.is_finite() or value <= 0:
        raise RankingFeaturePureComputeError(
            RankingFeatureProductionReasonCodeV1.NONPOSITIVE_MARK_PRICE,
            text,
        )
    return value


def population_sigma_log_returns_v1(mark_px: tuple[str, ...]) -> Decimal:
    """Population σ (ddof=0) over 60 log returns from 61 contiguous mark prices."""
    if len(mark_px) != MARK_COUNT:
        raise RankingFeaturePureComputeError(
            RankingFeatureProductionReasonCodeV1.INSUFFICIENT_PT1M_MARK_WARMUP,
            str(len(mark_px)),
        )
    values: list[Decimal] = []
    for raw in mark_px:
        values.append(_parse_positive_decimal(raw))
    logs: list[float] = []
    for prev, cur in zip(values, values[1:]):
        logs.append(math.log(float(cur / prev)))
    if len(logs) != LOG_RETURN_COUNT:
        raise RankingFeaturePureComputeError(
            RankingFeatureProductionReasonCodeV1.INSUFFICIENT_PT1M_MARK_WARMUP,
            str(len(logs)),
        )
    mean = sum(logs) / float(LOG_RETURN_COUNT)
    var = sum((item - mean) ** 2 for item in logs) / float(LOG_RETURN_COUNT)
    if var < 0:
        raise RankingFeaturePureComputeError(
            RankingFeatureProductionReasonCodeV1.COMPUTE_ERROR,
            "NEGATIVE_VARIANCE",
        )
    sigma = math.sqrt(var)
    if not math.isfinite(sigma):
        raise RankingFeaturePureComputeError(
            RankingFeatureProductionReasonCodeV1.COMPUTE_ERROR,
            "NON_FINITE_SIGMA",
        )
    return Decimal(format(sigma, ".16e"))


def pt1m_mid_relative_range_v1(mark_px: tuple[str, ...]) -> Decimal:
    """(MAX-MIN)/mid with mid=(MAX+MIN)/2; requires p_min>0 and mid>0."""
    if len(mark_px) != MARK_COUNT:
        raise RankingFeaturePureComputeError(
            RankingFeatureProductionReasonCodeV1.INSUFFICIENT_PT1M_MARK_WARMUP,
            str(len(mark_px)),
        )
    values: list[Decimal] = []
    for raw in mark_px:
        values.append(_parse_positive_decimal(raw))
    p_min = min(values)
    p_max = max(values)
    if p_min <= 0:
        raise RankingFeaturePureComputeError(
            RankingFeatureProductionReasonCodeV1.AMPLITUDE_PMIN_NONPOSITIVE,
        )
    mid = (p_max + p_min) / Decimal(2)
    if mid <= 0:
        raise RankingFeaturePureComputeError(
            RankingFeatureProductionReasonCodeV1.AMPLITUDE_MID_NONPOSITIVE,
        )
    spread = p_max - p_min
    return spread / mid
