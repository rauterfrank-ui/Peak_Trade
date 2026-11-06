"""Constants for additional-evidence session authorization v2 authority.

Sole productive issuance authority for:
canonical_volatility_numeric_max_age_additional_evidence_session_authorization/v2

Does not loosen wallclock authorization_artifact_v2 bindings and does not
extend/reactivate campaign authorization v1. This package never opens network
or executes a productive session by itself.
"""

from __future__ import annotations

from research.canonical_volatility_numeric_max_age_additional_evidence_session_preregistration_contract_v2.constants_v2 import (
    BOUND_RUNBOOK_DIGEST,
    CAPABILITY_VERSION as PREREGISTRATION_CONTRACT_VERSION,
    DEFAULT_CODE_BASELINE_SHA,
    EXPECTED_INSTRUMENT,
    EXPECTED_NETWORK_SCOPE,
    EXPECTED_SESSION_SCOPE,
    EXPECTED_VENUE,
    MINIMUM_SESSION_DURATION_SECONDS,
    PREREGISTRATION_RELATIVE_PATH,
)

PACKAGE_MARKER = (
    "MASTER_V2_CANONICAL_VOLATILITY_NUMERIC_MAX_AGE_ADDITIONAL_EVIDENCE_"
    "SESSION_AUTHORIZATION_V2_AUTHORITY_V1=true"
)

CAPABILITY_ID = (
    "MASTER_V2_CANONICAL_VOLATILITY_NUMERIC_MAX_AGE_ADDITIONAL_EVIDENCE_"
    "SESSION_AUTHORIZATION_V2_AUTHORITY_V1"
)
REVIEW_MODE_ID = CAPABILITY_ID

AUTHORIZATION_VERSION = (
    "canonical_volatility_numeric_max_age_additional_evidence_session_authorization/v2"
)
AUTHORIZATION_SCOPE = (
    "canonical_volatility_numeric_max_age_additional_evidence_session_execution_v2"
)

ISSUED_BY_AUTHORITY = (
    "research.canonical_volatility_numeric_max_age_additional_evidence_session_authorization_v2"
)
OWNER = ISSUED_BY_AUTHORITY

ADDITIONAL_EVIDENCE_AUTHORIZATION_V2_SOLE_ISSUANCE_AUTHORITY = True
WALLCLOCK_AUTHORIZATION_WRITER_UNCHANGED = True
CAMPAIGN_AUTHORIZATION_V1_UNCHANGED = True
NO_SECOND_ISSUANCE_AUTHORITY = True

REQUIRED_NETWORK_SCOPE = EXPECTED_NETWORK_SCOPE
REQUIRED_DURATION_SECONDS = MINIMUM_SESSION_DURATION_SECONDS
REQUIRED_VENUE = EXPECTED_VENUE
REQUIRED_INSTRUMENT = EXPECTED_INSTRUMENT
REQUIRED_SESSION_SCOPE = EXPECTED_SESSION_SCOPE

DEFAULT_CODE_BASELINE_SHA_BOUND = DEFAULT_CODE_BASELINE_SHA
DEFAULT_RUNBOOK_DIGEST = BOUND_RUNBOOK_DIGEST
DEFAULT_PREREGISTRATION_CONTRACT_VERSION = PREREGISTRATION_CONTRACT_VERSION
DEFAULT_PREREGISTRATION_PATH = PREREGISTRATION_RELATIVE_PATH

# Auth wall-clock TTL (issuance validity), independent of session duration.
AUTHORIZATION_TTL_SECONDS = 86400

CONSUMPTION_STATE_UNCONSUMED = "UNCONSUMED"
CONSUMPTION_STATE_CONSUMED = "CONSUMED"
CONSUMPTION_STATE_REVOKED = "REVOKED"
KNOWN_CONSUMPTION_STATES: tuple[str, ...] = (
    CONSUMPTION_STATE_UNCONSUMED,
    CONSUMPTION_STATE_CONSUMED,
    CONSUMPTION_STATE_REVOKED,
)

REVOCATION_STATE_ACTIVE = "ACTIVE"
REVOCATION_STATE_REVOKED = "REVOKED"
KNOWN_REVOCATION_STATES: tuple[str, ...] = (
    REVOCATION_STATE_ACTIVE,
    REVOCATION_STATE_REVOKED,
)

FULL_GIT_SHA_LENGTH = 40

