"""Targeted tests for the §11.14 flatten execution harness. No live POST."""

from __future__ import annotations

import json
import time
from pathlib import Path

import pytest

from src.ops.section_11_14_current_sui_xperp_pos_1_flatten_authority_and_pre_execution_repair_v1.constants_v1 import (
    BOUND_FROZEN_ENVELOPE_ID,
    BOUND_FROZEN_EVIDENCE_RELATIVE,
    BOUND_ORIGIN_MAIN_SHA,
    EXPECTED_SIGNED_POSITION,
    FLATTEN_ACTION,
    FLATTEN_CONFIRM_TOKEN_EXPECTED,
    FLATTEN_HTTP_ENDPOINT,
    FLATTEN_PURPOSE_EXPECTED,
    FLATTEN_SECTION,
    HISTORICAL_FROZEN_EVIDENCE_RELATIVE,
    INSTRUMENT_ID,
    MARGIN_MODE,
    ORDER_QTY_UNIT,
    ORDER_TYPE,
    POS_SIDE_OBSERVED,
    VENUE_REDUCE_ONLY_NO_FLIP,
)
from src.ops.section_11_14_current_sui_xperp_pos_1_flatten_authority_and_pre_execution_repair_v1.envelope_v1 import (
    build_flatten_sell_envelope_v1,
)
from src.ops.section_11_14_current_sui_xperp_pos_1_flatten_authority_and_pre_execution_repair_v1.execution_harness_v1 import (
    run_flatten_execution_harness_v1,
)
from src.ops.section_11_14_current_sui_xperp_pos_1_flatten_authority_and_pre_execution_repair_v1.position_recon_v1 import (
    FLAT_CONFIRMED,
    POSITION_RECON_AMBIGUOUS,
    RESIDUAL_POSITION,
    evaluate_flatten_position_recon_v1,
)
from src.ops.section_11_14_current_sui_xperp_pos_1_flatten_authority_and_pre_execution_repair_v1.productive_transport_adapter_v1 import (
    FlattenProductiveTransportAdapterError,
    construct_productive_flatten_submit_adapter_v1,
)
from src.ops.section_11_14_current_sui_xperp_pos_1_flatten_authority_and_pre_execution_repair_v1.wrapper_v1 import (
    RecordingFakeFlattenSubmitTransportV1,
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

ORIGIN_SHA = BOUND_ORIGIN_MAIN_SHA
NOW_MS = str(int(time.time() * 1000))
FROZEN_ROOT = Path(BOUND_FROZEN_EVIDENCE_RELATIVE)
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


def _run(**kwargs: object) -> dict:
    defaults: dict = {
        "origin_main_sha": ORIGIN_SHA,
        "mode": "execute",
        "session_armed": True,
        "capture_wired": True,
        "retry": False,
        "second_submit": False,
    }
    defaults.update(kwargs)
    return run_flatten_execution_harness_v1(**defaults)


def test_standing_live_flags_remain_false() -> None:
    assert LIVE_ENABLED is False
    assert LIVE_ARMED is False
    assert CANARY_AUTHORIZED is False
    assert POST_ALLOWED is False


def test_missing_candidate_zero_post() -> None:
    envelope = _envelope()
    fake = RecordingFakeFlattenSubmitTransportV1()
    result = _run(candidate=None, envelope=envelope, transport=fake)
    assert result["POST_COUNT"] == 0
    assert fake.calls == []
    assert "FLATTEN_GO_CANDIDATE_MISSING" in result["reasons"]


def test_invalid_candidate_zero_post() -> None:
    envelope = _envelope()
    fake = RecordingFakeFlattenSubmitTransportV1()
    result = _run(
        candidate=_candidate(envelope=envelope, confirm_token="NO"),
        envelope=envelope,
        transport=fake,
    )
    assert result["POST_COUNT"] == 0
    assert fake.calls == []
    assert "FLATTEN_CONFIRM_TOKEN_MISMATCH" in result["reasons"]


def test_wrong_envelope_zero_post() -> None:
    envelope = _envelope()
    fake = RecordingFakeFlattenSubmitTransportV1()
    result = _run(
        candidate=_candidate(envelope=envelope, exact_envelope_id="ab" * 20),
        envelope=envelope,
        transport=fake,
    )
    assert result["POST_COUNT"] == 0
    assert "FLATTEN_GO_ENVELOPE_MISMATCH" in result["reasons"]


def test_wrong_sha_zero_post() -> None:
    envelope = _envelope()
    fake = RecordingFakeFlattenSubmitTransportV1()
    result = _run(
        candidate=_candidate(envelope=envelope, origin_main_sha="0" * 40),
        envelope=envelope,
        transport=fake,
    )
    assert result["POST_COUNT"] == 0
    assert "FLATTEN_GO_SHA_MISMATCH" in result["reasons"]


def test_session_unarmed_zero_post() -> None:
    envelope = _envelope()
    fake = RecordingFakeFlattenSubmitTransportV1()
    result = _run(
        candidate=_candidate(envelope=envelope),
        envelope=envelope,
        transport=fake,
        session_armed=False,
    )
    assert result["POST_COUNT"] == 0
    assert fake.calls == []
    assert "SESSION_NOT_ARMED" in result["reasons"]


def test_capture_not_ready_zero_post() -> None:
    envelope = _envelope()
    fake = RecordingFakeFlattenSubmitTransportV1()
    result = _run(
        candidate=_candidate(envelope=envelope),
        envelope=envelope,
        transport=fake,
        capture_wired=False,
    )
    assert result["POST_COUNT"] == 0
    assert "CAPTURE_NOT_READY" in result["reasons"]


def test_consumed_candidate_zero_post() -> None:
    envelope = _envelope()
    fake = RecordingFakeFlattenSubmitTransportV1()
    result = _run(
        candidate=_candidate(envelope=envelope, consumed=True),
        envelope=envelope,
        transport=fake,
    )
    assert result["POST_COUNT"] == 0
    assert "CONSUMED_GO_CANNOT_BE_REUSED" in result["reasons"]


def test_retry_and_second_submit_zero_post() -> None:
    envelope = _envelope()
    fake = RecordingFakeFlattenSubmitTransportV1()
    retry = _run(
        candidate=_candidate(envelope=envelope),
        envelope=envelope,
        transport=fake,
        retry=True,
    )
    assert retry["POST_COUNT"] == 0
    assert "RETRY_FORBIDDEN" in retry["reasons"]
    second = _run(
        candidate=_candidate(envelope=envelope),
        envelope=envelope,
        transport=fake,
        second_submit=True,
    )
    assert second["POST_COUNT"] == 0
    assert "SECOND_SUBMIT_FORBIDDEN" in second["reasons"]


def test_transport_missing_zero_post() -> None:
    envelope = _envelope()
    result = _run(
        candidate=_candidate(envelope=envelope),
        envelope=envelope,
        transport=None,
    )
    assert result["POST_COUNT"] == 0
    assert "PRODUCTIVE_TRANSPORT_NOT_BOUND" in result["reasons"]


def test_dry_run_never_posts(tmp_path: Path) -> None:
    envelope = _envelope()
    fake = RecordingFakeFlattenSubmitTransportV1()
    result = _run(
        candidate=_candidate(envelope=envelope),
        envelope=envelope,
        transport=fake,
        mode="dry-run",
        session_armed=True,
        persist_root=tmp_path / "dry",
    )
    assert result["DRY_RUN"] is True
    assert result["POST_COUNT"] == 0
    assert result["WIRE_SEND"] is False
    assert fake.calls == []
    assert result["AUTHORITY_CANDIDATE_ACCEPTED"] is True
    assert result["CAPTURE_READY"] is True
    assert result["MANIFEST_VERIFY_RC"] == 0


def test_fake_exactly_one_post_then_durable_consume_blocks_second(tmp_path: Path) -> None:
    envelope = _envelope()
    candidate = _candidate(envelope=envelope)
    fake = RecordingFakeFlattenSubmitTransportV1()
    store = tmp_path / "durable"
    first = _run(
        candidate=candidate,
        envelope=envelope,
        transport=fake,
        durable_store=store,
        positions_payload={
            "code": "0",
            "data": [{"instId": INSTRUMENT_ID, "pos": "0", "posSide": "net", "mgnMode": "cross"}],
        },
        positions_get_performed=True,
    )
    assert first["FAKE_POST_COUNT"] == 1
    assert first["REAL_POST_COUNT"] == 0
    assert first["WIRE_SEND"] is False
    assert first["OWNER_TOKEN_CONSUMED"] is True
    assert len(fake.calls) == 1
    assert fake.calls[0]["endpoint"] == FLATTEN_HTTP_ENDPOINT
    assert fake.calls[0]["body"]["reduceOnly"] is True
    assert "posSide" not in fake.calls[0]["body"]
    assert first["POSITION_RECON"]["outcome"] == FLAT_CONFIRMED
    second_fake = RecordingFakeFlattenSubmitTransportV1()
    second = _run(
        candidate=candidate,
        envelope=envelope,
        transport=second_fake,
        durable_store=store,
    )
    assert second["POST_COUNT"] == 0
    assert second_fake.calls == []
    assert "CONSUMED_STATE_CANNOT_RESUBMIT" in second["reasons"]


def test_ambiguous_transport_fail_closed_no_retry(tmp_path: Path) -> None:
    envelope = _envelope()

    class Boom(RecordingFakeFlattenSubmitTransportV1):
        def post(self, *, endpoint: str, body: dict) -> dict:
            self.calls.append({"method": "POST", "endpoint": endpoint, "body": dict(body)})
            raise RuntimeError("INDETERMINATE_TIMEOUT")

    boom = Boom()
    store = tmp_path / "durable"
    first = _run(
        candidate=_candidate(envelope=envelope),
        envelope=envelope,
        transport=boom,
        durable_store=store,
    )
    assert first["POST_COUNT"] == 0
    assert first["AMBIGUOUS_TRANSPORT"] is True
    second = _run(
        candidate=_candidate(envelope=envelope),
        envelope=envelope,
        transport=RecordingFakeFlattenSubmitTransportV1(),
        durable_store=store,
    )
    assert second["POST_COUNT"] == 0
    assert "CONSUMED_STATE_CANNOT_RESUBMIT" in second["reasons"]


def test_productive_adapter_constructible_but_cannot_send() -> None:
    adapter = construct_productive_flatten_submit_adapter_v1()
    assert adapter.implemented is True
    assert adapter.inner.network_session_authorized is False
    with pytest.raises(FlattenProductiveTransportAdapterError, match="NETWORK_SESSION_NOT"):
        adapter.post(endpoint=FLATTEN_HTTP_ENDPOINT, body={"instId": INSTRUMENT_ID})


def test_productive_adapter_rejected_as_harness_transport() -> None:
    envelope = _envelope()
    adapter = construct_productive_flatten_submit_adapter_v1()
    with pytest.raises(Exception, match="PRODUCTIVE_ADAPTER_MUST_NOT_BE_USED_TO_SEND"):
        _run(
            candidate=_candidate(envelope=envelope),
            envelope=envelope,
            transport=adapter,
        )


def test_position_recon_empty_data_is_not_zero() -> None:
    empty = evaluate_flatten_position_recon_v1(
        payload={"code": "0", "data": []}, get_performed=True
    )
    assert empty["outcome"] == POSITION_RECON_AMBIGUOUS
    residual = evaluate_flatten_position_recon_v1(
        payload={
            "code": "0",
            "data": [{"instId": INSTRUMENT_ID, "pos": "1", "posSide": "net"}],
        },
        get_performed=True,
    )
    assert residual["outcome"] == RESIDUAL_POSITION
    flat = evaluate_flatten_position_recon_v1(
        payload={
            "code": "0",
            "data": [{"instId": INSTRUMENT_ID, "pos": "0", "posSide": "net"}],
        },
        get_performed=True,
    )
    assert flat["outcome"] == FLAT_CONFIRMED


def test_frozen_envelope_dry_run_offline() -> None:
    envelope = json.loads((FROZEN_ROOT / "FLATTEN_ENVELOPE.json").read_text(encoding="utf-8"))
    candidate = _candidate(envelope=envelope)
    result = run_flatten_execution_harness_v1(
        origin_main_sha=ORIGIN_SHA,
        candidate=candidate,
        envelope=envelope,
        mode="dry-run",
        frozen_evidence_root=str(FROZEN_ROOT),
    )
    assert result["AUTHORITY_CANDIDATE_ACCEPTED"] is True
    assert result["POST_COUNT"] == 0
    assert result["WIRE_SEND"] is False
    assert result["PRODUCTIVE_TRANSPORT_IMPLEMENTED"] is True
    assert result["PRODUCTIVE_TRANSPORT_USED"] is False
    assert envelope["FLATTEN_ENVELOPE_ID"] == BOUND_FROZEN_ENVELOPE_ID


def test_pre_wire_session_armed_never_network_sends_frozen_envelope() -> None:
    """Invocation-scoped session_armed=True must abort before any transport POST."""

    class NetworkTrapTransport:
        def __init__(self) -> None:
            self.calls: list[dict] = []

        def post(self, *, endpoint: str, body: dict) -> dict:
            self.calls.append({"endpoint": endpoint, "body": dict(body)})
            raise AssertionError("NETWORK_SEND_MUST_NOT_OCCUR")

    envelope = json.loads((FROZEN_ROOT / "FLATTEN_ENVELOPE.json").read_text(encoding="utf-8"))
    owner_declared = {
        "action": FLATTEN_ACTION,
        "purpose": FLATTEN_PURPOSE_EXPECTED,
        "confirm_token": FLATTEN_CONFIRM_TOKEN_EXPECTED,
        "origin_main_sha": ORIGIN_SHA,
        "instrument_id": INSTRUMENT_ID,
        "expected_signed_position": "1",
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
    }
    trap_declared = NetworkTrapTransport()
    declared = run_flatten_execution_harness_v1(
        origin_main_sha=ORIGIN_SHA,
        candidate=owner_declared,
        envelope=envelope,
        mode="execute",
        session_armed=True,
        capture_wired=True,
        retry=False,
        second_submit=False,
        transport=trap_declared,
        frozen_evidence_root=str(FROZEN_ROOT),
    )
    assert trap_declared.calls == []
    assert declared["REAL_POST_COUNT"] == 0
    assert declared["WIRE_SEND"] is False
    assert declared["POSITION_MUTATION_EXECUTED"] is False
    assert declared["AUTHORITY_RUNTIME_ISSUED"] is False
    assert declared["EVALUATOR_ISSUED"] is False
    assert any("FLATTEN_GO_FIELDS_MISSING" in str(item) for item in declared["reasons"])

    trap_complete = NetworkTrapTransport()
    complete = run_flatten_execution_harness_v1(
        origin_main_sha=ORIGIN_SHA,
        candidate=_candidate(envelope=envelope),
        envelope=envelope,
        mode="execute",
        session_armed=True,
        capture_wired=True,
        retry=False,
        second_submit=False,
        transport=trap_complete,
        frozen_evidence_root=str(FROZEN_ROOT),
    )
    assert trap_complete.calls == []
    assert complete["REAL_POST_COUNT"] == 0
    assert complete["WIRE_SEND"] is False
    assert complete["POSITION_MUTATION_EXECUTED"] is False
    assert complete["AUTHORITY_RUNTIME_ISSUED"] is False
    assert complete["EVALUATOR_ISSUED"] is False
    assert "NON_FAKE_TRANSPORT_FORBIDDEN_IN_THIS_HARNESS" in complete["reasons"]


def test_historical_frozen_envelope_is_not_current_submit_bind() -> None:
    historical_root = Path(HISTORICAL_FROZEN_EVIDENCE_RELATIVE)
    envelope = json.loads((historical_root / "FLATTEN_ENVELOPE.json").read_text(encoding="utf-8"))
    assert envelope["FLATTEN_ENVELOPE_ID"] != BOUND_FROZEN_ENVELOPE_ID
    candidate = _candidate(envelope=envelope)
    candidate["origin_main_sha"] = str(envelope["ORIGIN_MAIN_SHA"])
    result = run_flatten_execution_harness_v1(
        origin_main_sha=ORIGIN_SHA,
        candidate=candidate,
        envelope=envelope,
        mode="dry-run",
        frozen_evidence_root=str(historical_root),
    )
    assert result["AUTHORITY_CANDIDATE_ACCEPTED"] is False
    assert result["POST_COUNT"] == 0
    assert result["REAL_POST_COUNT"] == 0
    assert result["WIRE_SEND"] is False
    reasons = {str(item) for item in (result.get("reasons") or [])}
    assert "FLATTEN_GO_SHA_MISMATCH" in reasons
