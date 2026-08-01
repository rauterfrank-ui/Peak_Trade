"""Constants for S03 atomic Auth-v2 reissue→consume→execute orchestration owner."""

from __future__ import annotations

from research.canonical_volatility_numeric_max_age_additional_evidence_s03_productive_session_execution_owner_v1.constants_v1 import (
    BOUND_CAMPAIGN_ID,
    BOUND_DURATION_SECONDS,
    BOUND_INSTRUMENT,
    BOUND_NETWORK_SCOPE,
    BOUND_PREREGISTRATION_DIGEST,
    BOUND_PREREGISTRATION_ID,
    BOUND_SESSION_ID,
    BOUND_SESSION_LABEL,
    BOUND_SESSION_SCOPE,
    BOUND_VENUE,
    CANONICAL_EXECUTION_OWNER_SYMBOL as S03_EXECUTION_OWNER_SYMBOL,
)

PACKAGE_MARKER = (
    "MASTER_V2_CANONICAL_VOLATILITY_NUMERIC_MAX_AGE_ADDITIONAL_EVIDENCE_"
    "S03_ATOMIC_AUTH_V2_REISSUE_CONSUME_EXECUTE_WITH_EPHEMERAL_CONFIRM_TOKEN_V1=true"
)

CAPABILITY_ID = (
    "MASTER_V2_CANONICAL_VOLATILITY_NUMERIC_MAX_AGE_ADDITIONAL_EVIDENCE_"
    "S03_ATOMIC_AUTH_V2_REISSUE_CONSUME_EXECUTE_WITH_EPHEMERAL_CONFIRM_TOKEN_V1"
)
REVIEW_MODE_ID = CAPABILITY_ID

OWNER = (
    "research.canonical_volatility_numeric_max_age_additional_evidence_"
    "s03_atomic_auth_v2_reissue_consume_execute_v1"
)
CANONICAL_ATOMIC_OWNER_SYMBOL = (
    "run_s03_atomic_auth_v2_reissue_consume_and_execute_with_ephemeral_confirm_token_v1"
)
CLI_MODE = "additional-evidence-s03-atomic-reissue-consume-execute"

# Lifecycle invariants.
ISSUE_AND_CONSUME_MUST_SHARE_PROCESS_LIFETIME = True
TOKEN_LIFETIME_ENDS_AFTER_SUCCESSFUL_CONSUMPTION = True
TOKEN_PLAINTEXT_MUST_NOT_CROSS_PROCESS_BOUNDARY = True
AUTHORIZATION_REMAINS_SINGLE_USE = True
CONSUMPTION_BEFORE_SIDE_EFFECTS = True
FAIL_CLOSED = True
NO_SECOND_AUTHORIZATION_AUTHORITY = True
NO_SECOND_CONSUMPTION_AUTHORITY = True
NO_SECOND_EXECUTION_AUTHORITY = True
ORCHESTRATION_LIFECYCLE_AUTHORITY_ONLY = True

# Default import must not mutate productive auth / session state.
PRODUCTIVE_ATOMIC_EXECUTION_IN_DEFAULT_IMPORT = False
PRODUCTIVE_ATOMIC_EXECUTION_IN_THIS_CAPABILITY = True
HARD_STOP = True
NUMERIC_MAX_AGE_SELECTED = False
POLICY_ENFORCEMENT_ADDED = False

# Bound S03 semantics (reuse existing S03/prereg bindings; do not loosen).
BOUND_DURATION_SECONDS_V1 = BOUND_DURATION_SECONDS
BOUND_CAMPAIGN_ID_V1 = BOUND_CAMPAIGN_ID
BOUND_SESSION_ID_V1 = BOUND_SESSION_ID
BOUND_SESSION_LABEL_V1 = BOUND_SESSION_LABEL
BOUND_PREREGISTRATION_ID_V1 = BOUND_PREREGISTRATION_ID
BOUND_PREREGISTRATION_DIGEST_V1 = BOUND_PREREGISTRATION_DIGEST
BOUND_VENUE_V1 = BOUND_VENUE
BOUND_INSTRUMENT_V1 = BOUND_INSTRUMENT
BOUND_NETWORK_SCOPE_V1 = BOUND_NETWORK_SCOPE
BOUND_SESSION_SCOPE_V1 = BOUND_SESSION_SCOPE
REUSED_S03_EXECUTION_OWNER_SYMBOL = S03_EXECUTION_OWNER_SYMBOL

DEFAULT_UNCONSUMABLE_REVOCATION_REASON = (
    "bound_confirm_token_plaintext_ephemerally_destroyed_before_consumption"
)

MINIMUM_CONFIRM_TOKEN_ENTROPY_BITS = 256
CANONICAL_TOKEN_GENERATOR = "mint_productive_confirm_token_v1"
CANONICAL_AUTH_ISSUER = "issue_additional_evidence_session_authorization_v2"
CANONICAL_AUTH_REVOKER = "revoke_additional_evidence_session_authorization_v2"
CANONICAL_AUTH_CONSUMER = "consume_additional_evidence_session_authorization_v2"
CANONICAL_S03_EXECUTION_OWNER = "run_additional_evidence_s03_productive_session_v1"

ARTIFACT_RELATIVE_PATH = (
    "config/research/"
    "canonical_volatility_numeric_max_age_additional_evidence_"
    "s03_atomic_auth_v2_reissue_consume_execute_contract_v1.json"
)
SPEC_RELATIVE_PATH = (
    "docs/ops/specs/"
    "MASTER_V2_CANONICAL_VOLATILITY_NUMERIC_MAX_AGE_ADDITIONAL_EVIDENCE_"
    "S03_ATOMIC_AUTH_V2_REISSUE_CONSUME_EXECUTE_WITH_EPHEMERAL_CONFIRM_TOKEN_V1.md"
)

FORBIDDEN_IMPORT_SUBSTRINGS: tuple[str, ...] = (
    "execution.live",
    "live_trading",
    "order_entry",
    "private_endpoint",
)
