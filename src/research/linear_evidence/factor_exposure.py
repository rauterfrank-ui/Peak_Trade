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
