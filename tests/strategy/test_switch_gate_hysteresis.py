"""Tests for deterministic switch gate (hysteresis, min-hold, cooldown)."""

from __future__ import annotations

import pytest

from src.ops.gates.switch_gate import (
    SwitchGateConfig,
    SwitchGateState,
    step_switch_gate,
)


def test_hysteresis_prevents_chatter_in_band() -> None:
    cfg = SwitchGateConfig(hysteresis=0.2, min_hold_steps=0, cooldown_steps=0)
    st = SwitchGateState(active="bull")
    st2 = step_switch_gate(score=0.05, state=st, cfg=cfg)
    assert st2.active == "bull"
    st3 = step_switch_gate(score=-0.05, state=st2, cfg=cfg)
    assert st3.active == "bull"


def test_switch_occurs_outside_band() -> None:
    cfg = SwitchGateConfig(hysteresis=0.2, min_hold_steps=0, cooldown_steps=0)
    st = SwitchGateState(active="bull")
    st2 = step_switch_gate(score=-0.3, state=st, cfg=cfg)
    assert st2.active == "bear"


def test_min_hold_blocks_immediate_switch_back() -> None:
    cfg = SwitchGateConfig(hysteresis=0.1, min_hold_steps=3, cooldown_steps=0)
    st = SwitchGateState(active="bull")
    st = step_switch_gate(score=-1.0, state=st, cfg=cfg)  # switch to bear
    assert st.active == "bear"
    # try switching back immediately with strong bull score -> blocked by hold
    st2 = step_switch_gate(score=+1.0, state=st, cfg=cfg)
    assert st2.active == "bear"
    st3 = step_switch_gate(score=+1.0, state=st2, cfg=cfg)
    assert st3.active == "bear"
    # after hold expires, allow switch
    st4 = step_switch_gate(score=+1.0, state=st3, cfg=cfg)
    assert st4.active == "bull"


def test_cooldown_blocks_switching_after_a_switch() -> None:
    cfg = SwitchGateConfig(hysteresis=0.1, min_hold_steps=0, cooldown_steps=3)
    st = SwitchGateState(active="bull")
    st = step_switch_gate(score=-1.0, state=st, cfg=cfg)  # switch to bear, start cooldown
    assert st.active == "bear"
    st2 = step_switch_gate(score=+1.0, state=st, cfg=cfg)
    assert st2.active == "bear"
    st3 = step_switch_gate(score=+1.0, state=st2, cfg=cfg)
    assert st3.active == "bear"
    st4 = step_switch_gate(score=+1.0, state=st3, cfg=cfg)
    assert st4.active == "bull"


def test_invalid_config_rejected() -> None:
    with pytest.raises(ValueError):
        step_switch_gate(
            score=0.0,
            state=SwitchGateState(active="bull"),
            cfg=SwitchGateConfig(hysteresis=-0.1),
        )
