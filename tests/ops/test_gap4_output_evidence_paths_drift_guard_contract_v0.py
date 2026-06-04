"""Static contract for Gap-4 output/evidence paths drift guard v0.

Reads repo markdown/source only. Never executes scheduler/runtime/evidence helpers,
never copies/moves/archives evidence, never reads external archive paths as pass/fail SSOT,
and never treats durable planning or /tmp staging as verified evidence paths.
"""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SECTION5_DOC = (
    ROOT / "docs" / "ops" / "planning" / "SECTION5_PREFLIGHT_GAP_OWNER_MAP_CONTRACT_V0.md"
)
PREFLIGHT_CONTRACT = (
    ROOT / "docs" / "ops" / "runbooks" / "PAPER_SHADOW_247_PREFLIGHT_CONTRACT_V0.md"
)
HARDENING_OWNER = ROOT / "tests" / "ops" / "test_scheduler_dry_run_hardening_source_contract_v0.py"
GAP4_TESTS = ROOT / "tests" / "ops" / "test_gap4_output_evidence_paths_contract_v0.py"
HARD_GATE_TESTS = ROOT / "tests" / "ops" / "test_run_primary_evidence_retention_hard_gate_v0.py"
INVARIANT_TESTS = (
    ROOT / "tests" / "ops" / "test_primary_evidence_retention_invariant_contract_v0.py"
)
FINAL_MACHINE_LINES_HEADER = "## Final Machine Lines"
GAP4_SECTION_HEADER = "## Gap 4 Output/Evidence Paths Contract v0"
GAP4_GOVERNED_REFLECTION_HEADER = "## Gap 4 Governed Output Evidence Acceptance Reflection v0"
GAP4_REQ_A_CANDIDATE_REFLECTION_HEADER = (
    "## Gap 4 REQ-A Candidate Paper Bounded Retry Acceptance Reflection v0"
)
GAP4_REQ_A_STRICT_2A_REFLECTION_HEADER = (
    "## Gap 4 REQ-A Strict §2a Full Artifact Set Acceptance Reflection v0"
)
GAP4_REQ_B_TIER_D_BOUNDARY_REFLECTION_HEADER = "## Gap 4 REQ-B Tier-D Boundary Reflection v0"
GAP4_REQ_B_SHADOW_B07_B08_ADAPTER_PARITY_HEADER = "## Gap 4 REQ-B Shadow B07/B08 Adapter Parity v0"
GAP4_FULL_SCOPE_EVIDENCE_COMPLETENESS_REFLECTION_HEADER = (
    "## Gap 4 Full-Scope Evidence Completeness Reflection v0"
)
GAP4_FULL_SCOPE_GAP4_VERIFIED_REFLECTION_HEADER = "## Gap 4 Full-Scope Gap4 Verified Reflection v0"
GAP4_VERIFIED_FINAL_LINE_REFLECTION_HEADER = (
    "## Gap 4 Governed Output Evidence Paths Verified Final-Line Reflection v0"
)
PREFLIGHT_SYNTHESIS_DOCS_BLOCK_REFLECTION_HEADER = "## Preflight Synthesis Docs Block Reflection v0"
GAP7_GOVERNED_REFLECTION_HEADER = "## Gap 7 Governed Risk Boundary Acceptance Reflection v0"
GAP2A1_SECTION_HEADER = "## §2a.1 Primary Evidence Enforcement Contract v0"
_MARKER_TRUE = "=true"

# External planning posture only — must not appear as verified/enforced in repo SSOT.
GAP4_EVIDENCE_PATHS_PLANNED = True
GAP4_OUTPUT_EVIDENCE_PATHS_VERIFIED = False
TMP_IS_STAGING_NOT_CANONICAL_PROOF = True
EVIDENCE_EQUALS_APPROVAL = False
CRITERIA_COMPLETE_EQUALS_GAP_CLOSED = False

DRIFT_GUARD_REQUIRED_FINAL_LINES = (
    "PREFLIGHT_REMAINS_BLOCKED=true",
    "READY_FOR_OPERATOR_ARMING=false",
    "PATH_B_LIFT_DISCUSSION_READY=false",
    "ALL_GAPS_CLOSED=false",
    "GAP4_OUTPUT_EVIDENCE_PATHS_CONTRACT_V0=true",
    "GAP4_OUTPUT_EVIDENCE_PATHS_VERIFIED=true",
    "GAP4_OUTPUT_EVIDENCE_DEFAULT_ON=false",
    "GAP4_OUTPUT_EVIDENCE_OPT_IN_ONLY=true",
    "GAP2A1_PRIMARY_EVIDENCE_ENFORCED=false",
    "GAP5_STOP_PROOF_ACCEPTED=true",
    "GAP6_DRY_RUN_PROOF_ACCEPTED=true",
)

DRIFT_GUARD_FORBIDDEN_GAP4_REPO_TOKENS = (
    "GAP4_OUTPUT_EVIDENCE_DEFAULT_ON=true",
    "GAP2A1_PRIMARY_EVIDENCE_ENFORCED=true",
    "GAP2A1_ENFORCEMENT_DEFAULT_ON=true",
    "WORKSHEET_COMPLETE=true",
    "PATH_B_LIFT_DISCUSSION_READY=true",
    "ALL_GAPS_CLOSED=true",
    "READY_FOR_OPERATOR_ARMING=true",
    "PREFLIGHT_REMAINS_BLOCKED=false",
)

STATIC_HELPER_SURFACES = (
    "primary_evidence_retention_v0.py",
    "durable_closeout_copy_verify_v0.py",
    "test_run_primary_evidence_retention_hard_gate_v0.py",
)


def _final_machine_lines(text: str) -> str:
    return text.split(FINAL_MACHINE_LINES_HEADER, 1)[1]


def _gap4_criteria_section(text: str) -> str:
    return text.split(GAP4_SECTION_HEADER, 1)[1].split(
        "## Gap 6 Dry-Run Proof Criteria Contract v0", 1
    )[0]


def _gap4_governed_reflection_section(text: str) -> str:
    return text.split(GAP4_GOVERNED_REFLECTION_HEADER, 1)[1].split(
        GAP4_REQ_A_CANDIDATE_REFLECTION_HEADER, 1
    )[0]


def _gap4_req_a_candidate_reflection_section(text: str) -> str:
    return text.split(GAP4_REQ_A_CANDIDATE_REFLECTION_HEADER, 1)[1].split(
        GAP4_REQ_A_STRICT_2A_REFLECTION_HEADER, 1
    )[0]


