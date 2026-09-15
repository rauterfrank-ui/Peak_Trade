"""Acquire provenance-bound EEA public instruments + mark-price payloads.

Cap-2.1 remains a no-network producer. This layer only injects payloads.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Mapping, Sequence

from src.ops.current_productive_eea_universe_inventory_acquisition_v1.constants_v1 import (
    AUTHORIZED_HOST,
    ENDPOINT_PUBLIC_INSTRUMENTS,
    ENDPOINT_PUBLIC_MARK_PRICE,
    METHOD_GET,
    REQUIRED_INST_TYPES,
    SOURCE_KIND,
    VENUE,
)
from src.ops.current_productive_eea_universe_inventory_acquisition_v1.transport_v1 import (
    EeaPublicGetResultV1,
    EeaPublicUniverseGetPortV1,
    EeaUniverseAcquisitionError,
    UrllibEeaPublicUniverseGetTransportV1,
)


@dataclass(frozen=True)
class EeaUniverseAcquisitionResultV1:
    ok: bool
    host: str
    venue: str
    source_kind: str
    source_event_time: str
    instruments_payload: Mapping[str, Any]
    mark_price_payload: Mapping[str, Any]
    endpoints_used: tuple[str, ...]
    methods_used: tuple[str, ...]
    post_count: str
    request_count: int
    venue_live_contact: bool
    failure_codes: tuple[str, ...]
    provenance: Mapping[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "host": self.host,
            "venue": self.venue,
            "source_kind": self.source_kind,
            "source_event_time": self.source_event_time,
            "instruments_payload": dict(self.instruments_payload),
            "mark_price_payload": dict(self.mark_price_payload),
            "endpoints_used": list(self.endpoints_used),
            "methods_used": list(self.methods_used),
            "post_count": self.post_count,
            "request_count": self.request_count,
            "venue_live_contact": self.venue_live_contact,
            "failure_codes": list(self.failure_codes),
            "provenance": dict(self.provenance),
        }


def _utc_now_iso_v1() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _canonical_json(payload: Mapping[str, Any] | list[Any]) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _merge_okx_lists(
    *,
    results: Sequence[EeaPublicGetResultV1],
    expected_path: str,
) -> tuple[dict[str, Any], tuple[str, ...]]:
    rows: list[Mapping[str, Any]] = []
    failures: list[str] = []
    ts = ""
    for item in results:
        if item.path != expected_path:
            failures.append("PATH_MISMATCH")
            continue
        if item.method != METHOD_GET:
            failures.append("NON_GET_FORBIDDEN")
            continue
        if item.host != AUTHORIZED_HOST:
            failures.append("HOST_NOT_EEA_OKX")
            continue
        if item.http_status != 200 or not isinstance(item.payload, dict):
            failures.append(item.error_class or "HTTP_OR_PAYLOAD_FAILURE")
            continue
        code = str(item.payload.get("code", "")).strip()
        if code != "0":
            failures.append(f"VENUE_CODE_{code or 'MISSING'}")
            continue
        data = item.payload.get("data")
        if not isinstance(data, list):
            failures.append("DATA_NOT_LIST")
            continue
        for row in data:
            if isinstance(row, Mapping):
                rows.append(row)
        if not ts:
            ts = str(item.ts or item.payload.get("ts") or "").strip()
    envelope: dict[str, Any] = {"code": "0", "msg": "", "data": rows}
    if ts:
        envelope["ts"] = ts
    return envelope, tuple(failures)


def acquire_eea_universe_inventory_v1(
    *,
    transport: EeaPublicUniverseGetPortV1 | None = None,
    observed_at: str | None = None,
) -> EeaUniverseAcquisitionResultV1:
    """GET FUTURES+SWAP instruments and mark-price from eea.okx.com. No instId."""
    port = transport or UrllibEeaPublicUniverseGetTransportV1()
    observed = str(observed_at or _utc_now_iso_v1())
    instrument_hits: list[EeaPublicGetResultV1] = []
    mark_hits: list[EeaPublicGetResultV1] = []
    endpoints: list[str] = []
    methods: list[str] = []
    failures: list[str] = []
    live_contact = False
    for inst_type in REQUIRED_INST_TYPES:
        inst = port.get(
            path=ENDPOINT_PUBLIC_INSTRUMENTS,
            query={"instType": inst_type},
        )
        instrument_hits.append(inst)
        endpoints.append(f"{ENDPOINT_PUBLIC_INSTRUMENTS}?instType={inst_type}")
        methods.append(inst.method)
        live_contact = live_contact or bool(inst.venue_live_contact)
        mark = port.get(
            path=ENDPOINT_PUBLIC_MARK_PRICE,
            query={"instType": inst_type},
        )
        mark_hits.append(mark)
        endpoints.append(f"{ENDPOINT_PUBLIC_MARK_PRICE}?instType={inst_type}")
        methods.append(mark.method)
        live_contact = live_contact or bool(mark.venue_live_contact)
        if inst.method != METHOD_GET or mark.method != METHOD_GET:
            raise EeaUniverseAcquisitionError("NON_GET_FORBIDDEN")
        if "www.okx.com" in inst.host or "www.okx.com" in mark.host:
            raise EeaUniverseAcquisitionError("WWW_OKX_FORBIDDEN")
    instruments, inst_fail = _merge_okx_lists(
        results=instrument_hits, expected_path=ENDPOINT_PUBLIC_INSTRUMENTS
    )
    marks, mark_fail = _merge_okx_lists(results=mark_hits, expected_path=ENDPOINT_PUBLIC_MARK_PRICE)
    failures.extend(inst_fail)
    failures.extend(mark_fail)
    event_time = str(instruments.get("ts") or marks.get("ts") or observed).strip()
    instruments["source_event_time"] = event_time
    hard: list[str] = []
    soft: list[str] = []
    for code in failures:
        if code.startswith("VENUE_CODE_") or code in {
            "HTTP_OR_PAYLOAD_FAILURE",
            "DATA_NOT_LIST",
            "TIMEOUT",
            "HTTP_ERROR",
        }:
            soft.append(code)
        else:
            hard.append(code)
    if not instruments.get("data"):
        hard.append("INSTRUMENTS_EMPTY")
    if not marks.get("data"):
        hard.append("MARK_PRICE_EMPTY")
    unique_failures = tuple(dict.fromkeys(hard))
    unique_soft = tuple(dict.fromkeys(soft))
    ok = not unique_failures and bool(instruments.get("data")) and bool(marks.get("data"))
    provenance = {
        "ACQUISITION_OWNER": "CURRENT_PRODUCTIVE_EEA_UNIVERSE_INVENTORY_ACQUISITION_V1",
        "HOST": AUTHORIZED_HOST,
        "VENUE": VENUE,
        "SOURCE_KIND": SOURCE_KIND,
        "NETWORK_METHODS": list(methods),
        "ENDPOINTS": list(endpoints),
        "POST_COUNT": "0",
        "INST_TYPES": list(REQUIRED_INST_TYPES),
        "INSTID_FORCED": False,
        "CREDENTIALS_USED": False,
        "CAP21_NETWORK_OWNER": False,
        "CANARY_INSTRUMENT_AUTHORITY_IMPORTED": False,
        "INSTRUMENTS_DIGEST": hashlib.sha256(
            _canonical_json(instruments).encode("utf-8")
        ).hexdigest(),
        "MARK_PRICE_DIGEST": hashlib.sha256(_canonical_json(marks).encode("utf-8")).hexdigest(),
        "INSTRUMENT_ROW_COUNT": len(instruments.get("data") or []),
        "MARK_PRICE_ROW_COUNT": len(marks.get("data") or []),
        "VENUE_LIVE_CONTACT": live_contact,
        "FAILURE_CODES": list(unique_failures),
        "SOFT_FAILURE_CODES": list(unique_soft),
    }
    return EeaUniverseAcquisitionResultV1(
        ok=ok,
        host=AUTHORIZED_HOST,
        venue=VENUE,
        source_kind=SOURCE_KIND,
        source_event_time=event_time,
        instruments_payload=instruments,
        mark_price_payload=marks,
        endpoints_used=tuple(endpoints),
        methods_used=tuple(methods),
        post_count="0",
        request_count=len(endpoints),
        venue_live_contact=live_contact,
        failure_codes=unique_failures,
        provenance=provenance,
    )
