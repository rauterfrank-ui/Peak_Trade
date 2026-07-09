from __future__ import annotations

from dataclasses import dataclass
from math import isfinite
from typing import Dict, Iterable, List, Mapping, Sequence, Tuple

import numpy as np


_ALLOWED_STATUS = "DIAGNOSTIC_ONLY"
_AUTHORITY_EFFECT = "NONE"
_RUNTIME_EFFECT = "NONE"


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


def _as_float_matrix(
    rows: Sequence[Mapping[str, object]], feature_names: Sequence[str]
) -> Tuple[np.ndarray, List[int]]:
    matrix: List[List[float]] = []
    dropped: List[int] = []
    for idx, row in enumerate(rows):
        values: List[float] = []
        ok = True
        for name in feature_names:
            try:
                value = float(row[name])
            except (KeyError, TypeError, ValueError):
                ok = False
                break
            if not isfinite(value):
                ok = False
                break
            values.append(value)
        if ok:
            matrix.append(values)
        else:
            dropped.append(idx)
    if not matrix:
        return np.empty((0, len(feature_names)), dtype=float), dropped
    return np.asarray(matrix, dtype=float), dropped


def _stable_digest(parts: Iterable[object]) -> str:
    import hashlib
    import json

    payload = json.dumps(list(parts), sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


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
) -> SignalOrthogonalityEvidenceV1:
    cfg = config or SignalOrthogonalityConfigV1()
    cfg.validate()

    names = tuple(feature_names)
    if not names:
        raise ValueError("feature_names must not be empty")
    if len(set(names)) != len(names):
        raise ValueError("feature_names must be unique")

    matrix, dropped = _as_float_matrix(rows, names)
    row_count_before = len(rows)
    row_count_after = int(matrix.shape[0])

    reason_codes: List[str] = []
    if row_count_after < cfg.min_samples:
        reason_codes.append("INSUFFICIENT_SAMPLE_COUNT")

    rank = _rank(matrix)
    if rank < len(names):
        reason_codes.append("RANK_DEFICIENT_FEATURE_MATRIX")

    condition_number = _condition_number(matrix)
    if not isfinite(condition_number) or condition_number > cfg.condition_number_threshold:
        reason_codes.append("HIGH_CONDITION_NUMBER")

    corr = _pairwise_correlations(names, matrix)
    redundant = _redundant_pairs(names, corr, cfg.correlation_threshold)
    if redundant:
        reason_codes.append("SIGNAL_REDUNDANCY_REPORTED")

    vif = _vif_scores(names, matrix)

    diagnostics: Dict[str, object] = {
        "correlation_threshold": cfg.correlation_threshold,
        "condition_number_threshold": cfg.condition_number_threshold,
        "rank": rank,
        "condition_number": condition_number,
        "pairwise_correlation": corr,
        "redundant_pairs": redundant,
        "vif_scores": vif,
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
        coefficients={name: 0.0 for name in names},
        diagnostics=diagnostics,
        feature_matrix_digest=_stable_digest(
            [{name: row.get(name) for name in names} for row in rows]
        ),
        target_digest=_stable_digest([target_name, "diagnostic_only"]),
        config_digest=_stable_digest(
            [cfg.correlation_threshold, cfg.condition_number_threshold, cfg.min_samples]
        ),
        time_range={"policy": "offline_fixture_or_input_rows", "target_shift": "not_applicable"},
        instrument_universe_digest=_stable_digest(["offline_signal_orthogonality", names]),
        row_count_before_filter=row_count_before,
        row_count_after_filter=row_count_after,
        dropped_rows_by_reason={"non_finite_or_missing_feature": len(dropped)},
        validation_policy={
            "offline_only": True,
            "validation_split": "not_applicable_for_unsupervised_orthogonality_diagnostic",
            "random_split_allowed": False,
            "lookahead_allowed": False,
            "strategy_selection_effect": False,
        },
        cost_policy_output="diagnostic_only",
        status=_ALLOWED_STATUS,
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
                "trend_following": trend,
                "momentum_1h": momentum,
                "bollinger_bands": volatility,
                "liquidity_context": liquidity,
            }
        )
    return rows, ("trend_following", "momentum_1h", "bollinger_bands", "liquidity_context")


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
