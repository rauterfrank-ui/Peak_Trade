from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Mapping, Sequence, Tuple
import hashlib
import json
import math

import numpy as np

from .contracts import FeatureMatrixBindingV1, LinearModelDiagnosticsV1, LinearModelEvidenceV1
from .feature_matrix import build_feature_matrix_binding
from .fitters import (
    REASON_RANK_DEFICIENT_FEATURE_MATRIX,
    REASON_STRICT_ZERO_VARIANCE_FEATURE_EXCLUDED,
    exclude_strict_zero_variance_features_v0,
    fit_ols_lstsq,
    strict_zero_variance_feature_exclusion_reason_codes_v0,
)

MODEL_SPEC_VERSION = "parameter_sensitivity_active_feature_subset_v0"
EXCLUSION_REASON_ZERO_VARIANCE = "ZERO_VARIANCE_WITHIN_1D_SURFACE_FIT"


@dataclass(frozen=True)
class ParameterSensitivityGridPointModelSpecV1:
    parameter_value: float
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
            "parameter_value": self.parameter_value,
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
class ParameterSensitivityInputV1:
    instrument_id: str
    decision_time: str
    feature_availability_time: str
    target: float
    features: Mapping[str, float]


@dataclass(frozen=True)
class ParameterGridSpecV1:
    parameter_name: str
    scaled_feature_name: str
    parameter_values: Tuple[float, ...]


@dataclass(frozen=True)
class ParameterSensitivitySurfaceEvidenceV1:
    evidence_type: str
    model_family: str
    target_name: str
    feature_names: Tuple[str, ...]
    parameter_name: str
    parameter_values: Tuple[float, ...]
    n_samples: int
    n_features: int
    n_grid_points: int
    solver: str
    fit_intercept: bool
    grid_evidence: Tuple[LinearModelEvidenceV1, ...]
    surface_diagnostics: Dict[str, float]
    plateau_detected: bool
    fragile_spike_detected: bool
    robust_region_bounds: Tuple[float, float] | None
    feature_matrix_digest: str
    target_digest: str
    validation_policy: str
    status: str
    reason_codes: Tuple[str, ...]
    authority_effect: str
    runtime_effect: str
    model_spec_version: str = MODEL_SPEC_VERSION
    requested_feature_names: Tuple[str, ...] = ()
    active_feature_names: Tuple[str, ...] = ()
    excluded_feature_names: Tuple[str, ...] = ()
    exclusion_reason_codes: Tuple[str, ...] = ()
    requested_design_matrix_columns: int = 0
    active_design_matrix_columns: int = 0
    requested_rank: int = 0
    active_rank: int = 0
    required_active_rank: int = 0
    condition_number: float = float("inf")
    fit_status: str = "DIAGNOSTIC_ONLY"
    fit_reason_codes: Tuple[str, ...] = ()
    grid_point_model_specs: Tuple[ParameterSensitivityGridPointModelSpecV1, ...] = ()
    plateau_detection_admissible: bool = False
    fragility_detection_admissible: bool = False
    economic_interpretation_admissible: bool = False

    def to_dict(self) -> Dict[str, object]:
        return {
            "evidence_type": self.evidence_type,
            "model_family": self.model_family,
            "target_name": self.target_name,
            "feature_names": list(self.feature_names),
            "parameter_name": self.parameter_name,
            "parameter_values": list(self.parameter_values),
            "n_samples": self.n_samples,
            "n_features": self.n_features,
            "n_grid_points": self.n_grid_points,
            "solver": self.solver,
            "fit_intercept": self.fit_intercept,
            "grid_evidence": [
                {
                    "parameter_value": parameter_value,
                    "status": evidence.status,
                    "reason_codes": list(evidence.reason_codes),
                    "diagnostics": {
                        "rmse": evidence.diagnostics.rmse,
                        "r2_train": evidence.diagnostics.r2_train,
                        "r2_validation": evidence.diagnostics.r2_validation,
                    },
                    "model_spec": (
                        self.grid_point_model_specs[index].to_dict()
                        if index < len(self.grid_point_model_specs)
                        else {}
                    ),
                }
                for index, (parameter_value, evidence) in enumerate(
                    zip(self.parameter_values, self.grid_evidence)
                )
            ],
            "surface_diagnostics": dict(self.surface_diagnostics),
            "plateau_detected": self.plateau_detected,
            "fragile_spike_detected": self.fragile_spike_detected,
            "robust_region_bounds": (
                list(self.robust_region_bounds) if self.robust_region_bounds is not None else None
            ),
            "feature_matrix_digest": self.feature_matrix_digest,
            "target_digest": self.target_digest,
            "validation_policy": self.validation_policy,
            "status": self.status,
            "reason_codes": list(self.reason_codes),
            "authority_effect": self.authority_effect,
            "runtime_effect": self.runtime_effect,
            "model_spec_version": self.model_spec_version,
            "requested_feature_names": list(self.requested_feature_names),
            "active_feature_names": list(self.active_feature_names),
            "excluded_feature_names": list(self.excluded_feature_names),
            "exclusion_reason_codes": list(self.exclusion_reason_codes),
            "design_matrix_rows": self.n_samples,
            "requested_design_matrix_columns": self.requested_design_matrix_columns,
            "active_design_matrix_columns": self.active_design_matrix_columns,
            "requested_rank": self.requested_rank,
            "active_rank": self.active_rank,
            "required_active_rank": self.required_active_rank,
            "condition_number": self.condition_number,
            "fit_status": self.fit_status,
            "fit_reason_codes": list(self.fit_reason_codes),
            "plateau_detection_admissible": self.plateau_detection_admissible,
            "fragility_detection_admissible": self.fragility_detection_admissible,
            "economic_interpretation_admissible": self.economic_interpretation_admissible,
        }


