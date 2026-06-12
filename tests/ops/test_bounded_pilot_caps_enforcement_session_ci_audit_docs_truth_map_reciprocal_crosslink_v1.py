"""Static reciprocal crosslink guard for bounded-pilot caps enforcement ↔ session entry."""

from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CAPS_SPEC = ROOT / "docs" / "ops" / "specs" / "BOUNDED_PILOT_CAPS_ENFORCEMENT_POINT.md"
SESSION_SCRIPT = ROOT / "scripts" / "ops" / "run_bounded_pilot_session.py"
SESSION_TEST = ROOT / "tests" / "ops" / "test_run_bounded_pilot_session.py"
CHECKLIST = ROOT / "docs" / "ops" / "specs" / "PILOT_GO_NO_GO_CHECKLIST.md"
ENTRY_CONTRACT = ROOT / "docs/ops/specs/BOUNDED_REAL_MONEY_PILOT_ENTRY_CONTRACT.md"
LIVE_ENTRY_RUNBOOK = ROOT / "docs" / "ops" / "runbooks" / "RUNBOOK_BOUNDED_PILOT_LIVE_ENTRY.md"
ENTRY_GATE_GUARD_TEST = (
    ROOT
    / "tests"
    / "ops"
    / "test_run_bounded_pilot_session_operator_preflight_packet_runner_handoff_crosslink_v1.py"
)
REMOTE_DOCS_GUARD = ROOT / "tests" / "ops" / "test_remote_runtime_contract_docs_guard_v0.py"
TRUTH_MAP = ROOT / "docs" / "ops" / "registry" / "DOCS_TRUTH_MAP.md"
CI_AUDIT = ROOT / "docs" / "ops" / "CI_AUDIT_KNOWN_ISSUES.md"
TEST_REL = "tests/ops/test_bounded_pilot_caps_enforcement_session_ci_audit_docs_truth_map_reciprocal_crosslink_v1.py"
CAPS_SPEC_REL = "docs/ops/specs/BOUNDED_PILOT_CAPS_ENFORCEMENT_POINT.md"
SESSION_SCRIPT_REL = "scripts/ops/run_bounded_pilot_session.py"
SESSION_TEST_REL = "tests/ops/test_run_bounded_pilot_session.py"
CHECKLIST_REL = "docs/ops/specs/PILOT_GO_NO_GO_CHECKLIST.md"
ENTRY_CONTRACT_REL = "docs/ops/specs/BOUNDED_REAL_MONEY_PILOT_ENTRY_CONTRACT.md"
LIVE_ENTRY_RUNBOOK_REL = "docs/ops/runbooks/RUNBOOK_BOUNDED_PILOT_LIVE_ENTRY.md"
ENTRY_GATE_GUARD_REL = "tests/ops/test_run_bounded_pilot_session_operator_preflight_packet_runner_handoff_crosslink_v1.py"
REMOTE_DOCS_GUARD_REL = "tests/ops/test_remote_runtime_contract_docs_guard_v0.py"
CROSSLINK_PACKAGE_MARKER = (
    "BOUNDED_PILOT_CAPS_ENFORCEMENT_SESSION_CI_AUDIT_DOCS_TRUTH_MAP_RECIPROCAL_CROSSLINK_V1=true"
)


def _read(path: Path) -> str:
    assert path.is_file(), f"missing canonical surface: {path}"
    return path.read_text(encoding="utf-8")


def _plain(path: Path) -> str:
    return _read(path).replace("&#47;", "/")


def _docs_truth_map_chronicle_row(truth_map: str, needle: str) -> str:
    row_start = truth_map.index(needle)
    row_end = truth_map.index("\n", row_start)
    return truth_map[row_start:row_end]


def test_crosslink_package_marker_present_v1() -> None:
    assert CROSSLINK_PACKAGE_MARKER in _read(Path(__file__))


def test_caps_owner_documents_visibility_vs_enforcement_v1() -> None:
    text = _plain(CAPS_SPEC)
    assert "Ops Cockpit is **visibility**" in text
    assert "config is **declaration**" in text
    assert "execution path is **enforcement**" in text
    assert SESSION_SCRIPT_REL in text
    assert "pipeline.py" in text
    assert "live_session.py" in text
    assert "does **not** introduce new runtime logic" in text


def test_session_runner_referenced_as_entry_path_not_caps_owner_v1() -> None:
    text = _plain(SESSION_SCRIPT)
    assert 'contract": "run_bounded_pilot_session"' in text
    assert "--no-invoke" in text
    assert "fail-closed before handoff" in text


def test_checklist_references_pilot_caps_v1() -> None:
    checklist = _read(CHECKLIST)
    assert "Pilot Caps" in checklist
    assert "bounded caps" in checklist.lower()


def test_entry_gate_guard_referenced_v1() -> None:
    guard_text = _read(ENTRY_GATE_GUARD_TEST)
    assert (
        "RUN_BOUNDED_PILOT_SESSION_OPERATOR_PREFLIGHT_PACKET_RUNNER_HANDOFF_CI_AUDIT_DOCS_TRUTH_MAP_RECIPROCAL_CROSSLINK_V1=true"
        in guard_text
    )


