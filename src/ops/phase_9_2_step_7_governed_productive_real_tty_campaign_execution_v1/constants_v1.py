"""Constants for Step-7 productive Real-TTY campaign execution owner.

Layering (fail-closed separation):
  BINDING_CAMPAIGN_EXECUTOR — always forbids Real-Network
  PATH_IMPLEMENTATION — structural may_start only; never starts network
  REAL_TTY_CAMPAIGN_OWNER (this package) — owns campaign may-start + invoke edge
"""

from __future__ import annotations

from pathlib import Path

CAPABILITY_ID = "PHASE_9_2_STEP_7_PRODUCTIVE_REAL_TTY_CAMPAIGN_EXECUTION_OWNER_IMPLEMENTATION_V1"
TARGET_CAMPAIGN_CAPABILITY_ID = (
    "PHASE_9_2_STEP_7_REPEATED_MULTI_SESSION_CONTINUITY_CAMPAIGN_EXECUTION_V1"
)
TARGET_CAMPAIGN_CAPABILITY_ID_ALIAS = (
    "PHASE_9_2_STEP_7_REPEATED_MULTI_SESSION_CONTINUITY_CAMPAIGN_V1"
)
SCHEMA_VERSION = "phase_9_2_step_7_productive_real_tty_campaign_execution_owner.v1"
PRODUCER_VERSION = SCHEMA_VERSION
PACKAGE_MARKER = (
    "PHASE_9_2_STEP_7_PRODUCTIVE_REAL_TTY_CAMPAIGN_EXECUTION_OWNER_IMPLEMENTATION_V1=true"
)
OWNER = "ops.phase_9_2_step_7_governed_productive_real_tty_campaign_execution_v1"
AUTHORITY_OWNER = OWNER

BINDING_CAMPAIGN_CAPABILITY_ID = (
    "PHASE_9_2_STEP_7_REPEATED_MULTI_SESSION_CONTINUITY_CAMPAIGN_"
    "BINDING_AND_VERIFIER_IMPLEMENTATION_V1"
)
PATH_IMPLEMENTATION_CAPABILITY_ID = (
    "PHASE_9_2_STEP_7_PRODUCTIVE_CAMPAIGN_EXECUTION_PATH_IMPLEMENTATION_V1"
)
BINDING_PACKAGE = "ops.phase_9_2_step_7_repeated_multi_session_continuity_campaign_binding_v1"
PATH_PACKAGE = "ops.phase_9_2_step_7_productive_campaign_execution_path_v1"
STEP6_PATTERN_OWNER = "ops.phase_9_2_step_6_governed_productive_real_network_session_execution_v1"

SESSION_LADDER_STEP = "MULTI_SESSION_CONTINUITY_CAMPAIGN"
SESSION_SCOPE = "PHASE_9_2_MULTI_SESSION_CONTINUITY_CAMPAIGN"
CAMPAIGN_ID = "phase_9_2_multi_session_continuity_campaign_v1"
TARGET_SESSION_ID_PREFIX = "phase_9_2_public_md_multi_session_continuity_session_v1"

CONFIG_RELATIVE_PATH = (
    "config/ops/phase_9_2_step_7_governed_productive_real_tty_campaign_execution_v1.json"
)
CAMPAIGN_CONTRACT_RELATIVE_PATH = (
    "config/ops/phase_9_2_public_md_multi_session_continuity_campaign_contract_v1.json"
)
PATH_CONFIG_RELATIVE_PATH = "config/ops/phase_9_2_step_7_productive_campaign_execution_path_v1.json"
PRODUCTIVE_ENTRYPOINT_PATH = (
    "scripts/ops/run_phase_9_2_step_7_governed_productive_real_tty_campaign_execution_v1.py"
)
REAL_TTY_OPERATOR_ENTRYPOINT_PATH = (
    "scripts/ops/run_phase_9_2_step_7_real_tty_campaign_operator_entrypoint_v1.py"
)
DELEGATED_CURSOR_OPERATOR_ENTRYPOINT_PATH = (
    "scripts/ops/run_phase_9_2_step_7_delegated_cursor_secure_confirm_"
    "campaign_operator_entrypoint_v1.py"
)
PATH_ENTRYPOINT_PATH = "scripts/ops/run_phase_9_2_step_7_productive_campaign_execution_path_v1.py"
BINDING_ENTRYPOINT_PATH = (
    "scripts/ops/run_phase_9_2_step_7_repeated_multi_session_continuity_campaign_binding_v1.py"
)
CAPABILITY_DOC_RELATIVE_PATH = (
    "docs/ops/specs/CAPABILITY_PHASE_9_2_STEP_7_PRODUCTIVE_REAL_TTY_"
    "CAMPAIGN_EXECUTION_OWNER_IMPLEMENTATION_V1.md"
)
EVIDENCE_DIRNAME = "capability_phase_9_2_step_7_productive_real_tty_campaign_execution_owner_v1"

