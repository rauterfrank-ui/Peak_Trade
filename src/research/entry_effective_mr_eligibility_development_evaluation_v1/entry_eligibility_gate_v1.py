"""Research-only entry-effective eligibility gate (no Master-V2 mutation)."""

from __future__ import annotations

from typing import Any, Mapping

import pandas as pd

from src.backtest.strategy_signal_binding_v1 import (
    StrategySignalBindingResultV1,
    execute_configured_strategy_signal_series_v1,
)
from src.research.entry_effective_mr_eligibility_development_evaluation_v1.atr_percentile_eligibility_filter_v1 import (
    eligibility_mask_from_bars,
)


def apply_eligibility_gate_to_signals(
    signals: pd.Series,
    eligible_mask: pd.Series,
) -> pd.Series:
    """Zero signals at timestamps where the eligibility mask is False.

    Only acts on entries (new signal changes); zeroing a signal at a
    timestamp is equivalent to "no new entry intent" at that timestamp.
    """
    aligned = eligible_mask.reindex(signals.index)
    if aligned.isna().any():
        missing = signals.index.difference(eligible_mask.index)
        if not missing.empty:
            raise ValueError(f"ELIGIBILITY_MASK_INDEX_GAP:{list(missing[:5])}")
        aligned = aligned.fillna(False)
    allowed = aligned.astype(bool)
    return signals.where(allowed, 0).astype(signals.dtype)


def apply_eligibility_to_mapped_position_signal(signal: int, eligible: bool) -> int:
    """Apply the entry-effective eligibility gate to a single mapped MV2 signal.

    ``signal`` is the already-mapped MV2 replay position signal (the output
    of ``map_decision_evidence_to_position_signal_v1``: ``1`` for
    ``enter_long``, ``-1`` for ``enter_short``, ``0`` otherwise). Only new
    entry intent (``+1``/``-1``) is affected: when ``eligible`` is False the
    signal is forced to ``0`` (stand aside). ``0`` (flat/exit) always passes
    through unchanged regardless of eligibility.
    """
    sig = int(signal)
    if sig != 0 and not bool(eligible):
        return 0
    return sig


def execute_gated_configured_strategy_signal_series_v1(
    bars: pd.DataFrame,
    *,
    strategy_id: str,
    cfg: Mapping[str, Any],
) -> StrategySignalBindingResultV1:
    """Baseline configured strategy, then research-only pre-entry eligibility mask."""
    base = execute_configured_strategy_signal_series_v1(
        bars,
        strategy_id=strategy_id,
        cfg=cfg,
    )
    mask = eligibility_mask_from_bars(bars)
    gated = apply_eligibility_gate_to_signals(base.signals, mask)
    return StrategySignalBindingResultV1(signals=gated, provenance=base.provenance)


__all__ = [
    "apply_eligibility_gate_to_signals",
    "apply_eligibility_to_mapped_position_signal",
    "execute_gated_configured_strategy_signal_series_v1",
]
