"""Typed venue-contract-count domain for §11.13.5 canary order quantity.

Peak_Trade order-plan quantity is an executable venue order quantity
expressed as venue contract count. This is an Owner-ratified system
contract. It is not inferred from minSz==1, qty==\"1\", sz==\"1\", or
ctVal==1.

Canary contract sizing reuses the already-bound Z2BE/Z2BF object
``SUI_OPERATIVE_ORDER_SZ`` (unit ``CONTRACTS_SZ``). minSz is a floor.
lotSz is an increment admissibility check. Neither is a quantity source
and neither rewrites the typed count.
"""

from __future__ import annotations

from decimal import Decimal, InvalidOperation
from typing import Any, Mapping

ORDER_PLAN_QTY_SEMANTIC = "executable venue order quantity expressed as venue contract count"
ORDER_PLAN_QTY_UNIT = "contracts"
ORDER_PLAN_QTY_DOMAIN = "VENUE_CONTRACT_COUNT"
VENUE_ORDER_SZ_MAPPING = "IDENTITY_AFTER_CONTRACT_SIZING"
CONTRACT_SIZING_PRODUCER = (
    "venue_contract_count_v1.canary_venue_contract_count_v1"
    "@exposure_v1.build_canary_exposure_binding_v1"
)
CONTRACT_SIZING_FORMULA = "venue_contract_count = SUI_OPERATIVE_ORDER_SZ"
SUI_OPERATIVE_ORDER_SZ = "1"
SUI_OPERATIVE_ORDER_SZ_UNIT = "CONTRACTS_SZ"
MAX_SIZE_COMPARISON_DOMAIN = "venue_contract_count"
ONE_CONTRACT_EQUALS_ONE_SUI = False
FORBIDDEN_UPGRADE_MINSZ_1_TO_OPERATIVE_QTY_1 = True
# Historical producer token from #6150. minSz equality is no longer the
# quantity source. The string remains named so prior adjudication guards
# can observe the retired policy without resurrecting it.
MINIMUM_EXPOSURE_REQUIRES_MIN_SZ_QUANTITY = "MINIMUM_EXPOSURE_REQUIRES_MIN_SZ_QUANTITY"


class LiveCanaryVenueContractCountError(RuntimeError):
    """Fail-closed typed venue-contract-count violation."""


def _dec(raw: Any, *, field: str) -> Decimal:
    try:
        value = Decimal(str(raw))
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise LiveCanaryVenueContractCountError(f"INVALID_DECIMAL:{field}") from exc
    if value <= 0:
        raise LiveCanaryVenueContractCountError(f"NON_POSITIVE:{field}")
    return value


def canary_venue_contract_count_v1() -> str:
    """Return the Owner-ratified canary venue contract count.

    Source is ``SUI_OPERATIVE_ORDER_SZ``, not ``minSz``.
    """
    return SUI_OPERATIVE_ORDER_SZ


def assert_venue_contract_count_admissible_v1(
    *,
    venue_contract_count: str,
    instrument_min_sz: str,
    instrument_lot_sz: str,
) -> str:
    """Admit a typed contract count against minSz floor and lotSz increment.

    Does not floor, ceil, or round. Does not copy minSz into the count.
    Does not require the count to equal minSz.
    """
    count = _dec(venue_contract_count, field="venue_contract_count")
    min_sz = _dec(instrument_min_sz, field="instrument_min_sz")
    lot = _dec(instrument_lot_sz, field="instrument_lot_sz")
    if count < min_sz:
        raise LiveCanaryVenueContractCountError("QUANTITY_BELOW_MIN_SZ")
    if (count % lot) != 0:
        raise LiveCanaryVenueContractCountError("QUANTITY_NOT_MULTIPLE_OF_LOT_SZ")
    return str(venue_contract_count)


def assert_canary_minimum_operative_contract_count_v1(*, venue_contract_count: str) -> str:
    """Canary minimum exposure must equal the Owner-ratified operative count."""
    count = _dec(venue_contract_count, field="venue_contract_count")
    operative = _dec(SUI_OPERATIVE_ORDER_SZ, field="sui_operative_order_sz")
    if count != operative:
        raise LiveCanaryVenueContractCountError(
            "MINIMUM_EXPOSURE_REQUIRES_OPERATIVE_CONTRACT_COUNT"
        )
    return str(venue_contract_count)


def serialize_venue_sz_from_typed_contract_count_v1(
    *,
    venue_contract_count: str,
    quantity_domain: str,
) -> str:
    """Identity-serialize a typed venue contract count to Place Order sz."""
    if str(quantity_domain) != ORDER_PLAN_QTY_DOMAIN:
        raise LiveCanaryVenueContractCountError("ORDER_PLAN_QTY_DOMAIN_NOT_VENUE_CONTRACT_COUNT")
    _dec(venue_contract_count, field="venue_contract_count")
    return str(venue_contract_count)


def assert_identity_sz_after_contract_sizing_v1(
    *,
    quantity: str,
    sz: str,
    quantity_domain: str,
) -> None:
    if str(quantity_domain) != ORDER_PLAN_QTY_DOMAIN:
        raise LiveCanaryVenueContractCountError("ORDER_PLAN_QTY_DOMAIN_NOT_VENUE_CONTRACT_COUNT")
    if str(sz) != str(quantity):
        raise LiveCanaryVenueContractCountError("SZ_NOT_IDENTITY_AFTER_CONTRACT_SIZING")
    expected = serialize_venue_sz_from_typed_contract_count_v1(
        venue_contract_count=quantity,
        quantity_domain=quantity_domain,
    )
    if str(sz) != expected:
        raise LiveCanaryVenueContractCountError("SZ_NOT_IDENTITY_AFTER_CONTRACT_SIZING")


def select_max_size_field_for_order_type_v1(*, order_type: str) -> str:
    ord_type = str(order_type or "").strip().upper()
    if ord_type == "LIMIT":
        return "maxLmtSz"
    if ord_type == "MARKET":
        return "maxMktSz"
    raise LiveCanaryVenueContractCountError(f"UNSUPPORTED_ORDER_TYPE_FOR_MAX_SIZE:{ord_type}")


def compare_venue_contract_count_to_max_size_v1(
    *,
    venue_contract_count: str,
    order_type: str,
    max_lmt_sz: str | None,
    max_mkt_sz: str | None,
) -> Mapping[str, Any]:
    """Compare typed venue contract count against venue max-size fields.

    LIMIT uses maxLmtSz. MARKET uses maxMktSz. This helper does not read
    live instruments, bind freshness, or become a runtime consumer.
    """
    count = _dec(venue_contract_count, field="venue_contract_count")
    field = select_max_size_field_for_order_type_v1(order_type=order_type)
    raw = max_lmt_sz if field == "maxLmtSz" else max_mkt_sz
    if raw is None or not str(raw).strip():
        raise LiveCanaryVenueContractCountError(f"MAX_SIZE_FIELD_MISSING:{field}")
    limit = _dec(raw, field=field)
    if count > limit:
        raise LiveCanaryVenueContractCountError(f"VENUE_CONTRACT_COUNT_EXCEEDS_{field.upper()}")
    return {
        "ok": True,
        "quantity_domain": ORDER_PLAN_QTY_DOMAIN,
        "comparison_domain": MAX_SIZE_COMPARISON_DOMAIN,
        "order_type": str(order_type).strip().upper(),
        "max_size_field": field,
        "venue_contract_count": str(venue_contract_count),
        "max_size_raw": str(raw),
    }
