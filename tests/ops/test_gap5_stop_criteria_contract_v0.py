from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DOC = ROOT / "docs" / "ops" / "planning" / "SECTION5_PREFLIGHT_GAP_OWNER_MAP_CONTRACT_V0.md"
CI_AUDIT_RECIPROCAL_OWNER = ROOT / "docs" / "ops" / "CI_AUDIT_KNOWN_ISSUES.md"
GAP5_SECTION_HEADER = "## Gap 5 Stop Criteria Contract v0"
GAP5_GOVERNED_REFLECTION_HEADER = "## Gap 5 Governed Stop Proof Acceptance Reflection v0"
GAP5_ACCEPTED_FINAL_LINE_REFLECTION_HEADER = (
    "## Gap 5 Governed Stop Proof Accepted Final-Line Reflection v0"
)
FINAL_MACHINE_LINES_HEADER = "## Final Machine Lines"
GAP5_PARALLEL_MARKERS = (
    "GAP5_STOP_CRITERIA_CONTRACT_V0=true",
    "Gap 5 Stop Criteria Contract v0",
)
HARDENING_OWNER = ROOT / "tests" / "ops" / "test_scheduler_dry_run_hardening_source_contract_v0.py"
DRIFT_GUARD_OWNER = ROOT / "tests" / "ops" / "test_gap5_stop_criteria_drift_guard_contract_v0.py"
HARDENING_MARKER = "SCHEDULER_DRY_RUN_HARDENING_SOURCE_CONTRACT_V0=true"
SNAPSHOT_OWNER = ROOT / "tests" / "ops" / "test_snapshot_operator_stop_signals.py"
_MARKER_TRUE = "=true"


def _gap5_section(text: str) -> str:
    return text.split(GAP5_SECTION_HEADER, 1)[1].split("## Final Machine Lines", 1)[0]


def _gap5_criteria_section(text: str) -> str:
    return text.split(GAP5_SECTION_HEADER, 1)[1].split("## Gap 2 Canonical Job Set Contract v0", 1)[
        0
    ]


def _gap5_governed_reflection_section(text: str) -> str:
    return text.split(GAP5_GOVERNED_REFLECTION_HEADER, 1)[1].split(
        GAP5_ACCEPTED_FINAL_LINE_REFLECTION_HEADER, 1
    )[0]


def _gap5_accepted_final_line_reflection_section(text: str) -> str:
    return text.split(GAP5_ACCEPTED_FINAL_LINE_REFLECTION_HEADER, 1)[1].split(
        "## Gap 5 Governed Stop Rehearsal Verified Final-Line Reflection v0", 1
    )[0]


def test_gap5_stop_criteria_contract_is_present_and_non_authorizing():
    section = _gap5_criteria_section(DOC.read_text(encoding="utf-8"))

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
    section = _gap5_criteria_section(DOC.read_text(encoding="utf-8"))

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
    section = _gap5_criteria_section(DOC.read_text(encoding="utf-8"))

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
    section = _gap5_criteria_section(DOC.read_text(encoding="utf-8"))

    required_chain = [
        "Gap 1 remains the entrypoint boundary",
        "Gap 3 remains the canonical command-text contract",
        "Gap 4 remains the durable output/evidence path contract",
        "Gap 6 remains the dry-run proof criteria-only contract",
    ]

    for link in required_chain:
        assert link in section


def test_gap5_stop_criteria_contract_is_not_waiver_or_lifted():
    section = _gap5_criteria_section(DOC.read_text(encoding="utf-8"))
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
    ci_audit_owner = CI_AUDIT_RECIPROCAL_OWNER.resolve()
    parallel_docs: list[Path] = []

    for path in (ROOT / "docs").rglob("*.md"):
        resolved = path.resolve()
        if resolved == owner_map or resolved == ci_audit_owner:
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
    section = _gap5_criteria_section(DOC.read_text(encoding="utf-8"))
    assert SNAPSHOT_OWNER.is_file()
    assert "snapshot_operator_stop_signals.py" in section
    hardening_text = HARDENING_OWNER.read_text(encoding="utf-8")
    assert "test_snapshot_operator_stop_signals.py" in hardening_text


