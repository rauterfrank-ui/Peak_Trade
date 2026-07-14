from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass, replace
from math import isfinite
from typing import Dict, List, Mapping, Sequence, Tuple

from .factor_exposure_productive_contract_v0 import FactorExposureProductiveProvenanceV0

import numpy as np

from .fitters import REASON_ZERO_VARIANCE_FEATURE
from .signal_orthogonality import (
    _condition_number,
    _pairwise_correlations,
    _rank,
    _redundant_pairs,
    _vif_scores,
)

REASON_INSUFFICIENT_SAMPLE_COUNT = "INSUFFICIENT_SAMPLE_COUNT"
REASON_FACTOR_TIME_BINDING_MISSING = "FACTOR_TIME_BINDING_MISSING"
REASON_FACTOR_LOOKAHEAD_DETECTED = "FACTOR_LOOKAHEAD_DETECTED"
REASON_NON_MONOTONIC_TIME_ORDER = "NON_MONOTONIC_TIME_ORDER"
REASON_ZERO_VARIANCE_FACTOR = "ZERO_VARIANCE_FACTOR"
REASON_PERFECT_COLLINEARITY_DETECTED = "PERFECT_COLLINEARITY_DETECTED"
REASON_HIGH_PAIRWISE_CORRELATION = "HIGH_PAIRWISE_CORRELATION"
REASON_HIGH_VIF = "HIGH_VIF"
REASON_HIGH_CONDITION_NUMBER = "HIGH_CONDITION_NUMBER"
REASON_PRODUCTIVE_BINDING_MISSING = "PRODUCTIVE_BINDING_MISSING"
REASON_FIXTURE_SCAFFOLD_DIAGNOSTIC_ONLY = "FIXTURE_SCAFFOLD_DIAGNOSTIC_ONLY"
REASON_RANK_DEFICIENT = "RANK_DEFICIENT_FEATURE_MATRIX"
REASON_STRICT_ZERO_VARIANCE_FACTOR_EXCLUDED = "STRICT_ZERO_VARIANCE_FACTOR_EXCLUDED"

_AUTHORITY_EFFECT = "NONE"
_RUNTIME_EFFECT = "NONE"


@dataclass(frozen=True)
class FactorExposureConfigV1:
    correlation_threshold: float = 0.85
    vif_threshold: float = 10.0
    condition_number_threshold: float = 1000.0
    min_samples: int = 8

    def validate(self) -> None:
        if not 0.0 < self.correlation_threshold < 1.0:
            raise ValueError("correlation_threshold must be between 0 and 1")
        if self.vif_threshold <= 0:
            raise ValueError("vif_threshold must be positive")
        if self.condition_number_threshold <= 0:
            raise ValueError("condition_number_threshold must be positive")
        if self.min_samples < 3:
            raise ValueError("min_samples must be at least 3")


@dataclass(frozen=True)
class FactorExposureInputV1:
    instrument_id: str
    timestamp: int
    target_return: float
    factor_values: Mapping[str, float]
    factor_time: str | None = None
    decision_time: str | None = None

    def resolved_factor_time(self) -> str:
        if self.factor_time is not None:
            return self.factor_time
        return f"2026-01-01T{self.timestamp:02d}:00:00Z"

    def resolved_decision_time(self) -> str:
        if self.decision_time is not None:
            return self.decision_time
        return f"2026-01-01T{self.timestamp + 1:02d}:00:00Z"


@dataclass(frozen=True)
class FactorExposurePrecheckV0:
    zero_variance_factor_names: tuple[str, ...]
    reason_codes: tuple[str, ...]
    blocking: bool


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
    diagnostics: Dict[str, object]
    feature_matrix_digest: str
    target_digest: str
    config_digest: str
    validation_policy: str
    status: str
    reason_codes: Tuple[str, ...]
    authority_effect: str
    runtime_effect: str
    productive_provenance: FactorExposureProductiveProvenanceV0 | None = None
    original_feature_names: Tuple[str, ...] | None = None
    effective_feature_names: Tuple[str, ...] | None = None
    original_n_features: int | None = None
    effective_n_features: int | None = None
    excluded_factor_names: Tuple[str, ...] | None = None
    excluded_factor_count: int | None = None

    def to_dict(self) -> Dict[str, object]:
        payload: Dict[str, object] = {
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
            "config_digest": self.config_digest,
            "validation_policy": self.validation_policy,
            "status": self.status,
            "reason_codes": list(self.reason_codes),
            "authority_effect": self.authority_effect,
            "runtime_effect": self.runtime_effect,
        }
        if self.original_feature_names is not None:
            payload["original_feature_names"] = list(self.original_feature_names)
        if self.effective_feature_names is not None:
            payload["effective_feature_names"] = list(self.effective_feature_names)
        if self.original_n_features is not None:
            payload["original_n_features"] = int(self.original_n_features)
        if self.effective_n_features is not None:
            payload["effective_n_features"] = int(self.effective_n_features)
        if self.excluded_factor_names is not None:
            payload["excluded_factor_names"] = list(self.excluded_factor_names)
        if self.excluded_factor_count is not None:
            payload["excluded_factor_count"] = int(self.excluded_factor_count)
        if self.productive_provenance is not None:
            payload.update(self.productive_provenance.to_dict())
        return payload


def _stable_digest(payload: object) -> str:
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _sorted_unique_factor_names(factor_names: Sequence[str]) -> tuple[str, ...]:
    names = tuple(sorted(str(name) for name in factor_names))
    if not names:
        raise ValueError("TARGET_BINDING_MISSING")
    if len(set(names)) != len(names):
        raise ValueError("FEATURE_SCHEMA_DRIFT")
    return names


def _validate_temporal_bindings(
    records: Sequence[FactorExposureInputV1],
) -> list[FactorExposureInputV1]:
    if not records:
        raise ValueError("INSUFFICIENT_DATA")

    decision_times = [record.resolved_decision_time() for record in records]
    if any(not value for value in decision_times):
        raise ValueError(REASON_FACTOR_TIME_BINDING_MISSING)
    if decision_times != sorted(decision_times):
        raise ValueError(REASON_NON_MONOTONIC_TIME_ORDER)

    ordered = sorted(records, key=lambda record: record.resolved_decision_time())

    for record in ordered:
        factor_time = record.resolved_factor_time()
        decision_time = record.resolved_decision_time()
        if not factor_time:
            raise ValueError(REASON_FACTOR_TIME_BINDING_MISSING)
        if factor_time >= decision_time:
            raise ValueError(REASON_FACTOR_LOOKAHEAD_DETECTED)

    return ordered


