"""
STEP29M bollinger_bands v2 research strategy (offline-only, diagnostic-first).

Addresses ZERO_TRADE_EXECUTION_DEGENERATION via trade-eligibility and gate-trace surfaces.
Signal generation matches v1; v2 adds per-bar eligibility classification without forcing
trades or relaxing survival/suitability/risk/safety/economic policy gates.

Parent v1 remains immutable negative baseline: src/strategies/bollinger.py
Scope: STEP29M_BOLLINGER_BANDS_V2_RESEARCH_SCOPE_V0
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Dict, Optional

import pandas as pd

from src.strategies.base import BaseStrategy, StrategyMetadata
from src.strategies.bollinger import BollingerBandsStrategy, _calculate_bollinger_bands

STRATEGY_ID = "bollinger_bands"
STRATEGY_VERSION = "v2"
PARENT_STRATEGY_VERSION = "v1"
PARENT_OWNER = "src.strategies.bollinger.BollingerBandsStrategy"
SCOPE_ID = "STEP29M_BOLLINGER_BANDS_V2_RESEARCH_SCOPE_V0"
TERMINAL_FAILURE_CLASS = "ZERO_TRADE_EXECUTION_DEGENERATION"

RESEARCH_HYPOTHESIS = (
    "Zero-trade degeneration is diagnosable via signal-to-execution eligibility traces "
    "distinguishing signal inactivity, regime block, parameter degeneration, binding error, "
    "and canonical gate block — without artificial trade forcing."
)

V2_DEFAULT_PARAMS: dict[str, Any] = {
    "bb_period": 20,
    "bb_std": 2.0,
    "entry_threshold": 0.95,
    "exit_threshold": 0.50,
}


class EligibilityClassification(str, Enum):
    SIGNAL_INACTIVE = "SIGNAL_INACTIVE"
    SIGNAL_ACTIVE = "SIGNAL_ACTIVE"
    ENTRY_CANDIDATE = "ENTRY_CANDIDATE"
    REGIME_BLOCK = "REGIME_BLOCK"
    PARAMETER_DEGENERATE = "PARAMETER_DEGENERATE"
    BINDING_ERROR = "BINDING_ERROR"
    CANONICAL_GATE_BLOCK = "CANONICAL_GATE_BLOCK"


class BollingerBandsV2Strategy(BollingerBandsStrategy):
    """Diagnostic-first v2 adapter; v1 signal semantics preserved."""

    KEY = STRATEGY_ID
    RESEARCH_VERSION = STRATEGY_VERSION

    def __init__(
        self,
        bb_period: int = 20,
        bb_std: float = 2.0,
        entry_threshold: float = 0.95,
        exit_threshold: float = 0.50,
        config: Optional[Dict[str, Any]] = None,
        metadata: Optional[StrategyMetadata] = None,
    ) -> None:
        if metadata is None:
            metadata = StrategyMetadata(
                name="Bollinger Bands v2 (STEP29M Research)",
                description=RESEARCH_HYPOTHESIS,
                version=STRATEGY_VERSION,
                author="Peak_Trade",
                regime="ranging",
                tags=["mean-reversion", "bollinger", "step29m", "research_v2"],
            )
        merged = dict(V2_DEFAULT_PARAMS)
        if config:
            merged.update(config)
        super().__init__(
            bb_period=bb_period,
            bb_std=bb_std,
            entry_threshold=entry_threshold,
            exit_threshold=exit_threshold,
            config=merged,
            metadata=metadata,
        )

    def classify_eligibility_bar(
        self,
        *,
        close: float,
        prev_close: float,
        entry_level: float,
        prev_entry_level: float,
        exit_level: float,
        prev_exit_level: float,
        band_width: float,
        signal: int,
    ) -> EligibilityClassification:
        if self.bb_period <= 0 or self.bb_std <= 0:
            return EligibilityClassification.PARAMETER_DEGENERATE
        if not (0 < self.entry_threshold <= 1):
            return EligibilityClassification.PARAMETER_DEGENERATE
        if pd.isna(entry_level) or pd.isna(exit_level) or pd.isna(band_width):
            return EligibilityClassification.PARAMETER_DEGENERATE
        if band_width <= 0:
            return EligibilityClassification.PARAMETER_DEGENERATE

        cross_entry = (prev_close > prev_entry_level) and (close <= entry_level)
        if signal == 1 or cross_entry:
            return EligibilityClassification.ENTRY_CANDIDATE
        if signal == -1:
            return EligibilityClassification.SIGNAL_ACTIVE
        if close <= entry_level:
            return EligibilityClassification.SIGNAL_ACTIVE
        return EligibilityClassification.SIGNAL_INACTIVE

    def generate_trade_eligibility_trace(self, data: pd.DataFrame) -> pd.DataFrame:
        if "close" not in data.columns:
            raise ValueError("close column required")
        if len(data) < self.bb_period:
            raise ValueError(f"need at least {self.bb_period} bars")

        upper, middle, lower = _calculate_bollinger_bands(
            data["close"], period=self.bb_period, num_std=self.bb_std
        )
        entry_level = lower * self.entry_threshold
        exit_level = middle
        band_width = upper - lower
        signals = self.generate_signals(data)

        rows: list[dict[str, Any]] = []
        closes = data["close"]
        for i, idx in enumerate(data.index):
            prev_close = float(closes.iloc[i - 1]) if i > 0 else float(closes.iloc[i])
            classification = self.classify_eligibility_bar(
                close=float(closes.iloc[i]),
                prev_close=prev_close,
                entry_level=float(entry_level.iloc[i]),
                prev_entry_level=float(entry_level.iloc[i - 1])
                if i > 0
                else float(entry_level.iloc[i]),
                exit_level=float(exit_level.iloc[i]),
                prev_exit_level=float(exit_level.iloc[i - 1])
                if i > 0
                else float(exit_level.iloc[i]),
                band_width=float(band_width.iloc[i]),
                signal=int(signals.iloc[i]),
            )
            rows.append(
                {
                    "timestamp": str(idx),
                    "signal": int(signals.iloc[i]),
                    "close": float(closes.iloc[i]),
                    "entry_level": float(entry_level.iloc[i]),
                    "exit_level": float(exit_level.iloc[i]),
                    "band_width": float(band_width.iloc[i]),
                    "eligibility_classification": classification.value,
                    "gate_trace_stage": "SIGNAL_TO_ENTRY_ELIGIBILITY",
                }
            )

        trace = pd.DataFrame(rows)
        trace.attrs["entry_candidate_count"] = int(
            (
                trace["eligibility_classification"]
                == EligibilityClassification.ENTRY_CANDIDATE.value
            ).sum()
        )
        trace.attrs["signal_active_count"] = int(
            (
                trace["eligibility_classification"] == EligibilityClassification.SIGNAL_ACTIVE.value
            ).sum()
        )
        trace.attrs["signal_inactive_count"] = int(
            (
                trace["eligibility_classification"]
                == EligibilityClassification.SIGNAL_INACTIVE.value
            ).sum()
        )
        return trace

    def summarize_gate_trace(self, trace: pd.DataFrame) -> dict[str, int]:
        counts = trace["eligibility_classification"].value_counts().to_dict()
        return {str(k): int(v) for k, v in counts.items()}


def generate_signals(df: pd.DataFrame, params: Dict[str, Any]) -> pd.Series:
    config = dict(V2_DEFAULT_PARAMS)
    config.update(params)
    return BollingerBandsV2Strategy(config=config).generate_signals(df)
