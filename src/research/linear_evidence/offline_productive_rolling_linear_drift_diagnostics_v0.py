"""Offline productive rolling linear drift diagnostics v0.

Consumes manifest-verified productive parameter-sensitivity join inputs and
upstream orthogonality/factor-exposure/parameter-sensitivity context.
Diagnostic-only: no trading, parameter selection, promotion, or runtime authority.
"""

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Mapping, Sequence

from src.research.linear_evidence.drift import (
    DRIFT_DIAGNOSTIC_DEFAULTS_V0,
    MODEL_SPEC_VERSION,
    RollingLinearDriftEvidenceV1,
    RollingLinearDriftInputV1,
    fit_rolling_linear_drift,
    records_from_parameter_sensitivity_inputs,
)
from src.research.offline_parameter_sensitivity_productive_input_join_materializer_v0 import (
    MaterializationResultV0,
    MaterializationStatus,
)

DIAGNOSTICS_SCOPE_VERSION = "offline_productive_rolling_linear_drift_diagnostics.v0"
DIAGNOSTIC_EVIDENCE_ID = "offline_productive_rolling_linear_drift_diagnostics_v0"
TARGET_NAME = "target"
AUTHORITY_EFFECT = "NONE"
RUNTIME_EFFECT = "NONE"

DEFAULT_WINDOW_SIZE = 120
DEFAULT_WINDOW_STEP = 60
DEFAULT_MIN_SAMPLES = 20
DEFAULT_VALIDATION_FRACTION = 0.25
BASELINE_WINDOW_POLICY = "FIRST_SUCCESSFUL_WINDOW_ELSE_FIRST_WINDOW"


class ProductiveRollingLinearDriftStatus(str, Enum):
    PASS_STABLE = "PASS_STABLE"
    WARN_DRIFT_DETECTED = "WARN_DRIFT_DETECTED"
    BLOCK_DRIFT_EXCEEDS_POLICY = "BLOCK_DRIFT_EXCEEDS_POLICY"
    INSUFFICIENT_DATA = "INSUFFICIENT_DATA"
    INSUFFICIENT_WINDOWS = "INSUFFICIENT_WINDOWS"
    WINDOW_SAMPLE_INSUFFICIENT = "WINDOW_SAMPLE_INSUFFICIENT"
    FEATURE_LEAKAGE_BLOCKED = "FEATURE_LEAKAGE_BLOCKED"
    TARGET_BINDING_MISSING = "TARGET_BINDING_MISSING"
    FEATURE_BINDING_MISMATCH = "FEATURE_BINDING_MISMATCH"
    RANK_DEFICIENT_BLOCKED = "RANK_DEFICIENT_BLOCKED"
    HIGH_CONDITION_NUMBER = "HIGH_CONDITION_NUMBER"
    SOURCE_EVIDENCE_INVALID = "SOURCE_EVIDENCE_INVALID"
    INCONCLUSIVE = "INCONCLUSIVE"


class ProductiveRollingLinearDriftReason(str, Enum):
    COEFFICIENT_SIGN_UNSTABLE = "COEFFICIENT_SIGN_UNSTABLE"
    COEFFICIENT_MAGNITUDE_DRIFT = "COEFFICIENT_MAGNITUDE_DRIFT"
    VALIDATION_ERROR_DRIFT = "VALIDATION_ERROR_DRIFT"
    OUTLIER_DOMINATED = "OUTLIER_DOMINATED"
    RANK_DEFICIENT_BLOCKED = "RANK_DEFICIENT_BLOCKED"
    HIGH_CONDITION_NUMBER = "HIGH_CONDITION_NUMBER"
    INSUFFICIENT_SAMPLE_COUNT = "INSUFFICIENT_SAMPLE_COUNT"
    WINDOW_COVERAGE_INSUFFICIENT = "WINDOW_COVERAGE_INSUFFICIENT"
    LOOKAHEAD_BLOCKED = "LOOKAHEAD_BLOCKED"
    FEATURE_LEAKAGE_RISK = "FEATURE_LEAKAGE_RISK"
    SOURCE_BINDING_MISMATCH = "SOURCE_BINDING_MISMATCH"
    ACTIVE_FEATURE_SUBSET_APPLIED = "ACTIVE_FEATURE_SUBSET_APPLIED"
    POLICY_NOT_BOUND = "POLICY_NOT_BOUND"


