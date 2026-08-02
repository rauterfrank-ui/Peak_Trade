"""Constants for CAPABILITY_2_3_SINGLE_SELECTED_FUTURE_POLICY_V1."""

from __future__ import annotations

CAPABILITY_ID = "CAPABILITY_2_3_SINGLE_SELECTED_FUTURE_POLICY_V1"
SCHEMA_VERSION = "single_selected_future_selection.v1"
PRODUCER_VERSION = "single_selected_future_policy.v1"
PACKAGE_MARKER = "SINGLE_SELECTED_FUTURE_POLICY_V1=true"
OWNER = "ops.single_selected_future_policy_v1"
AUTHORITY_OWNER = OWNER
SINGLE_WRITER_IDENTITY = "single_selected_future_selection_writer_v1"

SELECTION_POLICY_ID = "single_selected_future_policy_v1"
SELECTION_POLICY_VERSION = "v1"
SELECTION_POLICY_PROVENANCE = (
    "CAPABILITY_2_2_PRODUCTIVE_FUTURES_RANKING_PRODUCER_V1 Top-20 candidate context "
    "+ CAPABILITY_2_3 owner requirements (deterministic single selection, hysteresis, "
    "min holding, open-position replacement pending, restart recovery, fail-closed). "
    "No dashboard/allowlist authority. No alpha/execution/runtime activation."
)

SELECTED_FUTURE_COUNT = 1
MAX_POSITIONS_EFFECTIVE = 1
SINGLE_SELECTED_FUTURE = True
MULTI_FUTURE_RUNTIME_AUTHORIZED = False
SELECTION_AUTHORITY_ADDED = True
ALPHA_AUTHORITY_ADDED = False
EXECUTION_AUTHORITY_ADDED = False
DASHBOARD_AUTHORITY = False
CORE_LOGIC_CHANGE = False
ACTIVATION_STATE = "CODE_EXISTS_BOUND_PERSISTED_RESTART_PROVEN_NOT_ACTIVATED"
RUNTIME_ACTIVATION_ALLOWED = False
LIVE_AUTHORIZED = False
ORDERS_AUTHORIZED = False
PAPER_EXECUTION_AUTHORIZED = False
TESTNET_AUTHORIZED = False
NETWORK_TRADING_SESSION_ALLOWED = False
VOLATILITY_NUMERIC_MAX_AGE_ENFORCING = False
ALPHA_ALLOWED_DEFAULT = False
MANUAL_OVERRIDE_ALLOWED = False

# Upstream Cap 2.2 ranking contract.
RANKING_CAPABILITY_ID = "CAPABILITY_2_2_PRODUCTIVE_FUTURES_RANKING_PRODUCER_V1"
RANKING_SCHEMA_VERSION = "productive_futures_ranking_snapshot.v1"
RANKING_PRODUCER_VERSION = "productive_futures_ranking_producer.v1"
VENUE = "okx_eea"

DEFAULT_MAX_RANKING_AGE_SECONDS = 86_400.0
DEFAULT_REFRESH_CADENCE_SECONDS = 300.0
DEFAULT_MIN_HOLDING_PERIOD_SECONDS = 3_600.0
DEFAULT_HYSTERESIS_RANK_IMPROVEMENT = 1
DEFAULT_MIN_HISTORY_SAMPLES = 1
DEFAULT_MIN_DATA_QUALITY_STATUS = "PASS"

SELECTION_FILENAME = "single_selected_future_selection_v1.json"
EVIDENCE_FILENAME = "single_selected_future_selection_evidence_v1.json"
WRITER_LOCK_FILENAME = "single_selected_future_selection_writer.lock"
MANIFEST_FILENAME = "MANIFEST.sha256"
STAGING_DIRNAME_PREFIX = ".single_selected_future_staging_"

STATE_SELECTED_ACTIVE = "SELECTED_ACTIVE"
STATE_SELECTED_DEGRADED = "SELECTED_DEGRADED"
STATE_SELECTED_EXIT_ONLY = "SELECTED_EXIT_ONLY"
STATE_REPLACEMENT_PENDING = "REPLACEMENT_PENDING"
STATE_NO_SELECTION = "NO_SELECTION"

SELECTION_STATES = frozenset(
    {
        STATE_SELECTED_ACTIVE,
        STATE_SELECTED_DEGRADED,
        STATE_SELECTED_EXIT_ONLY,
        STATE_REPLACEMENT_PENDING,
        STATE_NO_SELECTION,
    }
)

DATA_QUALITY_PASS = "PASS"
ELIGIBILITY_ELIGIBLE = "ELIGIBLE"

CALL_GRAPH = (
    "single_selected_future_entry_point",
    "load_productive_ranking_snapshot",
    "validate_ranking_bindings",
    "stale_and_integrity_checks",
    "selection_eligibility_classification",
    "deterministic_single_selection",
    "hysteresis_and_min_holding",
    "open_position_replacement_semantics",
    "atomic_persistence",
    "selection_verification",
    "restart_reload_proof",
    "evidence",
)

FORBIDDEN_CALL_GRAPH_TARGETS = frozenset(
    {
        "master_v2",
        "double_play",
        "execution",
        "dashboard_authority",
        "top_n_active_set",
        "live_orders",
        "allowlist_selection_authority",
        "runtime_activation",
    }
)
