"""Retain original monetary-normalization inputs with the original sizing hold.

No FX estimator, money movement or alternative sizing calculation. Readback
rebuilds the same original producers instead of trusting a stored currency label.
"""

from dataclasses import dataclass, asdict, fields
from decimal import Decimal
import json

from .contracts_v1 import MonetaryNormalizationError
from .normalize_v1 import (
    build_capital_risk_sizing_monetary_context_v1,
    crs_operands_from_monetary_context_v1,
)
from .instrument_monetary_identity_v1 import instrument_monetary_identity_from_okx_payload_v1
from src.ops.governed_productive_instrument_metadata_authority_producer_v1.current_productive_okx_instruments_row_producer_v1 import (
    produce_current_productive_instrument_quantity_constraints_from_okx_row_v1,
)


def _json(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)


@dataclass(frozen=True)
class SizingMonetarySourceV1:
    canonical_instrument_id: str
    venue_native_id: str
    decision_epoch: str
    observed_at: str
    fresh_pretrade_get_status: str
    account_equity_usdc: str
    native_reference_price: str
    native_protective_stop_price: str
    instruments_json: str
    index_tickers_json: str
    conversion_pair_instruments_json: str
    normalization_digest: str

    def rebuild_v1(self):
        if any(type(getattr(self, f.name)) is not str for f in fields(self)):
            raise ValueError("SIZING_MONETARY_SOURCE_STRING_FIELDS_REQUIRED")
        if any(not getattr(self, f.name) for f in fields(self)):
            raise ValueError("SIZING_MONETARY_SOURCE_INCOMPLETE")
        instruments = json.loads(self.instruments_json)
        ctx = build_capital_risk_sizing_monetary_context_v1(
            decision_epoch=self.decision_epoch,
            observed_at=self.observed_at,
            fresh_pretrade_get_status=self.fresh_pretrade_get_status,
            account_equity_amount=Decimal(self.account_equity_usdc),
            account_equity_currency="USDC",
            native_reference_price=Decimal(self.native_reference_price),
            native_protective_stop_price=Decimal(self.native_protective_stop_price),
            instruments_payload=instruments,
            venue_native_id=self.venue_native_id,
            index_tickers_payload=json.loads(self.index_tickers_json),
            conversion_pair_instruments_payload=json.loads(self.conversion_pair_instruments_json),
        )
        if ctx.normalization_digest != self.normalization_digest:
            raise ValueError("SIZING_MONETARY_SOURCE_NORMALIZATION_MISMATCH")
        identity = instrument_monetary_identity_from_okx_payload_v1(
            instruments, venue_native_id=self.venue_native_id
        )
        metadata = produce_current_productive_instrument_quantity_constraints_from_okx_row_v1(
            venue_native_id=self.venue_native_id,
            instruments_payload=instruments,
            observed_at_as_of=self.observed_at,
            bound_instrument_id=self.canonical_instrument_id,
        )
        if not metadata.produced or metadata.constraints is None:
            raise ValueError("SIZING_MONETARY_SOURCE_METADATA_INVALID")
        return ctx, identity, metadata.constraints

    def validate_sizing_v1(self, applied_input):
        ctx, identity, constraints = self.rebuild_v1()
        operands = crs_operands_from_monetary_context_v1(ctx)
        if (
            self.canonical_instrument_id != applied_input.instrument_id
            or self.venue_native_id != identity.inst_id
            or constraints != applied_input.instrument
            or operands
            != (
                applied_input.account_equity,
                applied_input.reference_price,
                applied_input.protective_stop_price,
            )
        ):
            raise ValueError("SIZING_MONETARY_SOURCE_OPERANDS_MISMATCH")
        return ctx

    def to_dict_v1(self):
        return {"schema": "sizing_monetary_source.v1", **asdict(self)}

    @classmethod
    def from_dict_v1(cls, value):
        if (
            not isinstance(value, dict)
            or set(value) != {"schema", *(f.name for f in fields(cls))}
            or value["schema"] != "sizing_monetary_source.v1"
        ):
            raise ValueError("SIZING_MONETARY_SOURCE_SCHEMA_INVALID")
        return cls(**{k: v for k, v in value.items() if k != "schema"})


def build_sizing_monetary_source_v1(
    *,
    canonical_instrument_id,
    venue_native_id,
    decision_epoch,
    observed_at,
    fresh_pretrade_get_status,
    account_equity_usdc,
    native_reference_price,
    native_protective_stop_price,
    instruments_payload,
    index_tickers_payload,
    conversion_pair_instruments_payload,
    normalization_digest,
):
    source = SizingMonetarySourceV1(
        canonical_instrument_id=canonical_instrument_id,
        venue_native_id=venue_native_id,
        decision_epoch=decision_epoch,
        observed_at=observed_at,
        fresh_pretrade_get_status=fresh_pretrade_get_status,
        account_equity_usdc=str(account_equity_usdc),
        native_reference_price=str(native_reference_price),
        native_protective_stop_price=str(native_protective_stop_price),
        instruments_json=_json(instruments_payload),
        index_tickers_json=_json(index_tickers_payload),
        conversion_pair_instruments_json=_json(conversion_pair_instruments_payload),
        normalization_digest=normalization_digest,
    )
    try:
        source.rebuild_v1()
    except (ValueError, TypeError, KeyError, ArithmeticError, MonetaryNormalizationError) as exc:
        raise ValueError("SIZING_MONETARY_SOURCE_BUILD_INVALID:" + str(exc)) from exc
    return source