class ProductiveRollingLinearDriftValidationError(ValueError):
    """Fail-closed validation for productive rolling linear drift diagnostics inputs."""


@dataclass(frozen=True)
class RollingWindowContractV0:
    window_size: int
    window_step: int
    min_samples: int
    validation_fraction: float
    baseline_window_policy: str
    solver: str
    fit_intercept: bool
    model_spec_version: str
    drift_thresholds: Mapping[str, float]

    def to_dict(self) -> dict[str, Any]:
        return {
            "window_size": self.window_size,
            "window_step": self.window_step,
            "min_samples": self.min_samples,
            "validation_fraction": self.validation_fraction,
            "baseline_window_policy": self.baseline_window_policy,
            "solver": self.solver,
            "fit_intercept": self.fit_intercept,
            "model_spec_version": self.model_spec_version,
            "drift_thresholds": dict(self.drift_thresholds),
            "random_split": False,
            "lookahead": False,
            "policy": "TIME_ORDERED_SLIDING_ROWS",
        }


def _stable_digest(payload: object) -> str:
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def verify_bundle_manifest(path: Path, *, verify_fn: Any) -> int:
    ok, _ = verify_fn(path)
    return 0 if ok else 1


def default_rolling_window_contract_v0() -> RollingWindowContractV0:
    return RollingWindowContractV0(
        window_size=DEFAULT_WINDOW_SIZE,
        window_step=DEFAULT_WINDOW_STEP,
        min_samples=DEFAULT_MIN_SAMPLES,
        validation_fraction=DEFAULT_VALIDATION_FRACTION,
        baseline_window_policy=BASELINE_WINDOW_POLICY,
        solver="numpy.linalg.lstsq",
        fit_intercept=True,
        model_spec_version=MODEL_SPEC_VERSION,
        drift_thresholds=dict(DRIFT_DIAGNOSTIC_DEFAULTS_V0),
    )


def _materialization_status_to_productive(
    status: MaterializationStatus,
) -> tuple[str, tuple[str, ...]]:
    if status == MaterializationStatus.TARGET_BINDING_MISSING:
        return (
            ProductiveRollingLinearDriftStatus.TARGET_BINDING_MISSING.value,
            (ProductiveRollingLinearDriftReason.INSUFFICIENT_SAMPLE_COUNT.value,),
        )
    if status == MaterializationStatus.INSUFFICIENT_DATA:
        return (
            ProductiveRollingLinearDriftStatus.INSUFFICIENT_DATA.value,
            (ProductiveRollingLinearDriftReason.INSUFFICIENT_SAMPLE_COUNT.value,),
        )
    return (
        ProductiveRollingLinearDriftStatus.SOURCE_EVIDENCE_INVALID.value,
        (ProductiveRollingLinearDriftReason.SOURCE_BINDING_MISMATCH.value,),
    )


