"""Phase 22 incremental research evidence and authority-negative tests."""

from __future__ import annotations

from pathlib import Path

import pytest

from src.experiments.canonical_optimization_universe_mi_enriched_m4_intake_v1 import (
    MiEnrichedM4IntakeRequestV1,
    run_mi_enriched_optimization_universe_experiment_plane_v1,
)
from src.learning.market_intelligence_forecast_calibration_offline_stack_v1.incremental_information_set_v1 import (
    STAGE_B0,
    STAGE_B1,
    STAGE_B2,
    STAGE_B5,
)
from src.learning.market_intelligence_forecast_calibration_offline_stack_v1.phase_22_incremental_research_evidence_v1 import (
    IncrementalStageResearchRequestV1,
    ResearchDisposition,
    assert_phase_22_authority_invariants_v1,
    run_incremental_stage_research_v1,
    run_phase_22_incremental_research_closure_v1,
)
from tests.experiments.test_canonical_optimization_universe_mi_enriched_m4_intake_v1 import (
    _intake_request,
)
from tests.learning.test_incremental_information_set_v1 import (
    _full_source_context,
    _info_set,
    _slot,
)
from src.learning.market_intelligence_forecast_calibration_offline_stack_v1.market_context_v1 import (
    GovernedMarketContextInputsV1,
    MICROSTRUCTURE_KIND_PROXY_OHLCV,
    compose_market_context_v1_from_governed_inputs,
)

_OBS = "2026-09-01T12:00:00Z"
_INST = "inst-eth-usdt-perp"
_HORIZON = {"n_bars": 2, "bar_spec_ref": "bar.spec.test"}


def test_authority_negative_terminal_invariants() -> None:
    terminal = assert_phase_22_authority_invariants_v1()
    assert terminal["OPTIMIZATION_PROMOTION_AUTHORITY"] == "NONE"
    assert terminal["NO_FEATURE_ADMISSION_BY_AVAILABILITY"] is True
    assert terminal["CROSS_MARKET_IS_CONTEXT_ONLY"] is True
    assert terminal["META_EVIDENCE_AUTHORITY"] == "NONE"


def test_b0_baseline_anchor_without_plane() -> None:
    result = run_incremental_stage_research_v1(
        IncrementalStageResearchRequestV1(
            stage_id=STAGE_B0,
            source_market_context=_full_source_context(),
            horizon_identity=_HORIZON,
            feature_versions={"fixture": "v1"},
            provenance_refs=["mi.provenance.phase22.test"],
        )
    )
    assert result["research_disposition"] == ResearchDisposition.BASELINE_ANCHOR.value
    assert result["incremental_comparison"] is None


def test_b5_deferred_disposition() -> None:
    result = run_incremental_stage_research_v1(
        IncrementalStageResearchRequestV1(
            stage_id=STAGE_B5,
            source_market_context=_full_source_context(),
            horizon_identity=_HORIZON,
            feature_versions={"fixture": "v1"},
            provenance_refs=["mi.provenance.phase22.test"],
        )
    )
    assert result["research_disposition"] == ResearchDisposition.DEFERRED.value


def test_b2_insufficient_when_derivatives_missing_in_source() -> None:
    source = compose_market_context_v1_from_governed_inputs(
        GovernedMarketContextInputsV1(
            observed_at=_OBS,
            instrument_ref=_INST,
            information_set_identity_body={"fixture": "no_deriv"},
            provenance_refs=["mi.provenance.phase22.test"],
            feature_versions={"fixture": "v1"},
            price_state=_slot("price.phase22"),
            flow_state=_slot("flow.phase22"),
            liquidity_microstructure_state=_slot(
                "micro.phase22", micro_kind=MICROSTRUCTURE_KIND_PROXY_OHLCV
            ),
            derivatives_state=None,
        )
    )
    b1 = run_incremental_stage_research_v1(
        IncrementalStageResearchRequestV1(
            stage_id=STAGE_B1,
            source_market_context=dict(source),
            horizon_identity=_HORIZON,
            feature_versions={"fixture": "v1"},
            provenance_refs=["mi.provenance.phase22.test"],
        )
    )
    b2 = run_incremental_stage_research_v1(
        IncrementalStageResearchRequestV1(
            stage_id=STAGE_B2,
            source_market_context=dict(source),
            horizon_identity=_HORIZON,
            feature_versions={"fixture": "v1"},
            provenance_refs=["mi.provenance.phase22.test"],
            predecessor_stage_result=dict(b1),
        )
    )
    assert b2["research_disposition"] == ResearchDisposition.INSUFFICIENT_EVIDENCE.value
    assert b2["missing_family"] == "DERIVATIVES_STATE"


