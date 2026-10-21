"""Optimization calibration keeps reachability, coverage, and ratification open."""

from __future__ import annotations

from scripts.ops.optimization_guardian_calibration_v1.calibrate_v1 import (
    run_optimization_calibration_v1,
)
from scripts.ops.optimization_guardian_scope_v1.scope_v1 import OPEN_FINDINGS


def test_three_instruments_stay_unratified(tmp_path) -> None:
    result = run_optimization_calibration_v1(output_dir=tmp_path / "b3")

    assert result["authority"] == "NONE"
    assert result["membership_ratified"] is False
    assert result["guardian_ratified"] is False
    assert result["prelude_ok"] is True
    assert result["prelude_current_verified"] is False
    assert result["prelude_edge_count"] > 0
    assert result["ghv_status"] == "ACCEPTED"
    assert result["ghv_authority"] == "NONE"
    assert result["ghv_coverage_gap"] is True
    assert result["ghv_observation_coverage_gap"] is True
    assert result["ghv_coverage_proof"] is False
    assert result["graph_status"] == "CURRENT_RELEVANCE_FAILURE"
    assert result["graph_integrator_invoked"] is True
    assert result["graph_global_causal_closure_proven"] is False
    assert str(result["graph_output_dir"]).startswith(str(tmp_path))
    assert result["ghosv_status"] == "ACCEPTED"
    assert result["ghosv_observation_proof"] is False
    assert result["ghosv_authority"] == "NONE"
    assert result["open_findings"] == OPEN_FINDINGS
    assert result["unresolved_kept"] is True
    assert result["f1_m9_out_of_scope"] is True
    assert result["instrument_ids"] == {
        "DOMAIN_GHV": "PARENT_OPTIMIZATION_GHV",
        "DOMAIN_CURRENT_CAUSAL_GRAPH": "PARENT_OPTIMIZATION_CURRENT_CAUSAL_GRAPH",
        "DOMAIN_GHOSV": "PARENT_OPTIMIZATION_GHOSV",
    }
    assert result["instrument_bound"] is True
    assert result["domain_bound"] is True
    assert result["domain_calibrated"] is False
    assert result["current_validated"] is False
    assert result["operationally_ready"] is False
    assert result["technical_state"] == "DOMAIN_BOUND"
    assert result["ghv_forward_traversal_completed"] is True
    assert result["ghv_forward_reachability_proven"] is False
    assert result["ghv_forward_coverage_gap"] is True
    assert result["ghv_causal_closure_proven"] is False
    assert result["full_core_reference"]["projected"] is True
    assert result["full_core_reference"]["causal_isolation"] == "NOT_PROVEN"
    assert result["full_core_reference"]["reachability"] == "UNKNOWN"