def classify_productive_rolling_drift_status_v0(
    *,
    evidence: RollingLinearDriftEvidenceV1,
    window_contract: RollingWindowContractV0,
) -> tuple[str, tuple[str, ...]]:
    thresholds = window_contract.drift_thresholds
    reason_codes: list[str] = []

    if "LOOKAHEAD_BLOCKED" in evidence.reason_codes:
        return (
            ProductiveRollingLinearDriftStatus.FEATURE_LEAKAGE_BLOCKED.value,
            (
                ProductiveRollingLinearDriftReason.LOOKAHEAD_BLOCKED.value,
                ProductiveRollingLinearDriftReason.FEATURE_LEAKAGE_RISK.value,
            ),
        )

    if evidence.n_samples < window_contract.window_size:
        return (
            ProductiveRollingLinearDriftStatus.INSUFFICIENT_DATA.value,
            (
                ProductiveRollingLinearDriftReason.INSUFFICIENT_SAMPLE_COUNT.value,
                ProductiveRollingLinearDriftReason.WINDOW_COVERAGE_INSUFFICIENT.value,
            ),
        )

    if evidence.n_windows == 0:
        return (
            ProductiveRollingLinearDriftStatus.INSUFFICIENT_WINDOWS.value,
            (ProductiveRollingLinearDriftReason.WINDOW_COVERAGE_INSUFFICIENT.value,),
        )

    if evidence.insufficient_window_count > 0 and evidence.successful_window_count == 0:
        return (
            ProductiveRollingLinearDriftStatus.WINDOW_SAMPLE_INSUFFICIENT.value,
            (ProductiveRollingLinearDriftReason.INSUFFICIENT_SAMPLE_COUNT.value,),
        )

    if evidence.rank_deficient_window_count > 0 and evidence.successful_window_count == 0:
        return (
            ProductiveRollingLinearDriftStatus.RANK_DEFICIENT_BLOCKED.value,
            (ProductiveRollingLinearDriftReason.RANK_DEFICIENT_BLOCKED.value,),
        )

    for code in evidence.reason_codes:
        if code == "COEFFICIENT_SIGN_UNSTABLE":
            reason_codes.append(ProductiveRollingLinearDriftReason.COEFFICIENT_SIGN_UNSTABLE.value)
        elif code in {"COEFFICIENT_MAGNITUDE_DRIFT", "COEFFICIENT_DRIFT_DETECTED"}:
            reason_codes.append(
                ProductiveRollingLinearDriftReason.COEFFICIENT_MAGNITUDE_DRIFT.value
            )
        elif code == "VALIDATION_ERROR_DRIFT":
            reason_codes.append(ProductiveRollingLinearDriftReason.VALIDATION_ERROR_DRIFT.value)
        elif code in {"OUTLIER_RATE_DRIFT", "OUTLIER_DOMINATED"}:
            reason_codes.append(ProductiveRollingLinearDriftReason.OUTLIER_DOMINATED.value)
        elif code == "RANK_DEFICIENT_BLOCKED":
            reason_codes.append(ProductiveRollingLinearDriftReason.RANK_DEFICIENT_BLOCKED.value)
        elif code == "HIGH_CONDITION_NUMBER":
            reason_codes.append(ProductiveRollingLinearDriftReason.HIGH_CONDITION_NUMBER.value)
        elif code == "ACTIVE_FEATURE_SUBSET_APPLIED":
            reason_codes.append(
                ProductiveRollingLinearDriftReason.ACTIVE_FEATURE_SUBSET_APPLIED.value
            )

    if evidence.blocked_window_count > 0:
        reason_codes.append(ProductiveRollingLinearDriftReason.HIGH_CONDITION_NUMBER.value)

    deduped = tuple(dict.fromkeys(reason_codes))

    if evidence.verdict == "PASS":
        return ProductiveRollingLinearDriftStatus.PASS_STABLE.value, deduped or (
            ProductiveRollingLinearDriftReason.ACTIVE_FEATURE_SUBSET_APPLIED.value,
        )

    if evidence.verdict == "FAIL":
        drift_threshold = float(thresholds.get("drift_detection_threshold", 0.5))
        if evidence.drift_score >= drift_threshold:
            return ProductiveRollingLinearDriftStatus.BLOCK_DRIFT_EXCEEDS_POLICY.value, deduped
        return ProductiveRollingLinearDriftStatus.WARN_DRIFT_DETECTED.value, deduped or (
            ProductiveRollingLinearDriftReason.POLICY_NOT_BOUND.value,
        )

    if evidence.verdict == "FAIL_CLOSED":
        if evidence.rank_deficient_window_count > 0:
            return ProductiveRollingLinearDriftStatus.RANK_DEFICIENT_BLOCKED.value, deduped or (
                ProductiveRollingLinearDriftReason.RANK_DEFICIENT_BLOCKED.value,
            )
        return ProductiveRollingLinearDriftStatus.FEATURE_LEAKAGE_BLOCKED.value, deduped or (
            ProductiveRollingLinearDriftReason.FEATURE_LEAKAGE_RISK.value,
        )

    if evidence.insufficient_window_count > 0:
        return (
            ProductiveRollingLinearDriftStatus.WINDOW_SAMPLE_INSUFFICIENT.value,
            deduped
            or (
                ProductiveRollingLinearDriftReason.INSUFFICIENT_SAMPLE_COUNT.value,
                ProductiveRollingLinearDriftReason.WINDOW_COVERAGE_INSUFFICIENT.value,
            ),
        )

    return ProductiveRollingLinearDriftStatus.INCONCLUSIVE.value, deduped or (
        ProductiveRollingLinearDriftReason.POLICY_NOT_BOUND.value,
    )


