"""Venue-derived minimum-exposure order plan for §11.13.5. No invented numeric policy."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from decimal import Decimal, ROUND_DOWN, InvalidOperation
from typing import Any, Mapping

from src.ops.okx_europe_adapter_lifecycle_contract_v0 import (
    CLIENT_ORDER_ID_ALLOWED_PATTERN,
    CLIENT_ORDER_ID_MAX_LENGTH,
    build_client_order_id,
)
from src.ops.section_11_12_8_actual_productive_testnet_campaign_run_start_v1.okx_response_mapper_v1 import (
    OkxResponseMapperError,
    build_venue_native_order_body_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.constants_v1 import (
    DEFAULT_INSTRUMENT_ID,
    DEFAULT_INST_TYPE,
    DEFAULT_ORDER_TYPE,
    DEFAULT_RULE_TYPE,
    DEFAULT_SIDE,
    DEFAULT_TD_MODE,
    LiveCanaryInstrumentBindingError,
    REUSED_BINDING_ACCOUNT_SCOPE,
    REUSED_BINDING_REST_HOST,
    REUSED_BINDING_VENUE,
    assert_live_canary_instrument_binding_v1,
    public_instruments_query_path_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.exposure_v1 import (
    LiveCanaryExposureError,
    build_canary_exposure_binding_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.pre_submit_state_v1 import (
    LiveCanaryPositionObservationError,
    observe_target_position_flatten_candidate_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.max_size_consumer_v1 import (
    LiveCanaryMaxSizeConsumerError,
    apply_fresh_max_size_pretrade_gate_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.venue_contract_count_v1 import (
    ORDER_PLAN_QTY_DOMAIN,
    ORDER_PLAN_QTY_UNIT,
    LiveCanaryVenueContractCountError,
    assert_identity_sz_after_contract_sizing_v1,
    serialize_venue_sz_from_typed_contract_count_v1,
)


class LiveCanaryOrderPlanError(RuntimeError):
    """Fail-closed canary order-plan violation."""


def _dec(raw: Any, *, field: str) -> Decimal:
    try:
        value = Decimal(str(raw))
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise LiveCanaryOrderPlanError(f"INVALID_DECIMAL:{field}") from exc
    if value <= 0:
        raise LiveCanaryOrderPlanError(f"NON_POSITIVE:{field}")
    return value


def extract_instrument_constraints_v1(
    *,
    instruments_payload: Mapping[str, Any],
    instrument_id: str = DEFAULT_INSTRUMENT_ID,
) -> dict[str, str]:
    try:
        assert_live_canary_instrument_binding_v1(instrument_id=instrument_id)
    except LiveCanaryInstrumentBindingError as exc:
        raise LiveCanaryOrderPlanError(str(exc)) from exc
    if str(instruments_payload.get("code") or "") != "0":
        raise LiveCanaryOrderPlanError("INSTRUMENTS_PAYLOAD_NOT_OK")
    data = instruments_payload.get("data")
    if not isinstance(data, list) or not data:
        raise LiveCanaryOrderPlanError("INSTRUMENTS_DATA_MISSING")
    row = None
    for item in data:
        if isinstance(item, Mapping) and str(item.get("instId") or "") == instrument_id:
            row = item
            break
    if row is None:
        raise LiveCanaryOrderPlanError(f"INSTRUMENT_NOT_FOUND:{instrument_id}")
    row_type = str(row.get("instType") or "").strip().upper()
    try:
        assert_live_canary_instrument_binding_v1(
            instrument_id=instrument_id,
            inst_type=row_type or DEFAULT_INST_TYPE,
            rule_type=str(row.get("ruleType") or "") or None,
        )
    except LiveCanaryInstrumentBindingError as exc:
        raise LiveCanaryOrderPlanError(str(exc)) from exc
    if row_type and row_type != DEFAULT_INST_TYPE:
        raise LiveCanaryOrderPlanError(f"INST_TYPE_BINDING_MISMATCH:{row_type}")
    rule = str(row.get("ruleType") or "").strip()
    if rule and rule != DEFAULT_RULE_TYPE:
        raise LiveCanaryOrderPlanError(f"RULE_TYPE_BINDING_MISMATCH:{rule}")
    required = ("minSz", "lotSz", "tickSz", "ctVal")
    out: dict[str, str] = {}
    for key in required:
        val = str(row.get(key) or "").strip()
        if not val:
            raise LiveCanaryOrderPlanError(f"INSTRUMENT_FIELD_MISSING:{key}")
        out[key] = val
    for key in ("minSz", "lotSz"):
        parsed = _dec(out[key], field=key)
        if parsed != parsed.to_integral_value():
            raise LiveCanaryOrderPlanError(f"INTEGER_CONTRACT_REQUIRED:{key}")
    ct_ccy = str(row.get("ctValCcy") or "").strip()
    if ct_ccy:
        out["ctValCcy"] = ct_ccy
    out["instType"] = row_type or DEFAULT_INST_TYPE
    if rule:
        out["ruleType"] = rule
    return out


def extract_reference_price_v1(*, ticker_payload: Mapping[str, Any]) -> str:
    if str(ticker_payload.get("code") or "") != "0":
        raise LiveCanaryOrderPlanError("TICKER_PAYLOAD_NOT_OK")
    data = ticker_payload.get("data")
    if not isinstance(data, list) or not data or not isinstance(data[0], Mapping):
        raise LiveCanaryOrderPlanError("TICKER_DATA_MISSING")
    last = str(data[0].get("last") or data[0].get("askPx") or "").strip()
    if not last:
        raise LiveCanaryOrderPlanError("TICKER_LAST_MISSING")
    return last


def quantize_limit_price_v1(*, reference_price: str, tick_sz: str) -> str:
    px = _dec(reference_price, field="reference_price")
    tick = _dec(tick_sz, field="tick_sz")
    steps = (px / tick).to_integral_value(rounding=ROUND_DOWN)
    if steps <= 0:
        raise LiveCanaryOrderPlanError("LIMIT_PRICE_NON_POSITIVE_AFTER_TICK")
    return format(steps * tick, "f")


def serialize_canary_clordid_v1(*, owner_go: str, origin_main_sha: str) -> str:
    material = hashlib.sha256(f"{owner_go}:{origin_main_sha}".encode("utf-8")).hexdigest()
    coid = build_client_order_id(
        run_id=material,
        session_id=material,
        intent_id=material,
        environment="LIVE",
        instrument_id=DEFAULT_INSTRUMENT_ID,
        sequence=0,
    )
    if not coid or len(coid) > CLIENT_ORDER_ID_MAX_LENGTH:
        raise LiveCanaryOrderPlanError("CLORDID_LENGTH_VIOLATION")
    if not CLIENT_ORDER_ID_ALLOWED_PATTERN.fullmatch(coid):
        raise LiveCanaryOrderPlanError("CLORDID_ALPHANUMERIC_VIOLATION")
    return coid


def serialize_canary_flatten_clordid_v1(*, owner_go: str, origin_main_sha: str) -> str:
    material = hashlib.sha256(f"{owner_go}:{origin_main_sha}:FLATTEN".encode("utf-8")).hexdigest()
    coid = build_client_order_id(
        run_id=material,
        session_id=material,
        intent_id=material,
        environment="LIVE",
        instrument_id=DEFAULT_INSTRUMENT_ID,
        sequence=1,
    )
    if not coid or len(coid) > CLIENT_ORDER_ID_MAX_LENGTH:
        raise LiveCanaryOrderPlanError("FLATTEN_CLORDID_LENGTH_VIOLATION")
    if not CLIENT_ORDER_ID_ALLOWED_PATTERN.fullmatch(coid):
        raise LiveCanaryOrderPlanError("FLATTEN_CLORDID_ALPHANUMERIC_VIOLATION")
    return coid


@dataclass(frozen=True)
class CanaryOrderPlanV1:
    instrument_id: str
    side: str
    order_type: str
    td_mode: str
    quantity: str
    quantity_domain: str
    quantity_unit: str
    limit_price: str
    min_sz: str
    lot_sz: str
    tick_sz: str
    ct_val: str
    ct_val_ccy: str | None
    min_executable_notional: str
    max_notional: str
    clordid: str
    venue_native_payload: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "instrument_id": self.instrument_id,
            "side": self.side,
            "order_type": self.order_type,
            "td_mode": self.td_mode,
            "quantity": self.quantity,
            "quantity_domain": self.quantity_domain,
            "quantity_unit": self.quantity_unit,
            "limit_price": self.limit_price,
            "min_sz": self.min_sz,
            "lot_sz": self.lot_sz,
            "tick_sz": self.tick_sz,
            "ct_val": self.ct_val,
            "ct_val_ccy": self.ct_val_ccy,
            "min_executable_notional": self.min_executable_notional,
            "max_notional": self.max_notional,
            "clordid": self.clordid,
            "venue_native_payload": dict(self.venue_native_payload),
        }


def build_minimum_valid_canary_order_plan_v1(
    *,
    instruments_payload: Mapping[str, Any],
    ticker_payload: Mapping[str, Any],
    owner_go: str,
    origin_main_sha: str,
    pretrade_decision_id: str,
    instrument_id: str = DEFAULT_INSTRUMENT_ID,
    side: str = DEFAULT_SIDE,
    td_mode: str = DEFAULT_TD_MODE,
    max_size_http_status: int = 200,
    max_size_endpoint: str = "",
    max_size_observed_at_utc: str | None = None,
    max_size_get_performed: bool = True,
    max_size_auth_header_sent: bool = False,
    max_size_historical_reuse: bool = False,
    max_size_body_sha256: str = "",
) -> CanaryOrderPlanV1:
    constraints = extract_instrument_constraints_v1(
        instruments_payload=instruments_payload,
        instrument_id=instrument_id,
    )
    reference = extract_reference_price_v1(ticker_payload=ticker_payload)
    limit_px = quantize_limit_price_v1(reference_price=reference, tick_sz=constraints["tickSz"])
    try:
        exposure = build_canary_exposure_binding_v1(
            venue=REUSED_BINDING_VENUE,
            account_scope=REUSED_BINDING_ACCOUNT_SCOPE,
            instrument_id=instrument_id,
            side=side,
            order_type=DEFAULT_ORDER_TYPE,
            td_mode=td_mode,
            instrument_min_sz=constraints["minSz"],
            instrument_lot_sz=constraints["lotSz"],
            instrument_ct_val=constraints["ctVal"],
            instrument_tick_sz=constraints["tickSz"],
            reference_price=limit_px,
        )
    except LiveCanaryExposureError as exc:
        raise LiveCanaryOrderPlanError(f"UNSAFE_QUANTITY:{exc}") from exc
    try:
        apply_fresh_max_size_pretrade_gate_v1(
            pretrade_decision_id=pretrade_decision_id,
            instruments_payload=instruments_payload,
            instrument_id=instrument_id,
            order_type=DEFAULT_ORDER_TYPE,
            venue_contract_count=exposure.quantity,
            quantity_domain=exposure.quantity_domain,
            http_status=max_size_http_status,
            endpoint=max_size_endpoint
            or public_instruments_query_path_v1(
                instrument_id=instrument_id, inst_type=DEFAULT_INST_TYPE
            ),
            observed_at_utc=max_size_observed_at_utc,
            get_performed=max_size_get_performed,
            rest_host=REUSED_BINDING_REST_HOST,
            auth_header_sent=max_size_auth_header_sent,
            historical_reuse=max_size_historical_reuse,
            body_sha256=max_size_body_sha256,
        )
    except LiveCanaryMaxSizeConsumerError as exc:
        raise LiveCanaryOrderPlanError(f"MAX_SIZE_GATE:{exc}") from exc
    clordid = serialize_canary_clordid_v1(owner_go=owner_go, origin_main_sha=origin_main_sha)
    try:
        typed_sz = serialize_venue_sz_from_typed_contract_count_v1(
            venue_contract_count=exposure.quantity,
            quantity_domain=exposure.quantity_domain,
        )
        payload = build_venue_native_order_body_v1(
            client_order_id=clordid,
            instrument=instrument_id,
            order_type=DEFAULT_ORDER_TYPE,
            side=side,
            quantity=typed_sz,
            td_mode=td_mode,
            px=limit_px,
        )
        if isinstance(payload, dict) and "sz" in payload:
            assert_identity_sz_after_contract_sizing_v1(
                quantity=exposure.quantity,
                sz=str(payload.get("sz") or ""),
                quantity_domain=exposure.quantity_domain,
            )
    except LiveCanaryVenueContractCountError as exc:
        raise LiveCanaryOrderPlanError(f"VENUE_SZ_IDENTITY:{exc}") from exc
    except OkxResponseMapperError as exc:
        raise LiveCanaryOrderPlanError(f"VENUE_NATIVE_BODY:{exc}") from exc
    return CanaryOrderPlanV1(
        instrument_id=instrument_id,
        side=str(side).upper(),
        order_type="LIMIT",
        td_mode=td_mode,
        quantity=exposure.quantity,
        quantity_domain=exposure.quantity_domain or ORDER_PLAN_QTY_DOMAIN,
        quantity_unit=exposure.quantity_unit or ORDER_PLAN_QTY_UNIT,
        limit_price=limit_px,
        min_sz=constraints["minSz"],
        lot_sz=constraints["lotSz"],
        tick_sz=constraints["tickSz"],
        ct_val=constraints["ctVal"],
        ct_val_ccy=constraints.get("ctValCcy"),
        min_executable_notional=exposure.min_executable_notional,
        max_notional=exposure.max_notional,
        clordid=clordid,
        venue_native_payload=payload,
    )


# Quote-lock LIMIT policy is implemented (Z2AL). This status is only the
# naked qty-plan / no-FlattenPricePermitV1 fail-closed gate. It is not a
# claim that price policy awaits a separate Owner GO. Live wire remains
# disabled. Entry max-size freshness is per-decision GET, not a cache.
FLATTEN_LIMIT_PRICE_GATE_STATUS = "NAKED_PX_FAIL_CLOSED_PRICE_PERMIT_REQUIRED"
FLATTEN_NAKED_PX_FAIL_CLOSED_REASON = (
    "FLATTEN_NAKED_PX_FAIL_CLOSED:" + FLATTEN_LIMIT_PRICE_GATE_STATUS
)


def _format_flatten_qty(value: Decimal) -> str:
    if value <= 0:
        raise LiveCanaryOrderPlanError("ZERO_POSITION_NO_FLATTEN_ORDER")
    integral = value.to_integral_value()
    if value == integral:
        return format(integral, "f")
    return format(value, "f")


@dataclass(frozen=True)
class CanaryFlattenOrderPlanV1:
    """Offline flatten plan. Not runtime-reachable and not price-authorized."""

    instrument_id: str
    side: str
    order_type: str
    td_mode: str
    quantity: str
    reduce_only: bool
    clordid: str
    limit_price: None
    price_gate_status: str
    venue_native_payload: None
    submitted_entry_sz_used: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "instrument_id": self.instrument_id,
            "side": self.side,
            "order_type": self.order_type,
            "td_mode": self.td_mode,
            "quantity": self.quantity,
            "reduce_only": self.reduce_only,
            "clordid": self.clordid,
            "limit_price": self.limit_price,
            "price_gate_status": self.price_gate_status,
            "venue_native_payload": self.venue_native_payload,
            "submitted_entry_sz_used": self.submitted_entry_sz_used,
        }


def build_minimum_valid_canary_flatten_order_plan_v1(
    *,
    positions_payload: Mapping[str, Any],
    owner_go: str,
    origin_main_sha: str,
    instrument_id: str = DEFAULT_INSTRUMENT_ID,
    td_mode: str = DEFAULT_TD_MODE,
    submitted_entry_sz: str | None = None,
) -> CanaryFlattenOrderPlanV1:
    """Build an Entry-separated flatten plan from observed position only.

    ``submitted_entry_sz`` is accepted only so tests can prove it is ignored.
    No LIMIT price is bound. No venue-native payload is produced.
    """
    del submitted_entry_sz
    try:
        observed = observe_target_position_flatten_candidate_v1(
            positions_payload=positions_payload,
            instrument_id=instrument_id,
        )
    except LiveCanaryPositionObservationError as exc:
        raise LiveCanaryOrderPlanError(f"FLATTEN_OBSERVATION:{exc}") from exc
    clordid = serialize_canary_flatten_clordid_v1(
        owner_go=owner_go,
        origin_main_sha=origin_main_sha,
    )
    return CanaryFlattenOrderPlanV1(
        instrument_id=observed.instrument_id,
        side=observed.candidate_flatten_side,
        order_type="LIMIT",
        td_mode=td_mode,
        quantity=_format_flatten_qty(observed.candidate_flatten_qty),
        reduce_only=True,
        clordid=clordid,
        limit_price=None,
        price_gate_status=FLATTEN_LIMIT_PRICE_GATE_STATUS,
        venue_native_payload=None,
        submitted_entry_sz_used=False,
    )


def serialize_canary_flatten_venue_native_payload_v1(
    plan: CanaryFlattenOrderPlanV1,
    *,
    px: str | None = None,
    price_permit: Any | None = None,
) -> dict[str, Any]:
    """Build a reduce-only LIMIT flatten body only when a price permit is bound.

    A naked ``px`` without ``price_permit`` remains unbound. This serializer
    never POSTs and never emits MARKET.
    """
    if price_permit is None:
        del px
        raise LiveCanaryOrderPlanError(FLATTEN_NAKED_PX_FAIL_CLOSED_REASON)
    permit_side = str(getattr(price_permit, "flatten_side", "") or "").strip().upper()
    permit_px = str(getattr(price_permit, "limit_price", "") or "").strip()
    if permit_side != str(plan.side).upper():
        raise LiveCanaryOrderPlanError("FLATTEN_PRICE_PERMIT_SIDE_MISMATCH")
    if not permit_px:
        raise LiveCanaryOrderPlanError("FLATTEN_PRICE_PERMIT_PX_MISSING")
    if px is not None and str(px).strip() != permit_px:
        raise LiveCanaryOrderPlanError("FLATTEN_NAKED_PX_CONFLICTS_WITH_PERMIT")
    if str(plan.order_type).upper() != "LIMIT":
        raise LiveCanaryOrderPlanError("FLATTEN_MARKET_FALLBACK_FORBIDDEN")
    if plan.reduce_only is not True:
        raise LiveCanaryOrderPlanError("FLATTEN_PLAN_REDUCE_ONLY_REQUIRED")
    try:
        return build_venue_native_order_body_v1(
            client_order_id=plan.clordid,
            instrument=plan.instrument_id,
            order_type="LIMIT",
            side=plan.side,
            quantity=plan.quantity,
            td_mode=plan.td_mode,
            px=permit_px,
            reduce_only=True,
        )
    except OkxResponseMapperError as exc:
        raise LiveCanaryOrderPlanError(f"FLATTEN_VENUE_NATIVE_BODY:{exc}") from exc
