from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Mapping, Sequence, Tuple
import hashlib
import json
import math

import numpy as np

from .contracts import LinearModelEvidenceV1
from .feature_matrix import build_feature_matrix_binding
from .fitters import fit_ols_lstsq


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
                }
                for parameter_value, evidence in zip(self.parameter_values, self.grid_evidence)
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
    validation_errors: List[float] = []

    for parameter_value in grid.parameter_values:
        scaled_rows = _scale_rows(
            rows,
            scaled_feature_name=grid.scaled_feature_name,
            parameter_value=parameter_value,
        )
        x, y, binding = build_feature_matrix_binding(
            scaled_rows,
            feature_names=feature_names,
            target_name=target_name,
            time_name="decision_time",
            validation_policy="TIME_ORDERED",
        )
        evidence = fit_ols_lstsq(
            x,
            y,
            binding,
            fit_intercept=True,
            validation_fraction=validation_fraction,
            evidence_type="parameter_sensitivity_surface_point",
        )
        grid_evidence.append(evidence)
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

    surface_diagnostics["grid_point_count"] = float(len(grid.parameter_values))

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
    )