def _resolve_baseline_window_index(
    evidence: RollingLinearDriftEvidenceV1,
) -> int:
    for index, window in enumerate(evidence.window_evidence):
        if window.status == "DIAGNOSTIC_ONLY":
            return index
    return 0 if evidence.window_evidence else -1


def _coefficient_delta(
    current: Mapping[str, float],
    reference: Mapping[str, float],
) -> dict[str, float]:
    names = sorted(set(current.keys()) | set(reference.keys()))
    deltas: dict[str, float] = {}
    for name in names:
        left = float(current.get(name, 0.0))
        right = float(reference.get(name, 0.0))
        deltas[name] = left - right
    return deltas


def _normalized_coefficient_drift(deltas: Mapping[str, float]) -> dict[str, float]:
    normalized: dict[str, float] = {}
    for name, delta in deltas.items():
        if name == "intercept":
            continue
        scale = max(abs(delta), 1e-9)
        normalized[name] = float(abs(delta) / scale) if scale > 0 else 0.0
    return normalized


def build_window_results_v0(
    evidence: RollingLinearDriftEvidenceV1,
    *,
    window_contract: RollingWindowContractV0,
) -> list[dict[str, Any]]:
    baseline_index = _resolve_baseline_window_index(evidence)
    baseline_coefficients = (
        dict(evidence.window_evidence[baseline_index].coefficients) if baseline_index >= 0 else {}
    )
    results: list[dict[str, Any]] = []
    previous_coefficients: dict[str, float] | None = None

    for index, window in enumerate(evidence.window_evidence):
        model_spec = (
            evidence.window_model_specs[index].to_dict()
            if index < len(evidence.window_model_specs)
            else {}
        )
        coefficients = dict(window.coefficients)
        delta_baseline = _coefficient_delta(coefficients, baseline_coefficients)
        delta_previous = (
            _coefficient_delta(coefficients, previous_coefficients)
            if previous_coefficients is not None
            else {}
        )
        sign_changes = {
            name: int(
                math.copysign(1.0, delta_baseline.get(name, 0.0))
                != math.copysign(1.0, baseline_coefficients.get(name, 0.0))
                and baseline_coefficients.get(name, 0.0) != 0.0
                and coefficients.get(name, 0.0) != 0.0
            )
            for name in coefficients
            if name != "intercept"
        }
        results.append(
            {
                "window_index": index,
                "time_range": dict(window.time_range),
                "status": window.status,
                "reason_codes": list(window.reason_codes),
                "feature_names": list(window.feature_names),
                "coefficients": coefficients,
                "intercept": float(coefficients.get("intercept", 0.0)),
                "rank": int(window.diagnostics.rank),
                "condition_number": float(window.diagnostics.condition_number),
                "sample_count": int(window.n_samples),
                "mae": float(window.diagnostics.mae),
                "rmse": float(window.diagnostics.rmse),
                "r2_train": float(window.diagnostics.r2_train),
                "r2_validation": window.diagnostics.r2_validation,
                "residual_mean": float(window.diagnostics.residual_mean),
                "residual_std": float(window.diagnostics.residual_std),
                "outlier_count": int(window.diagnostics.outlier_count),
                "coefficient_delta_from_baseline": delta_baseline,
                "coefficient_delta_from_previous": delta_previous,
                "normalized_coefficient_drift": _normalized_coefficient_drift(delta_baseline),
                "sign_change_from_baseline": sign_changes,
                "model_spec": model_spec,
                "is_baseline_window": index == baseline_index,
            }
        )
        previous_coefficients = coefficients

    return results


