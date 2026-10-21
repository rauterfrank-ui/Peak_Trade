"""Hard budgets. Crossing one yields INCOMPLETE and never PASS."""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Callable


@dataclass(frozen=True)
class BudgetV1:
    max_files: int = 40
    max_seconds: float = 20.0
    max_nodes: int = 400
    max_edges: int = 800
    max_depth: int = 6


@dataclass(frozen=True)
class BudgetSnapshotV1:
    files: int
    nodes: int
    edges: int
    file_closed: bool
    node_closed: bool
    edge_closed: bool
    time_closed: bool
    stop_reasons: tuple[str, ...]


class BudgetTrackerV1:
    def __init__(self, budget: BudgetV1, *, clock: Callable[[], float] | None = None) -> None:
        self.budget = budget
        self.files = 0
        self.nodes = 0
        self.edges = 0
        self.file_closed = False
        self.node_closed = False
        self.edge_closed = False
        self.time_closed = False
        self.stop_reasons: list[str] = []
        self._clock = clock or time.monotonic
        self._started = self._clock()

    @property
    def incomplete(self) -> bool:
        return self.file_closed or self.node_closed or self.edge_closed or self.time_closed

    def snapshot(self) -> BudgetSnapshotV1:
        return BudgetSnapshotV1(
            self.files,
            self.nodes,
            self.edges,
            self.file_closed,
            self.node_closed,
            self.edge_closed,
            self.time_closed,
            tuple(self.stop_reasons),
        )

    def restore(self, snap: BudgetSnapshotV1) -> None:
        self.files = snap.files
        self.nodes = snap.nodes
        self.edges = snap.edges
        self.file_closed = snap.file_closed
        self.node_closed = snap.node_closed
        self.edge_closed = snap.edge_closed
        self.time_closed = snap.time_closed
        self.stop_reasons = list(snap.stop_reasons)

    def _mark(self, reason: str) -> None:
        if reason not in self.stop_reasons:
            self.stop_reasons.append(reason)

    def _time_ok(self) -> bool:
        if self._clock() - self._started > self.budget.max_seconds:
            self.time_closed = True
            self._mark("TIME_BUDGET")
            return False
        return True

    def allow_file(self) -> bool:
        if not self._time_ok() or self.node_closed:
            return False
        if self.file_closed or self.files >= self.budget.max_files:
            self.file_closed = True
            self._mark("FILE_BUDGET")
            return False
        self.files += 1
        return True

    def allow_node(self) -> bool:
        if not self._time_ok() or self.node_closed:
            return False
        if self.nodes >= self.budget.max_nodes:
            self.node_closed = True
            self._mark("NODE_BUDGET")
            return False
        self.nodes += 1
        return True

    def allow_edge(self) -> bool:
        if not self._time_ok() or self.edge_closed:
            return False
        if self.edges >= self.budget.max_edges:
            self.edge_closed = True
            self._mark("EDGE_BUDGET")
            return False
        self.edges += 1
        return True


def slice_status_v1(
    tracker: BudgetTrackerV1, *, failed: bool = False, coverage_gap: bool = False
) -> str:
    if failed:
        return "FAIL"
    if coverage_gap or tracker.time_closed or tracker.node_closed or tracker.edge_closed:
        return "INCOMPLETE"
    return "PASS"
