"""UQ6 catalog: schemas, producers, freshness, lineage, consumer rights.

Inventories ratified UQ6-affected features and Class A decision surfaces.
Does not wire research feeders into suitability/core.
"""

from __future__ import annotations

from types import MappingProxyType
from typing import Mapping

from src.features.canonical_feature_data_contract_layer_v1.constants_v1 import (
    CLASS_A_DECISION_SURFACES,
    CMC_FEATURE_CONTRACT_VERSION,
    CMC_FEATURE_ID,
    I25_CONTRACT_OWNER,
    I25_FEATURE_ID,
    RESEARCH_FEEDER_IDS,
    UQ6_AFFECTED_FEATURE_IDS,
)
from src.features.canonical_feature_data_contract_layer_v1.models_v1 import (
    AuthorityClass,
    ConsumerRightsV1,
    FeatureCatalogEntryV1,
    FeatureDataContractLayerError,
    ProducerStatus,
    forbidden_consumer_rights,
    watchdog_freshness_policy,
)

_FRESHNESS = watchdog_freshness_policy()
_NO_CONSUMER = forbidden_consumer_rights()
_I25_RIGHTS = ConsumerRightsV1(
    core_decision=True,
    suitability=False,
    promotion=False,
    regime_classifier=False,
    dashboard_authority=False,
    execution_authority=False,
)
_CMC_RIGHTS = ConsumerRightsV1(
    core_decision=True,
    suitability=False,
    promotion=False,
    regime_classifier=False,
    dashboard_authority=False,
    execution_authority=False,
)


def _entry(
    *,
    feature_id: str,
    intent_id: str,
    display_name: str,
    authority_class: AuthorityClass,
    producer_status: ProducerStatus,
    producer_owner: str,
    notes: str,
    consumer_rights: ConsumerRightsV1 | None = None,
    equivalent_to_embedded_ta: bool = False,
) -> FeatureCatalogEntryV1:
    return FeatureCatalogEntryV1(
        feature_id=feature_id,
        intent_id=intent_id,
        display_name=display_name,
        authority_class=authority_class,
        producer_status=producer_status,
        consumer_rights=consumer_rights or _NO_CONSUMER,
        freshness=_FRESHNESS,
        schema_id=f"canonical_feature_data_contract_layer_v1/{feature_id}",
        producer_owner=producer_owner,
        equivalent_to_embedded_ta=equivalent_to_embedded_ta,
        notes=notes,
    )


_CATALOG_TUPLE: tuple[FeatureCatalogEntryV1, ...] = (
    _entry(
        feature_id="I03_FEATURE_CONTRACT_LAYER",
        intent_id="I03",
        display_name="Feature/Data Contract Layer",
        authority_class=AuthorityClass.CONTRACT_LAYER,
        producer_status=ProducerStatus.CATALOG_ONLY,
        producer_owner="features.canonical_feature_data_contract_layer_v1",
        notes="UQ6 CORE contract layer; not trading authority",
    ),
    _entry(
        feature_id="I03_FEATURE_ENGINE_STAGED",
        intent_id="I03",
        display_name="Feature Engine (staged/supporting)",
        authority_class=AuthorityClass.GOVERNED_SUPPORTING_ENGINE,
        producer_status=ProducerStatus.STAGED_ENGINE_INACTIVE,
        producer_owner="features.canonical_feature_data_contract_layer_v1.selective_engine_v1",
        notes="Selective engine only where justified; ACTIVATED=false",
    ),
    _entry(
        feature_id="I07_MAX_AGE_DIAGNOSTIC",
        intent_id="I07",
        display_name="Numeric max-age watchdog (non-enforcing)",
        authority_class=AuthorityClass.WATCHDOG_ONLY,
        producer_status=ProducerStatus.WATCHDOG_ONLY,
        producer_owner="Owner MAX_AGE_ROLE=WATCHDOG_ONLY",
        notes=(
            "WATCHDOG_ONLY / NON_ENFORCING; observation/telemetry/audit/evidence/"
            "warnings/research only; not a productive gate; separate from I25/CMC"
        ),
    ),
    _entry(
        feature_id=I25_FEATURE_ID,
        intent_id="I25",
        display_name="Typed volatility_estimate → CMC",
        authority_class=AuthorityClass.CANONICAL_FEATURE_INPUT,
        producer_status=ProducerStatus.JUSTIFIED_REUSE,
        producer_owner=I25_CONTRACT_OWNER,
        notes="Narrow EQUIV_PROVEN; not regime-classifier authority",
        consumer_rights=_I25_RIGHTS,
    ),
    _entry(
        feature_id=CMC_FEATURE_ID,
        intent_id="I03",
        display_name="CanonicalMarketContext feature contract",
        authority_class=AuthorityClass.CANONICAL_FEATURE_INPUT,
        producer_status=ProducerStatus.JUSTIFIED_REUSE,
        producer_owner="trading.master_v2.canonical_market_context_v1",
        notes=f"Pointer-only reuse of {CMC_FEATURE_CONTRACT_VERSION}; no CMC rebuild",
        consumer_rights=_CMC_RIGHTS,
    ),
    _entry(
        feature_id="I04_SENTIMENT_NEWS_ONCHAIN",
        intent_id="I04",
        display_name="Sentiment / news / onchain",
        authority_class=AuthorityClass.RESEARCH_FEEDER,
        producer_status=ProducerStatus.RESEARCH_FEEDER_NO_CORE_CONSUMER,
        producer_owner="unwired",
        notes="RESEARCH_FEEDER until Suitability consumer contract exists",
    ),
    _entry(
        feature_id="I05_ORDERBOOK_TICK",
        intent_id="I05",
        display_name="Orderbook / tick",
        authority_class=AuthorityClass.RESEARCH_FEEDER,
        producer_status=ProducerStatus.RESEARCH_FEEDER_NO_CORE_CONSUMER,
        producer_owner="unwired",
        notes="RESEARCH_FEEDER until consumer contract exists",
    ),
    _entry(
        feature_id="I38_WS_MARKET_STREAMS",
        intent_id="I38",
        display_name="WebSocket market streams",
        authority_class=AuthorityClass.CANONICAL_MD_LATER,
        producer_status=ProducerStatus.CATALOG_ONLY,
        producer_owner="unwired",
        notes="Not R1; REST MD remains current public-MD path",
    ),
    _entry(
        feature_id="I40_REGIME_ADAPTIVE_PARAMS",
        intent_id="I40",
        display_name="Regime-adaptive parameters",
        authority_class=AuthorityClass.GATED_META_INPUT,
        producer_status=ProducerStatus.CATALOG_ONLY,
        producer_owner="regime pipeline (non-auto-tune SSOT)",
        notes="Gated meta; not produced by I03 engine; no auto-tune",
    ),
    _entry(
        feature_id="I55_MACRO_REGIMES",
        intent_id="I55",
        display_name="Macro regimes",
        authority_class=AuthorityClass.RESEARCH_FEEDER,
        producer_status=ProducerStatus.RESEARCH_FEEDER_NO_CORE_CONSUMER,
        producer_owner="unwired",
        notes="RESEARCH_FEEDER; no core consumer",
    ),
    _entry(
        feature_id="I76_PSYCHOLOGY_FEATURES",
        intent_id="I76",
        display_name="Psychology features",
        authority_class=AuthorityClass.RESEARCH_FEEDER,
        producer_status=ProducerStatus.RESEARCH_FEEDER_NO_CORE_CONSUMER,
        producer_owner="src/reporting/psychology_*.py orphan",
        notes="RESEARCH_FEEDER / orphan; not core",
        equivalent_to_embedded_ta=False,
    ),
)

