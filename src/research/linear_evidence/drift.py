from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Mapping, Sequence, Tuple
import hashlib
import json
import math

import numpy as np

from .contracts import FeatureMatrixBindingV1, LinearModelDiagnosticsV1, LinearModelEvidenceV1
from .feature_matrix import build_feature_matrix_binding
from .fitters import (
    REASON_RANK_DEFICIENT_FEATURE_MATRIX,
    exclude_strict_zero_variance_features_v0,
    fit_ols_lstsq,
    strict_zero_variance_feature_exclusion_reason_codes_v0,
)

MODEL_SPEC_VERSION = "parameter_sensitivity_active_feature_subset_v0"
EXCLUSION_REASON_ZERO_VARIANCE_ROLLING = "ZERO_VARIANCE_WITHIN_ROLLING_FIT"
SCHEMA_VERSION = "rolling_linear_drift_diagnostics.v0"
GO_TOKEN_REQUIRED = "GO_OFFLINE_ROLLING_LINEAR_DRIFT_DIAGNOSTICS_V0"

DRIFT_DIAGNOSTIC_DEFAULTS_V0: Mapping[str, float] = {
    "coefficient_relative_change_threshold": 0.75,
    "coefficient_absolute_change_threshold": 1.0,
    "validation_rmse_relative_change_threshold": 2.0,
    "validation_mae_relative_change_threshold": 2.0,
    "validation_r2_absolute_change_threshold": 0.5,
    "residual_scale_shift_threshold": 1.5,
    "residual_location_shift_threshold": 1.5,
    "outlier_rate_change_threshold": 0.25,
    "max_condition_number": 1_000_000.0,
    "drift_detection_threshold": 0.5,
}


@dataclass(frozen=True)
class RollingLinearDriftInputV1:
    instrument_id: str
    decision_time: str
    feature_availability_time: str
    target: float
    features: Mapping[str, float]


@dataclass(frozen=True)
class RollingWindowModelSpecV1:
    window_index: int
    requested_feature_names: Tuple[str, ...]
    active_feature_names: Tuple[str, ...]
    excluded_feature_names: Tuple[str, ...]
    exclusion_reason_codes: Tuple[str, ...]
    design_matrix_rows: int
    requested_design_matrix_columns: int
    active_design_matrix_columns: int
    requested_rank: int
    active_rank: int
    required_active_rank: int
    condition_number: float
    fit_status: str
    fit_reason_codes: Tuple[str, ...]

    def to_dict(self) -> Dict[str, object]:
        return {
            "window_index": self.window_index,
            "requested_feature_names": list(self.requested_feature_names),
            "active_feature_names": list(self.active_feature_names),
            "excluded_feature_names": list(self.excluded_feature_names),
            "exclusion_reason_codes": list(self.exclusion_reason_codes),
            "design_matrix_rows": self.design_matrix_rows,
            "requested_design_matrix_columns": self.requested_design_matrix_columns,
            "active_design_matrix_columns": self.active_design_matrix_columns,
            "requested_rank": self.requested_rank,
            "active_rank": self.active_rank,
            "required_active_rank": self.required_active_rank,
            "condition_number": self.condition_number,
            "fit_status": self.fit_status,
            "fit_reason_codes": list(self.fit_reason_codes),
        }


