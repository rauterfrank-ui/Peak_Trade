"""Additive Market Intelligence research evidence projection (learning export unchanged)."""

from __future__ import annotations

from types import MappingProxyType
from typing import Any, Final, Mapping, Sequence

from src.learning.deterministic_decision_outcome_v0.serialization_v0 import compute_content_hash_v0
from src.learning.market_intelligence_forecast_calibration_offline_stack_v1.calibration_evidence_v1 import (
    build_calibration_evidence_v1,
)
from src.learning.market_intelligence_forecast_calibration_offline_stack_v1.constants_v1 import (
    STACK_DOMAIN,
)
from src.learning.market_intelligence_forecast_calibration_offline_stack_v1.forecast_evidence_v1 import (
    validate_forecast_evidence_v1,
)

SCHEMA_VERSION: Final[str] = "market_intelligence_research_evidence_v1"
EVIDENCE_CLASS_MI_RESEARCH: Final[str] = "MARKET_INTELLIGENCE_RESEARCH_EVIDENCE"
MI_RESEARCH_AUTHORITY: Final[str] = "NONE"


def project_market_intelligence_research_evidence_v1(
    *,
    forecast_evidence: Mapping[str, Any],
    calibration_evidence: Mapping[str, Any],
    drift_assessment_refs: Sequence[str] | None = None,
    legacy_learning_evidence_ref: str | None = None,
) -> MappingProxyType[str, Any]:
    forecast = validate_forecast_evidence_v1(forecast_evidence)
    calib = dict(calibration_evidence)
    if calib.get("forecast_evidence_id") != forecast["forecast_evidence_id"]:
        raise ValueError("CALIBRATION_FORECAST_ID_MISMATCH")

    body = {
        "schema_version": SCHEMA_VERSION,
        "domain": STACK_DOMAIN,
        "forecast_evidence_id": forecast["forecast_evidence_id"],
        "calibration_evidence_id": calib.get("calibration_evidence_id"),
        "n_bars": forecast["n_bars"],
        "bar_spec_ref": forecast["bar_spec_ref"],
        "forecast_kind": forecast["forecast_kind"],
        "evaluability": calib.get("evaluability"),
        "drift_assessment_refs": list(drift_assessment_refs or []),
        "legacy_learning_evidence_ref": legacy_learning_evidence_ref,
        "market_intelligence_research_authority": MI_RESEARCH_AUTHORITY,
        "evidence_class": EVIDENCE_CLASS_MI_RESEARCH,
        "productive_authority": "NONE",
        "runtime_reachability": False,
        "can_auto_promote": False,
    }
    digest = compute_content_hash_v0(body)
    body["research_evidence_id"] = f"mi.research.{digest[:48]}"
    body["content_digest"] = digest
    return MappingProxyType(body)


def build_calibration_bundle_for_projection_v1(**kwargs: Any) -> MappingProxyType[str, Any]:
    return build_calibration_evidence_v1(**kwargs)
