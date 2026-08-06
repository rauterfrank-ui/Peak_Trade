"""Constants for Step-5 productive real-network session activation and wiring."""

from __future__ import annotations

from pathlib import Path

CAPABILITY_ID = "PHASE_9_2_STEP_5_PRODUCTIVE_REAL_NETWORK_SESSION_ACTIVATION_AND_WIRING_V1"
SCHEMA_VERSION = "phase_9_2_step_5_productive_real_network_session_activation_and_wiring.v1"
PRODUCER_VERSION = SCHEMA_VERSION
OWNER = "ops.phase_9_2_step_5_productive_real_network_session_activation_and_wiring_v1"
AUTHORITY_OWNER = OWNER

STEP5_EXECUTION_CAPABILITY_ID = (
    "PHASE_9_2_STEP_5_GOVERNED_PRODUCTIVE_REAL_NETWORK_"
    "PROLONGED_NATURAL_MARKET_SESSION_EXECUTION_CAPABILITY_V1"
)
STEP5_EXECUTION_PACKAGE = (
    "ops.phase_9_2_step_5_governed_productive_real_network_"
    "prolonged_natural_market_session_execution_v1"
)
STEP4_ACTIVATION_PATTERN_OWNER = (
    "ops.phase_9_2_productive_public_md_rate_limit_reconnect_wallclock_binding_v1."
    "final_generic_session_activation_binding_v1"
)

SESSION_SCOPE = "PHASE_9_2_PROLONGED_NATURAL_MARKET_SESSION"
TARGET_SESSION_ID = "phase_9_2_public_md_prolonged_natural_market_session_v1"
CANONICAL_INSTRUMENT_ID = "ETH-USD_UM_XPERP-310404"

CONFIG_RELATIVE_PATH = (
    "config/ops/phase_9_2_step_5_productive_real_network_session_activation_and_wiring_v1.json"
)
SESSION_CONTRACT_RELATIVE_PATH = (
    "config/ops/phase_9_2_public_md_prolonged_natural_market_session_contract_v1.json"
)
BINDING_CONFIG_RELATIVE_PATH = (
    "config/ops/phase_9_2_productive_public_md_prolonged_natural_market_wallclock_binding_v1.json"
)
PRODUCTIVE_ENTRYPOINT_PATH = (
    "scripts/ops/run_phase_9_2_step_5_governed_productive_real_network_"
    "prolonged_natural_market_session_execution_v1.py"
)
ACTIVATION_CLI_PATH = (
    "scripts/ops/run_phase_9_2_step_5_productive_real_network_session_activation_and_wiring_v1.py"
)
EVIDENCE_DIRNAME = (
    "capability_phase_9_2_step_5_productive_real_network_session_activation_and_wiring_v1"
)

CANONICAL_PUBLIC_MD_FETCHER = (
    "src.ops.integrated_paper_shadow_productive_authorization_issuance_and_real_network_"
    "execution_v1.real_http_fetcher_v1.make_real_eea_public_md_fetcher_v1"
)
CANONICAL_WALLCLOCK_RUNNER = (
    "src.ops.integrated_paper_shadow_productive_authorization_issuance_and_real_network_"
    "execution_v1.productive_run_entrypoint_v1.run_productive_wallclock_session_v1"
)
CONFIRM_TOKEN_OWNER = (
    "ops.paper_shadow_observation_operator_go_session_preregistration_v1.confirm_token_v1"
)
AUTHORIZATION_ISSUANCE_OWNER = (
    "ops.integrated_paper_shadow_productive_authorization_issuance_and_real_network_"
    "execution_v1.productive_operator_go_producer_v1.issue_productive_authorization_v1"
)
STEP5_AUTHORIZATION_GATE_OWNER = f"{STEP5_EXECUTION_PACKAGE}.authorization_gate_v1"
STEP5_CONFIRM_TOKEN_HANDOFF_OWNER = f"{STEP5_EXECUTION_PACKAGE}.hidden_pty_handoff_v1"
STEP5_PROLONGED_EXECUTOR_OWNER = f"{STEP5_EXECUTION_PACKAGE}.prolonged_executor_v1"

