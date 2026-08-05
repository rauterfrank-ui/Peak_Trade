"""Constants for real Public-MD restart/recovery wallclock binding."""

from __future__ import annotations

from pathlib import Path

CAPABILITY_ID = "PHASE_9_2_PRODUCTIVE_PUBLIC_MD_RESTART_RECOVERY_REAL_NETWORK_WALLCLOCK_BINDING_V1"
SCHEMA_VERSION = "phase_9_2_productive_public_md_restart_recovery_real_network_wallclock_binding.v1"
PRODUCER_VERSION = SCHEMA_VERSION
PACKAGE_MARKER = (
    "PHASE_9_2_PRODUCTIVE_PUBLIC_MD_RESTART_RECOVERY_REAL_NETWORK_WALLCLOCK_BINDING_V1=true"
)
OWNER = "ops.phase_9_2_productive_public_md_restart_recovery_real_network_wallclock_binding_v1"
AUTHORITY_OWNER = OWNER

PREDECESSOR_CAPABILITY_ID = (
    "PHASE_9_2_PRODUCTIVE_RESTART_RECOVERY_POST_UNLOCK_RUNTIME_INVOCATION_V1"
)
PREDECESSOR_PR = 5668

CONFIG_RELATIVE_PATH = "config/ops/phase_9_2_productive_public_md_restart_recovery_real_network_wallclock_binding_v1.json"
EVIDENCE_DIRNAME = (
    "capability_phase_9_2_productive_public_md_restart_recovery_real_network_wallclock_binding_v1"
)

# Reuse sole productive entrypoint / session identity from prior Phase-9.2 surfaces.
PRODUCTIVE_ENTRYPOINT_ID = "PHASE_9_2_PRODUCTIVE_PUBLIC_MD_RESTART_RECOVERY_NETWORK_ENTRYPOINT_V1"
PRODUCTIVE_ENTRYPOINT_PATH = (
    "scripts/ops/run_phase_9_2_productive_public_md_restart_recovery_network_entrypoint_v1.py"
)
BINDING_CLI_PATH = "scripts/ops/run_phase_9_2_productive_public_md_restart_recovery_real_network_wallclock_binding_v1.py"

TARGET_SESSION_ID = "phase_9_2_public_md_restart_recovery_session_v1"
RESTART_CAMPAIGN_ID = "phase_9_2_restart_recovery_campaign_v1"
DURABLE_STATE_LINEAGE_ID = "phase_9_2_restart_durable_state_lineage_v1"
CONFIRMATION_SESSION_ID = "phase_9_2_restart_confirmation_session_v1"
CANONICAL_INSTRUMENT_ID = "ETH-USD_UM_XPERP-310404"

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
CANONICAL_RESTART_HARNESS = (
    "src.ops.phase_9_2_restart_recovery_session_contract_and_productive_harness_v1"
)
SESSION_GO_AUTHORITY = "src.ops.phase_9_2_productive_restart_recovery_session_go_capability_v1"
SEGMENT_AUTH_AUTHORITY = (
    "src.ops.phase_9_2_productive_public_md_restart_recovery_network_entrypoint_v1"
    ".segment_authorization_v1"
)
AUTHORIZATION_LEDGER_AUTHORITY = (
    "src.ops.phase_9_2_restart_recovery_session_contract_and_productive_harness_v1.authorization_v1"
)
BUNDLE_VERIFIER = (
    "src.ops.phase_9_2_restart_recovery_session_contract_and_productive_harness_v1.verifier_v1"
)

# Permanent unscoped enable remains false; unlock only via bound ACTIVE Session-GO.
NETWORK_SESSION_ALLOWED_BY_CAPABILITY_CONFIG = False
AUTHORIZATION_ISSUANCE_ALLOWED_BY_CAPABILITY_CONFIG = False
AUTHORIZATION_CONSUMPTION_ALLOWED_BY_CAPABILITY_CONFIG = False
PRODUCTIVE_NETWORK_SESSION_EXECUTION_AUTHORIZED = False
NO_PERMANENT_UNSCOPED_ENABLE_FLAG = True

PRE_PROCESS_MARKER_FILENAME = "phase_9_2_pre_restart_process_marker_v1.json"
BINDING_MANIFEST_FILENAME = "real_network_wallclock_binding_manifest_v1.json"
SEGMENT_RESULT_FILENAME = "real_network_segment_result_v1.json"

CORE_LOGIC_CHANGE = False
MASTER_V2_CHANGE = False
DOUBLE_PLAY_CHANGE = False
BULL_BEAR_CHANGE = False
DYNAMIC_SCOPE_LOGIC_CHANGE = False
CONFIRMATION_SEMANTICS_CHANGE = False
RISK_CHANGE = False
SAFETY_CHANGE = False
DASHBOARD_AUTHORITY_EFFECT = "NONE"
DASHBOARD_READ_ONLY_CONSUMER = True

FORBIDDEN_CONFIRM_TOKEN_ARGV_FLAGS = (
    "--confirm-token",
    "--confirm_token",
    "--confirm-token-plaintext",
)

REAL_NETWORK_ENV = "PEAK_TRADE_PSO_WALLCLOCK_ALLOW_REAL_NETWORK"


def repo_root_v1() -> Path:
    return Path(__file__).resolve().parents[3]