def _stable_digest(payload: object) -> str:
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _validate_records(
    records: Sequence[ParameterSensitivityInputV1],
) -> Tuple[List[ParameterSensitivityInputV1], Tuple[str, ...], str, str]:
    if not records:
        raise ValueError("INSUFFICIENT_DATA")

    decision_times = [record.decision_time for record in records]
    if decision_times != sorted(decision_times):
        raise ValueError("RANDOM_VALIDATION_SPLIT_BLOCKED")

    for record in records:
        if record.feature_availability_time > record.decision_time:
            raise ValueError("LOOKAHEAD_BLOCKED")

    feature_names = tuple(sorted(records[0].features.keys()))
    if not feature_names:
        raise ValueError("TARGET_BINDING_MISSING")

    for record in records:
        if tuple(sorted(record.features.keys())) != feature_names:
            raise ValueError("FEATURE_SCHEMA_DRIFT")
        row = [float(record.features[name]) for name in feature_names]
        if any(not math.isfinite(value) for value in row) or not math.isfinite(
            float(record.target)
        ):
            raise ValueError("INSUFFICIENT_DATA")

    rows = [
        {
            "decision_time": record.decision_time,
            "target": float(record.target),
            **{name: float(record.features[name]) for name in feature_names},
        }
        for record in records
    ]
    return (
        rows,
        feature_names,
        _stable_digest(rows),
        _stable_digest([row["target"] for row in rows]),
    )


def _scale_rows(
    rows: Sequence[Mapping[str, object]],
    *,
    scaled_feature_name: str,
    parameter_value: float,
) -> List[Dict[str, object]]:
    scaled_rows: List[Dict[str, object]] = []
    for row in rows:
        scaled = dict(row)
        scaled[scaled_feature_name] = float(row[scaled_feature_name]) * float(parameter_value)
        scaled_rows.append(scaled)
    return scaled_rows


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


def _blocked_grid_point_model_spec_v0(
    *,
    parameter_value: float,
    requested_feature_names: Sequence[str],
    excluded_feature_names: Sequence[str],
    exclusion_reason_codes: Sequence[str],
    design_matrix_rows: int,
    binding: FeatureMatrixBindingV1,
) -> tuple[LinearModelEvidenceV1, ParameterSensitivityGridPointModelSpecV1]:
    requested_columns = len(requested_feature_names) + 1
    reasons = tuple(dict.fromkeys([*exclusion_reason_codes, REASON_RANK_DEFICIENT_FEATURE_MATRIX]))
    blocked = LinearModelEvidenceV1(
        evidence_type="parameter_sensitivity_surface_point",
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
        instrument_universe_digest="fixture_universe",
        row_count_before_filter=binding.row_count_before_filter,
        row_count_after_filter=binding.row_count_after_filter,
        dropped_rows_by_reason=binding.dropped_rows_by_reason,
        validation_policy=binding.validation_policy,
        cost_policy_output="diagnostic_only",
        status="RANK_DEFICIENT_BLOCKED",
        reason_codes=reasons,
    )
    model_spec = ParameterSensitivityGridPointModelSpecV1(
        parameter_value=float(parameter_value),
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
        fit_status="RANK_DEFICIENT_BLOCKED",
        fit_reason_codes=reasons,
    )
    return blocked, model_spec


