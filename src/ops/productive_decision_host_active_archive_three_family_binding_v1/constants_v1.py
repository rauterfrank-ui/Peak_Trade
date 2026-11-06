"""Constants for CAPABILITY_PRODUCTIVE_DECISION_HOST_ACTIVE_ARCHIVE_THREE_FAMILY_BINDING_V1.

AUTHORITY_EFFECT=NONE for dashboard / projection surfaces.
CORE_LOGIC_CHANGE=false
TRADING_LOGIC_CHANGE=false
DASHBOARD_AUTHORITY_EFFECT=NONE
O2_AUTHORIZED_MODES remain {'dashboard-only'} (unchanged).
"""

from __future__ import annotations

CAPABILITY_ID = "CAPABILITY_PRODUCTIVE_DECISION_HOST_ACTIVE_ARCHIVE_THREE_FAMILY_BINDING_V1"
PACKAGE_MARKER = "PRODUCTIVE_DECISION_HOST_ACTIVE_ARCHIVE_THREE_FAMILY_BINDING_V1=true"
OWNER = "ops.productive_decision_host_active_archive_three_family_binding_v1"
SCHEMA_VERSION = "productive_decision_host_active_archive_three_family_binding.v1"
PRODUCER_VERSION = SCHEMA_VERSION

AUTHORITY_EFFECT = "NONE"
DASHBOARD_AUTHORITY_EFFECT = "NONE"
DASHBOARD_ROLE = "READ_ONLY_CONSUMER"
RUNTIME_MODE = "INTERNAL_SIMULATED_EXECUTION_PUBLIC_MD_CAPABLE_NO_ORDER"

PRODUCTIVE_HOST_MODULE = (
    "src/ops/wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_v1/"
    "decision_economics_cycle_bridge_v1.py"
)
PRODUCTIVE_HOST_SYMBOL = "run_bridge_cycle_v1"
PRODUCTIVE_HOST_ENTRY = (
    "ops.wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_v1."
    "decision_economics_cycle_bridge_v1.run_bridge_cycle_v1"
)

SINGLE_WRITER_IDENTITY = "productive_decision_host_active_archive_writer_v1"
WRITER_LOCK_FILENAME = "productive_decision_host_writer.lock"
SESSION_STATE_FILENAME = "session_contract_v1.json"
CYCLE_TRACE_FILENAME = "cycle_commit_trace.jsonl"

# Explicit Owner authorization tokens (fail-closed when absent).
OWNER_GO_ENV = "PEAK_TRADE_PRODUCTIVE_HOST_OWNER_GO"
EXPECTED_REPO_SHA_ENV = "PEAK_TRADE_PRODUCTIVE_HOST_EXPECTED_REPO_SHA"
ARCHIVE_ROOT_ENV = "PEAK_TRADE_WORKFLOW_DASHBOARD_V1_ARCHIVE_ROOT"

STATE_LAYOUT_VERSION = "v1"
RUNTIME_STATE_DIRNAME = "runtime_state"
EVIDENCE_SESSION_DIRNAME = "evidence_session"
DYNAMIC_SCOPE_STATE_DIRNAME = "dynamic_scope"
CONFIRMATION_STATE_DIRNAME = "confirmation"
ACTIVATION_STATE_DIRNAME = "activation"
ACCOUNTING_STATE_DIRNAME = "accounting"
CANONICAL_DECISION_SOURCE_DIRNAME = "canonical_decision_source"
CANONICAL_DECISION_SOURCE_FILENAME = "canonical_trading_decision_evidence.v1.json"
EXPORT_CURSOR_FILENAME = "family_export_cursor_v1.json"

FAMILY_DYNAMIC_SCOPE = "dynamic_scope"
FAMILY_CANONICAL_DECISION = "canonical_decision"
FAMILY_DOUBLE_PLAY = "double_play"
FAMILY_REGIME_BULL_BEAR_SWITCH = "regime_bull_bear_switch"
FAMILY_RISK_SIZING_CAPITAL = "risk_sizing_capital"
FAMILY_EXECUTION_RECONCILIATION = "execution_reconciliation"
FAMILY_ECONOMIC_SUMMARY = "economic_summary"
FAMILY_SAFETY_AUTHORITY = "safety_authority"

DYNAMIC_SCOPE_SIBLING_RELATIVE = "readmodels/dynamic_scope_state_v1.json"
CANONICAL_DECISION_SIBLING_RELATIVE = "readmodels/canonical_trading_decision_evidence.v1.json"
DOUBLE_PLAY_SIBLING_RELATIVE = "readmodels/double_play_dashboard_display.v1.json"
REGIME_BULL_BEAR_SWITCH_SIBLING_RELATIVE = "readmodels/regime_bull_bear_switch.v1.json"
RISK_SIZING_CAPITAL_SIBLING_RELATIVE = "readmodels/risk_sizing_capital.v1.json"
EXECUTION_RECONCILIATION_SIBLING_RELATIVE = "readmodels/execution_reconciliation.v1.json"
ECONOMIC_SUMMARY_SIBLING_RELATIVE = "readmodels/economic_summary.v1.json"
SAFETY_AUTHORITY_SIBLING_RELATIVE = "readmodels/safety_authority_fields.v1.json"

# Productive integrated replay yields ResultV1 intermediates by default. Export binds
# only when a complete PureStackDisplayDecisionBundleV1 (or equivalent Decision
# mapping) is already present on the replay intermediate. ResultV1→Decision mapping
# remains unauthorized (see double_play_input_gate_v1 / replay_commit_source_v1).
HARD_STOP_DOUBLE_PLAY_CANONICAL_INPUT_CONTRACT_MISMATCH = False
DOUBLE_PLAY_BLOCK_REASON = (
    "DOUBLE_PLAY_CANONICAL_DISPLAY_INPUTS_INCOMPLETE:"
    "Pure-Stack display export requires all seven Decision types on "
    "display_decision_bundle / pure_stack_display_decision_bundle or intermediate; "
    "TransitionDecision passthrough alone is insufficient; "
    "ResultV1→Decision mapping unauthorized; fixture/scenario fallbacks forbidden"
)

DEFAULT_MIN_CYCLE_INTERVAL_SECONDS = 1.0
DEFAULT_SMOKE_MAX_CYCLES = 8
DEFAULT_SMOKE_BACKOFF_SECONDS = 0.5

PUBLIC_MD_ALLOWED_HOSTS = ("www.okx.com", "okx.com")
PUBLIC_MD_ALLOWED_PATH_PREFIXES = ("/api/v5/public/", "/api/v5/market/")
FORBIDDEN_PRIVATE_PATH_PREFIXES = (
    "/api/v5/trade/",
    "/api/v5/account/",
    "/api/v5/users/",
)

O2_AUTHORIZED_MODES_REQUIRED = frozenset({"dashboard-only"})

LIVE_ORDERS = False
TESTNET_ORDERS = False
PAPER_EXCHANGE_ORDERS = False
EXCHANGE_CREDENTIAL_USE = False
REAL_CAPITAL_MOVEMENT = False
ORDER_PATH_ACTIVATED = False
LONG_RUNNING_PHASE_9_2_PROVEN = False
