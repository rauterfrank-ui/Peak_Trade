"""Research-only composite midband OR max-holding exit-efficiency gate (v6).

Wraps MV2 mapped-position-signal mapping after entry fill. Entries pass unchanged.
Stop-loss remains engine-first. Tracks open side and entry_fill_index via
position-feedback observation.
"""

from __future__ import annotations

from contextlib import contextmanager
from typing import Any, Iterator

import numpy as np
import pandas as pd

from src.research.bollinger_mr_midband_exit_efficiency_development_evaluation_v1.midband_exit_mechanism_v1 import (
    MidbandExitMechanismError,
    force_exit_signal_for_open_side,
    long_exit_mask_from_bars,
    short_exit_mask_from_bars,
)
from src.research.bollinger_mr_midband_exit_efficiency_development_evaluation_v6.composite_midband_max_holding_exit_mechanism_v6 import (
    composite_exit_triggered,
)
from src.research.bollinger_mr_midband_exit_efficiency_development_evaluation_v6.constants_v6 import (
    MAX_HOLDING_BARS,
)
from src.trading.master_v2.double_play_entry_exit_policy_v0 import ExistingPositionSide


def _bar_index_for_ts(bars: pd.DataFrame, ts: pd.Timestamp) -> int:
    loc = bars.index.get_loc(ts)
    if isinstance(loc, slice):
        raise MidbandExitMechanismError("BAR_INDEX_AMBIGUOUS_SLICE")
    if isinstance(loc, np.ndarray):
        raise MidbandExitMechanismError("BAR_INDEX_AMBIGUOUS_ARRAY")
    return int(loc)


