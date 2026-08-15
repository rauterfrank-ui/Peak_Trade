"""Constants for R6 S5 bounded-authorization preparation v1.

Preparation-only overlay. Does not grant Multi-Future authorization,
mutate G13, ratify N>1, activate a productive caller, or unlock submit.
"""

from __future__ import annotations

CAPABILITY_ID = "CANONICAL_R6_S5_BOUNDED_AUTHORIZATION_PREPARATION_V1"
PACKAGE_MARKER = "CANONICAL_R6_S5_BOUNDED_AUTHORIZATION_PREPARATION_V1=true"
CONTRACT_ID = "canonical_r6_s5_bounded_authorization_preparation"
CONTRACT_VERSION = "canonical_r6_s5_bounded_authorization_preparation/v1"
CONTRACT_OWNER = "ops.canonical_r6_s5_bounded_authorization_preparation_v1"
CONTRACT_CONFIG_REL_PATH = (
    "config/governance/canonical_r6_s5_bounded_authorization_preparation_v1.json"
)
CANONICAL_SERIALIZATION_VERSION = (
    "canonical_r6_s5_bounded_authorization_preparation_canonical_json_v1"
)

REMEDIATION_ID = "R6_S5_BOUNDED_AUTHORIZATION_PREPARATION"
SOURCE_GAP_IDS = ("RB-G13", "I01", "I50", "I85", "PHASE_8", "PHASE_8_2", "R6_S5")
DONE_CRITERION = "S5_BOUNDED_AUTHORIZATION_PREPARED_WITHOUT_GRANT"
TARGET_BINDING = "S5_PREPARATION_FAIL_CLOSED_SINGLE_FUTURE"

S1_OWNER = "ops.canonical_r6_phase_8_1_policy_precondition_v1"
S2_OWNER = "ops.canonical_r6_s2_portfolio_risk_contracts_v1"
S3_OWNER = "ops.canonical_r6_s3_multi_future_runtime_architecture_v1"
S4_OWNER = "ops.canonical_r6_s4_multi_future_shadow_sim_evidence_v1"
R6_S1_CLOSED = True
R6_S2_CLOSED = True
R6_S3_IMPLEMENTED_UNAUTHORIZED = True
R6_S4_EVIDENCE_PREPARED_UNAUTHORIZED = True

PREPARATION_IS_NOT_AUTHORIZATION = True
EVIDENCE_IS_NOT_AUTHORIZATION = True
S4_SIM_EVIDENCE_IS_NOT_LIVE_PROOF = True
S5_AUTHORIZATION_GRANTED = False
S5_PREPARED = True
MULTI_FUTURE_RUNTIME_IMPLEMENTED = True
MULTI_FUTURE_RUNTIME_AUTHORIZED = False
IMPLEMENTED_DOES_NOT_IMPLY_AUTHORIZED = True
AUTHORIZED_NOT_DERIVED_FROM_IMPLEMENTED = True
PREPARATION_DOES_NOT_IMPLY_AUTHORIZATION = True

CURRENT_EFFECTIVE_RUNTIME_MODE = "SINGLE_SELECTED_FUTURE"
MAX_POSITIONS_EFFECTIVE = 1
SELECTED_FUTURE_COUNT = 1
SINGLE_SELECTED_FUTURE = True
TOP_N_ACTIVE_SET_AUTHORITY = False
N_GREATER_THAN_ONE_RATIFIED = False
G13_STATUS = "INTENTIONAL_SAFETY_BARRIER"
G13_UNCHANGED = True
NO_SILENT_G13_BYPASS = True
NO_AUTOMATIC_STAGE_PROGRESSION = True
NO_AUTOMATIC_S5_TO_S6_PROGRESSION = True

IDENTITY_PLANE = "R6_S5_BOUNDED_AUTHORIZATION_PREPARATION"
IDENTITY_JOIN_KEY = "sha256"
MD5_12_FORBIDDEN = True
PACKAGE_N_LIVE_OWNER_JOIN_NOT_USED = True
PACKAGE_N_IS_NOT_MF_IDENTITY = True

SINGLE_FUTURE_LIVE_PROOF_MEANING = (
    "CAP_11_13_LIVE_CANARY_THEN_LIVE_ORDER_ECONOMIC_LADDER_NOT_I17_NOT_TESTNET_NOT_SHADOW"
)
SINGLE_FUTURE_LIVE_PROOF = False
SINGLE_FUTURE_LIVE_PROOF_REQUIRED_BEFORE_S5_AUTHORIZATION_GRANT = True
LIVE_CANARY_PROOF_REQUIRED = True
LIVE_ORDER_ECONOMIC_PROOF_REQUIRED = True
I17_IS_NOT_LIVE_PROOF = True
TESTNET_IS_NOT_LIVE_PROOF = True
SHADOW_IS_NOT_LIVE_PROOF = True
GET_ONLY_LIVE_IS_NOT_LIVE_ORDER_PROOF = True
SINGLE_FUTURE_LIVE_PROOF_STATUS = "UNPROVEN_REQUIRED_BEFORE_S5_AUTHORIZATION_GRANT"

