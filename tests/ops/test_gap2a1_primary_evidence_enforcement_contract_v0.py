from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DOC = ROOT / "docs" / "ops" / "planning" / "SECTION5_PREFLIGHT_GAP_OWNER_MAP_CONTRACT_V0.md"
PREFLIGHT = ROOT / "docs" / "ops" / "runbooks" / "PAPER_SHADOW_247_PREFLIGHT_CONTRACT_V0.md"
HARD_GATE_TESTS = ROOT / "tests" / "ops" / "test_run_primary_evidence_retention_hard_gate_v0.py"
BOUNDED_REVIEW_TESTS = (
    ROOT
    / "tests"
    / "ops"
    / "test_bounded_observation_review_durable_primary_evidence_contract_v0.py"
)


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


def test_gap2a1_pe3_docs_backed_run_type_applicability_crosslink_v0():
    section5 = DOC.read_text(encoding="utf-8")
    preflight = PREFLIGHT.read_text(encoding="utf-8")
    for token in (
        "PE3_RUN_TYPE_APPLICABILITY_CONTRACT_V0=true",
        "PRIMARY_EVIDENCE_REQUIRED_FOR_RUN_COMPLETION=true",
        "RUN_COMPLETION_INVALID_WITHOUT_DURABLE_PRIMARY_EVIDENCE=true",
    ):
        assert token in section5
        assert token in preflight
    assert "PE2_RUN_TYPE_GUARD_MATRIX" in preflight
    assert "PE3_RUN_TYPE_MATRIX_DOCS_ANCHOR_V0=true" in section5


def test_gap2a1_pe4_bounded_observation_mandatory_closeout_wiring_crosslink_v0():
    section5 = DOC.read_text(encoding="utf-8")
    preflight = PREFLIGHT.read_text(encoding="utf-8")
    bounded = BOUNDED_REVIEW_TESTS.read_text(encoding="utf-8")
    gap2a1 = section5.split("## §2a.1 Primary Evidence Enforcement Contract v0", 1)[1].split(
        "## Gap 1 Execute Entrypoint Contract v0", 1
    )[0]
    section_2a1 = preflight.split("## 2a.1", 1)[1].split("## 2b.", 1)[0]
    for token in (
        "PE4_BOUNDED_OBSERVATION_MANDATORY_CLOSEOUT_WIRING_GUARD_V0=true",
        "MANDATORY_DURABLE_CLOSEOUT_REQUIRED=true",
    ):
        assert token in gap2a1
        assert token in section_2a1
    assert "DURABLE_PRIMARY_EVIDENCE_MANDATORY_CLOSEOUT_WIRING_V0=true" in section_2a1
    assert "PE4_BOUNDED_CLOSEOUT_LANE_MATRIX" in gap2a1 or "bounded_observation_review" in gap2a1
    assert "PE4_BOUNDED_CLOSEOUT_LANE_MATRIX" in bounded
    assert BOUNDED_REVIEW_TESTS.name in gap2a1


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
