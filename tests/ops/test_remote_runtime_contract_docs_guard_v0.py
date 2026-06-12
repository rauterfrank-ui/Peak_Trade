"""Static docs guard for external Remote Runtime Charter v0 reflection.

Reads docs/ops/CI_AUDIT_KNOWN_ISSUES.md and DOCS_TRUTH_MAP only. Never starts
runtime, touches AWS/S3/Notion/Market production surfaces, or grants GO.
"""

from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
CI_AUDIT = REPO_ROOT / "docs" / "ops" / "CI_AUDIT_KNOWN_ISSUES.md"
DOCS_TRUTH_MAP = REPO_ROOT / "docs" / "ops" / "registry" / "DOCS_TRUTH_MAP.md"
TAXONOMY_SPEC = (
    REPO_ROOT / "docs" / "ops" / "specs" / "RUNTIME_LANE_TAXONOMY_AUTHORITY_LEVELS_CONTRACT_V0.md"
)
THIS_MODULE = Path(__file__).name

CHARTER_PATH = (
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/"
    "planning/remote_runtime_charter_v0_20260601T120000Z"
)
CONSOLIDATION_PATH = (
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/"
    "planning/remote_runtime_consolidation_after_cyber_input_blocked_v0_20260601T110000Z"
)
LOCAL_DRY_HOST_PREFLIGHT_CHARTER_PATH = (
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/"
    "planning/local_dry_host_no_run_preflight_charter_v0_20260601T024302Z"
)