@dataclass(frozen=True)
class RollingLinearDriftEvidenceV1:
    evidence_type: str
    model_family: str
    target_name: str
    feature_names: Tuple[str, ...]
    n_samples: int
    n_features: int
    window_size: int
    window_step: int
    n_windows: int
    solver: str
    fit_intercept: bool
    window_evidence: Tuple[LinearModelEvidenceV1, ...]
    window_model_specs: Tuple[RollingWindowModelSpecV1, ...]
    coefficient_drift: Dict[str, float]
    drift_score: float
    diagnostics: Dict[str, float]
    drift_metrics: Dict[str, float]
    feature_matrix_digest: str
    target_digest: str
    config_digest: str
    instrument_universe_digest: str
    validation_policy: str
    status: str
    verdict: str
    reason_codes: Tuple[str, ...]
    authority_effect: str
    runtime_effect: str
    model_spec_version: str = MODEL_SPEC_VERSION
    model_spec_alignment_active: bool = True
    successful_window_count: int = 0
    blocked_window_count: int = 0
    insufficient_window_count: int = 0
    rank_deficient_window_count: int = 0
    active_feature_subsets: Tuple[Tuple[str, ...], ...] = ()
    coefficient_sign_flip_counts: Dict[str, int] = field(default_factory=dict)
    economic_validity_offline_gate_pass: bool = False
    runtime_rewire_admissible: bool = False

    def to_dict(self) -> Dict[str, object]:
        return {
            "schema_version": SCHEMA_VERSION,
            "evidence_type": self.evidence_type,
            "model_family": self.model_family,
            "model_spec": self.model_spec_version,
            "model_spec_alignment_active": self.model_spec_alignment_active,
            "target_name": self.target_name,
            "feature_names_requested": list(self.feature_names),
            "feature_names": list(self.feature_names),
            "n_samples": self.n_samples,
            "n_features": self.n_features,
            "window_size": self.window_size,
            "window_step": self.window_step,
            "window_count": self.n_windows,
            "n_windows": self.n_windows,
            "successful_window_count": self.successful_window_count,
            "blocked_window_count": self.blocked_window_count,
            "insufficient_window_count": self.insufficient_window_count,
            "rank_deficient_window_count": self.rank_deficient_window_count,
            "solver": self.solver,
            "fit_intercept": self.fit_intercept,
            "active_feature_subsets": [list(subset) for subset in self.active_feature_subsets],
            "window_evidence": [
                {
                    "window_index": index,
                    "time_range": dict(evidence.time_range),
                    "status": evidence.status,
                    "reason_codes": list(evidence.reason_codes),
                    "coefficients": dict(evidence.coefficients),
                    "diagnostics": {
                        "rank": evidence.diagnostics.rank,
                        "condition_number": evidence.diagnostics.condition_number,
                        "rmse": evidence.diagnostics.rmse,
                        "mae": evidence.diagnostics.mae,
                        "r2_train": evidence.diagnostics.r2_train,
                        "r2_validation": evidence.diagnostics.r2_validation,
                        "residual_mean": evidence.diagnostics.residual_mean,
                        "residual_std": evidence.diagnostics.residual_std,
                        "outlier_count": evidence.diagnostics.outlier_count,
                    },
                    "model_spec": (
                        self.window_model_specs[index].to_dict()
                        if index < len(self.window_model_specs)
                        else {}
                    ),
                }
                for index, evidence in enumerate(self.window_evidence)
            ],
            "coefficient_drift": dict(self.coefficient_drift),
            "coefficient_sign_flip_counts": dict(self.coefficient_sign_flip_counts),
            "drift_score": self.drift_score,
            "diagnostics": dict(self.diagnostics),
            "drift_metrics": dict(self.drift_metrics),
            "coefficient_stability_metrics": {
                "coefficient_dispersion": self.drift_metrics.get("coefficient_dispersion", 0.0),
                "coefficient_stability_score": self.drift_metrics.get(
                    "coefficient_stability_score", 0.0
                ),
            },
            "rank_metrics": {
                "rank_deficient_window_count": float(self.rank_deficient_window_count),
                "full_rank_all_successful_windows": self.drift_metrics.get(
                    "full_rank_all_successful_windows", 0.0
                ),
            },
            "condition_number_metrics": {
                "condition_number_max": self.drift_metrics.get("condition_number_max", 0.0),
                "condition_number_median": self.drift_metrics.get("condition_number_median", 0.0),
            },
            "fit_quality_metrics": {
                "validation_rmse_change": self.drift_metrics.get("validation_rmse_change", 0.0),
                "validation_mae_change": self.drift_metrics.get("validation_mae_change", 0.0),
                "validation_r2_change": self.drift_metrics.get("validation_r2_change", 0.0),
            },
            "residual_drift_metrics": {
                "residual_location_shift": self.drift_metrics.get("residual_location_shift", 0.0),
                "residual_scale_shift": self.drift_metrics.get("residual_scale_shift", 0.0),
            },
            "outlier_metrics": {
                "outlier_rate_change": self.drift_metrics.get("outlier_rate_change", 0.0),
            },
            "feature_matrix_digest": self.feature_matrix_digest,
            "target_digest": self.target_digest,
            "config_digest": self.config_digest,
            "instrument_universe_digest": self.instrument_universe_digest,
            "validation_policy": self.validation_policy,
            "status": self.status,
            "verdict": self.verdict,
            "reason_codes": list(self.reason_codes),
            "authority_effect": self.authority_effect,
            "runtime_effect": self.runtime_effect,
            "economic_validity_offline_gate_pass": self.economic_validity_offline_gate_pass,
            "runtime_rewire_admissible": self.runtime_rewire_admissible,
        }


def _stable_digest(payload: object) -> str:
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _sort_records(
    records: Sequence[RollingLinearDriftInputV1],
) -> Tuple[RollingLinearDriftInputV1, ...]:
    return tuple(sorted(records, key=lambda record: (record.decision_time, record.instrument_id)))