def build_coefficient_drift_v0(evidence: RollingLinearDriftEvidenceV1) -> dict[str, Any]:
    return {
        "coefficient_drift": dict(evidence.coefficient_drift),
        "coefficient_sign_flip_counts": dict(evidence.coefficient_sign_flip_counts),
        "drift_score": float(evidence.drift_score),
        "baseline_window_index": _resolve_baseline_window_index(evidence),
        "max_coefficient_drift": float(max(evidence.coefficient_drift.values(), default=0.0)),
        "coefficient_sign_change_count": int(sum(evidence.coefficient_sign_flip_counts.values())),
    }


def build_fit_metric_drift_v0(evidence: RollingLinearDriftEvidenceV1) -> dict[str, Any]:
    return {
        "validation_rmse_change": float(evidence.drift_metrics.get("validation_rmse_change", 0.0)),
        "validation_mae_change": float(evidence.drift_metrics.get("validation_mae_change", 0.0)),
        "validation_r2_change": float(evidence.drift_metrics.get("validation_r2_change", 0.0)),
        "residual_location_shift": float(
            evidence.drift_metrics.get("residual_location_shift", 0.0)
        ),
        "residual_scale_shift": float(evidence.drift_metrics.get("residual_scale_shift", 0.0)),
        "outlier_rate_change": float(evidence.drift_metrics.get("outlier_rate_change", 0.0)),
        "max_validation_error_drift": float(
            max(
                evidence.drift_metrics.get("validation_rmse_change", 0.0),
                evidence.drift_metrics.get("validation_mae_change", 0.0),
            )
        ),
    }


def build_window_quality_diagnostics_v0(
    evidence: RollingLinearDriftEvidenceV1,
) -> dict[str, Any]:
    return {
        "window_count": int(evidence.n_windows),
        "valid_window_count": int(evidence.successful_window_count),
        "blocked_window_count": int(evidence.blocked_window_count),
        "insufficient_window_count": int(evidence.insufficient_window_count),
        "rank_deficient_window_count": int(evidence.rank_deficient_window_count),
        "condition_number_max": float(evidence.drift_metrics.get("condition_number_max", 0.0)),
        "condition_number_median": float(
            evidence.drift_metrics.get("condition_number_median", 0.0)
        ),
        "full_rank_all_successful_windows": float(
            evidence.drift_metrics.get("full_rank_all_successful_windows", 0.0)
        ),
        "window_coverage": float(evidence.n_windows / max(evidence.n_samples, 1)),
    }


def build_dropped_rows_by_reason_v0(
    evidence: RollingLinearDriftEvidenceV1,
) -> dict[str, Any]:
    aggregated: dict[str, int] = {}
    for window in evidence.window_evidence:
        for reason, count in window.dropped_rows_by_reason.items():
            aggregated[reason] = aggregated.get(reason, 0) + int(count)
    return {
        "dropped_rows_by_reason": aggregated,
        "windows_reporting_drops": int(
            sum(1 for window in evidence.window_evidence if window.dropped_rows_by_reason)
        ),
    }