GUARD_BLOCK_ANCHOR = "REMOTE_RUNTIME_EXTERNAL_CHARTER_CONTRACT_DOCS_GUARD_V0=true"
LOCAL_DRY_HOST_GUARD_BLOCK_ANCHOR = "LOCAL_DRY_HOST_NO_RUN_PREFLIGHT_CHARTER_REFLECTION_V0=true"
PREFLIGHT_PROCESS_GATE_HYGIENE_HEADING = (
    "## Preflight Process Gate Hygiene — active-run false-positive guard v0"
)
PREFLIGHT_PROCESS_GATE_HYGIENE_GUARD_BLOCK_ANCHOR = "PREFLIGHT_PROCESS_GATE_HYGIENE_GUARD_V1=true"
PREFLIGHT_PROCESS_GATE_HYGIENE_INPUT_BUNDLE = (
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/"
    "planning/systemwide_next_safe_scope_ranking_after_pr4153_closeout_select_single_next_safe_slice_no_run_v1_20260612T000800Z"
)
ORDER_CAPABILITY_REMAINING_READINESS_GAP_REVIEW_HEADING = (
    "## Order-Capability remaining readiness gap review — docs/tests-only visibility v1"
)
ORDER_CAPABILITY_REMAINING_READINESS_GAP_REVIEW_GUARD_BLOCK_ANCHOR = (
    "ORDER_CAPABILITY_REMAINING_READINESS_GAP_REVIEW_V1=true"
)
ORDER_CAPABILITY_REMAINING_READINESS_GAP_REVIEW_INPUT_BUNDLE = (
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/"
    "planning/systemwide_next_safe_scope_ranking_after_preflight_process_gate_hygiene_guard_merge_no_run_v1_20260612T002508Z"
)
ORDER_CAPABILITY_REMAINING_READINESS_GAP_REVIEW_EXPECTED: dict[str, str] = {
    "ORDER_CAPABILITY_REMAINING_READINESS_GAP_REVIEW_V1": "true",
    "ORDER_CAPABILITY_REMAINING_READINESS_GAP_REVIEW_DOCS_TESTS_ONLY": "true",
    "ORDER_CAPABILITY_PARKED_READ_ONLY_CONFIRMED": "true",
    "ORDER_CAPABILITY_EXISTING_CROSSLINK_GUARDS_REFERENCED": "true",
    "FIXTURE_BINDING_CROSSLINK_GUARD_REFERENCED": "true",
    "DEMO_INSTRUMENT_RULES_NORMALIZER_CROSSLINK_GUARD_REFERENCED": "true",
    "REMAINING_CONTRACT_SURFACES_INDEXED": "true",
    "NO_RUNTIME": "true",
    "NO_LIVE": "true",
    "NO_PREFLIGHT_LIFT": "true",
    "ORDER_CANCEL_EXECUTION_ARMING_TOUCHED": "false",
    "AUTHORITY_LIFT": "false",
    "TRADING_LOGIC_TOUCHED": "false",
    "MASTER_V2_LOGIC_TOUCHED": "false",
    "DOUBLE_PLAY_LOGIC_TOUCHED": "false",
    "RISK_KILLSWITCH_SCOPE_CAPITAL_TOUCHED": "false",
    "NEW_PARALLEL_SSOT_CREATED": "false",
    "PREFLIGHT_REMAINS_BLOCKED": "true",
    "ORDERFLOW_AUTHORIZATION_CREATED": "false",
    "CANCEL_EXECUTE_AUTHORIZATION_CREATED": "false",
    "READY_FOR_OPERATOR_ARMING_CHANGED": "false",
    "RUNTIME_LOGIC_TOUCHED": "false",
    "JSONL_EVIDENCE_DATASET_MUTATION": "false",
    "WORKFLOW_TOUCHED": "false",
    "MARKET_DASHBOARD_TOUCHED": "false",
}
SYSTEMWIDE_CI_DOCS_TRUTH_MAP_RESIDUAL_REVIEW_HEADING = (
    "## Systemwide CI/Docs required-check truth-map residual review — docs/tests-only guard v1"
)
SYSTEMWIDE_CI_DOCS_TRUTH_MAP_RESIDUAL_REVIEW_GUARD_BLOCK_ANCHOR = (
    "SYSTEMWIDE_CI_DOCS_REQUIRED_CHECK_TRUTH_MAP_RESIDUAL_REVIEW_V1=true"
)
SYSTEMWIDE_CI_DOCS_TRUTH_MAP_RESIDUAL_REVIEW_INPUT_BUNDLE = (
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/"
    "planning/systemwide_next_safe_scope_ranking_after_order_capability_readiness_gap_review_merge_no_run_v1_20260612T003655Z"
)
SYSTEMWIDE_CI_DOCS_TRUTH_MAP_RESIDUAL_REVIEW_EXPECTED: dict[str, str] = {
    "SYSTEMWIDE_CI_DOCS_REQUIRED_CHECK_TRUTH_MAP_RESIDUAL_REVIEW_V1": "true",
    "SYSTEMWIDE_CI_DOCS_REQUIRED_CHECK_TRUTH_MAP_RESIDUAL_REVIEW_DOCS_TESTS_ONLY": "true",
    "REQUIRED_CHECK_SAFETY_GATE_SURFACES_INDEXED": "true",
    "DOCS_TOKEN_POLICY_GATE_REFERENCED": "true",
    "SAME_REPO_APPROVAL_HARD_RETRIGGER_GUIDANCE_REFERENCED": "true",
    "WORKFLOW_SECRETS_VISIBILITY_GUARD_REFERENCED": "true",
    "WORKFLOW_WRITE_PERMISSIONS_VISIBILITY_GUARD_REFERENCED": "true",
    "PRB_SCHEDULED_SCORECARD_POSTURE_GUARD_REFERENCED": "true",
    "GH_SCHEDULE_MANUAL_ONLY_POSTURE_GUARD_REFERENCED": "true",
    "EXISTING_CI_DOCS_GUARDS_REFERENCED": "true",
    "NO_RUNTIME": "true",
    "NO_LIVE": "true",
    "NO_PREFLIGHT_LIFT": "true",
    "ORDER_CANCEL_EXECUTION_ARMING_TOUCHED": "false",
    "AUTHORITY_LIFT": "false",
    "TRADING_LOGIC_TOUCHED": "false",
    "MASTER_V2_LOGIC_TOUCHED": "false",
    "DOUBLE_PLAY_LOGIC_TOUCHED": "false",
    "RISK_KILLSWITCH_SCOPE_CAPITAL_TOUCHED": "false",
    "NEW_PARALLEL_SSOT_CREATED": "false",
    "PREFLIGHT_REMAINS_BLOCKED": "true",
    "WORKFLOW_TOUCHED": "false",
    "WORKFLOW_DISPATCH_EXECUTED": "false",
    "GH_RUN_RERUN_EXECUTED": "false",
    "JSONL_EVIDENCE_DATASET_MUTATION": "false",
    "MARKET_DASHBOARD_TOUCHED": "false",
}
SYSTEMWIDE_CI_DOCS_TRUTH_MAP_RESIDUAL_REVIEW_OWNER_TESTS = (
    "test_required_checks_safety_gate_surfaces_v0.py",
    "test_workflow_secrets_reference_visibility_contract_v0.py",
    "test_workflow_write_permissions_visibility_contract_v0.py",
    "test_residual_prb_scheduled_scorecard_workflow_contract_v0.py",
)
PRIMARY_EVIDENCE_RETENTION_INVARIANT_RESIDUAL_STATIC_REVIEW_HEADING = (
    "## Primary evidence retention invariant residual static review — docs/tests-only guard v1"
)
PRIMARY_EVIDENCE_RETENTION_INVARIANT_RESIDUAL_STATIC_REVIEW_GUARD_BLOCK_ANCHOR = (
    "PRIMARY_EVIDENCE_RETENTION_INVARIANT_RESIDUAL_STATIC_REVIEW_V1=true"
)
PRIMARY_EVIDENCE_RETENTION_INVARIANT_RESIDUAL_STATIC_REVIEW_INPUT_BUNDLE = (
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/"
    "planning/systemwide_next_safe_scope_ranking_after_ci_docs_required_check_truth_map_residual_review_merge_no_run_v1_20260612T005020Z"
)
PRIMARY_EVIDENCE_RETENTION_INVARIANT_RESIDUAL_STATIC_REVIEW_EXPECTED: dict[str, str] = {
    "PRIMARY_EVIDENCE_RETENTION_INVARIANT_RESIDUAL_STATIC_REVIEW_V1": "true",
    "PRIMARY_EVIDENCE_RETENTION_INVARIANT_RESIDUAL_STATIC_REVIEW_DOCS_TESTS_ONLY": "true",
    "DURABLE_OUTSIDE_TMP_REQUIRED": "true",
    "MANIFEST_CREATION_REQUIRED": "true",
    "MANIFEST_VERIFICATION_REQUIRED": "true",
    "CHECKSUM_VERIFICATION_REQUIRED": "true",
    "CLOSEOUT_INCOMPLETE_WITHOUT_PRIMARY_EVIDENCE": "true",
    "TMP_ONLY_EVIDENCE_INVALID": "true",
    "PAPER_SHADOW_TESTNET_LIVE_APPLICABILITY_INDEXED": "true",
    "RUNTIME_SCHEDULER_SUPERVISOR_FLOWS_INDEXED": "true",
    "EXISTING_RETENTION_GUARDS_REFERENCED": "true",
    "NO_RUNTIME": "true",
    "NO_RUN_START": "true",
    "NO_LIVE": "true",
    "NO_PREFLIGHT_LIFT": "true",
    "ORDER_CANCEL_EXECUTION_ARMING_TOUCHED": "false",
    "AUTHORITY_LIFT": "false",
    "TRADING_LOGIC_TOUCHED": "false",
    "MASTER_V2_LOGIC_TOUCHED": "false",
    "DOUBLE_PLAY_LOGIC_TOUCHED": "false",
    "RISK_KILLSWITCH_SCOPE_CAPITAL_TOUCHED": "false",
    "NEW_PARALLEL_SSOT_CREATED": "false",
    "PREFLIGHT_REMAINS_BLOCKED": "true",
    "WORKFLOW_TOUCHED": "false",
    "WORKFLOW_DISPATCH_EXECUTED": "false",
    "GH_RUN_RERUN_EXECUTED": "false",
    "JSONL_EVIDENCE_DATASET_MUTATION": "false",
    "MARKET_DASHBOARD_TOUCHED": "false",
    "EVIDENCE_DATASET_MUTATION": "false",
}
PRIMARY_EVIDENCE_RETENTION_INVARIANT_RESIDUAL_STATIC_REVIEW_OWNER_TESTS = (
    "test_primary_evidence_retention_invariant_contract_v0.py",
    "test_run_primary_evidence_retention_hard_gate_v0.py",
    "test_durable_closeout_copy_verify_v0.py",
)
PAPER_L2_PREFLIGHT_2A_RECIPROCAL_CROSSLINK_HEADING = (
    "## Paper-L2 120min hold-binding Preflight §2a reciprocal crosslink — docs/tests-only guard v1"
)
PAPER_L2_PREFLIGHT_2A_RECIPROCAL_CROSSLINK_GUARD_BLOCK_ANCHOR = (
    "PAPER_L2_120MIN_HOLD_BINDING_PREFLIGHT_2A_RECIPROCAL_CROSSLINK_V1=true"
)
PAPER_L2_PREFLIGHT_2A_RECIPROCAL_CROSSLINK_EXPECTED: dict[str, str] = {
    "PAPER_L2_120MIN_HOLD_BINDING_PREFLIGHT_2A_RECIPROCAL_CROSSLINK_V1": "true",
    "PAPER_L2_120MIN_HOLD_BINDING_PREFLIGHT_2A_CROSSLINK_DOCS_TESTS_ONLY": "true",
    "GAP4_REQ_A_PAPER_BOUNDED_V0_PREFLIGHT_2A_CROSSLINK_REFERENCED": "true",
    "PAPER_L2_120MIN_HOLD_BINDING_V0_PREFLIGHT_2A_CROSSLINK_REFERENCED": "true",
    "SCHEDULER_BOUNDARY_10B_REFERENCED": "true",
    "DURATION_7200_SECONDS_REFERENCED": "true",
    "PROFILE_FULLY_IMPLEMENTED_ON_MAIN": "true",
    "NO_EXECUTE": "true",
    "NO_PREFLIGHT_LIFT": "true",
    "NO_RUNTIME": "true",
    "NO_LIVE": "true",
    "ORDER_CANCEL_EXECUTION_ARMING_TOUCHED": "false",
    "AUTHORITY_LIFT": "false",
    "TRADING_LOGIC_TOUCHED": "false",
    "MASTER_V2_LOGIC_TOUCHED": "false",
    "DOUBLE_PLAY_LOGIC_TOUCHED": "false",
    "NEW_PARALLEL_SSOT_CREATED": "false",
    "PREFLIGHT_REMAINS_BLOCKED": "true",
    "MARKET_DASHBOARD_TOUCHED": "false",
    "DOCS_DRIFT_OR_POINTER_INTEGRITY_DEFERRED": "true",
}
PAPER_L2_PREFLIGHT_2A_RECIPROCAL_CROSSLINK_OWNER_TESTS = (
    "test_paper_l2_120min_hold_binding_profile_contract_v0.py",
    "test_gap4_req_a_300s_hold_binding_profile_contract_v0.py",
    "test_paper_shadow_247_preflight_contract_v0.py",
)
SECTION5_HOLD_BINDING_PROFILE_CROSSLINK_HEADING = (
    "## SECTION5 Gap Owner Map hold-binding profile crosslink — docs/tests-only guard v1"
)
SECTION5_HOLD_BINDING_PROFILE_CROSSLINK_GUARD_BLOCK_ANCHOR = (
    "SECTION5_HOLD_BINDING_PROFILE_PREFLIGHT_2A_RECIPROCAL_CROSSLINK_V1=true"
)
SECTION5_HOLD_BINDING_PROFILE_CROSSLINK_EXPECTED: dict[str, str] = {
    "SECTION5_HOLD_BINDING_PROFILE_PREFLIGHT_2A_RECIPROCAL_CROSSLINK_V1": "true",
    "SECTION5_HOLD_BINDING_PROFILE_CROSSLINK_DOCS_TESTS_ONLY": "true",
    "GAP4_REQ_A_PAPER_BOUNDED_V0_SECTION5_CROSSLINK_REFERENCED": "true",
    "PAPER_L2_120MIN_HOLD_BINDING_V0_SECTION5_CROSSLINK_REFERENCED": "true",
    "SCHEDULER_BOUNDARY_10A_REFERENCED": "true",
    "SCHEDULER_BOUNDARY_10B_REFERENCED": "true",
    "DURATION_7200_SECONDS_REFERENCED": "true",
    "PAPER_L2_120MIN_HOLD_BINDING_PREFLIGHT_2A_RECIPROCAL_CROSSLINK_V1": "true",
    "PROFILE_FULLY_IMPLEMENTED_ON_MAIN": "true",
    "NO_EXECUTE": "true",
    "NO_PREFLIGHT_LIFT": "true",
    "NO_RUNTIME": "true",
    "NO_LIVE": "true",
    "ORDER_CANCEL_EXECUTION_ARMING_TOUCHED": "false",
    "AUTHORITY_LIFT": "false",
    "TRADING_LOGIC_TOUCHED": "false",
    "MASTER_V2_LOGIC_TOUCHED": "false",
    "DOUBLE_PLAY_LOGIC_TOUCHED": "false",
    "NEW_PARALLEL_SSOT_CREATED": "false",
    "PREFLIGHT_REMAINS_BLOCKED": "true",
    "MARKET_DASHBOARD_TOUCHED": "false",
    "DOCS_DRIFT_OR_POINTER_INTEGRITY_DEFERRED": "true",
}
SECTION5_HOLD_BINDING_PROFILE_CROSSLINK_OWNER_TESTS = (
    "test_gap4_req_a_300s_hold_binding_profile_contract_v0.py",
    "test_paper_l2_120min_hold_binding_profile_contract_v0.py",
    "test_section5_preflight_gap_owner_map_contract_v0.py",
)
PE11_BOUNDED_FUTURES_CI_AUDIT_CROSSLINK_HEADING = (
    "## PE-11 Bounded Futures reachability CI_AUDIT ↔ SECTION5 reciprocal crosslink "
    "— docs/tests-only guard v1"
)
PE11_BOUNDED_FUTURES_CI_AUDIT_CROSSLINK_GUARD_BLOCK_ANCHOR = (
    "PE11_BOUNDED_FUTURES_CI_AUDIT_SECTION5_RECIPROCAL_CROSSLINK_V1=true"
)
PE11_BOUNDED_FUTURES_CI_AUDIT_CROSSLINK_EXPECTED: dict[str, str] = {
    "PE11_BOUNDED_FUTURES_CI_AUDIT_SECTION5_RECIPROCAL_CROSSLINK_V1": "true",
    "PE11_BOUNDED_FUTURES_CI_AUDIT_CROSSLINK_DOCS_TESTS_ONLY": "true",
    "PE11_BOUNDED_FUTURES_REACHABILITY_GOVERNED_REFLECTION_V0_REFERENCED": "true",
    "REACHABILITY_PROVEN_NOT_ORDER_AUTHORIZED": "true",
    "SECTION5_PE11_OWNER_REFERENCED": "true",
    "BOUNDED_FUTURES_PRIVATE_READONLY_CONTRACT_REFERENCED": "true",
    "ZERO_ORDER_PUBLIC_FUTURES_REACHABILITY_PROVEN_REFERENCED": "true",
    "PRIVATE_READONLY_WIRE_REACHABILITY_PROVEN_REFERENCED": "true",
    "NO_EXECUTE": "true",
    "NO_PREFLIGHT_LIFT": "true",
    "NO_RUNTIME": "true",
    "NO_LIVE": "true",
    "FUTURES_SESSION_AUTHORIZED_NOW": "false",
    "FUTURES_EXECUTE_AUTHORIZED": "false",
    "ORDER_CANCEL_EXECUTION_ARMING_TOUCHED": "false",
    "AUTHORITY_LIFT": "false",
    "TRADING_LOGIC_TOUCHED": "false",
    "MASTER_V2_LOGIC_TOUCHED": "false",
    "DOUBLE_PLAY_LOGIC_TOUCHED": "false",
    "NEW_PARALLEL_SSOT_CREATED": "false",
    "PREFLIGHT_REMAINS_BLOCKED": "true",
    "MARKET_DASHBOARD_TOUCHED": "false",
    "DOCS_DRIFT_OR_POINTER_INTEGRITY_DEFERRED": "true",
}
PE11_BOUNDED_FUTURES_CI_AUDIT_CROSSLINK_OWNER_TESTS = (
    "test_section5_preflight_gap_owner_map_contract_v0.py",
    "test_bounded_futures_private_readonly_contract_v0.py",
)
SECTION5_DOC = (
    REPO_ROOT / "docs" / "ops" / "planning" / "SECTION5_PREFLIGHT_GAP_OWNER_MAP_CONTRACT_V0.md"
)
PRIMARY_EVIDENCE_RETENTION_INVARIANT_RESIDUAL_STATIC_REVIEW_OWNER_SURFACES = (
    "PAPER_SHADOW_247_PREFLIGHT_CONTRACT_V0.md",
    "primary_evidence_retention_v0.py",
)
MARKET_DASHBOARD_TRADING_APP_TERMINAL_REBUILD_PR4162_HEADING = (
    "## Market Dashboard trading-app terminal rebuild PR #4162 DOCS_TRUTH_MAP static crosslink v1"
)
MARKET_DASHBOARD_TRADING_APP_TERMINAL_REBUILD_PR4162_GUARD_BLOCK_ANCHOR = (
    "MARKET_DASHBOARD_TRADING_APP_TERMINAL_REBUILD_PR4162_CROSSLINK_GUARD_IMPLEMENTED=true"
)
MARKET_DASHBOARD_TRADING_APP_TERMINAL_REBUILD_PR4162_RANKING_BUNDLE = (
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/"
    "planning/systemwide_next_safe_scope_ranking_after_market_dashboard_terminal_rebuild_pass_no_run_v1_20260612T075155Z"
)
MARKET_DASHBOARD_TRADING_APP_TERMINAL_REBUILD_PR4162_CLOSEOUT_BUNDLE = (
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/"
    "closeout/market_dashboard_trading_app_terminal_rebuild_pr4162_squash_merge_closeout_v1_20260612T074614Z"
)
MARKET_DASHBOARD_TRADING_APP_TERMINAL_REBUILD_PR4162_VISUAL_BUNDLE = (
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/"
    "review/market_dashboard_trading_app_terminal_rebuild_post_merge_visual_check_no_mutation_v1_20260612T074839Z"
)
MARKET_DASHBOARD_TRADING_APP_TERMINAL_REBUILD_PR4162_EXPECTED: dict[str, str] = {
    "MARKET_DASHBOARD_TRADING_APP_TERMINAL_REBUILD_PR4162_CROSSLINK_GUARD_IMPLEMENTED": "true",
    "MARKET_DASHBOARD_TRADING_APP_TERMINAL_REBUILD_PR4162_DOCS_TRUTH_MAP_CI_AUDIT_STATIC_CROSSLINK_GUARD_V1": "true",
    "MARKET_DASHBOARD_TRADING_APP_TERMINAL_REBUILD_PR4162_CROSSLINK_DOCS_TESTS_ONLY": "true",
    "MARKET_DASHBOARD_TRADING_APP_TERMINAL_REBUILD_PR4162_SURFACE_REFERENCED": "true",
    "MARKET_DASHBOARD_TRADING_APP_TERMINAL_REBUILD_PR4162_TESTS_REFERENCED": "true",
    "MARKET_DASHBOARD_TRADING_APP_TERMINAL_REBUILD_PR4162_PR4162_ANCHOR_REFERENCED": "true",
    "MARKET_DASHBOARD_LANE_CLOSED_AFTER_VISUAL_PASS": "true",
    "MARKET_DASHBOARD_READ_ONLY_NON_AUTHORITY": "true",
    "MARKET_AIRPORT_CREATED_OR_REFERENCED": "false",
    "ORDERFLOW_AUTHORIZATION_CREATED": "false",
    "CANCEL_EXECUTE_AUTHORIZATION_CREATED": "false",
    "READY_FOR_OPERATOR_ARMING_CHANGED": "false",
    "RUNTIME_LOGIC_TOUCHED": "false",
    "NEW_PARALLEL_SSOT_CREATED": "false",
    "PREFLIGHT_REMAINS_BLOCKED": "true",
    "PROTECTED_SCOPE_TOUCHED": "false",
    "MASTER_V2_LOGIC_TOUCHED": "false",
    "DOUBLE_PLAY_LOGIC_TOUCHED": "false",
    "TRADING_LOGIC_TOUCHED": "false",
}
MARKET_DASHBOARD_TRADING_APP_TERMINAL_REBUILD_PR4162_OWNER_TESTS = (
    "test_market_terminal_layout_v1.py",
)
MARKET_DASHBOARD_TRADING_APP_TERMINAL_REBUILD_PR4162_OWNER_SURFACES = ("MARKET_SURFACE_V0.md",)
ORDER_CAPABILITY_REMAINING_READINESS_GAP_REVIEW_OWNER_TESTS = (
    "test_order_capability_payload_builder_contract_v1.py",
    "test_order_capability_dry_validation_contract_v1.py",
    "test_order_capability_killswitch_abort_binding_contract_v1.py",
    "test_order_capability_cancel_cleanup_failclosed_contract_v1.py",
    "test_order_capability_offline_payload_readiness_v1.py",
    "test_order_capability_private_endpoint_boundary_contract_v1.py",
    "test_order_capability_side_price_qty_rules_contract_v1.py",
    "test_order_capability_demo_instrument_rules_binding_contract_v1.py",
    "test_run_order_capability_fixture_binding_dry_validation_v1.py",
    "test_order_capability_demo_instrument_rules_fixture_normalizer_contract_v1.py",
)
PREFLIGHT_PROCESS_GATE_HYGIENE_GUARD_EXPECTED: dict[str, str] = {
    "PREFLIGHT_PROCESS_GATE_HYGIENE_GUARD_V1": "true",
    "ACTIVE_RUN_CHECK_PEAK_TRADE_EXPLICIT_ONLY": "true",
    "ACTIVE_RUN_EXCLUDE_MACOS_SYSTEM_SUBSTRING_FALSE_POSITIVES": "true",
    "ACTIVE_RUN_EXCLUDE_SHELL_CURSOR_SELF_MATCH": "true",
    "UNTRACKED_DOT_PYTHON_VERSION_TOLERATED_WHEN_TRACKED_CLEAN": "true",
    "UNTRACKED_DOT_PYTHON_VERSION_MUST_NOT_BE_COMMITTED_OR_DELETED_BY_AUTOMATION": "true",
    "NO_RUNTIME": "true",
    "NO_LIVE": "true",
    "PREFLIGHT_REMAINS_BLOCKED": "true",
    "PREFLIGHT_LIFT": "false",
    "ORDER_CANCEL_EXECUTION_ARMING_TOUCHED": "false",
    "TRADING_LOGIC_TOUCHED": "false",
    "MASTER_V2_LOGIC_TOUCHED": "false",
    "DOUBLE_PLAY_LOGIC_TOUCHED": "false",
    "PARALLEL_DOCS_CREATED": "false",
    "PREFLIGHT_PROCESS_GATE_HYGIENE_DOCS_TESTS_ONLY": "true",
}

