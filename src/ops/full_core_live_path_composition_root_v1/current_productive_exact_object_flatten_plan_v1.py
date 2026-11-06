"""CURRENT Full-Core exact-object reduce-only flatten plan. Offline. No POST.

Derives CLOSE/FLATTEN side and quantity from a fresh net occupancy row.
Does not import Canary/§11.13.5/§11.14 authority. Does not fabricate ENTER.

RUNTIME_AUTHORIZATION_EFFECT=NONE
"""

from __future__ import annotations

from decimal import Decimal, ROUND_CEILING, ROUND_FLOOR, InvalidOperation
from typing import Any, Mapping

from src.ops.full_core_live_path_composition_root_v1.final_order_envelope_v1 import (
    FinalOrderEnvelopeV1,
    build_final_order_envelope_v1,
)
from src.ops.full_core_live_path_composition_root_v1.models_v1 import VenuePlanCandidateV1
from src.ops.okx_europe_adapter_lifecycle_contract_v0 import build_client_order_id
from src.ops.section_11_12_8_actual_productive_testnet_campaign_run_start_v1.okx_response_mapper_v1 import (
    OkxResponseMapperError,
    build_venue_native_order_body_v1,
)

PATH_KIND_EXACT_OBJECT_FLATTEN = "FULL_CORE_EXACT_OBJECT_FLATTEN"
SIDE_SOURCE = "FRESH_NET_POSITION_SIGN"
QUANTITY_SOURCE = "FRESH_ABS_POSITION"
INSTRUMENT_SOURCE = "OWNER_GRANTED_EXACT_OBJECT_AND_FRESH_GET"
PRICE_SOURCE = "FRESH_PRICE_LIMIT_AND_TICKER_IN_BAND"
ORDER_TYPE = "limit"
ALREADY_FLAT = "ALREADY_FLAT"
OBJECT_MISMATCH = "AUTHORIZED_OBJECT_MISMATCH"
MULTIPLE_POSITIONS = "UNEXPECTED_MULTIPLE_OPEN_POSITIONS"
PENDING_ORDERS = "UNEXPECTED_PENDING_ORDERS"
INCOMPATIBLE_POS_MODE = "INCOMPATIBLE_ACCOUNT_POSITION_MODE"
IDENTITY_AMBIGUOUS = "OCCUPANCY_IDENTITY_AMBIGUOUS"


class CurrentProductiveExactObjectFlattenPlanError(RuntimeError):
    """Fail-closed exact-object flatten-plan violation."""


def flatten_side_from_net_pos_v1(pos: Decimal) -> str:
    if pos > 0:
        return "sell"
    if pos < 0:
        return "buy"
    raise CurrentProductiveExactObjectFlattenPlanError(ALREADY_FLAT)


def _require_decimal(value: Any, code: str) -> Decimal:
    text = str(value or "").strip()
    if not text:
        raise CurrentProductiveExactObjectFlattenPlanError(code)
    try:
        parsed = Decimal(text)
    except (InvalidOperation, ValueError) as exc:
        raise CurrentProductiveExactObjectFlattenPlanError(code) from exc
    if not parsed.is_finite():
        raise CurrentProductiveExactObjectFlattenPlanError(code)
    return parsed


def _quantize_px(*, px: Decimal, tick: Decimal, side: str) -> Decimal:
    if tick <= 0:
        raise CurrentProductiveExactObjectFlattenPlanError("TICK_SZ_INVALID")
    steps = px / tick
    if side == "sell":
        steps = steps.to_integral_value(rounding=ROUND_FLOOR)
    else:
        steps = steps.to_integral_value(rounding=ROUND_CEILING)
    return steps * tick


def _first_row(payload: Any) -> dict[str, Any]:
    if not isinstance(payload, Mapping):
        raise CurrentProductiveExactObjectFlattenPlanError("PAYLOAD_MISSING")
    if str(payload.get("code") or "") != "0":
        raise CurrentProductiveExactObjectFlattenPlanError("OKX_CODE_NOT_ZERO")
    data = payload.get("data")
    if not isinstance(data, list) or not data:
        raise CurrentProductiveExactObjectFlattenPlanError("PAYLOAD_DATA_EMPTY")
    row = data[0]
    if not isinstance(row, Mapping):
        raise CurrentProductiveExactObjectFlattenPlanError("PAYLOAD_ROW_MALFORMED")
    return dict(row)


