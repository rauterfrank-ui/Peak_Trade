"""Static contract for CSC-RCHAIN-v1 accepted groups reflection guard v0.

Reads docs/ops/CI_AUDIT_KNOWN_ISSUES.md only. Never ingests JSONL, never
dispatches workflows, never touches runtime, scheduler, Notion, Market,
broker/exchange, network, secrets, or scan paths.
"""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
CI_AUDIT_KNOWN_ISSUES = REPO_ROOT / "docs" / "ops" / "CI_AUDIT_KNOWN_ISSUES.md"
DOCS_TRUTH_MAP = REPO_ROOT / "docs" / "ops" / "registry" / "DOCS_TRUTH_MAP.md"
THIS_MODULE = Path(__file__).name
CSC_LOSSLESS_V1_GUARD_MODULE = "test_csc_lossless_v1_dataset_reflection_contract_v0.py"
STATIC_INVENTORY_GUARD_MODULE = "test_static_inventory_schema_guard_contract_v0.py"
MAPPING_GUARD_MODULE = "test_cybersecurity_visibility_r_pending_mapping_guard_v0.py"

ACCEPT_GROUPS = (
    "CSC-RCHAIN-v1-006",
    "CSC-RCHAIN-v1-007",
    "CSC-RCHAIN-v1-008",
    "CSC-RCHAIN-v1-009a",
    "CSC-RCHAIN-v1-009b",
    "CSC-RCHAIN-v1-002-infra",
    "CSC-RCHAIN-v1-002-integration",
    "CSC-RCHAIN-v1-002-p101",
    "CSC-RCHAIN-v1-002-p117",
    "CSC-RCHAIN-v1-002-p50",
    "CSC-RCHAIN-v1-002-ci-workflow-visibility",
    "CSC-RCHAIN-v1-002-observability",
    "CSC-RCHAIN-v1-001-ops-autonomous-control-plane",
    "CSC-RCHAIN-v1-001-ops-control-plane-offline",
    "CSC-RCHAIN-v1-001-ops-gap-contracts",
    "CSC-RCHAIN-v1-001-ops-gap-contracts-gap4-gap5",
    "CSC-RCHAIN-v1-001-ops-gap-contracts-gap6-gap7",
    "CSC-RCHAIN-v1-001-ops-evidence-closeout-build-contracts",
    "CSC-RCHAIN-v1-001-ops-closeout-contracts",
    "CSC-RCHAIN-v1-001-ops-bounded-durable-evidence-contracts",
    "CSC-RCHAIN-v1-001-ops-post-closeout-contracts",
    "CSC-RCHAIN-v1-001-ops-remote-planning-contracts",
    "CSC-RCHAIN-v1-002-tests-misc-contracts",
)
PARK_GROUPS = (
    "CSC-RCHAIN-v1-001",
    "CSC-RCHAIN-v1-002",
    "CSC-RCHAIN-v1-003",
    "CSC-RCHAIN-v1-004",
    "CSC-RCHAIN-v1-005",
    "CSC-RCHAIN-v1-009",
)