GUARD_EXPECTED: dict[str, str] = {
    "REMOTE_RUNTIME_IS_BACKEND": "true",
    "LOCAL_REPO_GATES_REMAIN_AUTHORITATIVE": "true",
    "REMOTE_HOST_HAS_NO_INDEPENDENT_AUTHORITY": "true",
    "S3_AS_FINALIZED_EVIDENCE_TRANSPORT_ONLY": "true",
    "NOTION_AS_PROJECTION_ONLY": "true",
    "MARKET_DASHBOARD_AS_READONLY_PROJECTION_ONLY": "true",
    "MAX_RUNTIME_SECONDS_REQUIRED": "true",
    "FINALIZED_EVIDENCE_REQUIRED": "true",
    "DURABLE_COPY_REQUIRED": "true",
    "MANIFEST_VERIFY_REQUIRED": "true",
    "CYBER_INPUT_JSONL_BLOCKED": "true",
    "PREFLIGHT_REMAINS_BLOCKED": "true",
    "PATH_B_LIFT_DISCUSSION_READY": "false",
    "GLOBAL_PREFLIGHT_LIFTED": "false",
    "RUNTIME_STARTED": "false",
    "SCHEDULER_STARTED": "false",
    "PAPER_STARTED": "false",
    "SHADOW_STARTED": "false",
    "TESTNET_STARTED": "false",
    "LIVE_STARTED": "false",
    "AWS_TOUCHED": "false",
    "NETWORK_TOUCHED": "false",
    "NOTION_TOUCHED": "false",
    "MARKET_DASHBOARD_TOUCHED": "false",
    "PRODUCTION_CODE_TOUCHED": "false",
    "DOUBLE_PLAY_LOGIC_TOUCHED": "false",
    "TRADING_LOGIC_TOUCHED": "false",
    "PARALLEL_DOCS_CREATED": "false",
    "PARALLEL_BUILDS_CREATED": "false",
    "REMOTE_RUNTIME_EXTERNAL_CHARTER_CONTRACT_DOCS_GUARD_DOCS_TESTS_ONLY": "true",
}
LOCAL_DRY_HOST_GUARD_EXPECTED: dict[str, str] = {
    "LOCAL_DRY_HOST_NO_RUN_PREFLIGHT_CHARTER_REFLECTION_V0": "true",
    "LOCAL_DRY_HOST_SCOPE_READY": "true",
    "BACKEND_TARGET": "local-only-dry-host",
    "COST_CEILING": "0_EUR_CLOUD_SPEND",
    "REMOTE_RUNTIME_GO": "false",
    "NO_RUN_CHARTER": "true",
    "FUTURE_OPERATOR_GO_REQUIRED": "true",
    "MAX_RUNTIME_SECONDS_REQUIRED": "true",
    "NO_ACTIVE_RUN_CHECK_REQUIRED": "true",
    "ORPHAN_PROCESS_CHECK_REQUIRED": "true",
    "PRIMARY_EVIDENCE_REQUIRED": "true",
    "DURABLE_COPY_REQUIRED": "true",
    "MANIFEST_VERIFY_REQUIRED": "true",
    "CLOSEOUT_REQUIRED": "true",
    "TMP_ONLY_EVIDENCE_ACCEPTED": "false",
    "SECRETS_INCLUDED": "false",
    "AWS_TOUCHED": "false",
    "NETWORK_TOUCHED": "false",
    "NOTION_TOUCHED": "false",
    "MARKET_DASHBOARD_TOUCHED": "false",
    "RUNTIME_STARTED": "false",
    "SCHEDULER_STARTED": "false",
    "PAPER_STARTED": "false",
    "SHADOW_STARTED": "false",
    "TESTNET_STARTED": "false",
    "LIVE_STARTED": "false",
    "PRODUCTION_CODE_TOUCHED": "false",
    "PREFLIGHT_REMAINS_BLOCKED": "true",
    "PATH_B_LIFT_DISCUSSION_READY": "false",
    "GLOBAL_PREFLIGHT_LIFTED": "false",
    "DOUBLE_PLAY_LOGIC_TOUCHED": "false",
    "TRADING_LOGIC_TOUCHED": "false",
    "PARALLEL_DOCS_CREATED": "false",
    "PARALLEL_BUILDS_CREATED": "false",
    "LOCAL_DRY_HOST_NO_RUN_PREFLIGHT_DOCS_TESTS_ONLY": "true",
}

