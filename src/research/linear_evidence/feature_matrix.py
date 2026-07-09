from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping, Sequence
from typing import Any

import numpy as np

from .contracts import FeatureMatrixBindingV1


def _stable_digest(payload: Any) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str).encode()
    return hashlib.sha256(encoded).hexdigest()


def _as_float(value: object, *, field_name: str) -> float:
    try:
        result = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"NON_NUMERIC_FIELD:{field_name}") from exc
    if not np.isfinite(result):
        raise ValueError(f"NON_FINITE_FIELD:{field_name}")
    return result


def build_feature_matrix_binding(
    rows: Sequence[Mapping[str, object]],
    *,
    feature_names: Sequence[str],
    target_name: str,
    time_name: str = "decision_time",
    validation_policy: str = "TIME_ORDERED",
) -> tuple[np.ndarray, np.ndarray, FeatureMatrixBindingV1]:
    if validation_policy != "TIME_ORDERED":
        raise ValueError("RANDOM_VALIDATION_SPLIT_BLOCKED")
    if not rows:
        raise ValueError("INSUFFICIENT_DATA")
    if not feature_names:
        raise ValueError("INSUFFICIENT_DATA")

    ordered = sorted(rows, key=lambda row: str(row.get(time_name, "")))
    times = [str(row.get(time_name, "")) for row in ordered]
    if any(not t for t in times):
        raise ValueError("TARGET_BINDING_MISSING")
    if times != sorted(times):
        raise ValueError("TIME_ORDERING_FAILED")

    dropped: dict[str, int] = {}
    xs: list[list[float]] = []
    ys: list[float] = []
    kept_rows: list[Mapping[str, object]] = []

    for row in ordered:
        try:
            xs.append([_as_float(row.get(name), field_name=name) for name in feature_names])
            ys.append(_as_float(row.get(target_name), field_name=target_name))
            kept_rows.append(row)
        except ValueError as exc:
            dropped[str(exc)] = dropped.get(str(exc), 0) + 1

    if not xs:
        raise ValueError("INSUFFICIENT_DATA")

    x = np.asarray(xs, dtype=float)
    y = np.asarray(ys, dtype=float)
    binding = FeatureMatrixBindingV1(
        target_name=target_name,
        feature_names=tuple(feature_names),
        n_samples=int(x.shape[0]),
        n_features=int(x.shape[1]),
        feature_matrix_digest=_stable_digest(
            {"feature_names": list(feature_names), "x": x.tolist()}
        ),
        target_digest=_stable_digest({"target_name": target_name, "y": y.tolist()}),
        validation_policy=validation_policy,
        time_range={"start": str(kept_rows[0][time_name]), "end": str(kept_rows[-1][time_name])},
        row_count_before_filter=len(rows),
        row_count_after_filter=int(x.shape[0]),
        dropped_rows_by_reason=dropped,
    )
    return x, y, binding
