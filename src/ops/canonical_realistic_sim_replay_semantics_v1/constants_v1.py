"""Constants for R5 realistic sim/replay semantics v1.

Additive forensic overlay. Reuses existing I67 paper-sim, I79 replay-pack,
Cap7 simulated-execution, and Cap5.1 offline MD replay owners. Does not
create a second execution, order, promotion, or I17 shadow authority.

I67 remains GOVERNED_SUPPORTING_SIMULATION. I79 remains non-authoritative
replay evidence. Cap7 internal sim remains the canonical simulated path.
I17 PRODUCTIVE_SHADOW remains distinct and is not re-run here.
"""

from __future__ import annotations

CAPABILITY_ID = "CANONICAL_REALISTIC_SIM_REPLAY_SEMANTICS_V1"
PACKAGE_MARKER = "CANONICAL_REALISTIC_SIM_REPLAY_SEMANTICS_V1=true"
CONTRACT_ID = "canonical_realistic_sim_replay_semantics"
CONTRACT_VERSION = "canonical_realistic_sim_replay_semantics/v1"
CONTRACT_OWNER = "ops.canonical_realistic_sim_replay_semantics_v1"
CONTRACT_CONFIG_REL_PATH = "config/governance/canonical_realistic_sim_replay_semantics_v1.json"
CANONICAL_SERIALIZATION_VERSION = "canonical_realistic_sim_replay_semantics_canonical_json_v1"

REMEDIATION_ID = "R5_REALISTIC_SIM_REPLAY"
SOURCE_GAP_IDS = ("EG-I67-CAP7", "I79", "CLUSTER_J")
DONE_CRITERION = "MODE_SEMANTICS_ATTESTED;REPLAY_PACK_IF_COMMISSIONED"
TARGET_BINDING_I67 = "GOVERNED_SUPPORTING_SIMULATION"
TARGET_BINDING_I79 = "GOVERNED_SUPPORTING_NON_AUTHORITATIVE_REPLAY"
CLUSTER_ID = "J_SIM_BACKTEST_REPLAY"

I67_OWNER = "src.sim.paper.PaperTradingSimulator"
I67_OWNER_RELPATH = "src/sim/paper/simulator.py"
I67_CALLER_RELPATH = "scripts/aiops/run_paper_trading_session.py"
I67_ROLE = "GOVERNED_SUPPORTING_SIMULATION"
I67_CLASSIFICATION = "LOCAL_PAPER_SIMULATION_NOT_I17_NOT_CAP7"

I79_OWNER = "src.execution.replay_pack"
I79_CONTRACT_V1_RELPATH = "src/execution/replay_pack/contract.py"
I79_CONTRACT_V2_RELPATH = "src/execution/replay_pack/contract_v2.py"
I79_BUILDER_RELPATH = "src/execution/replay_pack/builder.py"
I79_VALIDATOR_RELPATH = "src/execution/replay_pack/validator.py"
I79_CLI_RELPATH = "scripts/execution/pt_replay_pack.py"
I79_DOCS_VNEXT_RELPATH = "docs/execution/REPLAY_PACK_VNEXT.md"
I79_DOCS_V1_RELPATH = "docs/execution/DETERMINISTIC_REPLAY_PACK.md"
I79_ROLE = "GOVERNED_SUPPORTING_NON_AUTHORITATIVE_REPLAY"
I79_CLASSIFICATION = "OFFLINE_EXECUTION_EVENT_BUNDLE_NOT_I17_NOT_CAP7"

CAP7_INTERNAL_SIM_OWNER = (
    "ops.wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_v1"
)
CAP7_INTERNAL_SIM_RELPATH = (
    "src/ops/wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_v1/"
    "decision_economics_cycle_bridge_v1.py"
)
CAP7_2_RUNTIME_OWNER = "ops.single_future_stateful_no_order_runtime_activation_v1"
CAP7_2_SIM_PORT_RELPATH = (
    "src/ops/single_future_stateful_no_order_runtime_activation_v1/simulated_execution_port_v1.py"
)
CAP7_OFFLINE_MD_REPLAY_OWNER = (
    "ops.single_future_canonical_runtime_deterministic_offline_evidence_v1"
)
CAP7_OFFLINE_MD_REPLAY_RELPATH = (
    "src/ops/single_future_canonical_runtime_deterministic_offline_evidence_v1/replay_engine_v1.py"
)
CAP7_CLASSIFICATION = "INTERNAL_SIMULATED_NOT_I17_NOT_I67_NOT_I79"