def _gap4_req_a_strict_2a_reflection_section(text: str) -> str:
    return text.split(GAP4_REQ_A_STRICT_2A_REFLECTION_HEADER, 1)[1].split(
        GAP4_REQ_B_TIER_D_BOUNDARY_REFLECTION_HEADER, 1
    )[0]


def _gap4_req_b_tier_d_boundary_reflection_section(text: str) -> str:
    return text.split(GAP4_REQ_B_TIER_D_BOUNDARY_REFLECTION_HEADER, 1)[1].split(
        GAP4_REQ_B_SHADOW_B07_B08_ADAPTER_PARITY_HEADER, 1
    )[0]


def _gap4_req_b_shadow_b07_b08_adapter_parity_section(text: str) -> str:
    return text.split(GAP4_REQ_B_SHADOW_B07_B08_ADAPTER_PARITY_HEADER, 1)[1].split(
        GAP4_FULL_SCOPE_EVIDENCE_COMPLETENESS_REFLECTION_HEADER, 1
    )[0]


def _gap4_full_scope_evidence_completeness_reflection_section(text: str) -> str:
    return text.split(GAP4_FULL_SCOPE_EVIDENCE_COMPLETENESS_REFLECTION_HEADER, 1)[1].split(
        GAP4_FULL_SCOPE_GAP4_VERIFIED_REFLECTION_HEADER, 1
    )[0]


def _gap4_full_scope_gap4_verified_reflection_section(text: str) -> str:
    return text.split(GAP4_FULL_SCOPE_GAP4_VERIFIED_REFLECTION_HEADER, 1)[1].split(
        GAP7_GOVERNED_REFLECTION_HEADER, 1
    )[0]


def _gap4_verified_final_line_reflection_section(text: str) -> str:
    return text.split(GAP4_VERIFIED_FINAL_LINE_REFLECTION_HEADER, 1)[1].split(
        PREFLIGHT_SYNTHESIS_DOCS_BLOCK_REFLECTION_HEADER, 1
    )[0]


def _gap4_section(text: str) -> str:
    return _gap4_criteria_section(text)


def _gap2a1_section(text: str) -> str:
    return text.split(GAP2A1_SECTION_HEADER, 1)[1].split(
        "## Gap 1 Execute Entrypoint Contract v0", 1
    )[0]


def _section5_text() -> str:
    return SECTION5_DOC.read_text(encoding="utf-8")


def test_gap4_output_evidence_paths_drift_guard_external_planning_constants_v0() -> None:
    assert GAP4_EVIDENCE_PATHS_PLANNED is True
    assert GAP4_OUTPUT_EVIDENCE_PATHS_VERIFIED is False
    assert TMP_IS_STAGING_NOT_CANONICAL_PROOF is True
    assert EVIDENCE_EQUALS_APPROVAL is False
    assert CRITERIA_COMPLETE_EQUALS_GAP_CLOSED is False


def test_gap4_output_evidence_paths_drift_guard_final_machine_lines_remain_blocked_v0() -> None:
    block = _final_machine_lines(_section5_text())
    for marker in DRIFT_GUARD_REQUIRED_FINAL_LINES:
        assert marker in block


def test_gap4_output_evidence_paths_drift_guard_repo_ssot_forbids_external_gap4_acceptance_token_v0() -> (
    None
):
    text = _section5_text()
    assert "GAP4_OUTPUT_EVIDENCE_ACCEPTED_EXTERNAL=true" not in text
    assert "GAP4_OUTPUT_EVIDENCE_PATHS_VERIFIED=false" in text


def test_gap4_output_evidence_paths_drift_guard_forbids_lift_and_verified_tokens_v0() -> None:
    block = _final_machine_lines(_section5_text())
    lines = {line.strip() for line in block.splitlines()}
    for token in DRIFT_GUARD_FORBIDDEN_GAP4_REPO_TOKENS:
        assert token not in lines


def test_gap4_output_evidence_paths_drift_guard_gap4_section_preserves_criteria_only_v0() -> None:
    section = _gap4_criteria_section(_section5_text())
    assert "GAP4_OUTPUT_EVIDENCE_PATHS_CONTRACT_V0=true" in section
    assert "GAP4_OUTPUT_EVIDENCE_PATHS_VERIFIED=false" in section
    assert "GAP4_OUTPUT_EVIDENCE_DEFAULT_ON=false" in section
    assert "GAP4_OUTPUT_EVIDENCE_OPT_IN_ONLY=true" in section
    assert "GAP4_DURABLE_OUTPUT_REQUIRED_FOR_FUTURE_RUNS=true" in section
    assert "contract-only, not verified" in section
    assert "not enforcement-on" in section
    assert "archived outside `/tmp`" in section
    for token in (
        "PE5_GAP4_GAP2A1_DEPENDENCY_GUARD_V0=true",
        "GAP4_OUTPUT_EVIDENCE_DEPENDS_ON_GAP2A1_PRIMARY_EVIDENCE_V0=true",
        "GAP4_COMPLETION_INVALID_WITHOUT_DURABLE_PRIMARY_EVIDENCE=true",
        "GAP4_COMPLETION_INVALID_WITHOUT_MANIFEST_VERIFY=true",
    ):
        assert token in section
    lines = {line.strip() for line in section.splitlines()}
    for token in DRIFT_GUARD_FORBIDDEN_GAP4_REPO_TOKENS:
        assert token not in lines
    assert "GAP4_OUTPUT_EVIDENCE_ACCEPTED=true" not in lines


def test_gap4_output_evidence_paths_drift_guard_gap2a1_remains_not_enforced_v0() -> None:
    section = _gap2a1_section(_section5_text())
    block = _final_machine_lines(_section5_text())
    assert "GAP2A1_PRIMARY_EVIDENCE_ENFORCED=false" in section
    assert "GAP2A1_ENFORCEMENT_DEFAULT_ON=false" in section
    assert "GAP2A1_ENFORCEMENT_OPT_IN_ONLY=true" in section
    assert "opt-in only" in section
    assert "GAP2A1_PRIMARY_EVIDENCE_ENFORCED=false" in block
    assert "GAP2A1_PRIMARY_EVIDENCE_ENFORCED=true" not in section


def test_gap4_output_evidence_paths_drift_guard_preflight_contract_remains_blocked_v0() -> None:
    text = PREFLIGHT_CONTRACT.read_text(encoding="utf-8")
    assert "Current status: **BLOCKED**." in text
    assert "Evidence ≠ approval" in text