OPERATOR_DECISION = (
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/"
    "planning/csc_rchain_v1_operator_decision_filed_v0_20260601T045040Z"
)
GROUPING_REVIEW = (
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/"
    "planning/csc_lossless_v1_r_chain_candidate_grouping_review_v0_20260601T044523Z"
)
EXTERNAL_AUTHORITY_BUNDLE = (
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/"
    "planning/csc_rchain_v1_external_full_authority_bundle_draft_and_wiring_check_readonly_v0_20260601T104257Z"
)
OPERATOR_BATCH_ACCEPT = (
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/"
    "planning/csc_rchain_v1_tier_a_002_ci_workflow_visibility_batch_operator_accept_and_governed_reflection_v0_20260601T111100Z"
)
EXTERNAL_BATCH_REVIEW = (
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/"
    "planning/csc_rchain_v1_tier_a_002_ci_workflow_visibility_batch_external_review_readonly_v0_20260601T110733Z"
)
REFRESHED_AUTHORITY_BUNDLE = (
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/"
    "planning/csc_rchain_v1_post_ops_closeout_contracts_batch_authority_refresh_and_next_batch_ranking_readonly_v0_20260601T133828Z"
)
GROUP_PARK_REAFFIRMED_GROUPS: tuple[str, ...] = (
    "CSC-RCHAIN-v1-002-tests-retained-park",
    "CSC-RCHAIN-v1-004-scripts-ops-retained-park",
    "CSC-RCHAIN-v1-001-tests-ops-retained-park",
    "CSC-RCHAIN-v1-005-tests-fixtures-retained-park",
    "CSC-RCHAIN-v1-002-tests-ci-retained-park",
    "CSC-RCHAIN-v1-002-tests-webui-retained-park",
    "CSC-RCHAIN-v1-002-tests-governance-retained-park",
    "CSC-RCHAIN-v1-002-tests-execution-retained-park",
    "CSC-RCHAIN-v1-002-tests-testnet-root-retained-park",
)
OPERATOR_BATCH_ACCEPT_TIER_A_003 = (
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/"
    "planning/csc_rchain_v1_tier_a_003_002_observability_batch_operator_accept_and_governed_reflection_v0_20260601T113119Z"
)
EXTERNAL_BATCH_REVIEW_TIER_A_003 = (
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/"
    "planning/csc_rchain_v1_tier_a_003_002_observability_batch_external_review_readonly_v0_20260601T112818Z"
)
OPERATOR_BATCH_ACCEPT_TIER_A_004 = (
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/"
    "planning/csc_rchain_v1_tier_a_004_001_ops_autonomous_control_plane_batch_operator_accept_and_governed_reflection_v0_20260601T114607Z"
)
EXTERNAL_BATCH_REVIEW_TIER_A_004 = (
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/"
    "planning/csc_rchain_v1_tier_a_004_001_ops_autonomous_control_plane_batch_external_review_readonly_v0_20260601T114411Z"
)
OPERATOR_BATCH_ACCEPT_TIER_A_005 = (
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/"
    "planning/csc_rchain_v1_tier_a_005_001_ops_control_plane_offline_batch_operator_accept_and_governed_reflection_v0_20260601T120540Z"
)
EXTERNAL_BATCH_REVIEW_TIER_A_005 = (
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/"
    "planning/csc_rchain_v1_tier_a_005_001_ops_control_plane_offline_batch_external_review_readonly_v0_20260601T120135Z"
)
OPERATOR_BATCH_ACCEPT_TIER_A_006 = (
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/"
    "planning/csc_rchain_v1_tier_a_006_001_ops_gap_contracts_batch_operator_accept_and_governed_reflection_v0_20260601T122137Z"
)
EXTERNAL_BATCH_REVIEW_TIER_A_006 = (
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/"
    "planning/csc_rchain_v1_tier_a_006_001_ops_gap_contracts_batch_external_review_readonly_v0_20260601T121851Z"
)
OPERATOR_BATCH_ACCEPT_TIER_A_007 = (
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/"
    "planning/csc_rchain_v1_tier_a_007_001_ops_gap_contracts_gap4_gap5_batch_operator_accept_and_governed_reflection_v0_20260601T124200Z"
)
EXTERNAL_BATCH_REVIEW_TIER_A_007 = (
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/"
    "planning/csc_rchain_v1_tier_a_007_001_ops_gap_contracts_gap4_gap5_batch_external_review_readonly_v0_20260601T123533Z"
)
OPERATOR_BATCH_ACCEPT_TIER_A_007_002 = (
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/"
    "planning/csc_rchain_v1_tier_a_007_002_ops_gap_contracts_gap6_gap7_batch_operator_accept_and_governed_reflection_v0_20260601T130015Z"
)
EXTERNAL_BATCH_REVIEW_TIER_A_007_002 = (
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/"
    "planning/csc_rchain_v1_tier_a_007_002_ops_gap_contracts_gap6_gap7_batch_external_review_readonly_v0_20260601T125721Z"
)
OPERATOR_BATCH_ACCEPT_TIER_A_007_003 = (
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/"
    "planning/csc_rchain_v1_tier_a_007_003_ops_evidence_closeout_build_contracts_batch_operator_accept_and_governed_reflection_v0_20260601T131510Z"
)
EXTERNAL_BATCH_REVIEW_TIER_A_007_003 = (
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/"
    "planning/csc_rchain_v1_tier_a_007_003_ops_evidence_closeout_build_contracts_batch_external_review_readonly_v0_20260601T131231Z"
)
OPERATOR_BATCH_ACCEPT_TIER_A_008_001 = (
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/"
    "planning/csc_rchain_v1_tier_a_008_001_ops_closeout_contracts_batch_operator_accept_and_governed_reflection_v0_20260601T134600Z"
)
EXTERNAL_BATCH_REVIEW_TIER_A_008_001 = (
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/"
    "planning/csc_rchain_v1_tier_a_008_001_ops_closeout_contracts_batch_external_review_readonly_v0_20260601T133200Z"
)
OPERATOR_BATCH_ACCEPT_TIER_A_009_001 = (
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/"
    "planning/csc_rchain_v1_pr02_tier_a_009_001_ops_bounded_durable_evidence_contracts_accept_wave_implementation_v0_20260601T140547Z"
)
EXTERNAL_BATCH_REVIEW_TIER_A_009_001 = (
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/"
    "planning/csc_rchain_v1_post_pr01_authority_refresh_and_pr02_scope_ranking_readonly_v0_20260601T140212Z"
)
OPERATOR_BATCH_ACCEPT_TIER_A_009_002 = (
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/"
    "planning/csc_rchain_v1_pr03_tier_a_009_002_ops_post_closeout_contracts_accept_wave_implementation_v0_20260601T142200Z"
)
EXTERNAL_BATCH_REVIEW_TIER_A_009_002 = (
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/"
    "planning/csc_rchain_v1_post_pr02_authority_refresh_and_pr03_scope_ranking_readonly_v0_20260601T141144Z"
)
OPERATOR_BATCH_ACCEPT_TIER_A_009_003 = (
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/"
    "planning/csc_rchain_v1_pr04_tier_a_009_003_ops_remote_planning_contracts_accept_wave_implementation_v0_20260601T142300Z"
)
EXTERNAL_BATCH_REVIEW_TIER_A_009_003 = (
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/"
    "planning/csc_rchain_v1_post_pr03_authority_refresh_and_pr04_scope_ranking_readonly_v0_20260601T142048Z"
)
OPERATOR_BATCH_ACCEPT_TIER_A_002_004 = (
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/"
    "planning/csc_rchain_v1_pr05_tier_a_002_004_tests_misc_contracts_accept_wave_implementation_v0_20260601T144600Z"
)
EXTERNAL_BATCH_REVIEW_TIER_A_002_004 = (
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/"
    "planning/csc_rchain_v1_post_pr04_authority_refresh_and_pr05_scope_ranking_readonly_v0_20260601T143905Z"
)
OPERATOR_BATCH_GROUP_PARK_REAFFIRM_002_001 = (
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/"
    "planning/csc_rchain_v1_pr06_group_park_reaffirm_002_001_tests_retained_park_implementation_v0_20260601T145300Z"
)
EXTERNAL_BATCH_REVIEW_PR06 = (
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/"
    "planning/csc_rchain_v1_post_pr05_authority_refresh_and_pr06_group_park_reaffirmation_scope_ranking_readonly_v0_20260601T144811Z"
)
OPERATOR_BATCH_GROUP_PARK_REAFFIRM_004_001 = (
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/"
    "planning/csc_rchain_v1_pr07_group_park_reaffirm_004_001_scripts_ops_retained_park_implementation_v0_20260601T150544Z"
)
EXTERNAL_BATCH_REVIEW_PR07 = (
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/"
    "planning/csc_rchain_v1_post_pr06_authority_refresh_and_pr07_group_park_reaffirmation_scope_ranking_readonly_v0_20260601T150139Z"
)
OPERATOR_BATCH_GROUP_PARK_REAFFIRM_001_001 = (
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/"
    "planning/csc_rchain_v1_pr08_group_park_reaffirm_001_001_tests_ops_retained_park_implementation_v0_20260601T151800Z"
)
EXTERNAL_BATCH_REVIEW_PR08 = (
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/"
    "planning/csc_rchain_v1_post_pr07_authority_refresh_and_pr08_group_park_reaffirmation_scope_ranking_readonly_v0_20260601T151436Z"
)
OPERATOR_BATCH_GROUP_PARK_REAFFIRM_005_001 = (
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/"
    "planning/csc_rchain_v1_pr09_group_park_reaffirm_005_001_tests_fixtures_retained_park_implementation_v0_20260601T153024Z"
)
EXTERNAL_BATCH_REVIEW_PR09 = (
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/"
    "planning/csc_rchain_v1_post_pr08_authority_refresh_and_pr09_group_park_reaffirmation_scope_ranking_readonly_v0_20260601T152834Z"
)
OPERATOR_BATCH_GROUP_PARK_REAFFIRM_002_002 = (
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/"
    "planning/csc_rchain_v1_pr10_group_park_reaffirm_002_002_tests_ci_retained_park_implementation_v0_20260601T153917Z"
)
EXTERNAL_BATCH_REVIEW_PR10 = (
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/"
    "planning/csc_rchain_v1_post_pr09_authority_refresh_and_pr10_group_park_reaffirmation_scope_ranking_readonly_v0_20260601T153648Z"
)
OPERATOR_BATCH_GROUP_PARK_REAFFIRM_002_003 = (
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/"
    "planning/csc_rchain_v1_pr11_group_park_reaffirm_002_003_tests_webui_retained_park_implementation_v0_20260601T154840Z"
)
EXTERNAL_BATCH_REVIEW_PR11 = (
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/"
    "planning/csc_rchain_v1_post_pr10_authority_refresh_and_pr11_group_park_reaffirmation_scope_ranking_readonly_v0_20260601T154526Z"
)
OPERATOR_BATCH_GROUP_PARK_REAFFIRM_002_004 = (
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/"
    "planning/csc_rchain_v1_pr12_group_park_reaffirm_002_004_tests_governance_retained_park_implementation_v0_20260601T155649Z"
)
EXTERNAL_BATCH_REVIEW_PR12 = (
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/"
    "planning/csc_rchain_v1_post_pr11_authority_refresh_and_pr12_group_park_reaffirmation_scope_ranking_readonly_v0_20260601T155403Z"
)
OPERATOR_BATCH_GROUP_PARK_REAFFIRM_002_005 = (
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/"
    "planning/csc_rchain_v1_pr13_group_park_reaffirm_002_005_tests_execution_retained_park_implementation_v0_20260601T160431Z"
)
EXTERNAL_BATCH_REVIEW_PR13 = (
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/"
    "planning/csc_rchain_v1_post_pr12_authority_refresh_and_pr13_group_park_reaffirmation_scope_ranking_readonly_v0_20260601T160218Z"
)
OPERATOR_BATCH_GROUP_PARK_REAFFIRM_002_006 = (
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/"
    "planning/csc_rchain_v1_pr14_group_park_reaffirm_002_006_tests_testnet_root_retained_park_implementation_v0_20260601T161724Z"
)
EXTERNAL_BATCH_REVIEW_PR14 = (
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/"
    "planning/csc_rchain_v1_post_pr13_authority_refresh_and_pr14_group_park_reaffirmation_or_finalization_scope_ranking_readonly_v0_20260601T161036Z"
)

GUARD_BLOCK_ANCHOR = "CYBERSECURITY_CSC_RCHAIN_V1_ACCEPTED_GROUPS_REFLECTION_GUARD_V0=true"

