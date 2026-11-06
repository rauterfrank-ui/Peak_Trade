"""Static reciprocal crosslink guard for bounded-pilot readiness preflight bundle."""

from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
READINESS_SCRIPT = ROOT / "scripts" / "ops" / "check_bounded_pilot_readiness.py"
READINESS_TEST = ROOT / "tests" / "ops" / "test_check_bounded_pilot_readiness.py"
LIVE_READINESS_SCRIPT = ROOT / "scripts" / "check_live_readiness.py"
PILOT_EVAL_SCRIPT = ROOT / "scripts" / "ops" / "pilot_go_no_go_eval_v1.py"
PAYLOAD_MAPPING_GUARD_TEST = (
    ROOT
    / "tests"
    / "ops"
    / "test_pilot_gonogo_eval_ops_cockpit_payload_field_mapping_crosslink_v1.py"
)
ENTRY_CONTRACT = ROOT / "docs" / "ops" / "specs" / "BOUNDED_REAL_MONEY_PILOT_ENTRY_CONTRACT.md"
LIVE_ENTRY_RUNBOOK = ROOT / "docs" / "ops" / "runbooks" / "RUNBOOK_BOUNDED_PILOT_LIVE_ENTRY.md"
TRUTH_MAP = ROOT / "docs" / "ops" / "registry" / "DOCS_TRUTH_MAP.md"
DOCS_TRUTH_MAP_YAML = ROOT / "config" / "ops" / "docs_truth_map.yaml"
CI_AUDIT = ROOT / "docs" / "ops" / "CI_AUDIT_KNOWN_ISSUES.md"
TEST_REL = "tests/ops/test_bounded_pilot_readiness_live_readiness_pilot_gonogo_eval_crosslink_v1.py"
READINESS_SCRIPT_REL = "scripts/ops/check_bounded_pilot_readiness.py"
READINESS_TEST_REL = "tests/ops/test_check_bounded_pilot_readiness.py"
LIVE_READINESS_SCRIPT_REL = "scripts/check_live_readiness.py"
PILOT_EVAL_REL = "scripts/ops/pilot_go_no_go_eval_v1.py"
PAYLOAD_MAPPING_GUARD_REL = (
    "tests/ops/test_pilot_gonogo_eval_ops_cockpit_payload_field_mapping_crosslink_v1.py"
)
ENTRY_CONTRACT_REL = "docs/ops/specs/BOUNDED_REAL_MONEY_PILOT_ENTRY_CONTRACT.md"
LIVE_ENTRY_RUNBOOK_REL = "docs/ops/runbooks/RUNBOOK_BOUNDED_PILOT_LIVE_ENTRY.md"
CROSSLINK_PACKAGE_MARKER = "BOUNDED_PILOT_READINESS_LIVE_READINESS_PILOT_GONOGO_EVAL_CI_AUDIT_DOCS_TRUTH_MAP_RECIPROCAL_CROSSLINK_V1=true"


def _docs_truth_map_chronicle_row(truth_map: str, needle: str) -> str:
    row_start = truth_map.index(needle)
    row_end = truth_map.index("\n", row_start)
    return truth_map[row_start:row_end]


def test_crosslink_package_marker_present_v1() -> None:
    assert CROSSLINK_PACKAGE_MARKER in Path(__file__).read_text(encoding="utf-8")


def test_bounded_pilot_readiness_owner_documents_bundle_composition_v1() -> None:
    text = READINESS_SCRIPT.read_text(encoding="utf-8")
    assert READINESS_SCRIPT.is_file()
    assert 'CONTRACT_ID = "bounded_pilot_readiness_v1"' in text
    assert "check_live_readiness.py" in text
    assert "pilot_go_no_go_eval_v1.py" in text
    assert "run_readiness_checks" in text
    assert 'stage="live"' in text
    assert "build_ops_cockpit_payload" in text
    assert "GO_FOR_NEXT_PHASE_ONLY" in text
    assert "Does not invoke a session" in text
    assert "does not authorize live trading" in text
    assert ENTRY_CONTRACT_REL.split("/")[-1].replace(".md", "") in text


def test_entry_contract_and_runbook_reference_bounded_pilot_readiness_v1() -> None:
    contract_text = ENTRY_CONTRACT.read_text(encoding="utf-8")
    runbook_text = LIVE_ENTRY_RUNBOOK.read_text(encoding="utf-8")
    assert ENTRY_CONTRACT.is_file()
    assert LIVE_ENTRY_RUNBOOK.is_file()
    assert "check_bounded_pilot_readiness.py" in contract_text
    assert "read-only" in contract_text.lower()
    assert READINESS_SCRIPT_REL in runbook_text
    assert "pilot_go_no_go_eval_v1" in runbook_text
    assert "GO_FOR_NEXT_PHASE_ONLY" in runbook_text


