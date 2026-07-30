"""Offline fixture probe — no network, no auth consume, no session evidence."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Mapping

from src.ops.okx_native_instrument_and_mark_price_runtime_binding_fail_closed_v1.constants_v1 import (
    CANONICAL_INSTRUMENT_ID,
    CAPABILITY_ID,
    MARK_PRICE_ENDPOINT,
    MARK_PRICE_FIELD,
)
from src.ops.okx_native_instrument_and_mark_price_runtime_binding_fail_closed_v1.mark_price_contract_v1 import (
    parse_public_mark_price_response_v1,
)
from src.ops.okx_native_instrument_and_mark_price_runtime_binding_fail_closed_v1.normalized_market_data_v1 import (
    build_normalized_public_market_data_v1,
)
from src.ops.okx_native_instrument_and_mark_price_runtime_binding_fail_closed_v1.public_instruments_validation_v1 import (
    extract_instruments_data_array_v1,
)
from src.ops.okx_native_instrument_and_mark_price_runtime_binding_fail_closed_v1.ticker_semantics_v1 import (
    parse_public_ticker_semantics_v1,
)
from src.ops.okx_native_instrument_and_mark_price_runtime_binding_fail_closed_v1.venue_instrument_mapping_v1 import (
    resolve_okx_venue_instrument_mapping_v1,
)


@dataclass
class OfflineProbeResultV1:
    ok: bool
    blockers: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    capability_id: str = CAPABILITY_ID
    normalized: dict[str, Any] = field(default_factory=dict)
    private_api_used: bool = False
    orders_created: bool = False
    authorization_consumed: bool = False
    wallclock_session_started: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class _FixtureTransportV1:
    def __init__(
        self,
        *,
        instruments: Mapping[str, Any],
        mark_price: Mapping[str, Any],
        ticker: Mapping[str, Any],
    ) -> None:
        self._instruments = instruments
        self._mark_price = mark_price
        self._ticker = ticker
        self.requested_inst_ids: list[str] = []

    class _Fetch:
        def __init__(self, payload: Mapping[str, Any]) -> None:
            self.payload = payload

    def fetch_instruments(self, *, venue_instrument_id: str, inst_type: str = "FUTURES"):
        self.requested_inst_ids.append(venue_instrument_id)
        return self._Fetch(self._instruments)

    def fetch_mark_price(self, *, venue_instrument_id: str, inst_type: str = "FUTURES"):
        self.requested_inst_ids.append(venue_instrument_id)
        return self._Fetch(self._mark_price)

    def fetch_ticker(self, *, venue_instrument_id: str):
        self.requested_inst_ids.append(venue_instrument_id)
        return self._Fetch(self._ticker)


def run_offline_okx_native_mark_price_binding_probe_v1(
    *,
    instruments_payload: Mapping[str, Any],
    mark_price_payload: Mapping[str, Any],
    ticker_payload: Mapping[str, Any],
    receive_ts_unix: float,
    max_stale_seconds: float = 30.0,
    canonical_instrument_id: str = CANONICAL_INSTRUMENT_ID,
) -> OfflineProbeResultV1:
    notes = [
        "OFFLINE_FIXTURE_PROBE",
        "NO_NETWORK",
        "NO_AUTHORIZATION_CONSUMPTION",
        "NO_PRODUCTIVE_SESSION_EVIDENCE",
        f"MARK_PRICE_ENDPOINT={MARK_PRICE_ENDPOINT}",
        f"MARK_PRICE_FIELD={MARK_PRICE_FIELD}",
    ]
    try:
        inventory = extract_instruments_data_array_v1(instruments_payload)
        mapping = resolve_okx_venue_instrument_mapping_v1(
            canonical_instrument_id=canonical_instrument_id,
            instruments_inventory=inventory,
        )
        transport = _FixtureTransportV1(
            instruments=instruments_payload,
            mark_price=mark_price_payload,
            ticker=ticker_payload,
        )
        # Request using resolved native venue ID only.
        mark_fetch = transport.fetch_mark_price(venue_instrument_id=mapping.venue_instrument_id)
        mark = parse_public_mark_price_response_v1(
            mark_fetch.payload,
            expected_venue_instrument_id=mapping.venue_instrument_id,
            receive_ts_unix=receive_ts_unix,
            max_stale_seconds=max_stale_seconds,
        )
        ticker = parse_public_ticker_semantics_v1(
            transport.fetch_ticker(venue_instrument_id=mapping.venue_instrument_id).payload,
            expected_venue_instrument_id=mapping.venue_instrument_id,
        )
        normalized = build_normalized_public_market_data_v1(
            mapping=mapping, mark=mark, ticker=ticker
        )
        # Ensure transport never saw a distinct hardcoded non-authority path.
        if any(i != mapping.venue_instrument_id for i in transport.requested_inst_ids):
            return OfflineProbeResultV1(
                ok=False,
                blockers=["TRANSPORT_USED_NON_VENUE_INSTRUMENT_ID"],
                notes=notes,
            )
        return OfflineProbeResultV1(
            ok=True,
            notes=notes
            + [
                f"RESOLVED_VENUE_INSTRUMENT_ID={mapping.venue_instrument_id}",
                f"MAPPING_DIGEST={mapping.mapping_digest}",
            ],
            normalized=normalized.to_dict(),
        )
    except Exception as exc:  # noqa: BLE001
        return OfflineProbeResultV1(ok=False, blockers=[str(exc)], notes=notes)


def load_fixture_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("FIXTURE_NOT_OBJECT")
    return payload