EXPECTED_MACHINE_LINES: dict[str, str] = {
    "CSC_RCHAIN_V1_OPERATOR_DECISION_RECORDED": "true",
    "CSC_RCHAIN_V1_ACCEPTED_GROUPS": (
        "CSC-RCHAIN-v1-006,CSC-RCHAIN-v1-007,CSC-RCHAIN-v1-008,"
        "CSC-RCHAIN-v1-009a,CSC-RCHAIN-v1-009b,CSC-RCHAIN-v1-002-infra,"
        "CSC-RCHAIN-v1-002-integration,CSC-RCHAIN-v1-002-p101,"
        "CSC-RCHAIN-v1-002-p117,CSC-RCHAIN-v1-002-p50,"
        "CSC-RCHAIN-v1-002-ci-workflow-visibility,"
        "CSC-RCHAIN-v1-002-observability,"
        "CSC-RCHAIN-v1-001-ops-autonomous-control-plane,"
        "CSC-RCHAIN-v1-001-ops-control-plane-offline,"
        "CSC-RCHAIN-v1-001-ops-gap-contracts,"
        "CSC-RCHAIN-v1-001-ops-gap-contracts-gap4-gap5,"
        "CSC-RCHAIN-v1-001-ops-gap-contracts-gap6-gap7,"
        "CSC-RCHAIN-v1-001-ops-evidence-closeout-build-contracts,"
        "CSC-RCHAIN-v1-001-ops-closeout-contracts,"
        "CSC-RCHAIN-v1-001-ops-bounded-durable-evidence-contracts,"
        "CSC-RCHAIN-v1-001-ops-post-closeout-contracts,"
        "CSC-RCHAIN-v1-001-ops-remote-planning-contracts,"
        "CSC-RCHAIN-v1-002-tests-misc-contracts"
    ),
    "CSC_RCHAIN_V1_ACCEPTED_GROUP_COUNT": "23",
    "CSC_RCHAIN_V1_ACCEPTED_CANDIDATE_COUNT": "258",
    "CSC_RCHAIN_V1_PARKED_GROUP_COUNT": "6",
    "CSC_RCHAIN_V1_REJECTED_GROUPS": "",
    "CSC_RCHAIN_V1_NEED_MORE_REVIEW_GROUPS": "",
    "SOURCE_DATASET_ID_FAMILY": "CSC-LOSSLESS-v1",
    "SOURCE_DATASET_RECORD_COUNT": "672",
    "NEW_RCHAIN_FAMILY": "CSC-RCHAIN-v1",
    "TRACEABILITY_TO_CSC_LOSSLESS_PASSED": "true",
    "OLD_R_ID_MAPPING_ALLOWED": "false",
    "OLD_R_ID_EQUIVALENCE_CLAIM_ALLOWED": "false",
    "OLD_R_ID_EQUIVALENCE_CLAIM_COUNT": "0",
    "OLD_RCHAIN_RESTORED": "false",
    "LEGACY_R_ID_REFERENCE_ALLOWED": "false",
    "FAKE_RECONSTRUCTION_ALLOWED": "false",
    "STATIC_INVENTORY_IS_SEPARATE_SOURCE": "true",
    "STATIC_INVENTORY_RECORD_COUNT": "162",
    "PARK_GROUPS_NOT_AUTHORIZED_FOR_REFLECTION": "true",
    "SCHEDULER_PARK_GROUPS_SPLIT_RECOMMENDED": "true",
    "GROUP_009_SPLIT_RECOMMENDED": "true",
    "SECURITY_SCAN_STARTED": "false",
    "RUNTIME_STARTED": "false",
    "SCHEDULER_STARTED": "false",
    "AWS_TOUCHED": "false",
    "NETWORK_TOUCHED": "false",
    "SECRETS_INCLUDED": "false",
    "CSC_RCHAIN_V1_HYBRID_AUTHORITY_POINTER_ACTIVE": "true",
    "CSC_RCHAIN_V1_EXTERNAL_AUTHORITY_BUNDLE": EXTERNAL_AUTHORITY_BUNDLE,
    "CSC_RCHAIN_V1_REFRESHED_AUTHORITY_BUNDLE": REFRESHED_AUTHORITY_BUNDLE,
    "CSC_RCHAIN_V1_EXTERNAL_AUTHORITY_CSV": "FULL_AUTHORITY_BUNDLE_DRAFT.csv",
    "CSC_RCHAIN_V1_EXTERNAL_AUTHORITY_JSON": "FULL_AUTHORITY_BUNDLE_DRAFT.json",
    "CSC_RCHAIN_V1_AUTHORITY_DRAFT_ROWS": "672",
    "CSC_RCHAIN_V1_ACCEPT_REPO_REFLECTED_COUNT": "258",
    "CSC_RCHAIN_V1_REVIEWED_PREPARED_ONLY_COUNT": "1",
    "CSC_RCHAIN_V1_PARK_COUNT": "413",
    "CSC_RCHAIN_V1_BASE_AUTHORITY_BUNDLE_SNAPSHOT_ACCEPT_COUNT": "129",
    "CSC_RCHAIN_V1_BASE_AUTHORITY_BUNDLE_SNAPSHOT_PARK_COUNT": "542",
    "CSC_RCHAIN_V1_COUNTS_CONSISTENT": "true",
    "CSC_RCHAIN_V1_REVIEWED_PREPARED_ONLY_UNIT": "CSC-RCHAIN-v1-002-p63",
    "CSC_RCHAIN_V1_REVIEWED_PREPARED_ONLY_CANDIDATE": "CSC-LOSSLESS-v1-000603",
    "CSC_RCHAIN_V1_REVIEWED_PREPARED_ONLY_TARGET": (
        "tests/p63/test_online_readiness_shadow_runner_v1.py"
    ),
    "CSC_RCHAIN_V1_002_P63_ACCEPTED": "false",
    "CSC_RCHAIN_V1_PARENT_002_REMAINS_PARKED": "true",
    "CSC_RCHAIN_V1_PARENT_009_REMAINS_PARKED": "true",
    "CSC_RCHAIN_V1_GROUPS_001_003_004_005_REMAIN_PARKED": "true",
    "CSC_RCHAIN_V1_OLD_124_COUNT_BUNDLES_HISTORICAL_ONLY": "true",
    "CSC_RCHAIN_V1_NO_OLD_R_ID_EQUIVALENCE_CLAIMS": "true",
    "CSC_RCHAIN_V1_NO_FAKE_RECONSTRUCTION": "true",
    "CSC_RCHAIN_V1_OLD_RCHAIN_RESTORED": "false",
    "CSC_RCHAIN_V1_NO_ENABLEMENT_CLAIMS": "true",
    "CSC_RCHAIN_V1_MASTER_V2_DOUBLE_PLAY_TRADING_LOGIC_NO_TOUCH": "true",
    "CSC_RCHAIN_V1_NO_PARALLEL_DOCS_BUILDS_SURFACES": "true",
    "CSC_RCHAIN_V1_GROUP_PARK_REAFFIRMATION_MODEL_ACTIVE": "true",
    "CSC_RCHAIN_V1_GROUP_PARK_REAFFIRMED_GROUPS": (
        "CSC-RCHAIN-v1-002-tests-retained-park,CSC-RCHAIN-v1-004-scripts-ops-retained-park,"
        "CSC-RCHAIN-v1-001-tests-ops-retained-park,CSC-RCHAIN-v1-005-tests-fixtures-retained-park,"
        "CSC-RCHAIN-v1-002-tests-ci-retained-park,"
        "CSC-RCHAIN-v1-002-tests-webui-retained-park,"
        "CSC-RCHAIN-v1-002-tests-governance-retained-park,"
        "CSC-RCHAIN-v1-002-tests-execution-retained-park,"
        "CSC-RCHAIN-v1-002-tests-testnet-root-retained-park"
    ),
    "CSC_RCHAIN_V1_GROUP_PARK_REAFFIRMED_GROUP_COUNT": "9",
    "CSC_RCHAIN_V1_GROUP_PARK_REAFFIRMED_CANDIDATE_COUNT": "238",
    "CSC_RCHAIN_V1_GROUP_PARK_REAFFIRMED_SUBSET_OF_PARK": "true",
}


def _ci_audit_text() -> str:
    return CI_AUDIT_KNOWN_ISSUES.read_text(encoding="utf-8")


def _guard_block(text: str) -> str:
    start = text.index("### CSC-RCHAIN-v1 accepted groups reflection guard v0")
    end_marker = "### CSC-RCHAIN-v1-003f-A governed reflection guard v0"
    if end_marker in text[start:]:
        end = text.index(end_marker, start)
    else:
        end = text.index("### Static visibility contract owners", start)
    return text[start:end]


def _guard_block_003f_a(text: str) -> str:
    start = text.index("### CSC-RCHAIN-v1-003f-A governed reflection guard v0")
    end_marker = "### CSC-RCHAIN-v1-003f-C governed reflection guard v0"
    if end_marker in text[start:]:
        end = text.index(end_marker, start)
    else:
        end = text.index("### Static visibility contract owners", start)
    return text[start:end]


def _guard_block_003f_c(text: str) -> str:
    start = text.index("### CSC-RCHAIN-v1-003f-C governed reflection guard v0")
    end_marker = "### CSC-RCHAIN-v1-003f-D governed reflection guard v0"
    if end_marker in text[start:]:
        end = text.index(end_marker, start)
    else:
        end = text.index("### Static visibility contract owners", start)
    return text[start:end]


def _guard_block_003f_d(text: str) -> str:
    start = text.index("### CSC-RCHAIN-v1-003f-D governed reflection guard v0")
    end_marker = "### CSC-RCHAIN-v1-003c governed reflection guard v0"
    if end_marker in text[start:]:
        end = text.index(end_marker, start)
    else:
        end = text.index("### Static visibility contract owners", start)
    return text[start:end]


def _guard_block_003c(text: str) -> str:
    start = text.index("### CSC-RCHAIN-v1-003c governed reflection guard v0")
    end_marker = "### CSC-RCHAIN-v1-003b governed reflection guard v0"
    if end_marker in text[start:]:
        end = text.index(end_marker, start)
    else:
        end = text.index("### Static visibility contract owners", start)
    return text[start:end]


def _guard_block_003b(text: str) -> str:
    start = text.index("### CSC-RCHAIN-v1-003b governed reflection guard v0")
    end_marker = "### CSC-RCHAIN-v1-003f-B governed reflection guard v0"
    if end_marker in text[start:]:
        end = text.index(end_marker, start)
    else:
        end = text.index("### Static visibility contract owners", start)
    return text[start:end]


def _guard_block_003f_b(text: str) -> str:
    start = text.index("### CSC-RCHAIN-v1-003f-B governed reflection guard v0")
    end_marker = "### CSC-RCHAIN-v1-003d governed reflection guard v0"
    if end_marker in text[start:]:
        end = text.index(end_marker, start)
    else:
        end = text.index("### Static visibility contract owners", start)
    return text[start:end]


def _guard_block_003d(text: str) -> str:
    start = text.index("### CSC-RCHAIN-v1-003d governed reflection guard v0")
    end_marker = "### CSC-RCHAIN-v1-005c governed reflection guard v0"
    if end_marker in text[start:]:
        end = text.index(end_marker, start)
    else:
        end = text.index("### Static visibility contract owners", start)
    return text[start:end]


def _guard_block_005c(text: str) -> str:
    start = text.index("### CSC-RCHAIN-v1-005c governed reflection guard v0")
    end_marker = "### CSC-RCHAIN-v1-005c governed reflection guard v0 (Slice-2)"
    if end_marker in text[start:]:
        end = text.index(end_marker, start)
    else:
        end = text.index("### Static visibility contract owners", start)
    return text[start:end]


