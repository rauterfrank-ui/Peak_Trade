"""Contract tests for STEP29M lean parameter and cost binding readiness v0."""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

from src.research.step29m_full_canonical_system_lean_parameter_and_cost_binding_readiness_v0 import (
    AUTHORITY_EFFECT,
    BITCOIN_DIRECTION_ALLOWED,
    FUTURES_ONLY,
    OPERATOR_GO,
    RUNTIME_EFFECT,
    SLICE_ID,
    build_baseline_readiness_report_v0,
    build_canonical_current_state_v0,
    build_cost_and_reference_binding_matrix_v0,
    build_parameter_classification_v0,
    build_reuse_first_assessment_v0,
    evaluate_readiness_v0,
)

ROOT = Path(__file__).resolve().parents[2]
MODULE = (
    ROOT
    / "src/research/step29m_full_canonical_system_lean_parameter_and_cost_binding_readiness_v0.py"
)


def test_slice_metadata_offline_only() -> None:
    assert SLICE_ID == "STEP29M_FULL_CANONICAL_SYSTEM_LEAN_PARAMETER_AND_COST_BINDING_READINESS_V0"
    assert AUTHORITY_EFFECT == "NONE"
    assert RUNTIME_EFFECT == "NONE"
    assert FUTURES_ONLY is True
    assert BITCOIN_DIRECTION_ALLOWED is False
    assert "GO_" in OPERATOR_GO


def test_no_runtime_imports() -> None:
    tree = ast.parse(MODULE.read_text(encoding="utf-8"))
    forbidden = ("src.trading.live", "src.scheduler", "src.orders")
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            for prefix in forbidden:
                assert not node.module.startswith(prefix)


def test_parameter_classification_fleet_only() -> None:
    rows = build_parameter_classification_v0()
    strategy_ids = {r.strategy_id for r in rows}
    assert strategy_ids == {"trend_following", "bollinger_bands", "momentum_1h"}
    core = [r for r in rows if r.tier == "CONSTITUTIONAL_CORE"]
    assert core
    assert all(r.changes_canonical_trading_semantics for r in core)
    calibratable = [r for r in rows if r.tier == "CALIBRATABLE"]
    assert {r.parameter_name for r in calibratable} == {"fee_bps", "slippage_bps"}


def test_reuse_first_no_parallel_ssot() -> None:
    assessment = build_reuse_first_assessment_v0(ROOT)
    assert assessment["parallel_strategy_ssot_created"] is False
    assert assessment["candidate_v2_strategy_implementation_created"] is False
    assert assessment["reuse_path"] == "CONSOLIDATE_TO_EXISTING_OWNER"


def test_cost_binding_matrix_realistic_costs() -> None:
    rows = build_cost_and_reference_binding_matrix_v0(ROOT)
    assert len(rows) == 3
    for row in rows:
        assert row.fee_bps == 10.0
        assert row.slippage_bps == 5.0
        assert row.funding_bound is True


def test_readiness_assessment_fail_closed_on_gaps() -> None:
    result = evaluate_readiness_v0(ROOT)
    assert result.assessment_verdict in {
        "PASS_READINESS_ASSESSMENT_COMPLETE",
        "FAIL_CLOSED_ASSESSMENT_PRECONDITION",
    }
    assert result.baseline_evaluation_admissible is True
    assert not result.blocking_gaps


def test_baseline_report_and_current_state() -> None:
    report = build_baseline_readiness_report_v0(ROOT)
    assert report["slice_id"] == SLICE_ID
    assert report["baseline_evaluation_admissible"] is True
    state = build_canonical_current_state_v0(ROOT)
    assert "full_canonical_chain_wired" in state
    assert state["baseline_evaluation_admissible"] is True


def test_no_candidate_v2_strategy_modules_required() -> None:
    assert not (ROOT / "src/strategies/step29m_trend_following_v2.py").exists()
    assert not (ROOT / "src/strategies/step29m_bollinger_bands_v2.py").exists()
    assert not (ROOT / "src/strategies/step29m_momentum_1h_v2.py").exists()
