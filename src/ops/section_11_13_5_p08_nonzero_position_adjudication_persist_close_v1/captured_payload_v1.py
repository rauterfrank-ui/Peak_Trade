"""Frozen authorized forensic capture. No extra-field reconstruction."""

from __future__ import annotations

from typing import Any, Mapping

from src.ops.section_11_13_5_p08_nonzero_position_adjudication_persist_close_v1.constants_v1 import (
    AUTHORIZED_EMPTY_DATA_IS_ZERO,
    HTTP_STATUS,
    OKX_CODE,
    OKX_MSG,
    QUERY,
    RAW_DATA_COUNT,
    REQUEST_TIMESTAMP,
    RESPONSE_TIMESTAMP,
    TARGET_INSTRUMENT_ID,
    TARGET_INSTRUMENT_MATCH_COUNT,
)

AUTHORIZED_TARGET_ROW: dict[str, str] = {
    "instId": "SUI-USD_UM_XPERP-310404",
    "pos": "1",
    "posSide": "net",
    "mgnMode": "cross",
    "lever": "3",
    "avgPx": "0.7774",
    "ccy": "USDC",
    "posId": "3891385768441942017",
    "tradeId": "1047017",
}

CAPTURED_ENVELOPE: dict[str, Any] = {
    "code": OKX_CODE,
    "msg": OKX_MSG,
    "data": [dict(AUTHORIZED_TARGET_ROW)],
}

CAPTURED_GET_METADATA: dict[str, Any] = {
    "REQUEST_TIMESTAMP": REQUEST_TIMESTAMP,
    "RESPONSE_TIMESTAMP": RESPONSE_TIMESTAMP,
    "HTTP_STATUS": HTTP_STATUS,
    "OKX_CODE": OKX_CODE,
    "OKX_MSG": OKX_MSG,
    "QUERY": dict(QUERY),
    "RAW_DATA_COUNT": RAW_DATA_COUNT,
    "TARGET_INSTRUMENT_MATCH_COUNT": TARGET_INSTRUMENT_MATCH_COUNT,
    "EMPTY_DATA_IS_ZERO": AUTHORIZED_EMPTY_DATA_IS_ZERO,
    "ORIGINAL_WIRE_BODY_BYTES_AVAILABLE": False,
    "RAW_FIELD_NORMALIZATION_PERFORMED": False,
    "PLAUSIBILITY_RECONSTRUCTION_PERFORMED": False,
    "FORENSIC_INPUT_MUTATED": False,
    "CAPTURED_FIELD_SET": "AUTHORIZED_FORENSIC_INPUT_ONLY",
}


class P08CapturedPayloadError(RuntimeError):
    """Fail-closed captured forensic-input binding violation."""


def captured_envelope_v1() -> dict[str, Any]:
    return {
        "code": CAPTURED_ENVELOPE["code"],
        "msg": CAPTURED_ENVELOPE["msg"],
        "data": [dict(AUTHORIZED_TARGET_ROW)],
    }


def bind_authorized_target_row_v1(row: Mapping[str, Any]) -> dict[str, str]:
    bound: dict[str, str] = {}
    for key, expected in AUTHORIZED_TARGET_ROW.items():
        if key not in row:
            raise P08CapturedPayloadError(f"AUTHORIZED_FIELD_MISSING:{key}")
        actual = row[key]
        if actual is None:
            raise P08CapturedPayloadError(f"AUTHORIZED_FIELD_NONE:{key}")
        text = str(actual)
        if text != expected:
            raise P08CapturedPayloadError(f"AUTHORIZED_FIELD_MISMATCH:{key}")
        bound[key] = text
    return bound


def bind_captured_envelope_v1(payload: Mapping[str, Any]) -> dict[str, Any]:
    if str(payload.get("code") or "") != OKX_CODE:
        raise P08CapturedPayloadError("OKX_CODE_MISMATCH")
    if str(payload.get("msg") if payload.get("msg") is not None else "") != OKX_MSG:
        raise P08CapturedPayloadError("OKX_MSG_MISMATCH")
    data = payload.get("data")
    if not isinstance(data, list):
        raise P08CapturedPayloadError("DATA_NOT_LIST")
    if len(data) != RAW_DATA_COUNT:
        raise P08CapturedPayloadError("RAW_DATA_COUNT_MISMATCH")
    row = data[0]
    if not isinstance(row, Mapping):
        raise P08CapturedPayloadError("TARGET_ROW_NOT_MAPPING")
    bound_row = bind_authorized_target_row_v1(row)
    if bound_row["instId"] != TARGET_INSTRUMENT_ID:
        raise P08CapturedPayloadError("TARGET_INSTRUMENT_MISMATCH")
    matching = [
        item
        for item in data
        if isinstance(item, Mapping)
        and str(item.get("instId") or "").strip() == TARGET_INSTRUMENT_ID
    ]
    if len(matching) != TARGET_INSTRUMENT_MATCH_COUNT:
        raise P08CapturedPayloadError("TARGET_INSTRUMENT_MATCH_COUNT_MISMATCH")
    return {
        "code": OKX_CODE,
        "msg": OKX_MSG,
        "data": [bound_row],
    }
