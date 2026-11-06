"""Constants for Phase 9.2 Step-6 adverse/stale-data session continuation binding."""

from __future__ import annotations

from pathlib import Path

CAPABILITY_ID = "PHASE_9_2_STEP_6_ADVERSE_STALE_DATA_SESSION_CONTINUATION_V1"
SCHEMA_VERSION = "phase_9_2_step_6_adverse_stale_data_session_continuation.v1"
PRODUCER_VERSION = SCHEMA_VERSION
PACKAGE_MARKER = "PHASE_9_2_STEP_6_ADVERSE_STALE_DATA_SESSION_CONTINUATION_V1=true"
OWNER = "ops.phase_9_2_step_6_adverse_stale_data_session_continuation_v1"
AUTHORITY_OWNER = OWNER

PREDECESSOR_CAPABILITY_ID = (
    "PHASE_9_2_STEP_5_PRODUCTIVE_SESSION_EVIDENCE_SEAL_AND_PRODUCTIVE_VERIFIER_V1"
)
SESSION_LADDER_STEP = "ADVERSE_STALE_DATA_SESSION"
SESSION_SCOPE = "PHASE_9_2_ADVERSE_STALE_DATA_SESSION"

CONFIG_RELATIVE_PATH = "config/ops/phase_9_2_step_6_adverse_stale_data_session_continuation_v1.json"
SESSION_CONTRACT_RELATIVE_PATH = (
    "config/ops/phase_9_2_public_md_adverse_stale_data_session_contract_v1.json"
)
EVIDENCE_DIRNAME = "capability_phase_9_2_step_6_adverse_stale_data_session_continuation_v1"
CAPABILITY_DOC_RELATIVE_PATH = (
    "docs/ops/specs/CAPABILITY_PHASE_9_2_STEP_6_ADVERSE_STALE_DATA_SESSION_CONTINUATION_V1.md"
)

PRODUCTIVE_ENTRYPOINT_ID = CAPABILITY_ID
PRODUCTIVE_ENTRYPOINT_PATH = (
    "scripts/ops/run_phase_9_2_step_6_adverse_stale_data_session_continuation_v1.py"
)
PRODUCTIVE_STEP6_EXECUTOR = (
    "ops.phase_9_2_step_6_adverse_stale_data_session_continuation_v1.productive_executor_v1"
)
FAILURE_INJECTION_SURFACE = (
    "ops.phase_9_2_step_6_adverse_stale_data_session_continuation_v1."
    "governed_injected_stale_data_fault_v1"
)
VERIFIER_PATH = "ops.phase_9_2_step_6_adverse_stale_data_session_continuation_v1.verifier_v1"
EVIDENCE_ROOT_RELATIVE = f"docs/evidence/{EVIDENCE_DIRNAME}"

TARGET_SESSION_ID = "phase_9_2_public_md_adverse_stale_data_session_v1"
RUNTIME_SESSION_ID = "phase_9_2_adverse_stale_data_runtime_session_v1"
CAMPAIGN_ID = "phase_9_2_adverse_stale_data_campaign_v1"
CONFIRMATION_SESSION_ID = "phase_9_2_adverse_stale_data_confirmation_session_v1"
CANONICAL_INSTRUMENT_ID = "ETH-USD_UM_XPERP-310404"

# Bounded adverse/stale proof duration (not prolonged Step-5).
MIN_WALLCLOCK_DURATION_SECONDS = 180
DEFAULT_WALLCLOCK_DURATION_SECONDS = 600
MAX_WALLCLOCK_DURATION_SECONDS = 3600
DURATION_AUTHORITY = "MONOTONIC_CLOCK"

CANONICAL_WALLCLOCK_RUNNER = (
    "src.ops.integrated_paper_shadow_productive_authorization_issuance_and_real_network_"
    "execution_v1.productive_run_entrypoint_v1.run_productive_wallclock_session_v1"
)
PACING_POLICY_OWNER = (
    "research.canonical_volatility_numeric_max_age_preregistered_productive_session_runner_v1."
    "public_md_rate_limit_policy_v1"
)
EEA_TRANSPORT_OWNER = "ops.integrated_paper_shadow_observation_wallclock_session_execution_v1.eea_public_md_transport_v1"
SESSION_RUNTIME_OWNER = (
    "ops.integrated_paper_shadow_observation_wallclock_session_execution_v1.session_runtime_v1"
)
STALENESS_OWNER = (
    "ops.integrated_paper_shadow_observation_wallclock_session_execution_v1.heartbeat_staleness_v1"
)
STALE_DATA_CLASSIFIER = f"{STALENESS_OWNER}.StalenessTrackerV1"
KILLSTATE_OWNER = (
    "ops.integrated_paper_shadow_observation_wallclock_session_execution_v1.killstate_runtime_v1"
)
ADVERSE_DATA_CLASSIFIER = f"{KILLSTATE_OWNER}.STALE_DATA"
BUNDLE_VERIFIER_OWNER = (
    "ops.integrated_paper_shadow_observation_wallclock_session_execution_v1.bundle_verifier_v1"
)
STEP4_BINDING_OWNER = "ops.phase_9_2_productive_public_md_rate_limit_reconnect_wallclock_binding_v1"
STEP5_BINDING_OWNER = (
    "ops.phase_9_2_productive_public_md_prolonged_natural_market_wallclock_binding_v1"
)
STEP5_EXECUTOR_OWNER = (
    "ops.phase_9_2_step_5_governed_productive_real_network_prolonged_natural_market_"
    "session_execution_v1"
)

