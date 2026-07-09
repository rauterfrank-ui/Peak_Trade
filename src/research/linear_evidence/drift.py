from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Mapping, Sequence, Tuple
import hashlib
import json
import math

import numpy as np

from .contracts import LinearModelDiagnosticsV1, LinearModelEvidenceV1


@dataclass(frozen=True)
class RollingLinearDriftInputV1:
    instrument_id: str
    decision_time: str
    feature_availability_time: str
    target: float
    features: Mapping[str, float]


@dataclass(frozen=True)
class RollingLinearDriftEvidenceV1:
    evidence_type: str
    model_family: str
    target_name: str
    feature_names: Tuple[str, ...]
    n_samples: int
    n_features: int
    window_size: int
    n_windows: int
    solver: str
    fit_intercept: bool
    window_evidence: Tuple[LinearModelEvidenceV1, ...]
    coefficient_drift: Dict[str, float]
    drift_score: float
    diagnostics: Dict[str, float]
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
            "n_samples": self.n_samples,
            "n_features": self.n_features,
            "window_size": self.window_size,
            "n_windows": self.n_windows,
            "solver": self.solver,
            "fit_intercept": self.fit_intercept,
            "window_evidence": [
                {
                    "time_range": dict(evidence.time_range),
                    "status": evidence.status,
                    "reason_codes": list(evidence.reason_codes),
                    "coefficients": dict(evidence.coefficients),
                    "diagnostics": {
                        "rank": evidence.diagnostics.rank,
                        "condition_number": evidence.diagnostics.condition_number,
                        "rmse": evidence.diagnostics.rmse,
                        "r2_train": evidence.diagnostics.r2_train,
                    },
                }
                for evidence in self.window_evidence
            ],
            "coefficient_drift": dict(self.coefficient_drift),
            "drift_score": self.drift_score,
            "diagnostics": dict(self.diagnostics),
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


