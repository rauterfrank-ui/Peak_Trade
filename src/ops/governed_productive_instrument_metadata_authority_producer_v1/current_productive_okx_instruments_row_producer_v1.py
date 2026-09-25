"""Produce CRS InstrumentQuantityConstraintsV1 from OKX instruments GET row.

Does not select instruments. Requires Cap24-bound venue_native_id match.
Fail-closed: no silent lot/min/ctVal defaults.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Any, Mapping

from src.governance.capital_risk_sizing_v1 import InstrumentQuantityConstraintsV1
from src.ops.governed_productive_instrument_metadata_authority_producer_v1.constants_v1 import (
    INSTRUMENT_METADATA_AUTHORITY_OWNER,
    OWNER,
    QUANTITY_UNIT_SEMANTICS_RATIFIED,
    SCHEMA_VERSION,
)

PRODUCER_IDENTITY = OWNER
REASON_INST_ROW_MISSING = "INSTRUMENT_METADATA_ROW_MISSING"
REASON_INST_ID_MISMATCH = "INSTRUMENT_METADATA_INST_ID_MISMATCH"
REASON_INST_NOT_LIVE = "INSTRUMENT_METADATA_INSTRUMENT_NOT_LIVE"
REASON_FIELD_MISSING = "INSTRUMENT_METADATA_REQUIRED_FIELD_MISSING"
REASON_FIELD_INVALID = "INSTRUMENT_METADATA_FIELD_INVALID"
REASON_OBSERVED_AT_MISSING = "INSTRUMENT_METADATA_OBSERVED_AT_MISSING"

_ALLOWED_SWAP_STATES = frozenset({"live", "Live"})


class CurrentProductiveInstrumentMetadataProducerError(RuntimeError):
    """Fail-closed instrument metadata producer violation."""


@dataclass(frozen=True)
class CurrentProductiveInstrumentMetadataProducerOutputV1:
    produced: bool
    constraints: InstrumentQuantityConstraintsV1 | None
    reason_codes: tuple[str, ...]
    producer_identity: str
    instrument_metadata_version: str
    observed_at_as_of: str


def _canonical_json(payload: Mapping[str, Any]) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _require_decimal(raw: Any, *, field: str) -> Decimal:
    text = str(raw or "").strip()
    if not text:
        raise CurrentProductiveInstrumentMetadataProducerError(f"{REASON_FIELD_MISSING}:{field}")
    try:
        value = Decimal(text)
    except (InvalidOperation, ValueError) as exc:
        raise CurrentProductiveInstrumentMetadataProducerError(
            f"{REASON_FIELD_INVALID}:{field}"
        ) from exc
    if not value.is_finite() or value <= 0:
        raise CurrentProductiveInstrumentMetadataProducerError(f"{REASON_FIELD_INVALID}:{field}")
    return value


def _first_row(payload: Any) -> Mapping[str, Any]:
    if isinstance(payload, Mapping):
        data = payload.get("data")
        if isinstance(data, list) and data and isinstance(data[0], Mapping):
            return data[0]
        if payload.get("instId"):
            return payload
    if isinstance(payload, list) and payload and isinstance(payload[0], Mapping):
        return payload[0]
    return {}


def _contract_kind_from_row(row: Mapping[str, Any]) -> str:
    inst_type = str(row.get("instType") or "").strip().upper()
    if inst_type in {"SWAP", "FUTURES"}:
        return "LINEAR"
    ct_type = str(row.get("ctType") or "").strip().lower()
    if ct_type == "linear":
        return "LINEAR"
    if ct_type == "inverse":
        return "INVERSE"
    raise CurrentProductiveInstrumentMetadataProducerError(f"{REASON_FIELD_INVALID}:contract_kind")


def produce_current_productive_instrument_quantity_constraints_from_okx_row_v1(
    *,
    venue_native_id: str,
    instruments_payload: Any,
    observed_at_as_of: str,
    bound_instrument_id: str = "",
) -> CurrentProductiveInstrumentMetadataProducerOutputV1:
    """Bind quantity metadata for the already-selected instrument only."""
    wanted = str(venue_native_id or "").strip()
    if not wanted:
        return CurrentProductiveInstrumentMetadataProducerOutputV1(
            produced=False,
            constraints=None,
            reason_codes=(REASON_INST_ROW_MISSING,),
            producer_identity=PRODUCER_IDENTITY,
            instrument_metadata_version="",
            observed_at_as_of=str(observed_at_as_of or ""),
        )
    if not str(observed_at_as_of or "").strip():
        return CurrentProductiveInstrumentMetadataProducerOutputV1(
            produced=False,
            constraints=None,
            reason_codes=(REASON_OBSERVED_AT_MISSING,),
            producer_identity=PRODUCER_IDENTITY,
            instrument_metadata_version="",
            observed_at_as_of="",
        )
    row = _first_row(instruments_payload)
    if not row:
        return CurrentProductiveInstrumentMetadataProducerOutputV1(
            produced=False,
            constraints=None,
            reason_codes=(REASON_INST_ROW_MISSING,),
            producer_identity=PRODUCER_IDENTITY,
            instrument_metadata_version="",
            observed_at_as_of=str(observed_at_as_of),
        )
    inst_id = str(row.get("instId") or "").strip()
    if inst_id != wanted:
        return CurrentProductiveInstrumentMetadataProducerOutputV1(
            produced=False,
            constraints=None,
            reason_codes=(REASON_INST_ID_MISMATCH,),
            producer_identity=PRODUCER_IDENTITY,
            instrument_metadata_version="",
            observed_at_as_of=str(observed_at_as_of),
        )
    state = str(row.get("state") or "").strip()
    if state and state not in _ALLOWED_SWAP_STATES:
        return CurrentProductiveInstrumentMetadataProducerOutputV1(
            produced=False,
            constraints=None,
            reason_codes=(REASON_INST_NOT_LIVE,),
            producer_identity=PRODUCER_IDENTITY,
            instrument_metadata_version="",
            observed_at_as_of=str(observed_at_as_of),
        )
    try:
        contract_multiplier = _require_decimal(row.get("ctVal"), field="ctVal")
        lot_size = _require_decimal(row.get("lotSz"), field="lotSz")
        minimum_quantity = _require_decimal(row.get("minSz"), field="minSz")
        tick_size = _require_decimal(row.get("tickSz"), field="tickSz")
        contract_kind = _contract_kind_from_row(row)
    except CurrentProductiveInstrumentMetadataProducerError as exc:
        code = str(exc).split(":", 1)[0]
        return CurrentProductiveInstrumentMetadataProducerOutputV1(
            produced=False,
            constraints=None,
            reason_codes=(code,),
            producer_identity=PRODUCER_IDENTITY,
            instrument_metadata_version="",
            observed_at_as_of=str(observed_at_as_of),
        )

    instrument_id = str(bound_instrument_id or wanted).strip() or wanted
    min_notional: Decimal | None = None
    if row.get("minNotional"):
        try:
            min_notional = _require_decimal(row.get("minNotional"), field="minNotional")
        except CurrentProductiveInstrumentMetadataProducerError:
            min_notional = None

    digest_material = {
        "schema": SCHEMA_VERSION,
        "producer": INSTRUMENT_METADATA_AUTHORITY_OWNER,
        "instId": inst_id,
        "ctVal": str(contract_multiplier),
        "lotSz": str(lot_size),
        "minSz": str(minimum_quantity),
        "tickSz": str(tick_size),
        "quantity_unit": QUANTITY_UNIT_SEMANTICS_RATIFIED,
        "observed_at": str(observed_at_as_of),
    }
    metadata_version = _sha256_text(_canonical_json(digest_material))

    constraints = InstrumentQuantityConstraintsV1(
        instrument_id=instrument_id,
        market_type="futures",
        contract_kind=contract_kind,
        contract_multiplier=contract_multiplier,
        lot_size=lot_size,
        minimum_quantity=minimum_quantity,
        maximum_quantity=None,
        minimum_notional=min_notional,
        tick_size=tick_size,
        instrument_metadata_version=metadata_version,
    )
    return CurrentProductiveInstrumentMetadataProducerOutputV1(
        produced=True,
        constraints=constraints,
        reason_codes=(),
        producer_identity=PRODUCER_IDENTITY,
        instrument_metadata_version=metadata_version,
        observed_at_as_of=str(observed_at_as_of),
    )
