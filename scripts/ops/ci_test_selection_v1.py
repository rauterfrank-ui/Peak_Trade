#!/usr/bin/env python3
"""Fail-closed diff-aware CI test selection for required tests job (v1)."""

from __future__ import annotations

import argparse
import fnmatch
import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path, PurePosixPath

FULL_CATEGORIES = frozenset(
    {
        "central_src",
        "global_test_infra",
        "dependencies",
        "packaging",
        "coverage_config",
        "config_paths",
        "unknown",
    }
)
NO_OP_CATEGORIES = frozenset({"docs_only", "workflow_only", "static_contract"})
FOCUSED_CATEGORIES = frozenset(
    {
        "scripts_focused",
        "tests_focused",
        "ci_bootstrap_focused",
        "strategy_regime_owner_focused",
        "market_dashboard_focused",
        "durable_completion_focused",
        "preflight_assembly_focused",
        "risk_killswitch_focused",
        "tiny_order_focused",
        "reconciliation_primary_evidence_focused",
        "master_v2_binding_contract_focused",
        "master_v2_replay_display_projection_digest_completion_evidence_focused",
        "offline_master_v2_double_play_scenario_replay_focused",
        "offline_master_v2_replay_six_node_validation_graph_binding_focused",
        "bounded_master_v2_testnet_completion_path_wiring_focused",
        "bounded_network_testnet_preflight_focused",
        "runtime_wallclock_evidence_emitter_focused",
        "testnet_wallclock_duration_evidence_focused",
        "wallclock_focused",
        "ci_infra_focused",
    }
)

# Mapping changes always force FULL (never self-FOCUSED).
CI_MAPPING_FULL_PATHS = frozenset({"config/ci/file_category_mapping.yaml"})

# Bounded canonical CI bootstrap selector + contract-test owner (self-FOCUSED).
CI_BOOTSTRAP_FOCUSED_PATHS = frozenset(
    {
        "scripts/ops/ci_test_selection_v1.py",
        "tests/ci/test_ci_diff_aware_test_selection_v1.py",
    }
)

# Shared / registry / framework prod paths — never strategy_regime_owner_focused.
STRATEGY_REGIME_OWNER_BLOCKED_PROD = frozenset(
    {
        "src/strategies/__init__.py",
        "src/strategies/composite.py",
        "src/strategies/registry.py",
        "src/strategies/base.py",
        "src/strategies/diagnostics.py",
        "src/strategies/regime_aware_portfolio.py",
        "src/regime/__init__.py",
        "src/regime/base.py",
        "src/regime/switching.py",
        "src/regime/config.py",
    }
)

# Explicit canonical test owners (fail-closed when prod is listed).
CANONICAL_STRATEGY_REGIME_TEST_OWNERS: dict[str, str] = {
    "src/strategies/vol_breakout.py": "tests/test_strategies_phase27.py",
    "src/strategies/vol_regime_filter.py": "tests/test_strategy_vol_regime_filter.py",
    "src/regime/detectors.py": "tests/test_regime_detection.py",
    "src/strategies/el_karoui/vol_model.py": "tests/strategies/el_karoui/test_vol_model.py",
}

MARKET_DASHBOARD_CI_POLICY_PATHS = frozenset(
    {
        "scripts/ops/ci_test_selection_v1.py",
        "config/ci/file_category_mapping.yaml",
        "tests/ci/test_ci_diff_aware_test_selection_v1.py",
    }
)

DURABLE_COMPLETION_FACADE_PATH = "src/ops/bounded_futures_testnet_durable_run_primary_evidence_completion_integration_contract_v0.py"

DURABLE_COMPLETION_CI_POLICY_PATHS = frozenset(
    {
        "scripts/ops/ci_test_selection_v1.py",
        "config/ci/file_category_mapping.yaml",
        "tests/ci/test_ci_diff_aware_test_selection_v1.py",
    }
)

DURABLE_COMPLETION_CI_WORKFLOW_REBUNDLE_PATHS = frozenset(
    {
        ".github/workflows/ci.yml",
    }
)

CANONICAL_DURABLE_COMPLETION_FOCUSED_TESTS: tuple[str, ...] = (
    "tests/ops/test_durable_completion_validation_graph_v1.py",
    "tests/ops/test_bounded_futures_testnet_durable_run_primary_evidence_completion_integration_contract_v0.py",
    "tests/ci/test_ci_diff_aware_test_selection_v1.py",
)

REQUIRED_DURABLE_COMPLETION_TEST_OWNERS: tuple[str, ...] = (
    "tests/ops/test_durable_completion_validation_graph_v1.py",
    "tests/ops/test_bounded_futures_testnet_durable_run_primary_evidence_completion_integration_contract_v0.py",
)

DURABLE_COMPLETION_FULL_REFACTOR_SRC_PATHS = frozenset(
    {
        "src/ops/durable_completion_validation/__init__.py",
        "src/ops/durable_completion_validation/identity.py",
        "src/ops/durable_completion_validation/models.py",
    }
)

DURABLE_COMPLETION_VALIDATOR_REBINDING_TEST_PATHS = frozenset(
    {
        "tests/ops/test_durable_completion_validation_graph_v1.py",
        "tests/ops/test_bounded_futures_testnet_durable_run_primary_evidence_completion_integration_contract_v0.py",
    }
)

DURABLE_COMPLETION_COMPLETION_INTEGRATION_TEST_OWNER = "tests/ops/test_bounded_futures_testnet_durable_run_primary_evidence_completion_integration_contract_v0.py"
DURABLE_COMPLETION_VALIDATION_GRAPH_TEST_OWNER = (
    "tests/ops/test_durable_completion_validation_graph_v1.py"
)

DURABLE_COMPLETION_WALLCLOCK_BINDING_REBINDING_TEST_PATHS = frozenset(
    {
        DURABLE_COMPLETION_FACADE_PATH,
        DURABLE_COMPLETION_COMPLETION_INTEGRATION_TEST_OWNER,
    }
)

MASTER_V2_BINDING_CONTRACT_TEST_OWNER = (
    "tests/ops/test_master_v2_decision_digest_completion_chain_binding_contract_v0.py"
)
MASTER_V2_BINDING_CONTRACT_COMPLETION_CHAIN_VALIDATOR = (
    "src/ops/durable_completion_validation/validators/completion_chain.py"
)
MASTER_V2_BINDING_CONTRACT_GRAPH_TEST_OWNER = (
    "tests/ops/test_durable_completion_validation_graph_v1.py"
)

MASTER_V2_BINDING_CONTRACT_SCOPED_PATHS = frozenset(
    {
        DURABLE_COMPLETION_FACADE_PATH,
        MASTER_V2_BINDING_CONTRACT_COMPLETION_CHAIN_VALIDATOR,
        MASTER_V2_BINDING_CONTRACT_GRAPH_TEST_OWNER,
        MASTER_V2_BINDING_CONTRACT_TEST_OWNER,
    }
)

OFFLINE_MASTER_V2_DOUBLE_PLAY_SCENARIO_REPLAY_OWNER_PATH = (
    "src/trading/master_v2/offline_double_play_scenario_replay_v0.py"
)
OFFLINE_MASTER_V2_DOUBLE_PLAY_SCENARIO_REPLAY_TRADING_TEST_OWNER = "tests/trading/master_v2/test_offline_master_v2_double_play_scenario_replay_binding_contract_v0.py"
OFFLINE_MASTER_V2_DOUBLE_PLAY_SCENARIO_REPLAY_OPS_TEST_OWNER = (
    "tests/ops/test_offline_master_v2_double_play_scenario_replay_completion_binding_contract_v0.py"
)
OFFLINE_MASTER_V2_DOUBLE_PLAY_SCENARIO_REPLAY_CI_POLICY_PATHS = frozenset(
    {
        "scripts/ops/ci_test_selection_v1.py",
        "config/ci/file_category_mapping.yaml",
        "tests/ci/test_ci_diff_aware_test_selection_v1.py",
    }
)
OFFLINE_MASTER_V2_DOUBLE_PLAY_SCENARIO_REPLAY_SCOPED_PATHS = frozenset(
    {
        OFFLINE_MASTER_V2_DOUBLE_PLAY_SCENARIO_REPLAY_OWNER_PATH,
        OFFLINE_MASTER_V2_DOUBLE_PLAY_SCENARIO_REPLAY_TRADING_TEST_OWNER,
        OFFLINE_MASTER_V2_DOUBLE_PLAY_SCENARIO_REPLAY_OPS_TEST_OWNER,
        *OFFLINE_MASTER_V2_DOUBLE_PLAY_SCENARIO_REPLAY_CI_POLICY_PATHS,
    }
)
OFFLINE_MASTER_V2_DOUBLE_PLAY_SCENARIO_REPLAY_CATEGORIZE_PATHS = frozenset(
    {
        OFFLINE_MASTER_V2_DOUBLE_PLAY_SCENARIO_REPLAY_OWNER_PATH,
        OFFLINE_MASTER_V2_DOUBLE_PLAY_SCENARIO_REPLAY_TRADING_TEST_OWNER,
        OFFLINE_MASTER_V2_DOUBLE_PLAY_SCENARIO_REPLAY_OPS_TEST_OWNER,
        "scripts/ops/ci_test_selection_v1.py",
    }
)
CANONICAL_OFFLINE_MASTER_V2_DOUBLE_PLAY_SCENARIO_REPLAY_FOCUSED_TESTS: tuple[str, ...] = (
    OFFLINE_MASTER_V2_DOUBLE_PLAY_SCENARIO_REPLAY_TRADING_TEST_OWNER,
    OFFLINE_MASTER_V2_DOUBLE_PLAY_SCENARIO_REPLAY_OPS_TEST_OWNER,
    "tests/ci/test_ci_diff_aware_test_selection_v1.py",
)

MASTER_V2_REPLAY_DISPLAY_PROJECTION_DIGEST_COMPLETION_EVIDENCE_SCOPED_PATHS = frozenset(
    {
        DURABLE_COMPLETION_FACADE_PATH,
        OFFLINE_MASTER_V2_DOUBLE_PLAY_SCENARIO_REPLAY_OWNER_PATH,
        MASTER_V2_BINDING_CONTRACT_TEST_OWNER,
        OFFLINE_MASTER_V2_DOUBLE_PLAY_SCENARIO_REPLAY_TRADING_TEST_OWNER,
        OFFLINE_MASTER_V2_DOUBLE_PLAY_SCENARIO_REPLAY_OPS_TEST_OWNER,
        *OFFLINE_MASTER_V2_DOUBLE_PLAY_SCENARIO_REPLAY_CI_POLICY_PATHS,
    }
)
CANONICAL_MASTER_V2_REPLAY_DISPLAY_PROJECTION_DIGEST_COMPLETION_EVIDENCE_FOCUSED_TARGETS: tuple[
    str, ...
] = (
    OFFLINE_MASTER_V2_DOUBLE_PLAY_SCENARIO_REPLAY_TRADING_TEST_OWNER,
    OFFLINE_MASTER_V2_DOUBLE_PLAY_SCENARIO_REPLAY_OPS_TEST_OWNER,
    MASTER_V2_BINDING_CONTRACT_TEST_OWNER,
)
MASTER_V2_REPLAY_DISPLAY_PROJECTION_DIGEST_COMPLETION_EVIDENCE_CI_SELECTOR_TARGETS: tuple[
    str, ...
] = (
    "tests/ci/test_ci_diff_aware_test_selection_v1.py::test_selector_master_v2_replay_display_projection_digest_completion_evidence_five_file_diff_focused",
    "tests/ci/test_ci_diff_aware_test_selection_v1.py::test_selector_master_v2_replay_display_projection_digest_completion_evidence_with_ci_policy_focused",
    "tests/ci/test_ci_diff_aware_test_selection_v1.py::test_selector_master_v2_replay_display_projection_digest_completion_evidence_foreign_path_escalates_full",
)

OFFLINE_MASTER_V2_REPLAY_SIX_NODE_VALIDATION_GRAPH_BINDING_OWNER_PATH = (
    "src/ops/offline_master_v2_replay_six_node_validation_graph_binding_v0.py"
)
OFFLINE_MASTER_V2_REPLAY_SIX_NODE_VALIDATION_GRAPH_BINDING_SCOPED_PATHS = frozenset(
    {
        OFFLINE_MASTER_V2_REPLAY_SIX_NODE_VALIDATION_GRAPH_BINDING_OWNER_PATH,
        OFFLINE_MASTER_V2_DOUBLE_PLAY_SCENARIO_REPLAY_OWNER_PATH,
        OFFLINE_MASTER_V2_DOUBLE_PLAY_SCENARIO_REPLAY_TRADING_TEST_OWNER,
        OFFLINE_MASTER_V2_DOUBLE_PLAY_SCENARIO_REPLAY_OPS_TEST_OWNER,
        *OFFLINE_MASTER_V2_DOUBLE_PLAY_SCENARIO_REPLAY_CI_POLICY_PATHS,
    }
)
CANONICAL_OFFLINE_MASTER_V2_REPLAY_SIX_NODE_VALIDATION_GRAPH_BINDING_FOCUSED_TESTS: tuple[
    str, ...
] = (
    OFFLINE_MASTER_V2_DOUBLE_PLAY_SCENARIO_REPLAY_TRADING_TEST_OWNER,
    OFFLINE_MASTER_V2_DOUBLE_PLAY_SCENARIO_REPLAY_OPS_TEST_OWNER,
    "tests/ci/test_ci_diff_aware_test_selection_v1.py",
)

