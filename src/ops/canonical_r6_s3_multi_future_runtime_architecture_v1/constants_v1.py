"""Constants for R6 S3 Phase-8.2 multi-future runtime architecture v1.

Implementation-only overlay behind fail-closed flags.
Does not authorize Multi-Future runtime, mutate G13, or create a
second execution/accounting writer.
"""

from __future__ import annotations

CAPABILITY_ID = "CANONICAL_R6_S3_MULTI_FUTURE_RUNTIME_ARCHITECTURE_V1"
PACKAGE_MARKER = "CANONICAL_R6_S3_MULTI_FUTURE_RUNTIME_ARCHITECTURE_V1=true"
CONTRACT_ID = "canonical_r6_s3_multi_future_runtime_architecture"
CONTRACT_VERSION = "canonical_r6_s3_multi_future_runtime_architecture/v1"
CONTRACT_OWNER = "ops.canonical_r6_s3_multi_future_runtime_architecture_v1"
CONTRACT_CONFIG_REL_PATH = (
    "config/governance/canonical_r6_s3_multi_future_runtime_architecture_v1.json"
)
CANONICAL_SERIALIZATION_VERSION = (
    "canonical_r6_s3_multi_future_runtime_architecture_canonical_json_v1"
)

REMEDIATION_ID = "R6_S3_RUNTIME_IMPLEMENTATION_UNAUTHORIZED_BEHIND_FLAGS"
SOURCE_GAP_IDS = ("RB-G13", "I01", "I50", "I85", "PHASE_8", "PHASE_8_2")
DONE_CRITERION = "PHASE_8_2_GRAPH_IMPLEMENTED_UNAUTHORIZED_BEHIND_FLAGS"
TARGET_BINDING = "S3_RUNTIME_ARCHITECTURE_FAIL_CLOSED_SINGLE_FUTURE"

# Strict flag split. AUTHORIZED is never derived from IMPLEMENTED.
MULTI_FUTURE_RUNTIME_IMPLEMENTED = True
MULTI_FUTURE_RUNTIME_AUTHORIZED = False
IMPLEMENTED_DOES_NOT_IMPLY_AUTHORIZED = True
AUTHORIZED_NOT_DERIVED_FROM_IMPLEMENTED = True

CURRENT_EFFECTIVE_RUNTIME_MODE = "SINGLE_SELECTED_FUTURE"
MAX_POSITIONS_EFFECTIVE = 1
SELECTED_FUTURE_COUNT = 1
SINGLE_SELECTED_FUTURE = True
TOP_N_ACTIVE_SET_AUTHORITY = False
G13_STATUS = "INTENTIONAL_SAFETY_BARRIER"
G13_UNCHANGED = True
NO_SILENT_G13_BYPASS = True
NO_AUTOMATIC_STAGE_PROGRESSION = True

ONE_ACTIVE_DIRECTIONAL_SIDE_PER_INSTRUMENT = True
SIMULTANEOUS_LONG_SHORT_PER_INSTRUMENT_ALLOWED = False
REVERSAL_REQUIRES_RECONCILED_FLAT_PER_INSTRUMENT = True
NO_POSITION_INCREASE_DURING_UNRESOLVED_RECONCILIATION = True
NO_ORDER_WITHOUT_SINGLE_USE_PERMISSION = True

SINGLE_GLOBAL_EXECUTION_WRITER = True
SINGLE_GLOBAL_ACCOUNTING_WRITER = True
DETERMINISTIC_INTENT_ARBITRATION = True
PER_INSTRUMENT_STATE_ISOLATION = True
PER_INSTRUMENT_RECONCILIATION = True
PORTFOLIO_RISK_BEFORE_GLOBAL_SAFETY = True
GLOBAL_SAFETY_CAN_ONLY_RESTRICT_OR_BLOCK = True
PORTFOLIO_ALLOCATOR_CANNOT_SUBMIT_ORDERS = True
RANKING_CANNOT_CREATE_RUNTIME_AUTHORITY = True
ECONOMIC_EVIDENCE_CANNOT_CREATE_RUNTIME_AUTHORITY = True
RESEARCH_CANNOT_CREATE_RUNTIME_AUTHORITY = True

