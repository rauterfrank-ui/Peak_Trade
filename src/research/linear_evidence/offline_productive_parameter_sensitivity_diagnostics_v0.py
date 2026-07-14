"""Offline productive parameter sensitivity diagnostics v0.

Consumes manifest-verified productive signal-matrix binding and upstream
orthogonality/factor-exposure context. Diagnostic-only: no parameter selection,
optimization, default mutation, or runtime authority.
"""

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Mapping, Sequence

from src.research.linear_evidence.parameter_sensitivity_productive_contract_v0 import (
    ALLOWED_CALIBRATABLE_PARAMETERS,
    AUTHORITY_EFFECT,
    PARAMETER_CLASS_EXPLICITLY_CALIBRATABLE,
    RUNTIME_EFFECT,
    classify_fleet_parameters_v0,
    stable_digest_v0,
    validate_parameter_variation_allowed_v0,
)
from src.research.linear_evidence.sensitivity import (
    ParameterGridSpecV1,
    ParameterSensitivityInputV1,
    ParameterSensitivitySurfaceEvidenceV1,
    fit_parameter_sensitivity_surface,
)
from src.research.offline_parameter_sensitivity_productive_input_join_materializer_v0 import (
    MaterializationResultV0,
    MaterializationStatus,
)

DIAGNOSTICS_SCOPE_VERSION = "offline_productive_parameter_sensitivity_diagnostics.v0"
DIAGNOSTIC_EVIDENCE_ID = "offline_productive_parameter_sensitivity_diagnostics_v0"
TARGET_NAME = "target"


class ProductiveParameterSensitivityStatus(str, Enum):
    DIAGNOSTIC_ONLY = "DIAGNOSTIC_ONLY"
    ROBUST_REGION_OBSERVED = "ROBUST_REGION_OBSERVED"
    FRAGILE_PARAMETER_RESPONSE = "FRAGILE_PARAMETER_RESPONSE"
    INSUFFICIENT_DATA = "INSUFFICIENT_DATA"
    INSUFFICIENT_ADMISSIBLE_PARAMETER_SURFACE = "INSUFFICIENT_ADMISSIBLE_PARAMETER_SURFACE"
    NON_COMPARABLE_BINDINGS = "NON_COMPARABLE_BINDINGS"
    SOURCE_EVIDENCE_INVALID = "SOURCE_EVIDENCE_INVALID"
    BOUNDARY_VIOLATION_BLOCKED = "BOUNDARY_VIOLATION_BLOCKED"


class ProductiveParameterSensitivityReason(str, Enum):
    BEST_SINGLE_POINT_NOT_EVIDENCE = "BEST_SINGLE_POINT_NOT_EVIDENCE"
    NO_ROBUST_PLATEAU = "NO_ROBUST_PLATEAU"
    BOUNDARY_OPTIMUM_RISK = "BOUNDARY_OPTIMUM_RISK"
    SIGN_OR_DIRECTION_UNSTABLE = "SIGN_OR_DIRECTION_UNSTABLE"
    RESPONSE_DOMINATED_BY_SINGLE_POINT = "RESPONSE_DOMINATED_BY_SINGLE_POINT"
    SAMPLE_COUNT_INSUFFICIENT = "SAMPLE_COUNT_INSUFFICIENT"
    PARAMETER_CLASS_NOT_ADMISSIBLE = "PARAMETER_CLASS_NOT_ADMISSIBLE"
    SOURCE_BINDING_MISMATCH = "SOURCE_BINDING_MISMATCH"
    DATASET_OR_UNIVERSE_MISMATCH = "DATASET_OR_UNIVERSE_MISMATCH"
    COST_POLICY_MISMATCH = "COST_POLICY_MISMATCH"
    RISK_SIZING_SEMANTICS_MISMATCH = "RISK_SIZING_SEMANTICS_MISMATCH"
    RUNTIME_IMPORT_BOUNDARY_VIOLATION = "RUNTIME_IMPORT_BOUNDARY_VIOLATION"
    ROBUST_PLATEAU_DETECTED = "ROBUST_PLATEAU_DETECTED"
    FRAGILE_PARAMETER_SPIKE = "FRAGILE_PARAMETER_SPIKE"