RECIPROCAL_OWNER_TESTS = (
    "test_remote_runtime_host_metadata_contract_v0.py",
    "test_s3_finalized_evidence_export_gate_v0.py",
    "test_scheduler_boundary_hard_block_contract_v0.py",
    "test_notion_post_closeout_sync_projection_spec_v0.py",
    "test_market_dashboard_readonly_run_projection_spec_v0.py",
    "test_ops_cockpit_payload_top_level_contract.py",
    "test_master_v2_double_play_pure_stack_readiness_map_static_crosslink_contract_v0.py",
)

OPS_COCKPIT_OPERATOR_SUMMARY_SPEC = (
    REPO_ROOT / "docs" / "ops" / "specs" / "OPS_COCKPIT_OPERATOR_SUMMARY_SURFACE.md"
)
OC1_PLANNING_BUNDLE_PATH = (
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/"
    "planning/ops_cockpit_operator_status_index_rc_v0_slice_oc1_docs_only_20260602T182955Z/"
)
OC_RELEASE_RC_INDEX_HEADING = "## Ops Cockpit / Operator Status Index RC v0 — meta-index v0"
OC_RELEASE_RC_BLOCK_ANCHOR = "OPS_COCKPIT_OR_OPERATOR_STATUS_INDEX_RC_V0=true"
OC_RELEASE_RC_EXPECTED: dict[str, str] = {
    "OPS_COCKPIT_OR_OPERATOR_STATUS_INDEX_RC_V0": "true",
    "SLICE_OC1_DOCS_ONLY": "true",
    "OPERATOR_EXPERIENCE_RELEASE_RC_V0_CORE_DONE": "true",
    "CYBERSECURITY_VISIBILITY_RELEASE_RC_V0_CORE_DONE": "true",
    "EVIDENCE_DURABLE_CLOSEOUT_RETENTION_RC_V0_CORE_DONE": "true",
    "ER_SSOT_PREFLIGHT_POINTER_ONLY": "true",
    "ER3_REPO_FOLLOWUP_DEFERRED": "true",
    "OPS_COCKPIT_REFLECTION_ONLY": "true",
    "OPS_COCKPIT_AUTHORITY_CHANGED": "false",
    "PREFLIGHT_REMAINS_BLOCKED": "true",
    "STOP_IDLE_PRESERVED": "true",
    "RETENTION_ENFORCEMENT_ACTIVATED": "false",
    "NOTION_AS_MIRROR_ONLY": "true",
    "NOTION_WRITES": "false",
    "WORKFLOW_DISPATCH_EXECUTED": "false",
    "NO_RUNTIME": "true",
    "NO_TRADING_AUTHORITY_CHANGE": "true",
    "MASTER_V2_LOGIC_CHANGED": "false",
    "DOUBLE_PLAY_LOGIC_CHANGED": "false",
    "PARALLEL_OPERATOR_STATUS_INDEX_CREATED": "false",
}

MV2_READONLY_ALIGNMENT_RC_HEADING = (
    "## Master V2 / Double Play Read-only Alignment Inventory RC v0 — docs reflection v0"
)
MV2_READONLY_ALIGNMENT_RC_BLOCK_ANCHOR = (
    "MASTER_V2_DOUBLE_PLAY_READONLY_ALIGNMENT_INVENTORY_RC_V0=true"
)
MV2_READONLY_ALIGNMENT_RC_EXPECTED: dict[str, str] = {
    "MASTER_V2_DOUBLE_PLAY_READONLY_ALIGNMENT_INVENTORY_RC_V0": "true",
    "SLICE_MV2_1_DOCS_REFLECTION_ONLY": "true",
    "RUNTIME_PRODUCER_PARKING_LIFTED": "false",
    "PREFLIGHT_REMAINS_BLOCKED": "true",
    "STOP_IDLE_PRESERVED": "true",
    "NO_RUNTIME": "true",
    "MASTER_V2_LOGIC_CHANGED": "false",
    "DOUBLE_PLAY_LOGIC_CHANGED": "false",
    "TRADING_AUTHORITY_CHANGED": "false",
    "PARALLEL_MASTER_V2_ALIGNMENT_INDEX_CREATED": "false",
    "FOLLOWUP_DOCS_SLICE_NEEDED": "false",
    "FOLLOWUP_TEST_GUARD_NEEDED": "false",
    "RUNTIME_STARTED": "false",
    "SCHEDULER_STARTED": "false",
    "LIVE_TOUCHED": "false",
    "READY_FOR_OPERATOR_ARMING": "false",
}
PURE_STACK_READINESS_MAP = (
    REPO_ROOT / "docs" / "ops" / "specs" / "MASTER_V2_DOUBLE_PLAY_PURE_STACK_READINESS_MAP_V0.md"
)
MV2_PURE_STACK_GUARD = (
    REPO_ROOT
    / "tests"
    / "ops"
    / "test_master_v2_double_play_pure_stack_readiness_map_static_crosslink_contract_v0.py"
)

FORBIDDEN_PARALLEL_DOC_FRAGMENTS = (
    "REMOTE_RUNTIME_HOST_CONTRACT_V0.md",
    "REMOTE_RUNTIME_CONSOLIDATION_V0.md",
    "REMOTE_RUNTIME_RUNBOOK_V0.md",
    "REMOTE_RUNTIME_AUTHORITY_V0.md",
)

FENCED_BLOCK_RX = re.compile(r"```[^\n]*\n(.*?)```", re.DOTALL)


def _ci_audit_text() -> str:
    return CI_AUDIT.read_text(encoding="utf-8")


def _fenced_blocks(text: str) -> list[str]:
    return [block.strip() for block in FENCED_BLOCK_RX.findall(text)]


