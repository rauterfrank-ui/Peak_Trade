"""Constants for PHASE_9_2_PRODUCTIVE_PUBLIC_MD_RESTART_RECOVERY_NETWORK_ENTRYPOINT_V1."""

from __future__ import annotations

from pathlib import Path

CAPABILITY_ID = "PHASE_9_2_PRODUCTIVE_PUBLIC_MD_RESTART_RECOVERY_NETWORK_ENTRYPOINT_V1"
SCHEMA_VERSION = "phase_9_2_productive_public_md_restart_recovery_network_entrypoint.v1"
PRODUCER_VERSION = "phase_9_2_productive_public_md_restart_recovery_network_entrypoint.v1"
PACKAGE_MARKER = "PHASE_9_2_PRODUCTIVE_PUBLIC_MD_RESTART_RECOVERY_NETWORK_ENTRYPOINT_V1=true"
OWNER = "ops.phase_9_2_productive_public_md_restart_recovery_network_entrypoint_v1"
AUTHORITY_OWNER = OWNER

PREDECESSOR_CAPABILITY_ID = "PHASE_9_2_RESTART_RECOVERY_SESSION_CONTRACT_AND_PRODUCTIVE_HARNESS_V1"
PREDECESSOR_PR = 5665
PREDECESSOR_MERGE_SHA = "a2b131c518df013d2498f9b312d3c64631f59e16"

CONFIG_RELATIVE_PATH = (
    "config/ops/phase_9_2_productive_public_md_restart_recovery_network_entrypoint_v1.json"
)
EVIDENCE_DIRNAME = (
    "capability_phase_9_2_productive_public_md_restart_recovery_network_entrypoint_v1"
)

TARGET_SESSION_ID = "phase_9_2_public_md_restart_recovery_session_v1"
RESTART_CAMPAIGN_ID = "phase_9_2_restart_recovery_campaign_v1"
DURABLE_STATE_LINEAGE_ID = "phase_9_2_restart_durable_state_lineage_v1"
CONFIRMATION_SESSION_ID = "phase_9_2_restart_confirmation_session_v1"
CANONICAL_INSTRUMENT_ID = "ETH-USD_UM_XPERP-310404"

SEGMENT_ROLE_PRE = "PRE_RESTART"
SEGMENT_ROLE_POST = "POST_RESTART"
SEGMENT_ROLES = (SEGMENT_ROLE_PRE, SEGMENT_ROLE_POST)
SEGMENT_PLAN = (SEGMENT_ROLE_PRE, SEGMENT_ROLE_POST)
SEGMENT_COUNT = 2

SEGMENT_PRE_ID = "segment_pre_restart_v1"
SEGMENT_POST_ID = "segment_post_restart_v1"
SEGMENT_PRE_PURPOSE = "INITIAL_RUN_AND_CHECKPOINT"
SEGMENT_POST_PURPOSE = "CONTROLLED_RESTART_AND_RECOVERY"

CONTROLLED_RESTART_EXIT_CODE = 82
CONTROLLED_RESTART_REASON = "CONTROLLED_PRE_RESTART_SEGMENT_COMPLETE"
EXIT_CODE_82_CLASSIFICATION = "CONTROLLED_SEGMENT_TRANSITION"

MINIMUM_PRE_RESTART_DISTINCT_OBSERVATIONS = 30
REQUIRED_RECONCILIATION_BEFORE_ALPHA = True

# Implementation defaults: entrypoint exists, session not authorized here.
NETWORK_SESSION_ALLOWED = False
AUTHORIZATION_ISSUANCE_ALLOWED = False
AUTHORIZATION_CONSUMPTION_ALLOWED = False
RUNTIME_SESSION_ALLOWED = False
PRODUCTIVE_NETWORK_SESSION_EXECUTION_ALLOWED = False
PUBLIC_MARKET_DATA_ALLOWED_FOR_TESTS = False

# Env gates required for a later Owner-authorized productive session (default off).
PRODUCTIVE_SESSION_GO_ENV = "PEAK_TRADE_PHASE92_RESTART_RECOVERY_SESSION_GO"
REAL_NETWORK_ENV = "PEAK_TRADE_PSO_WALLCLOCK_ALLOW_REAL_NETWORK"

CORE_LOGIC_CHANGE = False
MASTER_V2_CHANGE = False
DOUBLE_PLAY_CHANGE = False
BULL_BEAR_CHANGE = False
DYNAMIC_SCOPE_LOGIC_CHANGE = False
CONFIRMATION_SEMANTICS_CHANGE = False
VOLATILITY_POLICY_CHANGE = False
RISK_CHANGE = False
SAFETY_CHANGE = False
EXECUTION_ECONOMICS_CHANGE = False

LIVE_PATH_CHANGED = False
TESTNET_PATH_CHANGED = False
EXCHANGE_CREDENTIAL_PATH_CHANGED = False

EEA_PUBLIC_MD_HOST = "eea.okx.com"
NETWORK_ALLOWLIST = "OKX_EEA_PUBLIC_MARKET_DATA_ENDPOINTS_ONLY"
HTTP_METHOD_ALLOWLIST = "GET_ONLY"
RUNTIME_MODE = "PUBLIC_MD_NO_ORDER_INTERNAL_SIMULATED_EXECUTION"

ALLOWED_SIDE_EFFECTS = (
    "PUBLIC_MD_GET_EEA_ALLOWLISTED",
    "INTERNAL_SIMULATED_EXECUTION",
    "LOCAL_PERSISTENCE_UNDER_SESSION_ROOT",
    "LOCAL_EVIDENCE_UNDER_SESSION_ROOT",
)
FORBIDDEN_SIDE_EFFECTS = (
    "LIVE_ORDERS",
    "TESTNET_ORDERS",
    "PAPER_EXCHANGE_ORDERS",
    "EXCHANGE_CREDENTIAL_USE",
    "REAL_CAPITAL_MOVEMENT",
    "PRIVATE_ENDPOINT_ACCESS",
    "AUTH_HEADER_TRANSMISSION",
)

SEGMENT_AUTH_ENVELOPE_SCHEMA = "phase_9_2_restart_segment_authorization_envelope.v1"
SEGMENT_AUTH_ENVELOPE_FILENAME = "segment_authorization_envelope_v1.json"
ORCHESTRATION_MANIFEST_FILENAME = "productive_restart_orchestration_manifest_v1.json"
ORCHESTRATION_LOCK_FILENAME = "productive_restart_orchestration.lock"

DEFAULT_PRE_SEGMENT_MAX_DURATION_SECONDS = 180
DEFAULT_POST_SEGMENT_MAX_DURATION_SECONDS = 180

WALLCLOCK_RUNNER = (
    "src.ops.integrated_paper_shadow_productive_authorization_issuance_and_real_network_"
    "execution_v1.productive_run_entrypoint_v1"
)
OFFLINE_HARNESS = "src.ops.phase_9_2_restart_recovery_session_contract_and_productive_harness_v1"
CANONICAL_AUTH_ISSUANCE = (
    "src.ops.integrated_paper_shadow_productive_authorization_issuance_and_real_network_"
    "execution_v1"
)
CANONICAL_CHECKPOINT_CONTRACT = (
    "src.ops.phase_9_2_restart_recovery_session_contract_and_productive_harness_v1"
    ".state_root_adapter_v1"
)
CANONICAL_VERIFIER = (
    "src.ops.phase_9_2_restart_recovery_session_contract_and_productive_harness_v1.verifier_v1"
)


def repo_root_v1() -> Path:
    return Path(__file__).resolve().parents[3]
