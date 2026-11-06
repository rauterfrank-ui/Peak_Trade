"""Contract tests for MI-enriched M4 optimization intake v1."""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

from src.experiments.canonical_optimization_experiment_evidence_v1 import (
    build_optimization_experiment_evidence_from_plane_v1,
)
from src.experiments.canonical_optimization_universe_experiment_plane_v1 import (
    PLANE_STATUS_COMPLETE,
    PROPOSAL_DISPOSITION,
)
from src.experiments.canonical_optimization_universe_mi_enriched_m4_intake_v1 import (
    INTAKE_STATUS_ACCEPTED,
    INTAKE_STATUS_REJECTED_MI_INPUT,
    MiEnrichedM4IntakeError,
    MiEnrichedM4IntakeRequestV1,
    run_mi_enriched_optimization_universe_experiment_plane_v1,
    validate_mi_enriched_m4_intake_v1,
)
from src.experiments.canonical_m9_volatility_numeric_max_age_optimizable_surface_v1 import (
    SURFACE_ID as M9_SURFACE_ID,
)
from src.governance.optimization_proposal_governance_ingress_v1 import (
    DISPOSITION_PROPOSAL_ONLY,
    build_optimization_proposal_governance_ingress_from_plane_and_evidence_v1,
)
from src.learning.deterministic_decision_outcome_v0.learning_evidence_export_v1 import (
    export_learning_evidence_from_state_v1,
)
from src.learning.market_intelligence_forecast_calibration_offline_stack_v1.mi_research_evidence_v1 import (
    project_market_intelligence_research_evidence_v1,
)
from tests.experiments.test_canonical_optimization_universe_experiment_plane_v1 import (
    _plane_request,
)
from tests.learning.test_learning_evidence_export_v1 import _learning_state
from tests.learning.test_unified_blueprint_phase_8_mi_to_learning_integration_v1 import (
    _mint_forecast,
    _observation_for_n,
)
from src.learning.market_intelligence_forecast_calibration_offline_stack_v1.calibration_evidence_v1 import (
    build_calibration_evidence_v1,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = (
    REPO_ROOT
    / "src"
    / "experiments"
    / "canonical_optimization_universe_mi_enriched_m4_intake_v1.py"
)


def _mi_research_bundle() -> tuple[dict, dict]:
    obs = _observation_for_n(n_bars=2)
    forecast = _mint_forecast(n_bars=2, bar_spec_ref=str(obs["bar_spec_ref"]))
    calib = dict(
        build_calibration_evidence_v1(
            forecast_evidence=forecast,
            evaluation_observation=obs,
            realized_direction="UP",
        )
    )
    projection = dict(
        project_market_intelligence_research_evidence_v1(
            forecast_evidence=forecast,
            calibration_evidence=calib,
        )
    )
    return projection, forecast


def _intake_request(tmp_path: Path) -> MiEnrichedM4IntakeRequestV1:
    legacy = export_learning_evidence_from_state_v1(_learning_state(tmp_path))
    projection, _ = _mi_research_bundle()
    return MiEnrichedM4IntakeRequestV1(
        market_intelligence_research_evidence=projection,
        plane_request=_plane_request(legacy),
        legacy_learning_evidence=legacy,
    )


def test_valid_mi_input_reaches_m4_plane(tmp_path: Path) -> None:
    plane = run_mi_enriched_optimization_universe_experiment_plane_v1(_intake_request(tmp_path))
    assert plane["status"] == PLANE_STATUS_COMPLETE
    chain = plane["chain"]
    assert chain["mi_lineage_refs"]["forecast_evidence_id"]
    assert chain["mi_enriched_m4_intake"]["status"] == INTAKE_STATUS_ACCEPTED
    assert chain["challenger_evaluation"]
    assert chain["proposal"]["disposition"] == PROPOSAL_DISPOSITION


def test_malformed_mi_input_fails_closed(tmp_path: Path) -> None:
    req = _intake_request(tmp_path)
    bad = dict(req.market_intelligence_research_evidence)
    bad["schema_version"] = "bad"
    intake = validate_mi_enriched_m4_intake_v1(
        MiEnrichedM4IntakeRequestV1(
            market_intelligence_research_evidence=bad,
            plane_request=req.plane_request,
            legacy_learning_evidence=req.legacy_learning_evidence,
        )
    )
    assert intake["status"] == INTAKE_STATUS_REJECTED_MI_INPUT


def test_mi_lineage_in_optimization_experiment_evidence(tmp_path: Path) -> None:
    plane = run_mi_enriched_optimization_universe_experiment_plane_v1(_intake_request(tmp_path))
    opt_evidence = build_optimization_experiment_evidence_from_plane_v1(plane)
    economic = opt_evidence["evidence_slices"]["ECONOMIC_EVIDENCE"]
    assert (
        economic["mi_enriched_lineage_digest"]
        == plane["chain"]["mi_lineage_refs"]["lineage_digest"]
    )
    assert opt_evidence["provenance"]["mi_lineage_refs"]["forecast_evidence_id"]


def test_proposal_only_ingress_with_m9_surface(tmp_path: Path) -> None:
    plane = run_mi_enriched_optimization_universe_experiment_plane_v1(_intake_request(tmp_path))
    opt_evidence = build_optimization_experiment_evidence_from_plane_v1(plane)
    ingress = build_optimization_proposal_governance_ingress_from_plane_and_evidence_v1(
        plane_result=plane,
        optimization_experiment_evidence=opt_evidence,
        optimization_surface_id=M9_SURFACE_ID,
        parameter_config_delta={"max_age_seconds": 300},
    )
    assert ingress["disposition"] == DISPOSITION_PROPOSAL_ONLY


def test_productive_join_rejected(tmp_path: Path) -> None:
    req = _intake_request(tmp_path)
    with pytest.raises(MiEnrichedM4IntakeError, match="PRODUCTIVE_JOIN"):
        validate_mi_enriched_m4_intake_v1(
            MiEnrichedM4IntakeRequestV1(
                market_intelligence_research_evidence=req.market_intelligence_research_evidence,
                plane_request=req.plane_request,
                legacy_learning_evidence=req.legacy_learning_evidence,
                requested_productive_join=True,
            )
        )


def test_deterministic_replay(tmp_path: Path) -> None:
    first = run_mi_enriched_optimization_universe_experiment_plane_v1(_intake_request(tmp_path))
    second = run_mi_enriched_optimization_universe_experiment_plane_v1(_intake_request(tmp_path))
    assert first["plane_identity"] == second["plane_identity"]
    assert first["result_digest"] == second["result_digest"]


def test_ddo_plane_path_unchanged_without_mi_intake(tmp_path: Path) -> None:
    legacy = export_learning_evidence_from_state_v1(_learning_state(tmp_path))
    from src.experiments.canonical_optimization_universe_experiment_plane_v1 import (
        run_optimization_universe_experiment_plane_v1,
    )

    plane = run_optimization_universe_experiment_plane_v1(_plane_request(legacy))
    assert plane["status"] == PLANE_STATUS_COMPLETE
    assert "mi_lineage_refs" not in plane["chain"]


def test_module_has_no_network_or_order_paths() -> None:
    tree = ast.parse(MODULE_PATH.read_text(encoding="utf-8"))
    joined = ast.unparse(tree)
    for token in ("requests.", "httpx", "submit_order", "place_order", "urllib"):
        assert token not in joined