def build_factor_matrix(
    records: Sequence[FactorExposureInputV1],
) -> Tuple[np.ndarray, np.ndarray, Tuple[str, ...], str, str]:
    ordered = _validate_temporal_bindings(records)
    feature_names = _sorted_unique_factor_names(ordered[0].factor_values.keys())

    rows: List[List[float]] = []
    targets: List[float] = []
    for record in ordered:
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


def compute_factor_exposure_precheck_v0(
    matrix: np.ndarray,
    factor_names: Sequence[str],
    *,
    min_samples: int,
) -> FactorExposurePrecheckV0:
    reason_codes: list[str] = []
    if matrix.shape[0] < min_samples:
        reason_codes.append(REASON_INSUFFICIENT_SAMPLE_COUNT)

    zero_variance_factor_names: list[str] = []
    if matrix.size:
        for index, name in enumerate(factor_names):
            if float(np.var(matrix[:, index])) == 0.0:
                zero_variance_factor_names.append(str(name))
                reason_codes.append(f"{REASON_ZERO_VARIANCE_FACTOR}:{name}")

    blocking = bool(matrix.shape[0] < min_samples or zero_variance_factor_names)
    return FactorExposurePrecheckV0(
        zero_variance_factor_names=tuple(sorted(zero_variance_factor_names)),
        reason_codes=tuple(dict.fromkeys(reason_codes)),
        blocking=blocking,
    )


def _exclude_strict_zero_variance_factors_v0(
    matrix: np.ndarray,
    factor_names: tuple[str, ...],
) -> tuple[np.ndarray, tuple[str, ...], tuple[str, ...]]:
    """Deterministically exclude strictly zero-variance factor columns.

    Predicate: exact float(np.var(column)) == 0.0 on the canonical float matrix.
    Exclusion order is stable w.r.t. factor_names.
    """
    if matrix.size == 0 or not factor_names:
        return matrix, factor_names, ()
    excluded: list[str] = []
    keep_indices: list[int] = []
    for idx, name in enumerate(factor_names):
        if float(np.var(matrix[:, idx])) == 0.0:
            excluded.append(str(name))
        else:
            keep_indices.append(idx)
    if not excluded:
        return matrix, factor_names, ()
    if not keep_indices:
        return np.empty((matrix.shape[0], 0), dtype=float), (), tuple(excluded)
    kept = matrix[:, keep_indices]
    kept_names = tuple(factor_names[i] for i in keep_indices)
    return kept, kept_names, tuple(excluded)


def _blocked_diagnostics(*, computed: bool = False) -> dict[str, object]:
    return {
        "computed": computed,
        "rank": 0,
        "condition_number": None,
        "pairwise_correlation": {},
        "redundant_pairs": [],
        "vif_scores": {},
        "perfect_collinearity_count": 0,
        "sample_sufficiency": {"sufficient": False},
    }


def _blocked_evidence(
    *,
    factor_names: tuple[str, ...],
    matrix: np.ndarray,
    target_digest: str,
    feature_matrix_digest: str,
    cfg: FactorExposureConfigV1,
    precheck: FactorExposurePrecheckV0,
    extra_reasons: Sequence[str] = (),
    productive_binding_gap: bool = False,
    fixture_scaffold: bool = False,
) -> FactorExposureEvidenceV1:
    reasons = list(precheck.reason_codes)
    reasons.extend(extra_reasons)
    if productive_binding_gap and REASON_PRODUCTIVE_BINDING_MISSING not in reasons:
        reasons.append(REASON_PRODUCTIVE_BINDING_MISSING)
    if fixture_scaffold and REASON_FIXTURE_SCAFFOLD_DIAGNOSTIC_ONLY not in reasons:
        reasons.append(REASON_FIXTURE_SCAFFOLD_DIAGNOSTIC_ONLY)
    if precheck.zero_variance_factor_names and REASON_RANK_DEFICIENT not in reasons:
        reasons.append(REASON_RANK_DEFICIENT)

    status = "INSUFFICIENT_DATA"
    if precheck.zero_variance_factor_names or REASON_PERFECT_COLLINEARITY_DETECTED in reasons:
        status = "RANK_DEFICIENT_BLOCKED"
    elif REASON_RANK_DEFICIENT in reasons:
        status = "RANK_DEFICIENT_BLOCKED"
    elif REASON_HIGH_CONDITION_NUMBER in reasons:
        status = "RANK_DEFICIENT_BLOCKED"

    return FactorExposureEvidenceV1(
        evidence_type="factor_exposure",
        model_family="ordinary_least_squares",
        target_name="target_return",
        feature_names=factor_names if factor_names else ("",),
        n_samples=int(matrix.shape[0]),
        n_features=len(factor_names) if factor_names else 0,
        solver="numpy.linalg.lstsq",
        fit_intercept=True,
        coefficients={},
        diagnostics=_blocked_diagnostics(computed=False),
        feature_matrix_digest=feature_matrix_digest,
        target_digest=target_digest,
        config_digest=_stable_digest(
            [
                cfg.correlation_threshold,
                cfg.vif_threshold,
                cfg.condition_number_threshold,
                cfg.min_samples,
            ]
        ),
        validation_policy="time_ordered",
        status=status,
        reason_codes=tuple(dict.fromkeys(reasons)),
        authority_effect=_AUTHORITY_EFFECT,
        runtime_effect=_RUNTIME_EFFECT,
        original_feature_names=factor_names,
        effective_feature_names=factor_names,
        original_n_features=len(factor_names) if factor_names else 0,
        effective_n_features=len(factor_names) if factor_names else 0,
        excluded_factor_names=(),
        excluded_factor_count=0,
    )