def _records_to_rows(
    records: Sequence[RollingLinearDriftInputV1],
    feature_names: Sequence[str],
) -> List[Dict[str, object]]:
    return [
        {
            "decision_time": record.decision_time,
            "instrument_id": record.instrument_id,
            "target": float(record.target),
            **{name: float(record.features[name]) for name in feature_names},
        }
        for record in records
    ]


def _active_feature_binding_v0(
    binding: FeatureMatrixBindingV1,
    *,
    active_feature_names: Sequence[str],
) -> FeatureMatrixBindingV1:
    return FeatureMatrixBindingV1(
        target_name=binding.target_name,
        feature_names=tuple(active_feature_names),
        n_samples=binding.n_samples,
        n_features=len(active_feature_names),
        feature_matrix_digest=binding.feature_matrix_digest,
        target_digest=binding.target_digest,
        validation_policy=binding.validation_policy,
        time_range=binding.time_range,
        row_count_before_filter=binding.row_count_before_filter,
        row_count_after_filter=binding.row_count_after_filter,
        dropped_rows_by_reason=binding.dropped_rows_by_reason,
        status=binding.status,
        reason_codes=binding.reason_codes,
    )


def _compose_exclusion_reason_codes_v0(
    excluded_feature_names: Sequence[str],
) -> tuple[str, ...]:
    return tuple(
        dict.fromkeys(
            [
                *strict_zero_variance_feature_exclusion_reason_codes_v0(excluded_feature_names),
                *(
                    f"{EXCLUSION_REASON_ZERO_VARIANCE_ROLLING}:{name}"
                    for name in excluded_feature_names
                ),
                "ACTIVE_FEATURE_SUBSET_APPLIED",
            ]
        )
    )


def _blocked_window_model_spec_v0(
    *,
    window_index: int,
    requested_feature_names: Sequence[str],
    excluded_feature_names: Sequence[str],
    exclusion_reason_codes: Sequence[str],
    design_matrix_rows: int,
    binding: FeatureMatrixBindingV1,
    fit_status: str,
    fit_reason_codes: Sequence[str],
) -> tuple[LinearModelEvidenceV1, RollingWindowModelSpecV1]:
    requested_columns = len(requested_feature_names) + 1
    reasons = tuple(dict.fromkeys([*exclusion_reason_codes, *fit_reason_codes]))
    blocked = LinearModelEvidenceV1(
        evidence_type="rolling_linear_drift_window",
        model_family="OLS",
        target_name=binding.target_name,
        feature_names=tuple(requested_feature_names),
        n_samples=design_matrix_rows,
        n_features=len(requested_feature_names),
        solver="numpy.linalg.lstsq",
        fit_intercept=True,
        coefficients={},
        diagnostics=LinearModelDiagnosticsV1(
            rank=0,
            condition_number=0.0,
            rmse=0.0,
            mae=0.0,
            max_abs_error=0.0,
            r2_train=0.0,
            r2_validation=None,
            residual_mean=0.0,
            residual_std=0.0,
            outlier_count=0,
        ),
        feature_matrix_digest=binding.feature_matrix_digest,
        target_digest=binding.target_digest,
        config_digest="",
        time_range=binding.time_range,
        instrument_universe_digest="rolling_window",
        row_count_before_filter=binding.row_count_before_filter,
        row_count_after_filter=binding.row_count_after_filter,
        dropped_rows_by_reason=binding.dropped_rows_by_reason,
        validation_policy=binding.validation_policy,
        cost_policy_output="diagnostic_only",
        status=fit_status,
        reason_codes=reasons,
    )
    model_spec = RollingWindowModelSpecV1(
        window_index=window_index,
        requested_feature_names=tuple(requested_feature_names),
        active_feature_names=(),
        excluded_feature_names=tuple(excluded_feature_names),
        exclusion_reason_codes=tuple(exclusion_reason_codes),
        design_matrix_rows=design_matrix_rows,
        requested_design_matrix_columns=requested_columns,
        active_design_matrix_columns=0,
        requested_rank=requested_columns,
        active_rank=0,
        required_active_rank=0,
        condition_number=0.0,
        fit_status=fit_status,
        fit_reason_codes=reasons,
    )
    return blocked, model_spec


