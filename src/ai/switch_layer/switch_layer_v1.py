from __future__ import annotations

from dataclasses import asdict
from typing import Optional, Sequence

from .config_v1 import SwitchLayerConfigV1
from .types_v1 import MarketRegimeV1, SwitchDecisionV1


def _mean(xs: Sequence[float]) -> float:
    return sum(xs) / len(xs)


def _ema(values: Sequence[float], span: int) -> float:
    # deterministic single-value EMA over full series
    # alpha = 2/(span+1)
    alpha = 2.0 / (span + 1.0)
    ema = values[0]
    for v in values[1:]:
        ema = alpha * v + (1.0 - alpha) * ema
    return ema


def _clamp(x: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, x))


def decide_regime_v1(
    returns: Sequence[float],
    cfg: Optional[SwitchLayerConfigV1] = None,
) -> SwitchDecisionV1:
    """
    Simple deterministic regime switch:
    - Uses EMA(fast) vs EMA(slow) on cumulative returns proxy
    - Uses mean return over slow_window to determine bull/bear/neutral with thresholds
    - Produces confidence based on separation + threshold distance

    returns: sequence of per-step returns (e.g., close-to-close pct returns)
    """
    cfg = cfg or SwitchLayerConfigV1()

    n = len(returns)
    if n < cfg.require_min_samples:
        return SwitchDecisionV1(
            regime=MarketRegimeV1.NEUTRAL,
            confidence=cfg.min_confidence,
            evidence={
                "reason": "insufficient_samples",
                "n": n,
                "require_min_samples": cfg.require_min_samples,
                "cfg": asdict(cfg),
            },
        )

    slow_slice = list(returns[-cfg.slow_window :])
    fast_slice = list(returns[-cfg.fast_window :])

    mean_slow = _mean(slow_slice)
    mean_fast = _mean(fast_slice)

    # Build a smooth proxy series: cumulative sum of returns
    cum = []
    acc = 0.0
    for r in returns[-max(cfg.require_min_samples, cfg.slow_window) :]:
        acc += r
        cum.append(acc)

    ema_fast = _ema(cum, cfg.fast_window)
    ema_slow = _ema(cum, cfg.slow_window)
    sep = ema_fast - ema_slow

    # Primary classification based on mean_slow thresholds
    if mean_slow >= cfg.bull_threshold:
        regime = MarketRegimeV1.BULL
        dist = mean_slow - cfg.bull_threshold
    elif mean_slow <= cfg.bear_threshold:
        regime = MarketRegimeV1.BEAR
        dist = cfg.bear_threshold - mean_slow
    else:
        regime = MarketRegimeV1.NEUTRAL
        dist = min(
            abs(mean_slow - cfg.bull_threshold),
            abs(mean_slow - cfg.bear_threshold),
        )

    # Confidence: combine normalized distance + EMA separation sign agreement
    sep_bonus = (
        0.1
        if (
            (regime == MarketRegimeV1.BULL and sep > 0)
            or (regime == MarketRegimeV1.BEAR and sep < 0)
        )
        else 0.0
    )
    dist_score = _clamp(abs(dist) * 50.0, 0.0, 0.4)  # heuristic scaling
    base = cfg.min_confidence + dist_score + sep_bonus
    conf = _clamp(base, cfg.min_confidence, cfg.max_confidence)

    return SwitchDecisionV1(
        regime=regime,
        confidence=conf,
        evidence={
            "mean_slow": mean_slow,
            "mean_fast": mean_fast,
            "ema_fast": ema_fast,
            "ema_slow": ema_slow,
            "sep": sep,
            "dist": dist,
            "sep_bonus": sep_bonus,
            "cfg": asdict(cfg),
            "n": n,
        },
    )
