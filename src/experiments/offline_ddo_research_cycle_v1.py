"""Run two explicitly bounded native research steps from verified offline DDO evidence."""

from __future__ import annotations

import platform
from dataclasses import replace
from pathlib import Path
from typing import Any, Literal

import pandas as pd
from pydantic import BaseModel, ConfigDict, Field

from src.backtest.mv2_research_wiring_v1 import (
    STEP29L_INSTRUMENT_ADMISSION_CURRENT_SELECTED_INSTRUMENT_V1,
)
from src.evaluation.golden_vectors.contracts.models import ProtectedSemanticDigestsV1
from src.evaluation.golden_vectors.contracts.serialization import (
    require_iso8601_utc_z,
    require_sha256_hex,
)
from src.evaluation.golden_vectors.integration.domain_result_binding_v1 import source_tree_digest_v1
from src.evaluation.golden_vectors.integration.evaluation_receipt_v1 import (
    EvaluationReceiptArchiveV1,
)
from src.evaluation.golden_vectors.integration.offline_native_learning_replay_v1 import (
    evaluate_offline_native_learning_replay_v1,
)
from src.experiments.canonical_advanced_search_v1 import (
    SEARCH_METHOD_BOUNDED_DETERMINISTIC_CONSTRAINED_REGION_SEARCH,
    SEARCH_METHOD_VERSION,
    CanonicalAdvancedSearchRequestV1,
    SearchAxisV1,
    SearchSpaceV1,
    build_canonical_advanced_search_v1,
    canonical_advanced_search_constraint_v1,
    canonical_advanced_search_objective_v1,
    canonical_record_payload_v1,
)
from src.experiments.canonical_experiment_identity_v1 import (
    CanonicalCodeProvenanceV1,
    CanonicalExperimentIdentityRequestV1,
)
from src.experiments.canonical_experiment_memory_store_v1 import CanonicalExperimentMemoryStoreV1
from src.experiments.canonical_failure_memory_store_v1 import CanonicalFailureMemoryStoreV1
from src.experiments.canonical_meta_learning_v1 import canonical_meta_learning_policy_v1
from src.experiments.canonical_native_research_measurements_v1 import (
    NativeResearchExecutionContextV1,
    NativeResearchExperimentProviderV1,
    NativeResearchMeasurementsV1,
    native_research_identity_sources_v1,
    native_research_input_hashes_v1,
)
from src.experiments.canonical_native_research_session_v1 import (
    NativeResearchExecutionArchiveV1,
    measure_native_research_champion_v1,
    run_native_research_session_step_v1,
)
from src.experiments.canonical_optimization_universe_learning_input_v1 import (
    STATUS_ACCEPTED_OFFLINE_RESEARCH_INPUT,
    CanonicalOptimizationUniverseLearningInputRequestV1,
    validate_canonical_optimization_universe_learning_input_v1,
)
from src.experiments.canonical_reality_gap_store_persist_v1 import CanonicalRealityGapStoreV1
from src.experiments.canonical_reality_gap_store_v1 import RealityGapDimensionV1
from src.experiments.canonical_research_prepared_execution_v1 import (
    decode_request_value_v1,
    digest_v1,
    encode_request_value_v1,
    publish_v1,
    read_v1,
)
from src.experiments.canonical_robustness_suite_v1 import (
    canonical_robustness_policy_v1,
    derive_robustness_policy_digest_v1,
)
from src.learning.deterministic_decision_outcome_v0.learning_state_record_v0 import (
    learning_event_time_key_v0,
)
from src.learning.deterministic_decision_outcome_v0.offline_learning_follow_up_v1 import (
    export_completed_offline_learning_evidence_v1,
)

_ADMISSION = STEP29L_INSTRUMENT_ADMISSION_CURRENT_SELECTED_INSTRUMENT_V1
_PROVIDER = "OfflineDdoResearchCycleV1.NativeResearchExperimentProviderV1"


class _RequestModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)


class ResearchIdentitySourcesV1(_RequestModel):
    feature_pipeline_digest: str
    market_context_contract_digest: str
    bull_bear_logic_digest: str
    state_switch_logic_digest: str
    survival_logic_digest: str
    suitability_logic_digest: str
    double_play_logic_digest: str
    entry_position_exit_logic_digest: str


class ResearchCycleTimesV1(_RequestModel):
    baseline_search: str
    baseline_measurement: str
    first_search: str
    first_measurement: str
    meta: str
    next_search: str
    next_measurement: str
    evaluation: str


class ResearchGapDimensionV1(_RequestModel):
    name: str = Field(min_length=1)
    expected: float = Field(allow_inf_nan=False)
    observed: float = Field(allow_inf_nan=False)
    threshold: float = Field(ge=0, allow_inf_nan=False)
    unit: str = Field(min_length=1)