BOUNDED_MASTER_V2_TESTNET_COMPLETION_PATH_WIRING_OWNER_PATH = (
    "src/ops/bounded_master_v2_testnet_completion_path_wiring_v0.py"
)
BOUNDED_MASTER_V2_TESTNET_COMPLETION_PATH_WIRING_TEST_OWNER = (
    "tests/ops/test_bounded_master_v2_testnet_completion_path_wiring_contract_v0.py"
)
BOUNDED_MASTER_V2_TESTNET_COMPLETION_PATH_WIRING_ADAPTER_OWNER = (
    "scripts/ops/run_testnet_bounded_observation_adapter_v0.py"
)
BOUNDED_MASTER_V2_TESTNET_COMPLETION_PATH_WIRING_ADAPTER_TEST_OWNER = (
    "tests/ops/test_run_testnet_bounded_observation_adapter_v0.py"
)
BOUNDED_TESTNET_MARKET_INPUT_ADMISSION_WIRING_OWNER_PATH = (
    "src/ops/bounded_testnet_market_input_admission_wiring_v0.py"
)
BOUNDED_TESTNET_MARKET_INPUT_ADMISSION_WIRING_TEST_OWNER = (
    "tests/ops/test_bounded_testnet_market_input_admission_wiring_contract_v0.py"
)
BOUNDED_TESTNET_MARKET_INPUT_ADMISSION_WIRING_SCOPED_PATHS = frozenset(
    {
        BOUNDED_TESTNET_MARKET_INPUT_ADMISSION_WIRING_OWNER_PATH,
        BOUNDED_TESTNET_MARKET_INPUT_ADMISSION_WIRING_TEST_OWNER,
        BOUNDED_MASTER_V2_TESTNET_COMPLETION_PATH_WIRING_OWNER_PATH,
        BOUNDED_MASTER_V2_TESTNET_COMPLETION_PATH_WIRING_ADAPTER_OWNER,
        "scripts/ops/ci_test_selection_v1.py",
    }
)
BOUNDED_TESTNET_MARKET_INPUT_ADMISSION_WIRING_FOCUSED_TARGETS: tuple[str, ...] = (
    BOUNDED_TESTNET_MARKET_INPUT_ADMISSION_WIRING_TEST_OWNER,
    f"{BOUNDED_MASTER_V2_TESTNET_COMPLETION_PATH_WIRING_ADAPTER_TEST_OWNER}::test_plan_only_default_does_not_call_subprocess",
    f"{BOUNDED_MASTER_V2_TESTNET_COMPLETION_PATH_WIRING_ADAPTER_TEST_OWNER}::test_adapter_plan_no_live_authorization_escalation",
    f"{BOUNDED_TESTNET_MARKET_INPUT_ADMISSION_WIRING_TEST_OWNER}::test_producer_maps_valid_observation_to_market_input",
    f"{BOUNDED_TESTNET_MARKET_INPUT_ADMISSION_WIRING_TEST_OWNER}::test_adapter_forwards_validated_market_input_without_fixture_fallback",
    f"{BOUNDED_TESTNET_MARKET_INPUT_ADMISSION_WIRING_TEST_OWNER}::test_adapter_without_observation_still_fail_closed",
    f"{BOUNDED_TESTNET_MARKET_INPUT_ADMISSION_WIRING_TEST_OWNER}::test_missing_observation_stays_fail_closed",
    f"{BOUNDED_TESTNET_MARKET_INPUT_ADMISSION_WIRING_TEST_OWNER}::test_btc_instrument_rejected",
    f"{BOUNDED_TESTNET_MARKET_INPUT_ADMISSION_WIRING_TEST_OWNER}::test_stale_observation_fail_closed",
    f"{BOUNDED_TESTNET_MARKET_INPUT_ADMISSION_WIRING_TEST_OWNER}::test_ci_selector_market_input_admission_five_file_diff_focused",
)
BOUNDED_TESTNET_EXECUTE_PATH_MARKET_OBSERVATION_CLOSEOUT_BINDING_SCOPED_PATHS = frozenset(
    {
        BOUNDED_MASTER_V2_TESTNET_COMPLETION_PATH_WIRING_ADAPTER_OWNER,
        BOUNDED_MASTER_V2_TESTNET_COMPLETION_PATH_WIRING_ADAPTER_TEST_OWNER,
        BOUNDED_TESTNET_MARKET_INPUT_ADMISSION_WIRING_OWNER_PATH,
        BOUNDED_TESTNET_MARKET_INPUT_ADMISSION_WIRING_TEST_OWNER,
        BOUNDED_MASTER_V2_TESTNET_COMPLETION_PATH_WIRING_OWNER_PATH,
        "scripts/ops/ci_test_selection_v1.py",
    }
)
BOUNDED_TESTNET_EXECUTE_PATH_MARKET_OBSERVATION_CLOSEOUT_BINDING_FOCUSED_TARGETS: tuple[
    str, ...
] = (
    f"{BOUNDED_MASTER_V2_TESTNET_COMPLETION_PATH_WIRING_ADAPTER_TEST_OWNER}::test_closeout_without_market_observation_fail_closed",
    f"{BOUNDED_MASTER_V2_TESTNET_COMPLETION_PATH_WIRING_ADAPTER_TEST_OWNER}::test_closeout_forwards_validated_market_observation",
    f"{BOUNDED_MASTER_V2_TESTNET_COMPLETION_PATH_WIRING_ADAPTER_TEST_OWNER}::test_closeout_stale_market_observation_fail_closed",
    f"{BOUNDED_MASTER_V2_TESTNET_COMPLETION_PATH_WIRING_ADAPTER_TEST_OWNER}::test_staging_execute_without_market_observation_remains_non_authorizing",
    f"{BOUNDED_TESTNET_MARKET_INPUT_ADMISSION_WIRING_TEST_OWNER}::test_producer_maps_valid_observation_to_market_input",
    f"{BOUNDED_TESTNET_MARKET_INPUT_ADMISSION_WIRING_TEST_OWNER}::test_missing_observation_stays_fail_closed",
    f"{BOUNDED_TESTNET_MARKET_INPUT_ADMISSION_WIRING_TEST_OWNER}::test_stale_observation_fail_closed",
    f"{BOUNDED_TESTNET_MARKET_INPUT_ADMISSION_WIRING_TEST_OWNER}::test_adapter_forwards_validated_market_input_without_fixture_fallback",
    f"{BOUNDED_MASTER_V2_TESTNET_COMPLETION_PATH_WIRING_TEST_OWNER}::test_static_wiring_flags_present_without_market_input",
    f"{BOUNDED_MASTER_V2_TESTNET_COMPLETION_PATH_WIRING_ADAPTER_TEST_OWNER}::test_ci_selector_closeout_binding_five_file_diff_focused",
)
BOUNDED_TESTNET_RUNTIME_MARKET_OBSERVATION_PRODUCER_OWNER_PATH = (
    "src/ops/bounded_testnet_runtime_market_observation_producer_v0.py"
)
BOUNDED_TESTNET_RUNTIME_MARKET_OBSERVATION_PRODUCER_TEST_OWNER = (
    "tests/ops/test_bounded_testnet_runtime_market_observation_producer_v0.py"
)
BOUNDED_TESTNET_RUNTIME_MARKET_OBSERVATION_PRODUCER_SCOPED_PATHS = frozenset(
    {
        BOUNDED_TESTNET_RUNTIME_MARKET_OBSERVATION_PRODUCER_OWNER_PATH,
        BOUNDED_TESTNET_RUNTIME_MARKET_OBSERVATION_PRODUCER_TEST_OWNER,
        BOUNDED_MASTER_V2_TESTNET_COMPLETION_PATH_WIRING_ADAPTER_OWNER,
        BOUNDED_MASTER_V2_TESTNET_COMPLETION_PATH_WIRING_ADAPTER_TEST_OWNER,
        "scripts/ops/ci_test_selection_v1.py",
    }
)
BOUNDED_TESTNET_RUNTIME_MARKET_OBSERVATION_PRODUCER_FOCUSED_TARGETS: tuple[str, ...] = (
    BOUNDED_TESTNET_RUNTIME_MARKET_OBSERVATION_PRODUCER_TEST_OWNER,
    f"{BOUNDED_TESTNET_RUNTIME_MARKET_OBSERVATION_PRODUCER_TEST_OWNER}::test_valid_pf_ethusd_response_produces_canonical_observation",
    f"{BOUNDED_TESTNET_RUNTIME_MARKET_OBSERVATION_PRODUCER_TEST_OWNER}::test_http_503_fails_closed_without_retry",
    f"{BOUNDED_TESTNET_RUNTIME_MARKET_OBSERVATION_PRODUCER_TEST_OWNER}::test_live_host_rejected",
    f"{BOUNDED_TESTNET_RUNTIME_MARKET_OBSERVATION_PRODUCER_TEST_OWNER}::test_stale_timestamp_rejected",
    f"{BOUNDED_MASTER_V2_TESTNET_COMPLETION_PATH_WIRING_ADAPTER_TEST_OWNER}::test_plan_only_collect_public_testnet_market_observation_rejected",
    f"{BOUNDED_MASTER_V2_TESTNET_COMPLETION_PATH_WIRING_ADAPTER_TEST_OWNER}::test_execute_collect_public_testnet_market_observation_forwards_closeout",
    f"{BOUNDED_MASTER_V2_TESTNET_COMPLETION_PATH_WIRING_ADAPTER_TEST_OWNER}::test_execute_collect_http_503_fail_closed",
    f"{BOUNDED_MASTER_V2_TESTNET_COMPLETION_PATH_WIRING_ADAPTER_TEST_OWNER}::test_ci_selector_runtime_market_observation_producer_five_file_diff_focused",
)
BOUNDED_MASTER_V2_TESTNET_COMPLETION_PATH_WIRING_CI_POLICY_PATHS = frozenset(
    {
        "scripts/ops/ci_test_selection_v1.py",
        "config/ci/file_category_mapping.yaml",
        "tests/ci/test_ci_diff_aware_test_selection_v1.py",
    }
)
BOUNDED_MASTER_V2_TESTNET_COMPLETION_PATH_WIRING_SCOPED_PATHS = frozenset(
    {
        BOUNDED_MASTER_V2_TESTNET_COMPLETION_PATH_WIRING_OWNER_PATH,
        BOUNDED_MASTER_V2_TESTNET_COMPLETION_PATH_WIRING_TEST_OWNER,
        BOUNDED_MASTER_V2_TESTNET_COMPLETION_PATH_WIRING_ADAPTER_OWNER,
        OFFLINE_MASTER_V2_REPLAY_SIX_NODE_VALIDATION_GRAPH_BINDING_OWNER_PATH,
        OFFLINE_MASTER_V2_DOUBLE_PLAY_SCENARIO_REPLAY_OPS_TEST_OWNER,
        DURABLE_COMPLETION_COMPLETION_INTEGRATION_TEST_OWNER,
        *BOUNDED_MASTER_V2_TESTNET_COMPLETION_PATH_WIRING_CI_POLICY_PATHS,
    }
)
BOUNDED_MASTER_V2_TESTNET_COMPLETION_PATH_WIRING_CI_SELECTOR_TARGETS: tuple[str, ...] = (
    "tests/ci/test_ci_diff_aware_test_selection_v1.py::test_selector_bounded_master_v2_testnet_completion_path_wiring_five_file_diff_focused",
    "tests/ci/test_ci_diff_aware_test_selection_v1.py::test_selector_bounded_master_v2_testnet_wiring_foreign_path_escalates_full",
)
BOUNDED_MASTER_V2_TESTNET_COMPLETION_PATH_WIRING_FOCUSED_TARGETS: tuple[str, ...] = (
    BOUNDED_MASTER_V2_TESTNET_COMPLETION_PATH_WIRING_TEST_OWNER,
    f"{BOUNDED_MASTER_V2_TESTNET_COMPLETION_PATH_WIRING_ADAPTER_TEST_OWNER}::test_plan_only_default_does_not_call_subprocess",
    f"{BOUNDED_MASTER_V2_TESTNET_COMPLETION_PATH_WIRING_ADAPTER_TEST_OWNER}::test_plan_archive_dest_is_runs_testnet",
    f"{BOUNDED_MASTER_V2_TESTNET_COMPLETION_PATH_WIRING_ADAPTER_TEST_OWNER}::test_command_plan_never_uses_forbidden_paths",
    f"{BOUNDED_MASTER_V2_TESTNET_COMPLETION_PATH_WIRING_ADAPTER_TEST_OWNER}::test_adapter_plan_no_live_authorization_escalation",
    f"{BOUNDED_MASTER_V2_TESTNET_COMPLETION_PATH_WIRING_ADAPTER_TEST_OWNER}::test_plan_lists_wallclock_evidence_artifact",
    f"{BOUNDED_MASTER_V2_TESTNET_COMPLETION_PATH_WIRING_ADAPTER_TEST_OWNER}::test_plan_forwards_step_interval_seconds_to_staging_cmd",
    f"{BOUNDED_MASTER_V2_TESTNET_COMPLETION_PATH_WIRING_ADAPTER_TEST_OWNER}::test_plan_forwards_duration_minutes_and_max_steps_unchanged",
    f"{OFFLINE_MASTER_V2_DOUBLE_PLAY_SCENARIO_REPLAY_OPS_TEST_OWNER}::test_replay_output_accepted_by_completion_binding",
    f"{OFFLINE_MASTER_V2_DOUBLE_PLAY_SCENARIO_REPLAY_OPS_TEST_OWNER}::test_partial_replay_binding_fail_closed",
    f"{OFFLINE_MASTER_V2_DOUBLE_PLAY_SCENARIO_REPLAY_OPS_TEST_OWNER}::test_decision_id_drift_fail_closed",
    f"{OFFLINE_MASTER_V2_DOUBLE_PLAY_SCENARIO_REPLAY_OPS_TEST_OWNER}::test_digest_drift_fail_closed",
    f"{OFFLINE_MASTER_V2_DOUBLE_PLAY_SCENARIO_REPLAY_OPS_TEST_OWNER}::test_selected_future_drift_fail_closed",
    f"{OFFLINE_MASTER_V2_DOUBLE_PLAY_SCENARIO_REPLAY_OPS_TEST_OWNER}::test_six_node_validation_graph_unchanged",
    f"{OFFLINE_MASTER_V2_DOUBLE_PLAY_SCENARIO_REPLAY_OPS_TEST_OWNER}::test_no_paper_shadow_testnet_live_proof_claim",
    f"{OFFLINE_MASTER_V2_DOUBLE_PLAY_SCENARIO_REPLAY_OPS_TEST_OWNER}::test_replay_sourced_six_node_validation_graph_passes",
    f"{OFFLINE_MASTER_V2_DOUBLE_PLAY_SCENARIO_REPLAY_OPS_TEST_OWNER}::test_replay_graph_binding_fail_closed_on_digest_drift",
    f"{OFFLINE_MASTER_V2_DOUBLE_PLAY_SCENARIO_REPLAY_OPS_TEST_OWNER}::test_replay_graph_binding_zero_order_boundary",
    f"{DURABLE_COMPLETION_COMPLETION_INTEGRATION_TEST_OWNER}::test_package_marker_present",
    f"{DURABLE_COMPLETION_COMPLETION_INTEGRATION_TEST_OWNER}::test_canonical_owners_referenced_not_duplicated",
    f"{DURABLE_COMPLETION_COMPLETION_INTEGRATION_TEST_OWNER}::test_valid_static_proof_remains_non_authorizing",
)
MASTER_V2_BINDING_CONTRACT_FOCUSED_TARGETS: tuple[str, ...] = (
    f"{MASTER_V2_BINDING_CONTRACT_TEST_OWNER}::test_legacy_ops_only_reports_master_v2_binding_not_present",
    f"{MASTER_V2_BINDING_CONTRACT_TEST_OWNER}::test_complete_master_v2_binding_accepted",
    f"{MASTER_V2_BINDING_CONTRACT_TEST_OWNER}::test_master_v2_fields_bound_through_integration_and_validator",
    f"{MASTER_V2_BINDING_CONTRACT_TEST_OWNER}::test_missing_single_field_when_binding_present_fail_closed",
    f"{MASTER_V2_BINDING_CONTRACT_TEST_OWNER}::test_invalid_digest_format_fail_closed",
    f"{MASTER_V2_BINDING_CONTRACT_TEST_OWNER}::test_digest_drift_fail_closed",
    f"{MASTER_V2_BINDING_CONTRACT_TEST_OWNER}::test_decision_id_drift_fail_closed",
    f"{MASTER_V2_BINDING_CONTRACT_TEST_OWNER}::test_selected_future_drift_fail_closed",
    f"{MASTER_V2_BINDING_CONTRACT_TEST_OWNER}::test_owner_drift_fail_closed",
    f"{MASTER_V2_BINDING_CONTRACT_TEST_OWNER}::test_partial_chain_reference_fail_closed",
    f"{MASTER_V2_BINDING_CONTRACT_TEST_OWNER}::test_binding_presence_does_not_imply_trading_logic_executed",
    f"{MASTER_V2_BINDING_CONTRACT_TEST_OWNER}::test_six_node_validation_graph_unchanged",
    f"{MASTER_V2_BINDING_CONTRACT_GRAPH_TEST_OWNER}::test_graph_is_cycle_free",
    f"{MASTER_V2_BINDING_CONTRACT_GRAPH_TEST_OWNER}::test_graph_explicit_order_matches_dependencies",
    f"{MASTER_V2_BINDING_CONTRACT_GRAPH_TEST_OWNER}::test_graph_has_single_wallclock_validator_node",
    f"{MASTER_V2_BINDING_CONTRACT_GRAPH_TEST_OWNER}::test_graph_completion_chain_validator_composes_binding",
    f"{MASTER_V2_BINDING_CONTRACT_GRAPH_TEST_OWNER}::test_legacy_ops_only_completion_chain_master_v2_binding_not_present",
)

