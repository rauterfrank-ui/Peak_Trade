"""Structured supervisor trace (audit)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class StandingSupervisorTraceV1:
    run_id: str
    tick_index: int = 0
    bound_instrument_id: str = ""
    venue_native_id: str = ""
    recovery_completed: bool = False
    recovery_steps: list[str] = field(default_factory=list)
    public_supply_refreshed: bool = False
    public_marks_count: int = 0
    pretrade_truth_refreshed: bool = False
    pretrade_freshness_status: str = ""
    wp02_hook_invoked: bool = False
    continuous_admission_granted: bool = False
    continuous_admission_reasons: tuple[str, ...] = ()
    accepted_c1_count: int = 0
    governed_cycle_count: int = 0
    terminal_disposition: str = ""
    post_count: int = 0
    stall_reason: str = ""
    extra: dict[str, Any] = field(default_factory=dict)
