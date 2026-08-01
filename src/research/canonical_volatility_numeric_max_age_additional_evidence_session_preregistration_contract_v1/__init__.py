"""Additional evidence session preregistration contract v1.

Contract capability only: versioned floors, uniqueness guards, authorization
binding schema, and candidate validation. Does not create preregistrations,
issue/consume authorization, or execute sessions.
"""

from research.canonical_volatility_numeric_max_age_additional_evidence_session_preregistration_contract_v1.architecture_guards_v1 import (
    assert_architecture_guards_v1,
)
from research.canonical_volatility_numeric_max_age_additional_evidence_session_preregistration_contract_v1.constants_v1 import (
    CAPABILITY_ID,
    PACKAGE_MARKER,
    REVIEW_MODE_ID,
)
from research.canonical_volatility_numeric_max_age_additional_evidence_session_preregistration_contract_v1.contract_v1 import (
    build_additional_evidence_session_preregistration_contract_v1,
    build_example_additional_session_candidate_pair_v1,
    build_example_additional_session_candidate_v1,
    compute_candidate_preregistration_digest_v1,
    render_additional_evidence_session_preregistration_contract_v1,
    verify_additional_evidence_session_preregistration_contract_artifact_v1,
)
from research.canonical_volatility_numeric_max_age_additional_evidence_session_preregistration_contract_v1.models_v1 import (
    AdditionalEvidenceSessionCandidateV1,
    AdditionalEvidenceSessionPreregistrationContractError,
    AdditionalEvidenceSessionPreregistrationContractV1,
)
from research.canonical_volatility_numeric_max_age_additional_evidence_session_preregistration_contract_v1.validate_v1 import (
    validate_additional_evidence_session_preregistration_candidate_v1,
)

__all__ = [
    "AdditionalEvidenceSessionCandidateV1",
    "AdditionalEvidenceSessionPreregistrationContractError",
    "AdditionalEvidenceSessionPreregistrationContractV1",
    "CAPABILITY_ID",
    "PACKAGE_MARKER",
    "REVIEW_MODE_ID",
    "assert_architecture_guards_v1",
    "build_additional_evidence_session_preregistration_contract_v1",
    "build_example_additional_session_candidate_pair_v1",
    "build_example_additional_session_candidate_v1",
    "compute_candidate_preregistration_digest_v1",
    "render_additional_evidence_session_preregistration_contract_v1",
    "validate_additional_evidence_session_preregistration_candidate_v1",
    "verify_additional_evidence_session_preregistration_contract_artifact_v1",
]