class OfflineDdoResearchRequestV1(_RequestModel):
    schema_version: Literal["offline_ddo_research_request.v1"]
    learning_evidence_digest: str
    instrument_id: str
    strategy_id: str
    strategy_version: str
    dataset_sha256: str
    config_sha256: str
    bars_known_at: str
    evidence_source_class: Literal["TEST_ONLY_SYNTHETIC", "DECLARED_OFFLINE_DATA"]
    identity_sources: ResearchIdentitySourcesV1
    search_space_id: str
    parent_hypothesis_id: str
    hypothesis_kind: str
    regime: str
    seed: int
    first_axes: dict[str, list[int | float | str | bool]]
    next_axes: dict[str, list[int | float | str | bool]]
    search_space_cardinality_limit: int = Field(ge=1, le=128)
    market_universe: list[str] = Field(min_length=1)
    gap_dimensions: list[ResearchGapDimensionV1] = Field(min_length=1)
    observed_surface: Literal["SHADOW", "PAPER_EXCHANGE"]
    threshold_policy_digest: str
    protected_digest_baseline: ProtectedSemanticDigestsV1
    times: ResearchCycleTimesV1


def _space(name, axes):
    return SearchSpaceV1(name, tuple(SearchAxisV1(key, axes[key]) for key in sorted(axes)))


def _require_dataset_time(bars, request):
    if (
        "is_final" not in bars
        or not pd.api.types.is_bool_dtype(bars["is_final"])
        or bars["is_final"].isna().any()
        or not bars["is_final"].all()
        or "bar_interval" not in bars
        or not bars["bar_interval"].notna().all()
        or bars["bar_interval"].nunique() != 1
    ):
        raise ValueError("EXPLICIT_FINAL_SINGLE_INTERVAL_BARS_REQUIRED")
    interval = pd.Timedelta(bars["bar_interval"].iloc[0])
    known_at = pd.Timestamp(require_iso8601_utc_z(request.bars_known_at, field="bars_known_at"))
    if (
        pd.isna(interval)
        or interval <= pd.Timedelta(0)
        or bars.index[-1] + interval > known_at
        or known_at > pd.Timestamp(request.times.baseline_search)
    ):
        raise ValueError("OFFLINE_RESEARCH_DATASET_TIME_MISMATCH")


def _searches(request, identity, policy, params):
    common = CanonicalAdvancedSearchRequestV1(
        identity_template=identity,
        search_space=_space(
            request.search_space_id, {name: [params[name]] for name in request.first_axes}
        ),
        search_method=SEARCH_METHOD_BOUNDED_DETERMINISTIC_CONSTRAINED_REGION_SEARCH,
        search_method_version=SEARCH_METHOD_VERSION,
        seed=request.seed,
        budget=1,
        search_space_cardinality_limit=request.search_space_cardinality_limit,
        objective=canonical_advanced_search_objective_v1(),
        constraint=canonical_advanced_search_constraint_v1(),
        created_at=request.times.baseline_search,
        parent_hypothesis_id=request.parent_hypothesis_id,
        lineage_kind="ROOT",
        hypothesis_kind=request.hypothesis_kind,
        strategy_family=request.strategy_id,
        regime=request.regime,
        robustness_policy_digest=derive_robustness_policy_digest_v1(policy),
    )
    return (
        common,
        replace(
            common,
            search_space=_space(request.search_space_id, request.first_axes),
            created_at=request.times.first_search,
        ),
        replace(
            common,
            search_space=_space(request.search_space_id, request.next_axes),
            created_at=request.times.next_search,
        ),
    )


def _baseline(path, search, *, bars, cfg, request, horizon, policy):
    if not path.exists():
        (baseline,) = (row for row in search["candidates"] if row["status"] == "PROPOSED")
        measured = measure_native_research_champion_v1(
            candidate=baseline,
            bars=bars,
            cfg=cfg,
            strategy_id=request.strategy_id,
            strategy_version=request.strategy_version,
            instrument_id=request.instrument_id,
            time_horizon=horizon,
            market_universe=request.market_universe,
            robustness_policy=policy,
            created_at=request.times.baseline_measurement,
            instrument_admission_mode=_ADMISSION,
        )
        publish_v1(
            path,
            {
                "candidate": encode_request_value_v1(measured.candidate),
                "observations": encode_request_value_v1(measured.measurements.observations),
                "receipt": canonical_record_payload_v1(measured.measurements.receipt),
                "robustness_evidence": canonical_record_payload_v1(measured.robustness_evidence),
            },
        )
    packet = read_v1(path)
    return (
        decode_request_value_v1(packet["candidate"], ()),
        NativeResearchMeasurementsV1(
            observations=decode_request_value_v1(packet["observations"], ()),
            receipt=packet["receipt"],
        ),
    )


