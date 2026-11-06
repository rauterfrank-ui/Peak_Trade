"""Durable kill-switch state → productive MV2 host exit / trading_gate binding."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from src.ops.gates.risk_gate import (
    canonical_kill_switch_state_path,
    kill_switch_should_block_trading,
    resolve_kill_switch_limit_from_state_file,
)


@dataclass(frozen=True)
class DurableKillSwitchMv2BindingV1:
    killstate_active: bool
    killstate_trigger: str
    durable_read_ok: bool
    state_label: str
    blocks_new_entry: bool
    safety_exit_armed: bool
    owner: str = "ops.hard_facts_system_closure_v1.durable_kill_switch_mv2_binding_v1"


def resolve_durable_kill_switch_for_mv2_host_v1(
    *,
    kill_switch_state_path: Optional[str] = None,
    explicit_active: bool = False,
) -> DurableKillSwitchMv2BindingV1:
    """Single reader for MV2 HostExitPolicy producers — no parallel kill owner."""
    if explicit_active:
        return DurableKillSwitchMv2BindingV1(
            killstate_active=True,
            killstate_trigger="EXPLICIT_KILLSTATE_ACTIVE",
            durable_read_ok=True,
            state_label="EXPLICIT",
            blocks_new_entry=True,
            safety_exit_armed=True,
        )
    path = str(kill_switch_state_path or canonical_kill_switch_state_path())
    resolved = resolve_kill_switch_limit_from_state_file(path)
    label = "UNKNOWN"
    trigger = ""
    if Path(path).is_file():
        try:
            with Path(path).open(encoding="utf-8") as handle:
                data = json.load(handle)
            label = str(data.get("state") or "UNKNOWN").strip().upper()
        except Exception:
            label = "READ_ERROR"
    if resolved is True:
        trigger = f"DURABLE_KILL_SWITCH_{label or 'BLOCKING'}"
        return DurableKillSwitchMv2BindingV1(
            killstate_active=True,
            killstate_trigger=trigger,
            durable_read_ok=label not in {"UNKNOWN", "READ_ERROR"},
            state_label=label,
            blocks_new_entry=True,
            safety_exit_armed=True,
        )
    if resolved is False:
        return DurableKillSwitchMv2BindingV1(
            killstate_active=False,
            killstate_trigger="",
            durable_read_ok=True,
            state_label=label,
            blocks_new_entry=False,
            safety_exit_armed=False,
        )
    blocked = kill_switch_should_block_trading(explicit_active=False)
    return DurableKillSwitchMv2BindingV1(
        killstate_active=bool(blocked),
        killstate_trigger="DURABLE_KILL_SWITCH_FAIL_CLOSED" if blocked else "",
        durable_read_ok=False,
        state_label=label,
        blocks_new_entry=bool(blocked),
        safety_exit_armed=bool(blocked),
    )
