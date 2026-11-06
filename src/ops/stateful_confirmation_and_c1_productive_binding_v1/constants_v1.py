"""Constants for CAPABILITY_6_1_STATEFUL_CONFIRMATION_AND_C1_PRODUCTIVE_BINDING_V1."""

from __future__ import annotations

CAPABILITY_ID = "CAPABILITY_6_1_STATEFUL_CONFIRMATION_AND_C1_PRODUCTIVE_BINDING_V1"
SCHEMA_VERSION = "stateful_confirmation_and_c1_productive_binding.v1"
PRODUCER_VERSION = "stateful_confirmation_and_c1_productive_binding.v1"
PACKAGE_MARKER = "STATEFUL_CONFIRMATION_AND_C1_PRODUCTIVE_BINDING_V1=true"
OWNER = "ops.stateful_confirmation_and_c1_productive_binding_v1"
AUTHORITY_OWNER = OWNER
STATE_VERSION = "v1"

C1_PRODUCTIVELY_BOUND = True
C2_PRODUCTIVELY_BOUND = True
C3_PRODUCTIVELY_BOUND = True
CORE_LOGIC_CHANGE = False
ACTIVATION_CHANGED = False
RUNTIME_ACTIVATED = False
LIVE_PATH_CHANGED = False
TESTNET_PATH_CHANGED = False
ORDER_PATH_CHANGED = False
EXCHANGE_CREDENTIAL_PATH_CHANGED = False
NETWORK_SESSION_ALLOWED = False
AUTHORIZATION_CONSUMPTION_ALLOWED = False
SILENT_CONFIRMATION_REINITIALIZATION = False

MASTER_V2_NEW_PERSISTENCE_DOMAIN_MODEL_ALLOWED = False
DOUBLE_PLAY_NEW_PERSISTENCE_DOMAIN_MODEL_ALLOWED = False
SERIALIZATION_ADAPTER_HAS_NO_DECISION_AUTHORITY = True
FORCED_INTENT_ALLOWED = False
MASTER_V2_BYPASS_ALLOWED = False
DOUBLE_PLAY_BYPASS_ALLOWED = False
COMPOSITION_BYPASS_ALLOWED = False
RISK_BYPASS_ALLOWED = False
SAFETY_BYPASS_ALLOWED = False
DIRECT_FILL_INJECTION_ALLOWED = False

PRODUCTIVE_HOST = (
    "src/ops/wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_v1/"
    "decision_economics_cycle_bridge_v1.py"
)
PRODUCTIVE_DECISION_OWNER = (
    "trading.master_v2.integrated_offline_trading_logic_replay_v1."
    "run_integrated_offline_trading_logic_replay_v1"
)
C1_OWNER = "trading.market_state.distinct_market_observation_acceptor_v1"
C2_OWNER = "trading.market_state.directional_confirmation_progress_v1"
C3_OWNER = "trading.master_v2.directional_assessment_confirmation_integration_v1"

DEFAULT_VENUE = "OKX"
SINGLE_WRITER_IDENTITY = "stateful_confirmation_and_c1_productive_binding_v1_writer"
WRITER_LOCK_FILENAME = "confirmation_writer.lock"
CONFIRMATION_STATE_FILENAME = "confirmation_state_v1.json"
COMMIT_MARKER_FILENAME = "confirmation_commit_marker_v1.json"
MANIFEST_FILENAME = "MANIFEST.sha256"
EVIDENCE_FILENAME = "stateful_confirmation_and_c1_productive_binding_evidence_v1.json"
RESULT_FILENAME = "stateful_confirmation_and_c1_productive_binding_result_v1.json"
GATE_FILENAME = "stateful_confirmation_gate_results_v1.json"
FAILURE_INJECTION_FILENAME = "failure_injection_results.json"
STAGING_DIRNAME_PREFIX = ".cap61_confirmation_staging_"
SESSION_LOCK_FILENAME = "cap61_confirmation_session.lock"

