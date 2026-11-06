"""Project typed MI learning evidence onto the existing learning evidence export path."""

from __future__ import annotations

from types import MappingProxyType
from typing import Any, Final, Mapping

from src.learning.deterministic_decision_outcome_v0.learning_evidence_record_v1 import (
    validate_learning_evidence_record_v1,
)
from src.learning.market_intelligence_forecast_calibration_offline_stack_v1.mi_learning_evidence_record_v1 import (
    EVIDENCE_CLASS_MI_LEARNING,
    validate_mi_learning_evidence_record_v1,
)

EXPORT_PATH_SCHEMA: Final[str] = "mi_learning_evidence_learning_export_path_v1"
EXPORT_PATH_PRODUCER: Final[str] = (
    "peak_trade.learning.market_intelligence_mi_learning_evidence_learning_export_v1"
)
ROUTE_LEGACY_LEARNING_EVIDENCE: Final[str] = "LEGACY_DDO_LEARNING_EVIDENCE_EXPORT_V1"
ROUTE_MI_TYPED_ONLY: Final[str] = "MI_TYPED_LEARNING_EVIDENCE_ONLY"
ROUTE_MI_TYPED_WITH_LEGACY: Final[str] = "MI_TYPED_WITH_LEGACY_LEARNING_EVIDENCE_REF"


def route_learning_evidence_for_consumer_v1(
    *,
    mi_learning_evidence: Mapping[str, Any],
    legacy_learning_evidence: Mapping[str, Any] | None = None,
) -> MappingProxyType[str, Any]:
    """Explicit consumer routing; does not mutate DDO reducers or productive state."""
    mi_record = validate_mi_learning_evidence_record_v1(mi_learning_evidence)
    if mi_record.get("evidence_class") != EVIDENCE_CLASS_MI_LEARNING:
        raise ValueError("MI_LEARNING_EVIDENCE_CLASS_REQUIRED")
    legacy_ref = mi_record.get("legacy_learning_evidence_ref")
    legacy_validated = None
    if legacy_learning_evidence is not None:
        legacy_validated = validate_learning_evidence_record_v1(legacy_learning_evidence)
    route = ROUTE_MI_TYPED_ONLY
    if legacy_validated is not None or legacy_ref:
        route = ROUTE_MI_TYPED_WITH_LEGACY
    return MappingProxyType(
        {
            "consumer_route": route,
            "mi_learning_evidence_id": mi_record["mi_learning_evidence_id"],
            "forecast_evidence_id": mi_record["forecast_evidence_id"],
            "legacy_learning_evidence_record_id": (
                str(legacy_validated["record_id"]) if legacy_validated is not None else legacy_ref
            ),
            "legacy_ddo_export_compatible": legacy_validated is not None,
            "productive_ddo_reducer_mutated": False,
        }
    )


def export_mi_learning_evidence_onto_learning_path_v1(
    mi_learning_evidence: Mapping[str, Any],
    *,
    legacy_learning_evidence: Mapping[str, Any] | None = None,
) -> MappingProxyType[str, Any]:
    mi_record = validate_mi_learning_evidence_record_v1(mi_learning_evidence)
    consumer_route = route_learning_evidence_for_consumer_v1(
        mi_learning_evidence=mi_record,
        legacy_learning_evidence=legacy_learning_evidence,
    )
    legacy_payload = None
    if legacy_learning_evidence is not None:
        legacy_payload = dict(validate_learning_evidence_record_v1(legacy_learning_evidence))
    return MappingProxyType(
        {
            "schema_version": EXPORT_PATH_SCHEMA,
            "export_path_producer": EXPORT_PATH_PRODUCER,
            "mi_learning_evidence": dict(mi_record),
            "legacy_learning_evidence": legacy_payload,
            "consumer_route": dict(consumer_route),
            "learning_evidence_export_path": ROUTE_LEGACY_LEARNING_EVIDENCE,
            "external_effect_authorized": False,
            "runtime_reachability": False,
            "promotion_authority_created": False,
        }
    )
