"""Reentry-cooldown state machine for V7 (no MV2 / panel imports).

Bound to Operator Clarification Authority B4/B5/B6/B8:
- arm on confirmed qualifying forced-midband fill at bar t
- same-bar reentry on t forbidden
- blocked t+1..t+24 inclusive (and t); first eligible t+25
- count canonical sequential PT1H bar indices
- gap/duplicate/non-monotonic/non-PT1H fail-closed
- separate instances required for control vs treatment (B8)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import pandas as pd

from src.research.bollinger_mr_midband_exit_reentry_cooldown_development_evaluation_v8.constants_v8 import (
    COOLDOWN_ARMS_ON_TRIGGERS,
    COOLDOWN_BARS,
)

PT1H = pd.Timedelta(hours=1)


class CooldownStateError(ValueError):
    """Fail-closed bar-sequence or scope integrity error."""


@dataclass
class _ScopeArm:
    instrument_id: str
    direction: str
    exit_fill_bar_index: int | None = None
    armed_at_bar_index: int | None = None
    blocked_through_bar_index: int | None = None
    first_eligible_bar_index: int | None = None
    active: bool = False
    generation: int = 0
    rearm_count: int = 0


@dataclass
class _InstrumentClock:
    last_bar_index: int | None = None
    last_bar_ts: pd.Timestamp | None = None


@dataclass
class ReentryCooldownStateV7:
    """Per-arm cooldown state. Create separate instances for control vs treatment."""

    enabled: bool
    cooldown_bars: int = COOLDOWN_BARS
    instrument_id_expected: str | None = None
    _scopes: dict[tuple[str, str], _ScopeArm] = field(default_factory=dict)
    _clocks: dict[str, _InstrumentClock] = field(default_factory=dict)
    blocked_reentry_count: int = 0
    blocked_same_side_reentry_count: int = 0
    blocked_short_reentry_count: int = 0
    blocked_long_reentry_count: int = 0
    admitted_same_side_reentry_after_cooldown_count: int = 0
    cooldown_activation_count: int = 0
    same_bar_reentry_block_count: int = 0
    same_bar_reentry_attempts: int = 0
    cooldown_resets: int = 0
    generation_counter: int = 0
    scope_isolation_violations: int = 0
    invalid_sequence_diagnostic: str | None = None
    first_eligible_reentry_bar: int | None = None
    actual_reentry_bar: int | None = None
    reentry_delay_bars: int | None = None
    _pending_first_eligible: dict[tuple[str, str], int] = field(default_factory=dict)

    def _key(self, instrument_id: str, direction: str) -> tuple[str, str]:
        if direction not in ("long", "short"):
            raise CooldownStateError(f"INVALID_DIRECTION:{direction}")
        if self.instrument_id_expected is not None and instrument_id != self.instrument_id_expected:
            self.scope_isolation_violations += 1
            raise CooldownStateError(
                f"SCOPE_ISOLATION_VIOLATION:expected={self.instrument_id_expected}"
                f":got={instrument_id}"
            )
        return (instrument_id, direction)

    def observe_bar(
        self,
        *,
        instrument_id: str,
        bar_index: int,
        bar_ts: pd.Timestamp,
    ) -> None:
        """Advance per-instrument PT1H clock; fail closed on gap/dup/order errors."""
        ts = pd.Timestamp(bar_ts)
        if ts.tzinfo is None:
            self.invalid_sequence_diagnostic = "BAR_TS_TZ_NAIVE_FORBIDDEN"
            raise CooldownStateError("BAR_TS_TZ_NAIVE_FORBIDDEN")
        clock = self._clocks.get(instrument_id)
        if clock is None:
            self._clocks[instrument_id] = _InstrumentClock(
                last_bar_index=int(bar_index), last_bar_ts=ts
            )
            return
        assert clock.last_bar_index is not None and clock.last_bar_ts is not None
        if int(bar_index) == int(clock.last_bar_index):
            self.invalid_sequence_diagnostic = f"DUPLICATE_BAR_INDEX:{instrument_id}:{bar_index}"
            raise CooldownStateError(self.invalid_sequence_diagnostic)
        if int(bar_index) < int(clock.last_bar_index):
            self.invalid_sequence_diagnostic = (
                f"NON_MONOTONIC_BAR_INDEX:{instrument_id}:{clock.last_bar_index}->{bar_index}"
            )
            raise CooldownStateError(self.invalid_sequence_diagnostic)
        if int(bar_index) != int(clock.last_bar_index) + 1:
            self.invalid_sequence_diagnostic = (
                f"BAR_GAP:{instrument_id}:expected={clock.last_bar_index + 1}:got={bar_index}"
            )
            raise CooldownStateError(self.invalid_sequence_diagnostic)
        delta = ts - clock.last_bar_ts
        if delta != PT1H:
            self.invalid_sequence_diagnostic = (
                f"NON_PT1H_BAR_DELTA:{instrument_id}:delta={delta}:expected={PT1H}"
            )
            raise CooldownStateError(self.invalid_sequence_diagnostic)
        clock.last_bar_index = int(bar_index)
        clock.last_bar_ts = ts

    def on_midband_exit_fill(
        self,
        *,
        instrument_id: str,
        direction: str,
        exit_bar_index: int,
        trigger_kind: str,
    ) -> None:
        """Arm or re-arm cooldown after a confirmed midband(-composite) exit fill."""
        if not self.enabled:
            return
        if trigger_kind not in COOLDOWN_ARMS_ON_TRIGGERS:
            return
        key = self._key(instrument_id, direction)
        arm = self._scopes.get(key)
        if arm is None:
            arm = _ScopeArm(instrument_id=instrument_id, direction=direction)
            self._scopes[key] = arm
        t = int(exit_bar_index)
        if arm.armed_at_bar_index is not None:
            arm.rearm_count += 1
            self.cooldown_resets += 1
        self.generation_counter += 1
        arm.generation = int(self.generation_counter)
        arm.exit_fill_bar_index = t
        arm.armed_at_bar_index = t
        arm.blocked_through_bar_index = t + int(self.cooldown_bars)  # t+24
        arm.first_eligible_bar_index = t + int(self.cooldown_bars) + 1  # t+25
        arm.active = True
        self.cooldown_activation_count += 1
        self._pending_first_eligible[key] = int(arm.first_eligible_bar_index)

    def is_entry_eligible(
        self,
        *,
        instrument_id: str,
        direction: str,
        bar_index: int,
    ) -> bool:
        if not self.enabled:
            return True
        key = self._key(instrument_id, direction)
        arm = self._scopes.get(key)
        if (
            arm is None
            or not arm.active
            or arm.armed_at_bar_index is None
            or arm.first_eligible_bar_index is None
        ):
            return True
        # Block [t, t+24]; eligible from t+25
        return int(bar_index) >= int(arm.first_eligible_bar_index)

    def check_entry_allowed(
        self,
        *,
        instrument_id: str,
        direction: str,
        bar_index: int,
        record: bool = True,
    ) -> bool:
        """Return True if entry allowed; optionally record block/admit attribution."""
        allowed = self.is_entry_eligible(
            instrument_id=instrument_id, direction=direction, bar_index=bar_index
        )
        if not self.enabled:
            return True
        key = self._key(instrument_id, direction)
        arm = self._scopes.get(key)
        if arm is not None and arm.armed_at_bar_index is not None:
            if int(bar_index) == int(arm.armed_at_bar_index):
                if record:
                    self.same_bar_reentry_attempts += 1
                    if not allowed:
                        self.same_bar_reentry_block_count += 1
        if not allowed:
            if record:
                self.blocked_reentry_count += 1
                self.blocked_same_side_reentry_count += 1
                if direction == "short":
                    self.blocked_short_reentry_count += 1
                else:
                    self.blocked_long_reentry_count += 1
            return False
        if (
            record
            and arm is not None
            and arm.armed_at_bar_index is not None
            and arm.first_eligible_bar_index is not None
            and int(bar_index) >= int(arm.first_eligible_bar_index)
            and key in self._pending_first_eligible
        ):
            self.admitted_same_side_reentry_after_cooldown_count += 1
            if self.first_eligible_reentry_bar is None:
                self.first_eligible_reentry_bar = int(arm.first_eligible_bar_index)
            if self.actual_reentry_bar is None:
                self.actual_reentry_bar = int(bar_index)
                self.reentry_delay_bars = int(bar_index) - int(arm.armed_at_bar_index)
            arm.active = False
            del self._pending_first_eligible[key]
        return True

    def scope_snapshot(self, instrument_id: str, direction: str) -> dict[str, Any] | None:
        key = (instrument_id, direction)
        arm = self._scopes.get(key)
        if arm is None:
            return None
        return {
            "instrument_id": arm.instrument_id,
            "direction": arm.direction,
            "exit_fill_bar_index": arm.exit_fill_bar_index,
            "armed_at_bar_index": arm.armed_at_bar_index,
            "blocked_through_bar_index": arm.blocked_through_bar_index,
            "first_eligible_bar_index": arm.first_eligible_bar_index,
            "enabled": bool(self.enabled),
            "active": bool(arm.active),
            "generation": int(arm.generation),
            "rearm_count": int(arm.rearm_count),
        }

    def attribution(self) -> dict[str, Any]:
        return {
            "blocked_reentry_count": int(self.blocked_reentry_count),
            "blocked_same_side_reentry_count": int(self.blocked_same_side_reentry_count),
            "blocked_short_reentry_count": int(self.blocked_short_reentry_count),
            "blocked_long_reentry_count": int(self.blocked_long_reentry_count),
            "admitted_same_side_reentry_after_cooldown_count": int(
                self.admitted_same_side_reentry_after_cooldown_count
            ),
            "cooldown_activation_count": int(self.cooldown_activation_count),
            "same_bar_reentry_attempts": int(self.same_bar_reentry_attempts),
            "same_bar_reentry_block_count": int(self.same_bar_reentry_block_count),
            "cooldown_resets": int(self.cooldown_resets),
            "generation_counter": int(self.generation_counter),
            "scope_isolation_violations": int(self.scope_isolation_violations),
            "invalid_sequence_diagnostic": self.invalid_sequence_diagnostic,
            "first_eligible_reentry_bar": self.first_eligible_reentry_bar,
            "actual_reentry_bar": self.actual_reentry_bar,
            "reentry_delay_bars": self.reentry_delay_bars,
            "enabled": bool(self.enabled),
            "cooldown_bars": int(self.cooldown_bars),
        }


def create_cooldown_state(
    *, enabled: bool, instrument_id: str | None = None
) -> ReentryCooldownStateV7:
    return ReentryCooldownStateV7(enabled=bool(enabled), instrument_id_expected=instrument_id)


__all__ = [
    "CooldownStateError",
    "ReentryCooldownStateV7",
    "create_cooldown_state",
]
