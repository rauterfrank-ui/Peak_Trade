"""Constants for additional evidence session preregistration contract v2.

Resolves repository SHA semantics:

* code_baseline_sha — immutable ancestor baseline (not tip-of-main equality)
* artifact_creation_sha — provenance only
* execution_repository_sha — dynamic readiness input

Does not issue/consume authorization or execute sessions.
"""

from __future__ import annotations

PACKAGE_MARKER = (
    "MASTER_V2_CANONICAL_VOLATILITY_NUMERIC_MAX_AGE_ADDITIONAL_EVIDENCE_"
    "REPOSITORY_SHA_SEMANTICS_RESOLUTION_V1=true"
)

CAPABILITY_ID = (
    "MASTER_V2_CANONICAL_VOLATILITY_NUMERIC_MAX_AGE_ADDITIONAL_EVIDENCE_"
    "REPOSITORY_SHA_SEMANTICS_RESOLUTION_V1"
)
REVIEW_MODE_ID = CAPABILITY_ID
CAPABILITY_VERSION = (
    "canonical_volatility_numeric_max_age_additional_evidence_session_preregistration_contract/v2"
)
OWNER = (
    "research.canonical_volatility_numeric_max_age_additional_evidence_"
    "session_preregistration_contract_v2"
)

SCHEMA_NAME = (
    "canonical_volatility_numeric_max_age_additional_evidence_session_preregistration_contract"
)
SCHEMA_VERSION = "v2"
CONTRACT_VERSION = CAPABILITY_VERSION
CANDIDATE_SCHEMA_NAME = (
    "canonical_volatility_numeric_max_age_additional_evidence_session_preregistration_candidate"
)
CANDIDATE_SCHEMA_VERSION = (
    "canonical_volatility_numeric_max_age_additional_evidence_session_preregistration_candidate/v2"
)

# Deprecated/unsupported for new authorization readiness.
V1_CONTRACT_VERSION = (
    "canonical_volatility_numeric_max_age_additional_evidence_session_preregistration_contract/v1"
)
V1_CANDIDATE_SCHEMA_VERSION = (
    "canonical_volatility_numeric_max_age_additional_evidence_session_preregistration_candidate/v1"
)

REPOSITORY_BINDING_MODE = "IMMUTABLE_ANCESTOR_SHA"
KNOWN_REPOSITORY_BINDING_MODES: tuple[str, ...] = (REPOSITORY_BINDING_MODE,)
ARTIFACT_CREATION_SHA_ROLE = "PROVENANCE_ONLY"
EXECUTION_SHA_ROLE = "DYNAMIC_READINESS_INPUT"
TIP_OF_MAIN_EQUALITY_REQUIRED = False
SELF_COMMIT_SHA_EMBEDDING_REQUIRED = False
V1_NEW_AUTHORIZATION_READINESS_ALLOWED = False
REPOSITORY_SHA_FIELD_STATUS = "REMOVED_FROM_V2_USE_CODE_BASELINE_SHA"
SUPERSEDED_PR_5629 = True

# Immutable reviewed code baseline at capability start (origin/main tip).
# Must remain an ancestor of later execution SHAs; never tip-equality authority.
DEFAULT_CODE_BASELINE_SHA = "790065c2417a0006bef97b3496bfef30739e9ff3"

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

CANDIDATE_SCHEMA_CLOSED_WORLD = True
NESTED_OBJECTS_PRESENT = True
UNKNOWN_FIELDS_REJECTED = True
UNKNOWN_AUTHORITY_FIELDS_REJECTED = True
CANDIDATE_SCHEMA_VERSION_EXACT_MATCH = True
VENUE_VALUE_EXACT_MATCH = True
INSTRUMENT_VALUE_EXACT_MATCH = True
NETWORK_SCOPE_VALUE_EXACT_MATCH = True
SESSION_SCOPE_VALUE_EXACT_MATCH = True
BINDING_VALUE_NORMALIZATION_FORBIDDEN = True

AUTHORITY_NEGATIVE_CONTRACT_VERSION = (
    "canonical_volatility_numeric_max_age_additional_evidence_"
    "session_candidate_authority_negative/v2"
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
    "artifact_creation_sha",
    "authorization_binding",
    "authorization_required",
    "campaign_id",
    "code_baseline_sha",
    "critical_surface_manifest_digest",
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
    "repository_binding_mode",
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
    "code_baseline_sha",
    "critical_surface_manifest_digest",
    "design_digest",
    "maximum_session_count",
    "repository_binding_mode",
    "runbook_digest",
    "s01_s02_authorization_reuse_forbidden",
    "session_ids",
    "single_use_authorization_required",
)