_PYTEST_NODE_ID = re.compile(r"^[A-Za-z0-9_\-]+(?:\[[^\]]+\])?$")

DURABLE_COMPLETION_WALLCLOCK_BINDING_FOCUSED_TARGETS: tuple[str, ...] = (
    f"{DURABLE_COMPLETION_COMPLETION_INTEGRATION_TEST_OWNER}::test_package_marker_present",
    f"{DURABLE_COMPLETION_COMPLETION_INTEGRATION_TEST_OWNER}::test_canonical_owners_referenced_not_duplicated",
    f"{DURABLE_COMPLETION_COMPLETION_INTEGRATION_TEST_OWNER}::test_coherent_static_completion_happy_path_passes",
    f"{DURABLE_COMPLETION_COMPLETION_INTEGRATION_TEST_OWNER}::test_valid_static_proof_remains_non_authorizing",
    f"{DURABLE_COMPLETION_COMPLETION_INTEGRATION_TEST_OWNER}::test_missing_wallclock_evidence_fails_closed",
    f"{DURABLE_COMPLETION_COMPLETION_INTEGRATION_TEST_OWNER}::test_wrong_wallclock_relative_path_fails_closed",
    f"{DURABLE_COMPLETION_COMPLETION_INTEGRATION_TEST_OWNER}::test_completion_wallclock_semantic_binding_uses_canonical_evaluators",
    f"{DURABLE_COMPLETION_COMPLETION_INTEGRATION_TEST_OWNER}::test_invalid_wallclock_evidence_semantics_fails_closed",
    f"{DURABLE_COMPLETION_COMPLETION_INTEGRATION_TEST_OWNER}::test_missing_wallclock_required_fields_fails_closed",
    f"{DURABLE_COMPLETION_COMPLETION_INTEGRATION_TEST_OWNER}::test_wallclock_duration_proof_flags_drift_fails_closed",
    f"{DURABLE_COMPLETION_COMPLETION_INTEGRATION_TEST_OWNER}::test_required_wallclock_field_names_complete_in_binding",
    f"{DURABLE_COMPLETION_VALIDATION_GRAPH_TEST_OWNER}::test_graph_testnet_completion_includes_wallclock_required_path_binding",
    f"{DURABLE_COMPLETION_VALIDATION_GRAPH_TEST_OWNER}::test_graph_retention_review_completion_share_canonical_testnet_paths",
    f"{DURABLE_COMPLETION_VALIDATION_GRAPH_TEST_OWNER}::test_graph_seven_vs_eight_path_drift_fail_closed",
)

PE26_ASSEMBLY_OWNER = "src/ops/bounded_futures_testnet_preflight_execution_readiness_assembly_lifecycle_integration_contract_v0.py"

PREFLIGHT_ASSEMBLY_CI_POLICY_PATHS = frozenset(
    {
        "scripts/ops/ci_test_selection_v1.py",
        "config/ci/file_category_mapping.yaml",
        "tests/ci/test_ci_diff_aware_test_selection_v1.py",
    }
)

CANONICAL_PREFLIGHT_ASSEMBLY_FOCUSED_TESTS: tuple[str, ...] = (
    "tests/ops/test_bounded_futures_testnet_preflight_execution_readiness_assembly_lifecycle_integration_contract_v0.py",
    "tests/ops/test_bounded_futures_testnet_reconciliation_review_lifecycle_integration_contract_v0.py",
    "tests/ci/test_ci_diff_aware_test_selection_v1.py",
)

REQUIRED_PREFLIGHT_ASSEMBLY_TEST_OWNERS: tuple[str, ...] = (
    "tests/ops/test_bounded_futures_testnet_preflight_execution_readiness_assembly_lifecycle_integration_contract_v0.py",
    "tests/ops/test_bounded_futures_testnet_reconciliation_review_lifecycle_integration_contract_v0.py",
)

PE22_RISK_KILLSWITCH_OWNER = (
    "src/ops/bounded_futures_testnet_risk_killswitch_lifecycle_integration_contract_v0.py"
)
PE22_RISK_KILLSWITCH_TEST_OWNER = (
    "tests/ops/test_bounded_futures_testnet_risk_killswitch_lifecycle_integration_contract_v0.py"
)

RISK_KILLSWITCH_CI_POLICY_PATHS = frozenset(
    {
        "scripts/ops/ci_test_selection_v1.py",
        "config/ci/file_category_mapping.yaml",
        "tests/ci/test_ci_diff_aware_test_selection_v1.py",
    }
)

CANONICAL_RISK_KILLSWITCH_FOCUSED_TESTS: tuple[str, ...] = (
    "tests/ops/test_bounded_futures_testnet_risk_killswitch_lifecycle_integration_contract_v0.py",
    "tests/ops/test_order_capability_killswitch_abort_binding_contract_v1.py",
    "tests/ci/test_ci_diff_aware_test_selection_v1.py",
)

REQUIRED_RISK_KILLSWITCH_TEST_OWNERS: tuple[str, ...] = (
    "tests/ops/test_bounded_futures_testnet_risk_killswitch_lifecycle_integration_contract_v0.py",
    "tests/ops/test_order_capability_killswitch_abort_binding_contract_v1.py",
)

PE30_TINY_ORDER_OWNER = (
    "src/ops/bounded_futures_testnet_tiny_order_lifecycle_integration_contract_v0.py"
)
PE30_TINY_ORDER_TEST_OWNER = (
    "tests/ops/test_bounded_futures_testnet_tiny_order_lifecycle_integration_contract_v0.py"
)

TINY_ORDER_CI_POLICY_PATHS = frozenset(
    {
        "scripts/ops/ci_test_selection_v1.py",
        "config/ci/file_category_mapping.yaml",
        "tests/ci/test_ci_diff_aware_test_selection_v1.py",
    }
)

CANONICAL_TINY_ORDER_FOCUSED_TESTS: tuple[str, ...] = (
    "tests/ops/test_bounded_futures_testnet_tiny_order_lifecycle_integration_contract_v0.py",
    "tests/ops/test_order_capability_killswitch_abort_binding_contract_v1.py",
    "tests/ops/test_order_capability_cancel_cleanup_failclosed_contract_v1.py",
    "tests/ci/test_ci_diff_aware_test_selection_v1.py",
)

REQUIRED_TINY_ORDER_TEST_OWNERS: tuple[str, ...] = (
    "tests/ops/test_bounded_futures_testnet_tiny_order_lifecycle_integration_contract_v0.py",
    "tests/ops/test_order_capability_killswitch_abort_binding_contract_v1.py",
    "tests/ops/test_order_capability_cancel_cleanup_failclosed_contract_v1.py",
)

PE21_RECONCILIATION_PRIMARY_EVIDENCE_OWNER = "src/ops/bounded_futures_testnet_position_order_reconciliation_primary_evidence_integration_contract_v0.py"
PE21_RECONCILIATION_PRIMARY_EVIDENCE_TEST_OWNER = "tests/ops/test_bounded_futures_testnet_position_order_reconciliation_primary_evidence_integration_contract_v0.py"

RECONCILIATION_PRIMARY_EVIDENCE_CI_POLICY_PATHS = frozenset(
    {
        "scripts/ops/ci_test_selection_v1.py",
        "config/ci/file_category_mapping.yaml",
        "tests/ci/test_ci_diff_aware_test_selection_v1.py",
    }
)

CANONICAL_RECONCILIATION_PRIMARY_EVIDENCE_FOCUSED_TESTS: tuple[str, ...] = (
    "tests/ops/test_bounded_futures_testnet_position_order_reconciliation_primary_evidence_integration_contract_v0.py",
    "tests/ci/test_ci_diff_aware_test_selection_v1.py",
)

REQUIRED_RECONCILIATION_PRIMARY_EVIDENCE_TEST_OWNERS: tuple[str, ...] = (
    "tests/ops/test_bounded_futures_testnet_position_order_reconciliation_primary_evidence_integration_contract_v0.py",
)

BOUNDED_NETWORK_TESTNET_PREFLIGHT_OWNER = "src/ops/bounded_network_testnet_preflight_contract_v0.py"
BOUNDED_NETWORK_TESTNET_PREFLIGHT_TEST_OWNER = (
    "tests/ops/test_bounded_network_testnet_preflight_contract_v0.py"
)

BOUNDED_NETWORK_TESTNET_PREFLIGHT_CI_POLICY_PATHS = frozenset(
    {
        "scripts/ops/ci_test_selection_v1.py",
        "config/ci/file_category_mapping.yaml",
        "tests/ci/test_ci_diff_aware_test_selection_v1.py",
    }
)

CANONICAL_BOUNDED_NETWORK_TESTNET_PREFLIGHT_FOCUSED_TESTS: tuple[str, ...] = (
    "tests/ops/test_bounded_network_testnet_preflight_contract_v0.py",
)

REQUIRED_BOUNDED_NETWORK_TESTNET_PREFLIGHT_TEST_OWNERS: tuple[str, ...] = (
    "tests/ops/test_bounded_network_testnet_preflight_contract_v0.py",
)

RUNTIME_WALLCLOCK_EVIDENCE_EMITTER_OWNER = (
    "src/ops/runtime_wallclock_evidence_emitter_contract_v0.py"
)
RUNTIME_WALLCLOCK_EVIDENCE_EMITTER_TEST_OWNER = (
    "tests/ops/test_runtime_wallclock_evidence_emitter_contract_v0.py"
)

RUNTIME_WALLCLOCK_EVIDENCE_EMITTER_CI_POLICY_PATHS = frozenset(
    {
        "scripts/ops/ci_test_selection_v1.py",
        "tests/ci/test_ci_diff_aware_test_selection_v1.py",
    }
)

CANONICAL_RUNTIME_WALLCLOCK_EVIDENCE_EMITTER_FOCUSED_TESTS: tuple[str, ...] = (
    "tests/ops/test_runtime_wallclock_evidence_emitter_contract_v0.py",
    "tests/ops/test_testnet_wallclock_duration_evidence_contract_v0.py",
)

REQUIRED_RUNTIME_WALLCLOCK_EVIDENCE_EMITTER_TEST_OWNERS: tuple[str, ...] = (
    "tests/ops/test_runtime_wallclock_evidence_emitter_contract_v0.py",
)

TESTNET_WALLCLOCK_DURATION_EVIDENCE_OWNER = (
    "src/ops/testnet_wallclock_duration_evidence_contract_v0.py"
)
TESTNET_WALLCLOCK_DURATION_EVIDENCE_TEST_OWNER = (
    "tests/ops/test_testnet_wallclock_duration_evidence_contract_v0.py"
)

TESTNET_WALLCLOCK_DURATION_EVIDENCE_CI_POLICY_PATHS = frozenset(
    {
        "scripts/ops/ci_test_selection_v1.py",
        "tests/ci/test_ci_diff_aware_test_selection_v1.py",
    }
)

CANONICAL_TESTNET_WALLCLOCK_DURATION_EVIDENCE_FOCUSED_TESTS: tuple[str, ...] = (
    "tests/ops/test_testnet_wallclock_duration_evidence_contract_v0.py",
)

REQUIRED_TESTNET_WALLCLOCK_DURATION_EVIDENCE_TEST_OWNERS: tuple[str, ...] = (
    "tests/ops/test_testnet_wallclock_duration_evidence_contract_v0.py",
)

WALLCLOCK_FIELD_NAME_PAIRED_REWIRE_TEST_OWNERS: frozenset[str] = frozenset(
    {
        TESTNET_WALLCLOCK_DURATION_EVIDENCE_TEST_OWNER,
        "tests/ops/test_shadow_wallclock_duration_evidence_contract_v0.py",
    }
)

WALLCLOCK_OWNER = "src/ops/wallclock_session_evidence_v0.py"

WALLCLOCK_CI_POLICY_PATHS = frozenset(
    {
        "scripts/ops/ci_test_selection_v1.py",
        "config/ci/file_category_mapping.yaml",
        "tests/ci/test_ci_diff_aware_test_selection_v1.py",
    }
)

WALLCLOCK_SCRIPT_PATHS = frozenset(
    {
        "scripts/ops/shadow_247_futures_start_wrapper_skeleton_v0.py",
        "scripts/ops/run_shadow_bounded_observation_adapter_v0.py",
    }
)

CANONICAL_WALLCLOCK_FOCUSED_TESTS: tuple[str, ...] = (
    "tests/ops/test_run_shadow_bounded_observation_adapter_v0.py",
    "tests/ops/test_shadow_wallclock_duration_evidence_contract_v0.py",
    "tests/ops/test_shadow_247_futures_start_wrapper_skeleton_v0.py",
    "tests/ci/test_ci_diff_aware_test_selection_v1.py",
)

REQUIRED_WALLCLOCK_TEST_OWNERS: tuple[str, ...] = (
    "tests/ops/test_run_shadow_bounded_observation_adapter_v0.py",
    "tests/ops/test_shadow_wallclock_duration_evidence_contract_v0.py",
    "tests/ops/test_shadow_247_futures_start_wrapper_skeleton_v0.py",
)

CI_INFRA_WORKFLOW_ALLOWLIST = frozenset(
    {
        ".github/workflows/ci.yml",
        ".github/workflows/ci-export-pack-download-verify.yml",
        ".github/workflows/ci-scheduled-paper-and-export-smoke.yml",
        ".github/workflows/full_audit_weekly.yml",
        ".github/workflows/offline_suites.yml",
        ".github/workflows/paper_session_audit_evidence.yml",
        ".github/workflows/paper_tests_audit_evidence.yml",
        ".github/workflows/prbj-testnet-exec-events.yml",
        ".github/workflows/test-health-automation.yml",
    }
)

