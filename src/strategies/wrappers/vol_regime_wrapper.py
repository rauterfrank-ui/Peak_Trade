# src/strategies/wrappers/vol_regime_wrapper.py
"""
Universal vol-regime wrapper: gates signals/positions by allowed regimes.

Wraps any strategy-like object that provides generate_signals(data) -> pd.Series.
Masks output outside allowed_regimes (and optionally allows NaN/unknown labels).
Research/backtest only; deterministic.
"""

from __future__ import annotations

import logging
from typing import List, Set, Union

import pandas as pd

logger = logging.getLogger(__name__)


class VolRegimeWrapper:
    """
    Wraps a base strategy and masks signals or positions outside allowed regimes.

    The base_strategy is called as usual; the resulting series is then
    element-wise gated by regime_labels: only indices where the label is in
    allowed_regimes (or unknown if allow_unknown=True) pass through; others
    are zeroed.
    """

    def __init__(
        self,
        base_strategy,
        regime_labels: pd.Series,
        allowed_regimes: Union[Set[str], List[str]],
        mode: str = "signals",
        allow_unknown: bool = False,
    ) -> None:
        """
        Args:
            base_strategy: Object with generate_signals(data: pd.DataFrame) -> pd.Series.
            regime_labels: Series of regime labels, index aligned to signal index.
            allowed_regimes: Regime values that pass the gate.
            mode: "signals" or "positions" (same gating logic; for audit/logging).
            allow_unknown: If True, treat NaN/None in regime_labels as allowed.
        """
        self.base_strategy = base_strategy
        self.regime_labels = regime_labels
        self._allowed = set(allowed_regimes) if not isinstance(allowed_regimes, set) else allowed_regimes
        if mode not in ("signals", "positions"):
            raise ValueError(f"mode must be 'signals' or 'positions', got {mode!r}")
        self.mode = mode
        self.allow_unknown = allow_unknown

    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """
        Produce gated signals: base_strategy.generate_signals(data) then mask by regime.
        """
        raw = self.base_strategy.generate_signals(data)
        return self._apply_gate(raw)

    def _apply_gate(self, series: pd.Series) -> pd.Series:
        # Align regime_labels to series index; strict: no missing, no extra
        try:
            aligned = self.regime_labels.reindex(series.index)
        except Exception as e:
            raise ValueError(
                f"regime_labels could not be aligned to series index: {e}"
            ) from e
        if aligned.isna().any() and not self.allow_unknown:
            # Check for labels missing from regime_labels index (reindex produced NaN)
            missing = series.index.difference(self.regime_labels.index)
            if not missing.empty:
                raise ValueError(
                    f"regime_labels index does not cover all signal index entries. "
                    f"Missing (first 5): {list(missing[:5])}"
                )
        # Build allowed mask: in allowed set, or (allow_unknown and NaN)
        in_allowed = aligned.isin(self._allowed)
        if self.allow_unknown:
            allowed_mask = in_allowed | aligned.isna()
        else:
            allowed_mask = in_allowed.fillna(False)
        if not allowed_mask.index.equals(series.index):
            raise ValueError(
                "regime_labels alignment produced index mismatch with signal series"
            )
        out = series.where(allowed_mask, 0).astype(series.dtype)
        logger.info(
            "vol_regime_wrapper applied: allowed_regimes=%s, allow_unknown=%s, mode=%s",
            self._allowed,
            self.allow_unknown,
            self.mode,
        )
        return out
