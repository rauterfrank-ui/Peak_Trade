from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping

import numpy as np

from .contracts import FeatureMatrixBindingV1, LinearModelDiagnosticsV1, LinearModelEvidenceV1


def _digest(payload: object) -> str:
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str).encode()
    ).hexdigest()


def _r2(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    denom = float(np.sum((y_true - float(np.mean(y_true))) ** 2))
    if denom == 0.0:
        return 0.0
    return 1.0 - float(np.sum((y_true - y_pred) ** 2)) / denom


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
    reasons: list[str] = []
    if rank < design_train.shape[1]:
        status = "RANK_DEFICIENT_BLOCKED"
        reasons.append("HIGH_CONDITION_NUMBER")
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
