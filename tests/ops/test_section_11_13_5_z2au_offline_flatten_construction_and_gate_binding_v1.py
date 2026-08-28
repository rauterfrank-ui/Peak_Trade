"""Offline Z2AU flatten construction, B8-cap binding, and post-submit state.

No network. Positive path may prove request construction and gate
binding only. Never claims LIVE_FLATTEN_PROVABILITY=PROVEN.
"""

from __future__ import annotations

from dataclasses import replace
from typing import Any, Mapping

import pytest

from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.constants_v1 import (
    DEFAULT_INSTRUMENT_ID,
    ORDER_COUNT_LIMIT,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.flatten_limit_price_contract_v1 import (
    FRESHNESS_THRESHOLD_MS,
    FlattenPriceInputV1,
    LIVE_FLATTEN_PROVABILITY_STATUS,
    evaluate_canary_flatten_limit_price_contract_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.flatten_offline_pipeline_v1 import (
    evaluate_offline_flatten_construction_and_gates_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.flatten_orchestration_contract_v1 import (
    evaluate_canary_flatten_orchestration_contract_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.flatten_post_submit_evidence_state_v1 import (
    STATE_ACKNOWLEDGED,
    STATE_FILLED,
    STATE_NOT_SUBMITTED,
    STATE_POSITION_CLOSED_PROVEN,
    STATE_POSITION_REMAINS,
    STATE_SUBMITTED_UNACKNOWLEDGED,
    STATE_UNKNOWN_FAIL_CLOSED,
    evaluate_canary_flatten_post_submit_evidence_state_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.flatten_submit_transport_v1 import (
    DEDICATED_FLATTEN_TRANSPORT_LIVE_WIRE_ENABLED,
    LIVE_FLATTEN_PROVABILITY,
    LiveCanaryFlattenSubmitTransportError,
    build_canary_flatten_submit_request_v1,
    run_canary_flatten_submit_transport_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.http_client_v1 import (
    CanaryFlattenHttpPermitV1,
    LiveCanaryHttpClientV1,
    LiveCanaryHttpError,
    RecordingFakeCanaryTransportV1,
    UrllibLiveCanaryTransportV1,
)

OWNER_GO = "OWNER_GO_LIVE_CANARY_MINIMUM_EXPOSURE"
ORIGIN_SHA = "05366731f23f95f210c6d6b442130b4d114d912e"
TARGET = DEFAULT_INSTRUMENT_ID
OTHER = "BTC-USDT-SWAP"
QUOTE_TS = "1787145055768"
EVAL_TS = "1787145056000"


def _positions(*rows: Mapping[str, Any]) -> dict[str, Any]:
    return {"code": "0", "data": list(rows)}


def _pending(*rows: Mapping[str, Any]) -> dict[str, Any]:
    return {"code": "0", "data": list(rows)}


def _price_input(*, side: str = "SELL", pos: str = "1", **overrides: Any) -> FlattenPriceInputV1:
    payload: dict[str, Any] = {
        "flatten_side": side,
        "observed_signed_pos": pos,
        "bid": "64805.6",
        "ask": "64805.7",
        "quote_timestamp_ms": QUOTE_TS,
        "evaluation_timestamp_ms": EVAL_TS,
        "tick_sz": "0.1",
        "freshness_threshold_ms": str(FRESHNESS_THRESHOLD_MS),
    }
    payload.update(overrides)
    return FlattenPriceInputV1(**payload)


def _price_permit(*, side: str = "SELL", pos: str = "1") -> Any:
    decision = evaluate_canary_flatten_limit_price_contract_v1(_price_input(side=side, pos=pos))
    assert decision.permit is not None
    return decision.permit


def _construct(*, pos: str = "1", **overrides: Any) -> Any:
    side = "SELL" if int(pos) > 0 else "BUY"
    payload: dict[str, Any] = {
        "positions_payload": _positions({"instId": TARGET, "pos": pos}),
        "price_input": _price_input(side=side, pos=pos),
        "owner_go": OWNER_GO,
        "origin_main_sha": ORIGIN_SHA,
        "instrument_id": TARGET,
    }
    payload.update(overrides)
    return evaluate_offline_flatten_construction_and_gates_v1(**payload)


def test_positive_offline_construction_does_not_post_or_prove_live() -> None:
    verdict = _construct()
    assert verdict.submit_eligible is True
    assert verdict.request_body is not None
    assert verdict.request_body["side"] == "sell"
    assert verdict.request_body["reduceOnly"] is True
    assert verdict.request_body["ordType"] == "limit"
    assert verdict.request_body["sz"] == "1"
    assert verdict.request_body["instId"] == TARGET
    assert verdict.evidence_state == STATE_NOT_SUBMITTED
    assert verdict.live_flatten_provability == LIVE_FLATTEN_PROVABILITY_STATUS == "UNPROVEN"
    assert verdict.live_wire_enabled is False
    assert verdict.live_authorized is False
    assert verdict.order_count_limit == 1
    assert verdict.freshness_threshold_ms == 5000
    assert verdict.productive_venue_proof is False
    assert verdict.audit_class == "submit_eligible_state_not_posted"
    assert LIVE_FLATTEN_PROVABILITY == "UNPROVEN"
    assert DEDICATED_FLATTEN_TRANSPORT_LIVE_WIRE_ENABLED is False


def test_short_closes_buy_reduce_only() -> None:
    verdict = _construct(pos="-2")
    assert verdict.submit_eligible is True
    assert verdict.request_body is not None
    assert verdict.request_body["side"] == "buy"
    assert verdict.request_body["sz"] == "2"
    assert verdict.request_body["reduceOnly"] is True
    assert verdict.live_flatten_provability == "UNPROVEN"


def test_live_authorized_denies_construction(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "src.ops.section_11_13_5_live_canary_minimum_exposure_v1.flatten_offline_pipeline_v1.LIVE_AUTHORIZED",
        True,
    )
    verdict = _construct()
    assert verdict.submit_eligible is False
    assert verdict.request_body is None
    assert "LIVE_DISABLED_DEFAULT" in verdict.blocking_reasons
    assert verdict.evidence_state == STATE_NOT_SUBMITTED
    assert verdict.live_flatten_provability == "UNPROVEN"


def test_live_enabled_and_armed_deny(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "src.ops.section_11_13_5_live_canary_minimum_exposure_v1.flatten_offline_pipeline_v1.LIVE_ENABLED",
        True,
    )
    enabled = _construct()
    assert enabled.submit_eligible is False
    monkeypatch.setattr(
        "src.ops.section_11_13_5_live_canary_minimum_exposure_v1.flatten_offline_pipeline_v1.LIVE_ENABLED",
        False,
    )
    monkeypatch.setattr(
        "src.ops.section_11_13_5_live_canary_minimum_exposure_v1.flatten_offline_pipeline_v1.LIVE_ARMED",
        True,
    )
    armed = _construct()
    assert armed.submit_eligible is False
    assert "LIVE_DISABLED_DEFAULT" in armed.blocking_reasons


def test_missing_confirm_token_does_not_unlock_or_block_offline_construction() -> None:
    verdict = _construct(confirm_token=None)
    assert verdict.submit_eligible is True
    extra = _construct(confirm_token="not-a-live-unlock")
    assert extra.submit_eligible is True
    assert extra.live_authorized is False
    assert extra.live_flatten_provability == "UNPROVEN"


def test_no_position_denies() -> None:
    verdict = _construct(positions_payload=_positions())
    assert verdict.submit_eligible is False
    assert verdict.request_body is None
    assert verdict.evidence_state == STATE_NOT_SUBMITTED


def test_wrong_instrument_denies() -> None:
    verdict = _construct(instrument_id=OTHER)
    assert verdict.submit_eligible is False
    assert "INSTRUMENT_BINDING_MISMATCH" in verdict.blocking_reasons


def test_malformed_position_payload_denies() -> None:
    verdict = _construct(positions_payload={"code": "1", "data": [{"instId": TARGET, "pos": "1"}]})
    assert verdict.submit_eligible is False
    joined = " ".join(verdict.blocking_reasons)
    assert any(
        token in joined for token in ("POSITION", "CAP", "PAYLOAD", "EXCHANGE_STATE", "OBSERVATION")
    )


def test_duplicate_conflicting_position_rows_denies() -> None:
    verdict = _construct(
        positions_payload=_positions(
            {"instId": TARGET, "pos": "1"},
            {"instId": TARGET, "pos": "2"},
        )
    )
    assert verdict.submit_eligible is False
    joined = " ".join(verdict.blocking_reasons)
    assert "AMBIGUOUS" in joined or "POSITION" in joined or "CAP" in joined


def test_other_open_instrument_denies_via_b8_cap() -> None:
    verdict = _construct(
        positions_payload=_positions(
            {"instId": TARGET, "pos": "1"},
            {"instId": OTHER, "pos": "1"},
        )
    )
    assert verdict.submit_eligible is False
    assert any(
        "DENY_OTHER_OPEN_INSTRUMENT_PRESENT" in reason for reason in verdict.blocking_reasons
    )


def test_stale_quote_denies() -> None:
    verdict = _construct(
        price_input=_price_input(evaluation_timestamp_ms=str(int(QUOTE_TS) + 5001))
    )
    assert verdict.submit_eligible is False
    assert verdict.request_body is None


def test_malformed_quote_denies() -> None:
    verdict = _construct(price_input=_price_input(bid="not-a-price"))
    assert verdict.submit_eligible is False
    assert verdict.request_body is None


def test_zero_and_negative_requested_size_denied() -> None:
    zero = _construct(requested_qty="0")
    assert zero.submit_eligible is False
    negative = _construct(requested_qty="-1")
    assert negative.submit_eligible is False


def test_over_close_prevention() -> None:
    verdict = _construct(requested_qty="2")
    assert verdict.submit_eligible is False
    assert any("OVERSIZE_FLATTEN" in reason for reason in verdict.blocking_reasons)


def test_incorrect_side_mapping_denied() -> None:
    verdict = _construct(price_input=_price_input(side="BUY", pos="-1"))
    assert verdict.submit_eligible is False
    assert any("SIDE" in reason for reason in verdict.blocking_reasons)


def test_reduce_only_mismatch_denied() -> None:
    orch = evaluate_canary_flatten_orchestration_contract_v1(
        positions_payload=_positions({"instId": TARGET, "pos": "1"}),
        owner_go=OWNER_GO,
        origin_main_sha=ORIGIN_SHA,
    )
    assert orch.permit is not None and orch.flatten_plan is not None
    mutated = replace(orch.flatten_plan, reduce_only=False)
    with pytest.raises(LiveCanaryFlattenSubmitTransportError, match="FLATTEN_REDUCE_ONLY_REQUIRED"):
        build_canary_flatten_submit_request_v1(
            permit=orch.permit,
            plan=mutated,
            price_permit=_price_permit(),
            positions_payload=_positions({"instId": TARGET, "pos": "1"}),
        )


def test_transport_unavailable_denies_fake_only_path() -> None:
    orch = evaluate_canary_flatten_orchestration_contract_v1(
        positions_payload=_positions({"instId": TARGET, "pos": "1"}),
        owner_go=OWNER_GO,
        origin_main_sha=ORIGIN_SHA,
    )
    assert orch.permit is not None and orch.flatten_plan is not None
    with pytest.raises(
        LiveCanaryFlattenSubmitTransportError, match="PRODUCTIVE_WIRE|FAKE_TRANSPORT"
    ):
        run_canary_flatten_submit_transport_v1(
            permit=orch.permit,
            plan=orch.flatten_plan,
            price_permit=_price_permit(),
            positions_payload=_positions({"instId": TARGET, "pos": "1"}),
            transport=UrllibLiveCanaryTransportV1(wire_send_enabled=False),
        )


def test_first_post_attempt_failure_classifies_unknown_fail_closed() -> None:
    orch = evaluate_canary_flatten_orchestration_contract_v1(
        positions_payload=_positions({"instId": TARGET, "pos": "1"}),
        owner_go=OWNER_GO,
        origin_main_sha=ORIGIN_SHA,
    )
    fake = RecordingFakeCanaryTransportV1(post_status_code=500)
    result = run_canary_flatten_submit_transport_v1(
        permit=orch.permit,
        plan=orch.flatten_plan,
        price_permit=_price_permit(),
        positions_payload=_positions({"instId": TARGET, "pos": "1"}),
        transport=fake,
    )
    assert result["ok"] is False
    evidence = evaluate_canary_flatten_post_submit_evidence_state_v1(
        submit_attempted=True,
        send_attempted=True,
        http_status=500,
        response_body={"code": "0", "data": [{"sCode": "0"}]},
    )
    assert evidence.evidence_state == STATE_UNKNOWN_FAIL_CLOSED
    assert evidence.productive_venue_proof is False
    assert evidence.live_flatten_provability == "UNPROVEN"


def test_ambiguous_timeout_is_submitted_unacknowledged_no_retry() -> None:
    orch = evaluate_canary_flatten_orchestration_contract_v1(
        positions_payload=_positions({"instId": TARGET, "pos": "1"}),
        owner_go=OWNER_GO,
        origin_main_sha=ORIGIN_SHA,
    )
    fake = RecordingFakeCanaryTransportV1(raise_timeout_on_post=True)
    with pytest.raises(
        LiveCanaryFlattenSubmitTransportError, match="UNKNOWN_FLATTEN_SUBMIT_TIMEOUT"
    ):
        run_canary_flatten_submit_transport_v1(
            permit=orch.permit,
            plan=orch.flatten_plan,
            price_permit=_price_permit(),
            positions_payload=_positions({"instId": TARGET, "pos": "1"}),
            transport=fake,
        )
    evidence = evaluate_canary_flatten_post_submit_evidence_state_v1(
        submit_attempted=True,
        send_attempted=True,
        transport_error="UNKNOWN_FLATTEN_SUBMIT_TIMEOUT",
    )
    assert evidence.evidence_state == STATE_SUBMITTED_UNACKNOWLEDGED
    retry = evaluate_canary_flatten_post_submit_evidence_state_v1(
        submit_attempted=True,
        send_attempted=True,
        transport_error="UNKNOWN_FLATTEN_SUBMIT_NO_BLIND_RETRY",
    )
    assert retry.evidence_state == STATE_UNKNOWN_FAIL_CLOSED
    assert "NO_RETRY" in retry.blocking_reasons


def test_duplicate_flatten_submit_forbidden() -> None:
    client = LiveCanaryHttpClientV1(
        rest_base="https://eea.okx.com",
        rest_host="eea.okx.com",
        transport=RecordingFakeCanaryTransportV1(),
    )
    permit = CanaryFlattenHttpPermitV1(owner_go=OWNER_GO, clordid="flat", permit_id="f1")
    body = '{"instId":"%s","ordType":"limit","px":"1","sz":"1","reduceOnly":true}' % TARGET
    client.post_flatten_order(permit=permit, body_text=body, headers={"User-Agent": "test"})
    with pytest.raises(LiveCanaryHttpError, match="DUPLICATE_FLATTEN_SUBMIT_FORBIDDEN"):
        client.post_flatten_order(permit=permit, body_text=body, headers={"User-Agent": "test"})
    evidence = evaluate_canary_flatten_post_submit_evidence_state_v1(
        submit_attempted=True,
        send_attempted=False,
        transport_error="DUPLICATE_FLATTEN_SUBMIT_FORBIDDEN",
    )
    assert evidence.evidence_state == STATE_UNKNOWN_FAIL_CLOSED
    assert "NO_RETRY" in evidence.blocking_reasons


def test_order_count_limit_greater_than_one_denied(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "src.ops.section_11_13_5_live_canary_minimum_exposure_v1.flatten_offline_pipeline_v1.ORDER_COUNT_LIMIT",
        2,
    )
    verdict = _construct()
    assert verdict.submit_eligible is False
    assert "ORDER_COUNT_LIMIT_MUST_REMAIN_1" in verdict.blocking_reasons
    assert ORDER_COUNT_LIMIT == 1


def test_ack_without_snapshots_is_acknowledged_not_venue_proof() -> None:
    evidence = evaluate_canary_flatten_post_submit_evidence_state_v1(
        submit_attempted=True,
        send_attempted=True,
        http_status=200,
        response_body={"code": "0", "data": [{"sCode": "0", "ordId": "x", "sz": "1"}]},
    )
    assert evidence.evidence_state == STATE_ACKNOWLEDGED
    assert evidence.productive_venue_proof is False
    assert evidence.live_flatten_provability == "UNPROVEN"
    assert evidence.audit_class == "venue_acknowledgement"


def test_filled_requires_explicit_fill_fields() -> None:
    evidence = evaluate_canary_flatten_post_submit_evidence_state_v1(
        submit_attempted=True,
        send_attempted=True,
        http_status=200,
        response_body={
            "code": "0",
            "data": [{"sCode": "0", "ordId": "x", "sz": "1", "accFillSz": "1"}],
        },
    )
    assert evidence.evidence_state == STATE_FILLED
    assert evidence.filled_claimed is True
    assert evidence.productive_venue_proof is False
    assert evidence.live_flatten_provability == "UNPROVEN"


def test_injected_closed_snapshot_is_contract_not_venue_proof() -> None:
    evidence = evaluate_canary_flatten_post_submit_evidence_state_v1(
        submit_attempted=True,
        send_attempted=True,
        http_status=200,
        response_body={"code": "0", "data": [{"sCode": "0", "ordId": "x", "sz": "1"}]},
        pre_positions_payload=_positions({"instId": TARGET, "pos": "1"}),
        post_positions_payload=_positions({"instId": TARGET, "pos": "0"}),
        post_pending_orders_payload=_pending(),
    )
    assert evidence.evidence_state == STATE_POSITION_CLOSED_PROVEN
    assert evidence.position_closed_contract is True
    assert evidence.productive_venue_proof is False
    assert evidence.live_flatten_provability == "UNPROVEN"
    assert "INJECTED_SNAPSHOT_CONTRACT_ONLY" in evidence.blocking_reasons


def test_position_remains_after_ack() -> None:
    evidence = evaluate_canary_flatten_post_submit_evidence_state_v1(
        submit_attempted=True,
        send_attempted=True,
        http_status=200,
        response_body={"code": "0", "data": [{"sCode": "0", "ordId": "x"}]},
        pre_positions_payload=_positions({"instId": TARGET, "pos": "1"}),
        post_positions_payload=_positions({"instId": TARGET, "pos": "1"}),
        post_pending_orders_payload=_pending(),
    )
    assert evidence.evidence_state == STATE_POSITION_REMAINS
    assert evidence.productive_venue_proof is False


def test_not_submitted_construction_state() -> None:
    evidence = evaluate_canary_flatten_post_submit_evidence_state_v1(
        submit_attempted=False,
        send_attempted=False,
    )
    assert evidence.evidence_state == STATE_NOT_SUBMITTED
    assert evidence.actual_post is False
    assert evidence.live_flatten_provability == "UNPROVEN"