def derive_in_band_limit_px_v1(
    *,
    side: str,
    ticker: Mapping[str, Any],
    price_limit: Mapping[str, Any],
    tick_sz: str,
) -> str:
    """Derive an in-band limit px from fresh OKX price-limit semantics.

    OKX ``buyLmt`` is the maximum allowed buy price. OKX ``sellLmt`` is the
    minimum allowed sell price. They are independent bounds, not a closed
    ``[buyLmt, sellLmt]`` interval (``buyLmt`` may be greater than ``sellLmt``).
    """
    buy_lmt = _require_decimal(price_limit.get("buyLmt"), "BUY_LMT_MISSING")
    sell_lmt = _require_decimal(price_limit.get("sellLmt"), "SELL_LMT_MISSING")
    if buy_lmt <= 0 or sell_lmt <= 0:
        raise CurrentProductiveExactObjectFlattenPlanError("PRICE_BAND_INVALID")
    tick = _require_decimal(tick_sz, "TICK_SZ_MISSING")
    if side == "sell":
        raw = ticker.get("bidPx") or price_limit.get("sellLmt")
        candidate = _require_decimal(raw, "SELL_FLATTEN_PX_MISSING")
        if candidate < sell_lmt:
            candidate = sell_lmt
        px = _quantize_px(px=candidate, tick=tick, side=side)
        if px < sell_lmt:
            px = _quantize_px(px=sell_lmt, tick=tick, side="buy")
        if px < sell_lmt:
            raise CurrentProductiveExactObjectFlattenPlanError("LIMIT_PX_BELOW_SELL_LMT")
    elif side == "buy":
        raw = ticker.get("askPx") or price_limit.get("buyLmt")
        candidate = _require_decimal(raw, "BUY_FLATTEN_PX_MISSING")
        if candidate > buy_lmt:
            candidate = buy_lmt
        px = _quantize_px(px=candidate, tick=tick, side=side)
        if px > buy_lmt:
            px = _quantize_px(px=buy_lmt, tick=tick, side="sell")
        if px > buy_lmt:
            raise CurrentProductiveExactObjectFlattenPlanError("LIMIT_PX_ABOVE_BUY_LMT")
    else:
        raise CurrentProductiveExactObjectFlattenPlanError("UNSUPPORTED_FLATTEN_SIDE")
    text = format(px, "f")
    if "." in text:
        text = text.rstrip("0").rstrip(".")
    return text or "0"


