"""Constants for additional evidence session preregistration contract v1.

Contract capability only. Does not create session preregistrations, issue or
consume authorization, open network, or execute productive sessions.

Hardened by:
MASTER_V2_CANONICAL_VOLATILITY_NUMERIC_MAX_AGE_ADDITIONAL_EVIDENCE_SESSION_CONTRACT_HARDENING_V1
"""

from __future__ import annotations

PACKAGE_MARKER = (
    "MASTER_V2_CANONICAL_VOLATILITY_NUMERIC_MAX_AGE_ADDITIONAL_EVIDENCE_"
    "SESSION_PREREGISTRATION_CONTRACT_V1=true"
)

CAPABILITY_ID = (
    "MASTER_V2_CANONICAL_VOLATILITY_NUMERIC_MAX_AGE_ADDITIONAL_EVIDENCE_"
    "SESSION_PREREGISTRATION_CONTRACT_V1"
)
HARDENING_CAPABILITY_ID = (
    "MASTER_V2_CANONICAL_VOLATILITY_NUMERIC_MAX_AGE_ADDITIONAL_EVIDENCE_"
    "SESSION_CONTRACT_HARDENING_V1"
)
REVIEW_MODE_ID = HARDENING_CAPABILITY_ID
CAPABILITY_VERSION = (
    "canonical_volatility_numeric_max_age_additional_evidence_session_preregistration_contract/v1"
)
OWNER = (
    "research.canonical_volatility_numeric_max_age_additional_evidence_"
    "session_preregistration_contract_v1"
)

SCHEMA_NAME = (
    "canonical_volatility_numeric_max_age_additional_evidence_session_preregistration_contract"
)
SCHEMA_VERSION = "v1"
CONTRACT_VERSION = CAPABILITY_VERSION
CANDIDATE_SCHEMA_NAME = (
    "canonical_volatility_numeric_max_age_additional_evidence_session_preregistration_candidate"
)
# Exactly one admissible candidate schema version (no aliases / normalization).
CANDIDATE_SCHEMA_VERSION = (
    "canonical_volatility_numeric_max_age_additional_evidence_session_preregistration_candidate/v1"
)

# Canonical origin/main binding after additional-evidence contract merge (PR #5628).
# Rebased from bb5b1f4572deb451d238f890482254c690c164d2 (PR #5626 natural-age wiring).
BOUND_REPOSITORY_SHA = "790065c2417a0006bef97b3496bfef30739e9ff3"
BOUND_DESIGN_DIGEST = "965f6e09e50e434e363d380c2d62e43041a37ad7d87956e590609a16f011b537"
BOUND_RUNBOOK_DIGEST = "c7136936ff18057918dd5a59abda4126c9c7437bf097d5808f67d46c68811445"
BOUND_PRODUCTIVE_ACCUMULATION_DIGEST = (
    "777e3dd8aa3458f8687cabbadf63016ac478b5385568ee3d54d22c119880a62e"
)

EXISTING_EXHAUSTED_CAMPAIGN_ID = "cv_maxage_productive_evidence_campaign_v1_4b3bdcecab2c0bfe"
EXISTING_EXHAUSTED_SESSION_IDS: tuple[str, ...] = (
    "cv_maxage_productive_evidence_campaign_v1_4b3bdcecab2c0bfe_s01_8a97f48c839c",
    "cv_maxage_productive_evidence_campaign_v1_4b3bdcecab2c0bfe_s02_c02312c99747",
)
EXISTING_CAMPAIGN_MAXIMUM_SESSION_COUNT = 2
EXISTING_CAMPAIGN_PREREGISTRATION_DIGEST = (
    "1cfc1698796b1b931077cd692c7b0e97bc401f626d7e7b17bba1a777b62a252f"
)

TARGET_AGE_BUCKETS_SECONDS: tuple[int, ...] = (
    60,
    120,
    300,
    600,
    900,
    1800,
    3600,
    7200,
)

