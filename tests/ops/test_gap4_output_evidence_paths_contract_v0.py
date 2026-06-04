from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DOC = ROOT / "docs" / "ops" / "planning" / "SECTION5_PREFLIGHT_GAP_OWNER_MAP_CONTRACT_V0.md"
GAP4_SECTION_HEADER = "## Gap 4 Output/Evidence Paths Contract v0"
GAP4_GOVERNED_REFLECTION_HEADER = "## Gap 4 Governed Output Evidence Acceptance Reflection v0"
GAP4_VERIFIED_FINAL_LINE_REFLECTION_HEADER = (
    "## Gap 4 Governed Output Evidence Paths Verified Final-Line Reflection v0"
)
PREFLIGHT_SYNTHESIS_DOCS_BLOCK_REFLECTION_HEADER = "## Preflight Synthesis Docs Block Reflection v0"
FINAL_MACHINE_LINES_HEADER = "## Final Machine Lines"
GAP4_PARALLEL_MARKERS = (
    "GAP4_OUTPUT_EVIDENCE_PATHS_CONTRACT_V0=true",
    "Gap 4 Output/Evidence Paths Contract v0",
)
HARDENING_OWNER = ROOT / "tests" / "ops" / "test_scheduler_dry_run_hardening_source_contract_v0.py"
DRIFT_GUARD_OWNER = (
    ROOT / "tests" / "ops" / "test_gap4_output_evidence_paths_drift_guard_contract_v0.py"
)
HARDENING_MARKER = "SCHEDULER_DRY_RUN_HARDENING_SOURCE_CONTRACT_V0=true"
HARD_GATE_OWNER = ROOT / "tests" / "ops" / "test_run_primary_evidence_retention_hard_gate_v0.py"
GAP4_GAP2A1_DEPENDENCY_OWNER = (
    ROOT / "tests" / "ops" / "test_gap4_gap2a1_primary_evidence_dependency_contract_v0.py"
)
_MARKER_TRUE = "=true"


def _gap4_criteria_section(text: str) -> str:
    return text.split(GAP4_SECTION_HEADER, 1)[1].split(
        "## Gap 6 Dry-Run Proof Criteria Contract v0", 1
    )[0]


def _gap4_governed_reflection_section(text: str) -> str:
    return text.split(GAP4_GOVERNED_REFLECTION_HEADER, 1)[1].split(
        "## Gap 4 REQ-A Candidate Paper Bounded Retry Acceptance Reflection v0", 1
    )[0]


def _gap4_verified_final_line_reflection_section(text: str) -> str:
    return text.split(GAP4_VERIFIED_FINAL_LINE_REFLECTION_HEADER, 1)[1].split(
        PREFLIGHT_SYNTHESIS_DOCS_BLOCK_REFLECTION_HEADER, 1
    )[0]


def _final_machine_lines(text: str) -> str:
    return text.split(FINAL_MACHINE_LINES_HEADER, 1)[1]


def _gap4_section(text: str) -> str:
    return _gap4_criteria_section(text)


def test_gap4_output_evidence_paths_contract_is_present_and_non_authorizing():
    section = _gap4_section(DOC.read_text(encoding="utf-8"))

    required = [
        "GAP4_OUTPUT_EVIDENCE_PATHS_CONTRACT_V0=true",
        "GAP4_OUTPUT_EVIDENCE_PATHS_VERIFIED=false",
        "GAP4_OUTPUT_EVIDENCE_DEFAULT_ON=false",
        "GAP4_OUTPUT_EVIDENCE_OPT_IN_ONLY=true",
        "GAP4_DURABLE_OUTPUT_REQUIRED_FOR_FUTURE_RUNS=true",
        "PATH_B_LIFT_DISCUSSION_READY=false",
        "PREFLIGHT_REMAINS_BLOCKED=true",
    ]

    for marker in required:
        assert marker in section


def test_gap4_output_evidence_paths_contract_reuses_existing_surfaces():
    section = _gap4_section(DOC.read_text(encoding="utf-8"))

    required_surfaces = [
        "primary_evidence_retention_v0.py",
        "durable_closeout_copy_verify_v0.py",
        "run_scheduler.py",
    ]

    for surface in required_surfaces:
        assert surface in section


