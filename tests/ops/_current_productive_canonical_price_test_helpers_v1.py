"""PRE_EXTERNAL helpers: OKX-shaped CMC mark / index payloads and provenance."""

from __future__ import annotations

from typing import Any

from src.ops.full_core_live_path_composition_root_v1.current_productive_canonical_price_provenance_v1 import (
    ProductiveCycleCanonicalPriceProvenanceV1,
    build_cmc_mark_provenance_from_okx_mark_price_payload_v1,
    build_explicit_test_fixture_price_provenance_v1,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_master_v2_runtime_cycle_v1 import (
    resolve_index_ticker_inst_id_v1,
)
from src.ops.single_selected_future_runtime_binding_v1.models_v1 import BoundInstrumentV1


def okx_public_mark_price_payload_v1(
    *,
    native_id: str,
    mark_px: float,
    index_px: float | None = None,
) -> dict[str, Any]:
    idx = float(index_px) if index_px is not None else float(mark_px) * 0.995
    return {
        "code": "0",
        "data": [
            {
                "instId": str(native_id),
                "markPx": f"{float(mark_px):.8f}".rstrip("0").rstrip("."),
                "idxPx": f"{idx:.8f}".rstrip("0").rstrip("."),
            }
        ],
    }


def okx_index_tickers_payload_v1(*, index_inst_id: str, index_px: float) -> dict[str, Any]:
    return {
        "code": "0",
        "data": [
            {
                "instId": str(index_inst_id),
                "idxPx": f"{float(index_px):.8f}".rstrip("0").rstrip("."),
            }
        ],
    }


def provenance_from_okx_mark_payload_v1(
    *,
    native_id: str,
    mark_price_payload: dict[str, Any],
    index_tickers_payload: dict[str, Any] | None = None,
) -> ProductiveCycleCanonicalPriceProvenanceV1:
    return build_cmc_mark_provenance_from_okx_mark_price_payload_v1(
        mark_price_payload=mark_price_payload,
        venue_native_id=native_id,
        index_from_index_tickers=index_tickers_payload,
    )


def provenance_for_bound_v1(
    *,
    bound: BoundInstrumentV1,
    mark_px: float,
    index_px: float,
) -> ProductiveCycleCanonicalPriceProvenanceV1:
    native = str(bound.venue_native_id or bound.instrument_id or "").strip()
    return build_explicit_test_fixture_price_provenance_v1(
        venue_native_id=native,
        mark_px=float(mark_px),
        index_px=float(index_px),
    )


def observation_mark_payloads_for_bound_v1(
    *,
    bound: BoundInstrumentV1,
    mark_px: float,
    index_px: float | None = None,
) -> tuple[dict[str, Any], dict[str, Any] | None]:
    native = str(bound.venue_native_id or "").strip()
    idx = float(index_px) if index_px is not None else float(mark_px) * 0.995
    mark_payload = okx_public_mark_price_payload_v1(
        native_id=native, mark_px=float(mark_px), index_px=idx
    )
    index_inst = resolve_index_ticker_inst_id_v1(native)
    index_payload = okx_index_tickers_payload_v1(index_inst_id=index_inst, index_px=idx)
    return mark_payload, index_payload
