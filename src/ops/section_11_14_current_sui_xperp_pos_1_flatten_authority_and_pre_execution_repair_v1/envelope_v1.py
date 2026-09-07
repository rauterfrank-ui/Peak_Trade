"""Distinct §11.14 Flatten SELL envelope. Not the Entry BUY ExactExecutionEnvelope."""

from __future__ import annotations

import hashlib
import json
from decimal import Decimal, InvalidOperation
from typing import Any, Mapping

from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.flatten_limit_price_contract_v1 import (
    FlattenPriceInputV1,
    evaluate_canary_flatten_limit_price_contract_v1,
)
from src.ops.section_11_13_5_p11_pos_to_sz_unit_identity_independent_proof_v1.contract_v1 import (
    identity_flatten_sz_from_signed_pos_v1,
)
from src.ops.section_11_13_5_p12_execution_prerequisite_11_position_side_posside_v1.contract_v1 import (
    assert_request_pos_side_omitted_v1,
    flatten_order_side_from_signed_pos_v1,
)
from src.ops.section_11_13_5_p13_execution_prerequisite_12_exact_flatten_payload_v1.contract_v1 import (
    EXACT_FLATTEN_PAYLOAD_ALLOWED_KEYS,
)
from src.ops.section_11_14_current_sui_xperp_pos_1_flatten_authority_and_pre_execution_repair_v1.constants_v1 import (
    CLOSE_POSITION_ENDPOINT,
    EXPECTED_SIGNED_POSITION,
    FLATTEN_HTTP_ENDPOINT,
    INSTRUMENT_ID,
    MARGIN_MODE,
    ORDER_QTY_UNIT,
    ORDER_SIDE_FOR_POSITIVE_POS,
    ORDER_TYPE,
    POS_SIDE_OBSERVED,
    REDUCE_ONLY_REQUIRED,
    REQUEST_POS_SIDE_POLICY,
    RETRY_ALLOWED,
    SECOND_SUBMIT_ALLOWED,
    TD_MODE,
)
from src.ops.section_11_14_live_handoff_standing_fee_slippage_and_exact_execution_envelope_v1.fee_policy_v1 import (
    StandingFeePolicyV1,
    compute_expected_fee_amount_v1,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.constants_v1 import (
    CANARY_AUTHORIZED,
    LIVE_ARMED,
    LIVE_ENABLED,
    POST_ALLOWED,
)


class FlattenSellEnvelopeError(RuntimeError):
    """Fail-closed Flatten SELL envelope violation."""


ENVELOPE_KIND = "SECTION_11_14_FLATTEN_SELL_ENVELOPE_V1"
ENTRY_ENVELOPE_KIND = "SECTION_11_14_EXACT_EXECUTION_ENVELOPE_V1"


def _dec(raw: Any, *, field: str) -> Decimal:
    text = str(raw if raw is not None else "").strip()
    if not text or text == "UNKNOWN":
        raise FlattenSellEnvelopeError(f"ENVELOPE_INPUT_UNKNOWN:{field}")
    try:
        value = Decimal(text)
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise FlattenSellEnvelopeError(f"ENVELOPE_INPUT_UNPARSEABLE:{field}") from exc
    if not value.is_finite():
        raise FlattenSellEnvelopeError(f"ENVELOPE_INPUT_NON_FINITE:{field}")
    return value


def extract_flatten_ticker_quotes_v1(*, ticker_payload: Mapping[str, Any]) -> dict[str, str]:
    """Extract bid/ask/last/ts. Does not use last|askPx Entry reference."""
    if str(ticker_payload.get("code") or "") != "0":
        raise FlattenSellEnvelopeError("TICKER_PAYLOAD_NOT_OK")
    data = ticker_payload.get("data")
    if not isinstance(data, list) or not data or not isinstance(data[0], Mapping):
        raise FlattenSellEnvelopeError("TICKER_DATA_MISSING")
    row = data[0]
    bid = str(row.get("bidPx") or "").strip()
    ask = str(row.get("askPx") or "").strip()
    last = str(row.get("last") or "").strip()
    ts = str(row.get("ts") or "").strip()
    if not bid:
        raise FlattenSellEnvelopeError("BID_PX_MISSING")
    if not ask:
        raise FlattenSellEnvelopeError("ASK_PX_MISSING")
    if not last:
        raise FlattenSellEnvelopeError("LAST_MISSING")
    if not ts:
        raise FlattenSellEnvelopeError("QUOTE_TS_MISSING")
    return {"bidPx": bid, "askPx": ask, "last": last, "ts": ts}


def bind_flatten_sell_limit_slippage_v1(
    *,
    bid: str,
    limit_price: str,
    tick_sz: str,
) -> dict[str, str]:
    """Flatten SELL slippage: worst fill is the LIMIT. Distinct from Entry BUY."""
    bid_d = _dec(bid, field="bid")
    limit_d = _dec(limit_price, field="limit_price")
    tick_d = _dec(tick_sz, field="tick_sz")
    if tick_d <= 0:
        raise FlattenSellEnvelopeError("TICK_SZ_NON_POSITIVE")
    steps = (limit_d / tick_d).to_integral_value()
    if steps * tick_d != limit_d:
        raise FlattenSellEnvelopeError("FLATTEN_LIMIT_NOT_ON_TICK")
    if limit_d > bid_d:
        raise FlattenSellEnvelopeError("SELL_LIMIT_ABOVE_BID")
    slippage_abs = bid_d - limit_d
    frac = slippage_abs / bid_d if bid_d > 0 else Decimal("0")
    return {
        "SIDE": "SELL",
        "REFERENCE_PRICE": format(bid_d, "f"),
        "REFERENCE_KIND": "BID",
        "LIMIT_PRICE": format(limit_d, "f"),
        "WORST_FILL_PRICE": format(limit_d, "f"),
        "SLIPPAGE_ABS": format(slippage_abs, "f"),
        "SLIPPAGE_FRAC": format(frac, "f"),
        "POLICY": "FLATTEN_SELL_LIMIT_IS_WORST_FILL_DISTINCT_FROM_ENTRY_BUY",
    }


def evaluate_flatten_sell_price_band_v1(*, limit_price: str, sell_lmt: str) -> tuple[bool, str]:
    try:
        px = Decimal(str(limit_price))
        band = Decimal(str(sell_lmt))
    except (InvalidOperation, TypeError, ValueError):
        return False, "PRICE_OR_SELL_LMT_UNPARSEABLE"
    if px <= 0 or band <= 0:
        return False, "PRICE_OR_SELL_LMT_NON_POSITIVE"
    if px < band:
        return False, "LIMIT_PRICE_BELOW_SELL_LMT"
    return True, "WITHIN_SELL_LMT"


def evaluate_flatten_max_sell_v1(*, qty: str, max_sell: str) -> tuple[bool, str]:
    try:
        q = Decimal(str(qty))
        mx = Decimal(str(max_sell))
    except (InvalidOperation, TypeError, ValueError):
        return False, "QTY_OR_MAX_SELL_UNPARSEABLE"
    if q <= 0:
        return False, "QTY_NON_POSITIVE"
    if mx < q:
        return False, "INSUFFICIENT_MAX_SELL"
    return True, "MAX_SELL_COVERS_QTY"


def flatten_envelope_id_v1(payload: Mapping[str, Any]) -> str:
    material = json.dumps(dict(payload), sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(material.encode("utf-8")).hexdigest()


def build_flatten_sell_envelope_v1(
    *,
    origin_main_sha: str,
    signed_pos: str,
    pos_side: str,
    margin_mode: str,
    bid: str,
    ask: str,
    last: str,
    quote_ts_ms: str,
    evaluation_ts_ms: str,
    tick_sz: str,
    sell_lmt: str,
    max_sell: str,
    max_sell_px_sent: str,
    ct_val: str,
    fee_policy: StandingFeePolicyV1,
    pending_order_count: int,
    pending_order_gate_pass: bool,
) -> dict[str, Any]:
    if LIVE_ENABLED or LIVE_ARMED or CANARY_AUTHORIZED or POST_ALLOWED:
        raise FlattenSellEnvelopeError("STANDING_LIVE_FLAG_MUST_REMAIN_FALSE")
    pos = _dec(signed_pos, field="signed_pos")
    if pos != _dec(EXPECTED_SIGNED_POSITION, field="expected_pos"):
        raise FlattenSellEnvelopeError(f"POSITION_NOT_EXPECTED_POS_1:{signed_pos}")
    if pos <= 0:
        raise FlattenSellEnvelopeError("SIGNED_POS_NOT_POSITIVE")
    if str(pos_side or "").strip() != POS_SIDE_OBSERVED:
        raise FlattenSellEnvelopeError(f"POS_SIDE_MISMATCH:{pos_side}")
    if str(margin_mode or "").strip() != MARGIN_MODE:
        raise FlattenSellEnvelopeError(f"MARGIN_MODE_MISMATCH:{margin_mode}")
    side = flatten_order_side_from_signed_pos_v1(pos)
    if side != ORDER_SIDE_FOR_POSITIVE_POS:
        raise FlattenSellEnvelopeError(f"FLATTEN_SIDE_NOT_SELL:{side}")
    qty_d = identity_flatten_sz_from_signed_pos_v1(pos)
    qty = format(qty_d, "f")
    if qty_d != Decimal("1"):
        raise FlattenSellEnvelopeError(f"FLATTEN_QTY_NOT_ABS_POS_1:{qty}")
    decision = evaluate_canary_flatten_limit_price_contract_v1(
        FlattenPriceInputV1(
            flatten_side=side,
            observed_signed_pos=str(signed_pos),
            bid=bid,
            ask=ask,
            quote_timestamp_ms=quote_ts_ms,
            evaluation_timestamp_ms=evaluation_ts_ms,
            tick_sz=tick_sz,
        )
    )
    if not decision.permit_issued or decision.permit is None:
        reasons = ",".join(decision.reject_reasons) or "PRICE_PERMIT_DENIED"
        raise FlattenSellEnvelopeError(f"FLATTEN_LIMIT_PRICE_DENIED:{reasons}")
    limit_px = decision.permit.limit_price
    if str(max_sell_px_sent or "").strip() != str(limit_px).strip():
        raise FlattenSellEnvelopeError("MAX_SELL_PX_NOT_FLATTEN_LIMIT")
    band_ok, band_reason = evaluate_flatten_sell_price_band_v1(
        limit_price=limit_px, sell_lmt=sell_lmt
    )
    if not band_ok:
        raise FlattenSellEnvelopeError(f"SELL_LMT_VIOLATION:{band_reason}")
    size_ok, size_reason = evaluate_flatten_max_sell_v1(qty=qty, max_sell=max_sell)
    if not size_ok:
        raise FlattenSellEnvelopeError(f"SIZE_GATE:{size_reason}")
    slippage = bind_flatten_sell_limit_slippage_v1(bid=bid, limit_price=limit_px, tick_sz=tick_sz)
    if not fee_policy.policy_bound:
        raise FlattenSellEnvelopeError("FEE_POLICY_NOT_BOUND")
    fee_amt = compute_expected_fee_amount_v1(
        conservative_rate=fee_policy.conservative_rate,
        qty=qty,
        ct_val=ct_val,
        worst_fill_px=slippage["WORST_FILL_PRICE"],
        fee_ccy=fee_policy.fee_ccy,
        notional_ccy="USDC",
    )
    venue_body = {
        "instId": INSTRUMENT_ID,
        "tdMode": TD_MODE,
        "side": "sell",
        "ordType": "limit",
        "sz": qty,
        "px": limit_px,
        "reduceOnly": True,
    }
    assert_request_pos_side_omitted_v1(venue_body)
    if "posSide" in venue_body:
        raise FlattenSellEnvelopeError("POS_SIDE_MUST_BE_OMITTED_NET_MODE")
    unexpected = set(venue_body) - (EXACT_FLATTEN_PAYLOAD_ALLOWED_KEYS - {"clOrdId"})
    if unexpected:
        raise FlattenSellEnvelopeError(
            "UNEXPECTED_FLATTEN_PREVIEW_FIELD:" + ",".join(sorted(unexpected))
        )
    if venue_body["reduceOnly"] is not True:
        raise FlattenSellEnvelopeError("REDUCE_ONLY_NOT_JSON_BOOLEAN_TRUE")
    if "clOrdId" in venue_body:
        raise FlattenSellEnvelopeError("CLORDID_MUST_REMAIN_UNBOUND_UNTIL_OWNER_FLATTEN_GO")
    identity = {
        "KIND": ENVELOPE_KIND,
        "NOT_KIND": ENTRY_ENVELOPE_KIND,
        "INSTRUMENT_ID": INSTRUMENT_ID,
        "SIGNED_POS": format(pos, "f"),
        "POS_SIDE": POS_SIDE_OBSERVED,
        "MARGIN_MODE": MARGIN_MODE,
        "SIDE": side,
        "QTY": qty,
        "QTY_UNIT": ORDER_QTY_UNIT,
        "REDUCE_ONLY": REDUCE_ONLY_REQUIRED,
        "ORDER_TYPE": ORDER_TYPE,
        "REQUEST_POS_SIDE_POLICY": REQUEST_POS_SIDE_POLICY,
        "LIMIT_PRICE": limit_px,
        "BID": str(bid),
        "ASK": str(ask),
        "LAST": str(last),
        "QUOTE_TS_MS": str(quote_ts_ms),
        "MAX_SELL": str(max_sell),
        "MAX_SELL_PX": str(max_sell_px_sent),
        "SELL_LMT": str(sell_lmt),
        "ORIGIN_MAIN_SHA": str(origin_main_sha).strip().lower(),
        "RETRY_ALLOWED": RETRY_ALLOWED,
        "SECOND_SUBMIT_ALLOWED": SECOND_SUBMIT_ALLOWED,
        "HTTP_ENDPOINT": FLATTEN_HTTP_ENDPOINT,
        "CLOSE_POSITION_ENDPOINT_ALLOWLISTED": False,
        "CLOSE_POSITION_ENDPOINT": CLOSE_POSITION_ENDPOINT,
        "CLORDID_BOUND_ONLY_AFTER_OWNER_FLATTEN_GO": True,
    }
    envelope_id = flatten_envelope_id_v1(identity)
    return {
        **identity,
        "FLATTEN_ENVELOPE_ID": envelope_id,
        "VENUE_NATIVE_BODY_PREVIEW": venue_body,
        "SLIPPAGE": slippage,
        "EXPECTED_FEE": fee_amt,
        "FEE_RATE": fee_policy.conservative_rate,
        "PRICE_GATE_PASS": True,
        "SIZE_GATE_PASS": True,
        "PRICE_GATE_REASON": band_reason,
        "SIZE_GATE_REASON": size_reason,
        "PENDING_ORDER_COUNT": int(pending_order_count),
        "PENDING_ORDER_GATE_PASS": bool(pending_order_gate_pass),
        "OWNER_EXECUTION_AUTHORIZED": False,
        "FLATTEN_AUTHORIZED": False,
        "SUBMIT_REACHABLE": False,
    }