def test_gap4_output_evidence_paths_contract_is_not_default_on_or_lifted():
    section = _gap4_section(DOC.read_text(encoding="utf-8"))
    lines = {line.strip() for line in section.splitlines()}

    forbidden = [
        "READY_FOR_OPERATOR_ARMING=true",
        "PATH_B_LIFT_DISCUSSION_READY=true",
        "GAP4_OUTPUT_EVIDENCE_PATHS_VERIFIED=true",
        "GAP4_OUTPUT_EVIDENCE_DEFAULT_ON=true",
    ]

    for marker in forbidden:
        assert marker not in lines


def test_gap4_output_evidence_paths_contract_has_no_parallel_doc_surface():
    owner_map = DOC.resolve()
    parallel_docs: list[Path] = []

    for path in (ROOT / "docs").rglob("*.md"):
        if path.resolve() == owner_map:
            continue
        text = path.read_text(encoding="utf-8")
        if any(marker in text for marker in GAP4_PARALLEL_MARKERS):
            parallel_docs.append(path.relative_to(ROOT))

    assert parallel_docs == []


def test_gap4_owner_crosslinks_scheduler_dry_run_hardening_source_contract_v0():
    assert HARDENING_OWNER.is_file()
    text = HARDENING_OWNER.read_text(encoding="utf-8")
    assert "is_under_tmp" in text
    assert "test_gap4_output_evidence_paths_contract_v0.py" in text
    assert HARDENING_MARKER in text
    lines = {line.strip() for line in text.splitlines()}
    assert ("GAP4_OUTPUT_EVIDENCE_PATHS_VERIFIED" + _MARKER_TRUE) not in lines


def test_gap4_owner_crosslinks_primary_evidence_retention_hard_gate_v0():
    section = _gap4_section(DOC.read_text(encoding="utf-8"))
    assert HARD_GATE_OWNER.is_file()
    assert "test_run_primary_evidence_retention_hard_gate_v0.py" in section
    hardening_text = HARDENING_OWNER.read_text(encoding="utf-8")
    assert "test_run_primary_evidence_retention_hard_gate_v0.py" in hardening_text


def test_gap4_owner_crosslinks_output_evidence_paths_drift_guard_contract_v0():
    assert DRIFT_GUARD_OWNER.is_file()
    text = DRIFT_GUARD_OWNER.read_text(encoding="utf-8")
    assert "test_gap4_output_evidence_paths_contract_v0.py" in text
    assert "GAP4_OUTPUT_EVIDENCE_PATHS_VERIFIED=false" in text
    assert "DRIFT_GUARD_FORBIDDEN_GAP4_REPO_TOKENS" in text


def test_gap4_output_evidence_paths_contract_governed_reflection_non_authorizing_v0():
    text = DOC.read_text(encoding="utf-8")
    reflection = _gap4_governed_reflection_section(text)
    criteria = _gap4_criteria_section(text)
    block = _final_machine_lines(text)

    assert "GAP4_OUTPUT_EVIDENCE_GOVERNED_REFLECTION_V0=true" in reflection
    assert "GAP4_OUTPUT_EVIDENCE_ACCEPTED=true" in reflection
    assert "ACCEPTED_MODE=SCOPED_TIER_A_B_DURABLE_OUTPUT_EVIDENCE" in reflection
    assert "CRITERION4_FULL_SCOPE_REMAINS_PARTIAL=true" in reflection
    assert "EXTERNAL_ACCEPTANCE_RECORD_POINTER=" in reflection
    assert "Evidence acceptance is not runtime authorization" in reflection
    assert (
        "does not verify Gap-4 output evidence paths in criteria or Final Machine Lines"
        in reflection
    )
    assert "does not claim full-scope Gap-4 verification" in reflection
    assert "does not resolve Criterion 4 full-scope partial status" in reflection
    assert "does not verify Gap-7 risk boundaries" in reflection
    assert "does not enforce Gap-2a.1 primary evidence" in reflection
    assert "does not enable operator arming" in reflection
    assert "does not start or authorize Runtime, Paper, Shadow, Testnet, or Live" in reflection
    assert (
        "does not modify existing Gap-4 criteria/final machine-line verification status"
        in reflection
    )
    assert "GAP4_OUTPUT_EVIDENCE_PATHS_VERIFIED=false" in criteria
    assert "contract-only, not verified" in criteria
    assert "GAP4_OUTPUT_EVIDENCE_PATHS_VERIFIED=true" in block
    block_lines = {line.strip() for line in block.splitlines()}
    assert "GAP4_OUTPUT_EVIDENCE_ACCEPTED_EXTERNAL=true" not in text
    assert "FULL_SCOPE_GAP4_VERIFIED=true" in block_lines
    reflection_lines = {line.strip() for line in reflection.splitlines()}
    criteria_lines = {line.strip() for line in criteria.splitlines()}
    assert "GAP4_OUTPUT_EVIDENCE_ACCEPTED=true" in reflection_lines
    assert "GAP4_OUTPUT_EVIDENCE_ACCEPTED=true" not in criteria_lines
    assert "GAP4_OUTPUT_EVIDENCE_ACCEPTED=true" not in block_lines


