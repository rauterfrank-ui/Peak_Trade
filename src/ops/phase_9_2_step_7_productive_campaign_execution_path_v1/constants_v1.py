"""Constants for Step-7 productive campaign execution path implementation.

Distinct from the Binding-only campaign package
(`phase_9_2_step_7_repeated_multi_session_continuity_campaign_binding_v1`),
which permanently forbids Real-Network side effects.
"""

from __future__ import annotations

from pathlib import Path

CAPABILITY_ID = "PHASE_9_2_STEP_7_PRODUCTIVE_CAMPAIGN_EXECUTION_PATH_IMPLEMENTATION_V1"
SCHEMA_VERSION = "phase_9_2_step_7_productive_campaign_execution_path.v1"
PRODUCER_VERSION = SCHEMA_VERSION
PACKAGE_MARKER = "PHASE_9_2_STEP_7_PRODUCTIVE_CAMPAIGN_EXECUTION_PATH_IMPLEMENTATION_V1=true"
OWNER = "ops.phase_9_2_step_7_productive_campaign_execution_path_v1"
AUTHORITY_OWNER = OWNER

BINDING_CAMPAIGN_CAPABILITY_ID = (
    "PHASE_9_2_STEP_7_REPEATED_MULTI_SESSION_CONTINUITY_CAMPAIGN_"
    "BINDING_AND_VERIFIER_IMPLEMENTATION_V1"
)
BINDING_CAMPAIGN_PACKAGE = (
    "ops.phase_9_2_step_7_repeated_multi_session_continuity_campaign_binding_v1"
)
BINDING_CAMPAIGN_ROLE = "BINDING_CAMPAIGN_EXECUTOR"
PRODUCTIVE_CAMPAIGN_EXECUTOR_ROLE = "PRODUCTIVE_CAMPAIGN_EXECUTOR"

TARGET_CAMPAIGN_CAPABILITY_ID = "PHASE_9_2_STEP_7_REPEATED_MULTI_SESSION_CONTINUITY_CAMPAIGN_V1"
PREDECESSOR_CAPABILITY_ID = "PHASE_9_2_STEP_6_GOVERNED_PRODUCTIVE_REAL_NETWORK_SESSION_EXECUTION_V1"

SESSION_LADDER_STEP = "MULTI_SESSION_CONTINUITY_CAMPAIGN"
SESSION_SCOPE = "PHASE_9_2_MULTI_SESSION_CONTINUITY_CAMPAIGN"
CAMPAIGN_ID = "phase_9_2_multi_session_continuity_campaign_v1"
TARGET_SESSION_ID_PREFIX = "phase_9_2_public_md_multi_session_continuity_session_v1"

CONFIG_RELATIVE_PATH = "config/ops/phase_9_2_step_7_productive_campaign_execution_path_v1.json"
CAMPAIGN_CONTRACT_RELATIVE_PATH = (
    "config/ops/phase_9_2_public_md_multi_session_continuity_campaign_contract_v1.json"
)
PRODUCTIVE_ENTRYPOINT_PATH = (
    "scripts/ops/run_phase_9_2_step_7_productive_campaign_execution_path_v1.py"
)
BINDING_ENTRYPOINT_PATH = (
    "scripts/ops/run_phase_9_2_step_7_repeated_multi_session_continuity_campaign_binding_v1.py"
)
EVIDENCE_DIRNAME = "capability_phase_9_2_step_7_productive_campaign_execution_path_v1"
CAPABILITY_DOC_RELATIVE_PATH = (
    "docs/ops/specs/CAPABILITY_PHASE_9_2_STEP_7_PRODUCTIVE_CAMPAIGN_"
    "EXECUTION_PATH_IMPLEMENTATION_V1.md"
)

# Multi-session requirement expressed without inventing a governance count.
MULTI_SESSION_REQUIREMENT_OPERATOR = ">"
MULTI_SESSION_REQUIREMENT_OPERAND = 1
MULTI_SESSION_REQUIREMENT_EXPRESSION = ">1"

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
STEP5_NETWORK_SESSION_GO_PATTERN_OWNER = (
    "ops.phase_9_2_step_5_productive_real_network_session_activation_and_wiring_v1."
    "network_session_go_v1"
)

MODE_PROVE_PATH_ONLY = "PROVE_PATH_ONLY"
MODE_GOVERNED_MULTI_SESSION_CAMPAIGN = "GOVERNED_MULTI_SESSION_CAMPAIGN"

