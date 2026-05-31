from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DOC = ROOT / "docs" / "ops" / "planning" / "SECTION5_PREFLIGHT_GAP_OWNER_MAP_CONTRACT_V0.md"
GAP1_SECTION_HEADER = "## Gap 1 Execute Entrypoint Contract v0"
GAP1_PARALLEL_MARKERS = (
    "GAP1_EXECUTE_ENTRYPOINT_CONTRACT_V0=true",
    "Gap 1 Execute Entrypoint Contract v0",
)
HARDENING_OWNER = ROOT / "tests" / "ops" / "test_scheduler_dry_run_hardening_source_contract_v0.py"
HARDENING_MARKER = "SCHEDULER_DRY_RUN_HARDENING_SOURCE_CONTRACT_V0=true"
_MARKER_TRUE = "=true"


def _gap1_section(text: str) -> str:
    return text.split(GAP1_SECTION_HEADER, 1)[1].split("## Gap 3 Execute Command Contract v0", 1)[0]


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
    parallel_docs: list[Path] = []

    for path in (ROOT / "docs").rglob("*.md"):
        if path.resolve() == owner_map:
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
