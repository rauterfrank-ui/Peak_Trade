"""Constants for Phase 9.2 rate-limit/reconnect wallclock binding."""

from __future__ import annotations

from pathlib import Path

CAPABILITY_ID = "PHASE_9_2_PRODUCTIVE_PUBLIC_MD_RATE_LIMIT_RECONNECT_WALLCLOCK_BINDING_V1"
SCHEMA_VERSION = "phase_9_2_productive_public_md_rate_limit_reconnect_wallclock_binding.v1"
PRODUCER_VERSION = SCHEMA_VERSION
PACKAGE_MARKER = "PHASE_9_2_PRODUCTIVE_PUBLIC_MD_RATE_LIMIT_RECONNECT_WALLCLOCK_BINDING_V1=true"
OWNER = "ops.phase_9_2_productive_public_md_rate_limit_reconnect_wallclock_binding_v1"
AUTHORITY_OWNER = OWNER

PREDECESSOR_CAPABILITY_ID = (
    "PHASE_9_2_PRODUCTIVE_PUBLIC_MD_RESTART_RECOVERY_REAL_NETWORK_WALLCLOCK_BINDING_V1"
)
SESSION_LADDER_STEP = "RATE_LIMIT_RECONNECT_SESSION"
SESSION_SCOPE = "PHASE_9_2_RATE_LIMIT_RECONNECT_SESSION"

CONFIG_RELATIVE_PATH = (
    "config/ops/phase_9_2_productive_public_md_rate_limit_reconnect_wallclock_binding_v1.json"
)
SESSION_CONTRACT_RELATIVE_PATH = (
    "config/ops/phase_9_2_public_md_rate_limit_reconnect_session_contract_v1.json"
)
EVIDENCE_DIRNAME = (
    "capability_phase_9_2_productive_public_md_rate_limit_reconnect_wallclock_binding_v1"
)

PRODUCTIVE_ENTRYPOINT_ID = CAPABILITY_ID
PRODUCTIVE_ENTRYPOINT_PATH = (
    "scripts/ops/run_phase_9_2_productive_public_md_rate_limit_reconnect_wallclock_binding_v1.py"
)
BINDING_CLI_PATH = PRODUCTIVE_ENTRYPOINT_PATH

TARGET_SESSION_ID = "phase_9_2_public_md_rate_limit_reconnect_session_v1"
CAMPAIGN_ID = "phase_9_2_rate_limit_reconnect_campaign_v1"
CONFIRMATION_SESSION_ID = "phase_9_2_rate_limit_reconnect_confirmation_session_v1"
CANONICAL_INSTRUMENT_ID = "ETH-USD_UM_XPERP-310404"

SESSION_GO_SCHEMA_VERSION = "phase_9_2_productive_rate_limit_reconnect_session_go.v1"
DEFAULT_MAX_SESSION_DURATION_SECONDS = 3600

ACTIVATION_STATUS_INACTIVE = "INACTIVE"
ACTIVATION_STATUS_ACTIVE = "ACTIVE"
ACTIVATION_STATUS_EXPIRED = "EXPIRED"
ACTIVATION_STATUS_REVOKED = "REVOKED"
ACTIVATION_STATUSES = (
    ACTIVATION_STATUS_INACTIVE,
    ACTIVATION_STATUS_ACTIVE,
    ACTIVATION_STATUS_EXPIRED,
    ACTIVATION_STATUS_REVOKED,
)

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
RATE_LIMIT_METRIC_OWNER = "ops.phase_9_2_public_md_session_preflight_v1.rate_limit_metric_v1"
BUNDLE_VERIFIER_OWNER = (
    "ops.integrated_paper_shadow_observation_wallclock_session_execution_v1.bundle_verifier_v1"
)
CONFIRM_TOKEN_OWNER = (
    "ops.paper_shadow_observation_operator_go_session_preregistration_v1.confirm_token_v1"
)

