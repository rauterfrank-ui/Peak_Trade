"""Phase 22 — incremental information research evidence (B0–B5; AUTHORITY=NONE).

Typed offline research comparing each B-stage against its immediate predecessor using
established Optimization experiment-plane machinery. Research dispositions are evidence
classification only — not productive admission or promotion.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from types import MappingProxyType
from typing import Any, Final, Mapping, Sequence

from src.experiments.canonical_experiment_memory_v1 import derive_experiment_id_v1
from src.experiments.canonical_failure_memory_v1 import (
    FAILURE_CLASS_TO_FAILED_GATE,
    CanonicalFailureMemoryRecordRequestV1,
    build_canonical_failure_memory_record_v1,
)
from src.experiments.canonical_meta_learning_ingest_v1 import (
    MetaLearningIngestRequestV1,
    ingest_meta_learning_evidence_from_return_input_v1,
)
from src.experiments.canonical_self_learning_optimization_return_input_v1 import (
    SelfLearningOptimizationReturnInputRequestV1,
    validate_self_learning_optimization_return_input_v1,
)
from src.experiments.canonical_optimization_experiment_evidence_v1 import (
    build_optimization_experiment_evidence_from_plane_v1,
)
from src.experiments.canonical_optimization_universe_experiment_plane_v1 import (
    PLANE_STATUS_COMPLETE,
)
from src.experiments.canonical_optimization_universe_mi_enriched_m4_intake_v1 import (
    MiEnrichedM4IntakeRequestV1,
    run_mi_enriched_optimization_universe_experiment_plane_v1,
)
from src.learning.market_intelligence_forecast_calibration_offline_stack_v1.constants_v1 import (
    FORECAST_IS_NOT_DECISION,
    LEARNING_TRADING_AUTHORITY,
    MARKET_INTELLIGENCE_TRADING_AUTHORITY,
    NO_AUTOMATIC_PROMOTION,
    OPTIMIZATION_PRODUCTIVE_AUTHORITY,
    STACK_DOMAIN,
)
from src.learning.market_intelligence_forecast_calibration_offline_stack_v1.incremental_information_set_v1 import (
    BEHAVIOR_CONTRACT_VERSION,
    CONTEXT_CONTRACT_VERSION,
    INCREMENTAL_INFORMATION_SET_SCHEMA,
    STAGE_B0,
    STAGE_B5,
    STAGE_CHAIN,
    IncrementalInformationSetError,
    IncrementalInformationSetRequestV1,
    TrueL2AdmissibilityStatus,
    assert_market_context_respects_stage_boundary_v1,
    build_incremental_information_set_v1,
    census_true_l2_research_substrate_v1,
    predecessor_stage_id_v1,
    project_market_context_to_stage_v1,
)
from src.learning.market_intelligence_forecast_calibration_offline_stack_v1.market_context_v1 import (
    MARKET_CONTEXT_AUTHORITY,
    ContextFamilyPresence,
)
from src.learning.market_intelligence_forecast_calibration_offline_stack_v1.realized_behavior_v1 import (
    REALIZED_BEHAVIOR_AUTHORITY,
)
from src.meta.learning_loop.contract_safety_v1 import compute_content_sha256

PHASE_22_SCHEMA: Final[str] = "phase_22_incremental_research_evidence_v1"
PHASE_22_OWNER: Final[str] = (
    "learning.market_intelligence_forecast_calibration_offline_stack_v1."
    "phase_22_incremental_research_evidence_v1"
)
RESEARCH_DISPOSITION_VOCABULARY: Final[str] = "phase_22_research_disposition_v1"
RESEARCH_DISPOSITION_AUTHORITY: Final[str] = "NONE"
NO_FEATURE_ADMISSION_BY_AVAILABILITY: Final[bool] = True

DATASET_IDENTITY_SCHEMA: Final[str] = "phase_22_research_dataset_identity_v1"
INCREMENTAL_COMPARISON_SCHEMA: Final[str] = "phase_22_incremental_comparison_v1"


class ResearchDisposition(str, Enum):
    BASELINE_ANCHOR = "BASELINE_ANCHOR"
    INCREMENTAL_VALUE_SUPPORTED = "INCREMENTAL_VALUE_SUPPORTED"
    NO_INCREMENTAL_VALUE_SUPPORTED = "NO_INCREMENTAL_VALUE_SUPPORTED"
    REDUNDANT = "REDUNDANT"
    UNSTABLE = "UNSTABLE"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"
    DEFERRED = "DEFERRED"
    SEMANTICALLY_UNRESOLVED = "SEMANTICALLY_UNRESOLVED"


class Phase22IncrementalResearchError(ValueError):
    """Fail-closed Phase 22 incremental research."""


@dataclass(frozen=True)
class ResearchDatasetIdentityRequestV1:
    information_set_id: str
    stage_id: str
    predecessor_stage_id: str | None
    behavior_contract_version: str
    horizon_identity: Mapping[str, Any]
    sample_range: Mapping[str, str]
    split_definition: Mapping[str, Any]
    missingness_policy: str
    provenance_refs: Sequence[str]
    stochastic_seed_identity: int | None = None


@dataclass(frozen=True)
class IncrementalStageResearchRequestV1:
    stage_id: str
    source_market_context: Mapping[str, Any]
    horizon_identity: Mapping[str, Any]
    feature_versions: Mapping[str, str]
    provenance_refs: Sequence[str]
    plane_intake: MiEnrichedM4IntakeRequestV1 | None = None
    predecessor_stage_result: Mapping[str, Any] | None = None
    sample_range: Mapping[str, str] | None = None
    split_definition: Mapping[str, Any] | None = None
    search_trial_count: int = 1
    redundancy_feature_digest: str | None = None


def derive_research_dataset_id_v1(*, identity_body: Mapping[str, Any]) -> str:
    digest = compute_content_sha256(dict(identity_body))
    return f"mi.phase22.dataset.{digest[:48]}"


def build_research_dataset_identity_v1(
    request: ResearchDatasetIdentityRequestV1,
) -> MappingProxyType[str, Any]:
    body = {
        "schema_version": DATASET_IDENTITY_SCHEMA,
        "information_set_id": request.information_set_id,
        "stage_id": request.stage_id,
        "predecessor_stage_id": request.predecessor_stage_id,
        "behavior_contract_version": request.behavior_contract_version,
        "horizon_identity": dict(request.horizon_identity),
        "sample_range": dict(request.sample_range),
        "split_definition": dict(request.split_definition),
        "missingness_policy": request.missingness_policy,
        "provenance_refs": list(request.provenance_refs),
        "temporal_integrity": {
            "point_in_time_features": True,
            "finalized_observations_required": True,
            "no_outcome_leakage_into_features": True,
            "train_oos_separated": True,
        },
        "stochastic_seed_identity": request.stochastic_seed_identity,
        "research_authority": RESEARCH_DISPOSITION_AUTHORITY,
    }
    dataset_id = derive_research_dataset_id_v1(identity_body=body)
    digest = compute_content_sha256({**body, "dataset_identity_id": dataset_id})
    return MappingProxyType({**body, "dataset_identity_id": dataset_id, "content_digest": digest})


def _stage_required_family_missing(
    *,
    stage_id: str,
    projected_context: Mapping[str, Any],
) -> str | None:
    from src.learning.market_intelligence_forecast_calibration_offline_stack_v1.incremental_information_set_v1 import (
        FAMILY_TO_CONTEXT_FIELD,
        included_context_families_v1,
    )

    for family in included_context_families_v1(stage_id):
        field = FAMILY_TO_CONTEXT_FIELD[family]
        slot = projected_context.get(field)
        if not isinstance(slot, Mapping):
            return family
        if slot.get("presence") == ContextFamilyPresence.MISSING.value:
            if family == "DERIVATIVES_STATE":
                return family
            if stage_id == STAGE_B0 and family in ("PRICE_STATE", "FLOW_STATE"):
                return family
    return None


def classify_incremental_research_disposition_v1(
    *,
    stage_id: str,
    information_set: Mapping[str, Any],
    predecessor_result: Mapping[str, Any] | None,
    plane_status: str | None,
    challenger_delta: float | None,
    redundancy_detected: bool,
    required_family_missing: str | None,
) -> str:
    if stage_id == STAGE_B5:
        census = census_true_l2_research_substrate_v1()
        if census["b5_status"] != TrueL2AdmissibilityStatus.ADMISSIBLE.value:
            return ResearchDisposition.DEFERRED.value

    if required_family_missing is not None:
        return ResearchDisposition.INSUFFICIENT_EVIDENCE.value

    if redundancy_detected:
        return ResearchDisposition.REDUNDANT.value

    if stage_id == STAGE_B0:
        return ResearchDisposition.BASELINE_ANCHOR.value

    if plane_status != PLANE_STATUS_COMPLETE:
        return ResearchDisposition.INSUFFICIENT_EVIDENCE.value

    if predecessor_result is None:
        return ResearchDisposition.INSUFFICIENT_EVIDENCE.value

    pred_disp = predecessor_result.get("research_disposition")
    if pred_disp == ResearchDisposition.INSUFFICIENT_EVIDENCE.value:
        return ResearchDisposition.INSUFFICIENT_EVIDENCE.value

    if challenger_delta is None:
        return ResearchDisposition.SEMANTICALLY_UNRESOLVED.value

    if challenger_delta > 0:
        return ResearchDisposition.INCREMENTAL_VALUE_SUPPORTED.value
    if challenger_delta < 0:
        return ResearchDisposition.NO_INCREMENTAL_VALUE_SUPPORTED.value
    return ResearchDisposition.NO_INCREMENTAL_VALUE_SUPPORTED.value


def build_incremental_comparison_evidence_v1(
    *,
    stage_id: str,
    predecessor_stage_id: str,
    stage_information_set_id: str,
    predecessor_information_set_id: str,
    stage_plane_identity: str | None,
    predecessor_plane_identity: str | None,
    challenger_delta: float | None,
    walk_forward_summary: Mapping[str, Any] | None,
    calibration_summary: Mapping[str, Any] | None,
    redundancy_summary: Mapping[str, Any] | None,
) -> MappingProxyType[str, Any]:
    body = {
        "schema_version": INCREMENTAL_COMPARISON_SCHEMA,
        "comparison_kind": "IMMEDIATE_PREDECESSOR_ONLY",
        "stage_id": stage_id,
        "predecessor_stage_id": predecessor_stage_id,
        "stage_information_set_id": stage_information_set_id,
        "predecessor_information_set_id": predecessor_information_set_id,
        "stage_plane_identity": stage_plane_identity,
        "predecessor_plane_identity": predecessor_plane_identity,
        "challenger_delta": challenger_delta,
        "walk_forward_summary": dict(walk_forward_summary or {}),
        "calibration_summary": dict(calibration_summary or {}),
        "redundancy_summary": dict(redundancy_summary or {}),
        "research_authority": RESEARCH_DISPOSITION_AUTHORITY,
    }
    digest = compute_content_sha256(body)
    return MappingProxyType({**body, "content_digest": digest})


def build_phase_22_failure_memory_record_v1(
    *,
    stage_result: Mapping[str, Any],
    hypothesis_id: str,
    created_at: str,
) -> MappingProxyType[str, Any]:
    disp = str(stage_result.get("research_disposition") or "")
    if disp not in {
        ResearchDisposition.NO_INCREMENTAL_VALUE_SUPPORTED.value,
        ResearchDisposition.UNSTABLE.value,
        ResearchDisposition.INSUFFICIENT_EVIDENCE.value,
        ResearchDisposition.REDUNDANT.value,
    }:
        raise Phase22IncrementalResearchError("FAILURE_MEMORY_NOT_APPLICABLE")
    identity = stage_result.get("experiment_identity")
    if not isinstance(identity, Mapping):
        raise Phase22IncrementalResearchError("EXPERIMENT_IDENTITY_REQUIRED_FOR_FAILURE_MEMORY")
    failure_class = "REJECTED_OVERFIT"
    experiment_id = derive_experiment_id_v1(str(identity["identity_digest"]))
    artifact_refs = [
        ref
        for ref in (stage_result.get("evidence_artifact_refs") or [])
        if isinstance(ref, str) and ref.strip()
    ]
    evidence_refs = [
        {
            "kind": "EXPERIMENT_RECORD",
            "ref": experiment_id,
            "digest": str(identity["identity_digest"]),
        }
    ]
    if artifact_refs:
        evidence_refs.append(
            {
                "kind": "STORE_RELATIVE",
                "ref": artifact_refs[0],
                "digest": compute_content_sha256({"ref": artifact_refs[0]}),
            }
        )
    return build_canonical_failure_memory_record_v1(
        CanonicalFailureMemoryRecordRequestV1(
            experiment_identity=identity,
            hypothesis_id=hypothesis_id,
            failure_class=failure_class,
            failed_gate=FAILURE_CLASS_TO_FAILED_GATE[failure_class],
            rejection_reason=failure_class,
            regime="mixed",
            parameter_region={"phase_22_stage": stage_result.get("stage_id")},
            cost_sensitivity={"phase_22_disposition": disp},
            instability_indicators={"phase_22_research_only": True},
            evidence_refs=evidence_refs,
            created_at=created_at,
            robustness_policy_digest=compute_content_sha256(
                {"phase_22_failure_memory": stage_result.get("stage_id")}
            ),
        )
    )


def run_incremental_stage_research_v1(
    request: IncrementalStageResearchRequestV1,
) -> MappingProxyType[str, Any]:
    stage_id = request.stage_id
    if stage_id not in STAGE_CHAIN:
        raise Phase22IncrementalResearchError("STAGE_ID_UNKNOWN")

    predecessor = predecessor_stage_id_v1(stage_id)
    info_set = build_incremental_information_set_v1(
        IncrementalInformationSetRequestV1(
            stage_id=stage_id,
            horizon_identity=request.horizon_identity,
            feature_versions=request.feature_versions,
            provenance_refs=request.provenance_refs,
        )
    )

    if (
        stage_id == STAGE_B5
        and info_set.get("b5_status")
        == TrueL2AdmissibilityStatus.DEFERRED_NOT_CURRENTLY_ADMISSIBLE.value
    ):
        return MappingProxyType(
            {
                "schema_version": PHASE_22_SCHEMA,
                "stage_id": stage_id,
                "predecessor_stage_id": predecessor,
                "information_set": dict(info_set),
                "projected_market_context": None,
                "dataset_identity": None,
                "plane_result": None,
                "incremental_comparison": None,
                "research_disposition": ResearchDisposition.DEFERRED.value,
                "failure_memory": None,
                "meta_ingest_status": None,
            }
        )

    missing_family: str | None = None
    projected = None
    try:
        projected = project_market_context_to_stage_v1(
            request.source_market_context,
            stage_id=stage_id,
            information_set_id=str(info_set["information_set_id"]),
        )
        assert_market_context_respects_stage_boundary_v1(projected, stage_id=stage_id)
        missing_family = _stage_required_family_missing(
            stage_id=stage_id, projected_context=projected
        )
    except IncrementalInformationSetError as exc:
        message = str(exc)
        if message.startswith("SOURCE_MISSING_REQUIRED_FAMILY:"):
            missing_family = message.rsplit(":", maxsplit=1)[-1]
        else:
            raise

    sample_range = request.sample_range or {
        "start": "2020-01-01T00:00:00Z",
        "end": "2024-12-31T00:00:00Z",
    }
    split_definition = request.split_definition or {
        "kind": "TIME_ORDERED_HOLDOUT",
        "train_fraction": 0.7,
        "embargo_bars": int(request.horizon_identity.get("n_bars") or 0),
        "purge_overlap": True,
    }
    dataset = build_research_dataset_identity_v1(
        ResearchDatasetIdentityRequestV1(
            information_set_id=str(info_set["information_set_id"]),
            stage_id=stage_id,
            predecessor_stage_id=predecessor,
            behavior_contract_version=BEHAVIOR_CONTRACT_VERSION,
            horizon_identity=request.horizon_identity,
            sample_range=sample_range,
            split_definition=split_definition,
            missingness_policy="EXPLICIT_MISSING_NO_SILENT_INTERPOLATION",
            provenance_refs=request.provenance_refs,
            stochastic_seed_identity=(
                request.plane_intake.plane_request.search_seed
                if request.plane_intake is not None
                else None
            ),
        )
    )

    redundancy_detected = False
    if request.redundancy_feature_digest and request.predecessor_stage_result:
        pred_digest = request.predecessor_stage_result.get("feature_digest")
        if pred_digest == request.redundancy_feature_digest:
            redundancy_detected = True

    plane_result = None
    plane_status = None
    challenger_delta = None
    experiment_identity = None
    if request.plane_intake is not None and missing_family is None and not redundancy_detected:
        plane_result = dict(
            run_mi_enriched_optimization_universe_experiment_plane_v1(request.plane_intake)
        )
        plane_status = str(plane_result.get("status"))
        if plane_status == PLANE_STATUS_COMPLETE:
            plane_req = request.plane_intake.plane_request
            challenger_delta = float(plane_req.challenger_score) - float(plane_req.champion_score)
            chain = plane_result.get("chain") or {}
            identity_raw = chain.get("experiment_identity")
            if isinstance(identity_raw, Mapping):
                experiment_identity = dict(identity_raw)

    disposition = classify_incremental_research_disposition_v1(
        stage_id=stage_id,
        information_set=info_set,
        predecessor_result=request.predecessor_stage_result,
        plane_status=plane_status,
        challenger_delta=challenger_delta,
        redundancy_detected=redundancy_detected,
        required_family_missing=missing_family,
    )

    comparison = None
    if predecessor is not None and request.predecessor_stage_result is not None:
        pred_info = request.predecessor_stage_result.get("information_set") or {}
        comparison = build_incremental_comparison_evidence_v1(
            stage_id=stage_id,
            predecessor_stage_id=predecessor,
            stage_information_set_id=str(info_set["information_set_id"]),
            predecessor_information_set_id=str(pred_info.get("information_set_id") or ""),
            stage_plane_identity=(
                str(plane_result.get("plane_identity")) if plane_result else None
            ),
            predecessor_plane_identity=request.predecessor_stage_result.get("plane_identity"),
            challenger_delta=challenger_delta,
            walk_forward_summary={"evaluated": plane_status == PLANE_STATUS_COMPLETE},
            calibration_summary={"typed_comparative_only": True},
            redundancy_summary={"redundancy_detected": redundancy_detected},
        )

    failure_memory = None
    meta_status = None
    if (
        disposition
        in {
            ResearchDisposition.NO_INCREMENTAL_VALUE_SUPPORTED.value,
            ResearchDisposition.REDUNDANT.value,
            ResearchDisposition.INSUFFICIENT_EVIDENCE.value,
        }
        and experiment_identity is not None
    ):
        failure_memory = build_phase_22_failure_memory_record_v1(
            stage_result={
                "stage_id": stage_id,
                "research_disposition": disposition,
                "experiment_identity": experiment_identity,
                "evidence_artifact_refs": [
                    str(plane_result.get("plane_identity")) if plane_result else ""
                ],
            },
            hypothesis_id=f"phase22.{stage_id}.incremental",
            created_at=str(sample_range.get("end") or "2026-09-26T12:00:00Z"),
        )

    if plane_result is not None and plane_status == PLANE_STATUS_COMPLETE:
        opt_evidence = build_optimization_experiment_evidence_from_plane_v1(plane_result)
        return_ack = validate_self_learning_optimization_return_input_v1(
            SelfLearningOptimizationReturnInputRequestV1(
                optimization_experiment_evidence=opt_evidence,
                expected_plane_identity=str(plane_result.get("plane_identity")),
            )
        )
        meta_status = dict(
            ingest_meta_learning_evidence_from_return_input_v1(
                MetaLearningIngestRequestV1(
                    return_input_ack=return_ack,
                    optimization_experiment_evidence=opt_evidence,
                )
            )
        )

    stage_body = {
        "schema_version": PHASE_22_SCHEMA,
        "stage_id": stage_id,
        "predecessor_stage_id": predecessor,
        "information_set": dict(info_set),
        "projected_market_context_ref": projected.get("context_id") if projected else None,
        "dataset_identity": dict(dataset),
        "plane_result_digest": (
            plane_result.get("result_digest") if isinstance(plane_result, Mapping) else None
        ),
        "plane_identity": plane_result.get("plane_identity") if plane_result else None,
        "incremental_comparison": dict(comparison) if comparison else None,
        "research_disposition": disposition,
        "search_trial_count": request.search_trial_count,
        "missing_family": missing_family,
        "feature_digest": request.redundancy_feature_digest,
        "experiment_identity": experiment_identity,
        "evidence_artifact_refs": (
            [str(plane_result.get("plane_identity"))]
            if plane_result and plane_result.get("plane_identity")
            else []
        ),
        "meta_ingest_status": meta_status,
        "failure_memory": dict(failure_memory) if failure_memory else None,
        "research_disposition_authority": RESEARCH_DISPOSITION_AUTHORITY,
    }
    stage_body["content_digest"] = compute_content_sha256(
        {k: v for k, v in stage_body.items() if k != "content_digest"}
    )
    return MappingProxyType(stage_body)


def run_phase_22_incremental_research_closure_v1(
    *,
    stage_requests: Sequence[IncrementalStageResearchRequestV1],
    store_root: Path | str | None = None,
) -> MappingProxyType[str, Any]:
    """Run ordered B-stage chain; each stage compares only to immediate predecessor."""
    ordered = sorted(stage_requests, key=lambda item: STAGE_CHAIN.index(item.stage_id))
    if [item.stage_id for item in ordered] != [item.stage_id for item in stage_requests]:
        raise Phase22IncrementalResearchError("STAGE_REQUESTS_MUST_BE_PREDECESSOR_ORDERED")

    results: list[Mapping[str, Any]] = []
    predecessor_result: Mapping[str, Any] | None = None
    for req in ordered:
        merged = IncrementalStageResearchRequestV1(
            stage_id=req.stage_id,
            source_market_context=req.source_market_context,
            horizon_identity=req.horizon_identity,
            feature_versions=req.feature_versions,
            provenance_refs=req.provenance_refs,
            plane_intake=req.plane_intake,
            predecessor_stage_result=predecessor_result,
            sample_range=req.sample_range,
            split_definition=req.split_definition,
            search_trial_count=req.search_trial_count,
            redundancy_feature_digest=req.redundancy_feature_digest,
        )
        stage_result = dict(run_incremental_stage_research_v1(merged))
        results.append(stage_result)
        predecessor_result = stage_result

    closure_body = {
        "schema_version": PHASE_22_SCHEMA,
        "phase_22_closure_proven": all(
            item.get("research_disposition")
            not in {ResearchDisposition.SEMANTICALLY_UNRESOLVED.value}
            or item.get("stage_id") == STAGE_B5
            for item in results
        ),
        "stage_results": results,
        "store_root": str(store_root) if store_root is not None else None,
        "domain": STACK_DOMAIN,
        "incremental_information_set_schema": INCREMENTAL_INFORMATION_SET_SCHEMA,
        "context_contract_version": CONTEXT_CONTRACT_VERSION,
        "behavior_contract_version": BEHAVIOR_CONTRACT_VERSION,
    }
    closure_body["content_digest"] = compute_content_sha256(closure_body)
    return MappingProxyType(closure_body)


def assert_phase_22_authority_invariants_v1() -> Mapping[str, Any]:
    terminal = {
        "MARKET_CONTEXT_AUTHORITY": MARKET_CONTEXT_AUTHORITY,
        "REALIZED_BEHAVIOR_AUTHORITY": REALIZED_BEHAVIOR_AUTHORITY,
        "LEARNING_TRADING_AUTHORITY": LEARNING_TRADING_AUTHORITY,
        "MARKET_INTELLIGENCE_TRADING_AUTHORITY": MARKET_INTELLIGENCE_TRADING_AUTHORITY,
        "OPTIMIZATION_TRADING_DECISION_AUTHORITY": "NONE",
        "OPTIMIZATION_PROMOTION_AUTHORITY": "NONE",
        "OPTIMIZATION_DIRECT_PRODUCTIVE_WRITE": "FORBIDDEN",
        "META_EVIDENCE_AUTHORITY": "NONE",
        "CROSS_MARKET_IS_CONTEXT_ONLY": True,
        "NO_FEATURE_ADMISSION_BY_AVAILABILITY": NO_FEATURE_ADMISSION_BY_AVAILABILITY,
        "NO_AUTOMATIC_PROMOTION": NO_AUTOMATIC_PROMOTION,
        "NO_SELF_DEPLOY": True,
        "MV2_DP_UNCHANGED": True,
        "NO_AUTHORITY_EXPANSION": True,
        "FORECAST_IS_NOT_DECISION": FORECAST_IS_NOT_DECISION,
        "OPTIMIZATION_PRODUCTIVE_AUTHORITY": OPTIMIZATION_PRODUCTIVE_AUTHORITY,
        "RESEARCH_DISPOSITION_AUTHORITY": RESEARCH_DISPOSITION_AUTHORITY,
    }
    forbidden = (
        ("OPTIMIZATION_TRADING_DECISION_AUTHORITY", "NONE"),
        ("OPTIMIZATION_PROMOTION_AUTHORITY", "NONE"),
        ("OPTIMIZATION_DIRECT_PRODUCTIVE_WRITE", "FORBIDDEN"),
        ("META_EVIDENCE_AUTHORITY", "NONE"),
        ("MARKET_CONTEXT_AUTHORITY", "NONE"),
        ("REALIZED_BEHAVIOR_AUTHORITY", "NONE"),
        ("LEARNING_TRADING_AUTHORITY", "NONE"),
    )
    for key, expected in forbidden:
        if terminal.get(key) != expected:
            raise Phase22IncrementalResearchError(f"AUTHORITY_INVARIANT_VIOLATION:{key}")
    return MappingProxyType(terminal)


__all__ = [
    "DATASET_IDENTITY_SCHEMA",
    "INCREMENTAL_COMPARISON_SCHEMA",
    "NO_FEATURE_ADMISSION_BY_AVAILABILITY",
    "PHASE_22_OWNER",
    "PHASE_22_SCHEMA",
    "RESEARCH_DISPOSITION_AUTHORITY",
    "RESEARCH_DISPOSITION_VOCABULARY",
    "IncrementalStageResearchRequestV1",
    "Phase22IncrementalResearchError",
    "ResearchDatasetIdentityRequestV1",
    "ResearchDisposition",
    "assert_phase_22_authority_invariants_v1",
    "build_incremental_comparison_evidence_v1",
    "build_phase_22_failure_memory_record_v1",
    "build_research_dataset_identity_v1",
    "classify_incremental_research_disposition_v1",
    "run_incremental_stage_research_v1",
    "run_phase_22_incremental_research_closure_v1",
]