def _fit_window_with_active_feature_subset_v0(
    *,
    window_index: int,
    window_rows: Sequence[Mapping[str, object]],
    feature_names: Sequence[str],
    target_name: str,
    min_samples: int,
    max_condition_number: float,
    validation_fraction: float,
) -> tuple[LinearModelEvidenceV1, RollingWindowModelSpecV1]:
    x, y, binding = build_feature_matrix_binding(
        window_rows,
        feature_names=feature_names,
        target_name=target_name,
        time_name="decision_time",
        validation_policy="TIME_ORDERED",
    )
    requested_feature_names = binding.feature_names
    requested_columns = len(requested_feature_names) + 1

    if int(x.shape[0]) < min_samples:
        exclusion_reason_codes = ("INSUFFICIENT_SAMPLE_COUNT",)
        return _blocked_window_model_spec_v0(
            window_index=window_index,
            requested_feature_names=requested_feature_names,
            excluded_feature_names=(),
            exclusion_reason_codes=exclusion_reason_codes,
            design_matrix_rows=int(x.shape[0]),
            binding=binding,
            fit_status="INSUFFICIENT_DATA",
            fit_reason_codes=exclusion_reason_codes,
        )

    x_active, active_feature_names, excluded_feature_names = (
        exclude_strict_zero_variance_features_v0(x, requested_feature_names)
    )
    exclusion_reason_codes = _compose_exclusion_reason_codes_v0(excluded_feature_names)

    if not active_feature_names:
        return _blocked_window_model_spec_v0(
            window_index=window_index,
            requested_feature_names=requested_feature_names,
            excluded_feature_names=excluded_feature_names,
            exclusion_reason_codes=exclusion_reason_codes,
            design_matrix_rows=int(x.shape[0]),
            binding=binding,
            fit_status="RANK_DEFICIENT_BLOCKED",
            fit_reason_codes=(REASON_RANK_DEFICIENT_FEATURE_MATRIX,),
        )

    active_binding = _active_feature_binding_v0(
        binding,
        active_feature_names=active_feature_names,
    )
    ols_min_samples = max(4, int(x_active.shape[1]) + 2)
    if int(x_active.shape[0]) < ols_min_samples:
        exclusion_reason_codes = tuple(
            dict.fromkeys([*exclusion_reason_codes, "INSUFFICIENT_SAMPLE_COUNT"])
        )
        return _blocked_window_model_spec_v0(
            window_index=window_index,
            requested_feature_names=requested_feature_names,
            excluded_feature_names=excluded_feature_names,
            exclusion_reason_codes=exclusion_reason_codes,
            design_matrix_rows=int(x.shape[0]),
            binding=binding,
            fit_status="INSUFFICIENT_DATA",
            fit_reason_codes=("INSUFFICIENT_SAMPLE_COUNT",),
        )

    evidence = fit_ols_lstsq(
        x_active,
        y,
        active_binding,
        fit_intercept=True,
        validation_fraction=validation_fraction,
        evidence_type="rolling_linear_drift_window",
        instrument_universe_digest="rolling_window",
    )
    active_columns = len(active_feature_names) + 1
    required_active_rank = active_columns
    merged_reasons = tuple(dict.fromkeys([*exclusion_reason_codes, *evidence.reason_codes]))

    if evidence.diagnostics.condition_number > max_condition_number:
        fit_status = "ROBUSTNESS_FAILED"
        merged_reasons = tuple(dict.fromkeys([*merged_reasons, "HIGH_CONDITION_NUMBER"]))
    elif evidence.diagnostics.rank < required_active_rank:
        fit_status = "RANK_DEFICIENT_BLOCKED"
        merged_reasons = tuple(dict.fromkeys([*merged_reasons, "RANK_DEFICIENT_BLOCKED"]))
    else:
        fit_status = "DIAGNOSTIC_ONLY"

    evidence = LinearModelEvidenceV1(
        evidence_type=evidence.evidence_type,
        model_family=evidence.model_family,
        target_name=evidence.target_name,
        feature_names=requested_feature_names,
        n_samples=evidence.n_samples,
        n_features=len(requested_feature_names),
        solver=evidence.solver,
        fit_intercept=evidence.fit_intercept,
        coefficients=evidence.coefficients,
        diagnostics=evidence.diagnostics,
        feature_matrix_digest=binding.feature_matrix_digest,
        target_digest=evidence.target_digest,
        config_digest=evidence.config_digest,
        time_range=evidence.time_range,
        instrument_universe_digest=evidence.instrument_universe_digest,
        row_count_before_filter=evidence.row_count_before_filter,
        row_count_after_filter=evidence.row_count_after_filter,
        dropped_rows_by_reason=evidence.dropped_rows_by_reason,
        validation_policy=evidence.validation_policy,
        cost_policy_output=evidence.cost_policy_output,
        status=fit_status,
        reason_codes=merged_reasons,
        authority_effect=evidence.authority_effect,
        runtime_effect=evidence.runtime_effect,
    )
    model_spec = RollingWindowModelSpecV1(
        window_index=window_index,
        requested_feature_names=requested_feature_names,
        active_feature_names=active_feature_names,
        excluded_feature_names=excluded_feature_names,
        exclusion_reason_codes=exclusion_reason_codes,
        design_matrix_rows=int(x.shape[0]),
        requested_design_matrix_columns=requested_columns,
        active_design_matrix_columns=active_columns,
        requested_rank=requested_columns,
        active_rank=int(evidence.diagnostics.rank),
        required_active_rank=required_active_rank,
        condition_number=float(evidence.diagnostics.condition_number),
        fit_status=fit_status,
        fit_reason_codes=merged_reasons,
    )
    return evidence, model_spec


