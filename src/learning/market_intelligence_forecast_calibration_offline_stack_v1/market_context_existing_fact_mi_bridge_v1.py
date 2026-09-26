"""MI offline bridge for Phase 18 existing-fact MARKET_CONTEXT_V1 (no runtime effect)."""

from __future__ import annotations

from typing import Any, Mapping

from src.learning.market_intelligence_forecast_calibration_offline_stack_v1.constants_v1 import (
    EXTERNAL_EFFECT_AUTHORIZED,
    RUNTIME_REACHABILITY,
)
from src.learning.market_intelligence_forecast_calibration_offline_stack_v1.market_context_existing_fact_materialization_v1 import (
    ExistingFactMaterializationRequestV1,
    materialize_market_context_v1_from_existing_facts_v1,
    replay_market_context_serialization_v1,
)


def attach_market_context_to_mi_offline_cycle_v1(
    *,
    request: ExistingFactMaterializationRequestV1,
) -> dict[str, Any]:
    """Compose market context for MI/Learning offline evidence (observation-only)."""
    if EXTERNAL_EFFECT_AUTHORIZED or RUNTIME_REACHABILITY != "OFFLINE_ONLY":
        raise ValueError("MI_MARKET_CONTEXT_BRIDGE_RUNTIME_FORBIDDEN")
    record = dict(materialize_market_context_v1_from_existing_facts_v1(request))
    return {
        "bridge": "market_context_existing_fact_mi_bridge_v1",
        "market_context_authority": record["market_context_authority"],
        "context_id": record["context_id"],
        "information_set_ref": record["information_set_ref"],
        "serialized_market_context": replay_market_context_serialization_v1(record),
        "external_effect_authorized": False,
        "promotion_authority": "NONE",
        "selection_authority": "NONE",
    }


def read_market_context_from_mi_bridge_payload_v1(payload: Mapping[str, Any]) -> str:
    serialized = payload.get("serialized_market_context")
    if not isinstance(serialized, str) or not serialized.strip():
        raise ValueError("MI_BRIDGE_SERIALIZED_CONTEXT_MISSING")
    return serialized
