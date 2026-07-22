"""VOLATILITY_CONTRACTION_EXPANSION_BREAKOUT_V1 strategy producer.

Implements RV(24) contraction→expansion joint same-bar channel-break admission,
ex-ante exit reachability, and a deterministic exit state machine with opposite-break
invalidation (no trailing). No PnL/equity/stats truth. No evaluation.
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
from src.research.volatility_contraction_expansion_breakout_v1_exit_state_machine_v1 import (
    COOLDOWN_BARS_AFTER_EXIT_V1,
    EXIT_PRECEDENCE_ASCENDING_WINS_FIRST_V1,
    MIN_POST_FILL_BARS_REQUIRED_INCLUSIVE_V1,
    SIGNAL_LAG_BARS_V1,
    TIME_EXIT_MAX_BARS_V1,
    TRAILING_STOP_FORBIDDEN_V1,
    VcebExitReasonV1,
    entry_exit_reachable_ex_ante_v1,
    evaluate_exit_on_bar_v1,
    open_position_from_fill_v1,
)
from src.research.volatility_contraction_expansion_breakout_v1_vol_state_v1 import (
    compute_atr14_v1,
    compute_percentile_rank_120_realized_vol_v1,
    compute_realized_volatility_24_v1,
)
from src.trading.master_v2.strategy_suitability_agreement_material_v1 import (
    StrategyAgreementEventKindV1,
    StrategyEntrySideCarrierV1,
)

STRATEGY_IDENTITY_V1 = "VOLATILITY_CONTRACTION_EXPANSION_BREAKOUT_V1"
STRATEGY_ID_V1 = "volatility_contraction_expansion_breakout"
STRATEGY_VERSION_V1 = "v1"
SIGNAL_FAMILY_V1 = "VOLATILITY_REGIME"
PROGRAM_ID_V1 = "VOLATILITY_REGIME_RESEARCH_PROGRAM_V1"
BASELINE_ID_V1 = "UNCONDITIONAL_20_BAR_PRICE_CHANNEL_BREAKOUT_V1"
PREDECESSOR_STRATEGY_ID_V1 = "VOLATILITY_DECAY_BREAKOUT_WITH_EXPLICIT_DECAY_EXIT_V1"
PREVIOUS_STRATEGY_ID_V1 = "VOLATILITY_DECAY_BREAKOUT_V1"

CONTRACTION_PERCENTILE_INCLUSIVE_MAX_V1 = 0.30
CONTRACTION_MIN_CONSECUTIVE_BARS_V1 = 8
EXPANSION_ABSOLUTE_PERCENTILE_INCLUSIVE_MIN_V1 = 0.65
EXPANSION_RELATIVE_PERCENTILE_RISE_INCLUSIVE_MIN_V1 = 0.25
ENTRY_WINDOW_START_OFFSET_V1 = 1
ENTRY_WINDOW_END_OFFSET_V1 = 1
MAX_ENTRIES_PER_TRANSITION_EVENT_V1 = 1
EVENT_CONSUMPTION_V1 = "SINGLE_USE"
CHANNEL_LOOKBACK_BARS_V1 = CHANNEL_LOOKBACK_COMPLETED_BARS_V1
JOINT_COINCIDENCE_REQUIRED_V1 = True
ENTRY_ON_JOINT_TRIGGER_BAR_T_FORBIDDEN_V1 = True
VCB_STYLE_MULTI_BAR_RELEASE_WINDOW_FORBIDDEN_V1 = True
DECAY_ADMISSION_NOT_REQUIRED_V1 = True

EXIT_STATE_MACHINE_IMPLEMENTED_V1 = True
PRODUCTIVE_EXIT_PNL_EVALUATOR_REF_V1 = (
    "src/research/volatility_compression_breakout_v1_development_evaluation_v1/"
    "productive_exit_pnl_evaluator_v1.py"
)

EXIT_PARAMS_V1 = {
    "initial_stop_atr_multiple": 1.5,
    "trailing_stop_forbidden": TRAILING_STOP_FORBIDDEN_V1,
    "trailing_stop_not_used": True,
    "opposite_break_invalidation_authorized": True,
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


class VcebEventV1(str, Enum):
    ENTRY_EVENT = "ENTRY_EVENT"
    EXIT_EVENT = "EXIT_EVENT"
    NONE = "NONE"


class VcebReasonV1(str, Enum):
    SUCCESSFUL_ENTRY = "SUCCESSFUL_ENTRY"
    EXIT_EMITTED = "EXIT_EMITTED"
    ENTRY_SUPPRESSED_EXIT_UNREACHABLE = "ENTRY_SUPPRESSED_EXIT_UNREACHABLE"
    JOINT_TRIGGER_WITHOUT_BREAK_RESET = "JOINT_TRIGGER_WITHOUT_BREAK_RESET"
    NO_EVENT = "NO_EVENT"
    WARMUP = "WARMUP"
    POSITION_OPEN = "POSITION_OPEN"
    AWAITING_FILL = "AWAITING_FILL"
    AWAITING_REARM = "AWAITING_REARM"
    COOLDOWN = "COOLDOWN"


@dataclass(frozen=True)
class VcebBarResultV1:
    event: VcebEventV1
    entry_side: StrategyEntrySideCarrierV1
    event_kind: StrategyAgreementEventKindV1
    reason: VcebReasonV1
    exit_reason: Optional[VcebExitReasonV1] = None
    exit_price: Optional[float] = None
    fill_index: Optional[int] = None
    signal_index: Optional[int] = None
    confirmation_bar_index: Optional[int] = None
    percentile_rank_120: Optional[float] = None
    realized_volatility_24: Optional[float] = None
    upper_channel: Optional[float] = None
    lower_channel: Optional[float] = None


@dataclass(frozen=True)
class VcebRoundtripV1:
    side: str
    signal_index: int
    fill_index: int
    exit_index: int
    entry_price: float
    exit_price: float
    exit_reason: VcebExitReasonV1


def _contraction_through(
    ranks: np.ndarray,
    *,
    end_inclusive: int,
    bars: int = CONTRACTION_MIN_CONSECUTIVE_BARS_V1,
    thr: float = CONTRACTION_PERCENTILE_INCLUSIVE_MAX_V1,
) -> bool:
    if end_inclusive < bars - 1:
        return False
    start = end_inclusive - bars + 1
    window = ranks[start : end_inclusive + 1]
    if window.shape[0] != bars:
        return False
    if not np.isfinite(window).all():
        return False
    return bool(np.all(window <= thr))


def _is_expansion_trigger(
    *,
    rank_t: float,
    rank_tm1: float,
    rv_t: float,
    rv_tm1: float,
) -> bool:
    return (
        rank_t >= EXPANSION_ABSOLUTE_PERCENTILE_INCLUSIVE_MIN_V1
        and (rank_t - rank_tm1) >= EXPANSION_RELATIVE_PERCENTILE_RISE_INCLUSIVE_MIN_V1
        and rv_t > rv_tm1
    )


def generate_vceb_events_and_roundtrips_v1(
    data: pd.DataFrame,
    *,
    high_col: str = "high",
    low_col: str = "low",
    close_col: str = "close",
    open_col: str = "open",
    is_panel_last_bar_mask: Optional[np.ndarray] = None,
) -> tuple[list[VcebBarResultV1], list[VcebRoundtripV1]]:
    """Generate entry/exit events with guaranteed exit reachability for admitted entries.

    Joint CONTRACTION→EXPANSION + directional break is observed on completed bar t.
    ENTRY_EVENT is emitted on bar t (signal); fill is conceptually open of t+1 via lag.
    No fill on bar t. No trailing exits. Rearm requires a new full 8-bar contraction.
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

    results: list[VcebBarResultV1] = [
        VcebBarResultV1(
            event=VcebEventV1.NONE,
            entry_side=StrategyEntrySideCarrierV1.NONE,
            event_kind=StrategyAgreementEventKindV1.NONE,
            reason=VcebReasonV1.NO_EVENT,
        )
        for _ in range(n)
    ]
    roundtrips: list[VcebRoundtripV1] = []

    pending_signal: Optional[tuple[int, StrategyEntrySideCarrierV1]] = None
    position = None
    pending_roundtrip_meta: Optional[tuple[int, int, float]] = None
    cooldown_until = -1
    awaiting_rearm = False

    for i in range(n):
        rank_i = float(ranks_np[i]) if np.isfinite(ranks_np[i]) else None
        rv_i = float(rv_np[i]) if np.isfinite(rv_np[i]) else None
        u_i = float(upper.iloc[i]) if np.isfinite(upper.iloc[i]) else None
        lo_i = float(lower.iloc[i]) if np.isfinite(lower.iloc[i]) else None

        if i < cooldown_until:
            results[i] = VcebBarResultV1(
                event=VcebEventV1.NONE,
                entry_side=StrategyEntrySideCarrierV1.NONE,
                event_kind=StrategyAgreementEventKindV1.NONE,
                reason=VcebReasonV1.COOLDOWN,
                percentile_rank_120=rank_i,
                realized_volatility_24=rv_i,
                upper_channel=u_i,
                lower_channel=lo_i,
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
                results[i] = VcebBarResultV1(
                    event=VcebEventV1.NONE,
                    entry_side=StrategyEntrySideCarrierV1.NONE,
                    event_kind=StrategyAgreementEventKindV1.NONE,
                    reason=VcebReasonV1.POSITION_OPEN,
                    fill_index=fill_i,
                    signal_index=sig_i,
                    confirmation_bar_index=sig_i,
                    percentile_rank_120=rank_i,
                    realized_volatility_24=rv_i,
                    upper_channel=u_i,
                    lower_channel=lo_i,
                )
                continue
            if i < fill_i:
                results[i] = VcebBarResultV1(
                    event=VcebEventV1.NONE,
                    entry_side=StrategyEntrySideCarrierV1.NONE,
                    event_kind=StrategyAgreementEventKindV1.NONE,
                    reason=VcebReasonV1.AWAITING_FILL,
                    signal_index=sig_i,
                    confirmation_bar_index=sig_i,
                    percentile_rank_120=rank_i,
                    realized_volatility_24=rv_i,
                    upper_channel=u_i,
                    lower_channel=lo_i,
                )
                continue

        if position is not None and pending_roundtrip_meta is not None:
            if i <= position.fill_index:
                results[i] = VcebBarResultV1(
                    event=VcebEventV1.NONE,
                    entry_side=StrategyEntrySideCarrierV1.NONE,
                    event_kind=StrategyAgreementEventKindV1.NONE,
                    reason=VcebReasonV1.POSITION_OPEN,
                    fill_index=position.fill_index,
                    signal_index=pending_roundtrip_meta[0],
                    percentile_rank_120=rank_i,
                    realized_volatility_24=rv_i,
                    upper_channel=u_i,
                    lower_channel=lo_i,
                )
                continue
            h = float(high.iloc[i])
            lo = float(low.iloc[i])
            c = float(close.iloc[i])
            decision, position = evaluate_exit_on_bar_v1(
                position,
                bar_index=i,
                high=h,
                low=lo,
                close=c,
                percentile_rank=rank_i,
                upper_channel=u_i,
                lower_channel=lo_i,
                is_last_instrument_bar=(i == n - 1),
                is_last_panel_bar=bool(panel_last[i]),
            )
            if decision is not None:
                sig_i, fill_i, entry_px = pending_roundtrip_meta
                roundtrips.append(
                    VcebRoundtripV1(
                        side=decision.side,
                        signal_index=sig_i,
                        fill_index=fill_i,
                        exit_index=decision.exit_index,
                        entry_price=entry_px,
                        exit_price=decision.exit_price,
                        exit_reason=decision.reason,
                    )
                )
                results[i] = VcebBarResultV1(
                    event=VcebEventV1.EXIT_EVENT,
                    entry_side=StrategyEntrySideCarrierV1.NONE,
                    event_kind=StrategyAgreementEventKindV1.NONE,
                    reason=VcebReasonV1.EXIT_EMITTED,
                    exit_reason=decision.reason,
                    exit_price=decision.exit_price,
                    fill_index=fill_i,
                    signal_index=sig_i,
                    confirmation_bar_index=sig_i,
                    percentile_rank_120=rank_i,
                    realized_volatility_24=rv_i,
                    upper_channel=u_i,
                    lower_channel=lo_i,
                )
                position = None
                pending_roundtrip_meta = None
                awaiting_rearm = True
                cooldown_until = i + 1 + COOLDOWN_BARS_AFTER_EXIT_V1
                continue
            results[i] = VcebBarResultV1(
                event=VcebEventV1.NONE,
                entry_side=StrategyEntrySideCarrierV1.NONE,
                event_kind=StrategyAgreementEventKindV1.NONE,
                reason=VcebReasonV1.POSITION_OPEN,
                fill_index=position.fill_index,
                signal_index=pending_roundtrip_meta[0],
                percentile_rank_120=rank_i,
                realized_volatility_24=rv_i,
                upper_channel=u_i,
                lower_channel=lo_i,
            )
            continue

        # Flat: evaluate joint transition admission on completed bar t.
        if rank_i is None or rv_i is None or i < 1:
            results[i] = VcebBarResultV1(
                event=VcebEventV1.NONE,
                entry_side=StrategyEntrySideCarrierV1.NONE,
                event_kind=StrategyAgreementEventKindV1.NONE,
                reason=VcebReasonV1.WARMUP,
                percentile_rank_120=rank_i,
                realized_volatility_24=rv_i,
                upper_channel=u_i,
                lower_channel=lo_i,
            )
            continue

        rank_tm1 = float(ranks_np[i - 1]) if np.isfinite(ranks_np[i - 1]) else None
        rv_tm1 = float(rv_np[i - 1]) if np.isfinite(rv_np[i - 1]) else None
        if rank_tm1 is None or rv_tm1 is None:
            results[i] = VcebBarResultV1(
                event=VcebEventV1.NONE,
                entry_side=StrategyEntrySideCarrierV1.NONE,
                event_kind=StrategyAgreementEventKindV1.NONE,
                reason=VcebReasonV1.WARMUP,
                percentile_rank_120=rank_i,
                realized_volatility_24=rv_i,
                upper_channel=u_i,
                lower_channel=lo_i,
            )
            continue

        if awaiting_rearm:
            # Rearm only after a newly completed full 8-bar contraction through current bar.
            if _contraction_through(ranks_np, end_inclusive=i):
                awaiting_rearm = False
            else:
                results[i] = VcebBarResultV1(
                    event=VcebEventV1.NONE,
                    entry_side=StrategyEntrySideCarrierV1.NONE,
                    event_kind=StrategyAgreementEventKindV1.NONE,
                    reason=VcebReasonV1.AWAITING_REARM,
                    percentile_rank_120=rank_i,
                    realized_volatility_24=rv_i,
                    upper_channel=u_i,
                    lower_channel=lo_i,
                )
                continue

        contraction_prior = _contraction_through(ranks_np, end_inclusive=i - 1)
        expansion = _is_expansion_trigger(
            rank_t=rank_i,
            rank_tm1=rank_tm1,
            rv_t=rv_i,
            rv_tm1=rv_tm1,
        )

        if not (contraction_prior and expansion):
            results[i] = VcebBarResultV1(
                event=VcebEventV1.NONE,
                entry_side=StrategyEntrySideCarrierV1.NONE,
                event_kind=StrategyAgreementEventKindV1.NONE,
                reason=VcebReasonV1.NO_EVENT,
                percentile_rank_120=rank_i,
                realized_volatility_24=rv_i,
                upper_channel=u_i,
                lower_channel=lo_i,
            )
            continue

        # Expansion trigger on t: require same-bar directional break (joint coincidence).
        close_f = float(close.iloc[i])
        if u_i is None or lo_i is None or not np.isfinite(close_f):
            awaiting_rearm = True
            results[i] = VcebBarResultV1(
                event=VcebEventV1.NONE,
                entry_side=StrategyEntrySideCarrierV1.NONE,
                event_kind=StrategyAgreementEventKindV1.NONE,
                reason=VcebReasonV1.JOINT_TRIGGER_WITHOUT_BREAK_RESET,
                confirmation_bar_index=i,
                percentile_rank_120=rank_i,
                realized_volatility_24=rv_i,
                upper_channel=u_i,
                lower_channel=lo_i,
            )
            continue

        break_side = classify_price_channel_break_v1(close_f, u_i, lo_i)
        if break_side is PriceChannelBreakSideV1.NONE:
            awaiting_rearm = True
            results[i] = VcebBarResultV1(
                event=VcebEventV1.NONE,
                entry_side=StrategyEntrySideCarrierV1.NONE,
                event_kind=StrategyAgreementEventKindV1.NONE,
                reason=VcebReasonV1.JOINT_TRIGGER_WITHOUT_BREAK_RESET,
                confirmation_bar_index=i,
                percentile_rank_120=rank_i,
                realized_volatility_24=rv_i,
                upper_channel=u_i,
                lower_channel=lo_i,
            )
            continue

        side = (
            StrategyEntrySideCarrierV1.LONG
            if break_side is PriceChannelBreakSideV1.LONG
            else StrategyEntrySideCarrierV1.SHORT
        )

        # ENTRY_EVENT on confirmation bar t; fill at open of t+1 via signal_lag.
        # Entry window offsets [1] encode the sole fill bar relative to confirmation.
        if not entry_exit_reachable_ex_ante_v1(signal_index=i, series_length=n):
            awaiting_rearm = True
            results[i] = VcebBarResultV1(
                event=VcebEventV1.NONE,
                entry_side=StrategyEntrySideCarrierV1.NONE,
                event_kind=StrategyAgreementEventKindV1.NONE,
                reason=VcebReasonV1.ENTRY_SUPPRESSED_EXIT_UNREACHABLE,
                confirmation_bar_index=i,
                signal_index=i,
                percentile_rank_120=rank_i,
                realized_volatility_24=rv_i,
                upper_channel=u_i,
                lower_channel=lo_i,
            )
            continue

        pending_signal = (i, side)
        awaiting_rearm = True  # single-use; rearm requires new full contraction after exit/use
        results[i] = VcebBarResultV1(
            event=VcebEventV1.ENTRY_EVENT,
            entry_side=side,
            event_kind=StrategyAgreementEventKindV1.ENTRY,
            reason=VcebReasonV1.SUCCESSFUL_ENTRY,
            signal_index=i,
            confirmation_bar_index=i,
            percentile_rank_120=rank_i,
            realized_volatility_24=rv_i,
            upper_channel=u_i,
            lower_channel=lo_i,
        )

    if position is not None:
        raise ValueError("UNPAIRABLE_ENTRY_NO_EXIT_STRATEGY_EMITTED")

    return results, roundtrips


def generate_vceb_event_series_v1(data: pd.DataFrame, **kwargs: object) -> pd.DataFrame:
    rows, _ = generate_vceb_events_and_roundtrips_v1(data, **kwargs)  # type: ignore[arg-type]
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
            "confirmation_bar_index": [r.confirmation_bar_index for r in rows],
        },
        index=data.index,
    )


