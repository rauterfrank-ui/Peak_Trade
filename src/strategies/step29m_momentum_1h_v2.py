"""
STEP29M momentum_1h v2 research strategy (offline-only).

Addresses SPARSE_SAMPLE_SINGLE_TRADE_DOMINANCE via versioned minimum-activity and
anti-dominance guards. Signal frequency, regime coverage, holding period, and entry
filters are treated separately; no correlated trade duplication.

Parent v1 remains immutable negative baseline: src/strategies/momentum.py
Scope: STEP29M_MOMENTUM_1H_V2_RESEARCH_SCOPE_V0
"""

from __future__ import annotations

from typing import Any, Dict, Optional

import pandas as pd

from src.strategies.base import BaseStrategy, StrategyMetadata
from src.strategies.momentum import MomentumStrategy

STRATEGY_ID = "momentum_1h"
STRATEGY_VERSION = "v2"
PARENT_STRATEGY_VERSION = "v1"
PARENT_OWNER = "src.strategies.momentum.MomentumStrategy"
SCOPE_ID = "STEP29M_MOMENTUM_1H_V2_RESEARCH_SCOPE_V0"
TERMINAL_FAILURE_CLASS = "SPARSE_SAMPLE_SINGLE_TRADE_DOMINANCE"

RESEARCH_HYPOTHESIS = (
    "Versioned entry threshold reduction with minimum signal spacing and momentum-rise "
    "entry filter improves sample sufficiency while fixed dominance guards prevent "
    "single-trade economic claims."
)

MIN_TRADE_COUNT_GUARD = 30
MAX_SINGLE_TRADE_PROFIT_CONTRIBUTION = 0.35

V2_DEFAULT_PARAMS: dict[str, Any] = {
    "lookback_period": 20,
    "entry_threshold": 0.015,
    "exit_threshold": -0.01,
    "min_bars_between_entries": 12,
    "require_momentum_rise": True,
}


class Momentum1hV2Strategy(MomentumStrategy):
    """Versioned research adapter with activity and anti-dominance guards."""

    KEY = STRATEGY_ID
    RESEARCH_VERSION = STRATEGY_VERSION

    def __init__(
        self,
        lookback_period: int = 20,
        entry_threshold: float = 0.015,
        exit_threshold: float = -0.01,
        min_bars_between_entries: int = 12,
        require_momentum_rise: bool = True,
        config: Optional[Dict[str, Any]] = None,
        metadata: Optional[StrategyMetadata] = None,
    ) -> None:
        merged = dict(V2_DEFAULT_PARAMS)
        if config:
            merged.update(config)
        merged.update(
            {
                "lookback_period": lookback_period,
                "entry_threshold": entry_threshold,
                "exit_threshold": exit_threshold,
                "min_bars_between_entries": min_bars_between_entries,
                "require_momentum_rise": require_momentum_rise,
            }
        )
        if metadata is None:
            metadata = StrategyMetadata(
                name="Momentum 1h v2 (STEP29M Research)",
                description=RESEARCH_HYPOTHESIS,
                version=STRATEGY_VERSION,
                author="Peak_Trade",
                regime="trending",
                tags=["momentum", "step29m", "research_v2"],
            )
        super().__init__(config=merged, metadata=metadata)
        self.min_bars_between_entries = int(
            self.config.get("min_bars_between_entries", min_bars_between_entries)
        )
        self.require_momentum_rise = bool(
            self.config.get("require_momentum_rise", require_momentum_rise)
        )
        self.validate_v2()

    def validate_v2(self) -> None:
        if self.min_bars_between_entries < 0:
            raise ValueError("min_bars_between_entries must be >= 0")

    @staticmethod
    def dominance_guard_contract() -> dict[str, Any]:
        return {
            "min_trade_count": MIN_TRADE_COUNT_GUARD,
            "max_single_trade_profit_contribution": MAX_SINGLE_TRADE_PROFIT_CONTRIBUTION,
            "correlated_trade_duplication_allowed": False,
        }

    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        if "close" not in data.columns:
            raise ValueError("close column required")
        if len(data) < self.lookback_period:
            raise ValueError(f"need at least {self.lookback_period} bars")

        momentum = self.compute_momentum_series(data)
        signals = pd.Series(0, index=data.index, dtype=int)

        cross_up = (momentum.shift(1) < self.entry_threshold) & (momentum > self.entry_threshold)
        if self.require_momentum_rise:
            cross_up = cross_up & (momentum > momentum.shift(1))

        if self.min_bars_between_entries > 0:
            last_entry_idx: Optional[int] = None
            for i, idx in enumerate(data.index):
                if not bool(cross_up.loc[idx]):
                    continue
                if last_entry_idx is not None and (
                    i - last_entry_idx < self.min_bars_between_entries
                ):
                    cross_up.loc[idx] = False
                else:
                    last_entry_idx = i

        cross_down = (momentum.shift(1) > self.exit_threshold) & (momentum < self.exit_threshold)
        signals[cross_up] = 1
        signals[cross_down] = -1
        return signals


def generate_signals(df: pd.DataFrame, params: Dict[str, Any]) -> pd.Series:
    config = dict(V2_DEFAULT_PARAMS)
    config.update(params)
    return Momentum1hV2Strategy(config=config).generate_signals(df)
