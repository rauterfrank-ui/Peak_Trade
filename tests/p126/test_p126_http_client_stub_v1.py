import pytest

from src.execution.networked.http_client_stub_v1 import (
    HttpRequestV1,
    NetworkTransportDisabledError,
    http_request_stub_v1,
)


def _req() -> HttpRequestV1:
    return HttpRequestV1(method="GET", url="https://example.invalid", headers={"x": "y"})


def test_denies_by_default_even_with_transport_allow_no():
    with pytest.raises(NetworkTransportDisabledError):
        http_request_stub_v1(
            mode="shadow",
            dry_run=True,
            adapter="mock",
            intent="place_order",
            market="BTC-USD",
            qty=0.01,
            transport_allow="NO",
            request=_req(),
        )


def test_rejects_live_mode_via_entry_contract():
    with pytest.raises(Exception) as e:
        http_request_stub_v1(
            mode="live",
            dry_run=True,
            adapter="mock",
            intent="place_order",
            market="BTC-USD",
            qty=0.01,
            transport_allow="NO",
            request=_req(),
        )
    assert "mode" in str(e.value).lower() or "guard" in str(e.value).lower()


def test_transport_allow_yes_denies_via_transport_gate():
    with pytest.raises(Exception) as e:
        http_request_stub_v1(
            mode="shadow",
            dry_run=True,
            adapter="mock",
            intent="place_order",
            market="BTC-USD",
            qty=0.01,
            transport_allow="YES",
            request=_req(),
        )
    assert "transport" in str(e.value).lower() or "deny" in str(e.value).lower()


def test_test_allow_network_stub_returns_stub_response():
    resp = http_request_stub_v1(
        mode="shadow",
        dry_run=True,
        adapter="mock",
        intent="place_order",
        market="BTC-USD",
        qty=0.01,
        transport_allow="NO",
        request=_req(),
        test_allow_network_stub=True,
    )
    assert resp.ok is True
    assert resp.status_code == 200
    assert resp.json == {"stub": True}
