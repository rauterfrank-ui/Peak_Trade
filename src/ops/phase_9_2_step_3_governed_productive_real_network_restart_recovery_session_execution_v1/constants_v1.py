"""Constants for Step-3 governed restart/recovery session execution surface."""

from __future__ import annotations

from pathlib import Path

# This capability implements the productive execution surface only.
CAPABILITY_ID = (
    "PHASE_9_2_STEP_3_GOVERNED_PRODUCTIVE_REAL_NETWORK_"
    "RESTART_RECOVERY_SESSION_EXECUTION_SURFACE_IMPLEMENTATION_V1"
)
# Later separately authorized real-network session runtime (not activated here).
RUNTIME_CAPABILITY_ID = (
    "PHASE_9_2_STEP_3_GOVERNED_PRODUCTIVE_REAL_NETWORK_RESTART_RECOVERY_SESSION_EXECUTION_V1"
)
SCHEMA_VERSION = (
    "phase_9_2_step_3_governed_productive_real_network_"
    "restart_recovery_session_execution_surface.v1"
)
PRODUCER_VERSION = SCHEMA_VERSION
OWNER = (
    "ops.phase_9_2_step_3_governed_productive_real_network_restart_recovery_session_execution_v1"
)
AUTHORITY_OWNER = OWNER

BINDING_CAPABILITY_ID = (
    "PHASE_9_2_PRODUCTIVE_PUBLIC_MD_RESTART_RECOVERY_REAL_NETWORK_WALLCLOCK_BINDING_V1"
)
BINDING_PACKAGE = (
    "ops.phase_9_2_productive_public_md_restart_recovery_real_network_wallclock_binding_v1"
)
HARNESS_PACKAGE = "ops.phase_9_2_restart_recovery_session_contract_and_productive_harness_v1"
SESSION_GO_PACKAGE = "ops.phase_9_2_productive_restart_recovery_session_go_capability_v1"
NETWORK_ENTRYPOINT_PACKAGE = (
    "ops.phase_9_2_productive_public_md_restart_recovery_network_entrypoint_v1"
)

SESSION_LADDER_STEP = "RESTART_RECOVERY_SESSION"
SESSION_SCOPE = "PHASE_9_2_RESTART_RECOVERY_SESSION"
TARGET_SESSION_ID = "phase_9_2_public_md_restart_recovery_session_v1"
RESTART_CAMPAIGN_ID = "phase_9_2_restart_recovery_campaign_v1"
DURABLE_STATE_LINEAGE_ID = "phase_9_2_restart_durable_state_lineage_v1"
CONFIRMATION_SESSION_ID = "phase_9_2_restart_confirmation_session_v1"
CANONICAL_INSTRUMENT_ID = "ETH-USD_UM_XPERP-310404"

CONFIG_RELATIVE_PATH = (
    "config/ops/phase_9_2_step_3_governed_productive_real_network_"
    "restart_recovery_session_execution_v1.json"
)
SESSION_CONTRACT_RELATIVE_PATH = "config/ops/phase_9_2_restart_recovery_session_contract_v1.json"
BINDING_CONFIG_RELATIVE_PATH = "config/ops/phase_9_2_productive_public_md_restart_recovery_real_network_wallclock_binding_v1.json"
BINDING_CLI_PATH = (
    "scripts/ops/run_phase_9_2_productive_public_md_restart_recovery_"
    "real_network_wallclock_binding_v1.py"
)
PRODUCTIVE_ENTRYPOINT_PATH = (
    "scripts/ops/run_phase_9_2_step_3_governed_productive_real_network_"
    "restart_recovery_session_execution_v1.py"
)
EVIDENCE_DIRNAME = (
    "capability_phase_9_2_step_3_governed_productive_real_network_"
    "restart_recovery_session_execution_surface_implementation_v1"
)
CAPABILITY_DOC_RELATIVE_PATH = (
    "docs/ops/specs/CAPABILITY_PHASE_9_2_STEP_3_GOVERNED_PRODUCTIVE_REAL_NETWORK_"
    "RESTART_RECOVERY_SESSION_EXECUTION_SURFACE_IMPLEMENTATION_V1.md"
)

SEGMENT_ROLE_PRE = "PRE_RESTART"
SEGMENT_ROLE_POST = "POST_RESTART"
SEGMENT_PRE_ID = "segment_pre_restart_v1"
SEGMENT_POST_ID = "segment_post_restart_v1"
CONTROLLED_RESTART_EXIT_CODE = 82
EXIT_CODE_82_CLASSIFICATION = "CONTROLLED_SEGMENT_TRANSITION"
MINIMUM_PRE_RESTART_DISTINCT_OBSERVATIONS = 30