FEATURE_CATALOG: Mapping[str, FeatureCatalogEntryV1] = MappingProxyType(
    {entry.feature_id: entry for entry in _CATALOG_TUPLE}
)


def catalog_entry(feature_id: str) -> FeatureCatalogEntryV1:
    entry = FEATURE_CATALOG.get(feature_id)
    if entry is None:
        raise FeatureDataContractLayerError(f"unknown_feature_id:{feature_id}")
    return entry


def require_complete_uq6_catalog() -> None:
    present = frozenset(FEATURE_CATALOG)
    expected = frozenset(UQ6_AFFECTED_FEATURE_IDS)
    if present != expected:
        missing = sorted(expected - present)
        extra = sorted(present - expected)
        raise FeatureDataContractLayerError(
            f"uq6_catalog_incomplete:missing={missing}:extra={extra}"
        )
    for feeder_id in RESEARCH_FEEDER_IDS:
        entry = catalog_entry(feeder_id)
        rights = entry.consumer_rights
        if (
            rights.core_decision
            or rights.suitability
            or rights.promotion
            or rights.regime_classifier
            or rights.dashboard_authority
            or rights.execution_authority
        ):
            raise FeatureDataContractLayerError(
                f"research_feeder_consumer_rights_not_forbidden:{feeder_id}"
            )
    if len(CLASS_A_DECISION_SURFACES) != 13:
        raise FeatureDataContractLayerError(
            f"class_a_inventory_count_mismatch:{len(CLASS_A_DECISION_SURFACES)}"
        )
    assert_i07_watchdog_only_v1()


def assert_i07_watchdog_only_v1() -> None:
    entry = catalog_entry("I07_MAX_AGE_DIAGNOSTIC")
    if entry.authority_class is not AuthorityClass.WATCHDOG_ONLY:
        raise FeatureDataContractLayerError("i07_authority_class_not_watchdog_only")
    if entry.producer_status is not ProducerStatus.WATCHDOG_ONLY:
        raise FeatureDataContractLayerError("i07_producer_status_not_watchdog_only")
    freshness = entry.freshness
    if freshness.max_age_role != "WATCHDOG_ONLY":
        raise FeatureDataContractLayerError("i07_max_age_role_not_watchdog_only")
    if freshness.max_age_effect != "WATCHDOG_ONLY":
        raise FeatureDataContractLayerError("i07_max_age_effect_not_watchdog_only")
    if freshness.max_age_enforcing is not False:
        raise FeatureDataContractLayerError("i07_max_age_enforcing")
    if freshness.productive_gate is not False:
        raise FeatureDataContractLayerError("i07_productive_gate")
    if (
        freshness.can_block_trading
        or freshness.can_block_canary
        or freshness.can_change_selection
        or freshness.can_change_risk_decisions
        or freshness.can_change_execution
        or freshness.can_change_promotion
    ):
        raise FeatureDataContractLayerError("i07_productive_effect_claimed")
    rights = entry.consumer_rights
    if (
        rights.core_decision
        or rights.suitability
        or rights.promotion
        or rights.regime_classifier
        or rights.dashboard_authority
        or rights.execution_authority
    ):
        raise FeatureDataContractLayerError("i07_consumer_rights_not_forbidden")
