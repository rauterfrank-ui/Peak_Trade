"""Constants for R6 Phase-8.1 policy precondition v1.

Read-only forensic overlay. Reuses Cap 2.2/2.3/2.4/3.1/1.1/7.2 owners.
Does not implement Multi-Future runtime, change G13, or claim live proof.
"""

from __future__ import annotations

CAPABILITY_ID = "CANONICAL_R6_PHASE_8_1_POLICY_PRECONDITION_V1"
PACKAGE_MARKER = "CANONICAL_R6_PHASE_8_1_POLICY_PRECONDITION_V1=true"
CONTRACT_ID = "canonical_r6_phase_8_1_policy_precondition"
CONTRACT_VERSION = "canonical_r6_phase_8_1_policy_precondition/v1"
CONTRACT_OWNER = "ops.canonical_r6_phase_8_1_policy_precondition_v1"
CONTRACT_CONFIG_REL_PATH = "config/governance/canonical_r6_phase_8_1_policy_precondition_v1.json"
CANONICAL_SERIALIZATION_VERSION = "canonical_r6_phase_8_1_policy_precondition_canonical_json_v1"

REMEDIATION_ID = "R6_PHASE_8_1_POLICY_PRECONDITION"
SOURCE_GAP_IDS = ("RB-G13", "I01", "I50", "I85", "PHASE_8")
DONE_CRITERION = "PHASE_8_1_POLICY_CHECKLIST_FAIL_CLOSED_WITHOUT_G13_UNLOCK"
TARGET_BINDING = "S1_POLICY_FRAME_FAIL_CLOSED_SINGLE_FUTURE"

CAP23_OWNER = "ops.single_selected_future_policy_v1"
CAP24_OWNER = "ops.single_selected_future_runtime_binding_v1"
CAP22_OWNER = "ops.productive_futures_ranking_producer_v1"
CAP31_OWNER = "ops.productive_futures_accounting_runtime_binding_v1"
CAP11_RECON_OWNER = "ops.productive_reconciliation_runtime_binding_v1"
CAP72_OWNER = "ops.single_future_stateful_no_order_runtime_activation_v1"
ACCOUNTING_WRITER = "productive_futures_accounting_portfolio_writer_v1"
SELECTION_WRITER = "single_selected_future_selection_writer_v1"
RECON_WRITER = "productive_portfolio_position_state_writer_v1"

SINGLE_FUTURE_LIVE_PROOF_MEANING = (
    "CAP_11_13_LIVE_CANARY_THEN_LIVE_ORDER_ECONOMIC_LADDER_NOT_I17_NOT_TESTNET_NOT_SHADOW"
)
SINGLE_FUTURE_LIVE_PROOF = False
I17_IS_NOT_LIVE_PROOF = True
TESTNET_IS_NOT_LIVE_PROOF = True
SHADOW_IS_NOT_LIVE_PROOF = True
GET_ONLY_LIVE_IS_NOT_LIVE_ORDER_PROOF = True

MULTI_FUTURE_RUNTIME_AUTHORIZED = False
MULTI_FUTURE_RUNTIME_IMPLEMENTED = False
MAX_POSITIONS_EFFECTIVE = 1
SELECTED_FUTURE_COUNT = 1
SINGLE_SELECTED_FUTURE = True
TOP_N_ACTIVE_SET_AUTHORITY = False
G13_STATUS = "INTENTIONAL_SAFETY_BARRIER"
NO_SILENT_G13_BYPASS = True
NO_AUTOMATIC_STAGE_PROGRESSION = True
UQ5_RATIFIED = True
U_MF_S1_RATIFIED = True

CORE_LOGIC_CHANGE = False
RUNTIME_EFFECT = False
RUNTIME_AUTHORIZATION_EFFECT = "NONE"
AUTHORITY_EFFECT = "NONE"
RUNTIME_AUTHORITY_IMPACT = "NONE"
ACTIVATED = False
PRODUCTIVE_CALLER_EXISTS = False
TRADING_GRANT = False
PROMOTION_AUTHORITY = False
G14_NON_AUTHORITATIVE_UNTIL_PROMOTION = True

MAX_AGE_ENFORCEMENT_ENABLED = False
MAX_AGE_ROLE = "WATCHDOG_ONLY"
MAX_AGE_PRODUCTIVE_GATE = False
MAX_AGE_ALLOWED_USES = (
    "OBSERVATION_OF_DATA_AGE_STALENESS",
    "DIAGNOSTIC_TELEMETRY",
    "LOGGING_AUDIT",
    "EVIDENCE_COLLECTION",
    "WARNINGS_HEALTH_SIGNALS",
    "RESEARCH_FORENSIC_USE",
)

LIVE_AUTHORIZED = False
TESTNET_AUTHORIZED = False
CANARY_EXECUTE = False
NETWORK_EFFECT = False
ORDER_EFFECT = "NONE"
R6_RUNTIME_AUTHORIZED = False
S3_IMPLEMENTATION_AUTHORIZED = False
S5_AUTHORIZATION_GRANTED = False
S6_AUTONOMOUS_GRANTED = False

REQUIRED_OWNER_RELPATHS = (
    "src/ops/single_selected_future_policy_v1/constants_v1.py",
    "src/ops/single_selected_future_runtime_binding_v1/constants_v1.py",
    "src/ops/productive_futures_ranking_producer_v1/constants_v1.py",
    "src/ops/productive_futures_accounting_runtime_binding_v1/constants_v1.py",
    "src/ops/productive_reconciliation_runtime_binding_v1/constants_v1.py",
    "src/ops/single_future_stateful_no_order_runtime_activation_v1/constants_v1.py",
    "docs/planning/deferred/MULTI_FUTURE_ACTIVE_SET_ROTATION_REPLACEMENT_POLICY_V0_DEFERRED_REMINDER.md",
)
