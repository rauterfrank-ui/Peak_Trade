from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DOC = ROOT / "docs" / "ops" / "planning" / "SECTION5_PREFLIGHT_GAP_OWNER_MAP_CONTRACT_V0.md"


def test_section5_owner_map_contract_exists_and_is_non_authorizing():
    text = DOC.read_text(encoding="utf-8")

    required = [
        "SECTION5_OWNER_MAP_CONTRACT_V0=true",
        "SECTION5_GAP_CLOSURE_EXECUTED=false",
        "ALL_GAPS_CLOSED=false",
        "PATH_B_LIFT_DISCUSSION_READY=false",
        "PREFLIGHT_REMAINS_BLOCKED=true",
        "READY_FOR_OPERATOR_ARMING=false",
        "RUNTIME_APPROVED=false",
        "PREFLIGHT_LIFT_EXECUTED=false",
    ]

    for marker in required:
        assert marker in text


def test_section5_owner_map_contract_covers_all_gap_targets():
    text = DOC.read_text(encoding="utf-8")

    required_gaps = [
        "Execute entrypoint",
        "Canonical job set",
        "Execute command contracts",
        "Output/evidence paths",
        "Risk boundaries",
        "Primary-evidence enforcement",
        "§2a.1 prerequisites",
        "Stop/rehearsal and dry-run proof",
    ]

    for gap in required_gaps:
        assert gap in text


def test_section5_owner_map_contract_reuse_first_and_no_parallel_docs():
    text = DOC.read_text(encoding="utf-8")

    required = [
        "reuse-first",
        "Canonical owner to reuse first",
        "Prefer extending existing canonical owners over adding parallel documents",
        "Do not lift preflight",
        "Do not mark `READY_FOR_OPERATOR_ARMING=true`",
        "Do not approve runtime",
    ]

    for marker in required:
        assert marker in text


def _gap2a1_section(text: str) -> str:
    return text.split("## §2a.1 Primary Evidence Enforcement Contract v0", 1)[1].split(
        "## Gap 1 Execute Entrypoint Contract v0", 1
    )[0]


def test_section5_gap2a1_pe3_run_type_applicability_contract_v0() -> None:
    text = DOC.read_text(encoding="utf-8")
    section = _gap2a1_section(text)
    for token in (
        "PE3_RUN_TYPE_APPLICABILITY_CONTRACT_V0=true",
        "PE3_RUN_TYPE_MATRIX_DOCS_ANCHOR_V0=true",
        "SLICE_PE2_COMPLETE=true",
        "SLICE_PE3_DOCS_TESTS_ONLY=true",
        "PRIMARY_EVIDENCE_REQUIRED_FOR_RUN_COMPLETION=true",
        "RUN_COMPLETION_INVALID_WITHOUT_DURABLE_PRIMARY_EVIDENCE=true",
    ):
        assert token in section
    assert "PE2_RUN_TYPE_GUARD_MATRIX" in section
    assert "test_run_primary_evidence_retention_hard_gate_v0.py" in section
    assert "PAPER_SHADOW_247_PREFLIGHT_CONTRACT_V0.md" in section
    for run_type in ("Paper", "Shadow", "Testnet", "Live/Canary", "Scheduler", "Supervisor"):
        assert run_type in section
    assert "/tmp`-only insufficient" in section or "/tmp`-only is insufficient" in section
    assert "MANIFEST.sha256" in section
    assert "READY_FOR_OPERATOR_ARMING=false" in section
    assert "GAP2A1_PRIMARY_EVIDENCE_ENFORCED=false" in section
    collapsed = section.replace("**", "")
    assert "does not enable default enforcement" in collapsed.lower()


def _gap4_section(text: str) -> str:
    return text.split("## Gap 4 Output/Evidence Paths Contract v0", 1)[1].split(
        "## Gap 6 Dry-Run Proof Criteria Contract v0", 1
    )[0]


def test_section5_gap4_pe5_dependency_guard_v0() -> None:
    text = DOC.read_text(encoding="utf-8")
    gap4 = _gap4_section(text)
    gap2a1 = _gap2a1_section(text)
    for token in (
        "PE5_GAP4_GAP2A1_DEPENDENCY_GUARD_V0=true",
        "GAP4_OUTPUT_EVIDENCE_DEPENDS_ON_GAP2A1_PRIMARY_EVIDENCE_V0=true",
        "GAP4_COMPLETION_INVALID_WITHOUT_DURABLE_PRIMARY_EVIDENCE=true",
        "GAP4_COMPLETION_INVALID_WITHOUT_MANIFEST_VERIFY=true",
        "SLICE_PE5_TESTS_ONLY=true",
    ):
        assert token in gap4
    for token in (
        "PE5_GAP4_GAP2A1_DEPENDENCY_GUARD_V0=true",
        "GAP4_OUTPUT_EVIDENCE_DEPENDS_ON_GAP2A1_PRIMARY_EVIDENCE_V0=true",
    ):
        assert token in gap2a1
    assert "test_gap4_gap2a1_primary_evidence_dependency_contract_v0.py" in gap4
    assert "GAP4_OUTPUT_EVIDENCE_PATHS_VERIFIED=false" in gap4
    assert "READY_FOR_OPERATOR_ARMING=false" in gap4


def test_section5_eer1_readiness_review_index_crosslink_v0() -> None:
    text = DOC.read_text(encoding="utf-8")
    ci_audit = (ROOT / "docs" / "ops" / "CI_AUDIT_KNOWN_ISSUES.md").read_text(encoding="utf-8")
    gap2a1 = _gap2a1_section(text)
    for token in (
        "EVIDENCE_DURABLE_ENFORCEMENT_READINESS_REVIEW_RC_V0_STARTED=true",
        "EER1_READINESS_REVIEW_INDEX_COMPLETE=true",
        "PRIMARY_EVIDENCE_RUN_COMPLETION_CONTRACT_RC_V0_STATUS=CORE_COMPLETE_AFTER_PE6",
        "CYBERSECURITY_DEFENSIVE_VISIBILITY_CV3_PLUS_RC_V0_STATUS=CORE_COMPLETE_AFTER_CV3C",
        "GAP2A1_PRIMARY_EVIDENCE_ENFORCED=false",
        "ENFORCEMENT_ACTIVATED=false",
        "PREFLIGHT_REMAINS_BLOCKED=true",
        "READY_FOR_OPERATOR_ARMING=false",
    ):
        assert token in gap2a1
        assert token in ci_audit
    assert "Evidence Durable Enforcement Readiness Review RC v0" in ci_audit
    assert "Evidence Durable Enforcement Readiness Review index (EER1 guard)" in gap2a1
    assert "planning/docs/tests readiness review only" in gap2a1.lower()
    assert "PAPER_SHADOW_247_PREFLIGHT_CONTRACT_V0.md" in gap2a1
    assert "MANIFEST" in gap2a1 or "manifest" in gap2a1.lower()
    gap2a1_lines = {line.strip() for line in gap2a1.splitlines()}
    assert "GAP2A1_PRIMARY_EVIDENCE_ENFORCED=true" not in gap2a1_lines
    assert "READY_FOR_OPERATOR_ARMING=true" not in gap2a1_lines
