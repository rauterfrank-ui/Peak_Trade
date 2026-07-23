"""VOLATILITY_EXPANSION_FAILED_CONTINUATION_FADE_V1 strategy producer.

Implements confirmed RV(24) expansion → directional impulse → failed-continuation
fade triggers (extreme break / deep pullback / window exhaustion), opposite-side
admission, ex-ante exit reachability, and a deterministic exit state machine with
impulse-reclaim invalidation (no trailing). Successful VEPC-style continuation
cancels fade for the sequence. No PnL/equity/stats truth. No evaluation.
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
from src.research.volatility_expansion_failed_continuation_fade_v1_exit_state_machine_v1 import (
    COOLDOWN_BARS_AFTER_EXIT_V1,
    EXIT_PRECEDENCE_ASCENDING_WINS_FIRST_V1,
    MIN_POST_FILL_BARS_REQUIRED_INCLUSIVE_V1,
    SIGNAL_LAG_BARS_V1,
    TIME_EXIT_MAX_BARS_V1,
    TRAILING_STOP_FORBIDDEN_V1,
    VefcfExitReasonV1,
    entry_exit_reachable_ex_ante_v1,
    evaluate_exit_on_bar_v1,
    open_position_from_fill_v1,
)
from src.research.volatility_expansion_failed_continuation_fade_v1_vol_state_v1 import (
    compute_atr14_v1,
    compute_percentile_rank_120_realized_vol_v1,
    compute_realized_volatility_24_v1,
)
from src.trading.master_v2.strategy_suitability_agreement_material_v1 import (
    StrategyAgreementEventKindV1,
    StrategyEntrySideCarrierV1,
)

STRATEGY_IDENTITY_V1 = "VOLATILITY_EXPANSION_FAILED_CONTINUATION_FADE_V1"
STRATEGY_ID_V1 = "volatility_expansion_failed_continuation_fade"
STRATEGY_VERSION_V1 = "v1"
SIGNAL_FAMILY_V1 = "VOLATILITY_REGIME"
PROGRAM_ID_V1 = "VOLATILITY_REGIME_RESEARCH_PROGRAM_V1"
BASELINE_ID_V1 = "UNCONDITIONAL_20_BAR_PRICE_CHANNEL_BREAKOUT_V1"
PREDECESSOR_STRATEGY_ID_V1 = "VOLATILITY_EXPANSION_PULLBACK_CONTINUATION_V1"

EXPANSION_PERCENTILE_INCLUSIVE_MIN_V1 = 0.65
EXPANSION_MIN_CONSECUTIVE_BARS_V1 = 4
MAX_MONITORING_BARS_INCLUSIVE_V1 = 8
MIN_PULLBACK_FRACTION_QUALIFYING_V1 = 0.15
DEEP_PULLBACK_FRACTION_V1 = 0.50
MAX_ENTRIES_PER_EXPANSION_IMPULSE_SEQUENCE_V1 = 1
EVENT_CONSUMPTION_V1 = "SINGLE_USE"
CHANNEL_LOOKBACK_BARS_V1 = CHANNEL_LOOKBACK_COMPLETED_BARS_V1
ENTRY_ON_EXPANSION_CONFIRMATION_BAR_FORBIDDEN_V1 = True
IMMEDIATE_BREAKOUT_WITHOUT_FAILURE_FORBIDDEN_V1 = True
VEPC_CONTINUATION_ENTRY_FORBIDDEN_V1 = True
CONTRACTION_ADMISSION_NOT_REQUIRED_V1 = True
SUCCESSFUL_CONTINUATION_CANCELS_FADE_V1 = True

FADE_TRIGGERS_FIRST_WINS_V1 = (
    "IMPULSE_EXTREME_BREAK_AGAINST_IMPULSE",
    "DEEP_PULLBACK_WITHOUT_CONTINUATION",
    "QUALIFYING_PULLBACK_WINDOW_EXHAUSTION_WITHOUT_CONTINUATION",
)

EXIT_STATE_MACHINE_IMPLEMENTED_V1 = True
PRODUCTIVE_EXIT_PNL_EVALUATOR_REF_V1 = (
    "src/research/volatility_compression_breakout_v1_development_evaluation_v1/"
    "productive_exit_pnl_evaluator_v1.py"
)

EXIT_PARAMS_V1 = {
    "initial_stop_atr_multiple": 1.5,
    "trailing_stop_forbidden": TRAILING_STOP_FORBIDDEN_V1,
    "trailing_stop_not_used": True,
    "impulse_reclaim_invalidation_authorized": True,
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


class VefcfEventV1(str, Enum):
    ENTRY_EVENT = "ENTRY_EVENT"
    EXIT_EVENT = "EXIT_EVENT"
    NONE = "NONE"


class VefcfFadeTriggerV1(str, Enum):
    IMPULSE_EXTREME_BREAK_AGAINST_IMPULSE = "IMPULSE_EXTREME_BREAK_AGAINST_IMPULSE"
    DEEP_PULLBACK_WITHOUT_CONTINUATION = "DEEP_PULLBACK_WITHOUT_CONTINUATION"
    QUALIFYING_PULLBACK_WINDOW_EXHAUSTION_WITHOUT_CONTINUATION = (
        "QUALIFYING_PULLBACK_WINDOW_EXHAUSTION_WITHOUT_CONTINUATION"
    )


class VefcfReasonV1(str, Enum):
    SUCCESSFUL_ENTRY = "SUCCESSFUL_ENTRY"
    EXIT_EMITTED = "EXIT_EMITTED"
    ENTRY_SUPPRESSED_EXIT_UNREACHABLE = "ENTRY_SUPPRESSED_EXIT_UNREACHABLE"
    NO_EVENT = "NO_EVENT"
    WARMUP = "WARMUP"
    POSITION_OPEN = "POSITION_OPEN"
    AWAITING_FILL = "AWAITING_FILL"
    AWAITING_REARM = "AWAITING_REARM"
    AWAITING_IMPULSE = "AWAITING_IMPULSE"
    MONITORING_FAILED_CONTINUATION = "MONITORING_FAILED_CONTINUATION"
    CONTINUATION_CANCELLED_FADE = "CONTINUATION_CANCELLED_FADE"
    AMBIGUOUS_TRIGGER_FAIL_CLOSED = "AMBIGUOUS_TRIGGER_FAIL_CLOSED"
    COOLDOWN = "COOLDOWN"


@dataclass(frozen=True)
class VefcfBarResultV1:
    event: VefcfEventV1
    entry_side: StrategyEntrySideCarrierV1
    event_kind: StrategyAgreementEventKindV1
    reason: VefcfReasonV1
    exit_reason: Optional[VefcfExitReasonV1] = None
    exit_price: Optional[float] = None
    fill_index: Optional[int] = None
    signal_index: Optional[int] = None
    expansion_confirmation_index: Optional[int] = None
    impulse_index: Optional[int] = None
    fade_trigger: Optional[VefcfFadeTriggerV1] = None
    percentile_rank_120: Optional[float] = None
    realized_volatility_24: Optional[float] = None
    upper_channel: Optional[float] = None
    lower_channel: Optional[float] = None
    failed_impulse_extreme: Optional[float] = None
    pullback_swing_high: Optional[float] = None
    pullback_swing_low: Optional[float] = None


@dataclass(frozen=True)
class VefcfRoundtripV1:
    side: str
    signal_index: int
    fill_index: int
    exit_index: int
    entry_price: float
    exit_price: float
    exit_reason: VefcfExitReasonV1
    failed_impulse_extreme: float
    fade_trigger: VefcfFadeTriggerV1


@dataclass
class _SequenceState:
    expansion_confirmation_index: int
    impulse_index: Optional[int] = None
    impulse_side: Optional[StrategyEntrySideCarrierV1] = None
    impulse_high: Optional[float] = None
    impulse_low: Optional[float] = None
    impulse_range: Optional[float] = None
    pullback_qualifying: bool = False
    running_high: Optional[float] = None
    running_low: Optional[float] = None
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


def _opposite_side(side: StrategyEntrySideCarrierV1) -> StrategyEntrySideCarrierV1:
    if side is StrategyEntrySideCarrierV1.LONG:
        return StrategyEntrySideCarrierV1.SHORT
    if side is StrategyEntrySideCarrierV1.SHORT:
        return StrategyEntrySideCarrierV1.LONG
    raise ValueError("OPPOSITE_SIDE_UNDEFINED")


def _failed_impulse_extreme_for_side(
    impulse_side: StrategyEntrySideCarrierV1,
    *,
    impulse_high: float,
    impulse_low: float,
) -> float:
    # Contract: long fade reclaim uses short-impulse extreme (low);
    # short fade reclaim uses long-impulse extreme (high).
    if impulse_side is StrategyEntrySideCarrierV1.LONG:
        return float(impulse_high)
    if impulse_side is StrategyEntrySideCarrierV1.SHORT:
        return float(impulse_low)
    raise ValueError("IMPULSE_SIDE_UNDEFINED")


def _none_result(
    reason: VefcfReasonV1,
    *,
    percentile_rank_120: Optional[float] = None,
    realized_volatility_24: Optional[float] = None,
    upper_channel: Optional[float] = None,
    lower_channel: Optional[float] = None,
    expansion_confirmation_index: Optional[int] = None,
    impulse_index: Optional[int] = None,
    fade_trigger: Optional[VefcfFadeTriggerV1] = None,
    failed_impulse_extreme: Optional[float] = None,
    pullback_swing_high: Optional[float] = None,
    pullback_swing_low: Optional[float] = None,
) -> VefcfBarResultV1:
    return VefcfBarResultV1(
        event=VefcfEventV1.NONE,
        entry_side=StrategyEntrySideCarrierV1.NONE,
        event_kind=StrategyAgreementEventKindV1.NONE,
        reason=reason,
        percentile_rank_120=percentile_rank_120,
        realized_volatility_24=realized_volatility_24,
        upper_channel=upper_channel,
        lower_channel=lower_channel,
        expansion_confirmation_index=expansion_confirmation_index,
        impulse_index=impulse_index,
        fade_trigger=fade_trigger,
        failed_impulse_extreme=failed_impulse_extreme,
        pullback_swing_high=pullback_swing_high,
        pullback_swing_low=pullback_swing_low,
    )


def generate_vefcf_events_and_roundtrips_v1(
    data: pd.DataFrame,
    *,
    high_col: str = "high",
    low_col: str = "low",
    close_col: str = "close",
    open_col: str = "open",
    is_panel_last_bar_mask: Optional[np.ndarray] = None,
) -> tuple[list[VefcfBarResultV1], list[VefcfRoundtripV1]]:
    """Generate entry/exit events with guaranteed exit reachability for admitted fades.

    Expansion confirmation on completed bar t_exp (4 bars RV percentile >= 0.65).
    No entry on expansion confirmation bar. Impulse via 20-bar channel break while
    expansion remains active. Entry only after a failed-continuation trigger; fill
    at open of signal+1. Successful continuation cancels fade. No trailing exits.
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

    results: list[VefcfBarResultV1] = [_none_result(VefcfReasonV1.NO_EVENT) for _ in range(n)]
    roundtrips: list[VefcfRoundtripV1] = []

    pending_signal: Optional[tuple[int, StrategyEntrySideCarrierV1, float, VefcfFadeTriggerV1]] = (
        None  # signal_i, fade_side, failed_extreme, trigger
    )
    position = None
    pending_roundtrip_meta: Optional[tuple[int, int, float, float, VefcfFadeTriggerV1]] = (
        None  # sig, fill, entry_px, extreme, trigger
    )
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
                VefcfReasonV1.COOLDOWN,
                percentile_rank_120=rank_i,
                realized_volatility_24=rv_i,
                upper_channel=u_i,
                lower_channel=lo_i,
            )
            continue

        if pending_signal is not None:
            sig_i, side, extreme, trigger = pending_signal
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
                    failed_impulse_extreme=extreme,
                )
                pending_roundtrip_meta = (sig_i, fill_i, entry_px, extreme, trigger)
                pending_signal = None
                results[i] = VefcfBarResultV1(
                    event=VefcfEventV1.NONE,
                    entry_side=StrategyEntrySideCarrierV1.NONE,
                    event_kind=StrategyAgreementEventKindV1.NONE,
                    reason=VefcfReasonV1.POSITION_OPEN,
                    fill_index=fill_i,
                    signal_index=sig_i,
                    fade_trigger=trigger,
                    percentile_rank_120=rank_i,
                    realized_volatility_24=rv_i,
                    upper_channel=u_i,
                    lower_channel=lo_i,
                    failed_impulse_extreme=extreme,
                )
                continue
            if i < fill_i:
                results[i] = VefcfBarResultV1(
                    event=VefcfEventV1.NONE,
                    entry_side=StrategyEntrySideCarrierV1.NONE,
                    event_kind=StrategyAgreementEventKindV1.NONE,
                    reason=VefcfReasonV1.AWAITING_FILL,
                    signal_index=sig_i,
                    fade_trigger=trigger,
                    percentile_rank_120=rank_i,
                    realized_volatility_24=rv_i,
                    upper_channel=u_i,
                    lower_channel=lo_i,
                    failed_impulse_extreme=extreme,
                )
                continue

        if position is not None and pending_roundtrip_meta is not None:
            if i <= position.fill_index:
                results[i] = VefcfBarResultV1(
                    event=VefcfEventV1.NONE,
                    entry_side=StrategyEntrySideCarrierV1.NONE,
                    event_kind=StrategyAgreementEventKindV1.NONE,
                    reason=VefcfReasonV1.POSITION_OPEN,
                    fill_index=position.fill_index,
                    signal_index=pending_roundtrip_meta[0],
                    fade_trigger=pending_roundtrip_meta[4],
                    percentile_rank_120=rank_i,
                    realized_volatility_24=rv_i,
                    upper_channel=u_i,
                    lower_channel=lo_i,
                    failed_impulse_extreme=pending_roundtrip_meta[3],
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
                sig_i, fill_i, entry_px, extreme, trigger = pending_roundtrip_meta
                roundtrips.append(
                    VefcfRoundtripV1(
                        side=decision.side,
                        signal_index=sig_i,
                        fill_index=fill_i,
                        exit_index=decision.exit_index,
                        entry_price=entry_px,
                        exit_price=decision.exit_price,
                        exit_reason=decision.reason,
                        failed_impulse_extreme=extreme,
                        fade_trigger=trigger,
                    )
                )
                results[i] = VefcfBarResultV1(
                    event=VefcfEventV1.EXIT_EVENT,
                    entry_side=StrategyEntrySideCarrierV1.NONE,
                    event_kind=StrategyAgreementEventKindV1.NONE,
                    reason=VefcfReasonV1.EXIT_EMITTED,
                    exit_reason=decision.reason,
                    exit_price=decision.exit_price,
                    fill_index=fill_i,
                    signal_index=sig_i,
                    fade_trigger=trigger,
                    percentile_rank_120=rank_i,
                    realized_volatility_24=rv_i,
                    upper_channel=u_i,
                    lower_channel=lo_i,
                    failed_impulse_extreme=extreme,
                )
                position = None
                pending_roundtrip_meta = None
                seq = None
                awaiting_rearm = True
                cooldown_until = i + 1 + COOLDOWN_BARS_AFTER_EXIT_V1
                continue
            results[i] = VefcfBarResultV1(
                event=VefcfEventV1.NONE,
                entry_side=StrategyEntrySideCarrierV1.NONE,
                event_kind=StrategyAgreementEventKindV1.NONE,
                reason=VefcfReasonV1.POSITION_OPEN,
                fill_index=position.fill_index,
                signal_index=pending_roundtrip_meta[0],
                fade_trigger=pending_roundtrip_meta[4],
                percentile_rank_120=rank_i,
                realized_volatility_24=rv_i,
                upper_channel=u_i,
                lower_channel=lo_i,
                failed_impulse_extreme=pending_roundtrip_meta[3],
            )
            continue

        # Flat admission path.
        if rank_i is None or rv_i is None or not np.isfinite(c_i):
            results[i] = _none_result(
                VefcfReasonV1.WARMUP,
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
                    VefcfReasonV1.AWAITING_IMPULSE,
                    percentile_rank_120=rank_i,
                    realized_volatility_24=rv_i,
                    upper_channel=u_i,
                    lower_channel=lo_i,
                    expansion_confirmation_index=i,
                )
                continue
            results[i] = _none_result(
                VefcfReasonV1.AWAITING_REARM,
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
                    VefcfReasonV1.AWAITING_IMPULSE,
                    percentile_rank_120=rank_i,
                    realized_volatility_24=rv_i,
                    upper_channel=u_i,
                    lower_channel=lo_i,
                    expansion_confirmation_index=i,
                )
            else:
                results[i] = _none_result(
                    VefcfReasonV1.NO_EVENT,
                    percentile_rank_120=rank_i,
                    realized_volatility_24=rv_i,
                    upper_channel=u_i,
                    lower_channel=lo_i,
                )
            continue

        if i == seq.expansion_confirmation_index:
            results[i] = _none_result(
                VefcfReasonV1.AWAITING_IMPULSE,
                percentile_rank_120=rank_i,
                realized_volatility_24=rv_i,
                upper_channel=u_i,
                lower_channel=lo_i,
                expansion_confirmation_index=seq.expansion_confirmation_index,
            )
            continue

        expansion_active = _expansion_through(ranks_np, end_inclusive=i)

        if seq.impulse_index is None:
            if not expansion_active:
                seq = None
                awaiting_rearm = True
                results[i] = _none_result(
                    VefcfReasonV1.AWAITING_REARM,
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
                    VefcfReasonV1.AWAITING_IMPULSE,
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
                    VefcfReasonV1.AWAITING_REARM,
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
                    VefcfReasonV1.AWAITING_REARM,
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
            seq.running_high = None
            seq.running_low = None
            # Immediate post-impulse breakout fade without failure is forbidden.
            results[i] = _none_result(
                VefcfReasonV1.MONITORING_FAILED_CONTINUATION,
                percentile_rank_120=rank_i,
                realized_volatility_24=rv_i,
                upper_channel=u_i,
                lower_channel=lo_i,
                expansion_confirmation_index=seq.expansion_confirmation_index,
                impulse_index=i,
                failed_impulse_extreme=_failed_impulse_extreme_for_side(
                    impulse_side, impulse_high=h_i, impulse_low=l_i
                ),
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
                VefcfReasonV1.MONITORING_FAILED_CONTINUATION,
                percentile_rank_120=rank_i,
                realized_volatility_24=rv_i,
                upper_channel=u_i,
                lower_channel=lo_i,
                expansion_confirmation_index=seq.expansion_confirmation_index,
                impulse_index=seq.impulse_index,
            )
            continue

        if not np.isfinite(h_i) or not np.isfinite(l_i) or not np.isfinite(c_i):
            seq = None
            awaiting_rearm = True
            results[i] = _none_result(
                VefcfReasonV1.AMBIGUOUS_TRIGGER_FAIL_CLOSED,
                percentile_rank_120=rank_i,
                realized_volatility_24=rv_i,
                upper_channel=u_i,
                lower_channel=lo_i,
            )
            continue

        if bars_since_impulse > MAX_MONITORING_BARS_INCLUSIVE_V1:
            seq = None
            awaiting_rearm = True
            results[i] = _none_result(
                VefcfReasonV1.AWAITING_REARM,
                percentile_rank_120=rank_i,
                realized_volatility_24=rv_i,
                upper_channel=u_i,
                lower_channel=lo_i,
            )
            continue

        # Update running extremes after impulse for pullback depth.
        seq.running_high = h_i if seq.running_high is None else max(seq.running_high, h_i)
        seq.running_low = l_i if seq.running_low is None else min(seq.running_low, l_i)

        if seq.impulse_side is StrategyEntrySideCarrierV1.LONG:
            pullback_depth = (seq.impulse_high - seq.running_low) / seq.impulse_range
        else:
            pullback_depth = (seq.running_high - seq.impulse_low) / seq.impulse_range

        extreme_break = False
        if seq.impulse_side is StrategyEntrySideCarrierV1.LONG:
            extreme_break = l_i < seq.impulse_low
        else:
            extreme_break = h_i > seq.impulse_high

        deep_pullback = pullback_depth >= DEEP_PULLBACK_FRACTION_V1

        # Qualifying pullback freeze (VEPC-style swings) for continuation cancel /
        # window-exhaustion fade. Qualifying is >=15%; deep (>=50%) is a fade trigger.
        if (
            not seq.pullback_qualifying
            and MIN_PULLBACK_FRACTION_QUALIFYING_V1 <= pullback_depth < DEEP_PULLBACK_FRACTION_V1
        ):
            seq.pullback_qualifying = True
            seq.pullback_swing_high = float(seq.running_high)
            seq.pullback_swing_low = float(seq.running_low)

        continued = False
        if seq.pullback_qualifying:
            assert seq.pullback_swing_high is not None and seq.pullback_swing_low is not None
            if seq.impulse_side is StrategyEntrySideCarrierV1.LONG:
                continued = c_i > seq.pullback_swing_high
            else:
                continued = c_i < seq.pullback_swing_low

        # Ambiguity: fade trigger and successful continuation on the same bar.
        fade_candidate = extreme_break or deep_pullback
        if fade_candidate and continued:
            results[i] = _none_result(
                VefcfReasonV1.AMBIGUOUS_TRIGGER_FAIL_CLOSED,
                percentile_rank_120=rank_i,
                realized_volatility_24=rv_i,
                upper_channel=u_i,
                lower_channel=lo_i,
                expansion_confirmation_index=seq.expansion_confirmation_index,
                impulse_index=seq.impulse_index,
            )
            seq = None
            awaiting_rearm = True
            continue

        if continued and SUCCESSFUL_CONTINUATION_CANCELS_FADE_V1:
            results[i] = _none_result(
                VefcfReasonV1.CONTINUATION_CANCELLED_FADE,
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

        trigger: Optional[VefcfFadeTriggerV1] = None
        if extreme_break:
            trigger = VefcfFadeTriggerV1.IMPULSE_EXTREME_BREAK_AGAINST_IMPULSE
        elif deep_pullback:
            trigger = VefcfFadeTriggerV1.DEEP_PULLBACK_WITHOUT_CONTINUATION
        elif (
            bars_since_impulse == MAX_MONITORING_BARS_INCLUSIVE_V1
            and seq.pullback_qualifying
            and not continued
        ):
            trigger = VefcfFadeTriggerV1.QUALIFYING_PULLBACK_WINDOW_EXHAUSTION_WITHOUT_CONTINUATION
        elif bars_since_impulse == MAX_MONITORING_BARS_INCLUSIVE_V1 and not seq.pullback_qualifying:
            # Window exhausted without qualifying pullback and without fade trigger.
            seq = None
            awaiting_rearm = True
            results[i] = _none_result(
                VefcfReasonV1.AWAITING_REARM,
                percentile_rank_120=rank_i,
                realized_volatility_24=rv_i,
                upper_channel=u_i,
                lower_channel=lo_i,
            )
            continue

        if trigger is None:
            results[i] = _none_result(
                VefcfReasonV1.MONITORING_FAILED_CONTINUATION,
                percentile_rank_120=rank_i,
                realized_volatility_24=rv_i,
                upper_channel=u_i,
                lower_channel=lo_i,
                expansion_confirmation_index=seq.expansion_confirmation_index,
                impulse_index=seq.impulse_index,
                pullback_swing_high=seq.pullback_swing_high,
                pullback_swing_low=seq.pullback_swing_low,
                failed_impulse_extreme=_failed_impulse_extreme_for_side(
                    seq.impulse_side,
                    impulse_high=seq.impulse_high,
                    impulse_low=seq.impulse_low,
                ),
            )
            continue

        # Fade entry opposite the failed impulse.
        if i == seq.expansion_confirmation_index:
            results[i] = _none_result(
                VefcfReasonV1.NO_EVENT,
                percentile_rank_120=rank_i,
                realized_volatility_24=rv_i,
                upper_channel=u_i,
                lower_channel=lo_i,
            )
            continue

        if not entry_exit_reachable_ex_ante_v1(signal_index=i, series_length=n):
            results[i] = _none_result(
                VefcfReasonV1.ENTRY_SUPPRESSED_EXIT_UNREACHABLE,
                percentile_rank_120=rank_i,
                realized_volatility_24=rv_i,
                upper_channel=u_i,
                lower_channel=lo_i,
                expansion_confirmation_index=seq.expansion_confirmation_index,
                impulse_index=seq.impulse_index,
                fade_trigger=trigger,
            )
            seq = None
            awaiting_rearm = True
            continue

        fade_side = _opposite_side(seq.impulse_side)
        extreme = _failed_impulse_extreme_for_side(
            seq.impulse_side,
            impulse_high=seq.impulse_high,
            impulse_low=seq.impulse_low,
        )
        seq.entry_consumed = True
        pending_signal = (i, fade_side, extreme, trigger)
        results[i] = VefcfBarResultV1(
            event=VefcfEventV1.ENTRY_EVENT,
            entry_side=fade_side,
            event_kind=StrategyAgreementEventKindV1.ENTRY,
            reason=VefcfReasonV1.SUCCESSFUL_ENTRY,
            signal_index=i,
            expansion_confirmation_index=seq.expansion_confirmation_index,
            impulse_index=seq.impulse_index,
            fade_trigger=trigger,
            percentile_rank_120=rank_i,
            realized_volatility_24=rv_i,
            upper_channel=u_i,
            lower_channel=lo_i,
            failed_impulse_extreme=extreme,
            pullback_swing_high=seq.pullback_swing_high,
            pullback_swing_low=seq.pullback_swing_low,
        )
        seq = None
        awaiting_rearm = True

    return results, roundtrips


__all__ = [
    "BASELINE_ID_V1",
    "CHANNEL_LOOKBACK_BARS_V1",
    "CONTRACTION_ADMISSION_NOT_REQUIRED_V1",
    "DEEP_PULLBACK_FRACTION_V1",
    "ENTRY_ON_EXPANSION_CONFIRMATION_BAR_FORBIDDEN_V1",
    "EVENT_CONSUMPTION_V1",
    "EXIT_PARAMS_V1",
    "EXIT_STATE_MACHINE_IMPLEMENTED_V1",
    "EXPANSION_MIN_CONSECUTIVE_BARS_V1",
    "EXPANSION_PERCENTILE_INCLUSIVE_MIN_V1",
    "FADE_TRIGGERS_FIRST_WINS_V1",
    "IMMEDIATE_BREAKOUT_WITHOUT_FAILURE_FORBIDDEN_V1",
    "MAX_ENTRIES_PER_EXPANSION_IMPULSE_SEQUENCE_V1",
    "MAX_MONITORING_BARS_INCLUSIVE_V1",
    "MIN_PULLBACK_FRACTION_QUALIFYING_V1",
    "PREDECESSOR_STRATEGY_ID_V1",
    "PRODUCTIVE_EXIT_PNL_EVALUATOR_REF_V1",
    "PROGRAM_ID_V1",
    "SIGNAL_FAMILY_V1",
    "STRATEGY_ID_V1",
    "STRATEGY_IDENTITY_V1",
    "STRATEGY_VERSION_V1",
    "SUCCESSFUL_CONTINUATION_CANCELS_FADE_V1",
    "VEPC_CONTINUATION_ENTRY_FORBIDDEN_V1",
    "VefcfBarResultV1",
    "VefcfEventV1",
    "VefcfFadeTriggerV1",
    "VefcfReasonV1",
    "VefcfRoundtripV1",
    "classify_price_channel_break_v1",
    "compute_prior_high_low_channel_bounds_v1",
    "entry_exit_reachable_ex_ante_v1",
    "evaluate_exit_on_bar_v1",
    "generate_vefcf_events_and_roundtrips_v1",
    "open_position_from_fill_v1",
]