def test_gap5_owner_crosslinks_stop_criteria_drift_guard_contract_v0():
    assert DRIFT_GUARD_OWNER.is_file()
    text = DRIFT_GUARD_OWNER.read_text(encoding="utf-8")
    assert "test_gap5_stop_criteria_contract_v0.py" in text
    assert "GAP5_STOP_REHEARSAL_EXECUTED=false" in text
    assert "DRIFT_GUARD_FORBIDDEN_GAP5_REPO_TOKENS" in text


def test_gap5_stop_criteria_contract_governed_reflection_non_authorizing_v0():
    text = DOC.read_text(encoding="utf-8")
    reflection = _gap5_governed_reflection_section(text)
    criteria = _gap5_criteria_section(text)

    assert "GAP5_STOP_PROOF_GOVERNED_REFLECTION_V0=true" in reflection
    assert "GAP5_STOP_PROOF_ACCEPTED=true" in reflection
    assert "GAP5_STOP_REHEARSAL_EXECUTED=false" in reflection
    assert "EXTERNAL_ACCEPTANCE_RECORD_POINTER=" in reflection
    assert "Evidence acceptance is not runtime authorization" in reflection
    assert "does not verify Gap-4 output evidence paths" in reflection
    assert "does not enable operator arming" in reflection
    assert "does not start or authorize Runtime, Paper, Shadow, Testnet, or Live" in reflection
    assert "GAP5_STOP_PROOF_ACCEPTED=false" in criteria
    assert "does not accept or verify stop proof" in criteria
    assert "GAP5_STOP_PROOF_ACCEPTED_EXTERNAL=true" not in text


def test_gap5_stop_proof_accepted_final_line_reflection_non_authorizing_v0():
    text = DOC.read_text(encoding="utf-8")
    reflection = _gap5_accepted_final_line_reflection_section(text)
    criteria = _gap5_criteria_section(text)
    block = text.split(FINAL_MACHINE_LINES_HEADER, 1)[1]

    assert "GAP5_STOP_PROOF_ACCEPTED_FINAL_LINE_GOVERNED_REFLECTION_V0=true" in reflection
    assert "GAP5_STOP_PROOF_ACCEPTED=true" in reflection
    assert "GAP5_STOP_REHEARSAL_EXECUTED=false" in reflection
    assert "NO_RUNTIME_AUTHORITY=true" in reflection
    assert "Evidence acceptance is not runtime authorization" in reflection
    assert "does not lift preflight" in reflection
    assert "does not set `ALL_GAPS_CLOSED=true`" in reflection
    assert "GAP5_STOP_PROOF_ACCEPTED=false" in criteria
    assert "GAP5_STOP_PROOF_ACCEPTED=true" in block
    assert "GAP5_STOP_REHEARSAL_EXECUTED=true" in block
    assert "GAP7_RISK_BOUNDARY_VERIFIED=true" in block
    assert "PREFLIGHT_REMAINS_BLOCKED=false" in block
    assert "ALL_GAPS_CLOSED=true" in block
    assert "READY_FOR_OPERATOR_ARMING=true" in block


def test_gap5_stop_rehearsal_verified_final_line_reflection_non_authorizing_v0():
    text = DOC.read_text(encoding="utf-8")
    reflection = text.split(
        "## Gap 5 Governed Stop Rehearsal Verified Final-Line Reflection v0", 1
    )[1].split("## Gap 6 Governed Dry-Run Proof Acceptance Reflection v0", 1)[0]
    criteria = _gap5_criteria_section(text)
    block = text.split(FINAL_MACHINE_LINES_HEADER, 1)[1]

    assert "GAP5_STOP_REHEARSAL_VERIFIED_FINAL_LINE_GOVERNED_REFLECTION_V0=true" in reflection
    assert "GAP5_STOP_REHEARSAL_EXECUTED=true" in reflection
    assert "EXTERNAL_T2_REHEARSAL_EVIDENCE_POINTER=" in reflection
    assert "gap5_stop_rehearsal_bounded_execute_v0_20260604T215341Z" in reflection
    assert "does not send real process signals" in reflection
    assert "GAP5_STOP_REHEARSAL_EXECUTED=false" in criteria
    assert "GAP5_STOP_REHEARSAL_EXECUTED=true" in block
