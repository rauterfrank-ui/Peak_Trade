from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from math import isfinite
from typing import Dict, Iterable, List, Mapping, Sequence, Tuple

import numpy as np

from .fitters import (
    REASON_RANK_DEFICIENT_FEATURE_MATRIX,
    REASON_ZERO_VARIANCE_FEATURE,
)

_ALLOWED_STATUSES = frozenset(
    {
        "DIAGNOSTIC_ONLY",
        "INSUFFICIENT_DATA",
        "RANK_DEFICIENT_BLOCKED",
    }
)
_AUTHORITY_EFFECT = "NONE"
_RUNTIME_EFFECT = "NONE"
REASON_INSUFFICIENT_SAMPLE_COUNT = "INSUFFICIENT_SAMPLE_COUNT"
REASON_SIGNAL_REDUNDANCY_REPORTED = "SIGNAL_REDUNDANCY_REPORTED"
_REASON_INSUFFICIENT_SAMPLE_COUNT = REASON_INSUFFICIENT_SAMPLE_COUNT
_REASON_SIGNAL_REDUNDANCY_REPORTED = REASON_SIGNAL_REDUNDANCY_REPORTED
_REASON_HIGH_CONDITION_NUMBER = "HIGH_CONDITION_NUMBER"
_REASON_TIME_ORDERING_FAILED = "TIME_ORDERING_FAILED"
_REASON_LOOKAHEAD_BLOCKED = "LOOKAHEAD_BLOCKED"
_REASON_PRODUCTIVE_BINDING_GAP = "PRODUCTIVE_BINDING_GAP"
_DEFAULT_TIME_NAME = "decision_time"
_DEFAULT_FEATURE_TIME_NAME = "feature_time"


@dataclass(frozen=True)
class SignalOrthogonalityConfigV1:
    correlation_threshold: float = 0.85
    condition_number_threshold: float = 1000.0
    min_samples: int = 8

    def validate(self) -> None:
        if not 0.0 < self.correlation_threshold < 1.0:
            raise ValueError("correlation_threshold must be between 0 and 1")
        if self.condition_number_threshold <= 0:
            raise ValueError("condition_number_threshold must be positive")
        if self.min_samples < 3:
            raise ValueError("min_samples must be at least 3")


@dataclass(frozen=True)
class SignalOrthogonalityPrecheckV0:
    target_is_constant: bool
    zero_variance_feature_names: tuple[str, ...]
    reason_codes: tuple[str, ...]
    blocking: bool


@dataclass(frozen=True)
class SignalOrthogonalityEvidenceV1:
    evidence_type: str
    model_family: str
    target_name: str
    feature_names: Tuple[str, ...]
    n_samples: int
    n_features: int
    solver: str
    fit_intercept: bool
    coefficients: Mapping[str, float]
    diagnostics: Mapping[str, object]
    feature_matrix_digest: str
    target_digest: str
    config_digest: str
    time_range: Mapping[str, object]
    instrument_universe_digest: str
    row_count_before_filter: int
    row_count_after_filter: int
    dropped_rows_by_reason: Mapping[str, int]
    validation_policy: Mapping[str, object]
    cost_policy_output: str
    status: str
    authority_effect: str
    runtime_effect: str
    reason_codes: Tuple[str, ...]