def test_gap4_output_evidence_paths_drift_guard_helper_surfaces_are_static_references_v0() -> None:
    section = _gap4_section(_section5_text())
    for surface in STATIC_HELPER_SURFACES:
        assert surface in section
    assert HARD_GATE_TESTS.is_file()
    assert INVARIANT_TESTS.is_file()


def test_gap4_output_evidence_paths_drift_guard_hardening_tmp_boundary_anchors_v0() -> None:
    hardening_text = HARDENING_OWNER.read_text(encoding="utf-8")
    assert "from scripts.ops.primary_evidence_retention_v0 import is_under_tmp" in hardening_text
    assert "is_under_tmp(evidence_dir)" in hardening_text
    assert "is_under_tmp(durable_closeout_dest_dir)" in hardening_text
    gap4_section = _gap4_section(_section5_text())
    assert "archived outside `/tmp`" in gap4_section


def test_gap4_output_evidence_paths_drift_guard_gap5_gap6_tokens_untouched_v0() -> None:
    block = _final_machine_lines(_section5_text())
    assert "GAP5_STOP_PROOF_ACCEPTED=true" in block
    assert "GAP6_DRY_RUN_PROOF_ACCEPTED=true" in block
    assert "GAP6_DRY_RUN_RC0_OBSERVED=true" in block
    assert "GAP6_DRY_RUN_PROOF_VERIFIED=true" in block


def test_gap4_output_evidence_paths_drift_guard_stop_proof_not_from_inventory_only_v0() -> None:
    block = _final_machine_lines(_section5_text())
    text = _section5_text()
    assert "GAP5_STOP_PROOF_ACCEPTED=true" in block
    gap5_section = text.split("## Gap 5 Stop Criteria Contract v0", 1)[1].split(
        "## Gap 2 Canonical Job Set Contract v0", 1
    )[0]
    assert "linked through Gap 4" in gap5_section
    assert "does not accept or verify stop proof" in gap5_section


def test_gap4_output_evidence_paths_drift_guard_criteria_complete_does_not_close_gaps_v0() -> None:
    text = _section5_text()
    assert "SECTION5_OWNER_MAP_CONTRACT_V0_COMPLETE=true" in text
    assert "ALL_GAPS_CLOSED=false" in text
    assert "GAP4_OUTPUT_EVIDENCE_PATHS_VERIFIED=false" in text


def test_gap4_output_evidence_paths_drift_guard_evidence_not_approval_language_v0() -> None:
    section = _gap4_section(_section5_text())
    assert "contract-only" in section
    assert "not verified" in section
    assert "does not authorize runtime" in section
    assert "does not lift preflight" in section


