"""Static reciprocal crosslink guard for Pilot Row 7 fee/slippage conservative assumptions."""

from __future__ import annotations

import ast
import importlib.util
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FEE_SLIPPAGE_DOC = ROOT / "docs" / "ops" / "specs" / "FEE_SLIPPAGE_CONSERVATIVE_ASSUMPTIONS.md"
PILOT_SLICE_DOC = ROOT / "docs" / "ops" / "specs" / "PILOT_GO_NO_GO_OPERATIONAL_SLICE.md"
BACKTEST_SMOKE_TEST = ROOT / "tests" / "test_demo_execution_backtest_smoke.py"
PILOT_EVAL_SCRIPT = ROOT / "scripts" / "ops" / "pilot_go_no_go_eval_v1.py"
PILOT_EVAL_TEST = ROOT / "tests" / "ops" / "test_pilot_go_no_go_eval_v1.py"
TRUTH_MAP = ROOT / "docs" / "ops" / "registry" / "DOCS_TRUTH_MAP.md"
CI_AUDIT = ROOT / "docs" / "ops" / "CI_AUDIT_KNOWN_ISSUES.md"
TEST_REL = "tests/ops/test_pilot_fee_slippage_conservative_assumptions_crosslink_v1.py"
FEE_SLIPPAGE_DOC_REL = "docs/ops/specs/FEE_SLIPPAGE_CONSERVATIVE_ASSUMPTIONS.md"
BACKTEST_SMOKE_REL = "tests/test_demo_execution_backtest_smoke.py"
PILOT_EVAL_REL = "scripts/ops/pilot_go_no_go_eval_v1.py"
PILOT_EVAL_TEST_REL = "tests/ops/test_pilot_go_no_go_eval_v1.py"
CROSSLINK_PACKAGE_MARKER = "PILOT_FEE_SLIPPAGE_CONSERVATIVE_ASSUMPTIONS_CI_AUDIT_PILOT_GONOGO_BACKTEST_SMOKE_RECIPROCAL_CROSSLINK_V1=true"
CANONICAL_FEE_BPS = 10.0
CANONICAL_SLIPPAGE_BPS = 5.0


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


def test_fee_slippage_doc_documents_conservative_defaults_v1() -> None:
    text = FEE_SLIPPAGE_DOC.read_text(encoding="utf-8")
    assert FEE_SLIPPAGE_DOC.is_file()
    assert re.search(r"fee_bps\s*\|\s*10\.0", text)
    assert re.search(r"slippage_bps\s*\|\s*5\.0", text)
    assert "Row 7" in text
    assert "DOCS_TOKEN_FEE_SLIPPAGE_CONSERVATIVE_ASSUMPTIONS" in text


def test_backtest_smoke_uses_same_conservative_defaults_v1() -> None:
    from scripts.demo_execution_backtest import parse_args

    args = parse_args([])
    assert args.fee_bps == CANONICAL_FEE_BPS
    assert args.slippage_bps == CANONICAL_SLIPPAGE_BPS

    smoke_text = BACKTEST_SMOKE_TEST.read_text(encoding="utf-8")
    assert "assert args.fee_bps == 10.0" in smoke_text
    assert "assert args.slippage_bps == 5.0" in smoke_text


def test_pilot_eval_row7_intentionally_excluded_v1() -> None:
    mod = _load_pilot_eval_module()
    row_numbers = [num for num, _area, _fn in mod.ROWS]
    assert len(row_numbers) == 11
    assert 7 not in row_numbers
    assert 1 in row_numbers and 15 in row_numbers

    pilot_eval_text = PILOT_EVAL_SCRIPT.read_text(encoding="utf-8")
    assert "11 cockpit-based rows" in pilot_eval_text

    pilot_eval_test_text = PILOT_EVAL_TEST.read_text(encoding="utf-8")
    assert 'len(data["rows"]) == 11' in pilot_eval_test_text

    slice_text = PILOT_SLICE_DOC.read_text(encoding="utf-8")
    assert "Fee/Slippage Realism" in slice_text
    assert "FEE_SLIPPAGE_CONSERVATIVE_ASSUMPTIONS" in slice_text


def test_docs_truth_map_pilot_fee_slippage_chronicle_v1() -> None:
    truth_map = TRUTH_MAP.read_text(encoding="utf-8")
    row = _docs_truth_map_chronicle_row(
        truth_map,
        "Pilot Row 7 Fee/Slippage conservative assumptions CI_AUDIT ↔ pilot eval / backtest smoke reciprocal crosslink guard v1",
    )
    for required in (
        FEE_SLIPPAGE_DOC_REL,
        BACKTEST_SMOKE_REL,
        PILOT_EVAL_REL,
        PILOT_EVAL_TEST_REL,
        TEST_REL,
        CROSSLINK_PACKAGE_MARKER,
        "PILOT_EVAL_ROW7_INTENTIONALLY_EXCLUDED=true",
        "non-authorizing",
        "fee_bps=10.0",
        "slippage_bps=5.0",
    ):
        assert required.lower() in row.lower()


def test_ci_audit_pilot_fee_slippage_reciprocal_crosslink_v1() -> None:
    ci_audit = CI_AUDIT.read_text(encoding="utf-8")
    section_start = ci_audit.index(
        "## Pilot Row 7 Fee/Slippage conservative assumptions CI_AUDIT ↔ pilot eval / backtest smoke reciprocal crosslink — docs/tests-only guard v1"
    )
    section_text = ci_audit[section_start : section_start + 4500]
    for required in (
        CROSSLINK_PACKAGE_MARKER,
        "PILOT_EVAL_ROW7_INTENTIONALLY_EXCLUDED=true",
        "FEE_BPS_10_SLIPPAGE_BPS_5_CROSSLINKED=true",
        "BACKTEST_SMOKE_DEFAULTS_ALIGNED=true",
        "PILOT_GO_NO_GO_AUTHORITY_CREATED=false",
        "FEE_SLIPPAGE_ACCOUNTING_LOGIC_TOUCHED=false",
        FEE_SLIPPAGE_DOC_REL,
        BACKTEST_SMOKE_REL,
        PILOT_EVAL_REL,
        PILOT_EVAL_TEST_REL,
        TEST_REL,
        "fee_bps=10.0",
        "slippage_bps=5.0",
        "11 cockpit rows",
        "non-authorizing",
    ):
        assert required.lower() in section_text.lower()


def test_canonical_owners_referenced_in_docs_v1() -> None:
    truth_map = TRUTH_MAP.read_text(encoding="utf-8")
    ci_audit = CI_AUDIT.read_text(encoding="utf-8")
    for rel in (
        FEE_SLIPPAGE_DOC_REL,
        BACKTEST_SMOKE_REL,
        PILOT_EVAL_REL,
        PILOT_EVAL_TEST_REL,
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