def test_gap4_output_evidence_paths_verified_final_line_reflection_non_authorizing_v0() -> None:
    text = DOC.read_text(encoding="utf-8")
    reflection = _gap4_verified_final_line_reflection_section(text)
    criteria = _gap4_criteria_section(text)
    block = _final_machine_lines(text)

    assert (
        "GAP4_OUTPUT_EVIDENCE_PATHS_VERIFIED_FINAL_LINE_GOVERNED_REFLECTION_V0=true" in reflection
    )
    assert "GAP4_OUTPUT_EVIDENCE_PATHS_VERIFIED=true" in reflection
    assert "NO_RUNTIME_AUTHORITY=true" in reflection
    assert "FULL_SCOPE_GAP4_VERIFIED=false" in reflection
    assert "does not lift preflight" in reflection
    assert "Evidence verification is not runtime authorization" in reflection
    assert "GAP4_OUTPUT_EVIDENCE_PATHS_VERIFIED=false" in criteria
    assert "GAP4_OUTPUT_EVIDENCE_PATHS_VERIFIED=true" in block
    assert "GAP5_STOP_PROOF_ACCEPTED=true" in block
    assert "GAP7_RISK_BOUNDARY_VERIFIED=true" in block
    assert "ALL_GAPS_CLOSED=false" in block
    assert "READY_FOR_OPERATOR_ARMING=false" in block
    assert "PREFLIGHT_REMAINS_BLOCKED=true" in block
    block_lines = {line.strip() for line in block.splitlines()}
    assert "GAP4_OUTPUT_EVIDENCE_PATHS_VERIFIED=true" in block_lines
    assert "GAP4_OUTPUT_EVIDENCE_PATHS_VERIFIED=false" not in block_lines
    assert "FULL_SCOPE_GAP4_VERIFIED=true" in block_lines


def test_gap4_pe5_output_evidence_depends_on_gap2a1_primary_evidence_v0() -> None:
    section = _gap4_section(DOC.read_text(encoding="utf-8"))
    for token in (
        "PE5_GAP4_GAP2A1_DEPENDENCY_GUARD_V0=true",
        "GAP4_OUTPUT_EVIDENCE_DEPENDS_ON_GAP2A1_PRIMARY_EVIDENCE_V0=true",
        "GAP4_COMPLETION_INVALID_WITHOUT_DURABLE_PRIMARY_EVIDENCE=true",
        "GAP4_COMPLETION_INVALID_WITHOUT_MANIFEST_VERIFY=true",
        "SLICE_PE5_TESTS_ONLY=true",
    ):
        assert token in section
    assert "Gap4 ↔ Gap2a.1 dependency" in section
    assert GAP4_GAP2A1_DEPENDENCY_OWNER.name in section
    assert "GAP2A1_PRIMARY_EVIDENCE_ENFORCED=false" in section
    assert GAP4_GAP2A1_DEPENDENCY_OWNER.is_file()
