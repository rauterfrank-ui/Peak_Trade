"""Research-only V7 arm gate: identical V6 composite exits + optional reentry cooldown.

Control: composite exit gate ON, cooldown OFF.
Treatment: composite exit gate ON, cooldown ON (blocks same-scope entries).
Does not alter exit fills between arms when both use exit gate enabled=True.
"""

from __future__ import annotations

from contextlib import contextmanager
from typing import Any, Iterator

import numpy as np
import pandas as pd

from src.research.bollinger_mr_midband_exit_efficiency_development_evaluation_v1.midband_exit_mechanism_v1 import (
    MidbandExitMechanismError,
)
from src.research.bollinger_mr_midband_exit_efficiency_development_evaluation_v6.composite_exit_efficiency_gate_v6 import (
    optional_treatment_exit_efficiency_gate,
)
from src.research.bollinger_mr_midband_exit_reentry_cooldown_development_evaluation_v7.constants_v7 import (
    COOLDOWN_ARMS_ON_TRIGGERS,
)
from src.research.bollinger_mr_midband_exit_reentry_cooldown_development_evaluation_v7.cooldown_state_v7 import (
    CooldownStateError,
    ReentryCooldownStateV7,
    create_cooldown_state,
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
def optional_v7_control_or_treatment_gate(
    *,
    cooldown_enabled: bool,
    bars: pd.DataFrame | None,
    instrument_id: str,
) -> Iterator[dict[str, Any]]:
    """Apply identical V6 composite exits; optionally block reentries via cooldown."""
    if bars is None:
        raise MidbandExitMechanismError("V7_GATE_BARS_REQUIRED")

    cooldown: ReentryCooldownStateV7 = create_cooldown_state(
        enabled=bool(cooldown_enabled), instrument_id=instrument_id
    )
    combined: dict[str, Any] = {
        "cooldown_enabled": bool(cooldown_enabled),
        "instrument_id": instrument_id,
        "entries_blocked_by_cooldown": 0,
        "cooldown_state": cooldown,
    }

    with optional_treatment_exit_efficiency_gate(enabled=True, bars=bars) as exit_counters:
        combined["exit_counters"] = exit_counters
        if not cooldown_enabled:
            yield combined
            combined.update(cooldown.attribution())
            return

        import src.backtest.backtest_engine_position_feedback_adapter_v1 as feedback_mod
        import src.backtest.mv2_research_wiring_v1 as wiring_mod

        state: dict[str, Any] = {
            "current_ts": None,
            "open_side": None,
            "last_forced_trigger": None,
        }

        original_bind_bar = wiring_mod.bind_bar_for_mv2_wiring_v1
        original_bind_warmup = wiring_mod._bind_economic_research_warmup_observation_bar_v1
        original_map = wiring_mod.map_decision_evidence_to_position_signal_v1
        original_capture_wiring = wiring_mod.capture_backtest_engine_position_feedback_v1
        original_capture_feedback = feedback_mod.capture_backtest_engine_position_feedback_v1

        def _bind_bar_tracked(**kwargs):  # type: ignore[no-untyped-def]
            state["current_ts"] = pd.Timestamp(kwargs["bar"].name)
            ts = state["current_ts"]
            bar_index = _bar_index_for_ts(bars, ts)
            try:
                cooldown.observe_bar(instrument_id=instrument_id, bar_index=bar_index, bar_ts=ts)
            except CooldownStateError:
                raise
            return original_bind_bar(**kwargs)

        def _bind_warmup_tracked(**kwargs):  # type: ignore[no-untyped-def]
            state["current_ts"] = pd.Timestamp(kwargs["bar"].name)
            return original_bind_warmup(**kwargs)

        def _capture_tracked(**kwargs):  # type: ignore[no-untyped-def]
            feedback = original_capture_feedback(**kwargs)
            prior_side = state["open_side"]
            if feedback.has_open_trade:
                if feedback.existing_position_side == ExistingPositionSide.LONG:
                    state["open_side"] = "long"
                elif feedback.existing_position_side == ExistingPositionSide.SHORT:
                    state["open_side"] = "short"
                else:
                    raise MidbandExitMechanismError("OPEN_SIDE_UNBOUND")
            else:
                if prior_side is not None:
                    # Exit fill observed: arm cooldown if last composite trigger was midband*.
                    triggers = exit_counters.get("composite_exit_trigger_first_of") or []
                    trigger_kind = str(triggers[-1]) if triggers else ""
                    ts = state["current_ts"]
                    if ts is not None and trigger_kind in COOLDOWN_ARMS_ON_TRIGGERS:
                        exit_bar = _bar_index_for_ts(bars, ts)
                        cooldown.on_midband_exit_fill(
                            instrument_id=instrument_id,
                            direction=str(prior_side),
                            exit_bar_index=exit_bar,
                            trigger_kind=trigger_kind,
                        )
                        state["last_forced_trigger"] = trigger_kind
                state["open_side"] = None
            return feedback

        def _map_gated(evidence):  # type: ignore[no-untyped-def]
            raw_signal = int(original_map(evidence))
            open_side = state["open_side"]
            ts = state["current_ts"]
            if open_side is not None or ts is None:
                return raw_signal
            if raw_signal not in (-1, 1):
                return raw_signal
            direction = "long" if raw_signal == 1 else "short"
            bar_index = _bar_index_for_ts(bars, ts)
            allowed = cooldown.check_entry_allowed(
                instrument_id=instrument_id,
                direction=direction,
                bar_index=bar_index,
                record=True,
            )
            if not allowed:
                combined["entries_blocked_by_cooldown"] = (
                    int(combined["entries_blocked_by_cooldown"]) + 1
                )
                return 0
            return raw_signal

        wiring_mod.bind_bar_for_mv2_wiring_v1 = _bind_bar_tracked  # type: ignore[assignment]
        wiring_mod._bind_economic_research_warmup_observation_bar_v1 = _bind_warmup_tracked  # type: ignore[assignment]
        wiring_mod.map_decision_evidence_to_position_signal_v1 = _map_gated  # type: ignore[assignment]
        wiring_mod.capture_backtest_engine_position_feedback_v1 = _capture_tracked  # type: ignore[assignment]
        feedback_mod.capture_backtest_engine_position_feedback_v1 = _capture_tracked  # type: ignore[assignment]
        try:
            yield combined
        finally:
            wiring_mod.bind_bar_for_mv2_wiring_v1 = original_bind_bar  # type: ignore[assignment]
            wiring_mod._bind_economic_research_warmup_observation_bar_v1 = (  # type: ignore[assignment]
                original_bind_warmup
            )
            wiring_mod.map_decision_evidence_to_position_signal_v1 = original_map  # type: ignore[assignment]
            wiring_mod.capture_backtest_engine_position_feedback_v1 = (  # type: ignore[assignment]
                original_capture_wiring
            )
            feedback_mod.capture_backtest_engine_position_feedback_v1 = (  # type: ignore[assignment]
                original_capture_feedback
            )
            combined.update(cooldown.attribution())


__all__ = ["optional_v7_control_or_treatment_gate"]