CI_INFRA_CONTRACT_TEST_ALLOWLIST = frozenset(
    {
        "tests/ci/test_ci_diff_aware_test_selection_v1.py",
        "tests/ci/test_workflows_no_pull_request_target_contract_v0.py",
        "tests/ci/test_ci_scheduled_paper_export_smoke_workflow_contract_v0.py",
        "tests/ci/test_class_a_shadow_paper_scheduled_probe_workflow_contract_v0.py",
        "tests/ci/test_paper_session_audit_evidence_workflow_contract_v0.py",
        "tests/ci/test_paper_tests_audit_evidence_workflow_contract_v0.py",
        "tests/ci/test_prj_scheduled_shadow_paper_features_smoke_workflow_contract_v0.py",
        "tests/ci/test_shadow_paper_smoke_workflow_contract_v0.py",
    }
)

CI_INFRA_MINIMUM_CONTRACT_ANCHORS = frozenset(
    {
        "tests/ci/test_ci_diff_aware_test_selection_v1.py",
        "tests/ci/test_workflows_no_pull_request_target_contract_v0.py",
    }
)

CI_INFRA_CORE_FOCUSED_TESTS: tuple[str, ...] = (
    "tests/ci/test_ci_diff_aware_test_selection_v1.py",
    "tests/ci/test_workflows_no_pull_request_target_contract_v0.py",
    "tests/ci/test_ci_testowner_runtime_budget_reporting_contract_v0.py",
)

CANONICAL_MARKET_DASHBOARD_FOCUSED_TESTS: tuple[str, ...] = (
    "tests/webui/test_market_dashboard_no_bitcoin_futures_v1.py",
    "tests/webui/test_market_futures_only_canonical_completion_v1.py",
    "tests/webui/test_market_dashboard_readonly_structure_contract_v0.py",
    "tests/webui/test_market_governed_top20_f5_default_wiring_v1.py",
    "tests/webui/test_market_futures_universe_visual_matrix_v1.py",
    "tests/webui/test_market_dashboard_selected_instrument_workspace_v1.py",
    "tests/webui/test_market_dashboard_topn_navigation_visual_density_v1.py",
    "tests/webui/test_market_futures_first_root_cause_eradication_v1.py",
    "tests/webui/test_futures_read_only_market_dashboard_v0.py",
    "tests/webui/test_market_canonical_short_url_title_real_values_ui_v1.py",
    "tests/webui/test_market_ranking_funnel_readmodel_v0.py",
    "tests/test_market_surface_api.py",
    "tests/ci/test_ci_diff_aware_test_selection_v1.py",
)

_REPO_RELATIVE_PATH = re.compile(r"^[A-Za-z0-9_./-]+$")
_IMPORT_MODULE = re.compile(r"^[a-zA-Z0-9_.]+$")


@dataclass(frozen=True)
class SelectionResult:
    mode: str
    reason: str
    focused_pytest_targets: tuple[str, ...]
    focused_module_imports: tuple[str, ...] = ()

    def github_output_lines(self) -> list[str]:
        lines = [
            f"test_selection_mode={self.mode}",
            f"test_selection_reason={self.reason}",
            f"tests_execute_full={'true' if self.mode == 'FULL' else 'false'}",
            f"tests_execute_focused={'true' if self.mode == 'FOCUSED' else 'false'}",
            f"tests_execute_no_op={'true' if self.mode == 'NO_OP' else 'false'}",
        ]
        if self.focused_pytest_targets:
            lines.append(f"focused_pytest_targets={' '.join(self.focused_pytest_targets)}")
        else:
            lines.append("focused_pytest_targets=")
        if self.focused_module_imports:
            lines.append(f"focused_module_imports={' '.join(self.focused_module_imports)}")
        else:
            lines.append("focused_module_imports=")
        return lines


def _is_ci_bootstrap_scoped_path(path: str) -> bool:
    return path in CI_BOOTSTRAP_FOCUSED_PATHS


def _try_ci_bootstrap_focused(files: list[str]) -> SelectionResult | None:
    if not files:
        return None
    if not any(_is_ci_bootstrap_scoped_path(f) for f in files):
        return None
    if not all(f in CI_BOOTSTRAP_FOCUSED_PATHS for f in files):
        return None
    contract_test = "tests/ci/test_ci_diff_aware_test_selection_v1.py"
    if not _repo_path_exists(contract_test):
        return None
    return SelectionResult(
        "FOCUSED",
        "ci_bootstrap_focused",
        (contract_test,),
    )


def _requires_full_ci_selector_change(files: list[str]) -> bool:
    normalized = {PurePosixPath(f).as_posix() for f in files}
    scoped_md = {f for f in normalized if _is_market_dashboard_scoped_path(f)}
    if scoped_md and all(_is_market_dashboard_rebundle_path(f) for f in normalized):
        return False
    scoped_dc = {f for f in normalized if _is_durable_completion_scoped_path(f)}
    if scoped_dc and all(_is_durable_completion_rebundle_path(f) for f in normalized):
        return False
    scoped_pa = {f for f in normalized if _is_preflight_assembly_scoped_path(f)}
    if scoped_pa and all(_is_preflight_assembly_rebundle_path(f) for f in normalized):
        return False
    scoped_rk = {f for f in normalized if _is_risk_killswitch_scoped_path(f)}
    if scoped_rk and all(_is_risk_killswitch_rebundle_path(f) for f in normalized):
        return False
    scoped_to = {f for f in normalized if _is_tiny_order_scoped_path(f)}
    if scoped_to and all(_is_tiny_order_rebundle_path(f) for f in normalized):
        return False
    scoped_rpe = {f for f in normalized if _is_reconciliation_primary_evidence_scoped_path(f)}
    if scoped_rpe and all(_is_reconciliation_primary_evidence_rebundle_path(f) for f in normalized):
        return False
    scoped_bn = {f for f in normalized if _is_bounded_network_testnet_preflight_scoped_path(f)}
    if scoped_bn and all(
        _is_bounded_network_testnet_preflight_rebundle_path(f) for f in normalized
    ):
        return False
    scoped_rwe = {f for f in normalized if _is_runtime_wallclock_evidence_emitter_scoped_path(f)}
    if scoped_rwe and all(
        _is_runtime_wallclock_evidence_emitter_rebundle_path(f) for f in normalized
    ):
        return False
    if any(_is_ci_infra_scoped_path(f) for f in normalized) and all(
        _is_ci_infra_rebundle_path(f) for f in normalized
    ):
        return False
    if normalized <= CI_BOOTSTRAP_FOCUSED_PATHS:
        return False
    if normalized & CI_MAPPING_FULL_PATHS:
        return True
    if ".github/workflows/ci.yml" in normalized and (
        "scripts/ops/ci_test_selection_v1.py" in normalized
        or "config/ci/file_category_mapping.yaml" in normalized
        or any(f.startswith("tests/ci/test_ci_diff_aware_test_selection") for f in normalized)
    ):
        return True
    return False


def _is_market_dashboard_scoped_path(path: str) -> bool:
    if path.startswith("src/webui/market_futures_ohlcv_readmodel_v0/"):
        return True
    if path.startswith("src/webui/market_ranking_funnel_readmodel_v0/"):
        return True
    if path.startswith("templates/peak_trade_dashboard/partials/market_"):
        return True
    if path == "templates/peak_trade_dashboard/market_v0.html":
        return True
    if path.startswith("tests/fixtures/market_"):
        return True
    if path.startswith("tests/fixtures/futures_read_only_market_dashboard"):
        return True
    if path.startswith("tests/webui/test_market_"):
        return True
    if path.startswith("tests/webui/test_futures_read_only_market_dashboard"):
        return True
    if path == "tests/test_market_surface_api.py":
        return True
    market_webui_prefixes = (
        "src/webui/market_",
        "src/webui/futures_read_only_market_dashboard_",
        "src/webui/market_futures_ohlcv_",
        "src/webui/market_ranking_funnel_",
    )
    return any(path.startswith(prefix) and path.endswith(".py") for prefix in market_webui_prefixes)


def _is_market_dashboard_rebundle_path(path: str) -> bool:
    return _is_market_dashboard_scoped_path(path) or path in MARKET_DASHBOARD_CI_POLICY_PATHS


def _market_dashboard_focused_targets() -> tuple[str, ...]:
    targets: list[str] = []
    for path in CANONICAL_MARKET_DASHBOARD_FOCUSED_TESTS:
        if _repo_path_exists(path):
            targets.append(path)
    return tuple(sorted(targets))


def _is_durable_completion_scoped_path(path: str) -> bool:
    if path == DURABLE_COMPLETION_FACADE_PATH:
        return True
    if path.startswith("src/ops/durable_completion_validation/") and path.endswith(".py"):
        return True
    if path in {
        "tests/ops/test_durable_completion_validation_graph_v1.py",
        "tests/ops/test_bounded_futures_testnet_durable_run_primary_evidence_completion_integration_contract_v0.py",
    }:
        return True
    return False


def _is_durable_completion_rebundle_path(path: str) -> bool:
    return (
        _is_durable_completion_scoped_path(path)
        or path in DURABLE_COMPLETION_CI_POLICY_PATHS
        or path in DURABLE_COMPLETION_CI_WORKFLOW_REBUNDLE_PATHS
    )


def _split_pytest_target(target: str) -> tuple[str, str | None]:
    if "::" not in target:
        return target, None
    path, node = target.split("::", 1)
    return path, node or None


def _validate_pytest_target(target: str) -> bool:
    path, node = _split_pytest_target(target)
    if not _validate_repo_relative_path(path):
        return False
    if node is None:
        return True
    node_name = node.split("[", 1)[0]
    return bool(_PYTEST_NODE_ID.match(node_name))


def _repo_pytest_target_exists(target: str) -> bool:
    path, _ = _split_pytest_target(target)
    return _repo_path_exists(path)


def _is_durable_completion_wallclock_binding_rebinding_scope(files: list[str]) -> bool:
    if not files:
        return False
    if not any(path == DURABLE_COMPLETION_FACADE_PATH for path in files):
        return False
    if not any(path == DURABLE_COMPLETION_COMPLETION_INTEGRATION_TEST_OWNER for path in files):
        return False
    if _is_durable_completion_validator_rebinding_scope(files):
        return False
    for path in files:
        if path in DURABLE_COMPLETION_CI_POLICY_PATHS:
            continue
        if path in DURABLE_COMPLETION_CI_WORKFLOW_REBUNDLE_PATHS:
            continue
        if path in DURABLE_COMPLETION_WALLCLOCK_BINDING_REBINDING_TEST_PATHS:
            continue
        return False
    return True


def _durable_completion_wallclock_binding_focused_targets(
    files: list[str] | None = None,
) -> tuple[str, ...]:
    targets: list[str] = []
    for target in DURABLE_COMPLETION_WALLCLOCK_BINDING_FOCUSED_TARGETS:
        if _repo_pytest_target_exists(target):
            targets.append(target)
    if not targets:
        return ()
    if files and any(path in DURABLE_COMPLETION_CI_POLICY_PATHS for path in files):
        ci_owner = "tests/ci/test_ci_diff_aware_test_selection_v1.py"
        if _repo_path_exists(ci_owner):
            targets.append(ci_owner)
    return tuple(sorted(set(targets)))


def _is_durable_completion_validator_rebinding_scope(files: list[str]) -> bool:
    if not files:
        return False
    if any(path in DURABLE_COMPLETION_FULL_REFACTOR_SRC_PATHS for path in files):
        return False
    if not any(
        path.startswith("src/ops/durable_completion_validation/") and path.endswith(".py")
        for path in files
    ):
        return False
    has_validator_subpath = any(
        path.startswith("src/ops/durable_completion_validation/validators/")
        and path.endswith(".py")
        for path in files
    )
    has_rebinding_test = any(
        path in DURABLE_COMPLETION_VALIDATOR_REBINDING_TEST_PATHS for path in files
    )
    if not has_validator_subpath and not has_rebinding_test:
        return False
    for path in files:
        if path in DURABLE_COMPLETION_CI_POLICY_PATHS:
            continue
        if path in DURABLE_COMPLETION_CI_WORKFLOW_REBUNDLE_PATHS:
            continue
        if path.startswith("src/ops/durable_completion_validation/") and path.endswith(".py"):
            continue
        if path in DURABLE_COMPLETION_VALIDATOR_REBINDING_TEST_PATHS:
            continue
        if path == DURABLE_COMPLETION_FACADE_PATH and has_validator_subpath:
            continue
        return False
    return True


def _durable_completion_focused_targets(files: list[str] | None = None) -> tuple[str, ...]:
    graph_owner = "tests/ops/test_durable_completion_validation_graph_v1.py"
    if not _repo_path_exists(graph_owner):
        return ()
    if files and _is_durable_completion_wallclock_binding_rebinding_scope(files):
        return _durable_completion_wallclock_binding_focused_targets(files)
    if files and _is_durable_completion_validator_rebinding_scope(files):
        targets: list[str] = [graph_owner]
        if files and any(
            path in DURABLE_COMPLETION_CI_POLICY_PATHS
            or path in DURABLE_COMPLETION_CI_WORKFLOW_REBUNDLE_PATHS
            for path in files
        ):
            ci_owner = "tests/ci/test_ci_diff_aware_test_selection_v1.py"
            if _repo_path_exists(ci_owner):
                targets.append(ci_owner)
        return tuple(sorted(set(targets)))
    for path in REQUIRED_DURABLE_COMPLETION_TEST_OWNERS:
        if not _repo_path_exists(path):
            return ()
    full_targets: list[str] = []
    for path in CANONICAL_DURABLE_COMPLETION_FOCUSED_TESTS:
        if _repo_path_exists(path):
            full_targets.append(path)
    if len(full_targets) < len(REQUIRED_DURABLE_COMPLETION_TEST_OWNERS):
        return ()
    return tuple(sorted(full_targets))


def _is_preflight_assembly_scoped_path(path: str) -> bool:
    if path == PE26_ASSEMBLY_OWNER:
        return True
    if path in {
        "tests/ops/test_bounded_futures_testnet_preflight_execution_readiness_assembly_lifecycle_integration_contract_v0.py",
        "tests/ops/test_bounded_futures_testnet_reconciliation_review_lifecycle_integration_contract_v0.py",
    }:
        return True
    return False


def _is_preflight_assembly_rebundle_path(path: str) -> bool:
    return _is_preflight_assembly_scoped_path(path) or path in PREFLIGHT_ASSEMBLY_CI_POLICY_PATHS


def _preflight_assembly_focused_targets() -> tuple[str, ...]:
    for path in REQUIRED_PREFLIGHT_ASSEMBLY_TEST_OWNERS:
        if not _repo_path_exists(path):
            return ()
    targets: list[str] = []
    for path in CANONICAL_PREFLIGHT_ASSEMBLY_FOCUSED_TESTS:
        if _repo_path_exists(path):
            targets.append(path)
    if len(targets) < len(REQUIRED_PREFLIGHT_ASSEMBLY_TEST_OWNERS):
        return ()
    return tuple(sorted(targets))