MINIMUM_ADDITIONAL_PRODUCTIVE_SESSIONS = 2
MINIMUM_SESSION_DURATION_SECONDS = 10860
MINIMUM_POST_FIRST_PRODUCE_EVENT_SPAN_SECONDS = 7260
MINIMUM_MAXIMUM_CYCLES_PER_SESSION = 182
RECOMMENDED_MAXIMUM_CYCLES_PER_SESSION = 200
MINIMUM_MAXIMUM_REQUESTS_PER_SESSION = 182
RECOMMENDED_MAXIMUM_REQUESTS_PER_SESSION = 200
MINIMUM_INTERVAL_SECONDS = 2.0
MAXIMUM_REQUESTS_PER_CYCLE = 3

PUBLIC_MD_VENUE = "OKX"
PUBLIC_MD_NETWORK_SCOPE = "OKX_EEA_FUTURES_PUBLIC_MARKET_DATA_READ_ONLY"
CANONICAL_INSTRUMENT_ID = "ETH-USD_UM_XPERP-310404"
SESSION_SCOPE = "ADDITIONAL_NATURAL_AGE_EVIDENCE_SESSION_V1"

EXPECTED_VENUE = PUBLIC_MD_VENUE
EXPECTED_INSTRUMENT = CANONICAL_INSTRUMENT_ID
EXPECTED_NETWORK_SCOPE = PUBLIC_MD_NETWORK_SCOPE
EXPECTED_SESSION_SCOPE = SESSION_SCOPE

# Closed-world candidate schema policy (hardening).
CANDIDATE_SCHEMA_CLOSED_WORLD = True
NESTED_OBJECTS_PRESENT = True
UNKNOWN_FIELDS_REJECTED = True
UNKNOWN_AUTHORITY_FIELDS_REJECTED = True
CANDIDATE_SCHEMA_VERSION_EXACT_MATCH = True
VENUE_VALUE_EXACT_MATCH = True
INSTRUMENT_VALUE_EXACT_MATCH = True
NETWORK_SCOPE_VALUE_EXACT_MATCH = True
SESSION_SCOPE_VALUE_EXACT_MATCH = True
NORMALIZATION_OF_BINDING_VALUES_FORBIDDEN = True
BINDING_VALUE_NORMALIZATION_FORBIDDEN = True

AUTHORITY_NEGATIVE_CONTRACT_VERSION = (
    "canonical_volatility_numeric_max_age_additional_evidence_"
    "session_candidate_authority_negative/v1"
)

FORBIDDEN_AUTHORITY_FIELD_NAMES: tuple[str, ...] = (
    "trading_decision_authority",
    "numeric_max_age_selection_authority",
    "numeric_max_age_enforcement_authority",
    "authorization_issuance_authority",
    "authorization_consumption_authority",
    "session_execution_authority",
    "order_routing_authority",
    "live_trading_authority",
    "second_age_authority",
    "second_decision_authority",
)

ALLOWED_CANDIDATE_TOP_LEVEL_FIELDS: tuple[str, ...] = (
    "age_7200_observation_required",
    "authorization_binding",
    "authorization_required",
    "campaign_id",
    "design_digest",
    "duration_seconds",
    "evidence_write_authorized",
    "execution_authorized",
    "first_produce_required",
    "forbidden_artificial_controls",
    "instrument",
    "maximum_cycles_per_session",
    "maximum_requests_per_cycle",
    "maximum_requests_per_session",
    "minimum_interval_seconds",
    "multiple_market_regimes_required",
    "natural_age_progression_required",
    "network_authorized",
    "network_scope",
    "post_first_produce_event_span_seconds",
    "post_recompute_fresh_observation_required",
    "preregistration_digest",
    "recompute_after_age_floor_required",
    "repository_sha",
    "runbook_digest",
    "schema_name",
    "schema_version",
    "session_id",
    "session_preregistration_creation_authorized",
    "session_scope",
    "single_use_authorization_required",
    "target_age_buckets_seconds",
    "venue",
)

