"""Constants for Phase 9.2 prolonged natural-market wallclock binding."""

from __future__ import annotations

from pathlib import Path

CAPABILITY_ID = "PHASE_9_2_PRODUCTIVE_PUBLIC_MD_PROLONGED_NATURAL_MARKET_WALLCLOCK_BINDING_V1"
SCHEMA_VERSION = "phase_9_2_productive_public_md_prolonged_natural_market_wallclock_binding.v1"
PRODUCER_VERSION = SCHEMA_VERSION
PACKAGE_MARKER = "PHASE_9_2_PRODUCTIVE_PUBLIC_MD_PROLONGED_NATURAL_MARKET_WALLCLOCK_BINDING_V1=true"
OWNER = "ops.phase_9_2_productive_public_md_prolonged_natural_market_wallclock_binding_v1"
AUTHORITY_OWNER = OWNER

PREDECESSOR_CAPABILITY_ID = (
    "PHASE_9_2_PRODUCTIVE_PUBLIC_MD_RATE_LIMIT_RECONNECT_WALLCLOCK_BINDING_V1"
)
SESSION_LADDER_STEP = "PROLONGED_NATURAL_MARKET_SESSION"
SESSION_SCOPE = "PHASE_9_2_PROLONGED_NATURAL_MARKET_SESSION"

CONFIG_RELATIVE_PATH = (
    "config/ops/phase_9_2_productive_public_md_prolonged_natural_market_wallclock_binding_v1.json"
)
SESSION_CONTRACT_RELATIVE_PATH = (
    "config/ops/phase_9_2_public_md_prolonged_natural_market_session_contract_v1.json"
)
EVIDENCE_DIRNAME = (
    "capability_phase_9_2_productive_public_md_prolonged_natural_market_wallclock_binding_v1"
)

PRODUCTIVE_ENTRYPOINT_ID = CAPABILITY_ID
PRODUCTIVE_ENTRYPOINT_PATH = "scripts/ops/run_phase_9_2_productive_public_md_prolonged_natural_market_wallclock_binding_v1.py"
BINDING_CLI_PATH = PRODUCTIVE_ENTRYPOINT_PATH

TARGET_SESSION_ID = "phase_9_2_public_md_prolonged_natural_market_session_v1"
RUNTIME_SESSION_ID = "phase_9_2_prolonged_natural_market_runtime_session_v1"
CAMPAIGN_ID = "phase_9_2_prolonged_natural_market_campaign_v1"
CONFIRMATION_SESSION_ID = "phase_9_2_prolonged_natural_market_confirmation_session_v1"
CANONICAL_INSTRUMENT_ID = "ETH-USD_UM_XPERP-310404"

SESSION_GO_SCHEMA_VERSION = "phase_9_2_productive_prolonged_natural_market_session_go.v1"

# Prolonged duration bounds (monotonic authority for budgets).
MIN_WALLCLOCK_DURATION_SECONDS = 7200
DEFAULT_WALLCLOCK_DURATION_SECONDS = 7200
MAX_WALLCLOCK_DURATION_SECONDS = 21600
DEFAULT_MAX_SESSION_DURATION_SECONDS = MAX_WALLCLOCK_DURATION_SECONDS
DURATION_AUTHORITY = "MONOTONIC_CLOCK"
WALL_CLOCK_ROLE = "OPERATOR_PLANNING_AND_AUTHORIZATION_EXPIRY_ONLY"

# Step-5-specific disk / evidence growth bounds.
MAX_EVIDENCE_BYTES = 536870912  # 512 MiB
MAX_EVIDENCE_GROWTH_BYTES_PER_MINUTE = 2097152  # 2 MiB/min
DISK_FREE_MINIMUM_BYTES_BEFORE = 1610612736  # 1.5 GiB
DISK_RESERVE_BYTES = 1073741824  # 1.0 GiB
MAX_RESTART_COUNT = 1
MAX_RECOVERY_COUNT = 1
MAX_CONSECUTIVE_TRANSPORT_ERRORS = 3
SHUTDOWN_GRACE_SECONDS = 30.0

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
SESSION_LOCK_OWNER = (
    "ops.integrated_paper_shadow_observation_wallclock_session_execution_v1.session_lock_v1"
)
STEP4_BINDING_OWNER = "ops.phase_9_2_productive_public_md_rate_limit_reconnect_wallclock_binding_v1"
STEP3_BINDING_OWNER = (
    "ops.phase_9_2_productive_public_md_restart_recovery_real_network_wallclock_binding_v1"
)

