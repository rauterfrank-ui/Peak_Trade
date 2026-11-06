"""VOLATILITY_EXPANSION_PULLBACK_CONTINUATION_V1 strategy producer.

Implements confirmed RV(24) expansion → directional impulse → bounded pullback
(15–50% within ≤8 bars) → continuation resume admission, ex-ante exit reachability,
and a deterministic exit state machine with pullback-structure invalidation
(no trailing). No PnL/equity/stats truth. No evaluation.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional

import numpy as np
import pandas as pd

from src.research.price_channel_breakout_core_v1 import (
    CHANNEL_LOOKBACK_COMPLETED_BARS_V1,
    PriceChannelBreakSideV1,
    classify_price_channel_break_v1,
    compute_prior_high_low_channel_bounds_v1,
)
from src.research.volatility_expansion_pullback_continuation_v1_exit_state_machine_v1 import (
    COOLDOWN_BARS_AFTER_EXIT_V1,
    EXIT_PRECEDENCE_ASCENDING_WINS_FIRST_V1,
    MIN_POST_FILL_BARS_REQUIRED_INCLUSIVE_V1,
    SIGNAL_LAG_BARS_V1,
    TIME_EXIT_MAX_BARS_V1,
    TRAILING_STOP_FORBIDDEN_V1,
    VepcExitReasonV1,
    entry_exit_reachable_ex_ante_v1,
    evaluate_exit_on_bar_v1,
    open_position_from_fill_v1,
)
from src.research.volatility_expansion_pullback_continuation_v1_vol_state_v1 import (
    compute_atr14_v1,
    compute_percentile_rank_120_realized_vol_v1,
    compute_realized_volatility_24_v1,
)
from src.trading.master_v2.strategy_suitability_agreement_material_v1 import (
    StrategyAgreementEventKindV1,
    StrategyEntrySideCarrierV1,
)

STRATEGY_IDENTITY_V1 = "VOLATILITY_EXPANSION_PULLBACK_CONTINUATION_V1"
STRATEGY_ID_V1 = "volatility_expansion_pullback_continuation"
STRATEGY_VERSION_V1 = "v1"
SIGNAL_FAMILY_V1 = "VOLATILITY_REGIME"
PROGRAM_ID_V1 = "VOLATILITY_REGIME_RESEARCH_PROGRAM_V1"
BASELINE_ID_V1 = "UNCONDITIONAL_20_BAR_PRICE_CHANNEL_BREAKOUT_V1"
PREDECESSOR_STRATEGY_ID_V1 = "VOLATILITY_CONTRACTION_EXPANSION_BREAKOUT_V1"

EXPANSION_PERCENTILE_INCLUSIVE_MIN_V1 = 0.65
EXPANSION_MIN_CONSECUTIVE_BARS_V1 = 4
MAX_PULLBACK_BARS_INCLUSIVE_V1 = 8
MIN_PULLBACK_FRACTION_V1 = 0.15
MAX_PULLBACK_FRACTION_V1 = 0.50
MAX_ENTRIES_PER_EXPANSION_PULLBACK_SEQUENCE_V1 = 1
EVENT_CONSUMPTION_V1 = "SINGLE_USE"
CHANNEL_LOOKBACK_BARS_V1 = CHANNEL_LOOKBACK_COMPLETED_BARS_V1
ENTRY_ON_EXPANSION_CONFIRMATION_BAR_FORBIDDEN_V1 = True
IMMEDIATE_BREAKOUT_WITHOUT_PULLBACK_FORBIDDEN_V1 = True
CONTRACTION_ADMISSION_NOT_REQUIRED_V1 = True

EXIT_STATE_MACHINE_IMPLEMENTED_V1 = True
PRODUCTIVE_EXIT_PNL_EVALUATOR_REF_V1 = (
    "src/research/volatility_compression_breakout_v1_development_evaluation_v1/"
    "productive_exit_pnl_evaluator_v1.py"
)

EXIT_PARAMS_V1 = {
    "initial_stop_atr_multiple": 1.5,
    "trailing_stop_forbidden": TRAILING_STOP_FORBIDDEN_V1,
    "trailing_stop_not_used": True,
    "pullback_structure_invalidation_authorized": True,
    "regime_invalidation_percentile_rank_lt": 0.40,
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


class VepcEventV1(str, Enum):
    ENTRY_EVENT = "ENTRY_EVENT"
    EXIT_EVENT = "EXIT_EVENT"
    NONE = "NONE"


class VepcReasonV1(str, Enum):
    SUCCESSFUL_ENTRY = "SUCCESSFUL_ENTRY"
    EXIT_EMITTED = "EXIT_EMITTED"
    ENTRY_SUPPRESSED_EXIT_UNREACHABLE = "ENTRY_SUPPRESSED_EXIT_UNREACHABLE"
    NO_EVENT = "NO_EVENT"
    WARMUP = "WARMUP"
    POSITION_OPEN = "POSITION_OPEN"
    AWAITING_FILL = "AWAITING_FILL"
    AWAITING_REARM = "AWAITING_REARM"
    AWAITING_IMPULSE = "AWAITING_IMPULSE"
    AWAITING_PULLBACK = "AWAITING_PULLBACK"
    AWAITING_CONTINUATION = "AWAITING_CONTINUATION"
    PULLBACK_INVALIDATED = "PULLBACK_INVALIDATED"
    COOLDOWN = "COOLDOWN"


@dataclass(frozen=True)
class VepcBarResultV1:
    event: VepcEventV1
    entry_side: StrategyEntrySideCarrierV1
    event_kind: StrategyAgreementEventKindV1
    reason: VepcReasonV1
    exit_reason: Optional[VepcExitReasonV1] = None
    exit_price: Optional[float] = None
    fill_index: Optional[int] = None
    signal_index: Optional[int] = None
    expansion_confirmation_index: Optional[int] = None
    impulse_index: Optional[int] = None
    percentile_rank_120: Optional[float] = None
    realized_volatility_24: Optional[float] = None
    upper_channel: Optional[float] = None
    lower_channel: Optional[float] = None
    pullback_swing_high: Optional[float] = None
    pullback_swing_low: Optional[float] = None


@dataclass(frozen=True)
class VepcRoundtripV1:
    side: str
    signal_index: int
    fill_index: int
    exit_index: int
    entry_price: float
    exit_price: float
    exit_reason: VepcExitReasonV1
    pullback_swing_high: float
    pullback_swing_low: float


@dataclass
class _SequenceState:
    expansion_confirmation_index: int
    impulse_index: Optional[int] = None
    impulse_side: Optional[StrategyEntrySideCarrierV1] = None
    impulse_high: Optional[float] = None
    impulse_low: Optional[float] = None
    impulse_range: Optional[float] = None
    pullback_valid: bool = False
    # Running extremes after impulse (pre-freeze).
    running_high: Optional[float] = None
    running_low: Optional[float] = None
    # Frozen at first valid pullback bar; used for continuation + exits.
    pullback_swing_high: Optional[float] = None
    pullback_swing_low: Optional[float] = None
    entry_consumed: bool = False


def _expansion_through(
    ranks: np.ndarray,
    *,
    end_inclusive: int,
    bars: int = EXPANSION_MIN_CONSECUTIVE_BARS_V1,
    thr: float = EXPANSION_PERCENTILE_INCLUSIVE_MIN_V1,
) -> bool:
    if end_inclusive < bars - 1:
        return False
    start = end_inclusive - bars + 1
    window = ranks[start : end_inclusive + 1]
    if window.shape[0] != bars:
        return False
    if not np.isfinite(window).all():
        return False
    return bool(np.all(window >= thr))


def _none_result(
    reason: VepcReasonV1,
    *,
    percentile_rank_120: Optional[float] = None,
    realized_volatility_24: Optional[float] = None,
    upper_channel: Optional[float] = None,
    lower_channel: Optional[float] = None,
    expansion_confirmation_index: Optional[int] = None,
    impulse_index: Optional[int] = None,
    pullback_swing_high: Optional[float] = None,
    pullback_swing_low: Optional[float] = None,
) -> VepcBarResultV1:
    return VepcBarResultV1(
        event=VepcEventV1.NONE,
        entry_side=StrategyEntrySideCarrierV1.NONE,
        event_kind=StrategyAgreementEventKindV1.NONE,
        reason=reason,
        percentile_rank_120=percentile_rank_120,
        realized_volatility_24=realized_volatility_24,
        upper_channel=upper_channel,
        lower_channel=lower_channel,
        expansion_confirmation_index=expansion_confirmation_index,
        impulse_index=impulse_index,
        pullback_swing_high=pullback_swing_high,
        pullback_swing_low=pullback_swing_low,
    )


def generate_vepc_events_and_roundtrips_v1(
    data: pd.DataFrame,
    *,
    high_col: str = "high",
    low_col: str = "low",
    close_col: str = "close",
    open_col: str = "open",
    is_panel_last_bar_mask: Optional[np.ndarray] = None,
) -> tuple[list[VepcBarResultV1], list[VepcRoundtripV1]]:
    """Generate entry/exit events with guaranteed exit reachability for admitted entries.

    Expansion confirmation on completed bar t_exp (4 bars RV percentile >= 0.65).
    No entry on expansion confirmation bar. Impulse via 20-bar channel break while
    expansion remains active. Entry only after bounded pullback then continuation.
    Fill conceptually at open of signal+1. No trailing exits.
    """
    for col in (high_col, low_col, close_col, open_col):
        if col not in data.columns:
            raise ValueError(f"missing_column:{col}")

    n = len(data)
    if n == 0:
        return [], []

    high = data[high_col].astype(float)
    low = data[low_col].astype(float)
    close = data[close_col].astype(float)
    open_ = data[open_col].astype(float)
    rv = compute_realized_volatility_24_v1(close)
    rank = compute_percentile_rank_120_realized_vol_v1(rv)
    atr = compute_atr14_v1(high, low, close)
    upper, lower = compute_prior_high_low_channel_bounds_v1(
        high, low, lookback=CHANNEL_LOOKBACK_BARS_V1
    )

    ranks_np = rank.to_numpy(dtype=np.float64, copy=False)
    rv_np = rv.to_numpy(dtype=np.float64, copy=False)

    if is_panel_last_bar_mask is None:
        panel_last = np.zeros(n, dtype=bool)
        panel_last[-1] = True
    else:
        panel_last = np.asarray(is_panel_last_bar_mask, dtype=bool)
        if len(panel_last) != n:
            raise ValueError("PANEL_LAST_MASK_LENGTH_MISMATCH")

    results: list[VepcBarResultV1] = [_none_result(VepcReasonV1.NO_EVENT) for _ in range(n)]
    roundtrips: list[VepcRoundtripV1] = []

    pending_signal: Optional[tuple[int, StrategyEntrySideCarrierV1, float, float]] = (
        None  # signal_i, side, swing_high, swing_low
    )
    position = None
    pending_roundtrip_meta: Optional[tuple[int, int, float, float, float]] = None
    cooldown_until = -1
    awaiting_rearm = False
    seq: Optional[_SequenceState] = None

    for i in range(n):
        rank_i = float(ranks_np[i]) if np.isfinite(ranks_np[i]) else None
        rv_i = float(rv_np[i]) if np.isfinite(rv_np[i]) else None
        u_i = float(upper.iloc[i]) if np.isfinite(upper.iloc[i]) else None
        lo_i = float(lower.iloc[i]) if np.isfinite(lower.iloc[i]) else None
        h_i = float(high.iloc[i]) if np.isfinite(high.iloc[i]) else float("nan")
        l_i = float(low.iloc[i]) if np.isfinite(low.iloc[i]) else float("nan")
        c_i = float(close.iloc[i]) if np.isfinite(close.iloc[i]) else float("nan")

        if i < cooldown_until:
            results[i] = _none_result(
                VepcReasonV1.COOLDOWN,
                percentile_rank_120=rank_i,
                realized_volatility_24=rv_i,
                upper_channel=u_i,
                lower_channel=lo_i,
            )
            continue

        if pending_signal is not None:
            sig_i, side, swing_h, swing_l = pending_signal
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
                    pullback_swing_high=swing_h,
                    pullback_swing_low=swing_l,
                )
                pending_roundtrip_meta = (sig_i, fill_i, entry_px, swing_h, swing_l)
                pending_signal = None
                results[i] = VepcBarResultV1(
                    event=VepcEventV1.NONE,
                    entry_side=StrategyEntrySideCarrierV1.NONE,
                    event_kind=StrategyAgreementEventKindV1.NONE,
                    reason=VepcReasonV1.POSITION_OPEN,
                    fill_index=fill_i,
                    signal_index=sig_i,
                    percentile_rank_120=rank_i,
                    realized_volatility_24=rv_i,
                    upper_channel=u_i,
                    lower_channel=lo_i,
                    pullback_swing_high=swing_h,
                    pullback_swing_low=swing_l,
                )
                continue
            if i < fill_i:
                results[i] = _none_result(
                    VepcReasonV1.AWAITING_FILL,
                    percentile_rank_120=rank_i,
                    realized_volatility_24=rv_i,
                    upper_channel=u_i,
                    lower_channel=lo_i,
                    pullback_swing_high=swing_h,
                    pullback_swing_low=swing_l,
                )
                results[i] = VepcBarResultV1(
                    event=VepcEventV1.NONE,
                    entry_side=StrategyEntrySideCarrierV1.NONE,
                    event_kind=StrategyAgreementEventKindV1.NONE,
                    reason=VepcReasonV1.AWAITING_FILL,
                    signal_index=sig_i,
                    percentile_rank_120=rank_i,
                    realized_volatility_24=rv_i,
                    upper_channel=u_i,
                    lower_channel=lo_i,
                    pullback_swing_high=swing_h,
                    pullback_swing_low=swing_l,
                )
                continue

        if position is not None and pending_roundtrip_meta is not None:
            if i <= position.fill_index:
                results[i] = VepcBarResultV1(
                    event=VepcEventV1.NONE,
                    entry_side=StrategyEntrySideCarrierV1.NONE,
                    event_kind=StrategyAgreementEventKindV1.NONE,
                    reason=VepcReasonV1.POSITION_OPEN,
                    fill_index=position.fill_index,
                    signal_index=pending_roundtrip_meta[0],
                    percentile_rank_120=rank_i,
                    realized_volatility_24=rv_i,
                    upper_channel=u_i,
                    lower_channel=lo_i,
                    pullback_swing_high=pending_roundtrip_meta[3],
                    pullback_swing_low=pending_roundtrip_meta[4],
                )
                continue
            decision, position = evaluate_exit_on_bar_v1(
                position,
                bar_index=i,
                high=h_i,
                low=l_i,
                close=c_i,
                percentile_rank=rank_i,
                is_last_instrument_bar=(i == n - 1),
                is_last_panel_bar=bool(panel_last[i]),
            )
            if decision is not None:
                sig_i, fill_i, entry_px, swing_h, swing_l = pending_roundtrip_meta
                roundtrips.append(
                    VepcRoundtripV1(
                        side=decision.side,
                        signal_index=sig_i,
                        fill_index=fill_i,
                        exit_index=decision.exit_index,
                        entry_price=entry_px,
                        exit_price=decision.exit_price,
                        exit_reason=decision.reason,
                        pullback_swing_high=swing_h,
                        pullback_swing_low=swing_l,
                    )
                )
                results[i] = VepcBarResultV1(
                    event=VepcEventV1.EXIT_EVENT,
                    entry_side=StrategyEntrySideCarrierV1.NONE,
                    event_kind=StrategyAgreementEventKindV1.NONE,
                    reason=VepcReasonV1.EXIT_EMITTED,
                    exit_reason=decision.reason,
                    exit_price=decision.exit_price,
                    fill_index=fill_i,
                    signal_index=sig_i,
                    percentile_rank_120=rank_i,
                    realized_volatility_24=rv_i,
                    upper_channel=u_i,
                    lower_channel=lo_i,
                    pullback_swing_high=swing_h,
                    pullback_swing_low=swing_l,
                )
                position = None
                pending_roundtrip_meta = None
                seq = None
                awaiting_rearm = True
                cooldown_until = i + 1 + COOLDOWN_BARS_AFTER_EXIT_V1
                continue
            results[i] = VepcBarResultV1(
                event=VepcEventV1.NONE,
                entry_side=StrategyEntrySideCarrierV1.NONE,
                event_kind=StrategyAgreementEventKindV1.NONE,
                reason=VepcReasonV1.POSITION_OPEN,
                fill_index=position.fill_index,
                signal_index=pending_roundtrip_meta[0],
                percentile_rank_120=rank_i,
                realized_volatility_24=rv_i,
                upper_channel=u_i,
                lower_channel=lo_i,
                pullback_swing_high=pending_roundtrip_meta[3],
                pullback_swing_low=pending_roundtrip_meta[4],
            )
            continue

        # Flat admission path.
        if rank_i is None or rv_i is None or not np.isfinite(c_i):
            results[i] = _none_result(
                VepcReasonV1.WARMUP,
                percentile_rank_120=rank_i,
                realized_volatility_24=rv_i,
                upper_channel=u_i,
                lower_channel=lo_i,
            )
            continue

        if awaiting_rearm and seq is None:
            if _expansion_through(ranks_np, end_inclusive=i):
                awaiting_rearm = False
                seq = _SequenceState(expansion_confirmation_index=i)
                results[i] = _none_result(
                    VepcReasonV1.AWAITING_IMPULSE,
                    percentile_rank_120=rank_i,
                    realized_volatility_24=rv_i,
                    upper_channel=u_i,
                    lower_channel=lo_i,
                    expansion_confirmation_index=i,
                )
                continue
            results[i] = _none_result(
                VepcReasonV1.AWAITING_REARM,
                percentile_rank_120=rank_i,
                realized_volatility_24=rv_i,
                upper_channel=u_i,
                lower_channel=lo_i,
            )
            continue

        if seq is None:
            if _expansion_through(ranks_np, end_inclusive=i):
                seq = _SequenceState(expansion_confirmation_index=i)
                results[i] = _none_result(
                    VepcReasonV1.AWAITING_IMPULSE,
                    percentile_rank_120=rank_i,
                    realized_volatility_24=rv_i,
                    upper_channel=u_i,
                    lower_channel=lo_i,
                    expansion_confirmation_index=i,
                )
            else:
                results[i] = _none_result(
                    VepcReasonV1.NO_EVENT,
                    percentile_rank_120=rank_i,
                    realized_volatility_24=rv_i,
                    upper_channel=u_i,
                    lower_channel=lo_i,
                )
            continue

        # Active sequence — never enter on expansion confirmation bar.
        if i == seq.expansion_confirmation_index:
            results[i] = _none_result(
                VepcReasonV1.AWAITING_IMPULSE,
                percentile_rank_120=rank_i,
                realized_volatility_24=rv_i,
                upper_channel=u_i,
                lower_channel=lo_i,
                expansion_confirmation_index=seq.expansion_confirmation_index,
            )
            continue

        expansion_active = _expansion_through(ranks_np, end_inclusive=i)

        # Impulse discovery (only before impulse locked).
        if seq.impulse_index is None:
            if not expansion_active:
                # Expansion lost before impulse → reset and require rearm.
                seq = None
                awaiting_rearm = True
                results[i] = _none_result(
                    VepcReasonV1.AWAITING_REARM,
                    percentile_rank_120=rank_i,
                    realized_volatility_24=rv_i,
                    upper_channel=u_i,
                    lower_channel=lo_i,
                )
                continue
            break_side = classify_price_channel_break_v1(
                close=c_i, upper_channel=u_i, lower_channel=lo_i
            )
            if break_side is PriceChannelBreakSideV1.LONG:
                impulse_side = StrategyEntrySideCarrierV1.LONG
            elif break_side is PriceChannelBreakSideV1.SHORT:
                impulse_side = StrategyEntrySideCarrierV1.SHORT
            else:
                results[i] = _none_result(
                    VepcReasonV1.AWAITING_IMPULSE,
                    percentile_rank_120=rank_i,
                    realized_volatility_24=rv_i,
                    upper_channel=u_i,
                    lower_channel=lo_i,
                    expansion_confirmation_index=seq.expansion_confirmation_index,
                )
                continue
            if not (np.isfinite(h_i) and np.isfinite(l_i)) or h_i <= l_i:
                seq = None
                awaiting_rearm = True
                results[i] = _none_result(
                    VepcReasonV1.AWAITING_REARM,
                    percentile_rank_120=rank_i,
                    realized_volatility_24=rv_i,
                    upper_channel=u_i,
                    lower_channel=lo_i,
                )
                continue
            impulse_range = h_i - l_i
            if impulse_range <= 0:
                seq = None
                awaiting_rearm = True
                results[i] = _none_result(
                    VepcReasonV1.AWAITING_REARM,
                    percentile_rank_120=rank_i,
                    realized_volatility_24=rv_i,
                    upper_channel=u_i,
                    lower_channel=lo_i,
                )
                continue
            seq.impulse_index = i
            seq.impulse_side = impulse_side
            seq.impulse_high = h_i
            seq.impulse_low = l_i
            seq.impulse_range = impulse_range
            # Pullback extremes are measured only on bars after the impulse bar.
            seq.running_high = None
            seq.running_low = None
            # Immediate breakout entry without pullback is forbidden.
            results[i] = _none_result(
                VepcReasonV1.AWAITING_PULLBACK,
                percentile_rank_120=rank_i,
                realized_volatility_24=rv_i,
                upper_channel=u_i,
                lower_channel=lo_i,
                expansion_confirmation_index=seq.expansion_confirmation_index,
                impulse_index=i,
            )
            continue

        assert seq.impulse_index is not None
        assert seq.impulse_side is not None
        assert seq.impulse_high is not None
        assert seq.impulse_low is not None
        assert seq.impulse_range is not None

        bars_since_impulse = i - seq.impulse_index
        if bars_since_impulse < 1:
            results[i] = _none_result(
                VepcReasonV1.AWAITING_PULLBACK,
                percentile_rank_120=rank_i,
                realized_volatility_24=rv_i,
                upper_channel=u_i,
                lower_channel=lo_i,
                expansion_confirmation_index=seq.expansion_confirmation_index,
                impulse_index=seq.impulse_index,
            )
            continue

        if not np.isfinite(h_i) or not np.isfinite(l_i):
            seq = None
            awaiting_rearm = True
            results[i] = _none_result(
                VepcReasonV1.PULLBACK_INVALIDATED,
                percentile_rank_120=rank_i,
                realized_volatility_24=rv_i,
                upper_channel=u_i,
                lower_channel=lo_i,
            )
            continue

        # Pullback must not break impulse extreme (LONG: not below impulse_low;
        # SHORT: not above impulse_high).
        if seq.impulse_side is StrategyEntrySideCarrierV1.LONG:
            if l_i < seq.impulse_low:
                seq = None
                awaiting_rearm = True
                results[i] = _none_result(
                    VepcReasonV1.PULLBACK_INVALIDATED,
                    percentile_rank_120=rank_i,
                    realized_volatility_24=rv_i,
                    upper_channel=u_i,
                    lower_channel=lo_i,
                )
                continue
        else:
            if h_i > seq.impulse_high:
                seq = None
                awaiting_rearm = True
                results[i] = _none_result(
                    VepcReasonV1.PULLBACK_INVALIDATED,
                    percentile_rank_120=rank_i,
                    realized_volatility_24=rv_i,
                    upper_channel=u_i,
                    lower_channel=lo_i,
                )
                continue

        if not seq.pullback_valid:
            if bars_since_impulse > MAX_PULLBACK_BARS_INCLUSIVE_V1:
                seq = None
                awaiting_rearm = True
                results[i] = _none_result(
                    VepcReasonV1.PULLBACK_INVALIDATED,
                    percentile_rank_120=rank_i,
                    realized_volatility_24=rv_i,
                    upper_channel=u_i,
                    lower_channel=lo_i,
                )
                continue
            # Update running extremes only while seeking a valid pullback.
            seq.running_high = h_i if seq.running_high is None else max(seq.running_high, h_i)
            seq.running_low = l_i if seq.running_low is None else min(seq.running_low, l_i)
            if seq.impulse_side is StrategyEntrySideCarrierV1.LONG:
                pullback_depth = (seq.impulse_high - seq.running_low) / seq.impulse_range
            else:
                pullback_depth = (seq.running_high - seq.impulse_low) / seq.impulse_range
            if MIN_PULLBACK_FRACTION_V1 <= pullback_depth <= MAX_PULLBACK_FRACTION_V1:
                seq.pullback_valid = True
                seq.pullback_swing_high = float(seq.running_high)
                seq.pullback_swing_low = float(seq.running_low)
                results[i] = _none_result(
                    VepcReasonV1.AWAITING_CONTINUATION,
                    percentile_rank_120=rank_i,
                    realized_volatility_24=rv_i,
                    upper_channel=u_i,
                    lower_channel=lo_i,
                    expansion_confirmation_index=seq.expansion_confirmation_index,
                    impulse_index=seq.impulse_index,
                    pullback_swing_high=seq.pullback_swing_high,
                    pullback_swing_low=seq.pullback_swing_low,
                )
                continue
            if pullback_depth > MAX_PULLBACK_FRACTION_V1:
                seq = None
                awaiting_rearm = True
                results[i] = _none_result(
                    VepcReasonV1.PULLBACK_INVALIDATED,
                    percentile_rank_120=rank_i,
                    realized_volatility_24=rv_i,
                    upper_channel=u_i,
                    lower_channel=lo_i,
                )
                continue
            results[i] = _none_result(
                VepcReasonV1.AWAITING_PULLBACK,
                percentile_rank_120=rank_i,
                realized_volatility_24=rv_i,
                upper_channel=u_i,
                lower_channel=lo_i,
                expansion_confirmation_index=seq.expansion_confirmation_index,
                impulse_index=seq.impulse_index,
            )
            continue

        # Pullback valid — frozen swings; wait for continuation resume.
        assert seq.pullback_swing_high is not None and seq.pullback_swing_low is not None
        if seq.impulse_side is StrategyEntrySideCarrierV1.LONG:
            depth_now = (seq.impulse_high - min(seq.pullback_swing_low, l_i)) / seq.impulse_range
        else:
            depth_now = (max(seq.pullback_swing_high, h_i) - seq.impulse_low) / seq.impulse_range
        if depth_now > MAX_PULLBACK_FRACTION_V1:
            seq = None
            awaiting_rearm = True
            results[i] = _none_result(
                VepcReasonV1.PULLBACK_INVALIDATED,
                percentile_rank_120=rank_i,
                realized_volatility_24=rv_i,
                upper_channel=u_i,
                lower_channel=lo_i,
            )
            continue

        continued = False
        if seq.impulse_side is StrategyEntrySideCarrierV1.LONG:
            continued = c_i > seq.pullback_swing_high
        else:
            continued = c_i < seq.pullback_swing_low

        if not continued:
            results[i] = _none_result(
                VepcReasonV1.AWAITING_CONTINUATION,
                percentile_rank_120=rank_i,
                realized_volatility_24=rv_i,
                upper_channel=u_i,
                lower_channel=lo_i,
                expansion_confirmation_index=seq.expansion_confirmation_index,
                impulse_index=seq.impulse_index,
                pullback_swing_high=seq.pullback_swing_high,
                pullback_swing_low=seq.pullback_swing_low,
            )
            continue

        # Continuation confirmation on bar i; entry signal now; fill at i+1.
        if i == seq.expansion_confirmation_index:
            results[i] = _none_result(
                VepcReasonV1.NO_EVENT,
                percentile_rank_120=rank_i,
                realized_volatility_24=rv_i,
                upper_channel=u_i,
                lower_channel=lo_i,
            )
            continue

        if not entry_exit_reachable_ex_ante_v1(signal_index=i, series_length=n):
            results[i] = _none_result(
                VepcReasonV1.ENTRY_SUPPRESSED_EXIT_UNREACHABLE,
                percentile_rank_120=rank_i,
                realized_volatility_24=rv_i,
                upper_channel=u_i,
                lower_channel=lo_i,
                expansion_confirmation_index=seq.expansion_confirmation_index,
                impulse_index=seq.impulse_index,
                pullback_swing_high=seq.pullback_swing_high,
                pullback_swing_low=seq.pullback_swing_low,
            )
            seq = None
            awaiting_rearm = True
            continue

        swing_h = float(seq.pullback_swing_high)
        swing_l = float(seq.pullback_swing_low)
        side = seq.impulse_side
        seq.entry_consumed = True
        pending_signal = (i, side, swing_h, swing_l)
        results[i] = VepcBarResultV1(
            event=VepcEventV1.ENTRY_EVENT,
            entry_side=side,
            event_kind=StrategyAgreementEventKindV1.ENTRY,
            reason=VepcReasonV1.SUCCESSFUL_ENTRY,
            signal_index=i,
            expansion_confirmation_index=seq.expansion_confirmation_index,
            impulse_index=seq.impulse_index,
            percentile_rank_120=rank_i,
            realized_volatility_24=rv_i,
            upper_channel=u_i,
            lower_channel=lo_i,
            pullback_swing_high=swing_h,
            pullback_swing_low=swing_l,
        )
        # After successful entry signal, sequence is consumed; rearm after exit.
        seq = None
        awaiting_rearm = True

    return results, roundtrips


# Re-export shared channel core bindings for identity assertions.
__all__ = [
    "BASELINE_ID_V1",
    "CHANNEL_LOOKBACK_BARS_V1",
    "CONTRACTION_ADMISSION_NOT_REQUIRED_V1",
    "ENTRY_ON_EXPANSION_CONFIRMATION_BAR_FORBIDDEN_V1",
    "EVENT_CONSUMPTION_V1",
    "EXIT_PARAMS_V1",
    "EXIT_STATE_MACHINE_IMPLEMENTED_V1",
    "EXPANSION_MIN_CONSECUTIVE_BARS_V1",
    "EXPANSION_PERCENTILE_INCLUSIVE_MIN_V1",
    "IMMEDIATE_BREAKOUT_WITHOUT_PULLBACK_FORBIDDEN_V1",
    "MAX_ENTRIES_PER_EXPANSION_PULLBACK_SEQUENCE_V1",
    "MAX_PULLBACK_BARS_INCLUSIVE_V1",
    "MAX_PULLBACK_FRACTION_V1",
    "MIN_PULLBACK_FRACTION_V1",
    "PREDECESSOR_STRATEGY_ID_V1",
    "PRODUCTIVE_EXIT_PNL_EVALUATOR_REF_V1",
    "PROGRAM_ID_V1",
    "SIGNAL_FAMILY_V1",
    "STRATEGY_ID_V1",
    "STRATEGY_IDENTITY_V1",
    "STRATEGY_VERSION_V1",
    "VepcBarResultV1",
    "VepcEventV1",
    "VepcReasonV1",
    "VepcRoundtripV1",
    "classify_price_channel_break_v1",
    "compute_prior_high_low_channel_bounds_v1",
    "entry_exit_reachable_ex_ante_v1",
    "evaluate_exit_on_bar_v1",
    "generate_vepc_events_and_roundtrips_v1",
    "open_position_from_fill_v1",
]