def fit_factor_exposure(
    records: Sequence[FactorExposureInputV1],
    *,
    config: FactorExposureConfigV1 | None = None,
    productive_binding_gap: bool = False,
    fixture_scaffold: bool = False,
    min_samples: int | None = None,
    max_condition_number: float | None = None,
) -> FactorExposureEvidenceV1:
    cfg = config or FactorExposureConfigV1()
    if min_samples is not None:
        cfg = FactorExposureConfigV1(
            correlation_threshold=cfg.correlation_threshold,
            vif_threshold=cfg.vif_threshold,
            condition_number_threshold=max_condition_number or cfg.condition_number_threshold,
            min_samples=min_samples,
        )
    elif max_condition_number is not None:
        cfg = FactorExposureConfigV1(
            correlation_threshold=cfg.correlation_threshold,
            vif_threshold=cfg.vif_threshold,
            condition_number_threshold=max_condition_number,
            min_samples=cfg.min_samples,
        )
    cfg.validate()

    if not records:
        precheck = FactorExposurePrecheckV0(
            zero_variance_factor_names=(),
            reason_codes=(REASON_INSUFFICIENT_SAMPLE_COUNT,),
            blocking=True,
        )
        return _blocked_evidence(
            factor_names=(),
            matrix=np.empty((0, 0), dtype=float),
            target_digest=_stable_digest([]),
            feature_matrix_digest=_stable_digest([]),
            cfg=cfg,
            precheck=precheck,
            productive_binding_gap=productive_binding_gap,
            fixture_scaffold=fixture_scaffold,
        )

    x, y, factor_names, x_digest, y_digest = build_factor_matrix(records)
    original_factor_names = factor_names
    original_n_features = len(original_factor_names)

    x, factor_names, excluded_factor_names = _exclude_strict_zero_variance_factors_v0(
        x, factor_names
    )
    strict_exclusion_reason_codes = tuple(
        f"{REASON_STRICT_ZERO_VARIANCE_FACTOR_EXCLUDED}:{name}" for name in excluded_factor_names
    )
    strict_exclusion_applied = bool(excluded_factor_names)
    n_samples, n_features = x.shape

    if strict_exclusion_applied and not factor_names:
        precheck = FactorExposurePrecheckV0(
            zero_variance_factor_names=(),
            reason_codes=(),
            blocking=True,
        )
        blocked = _blocked_evidence(
            factor_names=original_factor_names,
            matrix=x,
            target_digest=y_digest,
            feature_matrix_digest=x_digest,
            cfg=cfg,
            precheck=precheck,
            extra_reasons=[*strict_exclusion_reason_codes, REASON_RANK_DEFICIENT],
            productive_binding_gap=productive_binding_gap,
            fixture_scaffold=fixture_scaffold,
        )
        return replace(
            blocked,
            original_feature_names=original_factor_names,
            effective_feature_names=(),
            original_n_features=original_n_features,
            effective_n_features=0,
            excluded_factor_names=excluded_factor_names,
            excluded_factor_count=len(excluded_factor_names),
        )

    precheck = compute_factor_exposure_precheck_v0(x, factor_names, min_samples=cfg.min_samples)
    if precheck.blocking or productive_binding_gap:
        blocked = _blocked_evidence(
            factor_names=factor_names,
            matrix=x,
            target_digest=y_digest,
            feature_matrix_digest=x_digest,
            cfg=cfg,
            precheck=precheck,
            productive_binding_gap=productive_binding_gap,
            fixture_scaffold=fixture_scaffold,
        )
        if not strict_exclusion_applied:
            return replace(
                blocked,
                original_feature_names=original_factor_names,
                effective_feature_names=factor_names,
                original_n_features=original_n_features,
                effective_n_features=len(factor_names),
            )
        return replace(
            blocked,
            reason_codes=tuple(
                dict.fromkeys([*strict_exclusion_reason_codes, *blocked.reason_codes])
            ),
            original_feature_names=original_factor_names,
            effective_feature_names=factor_names,
            original_n_features=original_n_features,
            effective_n_features=len(factor_names),
            excluded_factor_names=excluded_factor_names,
            excluded_factor_count=len(excluded_factor_names),
        )

    rank = _rank(x)
    condition_number = _condition_number(x)
    corr = _pairwise_correlations(factor_names, x) if len(factor_names) >= 2 else {}
    redundant = _redundant_pairs(factor_names, corr, cfg.correlation_threshold) if corr else []
    vif = _vif_scores(factor_names, x) if len(factor_names) >= 2 else {}

    reason_codes: list[str] = []
    perfect_collinearity_count = sum(1 for value in vif.values() if value == float("inf"))

    if rank < len(factor_names):
        reason_codes.append(REASON_PERFECT_COLLINEARITY_DETECTED)
        reason_codes.append(REASON_RANK_DEFICIENT)
    if perfect_collinearity_count:
        reason_codes.append(REASON_PERFECT_COLLINEARITY_DETECTED)
    if redundant:
        reason_codes.append(REASON_HIGH_PAIRWISE_CORRELATION)
    if any(value > cfg.vif_threshold for value in vif.values() if isfinite(value)):
        reason_codes.append(REASON_HIGH_VIF)
    if not isfinite(condition_number) or condition_number > cfg.condition_number_threshold:
        reason_codes.append(REASON_HIGH_CONDITION_NUMBER)

    if (
        REASON_PERFECT_COLLINEARITY_DETECTED in reason_codes
        or REASON_RANK_DEFICIENT in reason_codes
        or REASON_HIGH_CONDITION_NUMBER in reason_codes
    ):
        blocked = _blocked_evidence(
            factor_names=factor_names,
            matrix=x,
            target_digest=y_digest,
            feature_matrix_digest=x_digest,
            cfg=cfg,
            precheck=precheck,
            extra_reasons=reason_codes,
            fixture_scaffold=fixture_scaffold,
        )
        if not strict_exclusion_applied:
            return replace(
                blocked,
                original_feature_names=original_factor_names,
                effective_feature_names=factor_names,
                original_n_features=original_n_features,
                effective_n_features=len(factor_names),
            )
        return replace(
            blocked,
            reason_codes=tuple(
                dict.fromkeys([*strict_exclusion_reason_codes, *blocked.reason_codes])
            ),
            original_feature_names=original_factor_names,
            effective_feature_names=factor_names,
            original_n_features=original_n_features,
            effective_n_features=len(factor_names),
            excluded_factor_names=excluded_factor_names,
            excluded_factor_count=len(excluded_factor_names),
        )

    design = np.column_stack([np.ones(n_samples), x])
    beta, _, _, _ = np.linalg.lstsq(design, y, rcond=None)
    predictions = design @ beta
    errors = y - predictions

    ss_res = float(np.sum(errors**2))
    ss_tot = float(np.sum((y - float(np.mean(y))) ** 2))
    r2 = 0.0 if ss_tot == 0.0 else float(1.0 - ss_res / ss_tot)

    coefficients = {"intercept": float(beta[0])}
    coefficients.update({name: float(value) for name, value in zip(factor_names, beta[1:])})

    diagnostics: dict[str, object] = {
        "computed": True,
        "rank": rank,
        "condition_number": condition_number,
        "pairwise_correlation": corr,
        "redundant_pairs": redundant,
        "vif_scores": vif,
        "perfect_collinearity_count": perfect_collinearity_count,
        "rmse": float(np.sqrt(np.mean(errors**2))),
        "mae": float(np.mean(np.abs(errors))),
        "r2": r2,
        "max_abs_error": float(np.max(np.abs(errors))),
        "sample_sufficiency": {
            "sufficient": n_samples >= cfg.min_samples,
            "min_samples": cfg.min_samples,
            "actual_samples": n_samples,
        },
    }

    final_reasons = list(reason_codes)
    if strict_exclusion_applied:
        final_reasons.extend(strict_exclusion_reason_codes)
    if fixture_scaffold:
        final_reasons.append(REASON_FIXTURE_SCAFFOLD_DIAGNOSTIC_ONLY)

    return FactorExposureEvidenceV1(
        evidence_type="factor_exposure",
        model_family="ordinary_least_squares",
        target_name="target_return",
        feature_names=factor_names,
        n_samples=n_samples,
        n_features=n_features,
        solver="numpy.linalg.lstsq",
        fit_intercept=True,
        coefficients=coefficients,
        diagnostics=diagnostics,
        feature_matrix_digest=x_digest,
        target_digest=y_digest,
        config_digest=_stable_digest(
            [
                cfg.correlation_threshold,
                cfg.vif_threshold,
                cfg.condition_number_threshold,
                cfg.min_samples,
            ]
        ),
        validation_policy="time_ordered",
        status="DIAGNOSTIC_ONLY",
        reason_codes=tuple(dict.fromkeys(final_reasons)),
        authority_effect=_AUTHORITY_EFFECT,
        runtime_effect=_RUNTIME_EFFECT,
        original_feature_names=original_factor_names,
        effective_feature_names=factor_names,
        original_n_features=original_n_features,
        effective_n_features=len(factor_names),
        excluded_factor_names=excluded_factor_names if strict_exclusion_applied else (),
        excluded_factor_count=len(excluded_factor_names) if strict_exclusion_applied else 0,
    )


