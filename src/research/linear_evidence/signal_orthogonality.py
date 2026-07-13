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
