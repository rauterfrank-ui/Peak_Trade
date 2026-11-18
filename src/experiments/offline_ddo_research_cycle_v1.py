"""Run bounded native research from verified offline DDO evidence."""

from __future__ import annotations

import platform
from dataclasses import replace
from pathlib import Path
from typing import Any, Literal

import pandas as pd
from pydantic import BaseModel, ConfigDict, Field

from src.backtest.mv2_research_wiring_v1 import (
    STEP29L_INSTRUMENT_ADMISSION_BTC_DEMO_V1,
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
from src.experiments.canonical_research_result_to_meta_input_v1 import ResearchResultMetaInputV1
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


def _instrument_admission(request):
    return (
        STEP29L_INSTRUMENT_ADMISSION_BTC_DEMO_V1
        if request.observed_surface == "TESTNET"
        else _ADMISSION
    )


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


class ResearchFollowUpTimesV1(_RequestModel):
    meta: str
    search: str
    measurement: str


class ResearchGapDimensionV1(_RequestModel):
    name: str = Field(min_length=1)
    expected: float = Field(allow_inf_nan=False)
    observed: float = Field(allow_inf_nan=False)
    threshold: float = Field(ge=0, allow_inf_nan=False)
    unit: str = Field(min_length=1)


class _ResearchInputsV1(_RequestModel):
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
    gap_dimensions: list[ResearchGapDimensionV1]
    observed_surface: Literal["SHADOW", "PAPER_EXCHANGE", "TESTNET"]
    threshold_policy_digest: str
    protected_digest_baseline: ProtectedSemanticDigestsV1
    times: ResearchCycleTimesV1


class OfflineDdoResearchRequestV1(_ResearchInputsV1):
    schema_version: Literal["offline_ddo_research_request.v1"]
    learning_evidence_digest: str


class OfflineDdoResearchProfileV1(_ResearchInputsV1):
    schema_version: Literal["offline_ddo_research_profile.v1"]
    follow_up_times: ResearchFollowUpTimesV1
    campaign_meta: str | None = Field(default=None, exclude=True)


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
            instrument_admission_mode=_instrument_admission(request),
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
    request: OfflineDdoResearchRequestV1 | OfflineDdoResearchProfileV1,
    bars: pd.DataFrame,
    cfg: dict[str, Any],
    code: CanonicalCodeProvenanceV1,
) -> dict[str, Any]:
    """Consume one completed DDO cycle and a bounded request or research profile."""
    if request.observed_surface == "TESTNET":
        raise ValueError("OFFLINE_RESEARCH_TESTNET_CONFIRMED_ENTRY_REQUIRED")
    evidence = export_completed_offline_learning_evidence_v1(
        root, cycle_key, plan_digest=plan_digest
    )
    return _run_research(
        root,
        cycle_key,
        binding={"plan_digest": plan_digest},
        evidence=evidence,
        request=request,
        bars=bars,
        cfg=cfg,
        code=code,
    )


def run_offline_shadow_ddo_research_cycle_v1(
    root: Path,
    cycle_key: str,
    *,
    handoff: dict[str, Any],
    request: OfflineDdoResearchRequestV1 | OfflineDdoResearchProfileV1,
    bars: pd.DataFrame,
    cfg: dict[str, Any],
    code: CanonicalCodeProvenanceV1,
    campaign_history: tuple[ResearchResultMetaInputV1, ...] = (),
    shadow_measurement: dict[str, Any] | None = None,
    campaign_regions: tuple[dict[str, Any], ...] = (),
) -> dict[str, Any]:
    """Run the existing search and GVEF from a reverified I17 handoff."""
    evidence = handoff["learning_evidence"]
    provenance = evidence["outcome_evidence_provenance"]
    if (
        handoff["schema_version"] != "i17_shadow_ddo_learning_result_v1"
        or handoff["authority"] != "NONE"
        or handoff["source_class"] not in {"TEST_ONLY_SYNTHETIC", "DECLARED_OFFLINE_DATA"}
        or request.observed_surface != "SHADOW"
        or (
            handoff["source_class"] == "TEST_ONLY_SYNTHETIC"
            and request.evidence_source_class != "TEST_ONLY_SYNTHETIC"
        )
        or provenance["outcome_semantic_class"] != "SHADOW_COUNTERFACTUAL"
        or provenance["decision_source"] != "I17_SHADOW_OBS"
        or provenance["market_observation_source"] != "PUBLIC_MD"
        or provenance["fill_source_type"] != "NO_FILL"
        or provenance["lineage_digest"] != handoff["outcome_receipt_digest"]
    ):
        raise ValueError("OFFLINE_RESEARCH_I17_SHADOW_HANDOFF_MISMATCH")
    binding = {
        "shadow_handoff_digest": require_sha256_hex(
            handoff["handoff_digest"], field="shadow_handoff_digest"
        ),
        "shadow_outcome_receipt_digest": handoff["outcome_receipt_digest"],
    }
    if shadow_measurement is not None:
        if (
            shadow_measurement["exact_content_digest"] != handoff["outcome_receipt_digest"]
            or shadow_measurement["shadow_decision"]["decision_event_ref"]
            != provenance["decision_event_ref"]
        ):
            raise ValueError("OFFLINE_RESEARCH_SHADOW_MEASUREMENT_BINDING_MISMATCH")
        market = shadow_measurement["market_observation"]["measurement"]
        if (
            market["outcome_scalar_kind"] != "LOG_RETURN"
            or provenance["evaluation_horizon"] != "N_BARS"
            or market["n_bars"] != shadow_measurement["market_observation"]["request"]["n_bars"]
        ):
            raise ValueError("OFFLINE_RESEARCH_SHADOW_MEASUREMENT_SEMANTICS_MISMATCH")
        binding["shadow_log_return"] = {
            "value": market["log_return"],
            "horizon_start_time_utc": market["horizon_start_time_utc"],
            "evaluation_time_utc": market["evaluation_time_utc"],
            "n_bars": market["n_bars"],
        }
    return _run_research(
        root,
        cycle_key,
        binding=binding,
        evidence=evidence,
        request=request,
        bars=bars,
        cfg=cfg,
        code=code,
        campaign_history=campaign_history,
        campaign_regions=campaign_regions,
        allow_unmeasured_reality_gap=True,
    )