def test_readiness_tests_cover_fail_closed_bundle_v1() -> None:
    test_text = READINESS_TEST.read_text(encoding="utf-8")
    assert READINESS_TEST.is_file()
    assert "CONTRACT_ID" in test_text
    assert "GO_FOR_NEXT_PHASE_ONLY" in test_text
    assert "live_readiness" in test_text
    assert "go_no_go" in test_text


def test_payload_mapping_guard_referenced_v1() -> None:
    assert PAYLOAD_MAPPING_GUARD_TEST.is_file()
    guard_text = PAYLOAD_MAPPING_GUARD_TEST.read_text(encoding="utf-8")
    assert (
        "PILOT_GONOGO_EVAL_OPS_COCKPIT_PAYLOAD_FIELD_MAPPING_CI_AUDIT_DOCS_TRUTH_MAP_RECIPROCAL_CROSSLINK_V1=true"
        in guard_text
    )


def test_docs_truth_map_chronicle_v1() -> None:
    truth_map = TRUTH_MAP.read_text(encoding="utf-8")
    row = _docs_truth_map_chronicle_row(
        truth_map,
        "Bounded-pilot readiness ↔ live readiness ↔ pilot go/no-go eval CI_AUDIT reciprocal crosslink guard v1",
    )
    for required in (
        READINESS_SCRIPT_REL,
        READINESS_TEST_REL,
        LIVE_READINESS_SCRIPT_REL,
        PILOT_EVAL_REL,
        PAYLOAD_MAPPING_GUARD_REL,
        ENTRY_CONTRACT_REL,
        LIVE_ENTRY_RUNBOOK_REL,
        TEST_REL,
        CROSSLINK_PACKAGE_MARKER,
        "bounded_pilot_readiness_v1",
        "PREFLIGHT_REMAINS_BLOCKED=true",
        "non-authorizing",
        "PILOT_GONOGO_EVAL_PAYLOAD_FIELD_MAPPING_GUARD_REFERENCED=true",
        "NO_LIVE=true",
        "NO_RUNTIME=true",
        "NO_EXECUTE=true",
        "NO_PREFLIGHT_LIFT=true",
    ):
        assert required.lower() in row.lower()


def test_ci_audit_reciprocal_crosslink_v1() -> None:
    ci_audit = CI_AUDIT.read_text(encoding="utf-8")
    section_start = ci_audit.index(
        "## Bounded-pilot readiness ↔ live readiness ↔ pilot go/no-go eval CI_AUDIT reciprocal crosslink — docs/tests-only guard v1"
    )
    section_text = ci_audit[section_start : section_start + 5500]
    for required in (
        CROSSLINK_PACKAGE_MARKER,
        "bounded_pilot_readiness_v1",
        READINESS_SCRIPT_REL,
        READINESS_TEST_REL,
        LIVE_READINESS_SCRIPT_REL,
        PILOT_EVAL_REL,
        PAYLOAD_MAPPING_GUARD_REL,
        ENTRY_CONTRACT_REL,
        LIVE_ENTRY_RUNBOOK_REL,
        TEST_REL,
        "PREFLIGHT_REMAINS_BLOCKED=true",
        "PILOT_GONOGO_EVAL_PAYLOAD_FIELD_MAPPING_GUARD_REFERENCED=true",
        "BOUNDED_PILOT_READINESS_BUNDLE_DOCUMENTED=true",
        "LIVE_READINESS_STAGE_LIVE_BUNDLED=true",
        "PILOT_GO_NO_GO_EVAL_BUNDLED=true",
        "GO_FOR_NEXT_PHASE_ONLY_REQUIRED=true",
        "PILOT_GO_NO_GO_AUTHORITY_CREATED=false",
        "NO_EXECUTE=true",
        "NO_RUNTIME=true",
        "NO_LIVE=true",
        "NO_PREFLIGHT_LIFT=true",
        "non-authorizing",
        "read-only",
    ):
        assert required.lower() in section_text.lower()


def test_canonical_owners_referenced_in_docs_v1() -> None:
    truth_map = TRUTH_MAP.read_text(encoding="utf-8")
    ci_audit = CI_AUDIT.read_text(encoding="utf-8")
    assert DOCS_TRUTH_MAP_YAML.is_file()
    for rel in (
        READINESS_SCRIPT_REL,
        READINESS_TEST_REL,
        LIVE_READINESS_SCRIPT_REL,
        PILOT_EVAL_REL,
        PAYLOAD_MAPPING_GUARD_REL,
        ENTRY_CONTRACT_REL,
        LIVE_ENTRY_RUNBOOK_REL,
        TEST_REL,
    ):
        assert rel in truth_map
        assert rel in ci_audit


def test_guard_module_is_offline_static_only_v1() -> None:
    tree = ast.parse(Path(__file__).read_text(encoding="utf-8"))
    imports = {
        alias.name
        for node in ast.walk(tree)
        if isinstance(node, ast.Import)
        for alias in node.names
    }
    imports.update(
        alias.name.split(".")[0]
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom) and node.module
        for alias in node.names
    )
    forbidden = {"subprocess", "socket", "requests", "httpx", "urllib"}
    assert forbidden.isdisjoint(imports)