I17_SHADOW_CONTRACT_OWNER = "ops.paper_shadow_observation_operator_go_session_preregistration_v1"
I17_SHADOW_RUNNER_OWNER = "ops.integrated_paper_shadow_observation_wallclock_session_execution_v1"
I17_CLASSIFICATION = "PRODUCTIVE_SHADOW_NOT_SIM_NOT_REPLAY"
I17_CANONICAL_CLOSEOUT_STATUS = "CLOSED_PROVEN_PASS"
I57_CLASSIFICATION = "FORWARD_SIGNAL_ONLY_NOT_I17_NOT_I67"
I57_ROLE = "RESEARCH_FEEDER"
I72_ROLE = "GOVERNED_SUPPORTING_REPORTING"

R4_OWNER = "ops.canonical_i17_productive_shadow_contract_readiness_v1"

REQUIRED_OWNER_RELPATHS = (
    I67_OWNER_RELPATH,
    I67_CALLER_RELPATH,
    I79_CONTRACT_V1_RELPATH,
    I79_CONTRACT_V2_RELPATH,
    I79_BUILDER_RELPATH,
    I79_VALIDATOR_RELPATH,
    I79_CLI_RELPATH,
    I79_DOCS_VNEXT_RELPATH,
    I79_DOCS_V1_RELPATH,
    CAP7_INTERNAL_SIM_RELPATH,
    CAP7_2_SIM_PORT_RELPATH,
    CAP7_OFFLINE_MD_REPLAY_RELPATH,
    "src/ops/paper_shadow_observation_operator_go_session_preregistration_v1/"
    "preregistration_contract_v1.py",
    "src/ops/integrated_paper_shadow_observation_wallclock_session_execution_v1/constants_v1.py",
    "src/ops/canonical_i17_productive_shadow_contract_readiness_v1/constants_v1.py",
)

CORE_LOGIC_CHANGE = False
RUNTIME_EFFECT = False
RUNTIME_AUTHORIZATION_EFFECT = "NONE"
AUTHORITY_EFFECT = "NONE"
RUNTIME_AUTHORITY_IMPACT = "NONE"
ACTIVATED = False
PRODUCTIVE_CALLER_EXISTS = False
NEW_EXECUTION_PIPELINE = False
NEW_REPLAY_ENGINE = False
I67_SUBSTITUTES_I17 = False
I67_SUBSTITUTES_CAP7 = False
I79_SUBSTITUTES_I17 = False
I79_SUBSTITUTES_CAP7 = False
I79_SUBSTITUTES_CAP7_OFFLINE_MD_REPLAY = False
CAP7_OFFLINE_MD_REPLAY_IS_I79 = False
I67_CAP7_EQUIVALENCE = False
I67_I17_EQUIVALENCE = False
I79_I17_EQUIVALENCE = False
NAME_COLLISION_EQUIVALENCE = False
TRADING_GRANT = False
PROMOTION_AUTHORITY = False
PROMOTION_ELIGIBLE_DEFAULT = False
AUTO_PROMOTION = False
ORDER_PERMISSION_STATE = False
ORDER_EFFECT = "NONE"
G14_NON_AUTHORITATIVE_UNTIL_PROMOTION = True

MAX_AGE_ENFORCEMENT_ENABLED = False
MAX_AGE_ROLE = "WATCHDOG_ONLY"
NUMERIC_MAX_AGE_EFFECT = "WATCHDOG_ONLY"
MAX_AGE_CAN_BLOCK_TRADING = False
MAX_AGE_CAN_BLOCK_CANARY = False
MAX_AGE_CAN_CHANGE_SELECTION = False
MAX_AGE_CAN_CHANGE_RISK_DECISIONS = False
MAX_AGE_CAN_CHANGE_EXECUTION = False
MAX_AGE_CAN_CHANGE_PROMOTION = False
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
ORDER_EFFECT_FLAG = False
R6_MULTI_FUTURE_AUTHORIZED = False
PAPER_EXCHANGE_ORDER_EFFECT = False
I17_RERUN_AUTHORIZED = False
