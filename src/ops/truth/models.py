"""
Shared result models for docs drift guard and repo truth claims.

Deterministic statuses: PASS, FAIL, UNKNOWN (e.g. unsupported check or I/O ambiguity).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Mapping


class TruthStatus(str, Enum):
    """Outcome of a deterministic truth check."""

    PASS = "PASS"
    FAIL = "FAIL"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True)
class TruthCheckResult:
    """Single check outcome (one row in a report)."""

    check_id: str
    status: TruthStatus
    message: str
    details: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class DocsDriftViolation:
    """One docs-drift rule fired: sensitive paths changed without required doc updates."""

    rule_id: str
    triggered_paths: tuple[str, ...]
    required_docs: tuple[str, ...]


@dataclass(frozen=True)
class DocsDriftEvaluationResult:
    """Result of evaluating changed files against docs_truth_map rules."""

    status: TruthStatus
    violations: tuple[DocsDriftViolation, ...] = ()

    @property
    def ok(self) -> bool:
        return self.status is TruthStatus.PASS


@dataclass(frozen=True)
class RepoTruthEvaluationResult:
    """Aggregate result for repo truth claims (path existence, etc.)."""

    status: TruthStatus
    results: tuple[TruthCheckResult, ...] = ()

    @property
    def ok(self) -> bool:
        return self.status is TruthStatus.PASS
