"""Typed monetary contracts for normalization seam."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, fields
from decimal import Decimal
from typing import Any, Mapping

from src.ops.governed_productive_monetary_normalization_v1.constants_v1 import (
    AUTHORITY_SEMANTIC_IDENTITY,
    AUTHORITY_SEMANTIC_MONETARY_NORMALIZATION,
    CANONICAL_INTERNAL_RISK_NUMERAIRE,
    NORMALIZED_RATE_UNIT_USDC_PER_USDT,
    RAW_RATE_UNIT_USDT_PER_USDC,
    USDT_USDC_ENDPOINT,
    USDT_USDC_SOURCE_FIELD,
    USDT_USDC_SOURCE_IDENTITY,
    USDT_USDC_VENUE,
)

REASON_MISSING_EDGE = "MISSING_EDGE"
REASON_UNKNOWN_SOURCE_CURRENCY = "UNKNOWN_SOURCE_CURRENCY"
REASON_UNKNOWN_TARGET_CURRENCY = "UNKNOWN_TARGET_CURRENCY"
REASON_UNKNOWN_RATE_UNIT = "UNKNOWN_RATE_UNIT"
REASON_AMBIGUOUS_DIRECTION = "AMBIGUOUS_DIRECTION"
REASON_NON_POSITIVE_RATE = "NON_POSITIVE_RATE"
REASON_STALE_RATE = "STALE_RATE"
REASON_EPOCH_MISMATCH = "EPOCH_MISMATCH"
REASON_UNAUTHORIZED_SOURCE = "UNAUTHORIZED_SOURCE"
REASON_MISSING_PROVENANCE = "MISSING_PROVENANCE"
REASON_MISSING_SOURCE_TIMESTAMP = "MISSING_SOURCE_TIMESTAMP"
REASON_INSTRUMENT_MONETARY_IDENTITY_MISSING = "INSTRUMENT_MONETARY_IDENTITY_MISSING"
REASON_QUOTE_CURRENCY_MISMATCH = "QUOTE_CURRENCY_MISMATCH"
REASON_CONVERSION_TARGET_NOT_NUMERAIRE = "CONVERSION_TARGET_NOT_CANONICAL_NUMERAIRE"
REASON_DOUBLE_CONVERSION = "DOUBLE_CONVERSION_REJECTED"
REASON_NAKED_DECIMAL_FX = "NAKED_DECIMAL_FX_REJECTED"
REASON_MALFORMED_RATE = "MALFORMED_RATE"


class MonetaryNormalizationError(RuntimeError):
    """Fail-closed monetary normalization violation."""


@dataclass(frozen=True)
class MonetaryAmountV1:
    amount: Decimal
    currency: str

    def __post_init__(self) -> None:
        if not isinstance(self.amount, Decimal):
            object.__setattr__(self, "amount", Decimal(str(self.amount)))
        if not self.amount.is_finite():
            raise MonetaryNormalizationError(REASON_MALFORMED_RATE)
        if not str(self.currency or "").strip():
            raise MonetaryNormalizationError(REASON_UNKNOWN_SOURCE_CURRENCY)


@dataclass(frozen=True)
class ConversionEdgeV1:
    source_currency: str
    target_currency: str
    raw_rate: Decimal
    raw_rate_unit: str
    normalized_rate: Decimal
    normalized_rate_unit: str
    inversion_applied: bool
    venue: str
    endpoint: str
    source_identity: str
    source_field: str
    source_timestamp: str
    observed_at: str
    decision_epoch: str
    freshness_status: str
    payload_digest: str
    provenance_ref: str
    authority_semantic: str


@dataclass(frozen=True)
class InstrumentMonetaryIdentityV1:
    inst_id: str
    inst_type: str
    ct_type: str
    base_currency: str
    quote_currency: str
    settle_currency: str
    ct_val: Decimal
    ct_val_currency: str
    instrument_money_unit: str
    metadata_digest: str


@dataclass(frozen=True)
class CapitalRiskSizingMonetaryContextV1:
    """CRS operands after normalization — all in canonical risk numeraire where required."""

    canonical_numeraire: str
    account_equity: MonetaryAmountV1
    reference_price: MonetaryAmountV1
    protective_stop_price: MonetaryAmountV1
    instrument_money_unit: str
    native_reference_price: MonetaryAmountV1
    native_protective_stop_price: MonetaryAmountV1
    usdt_usdc_edge: ConversionEdgeV1 | None
    usdc_identity_edge: ConversionEdgeV1
    normalization_digest: str


def _sha256_mapping(payload: Mapping[str, Any]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def conversion_edge_digest_v1(edge: ConversionEdgeV1) -> str:
    payload = {
        field.name: getattr(edge, field.name)
        for field in fields(ConversionEdgeV1)
        if isinstance(getattr(edge, field.name), (str, bool, Decimal))
    }
    payload["raw_rate"] = str(edge.raw_rate)
    payload["normalized_rate"] = str(edge.normalized_rate)
    return _sha256_mapping(payload)


def validate_conversion_edge_v1(edge: ConversionEdgeV1) -> None:
    if not str(edge.source_currency or "").strip():
        raise MonetaryNormalizationError(REASON_UNKNOWN_SOURCE_CURRENCY)
    if not str(edge.target_currency or "").strip():
        raise MonetaryNormalizationError(REASON_UNKNOWN_TARGET_CURRENCY)
    if (
        not str(edge.raw_rate_unit or "").strip()
        or not str(edge.normalized_rate_unit or "").strip()
    ):
        raise MonetaryNormalizationError(REASON_UNKNOWN_RATE_UNIT)
    if (
        edge.endpoint != USDT_USDC_ENDPOINT
        and edge.authority_semantic != AUTHORITY_SEMANTIC_IDENTITY
    ):
        raise MonetaryNormalizationError(REASON_UNAUTHORIZED_SOURCE)
    if edge.authority_semantic == AUTHORITY_SEMANTIC_MONETARY_NORMALIZATION:
        if (
            edge.source_identity != USDT_USDC_SOURCE_IDENTITY
            or edge.source_field != USDT_USDC_SOURCE_FIELD
        ):
            raise MonetaryNormalizationError(REASON_UNAUTHORIZED_SOURCE)
        if edge.raw_rate_unit != RAW_RATE_UNIT_USDT_PER_USDC:
            raise MonetaryNormalizationError(REASON_AMBIGUOUS_DIRECTION)
        if edge.normalized_rate_unit != NORMALIZED_RATE_UNIT_USDC_PER_USDT:
            raise MonetaryNormalizationError(REASON_AMBIGUOUS_DIRECTION)
    if not edge.raw_rate.is_finite() or edge.raw_rate <= 0:
        raise MonetaryNormalizationError(REASON_NON_POSITIVE_RATE)
    if not edge.normalized_rate.is_finite() or edge.normalized_rate <= 0:
        raise MonetaryNormalizationError(REASON_NON_POSITIVE_RATE)
    if not str(edge.provenance_ref or "").strip() or not str(edge.payload_digest or "").strip():
        raise MonetaryNormalizationError(REASON_MISSING_PROVENANCE)
    if not str(edge.decision_epoch or "").strip():
        raise MonetaryNormalizationError(REASON_EPOCH_MISMATCH)
    if edge.authority_semantic == AUTHORITY_SEMANTIC_MONETARY_NORMALIZATION:
        if not str(edge.source_timestamp or "").strip():
            raise MonetaryNormalizationError(REASON_MISSING_SOURCE_TIMESTAMP)
    if edge.target_currency != CANONICAL_INTERNAL_RISK_NUMERAIRE and edge.authority_semantic != (
        AUTHORITY_SEMANTIC_IDENTITY
    ):
        raise MonetaryNormalizationError(REASON_CONVERSION_TARGET_NOT_NUMERAIRE)


def require_monetary_amount_v1(value: object, *, field: str) -> MonetaryAmountV1:
    if isinstance(value, MonetaryAmountV1):
        return value
    raise MonetaryNormalizationError(f"{REASON_NAKED_DECIMAL_FX}:{field}")


def monetary_context_digest_v1(ctx: CapitalRiskSizingMonetaryContextV1) -> str:
    material = {
        "numeraire": ctx.canonical_numeraire,
        "equity": str(ctx.account_equity.amount),
        "equity_ccy": ctx.account_equity.currency,
        "ref": str(ctx.reference_price.amount),
        "ref_ccy": ctx.reference_price.currency,
        "stop": str(ctx.protective_stop_price.amount),
        "stop_ccy": ctx.protective_stop_price.currency,
        "instrument_money_unit": ctx.instrument_money_unit,
        "usdc_identity": conversion_edge_digest_v1(ctx.usdc_identity_edge),
    }
    if ctx.usdt_usdc_edge is not None:
        material["usdt_usdc"] = conversion_edge_digest_v1(ctx.usdt_usdc_edge)
    return _sha256_mapping(material)
