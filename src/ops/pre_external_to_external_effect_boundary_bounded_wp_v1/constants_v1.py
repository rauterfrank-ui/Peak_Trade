"""Forensic census verdict for PRE_EXTERNAL_TO_EXTERNAL_EFFECT_BOUNDARY_BOUNDED_WP_V1 (proof-only)."""

from __future__ import annotations

PACKAGE_MARKER = "PRE_EXTERNAL_TO_EXTERNAL_EFFECT_BOUNDARY_BOUNDED_WP_V1=true"
OWNER = "ops.pre_external_to_external_effect_boundary_bounded_wp_v1"
CONTRACT_VERSION = "pre_external_to_external_effect_boundary_bounded_wp.v1"
BASELINE_ORIGIN_MAIN_SHA = "08fa64c22cfa073c2b32ee9238828b83694790c2"

REQUIRED_CLOSURE_COUNT = 0
UNKNOWN_BOUNDARY_PATH_COUNT = 0
PRE_EXTERNAL_TO_EXTERNAL_EFFECT_BOUNDARY_COMPLETE = True

# Phase-A census: CURRENT productive terminals at PRE_EXTERNAL (claims + orchestrators).
PRE_EXTERNAL_PRODUCTIVE_ENTRY_MODULES = (
    "src/ops/governed_productive_account_equity_authority_producer_v1/"
    "current_productive_fresh_runtime_to_pre_external_effect_applicability_v1.py",
    "src/ops/governed_productive_account_equity_authority_producer_v1/"
    "current_productive_fresh_runtime_from_persisted_cursor_to_pre_external_effect_applicability_v1.py",
    "src/ops/governed_productive_account_equity_authority_producer_v1/"
    "current_productive_fresh_runtime_cycle_after_non_executable_decision_v3.py",
    "src/ops/full_core_live_path_composition_root_v1/"
    "current_productive_governed_cycle_orchestrator_v1.py",
    "src/ops/full_core_live_path_composition_root_v1/"
    "current_productive_governed_continuous_cycle_orchestrator_v1.py",
)

INTENTIONALLY_LEGACY_PRE_EXTERNAL_CLAIM_MODULES = (
    "src/ops/governed_productive_account_equity_authority_producer_v1/"
    "current_productive_fresh_runtime_cycle_after_non_executable_decision_v1.py",
    "src/ops/governed_productive_account_equity_authority_producer_v1/"
    "current_productive_fresh_runtime_cycle_after_non_executable_decision_v2.py",
    "src/ops/governed_productive_account_equity_authority_producer_v1/"
    "current_productive_fresh_runtime_cycle_after_flatten_occupancy_absent_v1.py",
)

# Canonical join before any venue mutation (Full-Core live path authority).
EXECUTION_BOUNDARY_OWNER = (
    "src.ops.full_core_live_path_composition_root_v1.execution_boundary_v1."
    "halt_at_live_execution_boundary_v1"
)
EXTERNAL_EFFECT_GATE_OWNER = (
    "src.ops.full_core_live_path_composition_root_v1.external_effect_gate_v1."
    "evaluate_external_effect_v1"
)
ENVELOPE_BOUND_SEND_SEAM_OWNER = (
    "src.ops.full_core_live_path_composition_root_v1."
    "envelope_bound_external_effect_send_seam_v1."
    "attempt_envelope_bound_external_effect_send_v1"
)

# Static sink surfaces (reachable only from classified Owner-GO / proof modules).
EXTERNAL_EFFECT_SINK_SURFACES = (
    "evaluate_external_effect_v1",
    "invoke_external_effect_v1",
    "attempt_envelope_bound_external_effect_send_v1",
    "FullCoreGatedProductiveWireTransportV1.attempt_trade_order_post",
    "FullCoreProductiveHttpTradeOrderTransportV1.post_trade_order",
    "run_productive_wire_send_orchestrator_v1",
)

INTENTIONALLY_ISOLATED_OWNER_GO_POST_SLICES = (
    "src/ops/governed_productive_account_equity_authority_producer_v1/"
    "current_productive_envelope_bound_single_use_external_effect_send_seam_v1.py",
    "src/ops/governed_productive_account_equity_authority_producer_v1/"
    "current_productive_fresh_runtime_cycle_to_exact_envelope_bound_single_use_post_boundary_v1.py",
    "src/ops/governed_productive_account_equity_authority_producer_v1/"
    "current_productive_fresh_cap23_cap24_decision_and_one_shot_real_post_readiness_v1.py",
    "src/ops/governed_productive_account_equity_authority_producer_v1/"
    "current_productive_exact_object_disposition_to_one_shot_flatten_post_boundary_v1.py",
    "src/ops/full_core_live_path_composition_root_v1/"
    "current_productive_one_shot_fresh_envelope_permit_mint_durable_consume_and_post_join_v1.py",
)

CANARY_WIRE_SEND_HARNESS_PREFIX = (
    "src/ops/section_11_14_current_sui_xperp_pos_1_flatten_authority_and_pre_execution_repair_v1/"
)

STANDING_LIVE_PREDICATES_ADJUDICATION_CLASS = "NON_IMPLYING_STANDING_TRUE"
STEP_29Q_ADJUDICATION_CLASS = "PLAN_ONLY_FAIL_CLOSED"
PERMIT_MINT_ADJUDICATION_CLASS = "INTENTIONALLY_ISOLATED_OWNER_GO"
CONTINUOUS_RUN_ADJUDICATION_CLASS = "DEFINED_NOT_AUTHORIZED"

assert REQUIRED_CLOSURE_COUNT == 0
assert UNKNOWN_BOUNDARY_PATH_COUNT == 0
assert PRE_EXTERNAL_TO_EXTERNAL_EFFECT_BOUNDARY_COMPLETE is True

__all__ = [
    "BASELINE_ORIGIN_MAIN_SHA",
    "CANARY_WIRE_SEND_HARNESS_PREFIX",
    "CONTRACT_VERSION",
    "CONTINUOUS_RUN_ADJUDICATION_CLASS",
    "ENVELOPE_BOUND_SEND_SEAM_OWNER",
    "EXECUTION_BOUNDARY_OWNER",
    "EXTERNAL_EFFECT_GATE_OWNER",
    "EXTERNAL_EFFECT_SINK_SURFACES",
    "INTENTIONALLY_ISOLATED_OWNER_GO_POST_SLICES",
    "INTENTIONALLY_LEGACY_PRE_EXTERNAL_CLAIM_MODULES",
    "OWNER",
    "PACKAGE_MARKER",
    "PERMIT_MINT_ADJUDICATION_CLASS",
    "PRE_EXTERNAL_PRODUCTIVE_ENTRY_MODULES",
    "PRE_EXTERNAL_TO_EXTERNAL_EFFECT_BOUNDARY_COMPLETE",
    "REQUIRED_CLOSURE_COUNT",
    "STANDING_LIVE_PREDICATES_ADJUDICATION_CLASS",
    "STEP_29Q_ADJUDICATION_CLASS",
    "UNKNOWN_BOUNDARY_PATH_COUNT",
]
