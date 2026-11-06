"""Additional-evidence session authorization v2 authority.

Sole productive issuance authority for additional-evidence Numeric-Max-Age
sessions. Does not issue by import side effect, does not open network, and
does not execute sessions.
"""

from research.canonical_volatility_numeric_max_age_additional_evidence_session_authorization_v2.architecture_guards_v2 import (
    assert_architecture_guards_v2,
)
from research.canonical_volatility_numeric_max_age_additional_evidence_session_authorization_v2.artifact_v2 import (
    build_additional_evidence_session_authorization_v2,
    load_additional_evidence_session_authorization_v2,
    parse_additional_evidence_session_authorization_v2,
    verify_additional_evidence_session_authorization_v2,
    write_additional_evidence_session_authorization_v2,
)
from research.canonical_volatility_numeric_max_age_additional_evidence_session_authorization_v2.constants_v2 import (
    AUTHORIZATION_VERSION,
    CAPABILITY_ID,
    ISSUED_BY_AUTHORITY,
    PACKAGE_MARKER,
    REVIEW_MODE_ID,
)
from research.canonical_volatility_numeric_max_age_additional_evidence_session_authorization_v2.consume_v2 import (
    consume_additional_evidence_session_authorization_v2,
    revoke_additional_evidence_session_authorization_v2,
)
from research.canonical_volatility_numeric_max_age_additional_evidence_session_authorization_v2.discovery_v2 import (
    count_unconsumed_authorizations_for_scope_v2,
    discover_unconsumed_additional_evidence_authorizations_v2,
)
from research.canonical_volatility_numeric_max_age_additional_evidence_session_authorization_v2.issuance_v2 import (
    issue_additional_evidence_session_authorization_v2,
)
from research.canonical_volatility_numeric_max_age_additional_evidence_session_authorization_v2.models_v2 import (
    AdditionalEvidenceSessionAuthorizationV2,
    AdditionalEvidenceSessionAuthorizationV2Error,
)
from research.canonical_volatility_numeric_max_age_additional_evidence_session_authorization_v2.readiness_v2 import (
    evaluate_additional_evidence_authorization_issuance_readiness_v2,
)

__all__ = [
    "AUTHORIZATION_VERSION",
    "AdditionalEvidenceSessionAuthorizationV2",
    "AdditionalEvidenceSessionAuthorizationV2Error",
    "CAPABILITY_ID",
    "ISSUED_BY_AUTHORITY",
    "PACKAGE_MARKER",
    "REVIEW_MODE_ID",
    "assert_architecture_guards_v2",
    "build_additional_evidence_session_authorization_v2",
    "consume_additional_evidence_session_authorization_v2",
    "count_unconsumed_authorizations_for_scope_v2",
    "discover_unconsumed_additional_evidence_authorizations_v2",
    "evaluate_additional_evidence_authorization_issuance_readiness_v2",
    "issue_additional_evidence_session_authorization_v2",
    "load_additional_evidence_session_authorization_v2",
    "parse_additional_evidence_session_authorization_v2",
    "revoke_additional_evidence_session_authorization_v2",
    "verify_additional_evidence_session_authorization_v2",
    "write_additional_evidence_session_authorization_v2",
]
