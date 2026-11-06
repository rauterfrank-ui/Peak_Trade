"""Constants for R6 S4 multi-future shadow/sim evidence v1.

Evidence-only overlay over the unauthorized S3 architecture.
Does not authorize Multi-Future runtime, mutate G13, start S5, or
create a second execution/accounting writer.
"""

from __future__ import annotations

CAPABILITY_ID = "CANONICAL_R6_S4_MULTI_FUTURE_SHADOW_SIM_EVIDENCE_V1"
PACKAGE_MARKER = "CANONICAL_R6_S4_MULTI_FUTURE_SHADOW_SIM_EVIDENCE_V1=true"
CONTRACT_ID = "canonical_r6_s4_multi_future_shadow_sim_evidence"
CONTRACT_VERSION = "canonical_r6_s4_multi_future_shadow_sim_evidence/v1"
CONTRACT_OWNER = "ops.canonical_r6_s4_multi_future_shadow_sim_evidence_v1"
CONTRACT_CONFIG_REL_PATH = (
    "config/governance/canonical_r6_s4_multi_future_shadow_sim_evidence_v1.json"
)
CANONICAL_SERIALIZATION_VERSION = (
    "canonical_r6_s4_multi_future_shadow_sim_evidence_canonical_json_v1"
)

REMEDIATION_ID = "R6_S4_MULTI_FUTURE_SHADOW_SIM_EVIDENCE"
SOURCE_GAP_IDS = ("RB-G13", "I01", "I50", "I85", "PHASE_8", "PHASE_8_2", "R6_S4")
DONE_CRITERION = "MULTI_INSTRUMENT_SHADOW_SIM_EVIDENCE_BOUND_WITHOUT_AUTHORIZATION"
TARGET_BINDING = "S4_SHADOW_SIM_EVIDENCE_FAIL_CLOSED_SINGLE_FUTURE"

S1_OWNER = "ops.canonical_r6_phase_8_1_policy_precondition_v1"
S2_OWNER = "ops.canonical_r6_s2_portfolio_risk_contracts_v1"
S3_OWNER = "ops.canonical_r6_s3_multi_future_runtime_architecture_v1"
R6_S1_CLOSED = True
R6_S2_CLOSED = True
R6_S3_IMPLEMENTED_UNAUTHORIZED = True

MULTI_FUTURE_RUNTIME_IMPLEMENTED = True
MULTI_FUTURE_RUNTIME_AUTHORIZED = False
IMPLEMENTED_DOES_NOT_IMPLY_AUTHORIZED = True
EVIDENCE_IS_NOT_AUTHORIZATION = True
EVIDENCE_CANNOT_CREATE_RUNTIME_AUTHORITY = True

CURRENT_EFFECTIVE_RUNTIME_MODE = "SINGLE_SELECTED_FUTURE"
MAX_POSITIONS_EFFECTIVE = 1
SELECTED_FUTURE_COUNT = 1
SINGLE_SELECTED_FUTURE = True
TOP_N_ACTIVE_SET_AUTHORITY = False
G13_STATUS = "INTENTIONAL_SAFETY_BARRIER"
G13_UNCHANGED = True
NO_SILENT_G13_BYPASS = True
NO_AUTOMATIC_STAGE_PROGRESSION = True

FIXTURE_SEED = 20260815
FIXTURE_INSTRUMENT_A = "AAA-FUT"
FIXTURE_INSTRUMENT_B = "BBB-FUT"
FIXTURE_INSTRUMENT_IDS = (FIXTURE_INSTRUMENT_A, FIXTURE_INSTRUMENT_B)
MINIMUM_SIM_INSTRUMENT_CONTEXTS = 2

IDENTITY_PLANE = "R6_S4_MF_SHADOW_SIM_EVIDENCE"
IDENTITY_JOIN_KEY = "sha256"
MD5_12_FORBIDDEN = True
PACKAGE_N_LIVE_OWNER_JOIN_NOT_USED = True
PACKAGE_N_IS_NOT_MF_IDENTITY = True

SOURCE_EVIDENCE_S1 = "MANIFEST_VERIFIED"
SOURCE_EVIDENCE_S2 = "MANIFEST_VERIFIED"
SOURCE_EVIDENCE_S3 = "MANIFEST_VERIFIED"
SOURCE_EVIDENCE_EXTERNAL = "NOT_REFERENCED"

SIMULATED_EXECUTION_MODE = "INTERNAL_SIMULATED_OBSERVATION"
EXCHANGE_SUBMIT_ATTEMPTED = False
TESTNET_SUBMIT_ATTEMPTED = False
FILLS_COMMITTED = False

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
FUNDING_RUNTIME_ACTIVATED = False
R6_RUNTIME_AUTHORIZED = False
S4_AUTHORIZED = False
S4_EVIDENCE_PREPARED = True
S5_AUTHORIZATION_GRANTED = False
S6_AUTONOMOUS_GRANTED = False
NEXT_STAGE_AUTOMATICALLY_AUTHORIZED = False

REQUIRED_OWNER_RELPATHS = (
    "src/ops/canonical_r6_phase_8_1_policy_precondition_v1/constants_v1.py",
    "src/ops/canonical_r6_s2_portfolio_risk_contracts_v1/constants_v1.py",
    "src/ops/canonical_r6_s3_multi_future_runtime_architecture_v1/constants_v1.py",
    "src/ops/canonical_r6_s3_multi_future_runtime_architecture_v1/orchestrator_v1.py",
    "src/ops/single_selected_future_policy_v1/constants_v1.py",
    "src/ops/single_future_stateful_no_order_runtime_activation_v1/simulated_execution_port_v1.py",
    "src/ops/productive_futures_accounting_runtime_binding_v1/constants_v1.py",
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
        "src.sim.paper",
    }
)

NEGATIVE_CASE_IDS = (
    "duplicate_instrument_context",
    "state_contamination",
    "nondeterministic_arbitration",
    "conflicting_intents",
    "portfolio_risk_rejection",
    "writer_duplication_attempt",
    "accounting_writer_duplication_attempt",
    "stale_unknown_instrument_state",
    "restart_reconciliation_mismatch",
    "unauthorized_mf_activation_attempt",
    "g13_bypass_attempt",
    "order_submit_attempt",
)