def _is_risk_killswitch_scoped_path(path: str) -> bool:
    if path == PE22_RISK_KILLSWITCH_OWNER:
        return True
    if path == PE22_RISK_KILLSWITCH_TEST_OWNER:
        return True
    return False


def _is_risk_killswitch_rebundle_path(path: str) -> bool:
    return _is_risk_killswitch_scoped_path(path) or path in RISK_KILLSWITCH_CI_POLICY_PATHS


def _risk_killswitch_focused_targets() -> tuple[str, ...]:
    for path in REQUIRED_RISK_KILLSWITCH_TEST_OWNERS:
        if not _repo_path_exists(path):
            return ()
    targets: list[str] = []
    for path in CANONICAL_RISK_KILLSWITCH_FOCUSED_TESTS:
        if _repo_path_exists(path):
            targets.append(path)
    if len(targets) < len(REQUIRED_RISK_KILLSWITCH_TEST_OWNERS):
        return ()
    return tuple(sorted(targets))


def _is_tiny_order_scoped_path(path: str) -> bool:
    if path == PE30_TINY_ORDER_OWNER:
        return True
    if path == PE30_TINY_ORDER_TEST_OWNER:
        return True
    return False


def _is_tiny_order_rebundle_path(path: str) -> bool:
    return _is_tiny_order_scoped_path(path) or path in TINY_ORDER_CI_POLICY_PATHS


def _tiny_order_focused_targets() -> tuple[str, ...]:
    for path in REQUIRED_TINY_ORDER_TEST_OWNERS:
        if not _repo_path_exists(path):
            return ()
    targets: list[str] = []
    for path in CANONICAL_TINY_ORDER_FOCUSED_TESTS:
        if _repo_path_exists(path):
            targets.append(path)
    if len(targets) < len(REQUIRED_TINY_ORDER_TEST_OWNERS):
        return ()
    return tuple(sorted(targets))


def _is_bounded_network_testnet_preflight_scoped_path(path: str) -> bool:
    return path in {
        BOUNDED_NETWORK_TESTNET_PREFLIGHT_OWNER,
        BOUNDED_NETWORK_TESTNET_PREFLIGHT_TEST_OWNER,
    }


def _is_bounded_network_testnet_preflight_rebundle_path(path: str) -> bool:
    return (
        _is_bounded_network_testnet_preflight_scoped_path(path)
        or path in BOUNDED_NETWORK_TESTNET_PREFLIGHT_CI_POLICY_PATHS
    )


def _bounded_network_testnet_preflight_focused_targets() -> tuple[str, ...]:
    for path in REQUIRED_BOUNDED_NETWORK_TESTNET_PREFLIGHT_TEST_OWNERS:
        if not _repo_path_exists(path):
            return ()
    targets: list[str] = []
    for path in CANONICAL_BOUNDED_NETWORK_TESTNET_PREFLIGHT_FOCUSED_TESTS:
        if _repo_path_exists(path):
            targets.append(path)
    if len(targets) < len(REQUIRED_BOUNDED_NETWORK_TESTNET_PREFLIGHT_TEST_OWNERS):
        return ()
    return tuple(sorted(targets))


def _try_bounded_network_testnet_preflight_focused(files: list[str]) -> SelectionResult | None:
    if not files:
        return None
    if not any(_is_bounded_network_testnet_preflight_scoped_path(f) for f in files):
        return None
    if not all(_is_bounded_network_testnet_preflight_rebundle_path(f) for f in files):
        return None
    files_set = set(files)
    if (
        BOUNDED_NETWORK_TESTNET_PREFLIGHT_OWNER in files_set
        and BOUNDED_NETWORK_TESTNET_PREFLIGHT_TEST_OWNER not in files_set
    ):
        return None
    targets = _bounded_network_testnet_preflight_focused_targets()
    if not targets:
        return None
    modules: tuple[str, ...] = ("src.ops.bounded_network_testnet_preflight_contract_v0",)
    return SelectionResult(
        "FOCUSED",
        "bounded_network_testnet_preflight_focused",
        targets,
        modules,
    )


def _is_runtime_wallclock_evidence_emitter_scoped_path(path: str) -> bool:
    return path in {
        RUNTIME_WALLCLOCK_EVIDENCE_EMITTER_OWNER,
        RUNTIME_WALLCLOCK_EVIDENCE_EMITTER_TEST_OWNER,
    }


def _is_runtime_wallclock_evidence_emitter_rebundle_path(path: str) -> bool:
    return (
        _is_runtime_wallclock_evidence_emitter_scoped_path(path)
        or path in RUNTIME_WALLCLOCK_EVIDENCE_EMITTER_CI_POLICY_PATHS
    )


def _runtime_wallclock_evidence_emitter_focused_targets() -> tuple[str, ...]:
    for path in REQUIRED_RUNTIME_WALLCLOCK_EVIDENCE_EMITTER_TEST_OWNERS:
        if not _repo_path_exists(path):
            return ()
    targets: list[str] = []
    for path in CANONICAL_RUNTIME_WALLCLOCK_EVIDENCE_EMITTER_FOCUSED_TESTS:
        if _repo_path_exists(path):
            targets.append(path)
    if len(targets) < len(REQUIRED_RUNTIME_WALLCLOCK_EVIDENCE_EMITTER_TEST_OWNERS):
        return ()
    return tuple(sorted(targets))


def _try_runtime_wallclock_evidence_emitter_focused(files: list[str]) -> SelectionResult | None:
    if not files:
        return None
    if not any(_is_runtime_wallclock_evidence_emitter_scoped_path(f) for f in files):
        return None
    if not all(_is_runtime_wallclock_evidence_emitter_rebundle_path(f) for f in files):
        return None
    files_set = set(files)
    if (
        RUNTIME_WALLCLOCK_EVIDENCE_EMITTER_OWNER in files_set
        and RUNTIME_WALLCLOCK_EVIDENCE_EMITTER_TEST_OWNER not in files_set
    ):
        return None
    targets = _runtime_wallclock_evidence_emitter_focused_targets()
    if not targets:
        return None
    modules: tuple[str, ...] = ("src.ops.runtime_wallclock_evidence_emitter_contract_v0",)
    return SelectionResult(
        "FOCUSED",
        "runtime_wallclock_evidence_emitter_focused",
        targets,
        modules,
    )


def _is_testnet_wallclock_duration_evidence_scoped_path(path: str) -> bool:
    return path in {
        TESTNET_WALLCLOCK_DURATION_EVIDENCE_OWNER,
        TESTNET_WALLCLOCK_DURATION_EVIDENCE_TEST_OWNER,
    }


def _is_testnet_wallclock_duration_evidence_rebundle_path(path: str) -> bool:
    return (
        _is_testnet_wallclock_duration_evidence_scoped_path(path)
        or path in TESTNET_WALLCLOCK_DURATION_EVIDENCE_CI_POLICY_PATHS
    )


def _testnet_wallclock_duration_evidence_focused_targets() -> tuple[str, ...]:
    for path in REQUIRED_TESTNET_WALLCLOCK_DURATION_EVIDENCE_TEST_OWNERS:
        if not _repo_path_exists(path):
            return ()
    targets: list[str] = []
    for path in CANONICAL_TESTNET_WALLCLOCK_DURATION_EVIDENCE_FOCUSED_TESTS:
        if _repo_path_exists(path):
            targets.append(path)
    if len(targets) < len(REQUIRED_TESTNET_WALLCLOCK_DURATION_EVIDENCE_TEST_OWNERS):
        return ()
    return tuple(sorted(targets))


def _try_wallclock_field_name_paired_rewire(files: list[str]) -> SelectionResult | None:
    if not files:
        return None
    if set(files) != WALLCLOCK_FIELD_NAME_PAIRED_REWIRE_TEST_OWNERS:
        return None
    for path in WALLCLOCK_FIELD_NAME_PAIRED_REWIRE_TEST_OWNERS:
        if not _repo_path_exists(path):
            return None
    return SelectionResult(
        "NO_OP",
        "wallclock_field_name_paired_rewire_no_op",
        (),
    )


def _try_testnet_wallclock_duration_evidence_focused(files: list[str]) -> SelectionResult | None:
    if not files:
        return None
    if not any(_is_testnet_wallclock_duration_evidence_scoped_path(f) for f in files):
        return None
    if not all(_is_testnet_wallclock_duration_evidence_rebundle_path(f) for f in files):
        return None
    files_set = set(files)
    if (
        TESTNET_WALLCLOCK_DURATION_EVIDENCE_OWNER in files_set
        and TESTNET_WALLCLOCK_DURATION_EVIDENCE_TEST_OWNER not in files_set
    ):
        return None
    targets = _testnet_wallclock_duration_evidence_focused_targets()
    if not targets:
        return None
    modules: tuple[str, ...] = ("src.ops.testnet_wallclock_duration_evidence_contract_v0",)
    return SelectionResult(
        "FOCUSED",
        "testnet_wallclock_duration_evidence_focused",
        targets,
        modules,
    )


def _is_wallclock_scoped_path(path: str) -> bool:
    if path == WALLCLOCK_OWNER:
        return True
    if path in WALLCLOCK_SCRIPT_PATHS:
        return True
    if path in REQUIRED_WALLCLOCK_TEST_OWNERS:
        return True
    return False


def _is_wallclock_rebundle_path(path: str) -> bool:
    return _is_wallclock_scoped_path(path) or path in WALLCLOCK_CI_POLICY_PATHS


def _wallclock_focused_targets() -> tuple[str, ...]:
    for path in REQUIRED_WALLCLOCK_TEST_OWNERS:
        if not _repo_path_exists(path):
            return ()
    targets: list[str] = []
    for path in CANONICAL_WALLCLOCK_FOCUSED_TESTS:
        if _repo_path_exists(path):
            targets.append(path)
    if len(targets) < len(REQUIRED_WALLCLOCK_TEST_OWNERS):
        return ()
    return tuple(sorted(targets))


def _try_wallclock_focused(files: list[str]) -> SelectionResult | None:
    if not files:
        return None
    if not any(_is_wallclock_scoped_path(f) for f in files):
        return None
    if not all(_is_wallclock_rebundle_path(f) for f in files):
        return None
    files_set = set(files)
    if WALLCLOCK_OWNER in files_set and not set(REQUIRED_WALLCLOCK_TEST_OWNERS).issubset(files_set):
        return None
    targets = _wallclock_focused_targets()
    if not targets:
        return None
    modules: tuple[str, ...] = ("src.ops.wallclock_session_evidence_v0",)
    return SelectionResult(
        "FOCUSED",
        "wallclock_focused",
        targets,
        modules,
    )


def _is_ci_infra_workflow_path(path: str) -> bool:
    return path in CI_INFRA_WORKFLOW_ALLOWLIST


def _is_ci_infra_contract_test_path(path: str) -> bool:
    return path in CI_INFRA_CONTRACT_TEST_ALLOWLIST


def _is_ci_infra_scoped_path(path: str) -> bool:
    return (
        path in CI_BOOTSTRAP_FOCUSED_PATHS
        or _is_ci_infra_workflow_path(path)
        or _is_ci_infra_contract_test_path(path)
    )


def _is_ci_infra_rebundle_path(path: str) -> bool:
    if path in CI_MAPPING_FULL_PATHS:
        return False
    return (
        path in CI_BOOTSTRAP_FOCUSED_PATHS
        or _is_ci_infra_workflow_path(path)
        or _is_ci_infra_contract_test_path(path)
        or path == "tests/ci/test_ci_testowner_runtime_budget_reporting_contract_v0.py"
    )


def _ci_infra_focused_targets(files: list[str]) -> tuple[str, ...]:
    targets: list[str] = []
    seen: set[str] = set()

    def add(path: str) -> None:
        if path not in seen and _repo_path_exists(path):
            seen.add(path)
            targets.append(path)

    for path in CI_INFRA_CORE_FOCUSED_TESTS:
        add(path)
    for path in files:
        if _is_ci_infra_contract_test_path(path):
            add(path)
    if len([path for path in CI_INFRA_CORE_FOCUSED_TESTS if _repo_path_exists(path)]) < len(
        CI_INFRA_CORE_FOCUSED_TESTS
    ):
        return ()
    return tuple(sorted(targets))


def _try_ci_infra_focused(files: list[str]) -> SelectionResult | None:
    if not files:
        return None
    if not any(_is_ci_infra_scoped_path(f) for f in files):
        return None
    if not all(_is_ci_infra_rebundle_path(f) for f in files):
        return None
    for path in files:
        if path.startswith(".github/workflows/") and not _is_ci_infra_workflow_path(path):
            return None
    has_workflow = any(_is_ci_infra_workflow_path(f) for f in files)
    has_selector_script = "scripts/ops/ci_test_selection_v1.py" in files
    has_contract = any(_is_ci_infra_contract_test_path(f) for f in files)
    if has_workflow and not (has_selector_script or has_contract):
        return None
    # Selector script rebundles with foreign paths require both anchor contract tests
    # in the diff; pure ci_infra rebundles (workflow + selector + contract) run core suite.
    if has_selector_script and not CI_INFRA_MINIMUM_CONTRACT_ANCHORS.issubset(set(files)):
        if not (all(_is_ci_infra_rebundle_path(f) for f in files) and has_workflow and has_contract):
            return None
    targets = _ci_infra_focused_targets(files)
    if not targets:
        return None
    return SelectionResult(
        "FOCUSED",
        "ci_infra_focused",
        targets,
    )


def _has_ci_infra_substantive_intent(files: list[str]) -> bool:
    has_workflow = any(_is_ci_infra_workflow_path(f) for f in files)
    has_selector = any(f in CI_BOOTSTRAP_FOCUSED_PATHS for f in files)
    has_contract = any(_is_ci_infra_contract_test_path(f) for f in files)
    if has_workflow and not (has_selector or has_contract):
        return False
    return any(_is_ci_infra_scoped_path(f) for f in files)


def _try_reconciliation_primary_evidence_focused(files: list[str]) -> SelectionResult | None:
    if not files:
        return None
    if not any(_is_reconciliation_primary_evidence_scoped_path(f) for f in files):
        return None
    if not all(_is_reconciliation_primary_evidence_rebundle_path(f) for f in files):
        return None
    files_set = set(files)
    if (
        PE21_RECONCILIATION_PRIMARY_EVIDENCE_OWNER in files_set
        and PE21_RECONCILIATION_PRIMARY_EVIDENCE_TEST_OWNER not in files_set
    ):
        return None
    targets = _reconciliation_primary_evidence_focused_targets()
    if not targets:
        return None
    modules: tuple[str, ...] = (
        "src.ops.bounded_futures_testnet_position_order_reconciliation_primary_evidence_integration_contract_v0",
    )
    return SelectionResult(
        "FOCUSED",
        "reconciliation_primary_evidence_focused",
        targets,
        modules,
    )


def _is_reconciliation_primary_evidence_scoped_path(path: str) -> bool:
    if path == PE21_RECONCILIATION_PRIMARY_EVIDENCE_OWNER:
        return True
    if path == PE21_RECONCILIATION_PRIMARY_EVIDENCE_TEST_OWNER:
        return True
    return False


