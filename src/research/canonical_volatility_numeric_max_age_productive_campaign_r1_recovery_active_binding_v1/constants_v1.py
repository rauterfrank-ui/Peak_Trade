"""R1 recovery + sole active productive-campaign binding constants.

Owner policy: ABANDON old incomplete campaign; require fresh S01 under a new
campaign identity; exactly one ACTIVE binding; no parallel campaign authority.
Does not authorize network, session execution, threshold, or trading.
"""

from __future__ import annotations

PACKAGE_MARKER = (
    "MASTER_V2_CANONICAL_VOLATILITY_NUMERIC_MAX_AGE_PRODUCTIVE_"
    "CAMPAIGN_R1_RECOVERY_ACTIVE_BINDING_V1=true"
)

CAPABILITY_ID = (
    "MASTER_V2_CANONICAL_VOLATILITY_NUMERIC_MAX_AGE_PRODUCTIVE_"
    "CAMPAIGN_R1_RECOVERY_ACTIVE_BINDING_V1"
)
REVIEW_MODE_ID = CAPABILITY_ID
OWNER = (
    "research.canonical_volatility_numeric_max_age_productive_"
    "campaign_r1_recovery_active_binding_v1"
)

SCHEMA_DISPOSITION = "canonical_volatility_numeric_max_age_productive_campaign_r1_disposition/v1"
SCHEMA_ACTIVE_BINDING = "canonical_volatility_numeric_max_age_productive_campaign_active_binding/v1"

OWNER_POLICY = "R1_ABANDON_OLD_CAMPAIGN_AND_START_NEW_CAMPAIGN_FROM_FRESH_S01"

# Historical productive campaign — terminal tombstone only (never reactive).
TOMBSTONE_ABANDONED_CAMPAIGN_ID = "cv_maxage_productive_evidence_campaign_v1_4b3bdcecab2c0bfe"
TOMBSTONE_ABANDONED_SESSION_IDS: tuple[str, ...] = (
    "cv_maxage_productive_evidence_campaign_v1_4b3bdcecab2c0bfe_s01_8a97f48c839c",
    "cv_maxage_productive_evidence_campaign_v1_4b3bdcecab2c0bfe_s02_c02312c99747",
)
TOMBSTONE_ABANDONED_REPOSITORY_SHA = "b9f3ddcc5cb0f79160d20fb74e5cf4c77834c4da"
TOMBSTONE_DISPOSITION = "ABANDONED_INCOMPLETE_NON_AUTHORITATIVE"

OLD_CAMPAIGN_COMPLETION_ALLOWED = False
OLD_CAMPAIGN_REACTIVATION_ALLOWED = False
OLD_SESSION_REUSE_ALLOWED = False
CROSS_SHA_REUSE_ALLOWED = False
SYNTHETIC_S01_ALLOWED = False
MISSING_PERSISTENCE_TREATED_AS_ABSENT = True
EXACTLY_ONCE_REQUIRED = True
NATURAL_AGE_SOURCE = "FRESH_PERSISTED_S01_LIFECYCLE_HISTORY_ONLY"
ADDITIONAL_EVIDENCE_RECLASSIFICATION = False

ACTIVE_BINDING_STATUS = "ACTIVE"
ACTIVE_CAMPAIGN_CARDINALITY = 1

DISPOSITION_REL_PATH = (
    "config/governance/"
    "canonical_volatility_numeric_max_age_productive_campaign_r1_disposition_v1.json"
)
ACTIVE_BINDING_REL_PATH = (
    "config/governance/"
    "canonical_volatility_numeric_max_age_productive_campaign_active_binding_v1.json"
)
R1_PREREGISTRATION_REL_PATH = (
    "config/research/"
    "canonical_volatility_numeric_max_age_productive_evidence_session_"
    "preregistration_r1_active_v1.json"
)

SPEC_REL_PATH = (
    "docs/ops/specs/"
    "MASTER_V2_CANONICAL_VOLATILITY_NUMERIC_MAX_AGE_PRODUCTIVE_"
    "CAMPAIGN_R1_RECOVERY_AND_ACTIVE_BINDING_V1.md"
)

# Last known materialization provenance (bootstrap/tests only). Runtime SSOT is ACTIVE binding file.
R1_MATERIALIZED_REPOSITORY_SHA = "c47704d4551e15fe8f875bebc6dc7b10e2081c42"