@contextmanager
def optional_treatment_exit_efficiency_gate(
    *, enabled: bool, bars: pd.DataFrame | None
) -> Iterator[dict[str, int | list[str]]]:
    """Monkeypatch MV2 map + position feedback observation for composite exits."""
    counters: dict[str, int | list[str]] = {
        "exits_forced_by_gate": 0,
        "exit_bars_observed": 0,
        "entries_altered_by_gate": 0,
        "midband_exit_count": 0,
        "max_holding_exit_count": 0,
        "composite_exit_trigger_first_of": [],
    }
    if not enabled:
        yield counters
        return
    if bars is None:
        raise MidbandExitMechanismError("EXIT_GATE_BARS_REQUIRED")

    import src.backtest.backtest_engine_position_feedback_adapter_v1 as feedback_mod
    import src.backtest.mv2_research_wiring_v1 as wiring_mod

    long_mask = long_exit_mask_from_bars(bars)
    short_mask = short_exit_mask_from_bars(bars)
    state: dict[str, Any] = {
        "current_ts": None,
        "open_side": None,
        "entry_fill_index": None,
    }

    original_bind_bar = wiring_mod.bind_bar_for_mv2_wiring_v1
    original_bind_warmup = wiring_mod._bind_economic_research_warmup_observation_bar_v1
    original_map = wiring_mod.map_decision_evidence_to_position_signal_v1
    original_capture_wiring = wiring_mod.capture_backtest_engine_position_feedback_v1
    original_capture_feedback = feedback_mod.capture_backtest_engine_position_feedback_v1

    def _bind_bar_tracked(**kwargs):  # type: ignore[no-untyped-def]
        state["current_ts"] = pd.Timestamp(kwargs["bar"].name)
        return original_bind_bar(**kwargs)

    def _bind_warmup_tracked(**kwargs):  # type: ignore[no-untyped-def]
        state["current_ts"] = pd.Timestamp(kwargs["bar"].name)
        return original_bind_warmup(**kwargs)

    def _ensure_entry_fill_index_bound() -> None:
        if state["open_side"] is not None and state["entry_fill_index"] is None:
            ts = state["current_ts"]
            if ts is None:
                raise MidbandExitMechanismError("ENTRY_FILL_TS_MISSING")
            state["entry_fill_index"] = _bar_index_for_ts(bars, ts)

    def _capture_tracked(**kwargs):  # type: ignore[no-untyped-def]
        feedback = original_capture_feedback(**kwargs)
        prior_side = state["open_side"]
        if feedback.has_open_trade:
            if feedback.existing_position_side == ExistingPositionSide.LONG:
                new_side = "long"
            elif feedback.existing_position_side == ExistingPositionSide.SHORT:
                new_side = "short"
            else:
                raise MidbandExitMechanismError("OPEN_SIDE_UNBOUND")
            if prior_side is None:
                ts = state["current_ts"]
                if ts is not None:
                    state["entry_fill_index"] = _bar_index_for_ts(bars, ts)
                else:
                    epoch = kwargs.get("feedback_source_bar_epoch")
                    if epoch is not None:
                        state["entry_fill_index"] = int(epoch)
            state["open_side"] = new_side
        else:
            state["open_side"] = None
            state["entry_fill_index"] = None
        return feedback

    def _map_gated(evidence):  # type: ignore[no-untyped-def]
        raw_signal = int(original_map(evidence))
        open_side = state["open_side"]
        ts = state["current_ts"]

        if open_side is None:
            return raw_signal

        _ensure_entry_fill_index_bound()

        if ts is None:
            raise MidbandExitMechanismError("MISSING_STATE_OR_INDEX_BINDING")
        bar_index = _bar_index_for_ts(bars, ts)

        triggered, trigger_kind = composite_exit_triggered(
            open_side=open_side,
            ts=ts,
            long_mask=long_mask,
            short_mask=short_mask,
            entry_fill_index=state["entry_fill_index"],
            bar_index=bar_index,
            max_holding_bars=MAX_HOLDING_BARS,
        )
        if not triggered:
            return raw_signal

        forced = force_exit_signal_for_open_side(open_side)
        if forced is None:
            raise MidbandExitMechanismError("FORCE_EXIT_SIGNAL_MISSING")

        if trigger_kind == "midband":
            counters["midband_exit_count"] = int(counters["midband_exit_count"]) + 1
        elif trigger_kind == "max_holding":
            counters["max_holding_exit_count"] = int(counters["max_holding_exit_count"]) + 1
        elif trigger_kind == "midband_and_max_holding":
            counters["midband_exit_count"] = int(counters["midband_exit_count"]) + 1
            counters["max_holding_exit_count"] = int(counters["max_holding_exit_count"]) + 1
        trigger_list = counters["composite_exit_trigger_first_of"]
        assert isinstance(trigger_list, list)
        trigger_list.append(str(trigger_kind))

        counters["exit_bars_observed"] = int(counters["exit_bars_observed"]) + 1
        if int(forced) != raw_signal:
            counters["exits_forced_by_gate"] = int(counters["exits_forced_by_gate"]) + 1
            if raw_signal in (-1, 1) and open_side is None:
                counters["entries_altered_by_gate"] = int(counters["entries_altered_by_gate"]) + 1
        return int(forced)

    wiring_mod.bind_bar_for_mv2_wiring_v1 = _bind_bar_tracked  # type: ignore[assignment]
    wiring_mod._bind_economic_research_warmup_observation_bar_v1 = _bind_warmup_tracked  # type: ignore[assignment]
    wiring_mod.map_decision_evidence_to_position_signal_v1 = _map_gated  # type: ignore[assignment]
    wiring_mod.capture_backtest_engine_position_feedback_v1 = _capture_tracked  # type: ignore[assignment]
    feedback_mod.capture_backtest_engine_position_feedback_v1 = _capture_tracked  # type: ignore[assignment]
    try:
        yield counters
    finally:
        wiring_mod.bind_bar_for_mv2_wiring_v1 = original_bind_bar  # type: ignore[assignment]
        wiring_mod._bind_economic_research_warmup_observation_bar_v1 = original_bind_warmup  # type: ignore[assignment]
        wiring_mod.map_decision_evidence_to_position_signal_v1 = original_map  # type: ignore[assignment]
        wiring_mod.capture_backtest_engine_position_feedback_v1 = original_capture_wiring  # type: ignore[assignment]
        feedback_mod.capture_backtest_engine_position_feedback_v1 = (  # type: ignore[assignment]
            original_capture_feedback
        )


__all__ = ["optional_treatment_exit_efficiency_gate"]
