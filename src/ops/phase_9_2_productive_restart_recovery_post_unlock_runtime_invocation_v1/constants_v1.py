"""Constants for PHASE_9_2_PRODUCTIVE_RESTART_RECOVERY_POST_UNLOCK_RUNTIME_INVOCATION_V1."""

from __future__ import annotations

from pathlib import Path

CAPABILITY_ID = "PHASE_9_2_PRODUCTIVE_RESTART_RECOVERY_POST_UNLOCK_RUNTIME_INVOCATION_V1"
SCHEMA_VERSION = "phase_9_2_productive_restart_recovery_post_unlock_runtime_invocation.v1"
PRODUCER_VERSION = "phase_9_2_productive_restart_recovery_post_unlock_runtime_invocation.v1"
PACKAGE_MARKER = "PHASE_9_2_PRODUCTIVE_RESTART_RECOVERY_POST_UNLOCK_RUNTIME_INVOCATION_V1=true"
OWNER = "ops.phase_9_2_productive_restart_recovery_post_unlock_runtime_invocation_v1"
AUTHORITY_OWNER = OWNER

PREDECESSOR_CAPABILITY_ID = "PHASE_9_2_PRODUCTIVE_RESTART_RECOVERY_SESSION_GO_CAPABILITY_V1"
PREDECESSOR_MERGE_SHA = "9d81ed8bb6f4b34d461d8e47ed27bf6230786bb6"

CONFIG_RELATIVE_PATH = (
    "config/ops/phase_9_2_productive_restart_recovery_post_unlock_runtime_invocation_v1.json"
)
EVIDENCE_DIRNAME = (
    "capability_phase_9_2_productive_restart_recovery_post_unlock_runtime_invocation_v1"
)

# Existing productive Phase-9.2 network entrypoint remains the sole authority surface.
PRODUCTIVE_ENTRYPOINT_PATH = (
    "scripts/ops/run_phase_9_2_productive_public_md_restart_recovery_network_entrypoint_v1.py"
)
PRODUCTIVE_ENTRYPOINT_ID = "PHASE_9_2_PRODUCTIVE_PUBLIC_MD_RESTART_RECOVERY_NETWORK_ENTRYPOINT_V1"

# Canonical runners already present in repository (reuse-before-new).
CANONICAL_RUNTIME_RUNNER = (
    "src.ops.phase_9_2_productive_public_md_restart_recovery_network_entrypoint_v1"
    ".orchestrator_v1.run_offline_productive_restart_orchestration_v1"
)
CANONICAL_WALLCLOCK_RUNNER = (
    "src.ops.integrated_paper_shadow_productive_authorization_issuance_and_real_network_"
    "execution_v1.productive_run_entrypoint_v1.run_productive_wallclock_session_v1"
)
CANONICAL_RESTART_HARNESS = (
    "src.ops.phase_9_2_restart_recovery_session_contract_and_productive_harness_v1"
)
SESSION_GO_AUTHORITY = "src.ops.phase_9_2_productive_restart_recovery_session_go_capability_v1"
SESSION_GO_BUILDER = (
    "src.ops.phase_9_2_productive_restart_recovery_session_go_capability_v1"
    ".contract_v1.build_session_go_authority_v1"
)
AUTHORIZATION_AUTHORITY = (
    "src.ops.phase_9_2_restart_recovery_session_contract_and_productive_harness_v1.authorization_v1"
)
SESSION_LOCK_AUTHORITY = (
    "src.ops.phase_9_2_restart_recovery_session_contract_and_productive_harness_v1.lock_v1"
)

TARGET_SESSION_ID = "phase_9_2_public_md_restart_recovery_session_v1"

# This capability wires post-unlock invocation only; it does not authorize a live session.
NETWORK_SESSION_ALLOWED = False
AUTHORIZATION_ISSUANCE_ALLOWED = False
AUTHORIZATION_CONSUMPTION_ALLOWED = False
SESSION_EXECUTION_ALLOWED = False
RESTART_RECOVERY_EXECUTION_ALLOWED = False
PRODUCTIVE_NETWORK_SESSION_EXECUTION_ALLOWED = False

NO_PERMANENT_UNSCOPED_ENABLE_FLAG = True
PUBLIC_MD_ONLY = True
HTTP_GET_ONLY = True

CORE_LOGIC_CHANGE = False
MASTER_V2_CHANGE = False
DOUBLE_PLAY_CHANGE = False
BULL_BEAR_CHANGE = False
DYNAMIC_SCOPE_LOGIC_CHANGE = False
CONFIRMATION_SEMANTICS_CHANGE = False
RISK_CHANGE = False
SAFETY_CHANGE = False

LIVE_PATH_CHANGED = False
TESTNET_PATH_CHANGED = False
EXCHANGE_CREDENTIAL_PATH_CHANGED = False

INVOCATION_MANIFEST_FILENAME = "post_unlock_runtime_invocation_manifest_v1.json"
EXECUTE_MODE_FLAG = "execute"


def repo_root_v1() -> Path:
    return Path(__file__).resolve().parents[3]
