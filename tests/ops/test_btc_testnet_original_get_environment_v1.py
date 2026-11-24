"""Original K1 and HTTP GET code with synthetic credentials and a mocked endpoint."""

from base64 import b64encode
from dataclasses import replace
from hashlib import sha256
import hmac
import json
from types import SimpleNamespace

import pytest

from src.ops.full_core_live_path_composition_root_v1 import (
    checkout_independent_credential_okx_venue_auth_headers_v1 as auth,
    productive_read_only_get_transport_v1 as wire,
)
from src.ops.execution_reconciliation_get_provenance_v1 import (
    AuthenticatedReconciliationGetV1,
    ExecutionReconciliationSourceError,
)
from tests.ops.test_closing_execution_cost_provision_v1 import no_network as no_network

URL = "https://eea.okx.com/api/v5/account/config"
STAMP = "2026-11-24T12:00:00.000Z"


@pytest.fixture
def handles(monkeypatch):
    monkeypatch.setattr(auth, "format_k1_okx_access_timestamp_iso_ms_v1", lambda: STAMP)
    held = [
        auth.bind_already_held_k1_venue_auth_session_v1(
            api_key="synthetic-key",
            api_secret="synthetic-signing-value",
            passphrase="synthetic-phrase",
            execution_environment=mode,
        )
        for mode in ("LIVE", "TESTNET")
    ]
    try:
        yield held
    finally:
        for handle in held:
            auth.release_k1_venue_auth_session_v1(handle)


def test_demo_signing_has_mandatory_marker_and_same_original_hmac(handles):
    live, demo = handles
    headers = auth.build_k1_okx_demo_auth_headers_v1(handle=demo, url=URL, method="GET")
    expected = b64encode(
        hmac.new(
            b"synthetic-signing-value", (STAMP + "GET/api/v5/account/config").encode(), sha256
        ).digest()
    ).decode()
    assert headers["OK-ACCESS-SIGN"] == expected
    assert headers["x-simulated-trading"] == "1"
    assert demo.to_dict()["execution_environment"] == "TESTNET"
    assert "synthetic-" not in json.dumps(demo.to_dict())
    assert "x-simulated-trading" not in auth.build_k1_okx_venue_auth_headers_v1(
        handle=live, url=URL, method="GET"
    )
    with pytest.raises(auth.FullCoreK1OkxVenueAuthError, match="ENVIRONMENT_MISMATCH"):
        auth.build_k1_okx_venue_auth_headers_v1(handle=demo, url=URL, method="GET")
    with pytest.raises(auth.FullCoreK1OkxVenueAuthError, match="ENVIRONMENT_MISMATCH"):
        auth.build_k1_okx_demo_auth_headers_v1(handle=live, url=URL, method="GET")
    with pytest.raises(auth.FullCoreK1OkxVenueAuthError, match="ENVIRONMENT_MISMATCH"):
        auth.require_same_k1_venue_credential_v1(live, demo)


def test_relabeling_an_opaque_session_does_not_change_its_bound_environment(handles):
    _, demo = handles
    with pytest.raises(auth.FullCoreK1OkxVenueAuthError, match="SESSION_ENVIRONMENT_MISMATCH"):
        auth.build_k1_okx_venue_auth_headers_v1(
            handle=replace(demo, execution_environment="LIVE"), url=URL, method="GET"
        )


@pytest.mark.parametrize("marker", ["0", "1"])
def test_caller_cannot_override_the_demo_marker(handles, marker):
    with pytest.raises(auth.FullCoreK1OkxVenueAuthError, match="HEADER_FORBIDDEN"):
        auth.build_k1_okx_demo_auth_headers_v1(
            handle=handles[1],
            url=URL,
            method="GET",
            extra_headers={"x-simulated-trading": marker},
        )


@pytest.mark.parametrize(
    "url",
    [
        URL.replace("eea.okx.com", "www.okx.com"),
        URL.replace("eea.okx.com", "eea.okx.com:444"),
        URL.replace("eea.okx.com", "user@eea.okx.com"),
        URL + "#fragment",
    ],
)
def test_demo_signing_refuses_a_global_host_or_ambiguous_authority(handles, url):
    with pytest.raises(auth.FullCoreK1OkxVenueAuthError, match="DEMO_EEA_HOST_REQUIRED"):
        auth.build_k1_okx_demo_auth_headers_v1(handle=handles[1], url=url, method="GET")


def test_original_get_retains_actual_response_bytes_and_testnet_header(handles, monkeypatch):
    calls = []
    body = b'{"code":"0","data":[{"uid":"142","posMode":"net_mode"}]}'

    class Response:
        status = 200
        url = URL

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return None

        def read(self):
            return body

    class Endpoint:
        def open(self, request, timeout):
            assert request.method == "GET" and request.data is None
            assert request.full_url == URL
            assert request.get_header("X-simulated-trading") == "1"
            assert request.get_header("Ok-access-sign")
            calls.append(request.method)
            return Response()

    monkeypatch.setattr(wire, "build_opener", lambda *args: Endpoint())
    transport = wire.FullCoreProductiveReadOnlyGetTransportV1(
        handle=handles[1], execution_environment="TESTNET"
    )
    result, raw = transport.get_authenticated_response_v1(
        endpoint="/api/v5/account/config", pretrade_decision_id="explicit-test-context"
    )
    assert raw == body
    assert result.body_sha256 == sha256(body).hexdigest()
    assert result.data_safety_source_kind == "real"
    assert transport.execution_environment == "TESTNET"
    assert calls == ["GET"] and transport.methods_used == ["GET"]
    reader = AuthenticatedReconciliationGetV1(
        transport,
        account="142",
        clock=lambda: 0,
    )
    with pytest.raises(ExecutionReconciliationSourceError, match="GET_SEQUENCE_UNPROVEN"):
        reader.record_v1(
            SimpleNamespace(account="142", execution_environment="TESTNET"),
            "hold",
            SimpleNamespace(
                account_identity="142",
                execution_environment="LIVE",
                portfolio_reservation_id="hold",
            ),
            None,
            None,
            None,
        )


def test_transport_refuses_cross_environment_credentials_before_http(handles):
    for handle, mode in ((handles[0], "TESTNET"), (handles[1], "LIVE")):
        with pytest.raises(wire.FullCoreProductiveReadOnlyGetError, match="ENVIRONMENT_MISMATCH"):
            wire.FullCoreProductiveReadOnlyGetTransportV1(handle=handle, execution_environment=mode)
