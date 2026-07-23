"""VOLATILITY_TERM_STRUCTURE_REVERSION_V1 strategy producer.

Implements elevated short/long RV term-structure ratio → fade opposite the
short-horizon signed return, with term-structure-normalization exits.
No PnL/equity/stats truth. No evaluation.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional

import numpy as np
import pandas as pd

from src.research.volatility_term_structure_reversion_v1_exit_state_machine_v1 import (
    COOLDOWN_BARS_AFTER_EXIT_V1,
    EXIT_PRECEDENCE_ASCENDING_WINS_FIRST_V1,
    MIN_POST_FILL_BARS_REQUIRED_INCLUSIVE_V1,
    SIGNAL_LAG_BARS_V1,
    TIME_EXIT_MAX_BARS_V1,
    TRAILING_STOP_FORBIDDEN_V1,
    VtsrExitReasonV1,
    entry_exit_reachable_ex_ante_v1,
    evaluate_exit_on_bar_v1,
    open_position_from_fill_v1,
)
from src.research.volatility_term_structure_reversion_v1_vol_state_v1 import (
    RV_LONG_HORIZON_COMPLETED_BARS_V1,
    RV_SHORT_HORIZON_COMPLETED_BARS_V1,
    compute_atr14_v1,
    compute_percentile_rank_120_rv_term_structure_ratio_v1,
    compute_realized_volatility_long_48_v1,
    compute_realized_volatility_short_8_v1,
    compute_rv_term_structure_ratio_short_over_long_v1,
)
from src.trading.master_v2.strategy_suitability_agreement_material_v1 import (
    StrategyAgreementEventKindV1,
    StrategyEntrySideCarrierV1,
)

STRATEGY_IDENTITY_V1 = "VOLATILITY_TERM_STRUCTURE_REVERSION_V1"
STRATEGY_ID_V1 = "volatility_term_structure_reversion"
STRATEGY_VERSION_V1 = "v1"
SIGNAL_FAMILY_V1 = "VOLATILITY_REGIME"
PROGRAM_ID_V1 = "VOLATILITY_REGIME_RESEARCH_PROGRAM_V1"
BASELINE_ID_V1 = "UNCONDITIONAL_20_BAR_PRICE_CHANNEL_BREAKOUT_V1"
PREDECESSOR_STRATEGY_ID_V1 = "VOLATILITY_EXPANSION_FAILED_CONTINUATION_FADE_V1"
HYPOTHESIS_ID_V1 = "VOLATILITY_TERM_STRUCTURE_REVERSION_NON_BITCOIN_PERPETUALS_V1"

ELEVATED_RATIO_PERCENTILE_INCLUSIVE_MIN_V1 = 0.80
ELEVATED_MIN_CONSECUTIVE_BARS_V1 = 2
REARM_RATIO_PERCENTILE_STRICTLY_BELOW_V1 = 0.50
DEPRESSED_ENTRY_FORBIDDEN_IN_V1 = True
MAX_ENTRIES_PER_ELEVATED_EPISODE_V1 = 1
EVENT_CONSUMPTION_V1 = "SINGLE_USE"
SHORT_HORIZON_RETURN_LOOKBACK_COMPLETED_BARS_V1 = RV_SHORT_HORIZON_COMPLETED_BARS_V1
NO_CHANNEL_BREAKOUT_REQUIRED_V1 = True
NO_EXPANSION_STATE_REQUIRED_V1 = True
NO_COMPRESSION_BREAKOUT_REQUIRED_V1 = True
VEFCF_FAILED_CONTINUATION_FADE_ENTRY_FORBIDDEN_V1 = True
VEPC_PULLBACK_CONTINUATION_ENTRY_FORBIDDEN_V1 = True
VCB_COMPRESSION_BREAKOUT_ENTRY_FORBIDDEN_V1 = True

EXIT_STATE_MACHINE_IMPLEMENTED_V1 = True
PRODUCTIVE_EXIT_PNL_EVALUATOR_REF_V1 = (
    "src/research/volatility_compression_breakout_v1_development_evaluation_v1/"
    "productive_exit_pnl_evaluator_v1.py"
)

EXIT_PARAMS_V1 = {
    "initial_stop_atr_multiple": 1.5,
    "trailing_stop_forbidden": TRAILING_STOP_FORBIDDEN_V1,
    "trailing_stop_not_used": True,
    "term_structure_normalization_ratio_percentile_lt": 0.55,
    "regime_invalidation_ratio_percentile_lt": 0.40,
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


class VtsrEventV1(str, Enum):
    ENTRY_EVENT = "ENTRY_EVENT"
    EXIT_EVENT = "EXIT_EVENT"
    NONE = "NONE"


class VtsrReasonV1(str, Enum):
    SUCCESSFUL_ENTRY = "SUCCESSFUL_ENTRY"
    EXIT_EMITTED = "EXIT_EMITTED"
    ENTRY_SUPPRESSED_EXIT_UNREACHABLE = "ENTRY_SUPPRESSED_EXIT_UNREACHABLE"
    NO_EVENT = "NO_EVENT"
    WARMUP = "WARMUP"
    POSITION_OPEN = "POSITION_OPEN"
    AWAITING_FILL = "AWAITING_FILL"
    AWAITING_REARM = "AWAITING_REARM"
    ELEVATED_MONITORING = "ELEVATED_MONITORING"
    AMBIGUOUS_DIRECTION_FAIL_CLOSED = "AMBIGUOUS_DIRECTION_FAIL_CLOSED"
    INVALID_INPUT_FAIL_CLOSED = "INVALID_INPUT_FAIL_CLOSED"
    COOLDOWN = "COOLDOWN"
    EPISODE_CONSUMED = "EPISODE_CONSUMED"


@dataclass(frozen=True)
class VtsrBarResultV1:
    event: VtsrEventV1
    entry_side: StrategyEntrySideCarrierV1
    event_kind: StrategyAgreementEventKindV1
    reason: VtsrReasonV1
    exit_reason: Optional[VtsrExitReasonV1] = None
    exit_price: Optional[float] = None
    fill_index: Optional[int] = None
    signal_index: Optional[int] = None
    elevated_confirmation_index: Optional[int] = None
    ratio_percentile_120: Optional[float] = None
    rv_term_structure_ratio: Optional[float] = None
    realized_volatility_short_8: Optional[float] = None
    realized_volatility_long_48: Optional[float] = None
    short_horizon_signed_return: Optional[float] = None


@dataclass(frozen=True)
class VtsrRoundtripV1:
    side: str
    signal_index: int
    fill_index: int
    exit_index: int
    entry_price: float
    exit_price: float
    exit_reason: VtsrExitReasonV1
    elevated_confirmation_index: int
    short_horizon_signed_return: float


@dataclass
class _ElevatedEpisodeState:
    confirmation_index: int
    entry_consumed: bool = False


def _elevated_through(
    ranks: np.ndarray,
    *,
    end_inclusive: int,
    bars: int = ELEVATED_MIN_CONSECUTIVE_BARS_V1,
    thr: float = ELEVATED_RATIO_PERCENTILE_INCLUSIVE_MIN_V1,
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


def _short_horizon_signed_return_v1(close: np.ndarray, *, index: int) -> Optional[float]:
    lookback = SHORT_HORIZON_RETURN_LOOKBACK_COMPLETED_BARS_V1
    if index < lookback:
        return None
    c_now = float(close[index])
    c_prev = float(close[index - lookback])
    if not np.isfinite(c_now) or not np.isfinite(c_prev) or c_now <= 0.0 or c_prev <= 0.0:
        return None
    return (c_now / c_prev) - 1.0


def _fade_side_from_signed_return(
    signed_return: float,
) -> Optional[StrategyEntrySideCarrierV1]:
    if not np.isfinite(signed_return) or signed_return == 0.0:
        return None
    if signed_return > 0.0:
        return StrategyEntrySideCarrierV1.SHORT
    return StrategyEntrySideCarrierV1.LONG


def _none_result(
    reason: VtsrReasonV1,
    *,
    ratio_percentile_120: Optional[float] = None,
    rv_term_structure_ratio: Optional[float] = None,
    realized_volatility_short_8: Optional[float] = None,
    realized_volatility_long_48: Optional[float] = None,
    elevated_confirmation_index: Optional[int] = None,
    short_horizon_signed_return: Optional[float] = None,
) -> VtsrBarResultV1:
    return VtsrBarResultV1(
        event=VtsrEventV1.NONE,
        entry_side=StrategyEntrySideCarrierV1.NONE,
        event_kind=StrategyAgreementEventKindV1.NONE,
        reason=reason,
        ratio_percentile_120=ratio_percentile_120,
        rv_term_structure_ratio=rv_term_structure_ratio,
        realized_volatility_short_8=realized_volatility_short_8,
        realized_volatility_long_48=realized_volatility_long_48,
        elevated_confirmation_index=elevated_confirmation_index,
        short_horizon_signed_return=short_horizon_signed_return,
    )


def generate_vtsr_events_and_roundtrips_v1(
    data: pd.DataFrame,
    *,
    high_col: str = "high",
    low_col: str = "low",
    close_col: str = "close",
    open_col: str = "open",
    is_panel_last_bar_mask: Optional[np.ndarray] = None,
) -> tuple[list[VtsrBarResultV1], list[VtsrRoundtripV1]]:
    """Generate entry/exit events with guaranteed exit reachability for admitted fades.

    Elevated confirmation on completed bar t_conf (>=2 bars ratio percentile >= 0.80).
    Direction is opposite the short-horizon signed return over 8 completed bars.
    Fill at open of signal+1. Depressed-ratio entries forbidden. No trailing exits.
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

    short_rv = compute_realized_volatility_short_8_v1(close)
    long_rv = compute_realized_volatility_long_48_v1(close)
    ratio = compute_rv_term_structure_ratio_short_over_long_v1(close)
    rank = compute_percentile_rank_120_rv_term_structure_ratio_v1(ratio)
    atr = compute_atr14_v1(high, low, close)

    ranks_np = rank.to_numpy(dtype=np.float64, copy=False)
    ratio_np = ratio.to_numpy(dtype=np.float64, copy=False)
    short_np = short_rv.to_numpy(dtype=np.float64, copy=False)
    long_np = long_rv.to_numpy(dtype=np.float64, copy=False)
    close_np = close.to_numpy(dtype=np.float64, copy=False)

    if is_panel_last_bar_mask is None:
        panel_last = np.zeros(n, dtype=bool)
        panel_last[-1] = True
    else:
        panel_last = np.asarray(is_panel_last_bar_mask, dtype=bool)
        if len(panel_last) != n:
            raise ValueError("PANEL_LAST_MASK_LENGTH_MISMATCH")

    results: list[VtsrBarResultV1] = [_none_result(VtsrReasonV1.NO_EVENT) for _ in range(n)]
    roundtrips: list[VtsrRoundtripV1] = []

    pending_signal: Optional[tuple[int, StrategyEntrySideCarrierV1, int, float]] = (
        None  # signal_i, fade_side, elevated_conf_i, signed_ret
    )
    position = None
    pending_roundtrip_meta: Optional[tuple[int, int, float, int, float]] = (
        None  # sig, fill, entry_px, elevated_conf, signed_ret
    )
    cooldown_until = -1
    awaiting_rearm = False
    episode: Optional[_ElevatedEpisodeState] = None

    for i in range(n):
        rank_i = float(ranks_np[i]) if np.isfinite(ranks_np[i]) else None
        ratio_i = float(ratio_np[i]) if np.isfinite(ratio_np[i]) else None
        short_i = float(short_np[i]) if np.isfinite(short_np[i]) else None
        long_i = float(long_np[i]) if np.isfinite(long_np[i]) else None
        h_i = float(high.iloc[i]) if np.isfinite(high.iloc[i]) else float("nan")
        l_i = float(low.iloc[i]) if np.isfinite(low.iloc[i]) else float("nan")
        c_i = float(close.iloc[i]) if np.isfinite(close.iloc[i]) else float("nan")

        if i < cooldown_until:
            results[i] = _none_result(
                VtsrReasonV1.COOLDOWN,
                ratio_percentile_120=rank_i,
                rv_term_structure_ratio=ratio_i,
                realized_volatility_short_8=short_i,
                realized_volatility_long_48=long_i,
            )
            continue

        if pending_signal is not None:
            sig_i, side, elev_i, signed_ret = pending_signal
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
                pending_roundtrip_meta = (sig_i, fill_i, entry_px, elev_i, signed_ret)
                pending_signal = None
                results[i] = VtsrBarResultV1(
                    event=VtsrEventV1.NONE,
                    entry_side=StrategyEntrySideCarrierV1.NONE,
                    event_kind=StrategyAgreementEventKindV1.NONE,
                    reason=VtsrReasonV1.POSITION_OPEN,
                    fill_index=fill_i,
                    signal_index=sig_i,
                    elevated_confirmation_index=elev_i,
                    ratio_percentile_120=rank_i,
                    rv_term_structure_ratio=ratio_i,
                    realized_volatility_short_8=short_i,
                    realized_volatility_long_48=long_i,
                    short_horizon_signed_return=signed_ret,
                )
                continue
            if i < fill_i:
                results[i] = VtsrBarResultV1(
                    event=VtsrEventV1.NONE,
                    entry_side=StrategyEntrySideCarrierV1.NONE,
                    event_kind=StrategyAgreementEventKindV1.NONE,
                    reason=VtsrReasonV1.AWAITING_FILL,
                    signal_index=sig_i,
                    elevated_confirmation_index=elev_i,
                    ratio_percentile_120=rank_i,
                    rv_term_structure_ratio=ratio_i,
                    realized_volatility_short_8=short_i,
                    realized_volatility_long_48=long_i,
                    short_horizon_signed_return=signed_ret,
                )
                continue

        if position is not None and pending_roundtrip_meta is not None:
            if i <= position.fill_index:
                results[i] = VtsrBarResultV1(
                    event=VtsrEventV1.NONE,
                    entry_side=StrategyEntrySideCarrierV1.NONE,
                    event_kind=StrategyAgreementEventKindV1.NONE,
                    reason=VtsrReasonV1.POSITION_OPEN,
                    fill_index=position.fill_index,
                    signal_index=pending_roundtrip_meta[0],
                    elevated_confirmation_index=pending_roundtrip_meta[3],
                    ratio_percentile_120=rank_i,
                    rv_term_structure_ratio=ratio_i,
                    realized_volatility_short_8=short_i,
                    realized_volatility_long_48=long_i,
                    short_horizon_signed_return=pending_roundtrip_meta[4],
                )
                continue
            decision, position = evaluate_exit_on_bar_v1(
                position,
                bar_index=i,
                high=h_i,
                low=l_i,
                close=c_i,
                ratio_percentile=rank_i,
                is_last_instrument_bar=(i == n - 1),
                is_last_panel_bar=bool(panel_last[i]),
            )
            if decision is not None:
                sig_i, fill_i, entry_px, elev_i, signed_ret = pending_roundtrip_meta
                roundtrips.append(
                    VtsrRoundtripV1(
                        side=decision.side,
                        signal_index=sig_i,
                        fill_index=fill_i,
                        exit_index=decision.exit_index,
                        entry_price=entry_px,
                        exit_price=decision.exit_price,
                        exit_reason=decision.reason,
                        elevated_confirmation_index=elev_i,
                        short_horizon_signed_return=signed_ret,
                    )
                )
                results[i] = VtsrBarResultV1(
                    event=VtsrEventV1.EXIT_EVENT,
                    entry_side=StrategyEntrySideCarrierV1.NONE,
                    event_kind=StrategyAgreementEventKindV1.NONE,
                    reason=VtsrReasonV1.EXIT_EMITTED,
                    exit_reason=decision.reason,
                    exit_price=decision.exit_price,
                    fill_index=fill_i,
                    signal_index=sig_i,
                    elevated_confirmation_index=elev_i,
                    ratio_percentile_120=rank_i,
                    rv_term_structure_ratio=ratio_i,
                    realized_volatility_short_8=short_i,
                    realized_volatility_long_48=long_i,
                    short_horizon_signed_return=signed_ret,
                )
                position = None
                pending_roundtrip_meta = None
                episode = None
                awaiting_rearm = True
                cooldown_until = i + 1 + COOLDOWN_BARS_AFTER_EXIT_V1
                continue
            results[i] = VtsrBarResultV1(
                event=VtsrEventV1.NONE,
                entry_side=StrategyEntrySideCarrierV1.NONE,
                event_kind=StrategyAgreementEventKindV1.NONE,
                reason=VtsrReasonV1.POSITION_OPEN,
                fill_index=position.fill_index,
                signal_index=pending_roundtrip_meta[0],
                elevated_confirmation_index=pending_roundtrip_meta[3],
                ratio_percentile_120=rank_i,
                rv_term_structure_ratio=ratio_i,
                realized_volatility_short_8=short_i,
                realized_volatility_long_48=long_i,
                short_horizon_signed_return=pending_roundtrip_meta[4],
            )
            continue

        # Flat admission path.
        if rank_i is None or ratio_i is None or not np.isfinite(c_i):
            results[i] = _none_result(
                VtsrReasonV1.WARMUP,
                ratio_percentile_120=rank_i,
                rv_term_structure_ratio=ratio_i,
                realized_volatility_short_8=short_i,
                realized_volatility_long_48=long_i,
            )
            continue

        if awaiting_rearm:
            if rank_i < REARM_RATIO_PERCENTILE_STRICTLY_BELOW_V1:
                awaiting_rearm = False
                # fall through to possibly start a new elevated episode on same bar
            else:
                results[i] = _none_result(
                    VtsrReasonV1.AWAITING_REARM,
                    ratio_percentile_120=rank_i,
                    rv_term_structure_ratio=ratio_i,
                    realized_volatility_short_8=short_i,
                    realized_volatility_long_48=long_i,
                )
                continue

        if episode is not None and episode.entry_consumed:
            if not _elevated_through(ranks_np, end_inclusive=i):
                episode = None
                awaiting_rearm = True
                results[i] = _none_result(
                    VtsrReasonV1.AWAITING_REARM,
                    ratio_percentile_120=rank_i,
                    rv_term_structure_ratio=ratio_i,
                    realized_volatility_short_8=short_i,
                    realized_volatility_long_48=long_i,
                )
            else:
                results[i] = _none_result(
                    VtsrReasonV1.EPISODE_CONSUMED,
                    ratio_percentile_120=rank_i,
                    rv_term_structure_ratio=ratio_i,
                    realized_volatility_short_8=short_i,
                    realized_volatility_long_48=long_i,
                    elevated_confirmation_index=episode.confirmation_index,
                )
            continue

        if episode is None:
            if not _elevated_through(ranks_np, end_inclusive=i):
                results[i] = _none_result(
                    VtsrReasonV1.NO_EVENT,
                    ratio_percentile_120=rank_i,
                    rv_term_structure_ratio=ratio_i,
                    realized_volatility_short_8=short_i,
                    realized_volatility_long_48=long_i,
                )
                continue
            episode = _ElevatedEpisodeState(confirmation_index=i)

        # Attempt single entry on elevated confirmation bar only.
        if i != episode.confirmation_index:
            results[i] = _none_result(
                VtsrReasonV1.ELEVATED_MONITORING
                if _elevated_through(ranks_np, end_inclusive=i)
                else VtsrReasonV1.NO_EVENT,
                ratio_percentile_120=rank_i,
                rv_term_structure_ratio=ratio_i,
                realized_volatility_short_8=short_i,
                realized_volatility_long_48=long_i,
                elevated_confirmation_index=episode.confirmation_index,
            )
            if not _elevated_through(ranks_np, end_inclusive=i):
                episode = None
                awaiting_rearm = True
            continue

        signed_ret = _short_horizon_signed_return_v1(close_np, index=i)
        if signed_ret is None:
            episode.entry_consumed = True
            results[i] = _none_result(
                VtsrReasonV1.INVALID_INPUT_FAIL_CLOSED,
                ratio_percentile_120=rank_i,
                rv_term_structure_ratio=ratio_i,
                realized_volatility_short_8=short_i,
                realized_volatility_long_48=long_i,
                elevated_confirmation_index=episode.confirmation_index,
            )
            continue

        fade_side = _fade_side_from_signed_return(signed_ret)
        if fade_side is None:
            episode.entry_consumed = True
            results[i] = _none_result(
                VtsrReasonV1.AMBIGUOUS_DIRECTION_FAIL_CLOSED,
                ratio_percentile_120=rank_i,
                rv_term_structure_ratio=ratio_i,
                realized_volatility_short_8=short_i,
                realized_volatility_long_48=long_i,
                elevated_confirmation_index=episode.confirmation_index,
                short_horizon_signed_return=signed_ret,
            )
            continue

        if not entry_exit_reachable_ex_ante_v1(signal_index=i, series_length=n):
            episode.entry_consumed = True
            results[i] = _none_result(
                VtsrReasonV1.ENTRY_SUPPRESSED_EXIT_UNREACHABLE,
                ratio_percentile_120=rank_i,
                rv_term_structure_ratio=ratio_i,
                realized_volatility_short_8=short_i,
                realized_volatility_long_48=long_i,
                elevated_confirmation_index=episode.confirmation_index,
                short_horizon_signed_return=signed_ret,
            )
            continue

        episode.entry_consumed = True
        pending_signal = (i, fade_side, episode.confirmation_index, float(signed_ret))
        results[i] = VtsrBarResultV1(
            event=VtsrEventV1.ENTRY_EVENT,
            entry_side=fade_side,
            event_kind=StrategyAgreementEventKindV1.ENTRY,
            reason=VtsrReasonV1.SUCCESSFUL_ENTRY,
            signal_index=i,
            elevated_confirmation_index=episode.confirmation_index,
            ratio_percentile_120=rank_i,
            rv_term_structure_ratio=ratio_i,
            realized_volatility_short_8=short_i,
            realized_volatility_long_48=long_i,
            short_horizon_signed_return=float(signed_ret),
        )

    return results, roundtrips