def _build_drift_matrix(
    records: Sequence[RollingLinearDriftInputV1],
) -> Tuple[
    Tuple[RollingLinearDriftInputV1, ...],
    Tuple[str, ...],
    str,
    str,
    str,
]:
    if not records:
        raise ValueError("INSUFFICIENT_DATA")

    input_decision_times = [record.decision_time for record in records]
    if input_decision_times != sorted(input_decision_times):
        raise ValueError("RANDOM_VALIDATION_SPLIT_BLOCKED")

    sorted_records = _sort_records(records)
    for record in sorted_records:
        if record.feature_availability_time > record.decision_time:
            raise ValueError("LOOKAHEAD_BLOCKED")

    feature_names = tuple(sorted(sorted_records[0].features.keys()))
    if not feature_names:
        raise ValueError("TARGET_BINDING_MISSING")

    for record in sorted_records:
        if tuple(sorted(record.features.keys())) != feature_names:
            raise ValueError("FEATURE_SCHEMA_DRIFT")
        row = [float(record.features[name]) for name in feature_names]
        if any(not math.isfinite(value) for value in row) or not math.isfinite(
            float(record.target)
        ):
            raise ValueError("INSUFFICIENT_DATA")

    rows = _records_to_rows(sorted_records, feature_names)
    instrument_ids = sorted({record.instrument_id for record in sorted_records})
    return (
        sorted_records,
        feature_names,
        _stable_digest(rows),
        _stable_digest([row["target"] for row in rows]),
        _stable_digest(instrument_ids),
    )


def _relative_change(values: Sequence[float]) -> float:
    if len(values) < 2:
        return 0.0
    spread = float(max(values) - min(values))
    scale = max(abs(float(np.mean(values))), 1e-9)
    return spread / scale


def _absolute_change(values: Sequence[float]) -> float:
    if len(values) < 2:
        return 0.0
    return float(max(values) - min(values))


def _sign_flip_count(values: Sequence[float], *, min_abs_coefficient: float = 1e-6) -> int:
    if len(values) < 2:
        return 0
    signs = [
        1 if value > min_abs_coefficient else (-1 if value < -min_abs_coefficient else 0)
        for value in values
    ]
    flips = 0
    for index in range(1, len(signs)):
        if signs[index] != 0 and signs[index - 1] != 0 and signs[index] != signs[index - 1]:
            flips += 1
    return flips


def _series_change(values: Sequence[float]) -> float:
    if len(values) < 2:
        return 0.0
    baseline = max(abs(float(values[0])), 1e-9)
    return float(abs(values[-1] - values[0]) / baseline)


