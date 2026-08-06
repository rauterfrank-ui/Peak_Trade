"""Constants for Step-5 governed prolonged natural-market session execution."""

from __future__ import annotations

from pathlib import Path

CAPABILITY_ID = (
    "PHASE_9_2_STEP_5_GOVERNED_PRODUCTIVE_REAL_NETWORK_"
    "PROLONGED_NATURAL_MARKET_SESSION_EXECUTION_CAPABILITY_V1"
)
SCHEMA_VERSION = (
    "phase_9_2_step_5_governed_productive_real_network_"
    "prolonged_natural_market_session_execution.v1"
)
PRODUCER_VERSION = SCHEMA_VERSION
OWNER = (
    "ops.phase_9_2_step_5_governed_productive_real_network_"
    "prolonged_natural_market_session_execution_v1"
)
AUTHORITY_OWNER = OWNER

BINDING_CAPABILITY_ID = (
    "PHASE_9_2_PRODUCTIVE_PUBLIC_MD_PROLONGED_NATURAL_MARKET_WALLCLOCK_BINDING_V1"
)
PREDECESSOR_BINDING_PACKAGE = (
    "ops.phase_9_2_productive_public_md_prolonged_natural_market_wallclock_binding_v1"
)
STEP4_PATTERN_OWNER = "ops.phase_9_2_productive_public_md_rate_limit_reconnect_wallclock_binding_v1"

SESSION_LADDER_STEP = "PROLONGED_NATURAL_MARKET_SESSION"
SESSION_SCOPE = "PHASE_9_2_PROLONGED_NATURAL_MARKET_SESSION"
TARGET_SESSION_ID = "phase_9_2_public_md_prolonged_natural_market_session_v1"
RUNTIME_SESSION_ID = "phase_9_2_prolonged_natural_market_runtime_session_v1"
CONFIRMATION_SESSION_ID = "phase_9_2_prolonged_natural_market_confirmation_session_v1"
CANONICAL_INSTRUMENT_ID = "ETH-USD_UM_XPERP-310404"

CONFIG_RELATIVE_PATH = (
    "config/ops/phase_9_2_step_5_governed_productive_real_network_"
    "prolonged_natural_market_session_execution_v1.json"
)
SESSION_CONTRACT_RELATIVE_PATH = (
    "config/ops/phase_9_2_public_md_prolonged_natural_market_session_contract_v1.json"
)
BINDING_CONFIG_RELATIVE_PATH = (
    "config/ops/phase_9_2_productive_public_md_prolonged_natural_market_wallclock_binding_v1.json"
)
BINDING_CLI_PATH = "scripts/ops/run_phase_9_2_productive_public_md_prolonged_natural_market_wallclock_binding_v1.py"
PRODUCTIVE_ENTRYPOINT_PATH = (
    "scripts/ops/run_phase_9_2_step_5_governed_productive_real_network_"
    "prolonged_natural_market_session_execution_v1.py"
)
EVIDENCE_DIRNAME = (
    "capability_phase_9_2_step_5_governed_productive_real_network_"
    "prolonged_natural_market_session_execution_v1"
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
HIDDEN_PTY_CONFIRM_HANDOFF_OWNER = (
    "ops.phase_9_2_step_5_governed_productive_real_network_"
    "prolonged_natural_market_session_execution_v1.hidden_pty_handoff_v1"
)

PLANNED_SESSION_DURATION_SECONDS = 7200
MINIMUM_SUCCESSFUL_WALLCLOCK_SECONDS = 7200
MAX_SESSION_DURATION_SECONDS = 21600

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
GOVERNED_PUBLIC_MD_SESSION_EXECUTION_SCOPE = "paper_shadow_observation_wallclock_v1"
PRODUCTIVE_V2_ARTIFACT_NETWORK_SCOPE = "PUBLIC_MARKET_DATA_ONLY"
EEA_PUBLIC_MD_HOST = "eea.okx.com"
NETWORK_ALLOWLIST = "OKX_EEA_PUBLIC_MARKET_DATA_ENDPOINTS_ONLY"
HTTP_METHOD_ALLOWLIST = "GET_ONLY"
NETWORK_MODE = "PUBLIC_MD_GET_ONLY"

AUTHORIZATION_LEDGER_FILENAME = "step5_authorization_consumption_ledger_v1.jsonl"
CONFIRM_TOKEN_LEDGER_FILENAME = "step5_confirm_token_consumption_ledger_v1.jsonl"
SESSION_LOCK_NAME = "phase_9_2_step5_prolonged_natural_market_session_lock_v1"

FORBIDDEN_CONFIRM_TOKEN_ARGV_FLAGS = (
    "--confirm-token",
    "--confirm_token",
    "--confirm-token-plaintext",
)
FORBIDDEN_CONFIRM_TOKEN_ENV_KEYS = (
    "PEAK_TRADE_STEP5_CONFIRM_TOKEN",
    "CONFIRM_TOKEN",
    "CONFIRM_TOKEN_PLAINTEXT",
)

SESSION_EVIDENCE_SCHEMA_VERSION = "phase_9_2_step5_prolonged_natural_market_session_evidence.v1"

TERMINAL_CLASSES = (
    "PASS",
    "HARD_STOP",
    "INTERRUPTED",
    "STALE_DATA_STOP",
    "RATE_LIMIT_EXHAUSTED",
    "RECONNECT_EXHAUSTED",
    "NETWORK_FAILURE",
    "CONTRACT_MISMATCH",
    "AUTHORIZATION_FAILURE",
    "CONFIRM_TOKEN_FAILURE",
    "EVIDENCE_FAILURE",
    "DISK_BOUND_FAILURE",
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

PROLONGED_NATURAL_MARKET_LADDER_STEP_CLOSED = False
CAPABILITY_CLOSED = False
RUNTIME_REACHABLE = True
PRODUCTIVE_SESSION_REACHABLE = True

CALL_GRAPH_BEFORE = [
    "Step-5 Binding CLI (binding-only)",
    "Session contract + binding config digests",
    "assemble-session-request (binding)",
    "NO productive execution entrypoint",
]

CALL_GRAPH_AFTER = [
    "Governed Step-5 Session Request",
    "exact repository SHA validation",
    "exact session-contract digest validation",
    "exact binding-config digest validation",
    "authorization artifact validation",
    "hidden confirm-token handoff",
    "authorization/token scope validation",
    "single-use consumption boundary (fail-closed until separate Owner-GO)",
    "execution permit validation",
    "bounded prolonged Public-MD executor",
    "pacing / retry / backoff / reconnect control",
    "heartbeat / staleness / interrupt / recovery handling",
    "bounded disk/evidence writer",
    "terminal classification",
    "manifest assembly",
    "verifier",
]


def repo_root_v1() -> Path:
    return Path(__file__).resolve().parents[3]
