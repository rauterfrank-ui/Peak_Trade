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
