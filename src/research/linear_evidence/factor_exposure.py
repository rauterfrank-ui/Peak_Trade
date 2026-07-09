from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, List, Mapping, Sequence, Tuple
import json
import math
import hashlib

import numpy as np


@dataclass(frozen=True)
class FactorExposureInputV1:
    instrument_id: str
    timestamp: int
    target_return: float
    factor_values: Mapping[str, float]


@dataclass(frozen=True)
class FactorExposureEvidenceV1:
    evidence_type: str
    model_family: str
    target_name: str
    feature_names: Tuple[str, ...]
    n_samples: int
    n_features: int
    solver: str
    fit_intercept: bool
    coefficients: Dict[str, float]
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
            "solver": self.solver,
            "fit_intercept": self.fit_intercept,
            "coefficients": dict(self.coefficients),
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


def build_factor_matrix(
    records: Sequence[FactorExposureInputV1],
) -> Tuple[np.ndarray, np.ndarray, Tuple[str, ...], str, str]:
    if not records:
        raise ValueError("INSUFFICIENT_DATA")

    timestamps = [r.timestamp for r in records]
    if timestamps != sorted(timestamps):
        raise ValueError("RANDOM_VALIDATION_SPLIT_BLOCKED")

    feature_names = tuple(sorted(records[0].factor_values.keys()))
    if not feature_names:
        raise ValueError("TARGET_BINDING_MISSING")

    rows: List[List[float]] = []
    targets: List[float] = []
    for record in records:
        if tuple(sorted(record.factor_values.keys())) != feature_names:
            raise ValueError("FEATURE_SCHEMA_DRIFT")
        row = [float(record.factor_values[name]) for name in feature_names]
        if any(not math.isfinite(v) for v in row) or not math.isfinite(float(record.target_return)):
            raise ValueError("INSUFFICIENT_DATA")
        rows.append(row)
        targets.append(float(record.target_return))

    x = np.asarray(rows, dtype=float)
    y = np.asarray(targets, dtype=float)
    return x, y, feature_names, _stable_digest(rows), _stable_digest(targets)


def fit_factor_exposure(
    records: Sequence[FactorExposureInputV1],
    *,
    min_samples: int = 8,
    max_condition_number: float = 1_000_000.0,
) -> FactorExposureEvidenceV1:
    x, y, feature_names, x_digest, y_digest = build_factor_matrix(records)
    n_samples, n_features = x.shape

    reason_codes: List[str] = []
    if n_samples < min_samples:
        return FactorExposureEvidenceV1(
            evidence_type="factor_exposure",
            model_family="ordinary_least_squares",
            target_name="target_return",
            feature_names=feature_names,
            n_samples=n_samples,
            n_features=n_features,
            solver="numpy.linalg.lstsq",
            fit_intercept=True,
            coefficients={},
            diagnostics={},
            feature_matrix_digest=x_digest,
            target_digest=y_digest,
            validation_policy="time_ordered",
            status="INSUFFICIENT_DATA",
            reason_codes=("INSUFFICIENT_SAMPLE_COUNT",),
            authority_effect="NONE",
            runtime_effect="NONE",
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

    beta, residuals, _, _ = np.linalg.lstsq(design, y, rcond=None)
    predictions = design @ beta
    errors = y - predictions

    ss_res = float(np.sum(errors**2))
    ss_tot = float(np.sum((y - float(np.mean(y))) ** 2))
    r2 = 0.0 if ss_tot == 0.0 else float(1.0 - ss_res / ss_tot)

    coefficients = {"intercept": float(beta[0])}
    coefficients.update({name: float(value) for name, value in zip(feature_names, beta[1:])})

    diagnostics = {
        "rank": float(rank),
        "condition_number": condition_number,
        "rmse": float(np.sqrt(np.mean(errors**2))),
        "mae": float(np.mean(np.abs(errors))),
        "r2": r2,
        "max_abs_error": float(np.max(np.abs(errors))),
    }

    return FactorExposureEvidenceV1(
        evidence_type="factor_exposure",
        model_family="ordinary_least_squares",
        target_name="target_return",
        feature_names=feature_names,
        n_samples=n_samples,
        n_features=n_features,
        solver="numpy.linalg.lstsq",
        fit_intercept=True,
        coefficients=coefficients,
        diagnostics=diagnostics,
        feature_matrix_digest=x_digest,
        target_digest=y_digest,
        validation_policy="time_ordered",
        status=status,
        reason_codes=tuple(reason_codes),
        authority_effect="NONE",
        runtime_effect="NONE",
    )
