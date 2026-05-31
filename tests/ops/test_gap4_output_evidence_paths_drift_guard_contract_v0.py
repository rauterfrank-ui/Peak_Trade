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
    "GAP4_OUTPUT_EVIDENCE_PATHS_VERIFIED=false",
    "GAP4_OUTPUT_EVIDENCE_DEFAULT_ON=false",
    "GAP4_OUTPUT_EVIDENCE_OPT_IN_ONLY=true",
    "GAP2A1_PRIMARY_EVIDENCE_ENFORCED=false",
    "GAP5_STOP_PROOF_ACCEPTED=false",
    "GAP6_DRY_RUN_PROOF_ACCEPTED=false",
)

DRIFT_GUARD_FORBIDDEN_GAP4_REPO_TOKENS = (
    "GAP4_OUTPUT_EVIDENCE_PATHS_VERIFIED=true",
    "GAP4_OUTPUT_EVIDENCE_DEFAULT_ON=true",
    "GAP2A1_PRIMARY_EVIDENCE_ENFORCED=true",
    "GAP2A1_ENFORCEMENT_DEFAULT_ON=true",
    "GAP5_STOP_PROOF_ACCEPTED=true",
    "GAP6_DRY_RUN_PROOF_ACCEPTED=true",
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
    return text.split(GAP4_GOVERNED_REFLECTION_HEADER, 1)[1].split(FINAL_MACHINE_LINES_HEADER, 1)[0]


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
    assert "GAP5_STOP_PROOF_ACCEPTED=false" in block
    assert "GAP6_DRY_RUN_PROOF_ACCEPTED=false" in block
    assert "GAP6_DRY_RUN_RC0_OBSERVED=false" in block
    assert "GAP6_DRY_RUN_PROOF_VERIFIED=false" in block


def test_gap4_output_evidence_paths_drift_guard_stop_proof_not_from_inventory_only_v0() -> None:
    block = _final_machine_lines(_section5_text())
    text = _section5_text()
    assert "GAP5_STOP_PROOF_ACCEPTED=false" in block
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
    assert "GAP4_OUTPUT_EVIDENCE_PATHS_VERIFIED=false" in block
    assert "GAP7_RISK_BOUNDARY_VERIFIED=false" in block
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
    assert "GAP4_OUTPUT_EVIDENCE_PATHS_VERIFIED=true" not in block_lines
