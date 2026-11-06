"""Selective Feature Engine v1 — GOVERNED_SUPPORTING, inactive, fail-closed.

Justified work: normalize I25 and CMC contract pointers into FeatureContractRecordV1.
Does not activate into the productive trading call graph, does not enforce max-age,
does not wire research feeders into core/suitability, and does not bypass SSOT.
"""

from __future__ import annotations

from types import MappingProxyType
from typing import Any, Mapping

from src.features.canonical_feature_data_contract_layer_v1.catalog_v1 import catalog_entry
from src.features.canonical_feature_data_contract_layer_v1.constants_v1 import (
    ACTIVATED,
    ALT_DATA_CORE_CONSUMER_ALLOWED,
    JUSTIFIED_PRODUCER_IDS,
    MAX_AGE_CAN_BLOCK_CANARY,
    MAX_AGE_CAN_BLOCK_TRADING,
    MAX_AGE_CAN_CHANGE_EXECUTION,
    MAX_AGE_CAN_CHANGE_PROMOTION,
    MAX_AGE_CAN_CHANGE_RISK_DECISIONS,
    MAX_AGE_CAN_CHANGE_SELECTION,
    MAX_AGE_ENFORCEMENT_ENABLED,
    MAX_AGE_PRODUCTIVE_GATE,
    MAX_AGE_ROLE,
    RESEARCH_FEEDER_IDS,
    RUNTIME_EFFECT,
    SSOT_BYPASS_ALLOWED,
    VOLATILITY_NUMERIC_MAX_AGE_ENFORCING,
)
from src.features.canonical_feature_data_contract_layer_v1.models_v1 import (
    ConsumerIntent,
    FeatureContractRecordV1,
    FeatureDataContractLayerError,
)
from src.features.canonical_feature_data_contract_layer_v1.producer_normalization_v1 import (
    normalize_justified_producer_v1,
)

_FORBIDDEN_INTENTS = frozenset(
    {
        ConsumerIntent.CORE_DECISION,
        ConsumerIntent.SUITABILITY,
        ConsumerIntent.PROMOTION,
        ConsumerIntent.REGIME_CLASSIFIER,
        ConsumerIntent.DASHBOARD,
        ConsumerIntent.EXECUTION,
        ConsumerIntent.MAX_AGE_ENFORCE,
        ConsumerIntent.ACTIVATE_ENGINE,
        ConsumerIntent.SSOT_BYPASS,
    }
)


def _reject(message: str) -> None:
    raise FeatureDataContractLayerError(message)


def assert_engine_inactive_v1() -> None:
    if ACTIVATED is not False:
        _reject("engine_activated")
    if RUNTIME_EFFECT is not False:
        _reject("engine_runtime_effect")
    if VOLATILITY_NUMERIC_MAX_AGE_ENFORCING is not False:
        _reject("max_age_enforcing")
    if MAX_AGE_ENFORCEMENT_ENABLED is not False:
        _reject("max_age_enforcement_enabled")
    if MAX_AGE_ROLE != "WATCHDOG_ONLY":
        _reject("max_age_role_not_watchdog_only")
    if MAX_AGE_PRODUCTIVE_GATE is not False:
        _reject("max_age_productive_gate")
    if (
        MAX_AGE_CAN_BLOCK_TRADING
        or MAX_AGE_CAN_BLOCK_CANARY
        or MAX_AGE_CAN_CHANGE_SELECTION
        or MAX_AGE_CAN_CHANGE_RISK_DECISIONS
        or MAX_AGE_CAN_CHANGE_EXECUTION
        or MAX_AGE_CAN_CHANGE_PROMOTION
    ):
        _reject("max_age_productive_effect_claimed")
    if SSOT_BYPASS_ALLOWED is not False:
        _reject("ssot_bypass_allowed")
    if ALT_DATA_CORE_CONSUMER_ALLOWED is not False:
        _reject("alt_data_core_consumer_allowed")


def assert_consumer_intent_admissible_v1(*, feature_id: str, intent: ConsumerIntent) -> None:
    assert_engine_inactive_v1()
    if intent in _FORBIDDEN_INTENTS:
        _reject(f"consumer_intent_forbidden:{intent.value}:{feature_id}")
    if intent is ConsumerIntent.NORMALIZE and feature_id not in JUSTIFIED_PRODUCER_IDS:
        _reject(f"producer_not_justified_for_normalization:{feature_id}")
    if feature_id in RESEARCH_FEEDER_IDS and intent is not ConsumerIntent.CATALOG:
        _reject(f"research_feeder_non_catalog_intent:{feature_id}:{intent.value}")
    entry = catalog_entry(feature_id)
    if intent is ConsumerIntent.NORMALIZE and entry.equivalent_to_embedded_ta:
        _reject(f"embedded_ta_claimed_equivalent:{feature_id}")


def run_selective_engine_v1(
    *,
    feature_id: str,
    intent: ConsumerIntent,
) -> FeatureContractRecordV1:
    assert_consumer_intent_admissible_v1(feature_id=feature_id, intent=intent)
    if intent is ConsumerIntent.CATALOG:
        _reject("catalog_intent_does_not_emit_record")
    return normalize_justified_producer_v1(feature_id)


def engine_status_v1() -> Mapping[str, Any]:
    assert_engine_inactive_v1()
    return MappingProxyType(
        {
            "activated": ACTIVATED,
            "justified_producer_ids": list(JUSTIFIED_PRODUCER_IDS),
            "max_age_can_block_canary": MAX_AGE_CAN_BLOCK_CANARY,
            "max_age_enforcing": VOLATILITY_NUMERIC_MAX_AGE_ENFORCING,
            "max_age_enforcement_enabled": MAX_AGE_ENFORCEMENT_ENABLED,
            "max_age_productive_gate": MAX_AGE_PRODUCTIVE_GATE,
            "max_age_role": MAX_AGE_ROLE,
            "productive_call_graph_hooked": False,
            "research_feeder_core_consumer_allowed": ALT_DATA_CORE_CONSUMER_ALLOWED,
            "runtime_effect": RUNTIME_EFFECT,
            "ssot_bypass_allowed": SSOT_BYPASS_ALLOWED,
            "trading_authority": False,
        }
    )
