"""Offline SP-04 pre-submit second-open-instrument cap binding tests."""

from __future__ import annotations

import pytest

from src.ops.section_11_12_8_actual_productive_testnet_campaign_run_start_v1.constants_v1 import (
    CANONICAL_INSTRUMENT_SCOPE,
    CANONICAL_ORDER_SZ_FOR_VENUE_NATIVE_BODY_V1,
)
from src.ops.section_11_12_8_actual_productive_testnet_campaign_run_start_v1.productive_execution_port_v1 import (
    ActualStartPortError,
    construct_productive_testnet_execution_port_v1,
)

TARGET = CANONICAL_INSTRUMENT_SCOPE[0]
OTHER = "ETH-USD_UM_XPERP-310328"
POSITIONS_EP = "/api/v5/account/positions"
ORDER_EP = "/api/v5/trade/order"


class _RecordingPositionsTransport:
    def __init__(self, positions_result: dict | BaseException) -> None:
        self.positions_result = positions_result
        self.calls: list[tuple[str, str]] = []

    def request(self, *, method: str, endpoint: str, body: dict | None = None) -> dict:
        self.calls.append((method.upper(), endpoint))
        if method.upper() == "GET" and endpoint == POSITIONS_EP:
            if isinstance(self.positions_result, BaseException):
                raise self.positions_result
            return dict(self.positions_result)
        if method.upper() == "POST" and endpoint == ORDER_EP:
            return {
                "ok": True,
                "stubbed": True,
                "wire_sent": False,
                "network_send_boundary_reached": True,
                "http_status": 200,
                "response_body": {
                    "code": "0",
                    "data": [
                        {"sCode": "0", "sMsg": "stubbed", "clOrdId": (body or {}).get("clOrdId")}
                    ],
                },
            }
        raise AssertionError(f"unexpected {method} {endpoint}")


def _submit(port) -> dict:
    return port.submit_order_v1(
        client_order_id="c-cap",
        instrument=TARGET,
        order_type="LIMIT",
        side="buy",
        quantity=CANONICAL_ORDER_SZ_FOR_VENUE_NATIVE_BODY_V1,
        px="10000",
    )


def _ok_positions(rows: list[dict]) -> dict:
    return {
        "ok": True,
        "stubbed": True,
        "wire_sent": False,
        "response_body": {"code": "0", "data": rows},
    }


def test_t18_open_different_instrument_no_post() -> None:
    transport = _RecordingPositionsTransport(_ok_positions([{"instId": OTHER, "pos": "1"}]))
    port = construct_productive_testnet_execution_port_v1(
        authorized=True, transport=transport, stubbed=True
    )
    with pytest.raises(ActualStartPortError, match="DENY_OTHER_OPEN_INSTRUMENT_PRESENT"):
        _submit(port)
    assert transport.calls == [("GET", POSITIONS_EP)]


def test_t19_no_open_positions_mocked_post_proceeds() -> None:
    transport = _RecordingPositionsTransport(_ok_positions([]))
    port = construct_productive_testnet_execution_port_v1(
        authorized=True, transport=transport, stubbed=True
    )
    effect = _submit(port)
    assert effect["stubbed"] is True
    assert effect["live_order_effect"] == "NONE"
    assert transport.calls == [("GET", POSITIONS_EP), ("POST", ORDER_EP)]


def test_t20_positions_get_failure_no_post() -> None:
    transport = _RecordingPositionsTransport(RuntimeError("GET_FAILED"))
    port = construct_productive_testnet_execution_port_v1(
        authorized=True, transport=transport, stubbed=True
    )
    with pytest.raises(ActualStartPortError, match="DENY_POSITION_STATE_UNAVAILABLE"):
        _submit(port)
    assert transport.calls == [("GET", POSITIONS_EP)]


def test_t21_malformed_and_ambiguous_positions_no_post() -> None:
    malformed = _RecordingPositionsTransport(_ok_positions([{"instId": OTHER, "pos": "abc"}]))
    port = construct_productive_testnet_execution_port_v1(
        authorized=True, transport=malformed, stubbed=True
    )
    with pytest.raises(ActualStartPortError, match="DENY_INVALID_POSITION_PAYLOAD"):
        _submit(port)
    assert malformed.calls == [("GET", POSITIONS_EP)]

    ambiguous = _RecordingPositionsTransport(
        _ok_positions(
            [
                {"instId": OTHER, "pos": "1"},
                {"instId": OTHER, "pos": "1"},
            ]
        )
    )
    port = construct_productive_testnet_execution_port_v1(
        authorized=True, transport=ambiguous, stubbed=True
    )
    with pytest.raises(ActualStartPortError, match="DENY_AMBIGUOUS_POSITION_ROWS"):
        _submit(port)
    assert ambiguous.calls == [("GET", POSITIONS_EP)]


def test_t22_get_occurs_before_post() -> None:
    transport = _RecordingPositionsTransport(_ok_positions([]))
    port = construct_productive_testnet_execution_port_v1(
        authorized=True, transport=transport, stubbed=True
    )
    _submit(port)
    methods = [method for method, _endpoint in transport.calls]
    assert methods.index("GET") < methods.index("POST")
    assert transport.calls[0] == ("GET", POSITIONS_EP)
    assert transport.calls[1] == ("POST", ORDER_EP)
