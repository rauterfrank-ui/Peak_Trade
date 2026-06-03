from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DOC = ROOT / "docs" / "ops" / "planning" / "SECTION5_PREFLIGHT_GAP_OWNER_MAP_CONTRACT_V0.md"
HARD_GATE_TESTS = ROOT / "tests" / "ops" / "test_run_primary_evidence_retention_hard_gate_v0.py"


def test_gap2a1_primary_evidence_enforcement_contract_is_present_and_non_authorizing():
    text = DOC.read_text(encoding="utf-8")

    required = [
        "GAP2A1_PRIMARY_EVIDENCE_ENFORCEMENT_CONTRACT_V0=true",
        "GAP2A1_PRIMARY_EVIDENCE_ENFORCED=false",
        "GAP2A1_ENFORCEMENT_DEFAULT_ON=false",
        "GAP2A1_ENFORCEMENT_OPT_IN_ONLY=true",
        "PATH_B_LIFT_DISCUSSION_READY=false",
        "PREFLIGHT_REMAINS_BLOCKED=true",
        "READY_FOR_OPERATOR_ARMING=false",
        "RUNTIME_APPROVED=false",
    ]

    for marker in required:
        assert marker in text


def test_gap2a1_primary_evidence_enforcement_contract_reuses_existing_surfaces():
    text = DOC.read_text(encoding="utf-8")

    required_surfaces = [
        "scripts/ops/primary_evidence_retention_v0.py",
        "scripts/ops/durable_closeout_copy_verify_v0.py",
        "scripts/run_scheduler.py",
        "tests/ops/test_run_primary_evidence_retention_hard_gate_v0.py",
    ]

    for surface in required_surfaces:
        assert surface in text


def test_gap2a1_crosslinks_pe2_run_type_primary_evidence_guard_matrix_v0():
    text = HARD_GATE_TESTS.read_text(encoding="utf-8")
    assert "PE2_RUN_TYPE_GUARD_MATRIX" in text
    assert "test_pe2_run_type_primary_evidence_guard_matrix_row_v0" in text
    assert "paper" in text and "supervisor" in text


def test_gap2a1_primary_evidence_enforcement_contract_is_not_default_on():
    text = DOC.read_text(encoding="utf-8")
    section = text.split("## §2a.1 Primary Evidence Enforcement Contract v0", 1)[1].split(
        "## Final Machine Lines", 1
    )[0]

    forbidden = [
        "GAP2A1_PRIMARY_EVIDENCE_ENFORCED=true",
        "GAP2A1_ENFORCEMENT_DEFAULT_ON=true",
    ]

    for marker in forbidden:
        assert marker not in section
