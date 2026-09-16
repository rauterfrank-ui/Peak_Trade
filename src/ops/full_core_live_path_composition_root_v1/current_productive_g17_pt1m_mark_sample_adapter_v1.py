"""Full-Core thin adapter: finalized OKX PT1M mark-price candles -> G17 fields.

Reuses economic_md ``parse_okx_mark_candles_v1`` and
``select_finalized_contiguous_pt1m_marks_v1`` as library primitives only.
Does not schedule the economic_md producer, bind CMC, persist typed-vol
state, own HardeningSession/SideState, or change Master-V2 formulas.

RUNTIME_AUTHORIZATION_EFFECT=NONE
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Sequence

from src.ops.economic_md_input_producer_v1.constants_v1 import (
    CMC_AUTHORITY_TRANSFERRED,
    ECONOMIC_MD_PRODUCER_PRODUCTIVELY_SCHEDULED,
    LIBRARY_REUSE_AUTHORITY_TRANSFER,
    MARK_BAR,
    MARK_ENDPOINT_PATH,
    MARK_HISTORY_LIMIT,
    MINIMUM_FINALIZED_PT1M_MARKS,
)
from src.ops.economic_md_input_producer_v1.models_v1 import (
    FinalizedPt1mMarkObservationV1 as EconomicMdFinalizedPt1mMarkObservationV1,
)
from src.ops.economic_md_input_producer_v1.public_md_source_v1 import (
    EconomicMdPublicSourceError,
    parse_okx_mark_candles_v1,
)
from src.ops.economic_md_input_producer_v1.reason_codes_v1 import EconomicMdFailureCodeV1
from src.ops.economic_md_input_producer_v1.validation_v1 import (
    select_finalized_contiguous_pt1m_marks_v1,
)

PACKAGE_MARKER = "FULL_CORE_G17_PT1M_MARK_SAMPLE_ADAPTER_V1=true"
ADAPTER_OWNER = (
    "ops.full_core_live_path_composition_root_v1.current_productive_g17_pt1m_mark_sample_adapter_v1"
)
ENDPOINT_HISTORY_MARK_PRICE_CANDLES = MARK_ENDPOINT_PATH
MARK_HISTORY_BAR = MARK_BAR
MARK_HISTORY_LIMIT_PARAM = MARK_HISTORY_LIMIT
COLD_START_FINALIZED_PT1M_MARK_COUNT = MINIMUM_FINALIZED_PT1M_MARKS
FORBIDDEN_MARK_SOURCE_ENDPOINTS = frozenset(
    {
        "/api/v5/market/candles",
        "/api/v5/market/history-candles",
        "/api/v5/public/mark-price",
    }
)
MARKET_CANDLE_MIN_COLUMNS = 9
ECONOMIC_MD_PRODUCER_SCHEDULED_BY_ADAPTER = False
CMC_BINDING_PERFORMED = False
TYPED_VOL_HOST_PERSISTENCE_PERFORMED = False
PRESENCE_GATE_MUTATED = False

if ECONOMIC_MD_PRODUCER_PRODUCTIVELY_SCHEDULED is True:
    raise RuntimeError("ECONOMIC_MD_PRODUCER_SCHEDULE_LEAKAGE")
if LIBRARY_REUSE_AUTHORITY_TRANSFER is True:
    raise RuntimeError("LIBRARY_REUSE_AUTHORITY_TRANSFER_LEAKAGE")
if CMC_AUTHORITY_TRANSFERRED is True:
    raise RuntimeError("CMC_AUTHORITY_TRANSFER_LEAKAGE")


class FullCoreG17MarkSampleAdapterError(ValueError):
    """Fail-closed Full-Core mark-sample extraction / identity violation."""

    def __init__(self, reason_code: str, detail: str = "") -> None:
        self.reason_code = reason_code
        self.detail = detail
        super().__init__(f"{reason_code}:{detail}" if detail else reason_code)


@dataclass(frozen=True)
class FullCoreG17Pt1mMarkIngestFieldsV1:
    """Explicit G17 ingest kwargs. Not a G17 DTO and not an economic_md DTO."""

    venue: str
    canonical_instrument_id: str
    venue_instrument_id: str
    event_time_unix_seconds: float
    mark_price: float
    is_final: bool


@dataclass(frozen=True)
class FullCoreG17Pt1mMarkExtractionResultV1:
    samples: tuple[FullCoreG17Pt1mMarkIngestFieldsV1, ...]
    failure_codes: tuple[str, ...]
    source_endpoint: str
    bar: str
    limit: str


def refuse_forbidden_mark_source_endpoint_v1(source_endpoint: str) -> str:
    path = str(source_endpoint or "").split("?", 1)[0].strip()
    if not path.startswith("/"):
        path = "/" + path
    if path in FORBIDDEN_MARK_SOURCE_ENDPOINTS:
        raise FullCoreG17MarkSampleAdapterError(
            "FORBIDDEN_MARK_SOURCE_ENDPOINT",
            path,
        )
    if path != ENDPOINT_HISTORY_MARK_PRICE_CANDLES:
        raise FullCoreG17MarkSampleAdapterError(
            "MARK_SOURCE_ENDPOINT_MISMATCH",
            path,
        )
    return path


def refuse_homonym_dto_as_g17_sample_v1(obj: Any) -> None:
    """Homonym economic_md DTO is not a G17 ``sample=`` identity."""
    if isinstance(obj, EconomicMdFinalizedPt1mMarkObservationV1):
        raise FullCoreG17MarkSampleAdapterError("HOMONYM_DTO_IS_NOT_G17_SAMPLE")
    if isinstance(obj, Mapping) and "mark_px" in obj and "event_timestamp" in obj:
        raise FullCoreG17MarkSampleAdapterError("HOMONYM_MAPPING_IS_NOT_G17_SAMPLE")


def g17_ingest_kwargs_from_extracted_sample_v1(
    sample: FullCoreG17Pt1mMarkIngestFieldsV1,
) -> dict[str, Any]:
    """Explicit kwargs for ``ingest_finalized_pt1m_mark_sample_v1``. No DTO cast."""
    refuse_homonym_dto_as_g17_sample_v1(sample)
    if not isinstance(sample, FullCoreG17Pt1mMarkIngestFieldsV1):
        raise FullCoreG17MarkSampleAdapterError("INGEST_FIELDS_TYPE_MISMATCH")
    if sample.is_final is not True:
        raise FullCoreG17MarkSampleAdapterError("UNFINALIZED_SAMPLE_REJECTED")
    return {
        "venue": str(sample.venue),
        "canonical_instrument_id": str(sample.canonical_instrument_id),
        "venue_instrument_id": str(sample.venue_instrument_id),
        "event_time_unix_seconds": float(sample.event_time_unix_seconds),
        "mark_price": float(sample.mark_price),
        "is_final": True,
    }


def _refuse_market_candle_row_shape_v1(payload: Mapping[str, Any]) -> None:
    data = payload.get("data")
    if not isinstance(data, list):
        return
    for index, item in enumerate(data):
        if not isinstance(item, Sequence) or isinstance(item, (str, bytes)):
            continue
        if len(item) >= MARKET_CANDLE_MIN_COLUMNS:
            raise FullCoreG17MarkSampleAdapterError(
                "MARKET_CANDLE_CLOSE_SUBSTITUTION_FORBIDDEN",
                str(index),
            )


def _map_observation_to_ingest_fields_v1(
    observation: EconomicMdFinalizedPt1mMarkObservationV1,
    *,
    venue: str,
    canonical_instrument_id: str,
    venue_instrument_id: str,
) -> FullCoreG17Pt1mMarkIngestFieldsV1:
    event_time_unix_seconds = int(str(observation.event_timestamp).strip()) / 1000.0
    mark_price = float(observation.mark_px)
    if event_time_unix_seconds <= 0.0 or mark_price <= 0.0:
        raise FullCoreG17MarkSampleAdapterError("INVALID_NATIVE_MARK_SAMPLE_FIELDS")
    return FullCoreG17Pt1mMarkIngestFieldsV1(
        venue=venue,
        canonical_instrument_id=canonical_instrument_id,
        venue_instrument_id=venue_instrument_id,
        event_time_unix_seconds=event_time_unix_seconds,
        mark_price=mark_price,
        is_final=True,
    )


def extract_full_core_g17_pt1m_mark_ingest_fields_v1(
    payload: Mapping[str, Any] | None,
    *,
    venue: str,
    canonical_instrument_id: str,
    venue_instrument_id: str,
    receive_or_capture_timestamp: str,
    source_endpoint: str = ENDPOINT_HISTORY_MARK_PRICE_CANDLES,
) -> FullCoreG17Pt1mMarkExtractionResultV1:
    """Parse/select finalized mark-price candles and map explicit G17 ingest fields."""
    endpoint = refuse_forbidden_mark_source_endpoint_v1(source_endpoint)
    bound_venue = str(venue or "").strip()
    bound_canon = str(canonical_instrument_id or "").strip()
    bound_native = str(venue_instrument_id or "").strip()
    if not bound_venue or not bound_canon or not bound_native:
        return FullCoreG17Pt1mMarkExtractionResultV1(
            samples=(),
            failure_codes=("BOUND_INSTRUMENT_IDENTITY_INCOMPLETE",),
            source_endpoint=endpoint,
            bar=MARK_HISTORY_BAR,
            limit=MARK_HISTORY_LIMIT_PARAM,
        )
    if payload is None or not isinstance(payload, Mapping):
        return FullCoreG17Pt1mMarkExtractionResultV1(
            samples=(),
            failure_codes=(EconomicMdFailureCodeV1.PUBLIC_MD_SOURCE_UNAVAILABLE.value,),
            source_endpoint=endpoint,
            bar=MARK_HISTORY_BAR,
            limit=MARK_HISTORY_LIMIT_PARAM,
        )
    try:
        _refuse_market_candle_row_shape_v1(payload)
        raw_marks = parse_okx_mark_candles_v1(
            payload,
            venue_native_id=bound_native,
            receive_or_capture_timestamp=str(receive_or_capture_timestamp),
        )
        selected, codes = select_finalized_contiguous_pt1m_marks_v1(raw_marks)
    except FullCoreG17MarkSampleAdapterError as exc:
        return FullCoreG17Pt1mMarkExtractionResultV1(
            samples=(),
            failure_codes=(exc.reason_code,),
            source_endpoint=endpoint,
            bar=MARK_HISTORY_BAR,
            limit=MARK_HISTORY_LIMIT_PARAM,
        )
    except EconomicMdPublicSourceError as exc:
        return FullCoreG17Pt1mMarkExtractionResultV1(
            samples=(),
            failure_codes=(str(exc.failure_code),),
            source_endpoint=endpoint,
            bar=MARK_HISTORY_BAR,
            limit=MARK_HISTORY_LIMIT_PARAM,
        )
    if codes:
        return FullCoreG17Pt1mMarkExtractionResultV1(
            samples=(),
            failure_codes=tuple(str(code) for code in codes),
            source_endpoint=endpoint,
            bar=MARK_HISTORY_BAR,
            limit=MARK_HISTORY_LIMIT_PARAM,
        )
    samples: list[FullCoreG17Pt1mMarkIngestFieldsV1] = []
    try:
        for observation in selected:
            mapped = _map_observation_to_ingest_fields_v1(
                observation,
                venue=bound_venue,
                canonical_instrument_id=bound_canon,
                venue_instrument_id=bound_native,
            )
            if samples and mapped.event_time_unix_seconds <= samples[-1].event_time_unix_seconds:
                raise FullCoreG17MarkSampleAdapterError("EVENT_TIME_NOT_OLDEST_TO_NEWEST")
            samples.append(mapped)
    except FullCoreG17MarkSampleAdapterError as exc:
        return FullCoreG17Pt1mMarkExtractionResultV1(
            samples=(),
            failure_codes=(exc.reason_code,),
            source_endpoint=endpoint,
            bar=MARK_HISTORY_BAR,
            limit=MARK_HISTORY_LIMIT_PARAM,
        )
    if len(samples) != COLD_START_FINALIZED_PT1M_MARK_COUNT:
        return FullCoreG17Pt1mMarkExtractionResultV1(
            samples=(),
            failure_codes=(EconomicMdFailureCodeV1.INSUFFICIENT_FINALIZED_PT1M_MARKS.value,),
            source_endpoint=endpoint,
            bar=MARK_HISTORY_BAR,
            limit=MARK_HISTORY_LIMIT_PARAM,
        )
    return FullCoreG17Pt1mMarkExtractionResultV1(
        samples=tuple(samples),
        failure_codes=(),
        source_endpoint=endpoint,
        bar=MARK_HISTORY_BAR,
        limit=MARK_HISTORY_LIMIT_PARAM,
    )


def mark_history_get_query_v1(*, venue_native_id: str) -> dict[str, str]:
    return {
        "instId": str(venue_native_id or "").strip(),
        "bar": MARK_HISTORY_BAR,
        "limit": MARK_HISTORY_LIMIT_PARAM,
    }