# Durable artifact layout under evidence root (created only by issuance/consume).
DEFAULT_EVIDENCE_CAMPAIGN_ROOT = (
    "docs/evidence/canonical_volatility_max_age_productive_research_evidence_ledger_v1/campaigns"
)
AUTHORIZATION_FILENAME = "additional_evidence_session_authorization_v2.json"
CONSUMPTION_LEDGER_FILENAME = "consumption_ledger.jsonl"
REVOCATION_LEDGER_FILENAME = "revocation_ledger.jsonl"

CONSUME_BEFORE_SESSION_LOCK = True
CONSUME_BEFORE_EVIDENCE_CREATION = True
CONSUME_BEFORE_NETWORK = True
CONSUME_BEFORE_RUNTIME_INITIALIZATION = True

SIDE_EFFECT_AUTHORIZATION_CONSUMED = "AUTHORIZATION_CONSUMED"
SIDE_EFFECT_SESSION_LOCK = "SESSION_LOCK"
SIDE_EFFECT_EVIDENCE_CREATION = "EVIDENCE_CREATION"
SIDE_EFFECT_NETWORK = "NETWORK"
SIDE_EFFECT_RUNTIME_INITIALIZATION = "RUNTIME_INITIALIZATION"

FORBIDDEN_SIDE_EFFECT_BEFORE_CONSUME: tuple[str, ...] = (
    SIDE_EFFECT_SESSION_LOCK,
    SIDE_EFFECT_EVIDENCE_CREATION,
    SIDE_EFFECT_NETWORK,
    SIDE_EFFECT_RUNTIME_INITIALIZATION,
)

# Closed-world authorization artifact fields.
REQUIRED_AUTHORIZATION_FIELDS: tuple[str, ...] = (
    "authorization_version",
    "authorization_id",
    "authorization_digest",
    "authorization_scope",
    "preregistration_id",
    "preregistration_digest",
    "preregistration_contract_version",
    "preregistration_contract_digest",
    "code_baseline_sha",
    "execution_sha",
    "critical_surface_digest",
    "runbook_digest",
    "venue",
    "instrument",
    "network_scope",
    "session_scope",
    "duration_seconds",
    "earliest_start",
    "expires_at",
    "single_use",
    "issued_at",
    "issued_by_authority",
    "campaign_id",
    "confirm_token_fingerprint",
    "confirm_token_digest",
    "confirm_token_binding_sha256",
    "revocation_ledger_path",
    "consumption_ledger_path",
    "consumption_state",
    "revocation_state",
)

UNKNOWN_FIELD_POLICY = "REJECT_UNKNOWN_FIELDS"

# Hard non-goals for this capability package itself.
PRODUCTIVE_ISSUANCE_IN_DEFAULT_IMPORT = False
NETWORK_SIDE_EFFECTS_ON_CAPABILITY = False
SESSION_EXECUTION_AUTHORIZED = False
ORDERS_AUTHORIZED = False
LIVE_AUTHORIZED = False
TESTNET_AUTHORIZED = False
CREDENTIALS_AUTHORIZED = False
HARD_STOP = True
READY_FOR_AUTHORIZATION_ISSUANCE_CONSTANT = False
READY_FOR_PRODUCTIVE_SESSION_EXECUTION = False

ARTIFACT_RELATIVE_PATH = (
    "config/research/"
    "canonical_volatility_numeric_max_age_additional_evidence_"
    "session_authorization_contract_v2.json"
)
SPEC_RELATIVE_PATH = (
    "docs/ops/specs/"
    "MASTER_V2_CANONICAL_VOLATILITY_NUMERIC_MAX_AGE_ADDITIONAL_EVIDENCE_"
    "SESSION_AUTHORIZATION_V2_AUTHORITY_V1.md"
)

# Rejected foreign schemas (cross-authority isolation).
WALLCLOCK_AUTHORIZATION_SCHEMA = "authorization_artifact_v2"
CAMPAIGN_AUTHORIZATION_SCHEMA_PREFIX = (
    "canonical_volatility_numeric_max_age_productive_evidence_campaign_authorization/"
)
WALLCLOCK_NETWORK_SCOPE = "PUBLIC_MARKET_DATA_ONLY"
WALLCLOCK_DURATION_SECONDS = 3600

FORBIDDEN_IMPORT_SUBSTRINGS: tuple[str, ...] = (
    "execution.live",
    "place_order",
    "submit_order",
    "broker_adapter",
    "trading.master_v2.double_play",
)

CONFIRM_TOKEN_ADAPTER_ID = (
    "research.canonical_volatility_numeric_max_age_additional_evidence_"
    "session_authorization_v2.confirm_token_v2"
)