def _guard_block_005c_slice2(text: str) -> str:
    start = text.index("### CSC-RCHAIN-v1-005c governed reflection guard v0 (Slice-2)")
    end_marker = "### CSC-RCHAIN-v1-005c governed reflection guard v0 (Slice-3 Testnet)"
    if end_marker in text[start:]:
        end = text.index(end_marker, start)
    else:
        end = text.index("### Static visibility contract owners", start)
    return text[start:end]


def _guard_block_005c_slice3_testnet(text: str) -> str:
    start = text.index("### CSC-RCHAIN-v1-005c governed reflection guard v0 (Slice-3 Testnet)")
    end_marker = "### CSC-RCHAIN-v1-005c governed reflection guard v0 (Slice-4 Live-Named A)"
    if end_marker in text[start:]:
        end = text.index(end_marker, start)
    else:
        end = text.index("### Static visibility contract owners", start)
    return text[start:end]


def _guard_block_005c_slice4_live_named_a(text: str) -> str:
    start = text.index("### CSC-RCHAIN-v1-005c governed reflection guard v0 (Slice-4 Live-Named A)")
    end = text.index("### Static visibility contract owners", start)
    return text[start:end]


OPERATOR_ACCEPT_003F_A_SLICE_1 = (
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/"
    "planning/operator_accept_artifact_csc_rchain_003f_a_slice_1_v0_20260602T202456Z"
)
GOVERNED_REFLECTION_SUBGROUP_003F_A = "CSC-RCHAIN-v1-003f-A"
OPERATOR_ACCEPT_003F_C_SLICE_1 = (
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/"
    "planning/operator_accept_artifact_csc_rchain_003f_c_slice_1_v0_20260602T203750Z"
)
GOVERNED_REFLECTION_SUBGROUP_003F_C = "CSC-RCHAIN-v1-003f-C"
OPERATOR_ACCEPT_003F_D_SLICE_1 = (
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/"
    "planning/operator_accept_artifact_csc_rchain_003f_d_slice_1_v0_20260602T204916Z"
)
GOVERNED_REFLECTION_SUBGROUP_003F_D = "CSC-RCHAIN-v1-003f-D"
OPERATOR_ACCEPT_003C_SLICE_1 = (
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/"
    "planning/operator_accept_artifact_csc_rchain_003c_slice_1_v0_20260602T210125Z"
)
GOVERNED_REFLECTION_SUBGROUP_003C = "CSC-RCHAIN-v1-003c"
OPERATOR_ACCEPT_003B_SLICE_1 = (
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/"
    "planning/operator_accept_artifact_csc_rchain_003b_slice_1_v0_20260602T212003Z"
)
GOVERNED_REFLECTION_SUBGROUP_003B = "CSC-RCHAIN-v1-003b"
OPERATOR_ACCEPT_003F_B_SLICE_1 = (
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/"
    "planning/operator_accept_artifact_csc_rchain_003f_b_slice_1_v0_20260602T212936Z"
)
GOVERNED_REFLECTION_SUBGROUP_003F_B = "CSC-RCHAIN-v1-003f-B"
OPERATOR_ACCEPT_003D_SLICE_1 = (
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/"
    "planning/operator_accept_artifact_csc_rchain_003d_slice_1_v0_20260602T214239Z"
)
GOVERNED_REFLECTION_SUBGROUP_003D = "CSC-RCHAIN-v1-003d"
OPERATOR_ACCEPT_005C_SLICE_1 = (
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/"
    "planning/create_operator_accept_artifact_bundle_005c_slice1_v0_20260602T220533Z"
)
OPERATOR_ACCEPT_005C_SLICE_2 = (
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/"
    "planning/create_operator_accept_artifact_bundle_005c_slice2_v0_20260602T221918Z"
)
OPERATOR_ACCEPT_005C_SLICE_3_TESTNET = (
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/"
    "planning/create_operator_accept_artifact_bundle_005c_slice3_testnet_v0_20260602T223444Z"
)
OPERATOR_ACCEPT_005C_SLICE_4_LIVE_NAMED_A = (
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/"
    "planning/create_operator_accept_artifact_bundle_005c_slice4_live_named_a_v0_20260602T224627Z"
)
GOVERNED_REFLECTION_SUBGROUP_005C = "CSC-RCHAIN-v1-005c"
NARROWING_BASENAMES_005C_SLICE2: tuple[str, ...] = (
    "health_dashboard.py",
    "run_full_portfolio.py",
    "run_offline_realtime_ma_crossover.py",
    "run_strategy_from_config.py",
    "run_sweep_strategy.py",
)
NARROWING_BASENAMES_005C_SLICE3_TESTNET: tuple[str, ...] = (
    "shadow_testnet_readiness_scorecard.py",
    "orchestrate_testnet_runs.py",
    "run_testnet_session.py",
    "smoke_test_testnet_stack.py",
    "testnet_orchestrator_cli.py",
)
NARROWING_BASENAMES_005C_SLICE4_LIVE_NAMED_A: tuple[str, ...] = (
    "check_live_readiness.py",
    "check_docs_no_live_enable_patterns.sh",
    "live_pilot_scorecard.py",
    "live_alerts_cli.py",
    "live_monitor_cli.py",
)
SCHEDULER_BOUNDARY_CROSSLINK_MODULE = "tests/ci/test_cybersecurity_visibility_repo_static_histogram_scheduler_boundary_crosslink_v0.py"


