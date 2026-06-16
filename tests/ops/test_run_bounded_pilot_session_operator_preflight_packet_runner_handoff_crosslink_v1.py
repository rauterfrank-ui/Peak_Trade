"""Static reciprocal crosslink guard for bounded-pilot entry gate wrapper."""

from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SESSION_SCRIPT = ROOT / "scripts" / "ops" / "run_bounded_pilot_session.py"
SESSION_TEST = ROOT / "tests" / "ops" / "test_run_bounded_pilot_session.py"
PACKET_SCRIPT = ROOT / "scripts" / "ops" / "bounded_pilot_operator_preflight_packet.py"
READINESS_SCRIPT = ROOT / "scripts" / "ops" / "check_bounded_pilot_readiness.py"
RUNNER_SCRIPT = ROOT / "scripts" / "run_execution_session.py"
PACKET_GUARD_TEST = (
    ROOT
    / "tests"
    / "ops"
    / "test_bounded_pilot_operator_preflight_packet_readiness_stop_signal_snapshot_crosslink_v1.py"
)
LIVE_ENTRY_RUNBOOK = ROOT / "docs" / "ops" / "runbooks" / "RUNBOOK_BOUNDED_PILOT_LIVE_ENTRY.md"
ENTRY_CONTRACT = ROOT / "docs/ops/specs/BOUNDED_REAL_MONEY_PILOT_ENTRY_CONTRACT.md"
TRUTH_MAP = ROOT / "docs" / "ops" / "registry" / "DOCS_TRUTH_MAP.md"
DOCS_TRUTH_MAP_YAML = ROOT / "config" / "ops" / "docs_truth_map.yaml"
CI_AUDIT = ROOT / "docs" / "ops" / "CI_AUDIT_KNOWN_ISSUES.md"
TEST_REL = "tests/ops/test_run_bounded_pilot_session_operator_preflight_packet_runner_handoff_crosslink_v1.py"
SESSION_SCRIPT_REL = "scripts/ops/run_bounded_pilot_session.py"
SESSION_TEST_REL = "tests/ops/test_run_bounded_pilot_session.py"
PACKET_SCRIPT_REL = "scripts/ops/bounded_pilot_operator_preflight_packet.py"
READINESS_SCRIPT_REL = "scripts/ops/check_bounded_pilot_readiness.py"
RUNNER_SCRIPT_REL = "scripts/run_execution_session.py"
PACKET_GUARD_REL = "tests/ops/test_bounded_pilot_operator_preflight_packet_readiness_stop_signal_snapshot_crosslink_v1.py"
LIVE_ENTRY_RUNBOOK_REL = "docs/ops/runbooks/RUNBOOK_BOUNDED_PILOT_LIVE_ENTRY.md"
ENTRY_CONTRACT_REL = "docs/ops/specs/BOUNDED_REAL_MONEY_PILOT_ENTRY_CONTRACT.md"
CROSSLINK_PACKAGE_MARKER = "RUN_BOUNDED_PILOT_SESSION_OPERATOR_PREFLIGHT_PACKET_RUNNER_HANDOFF_CI_AUDIT_DOCS_TRUTH_MAP_RECIPROCAL_CROSSLINK_V1=true"


def _docs_truth_map_chronicle_row(truth_map: str, needle: str) -> str:
    row_start = truth_map.index(needle)
    row_end = truth_map.index("\n", row_start)
    return truth_map[row_start:row_end]


def test_crosslink_package_marker_present_v1() -> None:
    assert CROSSLINK_PACKAGE_MARKER in Path(__file__).read_text(encoding="utf-8")


def test_entry_gate_wrapper_owner_documents_chain_v1() -> None:
    text = SESSION_SCRIPT.read_text(encoding="utf-8")
    assert SESSION_SCRIPT.is_file()
    assert 'contract": "run_bounded_pilot_session"' in text
    assert "run_bounded_pilot_readiness" in text
    assert "build_operator_preflight_packet" in text
    assert "bounded_pilot_operator_preflight_packet" in text
    assert "check_bounded_pilot_readiness" in text
    assert "--no-invoke" in text
    assert RUNNER_SCRIPT_REL in text
    assert "bounded_pilot" in text
    assert "PT_BOUNDED_PILOT_INVOKED_FROM_GATE" in text
    assert "PT_LIVE_CONFIRM_TOKEN_ENV" in text
    assert "packet_ok" in text
    assert "fail-closed before handoff" in text


def test_runbook_references_entry_gate_wrapper_chain_v1() -> None:
    runbook_text = LIVE_ENTRY_RUNBOOK.read_text(encoding="utf-8")
    assert LIVE_ENTRY_RUNBOOK.is_file()
    assert SESSION_SCRIPT_REL in runbook_text
    assert RUNNER_SCRIPT_REL in runbook_text
    assert "--no-invoke" in runbook_text
    assert "packet_ok" in runbook_text


def test_entry_contract_references_entry_gate_wrapper_v1() -> None:
    contract_text = ENTRY_CONTRACT.read_text(encoding="utf-8")
    assert ENTRY_CONTRACT.is_file()
    assert "run_bounded_pilot_session.py" in contract_text
    assert "--no-invoke" in contract_text