def run_offline_paper_ddo_research_cycle_v1(
    root: Path,
    cycle_key: str,
    *,
    handoff: dict[str, Any],
    request: OfflineDdoResearchRequestV1 | OfflineDdoResearchProfileV1,
    bars: pd.DataFrame,
    cfg: dict[str, Any],
    code: CanonicalCodeProvenanceV1,
    campaign_history: tuple[ResearchResultMetaInputV1, ...] = (),
    paper_fee_observation: dict[str, Any] | None = None,
    campaign_regions: tuple[dict[str, Any], ...] = (),
) -> dict[str, Any]:
    """Connect the verified Paper owner to the existing offline research worker."""
    evidence = handoff["learning_evidence"]
    measurement = handoff["measurement"]
    provenance = evidence["outcome_evidence_provenance"]
    if (
        handoff["schema"] != "paper_episode_learning_handoff.v1"
        or handoff["authority"] != "NONE"
        or measurement["authority"] != "NONE"
        or measurement["execution_environment"] != "INTERNAL_SIMULATED_EXECUTION"
        or request.observed_surface != "PAPER_EXCHANGE"
        or provenance["outcome_semantic_class"] != "PAPER_SIMULATED_POSITION_OUTCOME"
        or provenance["evaluation_horizon"] != "SIMULATED_POSITION_LIFECYCLE"
        or provenance["outcome_scalar_kind"] != "NET_PNL_QUOTE_CURRENCY"
        or provenance["instrument_id"] != measurement["instrument_id"]
        or provenance["lineage_digest"] != measurement["outcome_digest"]
        or handoff["optimization_admission"]["learning_evidence_digest"] != evidence["content_hash"]
    ):
        raise ValueError("OFFLINE_RESEARCH_PAPER_HANDOFF_MISMATCH")
    if request.gap_dimensions:
        from src.backtest.cost_config_v0 import resolve_effective_backtest_cost_config

        if paper_fee_observation is None or len(request.gap_dimensions) != 1:
            raise ValueError("OFFLINE_RESEARCH_PAPER_GAP_SOURCE_REQUIRED")
        (dimension,) = request.gap_dimensions
        policy = paper_fee_observation["threshold_policy"]
        if (
            policy
            != {
                "authority": "NONE",
                "dimension": "fee",
                "scope": "SIMULATED_FILL_FEE_MODEL_PARITY",
                "threshold_bps": dimension.threshold,
            }
            or digest_v1(policy) != request.threshold_policy_digest
            or dimension.name != "fee"
            or dimension.unit != "bps"
            or dimension.expected != resolve_effective_backtest_cost_config(cfg).taker_fee_bps
            or dimension.observed != float(paper_fee_observation["fee_basis_points"])
            or paper_fee_observation["fees"] != measurement["fees"]
            or paper_fee_observation["currency"] != measurement["currency"]
        ):
            raise ValueError("OFFLINE_RESEARCH_PAPER_GAP_SEMANTICS_MISMATCH")
    return _run_research(
        root,
        cycle_key,
        binding={
            "paper_outcome_digest": require_sha256_hex(
                measurement["outcome_digest"], field="paper_outcome_digest"
            ),
            "paper_episode_id": measurement["episode_id"],
            "paper_archive_manifest_sha256": measurement["archive_manifest_sha256"],
            "paper_net_pnl": {
                "value": measurement["simulated_net_pnl"],
                "currency": measurement["currency"],
            },
            "paper_fee_observation": paper_fee_observation,
        },
        evidence=evidence,
        request=request,
        bars=bars,
        cfg=cfg,
        code=code,
        campaign_history=campaign_history,
        campaign_regions=campaign_regions,
        allow_unmeasured_reality_gap=True,
    )


