"""Offline optimization intake for additive MI research evidence (no productive join)."""

from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Any, Final, Mapping

from src.experiments.canonical_optimization_universe_learning_input_v1 import (
    CanonicalOptimizationUniverseLearningInputRequestV1,
    validate_canonical_optimization_universe_learning_input_v1,
)
from src.learning.deterministic_decision_outcome_v0.serialization_v0 import compute_content_hash_v0
from src.learning.market_intelligence_forecast_calibration_offline_stack_v1.constants_v1 import (
    OPTIMIZATION_PRODUCTIVE_AUTHORITY,
)
from src.learning.market_intelligence_forecast_calibration_offline_stack_v1.mi_research_evidence_v1 import (
    EVIDENCE_CLASS_MI_RESEARCH,
    SCHEMA_VERSION as MI_RESEARCH_SCHEMA_VERSION,
)

SCHEMA_VERSION: Final[str] = "market_intelligence_optimization_research_input_v1"
MI_OPTIMIZATION_INPUT_DOMAIN: Final[str] = (
    "peak_trade.learning.market_intelligence.optimization_research_input.v1"
)

STATUS_ACCEPTED: Final[str] = "ACCEPTED_OFFLINE_MI_RESEARCH_INPUT"
STATUS_REJECTED: Final[str] = "REJECTED_MI_RESEARCH_INPUT"


@dataclass(frozen=True)
class MarketIntelligenceOptimizationResearchInputRequestV1:
    market_intelligence_research_evidence: Mapping[str, Any] | None
    legacy_learning_evidence: Mapping[str, Any] | None = None
    requested_productive_join: bool = False
    requested_mv2_dp_binding: bool = False
    requested_cap23_binding: bool = False


class MarketIntelligenceOptimizationResearchInputError(ValueError):
    """Fail-closed MI optimization research input error."""


def validate_market_intelligence_optimization_research_input_v1(
    request: MarketIntelligenceOptimizationResearchInputRequestV1,
) -> MappingProxyType[str, Any]:
    if request.requested_productive_join:
        raise MarketIntelligenceOptimizationResearchInputError("PRODUCTIVE_JOIN_FORBIDDEN")
    if request.requested_mv2_dp_binding or request.requested_cap23_binding:
        raise MarketIntelligenceOptimizationResearchInputError("TRADING_BINDING_FORBIDDEN")

    legacy_ack = None
    if request.legacy_learning_evidence is not None:
        legacy_ack = validate_canonical_optimization_universe_learning_input_v1(
            CanonicalOptimizationUniverseLearningInputRequestV1(
                learning_evidence=request.legacy_learning_evidence
            )
        )

    mi = request.market_intelligence_research_evidence
    if mi is None:
        return MappingProxyType(
            _result(STATUS_REJECTED, "MISSING_MI_RESEARCH_EVIDENCE", legacy_ack)
        )

    if mi.get("schema_version") != MI_RESEARCH_SCHEMA_VERSION:
        return MappingProxyType(_result(STATUS_REJECTED, "MI_RESEARCH_SCHEMA_MISMATCH", legacy_ack))
    if mi.get("evidence_class") != EVIDENCE_CLASS_MI_RESEARCH:
        return MappingProxyType(_result(STATUS_REJECTED, "MI_EVIDENCE_CLASS_INVALID", legacy_ack))
    if mi.get("productive_authority") != "NONE":
        return MappingProxyType(
            _result(STATUS_REJECTED, "MI_PRODUCTIVE_AUTHORITY_FORBIDDEN", legacy_ack)
        )

    digest = str(mi.get("content_digest") or "")
    body = {
        "schema_version": SCHEMA_VERSION,
        "domain": MI_OPTIMIZATION_INPUT_DOMAIN,
        "status": STATUS_ACCEPTED,
        "reason": "OFFLINE_MI_RESEARCH_INPUT_ONLY",
        "optimization_productive_authority": OPTIMIZATION_PRODUCTIVE_AUTHORITY,
        "mi_research_evidence_digest": digest,
        "legacy_learning_input_ack": dict(legacy_ack) if legacy_ack is not None else None,
        "can_promote": False,
        "can_mutate_mv2_dp": False,
        "can_bind_cap23": False,
    }
    body["result_digest"] = compute_content_hash_v0(body)
    return MappingProxyType(body)


def _result(status: str, reason: str, legacy_ack: Mapping[str, Any] | None) -> dict[str, Any]:
    body = {
        "schema_version": SCHEMA_VERSION,
        "domain": MI_OPTIMIZATION_INPUT_DOMAIN,
        "status": status,
        "reason": reason,
        "optimization_productive_authority": OPTIMIZATION_PRODUCTIVE_AUTHORITY,
        "mi_research_evidence_digest": None,
        "legacy_learning_input_ack": dict(legacy_ack) if legacy_ack is not None else None,
        "can_promote": False,
        "can_mutate_mv2_dp": False,
        "can_bind_cap23": False,
    }
    body["result_digest"] = compute_content_hash_v0(body)
    return body
