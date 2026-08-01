"""Canonical volatility numeric max-age productive evidence campaign authorization v1.

Capability surface only. This package does not issue a productive authorization,
does not start a session, and does not open network or write productive evidence.
"""

from research.canonical_volatility_numeric_max_age_campaign_authorization_v1.artifact_v1 import (
    build_campaign_authorization_artifact_v1,
    load_campaign_authorization_artifact_v1,
    parse_campaign_authorization_artifact_v1,
    verify_campaign_authorization_artifact_v1,
    write_campaign_authorization_artifact_v1,
)
from research.canonical_volatility_numeric_max_age_campaign_authorization_v1.constants_v1 import (
    AUTHORIZATION_MAXIMUM_TOTAL_CONSUMPTIONS,
    AUTHORIZATION_SCOPE,
    AUTHORIZATION_SINGLE_USE_PER_SESSION,
    BOUND_CAMPAIGN_ID,
    BOUND_SESSION_IDS,
    CAMPAIGN_AUTHORIZATION_TTL_SECONDS,
    CAPABILITY_ID,
    MAXIMUM_SESSION_COUNT,
    PACKAGE_MARKER,
    REVIEW_MODE_ID,
    SCHEMA_VERSION,
)
from research.canonical_volatility_numeric_max_age_campaign_authorization_v1.consume_v1 import (
    consume_campaign_authorization_session_v1,
    revoke_campaign_authorization_v1,
)
from research.canonical_volatility_numeric_max_age_campaign_authorization_v1.gate_v1 import (
    require_campaign_authorization_runtime_release_v1,
)
from research.canonical_volatility_numeric_max_age_campaign_authorization_v1.models_v1 import (
    CampaignAuthorizationArtifactV1,
    CampaignAuthorizationError,
    RuntimeReleaseV1,
)

__all__ = [
    "AUTHORIZATION_MAXIMUM_TOTAL_CONSUMPTIONS",
    "AUTHORIZATION_SCOPE",
    "AUTHORIZATION_SINGLE_USE_PER_SESSION",
    "BOUND_CAMPAIGN_ID",
    "BOUND_SESSION_IDS",
    "CAMPAIGN_AUTHORIZATION_TTL_SECONDS",
    "CAPABILITY_ID",
    "CampaignAuthorizationArtifactV1",
    "CampaignAuthorizationError",
    "MAXIMUM_SESSION_COUNT",
    "PACKAGE_MARKER",
    "REVIEW_MODE_ID",
    "RuntimeReleaseV1",
    "SCHEMA_VERSION",
    "build_campaign_authorization_artifact_v1",
    "consume_campaign_authorization_session_v1",
    "load_campaign_authorization_artifact_v1",
    "parse_campaign_authorization_artifact_v1",
    "require_campaign_authorization_runtime_release_v1",
    "revoke_campaign_authorization_v1",
    "verify_campaign_authorization_artifact_v1",
    "write_campaign_authorization_artifact_v1",
]