def _is_reconciliation_primary_evidence_rebundle_path(path: str) -> bool:
    return (
        _is_reconciliation_primary_evidence_scoped_path(path)
        or path in RECONCILIATION_PRIMARY_EVIDENCE_CI_POLICY_PATHS
    )


def _reconciliation_primary_evidence_focused_targets() -> tuple[str, ...]:
    for path in REQUIRED_RECONCILIATION_PRIMARY_EVIDENCE_TEST_OWNERS:
        if not _repo_path_exists(path):
            return ()
    targets: list[str] = []
    for path in CANONICAL_RECONCILIATION_PRIMARY_EVIDENCE_FOCUSED_TESTS:
        if _repo_path_exists(path):
            targets.append(path)
    if len(targets) < len(REQUIRED_RECONCILIATION_PRIMARY_EVIDENCE_TEST_OWNERS):
        return ()
    return tuple(sorted(targets))


def _try_tiny_order_focused(files: list[str]) -> SelectionResult | None:
    if not files:
        return None
    if not any(_is_tiny_order_scoped_path(f) for f in files):
        return None
    if not all(_is_tiny_order_rebundle_path(f) for f in files):
        return None
    files_set = set(files)
    if PE30_TINY_ORDER_OWNER in files_set and PE30_TINY_ORDER_TEST_OWNER not in files_set:
        return None
    targets = _tiny_order_focused_targets()
    if not targets:
        return None
    modules: tuple[str, ...] = (
        "src.ops.bounded_futures_testnet_tiny_order_lifecycle_integration_contract_v0",
    )
    return SelectionResult(
        "FOCUSED",
        "tiny_order_focused",
        targets,
        modules,
    )


def _try_risk_killswitch_focused(files: list[str]) -> SelectionResult | None:
    if not files:
        return None
    if not any(_is_risk_killswitch_scoped_path(f) for f in files):
        return None
    if not all(_is_risk_killswitch_rebundle_path(f) for f in files):
        return None
    files_set = set(files)
    if PE22_RISK_KILLSWITCH_OWNER in files_set and PE22_RISK_KILLSWITCH_TEST_OWNER not in files_set:
        return None
    targets = _risk_killswitch_focused_targets()
    if not targets:
        return None
    modules: tuple[str, ...] = (
        "src.ops.bounded_futures_testnet_risk_killswitch_lifecycle_integration_contract_v0",
    )
    return SelectionResult(
        "FOCUSED",
        "risk_killswitch_focused",
        targets,
        modules,
    )


def _try_preflight_assembly_focused(files: list[str]) -> SelectionResult | None:
    if not files:
        return None
    if not any(_is_preflight_assembly_scoped_path(f) for f in files):
        return None
    if not all(_is_preflight_assembly_rebundle_path(f) for f in files):
        return None
    targets = _preflight_assembly_focused_targets()
    if not targets:
        return None
    modules: tuple[str, ...] = (
        "src.ops.bounded_futures_testnet_preflight_execution_readiness_assembly_lifecycle_integration_contract_v0",
    )
    return SelectionResult(
        "FOCUSED",
        "preflight_assembly_focused",
        targets,
        modules,
    )


def _has_productive_src_python(files: list[str]) -> bool:
    return any(f.startswith("src/") and f.endswith(".py") for f in files)


def _is_master_v2_binding_contract_scoped_path(path: str) -> bool:
    return path in MASTER_V2_BINDING_CONTRACT_SCOPED_PATHS


def _is_master_v2_binding_contract_scope(files: list[str]) -> bool:
    if not files:
        return False
    if MASTER_V2_BINDING_CONTRACT_TEST_OWNER not in files:
        return False
    if DURABLE_COMPLETION_FACADE_PATH not in files:
        return False
    for path in files:
        if path in DURABLE_COMPLETION_CI_POLICY_PATHS:
            return False
        if path in DURABLE_COMPLETION_CI_WORKFLOW_REBUNDLE_PATHS:
            return False
        if path not in MASTER_V2_BINDING_CONTRACT_SCOPED_PATHS:
            return False
    validator_paths = {
        p
        for p in files
        if p.startswith("src/ops/durable_completion_validation/validators/") and p.endswith(".py")
    }
    if validator_paths and validator_paths != {
        MASTER_V2_BINDING_CONTRACT_COMPLETION_CHAIN_VALIDATOR
    }:
        return False
    return True


def _master_v2_binding_focused_targets(files: list[str]) -> tuple[str, ...]:
    if MASTER_V2_BINDING_CONTRACT_TEST_OWNER not in files:
        return ()
    if not _repo_path_exists(MASTER_V2_BINDING_CONTRACT_GRAPH_TEST_OWNER):
        return ()
    selected: list[str] = []
    for target in MASTER_V2_BINDING_CONTRACT_FOCUSED_TARGETS:
        path, _ = _split_pytest_target(target)
        if path == MASTER_V2_BINDING_CONTRACT_TEST_OWNER:
            selected.append(target)
        elif _repo_pytest_target_exists(target):
            selected.append(target)
    if not selected:
        return ()
    return tuple(sorted(selected))


def _try_master_v2_binding_contract_focused(files: list[str]) -> SelectionResult | None:
    if not files:
        return None
    if not _is_master_v2_binding_contract_scope(files):
        return None
    targets = _master_v2_binding_focused_targets(files)
    if not targets:
        return None
    modules: tuple[str, ...] = (
        "src.ops.bounded_futures_testnet_durable_run_primary_evidence_completion_integration_contract_v0",
        "src.ops.durable_completion_validation",
    )
    return SelectionResult(
        "FOCUSED",
        "durable_completion_master_v2_binding_contract_focused",
        targets,
        modules,
    )


def _is_master_v2_replay_display_projection_digest_completion_evidence_scope(
    files: list[str],
) -> bool:
    if not files:
        return False
    required = {
        DURABLE_COMPLETION_FACADE_PATH,
        OFFLINE_MASTER_V2_DOUBLE_PLAY_SCENARIO_REPLAY_OWNER_PATH,
        MASTER_V2_BINDING_CONTRACT_TEST_OWNER,
        OFFLINE_MASTER_V2_DOUBLE_PLAY_SCENARIO_REPLAY_TRADING_TEST_OWNER,
        OFFLINE_MASTER_V2_DOUBLE_PLAY_SCENARIO_REPLAY_OPS_TEST_OWNER,
    }
    if not required.issubset(set(files)):
        return False
    for path in files:
        if path not in MASTER_V2_REPLAY_DISPLAY_PROJECTION_DIGEST_COMPLETION_EVIDENCE_SCOPED_PATHS:
            return False
    return True


def _master_v2_replay_display_projection_digest_completion_evidence_focused_targets(
    files: list[str] | None = None,
) -> tuple[str, ...]:
    targets: list[str] = []
    for (
        target
    ) in CANONICAL_MASTER_V2_REPLAY_DISPLAY_PROJECTION_DIGEST_COMPLETION_EVIDENCE_FOCUSED_TARGETS:
        path, node = _split_pytest_target(target)
        if node is None:
            if _repo_path_exists(path):
                targets.append(target)
        elif _repo_pytest_target_exists(target):
            targets.append(target)
    if files and any(
        path in OFFLINE_MASTER_V2_DOUBLE_PLAY_SCENARIO_REPLAY_CI_POLICY_PATHS for path in files
    ):
        for (
            ci_target
        ) in MASTER_V2_REPLAY_DISPLAY_PROJECTION_DIGEST_COMPLETION_EVIDENCE_CI_SELECTOR_TARGETS:
            if _repo_pytest_target_exists(ci_target):
                targets.append(ci_target)
    if not targets:
        return ()
    return tuple(sorted(set(targets)))


def _try_master_v2_replay_display_projection_digest_completion_evidence_focused(
    files: list[str],
) -> SelectionResult | None:
    if not _is_master_v2_replay_display_projection_digest_completion_evidence_scope(files):
        return None
    targets = _master_v2_replay_display_projection_digest_completion_evidence_focused_targets(files)
    if not targets:
        return None
    return SelectionResult(
        "FOCUSED",
        "master_v2_replay_display_projection_digest_completion_evidence_focused",
        targets,
        (
            "trading.master_v2.offline_double_play_scenario_replay_v0",
            "src.ops.bounded_futures_testnet_durable_run_primary_evidence_completion_integration_contract_v0",
            "src.ops.durable_completion_validation",
        ),
    )


def _is_offline_master_v2_replay_six_node_validation_graph_binding_scope(files: list[str]) -> bool:
    if not files:
        return False
    required = {
        OFFLINE_MASTER_V2_REPLAY_SIX_NODE_VALIDATION_GRAPH_BINDING_OWNER_PATH,
        OFFLINE_MASTER_V2_DOUBLE_PLAY_SCENARIO_REPLAY_OPS_TEST_OWNER,
    }
    files_set = set(files)
    if not required.issubset(files_set):
        return False
    for path in files:
        if path not in OFFLINE_MASTER_V2_REPLAY_SIX_NODE_VALIDATION_GRAPH_BINDING_SCOPED_PATHS:
            return False
    return True


def _offline_master_v2_replay_six_node_validation_graph_binding_focused_targets() -> tuple[
    str, ...
]:
    return tuple(
        path
        for path in CANONICAL_OFFLINE_MASTER_V2_REPLAY_SIX_NODE_VALIDATION_GRAPH_BINDING_FOCUSED_TESTS
        if _repo_path_exists(path)
    )


def _try_offline_master_v2_replay_six_node_validation_graph_binding_focused(
    files: list[str],
) -> SelectionResult | None:
    if not _is_offline_master_v2_replay_six_node_validation_graph_binding_scope(files):
        return None
    targets = _offline_master_v2_replay_six_node_validation_graph_binding_focused_targets()
    if not targets:
        return None
    return SelectionResult(
        "FOCUSED",
        "offline_master_v2_replay_six_node_validation_graph_binding_focused",
        targets,
        (
            "ops.offline_master_v2_replay_six_node_validation_graph_binding_v0",
            "trading.master_v2.offline_double_play_scenario_replay_v0",
            "src.ops.durable_completion_validation",
        ),
    )


def _is_bounded_testnet_market_input_admission_wiring_scope(files: list[str]) -> bool:
    if not files:
        return False
    required = {
        BOUNDED_TESTNET_MARKET_INPUT_ADMISSION_WIRING_OWNER_PATH,
        BOUNDED_TESTNET_MARKET_INPUT_ADMISSION_WIRING_TEST_OWNER,
    }
    files_set = set(files)
    if not required.issubset(files_set):
        return False
    for path in files:
        if path not in BOUNDED_TESTNET_MARKET_INPUT_ADMISSION_WIRING_SCOPED_PATHS:
            return False
    return True


def _bounded_testnet_market_input_admission_wiring_focused_targets(
    files: list[str] | None = None,
) -> tuple[str, ...]:
    targets: list[str] = []
    for target in BOUNDED_TESTNET_MARKET_INPUT_ADMISSION_WIRING_FOCUSED_TARGETS:
        path, node = _split_pytest_target(target)
        if node is None:
            if _repo_path_exists(path):
                targets.append(target)
        elif _repo_pytest_target_exists(target):
            targets.append(target)
    if not targets:
        return ()
    return tuple(sorted(set(targets)))


def _try_bounded_testnet_market_input_admission_wiring_focused(
    files: list[str],
) -> SelectionResult | None:
    if not _is_bounded_testnet_market_input_admission_wiring_scope(files):
        return None
    targets = _bounded_testnet_market_input_admission_wiring_focused_targets(files)
    if not targets:
        return None
    return SelectionResult(
        "FOCUSED",
        "bounded_testnet_market_input_admission_wiring_focused",
        targets,
        (
            "ops.bounded_testnet_market_input_admission_wiring_v0",
            "ops.bounded_master_v2_testnet_completion_path_wiring_v0",
        ),
    )


def _is_bounded_testnet_runtime_market_observation_producer_scope(files: list[str]) -> bool:
    if not files:
        return False
    files_set = set(files)
    required = {
        BOUNDED_TESTNET_RUNTIME_MARKET_OBSERVATION_PRODUCER_OWNER_PATH,
        BOUNDED_TESTNET_RUNTIME_MARKET_OBSERVATION_PRODUCER_TEST_OWNER,
        BOUNDED_MASTER_V2_TESTNET_COMPLETION_PATH_WIRING_ADAPTER_OWNER,
        BOUNDED_MASTER_V2_TESTNET_COMPLETION_PATH_WIRING_ADAPTER_TEST_OWNER,
    }
    if not required.issubset(files_set):
        return False
    for path in files:
        if path not in BOUNDED_TESTNET_RUNTIME_MARKET_OBSERVATION_PRODUCER_SCOPED_PATHS:
            return False
    return True


def _bounded_testnet_runtime_market_observation_producer_focused_targets(
    files: list[str] | None = None,
) -> tuple[str, ...]:
    targets: list[str] = []
    for target in BOUNDED_TESTNET_RUNTIME_MARKET_OBSERVATION_PRODUCER_FOCUSED_TARGETS:
        path, node = _split_pytest_target(target)
        if node is None:
            if _repo_path_exists(path):
                targets.append(target)
        elif _repo_pytest_target_exists(target):
            targets.append(target)
    if not targets:
        return ()
    return tuple(sorted(set(targets)))


def _try_bounded_testnet_runtime_market_observation_producer_focused(
    files: list[str],
) -> SelectionResult | None:
    if not _is_bounded_testnet_runtime_market_observation_producer_scope(files):
        return None
    targets = _bounded_testnet_runtime_market_observation_producer_focused_targets(files)
    if not targets:
        return None
    return SelectionResult(
        "FOCUSED",
        "bounded_testnet_runtime_market_observation_producer_focused",
        targets,
        (
            "ops.bounded_testnet_runtime_market_observation_producer_v0",
            "ops.bounded_testnet_market_input_admission_wiring_v0",
        ),
    )


def _is_bounded_testnet_execute_path_market_observation_closeout_binding_scope(
    files: list[str],
) -> bool:
    if not files:
        return False
    required = {
        BOUNDED_MASTER_V2_TESTNET_COMPLETION_PATH_WIRING_ADAPTER_OWNER,
        BOUNDED_MASTER_V2_TESTNET_COMPLETION_PATH_WIRING_ADAPTER_TEST_OWNER,
    }
    files_set = set(files)
    if not required.issubset(files_set):
        return False
    for path in files:
        if (
            path
            not in BOUNDED_TESTNET_EXECUTE_PATH_MARKET_OBSERVATION_CLOSEOUT_BINDING_SCOPED_PATHS
        ):
            return False
    return True


def _bounded_testnet_execute_path_market_observation_closeout_binding_focused_targets(
    files: list[str] | None = None,
) -> tuple[str, ...]:
    targets: list[str] = []
    for target in BOUNDED_TESTNET_EXECUTE_PATH_MARKET_OBSERVATION_CLOSEOUT_BINDING_FOCUSED_TARGETS:
        path, node = _split_pytest_target(target)
        if node is None:
            if _repo_path_exists(path):
                targets.append(target)
        elif _repo_pytest_target_exists(target):
            targets.append(target)
    if not targets:
        return ()
    return tuple(sorted(set(targets)))