def run_offline_testnet_ddo_research_cycle_v1(
    root: Path,
    cycle_key: str,
    *,
    handoff: dict[str, Any],
    request: OfflineDdoResearchRequestV1 | OfflineDdoResearchProfileV1,
    bars: pd.DataFrame,
    cfg: dict[str, Any],
    code: CanonicalCodeProvenanceV1,
    campaign_history: tuple[ResearchResultMetaInputV1, ...] = (),
    campaign_regions: tuple[dict[str, Any], ...] = (),
) -> dict[str, Any]:
    """Connect confirmed Demo-entry evidence to the bounded GVEF replay."""
    evidence = handoff["learning_evidence"]
    fill = handoff["measurement"]
    provenance = evidence["outcome_evidence_provenance"]
    if (
        handoff["schema"] != "btc_demo_entry_learning_handoff.v1"
        or fill["authority"] != "NONE"
        or fill["execution_environment"] != "TESTNET"
        or request.observed_surface != "TESTNET"
        or request.gap_dimensions
        or provenance["outcome_semantic_class"] != "TESTNET_VENUE_EVIDENCE"
        or provenance["fill_source_type"] != "VENUE_TESTNET"
        or provenance["outcome_source"] != "V2_CONFIRMED_TESTNET_ENTRY"
        or provenance["decision_event_ref"] != handoff["decision_event_ref"]
        or provenance["instrument_id"] != fill["instrument_id"]
        or provenance["lineage_digest"] != fill["source_digest"]
    ):
        raise ValueError("OFFLINE_RESEARCH_TESTNET_HANDOFF_MISMATCH")
    return _run_research(
        root,
        cycle_key,
        binding={"confirmed_testnet_entry": fill},
        evidence=evidence,
        request=request,
        bars=bars,
        cfg=cfg,
        code=code,
        campaign_history=campaign_history,
        campaign_regions=campaign_regions,
        allow_unmeasured_reality_gap=True,
    )


