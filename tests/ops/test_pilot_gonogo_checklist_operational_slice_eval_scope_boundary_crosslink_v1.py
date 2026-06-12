"""Static reciprocal crosslink guard for Pilot Go/No-Go 15→11 eval scope boundary."""

from __future__ import annotations

import ast
import importlib.util
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CHECKLIST_DOC = ROOT / "docs" / "ops" / "specs" / "PILOT_GO_NO_GO_CHECKLIST.md"
PILOT_SLICE_DOC = ROOT / "docs" / "ops" / "specs" / "PILOT_GO_NO_GO_OPERATIONAL_SLICE.md"
PILOT_EVAL_SCRIPT = ROOT / "scripts" / "ops" / "pilot_go_no_go_eval_v1.py"
PILOT_EVAL_TEST = ROOT / "tests" / "ops" / "test_pilot_go_no_go_eval_v1.py"
ROW7_GUARD_TEST = (
    ROOT / "tests" / "ops" / "test_pilot_fee_slippage_conservative_assumptions_crosslink_v1.py"
)
ROWS81011_GUARD_TEST = (
    ROOT / "tests" / "ops" / "test_pilot_gonogo_rows_8_10_11_exclusion_crosslink_v1.py"
)
TRUTH_MAP = ROOT / "docs" / "ops" / "registry" / "DOCS_TRUTH_MAP.md"
CI_AUDIT = ROOT / "docs" / "ops" / "CI_AUDIT_KNOWN_ISSUES.md"
TEST_REL = (
    "tests/ops/test_pilot_gonogo_checklist_operational_slice_eval_scope_boundary_crosslink_v1.py"
)
CHECKLIST_REL = "docs/ops/specs/PILOT_GO_NO_GO_CHECKLIST.md"
PILOT_SLICE_REL = "docs/ops/specs/PILOT_GO_NO_GO_OPERATIONAL_SLICE.md"
PILOT_EVAL_REL = "scripts/ops/pilot_go_no_go_eval_v1.py"
PILOT_EVAL_TEST_REL = "tests/ops/test_pilot_go_no_go_eval_v1.py"
ROW7_GUARD_REL = "tests/ops/test_pilot_fee_slippage_conservative_assumptions_crosslink_v1.py"
ROWS81011_GUARD_REL = "tests/ops/test_pilot_gonogo_rows_8_10_11_exclusion_crosslink_v1.py"
CROSSLINK_PACKAGE_MARKER = "PILOT_GONOGO_CHECKLIST_OPERATIONAL_SLICE_EVAL_SCOPE_BOUNDARY_CI_AUDIT_DOCS_TRUTH_MAP_RECIPROCAL_CROSSLINK_V1=true"
DOC_BASED_EXCLUDED_ROWS = (7, 8, 10, 11)
EVALUATED_ROWS = (1, 2, 3, 4, 5, 6, 9, 12, 13, 14, 15)
CHECKLIST_AREAS = (
    "Safety Gates",
    "Kill Switch",
    "Policy Posture",
    "Operator Visibility",
    "Pilot Caps",
    "Treasury Separation",
    "Fee/Slippage Realism",
    "Partial Fill Handling",
    "Stale State Handling",
    "Restart / Replay",
    "Incident Runbooks",
    "Evidence Continuity",
    "Dependency Degradation",
    "Human Supervision",
    "Ambiguity Rule",
)
CHECKLIST_ROW_PATTERN = re.compile(r"^\| (\d+) \|", re.MULTILINE)


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


def _numbered_table_rows(text: str) -> list[int]:
    return [int(match.group(1)) for match in CHECKLIST_ROW_PATTERN.finditer(text)]


def test_crosslink_package_marker_present_v1() -> None:
    assert CROSSLINK_PACKAGE_MARKER in Path(__file__).read_text(encoding="utf-8")


def test_checklist_remains_15_row_draft_source_v1() -> None:
    text = CHECKLIST_DOC.read_text(encoding="utf-8")
    assert CHECKLIST_DOC.is_file()
    assert "status: DRAFT" in text
    assert "DOCS_TOKEN_PILOT_GO_NO_GO_CHECKLIST" in text
    for area in CHECKLIST_AREAS:
        assert area in text
    assert len(CHECKLIST_AREAS) == 15


def test_operational_slice_remains_15_row_draft_mapping_v1() -> None:
    text = PILOT_SLICE_DOC.read_text(encoding="utf-8")
    assert PILOT_SLICE_DOC.is_file()
    assert "status: DRAFT" in text
    assert "DOCS_TOKEN_PILOT_GO_NO_GO_OPERATIONAL_SLICE" in text
    assert CHECKLIST_REL.split("/")[-1].replace(".md", "") in text
    row_numbers = _numbered_table_rows(text)
    assert row_numbers == list(range(1, 16))


