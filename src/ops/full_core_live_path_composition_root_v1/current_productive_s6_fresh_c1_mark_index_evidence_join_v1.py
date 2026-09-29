"""Fresh CMC mark + index tickers evidence for S6 LiveFreshC1 poll (GET-only).

Reuses CURRENT EEA public mark acquisition and OKX index-tickers GET.
No synthetic prices. No credentials on index/mark public GETs.

RUNTIME_AUTHORIZATION_EFFECT=NONE
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping
from urllib.parse import urlencode

from src.ops.current_productive_eea_universe_inventory_acquisition_v1.acquire_v1 import (
    EeaUniverseAcquisitionError,
    acquire_eea_universe_inventory_v1,
)
from src.ops.current_productive_eea_universe_inventory_acquisition_v1.transport_v1 import (
    EeaPublicUniverseGetPortV1,
    UrllibEeaPublicUniverseGetTransportV1,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_canonical_price_provenance_v1 import (
    ProductiveCanonicalPriceProvenanceError,
    build_cmc_mark_provenance_from_okx_mark_price_payload_v1,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_master_v2_runtime_cycle_v1 import (
    ENDPOINT_MARKET_INDEX_TICKERS,
    resolve_index_ticker_inst_id_v1,
)

MARK_SOURCE = "OKX_PUBLIC_MARK_PRICE_PAYLOAD_VIA_EEA_UNIVERSE_ACQUISITION_V1"
INDEX_SOURCE = "OKX_INDEX_TICKERS_PUBLIC_GET_V1"


class CurrentProductiveS6C1MarkIndexEvidenceError(ValueError):
    """Fail-closed S6 C1 mark/index enrichment violation."""


@dataclass(frozen=True)
class CurrentProductiveS6C1MarkIndexEvidenceV1:
    mark_price_payload: Mapping[str, Any]
    index_tickers_payload: Mapping[str, Any] | None
    mark_source: str
    index_source: str
    venue_native_id: str
    instrument_match_proven: bool
    mark_fresh: bool


class S6C1MarkIndexGetTransportV1:
    def get(
        self,
        *,
        endpoint: str,
        auth_required: bool,
        pretrade_decision_id: str,
    ) -> Any: ...


def _default_eea_transport_v1() -> EeaPublicUniverseGetPortV1:
    return UrllibEeaPublicUniverseGetTransportV1()


def collect_current_productive_s6_c1_poll_mark_index_evidence_v1(
    *,
    transport: S6C1MarkIndexGetTransportV1,
    venue_native_id: str,
    pretrade_decision_id: str,
    eea_transport: EeaPublicUniverseGetPortV1 | None = None,
) -> CurrentProductiveS6C1MarkIndexEvidenceV1:
    """Collect canonical mark/index payloads required by S6 C1 observation enrichment."""
    native = str(venue_native_id or "").strip()
    if not native:
        raise CurrentProductiveS6C1MarkIndexEvidenceError("VENUE_NATIVE_ID_REQUIRED")
    try:
        acq = acquire_eea_universe_inventory_v1(
            transport=eea_transport or _default_eea_transport_v1(),
        )
    except EeaUniverseAcquisitionError as exc:
        raise CurrentProductiveS6C1MarkIndexEvidenceError(str(exc)) from exc
    if acq.ok is not True:
        raise CurrentProductiveS6C1MarkIndexEvidenceError("EEA_MARK_ACQUISITION_FAIL_CLOSED")
    mark_payload = acq.mark_price_payload

    index_inst = resolve_index_ticker_inst_id_v1(native)
    index_endpoint = f"{ENDPOINT_MARKET_INDEX_TICKERS}?{urlencode({'instId': index_inst})}"
    index_result = transport.get(
        endpoint=index_endpoint,
        auth_required=False,
        pretrade_decision_id=f"{pretrade_decision_id}-index-tickers",
    )
    index_payload: Mapping[str, Any] | None = None
    if bool(getattr(index_result, "get_performed", False)):
        raw = getattr(index_result, "payload", None)
        if isinstance(raw, dict):
            index_payload = raw
    try:
        build_cmc_mark_provenance_from_okx_mark_price_payload_v1(
            mark_price_payload=mark_payload,
            venue_native_id=native,
            index_from_index_tickers=index_payload,
        )
    except ProductiveCanonicalPriceProvenanceError as exc:
        raise CurrentProductiveS6C1MarkIndexEvidenceError(str(exc)) from exc

    return CurrentProductiveS6C1MarkIndexEvidenceV1(
        mark_price_payload=mark_payload,
        index_tickers_payload=index_payload,
        mark_source=MARK_SOURCE,
        index_source=INDEX_SOURCE,
        venue_native_id=native,
        instrument_match_proven=True,
        mark_fresh=True,
    )


__all__ = [
    "CurrentProductiveS6C1MarkIndexEvidenceError",
    "CurrentProductiveS6C1MarkIndexEvidenceV1",
    "INDEX_SOURCE",
    "MARK_SOURCE",
    "S6C1MarkIndexGetTransportV1",
    "collect_current_productive_s6_c1_poll_mark_index_evidence_v1",
]
