"""Deterministic I04/I05/I55 consumer matrix (read-only, non-activating)."""

from __future__ import annotations

from types import MappingProxyType
from typing import Mapping

from src.features.canonical_alt_data_consumer_boundary_v1.constants_v1 import (
    I04_FEATURE_ID,
    I04_PRODUCER,
    I05_FEATURE_ID,
    I05_PRODUCER,
    I55_FEATURE_ID,
    I55_OUTPUT_SCHEMA,
    I55_PRODUCER,
    TARGET_BINDING,
)
from src.features.canonical_alt_data_consumer_boundary_v1.models_v1 import (
    AltDataConsumerBoundaryError,
    ConsumerClass,
    ConsumerMatrixRowV1,
    PathClass,
)

_B = PathClass.RESEARCH_FEEDER_VALID_NO_CANONICAL_CONSUMER_REQUIRED_YET
_NONE = "NONE"


def _primary(
    *,
    row_id: str,
    source_intent: str,
    producer: str,
    output_schema: str,
    current_consumer: str,
    consumer_class: ConsumerClass,
    duplicate_path_risk: str,
) -> ConsumerMatrixRowV1:
    return ConsumerMatrixRowV1(
        row_id=row_id,
        source_intent=source_intent,
        producer=producer,
        output_schema=output_schema,
        current_consumer=current_consumer,
        consumer_class=consumer_class,
        current_runtime_reachable=False,
        current_authority_effect=_NONE,
        r1_contract_compatible=True,
        r2_suitability_consumer_present=False,
        r3_meta_consumer_present=False,
        promotion_consumer_present=False,
        research_only=True,
        missing_contract=False,
        duplicate_path_risk=duplicate_path_risk,
        recommended_target_binding=TARGET_BINDING,
        path_class=_B,
    )


def _adjacent(
    *,
    row_id: str,
    source_intent: str,
    producer: str,
    output_schema: str,
    current_consumer: str,
    consumer_class: ConsumerClass,
    duplicate_path_risk: str,
    research_only: bool,
) -> ConsumerMatrixRowV1:
    return ConsumerMatrixRowV1(
        row_id=row_id,
        source_intent=source_intent,
        producer=producer,
        output_schema=output_schema,
        current_consumer=current_consumer,
        consumer_class=consumer_class,
        current_runtime_reachable=False,
        current_authority_effect=_NONE,
        r1_contract_compatible=True,
        r2_suitability_consumer_present=False,
        r3_meta_consumer_present=False,
        promotion_consumer_present=False,
        research_only=research_only,
        missing_contract=False,
        duplicate_path_risk=duplicate_path_risk,
        recommended_target_binding="KEEP_SEPARATE_FROM_ALT_DATA_RESEARCH_FEEDER",
        path_class=_B,
    )