CANONICAL_EXECUTION_WRITER_IDENTITY = (
    "ops.single_future_stateful_no_order_runtime_activation_v1.simulated_execution_port_v1"
)
CANONICAL_ACCOUNTING_WRITER_IDENTITY = "productive_futures_accounting_portfolio_writer_v1"
CANONICAL_SELECTION_WRITER_IDENTITY = "single_selected_future_selection_writer_v1"
CANONICAL_RECON_WRITER_IDENTITY = "productive_portfolio_position_state_writer_v1"

MASTER_V2_DOUBLE_PLAY_OWNER = (
    "ops.wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_v1"
)
PER_INSTRUMENT_RISK_OWNER = "src.governance.capital_risk_sizing_v1"
PORTFOLIO_RISK_CONTRACT_OWNER = "ops.canonical_r6_s2_portfolio_risk_contracts_v1"
SAFETY_OWNER = "trading.master_v2.safety_kernel_offline_replay_binding_adapter_v0"
RANKING_OWNER = "ops.productive_futures_ranking_producer_v1"
SELECTION_OWNER = "ops.single_selected_future_policy_v1"

S1_OWNER = "ops.canonical_r6_phase_8_1_policy_precondition_v1"
S2_OWNER = "ops.canonical_r6_s2_portfolio_risk_contracts_v1"
R6_S1_CLOSED = True
R6_S2_CLOSED = True

CORE_LOGIC_CHANGE = False
STRATEGY_LOGIC_MUTATED = False
RISK_LOGIC_CHANGE = False
RUNTIME_AUTHORIZATION_EFFECT = "NONE"
AUTHORITY_EFFECT = "NONE"
RUNTIME_AUTHORITY_IMPACT = "NONE"
ACTIVATED = False
PRODUCTIVE_CALLER_EXISTS = False
TRADING_GRANT = False
PROMOTION_AUTHORITY = False
SUBMIT_UNLOCKED = False
SECOND_EXECUTION_AUTHORITY_CREATED = False
SECOND_ACCOUNTING_AUTHORITY_CREATED = False
TRADING_AUTHORITY_EXPANDED = False

LIVE_AUTHORIZED = False
TESTNET_AUTHORIZED = False
CANARY_AUTHORIZED = False
CANARY_EXECUTE = False
NETWORK_EFFECT = "NONE"
ORDER_EFFECT = "NONE"
ACCOUNT_MUTATION_EFFECT = "NONE"
R6_RUNTIME_AUTHORIZED = False
S4_AUTHORIZED = False
S5_AUTHORIZATION_GRANTED = False
S6_AUTONOMOUS_GRANTED = False
NEXT_STAGE_AUTOMATICALLY_AUTHORIZED = False

PHASE_8_2_GRAPH = (
    "governed_candidate_input",
    "bounded_active_set_representation",
    "per_instrument_isolated_runtime_context",
    "per_instrument_master_v2_double_play",
    "per_instrument_risk_sizing",
    "global_portfolio_risk",
    "global_safety",
    "deterministic_cross_instrument_intent_arbitration",
    "one_canonical_execution_accounting_writer_boundary",
    "per_instrument_reconciliation_evidence_state",
)

ACTION_PRIORITY = (
    ("EXIT", 0),
    ("REDUCE", 1),
    ("HOLD", 2),
    ("ENTRY", 3),
    ("REVERSAL", 4),
)

REQUIRED_OWNER_RELPATHS = (
    "src/ops/canonical_r6_phase_8_1_policy_precondition_v1/constants_v1.py",
    "src/ops/canonical_r6_s2_portfolio_risk_contracts_v1/constants_v1.py",
    "src/ops/single_selected_future_policy_v1/constants_v1.py",
    "src/ops/single_selected_future_runtime_binding_v1/constants_v1.py",
    "src/ops/productive_futures_ranking_producer_v1/constants_v1.py",
    "src/ops/productive_futures_accounting_runtime_binding_v1/constants_v1.py",
    "src/ops/productive_reconciliation_runtime_binding_v1/constants_v1.py",
    "src/ops/single_future_stateful_no_order_runtime_activation_v1/constants_v1.py",
    "src/ops/single_future_stateful_no_order_runtime_activation_v1/simulated_execution_port_v1.py",
    "src/governance/capital_risk_sizing_v1.py",
)

FORBIDDEN_IMPORT_ROOTS = frozenset(
    {
        "src.orders",
        "src.live",
        "src.intents",
        "src.execution_simple",
        "src.risk.risk_layer_manager",
        "src.risk.enforcement",
        "src.portfolio",
        "src.execution.pipeline",
        "src.execution.orchestrator",
    }
)