def test_incremental_stage_with_m4_plane_and_meta_compat(tmp_path: Path) -> None:
    intake = _intake_request(tmp_path)
    plane = run_mi_enriched_optimization_universe_experiment_plane_v1(intake)
    b0 = run_incremental_stage_research_v1(
        IncrementalStageResearchRequestV1(
            stage_id=STAGE_B0,
            source_market_context=_full_source_context(),
            horizon_identity=_HORIZON,
            feature_versions={"fixture": "v1"},
            provenance_refs=["mi.provenance.phase22.test"],
            plane_intake=intake,
        )
    )
    b1 = run_incremental_stage_research_v1(
        IncrementalStageResearchRequestV1(
            stage_id=STAGE_B1,
            source_market_context=_full_source_context(),
            horizon_identity=_HORIZON,
            feature_versions={"fixture": "v1"},
            provenance_refs=["mi.provenance.phase22.test"],
            plane_intake=MiEnrichedM4IntakeRequestV1(
                market_intelligence_research_evidence=intake.market_intelligence_research_evidence,
                plane_request=intake.plane_request,
                legacy_learning_evidence=intake.legacy_learning_evidence,
            ),
            predecessor_stage_result=dict(b0),
        )
    )
    assert plane["status"] == "PLANE_OFFLINE_CHAIN_COMPLETE"
    assert b1["research_disposition"] in {
        ResearchDisposition.INCREMENTAL_VALUE_SUPPORTED.value,
        ResearchDisposition.NO_INCREMENTAL_VALUE_SUPPORTED.value,
        ResearchDisposition.SEMANTICALLY_UNRESOLVED.value,
    }
    assert b1["incremental_comparison"] is not None
    assert b1["incremental_comparison"]["predecessor_stage_id"] == STAGE_B0
    if b1["meta_ingest_status"] is not None:
        assert b1["meta_ingest_status"]["status"] == "META_LEARNING_INGEST_COMPLETE"


def test_closure_runs_predecessor_ordered_chain() -> None:
    source = _full_source_context()
    closure = run_phase_22_incremental_research_closure_v1(
        stage_requests=[
            IncrementalStageResearchRequestV1(
                stage_id=STAGE_B0,
                source_market_context=source,
                horizon_identity=_HORIZON,
                feature_versions={"fixture": "v1"},
                provenance_refs=["mi.provenance.phase22.test"],
            ),
            IncrementalStageResearchRequestV1(
                stage_id=STAGE_B5,
                source_market_context=source,
                horizon_identity=_HORIZON,
                feature_versions={"fixture": "v1"},
                provenance_refs=["mi.provenance.phase22.test"],
            ),
        ]
    )
    stages = [item["stage_id"] for item in closure["stage_results"]]
    assert stages == [STAGE_B0, STAGE_B5]
    assert closure["stage_results"][1]["research_disposition"] == ResearchDisposition.DEFERRED.value


def test_dataset_identity_deterministic() -> None:
    first = run_incremental_stage_research_v1(
        IncrementalStageResearchRequestV1(
            stage_id=STAGE_B0,
            source_market_context=_full_source_context(),
            horizon_identity=_HORIZON,
            feature_versions={"fixture": "v1"},
            provenance_refs=["mi.provenance.phase22.test"],
        )
    )
    second = run_incremental_stage_research_v1(
        IncrementalStageResearchRequestV1(
            stage_id=STAGE_B0,
            source_market_context=_full_source_context(),
            horizon_identity=_HORIZON,
            feature_versions={"fixture": "v1"},
            provenance_refs=["mi.provenance.phase22.test"],
        )
    )
    d1 = first["dataset_identity"]
    d2 = second["dataset_identity"]
    assert d1["dataset_identity_id"] == d2["dataset_identity_id"]