def test_gap4_output_evidence_paths_drift_guard_module_is_static_parse_only_v0() -> None:
    import ast

    tree = ast.parse(Path(__file__).read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert alias.name != "subprocess"
        elif isinstance(node, ast.ImportFrom):
            assert node.module != "subprocess"


def test_gap4_output_evidence_paths_drift_guard_owner_crosslinks_gap4_criteria_tests_v0() -> None:
    assert GAP4_TESTS.is_file()
    text = GAP4_TESTS.read_text(encoding="utf-8")
    assert "test_gap4_output_evidence_paths_drift_guard_contract_v0.py" in text


def test_gap4_output_evidence_paths_drift_guard_owner_crosslinks_hardening_source_contract_v0() -> (
    None
):
    assert HARDENING_OWNER.is_file()
    text = HARDENING_OWNER.read_text(encoding="utf-8")
    assert "test_gap4_output_evidence_paths_drift_guard_contract_v0.py" in text
    lines = {line.strip() for line in text.splitlines()}
    assert ("GAP4_OUTPUT_EVIDENCE_PATHS_VERIFIED" + _MARKER_TRUE) not in lines
    assert ("GAP2A1_PRIMARY_EVIDENCE_ENFORCED" + _MARKER_TRUE) not in lines


def test_gap4_output_evidence_paths_drift_guard_owner_crosslinks_gap5_gap4_dependency_v0() -> None:
    dependency = (
        ROOT / "tests" / "ops" / "test_gap5_gap4_durable_evidence_dependency_contract_v0.py"
    )
    assert dependency.is_file()
    text = dependency.read_text(encoding="utf-8")
    assert "test_gap4_output_evidence_paths_drift_guard_contract_v0.py" in text
    assert "GAP4_OUTPUT_EVIDENCE_PATHS_VERIFIED=false" in text


def test_gap4_output_evidence_paths_drift_guard_owner_crosslinks_gap2a1_drift_guard_v0() -> None:
    drift_guard = (
        ROOT
        / "tests"
        / "ops"
        / "test_gap2a1_primary_evidence_enforcement_drift_guard_contract_v0.py"
    )
    assert drift_guard.is_file()
    text = drift_guard.read_text(encoding="utf-8")
    assert "test_gap4_output_evidence_paths_drift_guard_contract_v0.py" in text
    assert "GAP2A1_PRIMARY_EVIDENCE_ENFORCED=false" in text


def test_gap4_output_evidence_paths_drift_guard_owner_crosslinks_gap4_gap2a1_dependency_v0() -> (
    None
):
    dependency = (
        ROOT / "tests" / "ops" / "test_gap4_gap2a1_primary_evidence_dependency_contract_v0.py"
    )
    assert dependency.is_file()
    text = dependency.read_text(encoding="utf-8")
    assert "test_gap4_output_evidence_paths_drift_guard_contract_v0.py" in text
    assert "GAP4_OUTPUT_EVIDENCE_PATHS_VERIFIED=false" in text


def test_gap4_output_evidence_paths_drift_guard_governed_reflection_scoped_acceptance_v0() -> None:
    text = _section5_text()
    reflection = _gap4_governed_reflection_section(text)
    criteria = _gap4_criteria_section(text)
    block = _final_machine_lines(text)

    assert "GAP4_OUTPUT_EVIDENCE_GOVERNED_REFLECTION_V0=true" in reflection
    assert "GAP4_OUTPUT_EVIDENCE_ACCEPTED=true" in reflection
    assert "ACCEPTED_MODE=SCOPED_TIER_A_B_DURABLE_OUTPUT_EVIDENCE" in reflection
    assert "CRITERION4_FULL_SCOPE_REMAINS_PARTIAL=true" in reflection
    assert "NO_REPO_FLAG_LIFT_FROM_EXTERNAL_ACCEPTANCE=true" in reflection
    assert "EXTERNAL_ACCEPTANCE_RECORD_POINTER=" in reflection
    assert "GAP4_OUTPUT_EVIDENCE_ACCEPTED_EXTERNAL=true" not in text
    block_lines = {line.strip() for line in block.splitlines()}
    assert "FULL_SCOPE_GAP4_VERIFIED=true" not in block_lines
    assert (
        "does not verify Gap-4 output evidence paths in criteria or Final Machine Lines"
        in reflection
    )
    assert "does not claim full-scope Gap-4 verification" in reflection
    assert "does not resolve Criterion 4 full-scope partial status" in reflection
    assert "does not verify Gap-7 risk boundaries" in reflection
    assert "does not enforce Gap-2a.1 primary evidence" in reflection
    assert "does not authorize scheduler execution" in reflection
    assert "does not enable operator arming" in reflection
    assert "does not open Path-B lift discussion" in reflection
    assert "does not start or authorize Runtime, Paper, Shadow, Testnet, or Live" in reflection
    assert (
        "does not modify existing Gap-4 criteria/final machine-line verification status"
        in reflection
    )
    assert "Evidence acceptance is not runtime authorization" in reflection
    assert "GAP4_OUTPUT_EVIDENCE_PATHS_VERIFIED=false" in criteria
    assert "contract-only, not verified" in criteria
    assert "GAP4_OUTPUT_EVIDENCE_PATHS_VERIFIED=true" in block
    assert "GAP7_RISK_BOUNDARY_VERIFIED=true" in block
    assert "GAP2A1_PRIMARY_EVIDENCE_ENFORCED=false" in block
    assert "GAP1_SCHEDULER_EXECUTION_AUTHORIZED=false" in block
    assert "GAP3_SCHEDULER_EXECUTION_AUTHORIZED=false" in block
    assert "READY_FOR_OPERATOR_ARMING=false" in block
    assert "PATH_B_LIFT_DISCUSSION_READY=false" in block
    assert "PREFLIGHT_REMAINS_BLOCKED=true" in block
    reflection_lines = {line.strip() for line in reflection.splitlines()}
    criteria_lines = {line.strip() for line in criteria.splitlines()}
    assert "GAP4_OUTPUT_EVIDENCE_ACCEPTED=true" in reflection_lines
    assert "GAP4_OUTPUT_EVIDENCE_ACCEPTED=true" not in criteria_lines
    assert "GAP4_OUTPUT_EVIDENCE_ACCEPTED=true" not in block_lines
    assert "GAP4_OUTPUT_EVIDENCE_PATHS_VERIFIED=true" in block_lines


def test_gap4_req_a_candidate_acceptance_reflection_drift_guard_scoped_v0() -> None:
    text = _section5_text()
    candidate = _gap4_req_a_candidate_reflection_section(text)
    criteria = _gap4_criteria_section(text)
    block = _final_machine_lines(text)

    assert "GAP4_REQ_A_CANDIDATE_ACCEPTANCE_REFLECTION_V0=true" in candidate
    assert "ACCEPTED_MODE=GAP4_REQ_A_CANDIDATE_PAPER_BOUNDED_300S_RETRY_EVIDENCE" in candidate
    assert "EXTERNAL_RETRY_ROOT_POINTER=" in candidate
    assert "gap4_req_a_paper_lane_retry_evidence_20260531T223848Z" in candidate
    assert "EXTERNAL_REINVENTORY_POINTER=" in candidate
    assert "gap4_req_a_post_retry_reinventory_v0_20260531T224542Z" in candidate
    assert "REQ_A_CANDIDATE_CLOSURE_READY=true" in candidate
    assert "REQ_A_CANDIDATE_REVIEW_ACCOUNT_FILLS_PRODUCED=true" in candidate
    assert "REVIEW_PASS_FOUND=true" in candidate
    assert "ACCOUNT_ARTIFACT_PRESENT=true" in candidate
    assert "FILLS_ARTIFACT_PRESENT=true" in candidate
    assert "FILLS_COUNT=0" in candidate
    assert "TARGET_MANIFEST_VERIFY_RC=0" in candidate
    assert "REQ_A_FULL_2A_ARTIFACT_SET_FOUND=false" in candidate
    assert "REQ_B_TIER_D_POPULATED_PATHS_FOUND=false" in candidate
    assert "REQ_C_CROSS_LANE_EVIDENCE_FOUND=false" in candidate
    assert "GAP4_FULL_SCOPE_EVIDENCE_COMPLETE=false" in candidate
    assert "GAP4_OUTPUT_EVIDENCE_PATHS_VERIFIED=false" in candidate
    assert "FULL_SCOPE_GAP4_VERIFIED=false" in candidate
    assert "NO_REPO_FLAG_LIFT_FROM_EXTERNAL_ACCEPTANCE=true" in candidate
    assert "PREFLIGHT_REMAINS_BLOCKED=true" in candidate
    assert "PATH_B_LIFT_DISCUSSION_READY=false" in candidate
    assert "GLOBAL_PREFLIGHT_LIFTED=false" in candidate
    assert "DOUBLE_PLAY_LOGIC_TOUCHED=false" in candidate
    assert "TRADING_LOGIC_TOUCHED=false" in candidate
    assert "not a PnL, fill-rate, or trading-performance claim" in candidate
    assert "does not set `REQ_A_FULL_2A_ARTIFACT_SET_FOUND=true`" in candidate
    assert "does not set `GAP4_OUTPUT_EVIDENCE_PATHS_VERIFIED=true`" in candidate
    assert "does not authorize scheduler execution or a further Paper-Lane retry" in candidate
    assert "Evidence acceptance is not runtime authorization" in candidate

    candidate_lines = {line.strip() for line in candidate.splitlines()}
    assert "REQ_A_FULL_2A_ARTIFACT_SET_FOUND=true" not in candidate_lines
    assert "GAP4_OUTPUT_EVIDENCE_PATHS_VERIFIED=true" not in candidate_lines
    assert "FULL_SCOPE_GAP4_VERIFIED=true" not in candidate_lines
    assert "REQ_A_CANDIDATE_CLOSURE_READY=true" in candidate_lines
    assert "REQ_A_CANDIDATE_CLOSURE_READY=true" not in {
        line.strip() for line in criteria.splitlines()
    }
    assert "REQ_A_CANDIDATE_CLOSURE_READY=true" not in {line.strip() for line in block.splitlines()}
    assert "GAP4_OUTPUT_EVIDENCE_PATHS_VERIFIED=false" in criteria
    assert "GAP4_OUTPUT_EVIDENCE_PATHS_VERIFIED=true" in block


def test_gap4_req_a_strict_2a_acceptance_reflection_drift_guard_scoped_v0() -> None:
    text = _section5_text()
    strict_2a = _gap4_req_a_strict_2a_reflection_section(text)
    candidate = _gap4_req_a_candidate_reflection_section(text)
    criteria = _gap4_criteria_section(text)
    block = _final_machine_lines(text)

    assert "GAP4_REQ_A_STRICT_2A_ACCEPTANCE_REFLECTION_V0=true" in strict_2a
    assert "ACCEPTED_MODE=GAP4_REQ_A_DERIVED_STRICT_2A_FULL_2A_ARTIFACT_SET" in strict_2a
    assert "EXTERNAL_DERIVED_STRICT_2A_ROOT_POINTER=" in strict_2a
    assert (
        "gap4_req_a_paper_lane_retry_evidence_20260531T223848Z_derived_strict_2a_layout_20260531T225744Z"
        in strict_2a
    )
    assert "EXTERNAL_SOURCE_RETRY_ROOT_POINTER=" in strict_2a
    assert "gap4_req_a_paper_lane_retry_evidence_20260531T223848Z" in strict_2a
    assert "EXTERNAL_REINVENTORY_POINTER=" in strict_2a
    assert "gap4_req_a_post_derived_strict_2a_reinventory_v0_20260531T225914Z" in strict_2a
    assert "GOVERNED_ACCEPTANCE_CHARTER_POINTER=" in strict_2a
    assert "gap4_req_a_strict_2a_acceptance_reflection_charter_v0_20260531T230038Z" in strict_2a
    assert "REQ_A_FULL_2A_ARTIFACT_SET_FOUND=true" in strict_2a
    assert "REQ_A_FULL_2A_SCOPE=derived_strict_2a_root_only" in strict_2a
    assert "REQ_A_CANDIDATE_CLOSURE_READY=true" in strict_2a
    assert "REQ_A_CANDIDATE_REVIEW_ACCOUNT_FILLS_PRODUCED=true" in strict_2a
    assert "REVIEW_PASS_FOUND=true" in strict_2a
    assert "ACCOUNT_ARTIFACT_PRESENT=true" in strict_2a
    assert "FILLS_ARTIFACT_PRESENT=true" in strict_2a
    assert "FILLS_COUNT=0" in strict_2a
    assert "A01_ARCHIVE_ROOT_STATUS=PRESENT_VALID" in strict_2a
    assert "A05_CONFIG_STATUS=PRESENT_VALID" in strict_2a
    assert "A06_PREFLIGHT_STATUS=PRESENT_NOT_AVAILABLE_WITH_EXPLANATION" in strict_2a
    assert "TARGET_DERIVED_MANIFEST_VERIFY_RC=0" in strict_2a
    assert "REQ_B_TIER_D_POPULATED_PATHS_FOUND=false" in strict_2a
    assert "REQ_C_CROSS_LANE_EVIDENCE_FOUND=false" in strict_2a
    assert "GAP4_FULL_SCOPE_EVIDENCE_COMPLETE=false" in strict_2a
    assert "GAP4_OUTPUT_EVIDENCE_PATHS_VERIFIED=false" in strict_2a
    assert "FULL_SCOPE_GAP4_VERIFIED=false" in strict_2a
    assert "NO_REPO_FLAG_LIFT_FROM_EXTERNAL_ACCEPTANCE=true" in strict_2a
    assert "PREFLIGHT_REMAINS_BLOCKED=true" in strict_2a
    assert "PATH_B_LIFT_DISCUSSION_READY=false" in strict_2a
    assert "GLOBAL_PREFLIGHT_LIFTED=false" in strict_2a
    assert "DOUBLE_PLAY_LOGIC_TOUCHED=false" in strict_2a
    assert "TRADING_LOGIC_TOUCHED=false" in strict_2a
    assert "not a PnL, fill-rate, or trading-performance claim" in strict_2a
    assert "not** a global or scoped preflight lift" in strict_2a
    assert "derived strict §2a root only" in strict_2a
    assert "does not set `GAP4_OUTPUT_EVIDENCE_PATHS_VERIFIED=true`" in strict_2a
    assert "does not authorize scheduler execution" in strict_2a
    assert "Evidence acceptance is not runtime authorization" in strict_2a

    strict_2a_lines = {line.strip() for line in strict_2a.splitlines()}
    candidate_lines = {line.strip() for line in candidate.splitlines()}
    criteria_lines = {line.strip() for line in criteria.splitlines()}
    block_lines = {line.strip() for line in block.splitlines()}

    assert "REQ_A_FULL_2A_ARTIFACT_SET_FOUND=true" in strict_2a_lines
    assert "REQ_A_FULL_2A_ARTIFACT_SET_FOUND=false" in candidate_lines
    assert "REQ_A_FULL_2A_ARTIFACT_SET_FOUND=true" not in candidate_lines
    assert "REQ_A_FULL_2A_ARTIFACT_SET_FOUND=true" not in criteria_lines
    assert "REQ_A_FULL_2A_ARTIFACT_SET_FOUND=true" not in block_lines
    assert "GAP4_OUTPUT_EVIDENCE_PATHS_VERIFIED=true" not in strict_2a_lines
    assert "FULL_SCOPE_GAP4_VERIFIED=true" not in strict_2a_lines
    assert "GLOBAL_PREFLIGHT_LIFTED=true" not in strict_2a_lines
    assert "PATH_B_LIFT_DISCUSSION_READY=true" not in strict_2a_lines
    assert "GAP4_OUTPUT_EVIDENCE_PATHS_VERIFIED=false" in criteria
    assert "GAP4_OUTPUT_EVIDENCE_PATHS_VERIFIED=true" in block


def test_gap4_req_b_shadow_b07_b08_adapter_parity_drift_guard_scoped_v0() -> None:
    text = _section5_text()
    parity = _gap4_req_b_shadow_b07_b08_adapter_parity_section(text)
    req_b = _gap4_req_b_tier_d_boundary_reflection_section(text)
    adapter_text = (
        ROOT / "scripts" / "ops" / "run_shadow_bounded_observation_adapter_v0.py"
    ).read_text(encoding="utf-8")

    assert "GAP4_REQ_B_SHADOW_B07_B08_ADAPTER_PARITY_V0=true" in parity
    assert "B07_B08_ADAPTER_PARITY_IMPLEMENTED=true" in parity
    assert "COMMAND_TRANSCRIPT.log" in parity
    assert "PROCESS_INVENTORY_BEFORE.txt" in parity
    assert "PROCESS_INVENTORY_AFTER.txt" in parity
    assert "SHADOW_B07_B08_MISSING=true" in parity
    assert "SHADOW_B09_B16_ARCHIVE_METADATA_CLOSED=true" in parity
    assert "REQ_B_TIER_D_POPULATED_PATHS_FOUND=false" in parity
    assert "PREFLIGHT_REMAINS_BLOCKED=true" in parity
    assert "PATH_B_LIFT_DISCUSSION_READY=false" in parity
    assert "GAP4_OUTPUT_EVIDENCE_PATHS_VERIFIED=false" in parity
    assert "FULL_SCOPE_GAP4_VERIFIED=false" in parity
    assert "does not set `SHADOW_B07_B08_MISSING=false`" in parity
    assert "does not set `REQ_B_TIER_D_POPULATED_PATHS_FOUND=true`" in parity
    assert "Evidence acceptance is not runtime authorization" in parity

    parity_lines = {line.strip() for line in parity.splitlines()}
    assert "SHADOW_B07_B08_MISSING=true" in parity_lines
    assert "SHADOW_B07_B08_MISSING=false" not in parity_lines
    assert "REQ_B_TIER_D_POPULATED_PATHS_FOUND=true" not in parity_lines
    assert "SHADOW_B07_B08_MISSING=true" in req_b

    assert "COMMAND_TRANSCRIPT_FILENAME" in adapter_text
    assert "_write_command_transcript" in adapter_text
    assert "_write_process_inventory_snapshot" in adapter_text


def test_gap4_req_b_tier_d_boundary_reflection_drift_guard_scoped_v0() -> None:
    text = _section5_text()
    req_b = _gap4_req_b_tier_d_boundary_reflection_section(text)
    strict_2a = _gap4_req_a_strict_2a_reflection_section(text)
    criteria = _gap4_criteria_section(text)
    block = _final_machine_lines(text)

    assert "GAP4_REQ_B_TIER_D_BOUNDARY_REFLECTION_V0=true" in req_b
    assert "ACCEPTED_MODE=GAP4_REQ_B_TIER_D_FAST_SIM_SHADOW_BOUNDARY_REFLECTION" in req_b
    assert "TIER_D_RUN_ID=gap4_req_b_tier_d_paper_candidate_20260531T230911Z" in req_b
    assert "EXTERNAL_FAST_SIM_BOUNDARY_CHARTER_POINTER=" in req_b
    assert "gap4_req_b_shadow_fast_sim_boundary_charter_v0_20260531T233134Z" in req_b
    assert "EXTERNAL_POST_TIER_D_REINVENTORY_POINTER=" in req_b
    assert "gap4_req_b_post_tier_d_populated_paths_reinventory_v0_20260531T232726Z" in req_b
    assert "REQ_A_FULL_2A_ARTIFACT_SET_FOUND=true" in req_b
    assert "REQ_B_TIER_D_PAPER_PATH_CANDIDATE_READY=true" in req_b
    assert "REQ_B_TIER_D_SHADOW_PATH_FOUND=true" in req_b
    assert "REQ_B_TIER_D_POPULATED_PATHS_FOUND=false" in req_b
    assert "SHADOW_FAST_SIM_ONLY=true" in req_b
    assert "SHADOW_REAL_10MIN_OBSERVATION=false" in req_b
    assert "SHADOW_EVIDENCE_TIMING_VERDICT=VALID_FAST_SIM_DRY_RUN" in req_b
    assert "PLANNED_PROFILE_LABEL_10_MIN=true" in req_b
    assert "PLANNED_STEPS=120" in req_b
    assert "PLANNED_INTERVAL_SECONDS=0" in req_b
    assert "ACTUAL_WALL_CLOCK_SECONDS=0" in req_b
    assert "REVIEW_VALIDATES_WALL_CLOCK_DURATION=false" in req_b
    assert "SHADOW_B07_B08_MISSING=true" in req_b
    assert "SHADOW_B09_B16_PARTIAL=true" in req_b
    assert "TIER_D_SHADOW_PATH_MANIFEST_VERIFY_RC=0" in req_b
    assert "SHADOW_REVIEW_PASS=true" in req_b
    assert "REQ_C_CROSS_LANE_EVIDENCE_FOUND=false" in req_b
    assert "GAP4_FULL_SCOPE_EVIDENCE_COMPLETE=false" in req_b
    assert "GAP4_OUTPUT_EVIDENCE_PATHS_VERIFIED=false" in req_b
    assert "FULL_SCOPE_GAP4_VERIFIED=false" in req_b
    assert "PREFLIGHT_REMAINS_BLOCKED=true" in req_b
    assert "PATH_B_LIFT_DISCUSSION_READY=false" in req_b
    assert "GLOBAL_PREFLIGHT_LIFTED=false" in req_b
    assert "DOUBLE_PLAY_LOGIC_TOUCHED=false" in req_b
    assert "TRADING_LOGIC_TOUCHED=false" in req_b
    assert "profile/deadline cap labels" in req_b
    assert "fast local simulation" in req_b
    assert "does not claim `SHADOW_REAL_10MIN_OBSERVATION=true`" in req_b
    assert "does not set `REQ_B_TIER_D_POPULATED_PATHS_FOUND=true`" in req_b
    assert "120 Fast-Sim steps emitted" in req_b
    assert "Evidence acceptance is not runtime authorization" in req_b

    req_b_lines = {line.strip() for line in req_b.splitlines()}
    strict_2a_lines = {line.strip() for line in strict_2a.splitlines()}
    criteria_lines = {line.strip() for line in criteria.splitlines()}
    block_lines = {line.strip() for line in block.splitlines()}

    assert "REQ_B_TIER_D_SHADOW_PATH_FOUND=true" in req_b_lines
    assert "REQ_B_TIER_D_POPULATED_PATHS_FOUND=false" in req_b_lines
    assert "SHADOW_REAL_10MIN_OBSERVATION=true" not in req_b_lines
    assert "REQ_B_TIER_D_POPULATED_PATHS_FOUND=true" not in req_b_lines
    assert "FULL_SCOPE_GAP4_VERIFIED=true" not in req_b_lines
    assert "GAP4_OUTPUT_EVIDENCE_PATHS_VERIFIED=true" not in req_b_lines
    assert "REQ_B_TIER_D_SHADOW_PATH_FOUND=true" not in strict_2a_lines
    assert "REQ_B_TIER_D_SHADOW_PATH_FOUND=true" not in criteria_lines
    assert "REQ_B_TIER_D_SHADOW_PATH_FOUND=true" not in block_lines
    assert "GAP4_OUTPUT_EVIDENCE_PATHS_VERIFIED=false" in criteria
    assert "GAP4_OUTPUT_EVIDENCE_PATHS_VERIFIED=true" in block


def test_gap4_full_scope_evidence_completeness_reflection_drift_guard_scoped_v0() -> None:
    text = _section5_text()
    full_scope = _gap4_full_scope_evidence_completeness_reflection_section(text)
    parity = _gap4_req_b_shadow_b07_b08_adapter_parity_section(text)
    criteria = _gap4_criteria_section(text)
    block = _final_machine_lines(text)

    assert "GAP4_FULL_SCOPE_EVIDENCE_COMPLETENESS_REFLECTION_V0=true" in full_scope
    assert "ACCEPTED_MODE=GAP4_FULL_SCOPE_EVIDENCE_EXTERNAL_COMPLETENESS_REFLECTION" in full_scope
    assert "EXTERNAL_COMPLETENESS_VERIFICATION_POINTER=" in full_scope
    assert "gap4_full_scope_evidence_completeness_verification_v0_20260601T010600Z" in full_scope
    assert "EXTERNAL_OUTPUT_EVIDENCE_PATHS_VERIFICATION_POINTER=" in full_scope
    assert "gap4_output_evidence_paths_verification_v0_20260601T010200Z" in full_scope
    assert "REQ_A_FULL_2A_ARTIFACT_SET_FOUND=true" in full_scope
    assert "REQ_A_TO_DERIVED_PAPER_LINKAGE_CONFIRMED=true" in full_scope
    assert "REQ_B_TIER_D_POPULATED_PATHS_FOUND=true" in full_scope
    assert "REQ_C_CROSS_LANE_EVIDENCE_FOUND=true" in full_scope
    assert "GAP4_OUTPUT_EVIDENCE_PATHS_VERIFIED=true" in full_scope
    assert "GAP4_FULL_SCOPE_EVIDENCE_COMPLETE=true" in full_scope
    assert "SHADOW_REAL_10MIN_OBSERVATION=false" in full_scope
    assert "TEN_MINUTE_RUN_STARTED=false" in full_scope
    assert "FULL_SCOPE_GAP4_VERIFIED=false" in full_scope
    assert "PREFLIGHT_REMAINS_BLOCKED=true" in full_scope
    assert "PATH_B_LIFT_DISCUSSION_READY=false" in full_scope
    assert "GLOBAL_PREFLIGHT_LIFTED=false" in full_scope
    assert "DOUBLE_PLAY_LOGIC_TOUCHED=false" in full_scope
    assert "TRADING_LOGIC_TOUCHED=false" in full_scope
    assert "does not set `FULL_SCOPE_GAP4_VERIFIED=true`" in full_scope
    assert "does not verify Gap-4 output evidence paths in criteria or Final Machine Lines" in (
        full_scope
    )
    assert "Evidence acceptance is not runtime authorization" in full_scope

    full_scope_lines = {line.strip() for line in full_scope.splitlines()}
    parity_lines = {line.strip() for line in parity.splitlines()}
    criteria_lines = {line.strip() for line in criteria.splitlines()}
    block_lines = {line.strip() for line in block.splitlines()}

    assert "GAP4_FULL_SCOPE_EVIDENCE_COMPLETE=true" in full_scope_lines
    assert "GAP4_OUTPUT_EVIDENCE_PATHS_VERIFIED=true" in full_scope_lines
    assert "REQ_B_TIER_D_POPULATED_PATHS_FOUND=true" in full_scope_lines
    assert "REQ_C_CROSS_LANE_EVIDENCE_FOUND=true" in full_scope_lines
    assert "FULL_SCOPE_GAP4_VERIFIED=true" not in full_scope_lines
    assert "GLOBAL_PREFLIGHT_LIFTED=true" not in full_scope_lines
    assert "PATH_B_LIFT_DISCUSSION_READY=true" not in full_scope_lines
    assert "SHADOW_REAL_10MIN_OBSERVATION=true" not in full_scope_lines
    assert "GAP4_FULL_SCOPE_EVIDENCE_COMPLETE=true" not in parity_lines
    assert "GAP4_FULL_SCOPE_EVIDENCE_COMPLETE=true" not in criteria_lines
    assert "GAP4_FULL_SCOPE_EVIDENCE_COMPLETE=true" not in block_lines
    assert "GAP4_OUTPUT_EVIDENCE_PATHS_VERIFIED=true" not in criteria_lines
    assert "GAP4_OUTPUT_EVIDENCE_PATHS_VERIFIED=true" in block_lines
    assert "GAP4_OUTPUT_EVIDENCE_PATHS_VERIFIED=false" in criteria
    assert "GAP4_OUTPUT_EVIDENCE_PATHS_VERIFIED=true" in block


def test_gap4_full_scope_gap4_verified_reflection_drift_guard_scoped_v0() -> None:
    text = _section5_text()
    verified = _gap4_full_scope_gap4_verified_reflection_section(text)
    completeness = _gap4_full_scope_evidence_completeness_reflection_section(text)
    criteria = _gap4_criteria_section(text)
    block = _final_machine_lines(text)

    assert "GAP4_FULL_SCOPE_GAP4_VERIFIED_REFLECTION_V0=true" in verified
    assert "ACCEPTED_MODE=GAP4_FULL_SCOPE_GAP4_VERIFIED_EXTERNAL_READ_ONLY_REFLECTION" in verified
    assert "EXTERNAL_VERIFIED_READ_ONLY_VERIFICATION_POINTER=" in verified
    assert "full_scope_gap4_verified_read_only_verification_v0_20260601T011200Z" in verified
    assert "EXTERNAL_VERIFIED_CHARTER_POINTER=" in verified
    assert "full_scope_gap4_verified_charter_v0_20260601T011000Z" in verified
    assert "CHARTER_VERIFIED=true" in verified
    assert "PR3845_CLOSEOUT_VERIFIED=true" in verified
    assert "GAP4_COMPLETENESS_BUNDLE_VERIFIED=true" in verified
    assert "REPO_CANONICAL_OWNER_REUSE_VERIFIED=true" in verified
    assert "REUSE_DRIFT_GUARD_VERIFIED=true" in verified
    assert "VERIFICATION_MANIFEST_VERIFY_RC=0" in verified
    assert "GAP4_FULL_SCOPE_EVIDENCE_COMPLETE=true" in verified
    assert "FULL_SCOPE_GAP4_VERIFIED=true" in verified
    assert "PREFLIGHT_REMAINS_BLOCKED=true" in verified
    assert "PATH_B_LIFT_DISCUSSION_READY=false" in verified
    assert "GLOBAL_PREFLIGHT_LIFTED=false" in verified
    assert "READY_FOR_OPERATOR_ARMING=false" in verified
    assert "RUNTIME_APPROVED=false" in verified
    assert "does not lift global preflight" in verified
    assert "does not enable operator arming" in verified
    assert "Evidence acceptance is not runtime authorization" in verified

    verified_lines = {line.strip() for line in verified.splitlines()}
    completeness_lines = {line.strip() for line in completeness.splitlines()}
    criteria_lines = {line.strip() for line in criteria.splitlines()}
    block_lines = {line.strip() for line in block.splitlines()}

    assert "FULL_SCOPE_GAP4_VERIFIED=true" in verified_lines
    assert "FULL_SCOPE_GAP4_VERIFIED=true" not in completeness_lines
    assert "FULL_SCOPE_GAP4_VERIFIED=true" not in criteria_lines
    assert "FULL_SCOPE_GAP4_VERIFIED=true" not in block_lines
    assert "FULL_SCOPE_GAP4_VERIFIED=false" in completeness_lines
    assert "PREFLIGHT_REMAINS_BLOCKED=true" in verified_lines
    assert "GLOBAL_PREFLIGHT_LIFTED=true" not in verified_lines
    assert "PATH_B_LIFT_DISCUSSION_READY=true" not in verified_lines
    assert "READY_FOR_OPERATOR_ARMING=true" not in verified_lines
    assert "PREFLIGHT_REMAINS_BLOCKED=true" in block
    assert "GAP4_OUTPUT_EVIDENCE_PATHS_VERIFIED=false" in criteria
    assert "GAP4_OUTPUT_EVIDENCE_PATHS_VERIFIED=true" in block


def test_gap4_verified_final_line_governed_reflection_scoped_verification_v0() -> None:
    text = _section5_text()
    reflection = _gap4_verified_final_line_reflection_section(text)
    acceptance = _gap4_governed_reflection_section(text)
    completeness = _gap4_full_scope_evidence_completeness_reflection_section(text)
    criteria = _gap4_criteria_section(text)
    block = _final_machine_lines(text)

    assert (
        "GAP4_OUTPUT_EVIDENCE_PATHS_VERIFIED_FINAL_LINE_GOVERNED_REFLECTION_V0=true" in reflection
    )
    assert "GAP4_OUTPUT_EVIDENCE_PATHS_VERIFIED=true" in reflection
    assert (
        "ACCEPTED_MODE=GAP4_OUTPUT_EVIDENCE_PATHS_SCOPED_EXTERNAL_VERIFICATION_FINAL_LINE_VERIFIED"
        in reflection
    )
    assert "GOVERNED_ACCEPTANCE_BASIS=GAP4_OUTPUT_EVIDENCE_ACCEPTED=true" in reflection
    assert "EXTERNAL_OUTPUT_EVIDENCE_PATHS_VERIFICATION_POINTER=" in reflection
    assert "gap4_output_evidence_paths_verification_v0_20260601T010200Z" in reflection
    assert "EXTERNAL_COMPLETENESS_VERIFICATION_POINTER=" in reflection
    assert "gap4_full_scope_evidence_completeness_verification_v0_20260601T010600Z" in reflection
    assert "INPUT_STRATEGY_POINTER=" in reflection
    assert "section5_remaining_gaps_closure_strategy_no_lift_v0_20260603T160500Z" in reflection
    assert "INPUT_GAP7_CLOSEOUT_POINTER=" in reflection
    assert (
        "pr3966_gap7_risk_boundary_final_line_reflection_post_merge_closeout_v0_20260603T161613Z"
        in reflection
    )
    assert "INPUT_GAP5_CLOSEOUT_POINTER=" in reflection
    assert (
        "pr3967_gap5_stop_proof_final_line_reflection_post_merge_closeout_v0_20260603T162700Z"
        in reflection
    )
    assert (
        "OPERATOR_GO=GO_GAP4_OUTPUT_EVIDENCE_PATHS_VERIFIED_FINAL_LINE_REPO_REFLECTION_DOCS_TESTS_V0"
        in reflection
    )
    assert "NO_RUNTIME_AUTHORITY=true" in reflection
    assert "FULL_SCOPE_GAP4_VERIFIED=false" in reflection
    assert "does not modify Gap-4 criteria block verification posture" in reflection
    assert "does not set `FULL_SCOPE_GAP4_VERIFIED=true`" in reflection
    assert "does not enable operator arming" in reflection
    assert "does not set `ALL_GAPS_CLOSED=true`" in reflection
    assert "does not lift preflight" in reflection
    assert "Evidence verification is not runtime authorization" in reflection
    assert "GAP4_OUTPUT_EVIDENCE_ACCEPTED=true" in acceptance
    assert "GAP4_OUTPUT_EVIDENCE_PATHS_VERIFIED=true" in completeness
    assert "GAP4_OUTPUT_EVIDENCE_PATHS_VERIFIED=false" in criteria
    assert "GAP4_OUTPUT_EVIDENCE_PATHS_VERIFIED=true" in block
    assert "GAP5_STOP_PROOF_ACCEPTED=true" in block
    assert "GAP7_RISK_BOUNDARY_VERIFIED=true" in block
    assert "ALL_GAPS_CLOSED=false" in block
    assert "READY_FOR_OPERATOR_ARMING=false" in block
    assert "PREFLIGHT_REMAINS_BLOCKED=true" in block
    reflection_lines = {line.strip() for line in reflection.splitlines()}
    criteria_lines = {line.strip() for line in criteria.splitlines()}
    block_lines = {line.strip() for line in block.splitlines()}
    assert "GAP4_OUTPUT_EVIDENCE_PATHS_VERIFIED=true" in reflection_lines
    assert "GAP4_OUTPUT_EVIDENCE_PATHS_VERIFIED=true" in block_lines
    assert "GAP4_OUTPUT_EVIDENCE_PATHS_VERIFIED=true" not in criteria_lines
    assert "GAP4_OUTPUT_EVIDENCE_PATHS_VERIFIED=false" not in block_lines
    assert "FULL_SCOPE_GAP4_VERIFIED=true" not in block_lines
