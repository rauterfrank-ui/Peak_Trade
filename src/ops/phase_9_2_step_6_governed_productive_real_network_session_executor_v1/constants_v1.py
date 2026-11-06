"""Constants for Step-6 productive real-network session executor binding."""

from __future__ import annotations

from pathlib import Path

CAPABILITY_ID = "PHASE_9_2_STEP_6_GOVERNED_PRODUCTIVE_REAL_NETWORK_SESSION_EXECUTOR_BINDING_V1"
SCHEMA_VERSION = "phase_9_2_step_6_governed_productive_real_network_session_executor.v1"
PRODUCER_VERSION = SCHEMA_VERSION
PACKAGE_MARKER = (
    "PHASE_9_2_STEP_6_GOVERNED_PRODUCTIVE_REAL_NETWORK_SESSION_EXECUTOR_BINDING_V1=true"
)
OWNER = "ops.phase_9_2_step_6_governed_productive_real_network_session_executor_v1"
AUTHORITY_OWNER = OWNER

PREDECESSOR_EXECUTION_BINDING_ID = (
    "PHASE_9_2_STEP_6_GOVERNED_ADVERSE_STALE_DATA_SESSION_EXECUTION_BINDING_V1"
)
PREDECESSOR_CONTINUATION_ID = "PHASE_9_2_STEP_6_ADVERSE_STALE_DATA_SESSION_CONTINUATION_V1"
TARGET_EXECUTION_CAPABILITY_ID = "PHASE_9_2_STEP_6_GOVERNED_ADVERSE_STALE_DATA_SESSION_EXECUTION_V1"

SESSION_LADDER_STEP = "ADVERSE_STALE_DATA_SESSION"
SESSION_SCOPE = "PHASE_9_2_ADVERSE_STALE_DATA_SESSION"
TARGET_SESSION_ID = "phase_9_2_public_md_adverse_stale_data_session_v1"
RUNTIME_SESSION_ID = "phase_9_2_adverse_stale_data_runtime_session_v1"
CAMPAIGN_ID = "phase_9_2_adverse_stale_data_campaign_v1"
CONFIRMATION_SESSION_ID = "phase_9_2_adverse_stale_data_confirmation_session_v1"
CANONICAL_INSTRUMENT_ID = "ETH-USD_UM_XPERP-310404"

CONFIG_RELATIVE_PATH = (
    "config/ops/phase_9_2_step_6_governed_productive_real_network_session_executor_v1.json"
)
SESSION_CONTRACT_RELATIVE_PATH = (
    "config/ops/phase_9_2_public_md_adverse_stale_data_session_contract_v1.json"
)
PREDECESSOR_EXECUTION_CONFIG_RELATIVE_PATH = (
    "config/ops/phase_9_2_step_6_governed_adverse_stale_data_session_execution_v1.json"
)
PRODUCTIVE_ENTRYPOINT_PATH = (
    "scripts/ops/run_phase_9_2_step_6_governed_productive_real_network_session_executor_v1.py"
)
EVIDENCE_DIRNAME = (
    "capability_phase_9_2_step_6_governed_productive_real_network_session_executor_v1"
)
CAPABILITY_DOC_RELATIVE_PATH = (
    "docs/ops/specs/CAPABILITY_PHASE_9_2_STEP_6_GOVERNED_PRODUCTIVE_REAL_NETWORK_"
    "SESSION_EXECUTOR_BINDING_V1.md"
)

MIN_WALLCLOCK_DURATION_SECONDS = 180
DEFAULT_WALLCLOCK_DURATION_SECONDS = 600
MAX_WALLCLOCK_DURATION_SECONDS = 3600
MAX_NETWORK_SESSION_COUNT = 1

CANONICAL_WALLCLOCK_RUNNER = (
    "src.ops.integrated_paper_shadow_productive_authorization_issuance_and_real_network_"
    "execution_v1.productive_run_entrypoint_v1.run_productive_wallclock_session_v1"
)
STALE_CONTROL_BINDING_OWNER = (
    "ops.phase_9_2_step_6_governed_adverse_stale_data_session_execution_v1.stale_control_binding_v1"
)
FAILURE_INJECTION_SURFACE = (
    "ops.phase_9_2_step_6_adverse_stale_data_session_continuation_v1."
    "governed_injected_stale_data_fault_v1"
)
CONFIRM_TOKEN_OWNER = (
    "ops.paper_shadow_observation_operator_go_session_preregistration_v1.confirm_token_v1"
)
HIDDEN_PTY_CONFIRM_HANDOFF_OWNER = (
    "ops.phase_9_2_step_6_governed_productive_real_network_session_executor_v1."
    "hidden_pty_handoff_v1"
)
STEP5_NETWORK_SESSION_GO_PATTERN_OWNER = (
    "ops.phase_9_2_step_5_productive_real_network_session_activation_and_wiring_v1."
    "network_session_go_v1"
)
RUNTIME_OVERRIDE_KEY_STALE_CONTROL = "governed_stale_data_control"
RUNTIME_OVERRIDE_KEY_TRANSPORT_FAULT = "governed_fault_schedule"