CONSUMER_MATRIX: tuple[ConsumerMatrixRowV1, ...] = (
    _primary(
        row_id="I04_PRIMARY",
        source_intent="I04",
        producer=I04_PRODUCER,
        output_schema="NONE",
        current_consumer="R1_CATALOG_ONLY",
        consumer_class=ConsumerClass.RESEARCH_FEEDER_NO_CORE_CONSUMER,
        duplicate_path_risk="NONE",
    ),
    _primary(
        row_id="I05_PRIMARY",
        source_intent="I05",
        producer=I05_PRODUCER,
        output_schema="NONE",
        current_consumer="R1_CATALOG_ONLY",
        consumer_class=ConsumerClass.RESEARCH_FEEDER_NO_CORE_CONSUMER,
        duplicate_path_risk="RESEARCH_VS_EXECUTION_MICROSTRUCTURE_BOUNDARY_DOCUMENTED",
    ),
    _adjacent(
        row_id="I05_VENUE_ORDERBOOK_API",
        source_intent="I05",
        producer="exchange_api_orderbook_intent",
        output_schema="venue_orderbook_fetch",
        current_consumer="src.execution.networked.entry_contract_v1",
        consumer_class=ConsumerClass.EXECUTION_VENUE_MD_FETCH_NOT_FEATURE_CONSUMER,
        duplicate_path_risk="DOCUMENTED_BOUNDARY_NOT_SHARED_AUTHORITY",
        research_only=False,
    ),
    _adjacent(
        row_id="I05_SAFETY_KERNEL_ORDERBOOK_GUARDS",
        source_intent="I05",
        producer="market_data_snapshot_fields",
        output_schema="orderbook_age_ms_and_depth",
        current_consumer="src.meta.learning_loop.independent_pre_trade_safety_kernel_v1",
        consumer_class=ConsumerClass.LEARNING_SAFETY_KERNEL_NOT_I05_FEATURE,
        duplicate_path_risk="DOCUMENTED_BOUNDARY_NOT_SHARED_AUTHORITY",
        research_only=False,
    ),
    _adjacent(
        row_id="I05_BOUCHAUD_OHLCV_PROXY",
        source_intent="I05",
        producer="OHLCV_PROXY_NOT_TRUE_TICK_L2",
        output_schema="research_ohlcv_proxy",
        current_consumer="src.strategies.bouchaud.bouchaud_microstructure_strategy",
        consumer_class=ConsumerClass.RESEARCH_STRATEGY_OHLCV_PROXY_NOT_I05_PRODUCER,
        duplicate_path_risk="DOCUMENTED_BOUNDARY_NOT_I05_PRODUCER",
        research_only=True,
    ),
    _adjacent(
        row_id="I05_SHADOW_TICK_NORMALIZER",
        source_intent="I05",
        producer="kraken_ws_trade_message_parser",
        output_schema="src.data.shadow.models.Tick",
        current_consumer="src.data.feeds.live_feed",
        consumer_class=ConsumerClass.SHADOW_TICK_PARSE_NOT_I05_FEATURE,
        duplicate_path_risk="DOCUMENTED_I38_LIVE_FEED_BOUNDARY_NOT_I05",
        research_only=False,
    ),
    _primary(
        row_id="I55_PRIMARY",
        source_intent="I55",
        producer=I55_PRODUCER,
        output_schema=I55_OUTPUT_SCHEMA,
        current_consumer="tests_only",
        consumer_class=ConsumerClass.RESEARCH_BRIEFING_LOADER_NON_AUTHORITY,
        duplicate_path_risk="LATENT_SIZING_TILT_FIELDS_UNWIRED",
    ),
    _adjacent(
        row_id="I55_BRIEFING_SIZING_TILT",
        source_intent="I55",
        producer=I55_PRODUCER,
        output_schema=I55_OUTPUT_SCHEMA,
        current_consumer="NONE_UNWIRED",
        consumer_class=ConsumerClass.NON_AUTHORITY_BRIEFING_METADATA,
        duplicate_path_risk="LATENT_SIZING_TILT_MUST_NOT_BIND_R3_MV2_DP",
        research_only=True,
    ),
)

PRIMARY_ROW_IDS = ("I04_PRIMARY", "I05_PRIMARY", "I55_PRIMARY")
KNOWN_PRODUCERS = frozenset(row.producer for row in CONSUMER_MATRIX)
KNOWN_SCHEMAS = frozenset(row.output_schema for row in CONSUMER_MATRIX)
KNOWN_CONSUMERS = frozenset(row.current_consumer for row in CONSUMER_MATRIX)
KNOWN_ROW_IDS = frozenset(row.row_id for row in CONSUMER_MATRIX)
R1_FEATURE_IDS = (I04_FEATURE_ID, I05_FEATURE_ID, I55_FEATURE_ID)


def matrix_by_row_id() -> Mapping[str, ConsumerMatrixRowV1]:
    return MappingProxyType({row.row_id: row for row in CONSUMER_MATRIX})


def require_row(row_id: str) -> ConsumerMatrixRowV1:
    try:
        return matrix_by_row_id()[row_id]
    except KeyError as exc:
        raise AltDataConsumerBoundaryError(f"unknown_consumer_row:{row_id}") from exc


def require_producer(producer: str) -> None:
    if producer not in KNOWN_PRODUCERS:
        raise AltDataConsumerBoundaryError(f"unknown_producer:{producer}")


def require_schema(schema_id: str) -> None:
    if schema_id not in KNOWN_SCHEMAS:
        raise AltDataConsumerBoundaryError(f"unknown_schema:{schema_id}")


def require_consumer(consumer: str) -> None:
    if consumer not in KNOWN_CONSUMERS:
        raise AltDataConsumerBoundaryError(f"unknown_consumer:{consumer}")


def primary_rows() -> tuple[ConsumerMatrixRowV1, ...]:
    lookup = matrix_by_row_id()
    return tuple(lookup[row_id] for row_id in PRIMARY_ROW_IDS)