def run_offline_ddo_research_cycle_v1(
    root: Path,
    cycle_key: str,
    *,
    plan_digest: str,
    request: OfflineDdoResearchRequestV1,
    bars: pd.DataFrame,
    cfg: dict[str, Any],
    code: CanonicalCodeProvenanceV1,
) -> dict[str, Any]:
    """Consume one completed DDO cycle and a separate offline research declaration."""
    evidence = export_completed_offline_learning_evidence_v1(
        root, cycle_key, plan_digest=plan_digest
    )
    admission = dict(
        validate_canonical_optimization_universe_learning_input_v1(
            CanonicalOptimizationUniverseLearningInputRequestV1(evidence)
        )
    )
    if admission["status"] != STATUS_ACCEPTED_OFFLINE_RESEARCH_INPUT:
        raise ValueError("OFFLINE_RESEARCH_LEARNING_EVIDENCE_NOT_ADMITTED")
    if (
        request.learning_evidence_digest != evidence["content_hash"]
        or request.instrument_id != evidence["outcome_evidence_provenance"]["instrument_id"]
    ):
        raise ValueError("OFFLINE_RESEARCH_REQUEST_LEARNING_BINDING_MISMATCH")
    if (
        not isinstance(bars.index, pd.DatetimeIndex)
        or bars.empty
        or bars.index.tz is None
        or bars.index.hasnans
        or not bars.index.is_unique
        or not bars.index.is_monotonic_increasing
    ):
        raise ValueError("ORDERED_UNIQUE_TIMEZONE_BOUND_BARS_REQUIRED")
    hashes = dict(native_research_input_hashes_v1(bars, cfg))
    if hashes != {"dataset_sha256": request.dataset_sha256, "config_sha256": request.config_sha256}:
        raise ValueError("OFFLINE_RESEARCH_INPUT_DIGEST_MISMATCH")

    times = [
        learning_event_time_key_v0(require_iso8601_utc_z(value, field=name))
        for name, value in request.times.model_dump().items()
    ]
    if times != sorted(set(times)) or times[0] <= learning_event_time_key_v0(
        evidence["observed_at_utc"]
    ):
        raise ValueError("OFFLINE_RESEARCH_TIME_ORDER_MISMATCH")
    _require_dataset_time(bars, request)
    require_sha256_hex(request.threshold_policy_digest, field="threshold_policy_digest")
    if len({value.name for value in request.gap_dimensions}) != len(request.gap_dimensions):
        raise ValueError("OFFLINE_RESEARCH_DUPLICATE_GAP_DIMENSION")

    params = cfg["economic_evaluation_v1"]["strategy_params"]
    identity = CanonicalExperimentIdentityRequestV1(
        git_sha=code.git_sha,
        working_tree_status=code.working_tree_status,
        dirty_paths_digest=code.dirty_paths_digest,
        strategy_identity=f"{request.strategy_id}.{request.strategy_version}",
        strategy_params=params,
        dataset_digest=request.dataset_sha256,
        seed=request.seed,
        environment={
            "python_version": platform.python_version(),
            "python_implementation": platform.python_implementation(),
        },
        parent_lineage_ref="ddo-learning-evidence:sha256:" + evidence["content_hash"],
        **request.identity_sources.model_dump(),
        **native_research_identity_sources_v1(
            cfg,
            instrument_id=request.instrument_id,
            bars=bars,
            instrument_admission_mode=_ADMISSION,
        ),
    )
    policy = canonical_robustness_policy_v1()
    baseline_search, first_search, next_search = _searches(request, identity, policy, params)
    baseline = build_canonical_advanced_search_v1(baseline_search)
    (baseline_candidate,) = (row for row in baseline["candidates"] if row["status"] == "PROPOSED")
    for search in (first_search, next_search):
        if any(
            row["experiment_id"] == baseline_candidate["experiment_id"]
            for row in build_canonical_advanced_search_v1(search)["candidates"]
        ):
            raise ValueError("OFFLINE_RESEARCH_SPACE_INCLUDES_BASELINE")
    gaps = tuple(RealityGapDimensionV1(**value.model_dump()) for value in request.gap_dimensions)
    utc_index = bars.index.tz_convert("UTC")
    horizon = {
        "start": utc_index[0].isoformat().replace("+00:00", "Z"),
        "end": utc_index[-1].isoformat().replace("+00:00", "Z"),
    }
    source_digest = source_tree_digest_v1()
    bound = {
        "schema_version": "offline_ddo_research_binding.v1",
        "plan_digest": plan_digest,
        "learning_evidence": evidence,
        "optimization_admission": admission,
        "request": request.model_dump(mode="json"),
        "identity": encode_request_value_v1(identity),
        "source_tree_digest": source_digest,
        "authority": "NONE",
    }

    directory = EvaluationReceiptArchiveV1(root).safe_path_v1(
        Path("offline-ddo-research") / cycle_key
    )
    workspace = EvaluationReceiptArchiveV1(directory)
    with workspace.lease_v1():
        return _execute(
            workspace,
            bound,
            request,
            bars=bars,
            cfg=cfg,
            identity=identity,
            baseline=baseline,
            first_search=first_search,
            next_search=next_search,
            gaps=gaps,
            horizon=horizon,
            policy=policy,
        )


