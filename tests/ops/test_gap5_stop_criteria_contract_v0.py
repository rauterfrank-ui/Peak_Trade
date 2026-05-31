from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DOC = ROOT / "docs" / "ops" / "planning" / "SECTION5_PREFLIGHT_GAP_OWNER_MAP_CONTRACT_V0.md"
GAP5_SECTION_HEADER = "## Gap 5 Stop Criteria Contract v0"
GAP5_PARALLEL_MARKERS = (
    "GAP5_STOP_CRITERIA_CONTRACT_V0=true",
    "Gap 5 Stop Criteria Contract v0",
)
HARDENING_OWNER = ROOT / "tests" / "ops" / "test_scheduler_dry_run_hardening_source_contract_v0.py"
HARDENING_MARKER = "SCHEDULER_DRY_RUN_HARDENING_SOURCE_CONTRACT_V0=true"
SNAPSHOT_OWNER = ROOT / "tests" / "ops" / "test_snapshot_operator_stop_signals.py"
_MARKER_TRUE = "=true"


def _gap5_section(text: str) -> str:
    return text.split(GAP5_SECTION_HEADER, 1)[1].split("## Final Machine Lines", 1)[0]


def test_gap5_stop_criteria_contract_is_present_and_non_authorizing():
    section = _gap5_section(DOC.read_text(encoding="utf-8"))

    required = [
        "GAP5_STOP_CRITERIA_CONTRACT_V0=true",
        "GAP5_CRITERIA_ONLY=true",
        "GAP5_TYPE2_WAIVER_GRANTED=false",
        "GAP5_STOP_REHEARSAL_EXECUTED=false",
        "GAP5_STOP_PROOF_ACCEPTED=false",
        "GAP5_RUNTIME_STOP_AUTHORITY_CHANGED=false",
        "GAP5_SCHEDULER_EXECUTION_AUTHORIZED=false",
        "GAP5_STOP_CRITERIA_DEFAULT_ON=false",
        "PATH_B_LIFT_DISCUSSION_READY=false",
        "PREFLIGHT_REMAINS_BLOCKED=true",
    ]

    for marker in required:
        assert marker in section


def test_gap5_stop_criteria_contract_is_criteria_only_not_waiver_or_proof_claimed():
    section = _gap5_section(DOC.read_text(encoding="utf-8"))

    required_language = [
        "docs/tests-only criteria contract",
        "prepares future stop / Type-2 / rehearsal readiness criteria only",
        "does not grant a Type-2 waiver",
        "does not execute or claim a stop-tool rehearsal",
        "does not accept or verify stop proof",
        "does not change Risk/KillSwitch or runtime stop authority",
        "criteria-only",
        "not waiver-granted",
        "not rehearsal-executed",
        "not proof-accepted",
        "not runtime-stop-authority-changed",
    ]

    for phrase in required_language:
        assert phrase in section


def test_gap5_stop_criteria_contract_reuses_existing_surfaces():
    section = _gap5_section(DOC.read_text(encoding="utf-8"))

    required_surfaces = [
        "scripts/ops/snapshot_operator_stop_signals.py",
        "scripts/run_scheduler.py",
        "config/scheduler/jobs.toml",
        "primary_evidence_retention_v0.py",
        "durable_closeout_copy_verify_v0.py",
    ]

    for surface in required_surfaces:
        assert surface in section


def test_gap5_stop_criteria_contract_references_dependency_chain():
    section = _gap5_section(DOC.read_text(encoding="utf-8"))

    required_chain = [
        "Gap 1 remains the entrypoint boundary",
        "Gap 3 remains the canonical command-text contract",
        "Gap 4 remains the durable output/evidence path contract",
        "Gap 6 remains the dry-run proof criteria-only contract",
    ]

    for link in required_chain:
        assert link in section


def test_gap5_stop_criteria_contract_is_not_waiver_or_lifted():
    section = _gap5_section(DOC.read_text(encoding="utf-8"))
    lines = {line.strip() for line in section.splitlines()}

    forbidden = [
        "READY_FOR_OPERATOR_ARMING=true",
        "PATH_B_LIFT_DISCUSSION_READY=true",
        "GAP5_TYPE2_WAIVER_GRANTED=true",
        "GAP5_STOP_REHEARSAL_EXECUTED=true",
        "GAP5_STOP_PROOF_ACCEPTED=true",
        "GAP5_RUNTIME_STOP_AUTHORITY_CHANGED=true",
        "GAP5_SCHEDULER_EXECUTION_AUTHORIZED=true",
        "GAP5_STOP_CRITERIA_DEFAULT_ON=true",
    ]

    for marker in forbidden:
        assert marker not in lines


def test_gap5_stop_criteria_contract_has_no_parallel_doc_surface():
    owner_map = DOC.resolve()
    parallel_docs: list[Path] = []

    for path in (ROOT / "docs").rglob("*.md"):
        if path.resolve() == owner_map:
            continue
        text = path.read_text(encoding="utf-8")
        if any(marker in text for marker in GAP5_PARALLEL_MARKERS):
            parallel_docs.append(path.relative_to(ROOT))

    assert parallel_docs == []


def test_gap5_owner_crosslinks_scheduler_dry_run_hardening_source_contract_v0():
    assert HARDENING_OWNER.is_file()
    text = HARDENING_OWNER.read_text(encoding="utf-8")
    assert "if not args.dry_run:" in text
    assert "test_gap5_stop_criteria_contract_v0.py" in text
    assert HARDENING_MARKER in text
    lines = {line.strip() for line in text.splitlines()}
    assert ("GAP5_TYPE2_WAIVER_GRANTED" + _MARKER_TRUE) not in lines
    assert ("GAP5_STOP_REHEARSAL_EXECUTED" + _MARKER_TRUE) not in lines
    assert ("GAP5_RUNTIME_STOP_AUTHORITY_CHANGED" + _MARKER_TRUE) not in lines


def test_gap5_owner_crosslinks_snapshot_operator_stop_signals_v0():
    section = _gap5_section(DOC.read_text(encoding="utf-8"))
    assert SNAPSHOT_OWNER.is_file()
    assert "snapshot_operator_stop_signals.py" in section
    hardening_text = HARDENING_OWNER.read_text(encoding="utf-8")
    assert "test_snapshot_operator_stop_signals.py" in hardening_text
