"""Focused tests for §11.13.5 canary order-submit transport observability (offline only)."""

from __future__ import annotations

import json

from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.constants_v1 import (
    DEFAULT_INSTRUMENT_ID,
    GENERAL_LIVE_SUBMIT_UNLOCKED,
    LIVE_AUTHORIZED,
    OWNER_GO_AUTHORING,
    SUBMIT_UNLOCKED,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.http_client_v1 import (
    CANARY_VENUE_NATIVE_REQUEST_FIELDS_V1,
    extract_canary_http_response_evidence_v1,
    extract_canary_venue_native_request_evidence_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.submit_transport_v1 import (
    LiveCanarySubmitTransportError,
    run_canary_submit_transport_v1,
)
from tests.ops.test_section_11_13_5_canary_submit_transport_v1 import (
    FIXTURE_MATERIAL,
    _fake_transport,
    _transport_kwargs,
)

_SECRET_MARKERS = (
    "must-not-leak",
    "session=secret",
    "Bearer leaked-token",
    "A" * 36,
    "B" * 32,
    "C" * 14,
    "ok-access-sign-value",
)


def _dumped(payload: object) -> str:
    return json.dumps(payload, default=str)


def test_http_200_top_level_code_1_retains_single_data_failure() -> None:
    transport = _fake_transport()
    transport.post_status_code = 200
    transport.post_body = json.dumps(
        {
            "code": "1",
            "msg": "All operations failed",
            "data": [
                {
                    "sCode": "51008",
                    "sMsg": "Order failed. Insufficient USDC balance in account.",
                    "ordId": "",
                    "clOrdId": "canary-cl-1",
                    "tag": "pt",
                }
            ],
        }
    ).encode("utf-8")
    result = run_canary_submit_transport_v1(**_transport_kwargs(transport=transport))
    assert result["ok"] is False
    assert result["CANARY_RESULT"] == "ENTRY_SUBMIT_TRANSPORT_RETURNED"
    evidence = result["http_error_evidence"]
    compact = result["submit_adjudication_evidence"]
    assert evidence["http_status"] == 200
    assert evidence["okx_code"] == "1"
    assert evidence["okx_msg"] == "All operations failed"
    assert evidence["okx_data_count"] == 1
    assert compact["HTTP_STATUS"] == 200
    assert compact["TOP_LEVEL_OKX_CODE"] == "1"
    assert compact["TOP_LEVEL_OKX_MSG"] == "All operations failed"
    assert compact["OKX_DATA_COUNT"] == 1
    row = compact["okx_data"][0]
    assert row["sCode"] == "51008"
    assert row["sMsg"] == "Order failed. Insufficient USDC balance in account."
    assert row["ordId"] == ""
    assert row["clOrdId"] == "canary-cl-1"
    assert row["tag"] == "pt"
    dumped = _dumped(result)
    assert "51008" in dumped
    assert compact["okx_data"] == result["http_error_evidence"]["okx_data"]


def test_multiple_data_entries_preserve_count_and_order() -> None:
    transport = _fake_transport()
    transport.post_body = json.dumps(
        {
            "code": "1",
            "msg": "All operations failed",
            "data": [
                {"sCode": "51008", "sMsg": "first", "clOrdId": "a"},
                {"sCode": "51000", "sMsg": "second", "ordId": "ord-2", "clOrdId": "b"},
            ],
        }
    ).encode("utf-8")
    result = run_canary_submit_transport_v1(**_transport_kwargs(transport=transport))
    compact = result["submit_adjudication_evidence"]
    assert compact["OKX_DATA_COUNT"] == 2
    assert len(compact["okx_data"]) == 2
    assert compact["okx_data"][0]["sCode"] == "51008"
    assert compact["okx_data"][0]["sMsg"] == "first"
    assert "ordId" not in compact["okx_data"][0]
    assert compact["okx_data"][1]["sCode"] == "51000"
    assert compact["okx_data"][1]["ordId"] == "ord-2"
    assert compact["okx_data"][1]["clOrdId"] == "b"


def test_successful_response_behavior_unchanged() -> None:
    transport = _fake_transport()
    result = run_canary_submit_transport_v1(**_transport_kwargs(transport=transport))
    assert result["ok"] is True
    assert result["CANARY_RESULT"] == "ENTRY_SUBMIT_TRANSPORT_RETURNED"
    assert result["LIVE_AUTHORIZED"] is False
    assert result["LIVE_CANARY_MINIMUM_EXPOSURE_EXECUTED"] is False
    assert result["RETRY_SAFE_NOW"] is False
    compact = result["submit_adjudication_evidence"]
    assert compact["HTTP_STATUS"] == 200
    assert compact["TOP_LEVEL_OKX_CODE"] == "0"
    assert compact["OKX_DATA_COUNT"] == 1
    assert compact["okx_data"][0]["sCode"] == "0"
    assert compact["okx_data"][0]["ordId"] == "ord-1"
    posts = [call for call in transport.calls if call.method == "POST"]
    assert len(posts) == 1


def test_venue_native_request_retains_present_optional_fields_and_marks_absent() -> None:
    present = extract_canary_venue_native_request_evidence_v1(
        body_text=json.dumps(
            {
                "instId": DEFAULT_INSTRUMENT_ID,
                "tdMode": "cross",
                "side": "buy",
                "ordType": "limit",
                "sz": "1",
                "px": "75149.7",
                "posSide": "net",
                "reduceOnly": False,
                "ccy": "USDC",
                "tgtCcy": "",
                "banAmend": True,
                "stpMode": "cancel_maker",
                "tag": "pt",
                "clOrdId": "cl-1",
                "secret": "must-not-copy",
                "OK-ACCESS-SIGN": "ok-access-sign-value",
            },
            separators=(",", ":"),
        )
    )
    assert present["parse_error"] is None
    fields = present["fields"]
    assert fields["instId"] == DEFAULT_INSTRUMENT_ID
    assert fields["tdMode"] == "cross"
    assert fields["side"] == "buy"
    assert fields["ordType"] == "limit"
    assert fields["sz"] == "1"
    assert fields["px"] == "75149.7"
    assert fields["posSide"] == "net"
    assert fields["reduceOnly"] is False
    assert fields["ccy"] == "USDC"
    assert fields["tgtCcy"] == ""
    assert fields["banAmend"] is True
    assert fields["stpMode"] == "cancel_maker"
    assert fields["tag"] == "pt"
    assert fields["clOrdId"] == "cl-1"
    assert "secret" not in fields
    assert "OK-ACCESS-SIGN" not in fields
    assert set(present["present_keys"]) == set(CANARY_VENUE_NATIVE_REQUEST_FIELDS_V1)
    assert present["absent_keys"] == []
    assert "must-not-copy" not in _dumped(present)

    absent_optional = extract_canary_venue_native_request_evidence_v1(
        body_text=json.dumps(
            {
                "instId": DEFAULT_INSTRUMENT_ID,
                "tdMode": "cross",
                "side": "buy",
                "ordType": "limit",
                "sz": "1",
                "px": "75149.7",
                "clOrdId": "cl-2",
            },
            separators=(",", ":"),
        )
    )
    fields_absent = absent_optional["fields"]
    assert "reduceOnly" not in fields_absent
    assert "posSide" not in fields_absent
    assert "ccy" not in fields_absent
    assert "tgtCcy" not in fields_absent
    assert "banAmend" not in fields_absent
    assert "stpMode" not in fields_absent
    assert "tag" not in fields_absent
    assert "reduceOnly" in absent_optional["absent_keys"]
    assert "px" in absent_optional["present_keys"]
    assert fields_absent["px"] == "75149.7"


def test_submit_result_preserves_actual_posted_wire_body_fields() -> None:
    transport = _fake_transport()
    result = run_canary_submit_transport_v1(**_transport_kwargs(transport=transport))
    posts = [call for call in transport.calls if call.method == "POST"]
    posted = json.loads(posts[0].body_text)
    evidence = result["venue_native_request_evidence"]
    compact = result["submit_adjudication_evidence"]
    assert evidence["fields"] == compact["venue_native_request"]
    for key, value in evidence["fields"].items():
        assert posted[key] == value
    for key in CANARY_VENUE_NATIVE_REQUEST_FIELDS_V1:
        if key in posted:
            assert key in evidence["present_keys"]
            assert key in evidence["fields"]
        else:
            assert key in evidence["absent_keys"]
            assert key not in evidence["fields"]
    assert "reduceOnly" not in posted
    assert "reduceOnly" not in evidence["fields"]


def test_credential_material_is_redacted_from_persisted_evidence() -> None:
    transport = _fake_transport()
    transport.post_status_code = 200
    transport.post_body = json.dumps(
        {
            "code": "1",
            "msg": "All operations failed",
            "data": [{"sCode": "1", "sMsg": "denied", "clOrdId": "x"}],
            "api_secret": "B" * 32,
        }
    ).encode("utf-8")
    transport.post_headers = {
        "Content-Type": "application/json",
        "OK-ACCESS-KEY": "must-not-leak",
        "OK-ACCESS-SIGN": "ok-access-sign-value",
        "OK-ACCESS-PASSPHRASE": "C" * 14,
        "Authorization": "Bearer leaked-token",
        "Set-Cookie": "session=secret",
    }
    result = run_canary_submit_transport_v1(**_transport_kwargs(transport=transport))
    dumped = _dumped(result)
    for marker in _SECRET_MARKERS:
        assert marker not in dumped
    headers = result["http_error_evidence"]["response_headers_safe"]
    header_blob = _dumped(headers).lower()
    assert "ok-access" not in header_blob
    assert "authorization" not in header_blob
    assert "cookie" not in header_blob
    assert result["http_error_evidence"]["SECRET_VALUES_INCLUDED"] is False
    assert result["submit_adjudication_evidence"]["SECRET_VALUES_INCLUDED"] is False
    assert result["venue_native_request_evidence"]["SECRET_VALUES_INCLUDED"] is False
    assert "api_secret" not in result["http_error_evidence"]["okx_data"][0]
    assert FIXTURE_MATERIAL not in dumped


def test_fail_closed_gates_remain_intact() -> None:
    assert LIVE_AUTHORIZED is False
    assert SUBMIT_UNLOCKED is False
    assert GENERAL_LIVE_SUBMIT_UNLOCKED is False
    kwargs = _transport_kwargs(owner_go=OWNER_GO_AUTHORING)
    transport = kwargs["transport"]
    try:
        run_canary_submit_transport_v1(**kwargs)
        raise AssertionError("authoring GO must remain fail-closed")
    except (LiveCanarySubmitTransportError, Exception) as exc:
        assert "AUTHORING_GO_CANNOT_EXECUTE_CANARY" in str(exc) or "OWNER_GO_MISMATCH" in str(exc)
    assert all(call.method != "POST" for call in transport.calls)

    blocked = _fake_transport()
    blocked.bodies_by_endpoint["/api/v5/account/positions"] = json.dumps(
        {"code": "0", "data": [{"instId": DEFAULT_INSTRUMENT_ID, "pos": "1"}]}
    ).encode("utf-8")
    try:
        run_canary_submit_transport_v1(**_transport_kwargs(transport=blocked))
        raise AssertionError("open position must remain fail-closed")
    except LiveCanarySubmitTransportError as exc:
        assert "OPEN_POSITION" in str(exc)
    assert all(call.method != "POST" for call in blocked.calls)


def test_extractor_does_not_drop_non_object_data_entries() -> None:
    evidence = extract_canary_http_response_evidence_v1(
        status_code=200,
        body_bytes=json.dumps(
            {
                "code": "1",
                "msg": "All operations failed",
                "data": [
                    {"sCode": "51008", "sMsg": "kept"},
                    "not-an-object",
                    {"sCode": "51000", "sMsg": "also-kept"},
                ],
            }
        ).encode("utf-8"),
    )
    assert evidence["okx_data_count"] == 3
    assert evidence["okx_data"][0]["sCode"] == "51008"
    assert evidence["okx_data"][1]["_entry_not_object"] is True
    assert evidence["okx_data"][2]["sMsg"] == "also-kept"
