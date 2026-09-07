"""Offline tests for §11.14 current pos=1 flatten authority/pre-execution repair."""

from __future__ import annotations

import ast
import json
import time
from decimal import Decimal
from pathlib import Path

import pytest

from src.ops.section_11_13_5_p12_execution_prerequisite_11_position_side_posside_v1.contract_v1 import (
    flatten_order_side_from_signed_pos_v1,
)
from src.ops.section_11_14_current_sui_xperp_pos_1_flatten_authority_and_pre_execution_repair_v1.capture_wiring_v1 import (
    CAPTURE_STAGE_ORDER,
    FlattenCaptureWiringError,
    record_flatten_capture_stage_v1,
)
from src.ops.section_11_14_current_sui_xperp_pos_1_flatten_authority_and_pre_execution_repair_v1.constants_v1 import (
    ACK_CAPTURE_KIND,
    CLOSE_POSITION_ENDPOINT,
    CONSUMED_ENTRY_OWNER_EXECUTION_GO,
    ENTRY_PURPOSE_FORBIDDEN,
    EXPECTED_SIGNED_POSITION,
    FLATTEN_ACTION,
    FLATTEN_CONFIRM_TOKEN_EXPECTED,
    FLATTEN_HTTP_ENDPOINT,
    FLATTEN_PURPOSE_EXPECTED,
    FLATTEN_SECTION,
    HISTORICAL_G12_FLATTEN_OWNER_GO,
    HISTORICAL_PRODUCTIVE_FLATTEN_OWNER_GO,
    HISTORICAL_PRODUCTIVE_FLATTEN_SHA,
    INSTRUMENT_ID,
    MARGIN_MODE,
    ORDER_QTY_UNIT,
    ORDER_TYPE,
    PATH_ACCOUNT_CONFIG,
    PATH_ORDERS_PENDING,
    POS_SIDE_OBSERVED,
    REDUCE_ONLY_REQUIRED,
    VENUE_REDUCE_ONLY_NO_FLIP,
)
from src.ops.section_11_14_current_sui_xperp_pos_1_flatten_authority_and_pre_execution_repair_v1.contract_v1 import (
    evaluate_flatten_go_candidate_v1,
    flatten_go_contract_schema_v1,
    reject_entry_go_on_flatten_path_v1,
    reject_flatten_go_on_entry_path_v1,
)
from src.ops.section_11_14_current_sui_xperp_pos_1_flatten_authority_and_pre_execution_repair_v1.envelope_v1 import (
    FlattenSellEnvelopeError,
    build_flatten_sell_envelope_v1,
    extract_flatten_ticker_quotes_v1,
)
from src.ops.section_11_14_current_sui_xperp_pos_1_flatten_authority_and_pre_execution_repair_v1.get_only_http_v1 import (
    FlattenGetOnlyHttpClientV1,
    FlattenGetOnlyHttpError,
    RecordingFakeFlattenGetOnlyTransportV1,
)
from src.ops.section_11_14_current_sui_xperp_pos_1_flatten_authority_and_pre_execution_repair_v1.get_only_preflight_v1 import (
    run_flatten_get_only_preflight_v1,
)
from src.ops.section_11_14_current_sui_xperp_pos_1_flatten_authority_and_pre_execution_repair_v1.restart_contract_v1 import (
    reconstruct_flatten_durable_state_v1,
)
from src.ops.section_11_14_current_sui_xperp_pos_1_flatten_authority_and_pre_execution_repair_v1.wrapper_v1 import (
    RecordingFakeFlattenSubmitTransportV1,
    evaluate_current_sha_flatten_wrapper_v1,
    reject_close_position_endpoint_v1,
)
from src.ops.section_11_14_live_handoff_standing_fee_slippage_and_exact_execution_envelope_v1.fee_policy_v1 import (
    bind_standing_fee_policy_from_trade_fee_payload_v1,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.constants_v1 import (
    CANARY_AUTHORIZED,
    LIVE_ARMED,
    LIVE_ENABLED,
    POST_ALLOWED,
)

PACKAGE_DIR = Path(
    "src/ops/section_11_14_current_sui_xperp_pos_1_flatten_authority_and_pre_execution_repair_v1"
)
ORIGIN_SHA = "eb07fa66f96bb3f25786f32f844a5dc99719478e"
NOW_MS = str(int(time.time() * 1000))

TRADE_FEE = {
    "code": "0",
    "data": [
        {
            "instType": "FUTURES",
            "instFamily": "SUI-USD_UM_XPERP",
            "taker": "-0.0005",
            "maker": "-0.0002",
            "takerUSDC": "-0.0005",
            "makerUSDC": "-0.0002",
            "delivery": "0.0003",
        }
    ],
}


def _fee_policy():
    return bind_standing_fee_policy_from_trade_fee_payload_v1(
        payload=TRADE_FEE, instrument_id=INSTRUMENT_ID
    )


def _envelope(**overrides: object) -> dict:
    kwargs = {
        "origin_main_sha": ORIGIN_SHA,
        "signed_pos": "1",
        "pos_side": "net",
        "margin_mode": "cross",
        "bid": "0.8200",
        "ask": "0.8201",
        "last": "0.8200",
        "quote_ts_ms": NOW_MS,
        "evaluation_ts_ms": NOW_MS,
        "tick_sz": "0.0001",
        "sell_lmt": "0.0001",
        "max_sell": "9",
        "max_sell_px_sent": "0.8200",
        "ct_val": "1",
        "fee_policy": _fee_policy(),
        "pending_order_count": 0,
        "pending_order_gate_pass": True,
    }
    kwargs.update(overrides)
    return build_flatten_sell_envelope_v1(**kwargs)


def _candidate(*, envelope: dict, **overrides: object) -> dict:
    payload = {
        "action": FLATTEN_ACTION,
        "section": FLATTEN_SECTION,
        "purpose": FLATTEN_PURPOSE_EXPECTED,
        "confirm_token": FLATTEN_CONFIRM_TOKEN_EXPECTED,
        "origin_main_sha": ORIGIN_SHA,
        "instrument_id": INSTRUMENT_ID,
        "expected_signed_position": EXPECTED_SIGNED_POSITION,
        "pos_side": POS_SIDE_OBSERVED,
        "margin_mode": MARGIN_MODE,
        "order_side": "SELL",
        "order_qty": "1",
        "order_qty_unit": ORDER_QTY_UNIT,
        "reduce_only": True,
        "order_type": ORDER_TYPE,
        "exact_envelope_id": envelope["FLATTEN_ENVELOPE_ID"],
        "single_use": True,
        "retry_allowed": False,
        "second_submit_allowed": False,
        "pre_submit_fresh_get_required": True,
        "post_submit_position_recon_required": True,
        "capture_required": True,
        "consumed": False,
        "venue_reduce_only_no_flip_acknowledgement": VENUE_REDUCE_ONLY_NO_FLIP,
    }
    payload.update(overrides)
    return payload


def _bodies(*, pos: str = "1") -> dict[str, bytes]:
    ticker = {
        "code": "0",
        "data": [
            {
                "instId": INSTRUMENT_ID,
                "bidPx": "0.8200",
                "askPx": "0.8201",
                "last": "0.8200",
                "ts": NOW_MS,
            }
        ],
    }
    instruments = {
        "code": "0",
        "data": [
            {
                "instId": INSTRUMENT_ID,
                "instType": "FUTURES",
                "ruleType": "xperp",
                "minSz": "1",
                "lotSz": "1",
                "tickSz": "0.0001",
                "ctVal": "1",
                "ctValCcy": "SUI",
                "settleCcy": "USDC",
                "state": "live",
            }
        ],
    }
    price_band = {
        "code": "0",
        "data": [
            {
                "instId": INSTRUMENT_ID,
                "instType": "FUTURES",
                "buyLmt": "2.0000",
                "sellLmt": "0.0001",
                "ts": NOW_MS,
                "enabled": True,
            }
        ],
    }
    config = {
        "code": "0",
        "data": [{"uid": "1", "acctLv": "2", "posMode": "net_mode", "perm": "read_only,trade"}],
    }
    balance = {
        "code": "0",
        "data": [
            {
                "adjEq": "12.5",
                "availEq": "12.5",
                "details": [{"ccy": "USDC", "availEq": "10.25", "availBal": "10.10"}],
            }
        ],
    }
    positions = {
        "code": "0",
        "data": [
            {
                "instId": INSTRUMENT_ID,
                "pos": pos,
                "posSide": "net",
                "mgnMode": "cross",
            }
        ],
    }
    leverage = {
        "code": "0",
        "data": [
            {
                "instId": INSTRUMENT_ID,
                "mgnMode": "cross",
                "posSide": "net",
                "lever": "3",
            }
        ],
    }
    max_size = {"code": "0", "data": [{"instId": INSTRUMENT_ID, "maxBuy": "9", "maxSell": "9"}]}
    pending = {"code": "0", "data": []}
    return {
        "/api/v5/public/instruments": json.dumps(instruments).encode(),
        "/api/v5/market/ticker": json.dumps(ticker).encode(),
        "/api/v5/public/price-limit": json.dumps(price_band).encode(),
        "/api/v5/account/config": json.dumps(config).encode(),
        "/api/v5/account/balance": json.dumps(balance).encode(),
        "/api/v5/account/positions": json.dumps(positions).encode(),
        "/api/v5/account/leverage-info": json.dumps(leverage).encode(),
        "/api/v5/account/trade-fee": json.dumps(TRADE_FEE).encode(),
        "/api/v5/account/max-size": json.dumps(max_size).encode(),
        PATH_ORDERS_PENDING: json.dumps(pending).encode(),
    }


def test_standing_live_flags_remain_false() -> None:
    assert LIVE_ENABLED is False
    assert LIVE_ARMED is False
    assert CANARY_AUTHORIZED is False
    assert POST_ALLOWED is False


def test_flatten_go_schema_is_not_issued() -> None:
    schema = flatten_go_contract_schema_v1()
    assert schema["ISSUED"] is False
    assert schema["PRESENT"] is False
    assert schema["MECHANISM_EXPECTED_VALUES_ARE_NOT_ISSUED_AUTHORITY"] is True
    assert "PEAK_TRADE_OWNER_FLATTEN_GO_" not in json.dumps(schema)


def test_entry_go_rejected_by_flatten_path() -> None:
    reasons = reject_entry_go_on_flatten_path_v1(
        owner_go=CONSUMED_ENTRY_OWNER_EXECUTION_GO,
        purpose=ENTRY_PURPOSE_FORBIDDEN,
    )
    assert "ENTRY_OWNER_GO_CANNOT_AUTHORIZE_FLATTEN" in reasons
    envelope = _envelope()
    verdict = evaluate_flatten_go_candidate_v1(
        candidate=_candidate(
            envelope=envelope,
            owner_go=CONSUMED_ENTRY_OWNER_EXECUTION_GO,
            purpose=ENTRY_PURPOSE_FORBIDDEN,
        ),
        origin_main_sha=ORIGIN_SHA,
        instrument_id=INSTRUMENT_ID,
        expected_signed_position="1",
        order_side="SELL",
        order_qty="1",
        exact_envelope_id=envelope["FLATTEN_ENVELOPE_ID"],
    )
    assert verdict["accepted"] is False
    assert any("ENTRY" in item for item in verdict["reasons"])


def test_flatten_go_rejected_by_entry_path() -> None:
    reasons = reject_flatten_go_on_entry_path_v1(
        purpose=FLATTEN_PURPOSE_EXPECTED,
        confirm_token=FLATTEN_CONFIRM_TOKEN_EXPECTED,
    )
    assert "FLATTEN_GO_CANNOT_AUTHORIZE_ENTRY" in reasons
    envelope = _envelope()
    verdict = evaluate_flatten_go_candidate_v1(
        candidate=_candidate(envelope=envelope),
        origin_main_sha=ORIGIN_SHA,
        instrument_id=INSTRUMENT_ID,
        expected_signed_position="1",
        order_side="SELL",
        order_qty="1",
        exact_envelope_id=envelope["FLATTEN_ENVELOPE_ID"],
        entry_path=True,
    )
    assert verdict["accepted"] is False
    assert "FLATTEN_GO_CANNOT_AUTHORIZE_ENTRY" in verdict["reasons"]


def test_consumed_wrong_sha_instrument_position_envelope_and_confirm_rejected() -> None:
    envelope = _envelope()
    eid = envelope["FLATTEN_ENVELOPE_ID"]
    base = dict(
        origin_main_sha=ORIGIN_SHA,
        instrument_id=INSTRUMENT_ID,
        expected_signed_position="1",
        order_side="SELL",
        order_qty="1",
        exact_envelope_id=eid,
    )
    consumed = evaluate_flatten_go_candidate_v1(
        candidate=_candidate(envelope=envelope, consumed=True), **base
    )
    assert consumed["accepted"] is False
    assert "CONSUMED_GO_CANNOT_BE_REUSED" in consumed["reasons"]
    sha = evaluate_flatten_go_candidate_v1(
        candidate=_candidate(envelope=envelope, origin_main_sha="0" * 40), **base
    )
    assert sha["accepted"] is False
    assert "FLATTEN_GO_SHA_MISMATCH" in sha["reasons"]
    inst = evaluate_flatten_go_candidate_v1(
        candidate=_candidate(envelope=envelope),
        **{**base, "instrument_id": "BTC-USD_UM_XPERP-1"},
    )
    assert inst["accepted"] is False
    pos = evaluate_flatten_go_candidate_v1(
        candidate=_candidate(envelope=envelope),
        **{**base, "expected_signed_position": "2"},
    )
    assert pos["accepted"] is False
    env = evaluate_flatten_go_candidate_v1(
        candidate=_candidate(envelope=envelope, exact_envelope_id="deadbeef"),
        **{**base, "exact_envelope_id": "deadbeef"},
    )
    # candidate envelope id equals supplied, so mismatch vs actual envelope is
    # not this check; force candidate != expected:
    env = evaluate_flatten_go_candidate_v1(
        candidate=_candidate(envelope=envelope, exact_envelope_id="ab" * 20),
        **base,
    )
    assert env["accepted"] is False
    assert "FLATTEN_GO_ENVELOPE_MISMATCH" in env["reasons"]
    confirm = evaluate_flatten_go_candidate_v1(
        candidate=_candidate(envelope=envelope, confirm_token="NO"), **base
    )
    assert confirm["accepted"] is False
    assert "FLATTEN_CONFIRM_TOKEN_MISMATCH" in confirm["reasons"]
    hist = evaluate_flatten_go_candidate_v1(
        candidate=_candidate(envelope=envelope, owner_go=HISTORICAL_G12_FLATTEN_OWNER_GO),
        **base,
    )
    assert "HISTORICAL_G12_FLATTEN_GO_FORBIDDEN" in hist["reasons"]
    hist2 = evaluate_flatten_go_candidate_v1(
        candidate=_candidate(envelope=envelope, owner_go=HISTORICAL_PRODUCTIVE_FLATTEN_OWNER_GO),
        **base,
    )
    assert "HISTORICAL_G12_FLATTEN_GO_FORBIDDEN" in hist2["reasons"]


def test_pos_plus_one_mints_sell_qty_one_reduce_only_omitted_posside_bid_tick() -> None:
    assert flatten_order_side_from_signed_pos_v1(Decimal("1")) == "SELL"
    envelope = _envelope()
    assert envelope["SIDE"] == "SELL"
    assert envelope["QTY"] == "1"
    assert envelope["REDUCE_ONLY"] is True
    assert envelope["REQUEST_POS_SIDE_POLICY"] == "OMITTED_FROM_VENUE_NATIVE_BODY"
    assert "posSide" not in envelope["VENUE_NATIVE_BODY_PREVIEW"]
    assert envelope["VENUE_NATIVE_BODY_PREVIEW"]["reduceOnly"] is True
    assert type(envelope["VENUE_NATIVE_BODY_PREVIEW"]["reduceOnly"]) is bool
    assert envelope["SLIPPAGE"]["REFERENCE_KIND"] == "BID"
    assert envelope["LIMIT_PRICE"] == "0.8200"
    assert envelope["KIND"] == "SECTION_11_14_FLATTEN_SELL_ENVELOPE_V1"
    assert envelope["NOT_KIND"] == "SECTION_11_14_EXACT_EXECUTION_ENVELOPE_V1"
    assert envelope["CLORDID_BOUND_ONLY_AFTER_OWNER_FLATTEN_GO"] is True


def test_stale_quote_and_sell_lmt_and_insufficient_max_sell_rejected() -> None:
    stale_ts = str(int(time.time() * 1000) - 20_000)
    with pytest.raises(FlattenSellEnvelopeError, match="STALE_QUOTE"):
        _envelope(quote_ts_ms=stale_ts, evaluation_ts_ms=str(int(time.time() * 1000)))
    with pytest.raises(FlattenSellEnvelopeError, match="SELL_LMT"):
        _envelope(sell_lmt="1.0000")
    with pytest.raises(FlattenSellEnvelopeError, match="INSUFFICIENT_MAX_SELL"):
        _envelope(max_sell="0")
    with pytest.raises(FlattenSellEnvelopeError, match="MAX_SELL_PX_NOT_FLATTEN_LIMIT"):
        _envelope(max_sell_px_sent="0.8199")


def test_ticker_extractor_requires_bid_not_last_ask_fallback() -> None:
    with pytest.raises(FlattenSellEnvelopeError, match="BID_PX_MISSING"):
        extract_flatten_ticker_quotes_v1(
            ticker_payload={
                "code": "0",
                "data": [{"last": "0.82", "askPx": "0.83", "ts": NOW_MS}],
            }
        )


def test_get_only_allowlist_and_mutation_verbs_impossible() -> None:
    transport = RecordingFakeFlattenGetOnlyTransportV1()
    client = FlattenGetOnlyHttpClientV1(transport=transport)
    with pytest.raises(FlattenGetOnlyHttpError, match="HTTP_METHOD_HARD_BLOCK_BEFORE_WIRE:POST"):
        client.post(endpoint=PATH_ACCOUNT_CONFIG)
    with pytest.raises(FlattenGetOnlyHttpError, match="MUTATION_ENDPOINT_HARD_BLOCK"):
        client.get(endpoint=FLATTEN_HTTP_ENDPOINT)
    with pytest.raises(FlattenGetOnlyHttpError, match="MUTATION_ENDPOINT_HARD_BLOCK"):
        client.get(endpoint=CLOSE_POSITION_ENDPOINT)
    pending = client.get(endpoint=PATH_ORDERS_PENDING)
    assert pending.method == "GET"
    assert transport.calls[0].method == "GET"
    assert client.counters.write_request_count == 0


def test_get_only_preflight_mints_current_sell_envelope(tmp_path: Path) -> None:
    transport = RecordingFakeFlattenGetOnlyTransportV1(bodies_by_path=_bodies())
    result = run_flatten_get_only_preflight_v1(
        origin_main_sha=ORIGIN_SHA,
        origin_main_tree="21b04907f77ac84c9eb52d994c91deaf9a827168",
        transport=transport,
        header_provider=lambda url: {"User-Agent": "test", "OK-ACCESS-KEY": "redacted-test"},
        persist_root=tmp_path,
    )
    assert result["POST_PERFORMED"] is False
    assert result["OWNER_GO_CONSUMED"] is False
    assert result["SESSION_ARMED"] is False
    assert result["CURRENT_ORIGIN_MAIN_SHA"] == ORIGIN_SHA
    assert result["FLATTEN_ORDER_ENVELOPE_CURRENT"] is True
    assert result["FLATTEN_SIDE"] == "SELL"
    assert result["FLATTEN_QTY"] == "1"
    assert result["FLATTEN_REDUCE_ONLY"] is True
    assert result["PENDING_ORDER_GATE_PASS"] is True
    assert result["CURRENT_PENDING_ORDER_COUNT"] == 0
    assert result["CURRENT_MAX_SELL_AT_FLATTEN_PRICE"] == "9"
    assert str(result["CURRENT_SELL_LIMIT"]) == str(result["FLATTEN_LIMIT_PRICE"])
    assert result["MANIFEST_VERIFY_RC"] == 0
    assert all(item["method"] == "GET" for item in result["GETS"])
    assert any(PATH_ORDERS_PENDING in str(item["endpoint"]) for item in result["GETS"])
    max_ep = next(item["endpoint"] for item in result["GETS"] if item["name"] == "MAX_SIZE")
    assert f"px={result['CURRENT_SELL_LIMIT']}" in max_ep


def test_get_only_preflight_stops_when_position_not_one() -> None:
    transport = RecordingFakeFlattenGetOnlyTransportV1(bodies_by_path=_bodies(pos="2"))
    result = run_flatten_get_only_preflight_v1(
        origin_main_sha=ORIGIN_SHA,
        transport=transport,
        header_provider=lambda url: {"User-Agent": "test", "OK-ACCESS-KEY": "redacted-test"},
    )
    assert result["FINAL_ACTION"] == ("HARD_STOP_POSITION_STATE_CHANGED_REQUIRES_NEW_ADJUDICATION")
    assert result["FLATTEN_ORDER_ENVELOPE_CURRENT"] is False
    assert result["GET_ENDPOINT_COUNT"] == 6


def test_pending_order_gate_denies_open_order() -> None:
    bodies = _bodies()
    bodies[PATH_ORDERS_PENDING] = json.dumps(
        {"code": "0", "data": [{"instId": INSTRUMENT_ID, "ordId": "1"}]}
    ).encode()
    transport = RecordingFakeFlattenGetOnlyTransportV1(bodies_by_path=bodies)
    result = run_flatten_get_only_preflight_v1(
        origin_main_sha=ORIGIN_SHA,
        transport=transport,
        header_provider=lambda url: {"User-Agent": "test", "OK-ACCESS-KEY": "redacted-test"},
    )
    assert result["PENDING_ORDER_GATE_PASS"] is False
    assert result["FLATTEN_ORDER_ENVELOPE_CURRENT"] is False


def test_wrapper_no_post_without_authority_or_arming_or_retry() -> None:
    envelope = _envelope()
    fake = RecordingFakeFlattenSubmitTransportV1()
    denied = evaluate_current_sha_flatten_wrapper_v1(
        origin_main_sha=ORIGIN_SHA,
        flatten_go_candidate=None,
        envelope=envelope,
        session_armed=True,
        capture_wired=True,
        transport=fake,
        entry_owner_go=CONSUMED_ENTRY_OWNER_EXECUTION_GO,
        entry_purpose=ENTRY_PURPOSE_FORBIDDEN,
    )
    assert denied["POST_PERFORMED"] is False
    assert denied["POST_COUNT"] == 0
    assert fake.calls == []
    unarmed = evaluate_current_sha_flatten_wrapper_v1(
        origin_main_sha=ORIGIN_SHA,
        flatten_go_candidate=_candidate(envelope=envelope),
        envelope=envelope,
        session_armed=False,
        capture_wired=True,
        transport=fake,
    )
    assert unarmed["POST_PERFORMED"] is False
    retry = evaluate_current_sha_flatten_wrapper_v1(
        origin_main_sha=ORIGIN_SHA,
        flatten_go_candidate=_candidate(envelope=envelope),
        envelope=envelope,
        session_armed=True,
        capture_wired=True,
        retry=True,
        transport=fake,
    )
    assert retry["POST_PERFORMED"] is False
    assert "RETRY_FORBIDDEN" in retry["reasons"]
    second = evaluate_current_sha_flatten_wrapper_v1(
        origin_main_sha=ORIGIN_SHA,
        flatten_go_candidate=_candidate(envelope=envelope),
        envelope=envelope,
        session_armed=True,
        capture_wired=True,
        second_submit=True,
        transport=fake,
    )
    assert second["POST_PERFORMED"] is False
    hist_sha = evaluate_current_sha_flatten_wrapper_v1(
        origin_main_sha=HISTORICAL_PRODUCTIVE_FLATTEN_SHA,
        flatten_go_candidate=_candidate(envelope=envelope),
        envelope=envelope,
        session_armed=True,
        capture_wired=True,
        transport=fake,
    )
    assert hist_sha["POST_PERFORMED"] is False
    assert "HISTORICAL_WRAPPER_SHA_MUST_NOT_BE_UNFROZEN" in hist_sha["reasons"]


def test_wrapper_fake_transport_only_expected_trade_order_route() -> None:
    envelope = _envelope()
    fake = RecordingFakeFlattenSubmitTransportV1()
    result = evaluate_current_sha_flatten_wrapper_v1(
        origin_main_sha=ORIGIN_SHA,
        flatten_go_candidate=_candidate(envelope=envelope),
        envelope=envelope,
        session_armed=True,
        capture_wired=True,
        transport=fake,
    )
    assert result["accepted"] is True
    assert result["FAKE_TRANSPORT_ONLY"] is True
    assert result["WIRE_SEND_EXECUTED"] is False
    assert result["FLATTEN_EXECUTED"] is False
    assert result["OWNER_TOKEN_CONSUMED"] is False
    assert len(fake.calls) == 1
    assert fake.calls[0]["endpoint"] == FLATTEN_HTTP_ENDPOINT
    with pytest.raises(Exception, match="CLOSE_POSITION"):
        reject_close_position_endpoint_v1(CLOSE_POSITION_ENDPOINT)
    with pytest.raises(Exception, match="CLOSE_POSITION"):
        fake.post(endpoint=CLOSE_POSITION_ENDPOINT, body={})


def test_capture_order_ack_distinct_no_historical_reuse() -> None:
    durable: dict = {"recorded_stages": []}
    stages = {
        "PRE_ACTION_STATE_CAPTURE": {"kind": "pre"},
        "SUBMIT_INTENT_CAPTURE": {"kind": "intent"},
        "ACK_CAPTURE": {"kind": ACK_CAPTURE_KIND, "ack_id": "ACK-1"},
        "BOUND_FILL_CAPTURE": {"kind": "fill", "fill_id": "FILL-1", "ack_id": "ACK-1"},
        "FEE_CAPTURE": {"kind": "fee"},
        "POST_ACTION_POSITION_CAPTURE": {"kind": "pos"},
        "HANDOFF_COMMIT": {"kind": "handoff"},
        "RESTART_RECONSTRUCTION": {"kind": "restart"},
    }
    for name in CAPTURE_STAGE_ORDER:
        durable = record_flatten_capture_stage_v1(
            durable=durable, stage=name, artifact=stages[name]
        )
    assert durable["complete"] is True
    assert durable["CAPTURE_EXECUTED"] is False
    with pytest.raises(FlattenCaptureWiringError, match="CAPTURE_EXECUTION_FORBIDDEN"):
        record_flatten_capture_stage_v1(
            durable={"recorded_stages": []},
            stage="PRE_ACTION_STATE_CAPTURE",
            artifact={},
            execute=True,
        )
    with pytest.raises(FlattenCaptureWiringError, match="HANDOFF_COMMIT_BEFORE_REQUIRED_CAPTURE"):
        record_flatten_capture_stage_v1(
            durable={
                "recorded_stages": [
                    "PRE_ACTION_STATE_CAPTURE",
                    "SUBMIT_INTENT_CAPTURE",
                    "NOT_ACK",
                    "BOUND_FILL_CAPTURE",
                    "FEE_CAPTURE",
                    "POST_ACTION_POSITION_CAPTURE",
                ]
            },
            stage="HANDOFF_COMMIT",
            artifact={},
        )
    with pytest.raises(FlattenCaptureWiringError, match="ACK_AND_FILL_IDENTITIES_MUST_REMAIN"):
        d = {"recorded_stages": list(CAPTURE_STAGE_ORDER[:3])}
        record_flatten_capture_stage_v1(
            durable=d,
            stage="BOUND_FILL_CAPTURE",
            artifact={"fill_id": "X", "ack_id": "X"},
        )
    with pytest.raises(FlattenCaptureWiringError, match="HISTORICAL_FILL_REUSE_FORBIDDEN"):
        d = {"recorded_stages": list(CAPTURE_STAGE_ORDER[:3])}
        record_flatten_capture_stage_v1(
            durable=d,
            stage="BOUND_FILL_CAPTURE",
            artifact={"fill_id": "F", "ack_id": "A", "historical_reuse": True},
        )


def test_restart_completed_and_incomplete_default_no_submit() -> None:
    done = reconstruct_flatten_durable_state_v1(
        {
            "durable_state": "COMPLETED",
            "action_identity": "flatten-1",
            "instrument_id": INSTRUMENT_ID,
            "client_order_id": "c1",
            "ack_id": "a1",
            "fill_id": "f1",
        }
    )
    assert done["resubmit_allowed"] is False
    assert done["action"] == "NO_SUBMIT"
    incomplete = reconstruct_flatten_durable_state_v1({"durable_state": "INCOMPLETE"})
    assert incomplete["resubmit_allowed"] is False
    assert incomplete["new_explicit_authority_required"] is True
    none = reconstruct_flatten_durable_state_v1(None)
    assert none["action"] == "NO_SUBMIT"


def test_package_has_no_default_true_live_flags() -> None:
    blob = "\n".join(path.read_text(encoding="utf-8") for path in PACKAGE_DIR.glob("*.py"))
    assert "LIVE_ENABLED = True" not in blob
    assert "LIVE_ARMED = True" not in blob
    assert "CANARY_AUTHORIZED = True" not in blob
    assert "POST_ALLOWED = True" not in blob
    tree = ast.parse((PACKAGE_DIR / "get_only_http_v1.py").read_text(encoding="utf-8"))
    assert tree is not None
