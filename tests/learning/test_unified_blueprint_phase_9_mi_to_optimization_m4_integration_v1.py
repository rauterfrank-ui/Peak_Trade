"""Phase 9 — orchestrator MI research input → M4 → optimization evidence (offline)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from src.experiments.canonical_m9_volatility_numeric_max_age_optimizable_surface_v1 import (
    SURFACE_ID as M9_SURFACE_ID,
)
from src.experiments.canonical_optimization_universe_experiment_plane_v1 import (
    PLANE_STATUS_COMPLETE,
)
from src.governance.optimization_proposal_governance_ingress_v1 import (
    ADMISSION_ADMITTED,
    DISPOSITION_PROPOSAL_ONLY,
    OptimizationProposalGovernanceAdmissionRequestV1,
    evaluate_optimization_proposal_governance_admission_v1,
    build_optimization_proposal_governance_ingress_from_plane_and_evidence_v1,
)
from src.learning.deterministic_decision_outcome_v0.learning_evidence_export_v1 import (
    export_learning_evidence_from_state_v1,
)
from src.learning.market_intelligence_forecast_calibration_offline_stack_v1.constants_v1 import (
    CAP23_SOLE_PRODUCTIVE_SELECTION_OWNER,
    MASTER_V2_DOUBLE_PLAY_SOLE_TRADING_AUTHORITY,
)
from src.learning.market_intelligence_forecast_calibration_offline_stack_v1.offline_orchestrator_v1 import (
    OfflineForecastScenarioV1,
    OfflineOrchestratorInputV1,
    run_market_intelligence_offline_orchestrator_cycle_v1,
)
from tests.experiments.test_canonical_optimization_universe_experiment_plane_v1 import (
    _plane_request,
)
from tests.learning.test_learning_evidence_export_v1 import _learning_state
from tests.learning.test_unified_blueprint_phase_8_mi_to_learning_integration_v1 import (
    _directional_payload,
    _observation_for_n,
)


def _scenario() -> OfflineForecastScenarioV1:
    obs = _observation_for_n(n_bars=2)
    return OfflineForecastScenarioV1(
        information_set_ref="info.set.phase9",
        forecast_created_at_utc="2026-09-01T12:00:00Z",
        outcome_horizon_end_utc="2026-09-01T14:00:00Z",
        n_bars=2,
        bar_spec_ref=str(obs["bar_spec_ref"]),
        market_state_refs=["mi.state.phase9"],
        forecast_model_ref="mi.model.offline.v1",
        probabilistic_payload=_directional_payload(),
        realized_direction="UP",
    )


def test_orchestrator_reaches_m4_and_proposal_ingress(tmp_path: Path) -> None:
    obs = _observation_for_n(n_bars=2)
    legacy_state = _learning_state(tmp_path)
    legacy = export_learning_evidence_from_state_v1(legacy_state)
    result: dict[str, Any] = run_market_intelligence_offline_orchestrator_cycle_v1(
        OfflineOrchestratorInputV1(
            scenarios=[_scenario()],
            evaluation_observations_by_n_bars={2: obs},
            learning_state_record=legacy_state,
            m4_experiment_plane_request=_plane_request(legacy),
            run_mi_enriched_m4_closure=True,
        )
    )
    assert result["optimization_research_input_acks"]
    closure = result["mi_enriched_m4_closure"]
    assert closure is not None
    plane = closure["plane_result"]
    assert plane["status"] == PLANE_STATUS_COMPLETE
    opt_evidence = closure["optimization_experiment_evidence"]
    assert opt_evidence is not None
    assert opt_evidence["provenance"]["mi_lineage_refs"]["forecast_evidence_id"]

    ingress = build_optimization_proposal_governance_ingress_from_plane_and_evidence_v1(
        plane_result=plane,
        optimization_experiment_evidence=opt_evidence,
        optimization_surface_id=M9_SURFACE_ID,
        parameter_config_delta={"max_age_seconds": 300},
    )
    assert ingress["disposition"] == DISPOSITION_PROPOSAL_ONLY
    admission = evaluate_optimization_proposal_governance_admission_v1(
        OptimizationProposalGovernanceAdmissionRequestV1(ingress=ingress)
    )
    assert admission.admission_status == ADMISSION_ADMITTED
    assert admission.promotion_authority == "NONE"
    assert result["external_effect_authorized"] is False
    assert MASTER_V2_DOUBLE_PLAY_SOLE_TRADING_AUTHORITY is True
    assert CAP23_SOLE_PRODUCTIVE_SELECTION_OWNER is True