def _block_containing(text: str, anchor: str) -> str:
    for block in _fenced_blocks(text):
        if anchor in block:
            return block
    raise AssertionError(f"missing fenced machine-line block containing {anchor!r}")


def _machine_line_values(block: str) -> dict[str, str]:
    values: dict[str, str] = {}
    for line in block.splitlines():
        stripped = line.strip()
        if "=" not in stripped or stripped.startswith("#"):
            continue
        key, _, value = stripped.partition("=")
        if key and value:
            values[key.strip()] = value.strip()
    return values


def test_ci_audit_remote_runtime_charter_section_present() -> None:
    text = _ci_audit_text()
    assert "## Remote Runtime Contract — external charter reflection v0" in text
    assert "### Remote Runtime external charter docs guard v0" in text
    assert CHARTER_PATH in text
    assert CONSOLIDATION_PATH in text
    assert THIS_MODULE in text


def test_ci_audit_guard_machine_lines() -> None:
    block = _block_containing(_ci_audit_text(), GUARD_BLOCK_ANCHOR)
    values = _machine_line_values(block)
    missing = set(GUARD_EXPECTED) - values.keys()
    assert not missing, f"missing guard keys: {sorted(missing)}"
    for key, expected in GUARD_EXPECTED.items():
        assert values[key] == expected, f"{key}={values[key]!r} expected {expected!r}"


def test_ci_audit_local_dry_host_no_run_section_present() -> None:
    text = _ci_audit_text()
    assert "## Local Dry Host No-Run Preflight Charter — external reflection v0" in text
    assert "### Local dry host no-run preflight docs guard v0" in text
    assert LOCAL_DRY_HOST_PREFLIGHT_CHARTER_PATH in text
    assert "no parallel local-dry-host runtime anchor" in text.lower()


def test_ci_audit_local_dry_host_guard_machine_lines() -> None:
    block = _block_containing(_ci_audit_text(), LOCAL_DRY_HOST_GUARD_BLOCK_ANCHOR)
    values = _machine_line_values(block)
    missing = set(LOCAL_DRY_HOST_GUARD_EXPECTED) - values.keys()
    assert not missing, f"missing local dry host guard keys: {sorted(missing)}"
    for key, expected in LOCAL_DRY_HOST_GUARD_EXPECTED.items():
        assert values[key] == expected, f"{key}={values[key]!r} expected {expected!r}"


def test_ci_audit_preflight_process_gate_hygiene_section_present_v1() -> None:
    text = _ci_audit_text()
    assert PREFLIGHT_PROCESS_GATE_HYGIENE_HEADING in text
    assert "### Preflight process gate hygiene docs guard v0" in text
    assert PREFLIGHT_PROCESS_GATE_HYGIENE_INPUT_BUNDLE in text
    assert "liveactivitiesd" in text
    assert "dns-result-order" in text
    assert "PhotosReliveWidget" in text
    assert "Shell/Cursor self-match" in text
    assert "untracked root `.python-version`" in text
    assert "must **not** commit or delete it blindly" in text
    assert THIS_MODULE in text
    assert "no parallel preflight hygiene anchor" in text.lower()


def test_ci_audit_preflight_process_gate_hygiene_machine_lines_v1() -> None:
    block = _block_containing(_ci_audit_text(), PREFLIGHT_PROCESS_GATE_HYGIENE_GUARD_BLOCK_ANCHOR)
    values = _machine_line_values(block)
    missing = set(PREFLIGHT_PROCESS_GATE_HYGIENE_GUARD_EXPECTED) - values.keys()
    assert not missing, f"missing preflight process gate hygiene keys: {sorted(missing)}"
    for key, expected in PREFLIGHT_PROCESS_GATE_HYGIENE_GUARD_EXPECTED.items():
        assert values[key] == expected, f"{key}={values[key]!r} expected {expected!r}"


def test_docs_truth_map_preflight_process_gate_hygiene_chronicle_v1() -> None:
    text = DOCS_TRUTH_MAP.read_text(encoding="utf-8")
    assert "Preflight process gate hygiene guard v1" in text
    assert THIS_MODULE in text
    assert "precise Peak_Trade active-run detection" in text
    assert "shell/Cursor self-match exclusion" in text
    assert "tolerated untracked root `.python-version` when tracked clean" in text
    assert "PREFLIGHT_PROCESS_GATE_HYGIENE_GUARD_V1=true" in text
    assert PREFLIGHT_PROCESS_GATE_HYGIENE_INPUT_BUNDLE.split("/")[-1] in text


def test_ci_audit_reuses_canonical_owners_not_parallel_surfaces() -> None:
    text = _ci_audit_text()
    section_start = text.index("## Remote Runtime Contract — external charter reflection v0")
    section = text[section_start:]
    assert "RUNTIME_LANE_TAXONOMY_AUTHORITY_LEVELS_CONTRACT_V0.md" in section
    assert "PAPER_SHADOW_247_PREFLIGHT_CONTRACT_V0.md" in section
    assert "SCHEDULER_BOUNDARY_HARD_BLOCK_CONTRACT_V0.md" in section
    assert "primary_evidence_retention_v0.py" in section
    assert "durable_closeout_copy_verify_v0.py" in section
    assert "no parallel remote-runtime anchor" in section.lower()
    assert "does **not** bypass Cyber" in section or "does not bypass Cyber" in section


def test_docs_truth_map_chronicle_references_guard_and_charter() -> None:
    text = DOCS_TRUTH_MAP.read_text(encoding="utf-8")
    assert THIS_MODULE in text
    assert "Remote Runtime external charter reflection docs guard v0" in text
    assert "Local Dry Host no-run preflight charter reflection docs guard v0" in text
    assert "REMOTE_RUNTIME_IS_BACKEND=true" in text
    assert "LOCAL_DRY_HOST_SCOPE_READY=true" in text
    assert "FORBIDDEN_NEW_SURFACES=0" in text
    assert CHARTER_PATH.split("/")[-1] in text or "120000Z" in text
    assert LOCAL_DRY_HOST_PREFLIGHT_CHARTER_PATH.split("/")[-1] in text or "024302Z" in text


def test_taxonomy_section_6a_backend_tokens_preserved() -> None:
    text = TAXONOMY_SPEC.read_text(encoding="utf-8")
    assert "REMOTE_RUNTIME_IS_BACKEND_NOT_LANE=true" in text
    assert "S3_FINALIZED_EVIDENCE_TRANSPORT_ONLY=true" in text
    assert "NOTION_PROJECTION_NON_AUTHORIZING=true" in text
    assert "MARKET_DASHBOARD_PROJECTION_READONLY=true" in text


def test_reciprocal_owner_crosslinks_present() -> None:
    owner_text = Path(__file__).read_text(encoding="utf-8")
    for module_name in RECIPROCAL_OWNER_TESTS:
        assert module_name in owner_text, f"missing reciprocal owner {module_name!r}"
        peer_text = (REPO_ROOT / "tests" / "ops" / module_name).read_text(encoding="utf-8")
        assert THIS_MODULE in peer_text, f"{module_name} missing reciprocal link to {THIS_MODULE}"


def test_no_parallel_remote_runtime_authority_docs_introduced() -> None:
    specs_dir = REPO_ROOT / "docs" / "ops" / "specs"
    runbooks_dir = REPO_ROOT / "docs" / "ops" / "runbooks"
    for fragment in FORBIDDEN_PARALLEL_DOC_FRAGMENTS:
        assert list(specs_dir.glob(f"*{fragment}*")) == [], fragment
        assert list(runbooks_dir.glob(f"*{fragment}*")) == [], fragment


def test_guard_module_declares_non_authorization() -> None:
    text = Path(__file__).read_text(encoding="utf-8")
    assert "Never starts runtime" in text or "Never starts" in text
    assert "grants GO" in text or "grants go" in text.lower()


def _oc_release_rc_index_section(text: str) -> str:
    start = text.find(OC_RELEASE_RC_INDEX_HEADING)
    assert start != -1, "missing Ops Cockpit / Operator Status Index RC v0 meta-index section"
    return text[start:]


def test_ci_audit_ops_cockpit_operator_status_index_rc_v0_section_present() -> None:
    text = _ci_audit_text()
    section = _oc_release_rc_index_section(text)
    assert "SLICE-OC-1" in section
    assert "SLICE-OC-2" in section
    assert "docs/tests-only" in section
    assert "OPS_COCKPIT_OPERATOR_SUMMARY_SURFACE.md" in section
    assert "PAPER_SHADOW_247_PREFLIGHT_CONTRACT_V0.md" in section
    assert "does **not** duplicate ER body" in section or "does not duplicate ER body" in section
    assert OPS_COCKPIT_OPERATOR_SUMMARY_SPEC.name in section
    assert OC1_PLANNING_BUNDLE_PATH in section
    assert "parallel operator-status hub" in section.lower()
    assert THIS_MODULE not in section


def test_ci_audit_ops_cockpit_operator_status_index_machine_lines() -> None:
    text = _ci_audit_text()
    block = _block_containing(text, OC_RELEASE_RC_BLOCK_ANCHOR)
    values = _machine_line_values(block)
    missing = set(OC_RELEASE_RC_EXPECTED) - values.keys()
    assert not missing, f"missing OC release RC keys: {sorted(missing)}"
    for key, expected in OC_RELEASE_RC_EXPECTED.items():
        assert values[key] == expected, f"{key}={values[key]!r} expected {expected!r}"