def _compute_drift_metrics(
    window_evidence: Sequence[LinearModelEvidenceV1],
    coefficient_drift: Mapping[str, float],
    *,
    coefficient_sign_flip_counts: Mapping[str, int],
    thresholds: Mapping[str, float],
) -> Dict[str, float]:
    successful = [evidence for evidence in window_evidence if evidence.status == "DIAGNOSTIC_ONLY"]
    condition_numbers = [
        float(evidence.diagnostics.condition_number)
        for evidence in successful
        if evidence.diagnostics.condition_number > 0
    ]
    validation_rmses = [float(evidence.diagnostics.rmse) for evidence in successful]
    validation_maes = [float(evidence.diagnostics.mae) for evidence in successful]
    validation_r2s = [
        float(evidence.diagnostics.r2_validation)
        for evidence in successful
        if evidence.diagnostics.r2_validation is not None
    ]
    residual_means = [float(evidence.diagnostics.residual_mean) for evidence in successful]
    residual_stds = [float(evidence.diagnostics.residual_std) for evidence in successful]
    outlier_rates = [
        float(evidence.diagnostics.outlier_count) / max(float(evidence.n_samples), 1.0)
        for evidence in successful
    ]

    coefficient_dispersion = float(max(coefficient_drift.values(), default=0.0))
    coefficient_stability_score = max(0.0, 1.0 - coefficient_dispersion)

    return {
        "coefficient_absolute_change": float(
            max(
                (
                    _absolute_change(
                        [float(evidence.coefficients.get(name, 0.0)) for evidence in successful]
                    )
                    for name in {
                        name
                        for evidence in successful
                        for name in evidence.coefficients
                        if name != "intercept"
                    }
                ),
                default=0.0,
            )
        ),
        "coefficient_relative_change": float(max(coefficient_drift.values(), default=0.0)),
        "coefficient_sign_flip_count": float(sum(coefficient_sign_flip_counts.values())),
        "coefficient_dispersion": coefficient_dispersion,
        "coefficient_stability_score": coefficient_stability_score,
        "condition_number_max": float(max(condition_numbers, default=0.0)),
        "condition_number_median": float(np.median(condition_numbers))
        if condition_numbers
        else 0.0,
        "validation_rmse_change": _series_change(validation_rmses),
        "validation_mae_change": _series_change(validation_maes),
        "validation_r2_change": _series_change(validation_r2s) if validation_r2s else 0.0,
        "residual_location_shift": _series_change(residual_means),
        "residual_scale_shift": _series_change(residual_stds),
        "outlier_rate_change": _series_change(outlier_rates),
        "rank_deficient_window_count": float(
            sum(1 for evidence in window_evidence if evidence.status == "RANK_DEFICIENT_BLOCKED")
        ),
        "successful_window_count": float(len(successful)),
        "blocked_window_count": float(
            sum(
                1
                for evidence in window_evidence
                if evidence.status in {"RANK_DEFICIENT_BLOCKED", "ROBUSTNESS_FAILED"}
            )
        ),
        "insufficient_window_count": float(
            sum(1 for evidence in window_evidence if evidence.status == "INSUFFICIENT_DATA")
        ),
        "full_rank_all_successful_windows": (
            1.0
            if successful
            and all(evidence.diagnostics.rank >= evidence.n_features + 1 for evidence in successful)
            else 0.0
        ),
        "drift_score": float(max(coefficient_drift.values(), default=0.0)),
        "unstable_coefficient_count": float(
            sum(
                1
                for score in coefficient_drift.values()
                if score >= thresholds["coefficient_relative_change_threshold"]
            )
        ),
    }


def _aggregate_verdict(
    *,
    window_evidence: Sequence[LinearModelEvidenceV1],
    drift_metrics: Mapping[str, float],
    coefficient_sign_flip_counts: Mapping[str, int],
    thresholds: Mapping[str, float],
    leakage_blocked: bool = False,
) -> tuple[str, str, Tuple[str, ...]]:
    if leakage_blocked:
        return "FAIL_CLOSED", "FAIL_CLOSED", ("LOOKAHEAD_BLOCKED", "FEATURE_LEAKAGE_RISK")

    if not window_evidence:
        return (
            "INCONCLUSIVE",
            "INCONCLUSIVE",
            ("INSUFFICIENT_SAMPLE_COUNT", "WINDOW_COVERAGE_INSUFFICIENT"),
        )

    reason_codes: List[str] = []
    insufficient_count = int(drift_metrics.get("insufficient_window_count", 0))
    blocked_count = int(drift_metrics.get("blocked_window_count", 0))
    successful_count = int(drift_metrics.get("successful_window_count", 0))
    rank_deficient_count = int(drift_metrics.get("rank_deficient_window_count", 0))

    if successful_count == 0:
        if insufficient_count > 0:
            return (
                "INCONCLUSIVE",
                "INCONCLUSIVE",
                ("INSUFFICIENT_SAMPLE_COUNT", "WINDOW_COVERAGE_INSUFFICIENT"),
            )
        if rank_deficient_count > 0:
            return "FAIL_CLOSED", "FAIL_CLOSED", ("RANK_DEFICIENT_BLOCKED",)
        return "INCONCLUSIVE", "INCONCLUSIVE", ("WINDOW_COVERAGE_INSUFFICIENT",)

    if rank_deficient_count > 0:
        reason_codes.append("RANK_DEFICIENT_BLOCKED")

    if (
        drift_metrics.get("coefficient_relative_change", 0.0)
        >= thresholds["drift_detection_threshold"]
    ):
        reason_codes.append("COEFFICIENT_MAGNITUDE_DRIFT")
        reason_codes.append("COEFFICIENT_DRIFT_DETECTED")

    feature_sign_flip_count = sum(
        count for name, count in coefficient_sign_flip_counts.items() if name != "intercept"
    )
    if feature_sign_flip_count > 0:
        reason_codes.append("COEFFICIENT_SIGN_UNSTABLE")

    if (
        drift_metrics.get("validation_rmse_change", 0.0)
        >= thresholds["validation_rmse_relative_change_threshold"]
    ):
        reason_codes.append("VALIDATION_ERROR_DRIFT")

    if (
        drift_metrics.get("residual_scale_shift", 0.0)
        >= thresholds["residual_scale_shift_threshold"]
    ):
        reason_codes.append("RESIDUAL_DISTRIBUTION_DRIFT")

    if drift_metrics.get("outlier_rate_change", 0.0) >= thresholds["outlier_rate_change_threshold"]:
        reason_codes.append("OUTLIER_RATE_DRIFT")

    if blocked_count > 0 and successful_count > 0:
        reason_codes.append("HIGH_CONDITION_NUMBER")

    deduped = tuple(dict.fromkeys(reason_codes))
    drift_reasons = {
        "COEFFICIENT_MAGNITUDE_DRIFT",
        "COEFFICIENT_DRIFT_DETECTED",
        "COEFFICIENT_SIGN_UNSTABLE",
        "VALIDATION_ERROR_DRIFT",
        "RESIDUAL_DISTRIBUTION_DRIFT",
        "OUTLIER_RATE_DRIFT",
    }
    if any(reason in drift_reasons for reason in deduped):
        return "FAIL", "FAIL", deduped

    if rank_deficient_count > 0:
        return "FAIL_CLOSED", "FAIL_CLOSED", deduped or ("RANK_DEFICIENT_BLOCKED",)

    return "PASS", "PASS", deduped or ("ACTIVE_FEATURE_SUBSET_APPLIED",)