def revalidate_authorized_occupancy_v1(
    *,
    positions_payload: Any,
    pending_payload: Any,
    config_payload: Any,
    granted_inst_id: str,
    granted_inst_type: str,
    granted_pos_id: str,
    granted_pos: str,
    granted_pos_side: str,
    granted_mgn_mode: str,
) -> dict[str, str]:
    if not isinstance(config_payload, Mapping) or str(config_payload.get("code") or "") != "0":
        raise CurrentProductiveExactObjectFlattenPlanError("CONFIG_GET_FAIL_CLOSED")
    config_data = config_payload.get("data") if isinstance(config_payload, Mapping) else []
    config_row = config_data[0] if isinstance(config_data, list) and config_data else {}
    pos_mode = str((config_row or {}).get("posMode") or "")
    if pos_mode != "net_mode":
        raise CurrentProductiveExactObjectFlattenPlanError(INCOMPATIBLE_POS_MODE)
    if not isinstance(pending_payload, Mapping) or str(pending_payload.get("code") or "") != "0":
        raise CurrentProductiveExactObjectFlattenPlanError("PENDING_GET_FAIL_CLOSED")
    pending = pending_payload.get("data") if isinstance(pending_payload, Mapping) else []
    if isinstance(pending, list) and pending:
        raise CurrentProductiveExactObjectFlattenPlanError(PENDING_ORDERS)
    if (
        not isinstance(positions_payload, Mapping)
        or str(positions_payload.get("code") or "") != "0"
    ):
        raise CurrentProductiveExactObjectFlattenPlanError("POSITIONS_GET_FAIL_CLOSED")
    rows = positions_payload.get("data")
    if not isinstance(rows, list):
        raise CurrentProductiveExactObjectFlattenPlanError("POSITIONS_PAYLOAD_MALFORMED")
    open_rows: list[dict[str, Any]] = []
    for item in rows:
        if not isinstance(item, Mapping):
            raise CurrentProductiveExactObjectFlattenPlanError(IDENTITY_AMBIGUOUS)
        try:
            pos_value = _require_decimal(item.get("pos"), "POS_MALFORMED")
        except CurrentProductiveExactObjectFlattenPlanError:
            continue
        if pos_value == 0:
            continue
        open_rows.append(dict(item))
    if not open_rows:
        raise CurrentProductiveExactObjectFlattenPlanError(ALREADY_FLAT)
    if len(open_rows) != 1:
        raise CurrentProductiveExactObjectFlattenPlanError(MULTIPLE_POSITIONS)
    row = open_rows[0]
    expected_pos = _require_decimal(granted_pos, "GRANTED_POS_MALFORMED")
    actual_pos = _require_decimal(row.get("pos"), "POS_MALFORMED")
    if actual_pos == 0:
        raise CurrentProductiveExactObjectFlattenPlanError(ALREADY_FLAT)
    checks = (
        (str(row.get("instId") or ""), granted_inst_id, "INST_ID"),
        (str(row.get("instType") or ""), granted_inst_type, "INST_TYPE"),
        (str(row.get("posId") or ""), granted_pos_id, "POS_ID"),
        (str(row.get("posSide") or ""), granted_pos_side, "POS_SIDE"),
        (str(row.get("mgnMode") or ""), granted_mgn_mode, "MGN_MODE"),
    )
    for actual, expected, label in checks:
        if actual != expected:
            raise CurrentProductiveExactObjectFlattenPlanError(f"{OBJECT_MISMATCH}:{label}")
    if actual_pos.copy_abs() != expected_pos.copy_abs():
        raise CurrentProductiveExactObjectFlattenPlanError(f"{OBJECT_MISMATCH}:POS")
    return {
        "instId": str(row.get("instId") or ""),
        "instType": str(row.get("instType") or ""),
        "posId": str(row.get("posId") or ""),
        "pos": format(actual_pos, "f"),
        "posSide": str(row.get("posSide") or ""),
        "mgnMode": str(row.get("mgnMode") or ""),
        "lever": str(row.get("lever") or ""),
        "avgPx": str(row.get("avgPx") or ""),
        "ccy": str(row.get("ccy") or ""),
        "tradeId": str(row.get("tradeId") or ""),
        "posMode": pos_mode,
    }


