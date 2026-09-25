"""Produce governed mark_price reference quote from MV2 market context mark.

Does not substitute index/candle_close/fill. Fail-closed on missing or
non-positive mark. Does not POST.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Any

from src.ops.governed_productive_reference_price_authority_producer_v1.constants_v1 import (
    PRICE_SEMANTICS_CLASS_RATIFIED,
    REFERENCE_PRICE_AUTHORITY_OWNER,
    SCHEMA_VERSION,
)

PRODUCER_IDENTITY = REFERENCE_PRICE_AUTHORITY_OWNER
REASON_MARK_MISSING = "REFERENCE_PRICE_MARK_MISSING"
REASON_MARK_INVALID = "REFERENCE_PRICE_MARK_INVALID"
REASON_OBSERVED_AT_MISSING = "REFERENCE_PRICE_OBSERVED_AT_MISSING"
REASON_INSTRUMENT_MISSING = "REFERENCE_PRICE_INSTRUMENT_ID_MISSING"


class CurrentProductiveReferencePriceProducerError(RuntimeError):
    """Fail-closed reference price producer violation."""


@dataclass(frozen=True)
class CurrentProductiveReferencePriceProducerOutputV1:
    produced: bool
    reference_price: Decimal | None
    reason_codes: tuple[str, ...]
    producer_identity: str
    reference_price_version: str
    price_semantics_class: str
    instrument_id: str
    observed_at_as_of: str


def _canonical_json(payload: dict[str, Any]) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _parse_mark(raw: Any) -> Decimal:
    text = str(raw or "").strip()
    if not text:
        raise CurrentProductiveReferencePriceProducerError(REASON_MARK_MISSING)
    try:
        value = Decimal(text)
    except (InvalidOperation, ValueError) as exc:
        raise CurrentProductiveReferencePriceProducerError(REASON_MARK_INVALID) from exc
    if not value.is_finite() or value <= 0:
        raise CurrentProductiveReferencePriceProducerError(REASON_MARK_INVALID)
    return value


def produce_current_productive_reference_price_from_mv2_mark_v1(
    *,
    mark_price: Any,
    instrument_id: str,
    observed_at_as_of: str,
) -> CurrentProductiveReferencePriceProducerOutputV1:
    """Bind mark_price as governed reference price for CRS capital_context."""
    inst = str(instrument_id or "").strip()
    if not inst:
        return CurrentProductiveReferencePriceProducerOutputV1(
            produced=False,
            reference_price=None,
            reason_codes=(REASON_INSTRUMENT_MISSING,),
            producer_identity=PRODUCER_IDENTITY,
            reference_price_version="",
            price_semantics_class=PRICE_SEMANTICS_CLASS_RATIFIED,
            instrument_id="",
            observed_at_as_of=str(observed_at_as_of or ""),
        )
    if not str(observed_at_as_of or "").strip():
        return CurrentProductiveReferencePriceProducerOutputV1(
            produced=False,
            reference_price=None,
            reason_codes=(REASON_OBSERVED_AT_MISSING,),
            producer_identity=PRODUCER_IDENTITY,
            reference_price_version="",
            price_semantics_class=PRICE_SEMANTICS_CLASS_RATIFIED,
            instrument_id=inst,
            observed_at_as_of="",
        )
    try:
        price = _parse_mark(mark_price)
    except CurrentProductiveReferencePriceProducerError as exc:
        code = str(exc)
        return CurrentProductiveReferencePriceProducerOutputV1(
            produced=False,
            reference_price=None,
            reason_codes=(code,),
            producer_identity=PRODUCER_IDENTITY,
            reference_price_version="",
            price_semantics_class=PRICE_SEMANTICS_CLASS_RATIFIED,
            instrument_id=inst,
            observed_at_as_of=str(observed_at_as_of),
        )

    digest_material = {
        "schema": SCHEMA_VERSION,
        "producer": REFERENCE_PRICE_AUTHORITY_OWNER,
        "instrument_id": inst,
        "price_semantics_class": PRICE_SEMANTICS_CLASS_RATIFIED,
        "mark_price": str(price),
        "observed_at": str(observed_at_as_of),
    }
    version = _sha256_text(_canonical_json(digest_material))

    return CurrentProductiveReferencePriceProducerOutputV1(
        produced=True,
        reference_price=price,
        reason_codes=(),
        producer_identity=PRODUCER_IDENTITY,
        reference_price_version=version,
        price_semantics_class=PRICE_SEMANTICS_CLASS_RATIFIED,
        instrument_id=inst,
        observed_at_as_of=str(observed_at_as_of),
    )