def test_ci_audit_ops_cockpit_operator_status_index_er_preflight_pointer_only() -> None:
    section = _oc_release_rc_index_section(_ci_audit_text())
    assert "ER SSOT — pointer only" in section or "ER SSOT" in section
    assert "PAPER_SHADOW_247_PREFLIGHT_CONTRACT_V0.md" in section
    assert "Operator Experience Release RC v0" in section
    assert "Cybersecurity Visibility Release RC v0" in section
    assert "Evidence Durable Closeout Retention RC v0" in section


def test_ci_audit_ops_cockpit_operator_status_index_slice_oc2_guard_owner_v0() -> None:
    section = _oc_release_rc_index_section(_ci_audit_text())
    assert "SLICE-OC-2" in section
    assert "test_ops_cockpit_" in section
    assert "test_ops_cockpit_" in section
    assert "extend existing" in section.lower() or "Tests-ops" in section


def _mv2_readonly_alignment_rc_section(text: str) -> str:
    start = text.find(MV2_READONLY_ALIGNMENT_RC_HEADING)
    assert start != -1, "missing Master V2 readonly alignment RC v0 section"
    return text[start:]


def test_ci_audit_mv2_readonly_alignment_rc_section_present_v0() -> None:
    text = _ci_audit_text()
    section = _mv2_readonly_alignment_rc_section(text)
    assert "SLICE-MV2-1" in section
    assert "SLICE-MV2-2" in section
    assert PURE_STACK_READINESS_MAP.is_file()
    assert "MASTER_V2_REUSE_REWIRE_INVENTORY_V1.md" in section
    assert "MARKET_SURFACE_V0.md" in section
    assert "parallel alignment index" in section.lower()
    assert "test_master_v2_" in section
    assert THIS_MODULE not in section


def test_ci_audit_mv2_readonly_alignment_rc_machine_lines_v0() -> None:
    text = _ci_audit_text()
    block = _block_containing(text, MV2_READONLY_ALIGNMENT_RC_BLOCK_ANCHOR)
    values = _machine_line_values(block)
    missing = set(MV2_READONLY_ALIGNMENT_RC_EXPECTED) - values.keys()
    assert not missing, f"missing MV2 readonly alignment RC keys: {sorted(missing)}"
    for key, expected in MV2_READONLY_ALIGNMENT_RC_EXPECTED.items():
        assert values[key] == expected, f"{key}={values[key]!r} expected {expected!r}"


def _order_capability_remaining_readiness_gap_review_section(text: str) -> str:
    start = text.find(ORDER_CAPABILITY_REMAINING_READINESS_GAP_REVIEW_HEADING)
    assert start != -1, "missing Order-Capability remaining readiness gap review section"
    next_heading = text.find("\n## ", start + 1)
    if next_heading == -1:
        return text[start:]
    return text[start:next_heading]


def test_ci_audit_order_capability_remaining_readiness_gap_review_section_present_v1() -> None:
    text = _ci_audit_text()
    section = _order_capability_remaining_readiness_gap_review_section(text)
    assert ORDER_CAPABILITY_REMAINING_READINESS_GAP_REVIEW_INPUT_BUNDLE in section
    assert "visibility/readiness only" in section
    assert "Payload builder" in section
    assert "Dry-validation" in section
    assert "Killswitch abort" in section
    assert "Cancel cleanup" in section
    assert "Offline payload readiness" in section
    assert "Private endpoint boundary" in section
    assert "Side / price / qty rules" in section
    assert "Demo instrument rules binding" in section
    assert "Fixture-binding DOCS_TRUTH_MAP static crosslink" in section
    assert "Demo instrument rules fixture normalizer DOCS_TRUTH_MAP static crosslink" in section
    assert "no parallel readiness ssot" in section.lower()
    assert THIS_MODULE in section
    for module_name in ORDER_CAPABILITY_REMAINING_READINESS_GAP_REVIEW_OWNER_TESTS:
        assert module_name in section, f"missing owner test reference {module_name!r}"


def test_ci_audit_order_capability_remaining_readiness_gap_review_machine_lines_v1() -> None:
    block = _block_containing(
        _ci_audit_text(),
        ORDER_CAPABILITY_REMAINING_READINESS_GAP_REVIEW_GUARD_BLOCK_ANCHOR,
    )
    values = _machine_line_values(block)
    missing = set(ORDER_CAPABILITY_REMAINING_READINESS_GAP_REVIEW_EXPECTED) - values.keys()
    assert not missing, f"missing order capability readiness gap review keys: {sorted(missing)}"
    for key, expected in ORDER_CAPABILITY_REMAINING_READINESS_GAP_REVIEW_EXPECTED.items():
        assert values[key] == expected, f"{key}={values[key]!r} expected {expected!r}"


def test_docs_truth_map_order_capability_remaining_readiness_gap_review_chronicle_v1() -> None:
    text = DOCS_TRUTH_MAP.read_text(encoding="utf-8")
    assert (
        "Order-Capability remaining readiness gap review docs/tests-only visibility guard v1"
        in text
    )
    assert THIS_MODULE in text
    assert "ORDER_CAPABILITY_REMAINING_READINESS_GAP_REVIEW_V1=true" in text
    assert "payload builder" in text
    assert "dry-validation" in text
    assert "killswitch abort" in text
    assert "cancel cleanup" in text
    assert "offline payload readiness" in text
    assert "private endpoint" in text
    assert "side-price-qty" in text
    assert "demo-instrument rules binding" in text
    assert "**no** runtime/live/preflight lift/order/cancel/execution/arming/authority lift" in text
    assert ORDER_CAPABILITY_REMAINING_READINESS_GAP_REVIEW_INPUT_BUNDLE.split("/")[-1] in text


def _systemwide_ci_docs_truth_map_residual_review_section(text: str) -> str:
    start = text.find(SYSTEMWIDE_CI_DOCS_TRUTH_MAP_RESIDUAL_REVIEW_HEADING)
    assert start != -1, "missing systemwide CI/docs truth-map residual review section"
    next_heading = text.find("\n## ", start + 1)
    if next_heading == -1:
        return text[start:]
    return text[start:next_heading]


def test_ci_audit_systemwide_ci_docs_truth_map_residual_review_section_present_v1() -> None:
    text = _ci_audit_text()
    section = _systemwide_ci_docs_truth_map_residual_review_section(text)
    assert SYSTEMWIDE_CI_DOCS_TRUTH_MAP_RESIDUAL_REVIEW_INPUT_BUNDLE in section
    assert "Post-PR #4154/#4155" in section
    assert "required-check safety gate surfaces" in section
    assert "docs-token-policy gate expectations" in section
    assert "same-repo approval/hard-retrigger guidance" in section
    assert "workflow secrets visibility" in section
    assert "workflow write-permission visibility" in section
    assert "residual PRB scheduled scorecard/manual-only posture" in section
    assert "MASTER_V2_CI_REQUIRED_CHECKS_SAFETY_GATE_POINTER_INDEX_V0.md" in section
    assert "github_rulesets_pr_reviews_policy.md" in section
    assert "no parallel required-check ssot" in section.lower()
    assert THIS_MODULE in section
    for module_name in SYSTEMWIDE_CI_DOCS_TRUTH_MAP_RESIDUAL_REVIEW_OWNER_TESTS:
        assert module_name in section, f"missing owner test reference {module_name!r}"


def test_ci_audit_systemwide_ci_docs_truth_map_residual_review_machine_lines_v1() -> None:
    block = _block_containing(
        _ci_audit_text(),
        SYSTEMWIDE_CI_DOCS_TRUTH_MAP_RESIDUAL_REVIEW_GUARD_BLOCK_ANCHOR,
    )
    values = _machine_line_values(block)
    missing = set(SYSTEMWIDE_CI_DOCS_TRUTH_MAP_RESIDUAL_REVIEW_EXPECTED) - values.keys()
    assert not missing, (
        f"missing systemwide CI/docs truth-map residual review keys: {sorted(missing)}"
    )
    for key, expected in SYSTEMWIDE_CI_DOCS_TRUTH_MAP_RESIDUAL_REVIEW_EXPECTED.items():
        assert values[key] == expected, f"{key}={values[key]!r} expected {expected!r}"


def test_docs_truth_map_systemwide_ci_docs_truth_map_residual_review_chronicle_v1() -> None:
    text = DOCS_TRUTH_MAP.read_text(encoding="utf-8")
    assert "Systemwide CI/Docs required-check truth-map residual review guard v1" in text
    assert THIS_MODULE in text
    assert "SYSTEMWIDE_CI_DOCS_REQUIRED_CHECK_TRUTH_MAP_RESIDUAL_REVIEW_V1=true" in text
    assert "required-check safety gate surfaces" in text
    assert "docs-token-policy gate expectations" in text
    assert "same-repo approval/hard-retrigger guidance" in text
    assert "workflow secrets visibility" in text
    assert "workflow write-permission visibility" in text
    assert "residual PRB scheduled scorecard/manual-only posture" in text
    assert (
        "**no** runtime/live/preflight lift/workflow mutation/workflow_dispatch/gh run rerun"
        in text
    )
    assert SYSTEMWIDE_CI_DOCS_TRUTH_MAP_RESIDUAL_REVIEW_INPUT_BUNDLE.split("/")[-1] in text


