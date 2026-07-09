"""Offline linear evidence diagnostics.

This package is offline-only and authority-neutral. It must not import runtime,
scheduler, live execution, or order adapter paths.
"""

from .contracts import (
    CostModelCalibrationEvidenceV1,
    FeatureMatrixBindingV1,
    LinearModelDiagnosticsV1,
    LinearModelEvidenceV1,
)
from .cost_model import build_cost_model_calibration_evidence
from .feature_matrix import build_feature_matrix_binding
from .fitters import fit_ols_lstsq

__all__ = [
    "CostModelCalibrationEvidenceV1",
    "FeatureMatrixBindingV1",
    "LinearModelDiagnosticsV1",
    "LinearModelEvidenceV1",
    "build_cost_model_calibration_evidence",
    "build_feature_matrix_binding",
    "fit_ols_lstsq",
]