NETWORK_SESSION_ALLOWED_BY_CAPABILITY_CONFIG = False
AUTHORIZATION_ISSUANCE_ALLOWED_BY_CAPABILITY_CONFIG = False
AUTHORIZATION_CONSUMPTION_ALLOWED_BY_CAPABILITY_CONFIG = False
PRODUCTIVE_NETWORK_SESSION_EXECUTION_AUTHORIZED = False
FAULT_SESSION_EXECUTION_AUTHORIZED = False
NO_PERMANENT_UNSCOPED_ENABLE_FLAG = True

# Wiring-layer capability: binds productive executor without starting a real session.
WIRING_CAPABILITY_ID = "PHASE_9_2_STEP_4_PRODUCTIVE_REAL_NETWORK_SESSION_EXECUTOR_WIRING_V1"
NETWORK_SESSION_ALLOWED = False
FAULT_SESSION_ALLOWED = False
PRODUCTIVE_SESSION_REACHABLE = True
READY_FOR_PRODUCTIVE_SESSION_EXECUTION = True
RATE_LIMIT_RECONNECT_LADDER_STEP_CLOSED = False
EEA_PUBLIC_MD_HOST = "eea.okx.com"
NETWORK_ALLOWLIST = "OKX_EEA_PUBLIC_MARKET_DATA_ENDPOINTS_ONLY"
HTTP_METHOD_ALLOWLIST = "GET_ONLY"
SESSION_EVIDENCE_SCHEMA_VERSION = "phase_9_2_rate_limit_reconnect_session_evidence.v1"
SESSION_EVIDENCE_REQUIRED_FIELDS = (
    "repository_sha",
    "config_digest",
    "authorization_id_or_digest",
    "session_id",
    "runtime_session_id",
    "confirmation_session_id",
    "started_at",
    "ended_at",
    "public_endpoint_classification",
    "request_count",
    "request_interval_distribution",
    "rate_limit_event_count",
    "rate_limit_classifications",
    "retry_count",
    "backoff_timeline",
    "reconnect_count",
    "reconnect_timeline",
    "stale_state_transitions",
    "heartbeat_state_transitions",
    "duplicate_observation_count",
    "confirmation_advance_count",
    "fill_count",
    "process_health_before",
    "process_health_after",
    "state_digest_before",
    "state_digest_after",
    "private_endpoint_reachable",
    "auth_header_present",
    "credential_access_reachable",
    "order_side_effect_occurred",
    "manifest_digest",
    "verifier_result",
)

BINDING_MANIFEST_FILENAME = "rate_limit_reconnect_wallclock_binding_manifest_v1.json"

CORE_LOGIC_CHANGE = False
MASTER_V2_CHANGE = False
DOUBLE_PLAY_CHANGE = False
BULL_BEAR_CHANGE = False
DYNAMIC_SCOPE_LOGIC_CHANGE = False
CONFIRMATION_SEMANTICS_CHANGE = False
RISK_CHANGE = False
SAFETY_CHANGE = False
DASHBOARD_AUTHORITY_EFFECT = "NONE"
DASHBOARD_READ_ONLY_CONSUMER = True

FORBIDDEN_CONFIRM_TOKEN_ARGV_FLAGS = (
    "--confirm-token",
    "--confirm_token",
    "--confirm-token-plaintext",
)

REAL_NETWORK_ENV = "PEAK_TRADE_PSO_WALLCLOCK_ALLOW_REAL_NETWORK"

SESSION_GO_REQUIRED_FIELDS = (
    "schema_version",
    "capability_id",
    "session_go_id",
    "session_id",
    "expected_repository_sha",
    "expected_config_digest",
    "entrypoint_id",
    "entrypoint_path",
    "public_md_only",
    "http_get_only",
    "max_session_duration_seconds",
    "session_scope",
    "issued_at",
    "not_before",
    "expires_at",
    "activation_status",
    "owner_go_required",
    "owner_session_go_required",
    "single_use_authorization_required",
    "confirm_token_required",
    "network_session_execution_authorized_by_this_go",
    "fixture_non_authoritative",
)

SESSION_GO_KNOWN_FIELDS = frozenset(
    SESSION_GO_REQUIRED_FIELDS
    + (
        "session_go_digest",
        "notes",
    )
)


def repo_root_v1() -> Path:
    return Path(__file__).resolve().parents[3]
