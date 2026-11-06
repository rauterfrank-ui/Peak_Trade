"""Constants for PHASE_9_2_PRODUCTIVE_RESTART_RECOVERY_SESSION_GO_CAPABILITY_V1."""

from __future__ import annotations

from pathlib import Path

CAPABILITY_ID = "PHASE_9_2_PRODUCTIVE_RESTART_RECOVERY_SESSION_GO_CAPABILITY_V1"
SCHEMA_VERSION = "phase_9_2_productive_restart_recovery_session_go.v1"
PRODUCER_VERSION = "phase_9_2_productive_restart_recovery_session_go.v1"
PACKAGE_MARKER = "PHASE_9_2_PRODUCTIVE_RESTART_RECOVERY_SESSION_GO_CAPABILITY_V1=true"
OWNER = "ops.phase_9_2_productive_restart_recovery_session_go_capability_v1"
AUTHORITY_OWNER = OWNER

PREDECESSOR_CAPABILITY_ID = "PHASE_9_2_PRODUCTIVE_PUBLIC_MD_RESTART_RECOVERY_NETWORK_ENTRYPOINT_V1"
PREDECESSOR_MERGE_SHA = "0cc5c91583733e37ccc2f4b3ad8696ec76b0c5d5"

CONFIG_RELATIVE_PATH = (
    "config/ops/phase_9_2_productive_restart_recovery_session_go_capability_v1.json"
)

TARGET_SESSION_ID = "phase_9_2_public_md_restart_recovery_session_v1"
TARGET_ENTRYPOINT_ID = "PHASE_9_2_PRODUCTIVE_PUBLIC_MD_RESTART_RECOVERY_NETWORK_ENTRYPOINT_V1"
TARGET_ENTRYPOINT_PATH = (
    "scripts/ops/run_phase_9_2_productive_public_md_restart_recovery_network_entrypoint_v1.py"
)
RESTART_RECOVERY_SCOPE = "PHASE_9_2_RESTART_RECOVERY_PRE_POST_SEGMENTS"
DEFAULT_MAX_SESSION_DURATION_SECONDS = 3600

ACTIVATION_STATUS_INACTIVE = "INACTIVE"
ACTIVATION_STATUS_ACTIVE = "ACTIVE"
ACTIVATION_STATUS_EXPIRED = "EXPIRED"
ACTIVATION_STATUS_REVOKED = "REVOKED"
ACTIVATION_STATUSES = (
    ACTIVATION_STATUS_INACTIVE,
    ACTIVATION_STATUS_ACTIVE,
    ACTIVATION_STATUS_EXPIRED,
    ACTIVATION_STATUS_REVOKED,
)

# Capability defaults: authority surface exists; no session execution here.
SESSION_EXECUTION_ALLOWED = False
NETWORK_SESSION_ALLOWED = False
AUTHORIZATION_ISSUANCE_ALLOWED = False
AUTHORIZATION_CONSUMPTION_ALLOWED = False
RESTART_RECOVERY_EXECUTION_ALLOWED = False

# Permanent unscoped enable remains forbidden; unlock only via bound ACTIVE Session-GO.
NO_PERMANENT_UNSCOPED_ENABLE_FLAG = True

PUBLIC_MD_ONLY = True
HTTP_GET_ONLY = True
PRIVATE_ENDPOINT_REACHABLE = False
AUTH_HEADER_PRESENT = False
EXCHANGE_CREDENTIALS_LOADED = False
REAL_EXECUTION_ADAPTER_CONSTRUCTED = False
EXCHANGE_ORDER_SUBMIT_REACHABLE = False

CORE_LOGIC_CHANGE = False
MASTER_V2_CHANGE = False
DOUBLE_PLAY_CHANGE = False
BULL_BEAR_CHANGE = False
DYNAMIC_SCOPE_LOGIC_CHANGE = False
CONFIRMATION_SEMANTICS_CHANGE = False
RISK_CHANGE = False
SAFETY_CHANGE = False

REQUIRED_FIELDS = (
    "schema_version",
    "capability_id",
    "session_go_id",
    "session_id",
    "expected_repository_sha",
    "expected_config_digest",
    "entrypoint_id",
    "entrypoint_path",
    "public_md_only",
    "http_get_only",
    "max_session_duration_seconds",
    "restart_recovery_scope",
    "issued_at",
    "not_before",
    "expires_at",
    "activation_status",
    "owner_go_required",
    "owner_session_go_required",
    "single_use_authorization_required",
    "confirm_token_required",
    "network_session_execution_authorized_by_this_go",
    "fixture_non_authoritative",
)

KNOWN_FIELDS = frozenset(
    REQUIRED_FIELDS
    + (
        "session_go_digest",
        "notes",
    )
)


def repo_root_v1() -> Path:
    return Path(__file__).resolve().parents[3]
