"""Order serialization dry-run contract (§11.12.2) — fixture-only, no network."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any, Mapping

from src.ops.capability_11_4_testnet_execution_adapter_and_lifecycle_closure_v1.constants_v1 import (
    CONTRACT_VERSION,
    ORDER_SERIALIZATION_DRY_RUN_CONTRACT_BOUND,
    ORDER_SERIALIZATION_DRY_RUN_OWNER,
    ORDER_SERIALIZATION_NETWORK_EFFECT,
    ORDER_SERIALIZATION_REQUIRED_FIELDS,
    OWNER,
    TESTNET_ORDER_SUBMIT_PERFORMED_IN_CAPABILITY_11_4,
)


class OrderSerializationDryRunError(RuntimeError):
    """Fail-closed order serialization dry-run violation."""


def _canonical_dumps(payload: Mapping[str, Any]) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


@dataclass(frozen=True)
class OrderSerializationDryRunRecordV1:
    """Fixture-only venue-native order serialization record."""

    client_order_id: str
    instrument_id: str
    side: str
    order_type: str
    quantity: str
    execution_mode: str
    venue_native_payload: dict[str, Any]
    serialization_digest: str
    source: str = "FIXTURE_ONLY"
    network_effect: str = "NONE"
    submitted: bool = False
    contract_version: str = CONTRACT_VERSION
    owner: str = ORDER_SERIALIZATION_DRY_RUN_OWNER


def build_order_serialization_dry_run_record_v1(
    *,
    client_order_id: str,
    instrument_id: str,
    side: str,
    order_type: str,
    quantity: str,
    execution_mode: str = "TESTNET",
    source: str = "FIXTURE_ONLY",
) -> OrderSerializationDryRunRecordV1:
    fields = {
        "client_order_id": client_order_id,
        "instrument_id": instrument_id,
        "side": side,
        "order_type": order_type,
        "quantity": quantity,
        "execution_mode": execution_mode,
    }
    for key in ORDER_SERIALIZATION_REQUIRED_FIELDS:
        if not fields.get(key):
            raise OrderSerializationDryRunError(f"ORDER_SERIALIZATION_FIELD_MISSING:{key}")
    if source != "FIXTURE_ONLY":
        raise OrderSerializationDryRunError(
            f"NON_FIXTURE_ORDER_SERIALIZATION_SOURCE_FORBIDDEN_IN_CAPABILITY_11_4:{source}"
        )
    if execution_mode != "TESTNET":
        raise OrderSerializationDryRunError(
            f"ORDER_SERIALIZATION_EXECUTION_MODE_NOT_TESTNET:{execution_mode}"
        )

    venue_native_payload = {
        "clOrdId": client_order_id,
        "instId": instrument_id,
        "side": side.lower(),
        "ordType": order_type.lower(),
        "sz": quantity,
        "tdMode": "cross",
        "dry_run": True,
    }
    digest = hashlib.sha256(_canonical_dumps(venue_native_payload).encode("utf-8")).hexdigest()
    return OrderSerializationDryRunRecordV1(
        client_order_id=client_order_id,
        instrument_id=instrument_id,
        side=side,
        order_type=order_type,
        quantity=quantity,
        execution_mode=execution_mode,
        venue_native_payload=venue_native_payload,
        serialization_digest=digest,
        source=source,
        network_effect=ORDER_SERIALIZATION_NETWORK_EFFECT,
        submitted=False,
    )


def refuse_order_serialization_network_submit_v1(
    *, record: OrderSerializationDryRunRecordV1
) -> dict[str, Any]:
    raise OrderSerializationDryRunError(
        "ORDER_SERIALIZATION_NETWORK_SUBMIT_FORBIDDEN_IN_CAPABILITY_11_4:" + record.client_order_id
    )


def prove_order_serialization_dry_run_contract_v1() -> dict[str, Any]:
    record = build_order_serialization_dry_run_record_v1(
        client_order_id="pt-coid-dryrun-demo",
        instrument_id="BTC-USDT-SWAP",
        side="BUY",
        order_type="LIMIT",
        quantity="1",
    )

    non_fixture_blocked = False
    try:
        build_order_serialization_dry_run_record_v1(
            client_order_id="pt-coid-dryrun-bad",
            instrument_id="BTC-USDT-SWAP",
            side="BUY",
            order_type="LIMIT",
            quantity="1",
            source="LIVE_NETWORK",
        )
    except OrderSerializationDryRunError as exc:
        non_fixture_blocked = "NON_FIXTURE" in str(exc)

    live_mode_blocked = False
    try:
        build_order_serialization_dry_run_record_v1(
            client_order_id="pt-coid-dryrun-live",
            instrument_id="BTC-USDT-SWAP",
            side="BUY",
            order_type="LIMIT",
            quantity="1",
            execution_mode="LIVE",
        )
    except OrderSerializationDryRunError as exc:
        live_mode_blocked = "NOT_TESTNET" in str(exc)

    submit_blocked = False
    try:
        refuse_order_serialization_network_submit_v1(record=record)
    except OrderSerializationDryRunError as exc:
        submit_blocked = "NETWORK_SUBMIT_FORBIDDEN" in str(exc)

    ok = all(
        [
            record.source == "FIXTURE_ONLY",
            record.submitted is False,
            record.network_effect == "NONE",
            record.venue_native_payload.get("dry_run") is True,
            bool(record.serialization_digest),
            non_fixture_blocked,
            live_mode_blocked,
            submit_blocked,
            ORDER_SERIALIZATION_DRY_RUN_CONTRACT_BOUND is True,
            TESTNET_ORDER_SUBMIT_PERFORMED_IN_CAPABILITY_11_4 is False,
            ORDER_SERIALIZATION_NETWORK_EFFECT == "NONE",
            record.owner == OWNER,
        ]
    )
    return {
        "ok": ok,
        "ORDER_SERIALIZATION_DRY_RUN_CONTRACT_BOUND": True,
        "ORDER_SERIALIZATION_NETWORK_EFFECT": "NONE",
        "TESTNET_ORDER_SUBMIT_PERFORMED_IN_CAPABILITY_11_4": False,
        "non_fixture_blocked": non_fixture_blocked,
        "live_mode_blocked": live_mode_blocked,
        "submit_blocked": submit_blocked,
        "required_fields": list(ORDER_SERIALIZATION_REQUIRED_FIELDS),
        "sample_digest": record.serialization_digest,
        "OWNER": ORDER_SERIALIZATION_DRY_RUN_OWNER,
    }