NUMERIC_POLICY_STATUS = "DEFERRED_UNRATIFIED"
CONCENTRATION_PERCENTAGE_RATIFIED = False
CORRELATION_THRESHOLD_RATIFIED = False
PORTFOLIO_VAR_LIMIT_RATIFIED = False
COMPONENT_VAR_LIMIT_RATIFIED = False
PER_INSTRUMENT_CAPITAL_BUDGET_RATIFIED = False
GROSS_NET_EXPOSURE_LIMIT_RATIFIED = False
MF_ROTATION_HYSTERESIS_POLICY_RATIFIED = False
MF_COOLDOWN_POLICY_RATIFIED = False
MF_OPEN_POSITION_TREATMENT_RATIFIED = False
SINGLE_FUTURE_DEFAULTS_ARE_NOT_MF_NUMERICS = True
ZERO_CORRELATION_OPTIMISTIC_FALLBACK_FORBIDDEN = True

OWNER_GO_S5_AUTHORIZATION_GRANT = False
OWNER_GO_N_GREATER_THAN_ONE_POLICY = False
OWNER_GO_G13_CONTROLLED_UNLOCK = False
OWNER_GO_PRODUCTIVE_MF_ACTIVATION = False
OWNER_GO_SUBMIT_UNLOCK = False
FUTURE_OWNER_GATE_IDS = (
    "OWNER_GO_S5_AUTHORIZATION_GRANT",
    "OWNER_GO_N_GREATER_THAN_ONE_POLICY",
    "OWNER_GO_G13_CONTROLLED_UNLOCK",
    "OWNER_GO_PRODUCTIVE_MF_ACTIVATION",
    "OWNER_GO_SUBMIT_UNLOCK",
)

CORE_LOGIC_CHANGE = False
STRATEGY_LOGIC_MUTATED = False
RISK_LOGIC_CHANGE = False
RUNTIME_AUTHORIZATION_EFFECT = "NONE"
AUTHORITY_EFFECT = "NONE"
RUNTIME_AUTHORITY_IMPACT = "NONE"
ACTIVATED = False
PRODUCTIVE_CALLER_EXISTS = False
PRODUCTIVE_MF_CALLER_AUTHORIZED = False
TRADING_GRANT = False
PROMOTION_AUTHORITY = False
BOUNDED_AUTO_PROMOTION = False
SUBMIT_UNLOCKED = False
SECOND_EXECUTION_AUTHORITY_CREATED = False
SECOND_ACCOUNTING_AUTHORITY_CREATED = False
SECOND_DECISION_AUTHORITY_CREATED = False
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
S6_AUTONOMOUS_GRANTED = False
NEXT_STAGE_AUTOMATICALLY_AUTHORIZED = False

SOURCE_EVIDENCE_S1 = "MANIFEST_VERIFIED"
SOURCE_EVIDENCE_S2 = "MANIFEST_VERIFIED"
SOURCE_EVIDENCE_S3 = "MANIFEST_VERIFIED"
SOURCE_EVIDENCE_S4 = "MANIFEST_VERIFIED"
SOURCE_EVIDENCE_EXTERNAL = "NOT_REFERENCED"

REQUIRED_OWNER_RELPATHS = (
    "src/ops/canonical_r6_phase_8_1_policy_precondition_v1/constants_v1.py",
    "src/ops/canonical_r6_s2_portfolio_risk_contracts_v1/constants_v1.py",
    "src/ops/canonical_r6_s3_multi_future_runtime_architecture_v1/constants_v1.py",
    "src/ops/canonical_r6_s4_multi_future_shadow_sim_evidence_v1/constants_v1.py",
    "src/ops/single_selected_future_policy_v1/constants_v1.py",
    "src/ops/single_future_stateful_no_order_runtime_activation_v1/constants_v1.py",
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
    "authorization_grant_true",
    "multi_future_runtime_authorized_true",
    "g13_changed",
    "max_positions_not_one",
    "n_greater_than_one_ratified",
    "productive_mf_caller_authorized",
    "submit_unlocked",
    "live_proof_from_shadow",
    "live_proof_from_testnet",
    "live_proof_from_i17",
    "live_proof_from_s4",
    "numeric_policy_treated_resolved",
    "second_execution_authority",
    "second_accounting_authority",
    "second_decision_authority",
    "automatic_s5_to_s6",
    "future_owner_gate_granted",
    "top_n_active_set_authority",
    "activated_true",
)
