"""Constants for CAPABILITY_6_2_DYNAMIC_SCOPE_PERSISTENCE_BINDING_V1."""

from __future__ import annotations

from src.ops.decision_config_ownership_and_consumer_closure_v1.canonical_values_v1 import (
    CANONICAL_ADVERSE_EXIT_DISTANCE as FROZEN_ADVERSE_EXIT_DISTANCE,
    CANONICAL_REVERSAL_DISTANCE as FROZEN_REVERSAL_DISTANCE,
    CANONICAL_UP_DISTANCE as FROZEN_UP_DISTANCE,
)

CAPABILITY_ID = "CAPABILITY_6_2_DYNAMIC_SCOPE_PERSISTENCE_BINDING_V1"
SCHEMA_VERSION = "dynamic_scope_persistence_binding.v1"
PRODUCER_VERSION = "dynamic_scope_persistence_binding.v1"
PACKAGE_MARKER = "DYNAMIC_SCOPE_PERSISTENCE_BINDING_V1=true"
OWNER = "ops.dynamic_scope_persistence_binding_v1"
AUTHORITY_OWNER = OWNER
STATE_VERSION = "v1"

DYNAMIC_SCOPE_PRODUCTIVELY_BOUND = True
DYNAMIC_SCOPE_STATE_PERSISTED = True
DYNAMIC_SCOPE_RESTART_PROVEN = True
SCOPE_REINITIALIZATION_ONLY_WHEN_SEMANTICALLY_VALID = True
SILENT_DYNAMIC_SCOPE_REINITIALIZATION = False
CORE_LOGIC_CHANGE = False
ACTIVATION_CHANGED = False
RUNTIME_ACTIVATED = False
LIVE_PATH_CHANGED = False
TESTNET_PATH_CHANGED = False
ORDER_PATH_CHANGED = False
EXCHANGE_CREDENTIAL_PATH_CHANGED = False
NETWORK_SESSION_ALLOWED = False
AUTHORIZATION_CONSUMPTION_ALLOWED = False

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
RUNTIME_SCOPE_STATE_OWNER = "trading.master_v2.double_play_state.RuntimeScopeState"
CANONICAL_SCOPE_SNAPSHOT_OWNER = (
    "trading.master_v2.canonical_scope_initialization_v1.CanonicalScopeSnapshotV1"
)
SCOPE_TRANSITION_OWNER = "trading.master_v2.double_play_state.transition_state"
SCOPE_BOUNDARY_OWNER = "trading.master_v2.double_play_state.update_dynamic_boundaries"
CONFIRMATION_BINDING_OWNER = "ops.stateful_confirmation_and_c1_productive_binding_v1"

DEFAULT_VENUE = "OKX"
SINGLE_WRITER_IDENTITY = "dynamic_scope_persistence_binding_v1_writer"
WRITER_LOCK_FILENAME = "dynamic_scope_writer.lock"
SCOPE_STATE_FILENAME = "dynamic_scope_state_v1.json"
COMMIT_MARKER_FILENAME = "dynamic_scope_commit_marker_v1.json"
MANIFEST_FILENAME = "MANIFEST.sha256"
EVIDENCE_FILENAME = "dynamic_scope_persistence_binding_evidence_v1.json"
RESULT_FILENAME = "dynamic_scope_persistence_binding_result_v1.json"
GATE_FILENAME = "dynamic_scope_gate_results_v1.json"
FAILURE_INJECTION_FILENAME = "failure_injection_results.json"
STAGING_DIRNAME_PREFIX = ".cap62_dynamic_scope_staging_"
SESSION_LOCK_FILENAME = "cap62_dynamic_scope_session.lock"

CALL_GRAPH_PREVIOUS_SCOPE_STEP = "previous_canonical_runtime_scope_state"
CALL_GRAPH_SCOPE_TRANSITION_STEP = "dynamic_scope_transition"
CALL_GRAPH_SCOPE_COMMIT_STEP = "canonical_dynamic_scope_state_commit"