def test_csc_rchain_v1_grouping_reflection_contract_v0() -> None:
    text = _ci_audit_text()
    block = _guard_block(text)
    collapsed = block.lower()

    assert GUARD_BLOCK_ANCHOR in block
    assert "CSC-RCHAIN-v1 accepted groups reflection guard v0" in text
    assert OPERATOR_DECISION in block
    assert GROUPING_REVIEW in block
    assert THIS_MODULE in block
    assert CSC_LOSSLESS_V1_GUARD_MODULE in block
    assert STATIC_INVENTORY_GUARD_MODULE in block
    assert MAPPING_GUARD_MODULE in block

    for key, value in EXPECTED_MACHINE_LINES.items():
        assert f"{key}={value}" in block, f"missing or wrong {key}={value}"

    for gid in ACCEPT_GROUPS:
        assert gid in block
    for gid in PARK_GROUPS:
        assert gid in block

    assert "CSC_RCHAIN_V1_PARKED_GROUPS=" in block
    parked_line = next(
        line for line in block.splitlines() if line.startswith("CSC_RCHAIN_V1_PARKED_GROUPS=")
    )
    for gid in PARK_GROUPS:
        assert gid in parked_line
    accepted_line = next(
        line for line in block.splitlines() if line.startswith("CSC_RCHAIN_V1_ACCEPTED_GROUPS=")
    )
    for gid in ACCEPT_GROUPS:
        assert gid in accepted_line
    assert "CSC-RCHAIN-v1-002-p63" not in accepted_line
    assert GOVERNED_REFLECTION_SUBGROUP_003F_A not in accepted_line
    assert GOVERNED_REFLECTION_SUBGROUP_003F_C not in accepted_line
    assert GOVERNED_REFLECTION_SUBGROUP_003F_D not in accepted_line
    assert GOVERNED_REFLECTION_SUBGROUP_003C not in accepted_line
    assert GOVERNED_REFLECTION_SUBGROUP_003B not in accepted_line
    assert GOVERNED_REFLECTION_SUBGROUP_003F_B not in accepted_line
    assert GOVERNED_REFLECTION_SUBGROUP_003D not in accepted_line
    assert GOVERNED_REFLECTION_SUBGROUP_005C not in accepted_line

    assert EXTERNAL_AUTHORITY_BUNDLE in block
    assert OPERATOR_BATCH_ACCEPT in block
    assert EXTERNAL_BATCH_REVIEW in block
    assert REFRESHED_AUTHORITY_BUNDLE in block
    assert OPERATOR_BATCH_ACCEPT_TIER_A_003 in block
    assert EXTERNAL_BATCH_REVIEW_TIER_A_003 in block
    assert OPERATOR_BATCH_ACCEPT_TIER_A_004 in block
    assert EXTERNAL_BATCH_REVIEW_TIER_A_004 in block
    assert OPERATOR_BATCH_ACCEPT_TIER_A_005 in block
    assert EXTERNAL_BATCH_REVIEW_TIER_A_005 in block
    assert OPERATOR_BATCH_ACCEPT_TIER_A_006 in block
    assert EXTERNAL_BATCH_REVIEW_TIER_A_006 in block
    assert OPERATOR_BATCH_ACCEPT_TIER_A_007 in block
    assert EXTERNAL_BATCH_REVIEW_TIER_A_007 in block
    assert OPERATOR_BATCH_ACCEPT_TIER_A_007_002 in block
    assert EXTERNAL_BATCH_REVIEW_TIER_A_007_002 in block
    assert OPERATOR_BATCH_ACCEPT_TIER_A_007_003 in block
    assert EXTERNAL_BATCH_REVIEW_TIER_A_007_003 in block
    assert OPERATOR_BATCH_ACCEPT_TIER_A_008_001 in block
    assert EXTERNAL_BATCH_REVIEW_TIER_A_008_001 in block
    assert OPERATOR_BATCH_ACCEPT_TIER_A_009_001 in block
    assert EXTERNAL_BATCH_REVIEW_TIER_A_009_001 in block
    assert OPERATOR_BATCH_ACCEPT_TIER_A_009_002 in block
    assert EXTERNAL_BATCH_REVIEW_TIER_A_009_002 in block
    assert OPERATOR_BATCH_ACCEPT_TIER_A_009_003 in block
    assert EXTERNAL_BATCH_REVIEW_TIER_A_009_003 in block
    assert OPERATOR_BATCH_ACCEPT_TIER_A_002_004 in block
    assert EXTERNAL_BATCH_REVIEW_TIER_A_002_004 in block
    assert OPERATOR_BATCH_GROUP_PARK_REAFFIRM_002_001 in block
    assert EXTERNAL_BATCH_REVIEW_PR06 in block
    assert OPERATOR_BATCH_GROUP_PARK_REAFFIRM_004_001 in block
    assert EXTERNAL_BATCH_REVIEW_PR07 in block
    assert OPERATOR_BATCH_GROUP_PARK_REAFFIRM_001_001 in block
    assert EXTERNAL_BATCH_REVIEW_PR08 in block
    assert OPERATOR_BATCH_GROUP_PARK_REAFFIRM_005_001 in block
    assert EXTERNAL_BATCH_REVIEW_PR09 in block
    assert OPERATOR_BATCH_GROUP_PARK_REAFFIRM_002_002 in block
    assert EXTERNAL_BATCH_REVIEW_PR10 in block
    assert OPERATOR_BATCH_GROUP_PARK_REAFFIRM_002_003 in block
    assert EXTERNAL_BATCH_REVIEW_PR11 in block
    assert OPERATOR_BATCH_GROUP_PARK_REAFFIRM_002_004 in block
    assert EXTERNAL_BATCH_REVIEW_PR12 in block
    assert OPERATOR_BATCH_GROUP_PARK_REAFFIRM_002_005 in block
    assert EXTERNAL_BATCH_REVIEW_PR13 in block
    assert OPERATOR_BATCH_GROUP_PARK_REAFFIRM_002_006 in block
    assert EXTERNAL_BATCH_REVIEW_PR14 in block
    assert "TIER-A-004-001-ops-autonomous-control-plane-v0" in block
    assert "TIER-A-005-001-ops-control-plane-offline-v0" in block
    assert "TIER-A-006-001-ops-gap-contracts-v0" in block
    assert "TIER-A-007-001-ops-gap-contracts-gap4-gap5-v0" in block
    assert "TIER-A-007-002-ops-gap-contracts-gap6-gap7-v0" in block
    assert "TIER-A-007-003-ops-evidence-closeout-build-contracts-v0" in block
    assert "TIER-A-008-001-ops-closeout-contracts-v0" in block
    assert "TIER-A-009-001-ops-bounded-durable-evidence-contracts-v0" in block
    assert "TIER-A-009-002-ops-post-closeout-contracts-v0" in block
    assert "CSC-RCHAIN-v1-001-ops-closeout-contracts" in block
    assert "CSC-RCHAIN-v1-001-ops-bounded-durable-evidence-contracts" in block
    assert "TIER-A-009-003-ops-remote-planning-contracts-v0" in block
    assert "CSC-RCHAIN-v1-001-ops-post-closeout-contracts" in block
    assert "CSC-RCHAIN-v1-001-ops-remote-planning-contracts" in block
    assert "remote_s3_preflight_contract_bundle" in collapsed
    assert "offline preflight/planning contract verification only" in collapsed
    assert "notion_post_closeout_sync_dry_run" in collapsed
    assert "TIER-A-002-004-tests-misc-contracts-v0" in block
    assert "CSC-RCHAIN-v1-002-tests-misc-contracts" in block
    assert "GROUP-PARK-REAFFIRM-002-001-tests-retained-park-v0" in block
    assert "GROUP-PARK-REAFFIRM-004-001-scripts-ops-retained-park-v0" in block
    assert "GROUP-PARK-REAFFIRM-001-001-tests-ops-retained-park-v0" in block
    assert "GROUP-PARK-REAFFIRM-005-001-tests-fixtures-retained-park-v0" in block
    assert "GROUP-PARK-REAFFIRM-002-002-tests-ci-retained-park-v0" in block
    assert "GROUP-PARK-REAFFIRM-002-003-tests-webui-retained-park-v0" in block
    assert "GROUP-PARK-REAFFIRM-002-004-tests-governance-retained-park-v0" in block
    assert "GROUP-PARK-REAFFIRM-002-005-tests-execution-retained-park-v0" in block
    assert "GROUP-PARK-REAFFIRM-002-006-tests-testnet-root-retained-park-v0" in block
    assert "CSC-RCHAIN-v1-002-tests-retained-park" in block
    assert "CSC-RCHAIN-v1-004-scripts-ops-retained-park" in block
    assert "CSC-RCHAIN-v1-001-tests-ops-retained-park" in block
    assert "CSC-RCHAIN-v1-005-tests-fixtures-retained-park" in block
    assert "CSC-RCHAIN-v1-002-tests-ci-retained-park" in block
    assert "CSC-RCHAIN-v1-002-tests-webui-retained-park" in block
    assert "CSC-RCHAIN-v1-002-tests-governance-retained-park" in block
    assert "CSC-RCHAIN-v1-002-tests-execution-retained-park" in block
    assert "CSC-RCHAIN-v1-002-tests-testnet-root-retained-park" in block
    assert "002-tests-retained-park" in collapsed
    assert "004-scripts-ops-retained-park" in collapsed
    assert "001-tests-ops-retained-park" in collapsed
    assert "005-tests-fixtures-retained-park" in collapsed
    assert "002-tests-ci-retained-park" in collapsed
    assert "002-tests-webui-retained-park" in collapsed
    assert "002-tests-governance-retained-park" in collapsed
    assert "002-tests-execution-retained-park" in collapsed
    assert "002-tests-testnet-root-retained-park" in collapsed
    assert "test_run_testnet_session" in collapsed
    assert "test_smoke_test_testnet_stack" in collapsed
    assert "test_testnet_limits" in collapsed
    assert "test_testnet_orchestration" in collapsed
    assert "test_testnet_orchestrator_smoke" in collapsed
    assert "test_testnet_profiles" in collapsed
    assert "test_decision_context_v0" in collapsed
    assert "test_decision_context_v1" in collapsed
    assert "test_paper_session_cli_contract" in collapsed
    assert "test_policy_enforcement_contract" in collapsed
    assert "test_testnet_exec_events_safe" in collapsed
    assert "venue_adapters/test_registry" in collapsed
    assert "test_live_mode_gate" in collapsed
    assert "test_wp0c_enforce_gate" in collapsed
    assert "policy_critic" in collapsed
    assert "test_double_play_dashboard_display_json_route" in collapsed
    assert "test_paper_shadow_summary_readmodel_v0" in collapsed
    assert "reference-only static context" in collapsed
    assert "test_master_v2_double_play" in collapsed
    assert "preflight_remote_runtime_runner_v0.py" in collapsed
    assert "test_promptfoo_model_config" in collapsed
    assert "test_prcd_aws_export_write_smoke_workflow_contract" in collapsed
    assert "contract/smoke tests" in collapsed
    assert "wave **a4**" in collapsed
    assert "preflight_s3_finalized_evidence_export" in collapsed
    assert "offline/preflight contract verification only" in collapsed
    assert "reviewed-prepared-only" in collapsed
    assert "historical/stale" in collapsed
    assert "does **not** ingest `FULL_AUTHORITY_BUNDLE_DRAFT.csv`" in block
    assert "CSC_RCHAIN_V1_002_P63_ACCEPTED=false" in block

    assert "CSC_RCHAIN_V1_GROUP_PARK_REAFFIRMATION_MODEL_ACTIVE=true" in block
    reaffirmed_line = next(
        line
        for line in block.splitlines()
        if line.startswith("CSC_RCHAIN_V1_GROUP_PARK_REAFFIRMED_GROUPS=")
    )
    for gid in GROUP_PARK_REAFFIRMED_GROUPS:
        assert gid in reaffirmed_line
    assert "CSC-RCHAIN-v1-002-tests-retained-park" not in accepted_line
    assert "CSC-RCHAIN-v1-004-scripts-ops-retained-park" not in accepted_line
    assert "CSC-RCHAIN-v1-001-tests-ops-retained-park" not in accepted_line
    assert "CSC-RCHAIN-v1-005-tests-fixtures-retained-park" not in accepted_line
    assert "CSC-RCHAIN-v1-002-tests-ci-retained-park" not in accepted_line
    assert "CSC-RCHAIN-v1-002-tests-webui-retained-park" not in accepted_line
    assert "CSC-RCHAIN-v1-002-tests-governance-retained-park" not in accepted_line
    assert "CSC-RCHAIN-v1-002-tests-execution-retained-park" not in accepted_line
    assert "CSC-RCHAIN-v1-002-tests-testnet-root-retained-park" not in accepted_line
    park_count = int(
        next(
            line.split("=", 1)[1]
            for line in block.splitlines()
            if line.startswith("CSC_RCHAIN_V1_PARK_COUNT=")
        )
    )
    reaffirmed_candidate_count = int(
        next(
            line.split("=", 1)[1]
            for line in block.splitlines()
            if line.startswith("CSC_RCHAIN_V1_GROUP_PARK_REAFFIRMED_CANDIDATE_COUNT=")
        )
    )
    accept_count = int(
        next(
            line.split("=", 1)[1]
            for line in block.splitlines()
            if line.startswith("CSC_RCHAIN_V1_ACCEPT_REPO_REFLECTED_COUNT=")
        )
    )
    reviewed_count = int(
        next(
            line.split("=", 1)[1]
            for line in block.splitlines()
            if line.startswith("CSC_RCHAIN_V1_REVIEWED_PREPARED_ONLY_COUNT=")
        )
    )
    assert accept_count + reviewed_count + park_count == 672
    assert accept_count == 258
    assert reviewed_count == 1
    assert park_count == 413
    assert reaffirmed_candidate_count == 238
    assert reaffirmed_candidate_count <= park_count
    assert "group park reaffirmation" in collapsed
    assert "Does **not** treat reaffirmed groups as accepted" in block

    assert "Does **not** treat PARK groups as accepted" in block
    assert "does **not** authorize definitive R-001/R-002/R-007 mapping" in block
    assert "does **not** claim old R-ID equivalence" in block
    assert "not** restoration of the legacy" in block
    assert "non-authorizing" in collapsed
    assert "security scans" in collapsed
    assert "fake reconstruction" in collapsed
    assert "CYBERSECURITY_VISIBILITY_CHAIN_PARALLEL_ANCHOR" not in text