# Permanent constants — never flip. Real network requires later separate Owner-GO.
NETWORK_SESSION_ALLOWED = False
NETWORK_SESSION_GO_DEFAULT = False
NETWORK_SESSION_GO_PERSISTED = False
AUTHORIZATION_ISSUANCE_ALLOWED = False
AUTHORIZATION_CONSUMPTION_ALLOWED = False
CONFIRM_TOKEN_ISSUANCE_ALLOWED = False
CONFIRM_TOKEN_CONSUMPTION_ALLOWED = False
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

GOVERNED_PUBLIC_MD_NETWORK_SCOPE = "okx_eea_futures_public_md_observe_v1"
EEA_PUBLIC_MD_HOST = "eea.okx.com"
NETWORK_ALLOWLIST = "OKX_EEA_PUBLIC_MARKET_DATA_ENDPOINTS_ONLY"
HTTP_METHOD_ALLOWLIST = "GET_ONLY"
NETWORK_MODE = "PUBLIC_MD_GET_ONLY"

FORBIDDEN_NETWORK_SESSION_GO_ENV_KEYS = (
    "NETWORK_SESSION_GO",
    "PEAK_TRADE_NETWORK_SESSION_GO",
    "PEAK_TRADE_STEP7_NETWORK_SESSION_GO",
    "PEAK_TRADE_STEP7_PRODUCTIVE_CAMPAIGN_NETWORK_SESSION_GO",
    "OWNER_NETWORK_SESSION_GO",
)
FORBIDDEN_CONFIRM_TOKEN_ARGV_FLAGS = (
    "--confirm-token",
    "--confirm_token",
    "--confirm-token-plaintext",
)
FORBIDDEN_CONFIRM_TOKEN_ENV_KEYS = (
    "PEAK_TRADE_STEP7_CONFIRM_TOKEN",
    "PEAK_TRADE_STEP7_PRODUCTIVE_CONFIRM_TOKEN",
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
    "BINDING_CAMPAIGN_EXECUTOR wire-harness / verify-bundle",
    "REAL_NETWORK_SESSION_FORBIDDEN_IN_THIS_BINDING_CAPABILITY",
    "PRODUCTIVE_NETWORK_SESSION_EXECUTION_AUTHORIZED=false",
    "STEP7_PRODUCTIVE_CAMPAIGN_EXECUTION_PATH_ABSENT=true",
    "HARD_STOP: no Owner-GO-capable productive Step-7 campaign path",
]

CALL_GRAPH_AFTER = [
    "BINDING_CAMPAIGN_EXECUTOR preserved fail-closed (unchanged)",
    "PRODUCTIVE_CAMPAIGN_EXECUTOR package present",
    "ephemeral NETWORK_SESSION_GO gate (parameter-only; default false)",
    "reuse Step-7 campaign harness + verifier + per-session evidence",
    "reuse Step-3 restart / Step-4 reconnect / Step-6 stale-adverse",
    "reuse Public-MD-only boundary (orders/credentials unreachable)",
    "reuse canonical wallclock / productive runtime owner",
    "Hidden-PTY confirm handoff bound for later campaign only (no mint here)",
    "MULTI_SESSION_REQUIREMENT_EXPRESSION=>1",
    "campaign_may_start=true only under later separate Owner-GO campaign gates",
    "THIS_CAPABILITY: NETWORK_SESSION_STARTED=false",
    "PHASE_9_2_STEP_7_STATUS remains OPEN until later campaign verifier PASS",
]

LATER_CAMPAIGN_INVOCATION = (
    "scripts/ops/run_phase_9_2_step_7_productive_campaign_execution_path_v1.py "
    "execute-governed-campaign --owner-go --operator-authorization-explicit "
    "--network-session-go --request-real-network "
    "(requires separate Owner-GO Real-TTY campaign capability; "
    "confirm token via Hidden-PTY only in that later campaign; "
    "this implementation capability never starts network)"
)


def repo_root_v1() -> Path:
    return Path(__file__).resolve().parents[3]


def multi_session_requirement_satisfied_v1(session_count: int) -> bool:
    """True iff campaign contains strictly more than one governed session."""
    return int(session_count) > int(MULTI_SESSION_REQUIREMENT_OPERAND)
