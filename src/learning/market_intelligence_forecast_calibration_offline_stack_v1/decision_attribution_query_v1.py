"""Read-only decision attribution query over existing DDO references (evidence-only)."""

from __future__ import annotations

from types import MappingProxyType
from typing import Any, Final, Mapping

from src.learning.deterministic_decision_outcome_v0.common_v0 import require_mapping
from src.learning.deterministic_decision_outcome_v0.evaluation_records_v0 import (
    validate_attribution_record_v0,
)
from src.learning.market_intelligence_forecast_calibration_offline_stack_v1.constants_v1 import (
    IS_EVIDENCE_ONLY,
    STACK_DOMAIN,
)
from src.learning.market_intelligence_forecast_calibration_offline_stack_v1.forecast_evidence_v1 import (
    validate_forecast_evidence_v1,
)

QUERY_SCHEMA_VERSION: Final[str] = "market_intelligence_decision_attribution_query_v1"
TRADING_AUTHORITY: Final[str] = "NONE"


def query_market_intelligence_decision_attribution_v1(
    *,
    attribution_record: Mapping[str, Any] | None,
    forecast_evidence: Mapping[str, Any] | None,
    calibration_evidence: Mapping[str, Any] | None,
    selected_instrument_ref: str | None = None,
    side_state_ref: str | None = None,
    regime_ref: str | None = None,
) -> MappingProxyType[str, Any]:
    forecast = (
        validate_forecast_evidence_v1(forecast_evidence) if forecast_evidence is not None else None
    )
    calib = dict(calibration_evidence) if calibration_evidence is not None else None
    attr = (
        validate_attribution_record_v0(attribution_record)
        if attribution_record is not None
        else None
    )

    decision_event_ref = None
    if forecast is not None and forecast.get("decision_event_ref"):
        decision_event_ref = forecast["decision_event_ref"]
    elif attr is not None:
        decision_event_ref = attr.get("decision_event_ref")

    body = {
        "schema_version": QUERY_SCHEMA_VERSION,
        "domain": STACK_DOMAIN,
        "decision_event_ref": decision_event_ref,
        "attribution_record_ref": attr.get("record_id") if attr is not None else None,
        "forecast_evidence_id": forecast["forecast_evidence_id"] if forecast else None,
        "calibration_evidence_id": calib.get("calibration_evidence_id") if calib else None,
        "actual_outcome_ref": calib.get("actual_outcome_ref") if calib else None,
        "selected_instrument_ref": selected_instrument_ref
        or (forecast.get("selected_instrument_ref") if forecast else None),
        "side_state_ref": side_state_ref,
        "regime_ref": regime_ref,
        "missing_context_explicit": {
            "side_state_ref": side_state_ref is None,
            "regime_ref": regime_ref is None,
            "attribution_record": attr is None,
        },
        "is_evidence_only": IS_EVIDENCE_ONLY,
        "trading_authority": TRADING_AUTHORITY,
    }
    if attr is not None:
        body["attribution_fields"] = {
            key: attr.get(key)
            for key in (
                "decision_event_ref",
                "outcome_record_ref",
                "evaluation_horizon",
            )
            if key in attr
        }
    if forecast is not None:
        body["forecast_refs"] = require_mapping(
            {
                "information_set_ref": forecast["information_set_ref"],
                "market_state_refs": list(forecast["market_state_refs"]),
            },
            "forecast_refs",
        )
    return MappingProxyType(body)