def _primary_evidence_retention_invariant_residual_static_review_section(text: str) -> str:
    start = text.find(PRIMARY_EVIDENCE_RETENTION_INVARIANT_RESIDUAL_STATIC_REVIEW_HEADING)
    assert start != -1, (
        "missing primary evidence retention invariant residual static review section"
    )
    next_heading = text.find("\n## ", start + 1)
    if next_heading == -1:
        return text[start:]
    return text[start:next_heading]


def test_ci_audit_primary_evidence_retention_invariant_residual_static_review_section_present_v1() -> (
    None
):
    text = _ci_audit_text()
    section = _primary_evidence_retention_invariant_residual_static_review_section(text)
    assert PRIMARY_EVIDENCE_RETENTION_INVARIANT_RESIDUAL_STATIC_REVIEW_INPUT_BUNDLE in section
    assert "Post-PR #4156" in section
    assert "primary-evidence completion invariant" in section
    assert "not complete" in section
    assert "stored only under `/tmp`" in section
    assert "not manifest-verified" in section
    assert "no parallel evidence-retention ssot" in section.lower()
    assert "PAPER_SHADOW_247_PREFLIGHT_CONTRACT_V0.md" in section
    assert "§2a" in section
    assert "primary_evidence_retention_v0.py" not in section
    assert THIS_MODULE in section
    for module_name in PRIMARY_EVIDENCE_RETENTION_INVARIANT_RESIDUAL_STATIC_REVIEW_OWNER_TESTS:
        assert module_name in section, f"missing owner test reference {module_name!r}"


def test_ci_audit_primary_evidence_retention_invariant_residual_static_review_machine_lines_v1() -> (
    None
):
    block = _block_containing(
        _ci_audit_text(),
        PRIMARY_EVIDENCE_RETENTION_INVARIANT_RESIDUAL_STATIC_REVIEW_GUARD_BLOCK_ANCHOR,
    )
    values = _machine_line_values(block)
    missing = (
        set(PRIMARY_EVIDENCE_RETENTION_INVARIANT_RESIDUAL_STATIC_REVIEW_EXPECTED) - values.keys()
    )
    assert not missing, (
        "missing primary evidence retention invariant residual static review keys: "
        f"{sorted(missing)}"
    )
    for (
        key,
        expected,
    ) in PRIMARY_EVIDENCE_RETENTION_INVARIANT_RESIDUAL_STATIC_REVIEW_EXPECTED.items():
        assert values[key] == expected, f"{key}={values[key]!r} expected {expected!r}"


def test_docs_truth_map_primary_evidence_retention_invariant_residual_static_review_chronicle_v1() -> (
    None
):
    text = DOCS_TRUTH_MAP.read_text(encoding="utf-8")
    assert "Primary evidence retention invariant residual static review guard v1" in text
    assert THIS_MODULE in text
    assert "PRIMARY_EVIDENCE_RETENTION_INVARIANT_RESIDUAL_STATIC_REVIEW_V1=true" in text
    assert "PAPER_SHADOW_247_PREFLIGHT_CONTRACT_V0.md" in text
    assert "primary_evidence_retention_v0.py" in text
    assert "test_primary_evidence_retention_invariant_contract_v0.py" in text
    assert "test_run_primary_evidence_retention_hard_gate_v0.py" in text
    assert "test_durable_closeout_copy_verify_v0.py" in text
    assert "outside `/tmp`" in text
    assert "manifest-created" in text
    assert "checksum-verified" in text
    assert "manifest-verified" in text
    assert "`/tmp`-only invalid" in text
    assert (
        "**no** runtime/run start/live/preflight lift/order/cancel/execution/arming/authority lift"
        in text
    )
    assert (
        PRIMARY_EVIDENCE_RETENTION_INVARIANT_RESIDUAL_STATIC_REVIEW_INPUT_BUNDLE.split("/")[-1]
        in text
    )


def _paper_l2_preflight_2a_reciprocal_crosslink_section(text: str) -> str:
    start = text.find(PAPER_L2_PREFLIGHT_2A_RECIPROCAL_CROSSLINK_HEADING)
    assert start != -1, "missing paper L2 preflight §2a reciprocal crosslink section"
    next_heading = text.find("\n## ", start + 1)
    if next_heading == -1:
        return text[start:]
    return text[start:next_heading]


def test_ci_audit_paper_l2_preflight_2a_reciprocal_crosslink_section_present_v1() -> None:
    text = _ci_audit_text()
    section = _paper_l2_preflight_2a_reciprocal_crosslink_section(text)
    assert (
        "GO_PAPER_L2_120MIN_HOLD_BINDING_PREFLIGHT_2A_RECIPROCAL_CROSSLINK_DOCS_TESTS_NO_RUN_V1"
        in section
    )
    assert "paper_l2_120min_hold_binding_v0" in section
    assert "gap4_req_a_paper_bounded_v0" in section
    assert "7200s" in section
    assert "§10b" in section
    assert "PAPER_SHADOW_247_PREFLIGHT_CONTRACT_V0.md" in section
    assert "SCHEDULER_BOUNDARY_HARD_BLOCK_CONTRACT_V0.md" in section
    assert "no parallel preflight crosslink ssot" in section.lower()
    assert THIS_MODULE in section
    for module_name in PAPER_L2_PREFLIGHT_2A_RECIPROCAL_CROSSLINK_OWNER_TESTS:
        assert module_name in section, f"missing owner test reference {module_name!r}"


def test_ci_audit_paper_l2_preflight_2a_reciprocal_crosslink_machine_lines_v1() -> None:
    block = _block_containing(
        _ci_audit_text(),
        PAPER_L2_PREFLIGHT_2A_RECIPROCAL_CROSSLINK_GUARD_BLOCK_ANCHOR,
    )
    values = _machine_line_values(block)
    missing = set(PAPER_L2_PREFLIGHT_2A_RECIPROCAL_CROSSLINK_EXPECTED) - values.keys()
    assert not missing, (
        f"missing paper L2 preflight §2a reciprocal crosslink keys: {sorted(missing)}"
    )
    for key, expected in PAPER_L2_PREFLIGHT_2A_RECIPROCAL_CROSSLINK_EXPECTED.items():
        assert values[key] == expected, f"{key}={values[key]!r} expected {expected!r}"


def _section5_hold_binding_profile_crosslink_section(text: str) -> str:
    start = text.find(SECTION5_HOLD_BINDING_PROFILE_CROSSLINK_HEADING)
    assert start != -1, "missing SECTION5 hold-binding profile crosslink section"
    next_heading = text.find("\n## ", start + 1)
    if next_heading == -1:
        return text[start:]
    return text[start:next_heading]


def test_ci_audit_section5_hold_binding_profile_crosslink_section_present_v1() -> None:
    text = _ci_audit_text()
    section = _section5_hold_binding_profile_crosslink_section(text)
    assert (
        "GO_SECTION5_GAP_OWNER_MAP_HOLD_BINDING_PROFILE_CROSSLINKS_DOCS_TESTS_NO_RUN_V1" in section
    )
    assert "gap4_req_a_paper_bounded_v0" in section
    assert "paper_l2_120min_hold_binding_v0" in section
    assert "7200s" in section or "7200" in section
    assert "§10a" in section
    assert "§10b" in section
    assert "SECTION5_PREFLIGHT_GAP_OWNER_MAP_CONTRACT_V0.md" in section
    assert "PAPER_SHADOW_247_PREFLIGHT_CONTRACT_V0.md" in section
    assert "no parallel gap-owner ssot" in section.lower()
    assert THIS_MODULE in section
    for module_name in SECTION5_HOLD_BINDING_PROFILE_CROSSLINK_OWNER_TESTS:
        assert module_name in section, f"missing owner test reference {module_name!r}"


def test_ci_audit_section5_hold_binding_profile_crosslink_machine_lines_v1() -> None:
    block = _block_containing(
        _ci_audit_text(),
        SECTION5_HOLD_BINDING_PROFILE_CROSSLINK_GUARD_BLOCK_ANCHOR,
    )
    values = _machine_line_values(block)
    missing = set(SECTION5_HOLD_BINDING_PROFILE_CROSSLINK_EXPECTED) - values.keys()
    assert not missing, f"missing SECTION5 hold-binding profile crosslink keys: {sorted(missing)}"
    for key, expected in SECTION5_HOLD_BINDING_PROFILE_CROSSLINK_EXPECTED.items():
        assert values[key] == expected, f"{key}={values[key]!r} expected {expected!r}"


def test_section5_doc_hold_binding_profile_crosslink_tokens_v1() -> None:
    text = SECTION5_DOC.read_text(encoding="utf-8")
    assert "Hold-binding profile Preflight §2a reciprocal crosslink (SECTION5 guard)" in text
    assert SECTION5_HOLD_BINDING_PROFILE_CROSSLINK_GUARD_BLOCK_ANCHOR in text
    assert "gap4_req_a_paper_bounded_v0" in text
    assert "paper_l2_120min_hold_binding_v0" in text
    assert "test_gap4_req_a_300s_hold_binding_profile_contract_v0.py" in text
    assert "test_paper_l2_120min_hold_binding_profile_contract_v0.py" in text


