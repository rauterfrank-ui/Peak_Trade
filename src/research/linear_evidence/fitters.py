from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass

import numpy as np

from .contracts import FeatureMatrixBindingV1, LinearModelDiagnosticsV1, LinearModelEvidenceV1

_UNIQUE_ROUND_DECIMALS = 12
REASON_CONSTANT_TARGET = "CONSTANT_TARGET"
REASON_ZERO_VARIANCE_FEATURE = "ZERO_VARIANCE_FEATURE"
REASON_CONSTANT_FEATURE_COLLINEAR_WITH_INTERCEPT = "CONSTANT_FEATURE_COLLINEAR_WITH_INTERCEPT"
REASON_RANK_DEFICIENT_FEATURE_MATRIX = "RANK_DEFICIENT_FEATURE_MATRIX"
REASON_STRICT_ZERO_VARIANCE_FEATURE_EXCLUDED = "STRICT_ZERO_VARIANCE_FEATURE_EXCLUDED"


@dataclass(frozen=True)
class OlsFitPrecheckDiagnosticsV0:
    target_variance: float
    target_unique_value_count: int
    target_is_constant: bool
    feature_variances: Mapping[str, float]
    feature_unique_value_counts: Mapping[str, int]
    zero_variance_feature_names: tuple[str, ...]
    intercept_collinear_feature_names: tuple[str, ...]
    reason_codes: tuple[str, ...]


def _digest(payload: object) -> str:
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str).encode()
    ).hexdigest()


