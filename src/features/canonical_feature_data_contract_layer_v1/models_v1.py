"""Fail-closed models for the UQ6 Feature/Data Contract Layer v1."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from types import MappingProxyType
from typing import Any, Mapping


class FeatureDataContractLayerError(ValueError):
    """Fail-closed Feature/Data Contract Layer error."""


class AuthorityClass(str, Enum):
    CANONICAL_FEATURE_INPUT = "CANONICAL_FEATURE_INPUT"
    GOVERNED_SUPPORTING_ENGINE = "GOVERNED_SUPPORTING_ENGINE"
    WATCHDOG_ONLY = "WATCHDOG_ONLY"
    RESEARCH_FEEDER = "RESEARCH_FEEDER"
    CANONICAL_DECISION_SURFACE = "CANONICAL_DECISION_SURFACE"
    CANONICAL_MD_LATER = "CANONICAL_MD_LATER"
    GATED_META_INPUT = "GATED_META_INPUT"
    CONTRACT_LAYER = "CONTRACT_LAYER"


class ProducerStatus(str, Enum):
    JUSTIFIED_REUSE = "JUSTIFIED_REUSE"
    CATALOG_ONLY = "CATALOG_ONLY"
    RESEARCH_FEEDER_NO_CORE_CONSUMER = "RESEARCH_FEEDER_NO_CORE_CONSUMER"
    STAGED_ENGINE_INACTIVE = "STAGED_ENGINE_INACTIVE"
    WATCHDOG_ONLY = "WATCHDOG_ONLY"


class ConsumerIntent(str, Enum):
    CATALOG = "CATALOG"
    NORMALIZE = "NORMALIZE"
    CORE_DECISION = "CORE_DECISION"
    SUITABILITY = "SUITABILITY"
    PROMOTION = "PROMOTION"
    REGIME_CLASSIFIER = "REGIME_CLASSIFIER"
    DASHBOARD = "DASHBOARD"
    EXECUTION = "EXECUTION"
    MAX_AGE_ENFORCE = "MAX_AGE_ENFORCE"
    ACTIVATE_ENGINE = "ACTIVATE_ENGINE"
    SSOT_BYPASS = "SSOT_BYPASS"


@dataclass(frozen=True)
class ConsumerRightsV1:
    core_decision: bool
    suitability: bool
    promotion: bool
    regime_classifier: bool
    dashboard_authority: bool
    execution_authority: bool

    def to_mapping(self) -> Mapping[str, bool]:
        return MappingProxyType(
            {
                "core_decision": self.core_decision,
                "suitability": self.suitability,
                "promotion": self.promotion,
                "regime_classifier": self.regime_classifier,
                "dashboard_authority": self.dashboard_authority,
                "execution_authority": self.execution_authority,
            }
        )


def forbidden_consumer_rights() -> ConsumerRightsV1:
    return ConsumerRightsV1(
        core_decision=False,
        suitability=False,
        promotion=False,
        regime_classifier=False,
        dashboard_authority=False,
        execution_authority=False,
    )


@dataclass(frozen=True)
class FreshnessPolicyV1:
    max_age_enforcing: bool
    max_age_effect: str
    max_age_role: str
    stale_behavior: str
    clock_authority: str
    can_block_trading: bool
    can_block_canary: bool
    can_change_selection: bool
    can_change_risk_decisions: bool
    can_change_execution: bool
    can_change_promotion: bool
    productive_gate: bool

    def to_mapping(self) -> Mapping[str, Any]:
        return MappingProxyType(
            {
                "can_block_canary": self.can_block_canary,
                "can_block_trading": self.can_block_trading,
                "can_change_execution": self.can_change_execution,
                "can_change_promotion": self.can_change_promotion,
                "can_change_risk_decisions": self.can_change_risk_decisions,
                "can_change_selection": self.can_change_selection,
                "clock_authority": self.clock_authority,
                "max_age_effect": self.max_age_effect,
                "max_age_enforcing": self.max_age_enforcing,
                "max_age_role": self.max_age_role,
                "productive_gate": self.productive_gate,
                "stale_behavior": self.stale_behavior,
            }
        )


def watchdog_freshness_policy() -> FreshnessPolicyV1:
    return FreshnessPolicyV1(
        max_age_enforcing=False,
        max_age_effect="WATCHDOG_ONLY",
        max_age_role="WATCHDOG_ONLY",
        stale_behavior="OBSERVE_LOG_TELEMETRY_EVIDENCE_ONLY",
        clock_authority="WATCHDOG_ONLY_NON_AUTHORITY",
        can_block_trading=False,
        can_block_canary=False,
        can_change_selection=False,
        can_change_risk_decisions=False,
        can_change_execution=False,
        can_change_promotion=False,
        productive_gate=False,
    )


@dataclass(frozen=True)
class FeatureCatalogEntryV1:
    feature_id: str
    intent_id: str
    display_name: str
    authority_class: AuthorityClass
    producer_status: ProducerStatus
    consumer_rights: ConsumerRightsV1
    freshness: FreshnessPolicyV1
    schema_id: str
    producer_owner: str
    equivalent_to_embedded_ta: bool
    notes: str

    def to_mapping(self) -> Mapping[str, Any]:
        return MappingProxyType(
            {
                "feature_id": self.feature_id,
                "intent_id": self.intent_id,
                "display_name": self.display_name,
                "authority_class": self.authority_class.value,
                "producer_status": self.producer_status.value,
                "consumer_rights": dict(self.consumer_rights.to_mapping()),
                "freshness": dict(self.freshness.to_mapping()),
                "schema_id": self.schema_id,
                "producer_owner": self.producer_owner,
                "equivalent_to_embedded_ta": self.equivalent_to_embedded_ta,
                "notes": self.notes,
            }
        )


@dataclass(frozen=True)
class FeatureContractRecordV1:
    feature_id: str
    schema_id: str
    producer_owner: str
    authority_class: AuthorityClass
    producer_status: ProducerStatus
    consumer_rights: ConsumerRightsV1
    freshness: FreshnessPolicyV1
    lineage_sha256: str
    payload_digest: str
    runtime_effect: bool
    activated: bool
    trading_authority: bool

    def to_mapping(self) -> Mapping[str, Any]:
        return MappingProxyType(
            {
                "feature_id": self.feature_id,
                "schema_id": self.schema_id,
                "producer_owner": self.producer_owner,
                "authority_class": self.authority_class.value,
                "producer_status": self.producer_status.value,
                "consumer_rights": dict(self.consumer_rights.to_mapping()),
                "freshness": dict(self.freshness.to_mapping()),
                "lineage_sha256": self.lineage_sha256,
                "payload_digest": self.payload_digest,
                "runtime_effect": self.runtime_effect,
                "activated": self.activated,
                "trading_authority": self.trading_authority,
            }
        )