NETWORK_SESSION_ALLOWED = False
AUTHORIZATION_ISSUANCE_ALLOWED = False
AUTHORIZATION_CONSUMPTION_ALLOWED = False
CONFIRM_TOKEN_CONSUMPTION_ALLOWED = False
FAULT_SESSION_EXECUTION_AUTHORIZED = False
PRODUCTIVE_NETWORK_SESSION_EXECUTION_AUTHORIZED = False
NO_PERMANENT_UNSCOPED_ENABLE_FLAG = True
READY_FOR_SEPARATE_GOVERNED_SESSION_EXECUTION = True
ADVERSE_STALE_DATA_LADDER_STEP_CLOSED = False
CAPABILITY_CLOSED = False
PHASE_9_2_STEP_6_STATUS = "OPEN"
NEXT_OPEN_PHASE_9_2_STEP = "6_ADVERSE_STALE_DATA_SESSION"

GOVERNED_PUBLIC_MD_NETWORK_SCOPE = "okx_eea_futures_public_md_observe_v1"
EEA_PUBLIC_MD_HOST = "eea.okx.com"
NETWORK_ALLOWLIST = "OKX_EEA_PUBLIC_MARKET_DATA_ENDPOINTS_ONLY"
HTTP_METHOD_ALLOWLIST = "GET_ONLY"

SESSION_EVIDENCE_SCHEMA_VERSION = "phase_9_2_adverse_stale_data_session_evidence.v1"
BINDING_MANIFEST_FILENAME = "adverse_stale_data_session_continuation_manifest_v1.json"

CORE_LOGIC_CHANGE = False
MASTER_V2_CHANGE = False
DOUBLE_PLAY_CHANGE = False
BULL_BEAR_CHANGE = False
DYNAMIC_SCOPE_LOGIC_CHANGE = False
CONFIRMATION_SEMANTICS_CHANGE = False
RISK_CHANGE = False
SAFETY_CHANGE = False
FORCED_INTENT_ALLOWED = False
DIRECT_FILL_INJECTION_ALLOWED = False
MASTER_V2_BYPASS_ALLOWED = False
DOUBLE_PLAY_BYPASS_ALLOWED = False
COMPOSITION_BYPASS_ALLOWED = False
RISK_BYPASS_ALLOWED = False
SAFETY_BYPASS_ALLOWED = False
DASHBOARD_AUTHORITY_EFFECT = "NONE"
DASHBOARD_READ_ONLY_CONSUMER = True
DASHBOARD_FILES_CHANGED = False
PRESENTATION_LAYER_CHANGED = False

NO_PARALLEL_STALENESS_MODEL = True
NO_PARALLEL_KILLSTATE_MODEL = True
NO_PARALLEL_SESSION_MODEL = True
NO_PARALLEL_EVIDENCE_MODEL = True

SESSION_EVIDENCE_REQUIRED_FIELDS = (
    "schema_version",
    "repository_sha",
    "config_digest",
    "session_id",
    "confirmation_session_id",
    "distinct_observation_count",
    "duplicate_observation_count",
    "stale_observation_count",
    "confirmation_advance_count",
    "stale_confirmation_advance_count",
    "duplicate_confirmation_advance_count",
    "fill_count",
    "fabricated_observation_count",
    "retry_count",
    "backoff_timeline",
    "minimum_request_interval_seconds",
    "private_endpoint_reachable",
    "credential_access_reachable",
    "order_side_effect_occurred",
    "claims",
    "verifier_result",
)

MANDATORY_TELEMETRY_FIELDS = (
    "distinct_observation_count",
    "duplicate_observation_count",
    "stale_observation_count",
    "confirmation_advance_count",
    "stale_confirmation_advance_count",
    "duplicate_confirmation_advance_count",
    "fill_count",
    "fabricated_observation_count",
    "retry_count",
    "backoff_count",
    "http_request_count",
    "stale_gate_activation_count",
    "killstate_trigger",
    "verifier_result",
)


def repo_root_v1() -> Path:
    return Path(__file__).resolve().parents[3]