def _try_bounded_testnet_execute_path_market_observation_closeout_binding_focused(
    files: list[str],
) -> SelectionResult | None:
    if not _is_bounded_testnet_execute_path_market_observation_closeout_binding_scope(files):
        return None
    targets = _bounded_testnet_execute_path_market_observation_closeout_binding_focused_targets(
        files
    )
    if not targets:
        return None
    return SelectionResult(
        "FOCUSED",
        "bounded_testnet_execute_path_market_observation_closeout_binding_focused",
        targets,
        (
            "ops.bounded_testnet_market_input_admission_wiring_v0",
            "ops.bounded_master_v2_testnet_completion_path_wiring_v0",
        ),
    )


def _is_bounded_master_v2_testnet_completion_path_wiring_scope(files: list[str]) -> bool:
    if not files:
        return False
    required = {
        BOUNDED_MASTER_V2_TESTNET_COMPLETION_PATH_WIRING_OWNER_PATH,
        BOUNDED_MASTER_V2_TESTNET_COMPLETION_PATH_WIRING_TEST_OWNER,
    }
    files_set = set(files)
    if not required.issubset(files_set):
        return False
    for path in files:
        if path not in BOUNDED_MASTER_V2_TESTNET_COMPLETION_PATH_WIRING_SCOPED_PATHS:
            return False
    return True


def _bounded_master_v2_testnet_completion_path_wiring_focused_targets(
    files: list[str] | None = None,
) -> tuple[str, ...]:
    targets: list[str] = []
    for target in BOUNDED_MASTER_V2_TESTNET_COMPLETION_PATH_WIRING_FOCUSED_TARGETS:
        path, node = _split_pytest_target(target)
        if node is None:
            if _repo_path_exists(path):
                targets.append(target)
        elif _repo_pytest_target_exists(target):
            targets.append(target)
    if files and any(
        path in BOUNDED_MASTER_V2_TESTNET_COMPLETION_PATH_WIRING_CI_POLICY_PATHS for path in files
    ):
        for ci_target in BOUNDED_MASTER_V2_TESTNET_COMPLETION_PATH_WIRING_CI_SELECTOR_TARGETS:
            if _repo_pytest_target_exists(ci_target):
                targets.append(ci_target)
    if not targets:
        return ()
    return tuple(sorted(set(targets)))


def _try_bounded_master_v2_testnet_completion_path_wiring_focused(
    files: list[str],
) -> SelectionResult | None:
    if not _is_bounded_master_v2_testnet_completion_path_wiring_scope(files):
        return None
    targets = _bounded_master_v2_testnet_completion_path_wiring_focused_targets(files)
    if not targets:
        return None
    return SelectionResult(
        "FOCUSED",
        "bounded_master_v2_testnet_completion_path_wiring_focused",
        targets,
        (
            "ops.bounded_master_v2_testnet_completion_path_wiring_v0",
            "ops.offline_master_v2_replay_six_node_validation_graph_binding_v0",
            "src.ops.bounded_futures_testnet_durable_run_primary_evidence_completion_integration_contract_v0",
        ),
    )


def _is_offline_master_v2_double_play_scenario_replay_scope(files: list[str]) -> bool:
    if not files:
        return False
    required = {
        OFFLINE_MASTER_V2_DOUBLE_PLAY_SCENARIO_REPLAY_OWNER_PATH,
        OFFLINE_MASTER_V2_DOUBLE_PLAY_SCENARIO_REPLAY_TRADING_TEST_OWNER,
        OFFLINE_MASTER_V2_DOUBLE_PLAY_SCENARIO_REPLAY_OPS_TEST_OWNER,
    }
    files_set = set(files)
    if not required.issubset(files_set):
        return False
    for path in files:
        if path not in OFFLINE_MASTER_V2_DOUBLE_PLAY_SCENARIO_REPLAY_SCOPED_PATHS:
            return False
    return True


def _offline_master_v2_double_play_scenario_replay_focused_targets() -> tuple[str, ...]:
    return tuple(
        path
        for path in CANONICAL_OFFLINE_MASTER_V2_DOUBLE_PLAY_SCENARIO_REPLAY_FOCUSED_TESTS
        if _repo_path_exists(path)
    )


def _try_offline_master_v2_double_play_scenario_replay_focused(
    files: list[str],
) -> SelectionResult | None:
    if not _is_offline_master_v2_double_play_scenario_replay_scope(files):
        return None
    targets = _offline_master_v2_double_play_scenario_replay_focused_targets()
    if not targets:
        return None
    return SelectionResult(
        "FOCUSED",
        "offline_master_v2_double_play_scenario_replay_focused",
        targets,
        ("trading.master_v2.offline_double_play_scenario_replay_v0",),
    )


def _try_durable_completion_focused(files: list[str]) -> SelectionResult | None:
    if not files:
        return None
    if not any(_is_durable_completion_scoped_path(f) for f in files):
        return None
    if not all(_is_durable_completion_rebundle_path(f) for f in files):
        return None
    targets = _durable_completion_focused_targets(files)
    if not targets:
        return None
    modules: tuple[str, ...] = ("src.ops.durable_completion_validation",)
    if _is_durable_completion_wallclock_binding_rebinding_scope(files):
        modules = (
            "src.ops.bounded_futures_testnet_durable_run_primary_evidence_completion_integration_contract_v0",
        )
    elif not _is_durable_completion_validator_rebinding_scope(files):
        modules = (
            "src.ops.bounded_futures_testnet_durable_run_primary_evidence_completion_integration_contract_v0",
            "src.ops.durable_completion_validation",
        )
    return SelectionResult(
        "FOCUSED",
        "durable_completion_focused",
        targets,
        modules,
    )


def _try_market_dashboard_focused(files: list[str]) -> SelectionResult | None:
    if not files:
        return None
    if not any(_is_market_dashboard_scoped_path(f) for f in files):
        return None
    if not all(_is_market_dashboard_rebundle_path(f) for f in files):
        return None
    targets = _market_dashboard_focused_targets()
    if not targets:
        return None
    modules: set[str] = set()
    for path in files:
        if path.startswith("src/webui/") and path.endswith(".py"):
            module = _prod_path_to_import_module(path)
            if _validate_import_module(module):
                modules.add(module)
    return SelectionResult(
        "FOCUSED",
        "market_dashboard_focused",
        targets,
        tuple(sorted(modules)),
    )


def categorize(path: str) -> str:
    p = PurePosixPath(path).as_posix()
    if p in OFFLINE_MASTER_V2_DOUBLE_PLAY_SCENARIO_REPLAY_CATEGORIZE_PATHS:
        return "offline_master_v2_double_play_scenario_replay_focused"
    if p == BOUNDED_TESTNET_MARKET_INPUT_ADMISSION_WIRING_OWNER_PATH:
        return "bounded_testnet_market_input_admission_wiring_focused"
    if p == BOUNDED_TESTNET_MARKET_INPUT_ADMISSION_WIRING_TEST_OWNER:
        return "bounded_testnet_market_input_admission_wiring_focused"
    if p == BOUNDED_TESTNET_RUNTIME_MARKET_OBSERVATION_PRODUCER_OWNER_PATH:
        return "bounded_testnet_runtime_market_observation_producer_focused"
    if p == BOUNDED_TESTNET_RUNTIME_MARKET_OBSERVATION_PRODUCER_TEST_OWNER:
        return "bounded_testnet_runtime_market_observation_producer_focused"
    if p == BOUNDED_MASTER_V2_TESTNET_COMPLETION_PATH_WIRING_ADAPTER_OWNER:
        return "bounded_testnet_execute_path_market_observation_closeout_binding_focused"
    if p == BOUNDED_MASTER_V2_TESTNET_COMPLETION_PATH_WIRING_ADAPTER_TEST_OWNER:
        return "bounded_testnet_execute_path_market_observation_closeout_binding_focused"
    if p == BOUNDED_MASTER_V2_TESTNET_COMPLETION_PATH_WIRING_OWNER_PATH:
        return "bounded_master_v2_testnet_completion_path_wiring_focused"
    if p == BOUNDED_MASTER_V2_TESTNET_COMPLETION_PATH_WIRING_TEST_OWNER:
        return "bounded_master_v2_testnet_completion_path_wiring_focused"
    if p in DURABLE_COMPLETION_CI_POLICY_PATHS:
        return "durable_completion_focused"
    if p == MASTER_V2_BINDING_CONTRACT_TEST_OWNER:
        return "master_v2_binding_contract_focused"
    if _is_durable_completion_scoped_path(p):
        return "durable_completion_focused"
    if p in PREFLIGHT_ASSEMBLY_CI_POLICY_PATHS:
        return "preflight_assembly_focused"
    if _is_preflight_assembly_scoped_path(p):
        return "preflight_assembly_focused"
    if p in RISK_KILLSWITCH_CI_POLICY_PATHS:
        return "risk_killswitch_focused"
    if _is_risk_killswitch_scoped_path(p):
        return "risk_killswitch_focused"
    if p in TINY_ORDER_CI_POLICY_PATHS:
        return "tiny_order_focused"
    if _is_tiny_order_scoped_path(p):
        return "tiny_order_focused"
    if p in RECONCILIATION_PRIMARY_EVIDENCE_CI_POLICY_PATHS:
        return "reconciliation_primary_evidence_focused"
    if _is_reconciliation_primary_evidence_scoped_path(p):
        return "reconciliation_primary_evidence_focused"
    if p in BOUNDED_NETWORK_TESTNET_PREFLIGHT_CI_POLICY_PATHS:
        return "bounded_network_testnet_preflight_focused"
    if _is_bounded_network_testnet_preflight_scoped_path(p):
        return "bounded_network_testnet_preflight_focused"
    if p in RUNTIME_WALLCLOCK_EVIDENCE_EMITTER_CI_POLICY_PATHS:
        return "runtime_wallclock_evidence_emitter_focused"
    if _is_runtime_wallclock_evidence_emitter_scoped_path(p):
        return "runtime_wallclock_evidence_emitter_focused"
    if p in TESTNET_WALLCLOCK_DURATION_EVIDENCE_CI_POLICY_PATHS:
        return "testnet_wallclock_duration_evidence_focused"
    if _is_testnet_wallclock_duration_evidence_scoped_path(p):
        return "testnet_wallclock_duration_evidence_focused"
    if p in MARKET_DASHBOARD_CI_POLICY_PATHS:
        return "market_dashboard_focused"
    if _is_market_dashboard_scoped_path(p):
        return "market_dashboard_focused"
    if p in WALLCLOCK_CI_POLICY_PATHS or _is_wallclock_scoped_path(p):
        return "wallclock_focused"
    if _is_ci_infra_contract_test_path(p):
        return "ci_infra_focused"
    if p in CI_BOOTSTRAP_FOCUSED_PATHS:
        return "ci_bootstrap_focused"
    if p in CI_MAPPING_FULL_PATHS:
        return "ci_mapping_change"
    if p.startswith("src/ops/") and (
        fnmatch.fnmatch(p, "src/ops/*_contract_v0.py")
        or fnmatch.fnmatch(p, "src/ops/*_contract_v1.py")
    ):
        return "static_contract"
    if p.startswith("tests/webui/") and fnmatch.fnmatch(
        Path(p).name, "test_*_structure_contract*.py"
    ):
        return "static_contract"
    if p.startswith("tests/ci/") or p.startswith("tests/ops/"):
        return "static_contract"
    if p == "pytest.ini" or p.endswith("/conftest.py") or p == "tests/conftest.py":
        return "global_test_infra"
    if _is_strategy_regime_owner_prod(p):
        return "strategy_regime_owner_focused"
    if p.startswith("src/"):
        return "central_src"
    if p.startswith("scripts/"):
        return "scripts_focused"
    if p.startswith("tests/"):
        return "tests_focused"
    if p.startswith("docs/") or p.startswith("out/") or p.endswith(".md"):
        return "docs_only"
    if p.startswith(".github/workflows/"):
        return "workflow_only"
    if fnmatch.fnmatch(p, "requirements*.txt") or p in {
        "requirements.txt",
        "pyproject.toml",
        "uv.lock",
    }:
        return "dependencies"
    if p in {"setup.cfg", "setup.py"}:
        return "packaging"
    if p == ".coveragerc":
        return "coverage_config"
    if p == "Makefile" or p.startswith("config/") or p.startswith("schemas/levelup/"):
        return "config_paths"
    return "unknown"


def _is_strategy_regime_owner_prod(path: str) -> bool:
    if path.endswith("__init__.py"):
        return False
    if path in STRATEGY_REGIME_OWNER_BLOCKED_PROD:
        return False
    if path.startswith("src/strategies/") and path.endswith(".py"):
        return True
    if path.startswith("src/regime/") and path.endswith(".py"):
        return True
    return False


def _is_canonical_test_owner(path: str) -> bool:
    if not (path.startswith("tests/") and path.endswith(".py")):
        return False
    if path.startswith("tests/ci/") or path.startswith("tests/ops/"):
        return False
    return True


def _repo_path_exists(path: str) -> bool:
    return Path(path).is_file()


def _prod_path_to_import_module(prod_path: str) -> str:
    return prod_path[:-3].replace("/", ".")


def _validate_repo_relative_path(path: str) -> bool:
    if not path or not _REPO_RELATIVE_PATH.match(path):
        return False
    if path.startswith("/") or ".." in path.split("/"):
        return False
    return path.startswith("tests/") and path.endswith(".py")


def _validate_import_module(module: str) -> bool:
    return bool(module and _IMPORT_MODULE.match(module))


def _discover_load_strategy_contract_tests(prod_path: str) -> tuple[str, ...]:
    module = _prod_path_to_import_module(prod_path)
    import_markers = (
        f"from {module} import",
        f"import {module}",
    )
    found: list[str] = []
    scripts_tests = Path("tests/scripts")
    if not scripts_tests.is_dir():
        return ()
    for candidate in sorted(scripts_tests.glob("test_*load_strategy*.py")):
        rel = candidate.as_posix()
        if not _repo_path_exists(rel):
            continue
        text = candidate.read_text(encoding="utf-8", errors="replace")
        if any(marker in text for marker in import_markers):
            found.append(rel)
    return tuple(found)


def _expected_canonical_test_owner(prod_path: str) -> str | None:
    if prod_path in CANONICAL_STRATEGY_REGIME_TEST_OWNERS:
        return CANONICAL_STRATEGY_REGIME_TEST_OWNERS[prod_path]
    if not prod_path.startswith("src/"):
        return None
    rel = PurePosixPath(prod_path[len("src/") :])
    if len(rel.parts) >= 2:
        return f"tests/{rel.parent}/test_{rel.stem}.py"
    return None


