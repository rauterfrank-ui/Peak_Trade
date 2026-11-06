"""CAPABILITY_O2_CANONICAL_LOCAL_LAUNCHER_AND_PROCESS_SUPERVISION_V1 constants."""

from __future__ import annotations

CAPABILITY_ID = "CAPABILITY_O2_CANONICAL_LOCAL_LAUNCHER_AND_PROCESS_SUPERVISION_V1"
SCHEMA_VERSION = "o2_canonical_local_launcher_and_process_supervision_v1"
SUPERVISION_BACKEND = "repository_owned_supervisor"
SUPERVISOR_IDENTITY = "peak_trade.canonical_local_launcher_supervisor_v1"
SINGLE_WRITER_IDENTITY = "peak_trade.canonical_local_launcher_single_writer_v1"

REGISTRY_DIRNAME = "canonical_local_launcher_v1"
WRITER_LOCK_FILENAME = "launcher_writer.lock"
SESSIONS_DIRNAME = "sessions"
ACTIVE_BY_MODE_DIRNAME = "active_by_mode"
TRANSITIONS_FILENAME = "transitions.jsonl"
SESSION_STATE_FILENAME = "session_state_v1.json"
HEARTBEAT_FILENAME = "heartbeat_v1.json"
SCAFFOLD_MARKER_FILENAME = "scaffold_worker_v1.marker"

# MVP active mode set — future modes remain unauthorized.
MODE_DASHBOARD_ONLY = "dashboard-only"
AUTHORIZED_MODES: frozenset[str] = frozenset({MODE_DASHBOARD_ONLY})

LIFECYCLE_STATES: frozenset[str] = frozenset(
    {
        "OFF",
        "PREFLIGHT",
        "ENV_VALIDATED",
        "AUTH_VALIDATED",
        "STARTING",
        "RUNNING",
        "DEGRADED",
        "STOPPING",
        "STOPPED",
        "FAILED",
        "RECOVERING",
        "OWNER_LOCKED",
    }
)

ACTIVE_LIFECYCLE_STATES: frozenset[str] = frozenset(
    {"PREFLIGHT", "ENV_VALIDATED", "AUTH_VALIDATED", "STARTING", "RUNNING", "DEGRADED", "STOPPING"}
)

DEFAULT_GRACEFUL_STOP_TIMEOUT_SECONDS = 2.0
DEFAULT_ESCALATION_KILL_TIMEOUT_SECONDS = 1.0
DEFAULT_HEALTH_STALE_SECONDS = 30.0

SETSID_CLI_REQUIRED = False
MACOS_LAUNCH_USES_START_NEW_SESSION = True

# Safety invariants stamped into every start/preflight result.
SAFETY_INVARIANTS: dict[str, bool] = {
    "NETWORK_SESSION_STARTED": False,
    "AUTHORIZATION_CONSUMED": False,
    "CONFIRM_TOKEN_MINTED": False,
    "ORDERS_SUBMITTED": False,
    "CREDENTIALS_USED": False,
    "CORE_LOGIC_CHANGED": False,
    "LEGACY_PATHS_DEAUTHORIZED": False,
    "SETSID_CLI_REQUIRED": False,
    "LIVE_SESSION_REGISTRY_IS_NOT_LIFECYCLE_AUTHORITY": True,
}