def _execute(
    workspace,
    bound,
    request,
    *,
    bars,
    cfg,
    identity,
    baseline,
    first_search,
    next_search,
    gaps,
    horizon,
    policy,
):
    publish_v1(workspace.safe_path_v1("request.json"), bound)
    champion, measurements = _baseline(
        workspace.safe_path_v1("baseline.json"),
        baseline,
        bars=bars,
        cfg=cfg,
        request=request,
        horizon=horizon,
        policy=policy,
    )
    archive = NativeResearchExecutionArchiveV1(workspace.safe_path_v1("native-archive"))
    context = NativeResearchExecutionContextV1(
        identity_template=identity,
        champion=champion,
        champion_measurements=measurements,
        created_at=request.times.first_measurement,
        time_horizon=horizon,
        market_universe=request.market_universe,
        gap_dimensions=gaps,
        observed_surface=request.observed_surface,
        threshold_policy_digest=request.threshold_policy_digest,
        robustness_policy=policy,
        instrument_admission_mode=_ADMISSION,
        experiment_memory_store=CanonicalExperimentMemoryStoreV1(
            workspace.safe_path_v1("experiments")
        ),
        failure_memory_store=CanonicalFailureMemoryStoreV1(workspace.safe_path_v1("failures")),
        reality_gap_store=CanonicalRealityGapStoreV1(workspace.safe_path_v1("gaps")),
    )
    provider = NativeResearchExperimentProviderV1(
        bars, cfg, request.strategy_id, request.strategy_version, request.instrument_id, context
    )
    step_args = {
        "archive": archive,
        "provider_ref": _PROVIDER,
        "evidence_source_class": request.evidence_source_class,
    }
    first = run_native_research_session_step_v1(
        search_request=first_search, provider=provider, prior_artifact_ids=(), **step_args
    )
    result = {
        "schema_version": "offline_ddo_research_result.v1",
        "request_digest": digest_v1(bound),
        "learning_evidence_digest": request.learning_evidence_digest,
        "optimization_admission_digest": bound["optimization_admission"]["result_digest"],
        "baseline_measurement_digest": measurements.receipt["content_digest"],
        "first_artifact_id": first.artifact_id,
        "first_search": canonical_record_payload_v1(first.search_record),
        "next_artifact_id": None,
        "next_search": None,
        "meta_feedback": None,
        "evaluation": None,
        "status": "FIRST_SEARCH_EXHAUSTED",
        "authority": "NONE",
    }
    if first.artifact_id is not None:
        artifact_ids = (first.artifact_id,)
        second = run_native_research_session_step_v1(
            search_request=next_search,
            provider=replace(
                provider, context=replace(context, created_at=request.times.next_measurement)
            ),
            prior_artifact_ids=artifact_ids,
            continuation_artifact_ids=artifact_ids,
            meta_created_at=request.times.meta,
            meta_policy=canonical_meta_learning_policy_v1(),
            **step_args,
        )
        result.update(
            next_artifact_id=second.artifact_id,
            next_search=canonical_record_payload_v1(second.search_record),
            meta_feedback=canonical_record_payload_v1(second.feedback_record),
            status="NEXT_SEARCH_EXHAUSTED",
        )
        if second.artifact_id is not None:
            evaluation = evaluate_offline_native_learning_replay_v1(
                workspace.safe_path_v1("gvef"),
                archive=archive,
                first_id=first.artifact_id,
                next_id=second.artifact_id,
                bound=bound,
                seed=request.seed,
                created_at=request.times.evaluation,
                protected=request.protected_digest_baseline,
            )
            result.update(
                evaluation=evaluation,
                status="MECHANISM_PASS"
                if evaluation["mechanism_status"] == "PASS"
                else "MECHANISM_BLOCKED",
            )

    result_path = workspace.safe_path_v1("result.json")
    publish_v1(result_path, result)
    return read_v1(result_path)
