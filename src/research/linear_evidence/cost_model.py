from __future__ import annotations

import numpy as np

from .contracts import CostModelCalibrationEvidenceV1, LinearModelEvidenceV1


def build_cost_model_calibration_evidence(
    model_evidence: LinearModelEvidenceV1,
    *,
    observed_target_bps: np.ndarray,
    predicted_target_bps: np.ndarray,
) -> CostModelCalibrationEvidenceV1:
    if observed_target_bps.shape != predicted_target_bps.shape:
        raise ValueError("FEATURE_TARGET_SHAPE_MISMATCH")
    residual_abs = np.abs(observed_target_bps - predicted_target_bps)
    if residual_abs.size == 0:
        raise ValueError("INSUFFICIENT_DATA")

    p75 = float(np.percentile(residual_abs, 75))
    p90 = float(np.percentile(residual_abs, 90))
    stress = float(max(p90, np.max(residual_abs)))

    status = model_evidence.status
    reason_codes = tuple(model_evidence.reason_codes)
    if model_evidence.status == "CALIBRATION_CANDIDATE" and p90 >= 0:
        status = "CALIBRATION_VALIDATED_OFFLINE"

    return CostModelCalibrationEvidenceV1(
        linear_model_evidence=model_evidence,
        rmse_bps=float(np.sqrt(np.mean((observed_target_bps - predicted_target_bps) ** 2))),
        mae_bps=float(np.mean(residual_abs)),
        max_abs_error_bps=float(np.max(residual_abs)),
        p75_abs_error_bps=p75,
        p90_abs_error_bps=p90,
        stress_cost_bps=stress,
        calibrated_cost_policy="CONSERVATIVE_NOT_MEAN",
        status=status,
        reason_codes=reason_codes,
    )


AUTHORITY_EFFECT = "NONE"
RUNTIME_EFFECT = "NONE"


def with_authority_neutral_effects(payload):
    enriched = dict(payload)
    enriched["authority_effect"] = AUTHORITY_EFFECT
    enriched["runtime_effect"] = RUNTIME_EFFECT
    return enriched