def _empty_evidence(
    *,
    target_name: str,
    window_size: int,
    window_step: int,
    status: str,
    verdict: str,
    reason_codes: Tuple[str, ...],
    n_samples: int = 0,
    feature_names: Tuple[str, ...] = (),
    feature_matrix_digest: str = "",
    target_digest: str = "",
    instrument_universe_digest: str = "",
    config_digest: str = "",
) -> RollingLinearDriftEvidenceV1:
    return RollingLinearDriftEvidenceV1(
        evidence_type="rolling_linear_drift",
        model_family="OLS",
        target_name=target_name,
        feature_names=feature_names,
        n_samples=n_samples,
        n_features=len(feature_names),
        window_size=window_size,
        window_step=window_step,
        n_windows=0,
        solver="numpy.linalg.lstsq",
        fit_intercept=True,
        window_evidence=(),
        window_model_specs=(),
        coefficient_drift={},
        drift_score=0.0,
        diagnostics={},
        drift_metrics={},
        feature_matrix_digest=feature_matrix_digest,
        target_digest=target_digest,
        config_digest=config_digest,
        instrument_universe_digest=instrument_universe_digest,
        validation_policy="TIME_ORDERED",
        status=status,
        verdict=verdict,
        reason_codes=reason_codes,
        authority_effect="NONE",
        runtime_effect="NONE",
    )


