"""Constants for Step-5 final generic auth-consume and network-start binding."""

from __future__ import annotations

from pathlib import Path

CAPABILITY_ID = (
    "PHASE_9_2_STEP_5_FINAL_GENERIC_SESSION_AUTHORIZATION_CONSUME_AND_NETWORK_START_BINDING_V1"
)
SCHEMA_VERSION = (
    "phase_9_2_step_5_final_generic_session_authorization_consume_and_network_start_binding.v1"
)
PRODUCER_VERSION = SCHEMA_VERSION
OWNER = (
    "ops.phase_9_2_step_5_final_generic_session_authorization_consume_and_network_start_binding_v1"
)
AUTHORITY_OWNER = OWNER

STEP5_EXECUTION_CAPABILITY_ID = (
    "PHASE_9_2_STEP_5_GOVERNED_PRODUCTIVE_REAL_NETWORK_"
    "PROLONGED_NATURAL_MARKET_SESSION_EXECUTION_CAPABILITY_V1"
)
STEP5_EXECUTION_PACKAGE = (
    "ops.phase_9_2_step_5_governed_productive_real_network_"
    "prolonged_natural_market_session_execution_v1"
)
STEP4_FINAL_GENERIC_PATTERN_OWNER = (
    "ops.phase_9_2_productive_public_md_rate_limit_reconnect_wallclock_binding_v1."
    "final_generic_session_activation_binding_v1"
)

SESSION_SCOPE = "PHASE_9_2_PROLONGED_NATURAL_MARKET_SESSION"
TARGET_SESSION_ID = "phase_9_2_public_md_prolonged_natural_market_session_v1"
RUNTIME_MODE = "PUBLIC_MD_GET_ONLY"
SESSION_TYPE = "PHASE_9_2_STEP_5_PROLONGED_NATURAL_MARKET"

CONFIG_RELATIVE_PATH = (
    "config/ops/phase_9_2_step_5_final_generic_session_authorization_"
    "consume_and_network_start_binding_v1.json"
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
BINDING_CLI_PATH = (
    "scripts/ops/run_phase_9_2_step_5_final_generic_session_authorization_"
    "consume_and_network_start_binding_v1.py"
)
EVIDENCE_DIRNAME = (
    "capability_phase_9_2_step_5_final_generic_session_authorization_"
    "consume_and_network_start_binding_v1"
)

AUTHORIZATION_ISSUANCE_OWNER = (
    "ops.integrated_paper_shadow_productive_authorization_issuance_and_real_network_"
    "execution_v1.productive_operator_go_producer_v1.issue_productive_authorization_v1"
)
CONFIRM_TOKEN_OWNER = (
    "ops.paper_shadow_observation_operator_go_session_preregistration_v1.confirm_token_v1"
)
HIDDEN_PTY_HANDOFF_OWNER = f"{STEP5_EXECUTION_PACKAGE}.hidden_pty_handoff_v1"
STEP5_AUTHORIZATION_GATE_OWNER = f"{STEP5_EXECUTION_PACKAGE}.authorization_gate_v1"
STEP5_EXECUTOR_OWNER = f"{STEP5_EXECUTION_PACKAGE}.governed_session_execution_v1"
STEP5_PROLONGED_EXECUTOR_OWNER = f"{STEP5_EXECUTION_PACKAGE}.prolonged_executor_v1"
CANONICAL_PUBLIC_MD_FETCHER = (
    "src.ops.integrated_paper_shadow_productive_authorization_issuance_and_real_network_"
    "execution_v1.real_http_fetcher_v1.make_real_eea_public_md_fetcher_v1"
)

PLANNED_SESSION_DURATION_SECONDS = 7200
MINIMUM_SUCCESSFUL_WALLCLOCK_SECONDS = 7200
MAX_SESSION_DURATION_SECONDS = 21600

NETWORK_ALLOWLIST = "OKX_EEA_PUBLIC_MARKET_DATA_ENDPOINTS_ONLY"
HTTP_METHOD_ALLOWLIST = "GET_ONLY"
NETWORK_MODE = "PUBLIC_MD_GET_ONLY"

# Permanent defaults — never flip; ephemeral GO is parameter-only.
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
GENERIC_STEP5_CONSUME_START_BINDING_COMPLETE = True

SIDE_EFFECT_AUTH_LEDGER_FILENAME = (
    "step5_final_generic_side_effect_authorization_consumption_ledger_v1.jsonl"
)
AUTHORIZATION_LEDGER_FILENAME = "step5_authorization_consumption_ledger_v1.jsonl"
CONFIRM_TOKEN_LEDGER_FILENAME = "step5_confirm_token_consumption_ledger_v1.jsonl"

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
FORBIDDEN_NETWORK_SESSION_GO_ENV_KEYS = (
    "NETWORK_SESSION_GO",
    "PEAK_TRADE_NETWORK_SESSION_GO",
    "PEAK_TRADE_STEP5_NETWORK_SESSION_GO",
    "OWNER_NETWORK_SESSION_GO",
)

CALL_GRAPH_BEFORE = [
    "Step-5 Execution CLI execute-governed-session",
    "digest/auth/token validate-only",
    "AUTHORIZATION_CONSUMPTION_DEFERRED_TO_LATER_SESSION_CAPABILITY",
    "CONFIRM_TOKEN_CONSUMPTION_DEFERRED_TO_LATER_SESSION_CAPABILITY",
    "LATER_SESSION_CAPABILITY_REQUIRED_FOR_CONSUME_AND_START",
    "FAIL_CLOSED_NO_NETWORK_NO_CONSUME",
]

CALL_GRAPH_AFTER = [
    "Step-5 Execution CLI / Binding CLI",
    "Step-5 preflight digests",
    "canonical authorization issuance binding (reuse)",
    "canonical hidden confirm-token issuance/input binding",
    "authorization validation (SHA/config/contract/scope/duration/expiry)",
    "confirm-token validation",
    "atomic single-use consumption (auth + token)",
    "consumed-authority object",
    "existing Step-5 governed executor",
    "existing Public-MD GET-only prolonged executor / runner",
    "existing evidence materialization",
    "existing verifier",
    "terminal result",
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