CALL_GRAPH_C1_STEP = "distinct_market_observation_acceptor"
CALL_GRAPH_C1_RESULT_STEP = "observation_acceptance_result"
CALL_GRAPH_C2_STEP = "directional_confirmation_progress"
CALL_GRAPH_C3_STEP = "directional_assessment_confirmation_integration"
CALL_GRAPH_COMMIT_STEP = "canonical_confirmation_state_commit"

CALL_GRAPH_BEFORE = (
    "persisted_single_selected_future",
    "selection_integrity_freshness_validation",
    "ranking_snapshot_reference_validation",
    "governed_universe_instrument_validation",
    "venue_native_instrument_binding",
    "single_selected_future_runtime_binding",
    "productive_reconciliation_startup_gate",
    "okx_public_market_data",
    "feature_pipeline",
    "regime_pipeline",
    "master_v2_double_play_integrated_offline_replay",
    "risk_position_sizing",
    "safety_kernel",
    "intended_side_quantity",
    "analytical_simulated_execution",
    "simulated_fill_fee_slippage",
    "canonical_futures_accounting",
    "session_persistent_portfolio",
    "realized_unrealized_pnl_equity_drawdown",
    "risk_state_from_accounting",
    "simulated_economics_no_order_path",
    "evidence",
    "full_economic_reconstruction_verifier",
)

CALL_GRAPH_AFTER = (
    "persisted_single_selected_future",
    "selection_integrity_freshness_validation",
    "ranking_snapshot_reference_validation",
    "governed_universe_instrument_validation",
    "venue_native_instrument_binding",
    "single_selected_future_runtime_binding",
    "productive_reconciliation_startup_gate",
    "okx_public_market_data",
    CALL_GRAPH_C1_STEP,
    CALL_GRAPH_C1_RESULT_STEP,
    "feature_pipeline",
    "regime_pipeline",
    CALL_GRAPH_C2_STEP,
    CALL_GRAPH_C3_STEP,
    "master_v2_double_play_integrated_offline_replay",
    CALL_GRAPH_COMMIT_STEP,
    "risk_position_sizing",
    "safety_kernel",
    "intended_side_quantity",
    "analytical_simulated_execution",
    "simulated_fill_fee_slippage",
    "canonical_futures_accounting",
    "session_persistent_portfolio",
    "realized_unrealized_pnl_equity_drawdown",
    "risk_state_from_accounting",
    "simulated_economics_no_order_path",
    "evidence",
    "full_economic_reconstruction_verifier",
)

REQUIRED_GATE_FLAGS = (
    "C1_PRODUCTIVELY_BOUND",
    "C2_PRODUCTIVELY_BOUND",
    "C3_PRODUCTIVELY_BOUND",
    "DUPLICATE_DOES_NOT_ADVANCE",
    "NO_SAMPLE_DOES_NOT_ADVANCE",
    "DECISION_CYCLE_DOES_NOT_ADVANCE_CONFIRMATION",
    "CONFIRMATION_SESSION_ID_STABLE",
    "CONFIRMATION_STATE_PERSISTED",
    "CONFIRMATION_RESTART_PROVEN",
    "INSTRUMENT_ISOLATION",
    "SINGLE_WRITER_PROVEN",
    "SILENT_CONFIRMATION_REINITIALIZATION_FALSE",
    "CORE_LOGIC_UNCHANGED",
    "GOLDEN_VECTOR_PARITY_PASS",
    "CALL_ORDER_PARITY_PROVEN",
    "INPUT_OUTPUT_PARITY_PROVEN",
    "STATE_TRANSITION_PARITY_PROVEN",
    "DECISION_REASON_PARITY_PROVEN",
    "RISK_PARITY_PROVEN",
    "SAFETY_PARITY_PROVEN",
    "EXIT_PRECEDENCE_PARITY_PROVEN",
    "DETERMINISTIC_REPLAY_PROVEN",
    "FAILURE_INJECTION_PROVEN",
    "EVIDENCE_VERIFIED",
    "RUNTIME_NOT_ACTIVATED",
    "NO_LIVE_ORDER_PATH",
    "NO_TESTNET_ORDER_PATH",
    "NO_NETWORK_ACCESS",
    "AUTHORIZATION_NOT_CONSUMED",
)

