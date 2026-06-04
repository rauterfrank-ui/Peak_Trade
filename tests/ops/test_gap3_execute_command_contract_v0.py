from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DOC = ROOT / "docs" / "ops" / "planning" / "SECTION5_PREFLIGHT_GAP_OWNER_MAP_CONTRACT_V0.md"
GAP3_SECTION_HEADER = "## Gap 3 Execute Command Contract v0"
CANONICAL_COMMAND = (
    "uv run python scripts/run_scheduler.py --config config/scheduler/jobs.toml "
    "--dry-run --once --verbose"
)
GAP3_PARALLEL_MARKERS = (
    "GAP3_EXECUTE_COMMAND_CONTRACT_V0=true",
    "Gap 3 Execute Command Contract v0",
)
HARDENING_OWNER = ROOT / "tests" / "ops" / "test_scheduler_dry_run_hardening_source_contract_v0.py"
HARDENING_MARKER = "SCHEDULER_DRY_RUN_HARDENING_SOURCE_CONTRACT_V0=true"
_MARKER_TRUE = "=true"


def _gap3_section(text: str) -> str:
    return text.split(GAP3_SECTION_HEADER, 1)[1].split(
        "## Gap 4 Output/Evidence Paths Contract v0", 1
    )[0]


def test_gap3_execute_command_contract_is_present_and_non_authorizing():
    section = _gap3_section(DOC.read_text(encoding="utf-8"))

    required = [
        "GAP3_EXECUTE_COMMAND_CONTRACT_V0=true",
        "GAP3_EXECUTE_COMMAND_VERIFIED=false",
        "GAP3_SCHEDULER_EXECUTION_AUTHORIZED=false",
        "GAP3_EXECUTE_COMMAND_DEFAULT_ON=false",
        "GAP3_EXECUTE_COMMAND_DRY_RUN_ONLY=true",
        "PATH_B_LIFT_DISCUSSION_READY=false",
        "PREFLIGHT_REMAINS_BLOCKED=true",
    ]

    for marker in required:
        assert marker in section


def test_gap3_execute_command_contract_contains_canonical_bounded_command():
    section = _gap3_section(DOC.read_text(encoding="utf-8"))
    assert CANONICAL_COMMAND in section


def test_gap3_execute_command_contract_reuses_existing_surfaces():
    section = _gap3_section(DOC.read_text(encoding="utf-8"))

    required_surfaces = [
        "scripts/run_scheduler.py",
        "config/scheduler/jobs.toml",
        "primary_evidence_retention_v0.py",
        "durable_closeout_copy_verify_v0.py",
    ]

    for surface in required_surfaces:
        assert surface in section


def test_gap3_execute_command_contract_is_not_execution_authorized_or_lifted():
    section = _gap3_section(DOC.read_text(encoding="utf-8"))
    lines = {line.strip() for line in section.splitlines()}

    forbidden = [
        "READY_FOR_OPERATOR_ARMING=true",
        "PATH_B_LIFT_DISCUSSION_READY=true",
        "GAP3_EXECUTE_COMMAND_VERIFIED" + _MARKER_TRUE,
        "GAP3_SCHEDULER_EXECUTION_AUTHORIZED=true",
        "GAP3_EXECUTE_COMMAND_DEFAULT_ON=true",
    ]

    for marker in forbidden:
        assert marker not in lines


def test_gap3_execute_command_contract_has_no_parallel_doc_surface():
    owner_map = DOC.resolve()
    parallel_docs: list[Path] = []

    for path in (ROOT / "docs").rglob("*.md"):
        if path.resolve() == owner_map:
            continue
        text = path.read_text(encoding="utf-8")
        if any(marker in text for marker in GAP3_PARALLEL_MARKERS):
            parallel_docs.append(path.relative_to(ROOT))

    assert parallel_docs == []


def test_gap3_owner_crosslinks_scheduler_dry_run_hardening_source_contract_v0():
    assert HARDENING_OWNER.is_file()
    text = HARDENING_OWNER.read_text(encoding="utf-8")
    assert "scripts/run_scheduler.py" in text
    assert "test_gap3_execute_command_contract_v0.py" in text
    assert HARDENING_MARKER in text
    lines = {line.strip() for line in text.splitlines()}
    assert ("GAP3_EXECUTE_COMMAND_VERIFIED" + _MARKER_TRUE) not in lines


def test_gap3_owner_crosslinks_gap2_gap3_command_dependency_contract_v0():
    dependency_guard = ROOT / "tests" / "ops" / "test_gap2_gap3_command_dependency_contract_v0.py"
    assert dependency_guard.is_file()
    text = dependency_guard.read_text(encoding="utf-8")
    assert "CANONICAL_BOUNDED_DRY_RUN_COMMAND" in text
    assert "GAP3_EXECUTE_COMMAND_VERIFIED=false" in text
    assert "GAP2_CANONICAL_JOB_SET_VERIFIED=false" in text
    assert "test_gap3_execute_command_contract_v0.py" in text