def build_source_binding_v0(
    materialization: MaterializationResultV0,
    *,
    source_evidence_refs: Sequence[str],
    window_contract: RollingWindowContractV0,
) -> dict[str, Any]:
    binding = materialization.join_result.binding if materialization.join_result else None
    return {
        "diagnostic_evidence_id": DIAGNOSTIC_EVIDENCE_ID,
        "diagnostics_scope_version": DIAGNOSTICS_SCOPE_VERSION,
        "source_evidence_refs": list(source_evidence_refs),
        "binding_digest": binding.binding_digest if binding else "",
        "signal_matrix_digest": binding.signal_matrix_digest if binding else "",
        "grid_id": binding.grid_id if binding else "",
        "strategy_id": binding.strategy_id if binding else "",
        "strategy_version": binding.strategy_version if binding else "",
        "productive_input_digest": materialization.productive_input_digest,
        "source_signal_matrix_digest": materialization.source_signal_matrix_digest,
        "source_binding_digest": materialization.source_binding_digest,
        "feature_matrix_digest": "",
        "target_digest": "",
        "instrument_universe_digest": "",
        "target_name": TARGET_NAME,
        "feature_names": [],
        "time_range": {},
        "row_count_before_filter": (
            materialization.join_result.row_count_before_filter
            if materialization.join_result
            else 0
        ),
        "row_count_after_filter": (
            materialization.join_result.row_count_after_filter if materialization.join_result else 0
        ),
        "window_contract": window_contract.to_dict(),
        "authority_effect": AUTHORITY_EFFECT,
        "runtime_effect": RUNTIME_EFFECT,
    }


def build_status_reason_taxonomy_v0(
    *,
    observed_status: str,
    observed_reason_codes: Sequence[str],
) -> dict[str, Any]:
    return {
        "supported_statuses": sorted(item.value for item in ProductiveRollingLinearDriftStatus),
        "supported_reason_codes": sorted(item.value for item in ProductiveRollingLinearDriftReason),
        "observed_status": observed_status,
        "observed_reason_codes": sorted(set(observed_reason_codes)),
    }


def build_authority_boundary_v0() -> dict[str, Any]:
    return {
        "offline_only": True,
        "diagnostic_only": True,
        "authority_effect": AUTHORITY_EFFECT,
        "runtime_effect": RUNTIME_EFFECT,
        "rolling_linear_drift_diagnostics_can_warn": True,
        "rolling_linear_drift_diagnostics_can_block_economic_evidence_by_policy": True,
        "rolling_linear_drift_diagnostics_can_not_trigger_runtime_action": True,
        "parameter_default_changed": False,
        "parameter_optimization_executed": False,
        "strategy_selection_changed": False,
        "economic_evaluation_executed": False,
        "promotion_pass_created": False,
        "runtime_rewire_admissible": False,
        "interpretation_boundary": [
            "Rolling drift surfaces temporal instability in linear relationships only.",
            "Drift warnings and blocks do not authorize parameter or strategy changes.",
            "Policy-bound classifications use versioned drift thresholds only.",
        ],
        "forbidden_claims": [
            "automatic parameter selection",
            "strategy selection change",
            "economic validity proof",
            "promotion admissibility",
            "runtime authority",
        ],
    }