# Domain-to-persistence classification matrix (canonical domain contracts only).
DOMAIN_TO_PERSISTENCE_MATRIX = (
    {
        "domain_field": "last_accepted_observation_identity",
        "canonical_owner": C1_OWNER,
        "classification": "PERSIST_DIRECTLY",
        "reason": "C1 epoch/identity cursor restore",
    },
    {
        "domain_field": "market_observation_epoch",
        "canonical_owner": C1_OWNER,
        "classification": "PERSIST_DIRECTLY",
        "reason": "monotonic DISTINCT epoch restore",
    },
    {
        "domain_field": "bound_instrument_key",
        "canonical_owner": C1_OWNER,
        "classification": "PERSIST_DIRECTLY",
        "reason": "instrument isolation",
    },
    {
        "domain_field": "last_accepted_transport",
        "canonical_owner": C1_OWNER,
        "classification": "EPHEMERAL",
        "reason": "transport never distinctness authority; optional diagnostics only",
    },
    {
        "domain_field": "confirmation_session_id",
        "canonical_owner": OWNER,
        "classification": "PERSIST_DIRECTLY",
        "reason": "stable lifecycle identity",
    },
    {
        "domain_field": "bull_confirmation_state",
        "canonical_owner": C3_OWNER,
        "classification": "PERSIST_DIRECTLY",
        "reason": "C2 cursor via C3 side carrier",
    },
    {
        "domain_field": "bear_confirmation_state",
        "canonical_owner": C3_OWNER,
        "classification": "PERSIST_DIRECTLY",
        "reason": "C2 cursor via C3 side carrier",
    },
    {
        "domain_field": "repository_sha",
        "canonical_owner": OWNER,
        "classification": "PERSIST_DIRECTLY",
        "reason": "binding integrity",
    },
    {
        "domain_field": "config_digest",
        "canonical_owner": OWNER,
        "classification": "PERSIST_DIRECTLY",
        "reason": "config binding integrity",
    },
    {
        "domain_field": "state_version",
        "canonical_owner": OWNER,
        "classification": "PERSIST_DIRECTLY",
        "reason": "schema version gate",
    },
    {
        "domain_field": "commit_identity",
        "canonical_owner": OWNER,
        "classification": "PERSIST_DIRECTLY",
        "reason": "commit marker / restart cursor",
    },
    {
        "domain_field": "feature_vectors",
        "canonical_owner": "feature_pipeline",
        "classification": "REBUILD_DETERMINISTICALLY",
        "reason": "rebuild from market observations",
    },
    {
        "domain_field": "DirectionalAssessmentV1",
        "canonical_owner": "trading.master_v2.directional_assessment_v1",
        "classification": "REBUILD_DETERMINISTICALLY",
        "reason": "derived from C3 evaluation",
    },
    {
        "domain_field": "MasterV2_internal_decision_dto",
        "canonical_owner": PRODUCTIVE_DECISION_OWNER,
        "classification": "FORBIDDEN_TO_PERSIST",
        "reason": "no parallel Master V2 persistence domain",
    },
    {
        "domain_field": "DoublePlay_internal_decision_dto",
        "canonical_owner": "trading.master_v2.double_play_composition_matrix_v1",
        "classification": "FORBIDDEN_TO_PERSIST",
        "reason": "no parallel Double Play persistence domain",
    },
    {
        "domain_field": "evidence_ledgers",
        "canonical_owner": OWNER,
        "classification": "EVIDENCE_ONLY",
        "reason": "claim surfaces only",
    },
)
