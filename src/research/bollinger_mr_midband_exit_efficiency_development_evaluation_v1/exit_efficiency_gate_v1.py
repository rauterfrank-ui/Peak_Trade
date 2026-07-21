"""Research-only middle-band exit-efficiency gate (no Master-V2 / engine mutation).

Wraps MV2 mapped-position-signal mapping after entry fill. Entries pass unchanged.
Stop-loss remains engine-first. Tracks open side via position-feedback observation.
"""

from __future__ import annotations

from contextlib import contextmanager
from typing import Any, Iterator

import pandas as pd

from src.research.bollinger_mr_midband_exit_efficiency_development_evaluation_v1.midband_exit_mechanism_v1 import (
    MidbandExitMechanismError,
    force_exit_signal_for_open_side,
    long_exit_mask_from_bars,
    midband_exit_triggered,
    short_exit_mask_from_bars,
)
from src.trading.master_v2.double_play_entry_exit_policy_v0 import ExistingPositionSide


@contextmanager
def optional_treatment_exit_efficiency_gate(
    *, enabled: bool, bars: pd.DataFrame | None
) -> Iterator[dict[str, int]]:
    """Monkeypatch MV2 map + position feedback observation for midband exits."""
    counters = {
        "exits_forced_by_gate": 0,
        "exit_bars_observed": 0,
        "entries_altered_by_gate": 0,
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
    state: dict[str, Any] = {"current_ts": None, "open_side": None}

    original_bind_bar = wiring_mod.bind_bar_for_mv2_wiring_v1
    original_bind_warmup = wiring_mod._bind_economic_research_warmup_observation_bar_v1
    original_map = wiring_mod.map_decision_evidence_to_position_signal_v1
    original_capture = feedback_mod.capture_backtest_engine_position_feedback_v1

    def _bind_bar_tracked(**kwargs):  # type: ignore[no-untyped-def]
        state["current_ts"] = pd.Timestamp(kwargs["bar"].name)
        return original_bind_bar(**kwargs)

    def _bind_warmup_tracked(**kwargs):  # type: ignore[no-untyped-def]
        state["current_ts"] = pd.Timestamp(kwargs["bar"].name)
        return original_bind_warmup(**kwargs)

    def _capture_tracked(**kwargs):  # type: ignore[no-untyped-def]
        feedback = original_capture(**kwargs)
        if feedback.has_open_trade:
            if feedback.existing_position_side == ExistingPositionSide.LONG:
                state["open_side"] = "long"
            elif feedback.existing_position_side == ExistingPositionSide.SHORT:
                state["open_side"] = "short"
            else:
                raise MidbandExitMechanismError("OPEN_SIDE_UNBOUND")
        else:
            state["open_side"] = None
        return feedback

    def _map_gated(evidence):  # type: ignore[no-untyped-def]
        raw_signal = int(original_map(evidence))
        open_side = state["open_side"]
        ts = state["current_ts"]

        # Flat: never invent entries from midband cross; pass entries/exits through.
        if open_side is None:
            return raw_signal

        triggered = midband_exit_triggered(
            open_side=open_side,
            ts=ts,
            long_mask=long_mask,
            short_mask=short_mask,
        )
        if not triggered:
            return raw_signal

        forced = force_exit_signal_for_open_side(open_side)
        if forced is None:
            raise MidbandExitMechanismError("FORCE_EXIT_SIGNAL_MISSING")
        counters["exit_bars_observed"] += 1
        if int(forced) != raw_signal:
            counters["exits_forced_by_gate"] += 1
            # Guard: forcing an exit must not look like a flat-entry rewrite.
            if raw_signal in (-1, 1) and open_side is None:
                counters["entries_altered_by_gate"] += 1
        return int(forced)

    wiring_mod.bind_bar_for_mv2_wiring_v1 = _bind_bar_tracked  # type: ignore[assignment]
    wiring_mod._bind_economic_research_warmup_observation_bar_v1 = _bind_warmup_tracked  # type: ignore[assignment]
    wiring_mod.map_decision_evidence_to_position_signal_v1 = _map_gated  # type: ignore[assignment]
    feedback_mod.capture_backtest_engine_position_feedback_v1 = _capture_tracked  # type: ignore[assignment]
    try:
        yield counters
    finally:
        wiring_mod.bind_bar_for_mv2_wiring_v1 = original_bind_bar  # type: ignore[assignment]
        wiring_mod._bind_economic_research_warmup_observation_bar_v1 = original_bind_warmup  # type: ignore[assignment]
        wiring_mod.map_decision_evidence_to_position_signal_v1 = original_map  # type: ignore[assignment]
        feedback_mod.capture_backtest_engine_position_feedback_v1 = original_capture  # type: ignore[assignment]


__all__ = ["optional_treatment_exit_efficiency_gate"]
