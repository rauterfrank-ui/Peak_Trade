"""Tests for OkxEeaPublicWsNetworkConnectorV1 (no live OKX network)."""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest

from src.ops.peak_trade_public_market_data_runtime_v1.constants_v1 import EEA_PUBLIC_WS_BASE
from src.ops.peak_trade_public_market_data_runtime_v1.ws_network_connector_v1 import (
    OkxEeaPublicWsNetworkConnectorV1,
    create_ratified_eea_public_ws_network_connector_v1,
)
from src.ops.peak_trade_public_market_data_runtime_v1.ws_transport_v1 import PublicWsTransportV1


def test_factory_binds_ratified_eea_url() -> None:
    conn = create_ratified_eea_public_ws_network_connector_v1()
    assert isinstance(conn, OkxEeaPublicWsNetworkConnectorV1)


def test_connect_subscribe_with_fake_websocket_app() -> None:
    connector = OkxEeaPublicWsNetworkConnectorV1(connect_timeout_seconds=2.0)
    hooks: dict = {}

    def ws_app_factory(url, on_open=None, on_message=None, on_error=None, on_close=None, **kwargs):
        hooks["on_open"] = on_open
        instance = MagicMock()

        def run_forever(**kw):
            if on_open is not None:
                on_open(instance)

        instance.run_forever.side_effect = run_forever
        return instance

    with patch("websocket.WebSocketApp", side_effect=ws_app_factory):
        connector.connect(EEA_PUBLIC_WS_BASE)
        ws_instance = connector._ws_app
        connector.subscribe([{"channel": "tickers", "instId": "ETH-USDT-SWAP"}])
        assert connector.state.connected is True
        assert connector.state.subscribed is True
        ws_instance.send.assert_called()
        sent = json.loads(ws_instance.send.call_args[0][0])
        assert sent["op"] == "subscribe"


def test_message_source_drains_inbox() -> None:
    connector = OkxEeaPublicWsNetworkConnectorV1()
    connector._enqueue({"tradeId": "1", "ts": "1000"})
    msgs = list(connector.message_source())
    assert len(msgs) == 1


def test_transport_integration_with_network_connector() -> None:
    connector = OkxEeaPublicWsNetworkConnectorV1(connect_timeout_seconds=2.0)

    def ws_app_factory(url, on_open=None, on_message=None, on_error=None, on_close=None, **kwargs):
        instance = MagicMock()

        def run_forever(**kw):
            if on_open is not None:
                on_open(instance)

        instance.run_forever.side_effect = run_forever

        def send(raw: str) -> None:
            if on_message is not None:
                on_message(instance, raw)

        instance.send.side_effect = send
        return instance

    with patch("websocket.WebSocketApp", side_effect=ws_app_factory):
        transport = PublicWsTransportV1.from_ratified_binding(
            connector=connector,
            message_source=connector.message_source,
            venue_native_id="ETH-USDT-SWAP",
        )
        transport.connect_and_subscribe()
        connector._ws_app.send(json.dumps({"tradeId": "9", "ts": "2000"}))
        out = transport.poll_messages()
        assert len(out) >= 1


def test_forbidden_ws_host_rejected() -> None:
    connector = OkxEeaPublicWsNetworkConnectorV1()
    with pytest.raises(Exception):
        connector.connect("wss://wseeapap.okx.com:8443/ws/v5/public")
