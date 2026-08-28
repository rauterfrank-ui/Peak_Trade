"""§11.13.5 productive flatten wiring tests. Synthetic only. No network."""

from __future__ import annotations

import inspect
from typing import Any, Mapping

import pytest

from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.config_v1 import (
    example_incomplete_config_dict_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.constants_v1 import (
    DEFAULT_INSTRUMENT_ID,
    LIVE_ARMED,
    LIVE_AUTHORIZED,
    LIVE_ENABLED,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.flatten_execute_authority_v1 import (
    FLATTEN_EXECUTE_CONFIRM_TOKEN_CANONICAL,
    FLATTEN_EXECUTE_OWNER_GO_CANONICAL,
    FLATTEN_EXECUTE_PURPOSE_CANONICAL,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.flatten_gated_submit_v1 import (
    FlattenGatedSubmitBoundaryV1,
    submit_productive_flatten_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.flatten_limit_price_contract_v1 import (
    FRESHNESS_THRESHOLD_MS,
    FlattenPriceInputV1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.flatten_post_action_proof_contract_v1 import (
    evaluate_canary_flatten_post_action_proof_contract_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.flatten_post_submit_evidence_state_v1 import (
    evaluate_canary_flatten_post_submit_evidence_state_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.flatten_pre_send_gate_v1 import (
    FlattenPreSendGateInputV1,
    evaluate_flatten_pre_send_gate_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.flatten_productive_transport_v1 import (
    GatedProductiveFlattenTransportV1,
    LiveCanaryFlattenProductiveTransportError,
    RecordingProductiveFlattenTransportV1,
    open_productive_flatten_urllib_post_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.flatten_submit_transport_v1 import (
    DEDICATED_FLATTEN_TRANSPORT_LIVE_WIRE_ENABLED,
    LIVE_FLATTEN_PROVABILITY,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.http_client_v1 import (
    CanaryPostRedirectBlockedError,
    LiveCanaryHttpRequestV1,
    LiveCanaryHttpResponseV1,
    RecordingFakeCanaryTransportV1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.runner_v1 import (
    run_section_11_13_5_live_canary_minimum_exposure_v1,
)

OWNER_GO = "OWNER_GO_LIVE_CANARY_MINIMUM_EXPOSURE"
ORIGIN_SHA = "7085b6e76fef9036319f6d9a4bce0329e5493b02"
TARGET = DEFAULT_INSTRUMENT_ID
OTHER = "ETH-USDT-SWAP"
QUOTE_TS = "1787145055768"
EVAL_TS = "1787145056000"
WIRING_GO = (
    "SECTION_11_13_5_POST_Z2AU_PRODUCTIVE_LIVE_FLATTEN_WIRING_MAX_SAFE_SLICE_"
    "FAIL_CLOSED_NO_NETWORK_NO_GET_NO_POST_NO_EXECUTE"
)


@pytest.fixture(autouse=True)
def _block_network(monkeypatch: pytest.MonkeyPatch) -> None:
    def _blocked(*_a: Any, **_k: Any) -> Any:
        raise AssertionError("NETWORK_FORBIDDEN_IN_FLATTEN_WIRING_TESTS")

    monkeypatch.setattr("urllib.request.urlopen", _blocked)
    monkeypatch.setattr("socket.create_connection", _blocked)


def _positions(*rows: Mapping[str, Any]) -> dict[str, Any]:
    return {"code": "0", "data": list(rows)}


def _pending(*rows: Mapping[str, Any]) -> dict[str, Any]:
    return {"code": "0", "data": list(rows)}


def _price(*, side: str = "SELL", pos: str = "1", **overrides: Any) -> FlattenPriceInputV1:
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


def _valid_gate(**overrides: Any) -> FlattenPreSendGateInputV1:
    payload: dict[str, Any] = {
        "live_authorized": True,
        "live_enabled": True,
        "live_armed": True,
        "flatten_live_wire_enabled": True,
        "allow_productive_wire_send": True,
        "flatten_execute_token": FLATTEN_EXECUTE_CONFIRM_TOKEN_CANONICAL,
        "flatten_execute_purpose": FLATTEN_EXECUTE_PURPOSE_CANONICAL,
        "flatten_execute_owner_go": FLATTEN_EXECUTE_OWNER_GO_CANONICAL,
        "positions_payload": _positions({"instId": TARGET, "pos": "1"}),
        "pending_orders_payload": _pending(),
        "price_input": _price(),
        "owner_go": OWNER_GO,
        "origin_main_sha": ORIGIN_SHA,
        "flatten_execute_bound_origin_main_sha": ORIGIN_SHA,
        "instrument_id": TARGET,
        "one_shot_no_retry": True,
        "duplicate_post_protection": True,
    }
    payload.update(overrides)
    return FlattenPreSendGateInputV1(**payload)


def test_standing_defaults_remain_fail_closed() -> None:
    assert LIVE_AUTHORIZED is False
    assert LIVE_ENABLED is False
    assert LIVE_ARMED is False
    assert DEDICATED_FLATTEN_TRANSPORT_LIVE_WIRE_ENABLED is False
    assert LIVE_FLATTEN_PROVABILITY == "UNPROVEN"


def test_synthetic_valid_set_is_structurally_reachable() -> None:
    transport = RecordingProductiveFlattenTransportV1()
    result = submit_productive_flatten_v1(gate_input=_valid_gate(), transport=transport)
    assert result.allowed is True
    assert result.send_attempted is True
    assert result.send_completed is True
    assert result.network_used is False
    assert result.productive_venue_proof is False
    assert result.live_flatten_provability == "UNPROVEN"
    assert len(transport.calls) == 1
    body = result.receipt.request_body
    assert body is not None
    assert body.get("reduceOnly") is True
    assert str(body.get("ordType") or "").lower() == "limit"
    assert str(body.get("sz")) == "1"
    assert str(body.get("instId")) == TARGET
    assert result.receipt.qty == "1"


def test_default_gate_and_config_cannot_reach_productive_send() -> None:
    denied = evaluate_flatten_pre_send_gate_v1(
        FlattenPreSendGateInputV1(
            live_authorized=False,
            live_enabled=False,
            live_armed=False,
            flatten_live_wire_enabled=False,
            allow_productive_wire_send=False,
            flatten_execute_token="",
            flatten_execute_purpose="",
            flatten_execute_owner_go="",
            positions_payload=_positions({"instId": TARGET, "pos": "1"}),
            pending_orders_payload=_pending(),
            price_input=_price(),
            owner_go=OWNER_GO,
            origin_main_sha=ORIGIN_SHA,
        )
    )
    assert denied.allowed is False
    transport = RecordingProductiveFlattenTransportV1()
    result = submit_productive_flatten_v1(
        gate_input=_valid_gate(
            live_authorized=False,
            live_enabled=False,
            live_armed=False,
            flatten_live_wire_enabled=False,
            allow_productive_wire_send=False,
            flatten_execute_token="",
            flatten_execute_purpose="",
            flatten_execute_owner_go="",
            flatten_execute_bound_origin_main_sha=None,
        ),
        transport=transport,
    )
    assert result.send_attempted is False
    assert transport.calls == []
    cfg = example_incomplete_config_dict_v1()
    assert cfg.get("flatten_live_wire_enabled") is False
    assert cfg.get("flatten_execute_token") == ""
    runner = run_section_11_13_5_live_canary_minimum_exposure_v1(
        mode="flatten_execute",
        origin_main_sha=ORIGIN_SHA,
        config_payload=cfg,
    )
    assert runner.payload.get("send_attempted") is False
    assert runner.payload.get("send_completed") is False
    assert runner.ok is False


@pytest.mark.parametrize(
    "override,needle",
    [
        ({"live_authorized": False}, "LIVE_AUTHORIZED_CLAIM_FALSE"),
        ({"live_enabled": False}, "LIVE_ENABLED_CLAIM_FALSE"),
        ({"live_armed": False}, "LIVE_ARMED_CLAIM_FALSE"),
        ({"flatten_live_wire_enabled": False}, "FLATTEN_LIVE_WIRE_CLAIM_FALSE"),
        ({"allow_productive_wire_send": False}, "ALLOW_PRODUCTIVE_WIRE_SEND_FALSE"),
        ({"flatten_execute_token": None}, "FLATTEN_EXECUTE_TOKEN_MISSING"),
        ({"flatten_execute_token": "WRONG"}, "FLATTEN_EXECUTE_TOKEN_MISMATCH"),
        ({"flatten_execute_purpose": "WRONG_PURPOSE"}, "FLATTEN_EXECUTE_PURPOSE_INVALID"),
        ({"flatten_execute_owner_go": WIRING_GO}, "FLATTEN_EXECUTE_OWNER_GO_FORBIDDEN"),
        (
            {"flatten_execute_owner_go": "SECTION_11_13_5_FLATTEN_EXECUTE"},
            "FLATTEN_EXECUTE_OWNER_GO_MISMATCH",
        ),
        ({"flatten_execute_bound_origin_main_sha": None}, "FLATTEN_EXECUTE_BOUND_SHA_MISSING"),
        ({"flatten_execute_bound_origin_main_sha": "abcd"}, "FLATTEN_EXECUTE_BOUND_SHA_MALFORMED"),
        ({"flatten_execute_bound_origin_main_sha": "a" * 40}, "FLATTEN_EXECUTE_BOUND_SHA_STALE"),
        ({"pending_orders_payload": None}, "OPEN_ORDER_STATE_UNAVAILABLE"),
        (
            {"pending_orders_payload": _pending({"instId": TARGET, "ordId": "1"})},
            "OPEN_ORDER_CONFLICT",
        ),
        ({"one_shot_no_retry": False}, "ONE_SHOT_NO_RETRY_REQUIRED"),
        ({"duplicate_post_protection": False}, "DUPLICATE_POST_PROTECTION_REQUIRED"),
        (
            {
                "positions_payload": _positions(
                    {"instId": TARGET, "pos": "1"}, {"instId": OTHER, "pos": "1"}
                )
            },
            "B8_CAP",
        ),
        ({"price_input": _price(quote_timestamp_ms="1")}, "STALE"),
    ],
)
def test_each_independent_gate_fails_closed(override: dict[str, Any], needle: str) -> None:
    transport = RecordingProductiveFlattenTransportV1()
    result = submit_productive_flatten_v1(gate_input=_valid_gate(**override), transport=transport)
    assert result.send_attempted is False
    assert transport.calls == []
    joined = " ".join(result.reasons)
    assert needle in joined


def test_boolean_allow_flag_is_never_sufficient() -> None:
    transport = RecordingProductiveFlattenTransportV1()
    result = submit_productive_flatten_v1(
        gate_input=_valid_gate(
            flatten_execute_token="",
            flatten_execute_purpose="",
            flatten_execute_owner_go="",
            flatten_execute_bound_origin_main_sha=None,
            allow_productive_wire_send=True,
        ),
        transport=transport,
    )
    assert result.send_attempted is False
    assert transport.calls == []
    assert any("FLATTEN_EXECUTE" in item for item in result.reasons)


def test_fake_transport_cannot_masquerade_as_productive() -> None:
    fake = RecordingFakeCanaryTransportV1()
    result = submit_productive_flatten_v1(gate_input=_valid_gate(), transport=fake)
    assert result.fake_transport_rejected is True
    assert result.send_attempted is False
    assert result.send_completed is False


def test_productive_transport_cannot_send_without_full_receipt() -> None:
    transport = RecordingProductiveFlattenTransportV1()
    result = submit_productive_flatten_v1(
        gate_input=_valid_gate(allow_productive_wire_send=False),
        transport=transport,
    )
    assert result.send_attempted is False
    assert transport.calls == []


def test_gated_transport_never_opens_network_even_with_valid_gate() -> None:
    transport = GatedProductiveFlattenTransportV1()
    result = submit_productive_flatten_v1(gate_input=_valid_gate(), transport=transport)
    assert result.send_attempted is True
    assert result.send_completed is False
    assert result.network_used is False
    assert transport.last_wire_attempted is False
    assert "PRODUCTIVE_NETWORK_SESSION_NOT_AUTHORIZED" in " ".join(result.reasons)


def test_gated_transport_mocked_wire_returns_response_when_authorized(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: list[Any] = []

    def _fake_open(request: Any) -> LiveCanaryHttpResponseV1:
        captured.append(request)
        return LiveCanaryHttpResponseV1(
            status_code=200,
            body_bytes=b'{"code":"0","data":[{"sCode":"0"}]}',
            elapsed_seconds=0.01,
            endpoint=request.endpoint,
            method="POST",
            send_attempted=True,
            wire_body_sha256="ab",
            wire_body_byte_len=1,
        )

    monkeypatch.setattr(
        "src.ops.section_11_13_5_live_canary_minimum_exposure_v1."
        "flatten_productive_transport_v1.open_productive_flatten_urllib_post_v1",
        _fake_open,
    )
    transport = GatedProductiveFlattenTransportV1()
    transport.network_session_authorized = True
    result = submit_productive_flatten_v1(gate_input=_valid_gate(), transport=transport)
    assert result.send_completed is True
    assert result.network_used is True
    assert transport.last_wire_attempted is True
    assert result.response is not None
    assert result.response.status_code == 200
    assert result.productive_venue_proof is False
    assert result.live_flatten_provability == "UNPROVEN"
    assert len(captured) == 1
    assert captured[0].method == "POST"
    assert captured[0].endpoint == "/api/v5/trade/order"
    assert "OK-ACCESS-SIGN" not in {str(k).upper() for k in captured[0].headers}


def test_gated_transport_redirect_fails_closed(monkeypatch: pytest.MonkeyPatch) -> None:
    def _redirect(_request: Any) -> LiveCanaryHttpResponseV1:
        raise CanaryPostRedirectBlockedError(
            status_code=302,
            location="https://eea.okx.com/elsewhere",
            body=b"",
            headers={},
        )

    monkeypatch.setattr(
        "src.ops.section_11_13_5_live_canary_minimum_exposure_v1."
        "flatten_productive_transport_v1.open_productive_flatten_urllib_post_v1",
        _redirect,
    )
    transport = GatedProductiveFlattenTransportV1()
    transport.network_session_authorized = True
    result = submit_productive_flatten_v1(gate_input=_valid_gate(), transport=transport)
    assert result.send_completed is False
    assert result.network_used is True
    assert any("POST_REDIRECT_FAIL_CLOSED" in item for item in result.reasons)


def test_gated_transport_wire_exception_fails_closed(monkeypatch: pytest.MonkeyPatch) -> None:
    def _boom(_request: Any) -> LiveCanaryHttpResponseV1:
        raise TimeoutError("mocked-timeout")

    monkeypatch.setattr(
        "src.ops.section_11_13_5_live_canary_minimum_exposure_v1."
        "flatten_productive_transport_v1.open_productive_flatten_urllib_post_v1",
        _boom,
    )
    transport = GatedProductiveFlattenTransportV1()
    transport.network_session_authorized = True
    result = submit_productive_flatten_v1(gate_input=_valid_gate(), transport=transport)
    assert result.send_completed is False
    assert result.network_used is True
    assert any("PRODUCTIVE_FLATTEN_WIRE_TIMEOUT" in item for item in result.reasons)


def test_gated_transport_second_send_duplicate_forbidden(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def _fake_open(request: Any) -> LiveCanaryHttpResponseV1:
        return LiveCanaryHttpResponseV1(
            status_code=200,
            body_bytes=b'{"code":"0","data":[]}',
            elapsed_seconds=0.01,
            endpoint=request.endpoint,
            method="POST",
            send_attempted=True,
        )

    monkeypatch.setattr(
        "src.ops.section_11_13_5_live_canary_minimum_exposure_v1."
        "flatten_productive_transport_v1.open_productive_flatten_urllib_post_v1",
        _fake_open,
    )
    transport = GatedProductiveFlattenTransportV1()
    transport.network_session_authorized = True
    receipt = evaluate_flatten_pre_send_gate_v1(_valid_gate())
    transport.attach_pre_send_receipt(receipt)
    request = LiveCanaryHttpRequestV1(
        method="POST",
        url="https://eea.okx.com/api/v5/trade/order",
        host="eea.okx.com",
        endpoint="/api/v5/trade/order",
        headers={"User-Agent": "test"},
        timeout_seconds=1.0,
        body_text="{}",
    )
    first = transport.send(request)
    assert first.status_code == 200
    with pytest.raises(LiveCanaryFlattenProductiveTransportError, match="DUPLICATE_POST_FORBIDDEN"):
        transport.send(request)


def test_open_productive_flatten_urllib_is_not_canary_transport() -> None:
    src = inspect.getsource(GatedProductiveFlattenTransportV1.send)
    assert "UrllibLiveCanaryTransportV1" not in src
    assert "post_entry_order" not in src
    assert "wire_send_enabled" not in src
    assert inspect.getsource(open_productive_flatten_urllib_post_v1)


def test_duplicate_send_is_blocked() -> None:
    transport = RecordingProductiveFlattenTransportV1()
    boundary = FlattenGatedSubmitBoundaryV1()
    first = boundary.submit(gate_input=_valid_gate(), transport=transport)
    assert first.send_completed is True
    second = boundary.submit(gate_input=_valid_gate(), transport=transport)
    assert second.send_attempted is False
    assert second.duplicate_blocked is True
    assert len(transport.calls) == 1


def test_retry_remains_prohibited_on_transport() -> None:
    transport = RecordingProductiveFlattenTransportV1()
    first = submit_productive_flatten_v1(gate_input=_valid_gate(), transport=transport)
    assert first.send_completed is True
    with pytest.raises(Exception, match="DUPLICATE_POST_FORBIDDEN"):
        transport.send(transport.calls[0])


def test_reduce_only_limit_and_b8_survive_composition() -> None:
    receipt = evaluate_flatten_pre_send_gate_v1(_valid_gate())
    assert receipt.allowed is True
    assert receipt.reduce_only is True
    assert str(receipt.ord_type).lower() == "limit"
    body = receipt.request_body or {}
    assert body.get("reduceOnly") is True
    assert str(body.get("ordType")).lower() == "limit"
    denied = evaluate_flatten_pre_send_gate_v1(
        _valid_gate(
            positions_payload=_positions(
                {"instId": TARGET, "pos": "1"},
                {"instId": OTHER, "pos": "2"},
            )
        )
    )
    assert denied.allowed is False
    assert any("B8_CAP" in item for item in denied.reasons)


def test_runner_does_not_flatten_on_preflight_or_execute() -> None:
    preflight = run_section_11_13_5_live_canary_minimum_exposure_v1(
        mode="preflight",
        origin_main_sha=ORIGIN_SHA,
        transport=RecordingProductiveFlattenTransportV1(),
    )
    assert preflight.mode == "preflight"
    assert preflight.payload.get("send_completed") is not True
    spy = RecordingProductiveFlattenTransportV1()
    with pytest.raises(Exception):
        run_section_11_13_5_live_canary_minimum_exposure_v1(
            mode="execute",
            origin_main_sha=ORIGIN_SHA,
            owner_go=OWNER_GO,
            live_canary_authorized=True,
            live_enabled=True,
            live_armed=True,
            transport=spy,
            allow_productive_wire_send=True,
        )
    assert spy.calls == []


def test_runner_flatten_execute_reaches_recording_transport_only_when_fully_gated() -> None:
    transport = RecordingProductiveFlattenTransportV1()
    result = run_section_11_13_5_live_canary_minimum_exposure_v1(
        mode="flatten_execute",
        origin_main_sha=ORIGIN_SHA,
        owner_go=OWNER_GO,
        live_canary_authorized=True,
        live_enabled=True,
        live_armed=True,
        allow_productive_wire_send=True,
        flatten_execute_token=FLATTEN_EXECUTE_CONFIRM_TOKEN_CANONICAL,
        flatten_execute_purpose=FLATTEN_EXECUTE_PURPOSE_CANONICAL,
        flatten_execute_owner_go=FLATTEN_EXECUTE_OWNER_GO_CANONICAL,
        flatten_execute_bound_origin_main_sha=ORIGIN_SHA,
        flatten_live_wire_enabled=True,
        positions_payload=_positions({"instId": TARGET, "pos": "1"}),
        pending_orders_payload=_pending(),
        price_input=_price(),
        transport=transport,
    )
    assert result.payload.get("send_completed") is True
    assert result.payload.get("network_used") is False
    assert result.payload.get("productive_venue_proof") is False
    assert result.payload.get("LIVE_FLATTEN_PROVABILITY") == "UNPROVEN"
    assert len(transport.calls) == 1


def test_post_submit_offline_contract_preserved() -> None:
    pre = _positions({"instId": TARGET, "pos": "1"})
    post = _positions({"instId": TARGET, "pos": "0"})
    pending = _pending()
    proof = evaluate_canary_flatten_post_action_proof_contract_v1(
        pre_positions_payload=pre,
        post_positions_payload=post,
        post_pending_orders_payload=pending,
        instrument_id=TARGET,
    )
    assert proof.pre_pos_nonzero is True
    assert proof.post_pos_zero is True
    assert proof.pending_empty is True
    assert proof.no_flip is True
    assert proof.offline_contract_satisfied is True
    assert proof.live_flatten_provability == "UNPROVEN"
    assert proof.submit_reachable is False
    assert proof.live_wire_enabled is False
    state = evaluate_canary_flatten_post_submit_evidence_state_v1(
        submit_attempted=True,
        send_attempted=True,
        http_status=200,
        response_body={"code": "0", "data": [{"sCode": "0"}]},
        pre_positions_payload=pre,
        post_positions_payload=post,
        post_pending_orders_payload=pending,
        instrument_id=TARGET,
        requested_qty="1",
    )
    assert state.productive_venue_proof is False
    assert state.live_flatten_provability == "UNPROVEN"
    assert state.actual_post is True  # injected send_attempted evidence, not venue POST
