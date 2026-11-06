"""Research-only HOLDOUT evaluation wiring for Exit V8 holdout successor v1.

Exactly one authorized holdout run of
``BOLLINGER_MR_MIDBAND_EXIT_REENTRY_COOLDOWN_NON_BITCOIN_PERPETUALS_HOLDOUT_V1``.

Import alone does not access sealed holdout data, claim a run slot, or execute.
Requires the separate operator execution GO env var plus bound authorization
fields before any evaluation path may proceed.

Lane/successor legality is read from existing backlog and holdout contract SSOTs
(``OPEN_BACKLOG`` / ``DEFINITION_ONLY_HOLDOUT_PREREGISTERED``) under
``CANONICAL_RESEARCH_LANE_POST_TERMINAL_LIFECYCLE_CONTRACT_V1``.
"""

BOLLINGER_MR_MIDBAND_EXIT_REENTRY_COOLDOWN_HOLDOUT_EVALUATION_V1 = True
HOLDOUT_EXECUTION_IMPLEMENTED = True
PACKAGE_MARKER = "BOLLINGER_MR_MIDBAND_EXIT_REENTRY_COOLDOWN_HOLDOUT_EVALUATION_V1=true"

__all__ = [
    "BOLLINGER_MR_MIDBAND_EXIT_REENTRY_COOLDOWN_HOLDOUT_EVALUATION_V1",
    "HOLDOUT_EXECUTION_IMPLEMENTED",
    "PACKAGE_MARKER",
]