CALL_GRAPH_BEFORE = (
    "persisted_single_selected_future",
    "selection_integrity_freshness_validation",
    "ranking_snapshot_reference_validation",
    "governed_universe_instrument_validation",
    "venue_native_instrument_binding",
    "single_selected_future_runtime_binding",
    "productive_reconciliation_startup_gate",
    "okx_public_market_data",
    "distinct_market_observation_acceptor",
    "observation_acceptance_result",
    "feature_pipeline",
    "regime_pipeline",
    "directional_confirmation_progress",
    "directional_assessment_confirmation_integration",
    "master_v2_double_play_integrated_offline_replay",
    "canonical_confirmation_state_commit",
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
    "distinct_market_observation_acceptor",
    "observation_acceptance_result",
    "feature_pipeline",
    "regime_pipeline",
    "directional_confirmation_progress",
    "directional_assessment_confirmation_integration",
    CALL_GRAPH_PREVIOUS_SCOPE_STEP,
    "master_v2_double_play_integrated_offline_replay",
    CALL_GRAPH_SCOPE_TRANSITION_STEP,
    "canonical_confirmation_state_commit",
    CALL_GRAPH_SCOPE_COMMIT_STEP,
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

ALLOWED_RESET_REASONS = (
    "FIRST_EVER_STATE",
    "OWNER_AUTHORIZED_RESET",
    "INSTRUMENT_IDENTITY_CHANGE",
    "CANONICAL_INVALIDATION_TRANSITION",
    "STATE_VERSION_MIGRATION",
    "GOVERNED_RECOVERY",
)

REQUIRED_GATE_FLAGS = (
    "DYNAMIC_SCOPE_PRODUCTIVELY_BOUND",
    "DYNAMIC_SCOPE_STATE_PERSISTED",
    "DYNAMIC_SCOPE_RESTART_PROVEN",
    "SCOPE_REINITIALIZATION_ONLY_WHEN_SEMANTICALLY_VALID",
    "SILENT_DYNAMIC_SCOPE_REINITIALIZATION_FALSE",
    "DUPLICATE_OBSERVATION_SCOPE_ADVANCE_FALSE",
    "NO_SAMPLE_SCOPE_ADVANCE_FALSE",
    "INSTRUMENT_ISOLATION",
    "EVENT_TIME_CONTINUITY_PROVEN",
    "CONFIRMATION_SCOPE_HANDOFF_PROVEN",
    "SINGLE_WRITER_PROVEN",
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

DOMAIN_TO_PERSISTENCE_MATRIX = (
    {
        "domain_field": "runtime_scope_state.anchor_price",
        "canonical_owner": RUNTIME_SCOPE_STATE_OWNER,
        "classification": "PERSIST_DIRECTLY",
        "reason": "trailing envelope SSOT restore",
    },
    {
        "domain_field": "runtime_scope_state.current_upscope_boundary",
        "canonical_owner": RUNTIME_SCOPE_STATE_OWNER,
        "classification": "PERSIST_DIRECTLY",
        "reason": "canonical scope boundary restore",
    },
    {
        "domain_field": "runtime_scope_state.current_downscope_boundary",
        "canonical_owner": RUNTIME_SCOPE_STATE_OWNER,
        "classification": "PERSIST_DIRECTLY",
        "reason": "canonical scope boundary restore",
    },
    {
        "domain_field": "runtime_scope_state.current_hysteresis_band",
        "canonical_owner": RUNTIME_SCOPE_STATE_OWNER,
        "classification": "PERSIST_DIRECTLY",
        "reason": "hysteresis band continuity",
    },
    {
        "domain_field": "runtime_scope_state.last_switch_tick",
        "canonical_owner": RUNTIME_SCOPE_STATE_OWNER,
        "classification": "PERSIST_DIRECTLY",
        "reason": "cooldown bookkeeping",
    },
    {
        "domain_field": "runtime_scope_state.now_tick",
        "canonical_owner": RUNTIME_SCOPE_STATE_OWNER,
        "classification": "PERSIST_DIRECTLY",
        "reason": "event-time ownership via tick cursor",
    },
    {
        "domain_field": "runtime_scope_state.scope_stability_ticks",
        "canonical_owner": RUNTIME_SCOPE_STATE_OWNER,
        "classification": "PERSIST_DIRECTLY",
        "reason": "stability continuity",
    },
    {
        "domain_field": "runtime_scope_state.switches_in_window",
        "canonical_owner": RUNTIME_SCOPE_STATE_OWNER,
        "classification": "PERSIST_DIRECTLY",
        "reason": "switch-window continuity",
    },
    {
        "domain_field": "runtime_scope_state.window_start_tick",
        "canonical_owner": RUNTIME_SCOPE_STATE_OWNER,
        "classification": "PERSIST_DIRECTLY",
        "reason": "switch-window continuity",
    },
    {
        "domain_field": "runtime_scope_state.last_completed_side_switch_tick",
        "canonical_owner": RUNTIME_SCOPE_STATE_OWNER,
        "classification": "PERSIST_DIRECTLY",
        "reason": "cooldown continuity",
    },
    {
        "domain_field": "runtime_scope_state.chop_latched",
        "canonical_owner": RUNTIME_SCOPE_STATE_OWNER,
        "classification": "PERSIST_DIRECTLY",
        "reason": "CHOP scope policy latch",
    },
    {
        "domain_field": "existing_scope CanonicalScopeSnapshotV1",
        "canonical_owner": CANONICAL_SCOPE_SNAPSHOT_OWNER,
        "classification": "PERSIST_DIRECTLY",
        "reason": "identity / evidence snapshot continuity",
    },
    {
        "domain_field": "confirmation_session_id",
        "canonical_owner": CONFIRMATION_BINDING_OWNER,
        "classification": "PERSIST_DIRECTLY",
        "reason": "Cap 6.1 confirmation linkage",
    },
    {
        "domain_field": "market_observation_epoch",
        "canonical_owner": CONFIRMATION_BINDING_OWNER,
        "classification": "PERSIST_DIRECTLY",
        "reason": "event-time / observation continuity",
    },
    {
        "domain_field": "position_context",
        "canonical_owner": OWNER,
        "classification": "PERSIST_DIRECTLY",
        "reason": "position-open / flat linkage for restart",
    },
    {
        "domain_field": "scope_direction_state",
        "canonical_owner": OWNER,
        "classification": "PERSIST_DIRECTLY",
        "reason": "directional context restore",
    },
    {
        "domain_field": "side_state",
        "canonical_owner": OWNER,
        "classification": "PERSIST_DIRECTLY",
        "reason": "directional / active-side cursor for trailing continuity",
    },
    {
        "domain_field": "host_trading_epoch",
        "canonical_owner": OWNER,
        "classification": "PERSIST_DIRECTLY",
        "reason": "host epoch cursor for restart continuity",
    },
    {
        "domain_field": "price_path_tail",
        "canonical_owner": OWNER,
        "classification": "PERSIST_DIRECTLY",
        "reason": "minimal feature rebuild input for restart continuity",
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
        "domain_field": "previous_state_digest",
        "canonical_owner": OWNER,
        "classification": "PERSIST_DIRECTLY",
        "reason": "predecessor commit reference",
    },
    {
        "domain_field": "DynamicScopeRules",
        "canonical_owner": SCOPE_BOUNDARY_OWNER,
        "classification": "REBUILD_DETERMINISTICALLY",
        "reason": "rebuilt from snapshot + frozen policy",
    },
    {
        "domain_field": "ScopeEventEvidence",
        "canonical_owner": "trading.master_v2.deterministic_scope_event_generator_v1",
        "classification": "REBUILD_DETERMINISTICALLY",
        "reason": "derived per cycle from trailing envelope",
    },
    {
        "domain_field": "feature_vectors",
        "canonical_owner": "feature_pipeline",
        "classification": "REBUILD_DETERMINISTICALLY",
        "reason": "rebuild from market observations",
    },
    {
        "domain_field": "cycle_local_mark_price",
        "canonical_owner": PRODUCTIVE_HOST,
        "classification": "EPHEMERAL",
        "reason": "cycle input only",
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
