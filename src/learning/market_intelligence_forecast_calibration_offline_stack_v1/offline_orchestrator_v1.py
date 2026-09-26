"""Deterministic offline MI orchestrator — composition only (no productive runtime)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Final, Mapping, Sequence

from src.experiments.canonical_failure_memory_store_v1 import CanonicalFailureMemoryStoreV1
from src.experiments.canonical_failure_memory_v1 import (
    CanonicalFailureMemoryRecordRequestV1,
    build_canonical_failure_memory_record_v1,
)
from src.learning.deterministic_decision_outcome_v0.drift_contracts_v0 import (
    validate_drift_assessment_record_v0,
)
from src.learning.deterministic_decision_outcome_v0.learning_evidence_export_v1 import (
    export_learning_evidence_from_state_v1,
)
from src.learning.market_intelligence_forecast_calibration_offline_stack_v1.calibration_evidence_v1 import (
    build_calibration_evidence_v1,
)
from src.learning.market_intelligence_forecast_calibration_offline_stack_v1.constants_v1 import (
    EXTERNAL_EFFECT_AUTHORIZED,
    RUNTIME_REACHABILITY,
    STACK_DOMAIN,
    WORKPACKAGE_ID,
)
from src.learning.market_intelligence_forecast_calibration_offline_stack_v1.decision_attribution_query_v1 import (
    query_market_intelligence_decision_attribution_v1,
)
from src.learning.market_intelligence_forecast_calibration_offline_stack_v1.forecast_evidence_v1 import (
    mint_forecast_evidence_v1,
    validate_forecast_evidence_v1,
)
from src.learning.market_intelligence_forecast_calibration_offline_stack_v1.forecast_outcome_join_v1 import (
    assert_n_bars_observation_unmodified_v1,
)
from src.learning.market_intelligence_forecast_calibration_offline_stack_v1.mi_optimization_research_input_v1 import (
    MarketIntelligenceOptimizationResearchInputRequestV1,
    validate_market_intelligence_optimization_research_input_v1,
)
from src.learning.market_intelligence_forecast_calibration_offline_stack_v1.mi_learning_evidence_learning_export_v1 import (
    export_mi_learning_evidence_onto_learning_path_v1,
)
from src.learning.market_intelligence_forecast_calibration_offline_stack_v1.mi_to_learning_evidence_bridge_v1 import (
    compose_mi_to_learning_evidence_v1,
)
from src.learning.market_intelligence_forecast_calibration_offline_stack_v1.mi_research_evidence_v1 import (
    project_market_intelligence_research_evidence_v1,
)
from src.learning.market_intelligence_forecast_calibration_offline_stack_v1.probabilistic_forecast_payload_v1 import (
    FORECAST_KIND_DIRECTIONAL_PROBABILITY,
)
from src.learning.market_intelligence_forecast_calibration_offline_stack_v1.support_disposition_v1 import (
    SUPPORT_INSUFFICIENT_EVIDENCE,
    SUPPORT_SUFFICIENT_EVIDENCE,
)
from src.experiments.canonical_optimization_universe_experiment_plane_v1 import (
    OptimizationUniverseExperimentPlaneRequestV1,
)
from src.experiments.canonical_optimization_universe_mi_enriched_m4_intake_v1 import (
    MiEnrichedM4ClosureRequestV1,
    MiEnrichedM4IntakeRequestV1,
    run_mi_enriched_m4_optimization_closure_v1,
)

ORCHESTRATOR_ID: Final[str] = (
    "peak_trade.learning.market_intelligence_forecast_calibration_offline_orchestrator_v1"
)
ORCHESTRATOR_SCHEMA: Final[str] = "market_intelligence_offline_orchestrator_cycle_v1"


@dataclass(frozen=True)
class OfflineForecastScenarioV1:
    information_set_ref: str
    forecast_created_at_utc: str
    outcome_horizon_end_utc: str
    n_bars: int
    bar_spec_ref: str
    market_state_refs: Sequence[str]
    forecast_model_ref: str
    probabilistic_payload: Mapping[str, Any]
    support_disposition: str = SUPPORT_SUFFICIENT_EVIDENCE
    realized_direction: str | None = None


@dataclass(frozen=True)
class OfflineOrchestratorInputV1:
    scenarios: Sequence[OfflineForecastScenarioV1]
    evaluation_observations_by_n_bars: Mapping[int, Mapping[str, Any]]
    learning_state_record: Mapping[str, Any] | None = None
    attribution_record: Mapping[str, Any] | None = None
    drift_assessments: Sequence[Mapping[str, Any]] | None = None
    failure_memory_store_root: Any | None = None
    failure_memory_request: CanonicalFailureMemoryRecordRequestV1 | None = None
    m4_experiment_plane_request: OptimizationUniverseExperimentPlaneRequestV1 | None = None
    run_mi_enriched_m4_closure: bool = False


def run_market_intelligence_offline_orchestrator_cycle_v1(
    request: OfflineOrchestratorInputV1,
) -> dict[str, Any]:
    if RUNTIME_REACHABILITY or EXTERNAL_EFFECT_AUTHORIZED:
        raise RuntimeError("OFFLINE_ORCHESTRATOR_RUNTIME_FORBIDDEN")

    drift_refs: list[str] = []
    for item in request.drift_assessments or ():
        assessment = validate_drift_assessment_record_v0(item)
        drift_refs.append(str(assessment["record_id"]))

    legacy_learning = None
    if request.learning_state_record is not None:
        legacy_learning = export_learning_evidence_from_state_v1(request.learning_state_record)

    forecasts: list[dict[str, Any]] = []
    calibrations: list[dict[str, Any]] = []
    projections: list[dict[str, Any]] = []
    mi_learning_exports: list[dict[str, Any]] = []

    for scenario in request.scenarios:
        forecast = mint_forecast_evidence_v1(
            information_set_ref=scenario.information_set_ref,
            forecast_created_at_utc=scenario.forecast_created_at_utc,
            outcome_horizon_end_utc=scenario.outcome_horizon_end_utc,
            n_bars=scenario.n_bars,
            bar_spec_ref=scenario.bar_spec_ref,
            forecast_kind=FORECAST_KIND_DIRECTIONAL_PROBABILITY,
            probabilistic_payload=scenario.probabilistic_payload,
            market_state_refs=scenario.market_state_refs,
            forecast_model_ref=scenario.forecast_model_ref,
            support_disposition=scenario.support_disposition,
            provenance={"orchestrator_id": ORCHESTRATOR_ID, "workpackage_id": WORKPACKAGE_ID},
            drift_assessment_refs=drift_refs,
        )
        validate_forecast_evidence_v1(forecast)
        obs = request.evaluation_observations_by_n_bars.get(scenario.n_bars)
        if obs is not None:
            before = dict(obs)
            calib = build_calibration_evidence_v1(
                forecast_evidence=forecast,
                evaluation_observation=obs,
                realized_direction=scenario.realized_direction,
            )
            assert_n_bars_observation_unmodified_v1(before, obs)
        else:
            calib = build_calibration_evidence_v1(
                forecast_evidence=forecast,
                evaluation_observation=None,
            )
        projection = project_market_intelligence_research_evidence_v1(
            forecast_evidence=forecast,
            calibration_evidence=calib,
            drift_assessment_refs=drift_refs,
            legacy_learning_evidence_ref=(
                str(legacy_learning["record_id"]) if legacy_learning is not None else None
            ),
        )
        forecasts.append(dict(forecast))
        calibrations.append(dict(calib))
        projections.append(dict(projection))
        mi_learning = compose_mi_to_learning_evidence_v1(
            forecast_evidence=forecast,
            evaluation_observation=obs,
            realized_direction=scenario.realized_direction,
            legacy_learning_evidence_ref=(
                str(legacy_learning["record_id"]) if legacy_learning is not None else None
            ),
            provenance={"orchestrator_id": ORCHESTRATOR_ID},
        )
        mi_learning_exports.append(
            dict(
                export_mi_learning_evidence_onto_learning_path_v1(
                    mi_learning,
                    legacy_learning_evidence=legacy_learning,
                )
            )
        )

    optimization_acks = [
        dict(
            validate_market_intelligence_optimization_research_input_v1(
                MarketIntelligenceOptimizationResearchInputRequestV1(
                    market_intelligence_research_evidence=projection,
                    legacy_learning_evidence=legacy_learning,
                )
            )
        )
        for projection in projections
    ]

    attribution = query_market_intelligence_decision_attribution_v1(
        attribution_record=request.attribution_record,
        forecast_evidence=forecasts[0] if forecasts else None,
        calibration_evidence=calibrations[0] if calibrations else None,
    )

    failure_memory_trace: dict[str, Any] | None = None
    if request.failure_memory_store_root is not None and request.failure_memory_request is not None:
        failure_memory_trace = compose_failure_memory_offline_iteration_v1(
            store_root=request.failure_memory_store_root,
            request=request.failure_memory_request,
        )

    mi_enriched_m4_closure = None
    if (
        request.run_mi_enriched_m4_closure
        and request.m4_experiment_plane_request is not None
        and legacy_learning is not None
        and projections
    ):
        mi_enriched_m4_closure = dict(
            run_mi_enriched_m4_optimization_closure_v1(
                MiEnrichedM4ClosureRequestV1(
                    intake_request=MiEnrichedM4IntakeRequestV1(
                        market_intelligence_research_evidence=projections[0],
                        plane_request=request.m4_experiment_plane_request,
                        legacy_learning_evidence=legacy_learning,
                        mi_learning_evidence_export=(
                            mi_learning_exports[0] if mi_learning_exports else None
                        ),
                    )
                )
            )
        )

    return {
        "schema_name": ORCHESTRATOR_SCHEMA,
        "domain": STACK_DOMAIN,
        "orchestrator_id": ORCHESTRATOR_ID,
        "forecasts": forecasts,
        "calibrations": calibrations,
        "research_projections": projections,
        "optimization_research_input_acks": optimization_acks,
        "mi_enriched_m4_closure": mi_enriched_m4_closure,
        "decision_attribution_query": dict(attribution),
        "legacy_learning_evidence": legacy_learning,
        "mi_learning_evidence_exports": mi_learning_exports,
        "failure_memory_replay": failure_memory_trace,
        "runtime_reachability": False,
        "external_effect_authorized": False,
    }


def compose_failure_memory_offline_iteration_v1(
    *,
    store_root: Any,
    request: CanonicalFailureMemoryRecordRequestV1,
) -> dict[str, Any]:
    store = CanonicalFailureMemoryStoreV1(store_root)
    record = build_canonical_failure_memory_record_v1(request)
    fingerprint = str(record["hypothesis_fingerprint"])
    duplicate_before = store.assess_duplicate(hypothesis_fingerprint=fingerprint)
    appended = store.append(record)
    duplicate_after = store.assess_duplicate(hypothesis_fingerprint=fingerprint)
    replay_store = CanonicalFailureMemoryStoreV1(store_root)
    first_list = replay_store.list_records()
    second_list = replay_store.list_records()
    return {
        "duplicate_before_append": dict(duplicate_before),
        "duplicate_after_append": dict(duplicate_after),
        "append_count": len(first_list),
        "deterministic_replay_equal": first_list == second_list,
        "failure_record_id": appended.get("failure_record_id"),
    }
