"""Offline outlier and window robustness diagnostics v0.

Additive diagnostic surface for causal attribution of rolling-window drift FAILs.
Reuses canonical linear-evidence owners; no economic evaluation or runtime authority.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Mapping, Sequence, Tuple
import hashlib
import json
import math

import numpy as np

from .drift import (
    DRIFT_DIAGNOSTIC_DEFAULTS_V0,
    MODEL_SPEC_VERSION,
    RollingLinearDriftInputV1,
    _compose_exclusion_reason_codes_v0,
    _records_to_rows,
    _sort_records,
    _stable_digest,
)
from .feature_matrix import build_feature_matrix_binding
from .fitters import (
    REASON_RANK_DEFICIENT_FEATURE_MATRIX,
    exclude_strict_zero_variance_features_v0,
    fit_ols_lstsq,
)

SCHEMA_VERSION = "outlier_and_window_robustness_diagnostic.v0"
GO_TOKEN_REQUIRED = "GO_OUTLIER_AND_WINDOW_ROBUSTNESS_DIAGNOSTIC_V0"
SOLVER = "numpy.linalg.lstsq"

# Diagnostic-only near-zero variance rule (does not alter productive feature selection).
NEAR_ZERO_VARIANCE_STD_THRESHOLD_V0 = 1e-9
NEAR_ZERO_VARIANCE_UNIQUE_COUNT_MAX_V0 = 1


def _safe_sqrt(value: float) -> float:
    return math.sqrt(max(0.0, float(value)))


PRIMARY_STATUSES = frozenset(
    {
        "STABLE",
        "ZERO_VARIANCE",
        "NEAR_ZERO_VARIANCE",
        "RANK_DEFICIENT",
        "ILL_CONDITIONED",
        "OUTLIER_SENSITIVE",
        "INSUFFICIENT_SAMPLE",
        "MIXED_FAILURE",
        "UNKNOWN",
    }
)

VERDICT_CLASSES = frozenset(
    {
        "PASS_WINDOW_AND_OUTLIER_ROBUSTNESS_DIAGNOSTIC_COMPLETED",
        "FAIL_CONFIRMED_WINDOW_SAMPLE_INSTABILITY",
        "FAIL_CONFIRMED_OUTLIER_DOMINATED_WINDOWS",
        "FAIL_CONFIRMED_ILL_CONDITIONING",
        "FAIL_CONFIRMED_MIXED_WINDOW_OUTLIER_CONDITIONING",
        "INCONCLUSIVE_DIAGNOSTIC_LIMITATION",
        "BLOCKED_INPUT_OR_CONTRACT_FAILURE",
    }
)


@dataclass(frozen=True)
class WindowRobustnessConfigV0:
    base_window_size: int = 120
    window_step: int = 60
    min_samples: int = 20
    validation_fraction: float = 0.25
    fit_intercept: bool = True
    target_name: str = "target"
    focus_window_ids: Tuple[int, ...] = (0, 1, 13, 14, 15)
    adjacent_window_sizes: Tuple[int, ...] = (119, 120, 121)
    larger_comparison_window_sizes: Tuple[int, ...] = (180, 240)
    max_condition_number: float = DRIFT_DIAGNOSTIC_DEFAULTS_V0["max_condition_number"]
    outlier_leverage_threshold: float = 3.0 / 120.0  # diagnostic reference only
    cooks_distance_threshold: float = 4.0 / 120.0
    influence_top_k: int = 3


def _json_safe(value: object) -> object:
    if isinstance(value, float):
        if math.isinf(value):
            return "Infinity"
        if math.isnan(value):
            return "NaN"
    if isinstance(value, dict):
        return {str(k): _json_safe(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(v) for v in value]
    return value


def _feature_variance_row(
    column: np.ndarray,
    *,
    feature_name: str,
    active: bool,
    exclusion_reason: str | None,
) -> Dict[str, object]:
    finite_mask = np.isfinite(column)
    finite_values = column[finite_mask]
    count = int(column.size)
    finite_count = int(finite_values.size)
    missing_count = count - finite_count
    if finite_count == 0:
        return {
            "feature_name": feature_name,
            "count": count,
            "finite_count": finite_count,
            "missing_count": missing_count,
            "mean": None,
            "standard_deviation": None,
            "variance": None,
            "minimum": None,
            "maximum": None,
            "unique_count": 0,
            "zero_variance": False,
            "near_zero_variance": False,
            "active": active,
            "exclusion_reason": exclusion_reason or "NON_FINITE_VALUES",
        }
    variance = float(np.var(finite_values))
    std = float(np.std(finite_values))
    unique_count = int(len(np.unique(np.round(finite_values, 12))))
    zero_variance = variance == 0.0
    near_zero_variance = (
        not zero_variance
        and std <= NEAR_ZERO_VARIANCE_STD_THRESHOLD_V0
        and unique_count <= NEAR_ZERO_VARIANCE_UNIQUE_COUNT_MAX_V0
    )
    return {
        "feature_name": feature_name,
        "count": count,
        "finite_count": finite_count,
        "missing_count": missing_count,
        "mean": float(np.mean(finite_values)),
        "standard_deviation": std,
        "variance": variance,
        "minimum": float(np.min(finite_values)),
        "maximum": float(np.max(finite_values)),
        "unique_count": unique_count,
        "zero_variance": zero_variance,
        "near_zero_variance": near_zero_variance,
        "active": active,
        "exclusion_reason": exclusion_reason,
    }


def _window_rows_and_binding(
    records: Sequence[RollingLinearDriftInputV1],
    feature_names: Sequence[str],
    *,
    target_name: str,
) -> tuple[list[Dict[str, object]], np.ndarray, np.ndarray, object]:
    rows = _records_to_rows(records, feature_names)
    x, y, binding = build_feature_matrix_binding(
        rows,
        feature_names=feature_names,
        target_name=target_name,
        time_name="decision_time",
        validation_policy="TIME_ORDERED",
    )
    return rows, x, y, binding


def _design_matrix(
    x: np.ndarray,
    *,
    fit_intercept: bool,
) -> np.ndarray:
    if fit_intercept:
        return np.column_stack([np.ones(x.shape[0]), x])
    return x


def _conditioning_diagnostics(
    design: np.ndarray,
    *,
    fit_intercept: bool,
    n_features: int,
) -> Dict[str, object]:
    if design.size == 0 or design.shape[0] < 2:
        return {
            "design_matrix_shape": list(design.shape),
            "matrix_rank": 0,
            "expected_rank": int(design.shape[1]) if design.ndim == 2 else 0,
            "rank_deficient": True,
            "condition_number": 0.0,
            "singular_values": [],
            "minimum_singular_value": 0.0,
            "maximum_singular_value": 0.0,
            "singular_value_ratio": None,
            "correlated_or_collinear_feature_pairs": [],
            "intercept_contribution": fit_intercept,
            "sample_to_parameter_ratio": 0.0,
            "conditioning_status": "INSUFFICIENT_SAMPLE",
            "conditioning_reason_codes": ["INSUFFICIENT_SAMPLE_COUNT"],
        }

    singular_values = np.linalg.svd(design, compute_uv=False)
    rank = int(np.sum(singular_values > 1e-12))
    expected_rank = int(design.shape[1])
    min_sv = float(np.min(singular_values)) if singular_values.size else 0.0
    max_sv = float(np.max(singular_values)) if singular_values.size else 0.0
    cond = float(np.linalg.cond(design)) if rank == expected_rank else float("inf")
    ratio = max_sv / min_sv if min_sv > 0 else float("inf")

    collinear_pairs: list[Dict[str, object]] = []
    if design.shape[0] > 1 and design.shape[1] > 1:
        with np.errstate(invalid="ignore", divide="ignore"):
            corr = np.corrcoef(design.T)
        names = (("intercept",) if fit_intercept else ()) + tuple(
            f"feature_{index}" for index in range(n_features)
        )
        for i in range(corr.shape[0]):
            for j in range(i + 1, corr.shape[0]):
                if np.isfinite(corr[i, j]) and abs(float(corr[i, j])) >= 0.99:
                    collinear_pairs.append(
                        {
                            "feature_a": names[i] if i < len(names) else str(i),
                            "feature_b": names[j] if j < len(names) else str(j),
                            "correlation": float(corr[i, j]),
                        }
                    )

    reason_codes: list[str] = []
    if rank < expected_rank:
        reason_codes.append("RANK_DEFICIENT")
    if math.isinf(cond) or cond > DRIFT_DIAGNOSTIC_DEFAULTS_V0["max_condition_number"]:
        reason_codes.append("HIGH_CONDITION_NUMBER")
    status = "ACCEPTABLE"
    if "RANK_DEFICIENT" in reason_codes and "HIGH_CONDITION_NUMBER" in reason_codes:
        status = "MIXED_FAILURE"
    elif "RANK_DEFICIENT" in reason_codes:
        status = "RANK_DEFICIENT"
    elif "HIGH_CONDITION_NUMBER" in reason_codes:
        status = "ILL_CONDITIONED"

    return {
        "design_matrix_shape": [int(design.shape[0]), int(design.shape[1])],
        "matrix_rank": rank,
        "expected_rank": expected_rank,
        "rank_deficient": rank < expected_rank,
        "condition_number": cond,
        "singular_values": [float(v) for v in singular_values.tolist()],
        "minimum_singular_value": min_sv,
        "maximum_singular_value": max_sv,
        "singular_value_ratio": ratio,
        "correlated_or_collinear_feature_pairs": collinear_pairs,
        "intercept_contribution": fit_intercept,
        "sample_to_parameter_ratio": float(design.shape[0]) / max(float(design.shape[1]), 1.0),
        "conditioning_status": status,
        "conditioning_reason_codes": reason_codes or ["STABLE"],
    }


def _compute_influence_diagnostics(
    x: np.ndarray,
    y: np.ndarray,
    binding: object,
    *,
    fit_intercept: bool,
    active_feature_names: Sequence[str],
    validation_fraction: float,
) -> Dict[str, object]:
    unavailable_reason: str | None = None
    n = int(x.shape[0])
    p = int(x.shape[1]) + (1 if fit_intercept else 0)
    if n < max(4, p + 2):
        return {
            "status": "UNAVAILABLE",
            "reason_code": "INSUFFICIENT_SAMPLE_COUNT",
            "residuals": [],
            "standardized_or_studentized_residuals": [],
            "leverage": [],
            "cooks_distance": [],
            "dffits": [],
            "dfbetas": {},
            "outlier_count": 0,
            "high_leverage_count": 0,
            "influential_observation_count": 0,
            "outlier_rate": 0.0,
            "high_leverage_rate": 0.0,
            "influential_observation_rate": 0.0,
            "max_abs_studentized_residual": None,
            "max_leverage": None,
            "max_cooks_distance": None,
        }

    active_binding = type(binding)(
        target_name=binding.target_name,
        feature_names=tuple(active_feature_names),
        n_samples=binding.n_samples,
        n_features=len(active_feature_names),
        feature_matrix_digest=binding.feature_matrix_digest,
        target_digest=binding.target_digest,
        validation_policy=binding.validation_policy,
        time_range=binding.time_range,
        row_count_before_filter=binding.row_count_before_filter,
        row_count_after_filter=binding.row_count_after_filter,
        dropped_rows_by_reason=binding.dropped_rows_by_reason,
        status=binding.status,
        reason_codes=binding.reason_codes,
    )

    try:
        evidence = fit_ols_lstsq(
            x,
            y,
            active_binding,
            fit_intercept=fit_intercept,
            validation_fraction=validation_fraction,
            evidence_type="window_robustness_influence",
            instrument_universe_digest="diagnostic_window",
        )
    except ValueError as exc:
        return {
            "status": "UNAVAILABLE",
            "reason_code": str(exc),
            "residuals": [],
            "standardized_or_studentized_residuals": [],
            "leverage": [],
            "cooks_distance": [],
            "dffits": [],
            "dfbetas": {},
            "outlier_count": 0,
            "high_leverage_count": 0,
            "influential_observation_count": 0,
            "outlier_rate": 0.0,
            "high_leverage_rate": 0.0,
            "influential_observation_rate": 0.0,
            "max_abs_studentized_residual": None,
            "max_leverage": None,
            "max_cooks_distance": None,
        }

    design = _design_matrix(x, fit_intercept=fit_intercept)
    rank = int(evidence.diagnostics.rank)
    if rank < p:
        unavailable_reason = "RANK_DEFICIENT_FOR_INFLUENCE"

    try:
        pinv = np.linalg.pinv(design)
        hat = design @ pinv
        leverage = np.clip(np.diag(hat), 0.0, 1.0)
        coeffs, _, _, _ = np.linalg.lstsq(design, y, rcond=None)
        y_hat = design @ coeffs
        residuals = y - y_hat
        mse = float(np.sum(residuals**2) / max(n - rank, 1))
        residual_std = float(np.sqrt(mse)) if mse > 0 else 0.0

        studentized: list[float | None] = []
        for index in range(n):
            denom = residual_std * math.sqrt(max(1.0 - leverage[index], 1e-12))
            if denom <= 0 or unavailable_reason:
                studentized.append(None)
            else:
                studentized.append(float(residuals[index] / denom))

        cooks = []
        dffits = []
        for index in range(n):
            if unavailable_reason or residual_std <= 0:
                cooks.append(None)
                dffits.append(None)
                continue
            cooks.append(
                float(
                    (residuals[index] ** 2 / max(p * mse, 1e-12))
                    * (leverage[index] / max(1.0 - leverage[index], 1e-12))
                )
            )
            dffits.append(
                float(
                    studentized[index]
                    * _safe_sqrt(leverage[index] / max(1.0 - leverage[index], 1e-12))
                )
                if studentized[index] is not None
                else None
            )

        dfbetas: Dict[str, object] = {}
        if unavailable_reason:
            for name in active_feature_names:
                dfbetas[name] = {"status": "UNAVAILABLE", "reason_code": unavailable_reason}
        else:
            for feat_index, name in enumerate(active_feature_names):
                col_index = feat_index + (1 if fit_intercept else 0)
                values = []
                for obs_index in range(n):
                    if residual_std <= 0:
                        values.append(None)
                        continue
                    x_j = design[obs_index, col_index]
                    xtx_inv_jj = float(pinv[col_index, col_index])
                    values.append(
                        float(
                            (residuals[obs_index] / max(residual_std, 1e-12))
                            * _safe_sqrt(xtx_inv_jj)
                            / max(1.0 - leverage[obs_index], 1e-12)
                        )
                        * x_j
                    )
                dfbetas[name] = values

        leverage_threshold = min(1.0, 2.0 * p / max(n, 1))
        finite_studentized = [abs(v) for v in studentized if v is not None]
        finite_cooks = [v for v in cooks if v is not None]
        outlier_count = sum(1 for v in finite_studentized if v > 3.0)
        high_leverage_count = int(np.sum(leverage > leverage_threshold))
        influential_count = sum(
            1
            for index in range(n)
            if (studentized[index] is not None and abs(studentized[index]) > 3.0)
            and leverage[index] > leverage_threshold
        )

        return {
            "status": "AVAILABLE" if not unavailable_reason else "PARTIAL",
            "reason_code": unavailable_reason,
            "residuals": [float(v) for v in residuals.tolist()],
            "standardized_or_studentized_residuals": studentized,
            "leverage": [float(v) for v in leverage.tolist()],
            "cooks_distance": cooks,
            "dffits": dffits,
            "dfbetas": dfbetas,
            "outlier_count": outlier_count,
            "high_leverage_count": high_leverage_count,
            "influential_observation_count": influential_count,
            "outlier_rate": outlier_count / max(n, 1),
            "high_leverage_rate": high_leverage_count / max(n, 1),
            "influential_observation_rate": influential_count / max(n, 1),
            "max_abs_studentized_residual": max(finite_studentized, default=None),
            "max_leverage": float(np.max(leverage)),
            "max_cooks_distance": max(finite_cooks, default=None),
            "baseline_fit_status": evidence.status,
            "baseline_observations_removed": 0,
        }
    except (np.linalg.LinAlgError, FloatingPointError) as exc:
        return {
            "status": "UNAVAILABLE",
            "reason_code": f"NUMERIC_FAILURE:{exc}",
            "residuals": [],
            "standardized_or_studentized_residuals": [],
            "leverage": [],
            "cooks_distance": [],
            "dffits": [],
            "dfbetas": {},
            "outlier_count": 0,
            "high_leverage_count": 0,
            "influential_observation_count": 0,
            "outlier_rate": 0.0,
            "high_leverage_rate": 0.0,
            "influential_observation_rate": 0.0,
            "max_abs_studentized_residual": None,
            "max_leverage": None,
            "max_cooks_distance": None,
        }


def build_window_plan_v0(
    records: Sequence[RollingLinearDriftInputV1],
    *,
    config: WindowRobustnessConfigV0 | None = None,
) -> Dict[str, object]:
    cfg = config or WindowRobustnessConfigV0()
    sorted_records = _sort_records(records)
    if not sorted_records:
        raise ValueError("INSUFFICIENT_DATA")

    feature_names = tuple(sorted(sorted_records[0].features.keys()))
    if not feature_names:
        raise ValueError("TARGET_BINDING_MISSING")

    for record in sorted_records:
        if tuple(sorted(record.features.keys())) != feature_names:
            raise ValueError("FEATURE_SCHEMA_DRIFT")
        row = [float(record.features[name]) for name in feature_names]
        if any(not math.isfinite(value) for value in row) or not math.isfinite(
            float(record.target)
        ):
            raise ValueError("NON_FINITE_VALUES_BLOCKED")

    n_samples = len(sorted_records)
    if n_samples < cfg.base_window_size:
        raise ValueError("INSUFFICIENT_SAMPLE_COUNT")
    all_rows = _records_to_rows(sorted_records, feature_names)
    input_digest = _stable_digest(all_rows)
    target_digest = _stable_digest([row["target"] for row in all_rows])
    instrument_ids = sorted({record.instrument_id for record in sorted_records})
    decision_times = sorted({record.decision_time for record in sorted_records})

    plan_entries: list[Dict[str, object]] = []
    seen_keys: set[tuple[int, int, int]] = set()

    def _append_plan_entry(
        *,
        window_id: str,
        start: int,
        window_size: int,
        plan_class: str,
    ) -> None:
        key = (start, window_size, hash(window_id) % 10_000)
        if key in seen_keys and plan_class == "SLIDING":
            return
        seen_keys.add(key)
        end = start + window_size
        if end > n_samples:
            return
        window_records = sorted_records[start:end]
        window_rows = _records_to_rows(window_records, feature_names)
        _, x, y, binding = _window_rows_and_binding(
            window_records,
            feature_names,
            target_name=cfg.target_name,
        )
        x_active, active_names, excluded_names = exclude_strict_zero_variance_features_v0(
            x, feature_names
        )
        exclusion_reasons = list(_compose_exclusion_reason_codes_v0(excluded_names))
        feature_matrix_digest = binding.feature_matrix_digest
        window_target_digest = _stable_digest([row["target"] for row in window_rows])
        window_input_digest = _stable_digest(window_rows)

        plan_entries.append(
            {
                "window_id": window_id,
                "plan_class": plan_class,
                "start_index": start,
                "window_size": window_size,
                "start_time": window_records[0].decision_time,
                "end_time": window_records[-1].decision_time,
                "n_rows": len(window_records),
                "n_decision_times": len({record.decision_time for record in window_records}),
                "n_instruments": len({record.instrument_id for record in window_records}),
                "feature_names_requested": list(feature_names),
                "feature_names_active": list(active_names),
                "feature_names_excluded": list(excluded_names),
                "exclusion_reasons": exclusion_reasons,
                "target_name": cfg.target_name,
                "fit_intercept": cfg.fit_intercept,
                "solver": SOLVER,
                "input_digest": window_input_digest,
                "feature_matrix_digest": feature_matrix_digest,
                "target_digest": window_target_digest,
            }
        )

    sliding_index = 0
    for start in range(0, n_samples - cfg.base_window_size + 1, max(1, cfg.window_step)):
        plan_class = "SLIDING"
        window_id = f"W{sliding_index}"
        _append_plan_entry(
            window_id=window_id,
            start=start,
            window_size=cfg.base_window_size,
            plan_class=plan_class,
        )
        if sliding_index in cfg.focus_window_ids:
            for alt_size in cfg.adjacent_window_sizes:
                if alt_size != cfg.base_window_size:
                    _append_plan_entry(
                        window_id=f"{window_id}_SIZE_{alt_size}",
                        start=start,
                        window_size=alt_size,
                        plan_class="ADJACENT_SIZE",
                    )
        sliding_index += 1

    for large_size in cfg.larger_comparison_window_sizes:
        if large_size <= n_samples:
            _append_plan_entry(
                window_id=f"LARGE_{large_size}",
                start=n_samples - large_size,
                window_size=large_size,
                plan_class="LARGER_COMPARISON",
            )

    return {
        "schema_version": SCHEMA_VERSION,
        "model_spec": MODEL_SPEC_VERSION,
        "base_window_size": cfg.base_window_size,
        "window_step": cfg.window_step,
        "min_samples": cfg.min_samples,
        "focus_window_ids": list(cfg.focus_window_ids),
        "adjacent_window_sizes": list(cfg.adjacent_window_sizes),
        "larger_comparison_window_sizes": list(cfg.larger_comparison_window_sizes),
        "n_samples_total": n_samples,
        "n_instruments_total": len(instrument_ids),
        "n_decision_times_total": len(decision_times),
        "input_digest": input_digest,
        "target_digest": target_digest,
        "feature_names_requested": list(feature_names),
        "windows": plan_entries,
    }


def compute_feature_variance_diagnostics_v0(
    window_plan: Mapping[str, object],
    records: Sequence[RollingLinearDriftInputV1],
) -> Dict[str, object]:
    sorted_records = _sort_records(records)
    feature_names = tuple(window_plan["feature_names_requested"])  # type: ignore[index]
    per_window: list[Dict[str, object]] = []

    for window in window_plan["windows"]:  # type: ignore[index]
        start = int(window["start_index"])
        size = int(window["window_size"])
        window_records = sorted_records[start : start + size]
        _, x, _, _ = _window_rows_and_binding(
            window_records,
            feature_names,
            target_name=str(window["target_name"]),
        )
        active_names = set(window["feature_names_active"])
        excluded = {
            str(name): str(window["exclusion_reasons"]) for name in window["feature_names_excluded"]
        }
        rows = []
        for index, name in enumerate(feature_names):
            reason = excluded.get(name)
            if name not in active_names and not reason:
                reason = "ZERO_VARIANCE_WITHIN_WINDOW"
            rows.append(
                _feature_variance_row(
                    x[:, index],
                    feature_name=name,
                    active=name in active_names,
                    exclusion_reason=reason,
                )
            )
        per_window.append({"window_id": window["window_id"], "features": rows})

    return {"windows": per_window}


def compute_active_feature_subset_stability_v0(
    window_plan: Mapping[str, object],
) -> Dict[str, object]:
    sliding = [
        window
        for window in window_plan["windows"]  # type: ignore[index]
        if window.get("plan_class") == "SLIDING"
    ]
    pairwise: list[Dict[str, object]] = []
    unstable_features: set[str] = set()
    windows_with_change: list[str] = []

    for index in range(len(sliding) - 1):
        left = sliding[index]
        right = sliding[index + 1]
        active_left = set(left["feature_names_active"])
        active_right = set(right["feature_names_active"])
        added = sorted(active_right - active_left)
        removed = sorted(active_left - active_right)
        intersection = active_left & active_right
        union = active_left | active_right
        jaccard = len(intersection) / max(len(union), 1)
        changed = bool(added or removed)
        if changed:
            windows_with_change.append(str(right["window_id"]))
            unstable_features.update(added)
            unstable_features.update(removed)
        pairwise.append(
            {
                "left_window_id": left["window_id"],
                "right_window_id": right["window_id"],
                "active_feature_set": sorted(active_right),
                "excluded_feature_set": sorted(right["feature_names_excluded"]),
                "added_features": added,
                "removed_features": removed,
                "intersection_size": len(intersection),
                "union_size": len(union),
                "jaccard_similarity": jaccard,
                "feature_subset_changed": changed,
                "change_reasons": (
                    ["ACTIVE_FEATURE_SUBSET_CHANGED"] if changed else ["STABLE_ACTIVE_SUBSET"]
                ),
            }
        )

    stable_subset = sliding[0]["feature_names_active"] if sliding else []
    if sliding:
        for window in sliding[1:]:
            if set(window["feature_names_active"]) != set(stable_subset):
                stable_subset = []
                break

    driver = "NONE"
    if windows_with_change:
        driver = "ZERO_VARIANCE_EXCLUSION" if unstable_features else "UNKNOWN"

    return {
        "pairwise_transitions": pairwise,
        "stable_active_feature_subset": list(stable_subset) if stable_subset else [],
        "unstable_features": sorted(unstable_features),
        "windows_with_subset_change": windows_with_change,
        "primary_subset_instability_driver": driver,
    }


def compute_rank_and_conditioning_diagnostics_v0(
    window_plan: Mapping[str, object],
    records: Sequence[RollingLinearDriftInputV1],
    *,
    config: WindowRobustnessConfigV0 | None = None,
) -> Dict[str, object]:
    cfg = config or WindowRobustnessConfigV0()
    sorted_records = _sort_records(records)
    feature_names = tuple(window_plan["feature_names_requested"])  # type: ignore[index]
    per_window: list[Dict[str, object]] = []

    for window in window_plan["windows"]:  # type: ignore[index]
        start = int(window["start_index"])
        size = int(window["window_size"])
        window_records = sorted_records[start : start + size]
        _, x, _, _ = _window_rows_and_binding(
            window_records,
            feature_names,
            target_name=str(window["target_name"]),
        )
        active_names = tuple(window["feature_names_active"])
        if not active_names:
            per_window.append(
                {
                    "window_id": window["window_id"],
                    **_conditioning_diagnostics(
                        np.empty((x.shape[0], 0)),
                        fit_intercept=cfg.fit_intercept,
                        n_features=0,
                    ),
                }
            )
            continue
        active_indices = [feature_names.index(name) for name in active_names]
        x_active = x[:, active_indices]
        design = _design_matrix(x_active, fit_intercept=cfg.fit_intercept)
        per_window.append(
            {
                "window_id": window["window_id"],
                **_conditioning_diagnostics(
                    design,
                    fit_intercept=cfg.fit_intercept,
                    n_features=len(active_names),
                ),
            }
        )

    return {"windows": per_window, "max_condition_number_policy": cfg.max_condition_number}


def _counterfactual_fit(
    window_records: Sequence[RollingLinearDriftInputV1],
    feature_names: Sequence[str],
    *,
    target_name: str,
    fit_intercept: bool,
    validation_fraction: float,
    drop_observation_index: int | None = None,
    use_standardized_design: bool = False,
) -> Dict[str, object]:
    fit_records = window_records
    if drop_observation_index is not None:
        fit_records = tuple(
            record for index, record in enumerate(window_records) if index != drop_observation_index
        )
    _, x, y, binding = _window_rows_and_binding(
        fit_records,
        feature_names,
        target_name=target_name,
    )
    x_active, active_names, excluded = exclude_strict_zero_variance_features_v0(x, feature_names)
    if not active_names:
        return {"status": "BLOCKED", "reason_code": REASON_RANK_DEFICIENT_FEATURE_MATRIX}

    x_fit = x_active
    if use_standardized_design:
        std = np.std(x_fit, axis=0)
        std[std == 0] = 1.0
        x_fit = (x_fit - np.mean(x_fit, axis=0)) / std

    active_binding = type(binding)(
        target_name=binding.target_name,
        feature_names=active_names,
        n_samples=int(x_fit.shape[0]),
        n_features=len(active_names),
        feature_matrix_digest=binding.feature_matrix_digest,
        target_digest=binding.target_digest,
        validation_policy=binding.validation_policy,
        time_range=binding.time_range,
        row_count_before_filter=binding.row_count_before_filter,
        row_count_after_filter=int(x_fit.shape[0]),
        dropped_rows_by_reason=binding.dropped_rows_by_reason,
        status=binding.status,
        reason_codes=binding.reason_codes,
    )
    try:
        evidence = fit_ols_lstsq(
            x_fit,
            y if drop_observation_index is None else y,
            active_binding,
            fit_intercept=fit_intercept,
            validation_fraction=validation_fraction,
            evidence_type="window_robustness_counterfactual",
            instrument_universe_digest="counterfactual_diagnostic",
        )
    except ValueError as exc:
        return {"status": "BLOCKED", "reason_code": str(exc)}

    design = _design_matrix(x_fit, fit_intercept=fit_intercept)
    conditioning = _conditioning_diagnostics(
        design,
        fit_intercept=fit_intercept,
        n_features=len(active_names),
    )
    return {
        "status": evidence.status,
        "coefficients": dict(evidence.coefficients),
        "condition_number": float(evidence.diagnostics.condition_number),
        "rank": int(evidence.diagnostics.rank),
        "rmse": float(evidence.diagnostics.rmse),
        "conditioning": conditioning,
        "excluded_features": list(excluded),
        "production_effect": "NONE",
    }


def compute_ill_conditioning_attribution_v0(
    window_plan: Mapping[str, object],
    records: Sequence[RollingLinearDriftInputV1],
    rank_conditioning: Mapping[str, object],
    influence: Mapping[str, object],
    *,
    config: WindowRobustnessConfigV0 | None = None,
) -> Dict[str, object]:
    cfg = config or WindowRobustnessConfigV0()
    sorted_records = _sort_records(records)
    feature_names = tuple(window_plan["feature_names_requested"])  # type: ignore[index]
    rank_by_id = {w["window_id"]: w for w in rank_conditioning["windows"]}  # type: ignore[index]
    influence_by_id = {w["window_id"]: w for w in influence["windows"]}  # type: ignore[index]
    attributions: list[Dict[str, object]] = []

    for window in window_plan["windows"]:  # type: ignore[index]
        window_id = str(window["window_id"])
        rank_info = rank_by_id.get(window_id, {})
        cond = float(rank_info.get("condition_number", 0.0) or 0.0)
        if not (
            rank_info.get("rank_deficient") or math.isinf(cond) or cond > cfg.max_condition_number
        ):
            continue

        start = int(window["start_index"])
        size = int(window["window_size"])
        window_records = sorted_records[start : start + size]
        baseline = _counterfactual_fit(
            window_records,
            feature_names,
            target_name=cfg.target_name,
            fit_intercept=cfg.fit_intercept,
            validation_fraction=cfg.validation_fraction,
        )
        without_zero_var = baseline
        standardized = _counterfactual_fit(
            window_records,
            feature_names,
            target_name=cfg.target_name,
            fit_intercept=cfg.fit_intercept,
            validation_fraction=cfg.validation_fraction,
            use_standardized_design=True,
        )

        influence_info = influence_by_id.get(window_id, {})
        top_obs: list[int] = []
        if influence_info.get("status") in {"AVAILABLE", "PARTIAL"}:
            cooks = influence_info.get("cooks_distance") or []
            indexed = [(index, value) for index, value in enumerate(cooks) if value is not None]
            indexed.sort(key=lambda item: item[1], reverse=True)
            top_obs = [index for index, _ in indexed[: cfg.influence_top_k]]

        loo_results = []
        for obs_index in top_obs:
            loo = _counterfactual_fit(
                window_records,
                feature_names,
                target_name=cfg.target_name,
                fit_intercept=cfg.fit_intercept,
                validation_fraction=cfg.validation_fraction,
                drop_observation_index=obs_index,
            )
            loo_results.append({"observation_index": obs_index, "result": loo})

        components: list[Dict[str, object]] = []
        if int(window["n_rows"]) < cfg.min_samples:
            components.append(
                {
                    "attribution_component": "SMALL_SAMPLE_SIZE",
                    "evidence": {"n_rows": window["n_rows"], "min_samples": cfg.min_samples},
                    "severity": "HIGH",
                    "causal_confidence": "MEDIUM",
                    "counterfactual_result": baseline,
                    "interpretation": "Sample count below configured minimum may amplify conditioning instability.",
                }
            )
        if window["feature_names_excluded"]:
            components.append(
                {
                    "attribution_component": "ZERO_OR_NEAR_ZERO_VARIANCE",
                    "evidence": {
                        "excluded": window["feature_names_excluded"],
                        "reasons": window["exclusion_reasons"],
                    },
                    "severity": "MEDIUM",
                    "causal_confidence": "HIGH",
                    "counterfactual_result": without_zero_var,
                    "interpretation": "Strict zero-variance exclusion changed active feature subset.",
                }
            )
        if rank_info.get("correlated_or_collinear_feature_pairs"):
            components.append(
                {
                    "attribution_component": "FEATURE_CORRELATION",
                    "evidence": rank_info["correlated_or_collinear_feature_pairs"],
                    "severity": "HIGH",
                    "causal_confidence": "MEDIUM",
                    "counterfactual_result": standardized,
                    "interpretation": "Highly correlated active features contribute to rank deficiency or ill-conditioning.",
                }
            )
        if loo_results:
            components.append(
                {
                    "attribution_component": "HIGH_LEVERAGE_OBSERVATIONS",
                    "evidence": {"leave_one_out": loo_results},
                    "severity": "MEDIUM",
                    "causal_confidence": "LOW",
                    "counterfactual_result": loo_results[0]["result"] if loo_results else {},
                    "interpretation": "Top Cook's-distance observations may contribute; attribution is comparative only.",
                }
            )
        if not components:
            components.append(
                {
                    "attribution_component": "UNKNOWN",
                    "evidence": rank_info,
                    "severity": "UNKNOWN",
                    "causal_confidence": "UNKNOWN",
                    "counterfactual_result": baseline,
                    "interpretation": "Ill-conditioning present without a single dominant attributable component.",
                }
            )

        attributions.append({"window_id": window_id, "attributions": components})

    return {"problematic_windows": attributions}


def compute_outlier_influence_diagnostics_v0(
    window_plan: Mapping[str, object],
    records: Sequence[RollingLinearDriftInputV1],
    *,
    config: WindowRobustnessConfigV0 | None = None,
) -> Dict[str, object]:
    cfg = config or WindowRobustnessConfigV0()
    sorted_records = _sort_records(records)
    feature_names = tuple(window_plan["feature_names_requested"])  # type: ignore[index]
    per_window: list[Dict[str, object]] = []

    for window in window_plan["windows"]:  # type: ignore[index]
        start = int(window["start_index"])
        size = int(window["window_size"])
        window_records = sorted_records[start : start + size]
        _, x, y, binding = _window_rows_and_binding(
            window_records,
            feature_names,
            target_name=str(window["target_name"]),
        )
        active_names = tuple(window["feature_names_active"])
        if not active_names:
            per_window.append(
                {
                    "window_id": window["window_id"],
                    "status": "UNAVAILABLE",
                    "reason_code": "NO_ACTIVE_FEATURES",
                }
            )
            continue
        active_indices = [feature_names.index(name) for name in active_names]
        x_active = x[:, active_indices]
        influence = _compute_influence_diagnostics(
            x_active,
            y,
            binding,
            fit_intercept=cfg.fit_intercept,
            active_feature_names=active_names,
            validation_fraction=cfg.validation_fraction,
        )
        per_window.append({"window_id": window["window_id"], **influence})

    return {"windows": per_window}


def compute_counterfactual_diagnostics_v0(
    window_plan: Mapping[str, object],
    records: Sequence[RollingLinearDriftInputV1],
    influence: Mapping[str, object],
    *,
    config: WindowRobustnessConfigV0 | None = None,
) -> Dict[str, object]:
    cfg = config or WindowRobustnessConfigV0()
    sorted_records = _sort_records(records)
    feature_names = tuple(window_plan["feature_names_requested"])  # type: ignore[index]
    influence_by_id = {w["window_id"]: w for w in influence["windows"]}  # type: ignore[index]
    counterfactuals: list[Dict[str, object]] = []

    focus_windows = [
        w
        for w in window_plan["windows"]  # type: ignore[index]
        if w.get("plan_class") in {"SLIDING", "ADJACENT_SIZE"}
        and (
            w["window_id"] in {f"W{i}" for i in cfg.focus_window_ids}
            or str(w["window_id"]).startswith("W1_")
            or str(w["window_id"]).startswith("W14")
        )
    ]

    for window in focus_windows:
        window_id = str(window["window_id"])
        start = int(window["start_index"])
        size = int(window["window_size"])
        window_records = sorted_records[start : start + size]
        baseline = _counterfactual_fit(
            window_records,
            feature_names,
            target_name=cfg.target_name,
            fit_intercept=cfg.fit_intercept,
            validation_fraction=cfg.validation_fraction,
        )
        counterfactuals.append(
            {
                "counterfactual_id": f"{window_id}_BASELINE",
                "window_id": window_id,
                "purpose": "BASELINE_ATTRIBUTION",
                "changed_diagnostic_condition": "NONE",
                "unchanged_semantic_bindings": True,
                "coefficient_delta": {},
                "sign_changes": [],
                "condition_number_delta": 0.0,
                "rank_delta": 0,
                "prediction_error_delta": 0.0,
                "interpretation": "Baseline fit with unmodified observations and bindings.",
                "production_effect": "NONE",
                "result": baseline,
            }
        )

        standardized = _counterfactual_fit(
            window_records,
            feature_names,
            target_name=cfg.target_name,
            fit_intercept=cfg.fit_intercept,
            validation_fraction=cfg.validation_fraction,
            use_standardized_design=True,
        )
        base_cond = float(baseline.get("condition_number", 0.0) or 0.0)
        std_cond = float(standardized.get("condition_number", 0.0) or 0.0)
        counterfactuals.append(
            {
                "counterfactual_id": f"{window_id}_STANDARDIZED_DESIGN",
                "window_id": window_id,
                "purpose": "CONDITIONING_ATTRIBUTION",
                "changed_diagnostic_condition": "STANDARDIZED_DESIGN_MATRIX",
                "unchanged_semantic_bindings": True,
                "coefficient_delta": {},
                "sign_changes": [],
                "condition_number_delta": std_cond - base_cond,
                "rank_delta": int(standardized.get("rank", 0)) - int(baseline.get("rank", 0)),
                "prediction_error_delta": float(standardized.get("rmse", 0.0))
                - float(baseline.get("rmse", 0.0)),
                "interpretation": "Standardized design matrix for conditioning attribution only.",
                "production_effect": "NONE",
                "result": standardized,
            }
        )

        influence_info = influence_by_id.get(window_id, {})
        if influence_info.get("status") in {"AVAILABLE", "PARTIAL"}:
            cooks = influence_info.get("cooks_distance") or []
            indexed = [(index, value) for index, value in enumerate(cooks) if value is not None]
            indexed.sort(key=lambda item: item[1], reverse=True)
            for obs_index, _ in indexed[: cfg.influence_top_k]:
                loo = _counterfactual_fit(
                    window_records,
                    feature_names,
                    target_name=cfg.target_name,
                    fit_intercept=cfg.fit_intercept,
                    validation_fraction=cfg.validation_fraction,
                    drop_observation_index=obs_index,
                )
                counterfactuals.append(
                    {
                        "counterfactual_id": f"{window_id}_LOO_{obs_index}",
                        "window_id": window_id,
                        "purpose": "LEAVE_ONE_OUT_INFLUENCE",
                        "changed_diagnostic_condition": f"EXCLUDE_OBSERVATION_{obs_index}",
                        "unchanged_semantic_bindings": True,
                        "coefficient_delta": {},
                        "sign_changes": [],
                        "condition_number_delta": float(loo.get("condition_number", 0.0) or 0.0)
                        - base_cond,
                        "rank_delta": int(loo.get("rank", 0)) - int(baseline.get("rank", 0)),
                        "prediction_error_delta": float(loo.get("rmse", 0.0))
                        - float(baseline.get("rmse", 0.0)),
                        "interpretation": "Leave-one-out counterfactual for influence attribution only.",
                        "production_effect": "NONE",
                        "result": loo,
                    }
                )

    return {"counterfactuals": counterfactuals}


def compute_window_sufficiency_diagnostics_v0(
    window_plan: Mapping[str, object],
    variance: Mapping[str, object],
    rank_conditioning: Mapping[str, object],
    subset_stability: Mapping[str, object],
    influence: Mapping[str, object],
    *,
    config: WindowRobustnessConfigV0 | None = None,
) -> Dict[str, object]:
    cfg = config or WindowRobustnessConfigV0()
    sliding_ids = [
        str(w["window_id"])
        for w in window_plan["windows"]  # type: ignore[index]
        if w.get("plan_class") == "SLIDING"
    ]
    rank_by_id = {w["window_id"]: w for w in rank_conditioning["windows"]}  # type: ignore[index]
    influence_by_id = {w["window_id"]: w for w in influence["windows"]}  # type: ignore[index]
    variance_by_id = {w["window_id"]: w for w in variance["windows"]}  # type: ignore[index]

    def _full_variance(window_id: str) -> bool:
        features = variance_by_id.get(window_id, {}).get("features", [])
        requested = window_plan["feature_names_requested"]  # type: ignore[index]
        if not features:
            return False
        return all(
            not feature.get("zero_variance") and not feature.get("near_zero_variance")
            for feature in features
            if feature["feature_name"] in requested
        )

    def _full_rank(window_id: str) -> bool:
        info = rank_by_id.get(window_id, {})
        return not info.get("rank_deficient", True)

    def _acceptable_conditioning(window_id: str) -> bool:
        info = rank_by_id.get(window_id, {})
        cond = float(info.get("condition_number", float("inf")) or float("inf"))
        if isinstance(info.get("condition_number"), str):
            return False
        return cond <= cfg.max_condition_number and not info.get("rank_deficient", True)

    def _stable_subset(window_id: str) -> bool:
        return window_id not in subset_stability.get("windows_with_subset_change", [])

    def _bounded_outlier(window_id: str) -> bool:
        info = influence_by_id.get(window_id, {})
        rate = float(info.get("influential_observation_rate", 0.0) or 0.0)
        return rate <= 0.1

    mins = {
        "minimum_window_with_full_requested_feature_variance": None,
        "minimum_window_with_full_rank": None,
        "minimum_window_with_acceptable_conditioning_under_existing_policy": None,
        "minimum_window_with_stable_active_feature_subset": None,
        "minimum_window_with_bounded_outlier_influence": None,
    }
    below: list[str] = []
    above: list[str] = []

    for window_id in sliding_ids:
        checks = [
            _full_variance(window_id),
            _full_rank(window_id),
            _acceptable_conditioning(window_id),
            _stable_subset(window_id),
            _bounded_outlier(window_id),
        ]
        keys = list(mins.keys())
        for key, ok in zip(keys, checks):
            if ok and mins[key] is None:
                mins[key] = window_id
        if not all(checks):
            below.append(window_id)
        else:
            above.append(window_id)

    transitions = []
    for index in range(len(sliding_ids) - 1):
        left = sliding_ids[index]
        right = sliding_ids[index + 1]
        if _acceptable_conditioning(left) != _acceptable_conditioning(right):
            transitions.append({"from": left, "to": right, "conditioning_transition": True})

    return {
        **mins,
        "windows_below_sufficiency": below,
        "windows_above_sufficiency": above,
        "sufficiency_transition_points": transitions,
    }


def classify_window_statuses_v0(
    window_plan: Mapping[str, object],
    variance: Mapping[str, object],
    rank_conditioning: Mapping[str, object],
    influence: Mapping[str, object],
    *,
    config: WindowRobustnessConfigV0 | None = None,
) -> Dict[str, object]:
    cfg = config or WindowRobustnessConfigV0()
    rank_by_id = {w["window_id"]: w for w in rank_conditioning["windows"]}  # type: ignore[index]
    influence_by_id = {w["window_id"]: w for w in influence["windows"]}  # type: ignore[index]
    variance_by_id = {w["window_id"]: w for w in variance["windows"]}  # type: ignore[index]
    statuses: list[Dict[str, object]] = []

    for window in window_plan["windows"]:  # type: ignore[index]
        window_id = str(window["window_id"])
        if int(window["n_rows"]) < cfg.min_samples:
            primary = "INSUFFICIENT_SAMPLE"
            reasons = ["INSUFFICIENT_SAMPLE_COUNT"]
        else:
            features = variance_by_id.get(window_id, {}).get("features", [])
            has_zero = any(f.get("zero_variance") for f in features)
            has_near_zero = any(f.get("near_zero_variance") for f in features)
            rank_info = rank_by_id.get(window_id, {})
            cond = rank_info.get("condition_number", 0.0)
            cond_value = float("inf") if cond == "Infinity" else float(cond or 0.0)
            rank_def = bool(rank_info.get("rank_deficient"))
            ill_cond = math.isinf(cond_value) or cond_value > cfg.max_condition_number
            infl = influence_by_id.get(window_id, {})
            outlier_sensitive = float(infl.get("influential_observation_rate", 0.0) or 0.0) > 0.1

            flags = []
            if has_zero:
                flags.append("ZERO_VARIANCE")
            if has_near_zero:
                flags.append("NEAR_ZERO_VARIANCE")
            if rank_def:
                flags.append("RANK_DEFICIENT")
            if ill_cond:
                flags.append("ILL_CONDITIONED")
            if outlier_sensitive:
                flags.append("OUTLIER_SENSITIVE")

            if len(flags) > 1:
                primary = "MIXED_FAILURE"
            elif len(flags) == 1:
                primary = flags[0]
            else:
                primary = "STABLE"
            reasons = flags or ["STABLE"]

        statuses.append(
            {
                "window_id": window_id,
                "primary_status": primary,
                "reason_codes": reasons,
                "blocking": primary
                in {
                    "RANK_DEFICIENT",
                    "ILL_CONDITIONED",
                    "MIXED_FAILURE",
                    "INSUFFICIENT_SAMPLE",
                },
                "diagnostic_only": True,
                "runtime_effect": "NONE",
                "authority_effect": "NONE",
            }
        )

    return {"windows": statuses}


def aggregate_diagnostic_verdict_v0(
    window_statuses: Mapping[str, object],
) -> tuple[str, str]:
    sliding = [
        s
        for s in window_statuses["windows"]  # type: ignore[index]
        if str(s["window_id"]).startswith("W") and "_SIZE_" not in str(s["window_id"])
    ]
    if not sliding:
        return "INCONCLUSIVE", "INCONCLUSIVE_DIAGNOSTIC_LIMITATION"

    primary_counts: Dict[str, int] = {}
    for status in sliding:
        primary = str(status["primary_status"])
        primary_counts[primary] = primary_counts.get(primary, 0) + 1

    has_ill = primary_counts.get("ILL_CONDITIONED", 0) + primary_counts.get("MIXED_FAILURE", 0) > 0
    has_outlier = primary_counts.get("OUTLIER_SENSITIVE", 0) > 0
    has_zero_var = (
        primary_counts.get("ZERO_VARIANCE", 0) + primary_counts.get("NEAR_ZERO_VARIANCE", 0) > 0
    )
    has_insufficient = primary_counts.get("INSUFFICIENT_SAMPLE", 0) > 0

    if has_ill and has_outlier:
        return "FAIL", "FAIL_CONFIRMED_MIXED_WINDOW_OUTLIER_CONDITIONING"
    if has_ill:
        return "FAIL", "FAIL_CONFIRMED_ILL_CONDITIONING"
    if has_outlier:
        return "FAIL", "FAIL_CONFIRMED_OUTLIER_DOMINATED_WINDOWS"
    if has_zero_var or has_insufficient:
        return "FAIL", "FAIL_CONFIRMED_WINDOW_SAMPLE_INSTABILITY"
    return "PASS", "PASS_WINDOW_AND_OUTLIER_ROBUSTNESS_DIAGNOSTIC_COMPLETED"


@dataclass
class WindowRobustnessDiagnosticResultV0:
    scope: str = "OUTLIER_AND_WINDOW_ROBUSTNESS_DIAGNOSTIC_V0"
    schema_version: str = SCHEMA_VERSION
    status: str = "PASS"
    verdict: str = "PASS_WINDOW_AND_OUTLIER_ROBUSTNESS_DIAGNOSTIC_COMPLETED"
    go_token: str = GO_TOKEN_REQUIRED
    model_spec: str = MODEL_SPEC_VERSION
    authority_effect: str = "NONE"
    runtime_effect: str = "NONE"
    economic_evaluation_executed: bool = False
    window_plan: Dict[str, object] = field(default_factory=dict)
    feature_variance_diagnostics: Dict[str, object] = field(default_factory=dict)
    active_feature_subset_stability: Dict[str, object] = field(default_factory=dict)
    rank_and_conditioning_diagnostics: Dict[str, object] = field(default_factory=dict)
    ill_conditioning_attribution: Dict[str, object] = field(default_factory=dict)
    outlier_influence_diagnostics: Dict[str, object] = field(default_factory=dict)
    counterfactual_diagnostics: Dict[str, object] = field(default_factory=dict)
    window_sufficiency_diagnostics: Dict[str, object] = field(default_factory=dict)
    window_statuses: Dict[str, object] = field(default_factory=dict)
    reason_codes: Tuple[str, ...] = ()

    def to_dict(self) -> Dict[str, object]:
        payload = {
            "scope": self.scope,
            "schema_version": self.schema_version,
            "status": self.status,
            "verdict": self.verdict,
            "go_token": self.go_token,
            "model_spec": self.model_spec,
            "authority_effect": self.authority_effect,
            "runtime_effect": self.runtime_effect,
            "economic_evaluation_executed": self.economic_evaluation_executed,
            "window_plan": self.window_plan,
            "feature_variance_diagnostics": self.feature_variance_diagnostics,
            "active_feature_subset_stability": self.active_feature_subset_stability,
            "rank_and_conditioning_diagnostics": self.rank_and_conditioning_diagnostics,
            "ill_conditioning_attribution": self.ill_conditioning_attribution,
            "outlier_influence_diagnostics": self.outlier_influence_diagnostics,
            "counterfactual_diagnostics": self.counterfactual_diagnostics,
            "window_sufficiency_diagnostics": self.window_sufficiency_diagnostics,
            "window_statuses": self.window_statuses,
            "reason_codes": list(self.reason_codes),
        }
        return _json_safe(payload)  # type: ignore[return-value]


def run_outlier_and_window_robustness_diagnostic_v0(
    records: Sequence[RollingLinearDriftInputV1],
    *,
    config: WindowRobustnessConfigV0 | None = None,
    go_token: str | None = None,
) -> WindowRobustnessDiagnosticResultV0:
    if go_token != GO_TOKEN_REQUIRED:
        return WindowRobustnessDiagnosticResultV0(
            status="FAIL_CLOSED",
            verdict="BLOCKED_INPUT_OR_CONTRACT_FAILURE",
            reason_codes=("GO_TOKEN_REQUIRED",),
        )

    cfg = config or WindowRobustnessConfigV0()
    try:
        sorted_records = _sort_records(records)
        if not sorted_records:
            raise ValueError("INSUFFICIENT_DATA")
        for record in sorted_records:
            if record.feature_availability_time > record.decision_time:
                raise ValueError("LOOKAHEAD_BLOCKED")

        window_plan = build_window_plan_v0(sorted_records, config=cfg)
        variance = compute_feature_variance_diagnostics_v0(window_plan, sorted_records)
        subset = compute_active_feature_subset_stability_v0(window_plan)
        rank_cond = compute_rank_and_conditioning_diagnostics_v0(
            window_plan, sorted_records, config=cfg
        )
        influence = compute_outlier_influence_diagnostics_v0(
            window_plan, sorted_records, config=cfg
        )
        ill_attr = compute_ill_conditioning_attribution_v0(
            window_plan,
            sorted_records,
            rank_cond,
            influence,
            config=cfg,
        )
        counterfactuals = compute_counterfactual_diagnostics_v0(
            window_plan,
            sorted_records,
            influence,
            config=cfg,
        )
        sufficiency = compute_window_sufficiency_diagnostics_v0(
            window_plan,
            variance,
            rank_cond,
            subset,
            influence,
            config=cfg,
        )
        statuses = classify_window_statuses_v0(
            window_plan,
            variance,
            rank_cond,
            influence,
            config=cfg,
        )
        status, verdict = aggregate_diagnostic_verdict_v0(statuses)
        return WindowRobustnessDiagnosticResultV0(
            status=status,
            verdict=verdict,
            go_token=GO_TOKEN_REQUIRED,
            window_plan=window_plan,
            feature_variance_diagnostics=variance,
            active_feature_subset_stability=subset,
            rank_and_conditioning_diagnostics=rank_cond,
            ill_conditioning_attribution=ill_attr,
            outlier_influence_diagnostics=influence,
            counterfactual_diagnostics=counterfactuals,
            window_sufficiency_diagnostics=sufficiency,
            window_statuses=statuses,
            reason_codes=(verdict,),
        )
    except ValueError as exc:
        return WindowRobustnessDiagnosticResultV0(
            status="FAIL_CLOSED",
            verdict="BLOCKED_INPUT_OR_CONTRACT_FAILURE",
            reason_codes=(str(exc),),
        )


def semantic_payload_for_replay(payload: Mapping[str, object]) -> str:
    """Deterministic semantic serialization excluding non-semantic provenance."""
    clone = json.loads(json.dumps(payload, sort_keys=True, default=str))
    for key in ("generated_at", "timestamp", "run_timestamp"):
        clone.pop(key, None)
    return json.dumps(clone, sort_keys=True, separators=(",", ":"))


def make_fixture_records_v0() -> Tuple[RollingLinearDriftInputV1, ...]:
    """Deterministic fixture reproducing W1 zero-variance and W14 ill-conditioning patterns."""
    records: list[RollingLinearDriftInputV1] = []
    for index in range(1020):
        hour = index % 24
        day = index // 24
        decision_time = f"2026-01-{day + 1:02d}T{hour:02d}:00:00Z"
        signal = float(index)
        trend = 1.0 if 60 <= (index % 120) < 120 else float(index % 5)
        duplicate = trend * 2.0 if index >= 840 else trend * 2.0 + float(index % 3) * 1e-12
        records.append(
            RollingLinearDriftInputV1(
                instrument_id="PF_ETHUSD",
                decision_time=decision_time,
                feature_availability_time=decision_time,
                target=0.5 * signal + 0.1,
                features={
                    "trend_following": trend,
                    "momentum_1h": float(index % 7),
                    "bollinger_bands": signal * 0.01,
                    "fee_bps": 0.0,
                    "slippage_bps": 0.0,
                    "duplicate_collinear": duplicate,
                },
            )
        )
    return tuple(records)


def make_small_fixture_records_v0() -> Tuple[RollingLinearDriftInputV1, ...]:
    """Compact fixture for unit tests."""
    records: list[RollingLinearDriftInputV1] = []
    for index in range(24):
        records.append(
            RollingLinearDriftInputV1(
                instrument_id="PF_ETHUSD",
                decision_time=f"2026-01-01T{index:02d}:00:00Z",
                feature_availability_time=f"2026-01-01T{index:02d}:00:00Z",
                target=float(index) * 0.3,
                features={
                    "signal": float(index),
                    "constant": 1.0 if index < 8 else float(index % 3),
                    "collinear": float(index) * 2.0,
                    "collinear_copy": float(index) * 2.0,
                },
            )
        )
    return tuple(records)
