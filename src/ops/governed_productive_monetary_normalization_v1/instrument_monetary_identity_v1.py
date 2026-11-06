"""Instrument monetary identity from OKX instruments row (authoritative metadata)."""

from __future__ import annotations

import hashlib
import json
from decimal import Decimal, InvalidOperation
from typing import Any, Mapping

from src.ops.governed_productive_instrument_metadata_authority_producer_v1.current_productive_okx_instruments_row_producer_v1 import (
    _first_row,
)
from src.ops.governed_productive_monetary_normalization_v1.contracts_v1 import (
    REASON_INSTRUMENT_MONETARY_IDENTITY_MISSING,
    InstrumentMonetaryIdentityV1,
    MonetaryNormalizationError,
)


def _find_row(payload: Any, *, wanted_inst_id: str) -> Mapping[str, Any]:
    if isinstance(payload, Mapping):
        data = payload.get("data")
        if isinstance(data, list):
            for row in data:
                if (
                    isinstance(row, Mapping)
                    and str(row.get("instId") or "").strip() == wanted_inst_id
                ):
                    return row
        if str(payload.get("instId") or "").strip() == wanted_inst_id:
            return payload
    if isinstance(payload, list):
        for row in payload:
            if isinstance(row, Mapping) and str(row.get("instId") or "").strip() == wanted_inst_id:
                return row
    return {}


def _require_currency(row: Mapping[str, Any], *keys: str, field: str) -> str:
    for key in keys:
        text = str(row.get(key) or "").strip().upper()
        if text:
            return text
    raise MonetaryNormalizationError(f"{REASON_INSTRUMENT_MONETARY_IDENTITY_MISSING}:{field}")


def _require_decimal_field(row: Mapping[str, Any], key: str) -> Decimal:
    text = str(row.get(key) or "").strip()
    if not text:
        raise MonetaryNormalizationError(f"{REASON_INSTRUMENT_MONETARY_IDENTITY_MISSING}:{key}")
    try:
        value = Decimal(text)
    except (InvalidOperation, ValueError) as exc:
        raise MonetaryNormalizationError(
            f"{REASON_INSTRUMENT_MONETARY_IDENTITY_MISSING}:{key}"
        ) from exc
    if not value.is_finite() or value <= 0:
        raise MonetaryNormalizationError(f"{REASON_INSTRUMENT_MONETARY_IDENTITY_MISSING}:{key}")
    return value


def instrument_monetary_identity_from_okx_row_v1(
    row: Mapping[str, Any],
) -> InstrumentMonetaryIdentityV1:
    inst_id = str(row.get("instId") or "").strip()
    if not inst_id:
        raise MonetaryNormalizationError(REASON_INSTRUMENT_MONETARY_IDENTITY_MISSING)
    inst_type = str(row.get("instType") or "").strip().upper()
    ct_type = str(row.get("ctType") or "").strip().lower()
    if ct_type != "linear":
        raise MonetaryNormalizationError(f"{REASON_INSTRUMENT_MONETARY_IDENTITY_MISSING}:ctType")
    quote = _require_currency(row, "quoteCcy", "settleCcy", field="quote")
    try:
        base = _require_currency(row, "baseCcy", field="base")
    except MonetaryNormalizationError:
        base = _require_currency(row, "ctValCcy", field="base")
    settle = _require_currency(row, "settleCcy", "quoteCcy", field="settle")
    ct_val = _require_decimal_field(row, "ctVal")
    ct_val_ccy = _require_currency(row, "ctValCcy", field="ctValCcy")
    digest_material = {
        "instId": inst_id,
        "instType": inst_type,
        "ctType": ct_type,
        "base": base,
        "quote": quote,
        "settle": settle,
        "ctVal": str(ct_val),
        "ctValCcy": ct_val_ccy,
    }
    digest = hashlib.sha256(
        json.dumps(digest_material, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    return InstrumentMonetaryIdentityV1(
        inst_id=inst_id,
        inst_type=inst_type,
        ct_type=ct_type,
        base_currency=base,
        quote_currency=quote,
        settle_currency=settle,
        ct_val=ct_val,
        ct_val_currency=ct_val_ccy,
        instrument_money_unit=quote,
        metadata_digest=digest,
    )


def instrument_monetary_identity_from_okx_payload_v1(
    payload: Any,
    *,
    venue_native_id: str,
) -> InstrumentMonetaryIdentityV1:
    wanted = str(venue_native_id or "").strip()
    row = _find_row(payload, wanted_inst_id=wanted)
    if not row:
        row = _first_row(payload)
        if str(row.get("instId") or "").strip() != wanted:
            raise MonetaryNormalizationError(REASON_INSTRUMENT_MONETARY_IDENTITY_MISSING)
    return instrument_monetary_identity_from_okx_row_v1(row)


def conversion_pair_monetary_identity_from_okx_payload_v1(
    payload: Any,
    *,
    pair_native_id: str,
) -> tuple[str, str]:
    """Return (base_currency, quote_currency) for the USDT/USDC conversion pair instrument."""
    row = _find_row(payload, wanted_inst_id=str(pair_native_id or "").strip())
    if not row:
        raise MonetaryNormalizationError(REASON_INSTRUMENT_MONETARY_IDENTITY_MISSING)
    identity = instrument_monetary_identity_from_okx_row_v1(row)
    return identity.base_currency, identity.quote_currency
