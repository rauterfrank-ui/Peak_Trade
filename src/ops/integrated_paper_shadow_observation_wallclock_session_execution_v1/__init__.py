"""INTEGRATED_PAPER_SHADOW_OBSERVATION_WALLCLOCK_SESSION_EXECUTION_CAPABILITY_V1.

Technical wallclock OKX-EEA public MD observation capability.
Does not create productive authorization. Does not grant Economic Validity.

Package __init__ imports only constants (no session-runtime side effects) so that
authorization gatekeeper → evidence writer imports cannot form a circular import.
"""

from __future__ import annotations

from typing import Any

from src.ops.integrated_paper_shadow_observation_wallclock_session_execution_v1.constants_v1 import (
    AUTHORITY_EFFECT_NONE,
    CAPABILITY_ID,
    NETWORK_SCOPE,
    PACKAGE_MARKER,
    PRODUCER_FAMILY,
    SCHEMA_VERSION,
    SESSION_EXECUTION_SCOPE,
)

__all__ = (
    "AUTHORITY_EFFECT_NONE",
    "CAPABILITY_ID",
    "NETWORK_SCOPE",
    "PACKAGE_MARKER",
    "PRODUCER_FAMILY",
    "SCHEMA_VERSION",
    "SESSION_EXECUTION_SCOPE",
    "preflight_wallclock_session_v1",
)


def __getattr__(name: str) -> Any:
    if name == "preflight_wallclock_session_v1":
        from src.ops.integrated_paper_shadow_observation_wallclock_session_execution_v1.session_runtime_v1 import (
            preflight_wallclock_session_v1,
        )

        return preflight_wallclock_session_v1
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
