"""Deterministic switch gate with hysteresis, min-hold, and cooldown.

Primitive for bull/bear specialist selection (double-play).
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SwitchGateConfig:
    hysteresis: float = 0.0
    min_hold_steps: int = 0
    cooldown_steps: int = 0


@dataclass(frozen=True)
class SwitchGateState:
    active: str  # e.g. "bull"|"bear"
    hold_remaining: int = 0
    cooldown_remaining: int = 0


def step_switch_gate(
    *,
    score: float,
    state: SwitchGateState,
    cfg: SwitchGateConfig,
    bull_label: str = "bull",
    bear_label: str = "bear",
) -> SwitchGateState:
    """
    Deterministic switch gate with hysteresis + min-hold + cooldown.

    Policy:
    - score >= +hysteresis => desire bull
    - score <= -hysteresis => desire bear
    - otherwise desire = current
    - When switching, enforce min_hold_steps and cooldown_steps.
    """
    if cfg.hysteresis < 0:
        raise ValueError("hysteresis must be >= 0")
    if cfg.min_hold_steps < 0 or cfg.cooldown_steps < 0:
        raise ValueError("min_hold_steps/cooldown_steps must be >= 0")

    active = state.active
    hold = max(0, int(state.hold_remaining))
    cd = max(0, int(state.cooldown_remaining))

    # decrement timers
    if hold > 0:
        hold -= 1
    if cd > 0:
        cd -= 1

    # desire based on hysteresis bands
    if score >= cfg.hysteresis:
        desire = bull_label
    elif score <= -cfg.hysteresis:
        desire = bear_label
    else:
        desire = active

    # do not switch during hold or cooldown
    if desire != active:
        if hold > 0 or cd > 0:
            return SwitchGateState(active=active, hold_remaining=hold, cooldown_remaining=cd)
        # switch now
        return SwitchGateState(
            active=desire,
            hold_remaining=cfg.min_hold_steps,
            cooldown_remaining=cfg.cooldown_steps,
        )

    return SwitchGateState(active=active, hold_remaining=hold, cooldown_remaining=cd)
