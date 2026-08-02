"""Constants for PHASE_9_1_STRATEGY_REGISTRY_CLOSURE_V1."""

from __future__ import annotations

CAPABILITY_ID = "PHASE_9_1_STRATEGY_REGISTRY_CLOSURE_V1"
SCHEMA_VERSION = "phase_9_1_strategy_registry_closure.v1"
PRODUCER_VERSION = "phase_9_1_strategy_registry_closure.v1"
OWNER = "ops.phase_9_1_strategy_registry_closure_v1"
AUTHORITY_OWNER = OWNER
PACKAGE_MARKER = "PHASE_9_1_STRATEGY_REGISTRY_CLOSURE_V1=true"

PREDECESSOR_CAPABILITY_ID = "CAPABILITY_7_2_SINGLE_FUTURE_STATEFUL_NO_ORDER_RUNTIME_ACTIVATION_V1"
PREDECESSOR_MERGE_SHA = "93409b8c65184d1534ffa84da7a163a037b67fc1"

CORE_LOGIC_CHANGE = False
LIVE_PATH_CHANGED = False
TESTNET_PATH_CHANGED = False
ORDER_PATH_CHANGED = False
EXCHANGE_CREDENTIAL_PATH_CHANGED = False
NETWORK_SESSION_ALLOWED = False
AUTHORIZATION_CONSUMPTION_ALLOWED = False
LIVE_ORDERS = False
TESTNET_ORDERS = False
PAPER_EXCHANGE_ORDERS = False
EXCHANGE_CREDENTIAL_USE = False
REAL_CAPITAL_MOVEMENT = False
MULTI_FUTURE_RUNTIME_AUTHORIZED = False
DASHBOARD_AUTHORITY_EFFECT = "NONE"
SILENT_AUTHORITY_PROMOTION = False

CONFIG_RELATIVE_PATH = "config/ops/phase_9_1_strategy_registry_closure_v1.json"
CONFIG_SCHEMA_VERSION = "phase_9_1_strategy_registry_closure_config.v1"

# Bound to existing strategy registry schema/policy (reuse-before-new).
BOUND_REGISTRY_SCHEMA_VERSION = "strategy_registry_v1"
BOUND_REGISTRY_POLICY_VERSION = "strategy_registry_policy_v1"

EVIDENCE_DIRNAME = "capability_phase_9_1_strategy_registry_closure_v1"
EVIDENCE_FILENAME = "phase_9_1_strategy_registry_closure_evidence_v1.json"
RESULT_FILENAME = "phase_9_1_strategy_registry_closure_result_v1.json"
MATRIX_FILENAME = "strategy_registry_matrix_v1.json"
CALL_GRAPH_FILENAME = "call_graph_v1.json"
BYPASS_PROOF_FILENAME = "bypass_negative_proof_v1.json"
FAILURE_INJECTION_FILENAME = "failure_injection_results.json"
PARITY_PROOF_FILENAME = "parity_proof_v1.json"
RESTART_PROOF_FILENAME = "restart_reconstruction_proof_v1.json"
CLAIM_MATRIX_FILENAME = "claim_matrix_v1.json"
MANIFEST_FILENAME = "MANIFEST.sha256"

PRODUCTIVE_HOST = (
    "src/ops/wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_v1/"
    "decision_economics_cycle_bridge_v1.py"
)
PRODUCTIVE_HOST_ENTRY = (
    "ops.wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_v1."
    "decision_economics_cycle_bridge_v1.run_bridge_cycle_v1"
)
MASTER_V2_AUTHORITY = "trading.master_v2.integrated_offline_trading_logic_replay_v1"
DOUBLE_PLAY_AUTHORITY = (
    "trading.master_v2.double_play_entry_exit_policy_v0.evaluate_double_play_entry_exit_policy_v0"
)
SUITABILITY_ADAPTER = "src.strategies.suitability_registry_adapter_v1"
REGISTRY_OWNER = "src.strategies.registry"

CLASSIFICATION_TIERS = (
    "CANONICAL_AUTHORITY",
    "AUTHORIZED_COMPOSITION_INPUT",
    "RESEARCH_INFORMATION",
    "EXPERIMENT_ONLY",
    "LEGACY_DEAUTHORIZED",
)

# Host-local suitability stub used by Cap 7.2 productive bridge (not a registry strategy).
HOST_COMPOSITION_STUB_ID = "strat-momentum-v1"

# Orphan module present under src/strategies but absent from strategy registry.
ORPHAN_MODULE_IDS = ("breakout_confirmation_v1",)

CALL_GRAPH_V1 = (
    "phase_9_1_config_bind",
    "strategy_registry_snapshot_load",
    "classification_matrix_build",
    "productive_caller_enumeration",
    "composition_eligibility_gate",
    "bypass_negative_proof",
    "restart_deterministic_reconstruction",
    "parity_proof",
    "evidence_materialize",
)
