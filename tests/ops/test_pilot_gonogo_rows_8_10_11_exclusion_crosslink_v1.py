"""Static reciprocal crosslink guard for Pilot Go/No-Go Rows 8/10/11 doc-based eval exclusion."""

from __future__ import annotations

import ast
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
EDGE_CASE_MATRIX_DOC = ROOT / "docs" / "ops" / "specs" / "PILOT_EXECUTION_EDGE_CASE_MATRIX.md"
PILOT_SLICE_DOC = ROOT / "docs" / "ops" / "specs" / "PILOT_GO_NO_GO_OPERATIONAL_SLICE.md"
PILOT_EVAL_SCRIPT = ROOT / "scripts" / "ops" / "pilot_go_no_go_eval_v1.py"
PILOT_EVAL_TEST = ROOT / "tests" / "ops" / "test_pilot_go_no_go_eval_v1.py"
RUNBOOKS_DIR = ROOT / "docs" / "ops" / "runbooks"
TRUTH_MAP = ROOT / "docs" / "ops" / "registry" / "DOCS_TRUTH_MAP.md"
CI_AUDIT = ROOT / "docs" / "ops" / "CI_AUDIT_KNOWN_ISSUES.md"
TEST_REL = "tests/ops/test_pilot_gonogo_rows_8_10_11_exclusion_crosslink_v1.py"
EDGE_CASE_MATRIX_REL = "docs/ops/specs/PILOT_EXECUTION_EDGE_CASE_MATRIX.md"
PILOT_SLICE_REL = "docs/ops/specs/PILOT_GO_NO_GO_OPERATIONAL_SLICE.md"
PILOT_EVAL_REL = "scripts/ops/pilot_go_no_go_eval_v1.py"
PILOT_EVAL_TEST_REL = "tests/ops/test_pilot_go_no_go_eval_v1.py"
RESTART_RUNBOOK_REL = "docs/ops/runbooks/RUNBOOK_PILOT_INCIDENT_RESTART_MID_SESSION.md"
CROSSLINK_PACKAGE_MARKER = (
    "PILOT_GONOGO_ROWS_8_10_11_EXCLUSION_CI_AUDIT_DOCS_TRUTH_MAP_RECIPROCAL_CROSSLINK_V1=true"
)
INCIDENT_RUNBOOK_BASENAMES = (
    "RUNBOOK_PILOT_INCIDENT_EXCHANGE_DEGRADED.md",
    "RUNBOOK_PILOT_INCIDENT_TELEMETRY_DEGRADED.md",
    "RUNBOOK_PILOT_INCIDENT_RECONCILIATION_MISMATCH.md",
    "RUNBOOK_PILOT_INCIDENT_TRANSFER_AMBIGUITY.md",
    "RUNBOOK_PILOT_INCIDENT_SESSION_END_MISMATCH.md",
    "RUNBOOK_PILOT_INCIDENT_UNEXPECTED_EXPOSURE.md",
    "RUNBOOK_PILOT_INCIDENT_RESTART_MID_SESSION.md",
)
EXCLUDED_DOC_BASED_ROWS = (8, 10, 11)


def _docs_truth_map_chronicle_row(truth_map: str, needle: str) -> str:
    row_start = truth_map.index(needle)
    row_end = truth_map.index("\n", row_start)
    return truth_map[row_start:row_end]


def _load_pilot_eval_module():
    spec = importlib.util.spec_from_file_location("pilot_go_no_go_eval_v1", PILOT_EVAL_SCRIPT)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_crosslink_package_marker_present_v1() -> None:
    assert CROSSLINK_PACKAGE_MARKER in Path(__file__).read_text(encoding="utf-8")


def test_pilot_eval_rows_8_10_11_intentionally_excluded_v1() -> None:
    mod = _load_pilot_eval_module()
    row_numbers = [num for num, _area, _fn in mod.ROWS]
    assert len(row_numbers) == 11
    for excluded in EXCLUDED_DOC_BASED_ROWS:
        assert excluded not in row_numbers

    pilot_eval_text = PILOT_EVAL_SCRIPT.read_text(encoding="utf-8")
    assert "11 cockpit-based rows" in pilot_eval_text

    pilot_eval_test_text = PILOT_EVAL_TEST.read_text(encoding="utf-8")
    assert 'len(data["rows"]) == 11' in pilot_eval_test_text