MULTI_SESSION_REQUIREMENT_OPERATOR = ">"
MULTI_SESSION_REQUIREMENT_OPERAND = 1
MULTI_SESSION_REQUIREMENT_EXPRESSION = ">1"
DEFAULT_PLANNED_SESSION_COUNT = 2

CANONICAL_WALLCLOCK_RUNNER = (
    "src.ops.integrated_paper_shadow_productive_authorization_issuance_and_real_network_"
    "execution_v1.productive_run_entrypoint_v1.run_productive_wallclock_session_v1"
)
CANONICAL_PUBLIC_MD_FETCHER = (
    "src.ops.integrated_paper_shadow_productive_authorization_issuance_and_real_network_"
    "execution_v1.real_http_fetcher_v1.make_real_eea_public_md_fetcher_v1"
)
STEP7_CAMPAIGN_HARNESS_OWNER = (
    "ops.phase_9_2_step_7_repeated_multi_session_continuity_campaign_binding_v1.campaign_harness_v1"
)
STEP7_CAMPAIGN_VERIFIER_OWNER = (
    "ops.phase_9_2_step_7_repeated_multi_session_continuity_campaign_binding_v1."
    "campaign_verifier_v1"
)
STEP7_CAMPAIGN_BUNDLE_OWNER = (
    "ops.phase_9_2_step_7_repeated_multi_session_continuity_campaign_binding_v1.campaign_bundle_v1"
)
STEP3_RESTART_OWNER = (
    "ops.phase_9_2_step_3_governed_productive_real_network_restart_recovery_session_execution_v1"
)
STEP4_RECONNECT_OWNER = (
    "ops.phase_9_2_productive_public_md_rate_limit_reconnect_wallclock_binding_v1"
)
STEP6_STALE_ADVERSE_OWNER = (
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
DELEGATED_CURSOR_SECURE_CONFIRM_BROKER_OWNER = (
    "ops.phase_9_2_step_7_governed_productive_real_tty_campaign_execution_v1."
    "delegated_cursor_secure_confirm_broker_v1"
)
STEP5_NETWORK_SESSION_GO_PATTERN_OWNER = (
    "ops.phase_9_2_step_5_productive_real_network_session_activation_and_wiring_v1."
    "network_session_go_v1"
)

# Dual authorization channels for Step-7 campaign confirm.
AUTH_CHANNEL_REAL_TTY_HUMAN_CONFIRM = "REAL_TTY_HUMAN_CONFIRM"
AUTH_CHANNEL_DELEGATED_CURSOR_SECURE_CONFIRM = "DELEGATED_CURSOR_SECURE_CONFIRM"
ALLOWED_AUTHORIZATION_CHANNELS = frozenset(
    {
        AUTH_CHANNEL_REAL_TTY_HUMAN_CONFIRM,
        AUTH_CHANNEL_DELEGATED_CURSOR_SECURE_CONFIRM,
    }
)
CONFIRM_TOKEN_ROLE_EPHEMERAL_EXECUTION_LATCH = "EPHEMERAL_EXECUTION_LATCH"
DEFAULT_AUTHORIZATION_CHANNEL = AUTH_CHANNEL_REAL_TTY_HUMAN_CONFIRM

MODE_PROVE_IMPLEMENTATION_ONLY = "PROVE_IMPLEMENTATION_ONLY"
MODE_GOVERNED_MULTI_SESSION_CAMPAIGN = "GOVERNED_MULTI_SESSION_CAMPAIGN"

# Permanent constants — never flip. Real start requires ephemeral GO + invoke.
NETWORK_SESSION_ALLOWED = False
NETWORK_SESSION_GO_DEFAULT = False
NETWORK_SESSION_GO_PERSISTED = False
AUTHORIZATION_ISSUANCE_ALLOWED = False
AUTHORIZATION_CONSUMPTION_ALLOWED = False
CONFIRM_TOKEN_ISSUANCE_ALLOWED = False
CONFIRM_TOKEN_CONSUMPTION_ALLOWED = False
CONFIRM_TOKEN_MINTING_ALLOWED = False
CAMPAIGN_EXECUTION_ALLOWED = False
CAMPAIGN_EXECUTION_SIDE_EFFECTS_AUTHORIZED = False
REAL_NETWORK_REQUESTS_ALLOWED = False
PRODUCTIVE_NETWORK_SESSION_EXECUTION_AUTHORIZED = False
NO_PERMANENT_UNSCOPED_ENABLE_FLAG = True
NETWORK_SESSION_STARTED_BY_THIS_CAPABILITY = False
AUTHORIZATION_REUSE_FORBIDDEN = True
CONFIRM_TOKEN_REUSE_FORBIDDEN = True

PHASE_9_2_STEP_6_STATUS = "CLOSED_PASS"
PHASE_9_2_STEP_7_STATUS = "OPEN"
PHASE_9_2_SESSION_LADDER_COMPLETE = False
MULTI_SESSION_CONTINUITY_LADDER_STEP_CLOSED = False
CAPABILITY_CLOSED = False
CAMPAIGN_EXECUTED = False
STEP7_STARTED = False
STEP7_PRODUCTIVE_CAMPAIGN_EXECUTION_PATH_PRESENT = True
STEP7_PRODUCTIVE_CAMPAIGN_EXECUTION_PATH_ABSENT = False
STEP7_BINDING_ONLY_PRESERVED = True
STEP7_CAMPAIGN_HARNESS_BOUND = True
STEP7_CAMPAIGN_VERIFIER_PRESENT = True
STEP7_REAL_TTY_CAMPAIGN_OWNER_PRESENT = True
STEP7_PRODUCTIVE_CAMPAIGN_INVOKE_EDGE_PRESENT = True
STEP7_PRODUCTIVE_CAMPAIGN_INVOKE_EDGE_RUNTIME_REACHABLE = True
PRODUCTIVE_CAMPAIGN_INVOKE_SYMBOL = "execute_governed_step7_campaign_v1"
READY_FOR_SEPARATE_OWNER_GO_REAL_TTY_CAMPAIGN = True
READY_FOR_SEPARATE_OWNER_GO_DELEGATED_CURSOR_CAMPAIGN = True
AUTH_CHANNEL_REAL_TTY_SUPPORTED = True
AUTH_CHANNEL_DELEGATED_CURSOR_SUPPORTED = True

GOVERNED_PUBLIC_MD_NETWORK_SCOPE = "okx_eea_futures_public_md_observe_v1"
EEA_PUBLIC_MD_HOST = "eea.okx.com"
NETWORK_ALLOWLIST = "OKX_EEA_PUBLIC_MARKET_DATA_ENDPOINTS_ONLY"
HTTP_METHOD_ALLOWLIST = "GET_ONLY"
NETWORK_MODE = "PUBLIC_MD_GET_ONLY"

FORBIDDEN_NETWORK_SESSION_GO_ENV_KEYS = (
    "NETWORK_SESSION_GO",
    "PEAK_TRADE_NETWORK_SESSION_GO",
    "PEAK_TRADE_STEP7_NETWORK_SESSION_GO",
    "PEAK_TRADE_STEP7_CAMPAIGN_NETWORK_SESSION_GO",
    "OWNER_NETWORK_SESSION_GO",
)
FORBIDDEN_CONFIRM_TOKEN_ARGV_FLAGS = (
    "--confirm-token",
    "--confirm_token",
    "--confirm-token-plaintext",
)
FORBIDDEN_CONFIRM_TOKEN_ENV_KEYS = (
    "PEAK_TRADE_STEP7_CONFIRM_TOKEN",
    "PEAK_TRADE_STEP7_CAMPAIGN_CONFIRM_TOKEN",
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

CALL_GRAPH_BEFORE = [
    "BINDING_CAMPAIGN_EXECUTOR forever fail-closed",
    "PATH_IMPLEMENTATION structural may_start only (never starts)",
    "HARD_STOP: MISSING_PRODUCTIVE_STEP7_REAL_TTY_CAMPAIGN_START_EXECUTION_OWNER",
]

CALL_GRAPH_AFTER = [
    "BINDING_CAMPAIGN_EXECUTOR preserved fail-closed (unchanged)",
    "PATH_IMPLEMENTATION preserved (unchanged; never starts)",
    "REAL_TTY_CAMPAIGN_OWNER present: execute_governed_step7_campaign_v1",
    "dual confirm channels: REAL_TTY_HUMAN_CONFIRM | DELEGATED_CURSOR_SECURE_CONFIRM",
    "campaign_may_start + Owner-GO + NETWORK_SESSION_GO + channel-bound confirm latch",
    "TOKEN_ROLE=EPHEMERAL_EXECUTION_LATCH (not human TTY presence proof)",
    "MULTI_SESSION_REQUIREMENT_EXPRESSION=>1",
    "reuse Step-7 harness + verifier + per-session evidence + campaign bundle",
    "reuse Step-3 restart / Step-4 reconnect / Step-6 stale-adverse",
    "exactly N wallclock invokes under TARGET_CAMPAIGN_CAPABILITY_ID (N>1)",
    "THIS_CAPABILITY: NETWORK_SESSION_STARTED=false (prove/materialize/tests use doubles)",
    "PHASE_9_2_STEP_7_STATUS remains OPEN until later Owner-GO campaign verifier PASS",
]

LATER_CAMPAIGN_INVOCATION = (
    "REAL_TTY: scripts/ops/run_phase_9_2_step_7_real_tty_campaign_operator_entrypoint_v1.py "
    "--owner-go --operator-authorization-explicit --network-session-go "
    "--request-real-network --planned-session-count 2 "
    f"--expected-capability-id {TARGET_CAMPAIGN_CAPABILITY_ID} "
    "(Hidden-PTY getpass; AUTHORIZATION_CHANNEL=REAL_TTY_HUMAN_CONFIRM) | "
    "CURSOR: scripts/ops/run_phase_9_2_step_7_delegated_cursor_secure_confirm_"
    "campaign_operator_entrypoint_v1.py "
    "--owner-go --operator-authorization-explicit --network-session-go "
    "--request-real-network --authorization-valid --planned-session-count 2 "
    f"--expected-capability-id {TARGET_CAMPAIGN_CAPABILITY_ID} "
    "(DELEGATED_CURSOR_SECURE_CONFIRM; EPHEMERAL_EXECUTION_LATCH; "
    "HEAD==origin/main + tracked worktree clean; digest-only evidence; "
    "this implementation capability never starts network)"
)


def repo_root_v1() -> Path:
    return Path(__file__).resolve().parents[3]


def multi_session_requirement_satisfied_v1(session_count: int) -> bool:
    """True iff campaign contains strictly more than one governed session."""
    return int(session_count) > int(MULTI_SESSION_REQUIREMENT_OPERAND)


def is_target_campaign_capability_id_v1(capability_id: str) -> bool:
    value = str(capability_id or "")
    return value in {TARGET_CAMPAIGN_CAPABILITY_ID, TARGET_CAMPAIGN_CAPABILITY_ID_ALIAS}
