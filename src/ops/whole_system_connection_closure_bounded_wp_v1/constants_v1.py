"""Forensic census verdict for WHOLE_SYSTEM_CONNECTION_CLOSURE_BOUNDED_WP_V1 (proof-only)."""

from __future__ import annotations

PACKAGE_MARKER = "WHOLE_SYSTEM_CONNECTION_CLOSURE_BOUNDED_WP_V1=true"
OWNER = "ops.whole_system_connection_closure_bounded_wp_v1"
CONTRACT_VERSION = "whole_system_connection_closure_bounded_wp.v1"
BASELINE_ORIGIN_MAIN_SHA = "46037a171cb7c41d3e1663d92b6db80335a85260"

# Phase-1 census (productive Decision → PRE_EXTERNAL); epistemic labels frozen at closeout.
REQUIRED_CLOSURE_COUNT = 0
UNKNOWN_PRODUCTIVE_PATH_COUNT = 0

WHOLE_SYSTEM_CONNECTION_COMPLETE = True

SOLE_TRADING_DECISION_AUTHORITY = (
    "trading.master_v2.integrated_offline_trading_logic_replay_v1."
    "run_integrated_offline_trading_logic_replay_v1"
)

PRODUCTIVE_CURSOR_BACKED_CYCLE_CALLERS = (
    "src/ops/governed_productive_account_equity_authority_producer_v1/"
    "current_productive_fresh_runtime_to_pre_external_effect_applicability_v1.py",
    "src/ops/governed_productive_account_equity_authority_producer_v1/"
    "current_productive_fresh_runtime_from_persisted_cursor_to_pre_external_effect_applicability_v1.py",
    "src/ops/governed_productive_account_equity_authority_producer_v1/"
    "current_productive_fresh_runtime_cycle_after_non_executable_decision_v3.py",
    "src/ops/current_mf_n5_full_autonomy_occupied_lane_mv2_dp_decision_state_addressing_join_v1/"
    "addressing_join_v1.py",
)

INTENTIONALLY_LEGACY_CYCLE_CALLERS = (
    "src/ops/governed_productive_account_equity_authority_producer_v1/"
    "current_productive_fresh_runtime_cycle_after_non_executable_decision_v1.py",
    "src/ops/governed_productive_account_equity_authority_producer_v1/"
    "current_productive_fresh_runtime_cycle_after_non_executable_decision_v2.py",
    "src/ops/governed_productive_account_equity_authority_producer_v1/"
    "current_productive_fresh_runtime_cycle_after_flatten_occupancy_absent_v1.py",
    "src/ops/governed_productive_account_equity_authority_producer_v1/"
    "current_productive_fresh_runtime_cycle_to_exact_envelope_bound_single_use_post_boundary_v1.py",
)

FINAL_D_T_ADJUDICATION_CLASS = "INTENTIONALLY_ISOLATED"
CURSORLESS_CALLER_ADJUDICATION_CLASS = "INTENTIONALLY_LEGACY"
MECHANICAL_COMPLETION_ADJUDICATION_CLASS = "ALREADY_ADJUDICATED"
CUTOVER_FLAGS_ADJUDICATION_CLASS = "REMAIN_FALSE_BY_DESIGN"

assert REQUIRED_CLOSURE_COUNT == 0
assert UNKNOWN_PRODUCTIVE_PATH_COUNT == 0
assert WHOLE_SYSTEM_CONNECTION_COMPLETE is True

__all__ = [
    "BASELINE_ORIGIN_MAIN_SHA",
    "CONTRACT_VERSION",
    "CURSORLESS_CALLER_ADJUDICATION_CLASS",
    "CUTOVER_FLAGS_ADJUDICATION_CLASS",
    "FINAL_D_T_ADJUDICATION_CLASS",
    "INTENTIONALLY_LEGACY_CYCLE_CALLERS",
    "MECHANICAL_COMPLETION_ADJUDICATION_CLASS",
    "OWNER",
    "PACKAGE_MARKER",
    "PRODUCTIVE_CURSOR_BACKED_CYCLE_CALLERS",
    "REQUIRED_CLOSURE_COUNT",
    "SOLE_TRADING_DECISION_AUTHORITY",
    "UNKNOWN_PRODUCTIVE_PATH_COUNT",
    "WHOLE_SYSTEM_CONNECTION_COMPLETE",
]