def fit_rolling_linear_drift(
    records: Sequence[RollingLinearDriftInputV1],
    *,
    target_name: str = "target",
    window_size: int = 6,
    window_step: int = 1,
    min_samples: int = 4,
    validation_fraction: float = 0.25,
    max_condition_number: float | None = None,
    thresholds: Mapping[str, float] | None = None,
) -> RollingLinearDriftEvidenceV1:
    effective_thresholds = dict(DRIFT_DIAGNOSTIC_DEFAULTS_V0)
    if thresholds:
        effective_thresholds.update(thresholds)
    if max_condition_number is not None:
        effective_thresholds["max_condition_number"] = max_condition_number

    config_payload = {
        "window_size": window_size,
        "window_step": window_step,
        "min_samples": min_samples,
        "validation_fraction": validation_fraction,
        "thresholds": effective_thresholds,
        "model_spec": MODEL_SPEC_VERSION,
    }
    config_digest = _stable_digest(config_payload)

    try:
        sorted_records, feature_names, x_digest, y_digest, universe_digest = _build_drift_matrix(
            records
        )
    except ValueError as exc:
        message = str(exc)
        if message == "LOOKAHEAD_BLOCKED":
            return _empty_evidence(
                target_name=target_name,
                window_size=window_size,
                window_step=window_step,
                status="FAIL_CLOSED",
                verdict="FAIL_CLOSED",
                reason_codes=("LOOKAHEAD_BLOCKED", "FEATURE_LEAKAGE_RISK"),
                n_samples=len(records),
                config_digest=config_digest,
            )
        if message == "TARGET_BINDING_MISSING":
            return _empty_evidence(
                target_name=target_name,
                window_size=window_size,
                window_step=window_step,
                status="FAIL_CLOSED",
                verdict="FAIL_CLOSED",
                reason_codes=("TARGET_BINDING_MISSING",),
                n_samples=len(records),
                config_digest=config_digest,
            )
        raise

    n_samples = len(sorted_records)
    if n_samples < window_size:
        return _empty_evidence(
            target_name=target_name,
            window_size=window_size,
            window_step=window_step,
            status="INCONCLUSIVE",
            verdict="INCONCLUSIVE",
            reason_codes=("INSUFFICIENT_SAMPLE_COUNT", "WINDOW_COVERAGE_INSUFFICIENT"),
            n_samples=n_samples,
            feature_names=feature_names,
            feature_matrix_digest=x_digest,
            target_digest=y_digest,
            instrument_universe_digest=universe_digest,
            config_digest=config_digest,
        )

    window_evidence: List[LinearModelEvidenceV1] = []
    window_model_specs: List[RollingWindowModelSpecV1] = []
    coeff_series: Dict[str, List[float]] = {}
    active_feature_subsets: List[Tuple[str, ...]] = []

    window_index = 0
    for start in range(0, n_samples - window_size + 1, max(1, window_step)):
        end = start + window_size
        window_records = sorted_records[start:end]
        window_rows = _records_to_rows(window_records, feature_names)
        evidence, model_spec = _fit_window_with_active_feature_subset_v0(
            window_index=window_index,
            window_rows=window_rows,
            feature_names=feature_names,
            target_name=target_name,
            min_samples=min_samples,
            max_condition_number=float(effective_thresholds["max_condition_number"]),
            validation_fraction=validation_fraction,
        )
        window_evidence.append(evidence)
        window_model_specs.append(model_spec)
        active_feature_subsets.append(model_spec.active_feature_names)
        for name, value in evidence.coefficients.items():
            coeff_series.setdefault(name, []).append(value)
        window_index += 1

    coefficient_drift: Dict[str, float] = {}
    coefficient_sign_flip_counts: Dict[str, int] = {}
    for name, values in coeff_series.items():
        coefficient_drift[name] = _relative_change(values)
        coefficient_sign_flip_counts[name] = _sign_flip_count(values)

    feature_coefficient_drift = {
        name: score for name, score in coefficient_drift.items() if name != "intercept"
    }
    drift_score = float(max(feature_coefficient_drift.values(), default=0.0))
    drift_metrics = _compute_drift_metrics(
        window_evidence,
        coefficient_drift,
        coefficient_sign_flip_counts=coefficient_sign_flip_counts,
        thresholds=effective_thresholds,
    )
    drift_metrics["drift_score"] = drift_score
    drift_metrics["window_count"] = float(len(window_evidence))

    status, verdict, reason_codes = _aggregate_verdict(
        window_evidence=window_evidence,
        drift_metrics=drift_metrics,
        coefficient_sign_flip_counts=coefficient_sign_flip_counts,
        thresholds=effective_thresholds,
    )

    diagnostics = {
        "drift_score": drift_score,
        "max_coefficient_drift": drift_score,
        "window_count": float(len(window_evidence)),
        "unstable_coefficient_count": drift_metrics.get("unstable_coefficient_count", 0.0),
    }

    return RollingLinearDriftEvidenceV1(
        evidence_type="rolling_linear_drift",
        model_family="OLS",
        target_name=target_name,
        feature_names=feature_names,
        n_samples=n_samples,
        n_features=len(feature_names),
        window_size=window_size,
        window_step=window_step,
        n_windows=len(window_evidence),
        solver="numpy.linalg.lstsq",
        fit_intercept=True,
        window_evidence=tuple(window_evidence),
        window_model_specs=tuple(window_model_specs),
        coefficient_drift=coefficient_drift,
        drift_score=drift_score,
        diagnostics=diagnostics,
        drift_metrics=drift_metrics,
        feature_matrix_digest=x_digest,
        target_digest=y_digest,
        config_digest=config_digest,
        instrument_universe_digest=universe_digest,
        validation_policy="TIME_ORDERED",
        status=status,
        verdict=verdict,
        reason_codes=reason_codes,
        authority_effect="NONE",
        runtime_effect="NONE",
        successful_window_count=int(drift_metrics.get("successful_window_count", 0)),
        blocked_window_count=int(drift_metrics.get("blocked_window_count", 0)),
        insufficient_window_count=int(drift_metrics.get("insufficient_window_count", 0)),
        rank_deficient_window_count=int(drift_metrics.get("rank_deficient_window_count", 0)),
        active_feature_subsets=tuple(active_feature_subsets),
        coefficient_sign_flip_counts=coefficient_sign_flip_counts,
    )


def records_from_parameter_sensitivity_inputs(
    records: Sequence[object],
) -> Tuple[RollingLinearDriftInputV1, ...]:
    converted: List[RollingLinearDriftInputV1] = []
    for record in records:
        converted.append(
            RollingLinearDriftInputV1(
                instrument_id=str(getattr(record, "instrument_id")),
                decision_time=str(getattr(record, "decision_time")),
                feature_availability_time=str(getattr(record, "feature_availability_time")),
                target=float(getattr(record, "target")),
                features=dict(getattr(record, "features")),
            )
        )
    return tuple(converted)
