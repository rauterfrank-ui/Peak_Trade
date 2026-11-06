"""Research-only entry-eligibility / stand-aside gate (no Master-V2 mutation)."""

from __future__ import annotations

from typing import Any, Mapping

import pandas as pd

from src.backtest.strategy_signal_binding_v1 import (
    StrategySignalBindingResultV1,
    execute_configured_strategy_signal_series_v1,
)
from src.research.regime_gated_standaside_mr_development_evaluation_v1.regime_features_v1 import (
    REGIME_RANGE,
    regime_labels_from_close,
)


def apply_standaside_gate_to_signals(
    signals: pd.Series,
    regime_labels: pd.Series,
) -> pd.Series:
    """Zero signals outside RANGE_BOUND (stand aside / no new entry intent)."""
    aligned = regime_labels.reindex(signals.index)
    if aligned.isna().any():
        missing = signals.index.difference(regime_labels.index)
        if not missing.empty:
            raise ValueError(f"REGIME_LABEL_INDEX_GAP:{list(missing[:5])}")
        aligned = aligned.fillna("TREND_STRONG")
    allowed = aligned.eq(REGIME_RANGE)
    return signals.where(allowed, 0).astype(signals.dtype)


def execute_gated_configured_strategy_signal_series_v1(
    bars: pd.DataFrame,
    *,
    strategy_id: str,
    cfg: Mapping[str, Any],
) -> StrategySignalBindingResultV1:
    """Baseline configured strategy, then research-only RANGE_BOUND eligibility mask."""
    base = execute_configured_strategy_signal_series_v1(
        bars,
        strategy_id=strategy_id,
        cfg=cfg,
    )
    labels = regime_labels_from_close(bars["close"])
    gated = apply_standaside_gate_to_signals(base.signals, labels)
    return StrategySignalBindingResultV1(signals=gated, provenance=base.provenance)


__all__ = [
    "apply_standaside_gate_to_signals",
    "execute_gated_configured_strategy_signal_series_v1",
]
