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
