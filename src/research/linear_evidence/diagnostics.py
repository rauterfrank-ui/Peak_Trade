"""Offline linear evidence diagnostics.

This module is intentionally offline-only and authority-neutral.
It provides small deterministic helpers shared by the linear evidence
surfaces without importing any runtime execution paths.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import sqrt
from typing import Dict, Iterable, Mapping, Sequence


AUTHORITY_EFFECT = "NONE"
RUNTIME_EFFECT = "NONE"


@dataclass(frozen=True)
class ResidualDiagnosticsV1:
    """Basic residual diagnostics for offline linear evidence."""

    n_samples: int
    mae: float
    rmse: float
    max_abs_error: float
    mean_error: float
    authority_effect: str = AUTHORITY_EFFECT
    runtime_effect: str = RUNTIME_EFFECT


def compute_residual_diagnostics(
    residuals: Sequence[float] | Iterable[float],
) -> ResidualDiagnosticsV1:
    values = [float(v) for v in residuals]
    if not values:
        return ResidualDiagnosticsV1(
            n_samples=0,
            mae=0.0,
            rmse=0.0,
            max_abs_error=0.0,
            mean_error=0.0,
        )

    abs_values = [abs(v) for v in values]
    n = len(values)
    return ResidualDiagnosticsV1(
        n_samples=n,
        mae=sum(abs_values) / n,
        rmse=sqrt(sum(v * v for v in values) / n),
        max_abs_error=max(abs_values),
        mean_error=sum(values) / n,
    )


def attach_authority_neutral_fields(payload: Mapping[str, object]) -> Dict[str, object]:
    enriched = dict(payload)
    enriched["authority_effect"] = AUTHORITY_EFFECT
    enriched["runtime_effect"] = RUNTIME_EFFECT
    return enriched


__all__ = [
    "AUTHORITY_EFFECT",
    "RUNTIME_EFFECT",
    "ResidualDiagnosticsV1",
    "attach_authority_neutral_fields",
    "compute_residual_diagnostics",
]
