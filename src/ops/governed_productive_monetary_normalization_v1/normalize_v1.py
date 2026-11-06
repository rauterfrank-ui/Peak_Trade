"""Normalization seam: instrument-native + capital → CRS canonical numeraire."""

from __future__ import annotations

from decimal import Decimal
from typing import Any, Mapping

from src.ops.governed_productive_monetary_normalization_v1.constants_v1 import (
    CANONICAL_INTERNAL_RISK_NUMERAIRE,
    USDT_USDC_PAIR_NATIVE_ID,
)
from src.ops.governed_productive_monetary_normalization_v1.contracts_v1 import (
    REASON_DOUBLE_CONVERSION,
    REASON_NAKED_DECIMAL_FX,
    REASON_QUOTE_CURRENCY_MISMATCH,
    CapitalRiskSizingMonetaryContextV1,
    ConversionEdgeV1,
    InstrumentMonetaryIdentityV1,
    MonetaryAmountV1,
    MonetaryNormalizationError,
    monetary_context_digest_v1,
    require_monetary_amount_v1,
    validate_conversion_edge_v1,
)
from src.ops.governed_productive_monetary_normalization_v1.identity_edge_v1 import (
    build_usdc_identity_conversion_edge_v1,
)
from src.ops.governed_productive_monetary_normalization_v1.instrument_monetary_identity_v1 import (
    conversion_pair_monetary_identity_from_okx_payload_v1,
    instrument_monetary_identity_from_okx_payload_v1,
)
from src.ops.governed_productive_monetary_normalization_v1.usdt_usdc_index_observation_v1 import (
    build_usdt_usdc_conversion_edge_from_index_tickers_v1,
)

NORMALIZATION_OWNER = "ops.governed_productive_monetary_normalization_v1.normalize_v1"


def _scale_quote_price(
    native: MonetaryAmountV1,
    *,
    edge: ConversionEdgeV1,
    target_quote: str,
) -> MonetaryAmountV1:
    """Convert a quote-denominated price (quote/base) using USDC/USDT edge."""
    if native.currency != edge.source_currency:
        raise MonetaryNormalizationError(REASON_QUOTE_CURRENCY_MISMATCH)
    if target_quote != edge.target_currency:
        raise MonetaryNormalizationError(REASON_QUOTE_CURRENCY_MISMATCH)
    converted = native.amount * edge.normalized_rate
    if not converted.is_finite() or converted <= 0:
        raise MonetaryNormalizationError(REASON_QUOTE_CURRENCY_MISMATCH)
    return MonetaryAmountV1(amount=converted, currency=target_quote)


