"""Scoped GHV adapter constants. AUTHORITY=NONE."""

from __future__ import annotations

from typing import Final

from scripts.ops.pin_scope_binding_v1.constants_v1 import (
    AUTHORITY,
    COVERAGE_PROOF,
    EXECUTION_AUTHORITY,
    GUARDIAN_IDENTITY,
    LIVE_GATE,
    NETWORK_ACCESS,
    RUNTIME_AUTHORIZATION_EFFECT,
    SAFETY_AUTHORITY,
    TRADING_AUTHORITY,
)

SCHEMA_ID: Final = "SCOPED_GHV_CROSSWALK_ADAPTER_V1"
SCHEMA_VERSION: Final = 1

DEFAULT_MAX_DEPTH: Final = 2
MAX_DEPTH_LIMIT: Final = 32
DIRECT_DEPTH: Final = 1

GRAPH_MATERIALIZED: Final = False
FORBIDDEN_PASS_KEYS: Final = frozenset(
    {"overall_pass", "guardian_pass", "universe_pass", "live_authorized", "coverage_pass"}
)

__all__ = [
    "AUTHORITY",
    "COVERAGE_PROOF",
    "EXECUTION_AUTHORITY",
    "GUARDIAN_IDENTITY",
    "LIVE_GATE",
    "NETWORK_ACCESS",
    "RUNTIME_AUTHORIZATION_EFFECT",
    "SAFETY_AUTHORITY",
    "TRADING_AUTHORITY",
]
