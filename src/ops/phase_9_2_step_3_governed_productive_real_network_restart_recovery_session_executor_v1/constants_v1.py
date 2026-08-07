"""Constants for Step-3 governed restart/recovery session executor implementation."""

from __future__ import annotations

from pathlib import Path

CAPABILITY_ID = (
    "PHASE_9_2_STEP_3_GOVERNED_PRODUCTIVE_REAL_NETWORK_"
    "RESTART_RECOVERY_SESSION_EXECUTOR_IMPLEMENTATION_V1"
)
RUNTIME_CAPABILITY_ID = (
    "PHASE_9_2_STEP_3_GOVERNED_PRODUCTIVE_REAL_NETWORK_RESTART_RECOVERY_SESSION_EXECUTION_V1"
)
SURFACE_CAPABILITY_ID = (
    "PHASE_9_2_STEP_3_GOVERNED_PRODUCTIVE_REAL_NETWORK_"
    "RESTART_RECOVERY_SESSION_EXECUTION_SURFACE_IMPLEMENTATION_V1"
)
SCHEMA_VERSION = (
    "phase_9_2_step_3_governed_productive_real_network_restart_recovery_session_executor.v1"
)
PRODUCER_VERSION = SCHEMA_VERSION
OWNER = "ops.phase_9_2_step_3_governed_productive_real_network_restart_recovery_session_executor_v1"
AUTHORITY_OWNER = OWNER

SURFACE_PACKAGE = (
    "ops.phase_9_2_step_3_governed_productive_real_network_restart_recovery_session_execution_v1"
)
BINDING_CAPABILITY_ID = (
    "PHASE_9_2_PRODUCTIVE_PUBLIC_MD_RESTART_RECOVERY_REAL_NETWORK_WALLCLOCK_BINDING_V1"
)
SESSION_GO_PACKAGE = "ops.phase_9_2_productive_restart_recovery_session_go_capability_v1"
SEGMENT_RUNNER_OWNER = (
    "ops.phase_9_2_productive_public_md_restart_recovery_real_network_wallclock_binding_v1."
    "segment_runner_v1"
)

SESSION_LADDER_STEP = "RESTART_RECOVERY_SESSION"
SESSION_SCOPE = "PHASE_9_2_RESTART_RECOVERY_SESSION"
TARGET_SESSION_ID = "phase_9_2_public_md_restart_recovery_session_v1"
RUNTIME_SESSION_ID = "phase_9_2_restart_recovery_runtime_session_v1"
CONFIRMATION_SESSION_ID = "phase_9_2_restart_confirmation_session_v1"
RESTART_CAMPAIGN_ID = "phase_9_2_restart_recovery_campaign_v1"
CANONICAL_INSTRUMENT_ID = "ETH-USD_UM_XPERP-310404"

CONFIG_RELATIVE_PATH = (
    "config/ops/phase_9_2_step_3_governed_productive_real_network_"
    "restart_recovery_session_executor_v1.json"
)
SURFACE_CONFIG_RELATIVE_PATH = (
    "config/ops/phase_9_2_step_3_governed_productive_real_network_"
    "restart_recovery_session_execution_v1.json"
)
SESSION_CONTRACT_RELATIVE_PATH = "config/ops/phase_9_2_restart_recovery_session_contract_v1.json"
BINDING_CONFIG_RELATIVE_PATH = (
    "config/ops/phase_9_2_productive_public_md_restart_recovery_"
    "real_network_wallclock_binding_v1.json"
)
SURFACE_CLI_PATH = (
    "scripts/ops/run_phase_9_2_step_3_governed_productive_real_network_"
    "restart_recovery_session_execution_v1.py"
)
PRODUCTIVE_ENTRYPOINT_PATH = (
    "scripts/ops/run_phase_9_2_step_3_governed_productive_real_network_"
    "restart_recovery_session_executor_v1.py"
)
EVIDENCE_DIRNAME = (
    "capability_phase_9_2_step_3_governed_productive_real_network_"
    "restart_recovery_session_executor_implementation_v1"
)
CAPABILITY_DOC_RELATIVE_PATH = (
    "docs/ops/specs/CAPABILITY_PHASE_9_2_STEP_3_GOVERNED_PRODUCTIVE_REAL_NETWORK_"
    "RESTART_RECOVERY_SESSION_EXECUTOR_IMPLEMENTATION_V1.md"
)

CONFIRM_TOKEN_OWNER = (
    "ops.paper_shadow_observation_operator_go_session_preregistration_v1.confirm_token_v1"
)
HIDDEN_PTY_CONFIRM_HANDOFF_OWNER = (
    "ops.phase_9_2_step_3_governed_productive_real_network_"
    "restart_recovery_session_executor_v1.hidden_pty_handoff_v1"
)
SESSION_LOCK_OWNER = (
    "ops.integrated_paper_shadow_observation_wallclock_session_execution_v1.session_lock_v1"
)
BUNDLE_VERIFIER_OWNER = (
    "ops.phase_9_2_restart_recovery_session_contract_and_productive_harness_v1.verifier_v1"
)

CONTROLLED_RESTART_EXIT_CODE = 82
EXIT_CODE_82_CLASSIFICATION = "CONTROLLED_SEGMENT_TRANSITION"
MINIMUM_PRE_RESTART_DISTINCT_OBSERVATIONS = 30
PLANNED_RESTART_TEST_CONTRACT_SECONDS = 3600

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

AUTHORIZATION_LEDGER_FILENAME = "step3_executor_authorization_consumption_ledger_v1.jsonl"
CONFIRM_TOKEN_LEDGER_FILENAME = "step3_executor_confirm_token_consumption_ledger_v1.jsonl"
SESSION_LOCK_NAME = "phase_9_2_step3_restart_recovery_session_lock_v1"

FORBIDDEN_CONFIRM_TOKEN_ARGV_FLAGS = (
    "--confirm-token",
    "--confirm_token",
    "--confirm-token-plaintext",
)
FORBIDDEN_CONFIRM_TOKEN_ENV_KEYS = (
    "PEAK_TRADE_STEP3_EXECUTOR_CONFIRM_TOKEN",
    "CONFIRM_TOKEN",
    "CONFIRM_TOKEN_PLAINTEXT",
)

SESSION_MANIFEST_SCHEMA = "phase_9_2_step_3_governed_restart_recovery_session_executor_manifest.v1"

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
    "Step-3 Surface CLI (validation + offline campaign; real network fail-closed)",
    "Binding segment_runner + Session-GO + harness verifier exist",
    "NO separate productive Step-3 executor with NETWORK_SESSION_GO side-effect boundary",
]

CALL_GRAPH_AFTER = [
    "Future Owner Session Command",
    "Canonical Authorization Issuance (separate; not this capability)",
    "Hidden PTY Confirm-Token Handoff binding",
    "Step-3 Productive Executor",
    "Step-3 Execution Surface Validation (consumed, unchanged fail-closed)",
    "Session Lock / Single Writer",
    "Governed Public-MD Session Start (ephemeral NETWORK_SESSION_GO only)",
    "Pre-Restart State and Digest Capture",
    "Controlled Process Restart (exit 82)",
    "Recovery Entrypoint",
    "Reconciliation Before Alpha",
    "Canonical State Reload",
    "Duplicate-Effect Protection",
    "Post-Recovery State and Digest Verification",
    "Evidence / Manifest Finalization",
    "Session Verifier",
    "REAL_NETWORK remains fail-closed under permanent constants in this capability",
]


def repo_root_v1() -> Path:
    return Path(__file__).resolve().parents[3]
