"""Preregistered productive session runner capability v1.

Defines the fail-closed CLI/runner path that executes an already preregistered
campaign session with exact session-id binding and consume-before-side-effects.
This capability package does not itself start a productive session or consume
authorization during merge.
"""

from research.canonical_volatility_numeric_max_age_preregistered_productive_session_runner_v1.constants_v1 import (
    CAPABILITY_ID,
    CLI_MODE,
    PACKAGE_MARKER,
    REVIEW_MODE_ID,
    SESSION_01_ID,
    SESSION_02_ID,
)
from research.canonical_volatility_numeric_max_age_preregistered_productive_session_runner_v1.models_v1 import (
    PreregisteredSessionRunnerError,
)
from research.canonical_volatility_numeric_max_age_preregistered_productive_session_runner_v1.runner_v1 import (
    run_preregistered_productive_session_v1,
)

__all__ = [
    "CAPABILITY_ID",
    "CLI_MODE",
    "PACKAGE_MARKER",
    "PreregisteredSessionRunnerError",
    "REVIEW_MODE_ID",
    "SESSION_01_ID",
    "SESSION_02_ID",
    "run_preregistered_productive_session_v1",
]
