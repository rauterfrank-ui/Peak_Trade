"""Constants for Step-6 governed productive Real-Network session execution.

Layering (fail-closed separation):
  BINDING_EXECUTOR — always forbids Real-Network
  PATH_IMPLEMENTATION — structural may_start only; never starts network
  SESSION_EXECUTION (this package) — owns session may-start + later invoke wiring
"""

from __future__ import annotations

from pathlib import Path

# Current PR capability: closes only the productive start-invoke edge.
CAPABILITY_ID = (
    "PHASE_9_2_STEP_6_PRODUCTIVE_REAL_NETWORK_SESSION_START_INVOKE_EDGE_IMPLEMENTATION_V1"
)
# Predecessor session-owner package capability (preserved; non-starting prove layer).
SESSION_EXECUTION_IMPLEMENTATION_CAPABILITY_ID = (
    "PHASE_9_2_STEP_6_GOVERNED_PRODUCTIVE_REAL_NETWORK_SESSION_EXECUTION_IMPLEMENTATION_V1"
)
TARGET_SESSION_CAPABILITY_ID = (
    "PHASE_9_2_STEP_6_GOVERNED_PRODUCTIVE_REAL_NETWORK_SESSION_EXECUTION_V1"
)
START_INVOKE_EDGE_CAPABILITY_ID = CAPABILITY_ID
SCHEMA_VERSION = "phase_9_2_step_6_productive_real_network_session_start_invoke_edge.v1"
PRODUCER_VERSION = SCHEMA_VERSION
PACKAGE_MARKER = (
    "PHASE_9_2_STEP_6_PRODUCTIVE_REAL_NETWORK_SESSION_START_INVOKE_EDGE_IMPLEMENTATION_V1=true"
)
OWNER = "ops.phase_9_2_step_6_governed_productive_real_network_session_execution_v1"
AUTHORITY_OWNER = OWNER

BINDING_EXECUTOR_CAPABILITY_ID = (
    "PHASE_9_2_STEP_6_GOVERNED_PRODUCTIVE_REAL_NETWORK_SESSION_EXECUTOR_BINDING_V1"
)
PATH_IMPLEMENTATION_CAPABILITY_ID = (
    "PHASE_9_2_STEP_6_PRODUCTIVE_REAL_NETWORK_EXECUTION_PATH_IMPLEMENTATION_V1"
)
PATH_PACKAGE = "ops.phase_9_2_step_6_productive_real_network_execution_path_v1"
BINDING_PACKAGE = "ops.phase_9_2_step_6_governed_productive_real_network_session_executor_v1"
STEP5_PATTERN_OWNER = (
    "ops.phase_9_2_step_5_governed_productive_real_network_"
    "prolonged_natural_market_session_execution_v1"
)

SESSION_LADDER_STEP = "ADVERSE_STALE_DATA_SESSION"
SESSION_SCOPE = "PHASE_9_2_ADVERSE_STALE_DATA_SESSION"
TARGET_SESSION_ID = "phase_9_2_public_md_adverse_stale_data_session_v1"
RUNTIME_SESSION_ID = "phase_9_2_adverse_stale_data_runtime_session_v1"
CANONICAL_INSTRUMENT_ID = "ETH-USD_UM_XPERP-310404"

CONFIG_RELATIVE_PATH = (
    "config/ops/phase_9_2_step_6_governed_productive_real_network_session_execution_v1.json"
)
SESSION_CONTRACT_RELATIVE_PATH = (
    "config/ops/phase_9_2_public_md_adverse_stale_data_session_contract_v1.json"
)
PATH_CONFIG_RELATIVE_PATH = (
    "config/ops/phase_9_2_step_6_productive_real_network_execution_path_v1.json"
)
PRODUCTIVE_ENTRYPOINT_PATH = (
    "scripts/ops/run_phase_9_2_step_6_governed_productive_real_network_session_execution_v1.py"
)
PATH_ENTRYPOINT_PATH = (
    "scripts/ops/run_phase_9_2_step_6_productive_real_network_execution_path_v1.py"
)
BINDING_ENTRYPOINT_PATH = (
    "scripts/ops/run_phase_9_2_step_6_governed_productive_real_network_session_executor_v1.py"
)
CAPABILITY_DOC_RELATIVE_PATH = (
    "docs/ops/specs/CAPABILITY_PHASE_9_2_STEP_6_PRODUCTIVE_REAL_NETWORK_"
    "SESSION_START_INVOKE_EDGE_IMPLEMENTATION_V1.md"
)
EVIDENCE_DIRNAME = (
    "capability_phase_9_2_step_6_productive_real_network_session_start_invoke_edge_v1"
)