REASON_VALIDATION_ERROR_TOO_HIGH = "VALIDATION_ERROR_TOO_HIGH"
REASON_COEFFICIENT_SIGN_UNSTABLE = "COEFFICIENT_SIGN_UNSTABLE"
REASON_BETA_INSTABILITY = "BETA_INSTABILITY"
REASON_DOMINANT_COMMON_FACTOR_EXPOSURE = "DOMINANT_COMMON_FACTOR_EXPOSURE"
REASON_CLUSTER_CONCENTRATION_HIGH = "CLUSTER_CONCENTRATION_HIGH"
REASON_FEATURE_LEAKAGE_RISK = "FEATURE_LEAKAGE_RISK"
REASON_TARGET_BINDING_MISSING = "TARGET_BINDING_MISSING"
REASON_FACTOR_INPUT_MISSING = "FACTOR_INPUT_MISSING"
REASON_TIME_ALIGNMENT_INVALID = "TIME_ALIGNMENT_INVALID"
REASON_RANDOM_VALIDATION_SPLIT_BLOCKED = "RANDOM_VALIDATION_SPLIT_BLOCKED"
REASON_OUTLIER_DOMINATED = "OUTLIER_DOMINATED"

PRODUCTIVE_FACTOR_GROUPS_V0: dict[str, str] = {
    "funding_rate_abs": "funding",
    "spread_bps": "liquidity_spread",
    "volatility_estimate": "volatility",
}

_DEFAULT_VALIDATION_FRACTION = 0.25
_DEFAULT_STABILITY_WINDOW_COUNT = 3
_EXPOSURE_SIMILARITY_THRESHOLD = 0.85
_VALIDATION_RMSE_MULTIPLIER = 3.0


@dataclass(frozen=True)
class FactorExposureDiagnosticsConfigV0:
    correlation_threshold: float = 0.85
    vif_threshold: float = 10.0
    condition_number_threshold: float = 1000.0
    min_samples: int = 8
    validation_fraction: float = _DEFAULT_VALIDATION_FRACTION
    stability_window_count: int = _DEFAULT_STABILITY_WINDOW_COUNT
    exposure_similarity_threshold: float = _EXPOSURE_SIMILARITY_THRESHOLD
    validation_rmse_multiplier: float = _VALIDATION_RMSE_MULTIPLIER

    def validate(self) -> None:
        base = FactorExposureConfigV1(
            correlation_threshold=self.correlation_threshold,
            vif_threshold=self.vif_threshold,
            condition_number_threshold=self.condition_number_threshold,
            min_samples=self.min_samples,
        )
        base.validate()
        if not 0.0 < self.validation_fraction < 1.0:
            raise ValueError("validation_fraction must be between 0 and 1")
        if self.stability_window_count < 2:
            raise ValueError("stability_window_count must be at least 2")


@dataclass(frozen=True)
class FactorExposureDiagnosticsEvidenceV0:
    evidence_type: str
    model_family: str
    target_name: str
    strategy_or_signal_id: str
    feature_names: Tuple[str, ...]
    factor_groups: Dict[str, str]
    n_samples: int
    n_features: int
    solver: str
    fit_intercept: bool
    coefficients: Dict[str, float]
    coefficient_signs: Dict[str, str]
    n_samples_train: int
    n_samples_validation: int
    train_r2: float
    validation_r2: float | None
    train_rmse: float
    validation_rmse: float | None
    train_mae: float
    validation_mae: float | None
    condition_number: float | None
    matrix_rank: int
    rank_deficient: bool
    residual_diagnostics: Dict[str, object]
    beta_stability: Dict[str, object]
    dominant_factor_exposures: Tuple[str, ...]
    common_exposure_similarity_matrix: Dict[str, Dict[str, float]]
    exposure_cluster_assignments: Dict[str, int]
    cluster_concentration_diagnostics: Dict[str, object]
    unexplained_residual_share: float
    dropped_rows_by_reason: Dict[str, int]
    missing_factor_groups: Tuple[str, ...]
    feature_matrix_digest: str
    target_digest: str
    config_digest: str
    source_evidence_refs: Tuple[str, ...]
    time_range: Dict[str, str]
    instrument_universe_digest: str
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
            "strategy_or_signal_id": self.strategy_or_signal_id,
            "feature_names": list(self.feature_names),
            "factor_groups": dict(self.factor_groups),
            "n_samples": self.n_samples,
            "n_features": self.n_features,
            "solver": self.solver,
            "fit_intercept": self.fit_intercept,
            "coefficients": dict(self.coefficients),
            "coefficient_signs": dict(self.coefficient_signs),
            "n_samples_train": self.n_samples_train,
            "n_samples_validation": self.n_samples_validation,
            "train_r2": self.train_r2,
            "validation_r2": self.validation_r2,
            "train_rmse": self.train_rmse,
            "validation_rmse": self.validation_rmse,
            "train_mae": self.train_mae,
            "validation_mae": self.validation_mae,
            "condition_number": self.condition_number,
            "matrix_rank": self.matrix_rank,
            "rank_deficient": self.rank_deficient,
            "residual_diagnostics": dict(self.residual_diagnostics),
            "beta_stability": dict(self.beta_stability),
            "dominant_factor_exposures": list(self.dominant_factor_exposures),
            "common_exposure_similarity_matrix": self.common_exposure_similarity_matrix,
            "exposure_cluster_assignments": dict(self.exposure_cluster_assignments),
            "cluster_concentration_diagnostics": dict(self.cluster_concentration_diagnostics),
            "unexplained_residual_share": self.unexplained_residual_share,
            "dropped_rows_by_reason": dict(self.dropped_rows_by_reason),
            "missing_factor_groups": list(self.missing_factor_groups),
            "feature_matrix_digest": self.feature_matrix_digest,
            "target_digest": self.target_digest,
            "config_digest": self.config_digest,
            "source_evidence_refs": list(self.source_evidence_refs),
            "time_range": dict(self.time_range),
            "instrument_universe_digest": self.instrument_universe_digest,
            "validation_policy": self.validation_policy,
            "status": self.status,
            "reason_codes": list(self.reason_codes),
            "authority_effect": self.authority_effect,
            "runtime_effect": self.runtime_effect,
        }