class ProductiveParameterSensitivityValidationError(ValueError):
    """Fail-closed validation for productive parameter sensitivity diagnostics inputs."""


@dataclass(frozen=True)
class ParameterPointResultV0:
    parameter_name: str
    parameter_value: float
    baseline_value: float
    metric_delta_from_baseline: float
    validation_rmse: float
    status: str
    reason_codes: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "parameter_name": self.parameter_name,
            "parameter_value": self.parameter_value,
            "baseline_value": self.baseline_value,
            "metric_delta_from_baseline": self.metric_delta_from_baseline,
            "validation_rmse": self.validation_rmse,
            "status": self.status,
            "reason_codes": list(self.reason_codes),
        }


@dataclass(frozen=True)
class ParameterSensitivityDiagnosticResultV0:
    parameter_name: str
    parameter_class: str
    baseline_value: float
    parameter_values: tuple[float, ...]
    target_name: str
    n_samples: int
    surface_evidence: ParameterSensitivitySurfaceEvidenceV1
    point_results: tuple[ParameterPointResultV0, ...]
    local_stability_metrics: dict[str, float]
    robust_region_bounds: tuple[float, float] | None
    fragility_classification: str
    status: str
    reason_codes: tuple[str, ...]
    authority_effect: str = AUTHORITY_EFFECT
    runtime_effect: str = RUNTIME_EFFECT

    def to_dict(self) -> dict[str, Any]:
        return {
            "parameter_name": self.parameter_name,
            "parameter_class": self.parameter_class,
            "baseline_value": self.baseline_value,
            "parameter_values": list(self.parameter_values),
            "target_name": self.target_name,
            "n_samples": self.n_samples,
            "surface_evidence": self.surface_evidence.to_dict(),
            "point_results": [item.to_dict() for item in self.point_results],
            "local_stability_metrics": dict(self.local_stability_metrics),
            "robust_region_bounds": (
                list(self.robust_region_bounds) if self.robust_region_bounds is not None else None
            ),
            "fragility_classification": self.fragility_classification,
            "status": self.status,
            "reason_codes": list(self.reason_codes),
            "authority_effect": self.authority_effect,
            "runtime_effect": self.runtime_effect,
        }


def _stable_digest(payload: object) -> str:
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def verify_bundle_manifest(path: Path, *, verify_fn: Any) -> int:
    ok, _ = verify_fn(path)
    return 0 if ok else 1


def _time_ordered_records(
    records: Sequence[ParameterSensitivityInputV1],
) -> tuple[ParameterSensitivityInputV1, ...]:
    return tuple(sorted(records, key=lambda record: (record.decision_time, record.instrument_id)))