def _strategy_regime_focused_targets(
    prod_path: str, test_path: str, all_files: list[str]
) -> tuple[str, ...] | None:
    if not (_is_strategy_regime_owner_prod(prod_path) and _is_canonical_test_owner(test_path)):
        return None
    expected_owner = _expected_canonical_test_owner(prod_path)
    if (
        expected_owner is None
        or test_path != expected_owner
        or not _repo_path_exists(expected_owner)
    ):
        return None
    if len([f for f in all_files if _is_strategy_regime_owner_prod(f)]) != 1:
        return None
    test_files = [f for f in all_files if _is_canonical_test_owner(f)]
    if len(test_files) != 1 or test_files[0] != test_path:
        return None
    extra = [f for f in all_files if f not in {prod_path, test_path}]
    if extra:
        return None

    targets: list[str] = []
    seen: set[str] = set()

    def add(path: str) -> None:
        if path not in seen and _validate_repo_relative_path(path) and _repo_path_exists(path):
            seen.add(path)
            targets.append(path)

    add(test_path)
    for load_test in _discover_load_strategy_contract_tests(prod_path):
        add(load_test)
    if not targets:
        return None
    return tuple(sorted(targets))


def _try_strategy_regime_owner_focused(files: list[str]) -> SelectionResult | None:
    categories = {categorize(f) for f in files}
    if "ci_bootstrap_focused" in categories or "ci_mapping_change" in categories:
        return None
    if categories & FULL_CATEGORIES:
        return None
    if categories & NO_OP_CATEGORIES:
        return None

    prod_files = sorted(f for f in files if _is_strategy_regime_owner_prod(f))
    test_files = sorted(f for f in files if _is_canonical_test_owner(f))
    if len(prod_files) != 1 or len(test_files) != 1:
        return None

    other = [f for f in files if f not in prod_files and f not in test_files]
    if other:
        return None

    prod_path = prod_files[0]
    test_path = test_files[0]
    targets = _strategy_regime_focused_targets(prod_path, test_path, files)
    if not targets:
        return None

    module = _prod_path_to_import_module(prod_path)
    if not _validate_import_module(module):
        return None

    return SelectionResult(
        "FOCUSED",
        "strategy_regime_owner_focused",
        targets,
        (module,),
    )


def _focused_targets(files: list[str]) -> tuple[str, ...]:
    targets: list[str] = []
    seen: set[str] = set()

    def add(path: str) -> None:
        if path not in seen and _repo_path_exists(path):
            seen.add(path)
            targets.append(path)

    for path in files:
        if path.startswith("tests/") and path.endswith(".py"):
            add(path)
        elif path.startswith("scripts/") and path.endswith(".py"):
            script_stem = PurePosixPath(path).stem
            for candidate in (
                f"tests/scripts/test_{script_stem}_load_strategy_v1.py",
                f"tests/scripts/test_{script_stem}.py",
            ):
                add(candidate)
        elif path == ".github/workflows/ci.yml":
            add("tests/ci/test_ci_diff_aware_test_selection_v1.py")
            add("tests/ci/test_ci_static_contract_narrow_code_filter_contract_v0.py")

    if not targets and any(categorize(f) in FOCUSED_CATEGORIES for f in files):
        add("tests/ci/test_ci_diff_aware_test_selection_v1.py")
    return tuple(sorted(targets))


def resolve_selection(
    files: list[str], *, force_full: bool = False, event_name: str = "pull_request"
) -> SelectionResult:
    normalized = sorted({PurePosixPath(f).as_posix() for f in files if f.strip()})
    if force_full or event_name in {"push", "merge_group", "schedule"}:
        return SelectionResult("FULL", "force_full_or_non_pr_event", ())
    if not normalized:
        return SelectionResult("FULL", "empty_diff_fail_closed", ())

    market_dashboard = _try_market_dashboard_focused(normalized)
    if market_dashboard is not None:
        return market_dashboard

    master_v2_binding = _try_master_v2_binding_contract_focused(normalized)
    if master_v2_binding is not None:
        return master_v2_binding

    master_v2_replay_display_projection = (
        _try_master_v2_replay_display_projection_digest_completion_evidence_focused(normalized)
    )
    if master_v2_replay_display_projection is not None:
        return master_v2_replay_display_projection

    offline_master_v2_replay_six_node = (
        _try_offline_master_v2_replay_six_node_validation_graph_binding_focused(normalized)
    )
    if offline_master_v2_replay_six_node is not None:
        return offline_master_v2_replay_six_node

    bounded_testnet_runtime_producer = (
        _try_bounded_testnet_runtime_market_observation_producer_focused(normalized)
    )
    if bounded_testnet_runtime_producer is not None:
        return bounded_testnet_runtime_producer

    bounded_testnet_closeout_binding = (
        _try_bounded_testnet_execute_path_market_observation_closeout_binding_focused(normalized)
    )
    if bounded_testnet_closeout_binding is not None:
        return bounded_testnet_closeout_binding

    bounded_testnet_market_input = _try_bounded_testnet_market_input_admission_wiring_focused(
        normalized
    )
    if bounded_testnet_market_input is not None:
        return bounded_testnet_market_input

    bounded_master_v2_testnet_wiring = (
        _try_bounded_master_v2_testnet_completion_path_wiring_focused(normalized)
    )
    if bounded_master_v2_testnet_wiring is not None:
        return bounded_master_v2_testnet_wiring

    offline_master_v2_replay = _try_offline_master_v2_double_play_scenario_replay_focused(
        normalized
    )
    if offline_master_v2_replay is not None:
        return offline_master_v2_replay

    durable_completion = _try_durable_completion_focused(normalized)
    if durable_completion is not None:
        return durable_completion

    preflight_assembly = _try_preflight_assembly_focused(normalized)
    if preflight_assembly is not None:
        return preflight_assembly

    risk_killswitch = _try_risk_killswitch_focused(normalized)
    if risk_killswitch is not None:
        return risk_killswitch

    tiny_order = _try_tiny_order_focused(normalized)
    if tiny_order is not None:
        return tiny_order

    reconciliation_primary_evidence = _try_reconciliation_primary_evidence_focused(normalized)
    if reconciliation_primary_evidence is not None:
        return reconciliation_primary_evidence

    bounded_network_testnet_preflight = _try_bounded_network_testnet_preflight_focused(normalized)
    if bounded_network_testnet_preflight is not None:
        return bounded_network_testnet_preflight

    runtime_wallclock_evidence_emitter = _try_runtime_wallclock_evidence_emitter_focused(normalized)
    if runtime_wallclock_evidence_emitter is not None:
        return runtime_wallclock_evidence_emitter

    wallclock_field_name_paired_rewire = _try_wallclock_field_name_paired_rewire(normalized)
    if wallclock_field_name_paired_rewire is not None:
        return wallclock_field_name_paired_rewire

    testnet_wallclock_duration_evidence = _try_testnet_wallclock_duration_evidence_focused(
        normalized
    )
    if testnet_wallclock_duration_evidence is not None:
        return testnet_wallclock_duration_evidence

    wallclock = _try_wallclock_focused(normalized)
    if wallclock is not None:
        return wallclock

    ci_bootstrap = _try_ci_bootstrap_focused(normalized)
    if ci_bootstrap is not None:
        return ci_bootstrap

    ci_infra = _try_ci_infra_focused(normalized)
    if ci_infra is not None:
        return ci_infra

    if any(_is_durable_completion_scoped_path(f) for f in normalized):
        if not all(_is_durable_completion_rebundle_path(f) for f in normalized):
            return SelectionResult("FULL", "durable_completion_foreign_path_requires_full", ())
        return SelectionResult("FULL", "durable_completion_incomplete_or_missing_test_owner", ())

    if any(_is_preflight_assembly_scoped_path(f) for f in normalized):
        if not all(_is_preflight_assembly_rebundle_path(f) for f in normalized):
            return SelectionResult("FULL", "preflight_assembly_foreign_path_requires_full", ())
        return SelectionResult("FULL", "preflight_assembly_incomplete_or_missing_test_owner", ())

    if any(_is_risk_killswitch_scoped_path(f) for f in normalized):
        if not all(_is_risk_killswitch_rebundle_path(f) for f in normalized):
            return SelectionResult("FULL", "risk_killswitch_foreign_path_requires_full", ())
        return SelectionResult("FULL", "risk_killswitch_incomplete_or_missing_test_owner", ())

    if any(_is_tiny_order_scoped_path(f) for f in normalized):
        if not all(_is_tiny_order_rebundle_path(f) for f in normalized):
            return SelectionResult("FULL", "tiny_order_foreign_path_requires_full", ())
        return SelectionResult("FULL", "tiny_order_incomplete_or_missing_test_owner", ())

    if any(_is_reconciliation_primary_evidence_scoped_path(f) for f in normalized):
        if not all(_is_reconciliation_primary_evidence_rebundle_path(f) for f in normalized):
            return SelectionResult(
                "FULL", "reconciliation_primary_evidence_foreign_path_requires_full", ()
            )
        return SelectionResult(
            "FULL", "reconciliation_primary_evidence_incomplete_or_missing_test_owner", ()
        )

    if any(_is_bounded_network_testnet_preflight_scoped_path(f) for f in normalized):
        if not all(_is_bounded_network_testnet_preflight_rebundle_path(f) for f in normalized):
            return SelectionResult(
                "FULL",
                "bounded_network_testnet_preflight_foreign_path_requires_full",
                (),
            )
        return SelectionResult(
            "FULL",
            "bounded_network_testnet_preflight_incomplete_or_missing_test_owner",
            (),
        )

    if any(_is_runtime_wallclock_evidence_emitter_scoped_path(f) for f in normalized):
        if not all(_is_runtime_wallclock_evidence_emitter_rebundle_path(f) for f in normalized):
            return SelectionResult(
                "FULL",
                "runtime_wallclock_evidence_emitter_foreign_path_requires_full",
                (),
            )
        return SelectionResult(
            "FULL",
            "runtime_wallclock_evidence_emitter_incomplete_or_missing_test_owner",
            (),
        )

    if any(_is_testnet_wallclock_duration_evidence_scoped_path(f) for f in normalized):
        if not all(_is_testnet_wallclock_duration_evidence_rebundle_path(f) for f in normalized):
            return SelectionResult(
                "FULL",
                "testnet_wallclock_duration_evidence_foreign_path_requires_full",
                (),
            )
        return SelectionResult(
            "FULL",
            "testnet_wallclock_duration_evidence_incomplete_or_missing_test_owner",
            (),
        )

    if any(_is_wallclock_scoped_path(f) for f in normalized):
        if not all(_is_wallclock_rebundle_path(f) for f in normalized):
            return SelectionResult("FULL", "wallclock_foreign_path_requires_full", ())
        return SelectionResult("FULL", "wallclock_incomplete_or_missing_test_owner", ())

    if any(_is_ci_bootstrap_scoped_path(f) for f in normalized):
        return SelectionResult("FULL", "ci_bootstrap_mixed_diff_requires_full", ())

    if any(_is_ci_infra_scoped_path(f) for f in normalized) and _has_ci_infra_substantive_intent(
        normalized
    ):
        if not all(_is_ci_infra_rebundle_path(f) for f in normalized):
            return SelectionResult("FULL", "ci_infra_foreign_path_requires_full", ())
        return SelectionResult("FULL", "ci_infra_incomplete_or_ambiguous", ())

    if _requires_full_ci_selector_change(normalized):
        return SelectionResult("FULL", "ci_mapping_or_workflow_selector_change_requires_full", ())

    categories = {categorize(f) for f in normalized}

    if "ci_mapping_change" in categories:
        return SelectionResult("FULL", "category_ci_mapping_change_requires_full", ())

    if categories & FULL_CATEGORIES:
        hit = sorted(categories & FULL_CATEGORIES)[0]
        return SelectionResult("FULL", f"category_{hit}_requires_full", ())

    if categories <= NO_OP_CATEGORIES:
        if _has_productive_src_python(normalized):
            return SelectionResult("FULL", "productive_src_no_op_blocked_fail_closed", ())
        return SelectionResult("NO_OP", "docs_workflow_or_static_contract_only", ())

    strategy_focused = _try_strategy_regime_owner_focused(normalized)
    if strategy_focused is not None:
        return strategy_focused

    if "strategy_regime_owner_focused" in categories:
        return SelectionResult("FULL", "strategy_regime_owner_incomplete_or_ambiguous", ())

    if categories <= (NO_OP_CATEGORIES | FOCUSED_CATEGORIES):
        return SelectionResult(
            "FOCUSED",
            "focused_script_or_test_diff",
            _focused_targets(normalized),
        )

    return SelectionResult("FULL", "mixed_or_unclassified_fail_closed", ())


def emit_validated_pytest_targets(raw: str) -> int:
    for part in raw.split():
        if not _validate_pytest_target(part) or not _repo_pytest_target_exists(part):
            print(f"invalid pytest target: {part!r}", file=sys.stderr)
            return 1
        print(part)
    return 0


def run_import_smoke(modules: str) -> int:
    import importlib

    repo_root = Path(__file__).resolve().parents[2]
    root_str = str(repo_root)
    if root_str not in sys.path:
        sys.path.insert(0, root_str)

    for part in modules.split():
        if not _validate_import_module(part):
            print(f"invalid import module: {part!r}", file=sys.stderr)
            return 1
        importlib.import_module(part)
        print(f"import smoke ok: {part}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="CI diff-aware test selection v1")
    parser.add_argument("--files", nargs="*", default=None, help="Changed file paths")
    parser.add_argument("--files-file", type=Path, default=None)
    parser.add_argument("--force-full", action="store_true")
    parser.add_argument("--event-name", default=os.environ.get("GITHUB_EVENT_NAME", "pull_request"))
    parser.add_argument("--github-output", action="store_true")
    parser.add_argument(
        "--emit-validated-pytest-targets",
        metavar="TARGETS",
        help="Print validated repo-relative pytest paths (one per line)",
    )
    parser.add_argument(
        "--import-smoke-modules",
        metavar="MODULES",
        help="Import listed Python modules (space-separated)",
    )
    args = parser.parse_args(argv)

    if args.emit_validated_pytest_targets is not None:
        return emit_validated_pytest_targets(args.emit_validated_pytest_targets)

    if args.import_smoke_modules is not None:
        return run_import_smoke(args.import_smoke_modules)

    files: list[str] = []
    if args.files_file and args.files_file.exists():
        files = [
            ln.strip()
            for ln in args.files_file.read_text(encoding="utf-8").splitlines()
            if ln.strip()
        ]
    elif args.files is not None:
        files = list(args.files)
    else:
        raw = os.environ.get("CHANGED_FILES", "")
        files = [ln.strip() for ln in raw.splitlines() if ln.strip()]

    result = resolve_selection(files, force_full=args.force_full, event_name=args.event_name)
    lines = result.github_output_lines()
    if args.github_output:
        out_path = os.environ.get("GITHUB_OUTPUT")
        if out_path:
            with open(out_path, "a", encoding="utf-8") as fh:
                fh.write("\n".join(lines) + "\n")
        else:
            print("\n".join(lines))
    else:
        print("\n".join(lines))
    return 0


if __name__ == "__main__":
    sys.exit(main())