def _r2_score(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    ss_tot = float(np.sum((y_true - float(np.mean(y_true))) ** 2))
    if ss_tot == 0.0:
        return 0.0
    ss_res = float(np.sum((y_true - y_pred) ** 2))
    return float(1.0 - ss_res / ss_tot)


def _coefficient_signs(coefficients: Mapping[str, float]) -> Dict[str, str]:
    signs: Dict[str, str] = {}
    for name, value in sorted(coefficients.items()):
        if name == "intercept":
            continue
        if value > 0:
            signs[name] = "positive"
        elif value < 0:
            signs[name] = "negative"
        else:
            signs[name] = "zero"
    return signs


def _resolve_factor_groups(feature_names: Sequence[str]) -> tuple[Dict[str, str], tuple[str, ...]]:
    groups = {
        name: PRODUCTIVE_FACTOR_GROUPS_V0.get(name, "NOT_AVAILABLE")
        for name in sorted(feature_names)
    }
    missing = tuple(
        sorted(
            {
                group
                for group in (
                    "market_common_return",
                    "volatility",
                    "trend",
                    "momentum",
                    "liquidity_spread",
                    "funding",
                    "regime",
                    "instrument_common_cluster",
                )
                if group not in groups.values()
            }
        )
    )
    return groups, missing


def _time_ordered_split(n: int, validation_fraction: float) -> int:
    if validation_fraction <= 0.0 or validation_fraction >= 1.0:
        raise ValueError(REASON_RANDOM_VALIDATION_SPLIT_BLOCKED)
    split = max(1, min(n - 1, int(round(n * (1.0 - validation_fraction)))))
    return split


def _fit_ols_split_metrics(
    x: np.ndarray,
    y: np.ndarray,
    factor_names: tuple[str, ...],
    *,
    validation_fraction: float,
) -> tuple[
    Dict[str, float],
    int,
    int,
    float,
    float | None,
    float,
    float | None,
    float,
    float | None,
    np.ndarray,
    int,
    float,
]:
    n = x.shape[0]
    split = _time_ordered_split(n, validation_fraction)
    x_train = x[:split]
    y_train = y[:split]
    x_val = x[split:]
    y_val = y[split:]

    design_train = np.column_stack([np.ones(x_train.shape[0]), x_train])
    design_all = np.column_stack([np.ones(x.shape[0]), x])
    design_val = (
        np.column_stack([np.ones(x_val.shape[0]), x_val]) if len(x_val) else np.empty((0, 0))
    )

    beta, _, rank, _ = np.linalg.lstsq(design_train, y_train, rcond=None)
    y_pred_train = design_train @ beta
    y_pred_val = design_val @ beta if len(x_val) else np.asarray([], dtype=float)
    y_pred_all = design_all @ beta
    residuals = y - y_pred_all

    coefficients = {"intercept": float(beta[0])}
    coefficients.update({name: float(value) for name, value in zip(factor_names, beta[1:])})

    train_r2 = _r2_score(y_train, y_pred_train)
    val_r2 = _r2_score(y_val, y_pred_val) if len(y_val) else None
    train_rmse = float(np.sqrt(np.mean((y_train - y_pred_train) ** 2)))
    val_rmse = float(np.sqrt(np.mean((y_val - y_pred_val) ** 2))) if len(y_val) else None
    train_mae = float(np.mean(np.abs(y_train - y_pred_train)))
    val_mae = float(np.mean(np.abs(y_val - y_pred_val))) if len(y_val) else None
    condition_number = float(np.linalg.cond(design_train))
    return (
        coefficients,
        split,
        n - split,
        train_r2,
        val_r2,
        train_rmse,
        val_rmse,
        train_mae,
        val_mae,
        residuals,
        int(rank),
        condition_number,
    )


def compute_beta_stability_v0(
    records: Sequence[FactorExposureInputV1],
    *,
    factor_names: tuple[str, ...],
    window_count: int,
    min_samples: int,
) -> dict[str, object]:
    if window_count < 2:
        return {"computed": False, "reason": "INSUFFICIENT_WINDOW_COUNT"}
    ordered = _validate_temporal_bindings(records)
    n = len(ordered)
    if n < min_samples:
        return {"computed": False, "reason": REASON_INSUFFICIENT_SAMPLE_COUNT}

    windows: list[dict[str, object]] = []
    per_factor_values: dict[str, list[float]] = {name: [] for name in factor_names}

    window_size = max(3, n // window_count)
    min_window_samples = max(3, min(min_samples, window_size))

    for start in range(0, n, window_size):
        chunk = ordered[start : start + window_size]
        if len(chunk) < min_window_samples:
            continue
        x, y, names, _, _ = build_factor_matrix(chunk)
        if names != factor_names:
            continue
        x, names, _ = _exclude_strict_zero_variance_factors_v0(x, names)
        if not names or x.shape[0] < min_window_samples:
            continue
        design = np.column_stack([np.ones(x.shape[0]), x])
        beta, _, _, _ = np.linalg.lstsq(design, y, rcond=None)
        coeffs = {name: float(value) for name, value in zip(names, beta[1:])}
        windows.append(
            {
                "start_index": start,
                "end_index": start + len(chunk) - 1,
                "n_samples": len(chunk),
                "coefficients": coeffs,
            }
        )
        for name, value in coeffs.items():
            per_factor_values.setdefault(name, []).append(value)

    if len(windows) < 2:
        return {"computed": False, "reason": REASON_INSUFFICIENT_SAMPLE_COUNT, "windows": windows}

    sign_unstable: list[str] = []
    beta_dispersion: dict[str, float] = {}
    for name, values in sorted(per_factor_values.items()):
        if len(values) < 2:
            continue
        signs = {1 if v > 0 else (-1 if v < 0 else 0) for v in values}
        if len(signs) > 1:
            sign_unstable.append(name)
        beta_dispersion[name] = float(np.std(values))

    return {
        "computed": True,
        "window_count": len(windows),
        "windows": windows,
        "sign_unstable_factors": tuple(sign_unstable),
        "beta_dispersion": beta_dispersion,
        "stable": not sign_unstable,
    }


def compute_exposure_similarity_matrix_v0(
    exposure_vectors: Mapping[str, Mapping[str, float]],
) -> dict[str, dict[str, float]]:
    ids = sorted(exposure_vectors.keys())
    names = factor_names_from_vectors(exposure_vectors)
    matrix: dict[str, dict[str, float]] = {}
    for left in ids:
        matrix[left] = {}
        left_vec = np.asarray(
            [exposure_vectors[left].get(name, 0.0) for name in names], dtype=float
        )
        left_norm = float(np.linalg.norm(left_vec))
        for right in ids:
            right_vec = np.asarray(
                [exposure_vectors[right].get(name, 0.0) for name in names], dtype=float
            )
            right_norm = float(np.linalg.norm(right_vec))
            if left_norm == 0.0 or right_norm == 0.0:
                matrix[left][right] = 1.0 if left == right else 0.0
            else:
                matrix[left][right] = float(np.dot(left_vec, right_vec) / (left_norm * right_norm))
    return matrix


def factor_names_from_vectors(
    exposure_vectors: Mapping[str, Mapping[str, float]],
) -> tuple[str, ...]:
    names: set[str] = set()
    for vector in exposure_vectors.values():
        names.update(vector.keys())
    return tuple(sorted(names))


def classify_exposure_clusters_v0(
    similarity_matrix: Mapping[str, Mapping[str, float | int]],
    *,
    threshold: float,
) -> tuple[dict[str, int], dict[str, object]]:
    ids = sorted(similarity_matrix.keys())
    if len(ids) <= 1:
        return {ids[0]: 0} if ids else {}, {
            "cluster_count": len(ids),
            "max_pairwise_similarity": 0.0,
        }

    parent = {item: item for item in ids}

    def find(node: str) -> str:
        while parent[node] != node:
            parent[node] = parent[parent[node]]
            node = parent[node]
        return node

    def union(a: str, b: str) -> None:
        root_a = find(a)
        root_b = find(b)
        if root_a != root_b:
            parent[root_b] = root_a

    max_similarity = 0.0
    high_pairs: list[tuple[str, str, float]] = []
    for index, left in enumerate(ids):
        for right in ids[index + 1 :]:
            value = float(similarity_matrix[left][right])
            max_similarity = max(max_similarity, abs(value))
            if abs(value) >= threshold:
                high_pairs.append((left, right, value))
                union(left, right)

    cluster_map: dict[str, int] = {}
    cluster_ids: dict[str, int] = {}
    next_cluster = 0
    for item in ids:
        root = find(item)
        if root not in cluster_ids:
            cluster_ids[root] = next_cluster
            next_cluster += 1
        cluster_map[item] = cluster_ids[root]

    cluster_sizes: dict[int, int] = {}
    for cluster in cluster_map.values():
        cluster_sizes[cluster] = cluster_sizes.get(cluster, 0) + 1
    max_cluster_size = max(cluster_sizes.values()) if cluster_sizes else 0
    concentration_ratio = max_cluster_size / len(ids) if ids else 0.0

    return cluster_map, {
        "cluster_count": next_cluster,
        "max_pairwise_similarity": max_similarity,
        "high_similarity_pairs": high_pairs,
        "cluster_sizes": cluster_sizes,
        "cluster_concentration_ratio": concentration_ratio,
        "cluster_concentration_high": concentration_ratio >= 0.67 and next_cluster <= 2,
    }


def fit_factor_exposure_diagnostics_v0(
    records: Sequence[FactorExposureInputV1],
    *,
    strategy_or_signal_id: str = "pooled",
    config: FactorExposureDiagnosticsConfigV0 | None = None,
    source_evidence_refs: Sequence[str] = (),
    instrument_universe_digest: str = "",
    time_range: Mapping[str, str] | None = None,
    dropped_rows_by_reason: Mapping[str, int] | None = None,
    productive_binding_gap: bool = False,
    fixture_scaffold: bool = False,
) -> FactorExposureDiagnosticsEvidenceV0:
    cfg = config or FactorExposureDiagnosticsConfigV0()
    cfg.validate()
    base_config = FactorExposureConfigV1(
        correlation_threshold=cfg.correlation_threshold,
        vif_threshold=cfg.vif_threshold,
        condition_number_threshold=cfg.condition_number_threshold,
        min_samples=cfg.min_samples,
    )

    empty_time_range: dict[str, str] = {}
    if not records:
        base = fit_factor_exposure(
            [],
            config=base_config,
            productive_binding_gap=productive_binding_gap,
            fixture_scaffold=fixture_scaffold,
        )
        return FactorExposureDiagnosticsEvidenceV0(
            evidence_type="factor_exposure_diagnostics",
            model_family="ordinary_least_squares",
            target_name=base.target_name,
            strategy_or_signal_id=strategy_or_signal_id,
            feature_names=(),
            factor_groups={},
            n_samples=0,
            n_features=0,
            solver="numpy.linalg.lstsq",
            fit_intercept=True,
            coefficients={},
            coefficient_signs={},
            n_samples_train=0,
            n_samples_validation=0,
            train_r2=0.0,
            validation_r2=None,
            train_rmse=0.0,
            validation_rmse=None,
            train_mae=0.0,
            validation_mae=None,
            condition_number=None,
            matrix_rank=0,
            rank_deficient=True,
            residual_diagnostics={"computed": False},
            beta_stability={"computed": False},
            dominant_factor_exposures=(),
            common_exposure_similarity_matrix={},
            exposure_cluster_assignments={},
            cluster_concentration_diagnostics={"computed": False},
            unexplained_residual_share=1.0,
            dropped_rows_by_reason=dict(dropped_rows_by_reason or {}),
            missing_factor_groups=tuple(
                sorted(
                    {
                        "market_common_return",
                        "volatility",
                        "trend",
                        "momentum",
                        "liquidity_spread",
                        "funding",
                        "regime",
                        "instrument_common_cluster",
                    }
                )
            ),
            feature_matrix_digest=base.feature_matrix_digest,
            target_digest=base.target_digest,
            config_digest=_stable_digest(
                [
                    cfg.correlation_threshold,
                    cfg.vif_threshold,
                    cfg.condition_number_threshold,
                    cfg.min_samples,
                    cfg.validation_fraction,
                    cfg.stability_window_count,
                ]
            ),
            source_evidence_refs=tuple(source_evidence_refs),
            time_range=dict(time_range or empty_time_range),
            instrument_universe_digest=instrument_universe_digest,
            validation_policy="time_ordered",
            status=base.status,
            reason_codes=base.reason_codes,
            authority_effect=_AUTHORITY_EFFECT,
            runtime_effect=_RUNTIME_EFFECT,
        )

    base = fit_factor_exposure(
        records,
        config=base_config,
        productive_binding_gap=productive_binding_gap,
        fixture_scaffold=fixture_scaffold,
    )
    reason_codes = list(base.reason_codes)
    if fixture_scaffold and REASON_FIXTURE_SCAFFOLD_DIAGNOSTIC_ONLY not in reason_codes:
        reason_codes.append(REASON_FIXTURE_SCAFFOLD_DIAGNOSTIC_ONLY)

    x, y, factor_names, x_digest, y_digest = build_factor_matrix(records)
    x, factor_names, excluded = _exclude_strict_zero_variance_factors_v0(x, factor_names)
    factor_groups, missing_groups = _resolve_factor_groups(factor_names)

    if base.status != "DIAGNOSTIC_ONLY" or not factor_names:
        return FactorExposureDiagnosticsEvidenceV0(
            evidence_type="factor_exposure_diagnostics",
            model_family="ordinary_least_squares",
            target_name=base.target_name,
            strategy_or_signal_id=strategy_or_signal_id,
            feature_names=factor_names,
            factor_groups=factor_groups,
            n_samples=int(x.shape[0]),
            n_features=len(factor_names),
            solver="numpy.linalg.lstsq",
            fit_intercept=True,
            coefficients=dict(base.coefficients),
            coefficient_signs=_coefficient_signs(base.coefficients),
            n_samples_train=0,
            n_samples_validation=0,
            train_r2=float(base.diagnostics.get("r2", 0.0))
            if base.diagnostics.get("computed")
            else 0.0,
            validation_r2=None,
            train_rmse=float(base.diagnostics.get("rmse", 0.0))
            if base.diagnostics.get("computed")
            else 0.0,
            validation_rmse=None,
            train_mae=float(base.diagnostics.get("mae", 0.0))
            if base.diagnostics.get("computed")
            else 0.0,
            validation_mae=None,
            condition_number=(
                float(base.diagnostics["condition_number"])
                if base.diagnostics.get("condition_number") is not None
                else None
            ),
            matrix_rank=int(base.diagnostics.get("rank", 0)),
            rank_deficient=base.status == "RANK_DEFICIENT_BLOCKED",
            residual_diagnostics={"computed": bool(base.diagnostics.get("computed"))},
            beta_stability={"computed": False},
            dominant_factor_exposures=(),
            common_exposure_similarity_matrix={},
            exposure_cluster_assignments={},
            cluster_concentration_diagnostics={"computed": False},
            unexplained_residual_share=1.0,
            dropped_rows_by_reason=dict(dropped_rows_by_reason or {}),
            missing_factor_groups=missing_groups,
            feature_matrix_digest=x_digest,
            target_digest=y_digest,
            config_digest=_stable_digest(
                [
                    cfg.correlation_threshold,
                    cfg.vif_threshold,
                    cfg.condition_number_threshold,
                    cfg.min_samples,
                    cfg.validation_fraction,
                    cfg.stability_window_count,
                ]
            ),
            source_evidence_refs=tuple(source_evidence_refs),
            time_range=dict(time_range or empty_time_range),
            instrument_universe_digest=instrument_universe_digest,
            validation_policy="time_ordered",
            status=base.status,
            reason_codes=tuple(reason_codes),
            authority_effect=_AUTHORITY_EFFECT,
            runtime_effect=_RUNTIME_EFFECT,
        )

    (
        coefficients,
        n_train,
        n_val,
        train_r2,
        val_r2,
        train_rmse,
        val_rmse,
        train_mae,
        val_mae,
        residuals,
        matrix_rank,
        condition_number,
    ) = _fit_ols_split_metrics(
        x,
        y,
        factor_names,
        validation_fraction=cfg.validation_fraction,
    )

    if not isfinite(condition_number) or condition_number > cfg.condition_number_threshold:
        reason_codes.append(REASON_HIGH_CONDITION_NUMBER)
    if matrix_rank < len(factor_names) + 1:
        reason_codes.append(REASON_RANK_DEFICIENT)

    residual_std = float(np.std(residuals))
    outlier_count = int(np.sum(np.abs(residuals) > 3.0 * residual_std)) if residual_std > 0 else 0
    if outlier_count > max(1, int(0.1 * len(residuals))):
        reason_codes.append(REASON_OUTLIER_DOMINATED)

    if (
        val_rmse is not None
        and train_rmse > 0
        and val_rmse > cfg.validation_rmse_multiplier * train_rmse
    ):
        reason_codes.append(REASON_VALIDATION_ERROR_TOO_HIGH)

    beta_stability = compute_beta_stability_v0(
        records,
        factor_names=factor_names,
        window_count=cfg.stability_window_count,
        min_samples=cfg.min_samples,
    )
    if beta_stability.get("computed") and beta_stability.get("sign_unstable_factors"):
        reason_codes.append(REASON_COEFFICIENT_SIGN_UNSTABLE)
        reason_codes.append(REASON_BETA_INSTABILITY)

    abs_coeffs = [
        (name, abs(float(value))) for name, value in coefficients.items() if name != "intercept"
    ]
    abs_coeffs.sort(key=lambda item: (-item[1], item[0]))
    dominant = tuple(name for name, _ in abs_coeffs[: min(2, len(abs_coeffs))])

    ss_tot = float(np.sum((y - float(np.mean(y))) ** 2))
    unexplained = 1.0 if ss_tot == 0.0 else float(np.sum(residuals**2) / ss_tot)

    status = "DIAGNOSTIC_ONLY"
    if REASON_RANK_DEFICIENT in reason_codes or REASON_HIGH_CONDITION_NUMBER in reason_codes:
        status = "RANK_DEFICIENT_BLOCKED"
    elif (
        REASON_VALIDATION_ERROR_TOO_HIGH in reason_codes or REASON_BETA_INSTABILITY in reason_codes
    ):
        status = "ROBUSTNESS_FAILED"

    return FactorExposureDiagnosticsEvidenceV0(
        evidence_type="factor_exposure_diagnostics",
        model_family="ordinary_least_squares",
        target_name=base.target_name,
        strategy_or_signal_id=strategy_or_signal_id,
        feature_names=factor_names,
        factor_groups=factor_groups,
        n_samples=int(x.shape[0]),
        n_features=len(factor_names),
        solver="numpy.linalg.lstsq",
        fit_intercept=True,
        coefficients=coefficients,
        coefficient_signs=_coefficient_signs(coefficients),
        n_samples_train=n_train,
        n_samples_validation=n_val,
        train_r2=train_r2,
        validation_r2=val_r2,
        train_rmse=train_rmse,
        validation_rmse=val_rmse,
        train_mae=train_mae,
        validation_mae=val_mae,
        condition_number=condition_number,
        matrix_rank=matrix_rank,
        rank_deficient=matrix_rank < len(factor_names) + 1,
        residual_diagnostics={
            "computed": True,
            "residual_mean": float(np.mean(residuals)),
            "residual_std": residual_std,
            "outlier_count": outlier_count,
            "max_abs_error": float(np.max(np.abs(residuals))),
        },
        beta_stability=beta_stability,
        dominant_factor_exposures=dominant,
        common_exposure_similarity_matrix={},
        exposure_cluster_assignments={},
        cluster_concentration_diagnostics={"computed": False},
        unexplained_residual_share=unexplained,
        dropped_rows_by_reason=dict(dropped_rows_by_reason or {}),
        missing_factor_groups=missing_groups,
        feature_matrix_digest=x_digest,
        target_digest=y_digest,
        config_digest=_stable_digest(
            [
                cfg.correlation_threshold,
                cfg.vif_threshold,
                cfg.condition_number_threshold,
                cfg.min_samples,
                cfg.validation_fraction,
                cfg.stability_window_count,
            ]
        ),
        source_evidence_refs=tuple(source_evidence_refs),
        time_range=dict(time_range or empty_time_range),
        instrument_universe_digest=instrument_universe_digest,
        validation_policy="time_ordered",
        status=status,
        reason_codes=tuple(dict.fromkeys(reason_codes)),
        authority_effect=_AUTHORITY_EFFECT,
        runtime_effect=_RUNTIME_EFFECT,
    )


def build_cross_entity_exposure_diagnostics_v0(
    grouped_records: Mapping[str, Sequence[FactorExposureInputV1]],
    *,
    config: FactorExposureDiagnosticsConfigV0 | None = None,
    source_evidence_refs: Sequence[str] = (),
    instrument_universe_digest: str = "",
    time_range: Mapping[str, str] | None = None,
    dropped_rows_by_reason: Mapping[str, int] | None = None,
) -> tuple[
    dict[str, FactorExposureDiagnosticsEvidenceV0],
    dict[str, dict[str, float]],
    dict[str, int],
    dict[str, object],
]:
    """Fit per-entity diagnostics and derive exposure similarity / cluster flags."""
    cfg = config or FactorExposureDiagnosticsConfigV0()
    per_entity: dict[str, FactorExposureDiagnosticsEvidenceV0] = {}
    exposure_vectors: dict[str, dict[str, float]] = {}

    for entity_id in sorted(grouped_records.keys()):
        entity_records = grouped_records[entity_id]
        evidence = fit_factor_exposure_diagnostics_v0(
            entity_records,
            strategy_or_signal_id=entity_id,
            config=cfg,
            source_evidence_refs=source_evidence_refs,
            instrument_universe_digest=instrument_universe_digest,
            time_range=time_range,
            dropped_rows_by_reason=dropped_rows_by_reason,
        )
        per_entity[entity_id] = evidence
        if evidence.coefficients:
            exposure_vectors[entity_id] = {
                name: float(value)
                for name, value in evidence.coefficients.items()
                if name != "intercept"
            }

    similarity = compute_exposure_similarity_matrix_v0(exposure_vectors)
    cluster_assignments, cluster_diag = classify_exposure_clusters_v0(
        similarity,
        threshold=cfg.exposure_similarity_threshold,
    )

    cluster_reasons: list[str] = []
    if cluster_diag.get("cluster_concentration_high"):
        cluster_reasons.append(REASON_CLUSTER_CONCENTRATION_HIGH)
    if float(cluster_diag.get("max_pairwise_similarity", 0.0)) >= cfg.exposure_similarity_threshold:
        cluster_reasons.append(REASON_DOMINANT_COMMON_FACTOR_EXPOSURE)

    updated: dict[str, FactorExposureDiagnosticsEvidenceV0] = {}
    for entity_id, evidence in per_entity.items():
        reasons = list(evidence.reason_codes)
        reasons.extend(cluster_reasons)
        status = evidence.status
        if cluster_reasons and status == "DIAGNOSTIC_ONLY":
            status = "ROBUSTNESS_FAILED"
        updated[entity_id] = replace(
            evidence,
            common_exposure_similarity_matrix=similarity,
            exposure_cluster_assignments=cluster_assignments,
            cluster_concentration_diagnostics={**cluster_diag, "computed": True},
            reason_codes=tuple(dict.fromkeys(reasons)),
            status=status,
        )

    return updated, similarity, cluster_assignments, cluster_diag


def make_deterministic_factor_exposure_fixture() -> list[FactorExposureInputV1]:
    records: list[FactorExposureInputV1] = []
    fixtures = [
        (
            "PF_ETHUSD",
            1,
            0.010,
            {"market_beta": 0.10, "liquidity_beta": 0.05, "volatility_beta": 0.20},
        ),
        (
            "PF_ETHUSD",
            2,
            0.012,
            {"market_beta": 0.11, "liquidity_beta": 0.04, "volatility_beta": 0.19},
        ),
        (
            "PF_ETHUSD",
            3,
            0.009,
            {"market_beta": 0.09, "liquidity_beta": 0.06, "volatility_beta": 0.21},
        ),
        (
            "PF_SOLUSD",
            4,
            -0.004,
            {"market_beta": -0.02, "liquidity_beta": 0.03, "volatility_beta": 0.25},
        ),
        (
            "PF_SOLUSD",
            5,
            -0.006,
            {"market_beta": -0.03, "liquidity_beta": 0.02, "volatility_beta": 0.26},
        ),
        (
            "PF_SOLUSD",
            6,
            0.003,
            {"market_beta": 0.04, "liquidity_beta": 0.08, "volatility_beta": 0.18},
        ),
        (
            "PF_AVAXUSD",
            7,
            0.007,
            {"market_beta": 0.08, "liquidity_beta": 0.07, "volatility_beta": 0.17},
        ),
        (
            "PF_AVAXUSD",
            8,
            0.006,
            {"market_beta": 0.07, "liquidity_beta": 0.07, "volatility_beta": 0.16},
        ),
        (
            "PF_DOTUSD",
            9,
            -0.002,
            {"market_beta": 0.01, "liquidity_beta": 0.01, "volatility_beta": 0.22},
        ),
        (
            "PF_DOTUSD",
            10,
            0.001,
            {"market_beta": 0.03, "liquidity_beta": 0.02, "volatility_beta": 0.20},
        ),
    ]
    for instrument_id, timestamp, target_return, factor_values in fixtures:
        records.append(
            FactorExposureInputV1(
                instrument_id=instrument_id,
                timestamp=timestamp,
                target_return=target_return,
                factor_values=factor_values,
                factor_time=f"2026-01-01T{timestamp:02d}:00:00Z",
                decision_time=f"2026-01-01T{timestamp + 1:02d}:00:00Z",
            )
        )
    return records
