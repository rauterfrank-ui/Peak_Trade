"""Explicit USD-index / USDC contractual payoff, never a spot FX rate.

The EEA linear X-Perp formula computes PnL and margin in selected margin.
The account FAQ names the selected currency for PnL, fees, funding and margin.
This narrowly scoped binding combines that rule with the original private
account and instrument observations. It does not prove a booked payment.
"""

from dataclasses import asdict, dataclass, replace
from decimal import Decimal
import json

from .contracts_v1 import MonetaryAmountV1, MonetaryNormalizationError
from .instrument_monetary_identity_v1 import instrument_monetary_identity_from_okx_payload_v1

RULE_ID = "OKX_EEA_LINEAR_XPERP_SELECTED_MARGIN_V1"
FORMULA_SOURCE = "https://www.okx.com/en-eu/help/calculation-of-contracts-profit-and-loss-eea"
CURRENCY_SOURCE = "https://www.okx.com/en-eu/help/faq-on-usd-margined-futures-contracts"


@dataclass(frozen=True)
class XperpSettlementRuleV1:
    account_identity: str
    venue_native_id: str
    observation_digest: str
    quote_currency: str = "USD"
    settlement_currency: str = "USDC"
    rule_id: str = RULE_ID

    def cash_multiplier_v1(self, quote_currency: str) -> Decimal:
        if quote_currency != self.quote_currency:
            raise MonetaryNormalizationError("XPERP_QUOTED_PRICE_UNIT_MISMATCH")
        # Contractual payoff coefficient, NOT USD/USDC spot-market parity.
        # A unit of base exposure times one quoted price unit pays one unit
        # of selected margin under the bound linear payoff rule.
        return Decimal(1)

    def cash_operand_v1(self, quoted: MonetaryAmountV1) -> MonetaryAmountV1:
        return MonetaryAmountV1(
            quoted.amount * self.cash_multiplier_v1(quoted.currency), self.settlement_currency
        )


def bind_xperp_settlement_rule_v1(
    sources_json, *, instruments_payload, venue_native_id, decision_epoch, evaluated_at_utc
):
    # Local import avoids reversing the cost owner's import-time dependency.
    from src.ops.portfolio_capital_reservation_budget_v1 import entry_execution_cost_v1 as cost

    raw = json.loads(sources_json)
    if set(raw) != {"account", "instruments"}:
        raise MonetaryNormalizationError("XPERP_ORIGINAL_PRIVATE_SOURCES_REQUIRED")
    account_source, instrument_source = (
        cost.FreshPretradeGetTransportResultV1(**raw[key]) for key in ("account", "instruments")
    )
    for source in (account_source, instrument_source):
        if (
            source.method != "GET"
            or source.get_performed is not True
            or source.http_status != 200
            or source.auth_header_sent is not True
            or source.historical_reuse is not False
            or source.error_class
        ):
            raise MonetaryNormalizationError("XPERP_ORIGINAL_PRIVATE_SOURCES_REQUIRED")
        cost.acquisition_age_seconds_v1(
            acquired_at_utc=decision_epoch, now_utc=source.acquired_at_utc
        )
        cost.acquisition_age_seconds_v1(
            acquired_at_utc=source.acquired_at_utc, now_utc=evaluated_at_utc
        )
    if cost._query(account_source.endpoint, "/api/v5/account/config") != {}:
        raise MonetaryNormalizationError("XPERP_ACCOUNT_QUERY_MISMATCH")
    if cost._query(instrument_source.endpoint, "/api/v5/account/instruments") != {
        "instType": ["FUTURES"],
        "instId": [venue_native_id],
    }:
        raise MonetaryNormalizationError("XPERP_INSTRUMENT_QUERY_MISMATCH")
    account_rows = cost._rows(account_source.payload)
    if len(account_rows) != 1 or not account_rows[0].get("uid"):
        raise MonetaryNormalizationError("XPERP_ACCOUNT_REQUIRED")
    account = account_rows[0]
    instrument = cost._one(cost._rows(instrument_source.payload), "instId", venue_native_id)
    if instrument_source.payload != instruments_payload:
        raise MonetaryNormalizationError("XPERP_INSTRUMENT_ORIGINAL_MISMATCH")
    cost._instrument_source_path_v1(instrument_source, instrument, account)
    if (
        instrument.get("ctMult") != "1"
        or Decimal(instrument["ctVal"]) <= 0
        or instrument.get("state") != "live"
    ):
        raise MonetaryNormalizationError("XPERP_LINEAR_PAYOFF_UNSUPPORTED")
    rule = XperpSettlementRuleV1(account["uid"], venue_native_id, cost.digest(raw))
    identity = instrument_monetary_identity_from_okx_payload_v1(
        instruments_payload, venue_native_id=venue_native_id
    )
    # USD is proven by the validated original underlying; it is not replaced
    # with the selected settlement currency from a blank quoteCcy field.
    identity = replace(
        identity,
        quote_currency="USD",
        instrument_money_unit="USD",
        metadata_digest=cost.digest(dict(original=identity.metadata_digest, rule=asdict(rule))),
    )
    return rule, identity
