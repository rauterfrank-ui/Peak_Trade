"""Static reciprocal crosslink guard for bounded-pilot operator preflight packet."""

from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PACKET_SCRIPT = ROOT / "scripts" / "ops" / "bounded_pilot_operator_preflight_packet.py"
PACKET_TEST = ROOT / "tests" / "ops" / "test_bounded_pilot_operator_preflight_packet.py"
READINESS_SCRIPT = ROOT / "scripts" / "ops" / "check_bounded_pilot_readiness.py"
READINESS_TEST = ROOT / "tests" / "ops" / "test_check_bounded_pilot_readiness.py"
STOP_SIGNAL_SCRIPT = ROOT / "scripts" / "ops" / "snapshot_operator_stop_signals.py"
READINESS_GUARD_TEST = (
    ROOT
    / "tests"
    / "ops"
    / "test_bounded_pilot_readiness_live_readiness_pilot_gonogo_eval_crosslink_v1.py"
)
LIVE_ENTRY_RUNBOOK = ROOT / "docs" / "ops" / "runbooks" / "RUNBOOK_BOUNDED_PILOT_LIVE_ENTRY.md"
TRUTH_MAP = ROOT / "docs" / "ops" / "registry" / "DOCS_TRUTH_MAP.md"
DOCS_TRUTH_MAP_YAML = ROOT / "config" / "ops" / "docs_truth_map.yaml"
CI_AUDIT = ROOT / "docs" / "ops" / "CI_AUDIT_KNOWN_ISSUES.md"
TEST_REL = "tests/ops/test_bounded_pilot_operator_preflight_packet_readiness_stop_signal_snapshot_crosslink_v1.py"
PACKET_SCRIPT_REL = "scripts/ops/bounded_pilot_operator_preflight_packet.py"
PACKET_TEST_REL = "tests/ops/test_bounded_pilot_operator_preflight_packet.py"
READINESS_SCRIPT_REL = "scripts/ops/check_bounded_pilot_readiness.py"
READINESS_TEST_REL = "tests/ops/test_check_bounded_pilot_readiness.py"
STOP_SIGNAL_SCRIPT_REL = "scripts/ops/snapshot_operator_stop_signals.py"
READINESS_GUARD_REL = (
    "tests/ops/test_bounded_pilot_readiness_live_readiness_pilot_gonogo_eval_crosslink_v1.py"
)
LIVE_ENTRY_RUNBOOK_REL = "docs/ops/runbooks/RUNBOOK_BOUNDED_PILOT_LIVE_ENTRY.md"
CROSSLINK_PACKAGE_MARKER = "BOUNDED_PILOT_OPERATOR_PREFLIGHT_PACKET_READINESS_STOP_SIGNAL_SNAPSHOT_CI_AUDIT_DOCS_TRUTH_MAP_RECIPROCAL_CROSSLINK_V1=true"


def _docs_truth_map_chronicle_row(truth_map: str, needle: str) -> str:
    row_start = truth_map.index(needle)
    row_end = truth_map.index("\n", row_start)
    return truth_map[row_start:row_end]


def test_crosslink_package_marker_present_v1() -> None:
    assert CROSSLINK_PACKAGE_MARKER in Path(__file__).read_text(encoding="utf-8")


def test_operator_preflight_packet_owner_documents_orchestration_v1() -> None:
    text = PACKET_SCRIPT.read_text(encoding="utf-8")
    assert PACKET_SCRIPT.is_file()
    assert 'CONTRACT_ID = "bounded_pilot_operator_preflight_packet_v1"' in text
    assert "run_bounded_pilot_readiness" in text
    assert "build_stop_signal_snapshot" in text
    assert "check_bounded_pilot_readiness" in text
    assert "snapshot_operator_stop_signals" in text
    assert "No new gate semantics" in text
    assert "no live authorization" in text
    assert "incident_stop_artifact" in text
    assert "kill_switch_file" in text
    assert "bounded_pilot_readiness_v1" in text


