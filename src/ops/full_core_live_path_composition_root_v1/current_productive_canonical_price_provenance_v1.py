"""Canonical CMC mark / index price provenance for CURRENT productive MV2 cycle.

Composition-root adapter only. Does not bind CMC inside Master V2 / Double Play.
Fail-closed when candle.close is presented as canonical M_t.

RUNTIME_AUTHORIZATION_EFFECT=NONE
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping


PRICE_CLASS_CMC_MARK = "CMC_MARK_PRICE"
PRICE_CLASS_INDEX = "INDEX_PRICE"

MARK_SOURCE_OKX_PUBLIC_MARK_PAYLOAD = "OKX_PUBLIC_MARK_PRICE_PAYLOAD"
MARK_SOURCE_CAP24_MARK_SIDECAR = "CAP24_MARK_PRICES_BY_NATIVE_ID_V1"
MARK_SOURCE_EXPLICIT_SYNTHETIC_FIXTURE = "EXPLICIT_SYNTHETIC_FIXTURE_MARK"
INDEX_SOURCE_OKX_MARK_IDX_PX = "OKX_MARK_PAYLOAD_IDX_PX"
INDEX_SOURCE_OKX_TICKER_IDX_PX = "OKX_TICKER_IDX_PX"
INDEX_SOURCE_OKX_INDEX_TICKERS = "OKX_INDEX_TICKERS_IDX_PX"
INDEX_SOURCE_EXPLICIT_TEST_FIXTURE = "EXPLICIT_TEST_FIXTURE_INDEX"

FINALIZATION_CURRENT = "CURRENT"
TEMPORAL_DERIVED_CURRENT = "DERIVED_CURRENT_VALUE"

FORBIDDEN_MARK_SOURCES = frozenset(
    {
        "ORDINARY_MARKET_CANDLE_CLOSE",
        "UNPROVEN",
    }
)


class ProductiveCanonicalPriceProvenanceError(ValueError):
    """Fail-closed canonical price provenance violation."""


@dataclass(frozen=True)
class ProductiveCycleCanonicalPriceProvenanceV1:
    """Explicit provenance for mark_px / index_px entering the productive MV2 cycle."""

    mark_price_class: str
    mark_source: str
    mark_px: float
    index_price_class: str
    index_source: str
    index_px: float
    venue_native_id: str
    mark_finalization_state: str
    mark_temporal_class: str
    index_temporal_class: str

    def validate_against_cycle_inputs_v1(
        self,
        *,
        mark_px: float,
        index_px: float,
        venue_native_id: str,
    ) -> None:
        native = str(venue_native_id or "").strip()
        if native != str(self.venue_native_id or "").strip():
            raise ProductiveCanonicalPriceProvenanceError("CMC_MARK_INSTRUMENT_BINDING_MISMATCH")
        if float(mark_px) != float(self.mark_px):
            raise ProductiveCanonicalPriceProvenanceError("CMC_MARK_PX_PROVENANCE_MISMATCH")
        if float(index_px) != float(self.index_px):
            raise ProductiveCanonicalPriceProvenanceError("INDEX_PX_PROVENANCE_MISMATCH")
        if self.mark_price_class != PRICE_CLASS_CMC_MARK:
            raise ProductiveCanonicalPriceProvenanceError("MARK_PRICE_CLASS_INVALID")
        if self.index_price_class != PRICE_CLASS_INDEX:
            raise ProductiveCanonicalPriceProvenanceError("INDEX_PRICE_CLASS_INVALID")
        if self.mark_source in FORBIDDEN_MARK_SOURCES:
            raise ProductiveCanonicalPriceProvenanceError("CMC_MARK_SOURCE_FORBIDDEN")
        if self.index_source == self.mark_source and self.index_source not in {
            INDEX_SOURCE_EXPLICIT_TEST_FIXTURE,
        }:
            raise ProductiveCanonicalPriceProvenanceError("INDEX_MARK_SOURCE_COLLAPSE_FORBIDDEN")


def build_cmc_mark_provenance_from_okx_mark_price_payload_v1(
    *,
    mark_price_payload: Mapping[str, Any],
    venue_native_id: str,
    index_from_index_tickers: Mapping[str, Any] | None = None,
    index_from_ticker: Mapping[str, Any] | None = None,
) -> ProductiveCycleCanonicalPriceProvenanceV1:
    """Resolve mark/index from OKX-shaped payloads with independent provenance."""

    from src.ops.full_core_live_path_composition_root_v1.current_productive_master_v2_runtime_cycle_v1 import (
        extract_index_px_from_index_tickers_payload_v1,
        extract_mark_and_index_from_payload_v1,
        extract_ticker_fields_v1,
        resolve_index_px_primary_secondary_tertiary_v1,
        resolve_index_ticker_inst_id_v1,
    )

    native = str(venue_native_id or "").strip()
    if not native:
        raise ProductiveCanonicalPriceProvenanceError("VENUE_NATIVE_ID_REQUIRED")
    mark_px, index_from_mark = extract_mark_and_index_from_payload_v1(
        mark_price_payload, native_id=native
    )
    if mark_px is None:
        raise ProductiveCanonicalPriceProvenanceError("CMC_MARK_MISSING_FAIL_CLOSED")
    index_inst = resolve_index_ticker_inst_id_v1(native)
    index_from_index = (
        extract_index_px_from_index_tickers_payload_v1(index_from_index_tickers, wanted=index_inst)
        if index_from_index_tickers is not None
        else None
    )
    index_from_ticker_px = None
    if index_from_ticker is not None:
        _bid, _ask, _vol, index_from_ticker_px = extract_ticker_fields_v1(
            index_from_ticker, native_id=native
        )
    index_px = resolve_index_px_primary_secondary_tertiary_v1(
        index_from_mark=index_from_mark,
        index_from_ticker=index_from_ticker_px,
        index_from_index_tickers=index_from_index,
    )
    if index_px is None:
        raise ProductiveCanonicalPriceProvenanceError("INDEX_PX_MISSING_FAIL_CLOSED")
    index_source = INDEX_SOURCE_OKX_INDEX_TICKERS
    if index_from_mark is not None:
        index_source = INDEX_SOURCE_OKX_MARK_IDX_PX
    elif index_from_ticker_px is not None:
        index_source = INDEX_SOURCE_OKX_TICKER_IDX_PX
    return ProductiveCycleCanonicalPriceProvenanceV1(
        mark_price_class=PRICE_CLASS_CMC_MARK,
        mark_source=MARK_SOURCE_OKX_PUBLIC_MARK_PAYLOAD,
        mark_px=float(mark_px),
        index_price_class=PRICE_CLASS_INDEX,
        index_source=index_source,
        index_px=float(index_px),
        venue_native_id=native,
        mark_finalization_state=FINALIZATION_CURRENT,
        mark_temporal_class=TEMPORAL_DERIVED_CURRENT,
        index_temporal_class=TEMPORAL_DERIVED_CURRENT,
    )


def build_provenance_from_resolved_cmc_mark_and_index_v1(
    *,
    venue_native_id: str,
    mark_px: float,
    index_px: float,
    mark_source: str = MARK_SOURCE_OKX_PUBLIC_MARK_PAYLOAD,
    index_source: str,
) -> ProductiveCycleCanonicalPriceProvenanceV1:
    """Bind already-resolved mark/index scalars with explicit source classes (fail-closed)."""

    native = str(venue_native_id or "").strip()
    if not native:
        raise ProductiveCanonicalPriceProvenanceError("VENUE_NATIVE_ID_REQUIRED")
    if float(mark_px) <= 0 or float(index_px) <= 0:
        raise ProductiveCanonicalPriceProvenanceError("NONPOSITIVE_PRICE_FORBIDDEN")
    if mark_source in FORBIDDEN_MARK_SOURCES:
        raise ProductiveCanonicalPriceProvenanceError("CMC_MARK_SOURCE_FORBIDDEN")
    if (
        str(mark_source) == MARK_SOURCE_OKX_PUBLIC_MARK_PAYLOAD
        and str(index_source) == INDEX_SOURCE_EXPLICIT_TEST_FIXTURE
    ):
        raise ProductiveCanonicalPriceProvenanceError(
            "SYNTHETIC_INDEX_OKX_MARK_SOURCE_COLLAPSE_FORBIDDEN"
        )
    return ProductiveCycleCanonicalPriceProvenanceV1(
        mark_price_class=PRICE_CLASS_CMC_MARK,
        mark_source=str(mark_source),
        mark_px=float(mark_px),
        index_price_class=PRICE_CLASS_INDEX,
        index_source=str(index_source),
        index_px=float(index_px),
        venue_native_id=native,
        mark_finalization_state=FINALIZATION_CURRENT,
        mark_temporal_class=TEMPORAL_DERIVED_CURRENT,
        index_temporal_class=TEMPORAL_DERIVED_CURRENT,
    )


def build_explicit_test_fixture_price_provenance_v1(
    *,
    venue_native_id: str,
    mark_px: float,
    index_px: float,
) -> ProductiveCycleCanonicalPriceProvenanceV1:
    """Explicit provenance for PRE_EXTERNAL tests (not candle-derived)."""

    native = str(venue_native_id or "").strip()
    if not native:
        raise ProductiveCanonicalPriceProvenanceError("VENUE_NATIVE_ID_REQUIRED")
    if float(mark_px) <= 0 or float(index_px) <= 0:
        raise ProductiveCanonicalPriceProvenanceError("NONPOSITIVE_PRICE_FORBIDDEN")
    return ProductiveCycleCanonicalPriceProvenanceV1(
        mark_price_class=PRICE_CLASS_CMC_MARK,
        mark_source=MARK_SOURCE_EXPLICIT_SYNTHETIC_FIXTURE,
        mark_px=float(mark_px),
        index_price_class=PRICE_CLASS_INDEX,
        index_source=INDEX_SOURCE_EXPLICIT_TEST_FIXTURE,
        index_px=float(index_px),
        venue_native_id=native,
        mark_finalization_state=FINALIZATION_CURRENT,
        mark_temporal_class=TEMPORAL_DERIVED_CURRENT,
        index_temporal_class=TEMPORAL_DERIVED_CURRENT,
    )


def build_provenance_from_governed_synthetic_close_mark_and_index_v1(
    *,
    venue_native_id: str,
    mark_px: float,
    index_px: float,
) -> ProductiveCycleCanonicalPriceProvenanceV1:
    """Truthful provenance for governed synthetic close-chain marks (offline paths)."""

    return build_provenance_from_resolved_cmc_mark_and_index_v1(
        venue_native_id=venue_native_id,
        mark_px=float(mark_px),
        index_px=float(index_px),
        mark_source=MARK_SOURCE_EXPLICIT_SYNTHETIC_FIXTURE,
        index_source=INDEX_SOURCE_EXPLICIT_TEST_FIXTURE,
    )


__all__ = [
    "FINALIZATION_CURRENT",
    "FORBIDDEN_MARK_SOURCES",
    "INDEX_SOURCE_EXPLICIT_TEST_FIXTURE",
    "INDEX_SOURCE_OKX_INDEX_TICKERS",
    "INDEX_SOURCE_OKX_MARK_IDX_PX",
    "INDEX_SOURCE_OKX_TICKER_IDX_PX",
    "MARK_SOURCE_CAP24_MARK_SIDECAR",
    "MARK_SOURCE_EXPLICIT_SYNTHETIC_FIXTURE",
    "MARK_SOURCE_OKX_PUBLIC_MARK_PAYLOAD",
    "PRICE_CLASS_CMC_MARK",
    "PRICE_CLASS_INDEX",
    "ProductiveCanonicalPriceProvenanceError",
    "ProductiveCycleCanonicalPriceProvenanceV1",
    "build_cmc_mark_provenance_from_okx_mark_price_payload_v1",
    "build_explicit_test_fixture_price_provenance_v1",
    "build_provenance_from_governed_synthetic_close_mark_and_index_v1",
    "build_provenance_from_resolved_cmc_mark_and_index_v1",
]