def test_session_tests_cover_no_invoke_and_handoff_v1() -> None:
    test_text = SESSION_TEST.read_text(encoding="utf-8")
    assert SESSION_TEST.is_file()
    assert "--no-invoke" in test_text
    assert "build_operator_preflight_packet" in test_text
    assert "packet_ok" in test_text
    assert RUNNER_SCRIPT_REL in test_text
    assert "PT_BOUNDED_PILOT_INVOKED_FROM_GATE" in test_text
    assert "bounded_pilot" in test_text


def test_packet_guard_referenced_v1() -> None:
    assert PACKET_GUARD_TEST.is_file()
    guard_text = PACKET_GUARD_TEST.read_text(encoding="utf-8")
    assert (
        "BOUNDED_PILOT_OPERATOR_PREFLIGHT_PACKET_READINESS_STOP_SIGNAL_SNAPSHOT_CI_AUDIT_DOCS_TRUTH_MAP_RECIPROCAL_CROSSLINK_V1=true"
        in guard_text
    )


def test_docs_truth_map_chronicle_v1() -> None:
    truth_map = TRUTH_MAP.read_text(encoding="utf-8")
    row = _docs_truth_map_chronicle_row(
        truth_map,
        "Bounded-pilot entry gate wrapper ↔ operator preflight packet ↔ runner handoff CI_AUDIT reciprocal crosslink guard v1",
    )
    for required in (
        SESSION_SCRIPT_REL,
        SESSION_TEST_REL,
        PACKET_SCRIPT_REL,
        READINESS_SCRIPT_REL,
        RUNNER_SCRIPT_REL,
        PACKET_GUARD_REL,
        LIVE_ENTRY_RUNBOOK_REL,
        ENTRY_CONTRACT_REL,
        TEST_REL,
        CROSSLINK_PACKAGE_MARKER,
        "run_bounded_pilot_session",
        "PREFLIGHT_REMAINS_BLOCKED=true",
        "non-authorizing",
        "BOUNDED_PILOT_OPERATOR_PREFLIGHT_PACKET_GUARD_REFERENCED=true",
        "NO_INVOKE_GATE_ONLY_PARITY=true",
        "NO_LIVE=true",
        "NO_RUNTIME=true",
        "NO_EXECUTE=true",
        "NO_PREFLIGHT_LIFT=true",
    ):
        assert required.lower() in row.lower()


def test_ci_audit_reciprocal_crosslink_v1() -> None:
    ci_audit = CI_AUDIT.read_text(encoding="utf-8")
    section_start = ci_audit.index(
        "## Bounded-pilot entry gate wrapper ↔ operator preflight packet ↔ runner handoff CI_AUDIT reciprocal crosslink — docs/tests-only guard v1"
    )
    section_text = ci_audit[section_start : section_start + 5500]
    for required in (
        CROSSLINK_PACKAGE_MARKER,
        "run_bounded_pilot_session",
        SESSION_SCRIPT_REL,
        SESSION_TEST_REL,
        PACKET_SCRIPT_REL,
        READINESS_SCRIPT_REL,
        RUNNER_SCRIPT_REL,
        PACKET_GUARD_REL,
        LIVE_ENTRY_RUNBOOK_REL,
        ENTRY_CONTRACT_REL,
        TEST_REL,
        "PREFLIGHT_REMAINS_BLOCKED=true",
        "BOUNDED_PILOT_OPERATOR_PREFLIGHT_PACKET_GUARD_REFERENCED=true",
        "RUN_BOUNDED_PILOT_SESSION_ENTRY_GATE_DOCUMENTED=true",
        "BOUNDED_PILOT_READINESS_GATES_FIRST=true",
        "OPERATOR_PREFLIGHT_PACKET_BEFORE_HANDOFF=true",
        "NO_INVOKE_GATE_ONLY_PARITY=true",
        "RUNNER_HANDOFF_BOUNDED_PILOT_MODE=true",
        "FAIL_CLOSED_BEFORE_HANDOFF=true",
        "PILOT_GO_NO_GO_AUTHORITY_CREATED=false",
        "NO_EXECUTE=true",
        "NO_RUNTIME=true",
        "NO_LIVE=true",
        "NO_PREFLIGHT_LIFT=true",
        "NO_SESSION_INVOKE_AUTHORIZED=true",
        "non-authorizing",
        "read-only",
    ):
        assert required.lower() in section_text.lower()


def test_canonical_owners_referenced_in_docs_v1() -> None:
    truth_map = TRUTH_MAP.read_text(encoding="utf-8")
    ci_audit = CI_AUDIT.read_text(encoding="utf-8")
    assert DOCS_TRUTH_MAP_YAML.is_file()
    for rel in (
        SESSION_SCRIPT_REL,
        SESSION_TEST_REL,
        PACKET_SCRIPT_REL,
        READINESS_SCRIPT_REL,
        RUNNER_SCRIPT_REL,
        PACKET_GUARD_REL,
        LIVE_ENTRY_RUNBOOK_REL,
        ENTRY_CONTRACT_REL,
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