def test_csc_rchain_v1_grouping_reflection_truth_map_crosslink_v0() -> None:
    truth_map = DOCS_TRUTH_MAP.read_text(encoding="utf-8")
    collapsed = truth_map.lower()

    assert "CSC-RCHAIN-v1 accepted groups reflection guard v0" in truth_map
    assert THIS_MODULE in truth_map
    assert "CSC_RCHAIN_V1_ACCEPTED_CANDIDATE_COUNT=258" in truth_map
    assert "CSC-RCHAIN-v1-002-ci-workflow-visibility" in truth_map
    assert "CSC-RCHAIN-v1-002-observability" in truth_map
    assert "CSC-RCHAIN-v1-001-ops-autonomous-control-plane" in truth_map
    assert "CSC-RCHAIN-v1-001-ops-control-plane-offline" in truth_map
    assert "CSC_RCHAIN_V1_ACCEPTED_GROUP_COUNT=23" in truth_map
    assert "CSC-RCHAIN-v1-001-ops-gap-contracts" in truth_map
    assert "CSC-RCHAIN-v1-001-ops-gap-contracts-gap4-gap5" in truth_map
    assert "CSC-RCHAIN-v1-001-ops-gap-contracts-gap6-gap7" in truth_map
    assert "CSC-RCHAIN-v1-001-ops-evidence-closeout-build-contracts" in truth_map
    assert "CSC-RCHAIN-v1-001-ops-closeout-contracts" in truth_map
    assert "CSC-RCHAIN-v1-001-ops-bounded-durable-evidence-contracts" in truth_map
    assert "CSC-RCHAIN-v1-001-ops-post-closeout-contracts" in truth_map
    assert "TIER-A-009-001-ops-bounded-durable-evidence-contracts-v0" in truth_map
    assert "TIER-A-009-002-ops-post-closeout-contracts-v0" in truth_map
    assert "140212Z" in truth_map
    assert "141144Z" in truth_map
    assert "142048Z" in truth_map
    assert "143905Z" in truth_map
    assert "144811Z" in truth_map
    assert "145300Z" in truth_map
    assert "150139Z" in truth_map
    assert "150544Z" in truth_map
    assert "151436Z" in truth_map
    assert "151800Z" in truth_map
    assert "152834Z" in truth_map
    assert "153024Z" in truth_map
    assert "153648Z" in truth_map
    assert "153917Z" in truth_map
    assert "154526Z" in truth_map
    assert "155403Z" in truth_map
    assert "155649Z" in truth_map
    assert "160218Z" in truth_map
    assert "160431Z" in truth_map
    assert "161036Z" in truth_map
    assert "161724Z" in truth_map
    assert "GROUP-PARK-REAFFIRM-002-001-tests-retained-park-v0" in truth_map
    assert "GROUP-PARK-REAFFIRM-004-001-scripts-ops-retained-park-v0" in truth_map
    assert "GROUP-PARK-REAFFIRM-001-001-tests-ops-retained-park-v0" in truth_map
    assert "GROUP-PARK-REAFFIRM-005-001-tests-fixtures-retained-park-v0" in truth_map
    assert "GROUP-PARK-REAFFIRM-002-002-tests-ci-retained-park-v0" in truth_map
    assert "GROUP-PARK-REAFFIRM-002-003-tests-webui-retained-park-v0" in truth_map
    assert "GROUP-PARK-REAFFIRM-002-004-tests-governance-retained-park-v0" in truth_map
    assert "GROUP-PARK-REAFFIRM-002-005-tests-execution-retained-park-v0" in truth_map
    assert "GROUP-PARK-REAFFIRM-002-006-tests-testnet-root-retained-park-v0" in truth_map
    assert "CSC-RCHAIN-v1-002-tests-retained-park" in truth_map
    assert "CSC-RCHAIN-v1-004-scripts-ops-retained-park" in truth_map
    assert "CSC-RCHAIN-v1-001-tests-ops-retained-park" in truth_map
    assert "CSC-RCHAIN-v1-005-tests-fixtures-retained-park" in truth_map
    assert "CSC-RCHAIN-v1-002-tests-ci-retained-park" in truth_map
    assert "CSC-RCHAIN-v1-002-tests-webui-retained-park" in truth_map
    assert "CSC-RCHAIN-v1-002-tests-governance-retained-park" in truth_map
    assert "CSC-RCHAIN-v1-002-tests-execution-retained-park" in truth_map
    assert "CSC-RCHAIN-v1-002-tests-testnet-root-retained-park" in truth_map
    assert "CSC_RCHAIN_V1_GROUP_PARK_REAFFIRMED_CANDIDATE_COUNT=238" in truth_map
    assert "CSC_RCHAIN_V1_GROUP_PARK_REAFFIRMED_GROUP_COUNT=9" in truth_map
    assert "CSC-RCHAIN-v1-001-ops-remote-planning-contracts" in truth_map
    assert "CSC-RCHAIN-v1-002-tests-misc-contracts" in truth_map
    assert "TIER-A-009-003-ops-remote-planning-contracts-v0" in truth_map
    assert "TIER-A-002-004-tests-misc-contracts-v0" in truth_map
    assert "CSC-RCHAIN-v1-009a" in truth_map
    assert "CSC-RCHAIN-v1-009b" in truth_map
    assert "CSC-RCHAIN-v1-002-infra" in truth_map
    assert "CSC-RCHAIN-v1-002-integration" in truth_map
    assert "CSC-RCHAIN-v1-002-p101" in truth_map
    assert "CSC-RCHAIN-v1-002-p117" in truth_map
    assert "CSC-RCHAIN-v1-002-p50" in truth_map
    assert "PARK_GROUPS_NOT_AUTHORIZED_FOR_REFLECTION=true" in truth_map
    assert "OLD_RCHAIN_RESTORED=false" in truth_map
    assert "external hybrid authority minimal repo pointer contract v0" in collapsed
    assert EXTERNAL_AUTHORITY_BUNDLE in truth_map
    assert "124" in truth_map and "historical" in collapsed
    assert "002-p63" in truth_map
    assert "CSC_RCHAIN_V1_GROUP_PARK_REAFFIRMATION_MODEL_ACTIVE=true" in truth_map
    assert "group park reaffirmation model" in collapsed
    assert "133828Z" in truth_map
    assert "non-authorizing" in collapsed


def test_csc_rchain_v1_grouping_reflection_reciprocal_owner_modules_exist_v0() -> None:
    text = _ci_audit_text()
    assert (REPO_ROOT / "tests" / "ci" / CSC_LOSSLESS_V1_GUARD_MODULE).is_file()
    assert (REPO_ROOT / "tests" / "ci" / STATIC_INVENTORY_GUARD_MODULE).is_file()
    assert (REPO_ROOT / "tests" / "ci" / MAPPING_GUARD_MODULE).is_file()
    static_section = text.split("### Static visibility contract owners", 1)[1].split(
        "## Remote Runtime Contract", 1
    )[0]
    assert THIS_MODULE in static_section
    assert GOVERNED_REFLECTION_SUBGROUP_003F_A in static_section
    assert GOVERNED_REFLECTION_SUBGROUP_003F_C in static_section
    assert GOVERNED_REFLECTION_SUBGROUP_003F_D in static_section
    assert GOVERNED_REFLECTION_SUBGROUP_003C in static_section
    assert GOVERNED_REFLECTION_SUBGROUP_003B in static_section
    assert GOVERNED_REFLECTION_SUBGROUP_003F_B in static_section
    assert GOVERNED_REFLECTION_SUBGROUP_003D in static_section
    assert GOVERNED_REFLECTION_SUBGROUP_005C in static_section
    assert SCHEDULER_BOUNDARY_CROSSLINK_MODULE in static_section


