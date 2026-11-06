"""Constants for R4 I17 PRODUCTIVE_SHADOW contract/evidence readiness v1.

Additive, non-activating overlay. Reuses existing I17 owners. Does not start
wallclock, network, orders, promotion, Live, Testnet, or Canary.

PRODUCTIVE_SHADOW_EXECUTE requires a later OWNER_GO_SHADOW_EXECUTE.
"""

from __future__ import annotations

from src.ops.integrated_paper_shadow_productive_authorization_issuance_and_real_network_execution_v1.constants_v1 import (  # noqa: E501
    I17_CANONICAL_DURATION_SECONDS,
    I17_EXTENDED_SOAK_BLOCKS_NEXT_PHASE,
    I17_EXTENDED_SOAK_DURATION_SECONDS,
    PRODUCER_FAMILY as I17_DURATION_OWNER_FAMILY,
)

CAPABILITY_ID = "CANONICAL_I17_PRODUCTIVE_SHADOW_CONTRACT_READINESS_V1"
PACKAGE_MARKER = "CANONICAL_I17_PRODUCTIVE_SHADOW_CONTRACT_READINESS_V1=true"
CONTRACT_ID = "canonical_i17_productive_shadow_contract_readiness"
CONTRACT_VERSION = "canonical_i17_productive_shadow_contract_readiness/v1"
CONTRACT_OWNER = "ops.canonical_i17_productive_shadow_contract_readiness_v1"
CONTRACT_CONFIG_REL_PATH = (
    "config/governance/canonical_i17_productive_shadow_contract_readiness_v1.json"
)
CANONICAL_SERIALIZATION_VERSION = (
    "canonical_i17_productive_shadow_contract_readiness_canonical_json_v1"
)

REMEDIATION_ID = "R4_I17_SHADOW_CONTRACT_AND_EVIDENCE_READINESS"
SOURCE_GAP_IDS = ("EG-I17-SHADOW", "I17", "UQ7")
SOURCE_INTENT = "I17"
CURRENT_ROLE = "TRANSITIONAL_GATE"
CURRENT_STATE = "PARTIAL_INACTIVE_GATED"
TARGET = "PRODUCTIVE_SHADOW_CONTRACT_READY_BUT_NOT_EXECUTED"
DONE_CRITERION = "CONTRACT_READINESS_WITHOUT_PRODUCTIVE_SHADOW_EXECUTE"

CANONICAL_SHADOW_CONTRACT_OWNER = (
    "ops.paper_shadow_observation_operator_go_session_preregistration_v1"
)
CANONICAL_SHADOW_OFFLINE_RUNNER_OWNER = "ops.integrated_paper_shadow_observation_session_v1"
CANONICAL_SHADOW_RUNNER_OWNER = (
    "ops.integrated_paper_shadow_observation_wallclock_session_execution_v1"
)
CANONICAL_SHADOW_PRODUCTIVE_ISSUANCE_OWNER = (
    "ops.integrated_paper_shadow_productive_authorization_issuance_and_real_network_execution_v1"
)
CANONICAL_SHADOW_EVIDENCE_OWNER = "ops.integrated_paper_shadow_observation_session_v1.evidence_v1"
CANONICAL_SHADOW_IDENTITY_BINDING = (
    "ops.paper_shadow_observation_operator_go_session_preregistration_v1"
    ".i17_paper_shadow_named_lane_identity_join_v1"
)
CANONICAL_SHADOW_PROMOTION_CONSUMER = "governance.promotion_loop.experiment_lineage_ref_producer_v1"
CANONICAL_SHADOW_ECONOMIC_OWNER = "ops.integrated_paper_shadow_economic_validity_pipeline_v1"
CANONICAL_SHADOW_RESTART_OWNER = (
    "ops.integrated_paper_shadow_observation_session_v1.session_lifecycle_v1"
)
I16_PROMOTION_LINEAGE_OWNER = "governance.promotion_loop.experiment_lineage_ref_producer_v1"
I82_IDENTITY_OWNER = "experiments.cross_lane_identity_join_v1"
R2_IDENTITY_OWNER = "src.strategies.registry.resolve_strategy_id"
R3_REGIME_META_OWNER = "regime.canonical_regime_meta_gated_selection_v1.gate_v1"

I57_CLASSIFICATION = "FORWARD_SIGNAL_ONLY_NOT_I17"
I67_CLASSIFICATION = "LOCAL_PAPER_SIMULATION_NOT_I17"
CAP7_INTERNAL_SIM_CLASSIFICATION = "INTERNAL_SIMULATED_NOT_I17"

REQUIRED_OWNER_RELPATHS = (
    "src/ops/paper_shadow_observation_operator_go_session_preregistration_v1/preregistration_contract_v1.py",
    "src/ops/paper_shadow_observation_operator_go_session_preregistration_v1/i17_paper_shadow_named_lane_identity_join_v1.py",
    "src/ops/integrated_paper_shadow_observation_session_v1/entrypoint_v1.py",
    "src/ops/integrated_paper_shadow_observation_session_v1/evidence_v1.py",
    "src/ops/integrated_paper_shadow_observation_session_v1/no_order_guard_v1.py",
    "src/ops/integrated_paper_shadow_observation_session_v1/session_lifecycle_v1.py",
    "src/ops/integrated_paper_shadow_observation_wallclock_session_execution_v1/constants_v1.py",
    "src/ops/integrated_paper_shadow_productive_authorization_issuance_and_real_network_execution_v1/constants_v1.py",
    "src/ops/integrated_paper_shadow_economic_validity_pipeline_v1.py",
    "src/governance/promotion_loop/experiment_lineage_ref_producer_v1.py",
    "src/experiments/cross_lane_identity_join_v1.py",
)

EVIDENCE_PACK_REQUIRED_FIELDS = (
    "mode",
    "run_id",
    "campaign_id",
    "session_id",
    "experiment_identity_id",
    "legacy_alias_md5_12",
    "origin_main_sha",
    "config_digest",
    "code_identity",
    "canonical_strategy_id",
    "regime_meta_provenance",
    "timestamps",
    "market_data_provenance",
    "decision_outputs",
    "risk_safety_outcomes",
    "zero_order_assertion",
    "restart_recovery_evidence",
    "reconciliation_economic_outputs",
    "evidence_manifest_seal",
    "verifier_result",
    "promotion_eligible",
    "promotion_eligible_reason",
    "authorization_state",
    "preflight_result",
    "network_permission_state",
    "order_permission_state",
    "trading_authority",
    "promotion_authority",
    "terminal_state",
)

CORE_LOGIC_CHANGE = False
RUNTIME_EFFECT = False
RUNTIME_AUTHORIZATION_EFFECT = "NONE"
AUTHORITY_EFFECT = "NONE"
RUNTIME_AUTHORITY_IMPACT = "NONE"
ACTIVATED = False
PRODUCTIVE_CALLER_EXISTS = False
PRODUCTIVE_SHADOW_EXECUTED = False
PRODUCTIVE_SHADOW_EVIDENCE_PROVEN = False
WALLCLOCK_SESSION_STARTED = False
NETWORK_SESSION_STARTED = False
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

I57_SUBSTITUTE_FORBIDDEN = True
I67_SUBSTITUTE_FORBIDDEN = True
MD5_12_CANONICAL_REF_FORBIDDEN = True
OWNER_GO_SHADOW_EXECUTE_REQUIRED = True