def _resolve_baseline_value(
    *,
    parameter_name: str,
    grid_spec: ParameterGridSpecV1,
    binding_baseline_fee_bps: float,
    binding_baseline_slippage_bps: float,
) -> float:
    if parameter_name == "fee_bps":
        return float(binding_baseline_fee_bps)
    if parameter_name == "slippage_bps":
        return float(binding_baseline_slippage_bps)
    values = grid_spec.parameter_values
    if not values:
        return 0.0
    return float(values[len(values) // 2])


def _validation_rmse_for_point(
    evidence: ParameterSensitivitySurfaceEvidenceV1,
    *,
    parameter_value: float,
) -> float:
    for index, value in enumerate(evidence.parameter_values):
        if float(value) == float(parameter_value):
            point = evidence.grid_evidence[index]
            diagnostics = point.diagnostics
            if diagnostics.r2_validation is None:
                return float("inf")
            gap = max(0.0, float(diagnostics.r2_train) - float(diagnostics.r2_validation))
            return float(diagnostics.rmse * (1.0 + gap))
    return float("inf")


def _build_point_results(
    *,
    parameter_name: str,
    baseline_value: float,
    evidence: ParameterSensitivitySurfaceEvidenceV1,
) -> tuple[ParameterPointResultV0, ...]:
    if not evidence.grid_evidence:
        return ()
    baseline_rmse = _validation_rmse_for_point(evidence, parameter_value=baseline_value)
    results: list[ParameterPointResultV0] = []
    for parameter_value in evidence.parameter_values:
        validation_rmse = _validation_rmse_for_point(evidence, parameter_value=parameter_value)
        if math.isfinite(baseline_rmse) and math.isfinite(validation_rmse):
            metric_delta = validation_rmse - baseline_rmse
        else:
            metric_delta = float("nan")
        results.append(
            ParameterPointResultV0(
                parameter_name=parameter_name,
                parameter_value=float(parameter_value),
                baseline_value=baseline_value,
                metric_delta_from_baseline=float(metric_delta),
                validation_rmse=float(validation_rmse),
                status=evidence.status,
                reason_codes=evidence.reason_codes,
            )
        )
    return tuple(results)


def _local_stability_metrics(
    *,
    point_results: Sequence[ParameterPointResultV0],
    surface_diagnostics: Mapping[str, float],
) -> dict[str, float]:
    deltas = [
        item.metric_delta_from_baseline
        for item in point_results
        if math.isfinite(item.metric_delta_from_baseline)
    ]
    if not deltas:
        return {
            "response_span": 0.0,
            "response_variance": 0.0,
            "local_sensitivity_max": float(surface_diagnostics.get("local_sensitivity_max", 0.0)),
            "direction_stability_score": 0.0,
            "monotonic_response": 0.0,
        }
    signs = [1.0 if delta >= 0.0 else -1.0 for delta in deltas if delta != 0.0]
    direction_stability = 1.0 if len(set(signs)) <= 1 else 0.0
    monotonic = 1.0
    for left, right in zip(deltas, deltas[1:]):
        if (right - left) * (1 if deltas[-1] >= deltas[0] else -1) < 0:
            monotonic = 0.0
            break
    return {
        "response_span": float(max(deltas) - min(deltas)),
        "response_variance": float(
            sum((delta - sum(deltas) / len(deltas)) ** 2 for delta in deltas) / len(deltas)
        ),
        "local_sensitivity_max": float(surface_diagnostics.get("local_sensitivity_max", 0.0)),
        "direction_stability_score": direction_stability,
        "monotonic_response": monotonic,
    }


def _boundary_optimum_risk(
    *,
    parameter_values: Sequence[float],
    validation_errors: Sequence[float],
) -> bool:
    finite = [
        (index, error) for index, error in enumerate(validation_errors) if math.isfinite(error)
    ]
    if len(finite) < 2:
        return False
    best_index = min(finite, key=lambda item: item[1])[0]
    return best_index in {0, len(parameter_values) - 1}


def _response_dominated_by_single_point(
    validation_errors: Sequence[float],
) -> bool:
    finite = [error for error in validation_errors if math.isfinite(error)]
    if len(finite) < 3:
        return False
    min_error = min(finite)
    median_error = sorted(finite)[len(finite) // 2]
    return min_error > 0 and median_error / min_error >= 3.0


def _classify_surface_status(
    *,
    evidence: ParameterSensitivitySurfaceEvidenceV1,
    parameter_name: str,
) -> tuple[str, tuple[str, ...], str]:
    reason_codes: list[str] = []
    if validate_parameter_variation_allowed_v0(parameter_name) is not None:
        return (
            ProductiveParameterSensitivityStatus.INSUFFICIENT_ADMISSIBLE_PARAMETER_SURFACE.value,
            (ProductiveParameterSensitivityReason.PARAMETER_CLASS_NOT_ADMISSIBLE.value,),
            "not_admissible",
        )

    validation_errors = [
        _validation_rmse_for_point(evidence, parameter_value=value)
        for value in evidence.parameter_values
    ]

    if evidence.status == "LEAKAGE_BLOCKED":
        return (
            ProductiveParameterSensitivityStatus.BOUNDARY_VIOLATION_BLOCKED.value,
            ("FEATURE_LEAKAGE_RISK",),
            "blocked",
        )
    if evidence.status == "INSUFFICIENT_DATA":
        return (
            ProductiveParameterSensitivityStatus.INSUFFICIENT_DATA.value,
            (ProductiveParameterSensitivityReason.SAMPLE_COUNT_INSUFFICIENT.value,),
            "insufficient_data",
        )
    if evidence.status == "RANK_DEFICIENT_BLOCKED":
        return (
            ProductiveParameterSensitivityStatus.BOUNDARY_VIOLATION_BLOCKED.value,
            ("RANK_DEFICIENT_FEATURE_MATRIX",),
            "rank_deficient",
        )

    if evidence.plateau_detected:
        reason_codes.append(ProductiveParameterSensitivityReason.ROBUST_PLATEAU_DETECTED.value)
    else:
        reason_codes.append(ProductiveParameterSensitivityReason.NO_ROBUST_PLATEAU.value)

    if evidence.fragile_spike_detected:
        reason_codes.append(ProductiveParameterSensitivityReason.FRAGILE_PARAMETER_SPIKE.value)

    if _boundary_optimum_risk(
        parameter_values=evidence.parameter_values,
        validation_errors=validation_errors,
    ):
        reason_codes.append(ProductiveParameterSensitivityReason.BOUNDARY_OPTIMUM_RISK.value)

    if _response_dominated_by_single_point(validation_errors):
        reason_codes.append(
            ProductiveParameterSensitivityReason.RESPONSE_DOMINATED_BY_SINGLE_POINT.value
        )

    reason_codes.append(ProductiveParameterSensitivityReason.BEST_SINGLE_POINT_NOT_EVIDENCE.value)

    for existing in evidence.reason_codes:
        if existing not in reason_codes:
            reason_codes.append(existing)

    if evidence.fragile_spike_detected:
        status = ProductiveParameterSensitivityStatus.FRAGILE_PARAMETER_RESPONSE.value
        fragility = "fragile_spike"
    elif evidence.plateau_detected:
        status = ProductiveParameterSensitivityStatus.ROBUST_REGION_OBSERVED.value
        fragility = "robust_plateau"
    else:
        status = ProductiveParameterSensitivityStatus.DIAGNOSTIC_ONLY.value
        fragility = "diagnostic_only"

    return status, tuple(dict.fromkeys(reason_codes)), fragility


def classify_parameter_sensitivity_surface_v0(
    *,
    evidence: ParameterSensitivitySurfaceEvidenceV1,
    parameter_name: str,
) -> tuple[str, tuple[str, ...], str]:
    return _classify_surface_status(evidence=evidence, parameter_name=parameter_name)


def fit_productive_parameter_sensitivity_v0(
    *,
    records: Sequence[ParameterSensitivityInputV1],
    grid_spec: ParameterGridSpecV1,
    baseline_fee_bps: float,
    baseline_slippage_bps: float,
) -> ParameterSensitivityDiagnosticResultV0:
    ordered = _time_ordered_records(records)
    evidence = fit_parameter_sensitivity_surface(ordered, grid=grid_spec, target_name=TARGET_NAME)
    baseline_value = _resolve_baseline_value(
        parameter_name=grid_spec.parameter_name,
        grid_spec=grid_spec,
        binding_baseline_fee_bps=baseline_fee_bps,
        binding_baseline_slippage_bps=baseline_slippage_bps,
    )
    point_results = _build_point_results(
        parameter_name=grid_spec.parameter_name,
        baseline_value=baseline_value,
        evidence=evidence,
    )
    local_metrics = _local_stability_metrics(
        point_results=point_results,
        surface_diagnostics=evidence.surface_diagnostics,
    )
    status, reason_codes, fragility = _classify_surface_status(
        evidence=evidence,
        parameter_name=grid_spec.parameter_name,
    )
    return ParameterSensitivityDiagnosticResultV0(
        parameter_name=grid_spec.parameter_name,
        parameter_class=PARAMETER_CLASS_EXPLICITLY_CALIBRATABLE,
        baseline_value=baseline_value,
        parameter_values=grid_spec.parameter_values,
        target_name=TARGET_NAME,
        n_samples=evidence.n_samples,
        surface_evidence=evidence,
        point_results=point_results,
        local_stability_metrics=local_metrics,
        robust_region_bounds=evidence.robust_region_bounds,
        fragility_classification=fragility,
        status=status,
        reason_codes=reason_codes,
    )


def build_parameter_surface_binding_v0(
    materialization: MaterializationResultV0,
) -> dict[str, Any]:
    binding = materialization.join_result.binding
    grid = materialization.join_result.grid
    return {
        "diagnostic_evidence_id": DIAGNOSTIC_EVIDENCE_ID,
        "diagnostics_scope_version": DIAGNOSTICS_SCOPE_VERSION,
        "binding_digest": binding.binding_digest,
        "signal_matrix_digest": binding.signal_matrix_digest,
        "grid_id": binding.grid_id,
        "grid_digest": binding.grid_digest,
        "strategy_id": binding.strategy_id,
        "strategy_version": binding.strategy_version,
        "baseline_fee_bps": binding.baseline_fee_bps,
        "baseline_slippage_bps": binding.baseline_slippage_bps,
        "admissible_parameters": list(ALLOWED_CALIBRATABLE_PARAMETERS),
        "parameter_names": list(grid.parameter_names),
        "parameter_value_grids": {
            name: list(values) for name, values in zip(grid.parameter_names, grid.parameter_values)
        },
        "dataset_digest": grid.data_digest_or_explicit_missing,
        "implementation_digest": materialization.provenance.implementation_digest,
        "row_count_before_filter": materialization.join_result.row_count_before_filter,
        "row_count_after_filter": materialization.join_result.row_count_after_filter,
        "authority_effect": AUTHORITY_EFFECT,
        "runtime_effect": RUNTIME_EFFECT,
    }


def build_parameter_classification_v0() -> list[dict[str, Any]]:
    rows = classify_fleet_parameters_v0()
    admissible = {
        name
        for name in ALLOWED_CALIBRATABLE_PARAMETERS
        if validate_parameter_variation_allowed_v0(name) is None
    }
    payload: list[dict[str, Any]] = []
    for row in rows:
        if (
            row.parameter_name not in admissible
            and row.parameter_class != PARAMETER_CLASS_EXPLICITLY_CALIBRATABLE
        ):
            continue
        payload.append(
            {
                "strategy_name": row.strategy_name,
                "parameter_name": row.parameter_name,
                "parameter_class": row.parameter_class,
                "baseline_value": row.baseline_value,
                "mutation_allowed": row.mutation_allowed,
                "sensitivity_variation_allowed": row.sensitivity_variation_allowed,
            }
        )
    return sorted(payload, key=lambda item: (item["strategy_name"], item["parameter_name"]))


def build_authority_boundary_v0() -> dict[str, Any]:
    return {
        "offline_only": True,
        "authority_effect": AUTHORITY_EFFECT,
        "runtime_effect": RUNTIME_EFFECT,
        "parameter_default_changed": False,
        "parameter_optimization_executed": False,
        "best_point_selected": False,
        "economic_evaluation_executed": False,
        "promotion_pass_created": False,
        "runtime_rewire_admissible": False,
        "interpretation_boundary": [
            "Sensitivity surfaces report local stability and fragility only.",
            "Robust plateaus do not authorize parameter changes.",
            "Boundary optima remain diagnostic risk signals only.",
            "No best-point selection or default mutation is permitted.",
        ],
        "forbidden_claims": [
            "automatic parameter selection",
            "parameter default change",
            "economic validity proof",
            "promotion admissibility",
            "runtime authority",
        ],
    }


def build_failure_taxonomy_v0(
    results: Mapping[str, ParameterSensitivityDiagnosticResultV0],
) -> dict[str, Any]:
    statuses = {item.status for item in results.values()}
    reasons: set[str] = set()
    for item in results.values():
        reasons.update(item.reason_codes)
    return {
        "supported_statuses": sorted(item.value for item in ProductiveParameterSensitivityStatus),
        "supported_reason_codes": sorted(
            item.value for item in ProductiveParameterSensitivityReason
        ),
        "observed_statuses": sorted(statuses),
        "observed_reason_codes": sorted(reasons),
    }


def build_parameter_sensitivity_interpretation_v0(
    *,
    results: Mapping[str, ParameterSensitivityDiagnosticResultV0],
    materialization: MaterializationResultV0,
) -> dict[str, Any]:
    stable_parameters: list[str] = []
    fragile_parameters: list[str] = []
    robust_regions: dict[str, list[float] | None] = {}
    boundary_risks: list[str] = []
    uncertainties: list[str] = []

    for name, result in sorted(results.items()):
        if result.status == ProductiveParameterSensitivityStatus.ROBUST_REGION_OBSERVED.value:
            stable_parameters.append(name)
            robust_regions[name] = (
                list(result.robust_region_bounds) if result.robust_region_bounds else None
            )
        elif result.status == ProductiveParameterSensitivityStatus.FRAGILE_PARAMETER_RESPONSE.value:
            fragile_parameters.append(name)
        if ProductiveParameterSensitivityReason.BOUNDARY_OPTIMUM_RISK.value in result.reason_codes:
            boundary_risks.append(name)
        if result.status == ProductiveParameterSensitivityStatus.INSUFFICIENT_DATA.value:
            uncertainties.append(f"{name}: insufficient sample count")

    comparable = materialization.status == MaterializationStatus.PASS
    if not comparable:
        uncertainties.append("productive binding not comparable across requested surfaces")

    return {
        "what_is_stable": stable_parameters,
        "what_is_fragile": fragile_parameters,
        "robust_regions_observed": robust_regions,
        "boundary_dependent_parameters": boundary_risks,
        "results_comparable": comparable,
        "remaining_uncertainties": uncertainties,
        "recommendation_policy": "DIAGNOSTIC_ONLY_NO_PARAMETER_CHANGE",
        "authority_effect": AUTHORITY_EFFECT,
        "runtime_effect": RUNTIME_EFFECT,
    }


def build_productive_parameter_sensitivity_diagnostics_artifacts_v0(
    *,
    materialization: MaterializationResultV0,
    source_evidence_refs: Sequence[str],
) -> dict[str, Any]:
    if materialization.status != MaterializationStatus.PASS:
        binding = build_parameter_surface_binding_v0(materialization)
        classification = build_parameter_classification_v0()
        if not ALLOWED_CALIBRATABLE_PARAMETERS:
            status = (
                ProductiveParameterSensitivityStatus.INSUFFICIENT_ADMISSIBLE_PARAMETER_SURFACE.value
            )
        else:
            status = ProductiveParameterSensitivityStatus.NON_COMPARABLE_BINDINGS.value
        return {
            "diagnostics_scope_version": DIAGNOSTICS_SCOPE_VERSION,
            "diagnostic_evidence_id": DIAGNOSTIC_EVIDENCE_ID,
            "source_evidence_refs": list(source_evidence_refs),
            "parameter_surface_binding": binding,
            "parameter_classification": classification,
            "parameter_sensitivity_results": {},
            "failure_taxonomy": build_failure_taxonomy_v0({}),
            "authority_boundary": build_authority_boundary_v0(),
            "parameter_sensitivity_interpretation": {
                "what_is_stable": [],
                "what_is_fragile": [],
                "robust_regions_observed": {},
                "boundary_dependent_parameters": [],
                "results_comparable": False,
                "remaining_uncertainties": ["productive materialization did not pass"],
                "recommendation_policy": "DIAGNOSTIC_ONLY_NO_PARAMETER_CHANGE",
                "authority_effect": AUTHORITY_EFFECT,
                "runtime_effect": RUNTIME_EFFECT,
            },
            "aggregate_status": status,
            "output_digest": _stable_digest(
                {
                    "status": status,
                    "binding_digest": binding.get("binding_digest", ""),
                }
            ),
        }

    binding = materialization.join_result.binding
    results: dict[str, ParameterSensitivityDiagnosticResultV0] = {}
    for grid_spec in materialization.join_result.grid_specs:
        results[grid_spec.parameter_name] = fit_productive_parameter_sensitivity_v0(
            records=materialization.records,
            grid_spec=grid_spec,
            baseline_fee_bps=binding.baseline_fee_bps,
            baseline_slippage_bps=binding.baseline_slippage_bps,
        )

    surface_binding = build_parameter_surface_binding_v0(materialization)
    classification = build_parameter_classification_v0()
    interpretation = build_parameter_sensitivity_interpretation_v0(
        results=results,
        materialization=materialization,
    )
    failure_taxonomy = build_failure_taxonomy_v0(results)
    authority_boundary = build_authority_boundary_v0()

    aggregate_status = ProductiveParameterSensitivityStatus.DIAGNOSTIC_ONLY.value
    statuses = {item.status for item in results.values()}
    if ProductiveParameterSensitivityStatus.FRAGILE_PARAMETER_RESPONSE.value in statuses:
        aggregate_status = ProductiveParameterSensitivityStatus.FRAGILE_PARAMETER_RESPONSE.value
    elif ProductiveParameterSensitivityStatus.ROBUST_REGION_OBSERVED.value in statuses:
        aggregate_status = ProductiveParameterSensitivityStatus.ROBUST_REGION_OBSERVED.value
    elif ProductiveParameterSensitivityStatus.INSUFFICIENT_DATA.value in statuses:
        aggregate_status = ProductiveParameterSensitivityStatus.INSUFFICIENT_DATA.value

    output_digest = _stable_digest(
        {
            "scope_version": DIAGNOSTICS_SCOPE_VERSION,
            "surface_binding": surface_binding,
            "results": {key: value.to_dict() for key, value in sorted(results.items())},
            "interpretation": interpretation,
        }
    )

    return {
        "diagnostics_scope_version": DIAGNOSTICS_SCOPE_VERSION,
        "diagnostic_evidence_id": DIAGNOSTIC_EVIDENCE_ID,
        "source_evidence_refs": list(source_evidence_refs),
        "parameter_surface_binding": surface_binding,
        "parameter_classification": classification,
        "parameter_sensitivity_results": {
            key: value.to_dict() for key, value in sorted(results.items())
        },
        "failure_taxonomy": failure_taxonomy,
        "authority_boundary": authority_boundary,
        "parameter_sensitivity_interpretation": interpretation,
        "aggregate_status": aggregate_status,
        "output_digest": output_digest,
    }


__all__ = [
    "DIAGNOSTIC_EVIDENCE_ID",
    "DIAGNOSTICS_SCOPE_VERSION",
    "ProductiveParameterSensitivityReason",
    "ProductiveParameterSensitivityStatus",
    "ProductiveParameterSensitivityValidationError",
    "ParameterSensitivityDiagnosticResultV0",
    "build_authority_boundary_v0",
    "build_failure_taxonomy_v0",
    "build_parameter_classification_v0",
    "build_parameter_sensitivity_interpretation_v0",
    "build_parameter_surface_binding_v0",
    "build_productive_parameter_sensitivity_diagnostics_artifacts_v0",
    "classify_parameter_sensitivity_surface_v0",
    "fit_productive_parameter_sensitivity_v0",
    "verify_bundle_manifest",
]