__all__ = [
    "BASELINE_ID_V1",
    "CHANNEL_LOOKBACK_BARS_V1",
    "CONTRACTION_MIN_CONSECUTIVE_BARS_V1",
    "CONTRACTION_PERCENTILE_INCLUSIVE_MAX_V1",
    "DECAY_ADMISSION_NOT_REQUIRED_V1",
    "ENTRY_ON_JOINT_TRIGGER_BAR_T_FORBIDDEN_V1",
    "ENTRY_WINDOW_END_OFFSET_V1",
    "ENTRY_WINDOW_START_OFFSET_V1",
    "EVENT_CONSUMPTION_V1",
    "EXIT_PARAMS_V1",
    "EXIT_STATE_MACHINE_IMPLEMENTED_V1",
    "EXPANSION_ABSOLUTE_PERCENTILE_INCLUSIVE_MIN_V1",
    "EXPANSION_RELATIVE_PERCENTILE_RISE_INCLUSIVE_MIN_V1",
    "JOINT_COINCIDENCE_REQUIRED_V1",
    "MAX_ENTRIES_PER_TRANSITION_EVENT_V1",
    "PREDECESSOR_STRATEGY_ID_V1",
    "PREVIOUS_STRATEGY_ID_V1",
    "PRODUCTIVE_EXIT_PNL_EVALUATOR_REF_V1",
    "PROGRAM_ID_V1",
    "SIGNAL_FAMILY_V1",
    "STRATEGY_ID_V1",
    "STRATEGY_IDENTITY_V1",
    "STRATEGY_VERSION_V1",
    "VCB_STYLE_MULTI_BAR_RELEASE_WINDOW_FORBIDDEN_V1",
    "VcebBarResultV1",
    "VcebEventV1",
    "VcebReasonV1",
    "VcebRoundtripV1",
    "classify_price_channel_break_v1",
    "compute_prior_high_low_channel_bounds_v1",
    "generate_vceb_event_series_v1",
    "generate_vceb_events_and_roundtrips_v1",
]