MODE_PROVE_BINDING_ONLY = "PROVE_BINDING_ONLY"
MODE_GOVERNED_REAL_NETWORK_SESSION = "GOVERNED_REAL_NETWORK_SESSION"

# Permanent constants — never flip. Real network requires ephemeral GO + real TTY.
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
FAULT_SESSION_EXECUTION_AUTHORIZED = False
NO_PERMANENT_UNSCOPED_ENABLE_FLAG = True

PHASE_9_2_STEP_6_STATUS = "OPEN"
NEXT_OPEN_PHASE_9_2_STEP = "6_ADVERSE_STALE_DATA_SESSION"
ADVERSE_STALE_DATA_LADDER_STEP_CLOSED = False
CAPABILITY_CLOSED = False
SESSION_EXECUTED = False
STEP6_PRODUCTIVE_REAL_NETWORK_SESSION_EXECUTOR_BOUND = True

GOVERNED_PUBLIC_MD_NETWORK_SCOPE = "okx_eea_futures_public_md_observe_v1"
EEA_PUBLIC_MD_HOST = "eea.okx.com"
NETWORK_ALLOWLIST = "OKX_EEA_PUBLIC_MARKET_DATA_ENDPOINTS_ONLY"
HTTP_METHOD_ALLOWLIST = "GET_ONLY"
NETWORK_MODE = "PUBLIC_MD_GET_ONLY"

FORBIDDEN_NETWORK_SESSION_GO_ENV_KEYS = (
    "NETWORK_SESSION_GO",
    "PEAK_TRADE_NETWORK_SESSION_GO",
    "PEAK_TRADE_STEP6_NETWORK_SESSION_GO",
    "OWNER_NETWORK_SESSION_GO",
)
FORBIDDEN_CONFIRM_TOKEN_ARGV_FLAGS = (
    "--confirm-token",
    "--confirm_token",
    "--confirm-token-plaintext",
)
FORBIDDEN_CONFIRM_TOKEN_ENV_KEYS = (
    "PEAK_TRADE_STEP6_CONFIRM_TOKEN",
    "CONFIRM_TOKEN",
    "CONFIRM_TOKEN_PLAINTEXT",
    "PEAK_TRADE_PSO_CONFIRM_TOKEN",
    "PEAK_TRADE_PSO_WALLCLOCK_CONFIRM_TOKEN",
)

TERMINAL_CLASSES = (
    "PASS",
    "HARD_STOP",
    "CONFIRM_TOKEN_FAILURE",
    "AUTHORIZATION_FAILURE",
    "CONTRACT_MISMATCH",
    "BINDING_PROOF",
)

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

NO_PARALLEL_STALENESS_MODEL = True
NO_PARALLEL_KILLSTATE_MODEL = True
NO_PARALLEL_SESSION_MODEL = True
NO_PARALLEL_EVIDENCE_MODEL = True

CALL_GRAPH_BEFORE = [
    "Step-6 execution binding package (NETWORK_SESSION forbidden)",
    "governed_stale_data_control productively bound but no productive executor",
    "HARD_STOP: REAL_NETWORK_SESSION_FORBIDDEN_IN_THIS_BINDING_CAPABILITY",
]

CALL_GRAPH_AFTER = [
    "PROVE_BINDING_ONLY (default; zero network calls)",
    "ephemeral NETWORK_SESSION_GO gate (parameter-only; default false)",
    "reuse Step-5 network_session_go pattern",
    "reuse bind_stale_control_into_runtime_overrides_v1",
    "reuse GovernedInjectedStaleDataControlV1 + RECEIVE_LAG schedule",
    "reuse run_productive_wallclock_session_v1 symbol (later session only)",
    "hidden-PTY confirm-token handoff + real TTY gate",
    "GOVERNED_REAL_NETWORK_SESSION gate (ephemeral; fail-closed without Owner-GO+TTY)",
    "MAX_NETWORK_SESSION_COUNT=1",
    "PHASE_9_2_STEP_6_STATUS remains OPEN until later session verifier PASS",
]

LATER_SESSION_INVOCATION = (
    "scripts/ops/run_phase_9_2_step_6_governed_productive_real_network_session_executor_v1.py "
    "execute-governed-session --owner-go --operator-authorization-explicit "
    "--network-session-go --request-real-network "
    "(requires real TTY; confirm token via hidden PTY/stdin getpass only; "
    "enable governed RECEIVE_LAG stale schedule only under that ephemeral GO; "
    "permanent NETWORK_SESSION_ALLOWED remains false; this binding PR never starts network)"
)


def repo_root_v1() -> Path:
    return Path(__file__).resolve().parents[3]
