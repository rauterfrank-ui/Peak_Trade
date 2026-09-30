"""Safety and WP identity constants (no runtime authorization)."""

from __future__ import annotations

from src.ops.hard_facts_system_closure_v1.constants_v1 import (
    EXTERNAL_EFFECT_AUTHORIZED,
    MAX_POSITIONS_EFFECTIVE,
    MULTI_FUTURE_RUNTIME_AUTHORIZED,
    POST_ALLOWED,
    PRE_EXTERNAL_TERMINAL,
    REAL_VENUE_POST_ALLOWED,
)

WORK_PACKAGE_ID = "n1_whole_system_hard_facts_integration_wp_v1"
EVIDENCE_ROOT_RELATIVE = (
    "evidence/ops/n1_whole_system_hard_facts_integration_wp_v1/20260930T041500Z"
)
BACKLOG_TOTAL = 26

BACKLOG_ROW_IDS: tuple[str, ...] = (
    "RW-PUB-G1",
    "RW-PUB-G5",
    "RW-PUB-G9",
    "RW-E1",
    "RW-E2",
    "RW-E3",
    "RW-E4",
    "RW-E5",
    "RW-E6",
    "RW-E7",
    "RW-E8",
    "RW-E9",
    "RW-E10",
    "RW-E11",
    "RW-E12",
    "RW-E13",
    "RW-E14",
    "RW-E15",
    "RW-E16",
    "RW-E17",
    "RW-E18",
    "RW-E19",
    "RW-E20",
    "RW-E21",
    "RW-E22",
    "RW-E23",
)

__all__ = [
    "BACKLOG_ROW_IDS",
    "BACKLOG_TOTAL",
    "EVIDENCE_ROOT_RELATIVE",
    "EXTERNAL_EFFECT_AUTHORIZED",
    "MAX_POSITIONS_EFFECTIVE",
    "MULTI_FUTURE_RUNTIME_AUTHORIZED",
    "POST_ALLOWED",
    "PRE_EXTERNAL_TERMINAL",
    "REAL_VENUE_POST_ALLOWED",
    "WORK_PACKAGE_ID",
]
