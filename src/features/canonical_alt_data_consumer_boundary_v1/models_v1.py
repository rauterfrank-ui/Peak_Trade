"""Fail-closed models for EG-ALT-CONSUMER consumer-boundary v1."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from types import MappingProxyType
from typing import Any, Mapping


class AltDataConsumerBoundaryError(ValueError):
    """Fail-closed EG-ALT-CONSUMER boundary error."""


class PathClass(str, Enum):
    EXISTING_CONSUMER_CONTRACT_PROVEN = "A"
    RESEARCH_FEEDER_VALID_NO_CANONICAL_CONSUMER_REQUIRED_YET = "B"
    ADDITIVE_NON_ACTIVATING_CONSUMER_CONTRACT_REQUIRED = "C"
    DUPLICATE_OR_BYPASS_PATH_FOUND_FAIL_CLOSED = "D"


class ConsumerClass(str, Enum):
    RESEARCH_FEEDER_NO_CORE_CONSUMER = "RESEARCH_FEEDER_NO_CORE_CONSUMER"
    RESEARCH_BRIEFING_LOADER_NON_AUTHORITY = "RESEARCH_BRIEFING_LOADER_NON_AUTHORITY"
    EXECUTION_VENUE_MD_FETCH_NOT_FEATURE_CONSUMER = "EXECUTION_VENUE_MD_FETCH_NOT_FEATURE_CONSUMER"
    LEARNING_SAFETY_KERNEL_NOT_I05_FEATURE = "LEARNING_SAFETY_KERNEL_NOT_I05_FEATURE"
    RESEARCH_STRATEGY_OHLCV_PROXY_NOT_I05_PRODUCER = (
        "RESEARCH_STRATEGY_OHLCV_PROXY_NOT_I05_PRODUCER"
    )
    SHADOW_TICK_PARSE_NOT_I05_FEATURE = "SHADOW_TICK_PARSE_NOT_I05_FEATURE"
    NON_AUTHORITY_BRIEFING_METADATA = "NON_AUTHORITY_BRIEFING_METADATA"
    FORENSIC_VERIFIER_READ_ONLY = "FORENSIC_VERIFIER_READ_ONLY"


@dataclass(frozen=True)
class ConsumerMatrixRowV1:
    row_id: str
    source_intent: str
    producer: str
    output_schema: str
    current_consumer: str
    consumer_class: ConsumerClass
    current_runtime_reachable: bool
    current_authority_effect: str
    r1_contract_compatible: bool
    r2_suitability_consumer_present: bool
    r3_meta_consumer_present: bool
    promotion_consumer_present: bool
    research_only: bool
    missing_contract: bool
    duplicate_path_risk: str
    recommended_target_binding: str
    path_class: PathClass

    def to_mapping(self) -> Mapping[str, Any]:
        return MappingProxyType(
            {
                "row_id": self.row_id,
                "source_intent": self.source_intent,
                "producer": self.producer,
                "output_schema": self.output_schema,
                "current_consumer": self.current_consumer,
                "consumer_class": self.consumer_class.value,
                "current_runtime_reachable": self.current_runtime_reachable,
                "current_authority_effect": self.current_authority_effect,
                "r1_contract_compatible": self.r1_contract_compatible,
                "r2_suitability_consumer_present": self.r2_suitability_consumer_present,
                "r3_meta_consumer_present": self.r3_meta_consumer_present,
                "promotion_consumer_present": self.promotion_consumer_present,
                "research_only": self.research_only,
                "missing_contract": self.missing_contract,
                "duplicate_path_risk": self.duplicate_path_risk,
                "recommended_target_binding": self.recommended_target_binding,
                "path_class": self.path_class.value,
            }
        )