def build_capital_risk_sizing_monetary_context_v1(
    *,
    decision_epoch: str,
    observed_at: str,
    fresh_pretrade_get_status: str,
    account_equity_amount: Decimal,
    account_equity_currency: str,
    native_reference_price: Decimal,
    native_protective_stop_price: Decimal,
    instruments_payload: Mapping[str, Any],
    venue_native_id: str,
    index_tickers_payload: Mapping[str, Any] | None,
    conversion_pair_instruments_payload: Mapping[str, Any] | None = None,
    already_canonical: bool = False,
) -> CapitalRiskSizingMonetaryContextV1:
    """Build typed CRS monetary context; fail-closed on missing edge or mixed units."""
    if already_canonical:
        raise MonetaryNormalizationError(REASON_DOUBLE_CONVERSION)

    instrument_identity = instrument_monetary_identity_from_okx_payload_v1(
        instruments_payload,
        venue_native_id=venue_native_id,
    )
    pair_payload = conversion_pair_instruments_payload or instruments_payload
    pair_base, pair_quote = conversion_pair_monetary_identity_from_okx_payload_v1(
        pair_payload,
        pair_native_id=USDT_USDC_PAIR_NATIVE_ID,
    )

    identity_edge = build_usdc_identity_conversion_edge_v1(
        decision_epoch=decision_epoch,
        observed_at=observed_at,
        freshness_status=fresh_pretrade_get_status,
    )
    validate_conversion_edge_v1(identity_edge)

    equity_ccy = str(account_equity_currency or "").strip().upper()
    if equity_ccy != CANONICAL_INTERNAL_RISK_NUMERAIRE:
        raise MonetaryNormalizationError(REASON_QUOTE_CURRENCY_MISMATCH)
    account_equity = MonetaryAmountV1(
        amount=Decimal(str(account_equity_amount)),
        currency=CANONICAL_INTERNAL_RISK_NUMERAIRE,
    )

    native_ref = MonetaryAmountV1(
        amount=Decimal(str(native_reference_price)),
        currency=instrument_identity.instrument_money_unit,
    )
    native_stop = MonetaryAmountV1(
        amount=Decimal(str(native_protective_stop_price)),
        currency=instrument_identity.instrument_money_unit,
    )

    usdt_edge: ConversionEdgeV1 | None = None
    canonical_ref = native_ref
    canonical_stop = native_stop

    if instrument_identity.instrument_money_unit == CANONICAL_INTERNAL_RISK_NUMERAIRE:
        if native_ref.currency != CANONICAL_INTERNAL_RISK_NUMERAIRE:
            raise MonetaryNormalizationError(REASON_QUOTE_CURRENCY_MISMATCH)
    elif instrument_identity.instrument_money_unit == "USDT":
        usdt_edge = build_usdt_usdc_conversion_edge_from_index_tickers_v1(
            index_tickers_payload=index_tickers_payload,
            decision_epoch=decision_epoch,
            observed_at=observed_at,
            fresh_pretrade_get_status=fresh_pretrade_get_status,
            pair_base_currency=pair_base,
            pair_quote_currency=pair_quote,
        )
        canonical_ref = _scale_quote_price(
            native_ref,
            edge=usdt_edge,
            target_quote=CANONICAL_INTERNAL_RISK_NUMERAIRE,
        )
        canonical_stop = _scale_quote_price(
            native_stop,
            edge=usdt_edge,
            target_quote=CANONICAL_INTERNAL_RISK_NUMERAIRE,
        )
    else:
        raise MonetaryNormalizationError(
            f"NORMALIZATION_UNAVAILABLE_FOR_{instrument_identity.instrument_money_unit}"
        )

    ctx = CapitalRiskSizingMonetaryContextV1(
        canonical_numeraire=CANONICAL_INTERNAL_RISK_NUMERAIRE,
        account_equity=account_equity,
        reference_price=canonical_ref,
        protective_stop_price=canonical_stop,
        instrument_money_unit=instrument_identity.instrument_money_unit,
        native_reference_price=native_ref,
        native_protective_stop_price=native_stop,
        usdt_usdc_edge=usdt_edge,
        usdc_identity_edge=identity_edge,
        normalization_digest="",
    )
    digest = monetary_context_digest_v1(ctx)
    return CapitalRiskSizingMonetaryContextV1(
        canonical_numeraire=ctx.canonical_numeraire,
        account_equity=ctx.account_equity,
        reference_price=ctx.reference_price,
        protective_stop_price=ctx.protective_stop_price,
        instrument_money_unit=ctx.instrument_money_unit,
        native_reference_price=ctx.native_reference_price,
        native_protective_stop_price=ctx.native_protective_stop_price,
        usdt_usdc_edge=ctx.usdt_usdc_edge,
        usdc_identity_edge=ctx.usdc_identity_edge,
        normalization_digest=digest,
    )


def crs_operands_from_monetary_context_v1(
    ctx: CapitalRiskSizingMonetaryContextV1,
) -> tuple[Decimal, Decimal, Decimal]:
    """Return (account_equity, reference_price, protective_stop) for CRS boundary."""
    eq = require_monetary_amount_v1(ctx.account_equity, field="account_equity")
    ref = require_monetary_amount_v1(ctx.reference_price, field="reference_price")
    stop = require_monetary_amount_v1(ctx.protective_stop_price, field="protective_stop_price")
    if eq.currency != CANONICAL_INTERNAL_RISK_NUMERAIRE:
        raise MonetaryNormalizationError(REASON_QUOTE_CURRENCY_MISMATCH)
    if ref.currency != CANONICAL_INTERNAL_RISK_NUMERAIRE:
        raise MonetaryNormalizationError(REASON_NAKED_DECIMAL_FX)
    if stop.currency != CANONICAL_INTERNAL_RISK_NUMERAIRE:
        raise MonetaryNormalizationError(REASON_NAKED_DECIMAL_FX)
    return eq.amount, ref.amount, stop.amount