def _compose_exclusion_reason_codes_v0(
    excluded_feature_names: Sequence[str],
) -> tuple[str, ...]:
    return tuple(
        dict.fromkeys(
            [
                *strict_zero_variance_feature_exclusion_reason_codes_v0(excluded_feature_names),
                *(f"{EXCLUSION_REASON_ZERO_VARIANCE}:{name}" for name in excluded_feature_names),
            ]
        )
    )


def _fit_grid_point_with_active_feature_subset_v0(
    *,
    parameter_value: float,
    scaled_rows: Sequence[Mapping[str, object]],
    feature_names: Sequence[str],
    target_name: str,
    validation_fraction: float,
) -> tuple[LinearModelEvidenceV1, ParameterSensitivityGridPointModelSpecV1]:
    x, y, binding = build_feature_matrix_binding(
        scaled_rows,
        feature_names=feature_names,
        target_name=target_name,
        time_name="decision_time",
        validation_policy="TIME_ORDERED",
    )
    requested_feature_names = binding.feature_names
    requested_columns = len(requested_feature_names) + 1
    x_active, active_feature_names, excluded_feature_names = (
        exclude_strict_zero_variance_features_v0(x, requested_feature_names)
    )
    exclusion_reason_codes = _compose_exclusion_reason_codes_v0(excluded_feature_names)

    if not active_feature_names:
        return _blocked_grid_point_model_spec_v0(
            parameter_value=parameter_value,
            requested_feature_names=requested_feature_names,
            excluded_feature_names=excluded_feature_names,
            exclusion_reason_codes=exclusion_reason_codes,
            design_matrix_rows=int(x.shape[0]),
            binding=binding,
        )

    active_binding = _active_feature_binding_v0(
        binding,
        active_feature_names=active_feature_names,
    )
    evidence = fit_ols_lstsq(
        x_active,
        y,
        active_binding,
        fit_intercept=True,
        validation_fraction=validation_fraction,
        evidence_type="parameter_sensitivity_surface_point",
    )
    active_columns = len(active_feature_names) + 1
    required_active_rank = active_columns
    merged_reasons = tuple(dict.fromkeys([*exclusion_reason_codes, *evidence.reason_codes]))
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
        status=evidence.status,
        reason_codes=merged_reasons,
        authority_effect=evidence.authority_effect,
        runtime_effect=evidence.runtime_effect,
    )
    model_spec = ParameterSensitivityGridPointModelSpecV1(
        parameter_value=float(parameter_value),
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
        fit_status=evidence.status,
        fit_reason_codes=merged_reasons,
    )
    return evidence, model_spec


def _validation_rmse(evidence: LinearModelEvidenceV1) -> float:
    diagnostics = evidence.diagnostics
    if diagnostics.r2_validation is None:
        return float("inf")
    train_r2 = diagnostics.r2_train
    validation_r2 = diagnostics.r2_validation
    if not math.isfinite(validation_r2):
        return float("inf")
    gap = max(0.0, float(train_r2) - float(validation_r2))
    return float(diagnostics.rmse * (1.0 + gap))


