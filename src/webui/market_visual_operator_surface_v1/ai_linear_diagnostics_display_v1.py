"""AI linear diagnostics display view model (optional, read-only parse).

If a linear diagnostics bundle root is configured and files are present, surfaces
coefficients, condition number, drift, factor exposure and orthogonality read-only.
Otherwise renders a compact empty ``MISSING_SOURCE`` state that names the required path.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .contracts import (
    ENV_LINEAR_DIAGNOSTICS_ROOT,
    ActivityState,
    load_json_or_none,
    resolved_dir_or_none,
)

FACTOR_EXPOSURE_FILE = "factor_exposure_diagnostics.json"
DRIFT_FILE = "rolling_linear_drift_diagnostics.json"
ORTHOGONALITY_FILE = "signal_orthogonality_diagnostics.json"


def _coefficients(payload: dict[str, Any]) -> list[dict[str, Any]]:
    names = payload.get("feature_names")
    coeffs = payload.get("coefficients")
    rows: list[dict[str, Any]] = []
    if isinstance(names, list) and isinstance(coeffs, list) and len(names) == len(coeffs):
        for name, value in zip(names, coeffs):
            if isinstance(value, (int, float)) and not isinstance(value, bool):
                rows.append({"feature": str(name), "coefficient": float(value)})
            else:
                rows.append({"feature": str(name), "coefficient": None})
    return rows


def _base_vm(*, activity_state: str) -> dict[str, Any]:
    return {
        "section_visible": True,
        "read_only": True,
        "non_authorizing": True,
        "activity_state": activity_state,
        "bundle_status": "MISSING_SOURCE",
        "coefficients": [],
        "condition_number": None,
        "matrix_rank": None,
        "rank_deficient": None,
        "drift_score": None,
        "drift_verdict": "",
        "dominant_factor_exposures": [],
        "orthogonality_coefficients": [],
        "source_id": "",
        "quality": "missing_source",
        "recovery_hint": (
            f"Set {ENV_LINEAR_DIAGNOSTICS_ROOT} to an offline linear diagnostics bundle "
            f"containing {FACTOR_EXPOSURE_FILE}, {DRIFT_FILE}, {ORTHOGONALITY_FILE}."
        ),
    }


def build_ai_linear_diagnostics_display_v1() -> dict[str, Any]:
    """Build the AI linear diagnostics display VM (optional; fail closed by default)."""
    bundle_root = resolved_dir_or_none(ENV_LINEAR_DIAGNOSTICS_ROOT)
    if bundle_root is None:
        return _base_vm(activity_state=ActivityState.NOT_AVAILABLE)

    factor = load_json_or_none(bundle_root / FACTOR_EXPOSURE_FILE)
    drift = load_json_or_none(bundle_root / DRIFT_FILE)
    ortho = load_json_or_none(bundle_root / ORTHOGONALITY_FILE)

    if not any(isinstance(x, dict) for x in (factor, drift, ortho)):
        vm = _base_vm(activity_state=ActivityState.AVAILABLE_NOT_RUN)
        vm["source_id"] = str(bundle_root)
        return vm

    factor = factor if isinstance(factor, dict) else {}
    drift = drift if isinstance(drift, dict) else {}
    ortho = ortho if isinstance(ortho, dict) else {}

    condition_number = factor.get("condition_number")
    dominant = factor.get("dominant_factor_exposures")
    dominant_list = dominant if isinstance(dominant, list) else []

    drift_score = drift.get("drift_score")

    return {
        "section_visible": True,
        "read_only": True,
        "non_authorizing": True,
        "activity_state": ActivityState.PROCESSED,
        "bundle_status": "loaded",
        "coefficients": _coefficients(factor),
        "condition_number": (
            float(condition_number)
            if isinstance(condition_number, (int, float)) and not isinstance(condition_number, bool)
            else None
        ),
        "matrix_rank": factor.get("matrix_rank"),
        "rank_deficient": factor.get("rank_deficient"),
        "drift_score": (
            float(drift_score)
            if isinstance(drift_score, (int, float)) and not isinstance(drift_score, bool)
            else None
        ),
        "drift_verdict": str(drift.get("verdict") or ""),
        "dominant_factor_exposures": dominant_list,
        "orthogonality_coefficients": _coefficients(ortho),
        "source_id": str(bundle_root),
        "quality": "loaded",
        "recovery_hint": "",
    }


__all__ = ["build_ai_linear_diagnostics_display_v1"]
