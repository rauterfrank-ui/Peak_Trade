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


def _gap3_section(text: str) -> str:
    return text.split(GAP3_SECTION_HEADER, 1)[1].split("## Gap 4 Output/Evidence Paths Contract v0", 1)[0]


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
        "GAP3_EXECUTE_COMMAND_VERIFIED=true",
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