FINAL_MACHINE_LINES_HEADER = "## Final Machine Lines"
GAP3_DRY_RUN_RC0_OBSERVED_FINAL_LINE_HEADER = (
    "## Gap 3 Governed Tier-2 Command Dry-Run RC0 Observed Final-Line Reflection v0"
)
GAP3_VERIFIED_FINAL_LINE_HEADER = (
    "## Gap 3 Governed Execute Command Verified Final-Line Reflection v0"
)
GAP3_ACCEPTED_FINAL_LINE_HEADER = (
    "## Gap 3 Governed Tier-2 Command Accepted Scoped-Criteria Final-Line Reflection v0"
)
CANONICAL_BOUNDED_DRY_RUN_COMMAND_TIER2 = (
    "uv run python scripts/run_scheduler.py --config config/scheduler/jobs.toml "
    "--dry-run --once --verbose --include-tags paper_shadow_247,preflight,readonly"
)


def _final_machine_lines(text: str) -> str:
    return text.split(FINAL_MACHINE_LINES_HEADER, 1)[1]


def _gap3_dry_run_rc0_observed_final_line_section(text: str) -> str:
    return text.split(GAP3_DRY_RUN_RC0_OBSERVED_FINAL_LINE_HEADER, 1)[1].split(
        GAP3_VERIFIED_FINAL_LINE_HEADER, 1
    )[0]


def _gap3_verified_final_line_section(text: str) -> str:
    return text.split(GAP3_VERIFIED_FINAL_LINE_HEADER, 1)[1].split(
        "## Gap 5 Governed Stop Proof Acceptance Reflection v0", 1
    )[0]


def test_gap3_dry_run_rc0_observed_final_line_governed_reflection_v0() -> None:
    text = DOC.read_text(encoding="utf-8")
    section = _gap3_dry_run_rc0_observed_final_line_section(text)
    criteria = _gap3_section(text)
    block = _final_machine_lines(text)

    assert (
        "GAP3_EXECUTE_COMMAND_DRY_RUN_RC0_OBSERVED_FINAL_LINE_GOVERNED_REFLECTION_V0=true"
        in section
    )
    assert "GAP3_EXECUTE_COMMAND_DRY_RUN_RC0_OBSERVED=true" in section
    assert "OBSERVED_NOT_VERIFIED_SEMANTIC_PRESERVED=true" in section
    assert "--no-registry --no-alerts" in section
    assert "does not set `GAP3_EXECUTE_COMMAND_VERIFIED=true`" in section
    assert "GAP3_EXECUTE_COMMAND_VERIFIED=false" in criteria
    assert "GAP3_EXECUTE_COMMAND_DRY_RUN_RC0_OBSERVED=true" in block
    assert "GAP3_ACCEPTED_SCOPED_CRITERIA=true" in block
    criteria_lines = {line.strip() for line in criteria.splitlines()}
    block_lines = {line.strip() for line in block.splitlines()}
    assert "GAP3_EXECUTE_COMMAND_DRY_RUN_RC0_OBSERVED=true" not in criteria_lines
    assert "GAP3_EXECUTE_COMMAND_DRY_RUN_RC0_OBSERVED=true" in block_lines
    assert "GAP3_EXECUTE_COMMAND_VERIFIED=false" in criteria_lines
    assert "GAP3_EXECUTE_COMMAND_VERIFIED=true" in block_lines


def test_gap3_verified_final_line_governed_reflection_v0() -> None:
    text = DOC.read_text(encoding="utf-8")
    section = _gap3_verified_final_line_section(text)
    observed = _gap3_dry_run_rc0_observed_final_line_section(text)
    criteria = _gap3_section(text)
    block = _final_machine_lines(text)

    assert "GAP3_EXECUTE_COMMAND_VERIFIED_FINAL_LINE_GOVERNED_REFLECTION_V0=true" in section
    assert "GAP3_VERIFIED_BAR_TIER=T1_PLUS_T2_COMMAND_BOUNDARY" in section
    assert "T1_STATIC_READONLY_SUFFICIENT_FOR_GAP3_VERIFIED=false" in section
    assert "T2_DRY_RUN_COMMAND_RC0_SUFFICIENT_FOR_GAP3_VERIFIED=true" in section
    assert "T3_BOUNDED_EXECUTE_REQUIRED_FOR_GAP3_VERIFIED=false" in section
    assert "GAP3_VERIFIED_REQUIRES_RUNTIME_EXECUTE=false" in section
    assert "VERIFIED_NOT_OBSERVED_SEMANTIC_PRESERVED=true" in section
    assert "GAP3_EXECUTE_COMMAND_DRY_RUN_RC0_OBSERVED=true" in observed
    assert "does not modify Gap-3 criteria block verification posture" in section
    assert "GAP3_EXECUTE_COMMAND_VERIFIED=false" in criteria
    assert "GAP3_EXECUTE_COMMAND_VERIFIED=true" in block
    assert "GAP3_VERIFIED_BAR_TIER=T1_PLUS_T2_COMMAND_BOUNDARY" in block
    assert "GAP3_EXECUTE_COMMAND_DRY_RUN_RC0_OBSERVED=true" in block
    assert "GAP3_ACCEPTED_SCOPED_CRITERIA=true" in block
    criteria_lines = {line.strip() for line in criteria.splitlines()}
    block_lines = {line.strip() for line in block.splitlines()}
    assert "GAP3_EXECUTE_COMMAND_VERIFIED=false" in criteria_lines
    assert "GAP3_EXECUTE_COMMAND_VERIFIED=true" in block_lines
    assert "GAP3_SCHEDULER_EXECUTION_AUTHORIZED=true" not in block_lines