def _analyze_surface(
    parameter_values: Sequence[float],
    validation_errors: Sequence[float],
    *,
    plateau_relative_tolerance: float,
    fragile_spike_ratio: float,
    min_plateau_points: int,
    max_validation_rmse: float,
) -> Tuple[Dict[str, float], bool, bool, Tuple[float, float] | None, List[str]]:
    reason_codes: List[str] = []
    diagnostics: Dict[str, float] = {}

    finite_errors = [value for value in validation_errors if math.isfinite(value)]
    if not finite_errors:
        reason_codes.append("VALIDATION_ERROR_TOO_HIGH")
        diagnostics["validation_rmse_median"] = float("inf")
        diagnostics["local_sensitivity_max"] = 0.0
        diagnostics["plateau_width_fraction"] = 0.0
        diagnostics["fragility_score"] = 0.0
        return diagnostics, False, False, None, reason_codes

    median_error = float(np.median(finite_errors))
    min_error = float(min(finite_errors))
    max_error = float(max(finite_errors))
    diagnostics["validation_rmse_median"] = median_error
    diagnostics["validation_rmse_min"] = min_error
    diagnostics["validation_rmse_max"] = max_error
    diagnostics["validation_rmse_range"] = max_error - min_error

    local_sensitivities: List[float] = []
    for left, right in zip(validation_errors, validation_errors[1:]):
        if math.isfinite(left) and math.isfinite(right):
            local_sensitivities.append(abs(float(right) - float(left)))
    local_sensitivity_max = float(max(local_sensitivities, default=0.0))
    diagnostics["local_sensitivity_max"] = local_sensitivity_max
    diagnostics["fragility_score"] = local_sensitivity_max / max(median_error, 1e-9)

    if median_error > max_validation_rmse:
        reason_codes.append("VALIDATION_ERROR_TOO_HIGH")

    tolerance = max(min_error * plateau_relative_tolerance, 1e-9)
    plateau_mask = [
        math.isfinite(error) and (error - min_error) <= tolerance for error in validation_errors
    ]
    plateau_runs: List[Tuple[int, int]] = []
    start: int | None = None
    for index, in_plateau in enumerate(plateau_mask):
        if in_plateau and start is None:
            start = index
        elif not in_plateau and start is not None:
            plateau_runs.append((start, index - 1))
            start = None
    if start is not None:
        plateau_runs.append((start, len(plateau_mask) - 1))

    plateau_detected = any((end - start + 1) >= min_plateau_points for start, end in plateau_runs)
    plateau_width = max((end - start + 1 for start, end in plateau_runs), default=0)
    diagnostics["plateau_width_points"] = float(plateau_width)
    diagnostics["plateau_width_fraction"] = plateau_width / max(len(parameter_values), 1)

    robust_region_bounds: Tuple[float, float] | None = None
    if plateau_detected:
        best_run = max(plateau_runs, key=lambda bounds: bounds[1] - bounds[0])
        robust_region_bounds = (
            float(parameter_values[best_run[0]]),
            float(parameter_values[best_run[1]]),
        )
        reason_codes.append("ROBUST_PLATEAU_DETECTED")

    fragile_spike_detected = False
    if len(validation_errors) >= 3:
        for index in range(1, len(validation_errors) - 1):
            center = validation_errors[index]
            left = validation_errors[index - 1]
            right = validation_errors[index + 1]
            if not all(math.isfinite(value) for value in (center, left, right)):
                continue
            neighbor_mean = 0.5 * (float(left) + float(right))
            if neighbor_mean <= 0.0:
                continue
            if float(center) * fragile_spike_ratio <= neighbor_mean:
                fragile_spike_detected = True
                break
    if fragile_spike_detected:
        reason_codes.append("FRAGILE_PARAMETER_SPIKE")

    return diagnostics, plateau_detected, fragile_spike_detected, robust_region_bounds, reason_codes


