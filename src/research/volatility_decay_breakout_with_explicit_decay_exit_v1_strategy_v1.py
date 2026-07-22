"""VOLATILITY_DECAY_BREAKOUT_WITH_EXPLICIT_DECAY_EXIT_V1 strategy producer.

Preserves VDB decay entry thesis; adds ex-ante exit-reachability gating and an
explicit deterministic exit state machine. No PnL/equity/stats truth. No evaluation.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional

import numpy as np
import pandas as pd

from src.research.volatility_decay_breakout_v1_strategy_v1 import (
    VolatilityDecayBreakoutEventV1 as _VdbEvent,
)
from src.research.volatility_decay_breakout_v1_strategy_v1 import (
    generate_volatility_decay_breakout_events_v1,
)
from src.research.volatility_decay_breakout_v1_vol_state_v1 import (
    compute_atr14_v1,
    compute_normalized_atr14_v1,
    compute_percentile_rank_120_normalized_atr_v1,
)
from src.research.volatility_decay_breakout_with_explicit_decay_exit_v1_exit_state_machine_v1 import (
    COOLDOWN_BARS_AFTER_EXIT_V1,
    EXIT_PRECEDENCE_ASCENDING_WINS_FIRST_V1,
    ExplicitDecayExitReasonV1,
    MIN_POST_FILL_BARS_REQUIRED_INCLUSIVE_V1,
    SIGNAL_LAG_BARS_V1,
    TIME_EXIT_MAX_BARS_V1,
    entry_exit_reachable_ex_ante_v1,
    evaluate_exit_on_bar_v1,
    open_position_from_fill_v1,
)
from src.trading.master_v2.strategy_suitability_agreement_material_v1 import (
    StrategyAgreementEventKindV1,
    StrategyEntrySideCarrierV1,
)

STRATEGY_IDENTITY_V1 = "VOLATILITY_DECAY_BREAKOUT_WITH_EXPLICIT_DECAY_EXIT_V1"
STRATEGY_ID_V1 = "volatility_decay_breakout_with_explicit_decay_exit"
STRATEGY_VERSION_V1 = "v1"
SIGNAL_FAMILY_V1 = "VOLATILITY_REGIME"
PROGRAM_ID_V1 = "VOLATILITY_REGIME_RESEARCH_PROGRAM_V1"
BASELINE_ID_V1 = "UNCONDITIONAL_20_BAR_PRICE_CHANNEL_BREAKOUT_V1"
PREDECESSOR_STRATEGY_ID_V1 = "VOLATILITY_DECAY_BREAKOUT_V1"

EXIT_STATE_MACHINE_IMPLEMENTED_V1 = True
PRODUCTIVE_EXIT_PNL_EVALUATOR_REF_V1 = (
    "src/research/volatility_compression_breakout_v1_development_evaluation_v1/"
    "productive_exit_pnl_evaluator_v1.py"
)

EXIT_PARAMS_V1 = {
    "initial_stop_atr_multiple": 1.5,
    "trailing_stop_atr_multiple": 2.0,
    "signal_exit_percentile_inclusive_min": 0.70,
    "regime_invalidation_percentile_rank_lt": 0.50,
    "time_exit_max_bars": TIME_EXIT_MAX_BARS_V1,
    "cooldown_bars_after_exit": COOLDOWN_BARS_AFTER_EXIT_V1,
    "min_post_fill_bars_required_inclusive": MIN_POST_FILL_BARS_REQUIRED_INCLUSIVE_V1,
    "first_event_wins": True,
    "precedence": list(EXIT_PRECEDENCE_ASCENDING_WINS_FIRST_V1),
    "exit_state_machine_implemented": True,
    "entry_only_implementation": False,
    "new_pnl_implementation_forbidden": True,
    "second_pnl_truth_forbidden": True,
    "second_equity_truth_forbidden": True,
    "second_stats_truth_forbidden": True,
    "synthetic_fills_solely_to_pair_trades_forbidden": True,
    "evaluator_side_reconstruction_of_missing_strategy_exits_forbidden": True,
    "productive_exit_pnl_evaluator_ref": PRODUCTIVE_EXIT_PNL_EVALUATOR_REF_V1,
}


class VdbxEventV1(str, Enum):
    ENTRY_EVENT = "ENTRY_EVENT"
    EXIT_EVENT = "EXIT_EVENT"
    NONE = "NONE"


class VdbxReasonV1(str, Enum):
    SUCCESSFUL_ENTRY = "SUCCESSFUL_ENTRY"
    EXIT_EMITTED = "EXIT_EMITTED"
    ENTRY_SUPPRESSED_EXIT_UNREACHABLE = "ENTRY_SUPPRESSED_EXIT_UNREACHABLE"
    NO_EVENT = "NO_EVENT"
    POSITION_OPEN = "POSITION_OPEN"
    AWAITING_FILL = "AWAITING_FILL"
    COOLDOWN = "COOLDOWN"


@dataclass(frozen=True)
class VdbxBarResultV1:
    event: VdbxEventV1
    entry_side: StrategyEntrySideCarrierV1
    event_kind: StrategyAgreementEventKindV1
    reason: VdbxReasonV1
    exit_reason: Optional[ExplicitDecayExitReasonV1] = None
    exit_price: Optional[float] = None
    fill_index: Optional[int] = None
    signal_index: Optional[int] = None


@dataclass(frozen=True)
class VdbxRoundtripV1:
    side: str
    signal_index: int
    fill_index: int
    exit_index: int
    entry_price: float
    exit_price: float
    exit_reason: ExplicitDecayExitReasonV1


def generate_vdbx_events_and_roundtrips_v1(
    data: pd.DataFrame,
    *,
    high_col: str = "high",
    low_col: str = "low",
    close_col: str = "close",
    open_col: str = "open",
    is_panel_last_bar_mask: Optional[np.ndarray] = None,
) -> tuple[list[VdbxBarResultV1], list[VdbxRoundtripV1]]:
    """Generate entry/exit events with guaranteed exit reachability for admitted entries."""
    for col in (high_col, low_col, close_col, open_col):
        if col not in data.columns:
            raise ValueError(f"missing_column:{col}")

    n = len(data)
    if n == 0:
        return [], []

    vdb_events = generate_volatility_decay_breakout_events_v1(
        data, high_col=high_col, low_col=low_col, close_col=close_col
    )
    high = data[high_col].astype(float)
    low = data[low_col].astype(float)
    close = data[close_col].astype(float)
    open_ = data[open_col].astype(float)
    atr = compute_atr14_v1(high, low, close)
    norm = compute_normalized_atr14_v1(high, low, close)
    rank = compute_percentile_rank_120_normalized_atr_v1(norm)

    if is_panel_last_bar_mask is None:
        panel_last = np.zeros(n, dtype=bool)
        panel_last[-1] = True
    else:
        panel_last = np.asarray(is_panel_last_bar_mask, dtype=bool)
        if len(panel_last) != n:
            raise ValueError("PANEL_LAST_MASK_LENGTH_MISMATCH")

    results: list[VdbxBarResultV1] = [
        VdbxBarResultV1(
            event=VdbxEventV1.NONE,
            entry_side=StrategyEntrySideCarrierV1.NONE,
            event_kind=StrategyAgreementEventKindV1.NONE,
            reason=VdbxReasonV1.NO_EVENT,
        )
        for _ in range(n)
    ]
    roundtrips: list[VdbxRoundtripV1] = []

    pending_signal: Optional[tuple[int, StrategyEntrySideCarrierV1]] = None
    position = None
    pending_roundtrip_meta: Optional[tuple[int, int, float]] = None
    cooldown_until = -1

    for i in range(n):
        if i < cooldown_until:
            results[i] = VdbxBarResultV1(
                event=VdbxEventV1.NONE,
                entry_side=StrategyEntrySideCarrierV1.NONE,
                event_kind=StrategyAgreementEventKindV1.NONE,
                reason=VdbxReasonV1.COOLDOWN,
            )
            continue

        if pending_signal is not None:
            sig_i, side = pending_signal
            fill_i = sig_i + SIGNAL_LAG_BARS_V1
            if i == fill_i:
                entry_px = float(open_.iloc[i])
                atr_fill = float(atr.iloc[i]) if np.isfinite(atr.iloc[i]) else float("nan")
                if not np.isfinite(entry_px) or not np.isfinite(atr_fill) or atr_fill <= 0:
                    raise ValueError(f"MISSING_FILL_DATA_FAIL_CLOSED:{i}")
                position = open_position_from_fill_v1(
                    side=side.value,  # type: ignore[arg-type]
                    fill_index=fill_i,
                    entry_price=entry_px,
                    atr_at_fill=atr_fill,
                )
                pending_roundtrip_meta = (sig_i, fill_i, entry_px)
                pending_signal = None
                results[i] = VdbxBarResultV1(
                    event=VdbxEventV1.NONE,
                    entry_side=StrategyEntrySideCarrierV1.NONE,
                    event_kind=StrategyAgreementEventKindV1.NONE,
                    reason=VdbxReasonV1.POSITION_OPEN,
                    fill_index=fill_i,
                    signal_index=sig_i,
                )
                continue
            if i < fill_i:
                results[i] = VdbxBarResultV1(
                    event=VdbxEventV1.NONE,
                    entry_side=StrategyEntrySideCarrierV1.NONE,
                    event_kind=StrategyAgreementEventKindV1.NONE,
                    reason=VdbxReasonV1.AWAITING_FILL,
                    signal_index=sig_i,
                )
                continue

        if position is not None and pending_roundtrip_meta is not None:
            if i <= position.fill_index:
                results[i] = VdbxBarResultV1(
                    event=VdbxEventV1.NONE,
                    entry_side=StrategyEntrySideCarrierV1.NONE,
                    event_kind=StrategyAgreementEventKindV1.NONE,
                    reason=VdbxReasonV1.POSITION_OPEN,
                    fill_index=position.fill_index,
                    signal_index=pending_roundtrip_meta[0],
                )
                continue
            h = float(high.iloc[i])
            lo = float(low.iloc[i])
            c = float(close.iloc[i])
            atr_i = float(atr.iloc[i]) if np.isfinite(atr.iloc[i]) else None
            pct_i = float(rank.iloc[i]) if np.isfinite(rank.iloc[i]) else None
            decision, position = evaluate_exit_on_bar_v1(
                position,
                bar_index=i,
                high=h,
                low=lo,
                close=c,
                atr=atr_i,
                percentile_rank=pct_i,
                is_last_instrument_bar=(i == n - 1),
                is_last_panel_bar=bool(panel_last[i]),
            )
            if decision is not None:
                sig_i, fill_i, entry_px = pending_roundtrip_meta
                roundtrips.append(
                    VdbxRoundtripV1(
                        side=decision.side,
                        signal_index=sig_i,
                        fill_index=fill_i,
                        exit_index=decision.exit_index,
                        entry_price=entry_px,
                        exit_price=decision.exit_price,
                        exit_reason=decision.reason,
                    )
                )
                results[i] = VdbxBarResultV1(
                    event=VdbxEventV1.EXIT_EVENT,
                    entry_side=StrategyEntrySideCarrierV1.NONE,
                    event_kind=StrategyAgreementEventKindV1.NONE,
                    reason=VdbxReasonV1.EXIT_EMITTED,
                    exit_reason=decision.reason,
                    exit_price=decision.exit_price,
                    fill_index=fill_i,
                    signal_index=sig_i,
                )
                position = None
                pending_roundtrip_meta = None
                cooldown_until = i + 1 + COOLDOWN_BARS_AFTER_EXIT_V1
                continue
            results[i] = VdbxBarResultV1(
                event=VdbxEventV1.NONE,
                entry_side=StrategyEntrySideCarrierV1.NONE,
                event_kind=StrategyAgreementEventKindV1.NONE,
                reason=VdbxReasonV1.POSITION_OPEN,
                fill_index=position.fill_index,
                signal_index=pending_roundtrip_meta[0],
            )
            continue

        vdb = vdb_events[i]
        if vdb.event is _VdbEvent.ENTRY_EVENT:
            if not entry_exit_reachable_ex_ante_v1(signal_index=i, series_length=n):
                results[i] = VdbxBarResultV1(
                    event=VdbxEventV1.NONE,
                    entry_side=StrategyEntrySideCarrierV1.NONE,
                    event_kind=StrategyAgreementEventKindV1.NONE,
                    reason=VdbxReasonV1.ENTRY_SUPPRESSED_EXIT_UNREACHABLE,
                    signal_index=i,
                )
                continue
            pending_signal = (i, vdb.entry_side)
            results[i] = VdbxBarResultV1(
                event=VdbxEventV1.ENTRY_EVENT,
                entry_side=vdb.entry_side,
                event_kind=StrategyAgreementEventKindV1.ENTRY,
                reason=VdbxReasonV1.SUCCESSFUL_ENTRY,
                signal_index=i,
            )
            continue

        results[i] = VdbxBarResultV1(
            event=VdbxEventV1.NONE,
            entry_side=StrategyEntrySideCarrierV1.NONE,
            event_kind=StrategyAgreementEventKindV1.NONE,
            reason=VdbxReasonV1.NO_EVENT,
        )

    if position is not None:
        raise ValueError("UNPAIRABLE_ENTRY_NO_EXIT_STRATEGY_EMITTED")

    return results, roundtrips


def generate_vdbx_event_series_v1(data: pd.DataFrame, **kwargs: object) -> pd.DataFrame:
    rows, _ = generate_vdbx_events_and_roundtrips_v1(data, **kwargs)  # type: ignore[arg-type]
    return pd.DataFrame(
        {
            "event": [r.event.value for r in rows],
            "entry_side": [r.entry_side.value for r in rows],
            "event_kind": [r.event_kind.value for r in rows],
            "reason": [r.reason.value for r in rows],
            "exit_reason": [r.exit_reason.value if r.exit_reason else None for r in rows],
            "exit_price": [r.exit_price for r in rows],
            "fill_index": [r.fill_index for r in rows],
            "signal_index": [r.signal_index for r in rows],
        },
        index=data.index,
    )


__all__ = [
    "BASELINE_ID_V1",
    "EXIT_PARAMS_V1",
    "EXIT_STATE_MACHINE_IMPLEMENTED_V1",
    "PREDECESSOR_STRATEGY_ID_V1",
    "PRODUCTIVE_EXIT_PNL_EVALUATOR_REF_V1",
    "PROGRAM_ID_V1",
    "SIGNAL_FAMILY_V1",
    "STRATEGY_ID_V1",
    "STRATEGY_IDENTITY_V1",
    "STRATEGY_VERSION_V1",
    "VdbxBarResultV1",
    "VdbxEventV1",
    "VdbxReasonV1",
    "VdbxRoundtripV1",
    "generate_vdbx_event_series_v1",
    "generate_vdbx_events_and_roundtrips_v1",
]
