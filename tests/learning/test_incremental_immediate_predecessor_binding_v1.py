"""Immediate-predecessor labels must name the stage result actually consumed."""
import pytest

from src.learning.market_intelligence_forecast_calibration_offline_stack_v1.phase_22_incremental_research_evidence_v1 import (
    IncrementalStageResearchRequestV1, Phase22IncrementalResearchError,
    run_incremental_stage_research_v1, run_phase_22_incremental_research_closure_v1,
)
from tests.learning.test_phase_22_incremental_research_evidence_v1 import _full_source_context, _HORIZON


def _request(stage, predecessor=None):
    return IncrementalStageResearchRequestV1(stage_id=stage, source_market_context=_full_source_context(),
        horizon_identity=_HORIZON, feature_versions={"fixture":"v1"}, provenance_refs=["test.predecessor"],
        predecessor_stage_result=predecessor)


def test_direct_wrong_predecessor_cannot_be_labeled_as_immediate():
    b0 = run_incremental_stage_research_v1(_request("B0"))
    with pytest.raises(Phase22IncrementalResearchError, match="PREDECESSOR_STAGE_MISMATCH"):
        run_incremental_stage_research_v1(_request("B2", dict(b0)))


def test_ordered_but_gapped_chain_is_rejected():
    with pytest.raises(Phase22IncrementalResearchError, match="PREDECESSOR_STAGE_MISMATCH"):
        run_phase_22_incremental_research_closure_v1(stage_requests=[_request("B0"), _request("B2")])


def test_duplicate_baseline_is_not_a_valid_chain():
    with pytest.raises(Phase22IncrementalResearchError, match="BASELINE_PREDECESSOR_FORBIDDEN"):
        run_phase_22_incremental_research_closure_v1(stage_requests=[_request("B0"), _request("B0")])


def test_contiguous_chain_binds_actual_information_set():
    result = run_phase_22_incremental_research_closure_v1(stage_requests=[_request("B0"), _request("B1")])
    b0, b1 = result["stage_results"]
    comparison = b1["incremental_comparison"]
    assert comparison["predecessor_stage_id"] == b0["stage_id"]
    assert comparison["predecessor_information_set_id"] == b0["information_set"]["information_set_id"]


def test_absent_predecessor_remains_explicitly_insufficient():
    result = run_incremental_stage_research_v1(_request("B1"))
    assert result["research_disposition"] == "INSUFFICIENT_EVIDENCE"
    assert result["incremental_comparison"] is None