def test_docs_truth_map_section5_hold_binding_profile_crosslink_chronicle_v1() -> None:
    text = DOCS_TRUTH_MAP.read_text(encoding="utf-8")
    assert (
        "SECTION5 Gap Owner Map hold-binding profile Preflight §2a reciprocal crosslink guard v1"
        in text
    )
    assert THIS_MODULE in text
    assert SECTION5_HOLD_BINDING_PROFILE_CROSSLINK_GUARD_BLOCK_ANCHOR in text
    assert "gap4_req_a_paper_bounded_v0" in text
    assert "paper_l2_120min_hold_binding_v0" in text
    assert "test_section5_preflight_gap_owner_map_contract_v0.py" in text
    assert "**no** execute / Preflight-Lift / runtime" in text
    assert "DOCS_DRIFT_OR_POINTER_INTEGRITY_DEFERRED=true" in text


def test_docs_truth_map_paper_l2_preflight_2a_reciprocal_crosslink_chronicle_v1() -> None:
    text = DOCS_TRUTH_MAP.read_text(encoding="utf-8")
    assert "Paper-L2 120min hold-binding Preflight §2a reciprocal crosslink guard v1" in text
    assert THIS_MODULE in text
    assert "PAPER_L2_120MIN_HOLD_BINDING_PREFLIGHT_2A_RECIPROCAL_CROSSLINK_V1=true" in text
    assert "paper_l2_120min_hold_binding_v0" in text
    assert "gap4_req_a_paper_bounded_v0" in text
    assert "7200s" in text
    assert "Scheduler Boundary §10b" in text
    assert "test_paper_l2_120min_hold_binding_profile_contract_v0.py" in text
    assert "test_paper_shadow_247_preflight_contract_v0.py" in text
    assert "**no** execute / Preflight-Lift / runtime" in text
    assert "DOCS_DRIFT_OR_POINTER_INTEGRITY_DEFERRED=true" in text


def _pe11_bounded_futures_ci_audit_crosslink_section(text: str) -> str:
    start = text.find(PE11_BOUNDED_FUTURES_CI_AUDIT_CROSSLINK_HEADING)
    assert start != -1, "missing PE-11 bounded futures CI_AUDIT crosslink section"
    next_heading = text.find("\n## ", start + 1)
    if next_heading == -1:
        return text[start:]
    return text[start:next_heading]


def test_ci_audit_pe11_bounded_futures_reachability_crosslink_section_present_v1() -> None:
    text = _ci_audit_text()
    section = _pe11_bounded_futures_ci_audit_crosslink_section(text)
    assert "GO_PE11_BOUNDED_FUTURES_CI_AUDIT_RECIPROCAL_CROSSLINK_DOCS_TESTS_NO_RUN_V1" in section
    assert "PE-11 Governed Bounded Futures Reachability Reflection v0" in section
    assert "SECTION5_PREFLIGHT_GAP_OWNER_MAP_CONTRACT_V0.md" in section
    assert "REACHABILITY_PROVEN_NOT_ORDER_AUTHORIZED" in section
    assert "no parallel pe-11 ssot" in section.lower()
    assert THIS_MODULE in section
    for module_name in PE11_BOUNDED_FUTURES_CI_AUDIT_CROSSLINK_OWNER_TESTS:
        assert module_name in section, f"missing owner test reference {module_name!r}"


def test_ci_audit_pe11_bounded_futures_reachability_crosslink_machine_lines_v1() -> None:
    block = _block_containing(
        _ci_audit_text(),
        PE11_BOUNDED_FUTURES_CI_AUDIT_CROSSLINK_GUARD_BLOCK_ANCHOR,
    )
    values = _machine_line_values(block)
    missing = set(PE11_BOUNDED_FUTURES_CI_AUDIT_CROSSLINK_EXPECTED) - values.keys()
    assert not missing, f"missing PE-11 CI_AUDIT crosslink keys: {sorted(missing)}"
    for key, expected in PE11_BOUNDED_FUTURES_CI_AUDIT_CROSSLINK_EXPECTED.items():
        assert values[key] == expected, f"{key}={values[key]!r} expected {expected!r}"


def test_section5_doc_pe11_bounded_futures_reachability_owner_present_v1() -> None:
    text = SECTION5_DOC.read_text(encoding="utf-8")
    assert "## PE-11 Governed Bounded Futures Reachability Reflection v0" in text
    assert "PE11_BOUNDED_FUTURES_REACHABILITY_GOVERNED_REFLECTION_V0=true" in text
    assert "REACHABILITY_PROVEN_NOT_ORDER_AUTHORIZED=true" in text
    assert "bounded_futures_private_readonly_contract_v0.py" in text
    assert PE11_BOUNDED_FUTURES_CI_AUDIT_CROSSLINK_GUARD_BLOCK_ANCHOR not in text


def test_docs_truth_map_pe11_bounded_futures_ci_audit_crosslink_chronicle_v1() -> None:
    text = DOCS_TRUTH_MAP.read_text(encoding="utf-8")
    assert (
        "PE-11 Bounded Futures reachability CI_AUDIT ↔ SECTION5 reciprocal crosslink guard v1"
        in text
    )
    assert THIS_MODULE in text
    assert PE11_BOUNDED_FUTURES_CI_AUDIT_CROSSLINK_GUARD_BLOCK_ANCHOR in text
    assert "REACHABILITY_PROVEN_NOT_ORDER_AUTHORIZED=true" in text
    assert "test_section5_preflight_gap_owner_map_contract_v0.py" in text
    assert "test_bounded_futures_private_readonly_contract_v0.py" in text
    assert "**no** execute / Preflight-Lift / futures-session / runtime" in text
    assert "DOCS_DRIFT_OR_POINTER_INTEGRITY_DEFERRED=true" in text


def _market_dashboard_trading_app_terminal_rebuild_pr4162_section(text: str) -> str:
    start = text.find(MARKET_DASHBOARD_TRADING_APP_TERMINAL_REBUILD_PR4162_HEADING)
    assert start != -1, "missing market dashboard trading-app terminal rebuild PR4162 section"
    next_heading = text.find("\n## ", start + 1)
    if next_heading == -1:
        return text[start:]
    return text[start:next_heading]


def test_ci_audit_market_dashboard_trading_app_terminal_rebuild_pr4162_section_present_v1() -> None:
    text = _ci_audit_text()
    section = _market_dashboard_trading_app_terminal_rebuild_pr4162_section(text)
    assert MARKET_DASHBOARD_TRADING_APP_TERMINAL_REBUILD_PR4162_RANKING_BUNDLE in section
    assert MARKET_DASHBOARD_TRADING_APP_TERMINAL_REBUILD_PR4162_CLOSEOUT_BUNDLE in section
    assert MARKET_DASHBOARD_TRADING_APP_TERMINAL_REBUILD_PR4162_VISUAL_BUNDLE in section
    assert "PR #4162 on main @ `9a8c259f1c5f41d8b617bd15b93d1c518473e80e`" in section
    assert "closed after visual PASS" in section
    assert "without reopening the Market Dashboard UI lane" in section
    assert THIS_MODULE in section
    for module_name in MARKET_DASHBOARD_TRADING_APP_TERMINAL_REBUILD_PR4162_OWNER_TESTS:
        assert module_name in section, f"missing owner test reference {module_name!r}"
    for surface_name in MARKET_DASHBOARD_TRADING_APP_TERMINAL_REBUILD_PR4162_OWNER_SURFACES:
        assert surface_name in section, f"missing owner surface reference {surface_name!r}"


def test_ci_audit_market_dashboard_trading_app_terminal_rebuild_pr4162_machine_lines_v1() -> None:
    block = _block_containing(
        _ci_audit_text(),
        MARKET_DASHBOARD_TRADING_APP_TERMINAL_REBUILD_PR4162_GUARD_BLOCK_ANCHOR,
    )
    values = _machine_line_values(block)
    missing = set(MARKET_DASHBOARD_TRADING_APP_TERMINAL_REBUILD_PR4162_EXPECTED) - values.keys()
    assert not missing, (
        f"missing market dashboard trading-app terminal rebuild PR4162 keys: {sorted(missing)}"
    )
    for key, expected in MARKET_DASHBOARD_TRADING_APP_TERMINAL_REBUILD_PR4162_EXPECTED.items():
        assert values[key] == expected, f"{key}={values[key]!r} expected {expected!r}"


def test_docs_truth_map_market_dashboard_trading_app_terminal_rebuild_pr4162_chronicle_v1() -> None:
    text = DOCS_TRUTH_MAP.read_text(encoding="utf-8")
    assert (
        "Market Dashboard trading-app terminal rebuild PR #4162 DOCS_TRUTH_MAP static crosslink guard v1"
        in text
    )
    assert THIS_MODULE in text
    assert (
        "MARKET_DASHBOARD_TRADING_APP_TERMINAL_REBUILD_PR4162_CROSSLINK_GUARD_IMPLEMENTED=true"
        in text
    )
    assert "MARKET_DASHBOARD_LANE_CLOSED_AFTER_VISUAL_PASS=true" in text
    assert "9a8c259f1c5f41d8b617bd15b93d1c518473e80e" in text
    assert "test_market_terminal_layout_v1.py" in text
    assert "data-market-trading-app-terminal-v1" in text
    assert (
        "**no** UI/runtime/trading/Master-V2/Double-Play-decision-logic/protected-scope touch/Market-Airport"
        in text
    )
    assert (
        MARKET_DASHBOARD_TRADING_APP_TERMINAL_REBUILD_PR4162_RANKING_BUNDLE.split("/")[-1] in text
    )