ALLOWED_AUTHORIZATION_BINDING_FIELDS: tuple[str, ...] = (
    "authorization_consumption_authorized",
    "authorization_issuance_authorized",
    "authorization_required",
    "campaign_id",
    "design_digest",
    "maximum_session_count",
    "repository_sha",
    "runbook_digest",
    "s01_s02_authorization_reuse_forbidden",
    "session_ids",
    "single_use_authorization_required",
)

# Hard non-goals / authority flags
SESSION_PREREGISTRATION_CREATION_AUTHORIZED = False
AUTHORIZATION_ISSUANCE_AUTHORIZED = False
AUTHORIZATION_CONSUMPTION_AUTHORIZED = False
NETWORK_ACCESS_AUTHORIZED = False
PRODUCTIVE_SESSION_EXECUTION_AUTHORIZED = False
NUMERIC_MAX_AGE_SELECTED = False
NUMERIC_MAX_AGE_ENFORCING = False
MASTER_V2_LOGIC_CHANGED = False
DOUBLE_PLAY_LOGIC_CHANGED = False
ENTRY_EXIT_PRECEDENCE_CHANGED = False
RISK_SAFETY_SEMANTICS_CHANGED = False
SECOND_AGE_AUTHORITY_PRESENT = False
SECOND_DECISION_AUTHORITY_PRESENT = False
TRADING_DECISION_AUTHORITY_PRESENT = False
NUMERIC_MAX_AGE_SELECTION_AUTHORITY_PRESENT = False
NUMERIC_MAX_AGE_ENFORCEMENT_AUTHORITY_PRESENT = False
AUTHORIZATION_ISSUANCE_AUTHORITY_PRESENT = False
AUTHORIZATION_CONSUMPTION_AUTHORITY_PRESENT = False
SESSION_EXECUTION_AUTHORITY_PRESENT = False
ORDER_ROUTING_AUTHORITY_PRESENT = False
HARD_STOP = True
READY_FOR_ADDITIONAL_SESSION_PREREGISTRATION = False
READY_FOR_AUTHORIZATION_ISSUANCE = False
READY_FOR_PRODUCTIVE_SESSION_EXECUTION = False
READY_FOR_NUMERIC_MAX_AGE_POLICY_DECISION = False
PREREGISTRATION_CREATED = False
AUTHORIZATION_ISSUED = False
SESSION_EXECUTED = False

ARTIFICIAL_DELAY_INJECTION = False
SYNTHETIC_EVENT_TIME_ADVANCE = False
AGE_OVERRIDE = False
AS_OF_OVERRIDE = False
RECOMPUTE_FORCE_FLAG = False
LIFECYCLE_STATE_EDIT = False
EVIDENCE_BACKFILL = False

FORBIDDEN_ARTIFICIAL_FLAGS: tuple[str, ...] = (
    "ARTIFICIAL_DELAY_INJECTION",
    "SYNTHETIC_EVENT_TIME_ADVANCE",
    "AGE_OVERRIDE",
    "AS_OF_OVERRIDE",
    "RECOMPUTE_FORCE_FLAG",
    "LIFECYCLE_STATE_EDIT",
    "EVIDENCE_BACKFILL",
)

ALLOWED_FORBIDDEN_ARTIFICIAL_CONTROLS_FIELDS: tuple[str, ...] = FORBIDDEN_ARTIFICIAL_FLAGS

OPERATOR_WORKFLOW: tuple[str, ...] = (
    "CONTRACT_CAPABILITY_MERGE",
    "CREATE_ADDITIONAL_SESSION_PREREGISTRATION",
    "ISSUE_SESSION_SPECIFIC_AUTHORIZATION",
    "EXECUTE_EXACTLY_ONE_SESSION",
    "VERIFY_TERMINAL_EVIDENCE",
    "REPEAT_FOR_SECOND_SESSION",
    "DERIVE_NUMERIC_MAX_AGE_EVIDENCE",
    "POLICY_DECISION_SEPARATE",
)