def test_operational_slice_documents_doc_based_rows_v1() -> None:
    slice_text = PILOT_SLICE_DOC.read_text(encoding="utf-8")
    assert "Partial Fill Handling" in slice_text
    assert "Restart / Replay" in slice_text
    assert "Incident Runbooks" in slice_text
    assert EDGE_CASE_MATRIX_REL.split("/")[-1].replace(".md", "") in slice_text
    assert "RUNBOOK_PILOT_INCIDENT_" in slice_text
    assert "RUNBOOK_PILOT_INCIDENT_RESTART_MID_SESSION" in slice_text


def test_edge_case_matrix_covers_rows_8_and_10_domains_v1() -> None:
    matrix_text = EDGE_CASE_MATRIX_DOC.read_text(encoding="utf-8")
    assert EDGE_CASE_MATRIX_DOC.is_file()
    assert "Partial fill" in matrix_text
    assert "Restart mid-session" in matrix_text
    assert "Replay ambiguity" in matrix_text
    assert "DOCS_TOKEN_PILOT_EXECUTION_EDGE_CASE_MATRIX" in matrix_text


def test_incident_and_restart_runbooks_exist_v1() -> None:
    for basename in INCIDENT_RUNBOOK_BASENAMES:
        path = RUNBOOKS_DIR / basename
        assert path.is_file(), f"missing runbook: {basename}"


def test_docs_truth_map_pilot_rows_8_10_11_exclusion_chronicle_v1() -> None:
    truth_map = TRUTH_MAP.read_text(encoding="utf-8")
    row = _docs_truth_map_chronicle_row(
        truth_map,
        "Pilot Rows 8/10/11 doc-based eval exclusion CI_AUDIT ↔ edge-case matrix / incident runbooks reciprocal crosslink guard v1",
    )
    for required in (
        EDGE_CASE_MATRIX_REL,
        PILOT_SLICE_REL,
        PILOT_EVAL_REL,
        PILOT_EVAL_TEST_REL,
        RESTART_RUNBOOK_REL,
        TEST_REL,
        CROSSLINK_PACKAGE_MARKER,
        "PILOT_EVAL_ROW8_INTENTIONALLY_EXCLUDED=true",
        "PILOT_EVAL_ROW10_INTENTIONALLY_EXCLUDED=true",
        "PILOT_EVAL_ROW11_INTENTIONALLY_EXCLUDED=true",
        "non-authorizing",
        "NEW_COCKPIT_ROW_CREATED=false",
    ):
        assert required.lower() in row.lower()


def test_ci_audit_pilot_rows_8_10_11_reciprocal_crosslink_v1() -> None:
    ci_audit = CI_AUDIT.read_text(encoding="utf-8")
    section_start = ci_audit.index(
        "## Pilot Rows 8/10/11 doc-based eval exclusion CI_AUDIT ↔ edge-case matrix / incident runbooks reciprocal crosslink — docs/tests-only guard v1"
    )
    section_text = ci_audit[section_start : section_start + 5000]
    for required in (
        CROSSLINK_PACKAGE_MARKER,
        "PILOT_EVAL_ROW8_INTENTIONALLY_EXCLUDED=true",
        "PILOT_EVAL_ROW10_INTENTIONALLY_EXCLUDED=true",
        "PILOT_EVAL_ROW11_INTENTIONALLY_EXCLUDED=true",
        "PILOT_GO_NO_GO_AUTHORITY_CREATED=false",
        "NEW_COCKPIT_ROW_CREATED=false",
        EDGE_CASE_MATRIX_REL,
        PILOT_SLICE_REL,
        PILOT_EVAL_REL,
        PILOT_EVAL_TEST_REL,
        RESTART_RUNBOOK_REL,
        TEST_REL,
        "RUNBOOK_PILOT_INCIDENT_",
        "11 cockpit rows",
        "non-authorizing",
    ):
        assert required.lower() in section_text.lower()


def test_canonical_owners_referenced_in_docs_v1() -> None:
    truth_map = TRUTH_MAP.read_text(encoding="utf-8")
    ci_audit = CI_AUDIT.read_text(encoding="utf-8")
    for rel in (
        EDGE_CASE_MATRIX_REL,
        PILOT_SLICE_REL,
        PILOT_EVAL_REL,
        PILOT_EVAL_TEST_REL,
        RESTART_RUNBOOK_REL,
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