ALLOWED_CONTRACT_TOP_LEVEL_FIELDS: tuple[str, ...] = (
    "age_7200_observation_required",
    "allowed_authorization_binding_fields",
    "allowed_candidate_top_level_fields",
    "allowed_forbidden_artificial_controls_fields",
    "artifact_creation_sha",
    "authority_negative_contract",
    "authorization_binding_schema",
    "authorization_consumption_authorized",
    "authorization_issuance_authorized",
    "authorization_per_session_required",
    "binding_value_normalization_forbidden",
    "candidate_schema_closed_world",
    "candidate_schema_name",
    "candidate_schema_version",
    "capability_id",
    "capability_version",
    "code_baseline_sha",
    "contract_digest",
    "coverage_requirements",
    "critical_surface_manifest_digest",
    "critical_surface_manifest_path",
    "design_digest",
    "exhausted_campaign_id",
    "exhausted_campaign_maximum_session_count",
    "exhausted_session_ids",
    "expected_instrument",
    "expected_network_scope",
    "expected_session_scope",
    "expected_venue",
    "forbidden_artificial_controls",
    "hard_stop",
    "maximum_requests_per_cycle",
    "minimum_additional_productive_sessions",
    "minimum_interval_seconds",
    "minimum_maximum_cycles_per_session",
    "minimum_maximum_requests_per_session",
    "minimum_post_first_produce_event_span_seconds",
    "minimum_session_duration_seconds",
    "nested_objects_present",
    "network_access_authorized",
    "numeric_max_age_enforcing",
    "numeric_max_age_selected",
    "operator_workflow",
    "post_recompute_fresh_required",
    "productive_session_execution_authorized",
    "ready_for_additional_session_preregistration",
    "ready_for_authorization_issuance",
    "ready_for_productive_session_execution",
    "recompute_after_age_floor_required",
    "recommended_maximum_cycles_per_session",
    "recommended_maximum_requests_per_session",
    "repository_binding_mode",
    "repository_sha_field_status",
    "required_candidate_fields",
    "runbook_digest",
    "schema_name",
    "schema_version",
    "self_commit_sha_embedding_required",
    "session_preregistration_creation_authorized",
    "single_use_authorization_required",
    "superseded_pr_5629",
    "target_age_buckets_seconds",
    "tip_of_main_equality_required",
    "unknown_authority_fields_rejected",
    "unknown_fields_rejected",
    "v1_new_authorization_readiness_allowed",
)

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
HARD_STOP = True
READY_FOR_ADDITIONAL_SESSION_PREREGISTRATION = False
READY_FOR_AUTHORIZATION_ISSUANCE = False
READY_FOR_PRODUCTIVE_SESSION_EXECUTION = False

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
    "CONTRACT_V2_CAPABILITY_MERGE",
    "CREATE_ADDITIONAL_SESSION_PREREGISTRATION_V2",
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
    "code_baseline_sha",
    "artifact_creation_sha",
    "critical_surface_manifest_digest",
    "repository_binding_mode",
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
    "trading_decision_authority_present": False,
    "numeric_max_age_selection_authority_present": False,
    "numeric_max_age_enforcement_authority_present": False,
    "authorization_issuance_authority_present": False,
    "authorization_consumption_authority_present": False,
    "session_execution_authority_present": False,
    "order_routing_authority_present": False,
    "second_age_authority_present": False,
    "second_decision_authority_present": False,
    "forbidden_authority_field_names": list(FORBIDDEN_AUTHORITY_FIELD_NAMES),
}

PACKAGE_RELATIVE_DIR = (
    "src/research/canonical_volatility_numeric_max_age_additional_evidence_"
    "session_preregistration_contract_v2"
)

# Contract/preregistration JSON artifacts embed this digest and must not be
# included in the digested path set (acyclic). Manifest lists paths only.
# Paths must remain lexicographically sorted.
CRITICAL_SURFACE_PATHS: tuple[str, ...] = tuple(
    sorted(
        (
            (
                "config/research/canonical_volatility_numeric_max_age_additional_evidence_"
                "critical_surface_manifest_v2.json"
            ),
            f"{PACKAGE_RELATIVE_DIR}/__init__.py",
            f"{PACKAGE_RELATIVE_DIR}/architecture_guards_v2.py",
            f"{PACKAGE_RELATIVE_DIR}/authorization_binding_v2.py",
            f"{PACKAGE_RELATIVE_DIR}/constants_v2.py",
            f"{PACKAGE_RELATIVE_DIR}/contract_v2.py",
            f"{PACKAGE_RELATIVE_DIR}/critical_surface_v2.py",
            f"{PACKAGE_RELATIVE_DIR}/git_binding_v2.py",
            f"{PACKAGE_RELATIVE_DIR}/models_v2.py",
            f"{PACKAGE_RELATIVE_DIR}/readiness_v2.py",
            f"{PACKAGE_RELATIVE_DIR}/uniqueness_v2.py",
            f"{PACKAGE_RELATIVE_DIR}/validate_v2.py",
        )
    )
)

CRITICAL_SURFACE_MANIFEST_RELATIVE_PATH = (
    "config/research/canonical_volatility_numeric_max_age_additional_evidence_"
    "critical_surface_manifest_v2.json"
)
ARTIFACT_RELATIVE_PATH = (
    "config/research/canonical_volatility_numeric_max_age_additional_evidence_"
    "session_preregistration_contract_v2.json"
)
PREREGISTRATION_RELATIVE_PATH = (
    "config/research/canonical_volatility_numeric_max_age_additional_evidence_"
    "session_preregistration_v2.json"
)
SPEC_RELATIVE_PATH = (
    "docs/ops/specs/"
    "MASTER_V2_CANONICAL_VOLATILITY_NUMERIC_MAX_AGE_ADDITIONAL_EVIDENCE_"
    "REPOSITORY_SHA_SEMANTICS_RESOLUTION_V1.md"
)
V1_SPEC_RELATIVE_PATH = (
    "docs/ops/specs/"
    "MASTER_V2_CANONICAL_VOLATILITY_NUMERIC_MAX_AGE_ADDITIONAL_EVIDENCE_"
    "SESSION_PREREGISTRATION_CONTRACT_V1.md"
)

FULL_GIT_SHA_LENGTH = 40
FULL_GIT_SHA_HEX_RE = r"^[0-9a-f]{40}$"

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

ACTIVE_V2_PREREGISTRATION_COUNT_REQUIRED = 1
