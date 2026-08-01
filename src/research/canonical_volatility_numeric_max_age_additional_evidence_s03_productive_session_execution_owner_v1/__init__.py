"""Additional-Evidence S03 productive session execution owner v1.

Sole typed execution owner for Auth-v2 → consume-before-side-effects → S03
natural-age session orchestration. Capability merge does not consume production
authorization, start a real session, or open network.
"""

from research.canonical_volatility_numeric_max_age_additional_evidence_s03_productive_session_execution_owner_v1.architecture_guards_v1 import (
    assert_architecture_guards_v1,
)
from research.canonical_volatility_numeric_max_age_additional_evidence_s03_productive_session_execution_owner_v1.constants_v1 import (
    CANONICAL_EXECUTION_OWNER_SYMBOL,
    CAPABILITY_ID,
    CLI_MODE,
    PACKAGE_MARKER,
    REVIEW_MODE_ID,
)
from research.canonical_volatility_numeric_max_age_additional_evidence_s03_productive_session_execution_owner_v1.models_v1 import (
    AdditionalEvidenceS03SessionExecutionOwnerError,
)
from research.canonical_volatility_numeric_max_age_additional_evidence_s03_productive_session_execution_owner_v1.offline_probe_v1 import (
    run_offline_capability_probe_v1,
)
from research.canonical_volatility_numeric_max_age_additional_evidence_s03_productive_session_execution_owner_v1.orchestrator_v1 import (
    preflight_s03_execution_owner_v1,
    run_additional_evidence_s03_productive_session_v1,
)

__all__ = [
    "AdditionalEvidenceS03SessionExecutionOwnerError",
    "CANONICAL_EXECUTION_OWNER_SYMBOL",
    "CAPABILITY_ID",
    "CLI_MODE",
    "PACKAGE_MARKER",
    "REVIEW_MODE_ID",
    "assert_architecture_guards_v1",
    "preflight_s03_execution_owner_v1",
    "run_additional_evidence_s03_productive_session_v1",
    "run_offline_capability_probe_v1",
]