def test_docs_truth_map_chronicle_v1() -> None:
    truth_map = _read(TRUTH_MAP)
    row = _docs_truth_map_chronicle_row(
        truth_map,
        "Bounded-pilot caps enforcement point ↔ run_bounded_pilot_session CI_AUDIT reciprocal crosslink guard v1",
    )
    for required in (
        CAPS_SPEC_REL,
        SESSION_SCRIPT_REL,
        SESSION_TEST_REL,
        CHECKLIST_REL,
        ENTRY_CONTRACT_REL,
        LIVE_ENTRY_RUNBOOK_REL,
        ENTRY_GATE_GUARD_REL,
        REMOTE_DOCS_GUARD_REL,
        TEST_REL,
        CROSSLINK_PACKAGE_MARKER,
        "CAPS_VISIBILITY_IS_NOT_EXECUTION_ENFORCEMENT=true",
        "CAPS_ENFORCEMENT_SEMANTIC_TOUCH=false",
        "SESSION_INVOKE_AUTHORIZED=false",
        "NO_SESSION_INVOKE_AUTHORIZED=true",
        "PREFLIGHT_LIFT_DIRECTLY_ALLOWED=false",
        "PREFLIGHT_REMAINS_BLOCKED=true",
        "PILOT_AUTHORITY_LIFT=false",
        "EVIDENCE_OR_DOCS_ANCHOR_NOT_RUNTIME_AUTHORITY=true",
        "visibility ≠ enforcement",
        "non-authorizing",
        "NO_LIVE=true",
        "NO_RUNTIME=true",
        "NO_EXECUTE=true",
        "NO_PREFLIGHT_LIFT=true",
    ):
        assert required.lower() in row.lower()


def test_ci_audit_reciprocal_crosslink_v1() -> None:
    ci_audit = _read(CI_AUDIT)
    section_start = ci_audit.index(
        "## Bounded-pilot caps enforcement point ↔ run_bounded_pilot_session CI_AUDIT reciprocal crosslink — docs/tests-only guard v1"
    )
    section_text = ci_audit[section_start : section_start + 5500]
    for required in (
        CROSSLINK_PACKAGE_MARKER,
        CAPS_SPEC_REL,
        SESSION_SCRIPT_REL,
        SESSION_TEST_REL,
        CHECKLIST_REL,
        ENTRY_CONTRACT_REL,
        LIVE_ENTRY_RUNBOOK_REL,
        ENTRY_GATE_GUARD_REL,
        REMOTE_DOCS_GUARD_REL,
        TEST_REL,
        "Visibility ≠ enforcement",
        "CAPS_VISIBILITY_IS_NOT_EXECUTION_ENFORCEMENT=true",
        "CAPS_ENFORCEMENT_SEMANTIC_TOUCH=false",
        "CAPS_ENFORCEMENT_POINT_DOCUMENTED=true",
        "RUN_BOUNDED_PILOT_SESSION_ENTRY_PATH_REFERENCED=true",
        "BOUNDED_PILOT_CAPS_OWNER_REFERENCED=true",
        "RUN_BOUNDED_PILOT_SESSION_ENTRY_GATE_GUARD_REFERENCED=true",
        "PILOT_CHECKLIST_CAPS_ROW_REFERENCED=true",
        "SESSION_INVOKE_AUTHORIZED=false",
        "NO_SESSION_INVOKE_AUTHORIZED=true",
        "PREFLIGHT_LIFT_DIRECTLY_ALLOWED=false",
        "PREFLIGHT_REMAINS_BLOCKED=true",
        "PILOT_AUTHORITY_LIFT=false",
        "EVIDENCE_OR_DOCS_ANCHOR_NOT_RUNTIME_AUTHORITY=true",
        "NO_EXECUTE=true",
        "NO_RUNTIME=true",
        "NO_LIVE=true",
        "NO_PREFLIGHT_LIFT=true",
        "U2B_PARKED=true",
        "MARKET_AIRPORT_EXCLUDED=true",
        "non-authorizing",
        "read-only",
    ):
        assert required.lower() in section_text.lower()


def test_canonical_owners_referenced_in_docs_v1() -> None:
    truth_map = _read(TRUTH_MAP)
    ci_audit = _read(CI_AUDIT)
    for rel in (
        CAPS_SPEC_REL,
        SESSION_SCRIPT_REL,
        SESSION_TEST_REL,
        CHECKLIST_REL,
        ENTRY_CONTRACT_REL,
        LIVE_ENTRY_RUNBOOK_REL,
        ENTRY_GATE_GUARD_REL,
        REMOTE_DOCS_GUARD_REL,
        TEST_REL,
    ):
        assert rel in truth_map
        assert rel in ci_audit


def test_guard_module_is_offline_static_only_v1() -> None:
    tree = ast.parse(_read(Path(__file__)))
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
