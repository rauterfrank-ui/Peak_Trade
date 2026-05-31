from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DOC = ROOT / "docs" / "ops" / "planning" / "SECTION5_PREFLIGHT_GAP_OWNER_MAP_CONTRACT_V0.md"
GAP6_SECTION_HEADER = "## Gap 6 Dry-Run Proof Criteria Contract v0"
GAP6_PARALLEL_MARKERS = (
    "GAP6_DRY_RUN_PROOF_CRITERIA_CONTRACT_V0=true",
    "Gap 6 Dry-Run Proof Criteria Contract v0",
)
HARDENING_OWNER = ROOT / "tests" / "ops" / "test_scheduler_dry_run_hardening_source_contract_v0.py"
HARDENING_MARKER = "SCHEDULER_DRY_RUN_HARDENING_SOURCE_CONTRACT_V0=true"
_MARKER_TRUE = "=true"


def _gap6_section(text: str) -> str:
    return text.split(GAP6_SECTION_HEADER, 1)[1].split("## Final Machine Lines", 1)[0]


def test_gap6_dry_run_proof_criteria_contract_is_present_and_non_authorizing():
    section = _gap6_section(DOC.read_text(encoding="utf-8"))

    required = [
        "GAP6_DRY_RUN_PROOF_CRITERIA_CONTRACT_V0=true",
        "GAP6_CRITERIA_ONLY=true",
        "GAP6_DRY_RUN_PROOF_ACCEPTED=false",
        "GAP6_DRY_RUN_PROOF_VERIFIED=false",
        "GAP6_DRY_RUN_RC0_OBSERVED=false",
        "GAP6_SCHEDULER_EXECUTION_AUTHORIZED=false",
        "GAP6_DRY_RUN_PROOF_DEFAULT_ON=false",
        "PATH_B_LIFT_DISCUSSION_READY=false",
        "PREFLIGHT_REMAINS_BLOCKED=true",
    ]

    for marker in required:
        assert marker in section


def test_gap6_dry_run_proof_criteria_contract_is_criteria_only_not_proof_claimed():
    section = _gap6_section(DOC.read_text(encoding="utf-8"))

    required_language = [
        "docs/tests-only criteria contract",
        "defines future dry-run proof acceptance criteria only",
        "does not claim that a dry-run proof exists",
        "does not claim RC=0 was observed",
        "does not accept or verify any proof",
        "criteria-only",
        "not proof-accepted",
        "not verified",
        "not scheduler-authorized",
    ]

    for phrase in required_language:
        assert phrase in section


def test_gap6_dry_run_proof_criteria_contract_reuses_existing_surfaces():
    section = _gap6_section(DOC.read_text(encoding="utf-8"))

    required_surfaces = [
        "scripts/run_scheduler.py",
        "config/scheduler/jobs.toml",
        "primary_evidence_retention_v0.py",
        "durable_closeout_copy_verify_v0.py",
    ]

    for surface in required_surfaces:
        assert surface in section


def test_gap6_dry_run_proof_criteria_contract_references_dependency_chain():
    section = _gap6_section(DOC.read_text(encoding="utf-8"))

    required_chain = [
        "Gap 1 remains the entrypoint boundary",
        "Gap 3 remains the canonical command-text contract",
        "Gap 4 remains the durable output/evidence path contract",
    ]

    for link in required_chain:
        assert link in section


def test_gap6_dry_run_proof_criteria_contract_is_not_proof_accepted_or_lifted():
    section = _gap6_section(DOC.read_text(encoding="utf-8"))
    lines = {line.strip() for line in section.splitlines()}

    forbidden = [
        "READY_FOR_OPERATOR_ARMING=true",
        "PATH_B_LIFT_DISCUSSION_READY=true",
        "GAP6_DRY_RUN_PROOF_ACCEPTED=true",
        "GAP6_DRY_RUN_PROOF_VERIFIED=true",
        "GAP6_DRY_RUN_RC0_OBSERVED" + _MARKER_TRUE,
        "GAP6_SCHEDULER_EXECUTION_AUTHORIZED=true",
        "GAP6_DRY_RUN_PROOF_DEFAULT_ON=true",
    ]

    for marker in forbidden:
        assert marker not in lines


def test_gap6_dry_run_proof_criteria_contract_has_no_parallel_doc_surface():
    owner_map = DOC.resolve()
    parallel_docs: list[Path] = []

    for path in (ROOT / "docs").rglob("*.md"):
        if path.resolve() == owner_map:
            continue
        text = path.read_text(encoding="utf-8")
        if any(marker in text for marker in GAP6_PARALLEL_MARKERS):
            parallel_docs.append(path.relative_to(ROOT))

    assert parallel_docs == []


def test_gap6_owner_crosslinks_scheduler_dry_run_hardening_source_contract_v0():
    assert HARDENING_OWNER.is_file()
    text = HARDENING_OWNER.read_text(encoding="utf-8")
    assert "scripts/run_scheduler.py" in text
    assert "test_gap6_dry_run_proof_criteria_contract_v0.py" in text
    assert HARDENING_MARKER in text
    lines = {line.strip() for line in text.splitlines()}
    assert ("GAP6_DRY_RUN_RC0_OBSERVED" + _MARKER_TRUE) not in lines
