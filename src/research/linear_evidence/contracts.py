from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping, Sequence


_ALLOWED_LINEAR_STATUSES = {
    "DIAGNOSTIC_ONLY",
    "CALIBRATION_CANDIDATE",
    "CALIBRATION_VALIDATION_FAILED",
    "CALIBRATION_VALIDATED_OFFLINE",
    "ROBUSTNESS_FAILED",
    "INSUFFICIENT_DATA",
    "LEAKAGE_BLOCKED",
    "RANK_DEFICIENT_BLOCKED",
}


@dataclass(frozen=True)
class FeatureMatrixBindingV1:
    target_name: str
    feature_names: tuple[str, ...]
    n_samples: int
    n_features: int
    feature_matrix_digest: str
    target_digest: str
    validation_policy: str
    time_range: Mapping[str, str]
    row_count_before_filter: int
    row_count_after_filter: int
    dropped_rows_by_reason: Mapping[str, int] = field(default_factory=dict)
    status: str = "DIAGNOSTIC_ONLY"
    reason_codes: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.validation_policy != "TIME_ORDERED":
            raise ValueError("RANDOM_VALIDATION_SPLIT_BLOCKED")
        if self.n_samples < 1 or self.n_features < 1:
            raise ValueError("INSUFFICIENT_DATA")
        if self.n_features != len(self.feature_names):
            raise ValueError("FEATURE_COUNT_MISMATCH")
        if self.status not in _ALLOWED_LINEAR_STATUSES:
            raise ValueError(f"unsupported linear evidence status: {self.status}")


@dataclass(frozen=True)
class LinearModelDiagnosticsV1:
    rank: int
    condition_number: float
    rmse: float
    mae: float
    max_abs_error: float
    r2_train: float
    r2_validation: float | None
    residual_mean: float
    residual_std: float
    outlier_count: int


@dataclass(frozen=True)
class LinearModelEvidenceV1:
    evidence_type: str
    model_family: str
    target_name: str
    feature_names: tuple[str, ...]
    n_samples: int
    n_features: int
    solver: str
    fit_intercept: bool
    coefficients: Mapping[str, float]
    diagnostics: LinearModelDiagnosticsV1
    feature_matrix_digest: str
    target_digest: str
    config_digest: str
    time_range: Mapping[str, str]
    instrument_universe_digest: str
    row_count_before_filter: int
    row_count_after_filter: int
    dropped_rows_by_reason: Mapping[str, int]
    validation_policy: str
    cost_policy_output: str
    status: str
    reason_codes: tuple[str, ...]
    authority_effect: str = "NONE"
    runtime_effect: str = "NONE"

    def __post_init__(self) -> None:
        if self.solver != "numpy.linalg.lstsq":
            raise ValueError("unsupported solver for v0")
        if self.validation_policy != "TIME_ORDERED":
            raise ValueError("RANDOM_VALIDATION_SPLIT_BLOCKED")
        if self.authority_effect != "NONE" or self.runtime_effect != "NONE":
            raise ValueError("linear evidence must be authority-neutral")
        if self.cost_policy_output not in {"diagnostic_only", "conservative_review_candidate"}:
            raise ValueError("COST_POLICY_BELOW_FLOOR_BLOCKED")
        if self.status not in _ALLOWED_LINEAR_STATUSES:
            raise ValueError(f"unsupported linear evidence status: {self.status}")


@dataclass(frozen=True)
class CostModelCalibrationEvidenceV1:
    linear_model_evidence: LinearModelEvidenceV1
    rmse_bps: float
    mae_bps: float
    max_abs_error_bps: float
    p75_abs_error_bps: float
    p90_abs_error_bps: float
    stress_cost_bps: float
    calibrated_cost_policy: str
    status: str
    reason_codes: tuple[str, ...]

    def __post_init__(self) -> None:
        if self.calibrated_cost_policy != "CONSERVATIVE_NOT_MEAN":
            raise ValueError("CALIBRATED_COST_POLICY_MUST_BE_CONSERVATIVE_NOT_MEAN")
        if self.linear_model_evidence.authority_effect != "NONE":
            raise ValueError("OLS_COST_DIAGNOSTICS_CAN_NOT_SET_AUTHORITY")
        if self.status not in _ALLOWED_LINEAR_STATUSES:
            raise ValueError(f"unsupported calibration evidence status: {self.status}")


def to_jsonable(value: Any) -> Any:
    if hasattr(value, "__dataclass_fields__"):
        return {k: to_jsonable(getattr(value, k)) for k in value.__dataclass_fields__}
    if isinstance(value, Mapping):
        return {str(k): to_jsonable(v) for k, v in value.items()}
    if isinstance(value, (tuple, list)):
        return [to_jsonable(v) for v in value]
    return value