NETWORK_SESSION_ALLOWED_BY_CAPABILITY_CONFIG = False
AUTHORIZATION_ISSUANCE_ALLOWED_BY_CAPABILITY_CONFIG = False
AUTHORIZATION_CONSUMPTION_ALLOWED_BY_CAPABILITY_CONFIG = False
PRODUCTIVE_NETWORK_SESSION_EXECUTION_AUTHORIZED = False
FAULT_SESSION_EXECUTION_AUTHORIZED = False
NO_PERMANENT_UNSCOPED_ENABLE_FLAG = True
NETWORK_SESSION_ALLOWED = False
FAULT_SESSION_ALLOWED = False
PRODUCTIVE_SESSION_REACHABLE = True
READY_FOR_PRODUCTIVE_SESSION_EXECUTION = True
PROLONGED_NATURAL_MARKET_LADDER_STEP_CLOSED = False
CAPABILITY_CLOSED = False

GOVERNED_PUBLIC_MD_NETWORK_SCOPE = "okx_eea_futures_public_md_observe_v1"
GOVERNED_PUBLIC_MD_SESSION_EXECUTION_SCOPE = "paper_shadow_observation_wallclock_v1"
PRODUCTIVE_V2_ARTIFACT_NETWORK_SCOPE = "PUBLIC_MARKET_DATA_ONLY"
EEA_PUBLIC_MD_HOST = "eea.okx.com"
NETWORK_ALLOWLIST = "OKX_EEA_PUBLIC_MARKET_DATA_ENDPOINTS_ONLY"
HTTP_METHOD_ALLOWLIST = "GET_ONLY"

HIDDEN_PTY_CONFIRM_HANDOFF_OWNER = (
    "ops.phase_9_2_productive_public_md_prolonged_natural_market_wallclock_binding_v1."
    "hidden_pty_confirm_handoff_v1"
)

SESSION_EVIDENCE_SCHEMA_VERSION = "phase_9_2_prolonged_natural_market_session_evidence.v1"
BINDING_MANIFEST_FILENAME = "prolonged_natural_market_wallclock_binding_manifest_v1.json"

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

MANDATORY_TELEMETRY_FIELDS = (
    "wallclock_duration_requested",
    "wallclock_duration_observed",
    "monotonic_duration_observed",
    "cycles",
    "distinct_observation_count",
    "duplicate_observation_count",
    "missing_observation_count",
    "out_of_order_observation_count",
    "stale_observation_count",
    "confirmation_phase_transitions",
    "candidate_count",
    "confirmed_count",
    "scope_transition_count",
    "hold_count",
    "entry_intent_count",
    "entry_fill_count",
    "reduce_intent_count",
    "reduce_fill_count",
    "exit_intent_count",
    "exit_fill_count",
    "total_fees",
    "total_slippage",
    "realized_pnl",
    "unrealized_pnl",
    "risk_veto_count",
    "safety_veto_count",
    "heartbeat_count",
    "heartbeat_gap_max",
    "http_request_count",
    "http_429_count",
    "retry_count",
    "backoff_count",
    "reconnect_attempt_count",
    "reconnect_success_count",
    "restart_count",
    "recovery_count",
    "checkpoint_count",
    "evidence_bytes",
    "evidence_growth_rate",
    "disk_free_bytes_before",
    "disk_free_bytes_after",
    "verifier_result",
)

CLAIM_FIELDS = (
    "STEP5_RUNTIME_REACHABLE",
    "STEP5_SESSION_STARTED",
    "STEP5_DURATION_COMPLETED",
    "STEP5_GRACEFUL_STOP_OBSERVED",
    "STEP5_INTERRUPT_RECOVERY_OBSERVED",
    "STEP5_RESTART_RECOVERY_OBSERVED",
    "RECONNECT_PATH_REACHABLE",
    "RECONNECT_NATURALLY_OCCURRED",
    "RECONNECT_OBSERVED",
    "STALE_DATA_NATURALLY_OCCURRED",
    "STALE_DATA_OBSERVED",
    "ENTRY_OBSERVED",
    "REDUCE_OBSERVED",
    "EXIT_OBSERVED",
    "NO_ORDER_BOUNDARY_PROVEN",
    "EVIDENCE_VERIFIED",
    "CAPABILITY_CLOSED",
)

RECONNECT_PATH_STATUS_NOT_NATURAL = "NOT_NATURALLY_OCCURRED_CLASSIFIED"

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
    "min_session_duration_seconds",
    "planned_session_duration_seconds",
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