MIN_WALLCLOCK_DURATION_SECONDS = 180
DEFAULT_WALLCLOCK_DURATION_SECONDS = 600
MAX_WALLCLOCK_DURATION_SECONDS = 3600
MAX_NETWORK_SESSION_COUNT = 1

CANONICAL_WALLCLOCK_RUNNER = (
    "src.ops.integrated_paper_shadow_productive_authorization_issuance_and_real_network_"
    "execution_v1.productive_run_entrypoint_v1.run_productive_wallclock_session_v1"
)
CANONICAL_PUBLIC_MD_FETCHER = (
    "src.ops.integrated_paper_shadow_productive_authorization_issuance_and_real_network_"
    "execution_v1.real_http_fetcher_v1.make_real_eea_public_md_fetcher_v1"
)
STALE_CONTROL_BINDING_OWNER = (
    "ops.phase_9_2_step_6_governed_adverse_stale_data_session_execution_v1.stale_control_binding_v1"
)
FAILURE_INJECTION_SURFACE = (
    "ops.phase_9_2_step_6_adverse_stale_data_session_continuation_v1."
    "governed_injected_stale_data_fault_v1"
)
STEP6_VERIFIER_OWNER = (
    "ops.phase_9_2_step_6_governed_productive_real_network_session_executor_v1.verifier_v1"
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

MODE_PROVE_IMPLEMENTATION_ONLY = "PROVE_IMPLEMENTATION_ONLY"
MODE_GOVERNED_REAL_NETWORK_SESSION = "GOVERNED_REAL_NETWORK_SESSION"

# Permanent constants — never flip. Real start requires ephemeral GO + invoke.
NETWORK_SESSION_ALLOWED = False
NETWORK_SESSION_GO_DEFAULT = False
NETWORK_SESSION_GO_PERSISTED = False
AUTHORIZATION_ISSUANCE_ALLOWED = False
AUTHORIZATION_CONSUMPTION_ALLOWED = False
CONFIRM_TOKEN_ISSUANCE_ALLOWED = False
CONFIRM_TOKEN_CONSUMPTION_ALLOWED = False
CONFIRM_TOKEN_MINTING_ALLOWED = False
SESSION_EXECUTION_ALLOWED = False
SESSION_EXECUTION_SIDE_EFFECTS_AUTHORIZED = False
REAL_NETWORK_REQUESTS_ALLOWED = False
PRODUCTIVE_NETWORK_SESSION_EXECUTION_AUTHORIZED = False
NO_PERMANENT_UNSCOPED_ENABLE_FLAG = True
NETWORK_SESSION_STARTED_BY_THIS_CAPABILITY = False

PHASE_9_2_STEP_6_STATUS = "OPEN"
PHASE_9_2_STEP_7_STATUS = "OPEN"
NEXT_OPEN_PHASE_9_2_STEP = "6_ADVERSE_STALE_DATA_SESSION"
ADVERSE_STALE_DATA_LADDER_STEP_CLOSED = False
CAPABILITY_CLOSED = False
SESSION_EXECUTED = False
STEP6_GOVERNED_PRODUCTIVE_SESSION_EXECUTION_CAPABILITY_PRESENT = True
STEP6_SESSION_OWNER_PRESENT = True
STEP6_PRODUCTIVE_REAL_NETWORK_EXECUTION_PATH_PRESENT = True
STEP6_PRODUCTIVE_REAL_NETWORK_EXECUTION_PATH_ABSENT = False
STEP6_PRODUCTIVE_REAL_NETWORK_START_INVOKE_EDGE_PRESENT = True
STEP6_PRODUCTIVE_REAL_NETWORK_START_INVOKE_EDGE_RUNTIME_REACHABLE = True
STEP6_BINDING_ONLY_EXECUTOR_PRESERVED = True
STEP6_PRODUCTIVE_PATH_IMPLEMENTATION_PRESERVED = True
STEP7_STARTED = False
PRODUCTIVE_SESSION_INVOKE_SYMBOL = "execute_governed_step6_session_v1"
READY_FOR_SEPARATE_OWNER_GO_REAL_TTY_SESSION = True

GOVERNED_PUBLIC_MD_NETWORK_SCOPE = "okx_eea_futures_public_md_observe_v1"
EEA_PUBLIC_MD_HOST = "eea.okx.com"
NETWORK_ALLOWLIST = "OKX_EEA_PUBLIC_MARKET_DATA_ENDPOINTS_ONLY"
HTTP_METHOD_ALLOWLIST = "GET_ONLY"
NETWORK_MODE = "PUBLIC_MD_GET_ONLY"

FORBIDDEN_NETWORK_SESSION_GO_ENV_KEYS = (
    "NETWORK_SESSION_GO",
    "PEAK_TRADE_NETWORK_SESSION_GO",
    "PEAK_TRADE_STEP6_NETWORK_SESSION_GO",
    "PEAK_TRADE_STEP6_SESSION_EXECUTION_NETWORK_SESSION_GO",
    "OWNER_NETWORK_SESSION_GO",
)
FORBIDDEN_CONFIRM_TOKEN_ARGV_FLAGS = (
    "--confirm-token",
    "--confirm_token",
    "--confirm-token-plaintext",
)
FORBIDDEN_CONFIRM_TOKEN_ENV_KEYS = (
    "PEAK_TRADE_STEP6_CONFIRM_TOKEN",
    "PEAK_TRADE_STEP6_SESSION_CONFIRM_TOKEN",
    "CONFIRM_TOKEN",
    "CONFIRM_TOKEN_PLAINTEXT",
    "PEAK_TRADE_PSO_CONFIRM_TOKEN",
    "PEAK_TRADE_PSO_WALLCLOCK_CONFIRM_TOKEN",
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

CALL_GRAPH_BEFORE = [
    "BINDING_EXECUTOR forever fail-closed",
    "PATH_IMPLEMENTATION structural may_start only (never starts)",
    "SESSION_EXECUTION package present (may_start; start deferred)",
    "HARD_STOP: PRODUCTIVE_REAL_NETWORK_START_INVOKE_EDGE_ABSENT",
]

CALL_GRAPH_AFTER = [
    "BINDING_EXECUTOR preserved fail-closed (unchanged)",
    "PATH_IMPLEMENTATION preserved (unchanged; never starts)",
    "SESSION_EXECUTION package preserved",
    "START_INVOKE_EDGE present: execute_governed_step6_session_v1",
    "session_execution_may_start + Owner-GO + NETWORK_SESSION_GO + Real-TTY + Hidden-Confirm",
    "exactly-one run_productive_wallclock_session_v1 under TARGET_SESSION_CAPABILITY_ID",
    "governed_stale_data_control overrides + canonical Public-MD fetcher",
    "evidence + productive verifier handoff wired",
    "THIS_CAPABILITY: NETWORK_SESSION_STARTED=false (prove/materialize/tests use doubles)",
    "PHASE_9_2_STEP_6_STATUS remains OPEN until later Owner-GO Real-TTY session verifier PASS",
]

LATER_SESSION_INVOCATION = (
    "execute_governed_step6_session_v1 under TARGET_SESSION_CAPABILITY_ID with "
    "--owner-go --operator-authorization-explicit --network-session-go "
    "--request-real-network + Real-TTY Hidden-PTY confirm "
    "(separate Owner-GO Real-TTY session after merge; this capability never starts network)"
)


def repo_root_v1() -> Path:
    return Path(__file__).resolve().parents[3]