def build_exact_object_flatten_plan_and_envelope_v1(
    *,
    occupancy: Mapping[str, str],
    instruments_payload: Any,
    price_limit_payload: Any,
    ticker_payload: Any,
    run_id: str,
    session_id: str,
    intent_id: str,
    creation_epoch: str,
    td_mode: str = "cross",
) -> tuple[VenuePlanCandidateV1, FinalOrderEnvelopeV1, str]:
    pos = _require_decimal(occupancy.get("pos"), "POS_MALFORMED")
    side = flatten_side_from_net_pos_v1(pos)
    qty_abs = pos.copy_abs()
    if qty_abs > pos.copy_abs():
        raise CurrentProductiveExactObjectFlattenPlanError("QTY_ABOVE_POSITION")
    qty = format(qty_abs, "f")
    if "." in qty:
        qty = qty.rstrip("0").rstrip(".")
    instrument = str(occupancy.get("instId") or "")
    instrument_row = _first_row(instruments_payload)
    if str(instrument_row.get("instId") or "") != instrument:
        raise CurrentProductiveExactObjectFlattenPlanError("INSTRUMENT_GET_INSTID_MISMATCH")
    state = str(instrument_row.get("state") or "")
    if state and state not in {"live", "Live"}:
        raise CurrentProductiveExactObjectFlattenPlanError("INSTRUMENT_NOT_LIVE")
    lot_sz = _require_decimal(instrument_row.get("lotSz") or "1", "LOT_SZ_MISSING")
    min_sz = _require_decimal(instrument_row.get("minSz") or "1", "MIN_SZ_MISSING")
    if qty_abs < min_sz:
        raise CurrentProductiveExactObjectFlattenPlanError("QTY_BELOW_MIN_SZ")
    if lot_sz > 0 and (qty_abs / lot_sz).to_integral_value() * lot_sz != qty_abs:
        raise CurrentProductiveExactObjectFlattenPlanError("QTY_NOT_LOT_MULTIPLE")
    ticker_row = _first_row(ticker_payload)
    limit_row = _first_row(price_limit_payload)
    px = derive_in_band_limit_px_v1(
        side=side,
        ticker=ticker_row,
        price_limit=limit_row,
        tick_sz=str(instrument_row.get("tickSz") or ""),
    )
    clordid = build_client_order_id(
        run_id=run_id,
        session_id=session_id,
        intent_id=intent_id,
        environment="live",
        instrument_id=instrument,
    )
    try:
        body = build_venue_native_order_body_v1(
            client_order_id=clordid,
            instrument=instrument,
            order_type=ORDER_TYPE,
            side=side,
            quantity=qty,
            td_mode=td_mode,
            px=px,
            reduce_only=True,
        )
    except OkxResponseMapperError as exc:
        raise CurrentProductiveExactObjectFlattenPlanError(f"VENUE_BODY_FAIL_CLOSED:{exc}") from exc
    if body.get("reduceOnly") is not True:
        raise CurrentProductiveExactObjectFlattenPlanError("REDUCE_ONLY_REQUIRED")
    if str(body.get("sz") or "") != qty:
        raise CurrentProductiveExactObjectFlattenPlanError("QTY_TRANSLATION_DRIFT")
    pos_side = str(occupancy.get("posSide") or "")
    if pos_side:
        body["posSide"] = pos_side
    plan = VenuePlanCandidateV1(
        instrument_id=instrument,
        side=side,
        quantity=qty,
        order_type=ORDER_TYPE,
        td_mode=td_mode,
        reduce_only=True,
        clordid=clordid,
        venue_native_payload=dict(body),
        quantity_source=QUANTITY_SOURCE,
        side_source=SIDE_SOURCE,
        instrument_source=INSTRUMENT_SOURCE,
        path_kind=PATH_KIND_EXACT_OBJECT_FLATTEN,
    )
    envelope = build_final_order_envelope_v1(
        instrument_id=instrument,
        side=side,
        order_type=ORDER_TYPE,
        quantity=qty,
        quantity_unit="CONTRACTS",
        td_mode=td_mode,
        reduce_only=True,
        client_order_id=clordid,
        path_kind=PATH_KIND_EXACT_OBJECT_FLATTEN,
        venue_plan_clordid=clordid,
        quantity_source=QUANTITY_SOURCE,
        side_source=SIDE_SOURCE,
        instrument_source=INSTRUMENT_SOURCE,
        admission_ref="OWNER_GRANTED_EXACT_OBJECT_DISPOSITION",
        provenance_ref="FRESH_AUTHENTICATED_READ_ONLY_GET",
        creation_epoch=creation_epoch,
        price=px,
        pos_side=pos_side,
    )
    if envelope.reduce_only is not True:
        raise CurrentProductiveExactObjectFlattenPlanError("ENVELOPE_REDUCE_ONLY_REQUIRED")
    if envelope.side != side:
        raise CurrentProductiveExactObjectFlattenPlanError("ENVELOPE_SIDE_DRIFT")
    return plan, envelope, PRICE_SOURCE
