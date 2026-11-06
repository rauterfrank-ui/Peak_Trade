"""Fail-closed EXECUTION_PREREQUISITE_12 exact flatten payload contract.

Contract boundary: venue-native Place Order JSON object immediately before
HMAC/transport. Not HTTP headers, not timestamp, not signature.

Field classes:

- observed-position derived: instId, side, sz
- standing configuration: tdMode, ordType, reduceOnly
- generated: clOrdId
- bound external input: px (FlattenPricePermitV1; not from observed position)
- omitted: posSide
- out of boundary: transport metadata

Does not GET, POST, flatten, or mint a send-time live px.
"""

from __future__ import annotations

from typing import Any, Mapping

from src.ops.section_11_13_5_p11_pos_to_sz_unit_identity_independent_proof_v1.contract_v1 import (
    NUMBER_OF_CONTRACTS,
    PosToSzUnitIdentityError,
    assert_flatten_body_identity_v1,
)
from src.ops.section_11_13_5_p12_execution_prerequisite_11_position_side_posside_v1.contract_v1 import (
    ORDER_SIDE_DOMAIN,
    PositionSidePossideError,
    assert_no_long_short_buy_sell_conflation_v1,
    assert_request_pos_side_omitted_v1,
)

EXACT_FLATTEN_PAYLOAD_ALLOWED_KEYS: frozenset[str] = frozenset(
    {
        "clOrdId",
        "instId",
        "side",
        "ordType",
        "sz",
        "tdMode",
        "px",
        "reduceOnly",
    }
)
VENUE_NATIVE_SIDE_DOMAIN: frozenset[str] = frozenset({"buy", "sell"})
VENUE_NATIVE_ORD_TYPE = "limit"
VENUE_NATIVE_TD_MODE = "cross"
REDUCE_ONLY_JSON_BOOLEAN_REQUIRED = True
REDUCE_ONLY_WIRE_TYPE_STATUS = "UNPROVEN"
PX_SOURCE_CLASS = "BOUND_EXTERNAL_INPUT_NOT_FROM_OBSERVED_POSITION"
CLORDID_SOURCE_CLASS = "DETERMINISTIC_GENERATED_NOT_FROM_POSITION"
SZ_UNIT = NUMBER_OF_CONTRACTS
SZ_TRANSFORMATION = "IDENTITY_ABS_SIGNED_POS_THEN_FORMAT_F_INTEGRAL_COLLAPSE"
SIDE_TRANSFORMATION = "P11_SELL_IF_SIGNED_POS_GT_0_ELSE_BUY_THEN_MAPPER_LOWER"
ORD_TYPE_TRANSFORMATION = "STANDING_LIMIT_THEN_MAPPER_LOWER"
TD_MODE_TRANSFORMATION = "STANDING_CANONICAL_CROSS_NOT_ROW_MGNMODE"
REDUCE_ONLY_TRANSFORMATION = "STANDING_JSON_BOOLEAN_TRUE_OMITTED_UNLESS_TRUE"
INST_ID_TRANSFORMATION = "COPY_OBSERVED_BOUND_INSTRUMENT_ID"
PX_TRANSFORMATION = "COPY_BOUND_PRICE_PERMIT_LIMIT_PRICE"
CLORDID_TRANSFORMATION = "SHA256_OWNER_GO_ORIGIN_MAIN_FLATTEN_THEN_CLIENT_ORDER_ID"
CONTRACT_BOUNDARY = "VENUE_NATIVE_JSON_BODY_IMMEDIATELY_BEFORE_HMAC_TRANSPORT"
CASE = "CASE_B_OFFLINE_CLOSABLE"
EXECUTION_PREREQUISITE_12_STATUS = "PASS"
P12_EXACT_FLATTEN_PAYLOAD_PROVEN = True
P12_EXACT_FLATTEN_PAYLOAD_CLOSED = True
SEND_TIME_PX_MINTED = False
SEND_TIME_PAYLOAD_INSTANCE_MINTED = False


class ExactFlattenPayloadError(RuntimeError):
    """Fail-closed EXECUTION_PREREQUISITE_12 exact-payload violation."""


def _norm_keyset(body: Mapping[str, Any]) -> set[str]:
    return {str(key) for key in body}


