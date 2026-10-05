"""Regression guards for PASS_006A closure integrity failures."""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
LOGIC_PATH = ROOT / "scripts/ops/peak_trade_forensic_closure_logic_v1.py"
FIXTURE_PATH = (
    Path(__file__).resolve().parent
    / "fixtures"
    / "runtime_surface_denominator_regression_fixture_v1.json"
)


def _load_logic():
    spec = importlib.util.spec_from_file_location("closure_logic", LOGIC_PATH)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_surface_candidates_are_not_true_runtime_surfaces() -> None:
    logic = _load_logic()
    rows = __import__("json").loads(FIXTURE_PATH.read_text(encoding="utf-8"))["ROWS"]
    counts = logic.verify_surface_classifications(rows)
    assert counts["TRUE_RUNTIME_SURFACE"] == 180
    assert len(rows) == 1402
    assert counts["TRUE_RUNTIME_SURFACE"] != len(rows)


def test_build_cross_flows_rejects_empty_semantic_edges() -> None:
    logic = _load_logic()
    with pytest.raises(logic.SemanticEdgesRequiredError):
        logic.require_semantic_edges_for_cross_flows([], min_expected=1)


def test_def001_closed_when_pre_external_prefix_matches() -> None:
    logic = _load_logic()
    defects = logic.build_current_defect_register(
        pre_external_wired=True,
        pre_external_prefix_match=True,
        prefix_path="exidence/.../prefix_probe_results.json",
    )
    d1 = next(d for d in defects if d["DEFECT_ID"] == "DEF-001")
    assert d1["CURRENT_STATUS"] == "CLOSED_REPAIRED_LANDED"
    assert not str(d1["CURRENT_SEVERITY"]).startswith("S1")