REQUIRED_CANDIDATE_FIELDS: tuple[str, ...] = (
    "schema_name",
    "schema_version",
    "campaign_id",
    "session_id",
    "repository_sha",
    "design_digest",
    "runbook_digest",
    "preregistration_digest",
    "venue",
    "instrument",
    "network_scope",
    "session_scope",
    "duration_seconds",
    "maximum_cycles_per_session",
    "maximum_requests_per_session",
    "minimum_interval_seconds",
    "maximum_requests_per_cycle",
    "target_age_buckets_seconds",
    "first_produce_required",
    "natural_age_progression_required",
    "age_7200_observation_required",
    "recompute_after_age_floor_required",
    "post_recompute_fresh_observation_required",
    "multiple_market_regimes_required",
    "authorization_required",
    "single_use_authorization_required",
    "post_first_produce_event_span_seconds",
    "authorization_binding",
    "forbidden_artificial_controls",
    "session_preregistration_creation_authorized",
    "execution_authorized",
    "network_authorized",
    "evidence_write_authorized",
)

COVERAGE_REQUIREMENTS: dict[str, bool | int] = {
    "minimum_additional_productive_sessions": MINIMUM_ADDITIONAL_PRODUCTIVE_SESSIONS,
    "multiple_market_regimes_required": True,
    "multiple_time_windows_required": True,
    "fresh_aged_recompute_pair_required": True,
    "post_recompute_fresh_required": True,
    "decision_sensitivity_evidence_required": True,
    "exit_risk_safety_independence_evidence_required": True,
}

AUTHORITY_NEGATIVE_CONTRACT: dict[str, object] = {
    "version": AUTHORITY_NEGATIVE_CONTRACT_VERSION,
    "trading_decision_authority_present": TRADING_DECISION_AUTHORITY_PRESENT,
    "numeric_max_age_selection_authority_present": (NUMERIC_MAX_AGE_SELECTION_AUTHORITY_PRESENT),
    "numeric_max_age_enforcement_authority_present": (
        NUMERIC_MAX_AGE_ENFORCEMENT_AUTHORITY_PRESENT
    ),
    "authorization_issuance_authority_present": AUTHORIZATION_ISSUANCE_AUTHORITY_PRESENT,
    "authorization_consumption_authority_present": (AUTHORIZATION_CONSUMPTION_AUTHORITY_PRESENT),
    "session_execution_authority_present": SESSION_EXECUTION_AUTHORITY_PRESENT,
    "order_routing_authority_present": ORDER_ROUTING_AUTHORITY_PRESENT,
    "second_age_authority_present": SECOND_AGE_AUTHORITY_PRESENT,
    "second_decision_authority_present": SECOND_DECISION_AUTHORITY_PRESENT,
    "forbidden_authority_field_names": list(FORBIDDEN_AUTHORITY_FIELD_NAMES),
}

ARTIFACT_RELATIVE_PATH = (
    "config/research/"
    "canonical_volatility_numeric_max_age_additional_evidence_"
    "session_preregistration_contract_v1.json"
)
SPEC_RELATIVE_PATH = (
    "docs/ops/specs/"
    "MASTER_V2_CANONICAL_VOLATILITY_NUMERIC_MAX_AGE_ADDITIONAL_EVIDENCE_"
    "SESSION_PREREGISTRATION_CONTRACT_V1.md"
)
HARDENING_SPEC_RELATIVE_PATH = (
    "docs/ops/specs/"
    "MASTER_V2_CANONICAL_VOLATILITY_NUMERIC_MAX_AGE_ADDITIONAL_EVIDENCE_"
    "SESSION_CONTRACT_HARDENING_V1.md"
)

FORBIDDEN_IMPORT_SUBSTRINGS: tuple[str, ...] = (
    "execution.live",
    "place_order",
    "submit_order",
    "broker_adapter",
    "trading.master_v2",
    "trading.double_play",
    "risk.",
    "safety.",
)