def _run_research(
    root,
    cycle_key,
    *,
    binding,
    evidence,
    request,
    bars,
    cfg,
    code,
    campaign_history=(),
    campaign_regions=(),
    allow_unmeasured_reality_gap=False,
):
    admission = dict(
        validate_canonical_optimization_universe_learning_input_v1(
            CanonicalOptimizationUniverseLearningInputRequestV1(evidence)
        )
    )
    if admission["status"] != STATUS_ACCEPTED_OFFLINE_RESEARCH_INPUT:
        raise ValueError("OFFLINE_RESEARCH_LEARNING_EVIDENCE_NOT_ADMITTED")
    instrument_id = evidence["outcome_evidence_provenance"]["instrument_id"]
    if request.instrument_id != instrument_id or (
        isinstance(request, OfflineDdoResearchRequestV1)
        and request.learning_evidence_digest != evidence["content_hash"]
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

    profile = request if isinstance(request, OfflineDdoResearchProfileV1) else None
    if profile is not None:
        request = OfflineDdoResearchRequestV1.model_validate(
            {
                **profile.model_dump(exclude={"follow_up_times"}),
                **hashes,
                "schema_version": "offline_ddo_research_request.v1",
                "learning_evidence_digest": evidence["content_hash"],
                "instrument_id": instrument_id,
            }
        )
    times = [
        learning_event_time_key_v0(require_iso8601_utc_z(value, field=name))
        for name, value in request.times.model_dump().items()
    ]
    if profile is not None:
        times.extend(
            learning_event_time_key_v0(require_iso8601_utc_z(value, field=f"follow_up_{name}"))
            for name, value in profile.follow_up_times.model_dump().items()
        )
    campaign_meta = profile.campaign_meta if profile is not None else None
    if campaign_meta is not None:
        times.insert(
            0,
            learning_event_time_key_v0(require_iso8601_utc_z(campaign_meta, field="campaign_meta")),
        )
    if times != sorted(set(times)) or times[0] <= learning_event_time_key_v0(
        evidence["observed_at_utc"]
    ):
        raise ValueError("OFFLINE_RESEARCH_TIME_ORDER_MISMATCH")
    if bool(campaign_meta) != bool(campaign_history):
        raise ValueError("OFFLINE_RESEARCH_CAMPAIGN_META_TIME_MISMATCH")
    _require_dataset_time(bars, request)
    require_sha256_hex(request.threshold_policy_digest, field="threshold_policy_digest")
    if len({value.name for value in request.gap_dimensions}) != len(request.gap_dimensions):
        raise ValueError("OFFLINE_RESEARCH_DUPLICATE_GAP_DIMENSION")
    if not request.gap_dimensions and not allow_unmeasured_reality_gap:
        raise ValueError("OFFLINE_RESEARCH_REALITY_GAP_EVIDENCE_REQUIRED")

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
            instrument_admission_mode=_instrument_admission(request),
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
        **binding,
        "learning_evidence": evidence,
        "optimization_admission": admission,
        "request": request.model_dump(mode="json"),
        "identity": encode_request_value_v1(identity),
        "source_tree_digest": source_digest,
        "authority": "NONE",
    }
    if profile is not None:
        bound["profile_digest"] = digest_v1(profile.model_dump(mode="json"))
        bound["follow_up_times"] = profile.follow_up_times.model_dump(mode="json")
    if campaign_history:
        bound["campaign_meta_at"] = campaign_meta
        bound["campaign_history"] = [
            {
                "experiment_id": unit.research_loop_record["selected_experiment_id"],
                "result_sha256": unit.research_loop_record["integrity"]["content_sha256"],
            }
            for unit in campaign_history
        ]
    if campaign_regions:
        bound["campaign_regions"] = list(campaign_regions)

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
            follow_up_times=profile.follow_up_times if profile is not None else None,
            campaign_history=campaign_history,
            campaign_meta=campaign_meta,
            campaign_regions=campaign_regions,
            allow_unmeasured_reality_gap=allow_unmeasured_reality_gap and not gaps,
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
    follow_up_times,
    campaign_history,
    campaign_meta,
    campaign_regions,
    allow_unmeasured_reality_gap,
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
        instrument_admission_mode=_instrument_admission(request),
        allow_unmeasured_reality_gap=allow_unmeasured_reality_gap,
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
        "campaign_regions": campaign_regions,
    }
    first = run_native_research_session_step_v1(
        search_request=first_search,
        provider=provider,
        prior_artifact_ids=(),
        campaign_history=campaign_history,
        meta_created_at=campaign_meta,
        meta_policy=canonical_meta_learning_policy_v1() if campaign_history else None,
        **step_args,
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
    if follow_up_times is not None:
        result["follow_up"] = None
    if campaign_history:
        result["campaign_meta_feedback"] = canonical_record_payload_v1(first.feedback_record)
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
            if follow_up_times is not None:
                result["follow_up"] = _run_follow_up(
                    workspace,
                    result["request_digest"],
                    evaluation,
                    artifact_ids=(first.artifact_id, second.artifact_id),
                    times=follow_up_times,
                    search=next_search,
                    provider=provider,
                    step_args=step_args,
                )
                if evaluation["mechanism_status"] == "INCOMPLETE":
                    result["status"] = "MECHANISM_INCOMPLETE"
                    return result

    result_path = workspace.safe_path_v1("result.json")
    publish_v1(result_path, result)
    return read_v1(result_path)


def _run_follow_up(
    workspace, request_digest, evaluation, *, artifact_ids, times, search, provider, step_args
):
    # The replay owner supplies this verdict only after verifying the saved receipt
    # against the plan and the original numeric packets.
    decision = {
        "schema_version": "offline_ddo_research_follow_up_decision.v1",
        "request_digest": request_digest,
        "evaluation": evaluation,
        "prior_artifact_ids": list(artifact_ids),
        "action": "SEARCH_ONCE" if evaluation["mechanism_status"] == "PASS" else "HOLD",
        "authority": "NONE",
    }
    path = workspace.safe_path_v1(
        Path("follow-up-decisions") / (evaluation["receipt_id"] + ".json")
    )
    publish_v1(path, decision)
    decision = read_v1(path)
    if decision["action"] == "HOLD":
        return {
            "decision": decision,
            "status": "WAITING_FOR_EVALUATION"
            if evaluation["mechanism_status"] == "INCOMPLETE"
            else "HELD_BY_EVALUATION",
        }
    step = run_native_research_session_step_v1(
        search_request=replace(search, created_at=times.search),
        provider=replace(provider, context=replace(provider.context, created_at=times.measurement)),
        prior_artifact_ids=artifact_ids,
        continuation_artifact_ids=artifact_ids,
        meta_created_at=times.meta,
        meta_policy=canonical_meta_learning_policy_v1(),
        **step_args,
    )
    return {
        "decision": decision,
        "status": "MEASURED" if step.artifact_id is not None else "SEARCH_EXHAUSTED",
        "artifact_id": step.artifact_id,
        "search": canonical_record_payload_v1(step.search_record),
        "meta_feedback": canonical_record_payload_v1(step.feedback_record),
    }