def test_csc_rchain_v1_003f_a_governed_reflection_slice1_contract_v0() -> None:
    text = _ci_audit_text()
    block = _guard_block_003f_a(text)
    collapsed = block.lower()

    assert OPERATOR_ACCEPT_003F_A_SLICE_1 in block
    assert GOVERNED_REFLECTION_SUBGROUP_003F_A in block
    assert SCHEDULER_BOUNDARY_CROSSLINK_MODULE in block
    assert THIS_MODULE in block
    assert "CSC_RCHAIN_V1_003F_A_GOVERNED_REFLECTION_SLICE1_V0=true" in block
    assert "CSC_RCHAIN_V1_003F_A_PARK_RETAINED=true" in block
    assert "REPO_GO_TOKEN=REPO_GO-CSC-RCHAIN-003F-A-SLICE-1" in block
    assert "network_gate.py" in block
    assert "shadow_session_scheduler_v1.py" in block
    assert "run_shadowloop_pack_v1.py" in block
    assert "**Does not** add" in block
    assert "CSC_RCHAIN_V1_ACCEPTED_GROUPS" in block
    assert "258" in block
    assert "413" in block
    assert "scheduler start authorized" not in collapsed


def test_csc_rchain_v1_003f_c_governed_reflection_slice1_contract_v0() -> None:
    text = _ci_audit_text()
    block = _guard_block_003f_c(text)
    collapsed = block.lower()

    assert OPERATOR_ACCEPT_003F_C_SLICE_1 in block
    assert GOVERNED_REFLECTION_SUBGROUP_003F_C in block
    assert SCHEDULER_BOUNDARY_CROSSLINK_MODULE in block
    assert THIS_MODULE in block
    assert "CSC_RCHAIN_V1_003F_C_GOVERNED_REFLECTION_SLICE1_V0=true" in block
    assert "CSC_RCHAIN_V1_003F_C_PARK_RETAINED=true" in block
    assert "REPO_GO_TOKEN=REPO_GO-CSC-RCHAIN-003F-C-SLICE-1" in block
    assert "live_session_registry.py" in block
    assert "armstrong_cycle_strategy.py" in block
    assert "el_karoui_vol_model_strategy.py" in block
    assert "sweeps/engine.py" in block or "engine.py" in block
    assert "CSC_RCHAIN_V1_003F_A_REOPENED=false" in block
    assert "**Does not** add" in block
    assert "CSC_RCHAIN_V1_ACCEPTED_GROUPS" in block
    assert "258" in block
    assert "413" in block
    assert "strategy run authorized" not in collapsed
    assert "live session started" not in collapsed


def test_csc_rchain_v1_003f_d_governed_reflection_slice1_contract_v0() -> None:
    text = _ci_audit_text()
    block = _guard_block_003f_d(text)
    collapsed = block.lower()

    assert OPERATOR_ACCEPT_003F_D_SLICE_1 in block
    assert GOVERNED_REFLECTION_SUBGROUP_003F_D in block
    assert SCHEDULER_BOUNDARY_CROSSLINK_MODULE in block
    assert THIS_MODULE in block
    assert "CSC_RCHAIN_V1_003F_D_GOVERNED_REFLECTION_SLICE1_V0=true" in block
    assert "CSC_RCHAIN_V1_003F_D_PARK_RETAINED=true" in block
    assert "REPO_GO_TOKEN=REPO_GO-CSC-RCHAIN-003F-D-SLICE-1" in block
    assert "PEAK_TRADE_PROJECT_SUMMARY.md" in block
    assert "Peak_Trade_setup_notes.md" in block
    assert "architecture.md" in block
    assert "live_track.py" in block
    assert "ops_cockpit.py" in block
    assert "src&#47;docs&#47;" in block
    assert "CSC_RCHAIN_V1_003F_A_REOPENED=false" in block
    assert "CSC_RCHAIN_V1_003F_C_REOPENED=false" in block
    assert "**Does not** add" in block
    assert "CSC_RCHAIN_V1_ACCEPTED_GROUPS" in block
    assert "258" in block
    assert "413" in block
    assert "live track authorized" not in collapsed
    assert "ops cockpit enabled" not in collapsed


def test_csc_rchain_v1_003c_governed_reflection_slice1_contract_v0() -> None:
    text = _ci_audit_text()
    block = _guard_block_003c(text)
    collapsed = block.lower()

    assert OPERATOR_ACCEPT_003C_SLICE_1 in block
    assert GOVERNED_REFLECTION_SUBGROUP_003C in block
    assert SCHEDULER_BOUNDARY_CROSSLINK_MODULE in block
    assert THIS_MODULE in block
    assert "CSC_RCHAIN_V1_003C_GOVERNED_REFLECTION_SLICE1_V0=true" in block
    assert "CSC_RCHAIN_V1_003C_PARK_RETAINED=true" in block
    assert "REPO_GO_TOKEN=REPO_GO-CSC-RCHAIN-003C-SLICE-1" in block
    assert "ai_activation_gate_v1.py" in block
    assert "live_mode_gate.py" in block
    assert "policy_critic" in block
    assert "rules.py" in block
    assert "strategy_switch_sanity_check.py" in block
    assert "tests&#47;governance" in block
    assert "CSC_RCHAIN_V1_003F_A_REOPENED=false" in block
    assert "CSC_RCHAIN_V1_003F_C_REOPENED=false" in block
    assert "CSC_RCHAIN_V1_003F_D_REOPENED=false" in block
    assert "**Does not** add" in block
    assert "CSC_RCHAIN_V1_ACCEPTED_GROUPS" in block
    assert "258" in block
    assert "413" in block
    assert "ai activation authorized" not in collapsed
    assert "live mode enabled" not in collapsed
    assert "policy critic enabled" not in collapsed


def test_csc_rchain_v1_003b_governed_reflection_slice1_contract_v0() -> None:
    text = _ci_audit_text()
    block = _guard_block_003b(text)
    collapsed = block.lower()

    assert OPERATOR_ACCEPT_003B_SLICE_1 in block
    assert GOVERNED_REFLECTION_SUBGROUP_003B in block
    assert SCHEDULER_BOUNDARY_CROSSLINK_MODULE in block
    assert THIS_MODULE in block
    assert "CSC_RCHAIN_V1_003B_GOVERNED_REFLECTION_SLICE1_V0=true" in block
    assert "CSC_RCHAIN_V1_003B_PARK_RETAINED=true" in block
    assert "REPO_GO_TOKEN=REPO_GO-CSC-RCHAIN-003B-SLICE-1" in block
    assert "live_session.py" in block
    assert "orchestrator.py" in block
    assert "pipeline.py" in block
    assert "registry.py" in block
    assert "execution" in block.lower()
    assert "CSC_RCHAIN_V1_003F_A_REOPENED=false" in block
    assert "CSC_RCHAIN_V1_003F_C_REOPENED=false" in block
    assert "CSC_RCHAIN_V1_003F_D_REOPENED=false" in block
    assert "CSC_RCHAIN_V1_003C_REOPENED=false" in block
    assert "CSC_RCHAIN_V1_003F_B_EXCLUDED=true" in block
    assert "**Does not** add" in block
    assert "CSC_RCHAIN_V1_ACCEPTED_GROUPS" in block
    assert "258" in block
    assert "413" in block
    assert "live session authorized" not in collapsed
    assert "orchestrator enabled" not in collapsed
    assert "execution enabled" not in collapsed


def test_csc_rchain_v1_003f_b_governed_reflection_slice1_contract_v0() -> None:
    text = _ci_audit_text()
    block = _guard_block_003f_b(text)
    collapsed = block.lower()

    assert OPERATOR_ACCEPT_003F_B_SLICE_1 in block
    assert GOVERNED_REFLECTION_SUBGROUP_003F_B in block
    assert SCHEDULER_BOUNDARY_CROSSLINK_MODULE in block
    assert THIS_MODULE in block
    assert "CSC_RCHAIN_V1_003F_B_GOVERNED_REFLECTION_SLICE1_V0=true" in block
    assert "CSC_RCHAIN_V1_003F_B_PARK_RETAINED=true" in block
    assert "REPO_GO_TOKEN=REPO_GO-CSC-RCHAIN-003F-B-SLICE-1" in block
    assert "kraken_live.py" in block
    assert "kraken_testnet.py" in block
    assert "markers_v0.py" in block
    assert "observation_harness_v0.py" in block
    assert "base.py" in block
    assert "exchange" in block.lower()
    assert "shadow-no-order-proof" in block.lower() or "shadow" in block.lower()
    assert "CSC_RCHAIN_V1_003F_A_REOPENED=false" in block
    assert "CSC_RCHAIN_V1_003F_C_REOPENED=false" in block
    assert "CSC_RCHAIN_V1_003F_D_REOPENED=false" in block
    assert "CSC_RCHAIN_V1_003C_REOPENED=false" in block
    assert "CSC_RCHAIN_V1_003B_REOPENED=false" in block
    assert "**Does not** add" in block
    assert "CSC_RCHAIN_V1_ACCEPTED_GROUPS" in block
    assert "258" in block
    assert "413" in block
    assert "kraken live authorized" not in collapsed
    assert "shadow proof executed" not in collapsed
    assert "execution enabled" not in collapsed