def _r2(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    denom = float(np.sum((y_true - float(np.mean(y_true))) ** 2))
    if denom == 0.0:
        return 0.0
    return 1.0 - float(np.sum((y_true - y_pred) ** 2)) / denom


def _target_is_constant(y: np.ndarray) -> bool:
    if y.size == 0:
        return False
    if float(np.var(y)) == 0.0:
        return True
    if int(len(np.unique(np.round(y, _UNIQUE_ROUND_DECIMALS)))) == 1:
        return True
    return float(np.max(y) - np.min(y)) <= 1e-9


def _feature_unique_value_count(column: np.ndarray) -> int:
    return int(len(np.unique(np.round(column, _UNIQUE_ROUND_DECIMALS))))


def exclude_strict_zero_variance_features_v0(
    x: np.ndarray,
    feature_names: Sequence[str],
) -> tuple[np.ndarray, tuple[str, ...], tuple[str, ...]]:
    """Deterministically exclude strictly zero-variance feature columns.

    Predicate: exact float(np.var(column)) == 0.0 on the canonical float matrix.
    Exclusion order is stable w.r.t. feature_names.
    """
    if x.size == 0 or not feature_names:
        return x, tuple(feature_names), ()
    excluded: list[str] = []
    keep_indices: list[int] = []
    for index, name in enumerate(feature_names):
        if float(np.var(x[:, index])) == 0.0:
            excluded.append(str(name))
        else:
            keep_indices.append(index)
    if not excluded:
        return x, tuple(feature_names), ()
    if not keep_indices:
        return np.empty((x.shape[0], 0), dtype=float), (), tuple(excluded)
    kept = x[:, keep_indices]
    kept_names = tuple(feature_names[index] for index in keep_indices)
    return kept, kept_names, tuple(excluded)


def strict_zero_variance_feature_exclusion_reason_codes_v0(
    excluded_feature_names: Sequence[str],
) -> tuple[str, ...]:
    return tuple(
        f"{REASON_STRICT_ZERO_VARIANCE_FEATURE_EXCLUDED}:{name}" for name in excluded_feature_names
    )


def _zero_variance_feature_names(x: np.ndarray, feature_names: Sequence[str]) -> tuple[str, ...]:
    names: list[str] = []
    for index, name in enumerate(feature_names):
        if float(np.var(x[:, index])) == 0.0:
            names.append(str(name))
    return tuple(sorted(names))


def _intercept_collinear_feature_names(
    x: np.ndarray,
    feature_names: Sequence[str],
) -> tuple[str, ...]:
    if x.shape[0] == 0:
        return ()
    ones = np.ones(x.shape[0])
    names: list[str] = []
    for index, name in enumerate(feature_names):
        column = x[:, index]
        if float(np.var(column)) == 0.0 and np.allclose(column, float(column[0]) * ones):
            names.append(str(name))
    return tuple(sorted(names))


def compose_ols_precheck_reason_codes_v0(
    *,
    target_is_constant: bool,
    zero_variance_feature_names: Sequence[str],
    intercept_collinear_feature_names: Sequence[str],
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if target_is_constant:
        reason_codes.append(REASON_CONSTANT_TARGET)
    for name in sorted(str(value) for value in zero_variance_feature_names):
        reason_codes.append(f"{REASON_ZERO_VARIANCE_FEATURE}:{name}")
    for name in sorted(str(value) for value in intercept_collinear_feature_names):
        reason_codes.append(f"{REASON_CONSTANT_FEATURE_COLLINEAR_WITH_INTERCEPT}:{name}")
    return tuple(reason_codes)


def compute_ols_fit_precheck_v0(
    x: np.ndarray,
    y: np.ndarray,
    feature_names: Sequence[str],
    *,
    fit_intercept: bool = True,
) -> OlsFitPrecheckDiagnosticsV0:
    if x.ndim != 2 or y.ndim != 1:
        raise ValueError("FEATURE_TARGET_SHAPE_MISMATCH")
    if x.shape[0] != y.shape[0]:
        raise ValueError("FEATURE_TARGET_ROW_MISMATCH")
    if x.shape[1] != len(feature_names):
        raise ValueError("FEATURE_COUNT_MISMATCH")

    zero_variance_feature_names = _zero_variance_feature_names(x, feature_names)
    intercept_collinear_feature_names = (
        _intercept_collinear_feature_names(x, feature_names) if fit_intercept else ()
    )
    target_is_constant = _target_is_constant(y)
    feature_variances = {
        str(name): float(np.var(x[:, index])) for index, name in enumerate(feature_names)
    }
    feature_unique_value_counts = {
        str(name): _feature_unique_value_count(x[:, index])
        for index, name in enumerate(feature_names)
    }
    return OlsFitPrecheckDiagnosticsV0(
        target_variance=float(np.var(y)),
        target_unique_value_count=_feature_unique_value_count(y),
        target_is_constant=target_is_constant,
        feature_variances=feature_variances,
        feature_unique_value_counts=feature_unique_value_counts,
        zero_variance_feature_names=zero_variance_feature_names,
        intercept_collinear_feature_names=intercept_collinear_feature_names,
        reason_codes=compose_ols_precheck_reason_codes_v0(
            target_is_constant=target_is_constant,
            zero_variance_feature_names=zero_variance_feature_names,
            intercept_collinear_feature_names=intercept_collinear_feature_names,
        ),
    )


def _blocked_constant_target_evidence_v0(
    precheck: OlsFitPrecheckDiagnosticsV0,
    binding: FeatureMatrixBindingV1,
    *,
    fit_intercept: bool,
    validation_fraction: float,
    evidence_type: str,
    instrument_universe_digest: str,
) -> LinearModelEvidenceV1:
    has_co_degeneracy = bool(
        precheck.zero_variance_feature_names or precheck.intercept_collinear_feature_names
    )
    status = "RANK_DEFICIENT_BLOCKED" if has_co_degeneracy else "INSUFFICIENT_DATA"
    reasons = list(precheck.reason_codes)
    if has_co_degeneracy and REASON_RANK_DEFICIENT_FEATURE_MATRIX not in reasons:
        reasons.append(REASON_RANK_DEFICIENT_FEATURE_MATRIX)

    diagnostics = LinearModelDiagnosticsV1(
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
    )
    return LinearModelEvidenceV1(
        evidence_type=evidence_type,
        model_family="OLS",
        target_name=binding.target_name,
        feature_names=binding.feature_names,
        n_samples=binding.n_samples,
        n_features=binding.n_features,
        solver="numpy.linalg.lstsq",
        fit_intercept=fit_intercept,
        coefficients={},
        diagnostics=diagnostics,
        feature_matrix_digest=binding.feature_matrix_digest,
        target_digest=binding.target_digest,
        config_digest=_digest(
            {"fit_intercept": fit_intercept, "validation_fraction": validation_fraction}
        ),
        time_range=binding.time_range,
        instrument_universe_digest=instrument_universe_digest,
        row_count_before_filter=binding.row_count_before_filter,
        row_count_after_filter=binding.row_count_after_filter,
        dropped_rows_by_reason=binding.dropped_rows_by_reason,
        validation_policy=binding.validation_policy,
        cost_policy_output="diagnostic_only",
        status=status,
        reason_codes=tuple(reasons),
    )


def fit_ols_lstsq(
    x: np.ndarray,
    y: np.ndarray,
    binding: FeatureMatrixBindingV1,
    *,
    fit_intercept: bool = True,
    validation_fraction: float = 0.25,
    evidence_type: str = "CostModelCalibrationEvidenceV1",
    instrument_universe_digest: str = "fixture_universe",
) -> LinearModelEvidenceV1:
    if x.ndim != 2 or y.ndim != 1:
        raise ValueError("FEATURE_TARGET_SHAPE_MISMATCH")
    if x.shape[0] != y.shape[0]:
        raise ValueError("FEATURE_TARGET_ROW_MISMATCH")
    if x.shape[0] < max(4, x.shape[1] + 2):
        raise ValueError("INSUFFICIENT_DATA")

    precheck = compute_ols_fit_precheck_v0(
        x,
        y,
        binding.feature_names,
        fit_intercept=fit_intercept,
    )

    if precheck.target_is_constant:
        return _blocked_constant_target_evidence_v0(
            precheck,
            binding,
            fit_intercept=fit_intercept,
            validation_fraction=validation_fraction,
            evidence_type=evidence_type,
            instrument_universe_digest=instrument_universe_digest,
        )

    n = x.shape[0]
    split = max(1, min(n - 1, int(round(n * (1.0 - validation_fraction)))))
    x_train = x[:split]
    y_train = y[:split]
    x_validation = x[split:]
    y_validation = y[split:]

    design_train = (
        np.column_stack([np.ones(x_train.shape[0]), x_train]) if fit_intercept else x_train
    )
    design_all = np.column_stack([np.ones(x.shape[0]), x]) if fit_intercept else x

    coeffs, _, rank, _ = np.linalg.lstsq(design_train, y_train, rcond=None)
    y_pred_all = design_all @ coeffs
    residuals = y - y_pred_all

    validation_pred = (
        (
            np.column_stack([np.ones(x_validation.shape[0]), x_validation])
            if fit_intercept
            else x_validation
        )
        @ coeffs
        if len(x_validation)
        else np.asarray([], dtype=float)
    )

    mae = float(np.mean(np.abs(residuals)))
    rmse = float(np.sqrt(np.mean(residuals**2)))
    max_abs_error = float(np.max(np.abs(residuals)))
    condition_number = float(np.linalg.cond(design_train))
    residual_std = float(np.std(residuals))
    outlier_cutoff = 3.0 * residual_std if residual_std > 0 else float("inf")

    names = (("intercept",) if fit_intercept else ()) + tuple(binding.feature_names)
    if len(names) != len(coeffs):
        raise ValueError("COEFFICIENT_NAME_COUNT_MISMATCH")
    coefficients: Mapping[str, float] = {name: float(value) for name, value in zip(names, coeffs)}
    validation_r2 = _r2(y_validation, validation_pred) if len(y_validation) else None

    status = "CALIBRATION_CANDIDATE"
    reasons = list(precheck.reason_codes)
    if rank < design_train.shape[1]:
        status = "RANK_DEFICIENT_BLOCKED"
        if REASON_RANK_DEFICIENT_FEATURE_MATRIX not in reasons:
            reasons.append(REASON_RANK_DEFICIENT_FEATURE_MATRIX)
    elif condition_number > 1_000_000:
        status = "ROBUSTNESS_FAILED"
        reasons.append("HIGH_CONDITION_NUMBER")

    diagnostics = LinearModelDiagnosticsV1(
        rank=int(rank),
        condition_number=condition_number,
        rmse=rmse,
        mae=mae,
        max_abs_error=max_abs_error,
        r2_train=_r2(y_train, design_train @ coeffs),
        r2_validation=validation_r2,
        residual_mean=float(np.mean(residuals)),
        residual_std=residual_std,
        outlier_count=int(np.sum(np.abs(residuals) > outlier_cutoff)),
    )

    return LinearModelEvidenceV1(
        evidence_type=evidence_type,
        model_family="OLS",
        target_name=binding.target_name,
        feature_names=binding.feature_names,
        n_samples=binding.n_samples,
        n_features=binding.n_features,
        solver="numpy.linalg.lstsq",
        fit_intercept=fit_intercept,
        coefficients=coefficients,
        diagnostics=diagnostics,
        feature_matrix_digest=binding.feature_matrix_digest,
        target_digest=binding.target_digest,
        config_digest=_digest(
            {"fit_intercept": fit_intercept, "validation_fraction": validation_fraction}
        ),
        time_range=binding.time_range,
        instrument_universe_digest=instrument_universe_digest,
        row_count_before_filter=binding.row_count_before_filter,
        row_count_after_filter=binding.row_count_after_filter,
        dropped_rows_by_reason=binding.dropped_rows_by_reason,
        validation_policy=binding.validation_policy,
        cost_policy_output="diagnostic_only",
        status=status,
        reason_codes=tuple(reasons),
    )
