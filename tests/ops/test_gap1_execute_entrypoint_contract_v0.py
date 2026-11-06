from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DOC = ROOT / "docs" / "ops" / "planning" / "SECTION5_PREFLIGHT_GAP_OWNER_MAP_CONTRACT_V0.md"
CI_AUDIT_RECIPROCAL_OWNER = ROOT / "docs" / "ops" / "CI_AUDIT_KNOWN_ISSUES.md"
GAP1_SECTION_HEADER = "## Gap 1 Execute Entrypoint Contract v0"
GAP1_RC0_OBSERVED_REFLECTION_HEADER = (
    "## Gap 1 Governed Execute Entrypoint Observed Evidence Reflection v0"
)
GAP1_RC0_OBSERVED_FINAL_LINE_REFLECTION_HEADER = (
    "## Gap 1 Governed Execute Entrypoint RC0 Observed Final-Line Reflection v0"
)
GAP1_VERIFIED_FINAL_LINE_REFLECTION_HEADER = (
    "## Gap 1 Governed Execute Entrypoint Verified Final-Line Reflection v0"
)
GAP4_GOVERNED_REFLECTION_HEADER = "## Gap 4 Governed Output Evidence Acceptance Reflection v0"
FINAL_MACHINE_LINES_HEADER = "## Final Machine Lines"
GAP1_PARALLEL_MARKERS = (
    "GAP1_EXECUTE_ENTRYPOINT_CONTRACT_V0=true",
    "Gap 1 Execute Entrypoint Contract v0",
)
HARDENING_OWNER = ROOT / "tests" / "ops" / "test_scheduler_dry_run_hardening_source_contract_v0.py"
HARDENING_MARKER = "SCHEDULER_DRY_RUN_HARDENING_SOURCE_CONTRACT_V0=true"
_MARKER_TRUE = "=true"


def _gap1_section(text: str) -> str:
    return text.split(GAP1_SECTION_HEADER, 1)[1].split("## Gap 3 Execute Command Contract v0", 1)[0]


def _gap1_rc0_observed_reflection_section(text: str) -> str:
    return text.split(GAP1_RC0_OBSERVED_REFLECTION_HEADER, 1)[1].split(
        GAP4_GOVERNED_REFLECTION_HEADER, 1
    )[0]


def _final_machine_lines(text: str) -> str:
    return text.split(FINAL_MACHINE_LINES_HEADER, 1)[1]


def test_gap1_execute_entrypoint_contract_is_present_and_non_authorizing():
    section = _gap1_section(DOC.read_text(encoding="utf-8"))

    required = [
        "GAP1_EXECUTE_ENTRYPOINT_CONTRACT_V0=true",
        "GAP1_EXECUTE_ENTRYPOINT_VERIFIED=false",
        "GAP1_RUNTIME_APPROVED=false",
        "GAP1_SCHEDULER_EXECUTION_AUTHORIZED=false",
        "GAP1_EXECUTE_ENTRYPOINT_DEFAULT_ON=false",
        "GAP1_ENTRYPOINT_DRY_RUN_ONLY=true",
        "PATH_B_LIFT_DISCUSSION_READY=false",
        "PREFLIGHT_REMAINS_BLOCKED=true",
    ]

    for marker in required:
        assert marker in section


def test_gap1_execute_entrypoint_contract_identifies_bounded_entrypoint():
    section = _gap1_section(DOC.read_text(encoding="utf-8"))
    assert "scripts/run_scheduler.py" in section
    assert "Gap 3 remains the canonical command-text contract" in section


def test_gap1_execute_entrypoint_contract_reuses_existing_surfaces():
    section = _gap1_section(DOC.read_text(encoding="utf-8"))

    required_surfaces = [
        "scripts/run_scheduler.py",
        "config/scheduler/jobs.toml",
        "primary_evidence_retention_v0.py",
        "durable_closeout_copy_verify_v0.py",
    ]

    for surface in required_surfaces:
        assert surface in section


def test_gap1_execute_entrypoint_contract_is_not_runtime_approved_or_lifted():
    section = _gap1_section(DOC.read_text(encoding="utf-8"))
    lines = {line.strip() for line in section.splitlines()}

    forbidden = [
        "READY_FOR_OPERATOR_ARMING=true",
        "PATH_B_LIFT_DISCUSSION_READY=true",
        "GAP1_EXECUTE_ENTRYPOINT_VERIFIED=true",
        "GAP1_RUNTIME_APPROVED=true",
        "GAP1_SCHEDULER_EXECUTION_AUTHORIZED=true",
        "GAP1_EXECUTE_ENTRYPOINT_DEFAULT_ON=true",
    ]

    for marker in forbidden:
        assert marker not in lines


def test_gap1_execute_entrypoint_contract_has_no_parallel_doc_surface():
    owner_map = DOC.resolve()
    ci_audit_owner = CI_AUDIT_RECIPROCAL_OWNER.resolve()
    parallel_docs: list[Path] = []

    for path in (ROOT / "docs").rglob("*.md"):
        resolved = path.resolve()
        if resolved == owner_map or resolved == ci_audit_owner:
            continue
        text = path.read_text(encoding="utf-8")
        if any(marker in text for marker in GAP1_PARALLEL_MARKERS):
            parallel_docs.append(path.relative_to(ROOT))

    assert parallel_docs == []