def test_runbook_references_operator_preflight_packet_v1() -> None:
    runbook_text = LIVE_ENTRY_RUNBOOK.read_text(encoding="utf-8")
    assert LIVE_ENTRY_RUNBOOK.is_file()
    assert PACKET_SCRIPT_REL in runbook_text
    assert STOP_SIGNAL_SCRIPT_REL.split("/")[-1].replace(".py", "") in runbook_text
    assert READINESS_SCRIPT_REL in runbook_text
    assert "read-only" in runbook_text.lower()


def test_packet_tests_cover_fail_closed_orchestration_v1() -> None:
    test_text = PACKET_TEST.read_text(encoding="utf-8")
    assert PACKET_TEST.is_file()
    assert "CONTRACT_ID" in test_text
    assert "run_bounded_pilot_readiness" in test_text
    assert "build_stop_signal_snapshot" in test_text
    assert "packet_ok" in test_text
    assert "stop_snapshot_ok" in test_text


def test_readiness_guard_referenced_v1() -> None:
    assert READINESS_GUARD_TEST.is_file()
    guard_text = READINESS_GUARD_TEST.read_text(encoding="utf-8")
    assert (
        "BOUNDED_PILOT_READINESS_LIVE_READINESS_PILOT_GONOGO_EVAL_CI_AUDIT_DOCS_TRUTH_MAP_RECIPROCAL_CROSSLINK_V1=true"
        in guard_text
    )


def test_docs_truth_map_chronicle_v1() -> None:
    truth_map = TRUTH_MAP.read_text(encoding="utf-8")
    row = _docs_truth_map_chronicle_row(
        truth_map,
        "Bounded-pilot operator preflight packet ↔ readiness ↔ stop-signal snapshot CI_AUDIT reciprocal crosslink guard v1",
    )
    for required in (
        PACKET_SCRIPT_REL,
        PACKET_TEST_REL,
        READINESS_SCRIPT_REL,
        READINESS_TEST_REL,
        STOP_SIGNAL_SCRIPT_REL,
        READINESS_GUARD_REL,
        LIVE_ENTRY_RUNBOOK_REL,
        TEST_REL,
        CROSSLINK_PACKAGE_MARKER,
        "bounded_pilot_operator_preflight_packet_v1",
        "PREFLIGHT_REMAINS_BLOCKED=true",
        "non-authorizing",
        "BOUNDED_PILOT_READINESS_GUARD_REFERENCED=true",
        "NO_LIVE=true",
        "NO_RUNTIME=true",
        "NO_EXECUTE=true",
        "NO_PREFLIGHT_LIFT=true",
    ):
        assert required.lower() in row.lower()


def test_ci_audit_reciprocal_crosslink_v1() -> None:
    ci_audit = CI_AUDIT.read_text(encoding="utf-8")
    section_start = ci_audit.index(
        "## Bounded-pilot operator preflight packet ↔ readiness ↔ stop-signal snapshot CI_AUDIT reciprocal crosslink — docs/tests-only guard v1"
    )
    section_text = ci_audit[section_start : section_start + 5500]
    for required in (
        CROSSLINK_PACKAGE_MARKER,
        "bounded_pilot_operator_preflight_packet_v1",
        PACKET_SCRIPT_REL,
        PACKET_TEST_REL,
        READINESS_SCRIPT_REL,
        READINESS_TEST_REL,
        STOP_SIGNAL_SCRIPT_REL,
        READINESS_GUARD_REL,
        LIVE_ENTRY_RUNBOOK_REL,
        TEST_REL,
        "PREFLIGHT_REMAINS_BLOCKED=true",
        "BOUNDED_PILOT_READINESS_GUARD_REFERENCED=true",
        "BOUNDED_PILOT_OPERATOR_PREFLIGHT_PACKET_ORCHESTRATION_DOCUMENTED=true",
        "BOUNDED_PILOT_READINESS_BUNDLED=true",
        "STOP_SIGNAL_SNAPSHOT_BUNDLED=true",
        "STOP_SIGNAL_HARD_ERROR_FAIL_CLOSED=true",
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
        PACKET_SCRIPT_REL,
        PACKET_TEST_REL,
        READINESS_SCRIPT_REL,
        READINESS_TEST_REL,
        STOP_SIGNAL_SCRIPT_REL,
        READINESS_GUARD_REL,
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