def test_pilot_eval_models_11_cockpit_rows_v1() -> None:
    mod = _load_pilot_eval_module()
    row_numbers = [num for num, _area, _fn in mod.ROWS]
    assert len(row_numbers) == 11
    assert row_numbers == list(EVALUATED_ROWS)
    for excluded in DOC_BASED_EXCLUDED_ROWS:
        assert excluded not in row_numbers

    pilot_eval_text = PILOT_EVAL_SCRIPT.read_text(encoding="utf-8")
    assert "11 cockpit-based rows" in pilot_eval_text
    assert CHECKLIST_REL.split("/")[-1].replace(".md", "") in pilot_eval_text
    assert PILOT_SLICE_REL.split("/")[-1].replace(".md", "") in pilot_eval_text

    pilot_eval_test_text = PILOT_EVAL_TEST.read_text(encoding="utf-8")
    assert 'len(data["rows"]) == 11' in pilot_eval_test_text


def test_row_level_guards_exist_for_doc_based_exclusions_v1() -> None:
    assert ROW7_GUARD_TEST.is_file()
    assert ROWS81011_GUARD_TEST.is_file()
    row7_text = ROW7_GUARD_TEST.read_text(encoding="utf-8")
    rows81011_text = ROWS81011_GUARD_TEST.read_text(encoding="utf-8")
    assert (
        "PILOT_FEE_SLIPPAGE_CONSERVATIVE_ASSUMPTIONS_CI_AUDIT_PILOT_GONOGO_BACKTEST_SMOKE_RECIPROCAL_CROSSLINK_V1=true"
        in row7_text
    )
    assert (
        "PILOT_GONOGO_ROWS_8_10_11_EXCLUSION_CI_AUDIT_DOCS_TRUTH_MAP_RECIPROCAL_CROSSLINK_V1=true"
        in rows81011_text
    )


def test_docs_truth_map_eval_scope_boundary_chronicle_v1() -> None:
    truth_map = TRUTH_MAP.read_text(encoding="utf-8")
    row = _docs_truth_map_chronicle_row(
        truth_map,
        "Pilot Go/No-Go checklist ↔ operational slice ↔ eval scope boundary CI_AUDIT reciprocal crosslink guard v1",
    )
    for required in (
        CHECKLIST_REL,
        PILOT_SLICE_REL,
        PILOT_EVAL_REL,
        PILOT_EVAL_TEST_REL,
        ROW7_GUARD_REL,
        ROWS81011_GUARD_REL,
        TEST_REL,
        CROSSLINK_PACKAGE_MARKER,
        "PILOT_CHECKLIST_15_ROW_DRAFT=true",
        "PILOT_OPERATIONAL_SLICE_15_ROW_DRAFT=true",
        "PILOT_EVAL_11_COCKPIT_ROWS=true",
        "PILOT_EVAL_ROWS_7_8_10_11_DOC_BASED_EXCLUDED=true",
        "DRAFT_POSTURE_CHANGED=false",
        "non-authorizing",
        "NEW_COCKPIT_ROW_CREATED=false",
    ):
        assert required.lower() in row.lower()


def test_ci_audit_eval_scope_boundary_reciprocal_crosslink_v1() -> None:
    ci_audit = CI_AUDIT.read_text(encoding="utf-8")
    section_start = ci_audit.index(
        "## Pilot Go/No-Go checklist ↔ operational slice ↔ eval scope boundary CI_AUDIT reciprocal crosslink — docs/tests-only guard v1"
    )
    section_text = ci_audit[section_start : section_start + 5500]
    for required in (
        CROSSLINK_PACKAGE_MARKER,
        "PILOT_CHECKLIST_15_ROW_DRAFT=true",
        "PILOT_OPERATIONAL_SLICE_15_ROW_DRAFT=true",
        "PILOT_EVAL_11_COCKPIT_ROWS=true",
        "PILOT_EVAL_ROWS_7_8_10_11_DOC_BASED_EXCLUDED=true",
        "PILOT_ROW7_GUARD_REFERENCED=true",
        "PILOT_ROWS_8_10_11_GUARD_REFERENCED=true",
        "PILOT_DOC_BASED_MISSING_NOT_PASS=true",
        "DRAFT_POSTURE_CHANGED=false",
        "PILOT_GO_NO_GO_AUTHORITY_CREATED=false",
        "NEW_COCKPIT_ROW_CREATED=false",
        CHECKLIST_REL,
        PILOT_SLICE_REL,
        PILOT_EVAL_REL,
        PILOT_EVAL_TEST_REL,
        ROW7_GUARD_REL,
        ROWS81011_GUARD_REL,
        TEST_REL,
        "15-row",
        "11 cockpit rows",
        "non-authorizing",
    ):
        assert required.lower() in section_text.lower()


def test_canonical_owners_referenced_in_docs_v1() -> None:
    truth_map = TRUTH_MAP.read_text(encoding="utf-8")
    ci_audit = CI_AUDIT.read_text(encoding="utf-8")
    for rel in (
        CHECKLIST_REL,
        PILOT_SLICE_REL,
        PILOT_EVAL_REL,
        PILOT_EVAL_TEST_REL,
        ROW7_GUARD_REL,
        ROWS81011_GUARD_REL,
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