def test_csc_rchain_v1_003d_governed_reflection_slice1_contract_v0() -> None:
    text = _ci_audit_text()
    block = _guard_block_003d(text)
    collapsed = block.lower()

    assert OPERATOR_ACCEPT_003D_SLICE_1 in block
    assert GOVERNED_REFLECTION_SUBGROUP_003D in block
    assert SCHEDULER_BOUNDARY_CROSSLINK_MODULE in block
    assert THIS_MODULE in block
    assert "CSC_RCHAIN_V1_003D_GOVERNED_REFLECTION_SLICE1_V0=true" in block
    assert "CSC_RCHAIN_V1_003D_PARK_RETAINED=true" in block
    assert "REPO_GO_TOKEN=REPO_GO-CSC-RCHAIN-003D-SLICE-1" in block
    assert "base.py" in block
    assert "exchange.py" in block
    assert "paper.py" in block
    assert "shadow.py" in block
    assert "testnet_executor.py" in block
    assert "orders" in block.lower()
    assert "routing-no-authority" in block.lower() or "routing" in block.lower()
    assert "CSC_RCHAIN_V1_003F_A_REOPENED=false" in block
    assert "CSC_RCHAIN_V1_003F_C_REOPENED=false" in block
    assert "CSC_RCHAIN_V1_003F_D_REOPENED=false" in block
    assert "CSC_RCHAIN_V1_003C_REOPENED=false" in block
    assert "CSC_RCHAIN_V1_003B_REOPENED=false" in block
    assert "CSC_RCHAIN_V1_003F_B_REOPENED=false" in block
    assert "**Does not** add" in block
    assert "CSC_RCHAIN_V1_ACCEPTED_GROUPS" in block
    assert "258" in block
    assert "413" in block
    assert "order placement authorized" not in collapsed
    assert "routing enabled" not in collapsed
    assert "testnet order enabled" not in collapsed
    assert "kraken live authorized" not in collapsed
    assert "execution enabled" not in collapsed


def test_csc_rchain_v1_005c_governed_reflection_slice1_contract_v0() -> None:
    text = _ci_audit_text()
    block = _guard_block_005c(text)
    collapsed = block.lower()

    assert OPERATOR_ACCEPT_005C_SLICE_1 in block
    assert GOVERNED_REFLECTION_SUBGROUP_005C in block
    assert SCHEDULER_BOUNDARY_CROSSLINK_MODULE in block
    assert THIS_MODULE in block
    assert "CSC_RCHAIN_V1_005C_GOVERNED_REFLECTION_SLICE1_V0=true" in block
    assert "CSC_RCHAIN_V1_005C_PARK_RETAINED=true" in block
    assert "REPO_GO_TOKEN=REPO_GO-CSC-RCHAIN-005C-SLICE-1" in block
    assert "run_backtest.py" in block
    assert "run_donchian_realistic.py" in block
    assert "run_ma_realistic.py" in block
    assert "research" in block.lower()
    assert "CSC_RCHAIN_V1_003D_REOPENED=false" in block
    assert "CSC_PARENT005A_EXCLUDED=true" in block
    assert "**Does not** add" in block
    assert "258" in block
    assert "413" in block
    assert "script execution authorized" not in collapsed
    assert "scheduler start authorized" not in collapsed
    assert "live trading enabled" not in collapsed


def test_csc_rchain_v1_005c_governed_reflection_slice2_contract_v0() -> None:
    text = _ci_audit_text()
    block = _guard_block_005c_slice2(text)
    collapsed = block.lower()

    assert OPERATOR_ACCEPT_005C_SLICE_2 in block
    assert GOVERNED_REFLECTION_SUBGROUP_005C in block
    assert SCHEDULER_BOUNDARY_CROSSLINK_MODULE in block
    assert THIS_MODULE in block
    assert "CSC_RCHAIN_V1_005C_GOVERNED_REFLECTION_SLICE2_V0=true" in block
    assert "CSC_RCHAIN_V1_005C_PARK_RETAINED=true" in block
    assert "REPO_GO_TOKEN=REPO_GO-CSC-RCHAIN-005C-SLICE-2" in block
    assert "RUN_SCHEDULER_000253_BLOCKED=true" in block
    assert "CSC_RCHAIN_V1_005C_SLICE1_REOPENED=false" in block
    for basename in NARROWING_BASENAMES_005C_SLICE2:
        assert basename in block
    assert "000250" in block
    assert "000251" in block
    assert "offline remainder" in collapsed
    assert "CSC_PARENT005A_EXCLUDED=true" in block
    assert "**Does not** add" in block
    assert "258" in block
    assert "413" in block
    assert "script execution authorized" not in collapsed
    assert "scheduler start authorized" not in collapsed
    assert "live trading enabled" not in collapsed
    assert "dashboard server start authorized" not in collapsed


def test_csc_rchain_v1_005c_governed_reflection_slice3_testnet_contract_v0() -> None:
    text = _ci_audit_text()
    block = _guard_block_005c_slice3_testnet(text)
    collapsed = block.lower()

    assert OPERATOR_ACCEPT_005C_SLICE_3_TESTNET in block
    assert GOVERNED_REFLECTION_SUBGROUP_005C in block
    assert SCHEDULER_BOUNDARY_CROSSLINK_MODULE in block
    assert THIS_MODULE in block
    assert "CSC_RCHAIN_V1_005C_GOVERNED_REFLECTION_SLICE3_TESTNET_V0=true" in block
    assert "CSC_RCHAIN_V1_005C_PARK_RETAINED=true" in block
    assert "REPO_GO_TOKEN=REPO_GO-CSC-RCHAIN-005C-SLICE-3-TESTNET" in block
    assert "RUN_SCHEDULER_000253_BLOCKED=true" in block
    assert "CSC_RCHAIN_V1_005C_SLICE1_REOPENED=false" in block
    assert "CSC_RCHAIN_V1_005C_SLICE2_REOPENED=false" in block
    assert "NO_TESTNET_EXECUTION_AUTHORITY=true" in block
    assert "TESTNET_NAMED_CLI_VISIBILITY_ONLY=true" in block
    for basename in NARROWING_BASENAMES_005C_SLICE3_TESTNET:
        assert basename in block
    assert "000158" in block
    assert "000236" in block
    assert "000257" in block
    assert "000258" in block
    assert "000259" in block
    assert "dual testnet+shadow" in collapsed or "dual testnet" in collapsed
    assert "testnet-named" in collapsed
    assert "CSC_PARENT005A_EXCLUDED=true" in block
    assert "**Does not** add" in block
    assert "258" in block
    assert "413" in block
    assert "script execution authorized" not in collapsed
    assert "scheduler start authorized" not in collapsed
    assert "testnet execution authorized" not in collapsed
    assert "testnet session authorized" not in collapsed
    assert "orchestrator dispatch authorized" not in collapsed


def test_csc_rchain_v1_005c_governed_reflection_slice4_live_named_a_contract_v0() -> None:
    text = _ci_audit_text()
    block = _guard_block_005c_slice4_live_named_a(text)
    collapsed = block.lower()

    assert OPERATOR_ACCEPT_005C_SLICE_4_LIVE_NAMED_A in block
    assert GOVERNED_REFLECTION_SUBGROUP_005C in block
    assert SCHEDULER_BOUNDARY_CROSSLINK_MODULE in block
    assert THIS_MODULE in block
    assert "CSC_RCHAIN_V1_005C_GOVERNED_REFLECTION_SLICE4_LIVE_NAMED_A_V0=true" in block
    assert "CSC_RCHAIN_V1_005C_PARK_RETAINED=true" in block
    assert "REPO_GO_TOKEN=REPO_GO-CSC-RCHAIN-005C-SLICE-4-LIVE-NAMED-A" in block
    assert "RUN_SCHEDULER_000253_BLOCKED=true" in block
    assert "CSC_RCHAIN_V1_005C_SLICE1_REOPENED=false" in block
    assert "CSC_RCHAIN_V1_005C_SLICE2_REOPENED=false" in block
    assert "CSC_RCHAIN_V1_005C_SLICE3_REOPENED=false" in block
    assert "NO_LIVE_EXECUTION_AUTHORITY=true" in block
    assert "NO_LIVE_READINESS_CLEARANCE_AUTHORITY=true" in block
    assert "NO_LIVE_ARMING_AUTHORITY=true" in block
    assert "LIVE_NAMED_CLI_VISIBILITY_ONLY=true" in block
    for basename in NARROWING_BASENAMES_005C_SLICE4_LIVE_NAMED_A:
        assert basename in block
    assert "000155" in block
    assert "000156" in block
    assert "000157" in block
    assert "000160" in block
    assert "000161" in block
    assert "live-named" in collapsed
    assert "guard/check-tier" in collapsed or "guard" in collapsed
    assert "CSC_PARENT005A_EXCLUDED=true" in block
    assert "**Does not** add" in block
    assert "258" in block
    assert "413" in block
    assert "script execution authorized" not in collapsed
    assert "scheduler start authorized" not in collapsed
    assert "live execution authorized" not in collapsed
    assert "live readiness clearance" not in collapsed
    assert "live arming authorized" not in collapsed