__all__ = [
    "BASELINE_ID_V1",
    "DEPRESSED_ENTRY_FORBIDDEN_IN_V1",
    "ELEVATED_MIN_CONSECUTIVE_BARS_V1",
    "ELEVATED_RATIO_PERCENTILE_INCLUSIVE_MIN_V1",
    "EVENT_CONSUMPTION_V1",
    "EXIT_PARAMS_V1",
    "EXIT_STATE_MACHINE_IMPLEMENTED_V1",
    "HYPOTHESIS_ID_V1",
    "MAX_ENTRIES_PER_ELEVATED_EPISODE_V1",
    "NO_CHANNEL_BREAKOUT_REQUIRED_V1",
    "NO_COMPRESSION_BREAKOUT_REQUIRED_V1",
    "NO_EXPANSION_STATE_REQUIRED_V1",
    "PREDECESSOR_STRATEGY_ID_V1",
    "PRODUCTIVE_EXIT_PNL_EVALUATOR_REF_V1",
    "PROGRAM_ID_V1",
    "REARM_RATIO_PERCENTILE_STRICTLY_BELOW_V1",
    "RV_LONG_HORIZON_COMPLETED_BARS_V1",
    "RV_SHORT_HORIZON_COMPLETED_BARS_V1",
    "SHORT_HORIZON_RETURN_LOOKBACK_COMPLETED_BARS_V1",
    "SIGNAL_FAMILY_V1",
    "STRATEGY_ID_V1",
    "STRATEGY_IDENTITY_V1",
    "STRATEGY_VERSION_V1",
    "VCB_COMPRESSION_BREAKOUT_ENTRY_FORBIDDEN_V1",
    "VEFCF_FAILED_CONTINUATION_FADE_ENTRY_FORBIDDEN_V1",
    "VEPC_PULLBACK_CONTINUATION_ENTRY_FORBIDDEN_V1",
    "VtsrBarResultV1",
    "VtsrEventV1",
    "VtsrReasonV1",
    "VtsrRoundtripV1",
    "generate_vtsr_events_and_roundtrips_v1",
]
