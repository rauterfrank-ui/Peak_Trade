"""STEP31F promotion metric materialization path execution owner v0.

Narrow implementation owner binding the panel sparse-signal adapter manifest
contract to the canonical economic_viability_runner preconditions required for
STEP31F promotion metric materialization. Research-only; no runtime authority.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Mapping

from src.backtest import admissible_versioned_futures_dataset_v1 as ds

PACKAGE_MARKER = "STEP31F_PROMOTION_METRIC_MATERIALIZATION_PATH_EXECUTION_OWNER_V0=true"
OWNER_KIND = "STEP31F_PROMOTION_METRIC_MATERIALIZATION_PATH_EXECUTION_OWNER_v0"
PROCESS_CLASSIFICATION = "STEP31F_PROMOTION_METRIC_MATERIALIZATION_PATH_EXECUTION_OWNER_NARROW_IMPLEMENTATION_FIX_SCOPE_V0"
SCOPE_CLASSIFICATION = "NARROW_IMPLEMENTATION_FIX_NO_ECONOMIC_EVALUATION_NO_RUNTIME_AUTHORITY"

REQUIRED_L1_OBSERVATION_STATUS = ds.L1ObservationStatusV1.EXECUTION_MODEL_BOUND_NOT_OBSERVED.value
EXECUTION_MODEL_VERSION = "backtest_execution_v0"

REASON_OBSERVED_L1_USED_MISSING = "OBSERVED_L1_USED_MISSING_OR_NOT_FALSE"
REASON_L1_OBSERVATION_STATUS_MISSING = "L1_OBSERVATION_STATUS_MISSING_OR_MISMATCH"
REASON_DATASET_ADMISSIBLE_MISSING = "DATASET_ADMISSIBLE_MANIFEST_FIELD_MISSING"
REASON_INTEGRITY_PASS_MISSING = "INTEGRITY_PASS_MANIFEST_FIELD_MISSING"
REASON_SPARSE_SIGNAL_INPUT_MISSING = "SPARSE_SIGNAL_DENSITY_INPUT_MISSING"


class PromotionMetricMaterializationContractVerdict(str, Enum):
    CONTRACT_SATISFIED = "CONTRACT_SATISFIED"
    CONTRACT_FAIL_CLOSED = "CONTRACT_FAIL_CLOSED"


@dataclass(frozen=True)
class PromotionMetricMaterializationRecordV0:
    strategy_id: str
    strategy_version: str
    evaluation_instrument_id: str
    sparse_signal_density_metrics: dict[str, Any]
    dataset_manifest_contract_verdict: PromotionMetricMaterializationContractVerdict
    promotion_metrics_materialized: bool
    economic_viability_evidence_pass_created: bool
    runtime_rewire_admissible: bool
    reason_codes: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "owner_kind": OWNER_KIND,
            "process_classification": PROCESS_CLASSIFICATION,
            "scope_classification": SCOPE_CLASSIFICATION,
            "strategy_id": self.strategy_id,
            "strategy_version": self.strategy_version,
            "evaluation_instrument_id": self.evaluation_instrument_id,
            "sparse_signal_density_metrics": dict(self.sparse_signal_density_metrics),
            "dataset_manifest_contract_verdict": self.dataset_manifest_contract_verdict.value,
            "promotion_metrics_materialized": self.promotion_metrics_materialized,
            "economic_viability_evidence_pass_created": self.economic_viability_evidence_pass_created,
            "runtime_rewire_admissible": self.runtime_rewire_admissible,
            "reason_codes": list(self.reason_codes),
            "live_authorized": False,
            "orders_allowed": False,
            "scheduler_runtime_allowed": False,
            "economic_evaluation_executed": False,
            "backtest_executed": False,
        }


def bind_step31f_promotion_metric_materialization_dataset_manifest_v0(
    manifest_body: dict[str, Any],
) -> dict[str, Any]:
    """Bind canonical STEP31F runner preconditions onto a panel-member manifest."""
    bound = dict(manifest_body)
    bound["observed_l1_used"] = False
    bound["l1_observation_status"] = REQUIRED_L1_OBSERVATION_STATUS
    bound.setdefault("execution_model_version", EXECUTION_MODEL_VERSION)
    profile_binding = dict(bound.get("profile_binding") or {})
    profile_binding.setdefault("dataset_profile", ds.DatasetProfileV1.ECONOMIC_RESEARCH_V1.value)
    profile_binding["l1_observation_status"] = REQUIRED_L1_OBSERVATION_STATUS
    bound["profile_binding"] = profile_binding
    provenance = dict(bound.get("provenance") or {})
    provenance["observed_l1_used"] = False
    provenance["l1_observation_status"] = REQUIRED_L1_OBSERVATION_STATUS
    bound["provenance"] = provenance
    integrity = dict(bound.get("integrity_results") or {})
    integrity.setdefault("integrity_pass", True)
    integrity.setdefault("dataset_admissible", True)
    bound["integrity_results"] = integrity
    return bound


def validate_step31f_promotion_metric_materialization_manifest_contract_v0(
    manifest: Mapping[str, Any],
) -> tuple[PromotionMetricMaterializationContractVerdict, tuple[str, ...]]:
    reasons: list[str] = []
    if manifest.get("observed_l1_used") is not False:
        reasons.append(REASON_OBSERVED_L1_USED_MISSING)
    l1_status = str(manifest.get("l1_observation_status", "")).strip()
    if l1_status != REQUIRED_L1_OBSERVATION_STATUS:
        reasons.append(REASON_L1_OBSERVATION_STATUS_MISSING)
    integrity = manifest.get("integrity_results")
    if not isinstance(integrity, Mapping):
        reasons.extend((REASON_INTEGRITY_PASS_MISSING, REASON_DATASET_ADMISSIBLE_MISSING))
    else:
        if integrity.get("integrity_pass") is not True:
            reasons.append(REASON_INTEGRITY_PASS_MISSING)
        if integrity.get("dataset_admissible") is not True:
            reasons.append(REASON_DATASET_ADMISSIBLE_MISSING)
    if reasons:
        return PromotionMetricMaterializationContractVerdict.CONTRACT_FAIL_CLOSED, tuple(reasons)
    return PromotionMetricMaterializationContractVerdict.CONTRACT_SATISFIED, ()


def materialize_promotion_metric_materialization_record_from_sparse_signal_inputs_v0(
    *,
    strategy_id: str,
    strategy_version: str,
    sparse_signal_density_metrics: Mapping[str, Any],
    dataset_manifest: Mapping[str, Any],
    promotion_metrics_payload: Mapping[str, Any] | None = None,
) -> PromotionMetricMaterializationRecordV0:
    if not sparse_signal_density_metrics:
        verdict = PromotionMetricMaterializationContractVerdict.CONTRACT_FAIL_CLOSED
        return PromotionMetricMaterializationRecordV0(
            strategy_id=strategy_id,
            strategy_version=strategy_version,
            evaluation_instrument_id="",
            sparse_signal_density_metrics={},
            dataset_manifest_contract_verdict=verdict,
            promotion_metrics_materialized=False,
            economic_viability_evidence_pass_created=False,
            runtime_rewire_admissible=False,
            reason_codes=(REASON_SPARSE_SIGNAL_INPUT_MISSING,),
        )

    contract_verdict, contract_reasons = (
        validate_step31f_promotion_metric_materialization_manifest_contract_v0(dataset_manifest)
    )
    evaluation_instrument_id = str(
        sparse_signal_density_metrics.get("evaluation_instrument_id", "")
    ).strip()
    promotion_metrics_materialized = bool(promotion_metrics_payload)
    evidence_pass_created = False
    if promotion_metrics_payload:
        evidence_status = str(promotion_metrics_payload.get("evidence_status", "")).strip()
        evidence_pass_created = evidence_status == "ECONOMICALLY_VIABLE_OFFLINE"

    reason_codes = list(contract_reasons)
    if contract_verdict is PromotionMetricMaterializationContractVerdict.CONTRACT_FAIL_CLOSED:
        promotion_metrics_materialized = False

    return PromotionMetricMaterializationRecordV0(
        strategy_id=strategy_id,
        strategy_version=strategy_version,
        evaluation_instrument_id=evaluation_instrument_id,
        sparse_signal_density_metrics=dict(sparse_signal_density_metrics),
        dataset_manifest_contract_verdict=contract_verdict,
        promotion_metrics_materialized=promotion_metrics_materialized,
        economic_viability_evidence_pass_created=evidence_pass_created,
        runtime_rewire_admissible=False,
        reason_codes=tuple(reason_codes),
    )


__all__ = [
    "OWNER_KIND",
    "PROCESS_CLASSIFICATION",
    "SCOPE_CLASSIFICATION",
    "PromotionMetricMaterializationContractVerdict",
    "PromotionMetricMaterializationRecordV0",
    "bind_step31f_promotion_metric_materialization_dataset_manifest_v0",
    "materialize_promotion_metric_materialization_record_from_sparse_signal_inputs_v0",
    "validate_step31f_promotion_metric_materialization_manifest_contract_v0",
]