def fit_parameter_sensitivity_surface(
    records: Sequence[ParameterSensitivityInputV1],
    *,
    grid: ParameterGridSpecV1,
    target_name: str = "target",
    min_samples: int = 8,
    min_grid_points: int = 3,
    validation_fraction: float = 0.25,
    plateau_relative_tolerance: float = 0.15,
    fragile_spike_ratio: float = 3.0,
    min_plateau_points: int = 3,
    max_validation_rmse: float = 0.75,
) -> ParameterSensitivitySurfaceEvidenceV1:
    try:
        rows, feature_names, x_digest, y_digest = _validate_records(records)
    except ValueError as exc:
        message = str(exc)
        if message == "LOOKAHEAD_BLOCKED":
            return ParameterSensitivitySurfaceEvidenceV1(
                evidence_type="parameter_sensitivity_surface",
                model_family="OLS",
                target_name=target_name,
                feature_names=(),
                parameter_name=grid.parameter_name,
                parameter_values=grid.parameter_values,
                n_samples=len(records),
                n_features=0,
                n_grid_points=len(grid.parameter_values),
                solver="numpy.linalg.lstsq",
                fit_intercept=True,
                grid_evidence=(),
                surface_diagnostics={},
                plateau_detected=False,
                fragile_spike_detected=False,
                robust_region_bounds=None,
                feature_matrix_digest="",
                target_digest="",
                validation_policy="TIME_ORDERED",
                status="LEAKAGE_BLOCKED",
                reason_codes=("FEATURE_LEAKAGE_RISK",),
                authority_effect="NONE",
                runtime_effect="NONE",
            )
        raise

    n_samples = len(rows)
    if n_samples < min_samples:
        return ParameterSensitivitySurfaceEvidenceV1(
            evidence_type="parameter_sensitivity_surface",
            model_family="OLS",
            target_name=target_name,
            feature_names=feature_names,
            parameter_name=grid.parameter_name,
            parameter_values=grid.parameter_values,
            n_samples=n_samples,
            n_features=len(feature_names),
            n_grid_points=len(grid.parameter_values),
            solver="numpy.linalg.lstsq",
            fit_intercept=True,
            grid_evidence=(),
            surface_diagnostics={},
            plateau_detected=False,
            fragile_spike_detected=False,
            robust_region_bounds=None,
            feature_matrix_digest=x_digest,
            target_digest=y_digest,
            validation_policy="TIME_ORDERED",
            status="INSUFFICIENT_DATA",
            reason_codes=("INSUFFICIENT_SAMPLE_COUNT",),
            authority_effect="NONE",
            runtime_effect="NONE",
        )

    if grid.scaled_feature_name not in feature_names:
        raise ValueError("TARGET_BINDING_MISSING")

    if len(grid.parameter_values) < min_grid_points:
        return ParameterSensitivitySurfaceEvidenceV1(
            evidence_type="parameter_sensitivity_surface",
            model_family="OLS",
            target_name=target_name,
            feature_names=feature_names,
            parameter_name=grid.parameter_name,
            parameter_values=grid.parameter_values,
            n_samples=n_samples,
            n_features=len(feature_names),
            n_grid_points=len(grid.parameter_values),
            solver="numpy.linalg.lstsq",
            fit_intercept=True,
            grid_evidence=(),
            surface_diagnostics={"grid_point_count": float(len(grid.parameter_values))},
            plateau_detected=False,
            fragile_spike_detected=False,
            robust_region_bounds=None,
            feature_matrix_digest=x_digest,
            target_digest=y_digest,
            validation_policy="TIME_ORDERED",
            status="INSUFFICIENT_DATA",
            reason_codes=("PARAMETER_GRID_TOO_SMALL",),
            authority_effect="NONE",
            runtime_effect="NONE",
        )

    grid_evidence: List[LinearModelEvidenceV1] = []
    grid_point_model_specs: List[ParameterSensitivityGridPointModelSpecV1] = []
    validation_errors: List[float] = []

    for parameter_value in grid.parameter_values:
        scaled_rows = _scale_rows(
            rows,
            scaled_feature_name=grid.scaled_feature_name,
            parameter_value=parameter_value,
        )
        evidence, model_spec = _fit_grid_point_with_active_feature_subset_v0(
            parameter_value=float(parameter_value),
            scaled_rows=scaled_rows,
            feature_names=feature_names,
            target_name=target_name,
            validation_fraction=validation_fraction,
        )
        grid_evidence.append(evidence)
        grid_point_model_specs.append(model_spec)
        validation_errors.append(_validation_rmse(evidence))

    (
        surface_diagnostics,
        plateau_detected,
        fragile_spike_detected,
        robust_region_bounds,
        surface_reasons,
    ) = _analyze_surface(
        grid.parameter_values,
        validation_errors,
        plateau_relative_tolerance=plateau_relative_tolerance,
        fragile_spike_ratio=fragile_spike_ratio,
        min_plateau_points=min_plateau_points,
        max_validation_rmse=max_validation_rmse,
    )

    aggregate_reasons: List[str] = list(surface_reasons)
    aggregate_status = "DIAGNOSTIC_ONLY"

    for evidence in grid_evidence:
        if evidence.status == "INSUFFICIENT_DATA":
            aggregate_status = "INSUFFICIENT_DATA"
            if "INSUFFICIENT_SAMPLE_COUNT" not in aggregate_reasons:
                aggregate_reasons.append("INSUFFICIENT_SAMPLE_COUNT")
        elif evidence.status == "RANK_DEFICIENT_BLOCKED":
            aggregate_status = "RANK_DEFICIENT_BLOCKED"
        elif evidence.status == "ROBUSTNESS_FAILED" and aggregate_status == "DIAGNOSTIC_ONLY":
            aggregate_status = "ROBUSTNESS_FAILED"

    for model_spec in grid_point_model_specs:
        for reason in model_spec.exclusion_reason_codes:
            if reason not in aggregate_reasons:
                aggregate_reasons.append(reason)

    surface_diagnostics["grid_point_count"] = float(len(grid.parameter_values))

    requested_columns = len(feature_names) + 1
    active_feature_names = (
        grid_point_model_specs[0].active_feature_names if grid_point_model_specs else ()
    )
    excluded_feature_names = (
        grid_point_model_specs[0].excluded_feature_names if grid_point_model_specs else ()
    )
    exclusion_reason_codes = (
        grid_point_model_specs[0].exclusion_reason_codes if grid_point_model_specs else ()
    )
    active_columns = len(active_feature_names) + 1 if active_feature_names else 0
    active_ranks = [spec.active_rank for spec in grid_point_model_specs]
    active_rank = min(active_ranks) if active_ranks else 0
    condition_numbers = [
        spec.condition_number
        for spec in grid_point_model_specs
        if math.isfinite(spec.condition_number)
    ]
    condition_number = float(max(condition_numbers, default=float("inf")))
    active_design_full_rank = bool(
        grid_point_model_specs
        and all(
            spec.active_rank == spec.required_active_rank and spec.active_rank > 0
            for spec in grid_point_model_specs
        )
    )
    plateau_detection_admissible = (
        active_design_full_rank and aggregate_status != "RANK_DEFICIENT_BLOCKED"
    )
    fragility_detection_admissible = plateau_detection_admissible

    return ParameterSensitivitySurfaceEvidenceV1(
        evidence_type="parameter_sensitivity_surface",
        model_family="OLS",
        target_name=target_name,
        feature_names=feature_names,
        parameter_name=grid.parameter_name,
        parameter_values=grid.parameter_values,
        n_samples=n_samples,
        n_features=len(feature_names),
        n_grid_points=len(grid.parameter_values),
        solver="numpy.linalg.lstsq",
        fit_intercept=True,
        grid_evidence=tuple(grid_evidence),
        surface_diagnostics=surface_diagnostics,
        plateau_detected=plateau_detected,
        fragile_spike_detected=fragile_spike_detected,
        robust_region_bounds=robust_region_bounds,
        feature_matrix_digest=x_digest,
        target_digest=y_digest,
        validation_policy="TIME_ORDERED",
        status=aggregate_status,
        reason_codes=tuple(dict.fromkeys(aggregate_reasons)),
        authority_effect="NONE",
        runtime_effect="NONE",
        model_spec_version=MODEL_SPEC_VERSION,
        requested_feature_names=feature_names,
        active_feature_names=active_feature_names,
        excluded_feature_names=excluded_feature_names,
        exclusion_reason_codes=exclusion_reason_codes,
        requested_design_matrix_columns=requested_columns,
        active_design_matrix_columns=active_columns,
        requested_rank=requested_columns,
        active_rank=active_rank,
        required_active_rank=active_columns,
        condition_number=condition_number,
        fit_status=aggregate_status,
        fit_reason_codes=tuple(dict.fromkeys(aggregate_reasons)),
        grid_point_model_specs=tuple(grid_point_model_specs),
        plateau_detection_admissible=plateau_detection_admissible,
        fragility_detection_admissible=fragility_detection_admissible,
        economic_interpretation_admissible=False,
    )
