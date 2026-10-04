"""Operational bound enforcement (not trading semantics)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from src.ops.paper_shadow_bounded_orchestrator_v1.run_contract_v1 import PaperShadowRunContractV1


@dataclass
class BoundedRunCountersV1:
    observation_count: int = 0
    cycle_count: int = 0
    simulated_execution_count: int = 0
    open_simulated_positions: int = 0
    elapsed_seconds: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "observation_count": self.observation_count,
            "cycle_count": self.cycle_count,
            "simulated_execution_count": self.simulated_execution_count,
            "open_simulated_positions": self.open_simulated_positions,
            "elapsed_seconds": self.elapsed_seconds,
        }


@dataclass(frozen=True)
class BoundCheckResultV1:
    stop: bool
    hard_kill: bool
    reason: str

    def to_dict(self) -> dict[str, Any]:
        return {"stop": self.stop, "hard_kill": self.hard_kill, "reason": self.reason}


def check_operational_bounds_v1(
    *,
    contract: PaperShadowRunContractV1,
    counters: BoundedRunCountersV1,
) -> BoundCheckResultV1:
    if counters.elapsed_seconds >= float(contract.run_duration_seconds):
        return BoundCheckResultV1(stop=True, hard_kill=False, reason="NORMAL_DURATION_COMPLETE")
    if counters.observation_count >= contract.max_observation_count:
        return BoundCheckResultV1(stop=True, hard_kill=False, reason="MAX_OBSERVATION_BOUND")
    if counters.cycle_count >= contract.max_cycle_count:
        return BoundCheckResultV1(stop=True, hard_kill=False, reason="MAX_CYCLE_BOUND")
    if counters.simulated_execution_count >= contract.max_simulated_execution_count:
        return BoundCheckResultV1(
            stop=True, hard_kill=False, reason="MAX_SIMULATED_EXECUTION_BOUND"
        )
    return BoundCheckResultV1(stop=False, hard_kill=False, reason="")