def _stable_digest(parts: Iterable[object]) -> str:
    payload = json.dumps(list(parts), sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _sorted_unique_feature_names(feature_names: Sequence[str]) -> tuple[str, ...]:
    names = tuple(sorted(str(name) for name in feature_names))
    if not names:
        raise ValueError("feature_names must not be empty")
    if len(set(names)) != len(names):
        raise ValueError("feature_names must be unique")
    return names


def _time_order_rows(
    rows: Sequence[Mapping[str, object]],
    *,
    time_name: str = _DEFAULT_TIME_NAME,
) -> list[Mapping[str, object]]:
    if not rows:
        return []
    ordered = sorted(rows, key=lambda row: str(row.get(time_name, "")))
    times = [str(row.get(time_name, "")) for row in ordered]
    if any(not value for value in times):
        raise ValueError("TIME_BINDING_MISSING")
    if times != sorted(times):
        raise ValueError(_REASON_TIME_ORDERING_FAILED)
    return list(ordered)


def _assert_feature_time_before_target_time(
    rows: Sequence[Mapping[str, object]],
    *,
    feature_time_name: str = _DEFAULT_FEATURE_TIME_NAME,
    target_time_name: str = _DEFAULT_TIME_NAME,
) -> None:
    for row in rows:
        feature_time = row.get(feature_time_name)
        target_time = row.get(target_time_name)
        if feature_time is None or target_time is None:
            continue
        if str(feature_time) >= str(target_time):
            raise ValueError(_REASON_LOOKAHEAD_BLOCKED)


def _as_float_matrix(
    rows: Sequence[Mapping[str, object]], feature_names: Sequence[str]
) -> Tuple[np.ndarray, dict[str, int]]:
    matrix: List[List[float]] = []
    dropped: dict[str, int] = {}
    for row in rows:
        values: List[float] = []
        ok = True
        for name in feature_names:
            try:
                value = float(row[name])
            except (KeyError, TypeError, ValueError):
                ok = False
                dropped["missing_or_non_numeric_feature"] = (
                    dropped.get("missing_or_non_numeric_feature", 0) + 1
                )
                break
            if not isfinite(value):
                ok = False
                dropped["non_finite_feature"] = dropped.get("non_finite_feature", 0) + 1
                break
            values.append(value)
        if ok:
            matrix.append(values)
    if not matrix:
        return np.empty((0, len(feature_names)), dtype=float), dropped
    return np.asarray(matrix, dtype=float), dropped


def compute_signal_orthogonality_precheck_v0(
    matrix: np.ndarray,
    feature_names: Sequence[str],
    *,
    min_samples: int,
) -> SignalOrthogonalityPrecheckV0:
    reason_codes: list[str] = []
    if matrix.shape[0] < min_samples:
        reason_codes.append(_REASON_INSUFFICIENT_SAMPLE_COUNT)

    zero_variance_feature_names: list[str] = []
    if matrix.size:
        for index, name in enumerate(feature_names):
            if float(np.var(matrix[:, index])) == 0.0:
                zero_variance_feature_names.append(str(name))
                reason_codes.append(f"{REASON_ZERO_VARIANCE_FEATURE}:{name}")

    blocking = bool(matrix.shape[0] < min_samples or zero_variance_feature_names)
    return SignalOrthogonalityPrecheckV0(
        target_is_constant=False,
        zero_variance_feature_names=tuple(sorted(zero_variance_feature_names)),
        reason_codes=tuple(dict.fromkeys(reason_codes)),
        blocking=blocking,
    )


def _validation_policy() -> dict[str, object]:
    return {
        "offline_only": True,
        "validation_split": "not_applicable_for_unsupervised_orthogonality_diagnostic",
        "random_split_allowed": False,
        "lookahead_allowed": False,
        "strategy_selection_effect": False,
        "feature_time_less_than_target_time": True,
        "time_ordered": True,
    }


def _blocked_diagnostics(*, computed: bool = False) -> dict[str, object]:
    return {
        "computed": computed,
        "correlation_threshold": None,
        "condition_number_threshold": None,
        "rank": 0,
        "condition_number": None,
        "pairwise_correlation": {},
        "redundant_pairs": [],
        "vif_scores": {},
        "sample_sufficiency": {"sufficient": False},
        "interpretation": "diagnostic_only_redundancy_report_no_strategy_selection_effect",
    }


def _blocked_evidence(
    *,
    names: tuple[str, ...],
    target_name: str,
    matrix: np.ndarray,
    rows: Sequence[Mapping[str, object]],
    row_count_before: int,
    dropped_rows: Mapping[str, int],
    cfg: SignalOrthogonalityConfigV1,
    precheck: SignalOrthogonalityPrecheckV0,
    time_range: Mapping[str, object],
    productive_binding_gap: bool,
) -> SignalOrthogonalityEvidenceV1:
    reasons = list(precheck.reason_codes)
    if productive_binding_gap and _REASON_PRODUCTIVE_BINDING_GAP not in reasons:
        reasons.append(_REASON_PRODUCTIVE_BINDING_GAP)
    if precheck.zero_variance_feature_names and REASON_RANK_DEFICIENT_FEATURE_MATRIX not in reasons:
        reasons.append(REASON_RANK_DEFICIENT_FEATURE_MATRIX)

    status = "INSUFFICIENT_DATA"
    if precheck.zero_variance_feature_names or REASON_RANK_DEFICIENT_FEATURE_MATRIX in reasons:
        status = "RANK_DEFICIENT_BLOCKED"

    return SignalOrthogonalityEvidenceV1(
        evidence_type="SignalOrthogonalityEvidenceV1",
        model_family="linear_diagnostics",
        target_name=target_name,
        feature_names=names,
        n_samples=int(matrix.shape[0]),
        n_features=len(names),
        solver="numpy_correlation_lstsq_vif",
        fit_intercept=True,
        coefficients={},
        diagnostics=_blocked_diagnostics(computed=False),
        feature_matrix_digest=_stable_digest(
            [{name: row.get(name) for name in names} for row in rows]
        ),
        target_digest=_stable_digest([target_name, "diagnostic_only"]),
        config_digest=_stable_digest(
            [cfg.correlation_threshold, cfg.condition_number_threshold, cfg.min_samples]
        ),
        time_range=time_range,
        instrument_universe_digest=_stable_digest(["offline_signal_orthogonality", names]),
        row_count_before_filter=row_count_before,
        row_count_after_filter=int(matrix.shape[0]),
        dropped_rows_by_reason=dict(dropped_rows),
        validation_policy=_validation_policy(),
        cost_policy_output="diagnostic_only",
        status=status,
        authority_effect=_AUTHORITY_EFFECT,
        runtime_effect=_RUNTIME_EFFECT,
        reason_codes=tuple(dict.fromkeys(reasons)),
    )


def _standardize(matrix: np.ndarray) -> np.ndarray:
    if matrix.size == 0:
        return matrix
    means = matrix.mean(axis=0)
    stds = matrix.std(axis=0)
    safe_stds = np.where(stds == 0.0, 1.0, stds)
    return (matrix - means) / safe_stds


def _pairwise_correlations(
    feature_names: Sequence[str], matrix: np.ndarray
) -> Dict[str, Dict[str, float]]:
    if matrix.shape[0] < 2:
        return {name: {other: 0.0 for other in feature_names} for name in feature_names}
    corr = np.corrcoef(matrix, rowvar=False)
    corr = np.nan_to_num(corr, nan=0.0, posinf=0.0, neginf=0.0)
    return {
        feature_names[i]: {feature_names[j]: float(corr[i, j]) for j in range(len(feature_names))}
        for i in range(len(feature_names))
    }


def _redundant_pairs(
    feature_names: Sequence[str], corr: Mapping[str, Mapping[str, float]], threshold: float
) -> List[Dict[str, object]]:
    pairs: List[Dict[str, object]] = []
    for i, left in enumerate(feature_names):
        for right in feature_names[i + 1 :]:
            value = float(corr[left][right])
            if abs(value) >= threshold:
                pairs.append(
                    {
                        "left": left,
                        "right": right,
                        "correlation": value,
                        "abs_correlation": abs(value),
                    }
                )
    pairs.sort(
        key=lambda item: (-float(item["abs_correlation"]), str(item["left"]), str(item["right"]))
    )
    return pairs


def _condition_number(matrix: np.ndarray) -> float:
    if matrix.shape[0] == 0 or matrix.shape[1] == 0:
        return float("inf")
    standardized = _standardize(matrix)
    try:
        value = float(np.linalg.cond(standardized))
    except np.linalg.LinAlgError:
        return float("inf")
    return value


def _rank(matrix: np.ndarray) -> int:
    if matrix.shape[0] == 0 or matrix.shape[1] == 0:
        return 0
    return int(np.linalg.matrix_rank(_standardize(matrix)))


def _vif_scores(feature_names: Sequence[str], matrix: np.ndarray) -> Dict[str, float]:
    scores: Dict[str, float] = {}
    if matrix.shape[0] <= matrix.shape[1] or matrix.shape[1] < 2:
        return {name: float("inf") for name in feature_names}
    x = _standardize(matrix)
    for idx, name in enumerate(feature_names):
        y = x[:, idx]
        others = np.delete(x, idx, axis=1)
        design = np.column_stack([np.ones(others.shape[0]), others])
        try:
            beta, *_ = np.linalg.lstsq(design, y, rcond=None)
            pred = design @ beta
            ss_res = float(np.sum((y - pred) ** 2))
            ss_tot = float(np.sum((y - y.mean()) ** 2))
            r2 = 1.0 - ss_res / ss_tot if ss_tot > 0 else 1.0
            if r2 >= 0.999999:
                scores[name] = float("inf")
            else:
                scores[name] = float(1.0 / max(1e-12, 1.0 - r2))
        except np.linalg.LinAlgError:
            scores[name] = float("inf")
    return scores


def analyze_signal_orthogonality(
    rows: Sequence[Mapping[str, object]],
    feature_names: Sequence[str],
    target_name: str = "diagnostic_only_no_target",
    config: SignalOrthogonalityConfigV1 | None = None,
    *,
    time_name: str = _DEFAULT_TIME_NAME,
    feature_time_name: str = _DEFAULT_FEATURE_TIME_NAME,
    productive_binding_gap: bool = False,
) -> SignalOrthogonalityEvidenceV1:
    cfg = config or SignalOrthogonalityConfigV1()
    cfg.validate()

    names = _sorted_unique_feature_names(feature_names)
    ordered_rows = _time_order_rows(rows, time_name=time_name)
    _assert_feature_time_before_target_time(
        ordered_rows,
        feature_time_name=feature_time_name,
        target_time_name=time_name,
    )

    row_count_before = len(rows)
    matrix, dropped = _as_float_matrix(ordered_rows, names)
    row_count_after = int(matrix.shape[0])

    time_range: Mapping[str, object]
    if ordered_rows and time_name in ordered_rows[0]:
        time_range = {
            "start": str(ordered_rows[0][time_name]),
            "end": str(ordered_rows[-1][time_name]),
            "policy": "time_ordered_finalized_bar_bound",
        }
    else:
        time_range = {"policy": "offline_fixture_or_input_rows", "target_shift": "not_applicable"}

    precheck = compute_signal_orthogonality_precheck_v0(
        matrix,
        names,
        min_samples=cfg.min_samples,
    )
    if precheck.blocking or productive_binding_gap:
        return _blocked_evidence(
            names=names,
            target_name=target_name,
            matrix=matrix,
            rows=ordered_rows,
            row_count_before=row_count_before,
            dropped_rows=dropped,
            cfg=cfg,
            precheck=precheck,
            time_range=time_range,
            productive_binding_gap=productive_binding_gap,
        )

    rank = _rank(matrix)
    condition_number = _condition_number(matrix)
    corr = _pairwise_correlations(names, matrix)
    redundant = _redundant_pairs(names, corr, cfg.correlation_threshold)
    vif = _vif_scores(names, matrix)

    reason_codes: list[str] = []
    if rank < len(names):
        reason_codes.append(REASON_RANK_DEFICIENT_FEATURE_MATRIX)
    if not isfinite(condition_number) or condition_number > cfg.condition_number_threshold:
        reason_codes.append(_REASON_HIGH_CONDITION_NUMBER)
    if redundant:
        reason_codes.append(_REASON_SIGNAL_REDUNDANCY_REPORTED)

    status = "DIAGNOSTIC_ONLY"
    if REASON_RANK_DEFICIENT_FEATURE_MATRIX in reason_codes:
        status = "RANK_DEFICIENT_BLOCKED"

    diagnostics: Dict[str, object] = {
        "computed": True,
        "correlation_threshold": cfg.correlation_threshold,
        "condition_number_threshold": cfg.condition_number_threshold,
        "rank": rank,
        "condition_number": condition_number,
        "pairwise_correlation": corr,
        "redundant_pairs": redundant,
        "vif_scores": vif,
        "sample_sufficiency": {
            "sufficient": row_count_after >= cfg.min_samples,
            "min_samples": cfg.min_samples,
            "actual_samples": row_count_after,
        },
        "interpretation": "diagnostic_only_redundancy_report_no_strategy_selection_effect",
    }

    return SignalOrthogonalityEvidenceV1(
        evidence_type="SignalOrthogonalityEvidenceV1",
        model_family="linear_diagnostics",
        target_name=target_name,
        feature_names=names,
        n_samples=row_count_after,
        n_features=len(names),
        solver="numpy_correlation_lstsq_vif",
        fit_intercept=True,
        coefficients={},
        diagnostics=diagnostics,
        feature_matrix_digest=_stable_digest(
            [{name: row.get(name) for name in names} for row in ordered_rows]
        ),
        target_digest=_stable_digest([target_name, "diagnostic_only"]),
        config_digest=_stable_digest(
            [cfg.correlation_threshold, cfg.condition_number_threshold, cfg.min_samples]
        ),
        time_range=time_range,
        instrument_universe_digest=_stable_digest(["offline_signal_orthogonality", names]),
        row_count_before_filter=row_count_before,
        row_count_after_filter=row_count_after,
        dropped_rows_by_reason=dict(dropped),
        validation_policy=_validation_policy(),
        cost_policy_output="diagnostic_only",
        status=status,
        authority_effect=_AUTHORITY_EFFECT,
        runtime_effect=_RUNTIME_EFFECT,
        reason_codes=tuple(dict.fromkeys(reason_codes)),
    )


def make_deterministic_signal_fixture() -> Tuple[List[Dict[str, float]], Tuple[str, ...]]:
    rows: List[Dict[str, float]] = []
    for idx in range(24):
        trend = float(idx)
        momentum = float(idx * 2 + (idx % 3) * 0.01)
        volatility = float((idx % 5) - 2)
        liquidity = float(10 + ((idx * 7) % 11))
        rows.append(
            {
                "decision_time": f"2026-01-01T{idx + 1:02d}:00:00Z",
                "feature_time": f"2026-01-01T{idx:02d}:00:00Z",
                "trend_following": trend,
                "momentum_1h": momentum,
                "bollinger_bands": volatility,
                "liquidity_context": liquidity,
            }
        )
    return rows, ("bollinger_bands", "liquidity_context", "momentum_1h", "trend_following")


def evidence_to_dict(evidence: SignalOrthogonalityEvidenceV1) -> Dict[str, object]:
    return {
        "evidence_type": evidence.evidence_type,
        "model_family": evidence.model_family,
        "target_name": evidence.target_name,
        "feature_names": list(evidence.feature_names),
        "n_samples": evidence.n_samples,
        "n_features": evidence.n_features,
        "solver": evidence.solver,
        "fit_intercept": evidence.fit_intercept,
        "coefficients": dict(evidence.coefficients),
        "diagnostics": dict(evidence.diagnostics),
        "feature_matrix_digest": evidence.feature_matrix_digest,
        "target_digest": evidence.target_digest,
        "config_digest": evidence.config_digest,
        "time_range": dict(evidence.time_range),
        "instrument_universe_digest": evidence.instrument_universe_digest,
        "row_count_before_filter": evidence.row_count_before_filter,
        "row_count_after_filter": evidence.row_count_after_filter,
        "dropped_rows_by_reason": dict(evidence.dropped_rows_by_reason),
        "validation_policy": dict(evidence.validation_policy),
        "cost_policy_output": evidence.cost_policy_output,
        "status": evidence.status,
        "authority_effect": evidence.authority_effect,
        "runtime_effect": evidence.runtime_effect,
        "reason_codes": list(evidence.reason_codes),
    }


SCOPE_POLICY_VERSION = "signal_orthogonality_diagnostic_policy.v0"
SCOPE_ROLE = "DIAGNOSTIC_ONLY"

REASON_INSUFFICIENT_DATA = "INSUFFICIENT_DATA"
REASON_INSUFFICIENT_OVERLAP = "INSUFFICIENT_OVERLAP"
REASON_NEAR_ZERO_VARIANCE_SIGNAL = "NEAR_ZERO_VARIANCE_SIGNAL"
REASON_DUPLICATE_SIGNAL = "DUPLICATE_SIGNAL"
REASON_NEAR_DUPLICATE_SIGNAL = "NEAR_DUPLICATE_SIGNAL"
REASON_HIGH_PAIRWISE_CORRELATION = "HIGH_PAIRWISE_CORRELATION"
REASON_FEATURE_ALIGNMENT_ERROR = "FEATURE_ALIGNMENT_ERROR"
REASON_TIMESTAMP_ALIGNMENT_ERROR = "TIMESTAMP_ALIGNMENT_ERROR"
REASON_INSTRUMENT_ALIGNMENT_ERROR = "INSTRUMENT_ALIGNMENT_ERROR"
REASON_NON_FINITE_VALUE_DETECTED = "NON_FINITE_VALUE_DETECTED"
REASON_FEATURE_LEAKAGE_RISK = "FEATURE_LEAKAGE_RISK"
REASON_INPUT_DIGEST_MISMATCH = "INPUT_DIGEST_MISMATCH"
REASON_NONDETERMINISTIC_OUTPUT = "NONDETERMINISTIC_OUTPUT"
REASON_RUNTIME_IMPORT_BOUNDARY_VIOLATION = "RUNTIME_IMPORT_BOUNDARY_VIOLATION"
REASON_ORDER_ADAPTER_IMPORT_BOUNDARY_VIOLATION = "ORDER_ADAPTER_IMPORT_BOUNDARY_VIOLATION"
REASON_SCHEDULER_IMPORT_BOUNDARY_VIOLATION = "SCHEDULER_IMPORT_BOUNDARY_VIOLATION"

FAILURE_TAXONOMY_V0: Dict[str, str] = {
    REASON_INSUFFICIENT_DATA: "Sample count below policy minimum; diagnostics blocked.",
    REASON_INSUFFICIENT_OVERLAP: "Pairwise overlap below policy minimum; pair blocked.",
    REASON_ZERO_VARIANCE_FEATURE: "Exact zero variance; signal excluded fail-closed.",
    REASON_NEAR_ZERO_VARIANCE_SIGNAL: "Variance below near-zero threshold; signal excluded.",
    REASON_DUPLICATE_SIGNAL: "Exact duplicate column detected.",
    REASON_NEAR_DUPLICATE_SIGNAL: "Near-linear duplicate detected via correlation threshold.",
    REASON_HIGH_PAIRWISE_CORRELATION: "Pairwise Pearson correlation exceeds policy threshold.",
    REASON_RANK_DEFICIENT_FEATURE_MATRIX: "Matrix rank below feature count.",
    _REASON_HIGH_CONDITION_NUMBER: "Condition number exceeds policy threshold.",
    REASON_FEATURE_ALIGNMENT_ERROR: "Feature column missing or misaligned in input rows.",
    REASON_TIMESTAMP_ALIGNMENT_ERROR: "Timestamp ordering or binding failed.",
    REASON_INSTRUMENT_ALIGNMENT_ERROR: "Instrument grain inconsistent across rows.",
    REASON_NON_FINITE_VALUE_DETECTED: "NaN or Inf detected in signal values.",
    REASON_FEATURE_LEAKAGE_RISK: "Feature time not strictly before decision time.",
    REASON_INPUT_DIGEST_MISMATCH: "Input digest mismatch on rematerialization.",
    REASON_NONDETERMINISTIC_OUTPUT: "Repeated run produced differing output digest.",
    REASON_RUNTIME_IMPORT_BOUNDARY_VIOLATION: "Forbidden runtime import detected.",
    REASON_ORDER_ADAPTER_IMPORT_BOUNDARY_VIOLATION: "Forbidden order adapter import detected.",
    REASON_SCHEDULER_IMPORT_BOUNDARY_VIOLATION: "Forbidden scheduler import detected.",
    REASON_INSUFFICIENT_SAMPLE_COUNT: "Row count below min_samples after filtering.",
    _REASON_SIGNAL_REDUNDANCY_REPORTED: "Redundant pairs reported; diagnostic only.",
    _REASON_PRODUCTIVE_BINDING_GAP: "No manifest-verified productive input bound.",
}


@dataclass(frozen=True)
class SignalOrthogonalityScopePolicyV0:
    version: str = SCOPE_POLICY_VERSION
    correlation_threshold: float = 0.85
    near_duplicate_correlation_threshold: float = 0.999
    condition_number_threshold: float = 1000.0
    min_samples: int = 8
    min_overlap_count: int = 8
    near_zero_variance_threshold: float = 1e-12
    rolling_stability_instability_threshold: float = 0.25
    rolling_time_slice_count: int = 4
    spearman_enabled: bool = True

    def validate(self) -> None:
        if self.version != SCOPE_POLICY_VERSION:
            raise ValueError("unsupported policy version")
        SignalOrthogonalityConfigV1(
            correlation_threshold=self.correlation_threshold,
            condition_number_threshold=self.condition_number_threshold,
            min_samples=self.min_samples,
        ).validate()
        if not 0.0 < self.near_duplicate_correlation_threshold <= 1.0:
            raise ValueError("near_duplicate_correlation_threshold must be in (0, 1]")
        if self.min_overlap_count < 3:
            raise ValueError("min_overlap_count must be at least 3")
        if self.rolling_time_slice_count < 2:
            raise ValueError("rolling_time_slice_count must be at least 2")

    def config_digest(self) -> str:
        return _stable_digest(
            [
                self.version,
                self.correlation_threshold,
                self.near_duplicate_correlation_threshold,
                self.condition_number_threshold,
                self.min_samples,
                self.min_overlap_count,
                self.near_zero_variance_threshold,
                self.rolling_stability_instability_threshold,
                self.rolling_time_slice_count,
                self.spearman_enabled,
            ]
        )

    def to_dict(self) -> Dict[str, object]:
        return {
            "version": self.version,
            "correlation_threshold": self.correlation_threshold,
            "near_duplicate_correlation_threshold": self.near_duplicate_correlation_threshold,
            "condition_number_threshold": self.condition_number_threshold,
            "min_samples": self.min_samples,
            "min_overlap_count": self.min_overlap_count,
            "near_zero_variance_threshold": self.near_zero_variance_threshold,
            "rolling_stability_instability_threshold": self.rolling_stability_instability_threshold,
            "rolling_time_slice_count": self.rolling_time_slice_count,
            "spearman_enabled": self.spearman_enabled,
            "diagnostic_only": True,
            "promotion_wirksam": False,
            "trading_wirksam": False,
        }


def _ordinal_ranks(values: np.ndarray) -> np.ndarray:
    order = np.argsort(values, kind="mergesort")
    ranks = np.empty(values.shape[0], dtype=float)
    ranks[order] = np.arange(values.shape[0], dtype=float)
    return ranks


def _pairwise_pearson(a: np.ndarray, b: np.ndarray) -> float:
    if a.shape[0] < 2:
        return 0.0
    corr = np.corrcoef(a, b)[0, 1]
    if not isfinite(float(corr)):
        return 0.0
    return float(corr)


def _pairwise_spearman(a: np.ndarray, b: np.ndarray) -> float:
    if a.shape[0] < 2:
        return 0.0
    return _pairwise_pearson(_ordinal_ranks(a), _ordinal_ranks(b))


def _extract_signal_column(
    rows: Sequence[Mapping[str, object]], name: str
) -> Tuple[np.ndarray, np.ndarray]:
    """Return (values, valid_mask) aligned to row order."""
    values: List[float] = []
    valid: List[bool] = []
    for row in rows:
        raw = row.get(name)
        try:
            value = float(raw)
        except (TypeError, ValueError):
            values.append(float("nan"))
            valid.append(False)
            continue
        if not isfinite(value):
            values.append(float("nan"))
            valid.append(False)
        else:
            values.append(value)
            valid.append(True)
    return np.asarray(values, dtype=float), np.asarray(valid, dtype=bool)


def _pairwise_overlap_count(valid_a: np.ndarray, valid_b: np.ndarray) -> int:
    return int(np.sum(valid_a & valid_b))


def _classify_signal_variance(
    matrix: np.ndarray, names: Sequence[str], *, policy: SignalOrthogonalityScopePolicyV0
) -> tuple[tuple[str, ...], dict[str, int]]:
    dropped: dict[str, int] = {}
    keep: list[str] = []
    for index, name in enumerate(names):
        column = matrix[:, index]
        variance = float(np.var(column)) if column.size else 0.0
        if variance == 0.0:
            dropped[f"{REASON_ZERO_VARIANCE_FEATURE}:{name}"] = (
                dropped.get(f"{REASON_ZERO_VARIANCE_FEATURE}:{name}", 0) + 1
            )
        elif variance < policy.near_zero_variance_threshold:
            dropped[f"{REASON_NEAR_ZERO_VARIANCE_SIGNAL}:{name}"] = (
                dropped.get(f"{REASON_NEAR_ZERO_VARIANCE_SIGNAL}:{name}", 0) + 1
            )
        else:
            keep.append(str(name))
    return tuple(keep), dropped


def _build_pairwise_records(
    rows: Sequence[Mapping[str, object]],
    feature_names: Sequence[str],
    *,
    policy: SignalOrthogonalityScopePolicyV0,
    sample_count: int,
) -> List[Dict[str, object]]:
    columns = {name: _extract_signal_column(rows, name) for name in feature_names}
    records: List[Dict[str, object]] = []
    for i, left in enumerate(feature_names):
        for right in feature_names[i + 1 :]:
            left_values, left_valid = columns[left]
            right_values, right_valid = columns[right]
            overlap_mask = left_valid & right_valid
            overlap_count = int(np.sum(overlap_mask))
            reason_codes: list[str] = []
            status = "OK"
            pearson = 0.0
            spearman: float | None = None
            if overlap_count < policy.min_overlap_count:
                reason_codes.append(REASON_INSUFFICIENT_OVERLAP)
                status = "BLOCKED"
            else:
                a = left_values[overlap_mask]
                b = right_values[overlap_mask]
                pearson = _pairwise_pearson(a, b)
                if policy.spearman_enabled:
                    spearman = _pairwise_spearman(a, b)
                if abs(pearson) >= policy.correlation_threshold:
                    reason_codes.append(REASON_HIGH_PAIRWISE_CORRELATION)
                if abs(pearson) >= policy.near_duplicate_correlation_threshold:
                    reason_codes.append(REASON_NEAR_DUPLICATE_SIGNAL)
                if np.allclose(a, b, rtol=0.0, atol=0.0):
                    reason_codes.append(REASON_DUPLICATE_SIGNAL)
                elif overlap_count < policy.min_samples:
                    reason_codes.append(REASON_INSUFFICIENT_DATA)
                    status = "INDICATIVE"
            records.append(
                {
                    "signal_a": left,
                    "signal_b": right,
                    "sample_count": sample_count,
                    "overlap_count": overlap_count,
                    "pearson_correlation": pearson,
                    "absolute_pearson_correlation": abs(pearson),
                    "spearman_correlation": spearman,
                    "status": status,
                    "reason_codes": reason_codes,
                }
            )
    records.sort(key=lambda item: (str(item["signal_a"]), str(item["signal_b"])))
    return records


def _build_overlap_matrix(
    rows: Sequence[Mapping[str, object]], feature_names: Sequence[str]
) -> Dict[str, Dict[str, int]]:
    columns = {name: _extract_signal_column(rows, name)[1] for name in feature_names}
    return {
        left: {
            right: _pairwise_overlap_count(columns[left], columns[right]) for right in feature_names
        }
        for left in feature_names
    }


def _build_correlation_matrix(
    feature_names: Sequence[str], matrix: np.ndarray
) -> Dict[str, Dict[str, float]]:
    return _pairwise_correlations(feature_names, matrix)


def _duplicate_groups(feature_names: Sequence[str], matrix: np.ndarray) -> List[List[str]]:
    groups: List[List[str]] = []
    assigned: set[str] = set()
    index_by_name = {name: idx for idx, name in enumerate(feature_names)}
    for i, left in enumerate(feature_names):
        if left in assigned:
            continue
        group = [left]
        for right in feature_names[i + 1 :]:
            if right in assigned:
                continue
            if np.allclose(
                matrix[:, i],
                matrix[:, index_by_name[right]],
                rtol=0.0,
                atol=0.0,
            ):
                group.append(right)
        if len(group) > 1:
            groups.append(sorted(group))
            assigned.update(group)
    return groups


def _near_duplicate_groups(
    pairwise_records: Sequence[Mapping[str, object]],
    *,
    threshold: float,
) -> List[List[str]]:
    graph: Dict[str, set[str]] = {}
    for record in pairwise_records:
        if REASON_NEAR_DUPLICATE_SIGNAL not in record.get("reason_codes", ()):
            continue
        left = str(record["signal_a"])
        right = str(record["signal_b"])
        graph.setdefault(left, set()).add(right)
        graph.setdefault(right, set()).add(left)
    groups: List[List[str]] = []
    seen: set[str] = set()
    for node in sorted(graph):
        if node in seen:
            continue
        stack = [node]
        component: set[str] = set()
        while stack:
            current = stack.pop()
            if current in seen:
                continue
            seen.add(current)
            component.add(current)
            stack.extend(sorted(graph.get(current, ())))
        if len(component) > 1:
            groups.append(sorted(component))
    groups.sort()
    return groups


def _rolling_stability(
    rows: Sequence[Mapping[str, object]],
    feature_names: Sequence[str],
    *,
    policy: SignalOrthogonalityScopePolicyV0,
    time_name: str,
) -> Dict[str, object]:
    if len(rows) < policy.min_samples:
        return {
            "status": "BLOCKED",
            "reason_codes": [REASON_INSUFFICIENT_DATA],
            "time_slice_count": 0,
            "pair_stability": [],
            "stable_pairs": [],
            "unstable_pairs": [],
        }
    ordered = _time_order_rows(list(rows), time_name=time_name)
    slice_size = max(1, len(ordered) // policy.rolling_time_slice_count)
    slices: List[List[Mapping[str, object]]] = []
    for index in range(policy.rolling_time_slice_count):
        start = index * slice_size
        end = (
            len(ordered)
            if index == policy.rolling_time_slice_count - 1
            else (index + 1) * slice_size
        )
        chunk = ordered[start:end]
        if chunk:
            slices.append(chunk)
    pair_stability: List[Dict[str, object]] = []
    stable_pairs: List[Dict[str, str]] = []
    unstable_pairs: List[Dict[str, object]] = []
    for i, left in enumerate(feature_names):
        for right in feature_names[i + 1 :]:
            slice_corrs: List[float] = []
            for chunk in slices:
                left_values, left_valid = _extract_signal_column(chunk, left)
                right_values, right_valid = _extract_signal_column(chunk, right)
                mask = left_valid & right_valid
                if int(np.sum(mask)) >= 3:
                    slice_corrs.append(_pairwise_pearson(left_values[mask], right_values[mask]))
            if len(slice_corrs) < 2:
                continue
            spread = max(slice_corrs) - min(slice_corrs)
            unstable = spread >= policy.rolling_stability_instability_threshold
            entry = {
                "signal_a": left,
                "signal_b": right,
                "slice_correlations": slice_corrs,
                "abs_correlation_spread": spread,
                "stable": not unstable,
            }
            pair_stability.append(entry)
            if unstable:
                unstable_pairs.append(entry)
            else:
                stable_pairs.append({"signal_a": left, "signal_b": right})
    return {
        "status": "COMPUTED",
        "reason_codes": [],
        "time_slice_count": len(slices),
        "pair_stability": pair_stability,
        "stable_pairs": stable_pairs,
        "unstable_pairs": unstable_pairs,
    }


def build_signal_orthogonality_scope_artifacts_v0(
    rows: Sequence[Mapping[str, object]],
    feature_names: Sequence[str],
    *,
    policy: SignalOrthogonalityScopePolicyV0 | None = None,
    time_name: str = _DEFAULT_TIME_NAME,
    feature_time_name: str = _DEFAULT_FEATURE_TIME_NAME,
    instrument_key: str = "instrument_id",
    input_digest: str | None = None,
    fixture_truth_pack_used: bool = False,
    productive_binding_found: bool = False,
) -> Dict[str, object]:
    """Build deterministic scope-v0 diagnostic artifacts (diagnostic-only)."""
    cfg_policy = policy or SignalOrthogonalityScopePolicyV0()
    cfg_policy.validate()
    cfg = SignalOrthogonalityConfigV1(
        correlation_threshold=cfg_policy.correlation_threshold,
        condition_number_threshold=cfg_policy.condition_number_threshold,
        min_samples=cfg_policy.min_samples,
    )

    names_before = _sorted_unique_feature_names(feature_names)
    ordered_rows = _time_order_rows(list(rows), time_name=time_name)
    try:
        _assert_feature_time_before_target_time(
            ordered_rows,
            feature_time_name=feature_time_name,
            target_time_name=time_name,
        )
    except ValueError as exc:
        reason = str(exc)
        if reason == _REASON_LOOKAHEAD_BLOCKED:
            reason = REASON_FEATURE_LEAKAGE_RISK
        raise ValueError(reason) from exc

    instruments = sorted(
        {str(row[instrument_key]) for row in ordered_rows if row.get(instrument_key) is not None}
    )
    if ordered_rows and any(instrument_key in row for row in ordered_rows):
        per_instrument_counts = {
            instrument: sum(1 for row in ordered_rows if str(row.get(instrument_key)) == instrument)
            for instrument in instruments
        }
        if len(set(per_instrument_counts.values())) > 1 and len(instruments) > 1:
            instrument_alignment_note = "instrument_row_counts_vary_by_design"
        else:
            instrument_alignment_note = "aligned"
    else:
        instrument_alignment_note = "NOT_APPLICABLE_WITH_REASON:no_instrument_key_in_rows"

    matrix, dropped_rows = _as_float_matrix(ordered_rows, names_before)
    sample_count = int(matrix.shape[0])
    kept_names, dropped_signals = _classify_signal_variance(matrix, names_before, policy=cfg_policy)
    keep_indices = [names_before.index(name) for name in kept_names]
    filtered_matrix = matrix[:, keep_indices] if keep_indices else np.empty((sample_count, 0))

    active_names = kept_names if kept_names else names_before
    evidence = analyze_signal_orthogonality(
        ordered_rows,
        active_names,
        config=cfg,
        time_name=time_name,
        feature_time_name=feature_time_name,
        productive_binding_gap=not productive_binding_found and not fixture_truth_pack_used,
    )

    pairwise_records = _build_pairwise_records(
        ordered_rows,
        active_names,
        policy=cfg_policy,
        sample_count=sample_count,
    )
    overlap_matrix = _build_overlap_matrix(ordered_rows, active_names)
    correlation_matrix = (
        _build_correlation_matrix(kept_names, filtered_matrix) if filtered_matrix.size else {}
    )
    duplicate_groups = (
        _duplicate_groups(kept_names, filtered_matrix) if filtered_matrix.size else []
    )
    near_duplicate_groups = _near_duplicate_groups(
        pairwise_records,
        threshold=cfg_policy.near_duplicate_correlation_threshold,
    )
    high_correlation_pairs = [
        {
            "signal_a": record["signal_a"],
            "signal_b": record["signal_b"],
            "pearson_correlation": record["pearson_correlation"],
            "absolute_pearson_correlation": record["absolute_pearson_correlation"],
        }
        for record in pairwise_records
        if REASON_HIGH_PAIRWISE_CORRELATION in record["reason_codes"]
    ]
    rolling = _rolling_stability(
        ordered_rows,
        active_names,
        policy=cfg_policy,
        time_name=time_name,
    )

    matrix_rank = (
        int(evidence.diagnostics.get("rank", 0)) if evidence.diagnostics.get("computed") else 0
    )
    condition_number = evidence.diagnostics.get("condition_number")
    config_digest = cfg_policy.config_digest()
    bound_input_digest = input_digest or evidence.feature_matrix_digest
    output_digest = _stable_digest(
        {
            "pairwise_records": pairwise_records,
            "correlation_matrix": correlation_matrix,
            "overlap_matrix": overlap_matrix,
            "duplicate_groups": duplicate_groups,
            "near_duplicate_groups": near_duplicate_groups,
            "matrix_rank": matrix_rank,
            "condition_number": condition_number,
            "config_digest": config_digest,
            "input_digest": bound_input_digest,
        }
    )

    signal_summary = {
        "signal_count_before_filter": len(names_before),
        "signal_count_after_filter": len(kept_names),
        "dropped_signals_by_reason": dropped_signals,
        "matrix_rank": matrix_rank,
        "condition_number": condition_number,
        "duplicate_groups": duplicate_groups,
        "near_duplicate_groups": near_duplicate_groups,
        "high_correlation_pairs": high_correlation_pairs,
        "stable_pairs": rolling.get("stable_pairs", []),
        "unstable_pairs": rolling.get("unstable_pairs", []),
        "time_slice_count": rolling.get("time_slice_count", 0),
        "instrument_count": len(instruments),
        "instrument_alignment_note": instrument_alignment_note,
        "input_digest": bound_input_digest,
        "config_digest": config_digest,
        "output_digest": output_digest,
        "pair_count": len(pairwise_records),
        "authority_effect": _AUTHORITY_EFFECT,
        "runtime_effect": _RUNTIME_EFFECT,
        "diagnostic_role": SCOPE_ROLE,
    }

    diagnostic_status = str(evidence.status)
    if not kept_names:
        diagnostic_status = "RANK_DEFICIENT_BLOCKED"

    return {
        "diagnostic_policy": cfg_policy.to_dict(),
        "failure_taxonomy": FAILURE_TAXONOMY_V0,
        "signal_summary": signal_summary,
        "pairwise_correlations": pairwise_records,
        "correlation_matrix": correlation_matrix,
        "overlap_matrix": overlap_matrix,
        "duplicate_groups": {"groups": duplicate_groups},
        "matrix_diagnostics": {
            "rank": matrix_rank,
            "condition_number": condition_number,
            "vif_scores": evidence.diagnostics.get("vif_scores", {}),
            "computed": evidence.diagnostics.get("computed", False),
            "reason_codes": list(evidence.reason_codes),
            "dropped_rows_by_reason": dict(dropped_rows),
        },
        "rolling_stability": rolling,
        "evidence": evidence_to_dict(evidence),
        "diagnostic_status": diagnostic_status,
        "output_digest": output_digest,
        "config_digest": config_digest,
        "input_digest": bound_input_digest,
    }
