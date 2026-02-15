from __future__ import annotations

from typing import Optional, Sequence

from src.ai.switch_layer import (
    MarketRegimeV1,
    SwitchDecisionV1,
    SwitchLayerConfigV1,
    decide_regime_v1,
)


def compute_market_regime_v1(
    returns: Sequence[float],
    cfg: Optional[SwitchLayerConfigV1] = None,
) -> SwitchDecisionV1:
    """
    Orchestration-safe wrapper (pure, deterministic). Does NOT trigger any AI calls.
    Intended to be mounted into higher-level decision contexts later.
    """
    return decide_regime_v1(returns=returns, cfg=cfg)
