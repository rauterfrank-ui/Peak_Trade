"""Additional evidence session preregistration contract v2.

Resolves repository SHA semantics to immutable ancestor baseline + critical
surface digest. Does not issue/consume authorization or execute sessions.
"""

from research.canonical_volatility_numeric_max_age_additional_evidence_session_preregistration_contract_v2.architecture_guards_v2 import (
    assert_architecture_guards_v2,
)
from research.canonical_volatility_numeric_max_age_additional_evidence_session_preregistration_contract_v2.constants_v2 import (
    CAPABILITY_ID,
    PACKAGE_MARKER,
    REPOSITORY_BINDING_MODE,
    REVIEW_MODE_ID,
)
from research.canonical_volatility_numeric_max_age_additional_evidence_session_preregistration_contract_v2.contract_v2 import (
    build_active_additional_evidence_session_preregistration_v2,
    build_additional_evidence_session_preregistration_contract_v2,
    build_example_additional_session_candidate_v2,
    compute_candidate_preregistration_digest_v2,
    render_additional_evidence_session_preregistration_contract_v2,
    verify_additional_evidence_session_preregistration_contract_artifact_v2,
)
from research.canonical_volatility_numeric_max_age_additional_evidence_session_preregistration_contract_v2.models_v2 import (
    AdditionalEvidenceSessionCandidateV2,
    AdditionalEvidenceSessionPreregistrationContractV2,
    AdditionalEvidenceSessionPreregistrationContractV2Error,
)
from research.canonical_volatility_numeric_max_age_additional_evidence_session_preregistration_contract_v2.readiness_v2 import (
    evaluate_authorization_readiness_v2,
)
from research.canonical_volatility_numeric_max_age_additional_evidence_session_preregistration_contract_v2.validate_v2 import (
    reject_v1_for_new_authorization_readiness_v2,
    validate_additional_evidence_session_preregistration_candidate_v2,
)

__all__ = [
    "AdditionalEvidenceSessionCandidateV2",
    "AdditionalEvidenceSessionPreregistrationContractV2",
    "AdditionalEvidenceSessionPreregistrationContractV2Error",
    "CAPABILITY_ID",
    "PACKAGE_MARKER",
    "REPOSITORY_BINDING_MODE",
    "REVIEW_MODE_ID",
    "assert_architecture_guards_v2",
    "build_active_additional_evidence_session_preregistration_v2",
    "build_additional_evidence_session_preregistration_contract_v2",
    "build_example_additional_session_candidate_v2",
    "compute_candidate_preregistration_digest_v2",
    "evaluate_authorization_readiness_v2",
    "reject_v1_for_new_authorization_readiness_v2",
    "render_additional_evidence_session_preregistration_contract_v2",
    "validate_additional_evidence_session_preregistration_candidate_v2",
    "verify_additional_evidence_session_preregistration_contract_artifact_v2",
]