def build_rolling_drift_interpretation_v0(
    *,
    evidence: RollingLinearDriftEvidenceV1,
    productive_status: str,
    reason_codes: Sequence[str],
) -> dict[str, Any]:
    unstable_features = sorted(
        name
        for name, count in evidence.coefficient_sign_flip_counts.items()
        if name != "intercept" and count > 0
    )
    drift_features = sorted(
        name
        for name, score in evidence.coefficient_drift.items()
        if name != "intercept" and score > 0.0
    )
    return {
        "productive_status": productive_status,
        "reason_codes": list(reason_codes),
        "stable_relationship_observed": productive_status
        == ProductiveRollingLinearDriftStatus.PASS_STABLE.value,
        "drift_detected": productive_status
        in {
            ProductiveRollingLinearDriftStatus.WARN_DRIFT_DETECTED.value,
            ProductiveRollingLinearDriftStatus.BLOCK_DRIFT_EXCEEDS_POLICY.value,
        },
        "coefficient_unstable_features": unstable_features,
        "coefficient_drift_features": drift_features,
        "remaining_uncertainties": (
            []
            if productive_status != ProductiveRollingLinearDriftStatus.INCONCLUSIVE.value
            else ["policy or sample coverage insufficient for definitive classification"]
        ),
        "recommendation_policy": "DIAGNOSTIC_ONLY_NO_PARAMETER_OR_STRATEGY_CHANGE",
        "authority_effect": AUTHORITY_EFFECT,
        "runtime_effect": RUNTIME_EFFECT,
    }


def fit_productive_rolling_linear_drift_v0(
    *,
    records: Sequence[RollingLinearDriftInputV1],
    window_contract: RollingWindowContractV0 | None = None,
) -> RollingLinearDriftEvidenceV1:
    contract = window_contract or default_rolling_window_contract_v0()
    ordered = tuple(
        sorted(records, key=lambda record: (record.decision_time, record.instrument_id))
    )
    return fit_rolling_linear_drift(
        ordered,
        target_name=TARGET_NAME,
        window_size=contract.window_size,
        window_step=contract.window_step,
        min_samples=contract.min_samples,
        validation_fraction=contract.validation_fraction,
        thresholds=contract.drift_thresholds,
    )


