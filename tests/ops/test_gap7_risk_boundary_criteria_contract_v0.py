from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DOC = ROOT / "docs" / "ops" / "planning" / "SECTION5_PREFLIGHT_GAP_OWNER_MAP_CONTRACT_V0.md"
GAP7_SECTION_HEADER = "## Gap 7 Risk Boundary Criteria Contract v0"
GAP7_PARALLEL_MARKERS = (
    "GAP7_RISK_BOUNDARY_CRITERIA_CONTRACT_V0=true",
    "Gap 7 Risk Boundary Criteria Contract v0",
)
HARDENING_OWNER = ROOT / "tests" / "ops" / "test_scheduler_dry_run_hardening_source_contract_v0.py"
HARDENING_MARKER = "SCHEDULER_DRY_RUN_HARDENING_SOURCE_CONTRACT_V0=true"
BOUNDARY_OWNER = ROOT / "tests" / "ops" / "test_scheduler_boundary_hard_block_contract_v0.py"
_MARKER_TRUE = "=true"


def _gap7_section(text: str) -> str:
    return text.split(GAP7_SECTION_HEADER, 1)[1].split("## Final Machine Lines", 1)[0]


def test_gap7_risk_boundary_criteria_contract_is_present_and_non_authorizing():
    section = _gap7_section(DOC.read_text(encoding="utf-8"))

    required = [
        "GAP7_RISK_BOUNDARY_CRITERIA_CONTRACT_V0=true",
        "GAP7_CRITERIA_ONLY=true",
        "GAP7_RISK_BOUNDARY_VERIFIED=false",
        "GAP7_RISK_KILLSWITCH_AUTHORITY_CHANGED=false",
        "GAP7_RISK_KILLSWITCH_RUNTIME_CHANGED=false",
        "GAP7_MASTER_V2_DOUBLE_PLAY_CHANGED=false",
        "GAP7_BULL_BEAR_SCOPE_CAPITAL_CHANGED=false",
        "GAP7_EXECUTION_LIVE_GATES_CHANGED=false",
        "GAP7_SCHEDULER_EXECUTION_AUTHORIZED=false",
        "GAP7_RUNTIME_APPROVED=false",
        "GAP7_RISK_BOUNDARY_DEFAULT_ON=false",
        "PATH_B_LIFT_DISCUSSION_READY=false",
        "PREFLIGHT_REMAINS_BLOCKED=true",
    ]

    for marker in required:
        assert marker in section


def test_gap7_risk_boundary_criteria_contract_is_criteria_only_not_verified_or_changed():
    section = _gap7_section(DOC.read_text(encoding="utf-8"))

    required_language = [
        "docs/tests-only criteria contract",
        "prepares future Risk Boundary / Risk-KillSwitch criteria only",
        "Existing Risk/KillSwitch surfaces are referenced as read-only boundary surfaces only",
        "does not verify or activate Risk Boundaries",
        "does not change Risk/KillSwitch authority",
        "does not change Risk/KillSwitch runtime behavior",
        "does not change Master V2 / Double Play logic",
        "does not change Bull/Bear side-switching or Scope/Capital behavior",
        "does not change execution/live gates",
        "criteria-only",
        "not verified",
        "no authority change",
        "no runtime change",
        "not scheduler-authorized",
        "not runtime-approved",
    ]

    for phrase in required_language:
        assert phrase in section


def test_gap7_risk_boundary_criteria_contract_reuses_existing_surfaces():
    section = _gap7_section(DOC.read_text(encoding="utf-8"))

    required_surfaces = [
        "docs/risk/KILL_SWITCH_RUNBOOK.md",
        "SCHEDULER_BOUNDARY_HARD_BLOCK_CONTRACT_V0.md",
        "MASTER_V2_DECISION_AUTHORITY_MAP_V1.md",
        "snapshot_operator_stop_signals.py",
        "test_scheduler_boundary_hard_block_contract_v0.py",
        "scripts/run_scheduler.py",
        "config/scheduler/jobs.toml",
        "primary_evidence_retention_v0.py",
        "durable_closeout_copy_verify_v0.py",
    ]

    for surface in required_surfaces:
        assert surface in section


def test_gap7_risk_boundary_criteria_contract_references_dependency_chain():
    section = _gap7_section(DOC.read_text(encoding="utf-8"))

    required_chain = [
        "Gap 1 remains the entrypoint boundary",
        "Gap 2 remains the canonical job-set criteria contract",
        "Gap 3 remains the canonical command-text contract",
        "Gap 4 remains the durable output/evidence path contract",
        "Gap 5 remains the stop criteria contract",
        "Gap 6 remains the dry-run proof criteria contract",
    ]

    for link in required_chain:
        assert link in section


def test_gap7_risk_boundary_criteria_contract_is_not_verified_or_lifted():
    section = _gap7_section(DOC.read_text(encoding="utf-8"))
    lines = {line.strip() for line in section.splitlines()}

    forbidden = [
        "READY_FOR_OPERATOR_ARMING=true",
        "PATH_B_LIFT_DISCUSSION_READY=true",
        "GAP7_RISK_BOUNDARY_VERIFIED=true",
        "GAP7_RISK_KILLSWITCH_AUTHORITY_CHANGED=true",
        "GAP7_RISK_KILLSWITCH_RUNTIME_CHANGED=true",
        "GAP7_MASTER_V2_DOUBLE_PLAY_CHANGED=true",
        "GAP7_BULL_BEAR_SCOPE_CAPITAL_CHANGED=true",
        "GAP7_EXECUTION_LIVE_GATES_CHANGED=true",
        "GAP7_SCHEDULER_EXECUTION_AUTHORIZED=true",
        "GAP7_RUNTIME_APPROVED=true",
        "GAP7_RISK_BOUNDARY_DEFAULT_ON=true",
    ]

    for marker in forbidden:
        assert marker not in lines


def test_gap7_risk_boundary_criteria_contract_has_no_parallel_doc_surface():
    owner_map = DOC.resolve()
    parallel_docs: list[Path] = []

    for path in (ROOT / "docs").rglob("*.md"):
        if path.resolve() == owner_map:
            continue
        text = path.read_text(encoding="utf-8")
        if any(marker in text for marker in GAP7_PARALLEL_MARKERS):
            parallel_docs.append(path.relative_to(ROOT))

    assert parallel_docs == []


def test_gap7_owner_crosslinks_scheduler_dry_run_hardening_source_contract_v0():
    assert HARDENING_OWNER.is_file()
    text = HARDENING_OWNER.read_text(encoding="utf-8")
    assert "assert_scheduler_start_authorized" in text
    assert "test_gap7_risk_boundary_criteria_contract_v0.py" in text
    assert HARDENING_MARKER in text
    lines = {line.strip() for line in text.splitlines()}
    assert ("GAP7_RISK_KILLSWITCH_AUTHORITY_CHANGED" + _MARKER_TRUE) not in lines
    assert ("GAP7_MASTER_V2_DOUBLE_PLAY_CHANGED" + _MARKER_TRUE) not in lines
    assert ("GAP7_RISK_BOUNDARY_VERIFIED" + _MARKER_TRUE) not in lines


def test_gap7_owner_crosslinks_scheduler_boundary_hard_block_contract_v0():
    section = _gap7_section(DOC.read_text(encoding="utf-8"))
    assert BOUNDARY_OWNER.is_file()
    assert "test_scheduler_boundary_hard_block_contract_v0.py" in section
    hardening_text = HARDENING_OWNER.read_text(encoding="utf-8")
    assert "test_scheduler_boundary_hard_block_contract_v0.py" in hardening_text
