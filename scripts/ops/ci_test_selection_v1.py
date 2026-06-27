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
        "okx_europe_adapter_lifecycle_focused",
        "bounded_futures_testnet_contract_focused",
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

# Bounded canonical CI bootstrap selector + partition helper + contract-test owner (self-FOCUSED).
DURABLE_COMPLETION_INTEGRATION_PARTITIONS_HELPER = (
    "scripts/ops/durable_completion_integration_partitions_v0.py"
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

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from scripts.ops.durable_completion_integration_partitions_v0 import (  # noqa: E402
    CI_GLB019_SYNTHETIC_PATCH_BUILDER,
    CORE_ALWAYS_PARTITIONS,
    GLB019_A2B_ALLOWED_FILES,
    PE33_EXHAUSTIVE_OWNER,
    PE33_PR_SMOKE_NODE_IDS,
    INTEGRATION_TEST_OWNER,
    Glb019A2bChangeContractOutcome,
    Glb019A2bChangeContractResult,
    classify_glb019_a2b_additive_patch,
    collect_glb019_a2b_patch_text,
    evaluate_glb019_a2b_change_contract,
    expand_partitions_to_pytest_targets,
    expand_pe33_pr_smoke_pytest_targets,
    expand_pe31_durable_completion_binding_graph_pytest_targets,
    expand_pe31_durable_completion_binding_integration_pytest_targets,
    integration_owner_node_count,
    integration_partition_inventory,
    is_glb019_a2b_structural_contract_candidate,
    partition_union_node_count,
    partitions_for_changed_files,
    patch_includes_glb019_guarded_selector_owner_rewire,
)

CI_BOOTSTRAP_FOCUSED_PATHS = frozenset(
    {
        "scripts/ops/ci_test_selection_v1.py",
        DURABLE_COMPLETION_INTEGRATION_PARTITIONS_HELPER,
        "tests/ci/test_ci_diff_aware_test_selection_v1.py",
        CI_GLB019_SYNTHETIC_PATCH_BUILDER,
    }
)

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

DURABLE_COMPLETION_VALIDATION_GRAPH_TEST_OWNER = (
    "tests/ops/test_durable_completion_validation_graph_v1.py"
)
DURABLE_COMPLETION_INTEGRATION_TEST_OWNER = "tests/ops/test_bounded_futures_testnet_durable_run_primary_evidence_completion_integration_contract_v0.py"
DURABLE_COMPLETION_GRAPH_WIRING_PATH = "src/ops/durable_completion_validation/graph.py"
DURABLE_COMPLETION_PUBLIC_API_PATH = "src/ops/durable_completion_validation/__init__.py"

GLB019_A2B_SELECTOR_OWNER = "scripts/ops/ci_test_selection_v1.py"

GLB019_A2B_CLOSED_FILESET = GLB019_A2B_ALLOWED_FILES

GLB019_A2B_PROD_RELEVANT_FILES = frozenset(
    {
        DURABLE_COMPLETION_FACADE_PATH,
        DURABLE_COMPLETION_INTEGRATION_TEST_OWNER,
        DURABLE_COMPLETION_GRAPH_WIRING_PATH,
        "src/ops/durable_completion_validation/validators/event_stream.py",
        DURABLE_COMPLETION_VALIDATION_GRAPH_TEST_OWNER,
    }
)

GLB019_A2B_BOOTSTRAP_ONLY_FILES = frozenset(
    {
        DURABLE_COMPLETION_INTEGRATION_PARTITIONS_HELPER,
        "tests/ci/test_ci_diff_aware_test_selection_v1.py",
    }
)

CANONICAL_DURABLE_COMPLETION_FOCUSED_TESTS: tuple[str, ...] = (
    DURABLE_COMPLETION_VALIDATION_GRAPH_TEST_OWNER,
    DURABLE_COMPLETION_INTEGRATION_TEST_OWNER,
    "tests/ci/test_ci_diff_aware_test_selection_v1.py",
)

CANONICAL_DURABLE_COMPLETION_VALIDATION_GRAPH_FOCUSED_TESTS: tuple[str, ...] = (
    DURABLE_COMPLETION_VALIDATION_GRAPH_TEST_OWNER,
    "tests/ci/test_ci_diff_aware_test_selection_v1.py",
)

REQUIRED_DURABLE_COMPLETION_TEST_OWNERS: tuple[str, ...] = (
    DURABLE_COMPLETION_VALIDATION_GRAPH_TEST_OWNER,
    DURABLE_COMPLETION_INTEGRATION_TEST_OWNER,
)

DURABLE_COMPLETION_INTEGRATION_PE_PROD_PATHS = frozenset(
    {
        "src/ops/bounded_futures_testnet_position_order_reconciliation_primary_evidence_integration_contract_v0.py",
        "src/ops/bounded_futures_testnet_reconciliation_review_lifecycle_integration_contract_v0.py",
        "src/ops/bounded_futures_testnet_risk_killswitch_lifecycle_integration_contract_v0.py",
        "src/ops/bounded_futures_testnet_capital_slot_ratchet_release_lifecycle_integration_contract_v0.py",
        "src/ops/bounded_futures_testnet_pilot_envelope_lifecycle_integration_contract_v0.py",
        "src/ops/bounded_futures_testnet_operator_closure_lifecycle_integration_contract_v0.py",
        "src/ops/bounded_futures_testnet_handoff_staleness_revocation_recovery_boundary_contract_v0.py",
        "src/ops/bounded_futures_testnet_operator_review_handoff_boundary_contract_v0.py",
        "src/ops/bounded_futures_testnet_operator_review_admission_presentation_boundary_contract_v0.py",
        "src/ops/bounded_futures_testnet_operator_review_admission_presentation_lifecycle_integration_contract_v0.py",
        "src/ops/bounded_futures_testnet_operator_review_chain_durable_evidence_traceability_boundary_contract_v0.py",
        "src/ops/bounded_futures_testnet_preflight_execution_readiness_review_lifecycle_integration_contract_v0.py",
        "src/ops/bounded_futures_testnet_cross_slice_proof_coherence_integration_contract_v0.py",
        "src/ops/testnet_wallclock_duration_evidence_contract_v0.py",
        "src/ops/wallclock_session_evidence_v0.py",
    }
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

DURABLE_COMPLETION_COMPLETION_INTEGRATION_TEST_OWNER = DURABLE_COMPLETION_INTEGRATION_TEST_OWNER

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
    f"{BOUNDED_MASTER_V2_TESTNET_COMPLETION_PATH_WIRING_ADAPTER_TEST_OWNER}::test_adapter_plan_wiring_exposes_replay_proof_classification_fields",
    f"{BOUNDED_MASTER_V2_TESTNET_COMPLETION_PATH_WIRING_ADAPTER_TEST_OWNER}::test_adapter_replay_proof_classification_plan_execute_closeout_parity",
    f"{BOUNDED_MASTER_V2_TESTNET_COMPLETION_PATH_WIRING_ADAPTER_TEST_OWNER}::test_adapter_replay_proof_classification_preserves_non_authorizing_boundaries",
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
BOUNDED_MASTER_V2_TESTNET_COMPLETION_PATH_WIRING_CONTRACT_FOCUSED_NODES: tuple[str, ...] = (
    f"{BOUNDED_MASTER_V2_TESTNET_COMPLETION_PATH_WIRING_TEST_OWNER}::test_wiring_owner_references_replay_proof_classification_symbols",
    f"{BOUNDED_MASTER_V2_TESTNET_COMPLETION_PATH_WIRING_TEST_OWNER}::test_full_e2e_bound_classification_bound_with_valid_market_input",
    f"{BOUNDED_MASTER_V2_TESTNET_COMPLETION_PATH_WIRING_TEST_OWNER}::test_partial_replay_proof_classification_fails_closed",
    f"{BOUNDED_MASTER_V2_TESTNET_COMPLETION_PATH_WIRING_TEST_OWNER}::test_missing_replay_proof_classification_fails_closed",
    f"{BOUNDED_MASTER_V2_TESTNET_COMPLETION_PATH_WIRING_TEST_OWNER}::test_unknown_replay_proof_classification_fails_closed",
    f"{BOUNDED_MASTER_V2_TESTNET_COMPLETION_PATH_WIRING_TEST_OWNER}::test_replay_proof_identity_drift_fails_closed",
    f"{BOUNDED_MASTER_V2_TESTNET_COMPLETION_PATH_WIRING_TEST_OWNER}::test_invalid_replay_proof_classification_fails_closed_in_evaluator",
)
BOUNDED_MASTER_V2_TESTNET_COMPLETION_PATH_WIRING_FOCUSED_TARGETS: tuple[str, ...] = (
    *BOUNDED_MASTER_V2_TESTNET_COMPLETION_PATH_WIRING_CONTRACT_FOCUSED_NODES,
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

MASTER_V2_ARITHMETIC_KERNEL_SEAM_FAIL_CLOSED_CONTRACT_TEST_OWNER = (
    "tests/ops/test_master_v2_arithmetic_kernel_seam_fail_closed_contract_v0.py"
)

MASTER_V2_ARITHMETIC_KERNEL_SEAM_FAIL_CLOSED_CONTRACT_CI_POLICY_PATHS = frozenset(
    {
        "scripts/ops/ci_test_selection_v1.py",
        "tests/ci/test_ci_diff_aware_test_selection_v1.py",
    }
)

MASTER_V2_ARITHMETIC_KERNEL_SEAM_FAIL_CLOSED_CONTRACT_SCOPED_PATHS = frozenset(
    {
        MASTER_V2_ARITHMETIC_KERNEL_SEAM_FAIL_CLOSED_CONTRACT_TEST_OWNER,
        *MASTER_V2_ARITHMETIC_KERNEL_SEAM_FAIL_CLOSED_CONTRACT_CI_POLICY_PATHS,
    }
)

MASTER_V2_ARITHMETIC_KERNEL_SEAM_FAIL_CLOSED_CONTRACT_FOCUSED_NODES: tuple[str, ...] = (
    f"{MASTER_V2_ARITHMETIC_KERNEL_SEAM_FAIL_CLOSED_CONTRACT_TEST_OWNER}::test_canonical_futures_accounting_kernel_identity_and_decimal_semantics",
    f"{MASTER_V2_ARITHMETIC_KERNEL_SEAM_FAIL_CLOSED_CONTRACT_TEST_OWNER}::test_master_v2_completion_adapter_replay_paths_unwired_from_futures_accounting",
    f"{MASTER_V2_ARITHMETIC_KERNEL_SEAM_FAIL_CLOSED_CONTRACT_TEST_OWNER}::test_completion_and_adapter_machine_summary_forbids_trading_arithmetic_proven_claims",
    f"{MASTER_V2_ARITHMETIC_KERNEL_SEAM_FAIL_CLOSED_CONTRACT_TEST_OWNER}::test_zero_order_lifecycle_and_classification_do_not_imply_arithmetic_evidence",
    f"{MASTER_V2_ARITHMETIC_KERNEL_SEAM_FAIL_CLOSED_CONTRACT_TEST_OWNER}::test_contract_is_non_authorizing",
    f"{MASTER_V2_ARITHMETIC_KERNEL_SEAM_FAIL_CLOSED_CONTRACT_TEST_OWNER}::test_future_seam_must_reuse_decimal_kernel_without_formula_duplication",
)

MASTER_V2_ARITHMETIC_KERNEL_SEAM_FAIL_CLOSED_CONTRACT_CI_SELECTOR_TARGETS: tuple[str, ...] = (
    "tests/ci/test_ci_diff_aware_test_selection_v1.py::test_selector_master_v2_arithmetic_kernel_seam_fail_closed_contract_test_only_focused",
    "tests/ci/test_ci_diff_aware_test_selection_v1.py::test_selector_master_v2_arithmetic_kernel_seam_fail_closed_contract_foreign_path_escalates_full",
)

DUPLICATE_PNL_OWNER_BOUNDARY_CONTRACT_TEST_OWNER = (
    "tests/ops/test_duplicate_pnl_owner_boundary_contract_v0.py"
)

DUPLICATE_PNL_OWNER_BOUNDARY_CONTRACT_CI_POLICY_PATHS = frozenset(
    {
        "scripts/ops/ci_test_selection_v1.py",
        "tests/ci/test_ci_diff_aware_test_selection_v1.py",
    }
)

DUPLICATE_PNL_OWNER_BOUNDARY_CONTRACT_SCOPED_PATHS = frozenset(
    {
        DUPLICATE_PNL_OWNER_BOUNDARY_CONTRACT_TEST_OWNER,
        *DUPLICATE_PNL_OWNER_BOUNDARY_CONTRACT_CI_POLICY_PATHS,
    }
)

DUPLICATE_PNL_OWNER_BOUNDARY_CONTRACT_FOCUSED_NODES: tuple[str, ...] = (
    f"{DUPLICATE_PNL_OWNER_BOUNDARY_CONTRACT_TEST_OWNER}::test_pnl_owner_inventory_complete_and_roles_unique",
    f"{DUPLICATE_PNL_OWNER_BOUNDARY_CONTRACT_TEST_OWNER}::test_exactly_one_futures_arithmetic_kernel_candidate",
    f"{DUPLICATE_PNL_OWNER_BOUNDARY_CONTRACT_TEST_OWNER}::test_local_pnl_owners_retain_local_scope_not_global_ssot",
    f"{DUPLICATE_PNL_OWNER_BOUNDARY_CONTRACT_TEST_OWNER}::test_master_v2_and_completion_adapter_paths_import_no_alternative_pnl_owner",
    f"{DUPLICATE_PNL_OWNER_BOUNDARY_CONTRACT_TEST_OWNER}::test_contract_defines_no_pnl_fee_funding_formulas",
    f"{DUPLICATE_PNL_OWNER_BOUNDARY_CONTRACT_TEST_OWNER}::test_contract_is_non_authorizing",
)

DUPLICATE_PNL_OWNER_BOUNDARY_CONTRACT_CI_SELECTOR_TARGETS: tuple[str, ...] = (
    "tests/ci/test_ci_diff_aware_test_selection_v1.py::test_selector_duplicate_pnl_owner_boundary_contract_test_only_focused",
    "tests/ci/test_ci_diff_aware_test_selection_v1.py::test_selector_duplicate_pnl_owner_boundary_contract_foreign_path_escalates_full",
)

RECONCILIATION_DECIMAL_FLOAT_OWNER_BOUNDARY_CONTRACT_TEST_OWNER = (
    "tests/ops/test_reconciliation_decimal_float_owner_boundary_contract_v0.py"
)

RECONCILIATION_DECIMAL_FLOAT_OWNER_BOUNDARY_CONTRACT_CI_POLICY_PATHS = frozenset(
    {
        "scripts/ops/ci_test_selection_v1.py",
        "tests/ci/test_ci_diff_aware_test_selection_v1.py",
    }
)

RECONCILIATION_DECIMAL_FLOAT_OWNER_BOUNDARY_CONTRACT_SCOPED_PATHS = frozenset(
    {
        RECONCILIATION_DECIMAL_FLOAT_OWNER_BOUNDARY_CONTRACT_TEST_OWNER,
        *RECONCILIATION_DECIMAL_FLOAT_OWNER_BOUNDARY_CONTRACT_CI_POLICY_PATHS,
    }
)

RECONCILIATION_DECIMAL_FLOAT_OWNER_BOUNDARY_CONTRACT_FOCUSED_NODES: tuple[str, ...] = (
    f"{RECONCILIATION_DECIMAL_FLOAT_OWNER_BOUNDARY_CONTRACT_TEST_OWNER}::test_reconciliation_owner_inventory_complete_and_roles_unique",
    f"{RECONCILIATION_DECIMAL_FLOAT_OWNER_BOUNDARY_CONTRACT_TEST_OWNER}::test_exactly_one_execution_decimal_reconciliation_candidate",
    f"{RECONCILIATION_DECIMAL_FLOAT_OWNER_BOUNDARY_CONTRACT_TEST_OWNER}::test_ops_float_reconciliation_owner_remains_locally_bounded",
    f"{RECONCILIATION_DECIMAL_FLOAT_OWNER_BOUNDARY_CONTRACT_TEST_OWNER}::test_decimal_float_boundary_explicit_not_interchangeable",
    f"{RECONCILIATION_DECIMAL_FLOAT_OWNER_BOUNDARY_CONTRACT_TEST_OWNER}::test_absolute_and_relative_tolerance_semantics_not_interchangeable",
    f"{RECONCILIATION_DECIMAL_FLOAT_OWNER_BOUNDARY_CONTRACT_TEST_OWNER}::test_master_v2_completion_adapter_paths_import_no_operative_reconciliation_owner",
    f"{RECONCILIATION_DECIMAL_FLOAT_OWNER_BOUNDARY_CONTRACT_TEST_OWNER}::test_contract_defines_no_reconciliation_formulas_and_is_non_authorizing",
)

RECONCILIATION_DECIMAL_FLOAT_OWNER_BOUNDARY_CONTRACT_CI_SELECTOR_TARGETS: tuple[str, ...] = (
    "tests/ci/test_ci_diff_aware_test_selection_v1.py::test_selector_reconciliation_decimal_float_owner_boundary_contract_test_only_focused",
    "tests/ci/test_ci_diff_aware_test_selection_v1.py::test_selector_reconciliation_decimal_float_owner_boundary_contract_foreign_path_escalates_full",
)

DYNAMIC_SCOPE_OWNER_BOUNDARY_CONTRACT_TEST_OWNER = (
    "tests/ops/test_master_v2_dynamic_scope_owner_boundary_contract_v0.py"
)

DYNAMIC_SCOPE_OWNER_BOUNDARY_CONTRACT_CI_POLICY_PATHS = frozenset(
    {
        "scripts/ops/ci_test_selection_v1.py",
        "tests/ci/test_ci_diff_aware_test_selection_v1.py",
    }
)

DYNAMIC_SCOPE_OWNER_BOUNDARY_CONTRACT_SCOPED_PATHS = frozenset(
    {
        DYNAMIC_SCOPE_OWNER_BOUNDARY_CONTRACT_TEST_OWNER,
        *DYNAMIC_SCOPE_OWNER_BOUNDARY_CONTRACT_CI_POLICY_PATHS,
    }
)

DYNAMIC_SCOPE_OWNER_BOUNDARY_CONTRACT_FOCUSED_NODES: tuple[str, ...] = (
    f"{DYNAMIC_SCOPE_OWNER_BOUNDARY_CONTRACT_TEST_OWNER}::test_dynamic_scope_owner_inventory_complete_and_roles_unique",
    f"{DYNAMIC_SCOPE_OWNER_BOUNDARY_CONTRACT_TEST_OWNER}::test_exactly_one_dynamic_scope_pure_model_candidate",
    f"{DYNAMIC_SCOPE_OWNER_BOUNDARY_CONTRACT_TEST_OWNER}::test_local_consumers_remain_bounded_not_operative_ssot",
    f"{DYNAMIC_SCOPE_OWNER_BOUNDARY_CONTRACT_TEST_OWNER}::test_master_v2_completion_adapter_paths_import_no_parallel_dynamic_scope_owner",
    f"{DYNAMIC_SCOPE_OWNER_BOUNDARY_CONTRACT_TEST_OWNER}::test_contract_crosslinks_dse_static_markers_without_redefinition",
    f"{DYNAMIC_SCOPE_OWNER_BOUNDARY_CONTRACT_TEST_OWNER}::test_contract_defines_no_dynamic_scope_formulas_and_is_non_authorizing",
    f"{DYNAMIC_SCOPE_OWNER_BOUNDARY_CONTRACT_TEST_OWNER}::test_forbidden_authority_and_repair_claim_keys_absent",
)

DYNAMIC_SCOPE_OWNER_BOUNDARY_CONTRACT_CI_SELECTOR_TARGETS: tuple[str, ...] = (
    "tests/ci/test_ci_diff_aware_test_selection_v1.py::test_selector_dynamic_scope_owner_boundary_contract_test_only_focused",
    "tests/ci/test_ci_diff_aware_test_selection_v1.py::test_selector_dynamic_scope_owner_boundary_contract_foreign_path_escalates_full",
)

STATE_SWITCH_OWNER_BOUNDARY_CONTRACT_TEST_OWNER = (
    "tests/ops/test_master_v2_state_switch_owner_boundary_contract_v0.py"
)

STATE_SWITCH_OWNER_BOUNDARY_CONTRACT_CI_POLICY_PATHS = frozenset(
    {
        "scripts/ops/ci_test_selection_v1.py",
        "tests/ci/test_ci_diff_aware_test_selection_v1.py",
    }
)

STATE_SWITCH_OWNER_BOUNDARY_CONTRACT_SCOPED_PATHS = frozenset(
    {
        STATE_SWITCH_OWNER_BOUNDARY_CONTRACT_TEST_OWNER,
        *STATE_SWITCH_OWNER_BOUNDARY_CONTRACT_CI_POLICY_PATHS,
    }
)

STATE_SWITCH_OWNER_BOUNDARY_CONTRACT_FOCUSED_NODES: tuple[str, ...] = (
    f"{STATE_SWITCH_OWNER_BOUNDARY_CONTRACT_TEST_OWNER}::test_state_switch_owner_inventory_complete_and_roles_unique",
    f"{STATE_SWITCH_OWNER_BOUNDARY_CONTRACT_TEST_OWNER}::test_exactly_one_state_switch_pure_model_candidate",
    f"{STATE_SWITCH_OWNER_BOUNDARY_CONTRACT_TEST_OWNER}::test_local_consumers_remain_bounded_not_operative_ssot",
    f"{STATE_SWITCH_OWNER_BOUNDARY_CONTRACT_TEST_OWNER}::test_master_v2_completion_adapter_paths_import_no_parallel_state_switch_owner",
    f"{STATE_SWITCH_OWNER_BOUNDARY_CONTRACT_TEST_OWNER}::test_contract_crosslinks_ss_static_markers_without_redefinition",
    f"{STATE_SWITCH_OWNER_BOUNDARY_CONTRACT_TEST_OWNER}::test_contract_defines_no_state_switch_formulas_and_is_non_authorizing",
    f"{STATE_SWITCH_OWNER_BOUNDARY_CONTRACT_TEST_OWNER}::test_forbidden_authority_and_side_switch_claim_keys_absent",
)

STATE_SWITCH_OWNER_BOUNDARY_CONTRACT_CI_SELECTOR_TARGETS: tuple[str, ...] = (
    "tests/ci/test_ci_diff_aware_test_selection_v1.py::test_selector_state_switch_owner_boundary_contract_test_only_focused",
    "tests/ci/test_ci_diff_aware_test_selection_v1.py::test_selector_state_switch_owner_boundary_contract_foreign_path_escalates_full",
)

CAPITAL_SLOT_OWNER_BOUNDARY_CONTRACT_TEST_OWNER = (
    "tests/ops/test_master_v2_capital_slot_owner_boundary_contract_v0.py"
)

CAPITAL_SLOT_OWNER_BOUNDARY_CONTRACT_CI_POLICY_PATHS = frozenset(
    {
        "scripts/ops/ci_test_selection_v1.py",
        "tests/ci/test_ci_diff_aware_test_selection_v1.py",
    }
)

CAPITAL_SLOT_OWNER_BOUNDARY_CONTRACT_SCOPED_PATHS = frozenset(
    {
        CAPITAL_SLOT_OWNER_BOUNDARY_CONTRACT_TEST_OWNER,
        *CAPITAL_SLOT_OWNER_BOUNDARY_CONTRACT_CI_POLICY_PATHS,
    }
)

CAPITAL_SLOT_OWNER_BOUNDARY_CONTRACT_FOCUSED_NODES: tuple[str, ...] = (
    f"{CAPITAL_SLOT_OWNER_BOUNDARY_CONTRACT_TEST_OWNER}::test_capital_slot_owner_inventory_complete_and_roles_unique",
    f"{CAPITAL_SLOT_OWNER_BOUNDARY_CONTRACT_TEST_OWNER}::test_exactly_one_capital_slot_pure_model_candidate",
    f"{CAPITAL_SLOT_OWNER_BOUNDARY_CONTRACT_TEST_OWNER}::test_local_consumers_remain_bounded_not_operative_ssot",
    f"{CAPITAL_SLOT_OWNER_BOUNDARY_CONTRACT_TEST_OWNER}::test_master_v2_completion_adapter_paths_import_no_parallel_capital_slot_owner",
    f"{CAPITAL_SLOT_OWNER_BOUNDARY_CONTRACT_TEST_OWNER}::test_contract_crosslinks_csr_static_markers_without_redefinition",
    f"{CAPITAL_SLOT_OWNER_BOUNDARY_CONTRACT_TEST_OWNER}::test_contract_defines_no_capital_slot_formulas_and_is_non_authorizing",
    f"{CAPITAL_SLOT_OWNER_BOUNDARY_CONTRACT_TEST_OWNER}::test_forbidden_authority_and_ratchet_claim_keys_absent",
)

CAPITAL_SLOT_OWNER_BOUNDARY_CONTRACT_CI_SELECTOR_TARGETS: tuple[str, ...] = (
    "tests/ci/test_ci_diff_aware_test_selection_v1.py::test_selector_capital_slot_owner_boundary_contract_test_only_focused",
    "tests/ci/test_ci_diff_aware_test_selection_v1.py::test_selector_capital_slot_owner_boundary_contract_foreign_path_escalates_full",
)

PE22_DURABLE_COMPLETION_BINDING_CONTRACT_TEST_OWNER = (
    "tests/ops/test_pe22_durable_completion_binding_contract_v0.py"
)

PE22_DURABLE_COMPLETION_BINDING_CI_POLICY_PATHS = frozenset(
    {
        "scripts/ops/ci_test_selection_v1.py",
        "tests/ci/test_ci_diff_aware_test_selection_v1.py",
    }
)

PE22_DURABLE_COMPLETION_BINDING_SCOPED_PATHS = frozenset(
    {
        PE22_DURABLE_COMPLETION_BINDING_CONTRACT_TEST_OWNER,
        *PE22_DURABLE_COMPLETION_BINDING_CI_POLICY_PATHS,
    }
)

PE22_DURABLE_COMPLETION_BINDING_FOCUSED_NODES: tuple[str, ...] = (
    f"{PE22_DURABLE_COMPLETION_BINDING_CONTRACT_TEST_OWNER}::test_pe22_durable_completion_binding_package_marker_present",
    f"{PE22_DURABLE_COMPLETION_BINDING_CONTRACT_TEST_OWNER}::test_pe22_durable_completion_canonical_binding_registry_complete",
    f"{PE22_DURABLE_COMPLETION_BINDING_CONTRACT_TEST_OWNER}::test_pe22_durable_completion_registry_upstream_owner_matches_pe22_contract",
    f"{PE22_DURABLE_COMPLETION_BINDING_CONTRACT_TEST_OWNER}::test_pe22_durable_completion_dependency_direction_is_downstream_only",
    f"{PE22_DURABLE_COMPLETION_BINDING_CONTRACT_TEST_OWNER}::test_pe22_durable_completion_sole_canonical_upstream_module_in_completion_facade",
    f"{PE22_DURABLE_COMPLETION_BINDING_CONTRACT_TEST_OWNER}::test_pe22_durable_completion_completion_chain_validator_imports_canonical_pe22_owner_only",
    f"{PE22_DURABLE_COMPLETION_BINDING_CONTRACT_TEST_OWNER}::test_pe22_durable_completion_binding_authority_neutral_on_happy_path",
    f"{PE22_DURABLE_COMPLETION_BINDING_CONTRACT_TEST_OWNER}::test_pe22_source_revision_mismatch_with_completion_input_fails",
    f"{PE22_DURABLE_COMPLETION_BINDING_CONTRACT_TEST_OWNER}::test_pe22_integration_input_digest_drift_fails",
    f"{PE22_DURABLE_COMPLETION_BINDING_CONTRACT_TEST_OWNER}::test_pe22_integration_owner_mismatch_fails",
    f"{PE22_DURABLE_COMPLETION_BINDING_CONTRACT_TEST_OWNER}::test_pe22_referenced_upstream_digest_drift_in_completion_chain_fails",
    f"{PE22_DURABLE_COMPLETION_BINDING_CONTRACT_TEST_OWNER}::test_pe22_completion_binding_source_revision_consistent_on_happy_path",
    f"{PE22_DURABLE_COMPLETION_BINDING_CONTRACT_TEST_OWNER}::test_graph_pe22_canonical_binding_registry_aligns_with_integration_owner",
    f"{PE22_DURABLE_COMPLETION_BINDING_CONTRACT_TEST_OWNER}::test_graph_completion_chain_validator_imports_canonical_pe22_owner_only",
    f"{PE22_DURABLE_COMPLETION_BINDING_CONTRACT_TEST_OWNER}::test_graph_completion_chain_validator_is_canonical_pe22_binding_entrypoint",
    f"{PE22_DURABLE_COMPLETION_BINDING_CONTRACT_TEST_OWNER}::test_graph_pe22_binding_authority_neutral_on_happy_path",
    f"{PE22_DURABLE_COMPLETION_BINDING_CONTRACT_TEST_OWNER}::test_graph_pe22_source_revision_drift_fail_closed_via_completion_chain_validator",
    f"{PE22_DURABLE_COMPLETION_BINDING_CONTRACT_TEST_OWNER}::test_graph_pe22_integration_input_digest_drift_fail_closed",
    f"{PE22_DURABLE_COMPLETION_BINDING_CONTRACT_TEST_OWNER}::test_graph_pe22_referenced_proof_digest_drift_in_completion_chain_fail_closed",
    f"{PE22_DURABLE_COMPLETION_BINDING_CONTRACT_TEST_OWNER}::test_graph_pe22_completion_chain_digest_alignment_fail_closed",
)

PE22_DURABLE_COMPLETION_BINDING_CI_SELECTOR_TARGETS: tuple[str, ...] = (
    "tests/ci/test_ci_diff_aware_test_selection_v1.py::test_selector_pe22_durable_completion_binding_contract_test_only_focused",
    "tests/ci/test_ci_diff_aware_test_selection_v1.py::test_selector_pe22_durable_completion_binding_contract_foreign_path_escalates_full",
)

INV016_DURABLE_COMPLETION_BINDING_CONTRACT_TEST_OWNER = (
    "tests/ops/test_inv016_durable_completion_binding_contract_v0.py"
)

INV016_DURABLE_COMPLETION_BINDING_CI_POLICY_PATHS = frozenset(
    {
        "scripts/ops/ci_test_selection_v1.py",
        "tests/ci/test_ci_diff_aware_test_selection_v1.py",
    }
)

INV016_DURABLE_COMPLETION_BINDING_SCOPED_PATHS = frozenset(
    {
        INV016_DURABLE_COMPLETION_BINDING_CONTRACT_TEST_OWNER,
        *INV016_DURABLE_COMPLETION_BINDING_CI_POLICY_PATHS,
    }
)

INV016_DURABLE_COMPLETION_BINDING_FOCUSED_NODES: tuple[str, ...] = (
    f"{INV016_DURABLE_COMPLETION_BINDING_CONTRACT_TEST_OWNER}::test_inv016_durable_completion_binding_package_marker_present",
    f"{INV016_DURABLE_COMPLETION_BINDING_CONTRACT_TEST_OWNER}::test_inv016_durable_completion_canonical_binding_registry_complete",
    f"{INV016_DURABLE_COMPLETION_BINDING_CONTRACT_TEST_OWNER}::test_inv016_durable_completion_registry_upstream_owner_matches_inv016_contract",
    f"{INV016_DURABLE_COMPLETION_BINDING_CONTRACT_TEST_OWNER}::test_inv016_durable_completion_dependency_direction_is_downstream_only",
    f"{INV016_DURABLE_COMPLETION_BINDING_CONTRACT_TEST_OWNER}::test_inv016_durable_completion_sole_canonical_completion_facade_import_in_wiring_owner",
    f"{INV016_DURABLE_COMPLETION_BINDING_CONTRACT_TEST_OWNER}::test_inv016_durable_completion_completion_chain_validator_references_inv016_digest_fields",
    f"{INV016_DURABLE_COMPLETION_BINDING_CONTRACT_TEST_OWNER}::test_inv016_durable_completion_binding_authority_neutral_on_happy_path",
    f"{INV016_DURABLE_COMPLETION_BINDING_CONTRACT_TEST_OWNER}::test_inv016_missing_market_input_fails_closed",
    f"{INV016_DURABLE_COMPLETION_BINDING_CONTRACT_TEST_OWNER}::test_inv016_dashboard_display_projection_digest_drift_fails_closed",
    f"{INV016_DURABLE_COMPLETION_BINDING_CONTRACT_TEST_OWNER}::test_inv016_replay_proof_classification_not_full_e2e_fails_closed",
    f"{INV016_DURABLE_COMPLETION_BINDING_CONTRACT_TEST_OWNER}::test_inv016_canonical_completion_owner_reference_consistent_on_happy_path",
    f"{INV016_DURABLE_COMPLETION_BINDING_CONTRACT_TEST_OWNER}::test_graph_inv016_canonical_binding_registry_aligns_with_wiring_owner",
    f"{INV016_DURABLE_COMPLETION_BINDING_CONTRACT_TEST_OWNER}::test_graph_completion_chain_validator_imports_master_v2_digest_binding_only",
    f"{INV016_DURABLE_COMPLETION_BINDING_CONTRACT_TEST_OWNER}::test_graph_completion_chain_validator_is_canonical_inv016_binding_entrypoint",
    f"{INV016_DURABLE_COMPLETION_BINDING_CONTRACT_TEST_OWNER}::test_graph_inv016_binding_authority_neutral_on_happy_path",
    f"{INV016_DURABLE_COMPLETION_BINDING_CONTRACT_TEST_OWNER}::test_graph_inv016_dashboard_display_projection_digest_drift_fail_closed",
    f"{INV016_DURABLE_COMPLETION_BINDING_CONTRACT_TEST_OWNER}::test_graph_inv016_completion_chain_master_v2_digest_alignment_fail_closed",
    f"{INV016_DURABLE_COMPLETION_BINDING_CONTRACT_TEST_OWNER}::test_inv016_f1_contract_only_scope_without_package_f_complete",
    f"{INV016_DURABLE_COMPLETION_BINDING_CONTRACT_TEST_OWNER}::test_inv016_f2_inv017_and_inv005_runtime_parking_unchanged",
    f"{INV016_DURABLE_COMPLETION_BINDING_CONTRACT_TEST_OWNER}::test_inv016_no_runtime_network_credential_or_trading_readiness_claimed",
)

INV016_DURABLE_COMPLETION_BINDING_CI_SELECTOR_TARGETS: tuple[str, ...] = (
    "tests/ci/test_ci_diff_aware_test_selection_v1.py::test_selector_inv016_durable_completion_binding_contract_test_only_focused",
    "tests/ci/test_ci_diff_aware_test_selection_v1.py::test_selector_inv016_durable_completion_binding_contract_foreign_path_escalates_full",
)

MASTER_V2_ARITHMETIC_DECIMAL_FLOAT_CONVERSION_BOUNDARY_CONTRACT_TEST_OWNER = (
    "tests/ops/test_master_v2_arithmetic_decimal_float_conversion_boundary_contract_v0.py"
)

MASTER_V2_ARITHMETIC_DECIMAL_FLOAT_CONVERSION_BOUNDARY_CONTRACT_CI_POLICY_PATHS = frozenset(
    {
        "scripts/ops/ci_test_selection_v1.py",
        "tests/ci/test_ci_diff_aware_test_selection_v1.py",
    }
)

MASTER_V2_ARITHMETIC_DECIMAL_FLOAT_CONVERSION_BOUNDARY_CONTRACT_SCOPED_PATHS = frozenset(
    {
        MASTER_V2_ARITHMETIC_DECIMAL_FLOAT_CONVERSION_BOUNDARY_CONTRACT_TEST_OWNER,
        *MASTER_V2_ARITHMETIC_DECIMAL_FLOAT_CONVERSION_BOUNDARY_CONTRACT_CI_POLICY_PATHS,
    }
)

MASTER_V2_ARITHMETIC_DECIMAL_FLOAT_CONVERSION_BOUNDARY_CONTRACT_FOCUSED_NODES: tuple[str, ...] = (
    f"{MASTER_V2_ARITHMETIC_DECIMAL_FLOAT_CONVERSION_BOUNDARY_CONTRACT_TEST_OWNER}::test_master_v2_float_source_and_futures_kernel_decimal_target_not_interchangeable",
    f"{MASTER_V2_ARITHMETIC_DECIMAL_FLOAT_CONVERSION_BOUNDARY_CONTRACT_TEST_OWNER}::test_to_decimal_exists_but_is_not_complete_master_v2_seam_contract",
    f"{MASTER_V2_ARITHMETIC_DECIMAL_FLOAT_CONVERSION_BOUNDARY_CONTRACT_TEST_OWNER}::test_strict_decimal_quantization_owner_rejects_float_and_remains_protected",
    f"{MASTER_V2_ARITHMETIC_DECIMAL_FLOAT_CONVERSION_BOUNDARY_CONTRACT_TEST_OWNER}::test_value_boundary_matrix_complete_for_future_kernel_binding",
    f"{MASTER_V2_ARITHMETIC_DECIMAL_FLOAT_CONVERSION_BOUNDARY_CONTRACT_TEST_OWNER}::test_rounding_and_quantization_are_distinct_with_tick_lot_owners",
    f"{MASTER_V2_ARITHMETIC_DECIMAL_FLOAT_CONVERSION_BOUNDARY_CONTRACT_TEST_OWNER}::test_nan_infinity_overflow_and_special_values_require_fail_closed_wiring",
    f"{MASTER_V2_ARITHMETIC_DECIMAL_FLOAT_CONVERSION_BOUNDARY_CONTRACT_TEST_OWNER}::test_epsilon_tolerance_is_not_decimal_precision_contract",
    f"{MASTER_V2_ARITHMETIC_DECIMAL_FLOAT_CONVERSION_BOUNDARY_CONTRACT_TEST_OWNER}::test_no_current_kernel_binding_and_contract_is_non_authorizing",
)

MASTER_V2_ARITHMETIC_DECIMAL_FLOAT_CONVERSION_BOUNDARY_CONTRACT_CI_SELECTOR_TARGETS: tuple[
    str, ...
] = (
    "tests/ci/test_ci_diff_aware_test_selection_v1.py::test_selector_master_v2_arithmetic_decimal_float_conversion_boundary_contract_test_only_focused",
    "tests/ci/test_ci_diff_aware_test_selection_v1.py::test_selector_master_v2_arithmetic_decimal_float_conversion_boundary_contract_foreign_path_escalates_full",
)

MASTER_V2_ARITHMETIC_DECIMAL_FLOAT_CONVERSION_IMPLEMENTATION_PRODUCTION_PATH = (
    "src/trading/master_v2/arithmetic_decimal_float_conversion_v0.py"
)

MASTER_V2_ARITHMETIC_DECIMAL_FLOAT_CONVERSION_IMPLEMENTATION_TEST_OWNER = (
    "tests/ops/test_master_v2_arithmetic_decimal_float_conversion_implementation_v0.py"
)

MASTER_V2_ARITHMETIC_DECIMAL_FLOAT_CONVERSION_IMPLEMENTATION_CI_POLICY_PATHS = frozenset(
    {
        "scripts/ops/ci_test_selection_v1.py",
        "tests/ci/test_ci_diff_aware_test_selection_v1.py",
    }
)

MASTER_V2_ARITHMETIC_DECIMAL_FLOAT_CONVERSION_IMPLEMENTATION_SCOPED_PATHS = frozenset(
    {
        MASTER_V2_ARITHMETIC_DECIMAL_FLOAT_CONVERSION_IMPLEMENTATION_PRODUCTION_PATH,
        MASTER_V2_ARITHMETIC_DECIMAL_FLOAT_CONVERSION_IMPLEMENTATION_TEST_OWNER,
        *MASTER_V2_ARITHMETIC_DECIMAL_FLOAT_CONVERSION_IMPLEMENTATION_CI_POLICY_PATHS,
    }
)

MASTER_V2_ARITHMETIC_DECIMAL_FLOAT_CONVERSION_IMPLEMENTATION_FOCUSED_NODES: tuple[str, ...] = (
    f"{MASTER_V2_ARITHMETIC_DECIMAL_FLOAT_CONVERSION_IMPLEMENTATION_TEST_OWNER}::test_all_19_field_policies_convert_successfully[price]",
    f"{MASTER_V2_ARITHMETIC_DECIMAL_FLOAT_CONVERSION_IMPLEMENTATION_TEST_OWNER}::test_all_19_field_policies_convert_successfully[mark_price]",
    f"{MASTER_V2_ARITHMETIC_DECIMAL_FLOAT_CONVERSION_IMPLEMENTATION_TEST_OWNER}::test_all_19_field_policies_convert_successfully[entry_price]",
    f"{MASTER_V2_ARITHMETIC_DECIMAL_FLOAT_CONVERSION_IMPLEMENTATION_TEST_OWNER}::test_all_19_field_policies_convert_successfully[qty]",
    f"{MASTER_V2_ARITHMETIC_DECIMAL_FLOAT_CONVERSION_IMPLEMENTATION_TEST_OWNER}::test_all_19_field_policies_convert_successfully[contract_size]",
    f"{MASTER_V2_ARITHMETIC_DECIMAL_FLOAT_CONVERSION_IMPLEMENTATION_TEST_OWNER}::test_all_19_field_policies_convert_successfully[tick_size]",
    f"{MASTER_V2_ARITHMETIC_DECIMAL_FLOAT_CONVERSION_IMPLEMENTATION_TEST_OWNER}::test_all_19_field_policies_convert_successfully[min_qty]",
    f"{MASTER_V2_ARITHMETIC_DECIMAL_FLOAT_CONVERSION_IMPLEMENTATION_TEST_OWNER}::test_all_19_field_policies_convert_successfully[realized_pnl]",
    f"{MASTER_V2_ARITHMETIC_DECIMAL_FLOAT_CONVERSION_IMPLEMENTATION_TEST_OWNER}::test_all_19_field_policies_convert_successfully[unrealized_pnl]",
    f"{MASTER_V2_ARITHMETIC_DECIMAL_FLOAT_CONVERSION_IMPLEMENTATION_TEST_OWNER}::test_all_19_field_policies_convert_successfully[notional]",
    f"{MASTER_V2_ARITHMETIC_DECIMAL_FLOAT_CONVERSION_IMPLEMENTATION_TEST_OWNER}::test_all_19_field_policies_convert_successfully[fee_bps]",
    f"{MASTER_V2_ARITHMETIC_DECIMAL_FLOAT_CONVERSION_IMPLEMENTATION_TEST_OWNER}::test_all_19_field_policies_convert_successfully[funding_rate]",
    f"{MASTER_V2_ARITHMETIC_DECIMAL_FLOAT_CONVERSION_IMPLEMENTATION_TEST_OWNER}::test_all_19_field_policies_convert_successfully[equity]",
    f"{MASTER_V2_ARITHMETIC_DECIMAL_FLOAT_CONVERSION_IMPLEMENTATION_TEST_OWNER}::test_all_19_field_policies_convert_successfully[initial_margin_rate]",
    f"{MASTER_V2_ARITHMETIC_DECIMAL_FLOAT_CONVERSION_IMPLEMENTATION_TEST_OWNER}::test_all_19_field_policies_convert_successfully[maintenance_margin_rate]",
    f"{MASTER_V2_ARITHMETIC_DECIMAL_FLOAT_CONVERSION_IMPLEMENTATION_TEST_OWNER}::test_all_19_field_policies_convert_successfully[quote_currency_notional]",
    f"{MASTER_V2_ARITHMETIC_DECIMAL_FLOAT_CONVERSION_IMPLEMENTATION_TEST_OWNER}::test_all_19_field_policies_convert_successfully[fee_rate]",
    f"{MASTER_V2_ARITHMETIC_DECIMAL_FLOAT_CONVERSION_IMPLEMENTATION_TEST_OWNER}::test_all_19_field_policies_convert_successfully[maintenance_margin]",
    f"{MASTER_V2_ARITHMETIC_DECIMAL_FLOAT_CONVERSION_IMPLEMENTATION_TEST_OWNER}::test_all_19_field_policies_convert_successfully[adverse_slippage_bps]",
    f"{MASTER_V2_ARITHMETIC_DECIMAL_FLOAT_CONVERSION_IMPLEMENTATION_TEST_OWNER}::test_rejects_bool_missing_and_invalid_type",
    f"{MASTER_V2_ARITHMETIC_DECIMAL_FLOAT_CONVERSION_IMPLEMENTATION_TEST_OWNER}::test_rejects_non_finite_values",
    f"{MASTER_V2_ARITHMETIC_DECIMAL_FLOAT_CONVERSION_IMPLEMENTATION_TEST_OWNER}::test_negative_zero_and_overflow_boundaries",
    f"{MASTER_V2_ARITHMETIC_DECIMAL_FLOAT_CONVERSION_IMPLEMENTATION_TEST_OWNER}::test_deterministic_decimal_no_float_leakage",
    f"{MASTER_V2_ARITHMETIC_DECIMAL_FLOAT_CONVERSION_IMPLEMENTATION_TEST_OWNER}::test_conversion_quantization_tick_lot_separation",
    f"{MASTER_V2_ARITHMETIC_DECIMAL_FLOAT_CONVERSION_IMPLEMENTATION_TEST_OWNER}::test_batch_partial_and_complete_semantics",
    f"{MASTER_V2_ARITHMETIC_DECIMAL_FLOAT_CONVERSION_IMPLEMENTATION_TEST_OWNER}::test_immutable_non_authorizing_no_wiring",
)

MASTER_V2_ARITHMETIC_DECIMAL_FLOAT_CONVERSION_IMPLEMENTATION_CI_SELECTOR_TARGETS: tuple[
    str, ...
] = (
    "tests/ci/test_ci_diff_aware_test_selection_v1.py::test_selector_master_v2_arithmetic_decimal_float_conversion_implementation_test_only_focused",
    "tests/ci/test_ci_diff_aware_test_selection_v1.py::test_selector_master_v2_arithmetic_decimal_float_conversion_implementation_foreign_path_escalates_full",
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

BOUNDED_FUTURES_TESTNET_CONTRACT_OWNER = "src/ops/bounded_futures_testnet_contract_v0.py"
BOUNDED_FUTURES_TESTNET_VENUE_BINDING_OWNER = "src/ops/bounded_futures_testnet_venue_binding_v0.py"
AWS_SHADOW_PAPER_TESTNET_OKX_EUROPE_COMPATIBILITY_OWNER = (
    "src/ops/aws_shadow_paper_testnet_okx_europe_compatibility_contract_v0.py"
)
AWS_SHADOW_PAPER_TESTNET_OKX_EUROPE_COMPATIBILITY_TEST_OWNER = (
    "tests/ops/test_aws_shadow_paper_testnet_okx_europe_compatibility_contract_v0.py"
)

BOUNDED_FUTURES_TESTNET_CONTRACT_CI_POLICY_PATHS = frozenset(
    {
        "scripts/ops/ci_test_selection_v1.py",
        "config/ci/file_category_mapping.yaml",
        "tests/ci/test_ci_diff_aware_test_selection_v1.py",
    }
)

REQUIRED_BOUNDED_FUTURES_TESTNET_CONTRACT_TEST_OWNERS: tuple[str, ...] = (
    "tests/ops/test_bounded_futures_testnet_contract_v0.py",
    "tests/ops/test_bounded_futures_testnet_adapter_contract_v0.py",
    "tests/ops/test_order_capability_dry_validation_contract_v1.py",
    "tests/ops/test_archive_futures_testnet_harness_v0.py",
    "tests/ops/test_run_order_capability_dry_validation_adapter_v1.py",
    "tests/ops/test_bounded_futures_testnet_okx_eea_xperp_binding_contract_v0.py",
    AWS_SHADOW_PAPER_TESTNET_OKX_EUROPE_COMPATIBILITY_TEST_OWNER,
    "tests/ops/test_bounded_futures_testnet_validate_only_lifecycle_integration_contract_v0.py",
)

CANONICAL_BOUNDED_FUTURES_TESTNET_CONTRACT_FOCUSED_TESTS: tuple[str, ...] = (
    *REQUIRED_BOUNDED_FUTURES_TESTNET_CONTRACT_TEST_OWNERS,
    "tests/ci/test_ci_diff_aware_test_selection_v1.py",
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

OKX_EUROPE_ADAPTER_LIFECYCLE_OWNER = "src/ops/okx_europe_adapter_lifecycle_contract_v0.py"
OKX_EUROPE_ADAPTER_LIFECYCLE_TEST_OWNER = (
    "tests/ops/test_okx_europe_adapter_lifecycle_contract_v0.py"
)
BOUNDED_FUTURES_TESTNET_ADAPTER_CAPABILITY_LIFECYCLE_INTEGRATION_OWNER = (
    "src/ops/bounded_futures_testnet_adapter_capability_lifecycle_integration_contract_v0.py"
)
BOUNDED_FUTURES_TESTNET_ADAPTER_CAPABILITY_LIFECYCLE_INTEGRATION_TEST_OWNER = (
    "tests/ops/test_bounded_futures_testnet_adapter_capability_lifecycle_integration_contract_v0.py"
)

OKX_EUROPE_ADAPTER_LIFECYCLE_CI_POLICY_PATHS = frozenset(
    {
        "scripts/ops/ci_test_selection_v1.py",
        "config/ci/file_category_mapping.yaml",
        "tests/ci/test_ci_diff_aware_test_selection_v1.py",
    }
)

REQUIRED_OKX_EUROPE_ADAPTER_LIFECYCLE_TEST_OWNERS: tuple[str, ...] = (
    OKX_EUROPE_ADAPTER_LIFECYCLE_TEST_OWNER,
    "tests/ops/test_bounded_futures_testnet_okx_eea_xperp_binding_contract_v0.py",
    AWS_SHADOW_PAPER_TESTNET_OKX_EUROPE_COMPATIBILITY_TEST_OWNER,
)

CANONICAL_OKX_EUROPE_ADAPTER_LIFECYCLE_FOCUSED_TESTS: tuple[str, ...] = (
    *REQUIRED_OKX_EUROPE_ADAPTER_LIFECYCLE_TEST_OWNERS,
    BOUNDED_FUTURES_TESTNET_ADAPTER_CAPABILITY_LIFECYCLE_INTEGRATION_TEST_OWNER,
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

WORKFLOW_CONTRACT_FAST_LANE_OWNERS: dict[str, str] = {
    ".github/workflows/cursor_auto_pr.yml": (
        "tests/ci/test_cursor_auto_pr_pre_pr_validation_enforcement_contract_v0.py"
    ),
    ".github/workflows/pr-head-sha-required-checks-liveness-guard.yml": (
        "tests/ci/test_pr_head_sha_required_checks_liveness_guard.py"
    ),
}

FAST_LANE_CONTRACT_REBUNDLE_PATHS = (
    frozenset(
        {
            ".github/workflows/ci.yml",
            "scripts/ops/ci_test_selection_v1.py",
            "tests/ci/test_ci_diff_aware_test_selection_v1.py",
            "tests/ci/test_ci_static_contract_narrow_code_filter_contract_v0.py",
        }
    )
    | frozenset(WORKFLOW_CONTRACT_FAST_LANE_OWNERS.keys())
    | frozenset(WORKFLOW_CONTRACT_FAST_LANE_OWNERS.values())
)

FAST_LANE_CONTRACT_WIRING_WORKFLOWS = frozenset({".github/workflows/ci.yml"})

# Closed allowlist for MATRIX_CONTRACT_FOCUSED rebundle (fail-closed outside this set).
MATRIX_CI_CONTRACT_REBUNDLE_PATHS = frozenset(
    {
        ".github/workflows/ci.yml",
        ".github/workflows/cursor_auto_pr.yml",
        ".github/workflows/pr-head-sha-required-checks-liveness-guard.yml",
        "scripts/ops/ci_test_selection_v1.py",
        "tests/ci/test_ci_diff_aware_test_selection_v1.py",
        "tests/ci/test_cursor_auto_pr_pre_pr_validation_enforcement_contract_v0.py",
        "tests/ci/test_pr_head_sha_required_checks_liveness_guard.py",
    }
)

MATRIX_CONTRACT_REBUNDLE_ID = "ci_workflow_selector_contract_rebundle_v1"

MATRIX_SELECTOR_SELF_CHANGE_PATHS = frozenset(
    {
        "scripts/ops/ci_test_selection_v1.py",
        "tests/ci/test_ci_diff_aware_test_selection_v1.py",
    }
)

FAST_LANE_FULL_STATIC_PATHS = frozenset(
    {
        ".github/workflows/ci.yml",
        "scripts/ops/ci_test_selection_v1.py",
        "config/ci/file_category_mapping.yaml",
        "pytest.ini",
        "Makefile",
        "pyproject.toml",
        "uv.lock",
        "requirements.txt",
    }
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

INVALID_SELECTION_MODE = "INVALID"
PR_LIKE_EVENTS = frozenset({"pull_request", "merge_group", "push"})
EXHAUSTIVE_AUTHORIZED_EVENTS = frozenset({"schedule", "workflow_dispatch"})

PR_BOUNDED_FULL_VERSION_SMOKE_TARGETS: tuple[str, ...] = (
    "tests/test_stability_smoke.py",
    "tests/test_data_contracts.py",
    "tests/test_error_taxonomy.py",
    "tests/test_resilience.py",
)

PR_BOUNDED_FULL_PY311_CORE_TARGETS: tuple[str, ...] = (
    "tests/ci/test_ci_diff_aware_test_selection_v1.py",
    "tests/ci/test_ci_static_contract_narrow_code_filter_contract_v0.py",
    "tests/ci/test_required_checks_config.py",
    "tests/ci/test_required_checks_hygiene.py",
    "tests/ci/test_workflows_no_pull_request_target_contract_v0.py",
    "tests/ci/test_ci_testowner_runtime_budget_reporting_contract_v0.py",
    "tests/ci/test_pr_head_sha_required_checks_liveness_guard.py",
)

PR_BOUNDED_FULL_CI_CHANGE_EXTRA_TARGETS: tuple[str, ...] = (
    "tests/ci/test_cursor_auto_pr_pre_pr_validation_enforcement_contract_v0.py",
    "tests/ci/test_ci_scheduled_paper_export_smoke_workflow_contract_v0.py",
    "tests/ci/test_class_a_shadow_paper_scheduled_probe_workflow_contract_v0.py",
    "tests/ci/test_paper_session_audit_evidence_workflow_contract_v0.py",
    "tests/ci/test_paper_tests_audit_evidence_workflow_contract_v0.py",
    "tests/ci/test_prj_scheduled_shadow_paper_features_smoke_workflow_contract_v0.py",
    "tests/ci/test_shadow_paper_smoke_workflow_contract_v0.py",
)

PR_BOUNDED_FULL_VAR_SUITE_ADAPTER_TRIGGER_PATHS: frozenset[str] = frozenset(
    {
        "src/risk/validation/var_suite_adapter.py",
        "src/risk/validation/var_suite_backtest_wiring_v1.py",
        "scripts/run_var_suite_from_backtest_run_v1.py",
        "tests/risk/validation/test_var_suite_adapter_v0.py",
        "tests/risk/validation/test_var_suite_backtest_wiring_v1.py",
        "tests/scripts/test_backtest_returns_var_suite_offline_v1.py",
    }
)

PR_BOUNDED_FULL_VAR_SUITE_ADAPTER_TARGETS: tuple[str, ...] = (
    "tests/risk/validation/test_var_suite_adapter_v0.py",
    "tests/risk/validation/test_var_suite_backtest_wiring_v1.py",
    "tests/scripts/test_backtest_returns_var_suite_offline_v1.py",
)

PR_BOUNDED_FULL_PACKAGE_A_META_TRIGGER_PATHS: frozenset[str] = frozenset(
    {
        "src/meta/learning_loop/contract_safety_v1.py",
        "src/meta/learning_loop/config_patch_manifest_v1.py",
        "tests/meta/test_contract_safety_v1.py",
        "tests/meta/test_config_patch_manifest_v1_contract.py",
        "tests/meta/test_config_patch_manifest_v1_promotion_input_loader_v1.py",
    }
)

PR_BOUNDED_FULL_PACKAGE_A_META_TARGETS: tuple[str, ...] = (
    "tests/meta/test_contract_safety_v1.py",
    "tests/meta/test_config_patch_manifest_v1_contract.py",
    "tests/meta/test_config_patch_manifest_v1_promotion_input_loader_v1.py",
)

PR_BOUNDED_FULL_PACKAGE_B_PROMOTION_INPUT_TRIGGER_PATHS: frozenset[str] = frozenset(
    {
        "scripts/run_promotion_proposal_cycle.py",
        "src/governance/promotion_loop/proposal_input_refs_v1.py",
        "tests/scripts/test_run_promotion_proposal_cycle_manifest_input_v1.py",
        "tests/scripts/test_run_promotion_proposal_cycle_manifest_lineage_fk_v1.py",
        "tests/governance/promotion_loop/test_proposal_input_refs_v1.py",
    }
)

PR_BOUNDED_FULL_PACKAGE_B_PROMOTION_INPUT_TARGETS: tuple[str, ...] = (
    "tests/meta/test_config_patch_manifest_v1_promotion_input_loader_v1.py",
    "tests/scripts/test_run_promotion_proposal_cycle_manifest_input_v1.py",
    "tests/scripts/test_run_promotion_proposal_cycle_manifest_lineage_fk_v1.py",
    "tests/governance/promotion_loop/test_proposal_input_refs_v1.py",
)

PR_BOUNDED_FULL_PACKAGE_D_LEARNING_BRIDGE_TRIGGER_PATHS: frozenset[str] = frozenset(
    {
        "src/meta/learning_loop/manifest_bridge_v1.py",
        "src/meta/learning_loop/bridge.py",
        "scripts/run_learning_manifest_bridge_v1.py",
        "tests/meta/test_learning_manifest_bridge_v1.py",
    }
)

PR_BOUNDED_FULL_PACKAGE_D_LEARNING_BRIDGE_TARGETS: tuple[str, ...] = (
    "tests/meta/test_learning_loop_bridge.py",
    "tests/meta/test_config_patch_manifest_v1_contract.py",
    "tests/meta/test_learning_manifest_bridge_v1.py",
)

PR_BOUNDED_FULL_PACKAGE_A_GOVERNANCE_TRIGGER_PATHS: frozenset[str] = frozenset(
    {
        "src/governance/promotion_loop/candidate_lineage_manifest_v1.py",
        "tests/governance/promotion_loop/test_candidate_lineage_manifest_v1_contract.py",
    }
)

PR_BOUNDED_FULL_PACKAGE_A_GOVERNANCE_TARGETS: tuple[str, ...] = (
    "tests/governance/promotion_loop/test_candidate_lineage_manifest_v1_contract.py",
)

PR_BOUNDED_FULL_PACKAGE_F_CANDIDATE_LINEAGE_PRODUCTION_TRIGGER_PATHS: frozenset[str] = frozenset(
    {
        "src/governance/promotion_loop/candidate_lineage_manifest_v1.py",
        "src/governance/promotion_loop/backtest_lineage_ref_producer_v1.py",
        "src/governance/promotion_loop/var_suite_lineage_ref_producer_v1.py",
        "scripts/run_candidate_lineage_manifest_v1.py",
        "scripts/run_backtest_lineage_ref_producer_v1.py",
        "scripts/run_var_suite_lineage_ref_producer_v1.py",
        "tests/governance/promotion_loop/test_candidate_lineage_manifest_v1_producer_v1.py",
        "tests/governance/promotion_loop/test_backtest_lineage_ref_producer_v1.py",
        "tests/governance/promotion_loop/test_var_suite_lineage_ref_producer_v1.py",
        "tests/scripts/test_run_candidate_lineage_manifest_v1.py",
        "tests/scripts/test_run_backtest_lineage_ref_producer_v1.py",
        "tests/scripts/test_run_var_suite_lineage_ref_producer_v1.py",
    }
)

PR_BOUNDED_FULL_PACKAGE_F_CANDIDATE_LINEAGE_PRODUCTION_TARGETS: tuple[str, ...] = (
    "tests/governance/promotion_loop/test_candidate_lineage_manifest_v1_contract.py",
    "tests/governance/promotion_loop/test_candidate_lineage_manifest_v1_producer_v1.py",
    "tests/governance/promotion_loop/test_backtest_lineage_ref_producer_v1.py",
    "tests/governance/promotion_loop/test_var_suite_lineage_ref_producer_v1.py",
    "tests/scripts/test_run_candidate_lineage_manifest_v1.py",
    "tests/scripts/test_run_backtest_lineage_ref_producer_v1.py",
    "tests/scripts/test_run_var_suite_lineage_ref_producer_v1.py",
    "tests/test_run_summary_contract.py",
    *PR_BOUNDED_FULL_VAR_SUITE_ADAPTER_TARGETS,
)

PR_BOUNDED_FULL_PACKAGE_G_LEARNING_DURABLE_EVIDENCE_TRIGGER_PATHS: frozenset[str] = frozenset(
    {
        "src/meta/learning_loop/manifest_durable_evidence_binding_v1.py",
        "scripts/run_learning_manifest_durable_evidence_binding_v1.py",
        "tests/meta/test_learning_manifest_durable_evidence_binding_v1.py",
        "tests/scripts/test_run_learning_manifest_durable_evidence_binding_v1.py",
    }
)

PR_BOUNDED_FULL_PACKAGE_G_LEARNING_DURABLE_EVIDENCE_TARGETS: tuple[str, ...] = (
    "tests/meta/test_config_patch_manifest_v1_contract.py",
    "tests/meta/test_learning_manifest_bridge_v1.py",
    "tests/meta/test_learning_manifest_durable_evidence_binding_v1.py",
    "tests/scripts/test_run_learning_manifest_durable_evidence_binding_v1.py",
    "tests/governance/promotion_loop/test_candidate_lineage_manifest_v1_contract.py",
    "tests/governance/promotion_loop/test_candidate_lineage_manifest_v1_producer_v1.py",
)

PR_BOUNDED_FULL_PACKAGE_K_VAR_SUITE_DURABLE_EVIDENCE_TRIGGER_PATHS: frozenset[str] = frozenset(
    {
        "src/meta/learning_loop/var_suite_durable_evidence_binding_v1.py",
        "scripts/run_var_suite_durable_evidence_binding_v1.py",
        "tests/meta/test_var_suite_durable_evidence_binding_v1.py",
        "tests/scripts/test_run_var_suite_durable_evidence_binding_v1.py",
    }
)

PR_BOUNDED_FULL_PACKAGE_K_VAR_SUITE_DURABLE_EVIDENCE_TARGETS: tuple[str, ...] = (
    "tests/meta/test_var_suite_durable_evidence_binding_v1.py",
    "tests/scripts/test_run_var_suite_durable_evidence_binding_v1.py",
    "tests/governance/promotion_loop/test_var_suite_lineage_ref_producer_v1.py",
    "tests/scripts/test_run_var_suite_lineage_ref_producer_v1.py",
    "tests/risk/validation/test_var_suite_backtest_wiring_v1.py",
    "tests/governance/promotion_loop/test_candidate_lineage_manifest_v1_contract.py",
)

PR_BOUNDED_FULL_PACKAGE_E_GOVERNANCE_CLOSEOUT_TRIGGER_PATHS: frozenset[str] = frozenset(
    {
        "src/governance/promotion_loop/engine.py",
        "src/governance/promotion_loop/safety.py",
        "src/governance/promotion_loop/policy.py",
        "tests/governance/promotion_loop/test_engine_manifest_era_v1.py",
        "tests/governance/promotion_loop/test_safety_manifest_era_v1.py",
        "tests/governance/promotion_loop/test_policy_manifest_era_v1.py",
        "tests/scripts/test_offline_learning_promotion_e2e_v1.py",
    }
)

PR_BOUNDED_FULL_PACKAGE_E_GOVERNANCE_CLOSEOUT_TARGETS: tuple[str, ...] = (
    "tests/governance/promotion_loop/test_engine_manifest_era_v1.py",
    "tests/governance/promotion_loop/test_safety_manifest_era_v1.py",
    "tests/governance/promotion_loop/test_policy_manifest_era_v1.py",
    "tests/scripts/test_offline_learning_promotion_e2e_v1.py",
    "tests/meta/test_config_patch_manifest_v1_promotion_input_loader_v1.py",
    "tests/governance/promotion_loop/test_proposal_input_refs_v1.py",
    "tests/meta/test_learning_manifest_bridge_v1.py",
)


def resolve_pr_bounded_full_targets(files: list[str]) -> tuple[str, ...]:
    """Conservative, deterministic PR_BOUNDED_FULL pytest targets (3.11 main lane)."""
    targets: list[str] = []
    seen: set[str] = set()

    def add(path: str) -> None:
        if path not in seen and _repo_path_exists(path):
            seen.add(path)
            targets.append(path)

    for path in PR_BOUNDED_FULL_VERSION_SMOKE_TARGETS:
        add(path)
    for path in PR_BOUNDED_FULL_PY311_CORE_TARGETS:
        add(path)

    normalized = {PurePosixPath(f).as_posix() for f in files if f.strip()}
    ci_central = {
        ".github/workflows/ci.yml",
        "scripts/ops/ci_test_selection_v1.py",
        "config/ci/file_category_mapping.yaml",
    }
    if normalized & ci_central:
        for path in CI_INFRA_CONTRACT_TEST_ALLOWLIST:
            add(path)
        for path in CI_INFRA_CORE_FOCUSED_TESTS:
            add(path)
        for path in PR_BOUNDED_FULL_CI_CHANGE_EXTRA_TARGETS:
            add(path)

    if normalized & PR_BOUNDED_FULL_VAR_SUITE_ADAPTER_TRIGGER_PATHS:
        for path in PR_BOUNDED_FULL_VAR_SUITE_ADAPTER_TARGETS:
            add(path)

    if normalized & PR_BOUNDED_FULL_PACKAGE_A_META_TRIGGER_PATHS:
        for path in PR_BOUNDED_FULL_PACKAGE_A_META_TARGETS:
            add(path)

    if normalized & PR_BOUNDED_FULL_PACKAGE_A_GOVERNANCE_TRIGGER_PATHS:
        for path in PR_BOUNDED_FULL_PACKAGE_A_GOVERNANCE_TARGETS:
            add(path)

    if normalized & PR_BOUNDED_FULL_PACKAGE_F_CANDIDATE_LINEAGE_PRODUCTION_TRIGGER_PATHS:
        for path in PR_BOUNDED_FULL_PACKAGE_F_CANDIDATE_LINEAGE_PRODUCTION_TARGETS:
            add(path)

    if normalized & PR_BOUNDED_FULL_PACKAGE_G_LEARNING_DURABLE_EVIDENCE_TRIGGER_PATHS:
        for path in PR_BOUNDED_FULL_PACKAGE_G_LEARNING_DURABLE_EVIDENCE_TARGETS:
            add(path)

    if normalized & PR_BOUNDED_FULL_PACKAGE_K_VAR_SUITE_DURABLE_EVIDENCE_TRIGGER_PATHS:
        for path in PR_BOUNDED_FULL_PACKAGE_K_VAR_SUITE_DURABLE_EVIDENCE_TARGETS:
            add(path)

    if normalized & PR_BOUNDED_FULL_PACKAGE_B_PROMOTION_INPUT_TRIGGER_PATHS:
        for path in PR_BOUNDED_FULL_PACKAGE_B_PROMOTION_INPUT_TARGETS:
            add(path)

    if normalized & PR_BOUNDED_FULL_PACKAGE_D_LEARNING_BRIDGE_TRIGGER_PATHS:
        for path in PR_BOUNDED_FULL_PACKAGE_D_LEARNING_BRIDGE_TARGETS:
            add(path)

    if normalized & PR_BOUNDED_FULL_PACKAGE_E_GOVERNANCE_CLOSEOUT_TRIGGER_PATHS:
        for path in PR_BOUNDED_FULL_PACKAGE_E_GOVERNANCE_CLOSEOUT_TARGETS:
            add(path)

    if not targets:
        return ()
    return tuple(sorted(targets))


def _is_pr_like_event(event_name: str) -> bool:
    return event_name in PR_LIKE_EVENTS


@dataclass(frozen=True)
class SelectionResult:
    mode: str
    reason: str
    focused_pytest_targets: tuple[str, ...]
    focused_module_imports: tuple[str, ...] = ()
    pr_bounded_pytest_targets: tuple[str, ...] = ()

    def github_output_lines(self) -> list[str]:
        is_contract_focused = self.mode == "CONTRACT_FOCUSED"
        is_pr_bounded = self.mode == "PR_BOUNDED_FULL"
        is_exhaustive = self.mode == "EXHAUSTIVE_FULL"
        is_invalid = self.mode == INVALID_SELECTION_MODE
        is_no_op = self.mode == "NO_OP"
        lines = [
            f"test_selection_mode={self.mode}",
            f"test_selection_reason={self.reason}",
            f"tests_execute_full={'true' if is_exhaustive else 'false'}",
            f"tests_execute_contract_focused={'true' if is_contract_focused else 'false'}",
            f"tests_execute_focused={'true' if is_contract_focused else 'false'}",
            f"tests_execute_pr_bounded_full={'true' if is_pr_bounded else 'false'}",
            f"tests_execute_exhaustive_full={'true' if is_exhaustive else 'false'}",
            f"tests_execute_no_op={'true' if is_no_op else 'false'}",
            f"tests_execute_invalid={'true' if is_invalid else 'false'}",
        ]
        if self.focused_pytest_targets:
            lines.append(f"focused_pytest_targets={' '.join(self.focused_pytest_targets)}")
        else:
            lines.append("focused_pytest_targets=")
        if self.focused_module_imports:
            lines.append(f"focused_module_imports={' '.join(self.focused_module_imports)}")
        else:
            lines.append("focused_module_imports=")
        if self.pr_bounded_pytest_targets:
            lines.append(f"pr_bounded_pytest_targets={' '.join(self.pr_bounded_pytest_targets)}")
        else:
            lines.append("pr_bounded_pytest_targets=")
        return lines


def _is_selector_self_change_bootstrap(files: list[str]) -> bool:
    normalized = {PurePosixPath(f).as_posix() for f in files if f.strip()}
    return (
        ".github/workflows/ci.yml" in normalized
        and "scripts/ops/ci_test_selection_v1.py" in normalized
    )


def _finalize_selection_result(
    result: SelectionResult,
    files: list[str],
    *,
    event_name: str,
    force_exhaustive: bool,
) -> SelectionResult:
    if force_exhaustive:
        if event_name not in EXHAUSTIVE_AUTHORIZED_EVENTS:
            return SelectionResult(
                INVALID_SELECTION_MODE,
                "force_exhaustive_on_unauthorized_event",
                (),
            )
        return SelectionResult(
            "EXHAUSTIVE_FULL",
            "workflow_dispatch_explicit_exhaustive",
            (),
        )

    if event_name == "schedule":
        return SelectionResult("EXHAUSTIVE_FULL", "scheduled_nightly", ())

    if result.mode == INVALID_SELECTION_MODE:
        return result

    if result.mode == "NO_OP":
        return result

    if result.mode == "FOCUSED":
        if _is_selector_self_change_bootstrap(files):
            bounded = tuple(
                sorted(
                    set(resolve_pr_bounded_full_targets(files)) | set(result.focused_pytest_targets)
                )
            )
            if not bounded:
                return SelectionResult(
                    INVALID_SELECTION_MODE,
                    "pr_bounded_full_empty_targets_fail_closed",
                    (),
                )
            return SelectionResult(
                "PR_BOUNDED_FULL",
                "selector_self_change_bootstrap",
                (),
                (),
                bounded,
            )
        return SelectionResult(
            "CONTRACT_FOCUSED",
            result.reason,
            result.focused_pytest_targets,
            result.focused_module_imports,
            result.pr_bounded_pytest_targets,
        )

    if result.mode == "FULL":
        if _is_pr_like_event(event_name) or event_name == "workflow_dispatch":
            bounded = resolve_pr_bounded_full_targets(files)
            if not bounded:
                return SelectionResult(
                    INVALID_SELECTION_MODE,
                    "pr_bounded_full_empty_targets_fail_closed",
                    (),
                )
            return SelectionResult(
                "PR_BOUNDED_FULL",
                result.reason,
                (),
                (),
                bounded,
            )
        return SelectionResult("EXHAUSTIVE_FULL", result.reason, ())

    if result.mode in {"CONTRACT_FOCUSED", "PR_BOUNDED_FULL", "EXHAUSTIVE_FULL"}:
        if result.mode == "EXHAUSTIVE_FULL" and _is_pr_like_event(event_name):
            bounded = resolve_pr_bounded_full_targets(files)
            if not bounded:
                return SelectionResult(
                    INVALID_SELECTION_MODE,
                    "pr_event_exhaustive_blocked_fail_closed",
                    (),
                )
            return SelectionResult(
                "PR_BOUNDED_FULL",
                "pr_event_exhaustive_blocked_fail_closed",
                (),
                (),
                bounded,
            )
        return result

    return SelectionResult(
        INVALID_SELECTION_MODE,
        f"incoherent_selection_mode_{result.mode}",
        (),
    )


@dataclass(frozen=True)
class FastLaneContractSelection:
    mode: str
    reason: str
    pytest_targets: tuple[str, ...]

    def github_output_lines(self) -> list[str]:
        lines = [
            f"fast_lane_contract_mode={self.mode}",
            f"fast_lane_contract_reason={self.reason}",
        ]
        if self.pytest_targets:
            lines.append(f"fast_lane_contract_pytest_targets={' '.join(self.pytest_targets)}")
        else:
            lines.append("fast_lane_contract_pytest_targets=")
        return lines


@dataclass(frozen=True)
class MatrixContractSelection:
    mode: str
    reason: str
    pytest_targets: tuple[str, ...]
    rebundle_id: str = ""

    def github_output_lines(self) -> list[str]:
        lines = [
            f"matrix_contract_mode={self.mode}",
            f"matrix_contract_reason={self.reason}",
            f"matrix_contract_rebundle_id={self.rebundle_id}",
            f"tests_execute_matrix_contract_focused={'true' if self.mode == 'MATRIX_CONTRACT_FOCUSED' else 'false'}",
        ]
        if self.pytest_targets:
            lines.append(f"matrix_contract_pytest_targets={' '.join(self.pytest_targets)}")
        else:
            lines.append("matrix_contract_pytest_targets=")
        return lines


def _is_matrix_contract_docs_noise(path: str) -> bool:
    return path.startswith("docs/") or path.startswith("out/") or path.endswith(".md")


def _matrix_contract_rebundle_targets(substantive: frozenset[str]) -> tuple[str, ...] | None:
    selector_owner = "scripts/ops/ci_test_selection_v1.py"
    selector_test = "tests/ci/test_ci_diff_aware_test_selection_v1.py"
    ci_wiring = ".github/workflows/ci.yml"

    if substantive == MATRIX_SELECTOR_SELF_CHANGE_PATHS:
        return None

    targets: set[str] = set()
    if selector_owner in substantive or ci_wiring in substantive:
        if selector_test not in substantive:
            return None
        targets.add(selector_test)

    for workflow, test_owner in WORKFLOW_CONTRACT_FAST_LANE_OWNERS.items():
        if workflow in substantive:
            if test_owner not in substantive:
                return None
            targets.add(test_owner)
        elif test_owner in substantive:
            return None

    if not targets:
        return None

    missing = [target for target in targets if not _repo_path_exists(target)]
    if missing:
        return None
    return tuple(sorted(targets))


def resolve_matrix_contract_selection(files: list[str]) -> MatrixContractSelection:
    normalized = sorted({PurePosixPath(f.strip()).as_posix() for f in files if f and f.strip()})
    substantive_list = [f for f in normalized if not _is_matrix_contract_docs_noise(f)]
    substantive = frozenset(substantive_list)

    if not substantive:
        return MatrixContractSelection("MATRIX_NO_OP", "no_substantive_matrix_paths", ())

    if any(f not in MATRIX_CI_CONTRACT_REBUNDLE_PATHS for f in substantive):
        return MatrixContractSelection("MATRIX_UNMAPPED", "matrix_contract_not_applicable", ())

    if substantive == MATRIX_SELECTOR_SELF_CHANGE_PATHS:
        return MatrixContractSelection(
            "MATRIX_FULL",
            "matrix_contract_selector_self_change_requires_full",
            (),
        )

    if not any(workflow in substantive for workflow in WORKFLOW_CONTRACT_FAST_LANE_OWNERS):
        return MatrixContractSelection(
            "MATRIX_UNMAPPED",
            "matrix_contract_central_wiring_defer_to_ci_infra",
            (),
        )

    targets = _matrix_contract_rebundle_targets(substantive)
    if targets is None:
        return MatrixContractSelection(
            "MATRIX_FULL",
            "matrix_contract_incomplete_rebundle_mapping",
            (),
        )

    return MatrixContractSelection(
        "MATRIX_CONTRACT_FOCUSED",
        "matrix_contract_rebundle_complete",
        targets,
        rebundle_id=MATRIX_CONTRACT_REBUNDLE_ID,
    )


def _is_fast_lane_docs_noise(path: str) -> bool:
    return path.startswith("docs/") or path.startswith("out/") or path.endswith(".md")


def _fast_lane_requires_full_static(path: str) -> bool:
    if path in FAST_LANE_FULL_STATIC_PATHS:
        return True
    if path.endswith("/conftest.py") or path == "tests/conftest.py":
        return True
    if path.startswith("src/"):
        return True
    if path.startswith("scripts/"):
        return True
    if path.startswith(("tests/ops/", "tests/webui/", "tests/fixtures/")):
        return True
    if path.startswith(("config/", "schemas/")):
        return True
    if path.startswith("requirements"):
        return True
    if path.startswith(".github/workflows/") and path not in WORKFLOW_CONTRACT_FAST_LANE_OWNERS:
        return True
    if path.startswith("tests/") and not path.startswith("tests/ci/"):
        return True
    return False


DURABLE_COMPLETION_FAST_LANE_GRAPH_STRUCTURE_NODE_IDS: tuple[str, ...] = (
    f"{DURABLE_COMPLETION_VALIDATION_GRAPH_TEST_OWNER}::test_graph_is_cycle_free",
    f"{DURABLE_COMPLETION_VALIDATION_GRAPH_TEST_OWNER}::test_graph_explicit_order_matches_dependencies",
    f"{DURABLE_COMPLETION_VALIDATION_GRAPH_TEST_OWNER}::test_graph_aggregates_fail_reasons_from_executed_validators",
)

DURABLE_COMPLETION_FAST_LANE_SELECTOR_ANCHOR_NODE_IDS: tuple[str, ...] = (
    "tests/ci/test_ci_diff_aware_test_selection_v1.py::test_integration_partition_inventory_covers_all_nodes",
    "tests/ci/test_ci_diff_aware_test_selection_v1.py::test_selector_pr4550_cross_slice_coherence_bounded_node_ids",
)

DURABLE_COMPLETION_FAST_LANE_MASTER_V2_EVENT_STREAM_SCOPED_PATHS = frozenset(
    {
        "src/ops/durable_completion_validation/validators/event_stream.py",
    }
)

DURABLE_COMPLETION_FAST_LANE_MASTER_V2_EVENT_STREAM_HAPPY_PATH_NODE_IDS: tuple[str, ...] = (
    f"{DURABLE_COMPLETION_INTEGRATION_TEST_OWNER}::test_master_v2_kill_all_event_stream_happy_path",
    f"{DURABLE_COMPLETION_INTEGRATION_TEST_OWNER}::test_master_v2_state_switch_event_stream_happy_path_non_authorizing",
)

DURABLE_COMPLETION_MATRIX_MASTER_V2_EVENT_STREAM_BOUNDED_SCOPED_PATHS = frozenset(
    {
        DURABLE_COMPLETION_FACADE_PATH,
        "src/ops/durable_completion_validation/validators/event_stream.py",
        DURABLE_COMPLETION_INTEGRATION_TEST_OWNER,
        "tests/ci/test_ci_diff_aware_test_selection_v1.py",
    }
)

DURABLE_COMPLETION_MATRIX_MASTER_V2_EVENT_STREAM_BOUNDED_NODE_IDS: tuple[str, ...] = (
    f"{DURABLE_COMPLETION_INTEGRATION_TEST_OWNER}::test_master_v2_state_switch_event_stream_happy_path_non_authorizing",
    f"{DURABLE_COMPLETION_INTEGRATION_TEST_OWNER}::test_master_v2_kill_all_event_stream_happy_path",
    f"{DURABLE_COMPLETION_INTEGRATION_TEST_OWNER}::test_master_v2_missing_required_event_fail_closed",
    f"{DURABLE_COMPLETION_INTEGRATION_TEST_OWNER}::test_master_v2_kill_all_terminal_break_fail_closed",
    f"{DURABLE_COMPLETION_INTEGRATION_TEST_OWNER}::test_completion_proof_chain_pe38_digest_bound_positive",
    f"{DURABLE_COMPLETION_INTEGRATION_TEST_OWNER}::test_glb019_missing_proof_fail_closed",
    f"{DURABLE_COMPLETION_VALIDATION_GRAPH_TEST_OWNER}::test_graph_explicit_order_matches_dependencies",
    "tests/ci/test_ci_diff_aware_test_selection_v1.py::test_selector_pr4554_fast_lane_durable_completion_bounded_master_v2_event_stream",
)


def _is_durable_completion_matrix_master_v2_event_stream_bounded_scope(files: list[str]) -> bool:
    if not any(
        path in DURABLE_COMPLETION_FAST_LANE_MASTER_V2_EVENT_STREAM_SCOPED_PATHS for path in files
    ):
        return False
    for path in files:
        if path in DURABLE_COMPLETION_CI_POLICY_PATHS:
            continue
        if path in DURABLE_COMPLETION_CI_WORKFLOW_REBUNDLE_PATHS:
            continue
        if path in DURABLE_COMPLETION_MATRIX_MASTER_V2_EVENT_STREAM_BOUNDED_SCOPED_PATHS:
            continue
        return False
    return True


def _durable_completion_matrix_master_v2_event_stream_bounded_targets() -> tuple[str, ...]:
    targets: list[str] = []
    for target in DURABLE_COMPLETION_MATRIX_MASTER_V2_EVENT_STREAM_BOUNDED_NODE_IDS:
        if not _repo_pytest_target_exists(target):
            return ()
        targets.append(target)
    return tuple(sorted(set(targets)))


def _durable_completion_pe33_pr_smoke_pytest_targets() -> tuple[str, ...]:
    try:
        return expand_pe33_pr_smoke_pytest_targets()
    except (KeyError, RuntimeError, OSError, ValueError):
        return ()


def _durable_completion_normal_pr_graph_structure_targets() -> tuple[str, ...]:
    return DURABLE_COMPLETION_FAST_LANE_GRAPH_STRUCTURE_NODE_IDS


def _durable_completion_normal_pr_selector_anchor_targets() -> tuple[str, ...]:
    return DURABLE_COMPLETION_FAST_LANE_SELECTOR_ANCHOR_NODE_IDS


def _partition_selection_uses_pe33_pr_smoke(partition_selection: frozenset[str]) -> bool:
    return "pe33_pr_smoke" in partition_selection


def _partition_selection_uses_pe31_durable_completion_binding(
    partition_selection: frozenset[str],
) -> bool:
    return "pe31_durable_completion_binding" in partition_selection


def _is_pe31_durable_completion_binding_testowner_only_scope(
    changed_files: list[str],
) -> bool:
    """True when changed_files are only B2 durable-completion binding testowners."""
    if not changed_files:
        return False
    allowed = {
        DURABLE_COMPLETION_INTEGRATION_TEST_OWNER,
        DURABLE_COMPLETION_VALIDATION_GRAPH_TEST_OWNER,
    }
    if not set(changed_files).issubset(allowed):
        return False
    return not any(path.startswith("src/") for path in changed_files)


def _durable_completion_pe31_durable_completion_binding_integration_targets() -> tuple[str, ...]:
    try:
        return expand_pe31_durable_completion_binding_integration_pytest_targets()
    except (KeyError, RuntimeError, OSError, ValueError):
        return ()


def _durable_completion_pe31_durable_completion_binding_graph_targets() -> tuple[str, ...]:
    try:
        return expand_pe31_durable_completion_binding_graph_pytest_targets()
    except (KeyError, RuntimeError, OSError, ValueError):
        return ()


def _durable_completion_pe31_durable_completion_binding_core_targets() -> tuple[str, ...]:
    try:
        return expand_partitions_to_pytest_targets(frozenset(CORE_ALWAYS_PARTITIONS))
    except (KeyError, RuntimeError, OSError, ValueError):
        return ()


def _durable_completion_fast_lane_master_v2_event_stream_happy_path_targets(
    files: list[str],
) -> tuple[str, ...]:
    if not any(
        path in DURABLE_COMPLETION_FAST_LANE_MASTER_V2_EVENT_STREAM_SCOPED_PATHS for path in files
    ):
        return ()
    for target in DURABLE_COMPLETION_FAST_LANE_MASTER_V2_EVENT_STREAM_HAPPY_PATH_NODE_IDS:
        if not _repo_pytest_target_exists(target):
            return ()
    return DURABLE_COMPLETION_FAST_LANE_MASTER_V2_EVENT_STREAM_HAPPY_PATH_NODE_IDS


def _durable_completion_fast_lane_bounded_targets(files: list[str]) -> tuple[str, ...]:
    """Fast-Lane: PE-33 PR smoke + Master-V2 event-stream happy-path + graph + selector anchors only."""
    graph_owner = DURABLE_COMPLETION_VALIDATION_GRAPH_TEST_OWNER
    selector_owner = "tests/ci/test_ci_diff_aware_test_selection_v1.py"
    if not _repo_path_exists(graph_owner) or not _repo_path_exists(selector_owner):
        return ()
    for target in (
        *_durable_completion_normal_pr_graph_structure_targets(),
        *_durable_completion_normal_pr_selector_anchor_targets(),
    ):
        if not _repo_pytest_target_exists(target):
            return ()
    targets: set[str] = set(_durable_completion_normal_pr_graph_structure_targets())
    targets.update(_durable_completion_normal_pr_selector_anchor_targets())
    partition_selection = partitions_for_changed_files(files)
    if partition_selection is None:
        return ()
    if _partition_selection_uses_pe33_pr_smoke(partition_selection):
        smoke_targets = _durable_completion_pe33_pr_smoke_pytest_targets()
        if not smoke_targets:
            return ()
        targets.update(smoke_targets)
        return tuple(sorted(targets))
    if _partition_selection_uses_pe31_durable_completion_binding(partition_selection):
        binding_integration = (
            _durable_completion_pe31_durable_completion_binding_integration_targets()
        )
        binding_graph = _durable_completion_pe31_durable_completion_binding_graph_targets()
        if not binding_integration or not binding_graph:
            return ()
        targets.update(binding_integration)
        targets.update(binding_graph)
        return tuple(sorted(targets))
    master_v2_targets = _durable_completion_fast_lane_master_v2_event_stream_happy_path_targets(
        files
    )
    if master_v2_targets:
        targets.update(master_v2_targets)
    return tuple(sorted(targets))


def resolve_fast_lane_contract_selection(files: list[str]) -> FastLaneContractSelection:
    normalized = sorted({f.strip() for f in files if f and f.strip()})
    substantive = [f for f in normalized if not _is_fast_lane_docs_noise(f)]

    if not substantive:
        return FastLaneContractSelection("NO_OP", "no_substantive_fast_lane_paths", ())

    if _has_durable_completion_integration_partition_scope(substantive) and all(
        _is_durable_completion_integration_partition_rebundle_path(f, files=substantive)
        for f in substantive
    ):
        bounded_targets = _durable_completion_fast_lane_bounded_targets(substantive)
        if bounded_targets:
            return FastLaneContractSelection(
                "DURABLE_COMPLETION_BOUNDED",
                "durable_completion_bounded_partition",
                bounded_targets,
            )

    rebundle_only = all(f in FAST_LANE_CONTRACT_REBUNDLE_PATHS for f in substantive)
    if not rebundle_only and any(_fast_lane_requires_full_static(f) for f in substantive):
        return FastLaneContractSelection(
            "FULL_STATIC_CONTRACTS",
            "central_or_unmapped_fast_lane_path_requires_full_static",
            (),
        )

    workflow_files = [f for f in substantive if f.startswith(".github/workflows/")]
    test_ci_files = [f for f in substantive if f.startswith("tests/ci/")]
    other = [f for f in substantive if f not in workflow_files and f not in test_ci_files]
    if other and not (rebundle_only and all(f in FAST_LANE_CONTRACT_REBUNDLE_PATHS for f in other)):
        return FastLaneContractSelection(
            "FULL_STATIC_CONTRACTS",
            "unclassified_fast_lane_path_requires_full_static",
            (),
        )

    allowed_tests = set(WORKFLOW_CONTRACT_FAST_LANE_OWNERS.values())
    if test_ci_files and any(t not in allowed_tests for t in test_ci_files):
        if not (
            rebundle_only and all(t in FAST_LANE_CONTRACT_REBUNDLE_PATHS for t in test_ci_files)
        ):
            return FastLaneContractSelection(
                "FULL_STATIC_CONTRACTS",
                "tests_ci_not_in_workflow_contract_owner_map",
                (),
            )

    mapped_workflows = [w for w in workflow_files if w in WORKFLOW_CONTRACT_FAST_LANE_OWNERS]
    if test_ci_files and not mapped_workflows:
        return FastLaneContractSelection(
            "FULL_STATIC_CONTRACTS",
            "tests_ci_without_workflow_owner_map_fail_closed",
            (),
        )

    if workflow_files:
        unknown = [
            w
            for w in workflow_files
            if w not in WORKFLOW_CONTRACT_FAST_LANE_OWNERS
            and not (rebundle_only and w in FAST_LANE_CONTRACT_WIRING_WORKFLOWS)
        ]
        if unknown:
            return FastLaneContractSelection(
                "FULL_STATIC_CONTRACTS",
                "unknown_workflow_requires_full_static",
                (),
            )
        expected = sorted({WORKFLOW_CONTRACT_FAST_LANE_OWNERS[w] for w in mapped_workflows})
        workflow_tests = sorted(
            t for t in test_ci_files if t in WORKFLOW_CONTRACT_FAST_LANE_OWNERS.values()
        )
        if workflow_tests and workflow_tests != expected:
            return FastLaneContractSelection(
                "FULL_STATIC_CONTRACTS",
                "workflow_test_owner_set_mismatch_requires_full_static",
                (),
            )
        missing = [t for t in expected if not _repo_path_exists(t)]
        if missing:
            return FastLaneContractSelection(
                "FULL_STATIC_CONTRACTS",
                "workflow_contract_test_owner_missing_on_disk",
                (),
            )
        if expected:
            return FastLaneContractSelection(
                "CONTRACT_FOCUSED",
                "workflow_contract_owner_map_complete",
                tuple(expected),
            )

    central_wiring = {
        ".github/workflows/ci.yml",
        "scripts/ops/ci_test_selection_v1.py",
    }
    if any(f in central_wiring for f in substantive):
        return FastLaneContractSelection(
            "FULL_STATIC_CONTRACTS",
            "central_ci_wiring_requires_full_static",
            (),
        )

    return FastLaneContractSelection("NO_OP", "no_workflow_contract_fast_lane_paths", ())


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
    scoped_okx = {f for f in normalized if _is_okx_europe_adapter_lifecycle_scoped_path(f)}
    if scoped_okx and all(_is_okx_europe_adapter_lifecycle_rebundle_path(f) for f in normalized):
        return False
    scoped_bftc = {f for f in normalized if _is_bounded_futures_testnet_contract_scoped_path(f)}
    if scoped_bftc and all(
        _is_bounded_futures_testnet_contract_rebundle_path(f) for f in normalized
    ):
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
        DURABLE_COMPLETION_VALIDATION_GRAPH_TEST_OWNER,
        DURABLE_COMPLETION_INTEGRATION_TEST_OWNER,
    }:
        return True
    return False


def _has_durable_completion_integration_partition_scope(files: list[str]) -> bool:
    if any(_is_durable_completion_scoped_path(f) for f in files):
        return True
    files_set = set(files)
    if DURABLE_COMPLETION_VALIDATION_GRAPH_TEST_OWNER not in files_set:
        return False
    return any(f in DURABLE_COMPLETION_INTEGRATION_PE_PROD_PATHS for f in files)


def _is_durable_completion_integration_partition_rebundle_path(
    path: str,
    *,
    files: list[str],
) -> bool:
    if _is_durable_completion_rebundle_path(path):
        return True
    if path == DURABLE_COMPLETION_INTEGRATION_PARTITIONS_HELPER:
        return True
    if path == CI_GLB019_SYNTHETIC_PATCH_BUILDER:
        return True
    if path in DURABLE_COMPLETION_INTEGRATION_PE_PROD_PATHS:
        return DURABLE_COMPLETION_VALIDATION_GRAPH_TEST_OWNER in files
    return False


def _is_durable_completion_validation_graph_only_scoped_path(path: str) -> bool:
    if path == DURABLE_COMPLETION_VALIDATION_GRAPH_TEST_OWNER:
        return True
    if not path.startswith("src/ops/durable_completion_validation/"):
        return False
    if path in {DURABLE_COMPLETION_GRAPH_WIRING_PATH, DURABLE_COMPLETION_PUBLIC_API_PATH}:
        return False
    return path.endswith(".py")


def _requires_durable_completion_integration_test_owner(files: list[str]) -> bool:
    for path in files:
        if path in {
            DURABLE_COMPLETION_FACADE_PATH,
            DURABLE_COMPLETION_INTEGRATION_TEST_OWNER,
            DURABLE_COMPLETION_GRAPH_WIRING_PATH,
            DURABLE_COMPLETION_PUBLIC_API_PATH,
        }:
            return True
        if path in DURABLE_COMPLETION_INTEGRATION_PE_PROD_PATHS:
            return True
        if _is_durable_completion_scoped_path(
            path
        ) and not _is_durable_completion_validation_graph_only_scoped_path(path):
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


def _durable_completion_focused_targets(
    files: list[str] | None = None,
    *,
    patch_text: str | None = None,
) -> tuple[str, ...]:
    graph_owner = DURABLE_COMPLETION_VALIDATION_GRAPH_TEST_OWNER
    if not _repo_path_exists(graph_owner):
        return ()
    if files and patch_text:
        glb019_partitions = classify_glb019_a2b_additive_patch(patch_text, repo_root=_REPO_ROOT)
        if glb019_partitions is not None:
            contract_test = "tests/ci/test_ci_diff_aware_test_selection_v1.py"
            targets: list[str] = [graph_owner]
            if _repo_path_exists(contract_test):
                targets.append(contract_test)
            try:
                targets.extend(expand_partitions_to_pytest_targets(glb019_partitions))
            except (KeyError, RuntimeError, OSError, ValueError):
                return ()
            return tuple(sorted(set(targets)))
    if files and _is_durable_completion_wallclock_binding_rebinding_scope(files):
        return _durable_completion_wallclock_binding_focused_targets(files)
    if files and _is_durable_completion_matrix_master_v2_event_stream_bounded_scope(files):
        bounded = _durable_completion_matrix_master_v2_event_stream_bounded_targets()
        if bounded:
            return bounded
    if files and not _requires_durable_completion_integration_test_owner(files):
        validation_targets: list[str] = []
        for path in CANONICAL_DURABLE_COMPLETION_VALIDATION_GRAPH_FOCUSED_TESTS:
            if _repo_path_exists(path):
                validation_targets.append(path)
        if graph_owner not in validation_targets:
            return ()
        return tuple(sorted(validation_targets))
    for path in REQUIRED_DURABLE_COMPLETION_TEST_OWNERS:
        if not _repo_path_exists(path):
            return ()
    contract_test = "tests/ci/test_ci_diff_aware_test_selection_v1.py"
    targets: list[str] = []
    if _repo_path_exists(contract_test):
        targets.append(contract_test)
    if not files:
        targets.append(DURABLE_COMPLETION_INTEGRATION_TEST_OWNER)
        if _repo_path_exists(graph_owner):
            targets.insert(0, graph_owner)
        return tuple(sorted(set(targets)))
    if any(
        path in files
        for path in (DURABLE_COMPLETION_GRAPH_WIRING_PATH, DURABLE_COMPLETION_PUBLIC_API_PATH)
    ):
        partition_selection = partitions_for_changed_files(files)
        if partition_selection is not None and partition_selection:
            try:
                if _partition_selection_uses_pe33_pr_smoke(partition_selection):
                    targets.extend(_durable_completion_normal_pr_graph_structure_targets())
                    targets.extend(_durable_completion_pe33_pr_smoke_pytest_targets())
                    return tuple(sorted(set(targets)))
                if partition_union_node_count(partition_selection) < integration_owner_node_count():
                    targets.extend(_durable_completion_normal_pr_graph_structure_targets())
                    targets.extend(expand_partitions_to_pytest_targets(partition_selection))
                    return tuple(sorted(set(targets)))
            except (KeyError, RuntimeError, OSError, ValueError):
                return ()
        if partition_selection is not None and not partition_selection:
            if _repo_path_exists(graph_owner):
                targets.insert(0, graph_owner)
            return tuple(sorted(set(targets)))
        targets.append(DURABLE_COMPLETION_INTEGRATION_TEST_OWNER)
        if _repo_path_exists(graph_owner):
            targets.insert(0, graph_owner)
        return tuple(sorted(set(targets)))
    partition_selection = partitions_for_changed_files(files)
    if partition_selection is None:
        targets.append(DURABLE_COMPLETION_INTEGRATION_TEST_OWNER)
        if _repo_path_exists(graph_owner):
            targets.insert(0, graph_owner)
        return tuple(sorted(set(targets)))
    if not partition_selection:
        targets.extend(_durable_completion_normal_pr_graph_structure_targets())
        return tuple(sorted(set(targets)))
    try:
        if _partition_selection_uses_pe33_pr_smoke(partition_selection):
            targets.extend(_durable_completion_normal_pr_graph_structure_targets())
            targets.extend(_durable_completion_pe33_pr_smoke_pytest_targets())
            return tuple(sorted(set(targets)))
        if _partition_selection_uses_pe31_durable_completion_binding(partition_selection):
            targets.extend(
                _durable_completion_pe31_durable_completion_binding_integration_targets()
            )
            targets.extend(_durable_completion_pe31_durable_completion_binding_graph_targets())
            targets.extend(_durable_completion_normal_pr_selector_anchor_targets())
            return tuple(sorted(set(targets)))
        selected_nodes = partition_union_node_count(partition_selection)
        if selected_nodes >= integration_owner_node_count():
            targets.append(DURABLE_COMPLETION_INTEGRATION_TEST_OWNER)
        else:
            targets.extend(_durable_completion_normal_pr_graph_structure_targets())
            targets.extend(expand_partitions_to_pytest_targets(partition_selection))
    except (KeyError, RuntimeError, OSError, ValueError):
        return ()
    return tuple(sorted(set(targets)))


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


def _is_okx_europe_adapter_lifecycle_scoped_path(path: str) -> bool:
    if path == OKX_EUROPE_ADAPTER_LIFECYCLE_OWNER:
        return True
    if path == BOUNDED_FUTURES_TESTNET_ADAPTER_CAPABILITY_LIFECYCLE_INTEGRATION_OWNER:
        return True
    if path == BOUNDED_FUTURES_TESTNET_ADAPTER_CAPABILITY_LIFECYCLE_INTEGRATION_TEST_OWNER:
        return True
    return path in REQUIRED_OKX_EUROPE_ADAPTER_LIFECYCLE_TEST_OWNERS


def _is_okx_europe_adapter_lifecycle_rebundle_path(path: str) -> bool:
    return (
        _is_okx_europe_adapter_lifecycle_scoped_path(path)
        or path in OKX_EUROPE_ADAPTER_LIFECYCLE_CI_POLICY_PATHS
    )


def _okx_europe_adapter_lifecycle_focused_targets() -> tuple[str, ...]:
    for path in REQUIRED_OKX_EUROPE_ADAPTER_LIFECYCLE_TEST_OWNERS:
        if not _repo_path_exists(path):
            return ()
    targets: list[str] = []
    for path in CANONICAL_OKX_EUROPE_ADAPTER_LIFECYCLE_FOCUSED_TESTS:
        if _repo_path_exists(path):
            targets.append(path)
    if len(targets) < len(REQUIRED_OKX_EUROPE_ADAPTER_LIFECYCLE_TEST_OWNERS):
        return ()
    return tuple(sorted(targets))


def _is_bounded_futures_testnet_contract_scoped_path(path: str) -> bool:
    if path == BOUNDED_FUTURES_TESTNET_CONTRACT_OWNER:
        return True
    if path == BOUNDED_FUTURES_TESTNET_VENUE_BINDING_OWNER:
        return True
    if path == AWS_SHADOW_PAPER_TESTNET_OKX_EUROPE_COMPATIBILITY_OWNER:
        return True
    return path in REQUIRED_BOUNDED_FUTURES_TESTNET_CONTRACT_TEST_OWNERS


def _is_bounded_futures_testnet_contract_rebundle_path(path: str) -> bool:
    return (
        _is_bounded_futures_testnet_contract_scoped_path(path)
        or path in BOUNDED_FUTURES_TESTNET_CONTRACT_CI_POLICY_PATHS
    )


def _bounded_futures_testnet_contract_focused_targets() -> tuple[str, ...]:
    for path in REQUIRED_BOUNDED_FUTURES_TESTNET_CONTRACT_TEST_OWNERS:
        if not _repo_path_exists(path):
            return ()
    targets: list[str] = []
    for path in CANONICAL_BOUNDED_FUTURES_TESTNET_CONTRACT_FOCUSED_TESTS:
        if _repo_path_exists(path):
            targets.append(path)
    if len(targets) < len(REQUIRED_BOUNDED_FUTURES_TESTNET_CONTRACT_TEST_OWNERS):
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
        if not (
            all(_is_ci_infra_rebundle_path(f) for f in files) and has_workflow and has_contract
        ):
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


def _try_okx_europe_adapter_lifecycle_focused(files: list[str]) -> SelectionResult | None:
    if not files:
        return None
    if not any(_is_okx_europe_adapter_lifecycle_scoped_path(f) for f in files):
        return None
    if not all(_is_okx_europe_adapter_lifecycle_rebundle_path(f) for f in files):
        return None
    files_set = set(files)
    if (
        OKX_EUROPE_ADAPTER_LIFECYCLE_OWNER in files_set
        and OKX_EUROPE_ADAPTER_LIFECYCLE_TEST_OWNER not in files_set
    ):
        return None
    if (
        BOUNDED_FUTURES_TESTNET_ADAPTER_CAPABILITY_LIFECYCLE_INTEGRATION_OWNER in files_set
        and BOUNDED_FUTURES_TESTNET_ADAPTER_CAPABILITY_LIFECYCLE_INTEGRATION_TEST_OWNER
        not in files_set
    ):
        return None
    targets = _okx_europe_adapter_lifecycle_focused_targets()
    if not targets:
        return None
    modules: tuple[str, ...] = ("src.ops.okx_europe_adapter_lifecycle_contract_v0",)
    return SelectionResult(
        "FOCUSED",
        "okx_europe_adapter_lifecycle_focused",
        targets,
        modules,
    )


def _try_bounded_futures_testnet_contract_focused(files: list[str]) -> SelectionResult | None:
    if not files:
        return None
    if not any(_is_bounded_futures_testnet_contract_scoped_path(f) for f in files):
        return None
    if not all(_is_bounded_futures_testnet_contract_rebundle_path(f) for f in files):
        return None
    files_set = set(files)
    if (
        BOUNDED_FUTURES_TESTNET_CONTRACT_OWNER in files_set
        and "tests/ops/test_bounded_futures_testnet_contract_v0.py" not in files_set
    ):
        return None
    targets = _bounded_futures_testnet_contract_focused_targets()
    if not targets:
        return None
    modules: tuple[str, ...] = (
        "src.ops.bounded_futures_testnet_contract_v0",
        "src.ops.bounded_futures_testnet_venue_binding_v0",
    )
    return SelectionResult(
        "FOCUSED",
        "bounded_futures_testnet_contract_focused",
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


def _is_master_v2_arithmetic_kernel_seam_scoped_path(path: str) -> bool:
    return path in MASTER_V2_ARITHMETIC_KERNEL_SEAM_FAIL_CLOSED_CONTRACT_SCOPED_PATHS


def _is_master_v2_arithmetic_kernel_seam_rebundle_path(path: str) -> bool:
    return _is_master_v2_arithmetic_kernel_seam_scoped_path(path)


def _is_master_v2_arithmetic_kernel_seam_scope(files: list[str]) -> bool:
    if not files:
        return False
    files_set = set(files)
    if MASTER_V2_ARITHMETIC_KERNEL_SEAM_FAIL_CLOSED_CONTRACT_TEST_OWNER not in files_set:
        return False
    return all(
        path in MASTER_V2_ARITHMETIC_KERNEL_SEAM_FAIL_CLOSED_CONTRACT_SCOPED_PATHS for path in files
    )


def _master_v2_arithmetic_kernel_seam_focused_targets(
    files: list[str] | None = None,
) -> tuple[str, ...]:
    if not _repo_path_exists(MASTER_V2_ARITHMETIC_KERNEL_SEAM_FAIL_CLOSED_CONTRACT_TEST_OWNER):
        return ()
    targets: list[str] = []
    for node in MASTER_V2_ARITHMETIC_KERNEL_SEAM_FAIL_CLOSED_CONTRACT_FOCUSED_NODES:
        if _repo_pytest_target_exists(node):
            targets.append(node)
    if len(targets) != len(MASTER_V2_ARITHMETIC_KERNEL_SEAM_FAIL_CLOSED_CONTRACT_FOCUSED_NODES):
        return ()
    if files and any(
        path in MASTER_V2_ARITHMETIC_KERNEL_SEAM_FAIL_CLOSED_CONTRACT_CI_POLICY_PATHS
        for path in files
    ):
        for ci_target in MASTER_V2_ARITHMETIC_KERNEL_SEAM_FAIL_CLOSED_CONTRACT_CI_SELECTOR_TARGETS:
            if _repo_pytest_target_exists(ci_target):
                targets.append(ci_target)
    return tuple(sorted(set(targets)))


def _try_master_v2_arithmetic_kernel_seam_fail_closed_contract_focused(
    files: list[str],
) -> SelectionResult | None:
    if not _is_master_v2_arithmetic_kernel_seam_scope(files):
        return None
    targets = _master_v2_arithmetic_kernel_seam_focused_targets(files)
    if not targets:
        return None
    return SelectionResult(
        "FOCUSED",
        "master_v2_arithmetic_kernel_seam_fail_closed_contract_focused",
        targets,
        ("src.execution.paper.futures_accounting",),
    )


def _is_duplicate_pnl_owner_boundary_scoped_path(path: str) -> bool:
    return path in DUPLICATE_PNL_OWNER_BOUNDARY_CONTRACT_SCOPED_PATHS


def _is_duplicate_pnl_owner_boundary_rebundle_path(path: str) -> bool:
    return _is_duplicate_pnl_owner_boundary_scoped_path(path)


def _is_duplicate_pnl_owner_boundary_scope(files: list[str]) -> bool:
    if not files:
        return False
    files_set = set(files)
    if DUPLICATE_PNL_OWNER_BOUNDARY_CONTRACT_TEST_OWNER not in files_set:
        return False
    return all(path in DUPLICATE_PNL_OWNER_BOUNDARY_CONTRACT_SCOPED_PATHS for path in files)


def _duplicate_pnl_owner_boundary_focused_targets(
    files: list[str] | None = None,
) -> tuple[str, ...]:
    if not _repo_path_exists(DUPLICATE_PNL_OWNER_BOUNDARY_CONTRACT_TEST_OWNER):
        return ()
    targets: list[str] = []
    for node in DUPLICATE_PNL_OWNER_BOUNDARY_CONTRACT_FOCUSED_NODES:
        if _repo_pytest_target_exists(node):
            targets.append(node)
    if len(targets) != len(DUPLICATE_PNL_OWNER_BOUNDARY_CONTRACT_FOCUSED_NODES):
        return ()
    if files and any(
        path in DUPLICATE_PNL_OWNER_BOUNDARY_CONTRACT_CI_POLICY_PATHS for path in files
    ):
        for ci_target in DUPLICATE_PNL_OWNER_BOUNDARY_CONTRACT_CI_SELECTOR_TARGETS:
            if _repo_pytest_target_exists(ci_target):
                targets.append(ci_target)
    return tuple(sorted(set(targets)))


def _try_duplicate_pnl_owner_boundary_contract_focused(
    files: list[str],
) -> SelectionResult | None:
    if not _is_duplicate_pnl_owner_boundary_scope(files):
        return None
    targets = _duplicate_pnl_owner_boundary_focused_targets(files)
    if not targets:
        return None
    return SelectionResult(
        "FOCUSED",
        "duplicate_pnl_owner_boundary_contract_focused",
        targets,
        (),
    )


def _is_reconciliation_decimal_float_owner_boundary_scoped_path(path: str) -> bool:
    return path in RECONCILIATION_DECIMAL_FLOAT_OWNER_BOUNDARY_CONTRACT_SCOPED_PATHS


def _is_reconciliation_decimal_float_owner_boundary_rebundle_path(path: str) -> bool:
    return _is_reconciliation_decimal_float_owner_boundary_scoped_path(path)


def _is_reconciliation_decimal_float_owner_boundary_scope(files: list[str]) -> bool:
    if not files:
        return False
    files_set = set(files)
    if RECONCILIATION_DECIMAL_FLOAT_OWNER_BOUNDARY_CONTRACT_TEST_OWNER not in files_set:
        return False
    return all(
        path in RECONCILIATION_DECIMAL_FLOAT_OWNER_BOUNDARY_CONTRACT_SCOPED_PATHS for path in files
    )


def _reconciliation_decimal_float_owner_boundary_focused_targets(
    files: list[str] | None = None,
) -> tuple[str, ...]:
    if not _repo_path_exists(RECONCILIATION_DECIMAL_FLOAT_OWNER_BOUNDARY_CONTRACT_TEST_OWNER):
        return ()
    targets: list[str] = []
    for node in RECONCILIATION_DECIMAL_FLOAT_OWNER_BOUNDARY_CONTRACT_FOCUSED_NODES:
        if _repo_pytest_target_exists(node):
            targets.append(node)
    if len(targets) != len(RECONCILIATION_DECIMAL_FLOAT_OWNER_BOUNDARY_CONTRACT_FOCUSED_NODES):
        return ()
    if files and any(
        path in RECONCILIATION_DECIMAL_FLOAT_OWNER_BOUNDARY_CONTRACT_CI_POLICY_PATHS
        for path in files
    ):
        for ci_target in RECONCILIATION_DECIMAL_FLOAT_OWNER_BOUNDARY_CONTRACT_CI_SELECTOR_TARGETS:
            if _repo_pytest_target_exists(ci_target):
                targets.append(ci_target)
    return tuple(sorted(set(targets)))


def _try_reconciliation_decimal_float_owner_boundary_contract_focused(
    files: list[str],
) -> SelectionResult | None:
    if not _is_reconciliation_decimal_float_owner_boundary_scope(files):
        return None
    targets = _reconciliation_decimal_float_owner_boundary_focused_targets(files)
    if not targets:
        return None
    return SelectionResult(
        "FOCUSED",
        "reconciliation_decimal_float_owner_boundary_contract_focused",
        targets,
        (),
    )


def _is_dynamic_scope_owner_boundary_scoped_path(path: str) -> bool:
    return path in DYNAMIC_SCOPE_OWNER_BOUNDARY_CONTRACT_SCOPED_PATHS


def _is_dynamic_scope_owner_boundary_rebundle_path(path: str) -> bool:
    return _is_dynamic_scope_owner_boundary_scoped_path(path)


def _is_dynamic_scope_owner_boundary_scope(files: list[str]) -> bool:
    if not files:
        return False
    files_set = set(files)
    if DYNAMIC_SCOPE_OWNER_BOUNDARY_CONTRACT_TEST_OWNER not in files_set:
        return False
    return all(path in DYNAMIC_SCOPE_OWNER_BOUNDARY_CONTRACT_SCOPED_PATHS for path in files)


def _dynamic_scope_owner_boundary_focused_targets(
    files: list[str] | None = None,
) -> tuple[str, ...]:
    if not _repo_path_exists(DYNAMIC_SCOPE_OWNER_BOUNDARY_CONTRACT_TEST_OWNER):
        return ()
    targets: list[str] = []
    for node in DYNAMIC_SCOPE_OWNER_BOUNDARY_CONTRACT_FOCUSED_NODES:
        if _repo_pytest_target_exists(node):
            targets.append(node)
    if len(targets) != len(DYNAMIC_SCOPE_OWNER_BOUNDARY_CONTRACT_FOCUSED_NODES):
        return ()
    if files and any(
        path in DYNAMIC_SCOPE_OWNER_BOUNDARY_CONTRACT_CI_POLICY_PATHS for path in files
    ):
        for ci_target in DYNAMIC_SCOPE_OWNER_BOUNDARY_CONTRACT_CI_SELECTOR_TARGETS:
            if _repo_pytest_target_exists(ci_target):
                targets.append(ci_target)
    return tuple(sorted(set(targets)))


def _try_dynamic_scope_owner_boundary_contract_focused(
    files: list[str],
) -> SelectionResult | None:
    if not _is_dynamic_scope_owner_boundary_scope(files):
        return None
    targets = _dynamic_scope_owner_boundary_focused_targets(files)
    if not targets:
        return None
    return SelectionResult(
        "FOCUSED",
        "dynamic_scope_owner_boundary_contract_focused",
        targets,
        (),
    )


def _is_state_switch_owner_boundary_scoped_path(path: str) -> bool:
    return path in STATE_SWITCH_OWNER_BOUNDARY_CONTRACT_SCOPED_PATHS


def _is_state_switch_owner_boundary_rebundle_path(path: str) -> bool:
    return _is_state_switch_owner_boundary_scoped_path(path)


def _is_state_switch_owner_boundary_scope(files: list[str]) -> bool:
    if not files:
        return False
    files_set = set(files)
    if STATE_SWITCH_OWNER_BOUNDARY_CONTRACT_TEST_OWNER not in files_set:
        return False
    return all(path in STATE_SWITCH_OWNER_BOUNDARY_CONTRACT_SCOPED_PATHS for path in files)


def _state_switch_owner_boundary_focused_targets(
    files: list[str] | None = None,
) -> tuple[str, ...]:
    if not _repo_path_exists(STATE_SWITCH_OWNER_BOUNDARY_CONTRACT_TEST_OWNER):
        return ()
    targets: list[str] = []
    for node in STATE_SWITCH_OWNER_BOUNDARY_CONTRACT_FOCUSED_NODES:
        if _repo_pytest_target_exists(node):
            targets.append(node)
    if len(targets) != len(STATE_SWITCH_OWNER_BOUNDARY_CONTRACT_FOCUSED_NODES):
        return ()
    if files and any(
        path in STATE_SWITCH_OWNER_BOUNDARY_CONTRACT_CI_POLICY_PATHS for path in files
    ):
        for ci_target in STATE_SWITCH_OWNER_BOUNDARY_CONTRACT_CI_SELECTOR_TARGETS:
            if _repo_pytest_target_exists(ci_target):
                targets.append(ci_target)
    return tuple(sorted(set(targets)))


def _try_state_switch_owner_boundary_contract_focused(
    files: list[str],
) -> SelectionResult | None:
    if not _is_state_switch_owner_boundary_scope(files):
        return None
    targets = _state_switch_owner_boundary_focused_targets(files)
    if not targets:
        return None
    return SelectionResult(
        "FOCUSED",
        "state_switch_owner_boundary_contract_focused",
        targets,
        (),
    )


def _is_capital_slot_owner_boundary_scoped_path(path: str) -> bool:
    return path in CAPITAL_SLOT_OWNER_BOUNDARY_CONTRACT_SCOPED_PATHS


def _is_capital_slot_owner_boundary_rebundle_path(path: str) -> bool:
    return _is_capital_slot_owner_boundary_scoped_path(path)


def _is_capital_slot_owner_boundary_scope(files: list[str]) -> bool:
    if not files:
        return False
    files_set = set(files)
    if CAPITAL_SLOT_OWNER_BOUNDARY_CONTRACT_TEST_OWNER not in files_set:
        return False
    return all(path in CAPITAL_SLOT_OWNER_BOUNDARY_CONTRACT_SCOPED_PATHS for path in files)


def _capital_slot_owner_boundary_focused_targets(
    files: list[str] | None = None,
) -> tuple[str, ...]:
    if not _repo_path_exists(CAPITAL_SLOT_OWNER_BOUNDARY_CONTRACT_TEST_OWNER):
        return ()
    targets: list[str] = []
    for node in CAPITAL_SLOT_OWNER_BOUNDARY_CONTRACT_FOCUSED_NODES:
        if _repo_pytest_target_exists(node):
            targets.append(node)
    if len(targets) != len(CAPITAL_SLOT_OWNER_BOUNDARY_CONTRACT_FOCUSED_NODES):
        return ()
    if files and any(
        path in CAPITAL_SLOT_OWNER_BOUNDARY_CONTRACT_CI_POLICY_PATHS for path in files
    ):
        for ci_target in CAPITAL_SLOT_OWNER_BOUNDARY_CONTRACT_CI_SELECTOR_TARGETS:
            if _repo_pytest_target_exists(ci_target):
                targets.append(ci_target)
    return tuple(sorted(set(targets)))


def _try_capital_slot_owner_boundary_contract_focused(
    files: list[str],
) -> SelectionResult | None:
    if not _is_capital_slot_owner_boundary_scope(files):
        return None
    targets = _capital_slot_owner_boundary_focused_targets(files)
    if not targets:
        return None
    return SelectionResult(
        "FOCUSED",
        "capital_slot_owner_boundary_contract_focused",
        targets,
        (),
    )


def _is_pe22_durable_completion_binding_scoped_path(path: str) -> bool:
    return path in PE22_DURABLE_COMPLETION_BINDING_SCOPED_PATHS


def _is_pe22_durable_completion_binding_rebundle_path(path: str) -> bool:
    return _is_pe22_durable_completion_binding_scoped_path(path)


def _is_pe22_durable_completion_binding_scope(files: list[str]) -> bool:
    if not files:
        return False
    files_set = set(files)
    if PE22_DURABLE_COMPLETION_BINDING_CONTRACT_TEST_OWNER not in files_set:
        return False
    return all(path in PE22_DURABLE_COMPLETION_BINDING_SCOPED_PATHS for path in files)


def _pe22_durable_completion_binding_focused_targets(
    files: list[str] | None = None,
) -> tuple[str, ...]:
    if not _repo_path_exists(PE22_DURABLE_COMPLETION_BINDING_CONTRACT_TEST_OWNER):
        return ()
    targets: list[str] = []
    for node in PE22_DURABLE_COMPLETION_BINDING_FOCUSED_NODES:
        if _repo_pytest_target_exists(node):
            targets.append(node)
    if len(targets) != len(PE22_DURABLE_COMPLETION_BINDING_FOCUSED_NODES):
        return ()
    if files and any(path in PE22_DURABLE_COMPLETION_BINDING_CI_POLICY_PATHS for path in files):
        for ci_target in PE22_DURABLE_COMPLETION_BINDING_CI_SELECTOR_TARGETS:
            if _repo_pytest_target_exists(ci_target):
                targets.append(ci_target)
    return tuple(sorted(set(targets)))


def _try_pe22_durable_completion_binding_contract_focused(
    files: list[str],
) -> SelectionResult | None:
    if not _is_pe22_durable_completion_binding_scope(files):
        return None
    targets = _pe22_durable_completion_binding_focused_targets(files)
    if not targets:
        return None
    return SelectionResult(
        "FOCUSED",
        "pe22_durable_completion_binding_focused",
        targets,
        (),
    )


def _is_inv016_durable_completion_binding_scoped_path(path: str) -> bool:
    return path in INV016_DURABLE_COMPLETION_BINDING_SCOPED_PATHS


def _is_inv016_durable_completion_binding_rebundle_path(path: str) -> bool:
    return _is_inv016_durable_completion_binding_scoped_path(path)


def _is_inv016_durable_completion_binding_scope(files: list[str]) -> bool:
    if not files:
        return False
    files_set = set(files)
    if INV016_DURABLE_COMPLETION_BINDING_CONTRACT_TEST_OWNER not in files_set:
        return False
    return all(path in INV016_DURABLE_COMPLETION_BINDING_SCOPED_PATHS for path in files)


def _inv016_durable_completion_binding_focused_targets(
    files: list[str] | None = None,
) -> tuple[str, ...]:
    if not _repo_path_exists(INV016_DURABLE_COMPLETION_BINDING_CONTRACT_TEST_OWNER):
        return ()
    targets: list[str] = []
    for node in INV016_DURABLE_COMPLETION_BINDING_FOCUSED_NODES:
        if _repo_pytest_target_exists(node):
            targets.append(node)
    if len(targets) != len(INV016_DURABLE_COMPLETION_BINDING_FOCUSED_NODES):
        return ()
    if files and any(path in INV016_DURABLE_COMPLETION_BINDING_CI_POLICY_PATHS for path in files):
        for ci_target in INV016_DURABLE_COMPLETION_BINDING_CI_SELECTOR_TARGETS:
            if _repo_pytest_target_exists(ci_target):
                targets.append(ci_target)
    return tuple(sorted(set(targets)))


def _try_inv016_durable_completion_binding_contract_focused(
    files: list[str],
) -> SelectionResult | None:
    if not _is_inv016_durable_completion_binding_scope(files):
        return None
    targets = _inv016_durable_completion_binding_focused_targets(files)
    if not targets:
        return None
    return SelectionResult(
        "FOCUSED",
        "inv016_durable_completion_binding_focused",
        targets,
        (),
    )


def _is_master_v2_arithmetic_decimal_float_conversion_boundary_scoped_path(path: str) -> bool:
    return path in MASTER_V2_ARITHMETIC_DECIMAL_FLOAT_CONVERSION_BOUNDARY_CONTRACT_SCOPED_PATHS


def _is_master_v2_arithmetic_decimal_float_conversion_boundary_rebundle_path(path: str) -> bool:
    return _is_master_v2_arithmetic_decimal_float_conversion_boundary_scoped_path(path)


def _is_master_v2_arithmetic_decimal_float_conversion_boundary_scope(files: list[str]) -> bool:
    if not files:
        return False
    files_set = set(files)
    if MASTER_V2_ARITHMETIC_DECIMAL_FLOAT_CONVERSION_BOUNDARY_CONTRACT_TEST_OWNER not in files_set:
        return False
    return all(
        path in MASTER_V2_ARITHMETIC_DECIMAL_FLOAT_CONVERSION_BOUNDARY_CONTRACT_SCOPED_PATHS
        for path in files
    )


def _master_v2_arithmetic_decimal_float_conversion_boundary_focused_targets(
    files: list[str] | None = None,
) -> tuple[str, ...]:
    if not _repo_path_exists(
        MASTER_V2_ARITHMETIC_DECIMAL_FLOAT_CONVERSION_BOUNDARY_CONTRACT_TEST_OWNER
    ):
        return ()
    targets: list[str] = []
    for node in MASTER_V2_ARITHMETIC_DECIMAL_FLOAT_CONVERSION_BOUNDARY_CONTRACT_FOCUSED_NODES:
        if _repo_pytest_target_exists(node):
            targets.append(node)
    if len(targets) != len(
        MASTER_V2_ARITHMETIC_DECIMAL_FLOAT_CONVERSION_BOUNDARY_CONTRACT_FOCUSED_NODES
    ):
        return ()
    if files and any(
        path in MASTER_V2_ARITHMETIC_DECIMAL_FLOAT_CONVERSION_BOUNDARY_CONTRACT_CI_POLICY_PATHS
        for path in files
    ):
        for (
            ci_target
        ) in MASTER_V2_ARITHMETIC_DECIMAL_FLOAT_CONVERSION_BOUNDARY_CONTRACT_CI_SELECTOR_TARGETS:
            if _repo_pytest_target_exists(ci_target):
                targets.append(ci_target)
    return tuple(sorted(set(targets)))


def _try_master_v2_arithmetic_decimal_float_conversion_boundary_contract_focused(
    files: list[str],
) -> SelectionResult | None:
    if not _is_master_v2_arithmetic_decimal_float_conversion_boundary_scope(files):
        return None
    targets = _master_v2_arithmetic_decimal_float_conversion_boundary_focused_targets(files)
    if not targets:
        return None
    return SelectionResult(
        "FOCUSED",
        "master_v2_arithmetic_decimal_float_conversion_boundary_contract_focused",
        targets,
        (),
    )


def _is_master_v2_arithmetic_decimal_float_conversion_implementation_scoped_path(path: str) -> bool:
    return path in MASTER_V2_ARITHMETIC_DECIMAL_FLOAT_CONVERSION_IMPLEMENTATION_SCOPED_PATHS


def _is_master_v2_arithmetic_decimal_float_conversion_implementation_rebundle_path(
    path: str,
) -> bool:
    return _is_master_v2_arithmetic_decimal_float_conversion_implementation_scoped_path(path)


def _is_master_v2_arithmetic_decimal_float_conversion_implementation_scope(
    files: list[str],
) -> bool:
    if not files:
        return False
    files_set = set(files)
    if MASTER_V2_ARITHMETIC_DECIMAL_FLOAT_CONVERSION_IMPLEMENTATION_TEST_OWNER not in files_set:
        return False
    return all(
        path in MASTER_V2_ARITHMETIC_DECIMAL_FLOAT_CONVERSION_IMPLEMENTATION_SCOPED_PATHS
        for path in files
    )


def _master_v2_arithmetic_decimal_float_conversion_implementation_focused_targets(
    files: list[str] | None = None,
) -> tuple[str, ...]:
    if not _repo_path_exists(
        MASTER_V2_ARITHMETIC_DECIMAL_FLOAT_CONVERSION_IMPLEMENTATION_TEST_OWNER
    ):
        return ()
    targets: list[str] = []
    for node in MASTER_V2_ARITHMETIC_DECIMAL_FLOAT_CONVERSION_IMPLEMENTATION_FOCUSED_NODES:
        if _repo_pytest_target_exists(node):
            targets.append(node)
    if len(targets) != len(
        MASTER_V2_ARITHMETIC_DECIMAL_FLOAT_CONVERSION_IMPLEMENTATION_FOCUSED_NODES
    ):
        return ()
    if files and any(
        path in MASTER_V2_ARITHMETIC_DECIMAL_FLOAT_CONVERSION_IMPLEMENTATION_CI_POLICY_PATHS
        for path in files
    ):
        for (
            ci_target
        ) in MASTER_V2_ARITHMETIC_DECIMAL_FLOAT_CONVERSION_IMPLEMENTATION_CI_SELECTOR_TARGETS:
            if _repo_pytest_target_exists(ci_target):
                targets.append(ci_target)
    return tuple(sorted(set(targets)))


def _try_master_v2_arithmetic_decimal_float_conversion_implementation_focused(
    files: list[str],
) -> SelectionResult | None:
    if not _is_master_v2_arithmetic_decimal_float_conversion_implementation_scope(files):
        return None
    targets = _master_v2_arithmetic_decimal_float_conversion_implementation_focused_targets(files)
    if not targets:
        return None
    return SelectionResult(
        "FOCUSED",
        "master_v2_arithmetic_decimal_float_conversion_implementation_focused",
        targets,
        ("src.trading.master_v2.arithmetic_decimal_float_conversion_v0",),
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
    files_set = set(files)
    for path in files:
        if (
            path
            not in BOUNDED_TESTNET_EXECUTE_PATH_MARKET_OBSERVATION_CLOSEOUT_BINDING_SCOPED_PATHS
        ):
            return False
    assertion_only_rebundle = frozenset(
        {
            BOUNDED_MASTER_V2_TESTNET_COMPLETION_PATH_WIRING_ADAPTER_TEST_OWNER,
            "scripts/ops/ci_test_selection_v1.py",
        }
    )
    if files_set == assertion_only_rebundle:
        return True
    required = {
        BOUNDED_MASTER_V2_TESTNET_COMPLETION_PATH_WIRING_ADAPTER_OWNER,
        BOUNDED_MASTER_V2_TESTNET_COMPLETION_PATH_WIRING_ADAPTER_TEST_OWNER,
    }
    if not required.issubset(files_set):
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


def _normalize_changed_files(files: list[str]) -> tuple[str, ...]:
    return tuple(sorted({PurePosixPath(f).as_posix() for f in files if f.strip()}))


def _is_glb019_a2b_structural_contract_candidate(changed_files: list[str]) -> bool:
    return is_glb019_a2b_structural_contract_candidate(changed_files)


def _is_established_durable_completion_rebinding_scope(files: list[str]) -> bool:
    if _is_durable_completion_wallclock_binding_rebinding_scope(files):
        return True
    if _is_durable_completion_validator_rebinding_scope(files):
        return True
    if not files:
        return False
    files_set = set(files)
    if (
        DURABLE_COMPLETION_FACADE_PATH in files_set
        and DURABLE_COMPLETION_VALIDATION_GRAPH_TEST_OWNER in files_set
        and any(
            path.startswith("src/ops/durable_completion_validation/") and path.endswith(".py")
            for path in files
        )
        and all(_is_durable_completion_rebundle_path(path) for path in files)
    ):
        return True
    return False


def _is_glb019_partition_bootstrap_plus_central_prod_mix(changed_files: list[str]) -> bool:
    """Fail-closed only for GLB-019 partition bootstrap mixed with central completion prod."""
    normalized = list(_normalize_changed_files(changed_files))
    if not normalized:
        return False
    if _is_glb019_a2b_structural_contract_candidate(normalized):
        return False
    central_prod_paths = {DURABLE_COMPLETION_FACADE_PATH, DURABLE_COMPLETION_INTEGRATION_TEST_OWNER}
    if not any(path in central_prod_paths for path in normalized):
        return False
    bootstrap_slice = frozenset(
        {
            DURABLE_COMPLETION_INTEGRATION_PARTITIONS_HELPER,
            "tests/ci/test_ci_diff_aware_test_selection_v1.py",
            GLB019_A2B_SELECTOR_OWNER,
        }
    )
    if not any(path in bootstrap_slice for path in normalized):
        return False
    if _is_established_durable_completion_rebinding_scope(normalized):
        return False
    return True


def _glb019_a2b_unparseable_fallback_targets() -> tuple[str, ...]:
    targets: list[str] = []
    for path in (
        DURABLE_COMPLETION_VALIDATION_GRAPH_TEST_OWNER,
        "tests/ci/test_ci_diff_aware_test_selection_v1.py",
        DURABLE_COMPLETION_INTEGRATION_TEST_OWNER,
    ):
        if _repo_path_exists(path):
            targets.append(path)
    return tuple(sorted(set(targets)))


def _selection_result_for_glb019_a2b_change_contract(
    files: list[str],
    contract: Glb019A2bChangeContractResult,
    *,
    patch_text: str | None,
) -> SelectionResult | None:
    if contract.outcome == Glb019A2bChangeContractOutcome.PASS:
        targets = _durable_completion_focused_targets(files, patch_text=patch_text)
        if not targets:
            return None
        return SelectionResult(
            "FOCUSED",
            "glb019_a2b_additive_change_contract",
            targets,
            (
                "src.ops.bounded_futures_testnet_durable_run_primary_evidence_completion_integration_contract_v0",
                "src.ops.durable_completion_validation",
            ),
        )
    if contract.outcome == Glb019A2bChangeContractOutcome.REJECT:
        return SelectionResult("FULL", "durable_completion_foreign_path_requires_full", ())
    if contract.outcome == Glb019A2bChangeContractOutcome.UNAVAILABLE_OR_UNPARSEABLE:
        targets = _glb019_a2b_unparseable_fallback_targets()
        if not targets:
            return None
        return SelectionResult(
            "FOCUSED",
            "durable_completion_focused",
            targets,
            (
                "src.ops.bounded_futures_testnet_durable_run_primary_evidence_completion_integration_contract_v0",
                "src.ops.durable_completion_validation",
            ),
        )
    return None


def _effective_glb019_patch_text(
    changed_files: list[str],
    patch_text: str | None,
) -> str | None:
    if not patch_text:
        return None
    if not _is_glb019_a2b_structural_contract_candidate(changed_files):
        return None
    return patch_text


def _try_durable_completion_focused(
    files: list[str],
    *,
    patch_text: str | None = None,
) -> SelectionResult | None:
    if not files:
        return None
    if _is_glb019_partition_bootstrap_plus_central_prod_mix(files):
        return None
    if not _has_durable_completion_integration_partition_scope(files):
        return None
    if not all(
        _is_durable_completion_integration_partition_rebundle_path(f, files=files) for f in files
    ):
        return None
    if _is_pe31_durable_completion_binding_testowner_only_scope(files):
        partition_selection = partitions_for_changed_files(files)
        if (
            partition_selection is not None
            and _partition_selection_uses_pe31_durable_completion_binding(partition_selection)
        ):
            targets = _durable_completion_focused_targets(files, patch_text=patch_text)
            if targets:
                return SelectionResult(
                    "FOCUSED",
                    "durable_completion_focused",
                    targets,
                    (
                        "src.ops.bounded_futures_testnet_durable_run_primary_evidence_completion_integration_contract_v0",
                        "src.ops.durable_completion_validation",
                    ),
                )
        if (
            partition_selection is None
            and len(files) == 1
            and files[0] == DURABLE_COMPLETION_INTEGRATION_TEST_OWNER
        ):
            return None
    patch_text = _effective_glb019_patch_text(files, patch_text)
    selector_owner_changed = GLB019_A2B_SELECTOR_OWNER in files
    guarded_mixed_candidate = _is_glb019_a2b_structural_contract_candidate(files)
    if selector_owner_changed and guarded_mixed_candidate:
        if not patch_text:
            return None
        if not patch_includes_glb019_guarded_selector_owner_rewire(
            patch_text,
            changed_files=files,
        ):
            return None
        contract = evaluate_glb019_a2b_change_contract(patch_text, repo_root=_REPO_ROOT)
        return _selection_result_for_glb019_a2b_change_contract(
            files,
            contract,
            patch_text=patch_text,
        )
    central_prod_paths = {DURABLE_COMPLETION_FACADE_PATH, DURABLE_COMPLETION_INTEGRATION_TEST_OWNER}
    has_central_prod = any(path in central_prod_paths for path in files)
    skip_glb019_central_prod_gate = _is_pe31_durable_completion_binding_testowner_only_scope(files)
    if (
        has_central_prod
        and _is_glb019_a2b_structural_contract_candidate(files)
        and not skip_glb019_central_prod_gate
    ):
        if patch_text:
            contract = evaluate_glb019_a2b_change_contract(patch_text, repo_root=_REPO_ROOT)
            glb019_selection = _selection_result_for_glb019_a2b_change_contract(
                files,
                contract,
                patch_text=patch_text,
            )
            if glb019_selection is not None:
                return glb019_selection
            return None
        if len(files) == 1 and files[0] in central_prod_paths:
            return None
    glb019_contract = (
        classify_glb019_a2b_additive_patch(patch_text, repo_root=_REPO_ROOT) if patch_text else None
    )
    targets = _durable_completion_focused_targets(files, patch_text=patch_text)
    if not targets:
        return None
    if glb019_contract is not None:
        return SelectionResult(
            "FOCUSED",
            "glb019_a2b_additive_change_contract",
            targets,
            (
                "src.ops.bounded_futures_testnet_durable_run_primary_evidence_completion_integration_contract_v0",
                "src.ops.durable_completion_validation",
            ),
        )
    integration_required = _requires_durable_completion_integration_test_owner(files)
    if _is_durable_completion_wallclock_binding_rebinding_scope(files):
        modules: tuple[str, ...] = (
            "src.ops.bounded_futures_testnet_durable_run_primary_evidence_completion_integration_contract_v0",
        )
        reason = "durable_completion_focused"
    elif integration_required:
        modules = (
            "src.ops.bounded_futures_testnet_durable_run_primary_evidence_completion_integration_contract_v0",
            "src.ops.durable_completion_validation",
        )
        reason = "durable_completion_focused"
    else:
        modules = ("src.ops.durable_completion_validation",)
        reason = "durable_completion_validation_graph_focused"
    return SelectionResult(
        "FOCUSED",
        reason,
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
    if p in OKX_EUROPE_ADAPTER_LIFECYCLE_CI_POLICY_PATHS:
        return "okx_europe_adapter_lifecycle_focused"
    if _is_okx_europe_adapter_lifecycle_scoped_path(p):
        return "okx_europe_adapter_lifecycle_focused"
    if p in BOUNDED_FUTURES_TESTNET_CONTRACT_CI_POLICY_PATHS:
        return "bounded_futures_testnet_contract_focused"
    if _is_bounded_futures_testnet_contract_scoped_path(p):
        return "bounded_futures_testnet_contract_focused"
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
            if path == "scripts/run_promotion_proposal_cycle.py":
                for candidate in PR_BOUNDED_FULL_PACKAGE_B_PROMOTION_INPUT_TARGETS:
                    add(candidate)
            elif path == "scripts/run_learning_manifest_bridge_v1.py":
                for candidate in PR_BOUNDED_FULL_PACKAGE_D_LEARNING_BRIDGE_TARGETS:
                    add(candidate)
            elif path == "scripts/run_candidate_lineage_manifest_v1.py":
                for candidate in PR_BOUNDED_FULL_PACKAGE_F_CANDIDATE_LINEAGE_PRODUCTION_TARGETS:
                    add(candidate)
            elif path == "scripts/run_backtest_lineage_ref_producer_v1.py":
                for candidate in PR_BOUNDED_FULL_PACKAGE_F_CANDIDATE_LINEAGE_PRODUCTION_TARGETS:
                    add(candidate)
            elif path == "scripts/run_var_suite_lineage_ref_producer_v1.py":
                for candidate in PR_BOUNDED_FULL_PACKAGE_F_CANDIDATE_LINEAGE_PRODUCTION_TARGETS:
                    add(candidate)
            elif path == "scripts/run_learning_manifest_durable_evidence_binding_v1.py":
                for candidate in PR_BOUNDED_FULL_PACKAGE_G_LEARNING_DURABLE_EVIDENCE_TARGETS:
                    add(candidate)
            elif path == "scripts/run_var_suite_durable_evidence_binding_v1.py":
                for candidate in PR_BOUNDED_FULL_PACKAGE_K_VAR_SUITE_DURABLE_EVIDENCE_TARGETS:
                    add(candidate)
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
    files: list[str],
    *,
    force_full: bool = False,
    force_exhaustive: bool = False,
    event_name: str = "pull_request",
    patch_text: str | None = None,
) -> SelectionResult:
    normalized = sorted({PurePosixPath(f).as_posix() for f in files if f.strip()})
    exhaustive_requested = force_exhaustive or force_full
    if exhaustive_requested and event_name in EXHAUSTIVE_AUTHORIZED_EVENTS:
        return SelectionResult("EXHAUSTIVE_FULL", "force_exhaustive_authorized_event", ())
    if not normalized:
        return SelectionResult("FULL", "empty_diff_fail_closed", ())

    market_dashboard = _try_market_dashboard_focused(normalized)
    if market_dashboard is not None:
        return market_dashboard

    master_v2_binding = _try_master_v2_binding_contract_focused(normalized)
    if master_v2_binding is not None:
        return master_v2_binding

    master_v2_arithmetic_kernel_seam = (
        _try_master_v2_arithmetic_kernel_seam_fail_closed_contract_focused(normalized)
    )
    if master_v2_arithmetic_kernel_seam is not None:
        return master_v2_arithmetic_kernel_seam

    duplicate_pnl_owner_boundary = _try_duplicate_pnl_owner_boundary_contract_focused(normalized)
    if duplicate_pnl_owner_boundary is not None:
        return duplicate_pnl_owner_boundary

    reconciliation_decimal_float_owner_boundary = (
        _try_reconciliation_decimal_float_owner_boundary_contract_focused(normalized)
    )
    if reconciliation_decimal_float_owner_boundary is not None:
        return reconciliation_decimal_float_owner_boundary

    dynamic_scope_owner_boundary = _try_dynamic_scope_owner_boundary_contract_focused(normalized)
    if dynamic_scope_owner_boundary is not None:
        return dynamic_scope_owner_boundary

    state_switch_owner_boundary = _try_state_switch_owner_boundary_contract_focused(normalized)
    if state_switch_owner_boundary is not None:
        return state_switch_owner_boundary

    capital_slot_owner_boundary = _try_capital_slot_owner_boundary_contract_focused(normalized)
    if capital_slot_owner_boundary is not None:
        return capital_slot_owner_boundary

    pe22_durable_completion_binding = _try_pe22_durable_completion_binding_contract_focused(
        normalized
    )
    if pe22_durable_completion_binding is not None:
        return pe22_durable_completion_binding

    inv016_durable_completion_binding = _try_inv016_durable_completion_binding_contract_focused(
        normalized
    )
    if inv016_durable_completion_binding is not None:
        return inv016_durable_completion_binding

    master_v2_arithmetic_decimal_float_conversion_boundary = (
        _try_master_v2_arithmetic_decimal_float_conversion_boundary_contract_focused(normalized)
    )
    if master_v2_arithmetic_decimal_float_conversion_boundary is not None:
        return master_v2_arithmetic_decimal_float_conversion_boundary

    master_v2_arithmetic_decimal_float_conversion_implementation = (
        _try_master_v2_arithmetic_decimal_float_conversion_implementation_focused(normalized)
    )
    if master_v2_arithmetic_decimal_float_conversion_implementation is not None:
        return master_v2_arithmetic_decimal_float_conversion_implementation

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

    effective_patch = _effective_glb019_patch_text(normalized, patch_text)
    durable_completion = _try_durable_completion_focused(normalized, patch_text=effective_patch)
    if durable_completion is not None:
        return durable_completion

    ci_bootstrap = _try_ci_bootstrap_focused(normalized)
    if ci_bootstrap is not None:
        return ci_bootstrap

    if _is_glb019_partition_bootstrap_plus_central_prod_mix(normalized):
        return SelectionResult("FULL", "durable_completion_foreign_path_requires_full", ())

    preflight_assembly = _try_preflight_assembly_focused(normalized)
    if preflight_assembly is not None:
        return preflight_assembly

    okx_europe_adapter_lifecycle = _try_okx_europe_adapter_lifecycle_focused(normalized)
    if okx_europe_adapter_lifecycle is not None:
        return okx_europe_adapter_lifecycle

    bounded_futures_testnet_contract = _try_bounded_futures_testnet_contract_focused(normalized)
    if bounded_futures_testnet_contract is not None:
        return bounded_futures_testnet_contract

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

    ci_infra = _try_ci_infra_focused(normalized)
    if ci_infra is not None:
        return ci_infra

    if _has_durable_completion_integration_partition_scope(normalized):
        if not all(
            _is_durable_completion_integration_partition_rebundle_path(f, files=normalized)
            for f in normalized
        ):
            return SelectionResult("FULL", "durable_completion_foreign_path_requires_full", ())
        return SelectionResult("FULL", "durable_completion_incomplete_or_missing_test_owner", ())

    if any(_is_preflight_assembly_scoped_path(f) for f in normalized):
        if not all(_is_preflight_assembly_rebundle_path(f) for f in normalized):
            return SelectionResult("FULL", "preflight_assembly_foreign_path_requires_full", ())
        return SelectionResult("FULL", "preflight_assembly_incomplete_or_missing_test_owner", ())

    if any(_is_okx_europe_adapter_lifecycle_scoped_path(f) for f in normalized):
        if not all(_is_okx_europe_adapter_lifecycle_rebundle_path(f) for f in normalized):
            return SelectionResult(
                "FULL",
                "okx_europe_adapter_lifecycle_foreign_path_requires_full",
                (),
            )
        return SelectionResult(
            "FULL",
            "okx_europe_adapter_lifecycle_incomplete_or_missing_test_owner",
            (),
        )

    if any(_is_bounded_futures_testnet_contract_scoped_path(f) for f in normalized):
        if not all(_is_bounded_futures_testnet_contract_rebundle_path(f) for f in normalized):
            return SelectionResult(
                "FULL",
                "bounded_futures_testnet_contract_foreign_path_requires_full",
                (),
            )
        return SelectionResult(
            "FULL",
            "bounded_futures_testnet_contract_incomplete_or_missing_test_owner",
            (),
        )

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

    if any(_is_ci_bootstrap_scoped_path(f) for f in normalized):
        return SelectionResult("FULL", "ci_bootstrap_mixed_diff_requires_full", ())

    if any(_is_master_v2_arithmetic_kernel_seam_scoped_path(f) for f in normalized):
        if not all(_is_master_v2_arithmetic_kernel_seam_rebundle_path(f) for f in normalized):
            return SelectionResult(
                "FULL",
                "master_v2_arithmetic_kernel_seam_fail_closed_contract_foreign_path_requires_full",
                (),
            )
        return SelectionResult(
            "FULL",
            "master_v2_arithmetic_kernel_seam_fail_closed_contract_incomplete_or_missing_test_owner",
            (),
        )

    if any(_is_duplicate_pnl_owner_boundary_scoped_path(f) for f in normalized):
        if not all(_is_duplicate_pnl_owner_boundary_rebundle_path(f) for f in normalized):
            return SelectionResult(
                "FULL",
                "duplicate_pnl_owner_boundary_contract_foreign_path_requires_full",
                (),
            )
        return SelectionResult(
            "FULL",
            "duplicate_pnl_owner_boundary_contract_incomplete_or_missing_test_owner",
            (),
        )

    if any(_is_reconciliation_decimal_float_owner_boundary_scoped_path(f) for f in normalized):
        if not all(
            _is_reconciliation_decimal_float_owner_boundary_rebundle_path(f) for f in normalized
        ):
            return SelectionResult(
                "FULL",
                "reconciliation_decimal_float_owner_boundary_contract_foreign_path_requires_full",
                (),
            )
        return SelectionResult(
            "FULL",
            "reconciliation_decimal_float_owner_boundary_contract_incomplete_or_missing_test_owner",
            (),
        )

    if any(_is_dynamic_scope_owner_boundary_scoped_path(f) for f in normalized):
        if not all(_is_dynamic_scope_owner_boundary_rebundle_path(f) for f in normalized):
            return SelectionResult(
                "FULL",
                "dynamic_scope_owner_boundary_contract_foreign_path_requires_full",
                (),
            )
        return SelectionResult(
            "FULL",
            "dynamic_scope_owner_boundary_contract_incomplete_or_missing_test_owner",
            (),
        )

    if any(_is_state_switch_owner_boundary_scoped_path(f) for f in normalized):
        if not all(_is_state_switch_owner_boundary_rebundle_path(f) for f in normalized):
            return SelectionResult(
                "FULL",
                "state_switch_owner_boundary_contract_foreign_path_requires_full",
                (),
            )
        return SelectionResult(
            "FULL",
            "state_switch_owner_boundary_contract_incomplete_or_missing_test_owner",
            (),
        )

    if any(_is_capital_slot_owner_boundary_scoped_path(f) for f in normalized):
        if not all(_is_capital_slot_owner_boundary_rebundle_path(f) for f in normalized):
            return SelectionResult(
                "FULL",
                "capital_slot_owner_boundary_contract_foreign_path_requires_full",
                (),
            )
        return SelectionResult(
            "FULL",
            "capital_slot_owner_boundary_contract_incomplete_or_missing_test_owner",
            (),
        )

    if any(_is_pe22_durable_completion_binding_scoped_path(f) for f in normalized):
        if not all(_is_pe22_durable_completion_binding_rebundle_path(f) for f in normalized):
            return SelectionResult(
                "FULL",
                "pe22_durable_completion_binding_foreign_path_requires_full",
                (),
            )
        return SelectionResult(
            "FULL",
            "pe22_durable_completion_binding_incomplete_or_missing_test_owner",
            (),
        )

    if any(_is_inv016_durable_completion_binding_scoped_path(f) for f in normalized):
        if not all(_is_inv016_durable_completion_binding_rebundle_path(f) for f in normalized):
            return SelectionResult(
                "FULL",
                "inv016_durable_completion_binding_foreign_path_requires_full",
                (),
            )
        return SelectionResult(
            "FULL",
            "inv016_durable_completion_binding_incomplete_or_missing_test_owner",
            (),
        )

    if any(
        _is_master_v2_arithmetic_decimal_float_conversion_boundary_scoped_path(f)
        for f in normalized
    ):
        if not all(
            _is_master_v2_arithmetic_decimal_float_conversion_boundary_rebundle_path(f)
            for f in normalized
        ):
            return SelectionResult(
                "FULL",
                "master_v2_arithmetic_decimal_float_conversion_boundary_contract_foreign_path_requires_full",
                (),
            )
        return SelectionResult(
            "FULL",
            "master_v2_arithmetic_decimal_float_conversion_boundary_contract_incomplete_or_missing_test_owner",
            (),
        )

    if any(
        _is_master_v2_arithmetic_decimal_float_conversion_implementation_scoped_path(f)
        for f in normalized
    ):
        if not all(
            _is_master_v2_arithmetic_decimal_float_conversion_implementation_rebundle_path(f)
            for f in normalized
        ):
            return SelectionResult(
                "FULL",
                "master_v2_arithmetic_decimal_float_conversion_implementation_foreign_path_requires_full",
                (),
            )
        return SelectionResult(
            "FULL",
            "master_v2_arithmetic_decimal_float_conversion_implementation_incomplete_or_missing_test_owner",
            (),
        )

    if any(_is_wallclock_scoped_path(f) for f in normalized):
        if not all(_is_wallclock_rebundle_path(f) for f in normalized):
            return SelectionResult("FULL", "wallclock_foreign_path_requires_full", ())
        return SelectionResult("FULL", "wallclock_incomplete_or_missing_test_owner", ())

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
    parser.add_argument(
        "--force-exhaustive",
        action="store_true",
        help="Select EXHAUSTIVE_FULL (schedule/workflow_dispatch only)",
    )
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
    parser.add_argument(
        "--patch-file",
        type=Path,
        default=None,
        help="Unified diff patch for GLB-019 A2/B change-contract classification (tests/probes)",
    )
    parser.add_argument(
        "--diff-base-ref",
        default=os.environ.get("DIFF_BASE_REF", "origin/main"),
        help="Base ref for merge-base patch collection (CI path)",
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

    patch_text: str | None = None
    if args.patch_file is not None:
        if not args.patch_file.is_file():
            print(f"missing patch file: {args.patch_file}", file=sys.stderr)
            return 1
        patch_text = args.patch_file.read_text(encoding="utf-8")
    elif _is_glb019_a2b_structural_contract_candidate(
        files
    ) and not _is_pe31_durable_completion_binding_testowner_only_scope(files):
        patch_text = collect_glb019_a2b_patch_text(
            base_ref=args.diff_base_ref,
            repo_root=_REPO_ROOT,
            changed_files=files,
        )

    matrix_contract = resolve_matrix_contract_selection(files)
    result = resolve_selection(
        files,
        force_full=args.force_full,
        force_exhaustive=args.force_exhaustive,
        event_name=args.event_name,
        patch_text=patch_text,
    )
    if matrix_contract.mode == "MATRIX_CONTRACT_FOCUSED":
        result = SelectionResult(
            "FOCUSED",
            matrix_contract.reason,
            matrix_contract.pytest_targets,
        )
    result = _finalize_selection_result(
        result,
        files,
        event_name=args.event_name,
        force_exhaustive=args.force_exhaustive
        or (args.force_full and args.event_name in EXHAUSTIVE_AUTHORIZED_EVENTS),
    )
    lines = result.github_output_lines()
    lines.extend(matrix_contract.github_output_lines())
    lines.extend(resolve_fast_lane_contract_selection(files).github_output_lines())
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