def _r2(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    denom = float(np.sum((y_true - float(np.mean(y_true))) ** 2))
    if denom == 0.0:
        return 0.0
    return 1.0 - float(np.sum((y_true - y_pred) ** 2)) / denom


def _build_drift_matrix(
    records: Sequence[RollingLinearDriftInputV1],
) -> Tuple[np.ndarray, np.ndarray, Tuple[str, ...], List[str], str, str]:
    if not records:
        raise ValueError("INSUFFICIENT_DATA")

    decision_times = [r.decision_time for r in records]
    if decision_times != sorted(decision_times):
        raise ValueError("RANDOM_VALIDATION_SPLIT_BLOCKED")

    for record in records:
        if record.feature_availability_time > record.decision_time:
            raise ValueError("LOOKAHEAD_BLOCKED")

    feature_names = tuple(sorted(records[0].features.keys()))
    if not feature_names:
        raise ValueError("TARGET_BINDING_MISSING")

    rows: List[List[float]] = []
    targets: List[float] = []
    for record in records:
        if tuple(sorted(record.features.keys())) != feature_names:
            raise ValueError("FEATURE_SCHEMA_DRIFT")
        row = [float(record.features[name]) for name in feature_names]
        if any(not math.isfinite(v) for v in row) or not math.isfinite(float(record.target)):
            raise ValueError("INSUFFICIENT_DATA")
        rows.append(row)
        targets.append(float(record.target))

    x = np.asarray(rows, dtype=float)
    y = np.asarray(targets, dtype=float)
    return x, y, feature_names, decision_times, _stable_digest(rows), _stable_digest(targets)


def _fit_window_linear_evidence(
    x: np.ndarray,
    y: np.ndarray,
    *,
    feature_names: Tuple[str, ...],
    target_name: str,
    time_range: Mapping[str, str],
    feature_matrix_digest: str,
    target_digest: str,
    max_condition_number: float,
    min_samples: int,
) -> LinearModelEvidenceV1:
    n_samples, n_features = x.shape
    reason_codes: List[str] = []

    if n_samples < min_samples:
        return LinearModelEvidenceV1(
            evidence_type="rolling_linear_drift_window",
            model_family="OLS",
            target_name=target_name,
            feature_names=feature_names,
            n_samples=n_samples,
            n_features=n_features,
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
            feature_matrix_digest=feature_matrix_digest,
            target_digest=target_digest,
            config_digest=_stable_digest({"window_size": n_samples}),
            time_range=dict(time_range),
            instrument_universe_digest="rolling_window",
            row_count_before_filter=n_samples,
            row_count_after_filter=n_samples,
            dropped_rows_by_reason={},
            validation_policy="TIME_ORDERED",
            cost_policy_output="diagnostic_only",
            status="INSUFFICIENT_DATA",
            reason_codes=("INSUFFICIENT_SAMPLE_COUNT",),
        )

    design = np.column_stack([np.ones(n_samples), x])
    rank = int(np.linalg.matrix_rank(design))
    condition_number = float(np.linalg.cond(design))

    if rank < design.shape[1]:
        status = "RANK_DEFICIENT_BLOCKED"
        reason_codes.append("HIGH_CONDITION_NUMBER")
    elif condition_number > max_condition_number:
        status = "ROBUSTNESS_FAILED"
        reason_codes.append("HIGH_CONDITION_NUMBER")
    else:
        status = "DIAGNOSTIC_ONLY"

    coeffs, _, _, _ = np.linalg.lstsq(design, y, rcond=None)
    predictions = design @ coeffs
    residuals = y - predictions
    residual_std = float(np.std(residuals))
    outlier_cutoff = 3.0 * residual_std if residual_std > 0 else float("inf")

    coeff_names = ("intercept",) + feature_names
    coefficients = {name: float(value) for name, value in zip(coeff_names, coeffs)}

    diagnostics = LinearModelDiagnosticsV1(
        rank=rank,
        condition_number=condition_number,
        rmse=float(np.sqrt(np.mean(residuals**2))),
        mae=float(np.mean(np.abs(residuals))),
        max_abs_error=float(np.max(np.abs(residuals))),
        r2_train=_r2(y, predictions),
        r2_validation=None,
        residual_mean=float(np.mean(residuals)),
        residual_std=residual_std,
        outlier_count=int(np.sum(np.abs(residuals) > outlier_cutoff)),
    )

    return LinearModelEvidenceV1(
        evidence_type="rolling_linear_drift_window",
        model_family="OLS",
        target_name=target_name,
        feature_names=feature_names,
        n_samples=n_samples,
        n_features=n_features,
        solver="numpy.linalg.lstsq",
        fit_intercept=True,
        coefficients=coefficients,
        diagnostics=diagnostics,
        feature_matrix_digest=feature_matrix_digest,
        target_digest=target_digest,
        config_digest=_stable_digest({"window_size": n_samples}),
        time_range=dict(time_range),
        instrument_universe_digest="rolling_window",
        row_count_before_filter=n_samples,
        row_count_after_filter=n_samples,
        dropped_rows_by_reason={},
        validation_policy="TIME_ORDERED",
        cost_policy_output="diagnostic_only",
        status=status,
        reason_codes=tuple(reason_codes),
    )


def fit_rolling_linear_drift(
    records: Sequence[RollingLinearDriftInputV1],
    *,
    target_name: str = "target",
    window_size: int = 6,
    min_samples: int = 4,
    max_condition_number: float = 1_000_000.0,
    unstable_coefficient_threshold: float = 0.75,
    drift_detection_threshold: float = 0.5,
) -> RollingLinearDriftEvidenceV1:
    try:
        x, y, feature_names, decision_times, x_digest, y_digest = _build_drift_matrix(records)
    except ValueError as exc:
        message = str(exc)
        if message == "LOOKAHEAD_BLOCKED":
            return RollingLinearDriftEvidenceV1(
                evidence_type="rolling_linear_drift",
                model_family="OLS",
                target_name=target_name,
                feature_names=(),
                n_samples=len(records),
                n_features=0,
                window_size=window_size,
                n_windows=0,
                solver="numpy.linalg.lstsq",
                fit_intercept=True,
                window_evidence=(),
                coefficient_drift={},
                drift_score=0.0,
                diagnostics={},
                feature_matrix_digest="",
                target_digest="",
                validation_policy="TIME_ORDERED",
                status="LEAKAGE_BLOCKED",
                reason_codes=("LOOKAHEAD_BLOCKED",),
                authority_effect="NONE",
                runtime_effect="NONE",
            )
        raise

    n_samples = x.shape[0]
    if n_samples < window_size:
        return RollingLinearDriftEvidenceV1(
            evidence_type="rolling_linear_drift",
            model_family="OLS",
            target_name=target_name,
            feature_names=feature_names,
            n_samples=n_samples,
            n_features=len(feature_names),
            window_size=window_size,
            n_windows=0,
            solver="numpy.linalg.lstsq",
            fit_intercept=True,
            window_evidence=(),
            coefficient_drift={},
            drift_score=0.0,
            diagnostics={},
            feature_matrix_digest=x_digest,
            target_digest=y_digest,
            validation_policy="TIME_ORDERED",
            status="INSUFFICIENT_DATA",
            reason_codes=("INSUFFICIENT_SAMPLE_COUNT",),
            authority_effect="NONE",
            runtime_effect="NONE",
        )

    window_evidence: List[LinearModelEvidenceV1] = []
    coeff_series: Dict[str, List[float]] = {}

    for start in range(0, n_samples - window_size + 1):
        end = start + window_size
        x_window = x[start:end]
        y_window = y[start:end]
        window_digest = _stable_digest(x_window.tolist())
        target_window_digest = _stable_digest(y_window.tolist())
        evidence = _fit_window_linear_evidence(
            x_window,
            y_window,
            feature_names=feature_names,
            target_name=target_name,
            time_range={
                "start": decision_times[start],
                "end": decision_times[end - 1],
            },
            feature_matrix_digest=window_digest,
            target_digest=target_window_digest,
            max_condition_number=max_condition_number,
            min_samples=min_samples,
        )
        window_evidence.append(evidence)
        for name, value in evidence.coefficients.items():
            coeff_series.setdefault(name, []).append(value)

    aggregate_reasons: List[str] = []
    aggregate_status = "DIAGNOSTIC_ONLY"

    for evidence in window_evidence:
        if evidence.status == "INSUFFICIENT_DATA":
            aggregate_status = "INSUFFICIENT_DATA"
            aggregate_reasons.append("INSUFFICIENT_SAMPLE_COUNT")
        elif evidence.status == "RANK_DEFICIENT_BLOCKED":
            aggregate_status = "RANK_DEFICIENT_BLOCKED"
            aggregate_reasons.append("HIGH_CONDITION_NUMBER")
        elif evidence.status == "ROBUSTNESS_FAILED" and aggregate_status == "DIAGNOSTIC_ONLY":
            aggregate_status = "ROBUSTNESS_FAILED"
            aggregate_reasons.append("HIGH_CONDITION_NUMBER")

    coefficient_drift: Dict[str, float] = {}
    for name, values in coeff_series.items():
        if len(values) < 2:
            coefficient_drift[name] = 0.0
            continue
        spread = float(max(values) - min(values))
        scale = max(abs(float(np.mean(values))), 1e-9)
        coefficient_drift[name] = spread / scale

    drift_score = float(max(coefficient_drift.values(), default=0.0))
    unstable = [
        name for name, score in coefficient_drift.items() if score >= unstable_coefficient_threshold
    ]
    if unstable and aggregate_status == "DIAGNOSTIC_ONLY":
        aggregate_reasons.append("UNSTABLE_COEFFICIENTS")

    if (
        drift_score >= drift_detection_threshold
        and "COEFFICIENT_DRIFT_DETECTED" not in aggregate_reasons
    ):
        aggregate_reasons.append("COEFFICIENT_DRIFT_DETECTED")

    diagnostics = {
        "drift_score": drift_score,
        "max_coefficient_drift": drift_score,
        "window_count": float(len(window_evidence)),
        "unstable_coefficient_count": float(len(unstable)),
    }

    return RollingLinearDriftEvidenceV1(
        evidence_type="rolling_linear_drift",
        model_family="OLS",
        target_name=target_name,
        feature_names=feature_names,
        n_samples=n_samples,
        n_features=len(feature_names),
        window_size=window_size,
        n_windows=len(window_evidence),
        solver="numpy.linalg.lstsq",
        fit_intercept=True,
        window_evidence=tuple(window_evidence),
        coefficient_drift=coefficient_drift,
        drift_score=drift_score,
        diagnostics=diagnostics,
        feature_matrix_digest=x_digest,
        target_digest=y_digest,
        validation_policy="TIME_ORDERED",
        status=aggregate_status,
        reason_codes=tuple(dict.fromkeys(aggregate_reasons)),
        authority_effect="NONE",
        runtime_effect="NONE",
    )
