from __future__ import annotations

import pytest

from src.execution.networked.entry_contract_v1 import ExecutionEntryGuardError
from src.execution.networked.transport_gate_v1 import TransportGateError, TransportGateV1
from src.execution.networked.transport_stub_v1 import (
    HttpRequestV1,
    NetworkedTransportStubV1,
    build_networked_transport_stub_v1,
)


def _ctx_ok() -> dict:
    return {
        "mode": "shadow",
        "dry_run": True,
        "intent": "place_order",
        "market": "BTC-USD",
        "qty": 0.01,
        "env": {},
    }


def test_transport_stub_builds() -> None:
    t = build_networked_transport_stub_v1()
    assert isinstance(t, NetworkedTransportStubV1)


def test_transport_stub_denies_without_network_io_default_gate_allows_only_no() -> None:
    t = build_networked_transport_stub_v1()
    req = HttpRequestV1(method="GET", url="https://example.invalid", headers={})
    resp = t.request(request=req, ctx=_ctx_ok())
    assert resp.ok is False
    assert resp.status_code == 599
    assert "STUB_DENY" in (resp.error or "")


def test_transport_stub_respects_entry_contract_guard() -> None:
    t = build_networked_transport_stub_v1()
    req = HttpRequestV1(method="GET", url="https://example.invalid", headers={})
    bad = _ctx_ok()
    bad["mode"] = "live"
    with pytest.raises(ExecutionEntryGuardError):
        _ = t.request(request=req, ctx=bad)


def test_transport_stub_blocks_if_gate_configured_to_allow_transport_yes() -> None:
    gate = TransportGateV1(transport_allow="YES")
    t = NetworkedTransportStubV1(gate=gate)
    req = HttpRequestV1(method="GET", url="https://example.invalid", headers={})
    with pytest.raises(TransportGateError):
        _ = t.request(request=req, ctx=_ctx_ok())