CANONICAL_WALLCLOCK_RUNNER = (
    "src.ops.integrated_paper_shadow_productive_authorization_issuance_and_real_network_"
    "execution_v1.productive_run_entrypoint_v1.run_productive_wallclock_session_v1"
)
BUNDLE_VERIFIER_OWNER = (
    "ops.phase_9_2_restart_recovery_session_contract_and_productive_harness_v1.verifier_v1"
)
SEGMENT_RUNNER_OWNER = (
    "ops.phase_9_2_productive_public_md_restart_recovery_real_network_wallclock_binding_v1."
    "segment_runner_v1"
)
CONFIRM_TOKEN_OWNER = (
    "ops.paper_shadow_observation_operator_go_session_preregistration_v1.confirm_token_v1"
)
AUTHORIZATION_ISSUANCE_OWNER = (
    "ops.integrated_paper_shadow_productive_authorization_issuance_and_real_network_"
    "execution_v1.productive_operator_go_producer_v1"
)
PACING_POLICY_OWNER = (
    "research.canonical_volatility_numeric_max_age_preregistered_productive_session_runner_v1."
    "public_md_rate_limit_policy_v1"
)
EEA_TRANSPORT_OWNER = "ops.integrated_paper_shadow_observation_wallclock_session_execution_v1.eea_public_md_transport_v1"
STALENESS_OWNER = (
    "ops.integrated_paper_shadow_observation_wallclock_session_execution_v1.heartbeat_staleness_v1"
)

NETWORK_SESSION_ALLOWED = False
AUTHORIZATION_ISSUANCE_ALLOWED = False
AUTHORIZATION_CONSUMPTION_ALLOWED = False
CONFIRM_TOKEN_ISSUANCE_ALLOWED = False
CONFIRM_TOKEN_CONSUMPTION_ALLOWED = False
SESSION_EXECUTION_SIDE_EFFECTS_AUTHORIZED = False
REAL_NETWORK_REQUESTS_ALLOWED = False
PRODUCTIVE_NETWORK_SESSION_EXECUTION_AUTHORIZED = False
NO_PERMANENT_UNSCOPED_ENABLE_FLAG = True

GOVERNED_PUBLIC_MD_NETWORK_SCOPE = "okx_eea_futures_public_md_observe_v1"
NETWORK_ALLOWLIST = "OKX_EEA_PUBLIC_MARKET_DATA_ENDPOINTS_ONLY"
HTTP_METHOD_ALLOWLIST = "GET_ONLY"
NETWORK_MODE = "PUBLIC_MD_GET_ONLY"
EEA_PUBLIC_MD_HOST = "eea.okx.com"

MIN_REQUEST_INTERVAL_SECONDS = 2.0
MAX_RETRY_ATTEMPTS = 3
BACKOFF_BASE_SECONDS = 1.0
BACKOFF_MAX_SECONDS = 30.0
ZERO_INTERVAL_RETRY_FORBIDDEN = True

FORBIDDEN_CONFIRM_TOKEN_ARGV_FLAGS = (
    "--confirm-token",
    "--confirm_token",
    "--confirm-token-plaintext",
)
FORBIDDEN_CONFIRM_TOKEN_ENV_KEYS = (
    "PEAK_TRADE_STEP3_CONFIRM_TOKEN",
    "CONFIRM_TOKEN",
    "CONFIRM_TOKEN_PLAINTEXT",
)

SESSION_MANIFEST_SCHEMA = "phase_9_2_step_3_governed_restart_recovery_session_execution_manifest.v1"

CORE_LOGIC_CHANGE = False
MASTER_V2_CHANGE = False
DOUBLE_PLAY_CHANGE = False
BULL_BEAR_CHANGE = False
DYNAMIC_SCOPE_LOGIC_CHANGE = False
RISK_CHANGE = False
SAFETY_CHANGE = False
DASHBOARD_AUTHORITY_EFFECT = "NONE"
DASHBOARD_READ_ONLY_CONSUMER = True
DASHBOARD_FILES_CHANGED = False
PRESENTATION_LAYER_CHANGED = False

RESTART_RECOVERY_LADDER_STEP_CLOSED = False
CAPABILITY_CLOSED = False
RUNTIME_REACHABLE = True
PRODUCTIVE_SESSION_REACHABLE = True
REAL_PUBLIC_MD_RESTART_SESSION_COMPLETED = False

CALL_GRAPH_BEFORE = [
    "Step-3 Binding CLI (binding-only; refuses --request-real-network)",
    "Network entrypoint execute-post-unlock (real network forbidden)",
    "Session-GO / segment auth / offline harness / bundle verifier exist",
    "NO productive Step-3 governed execution surface entrypoint",
]

CALL_GRAPH_AFTER = [
    "Governed Step-3 execution request",
    "exact repository SHA validation",
    "exact config digest validation",
    "exact session-contract / binding-config digest validation",
    "Session-GO ACTIVE artifact validation",
    "OWNER_GO + OPERATOR_AUTHORIZATION + NETWORK_SESSION_GO gates",
    "authorization artifact scope/SHA/config/instrument validation",
    "hidden confirm-token handoff binding (no argv/env plaintext)",
    "canonical Public-MD GET-only provider contract",
    "PRE_RESTART segment via bound segment_runner + offline provider",
    "controlled process/session boundary (exit 82)",
    "POST_RESTART segment in new-process identity",
    "reconciliation before alpha",
    "duplicate observation/confirmation/intent/fill guards",
    "session manifest schema",
    "offline/bundle verifier bindings",
    "REAL_NETWORK remains fail-closed in this surface capability",
]


def repo_root_v1() -> Path:
    return Path(__file__).resolve().parents[3]