PLANNED_SESSION_DURATION_SECONDS = 7200
MINIMUM_SUCCESSFUL_WALLCLOCK_SECONDS = 7200
MAX_SESSION_DURATION_SECONDS = 21600

# Permanent defaults — never flip; ephemeral NETWORK_SESSION_GO is parameter-only.
NETWORK_SESSION_ALLOWED = False
NETWORK_SESSION_GO_DEFAULT = False
NETWORK_SESSION_GO_PERSISTED = False
AUTHORIZATION_ISSUANCE_ALLOWED = False
AUTHORIZATION_CONSUMPTION_ALLOWED = False
CONFIRM_TOKEN_ISSUANCE_ALLOWED = False
CONFIRM_TOKEN_CONSUMPTION_ALLOWED = False
SESSION_EXECUTION_SIDE_EFFECTS_AUTHORIZED = False
REAL_NETWORK_REQUESTS_ALLOWED = False
PRODUCTIVE_NETWORK_SESSION_EXECUTION_AUTHORIZED = False
NO_PERMANENT_UNSCOPED_ENABLE_FLAG = True

NETWORK_ALLOWLIST = "OKX_EEA_PUBLIC_MARKET_DATA_ENDPOINTS_ONLY"
HTTP_METHOD_ALLOWLIST = "GET_ONLY"
NETWORK_MODE = "PUBLIC_MD_GET_ONLY"

FORBIDDEN_NETWORK_SESSION_GO_ENV_KEYS = (
    "NETWORK_SESSION_GO",
    "PEAK_TRADE_NETWORK_SESSION_GO",
    "PEAK_TRADE_STEP5_NETWORK_SESSION_GO",
    "OWNER_NETWORK_SESSION_GO",
)

FORBIDDEN_CONFIRM_TOKEN_ARGV_FLAGS = (
    "--confirm-token",
    "--confirm_token",
    "--confirm-token-plaintext",
)
FORBIDDEN_CONFIRM_TOKEN_ENV_KEYS = (
    "PEAK_TRADE_STEP5_CONFIRM_TOKEN",
    "CONFIRM_TOKEN",
    "CONFIRM_TOKEN_PLAINTEXT",
    "PEAK_TRADE_PSO_CONFIRM_TOKEN",
)

CALL_GRAPH_BEFORE = [
    "Step-5 Execution CLI execute-governed-session",
    "digest/auth/token validate-only",
    "EXECUTION_PERMIT_NOT_AUTHORIZED_IN_THIS_CAPABILITY",
    "NETWORK_SESSION_ALLOWED_FALSE",
    "REAL_NETWORK_FETCHER_NOT_WIRED_IN_THIS_CAPABILITY",
    "FAIL_CLOSED_NO_NETWORK_NO_CONSUME",
]

CALL_GRAPH_AFTER = [
    "Step-5 Execution CLI",
    "Step-5 Activation + Wiring gate",
    "ephemeral NETWORK_SESSION_GO (parameter-only, default false)",
    "SHA / session-contract / binding-config digest binding",
    "capability + authorization + confirm-token scope binding",
    "Step-4-pattern authorization adapter (validate; consume deferred)",
    "Step-4-pattern hidden-PTY confirm-token adapter (validate; consume deferred)",
    "canonical Public-MD fetcher factory wired",
    "bounded prolonged Public-MD executor (later session only)",
    "Public-MD GET-only boundary",
    "evidence + verifier",
    "process cleanup",
]

MISSING_EDGES_BEFORE = [
    "REAL_PUBLIC_MD_FETCHER_WIRE_INTO_STEP5_EXECUTOR",
    "EPHEMERAL_NETWORK_SESSION_GO_GATE",
    "STEP4_PATTERN_ACTIVATION_PERMIT_FOR_STEP5",
]

CORE_LOGIC_CHANGE = False
DASHBOARD_AUTHORITY_EFFECT = "NONE"
DASHBOARD_READ_ONLY_CONSUMER = True
DASHBOARD_FILES_CHANGED = False
PRESENTATION_LAYER_CHANGED = False
NETWORK_SESSION_STARTED_BY_THIS_CAPABILITY = False
CAPABILITY_CLOSED = False


def repo_root_v1() -> Path:
    return Path(__file__).resolve().parents[3]
