from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DOC = ROOT / "docs" / "ops" / "planning" / "SECTION5_PREFLIGHT_GAP_OWNER_MAP_CONTRACT_V0.md"
GAP4_SECTION_HEADER = "## Gap 4 Output/Evidence Paths Contract v0"
GAP4_PARALLEL_MARKERS = (
    "GAP4_OUTPUT_EVIDENCE_PATHS_CONTRACT_V0=true",
    "Gap 4 Output/Evidence Paths Contract v0",
)


def _gap4_section(text: str) -> str:
    return text.split(GAP4_SECTION_HEADER, 1)[1].split("## Final Machine Lines", 1)[0]


def test_gap4_output_evidence_paths_contract_is_present_and_non_authorizing():
    section = _gap4_section(DOC.read_text(encoding="utf-8"))

    required = [
        "GAP4_OUTPUT_EVIDENCE_PATHS_CONTRACT_V0=true",
        "GAP4_OUTPUT_EVIDENCE_PATHS_VERIFIED=false",
        "GAP4_OUTPUT_EVIDENCE_DEFAULT_ON=false",
        "GAP4_OUTPUT_EVIDENCE_OPT_IN_ONLY=true",
        "GAP4_DURABLE_OUTPUT_REQUIRED_FOR_FUTURE_RUNS=true",
        "PATH_B_LIFT_DISCUSSION_READY=false",
        "PREFLIGHT_REMAINS_BLOCKED=true",
    ]

    for marker in required:
        assert marker in section


def test_gap4_output_evidence_paths_contract_reuses_existing_surfaces():
    section = _gap4_section(DOC.read_text(encoding="utf-8"))

    required_surfaces = [
        "primary_evidence_retention_v0.py",
        "durable_closeout_copy_verify_v0.py",
        "run_scheduler.py",
    ]

    for surface in required_surfaces:
        assert surface in section


def test_gap4_output_evidence_paths_contract_is_not_default_on_or_lifted():
    section = _gap4_section(DOC.read_text(encoding="utf-8"))
    lines = {line.strip() for line in section.splitlines()}

    forbidden = [
        "READY_FOR_OPERATOR_ARMING=true",
        "PATH_B_LIFT_DISCUSSION_READY=true",
        "GAP4_OUTPUT_EVIDENCE_PATHS_VERIFIED=true",
        "GAP4_OUTPUT_EVIDENCE_DEFAULT_ON=true",
    ]

    for marker in forbidden:
        assert marker not in lines


def test_gap4_output_evidence_paths_contract_has_no_parallel_doc_surface():
    owner_map = DOC.resolve()
    parallel_docs: list[Path] = []

    for path in (ROOT / "docs").rglob("*.md"):
        if path.resolve() == owner_map:
            continue
        text = path.read_text(encoding="utf-8")
        if any(marker in text for marker in GAP4_PARALLEL_MARKERS):
            parallel_docs.append(path.relative_to(ROOT))

    assert parallel_docs == []