def build_productive_rolling_linear_drift_diagnostics_artifacts_v0(
    *,
    materialization: MaterializationResultV0,
    source_evidence_refs: Sequence[str],
    window_contract: RollingWindowContractV0 | None = None,
) -> dict[str, Any]:
    contract = window_contract or default_rolling_window_contract_v0()

    if materialization.status != MaterializationStatus.PASS:
        status, reason_codes = _materialization_status_to_productive(materialization.status)
        source_binding = build_source_binding_v0(
            materialization,
            source_evidence_refs=source_evidence_refs,
            window_contract=contract,
        )
        return {
            "diagnostics_scope_version": DIAGNOSTICS_SCOPE_VERSION,
            "diagnostic_evidence_id": DIAGNOSTIC_EVIDENCE_ID,
            "source_evidence_refs": list(source_evidence_refs),
            "source_binding": source_binding,
            "rolling_window_contract": contract.to_dict(),
            "window_results": [],
            "coefficient_drift": {},
            "fit_metric_drift": {},
            "window_quality_diagnostics": {
                "window_count": 0,
                "valid_window_count": 0,
                "blocked_window_count": 0,
            },
            "dropped_rows_by_reason": {"dropped_rows_by_reason": {}, "windows_reporting_drops": 0},
            "status_reason_taxonomy": build_status_reason_taxonomy_v0(
                observed_status=status,
                observed_reason_codes=reason_codes,
            ),
            "interpretation": {
                "productive_status": status,
                "reason_codes": list(reason_codes),
                "stable_relationship_observed": False,
                "drift_detected": False,
                "coefficient_unstable_features": [],
                "coefficient_drift_features": [],
                "remaining_uncertainties": ["productive materialization did not pass"],
                "recommendation_policy": "DIAGNOSTIC_ONLY_NO_PARAMETER_OR_STRATEGY_CHANGE",
                "authority_effect": AUTHORITY_EFFECT,
                "runtime_effect": RUNTIME_EFFECT,
            },
            "authority_boundary": build_authority_boundary_v0(),
            "aggregate_status": status,
            "reason_codes": list(reason_codes),
            "output_digest": _stable_digest({"status": status, "binding": source_binding}),
        }

    drift_records = records_from_parameter_sensitivity_inputs(materialization.records)
    evidence = fit_productive_rolling_linear_drift_v0(
        records=drift_records,
        window_contract=contract,
    )
    productive_status, reason_codes = classify_productive_rolling_drift_status_v0(
        evidence=evidence,
        window_contract=contract,
    )

    source_binding = build_source_binding_v0(
        materialization,
        source_evidence_refs=source_evidence_refs,
        window_contract=contract,
    )
    source_binding["feature_matrix_digest"] = evidence.feature_matrix_digest
    source_binding["target_digest"] = evidence.target_digest
    source_binding["instrument_universe_digest"] = evidence.instrument_universe_digest
    source_binding["feature_names"] = list(evidence.feature_names)
    if evidence.window_evidence:
        source_binding["time_range"] = dict(evidence.window_evidence[0].time_range)
        source_binding["time_range"]["end"] = evidence.window_evidence[-1].time_range.get("end", "")

    window_results = build_window_results_v0(evidence, window_contract=contract)
    coefficient_drift = build_coefficient_drift_v0(evidence)
    fit_metric_drift = build_fit_metric_drift_v0(evidence)
    window_quality = build_window_quality_diagnostics_v0(evidence)
    dropped_rows = build_dropped_rows_by_reason_v0(evidence)
    interpretation = build_rolling_drift_interpretation_v0(
        evidence=evidence,
        productive_status=productive_status,
        reason_codes=reason_codes,
    )

    output_digest = _stable_digest(
        {
            "scope_version": DIAGNOSTICS_SCOPE_VERSION,
            "source_binding": source_binding,
            "window_results": window_results,
            "coefficient_drift": coefficient_drift,
            "fit_metric_drift": fit_metric_drift,
            "productive_status": productive_status,
            "interpretation": interpretation,
        }
    )

    return {
        "diagnostics_scope_version": DIAGNOSTICS_SCOPE_VERSION,
        "diagnostic_evidence_id": DIAGNOSTIC_EVIDENCE_ID,
        "source_evidence_refs": list(source_evidence_refs),
        "source_binding": source_binding,
        "rolling_window_contract": contract.to_dict(),
        "window_results": window_results,
        "coefficient_drift": coefficient_drift,
        "fit_metric_drift": fit_metric_drift,
        "window_quality_diagnostics": window_quality,
        "dropped_rows_by_reason": dropped_rows,
        "status_reason_taxonomy": build_status_reason_taxonomy_v0(
            observed_status=productive_status,
            observed_reason_codes=reason_codes,
        ),
        "interpretation": interpretation,
        "authority_boundary": build_authority_boundary_v0(),
        "aggregate_status": productive_status,
        "reason_codes": list(reason_codes),
        "drift_evidence": evidence.to_dict(),
        "output_digest": output_digest,
    }


__all__ = [
    "AUTHORITY_EFFECT",
    "BASELINE_WINDOW_POLICY",
    "DEFAULT_MIN_SAMPLES",
    "DEFAULT_VALIDATION_FRACTION",
    "DEFAULT_WINDOW_SIZE",
    "DEFAULT_WINDOW_STEP",
    "DIAGNOSTIC_EVIDENCE_ID",
    "DIAGNOSTICS_SCOPE_VERSION",
    "RUNTIME_EFFECT",
    "ProductiveRollingLinearDriftReason",
    "ProductiveRollingLinearDriftStatus",
    "ProductiveRollingLinearDriftValidationError",
    "RollingWindowContractV0",
    "build_authority_boundary_v0",
    "build_coefficient_drift_v0",
    "build_dropped_rows_by_reason_v0",
    "build_fit_metric_drift_v0",
    "build_productive_rolling_linear_drift_diagnostics_artifacts_v0",
    "build_rolling_drift_interpretation_v0",
    "build_source_binding_v0",
    "build_status_reason_taxonomy_v0",
    "build_window_quality_diagnostics_v0",
    "build_window_results_v0",
    "classify_productive_rolling_drift_status_v0",
    "default_rolling_window_contract_v0",
    "fit_productive_rolling_linear_drift_v0",
    "verify_bundle_manifest",
]
