"""Canonical volatility numeric max-age parameter research execution v1.

Non-enforcing, counterfactual-only research capability. Does not select,
promote, or enforce a numeric max-age threshold.
"""

from research.canonical_volatility_numeric_max_age_parameter_research_execution_v1.architecture_guards_v1 import (
    assert_architecture_guards_v1,
)
from research.canonical_volatility_numeric_max_age_parameter_research_execution_v1.constants_v1 import (
    CAPABILITY_ID,
    CAPABILITY_VERSION,
    EXPECTED_PREREGISTRATION_DIGEST,
    HARD_STOP,
    NUMERIC_THRESHOLD_SELECTED,
    PACKAGE_MARKER,
    PARAMETER_PROMOTED,
    THRESHOLD_STATUS,
)
from research.canonical_volatility_numeric_max_age_parameter_research_execution_v1.contracts_v1 import (
    MaxAgeResearchExecutionError,
    bind_candidate_domain_v1,
    bind_hypothesis_contract_v1,
    bind_robustness_execution_contract_v1,
    bind_split_and_embargo_contract_v1,
    verify_preregistration_digest_v1,
)
from research.canonical_volatility_numeric_max_age_parameter_research_execution_v1.runner_v1 import (
    run_max_age_parameter_research_execution_v1,
)

__all__ = [
    "CAPABILITY_ID",
    "CAPABILITY_VERSION",
    "EXPECTED_PREREGISTRATION_DIGEST",
    "HARD_STOP",
    "MaxAgeResearchExecutionError",
    "NUMERIC_THRESHOLD_SELECTED",
    "PACKAGE_MARKER",
    "PARAMETER_PROMOTED",
    "THRESHOLD_STATUS",
    "assert_architecture_guards_v1",
    "bind_candidate_domain_v1",
    "bind_hypothesis_contract_v1",
    "bind_robustness_execution_contract_v1",
    "bind_split_and_embargo_contract_v1",
    "run_max_age_parameter_research_execution_v1",
    "verify_preregistration_digest_v1",
]
