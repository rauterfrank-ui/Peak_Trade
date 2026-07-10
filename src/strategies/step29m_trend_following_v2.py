"""
STEP29M trend_following v2 research strategy (offline-only).

Addresses NEGATIVE_NET_EDGE_WITH_ADEQUATE_TRADE_ACTIVITY via a single causal hypothesis:
late exits during weakening-but-not-reversed trends erode net edge. v2 preserves v1 entry
semantics and adds DI-spread-confirmed exit timing plus turnover cooldown — no signal
starvation, no cost/period/policy relaxation.

Parent v1 remains immutable negative baseline: src/strategies/trend_following.py
Scope: STEP29M_TREND_FOLLOWING_V2_RESEARCH_SCOPE_V0
"""

from __future__ import annotations

from typing import Any, Dict, Optional

import numpy as np
import pandas as pd

from src.strategies.base import BaseStrategy, StrategyMetadata
from src.strategies.trend_following import TrendFollowingStrategy

STRATEGY_ID = "trend_following"
STRATEGY_VERSION = "v2"
PARENT_STRATEGY_VERSION = "v1"
PARENT_OWNER = "src.strategies.trend_following.TrendFollowingStrategy"
SCOPE_ID = "STEP29M_TREND_FOLLOWING_V2_RESEARCH_SCOPE_V0"
TERMINAL_FAILURE_CLASS = "NEGATIVE_NET_EDGE_WITH_ADEQUATE_TRADE_ACTIVITY"

RESEARCH_HYPOTHESIS = (
    "DI-spread-confirmed exit timing reduces premature exits during transient ADX dips "
    "while turnover cooldown limits re-entry churn; v1 entry semantics unchanged."
)

V2_DEFAULT_PARAMS: dict[str, Any] = {
    "adx_period": 14,
    "adx_threshold": 25.0,
    "exit_threshold": 20.0,
    "ma_period": 50,
    "use_ma_filter": True,
    "exit_di_spread_min": 5.0,
    "min_bars_between_entries": 4,
}


class TrendFollowingV2Strategy(TrendFollowingStrategy):
    """Versioned research adapter extending immutable v1 entry semantics."""

    KEY = STRATEGY_ID
    RESEARCH_VERSION = STRATEGY_VERSION

    def __init__(
        self,
        adx_period: int = 14,
        adx_threshold: float = 25.0,
        exit_threshold: float = 20.0,
        ma_period: int = 50,
        use_ma_filter: bool = True,
        exit_di_spread_min: float = 5.0,
        min_bars_between_entries: int = 4,
        config: Optional[Dict[str, Any]] = None,
        metadata: Optional[StrategyMetadata] = None,
    ) -> None:
        initial_config = dict(V2_DEFAULT_PARAMS)
        if config:
            initial_config.update(config)
        initial_config.update(
            {
                "adx_period": adx_period,
                "adx_threshold": adx_threshold,
                "exit_threshold": exit_threshold,
                "ma_period": ma_period,
                "use_ma_filter": use_ma_filter,
                "exit_di_spread_min": exit_di_spread_min,
                "min_bars_between_entries": min_bars_between_entries,
            }
        )
        if metadata is None:
            metadata = StrategyMetadata(
                name="Trend Following v2 (STEP29M Research)",
                description=RESEARCH_HYPOTHESIS,
                version=STRATEGY_VERSION,
                author="Peak_Trade",
                regime="trending",
                tags=["trend", "adx", "step29m", "research_v2"],
            )
        super().__init__(config=initial_config, metadata=metadata)
        self.exit_di_spread_min = float(self.config.get("exit_di_spread_min", exit_di_spread_min))
        self.min_bars_between_entries = int(
            self.config.get("min_bars_between_entries", min_bars_between_entries)
        )
        self.validate_v2()

    def validate_v2(self) -> None:
        if self.exit_di_spread_min < 0:
            raise ValueError("exit_di_spread_min must be >= 0")
        if self.min_bars_between_entries < 0:
            raise ValueError("min_bars_between_entries must be >= 0")

    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        required_cols = ["high", "low", "close"]
        for col in required_cols:
            if col not in data.columns:
                raise ValueError(f"missing column: {col}")

        min_bars = max(self.adx_period * 2, self.ma_period) + 10
        if len(data) < min_bars:
            raise ValueError(f"need at least {min_bars} bars, got {len(data)}")

        adx, plus_di, minus_di = self._compute_adx(data)
        ma = data["close"].rolling(window=self.ma_period).mean()
        di_spread = (plus_di - minus_di).abs()

        signals = pd.Series(0, index=data.index, dtype=int)

        adx_strong = adx > self.adx_threshold
        uptrend = plus_di > minus_di
        if self.use_ma_filter:
            entry_condition = adx_strong & uptrend & (data["close"] > ma)
        else:
            entry_condition = adx_strong & uptrend

        adx_weak = adx < self.exit_threshold
        downtrend = minus_di > plus_di
        di_spread_confirmed = di_spread >= self.exit_di_spread_min
        exit_condition = (adx_weak & di_spread_confirmed) | (downtrend & di_spread_confirmed)

        entry_trigger = entry_condition & ~entry_condition.shift(1, fill_value=False).astype(bool)
        if self.min_bars_between_entries > 0:
            last_entry_idx: Optional[int] = None
            for i, idx in enumerate(data.index):
                if not bool(entry_trigger.loc[idx]):
                    continue
                if last_entry_idx is not None and (
                    i - last_entry_idx < self.min_bars_between_entries
                ):
                    entry_trigger.loc[idx] = False
                else:
                    last_entry_idx = i

        exit_trigger = exit_condition & ~exit_condition.shift(1, fill_value=False).astype(bool)

        signals[entry_trigger] = 1
        signals[exit_trigger] = -1
        return signals


def generate_signals(df: pd.DataFrame, params: Dict[str, Any]) -> pd.Series:
    config = dict(V2_DEFAULT_PARAMS)
    config.update(params)
    return TrendFollowingV2Strategy(config=config).generate_signals(df)