def assert_exact_flatten_payload_keyset_v1(body: Mapping[str, Any]) -> None:
    observed = _norm_keyset(body)
    missing = sorted(EXACT_FLATTEN_PAYLOAD_ALLOWED_KEYS - observed)
    unexpected = sorted(observed - EXACT_FLATTEN_PAYLOAD_ALLOWED_KEYS)
    if missing:
        raise ExactFlattenPayloadError(f"MISSING_REQUIRED_PAYLOAD_FIELD:{','.join(missing)}")
    if unexpected:
        raise ExactFlattenPayloadError(f"UNEXPECTED_PAYLOAD_FIELD:{','.join(unexpected)}")
    lowered = {str(key).strip().lower() for key in body}
    if "posside" in lowered:
        raise ExactFlattenPayloadError("REQUEST_POS_SIDE_PRESENT_ON_FLATTEN_BODY")
    if "tgtccy" in lowered:
        raise ExactFlattenPayloadError("TGTCCY_PRESENT_ON_FLATTEN_BODY")


def assert_exact_flatten_payload_contract_v1(
    body: Mapping[str, Any],
    *,
    instrument_id: str,
    side: str,
    quantity: str,
    td_mode: str,
    px: str,
    clordid: str,
) -> None:
    """Validate the venue-native flatten body against bound inputs.

    ``side`` is the plan-level BUY/SELL token. The mapper emits lowercase.
    ``px`` must already be the bound permit price; naked px is not accepted.
    """
    if not isinstance(body, Mapping):
        raise ExactFlattenPayloadError("FLATTEN_BODY_NOT_MAPPING")
    assert_exact_flatten_payload_keyset_v1(body)
    expected_instrument = str(instrument_id or "").strip()
    if not expected_instrument:
        raise ExactFlattenPayloadError("INSTRUMENT_ID_MISSING")
    if str(body.get("instId") or "") != expected_instrument:
        raise ExactFlattenPayloadError("INST_ID_MISMATCH")
    plan_side = str(side or "").strip().upper()
    if plan_side not in ORDER_SIDE_DOMAIN:
        raise ExactFlattenPayloadError(f"INVALID_FLATTEN_ORDER_SIDE:{plan_side or 'MISSING'}")
    try:
        assert_request_pos_side_omitted_v1(body)
        assert_flatten_body_identity_v1(body, quantity=quantity)
        assert_no_long_short_buy_sell_conflation_v1(plan_side)
    except (PosToSzUnitIdentityError, PositionSidePossideError) as exc:
        raise ExactFlattenPayloadError(str(exc)) from exc
    venue_side = str(body.get("side") or "")
    if venue_side not in VENUE_NATIVE_SIDE_DOMAIN:
        raise ExactFlattenPayloadError(f"INVALID_VENUE_NATIVE_SIDE:{venue_side or 'MISSING'}")
    if venue_side != plan_side.lower():
        raise ExactFlattenPayloadError("FLATTEN_BODY_SIDE_NOT_PLAN_SIDE")
    expected_td = str(td_mode or "").strip()
    if expected_td != VENUE_NATIVE_TD_MODE:
        raise ExactFlattenPayloadError(f"INCORRECT_TD_MODE:{expected_td or 'MISSING'}")
    if str(body.get("tdMode") or "") != VENUE_NATIVE_TD_MODE:
        raise ExactFlattenPayloadError("INCORRECT_TD_MODE")
    if str(body.get("ordType") or "") != VENUE_NATIVE_ORD_TYPE:
        raise ExactFlattenPayloadError("INCORRECT_ORD_TYPE")
    if body.get("reduceOnly") is not True:
        raise ExactFlattenPayloadError("REDUCE_ONLY_MISMATCH")
    expected_px = str(px or "").strip()
    if not expected_px:
        raise ExactFlattenPayloadError("PX_MISSING")
    if str(body.get("px") or "") != expected_px:
        raise ExactFlattenPayloadError("PX_MISMATCH")
    expected_clordid = str(clordid or "").strip()
    if not expected_clordid:
        raise ExactFlattenPayloadError("CLORDID_MISSING")
    if str(body.get("clOrdId") or "") != expected_clordid:
        raise ExactFlattenPayloadError("CLORDID_MISMATCH")
    if str(body.get("sz") or "") != str(quantity):
        raise ExactFlattenPayloadError("SZ_MISMATCH")