def test_gap1_owner_crosslinks_scheduler_dry_run_hardening_source_contract_v0():
    assert HARDENING_OWNER.is_file()
    text = HARDENING_OWNER.read_text(encoding="utf-8")
    assert "scripts/run_scheduler.py" in text
    assert "test_gap1_execute_entrypoint_contract_v0.py" in text
    assert HARDENING_MARKER in text
    lines = {line.strip() for line in text.splitlines()}
    assert ("GAP1_EXECUTE_ENTRYPOINT_VERIFIED" + _MARKER_TRUE) not in lines


def test_gap1_execute_entrypoint_contract_owner_crosslinks_drift_guard_v0() -> None:
    drift_guard = ROOT / "tests" / "ops" / "test_gap1_execute_entrypoint_drift_guard_contract_v0.py"
    assert drift_guard.is_file()
    text = drift_guard.read_text(encoding="utf-8")
    assert "test_gap1_execute_entrypoint_contract_v0.py" in text
    assert "GAP1_RUNTIME_APPROVED=false" in text


def test_gap1_rc0_observed_governed_reflection_present_and_non_authorizing_v0() -> None:
    text = DOC.read_text(encoding="utf-8")
    reflection = _gap1_rc0_observed_reflection_section(text)
    block = _final_machine_lines(text)
    block_lines = {line.strip() for line in block.splitlines()}

    assert "GAP1_EXECUTE_ENTRYPOINT_OBSERVED_GOVERNED_REFLECTION_V0=true" in reflection
    assert "GAP1_EXECUTE_ENTRYPOINT_RC0_OBSERVED=true" in reflection
    assert "scripts/run_scheduler.py" in reflection
    assert (
        "gap6_bounded_dry_run_evidence_capture_operator_authorized_v0_20260603T153911Z"
        in reflection
    )
    assert "GAP1_EXECUTE_ENTRYPOINT_VERIFIED=false" in reflection
    assert "PREFLIGHT_REMAINS_BLOCKED=true" in reflection
    assert "GAP1_EXECUTE_ENTRYPOINT_VERIFIED=true" in block
    assert "GAP1_EXECUTE_ENTRYPOINT_RC0_OBSERVED=true" in block_lines
    assert "ALL_GAPS_CLOSED=true" in block
    assert "READY_FOR_OPERATOR_ARMING=true" in block


def _gap1_rc0_observed_final_line_section(text: str) -> str:
    return text.split(GAP1_RC0_OBSERVED_FINAL_LINE_REFLECTION_HEADER, 1)[1].split(
        GAP1_VERIFIED_FINAL_LINE_REFLECTION_HEADER, 1
    )[0]


def _gap1_verified_final_line_section(text: str) -> str:
    return text.split(GAP1_VERIFIED_FINAL_LINE_REFLECTION_HEADER, 1)[1].split(
        "## Tier-1 Governed Zero-Dispatch Manifest Observed Final-Line Reflection v0", 1
    )[0]


def test_gap1_verified_final_line_governed_reflection_v0() -> None:
    text = DOC.read_text(encoding="utf-8")
    section = _gap1_verified_final_line_section(text)
    observed = _gap1_rc0_observed_final_line_section(text)
    criteria = _gap1_section(text)
    block = _final_machine_lines(text)

    assert "GAP1_EXECUTE_ENTRYPOINT_VERIFIED_FINAL_LINE_GOVERNED_REFLECTION_V0=true" in section
    assert "GAP1_VERIFIED_BAR_TIER=T1_PLUS_T2_ENTRYPOINT_BOUNDARY" in section
    assert "T1_STATIC_READONLY_SUFFICIENT_FOR_GAP1_VERIFIED=false" in section
    assert "T2_ENTRYPOINT_DRY_RUN_RC0_SUFFICIENT_FOR_GAP1_VERIFIED=true" in section
    assert "T3_BOUNDED_EXECUTE_REQUIRED_FOR_GAP1_VERIFIED=false" in section
    assert "GAP1_VERIFIED_REQUIRES_RUNTIME_EXECUTE=false" in section
    assert "VERIFIED_NOT_OBSERVED_SEMANTIC_PRESERVED=true" in section
    assert "GAP1_EXECUTE_ENTRYPOINT_RC0_OBSERVED=true" in observed
    assert "does not modify Gap-1 criteria block verification posture" in section
    assert "GAP1_EXECUTE_ENTRYPOINT_VERIFIED=false" in criteria
    assert "GAP1_EXECUTE_ENTRYPOINT_VERIFIED=true" in block
    assert "GAP1_VERIFIED_BAR_TIER=T1_PLUS_T2_ENTRYPOINT_BOUNDARY" in block
    assert "GAP1_EXECUTE_ENTRYPOINT_RC0_OBSERVED=true" in block
    criteria_lines = {line.strip() for line in criteria.splitlines()}
    block_lines = {line.strip() for line in block.splitlines()}
    assert "GAP1_EXECUTE_ENTRYPOINT_VERIFIED=false" in criteria_lines
    assert "GAP1_EXECUTE_ENTRYPOINT_VERIFIED=true" in block_lines
    assert "GAP1_SCHEDULER_EXECUTION_AUTHORIZED=true" not in block_lines
