"""Whole-system connection closure bounded WP v1 (census + static proof only)."""

from __future__ import annotations

from src.ops.whole_system_connection_closure_bounded_wp_v1.constants_v1 import (
    BASELINE_ORIGIN_MAIN_SHA,
    CONTRACT_VERSION,
    CURSORLESS_CALLER_ADJUDICATION_CLASS,
    CUTOVER_FLAGS_ADJUDICATION_CLASS,
    FINAL_D_T_ADJUDICATION_CLASS,
    INTENTIONALLY_LEGACY_CYCLE_CALLERS,
    MECHANICAL_COMPLETION_ADJUDICATION_CLASS,
    OWNER,
    PACKAGE_MARKER,
    PRODUCTIVE_CURSOR_BACKED_CYCLE_CALLERS,
    REQUIRED_CLOSURE_COUNT,
    SOLE_TRADING_DECISION_AUTHORITY,
    UNKNOWN_PRODUCTIVE_PATH_COUNT,
    WHOLE_SYSTEM_CONNECTION_COMPLETE,
)
from src.ops.whole_system_connection_closure_bounded_wp_v1.proof_v1 import (
    WholeSystemConnectionProofResultV1,
    prove_whole_system_connection_closure_v1,
)

__all__ = [
    "BASELINE_ORIGIN_MAIN_SHA",
    "CONTRACT_VERSION",
    "CURSORLESS_CALLER_ADJUDICATION_CLASS",
    "CUTOVER_FLAGS_ADJUDICATION_CLASS",
    "FINAL_D_T_ADJUDICATION_CLASS",
    "INTENTIONALLY_LEGACY_CYCLE_CALLERS",
    "MECHANICAL_COMPLETION_ADJUDICATION_CLASS",
    "OWNER",
    "PACKAGE_MARKER",
    "PRODUCTIVE_CURSOR_BACKED_CYCLE_CALLERS",
    "REQUIRED_CLOSURE_COUNT",
    "SOLE_TRADING_DECISION_AUTHORITY",
    "UNKNOWN_PRODUCTIVE_PATH_COUNT",
    "WHOLE_SYSTEM_CONNECTION_COMPLETE",
    "WholeSystemConnectionProofResultV1",
    "prove_whole_system_connection_closure_v1",
]
