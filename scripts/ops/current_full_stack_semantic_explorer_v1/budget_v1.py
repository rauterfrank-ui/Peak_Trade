"""Hard budgets. Crossing one yields INCOMPLETE and never PASS."""

from __future__ import annotations

import time
from dataclasses import dataclass


@dataclass(frozen=True)
class BudgetV1:
    max_files: int = 40
    max_seconds: float = 20.0
    max_nodes: int = 400
    max_edges: int = 800
    max_depth: int = 6


class BudgetTrackerV1:
    def __init__(self, budget: BudgetV1) -> None:
        self.budget = budget
        self.files = 0
        self.nodes = 0
        self.edges = 0
        self.incomplete = False
        self._started = time.monotonic()

    def _time_ok(self) -> bool:
        if time.monotonic() - self._started > self.budget.max_seconds:
            self.incomplete = True
            return False
        return True

    def allow_file(self) -> bool:
        if self.incomplete or not self._time_ok():
            self.incomplete = True
            return False
        if self.files >= self.budget.max_files:
            self.incomplete = True
            return False
        self.files += 1
        return True

    def allow_node(self) -> bool:
        if self.incomplete or not self._time_ok():
            self.incomplete = True
            return False
        if self.nodes >= self.budget.max_nodes:
            self.incomplete = True
            return False
        self.nodes += 1
        return True

    def allow_edge(self) -> bool:
        if self.incomplete or not self._time_ok():
            self.incomplete = True
            return False
        if self.edges >= self.budget.max_edges:
            self.incomplete = True
            return False
        self.edges += 1
        return True


def slice_status_v1(tracker: BudgetTrackerV1, *, failed: bool = False) -> str:
    if failed:
        return "FAIL"
    if tracker.incomplete:
        return "INCOMPLETE"
    return "PASS"
