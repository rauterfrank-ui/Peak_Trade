"""Cumulative WP backlog matrix (evidence discipline)."""

from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any, Literal

from src.ops.n1_whole_system_hard_facts_integration_wp_v1.constants_v1 import (
    BACKLOG_ROW_IDS,
    BACKLOG_TOTAL,
)

RowStatus = Literal["CLOSED", "DEFERRED_BY_DESIGN", "TRUE_BLOCKER", "OPEN"]


@dataclass(frozen=True)
class BacklogRowV1:
    backlog_id: str
    status: RowStatus
    changed_files: tuple[str, ...] = ()
    tests: tuple[str, ...] = ()
    notes: str = ""


def initial_backlog_rows_v1() -> dict[str, BacklogRowV1]:
    rows: dict[str, BacklogRowV1] = {}
    for row_id in BACKLOG_ROW_IDS:
        rows[row_id] = BacklogRowV1(backlog_id=row_id, status="OPEN")
    return rows


def close_row_v1(
    rows: dict[str, BacklogRowV1],
    *,
    backlog_id: str,
    changed_files: tuple[str, ...],
    tests: tuple[str, ...],
    notes: str = "",
) -> None:
    rows[backlog_id] = BacklogRowV1(
        backlog_id=backlog_id,
        status="CLOSED",
        changed_files=changed_files,
        tests=tests,
        notes=notes,
    )


def summarize_backlog_v1(rows: dict[str, BacklogRowV1]) -> dict[str, Any]:
    closed = sum(1 for r in rows.values() if r.status == "CLOSED")
    deferred = sum(1 for r in rows.values() if r.status == "DEFERRED_BY_DESIGN")
    blocker = sum(1 for r in rows.values() if r.status == "TRUE_BLOCKER")
    return {
        "BACKLOG_TOTAL": BACKLOG_TOTAL,
        "BACKLOG_CLOSED": closed,
        "BACKLOG_DEFERRED_BY_DESIGN": deferred,
        "BACKLOG_TRUE_BLOCKER": blocker,
        "rows": {k: asdict(v) for k, v in rows.items()},
    }
