"""Offline negative tests for the isolated read-only observation GET path."""

from __future__ import annotations

import ast
import base64
import hashlib
import hmac
from datetime import datetime, timezone
from pathlib import Path

import pytest

from src.ops.current_read_only_observation_get_path_v1.constants_v1 import (
    ALLOWED_ENDPOINTS,
    ALLOWED_METHODS,
    AUTHORIZED_HOST,
    CREDENTIAL_CLASS,
    FORBIDDEN_TRADE_CREDENTIAL_CLASS,
    FORBIDDEN_TRADE_SECRETREF_URI,
    NETWORK_SEND_AUTHORIZED,
    POST_ALLOWED,
    SECRETREF_URI,
)
from src.ops.current_read_only_observation_get_path_v1.credential_v1 import (
    bind_read_only_observation_credential_v1,
    refuse_vault_file_v1,
)
from src.ops.current_read_only_observation_get_path_v1.errors_v1 import (
    ReadOnlyObservationGetError,
)
from src.ops.current_read_only_observation_get_path_v1.handle_v1 import (
    release_read_only_observation_session_v1,
)
from src.ops.current_read_only_observation_get_path_v1.signer_v1 import (
    build_read_only_observation_get_headers_v1,
)
from src.ops.current_read_only_observation_get_path_v1.transport_v1 import (
    ReadOnlyObservationSenderResultV1,
    complete_read_only_observation_get_v1,
    prepare_read_only_observation_get_v1,
)

_PACKAGE = Path("src/ops/current_read_only_observation_get_path_v1")
_FORBIDDEN_IMPORT_MARKERS = (
    "checkout_independent_credential_okx_venue_auth_headers_v1",
    "checkout_independent_credential_os_native_store_acquisition_v1",
    "current_productive_k1_opaque_signing_handle_from_macos_os_native_store_v1",
    "current_productive_k1_runtime_binding_to_one_shot_actual_venue_post_pre_live_boundary_v1",
    "full_core_productive_http_post_transport_v1",
    "build_k1_okx_venue_auth_headers_v1",
    "section_11_13_5_live_canary_minimum_exposure_v1",
    "single_selected_future_policy_v1",
    "single_selected_future_runtime_binding_v1",
    "src.trading",
    "urllib.request",
    "urlopen",
)
_FORBIDDEN_METHODS = ("POST", "PUT", "PATCH", "DELETE", "HEAD", "")
_FORBIDDEN_ENDPOINTS = (
    "/api/v5/trade/order",
    "/api/v5/trade/cancel-order",
    "/api/v5/trade/amend-order",
    "/api/v5/trade/amend-algos",
    "/api/v5/asset/transfer",
    "/api/v5/asset/withdrawal",
    "/api/v5/account/set-position-mode",
)
_NOW = datetime(2026, 10, 23, 21, 16, 0, tzinfo=timezone.utc)


def _bind():
    return bind_read_only_observation_credential_v1(
        credential_class=CREDENTIAL_CLASS,
        secret_reference=SECRETREF_URI,
        api_key="ro-key",
        api_secret="ro-secret",
        passphrase="ro-phrase",
    )


def test_pins_and_method_set() -> None:
    assert ALLOWED_METHODS == frozenset({"GET"})
    assert POST_ALLOWED is False
    assert NETWORK_SEND_AUTHORIZED is False
    assert AUTHORIZED_HOST == "eea.okx.com"
    assert "/api/v5/trade/orders-pending" in ALLOWED_ENDPOINTS
    assert len(ALLOWED_ENDPOINTS) == 6


def test_trade_credential_and_vault_are_rejected() -> None:
    with pytest.raises(ReadOnlyObservationGetError, match="TRADE_CREDENTIAL_FORBIDDEN"):
        bind_read_only_observation_credential_v1(
            credential_class=FORBIDDEN_TRADE_CREDENTIAL_CLASS,
            secret_reference=SECRETREF_URI,
            api_key="k",
            api_secret="s",
            passphrase="p",
        )
    with pytest.raises(ReadOnlyObservationGetError, match="TRADE_CREDENTIAL_FORBIDDEN"):
        bind_read_only_observation_credential_v1(
            credential_class=CREDENTIAL_CLASS,
            secret_reference=FORBIDDEN_TRADE_SECRETREF_URI,
            api_key="k",
            api_secret="s",
            passphrase="p",
        )
    with pytest.raises(ReadOnlyObservationGetError, match="VAULT_READ_FORBIDDEN"):
        refuse_vault_file_v1(Path("unused-vault.json"))


@pytest.mark.parametrize("method", _FORBIDDEN_METHODS)
def test_signer_and_transport_reject_non_get(method: str) -> None:
    handle = _bind()
    try:
        with pytest.raises(ReadOnlyObservationGetError, match="METHOD_FORBIDDEN|SIGNER_METHOD"):
            prepare_read_only_observation_get_v1(
                handle=handle,
                endpoint="/api/v5/account/config",
                method=method,
            )
        with pytest.raises(ReadOnlyObservationGetError, match="SIGNER_METHOD_FORBIDDEN"):
            build_read_only_observation_get_headers_v1(
                handle=handle,
                url=f"https://{AUTHORIZED_HOST}/api/v5/account/config",
                method=method or "POST",
            )
    finally:
        release_read_only_observation_session_v1(handle)


def test_get_signature_uses_empty_body() -> None:
    handle = _bind()
    try:
        headers = build_read_only_observation_get_headers_v1(
            handle=handle,
            url=f"https://{AUTHORIZED_HOST}/api/v5/trade/orders-pending?instType=SWAP",
            method="GET",
            now=_NOW,
        )
        timestamp = "2026-10-23T21:16:00.000Z"
        prehash = f"{timestamp}GET/api/v5/trade/orders-pending?instType=SWAP"
        expected = base64.b64encode(
            hmac.new(b"ro-secret", prehash.encode("utf-8"), hashlib.sha256).digest()
        ).decode("ascii")
        assert headers["OK-ACCESS-SIGN"] == expected
        assert headers["OK-ACCESS-TIMESTAMP"] == timestamp
        assert "Content-Type" not in headers
    finally:
        release_read_only_observation_session_v1(handle)


@pytest.mark.parametrize("endpoint", _FORBIDDEN_ENDPOINTS)
def test_forbidden_endpoints(endpoint: str) -> None:
    handle = _bind()
    try:
        with pytest.raises(ReadOnlyObservationGetError, match="ENDPOINT_FORBIDDEN"):
            prepare_read_only_observation_get_v1(handle=handle, endpoint=endpoint)
    finally:
        release_read_only_observation_session_v1(handle)


@pytest.mark.parametrize(
    "endpoint",
    [
        "http://eea.okx.com/api/v5/account/config",
        "https://www.okx.com/api/v5/account/config",
        "https://okx.com/api/v5/account/balance",
        "https://evil.example/api/v5/account/positions",
    ],
)
def test_foreign_hosts_and_schemes(endpoint: str) -> None:
    handle = _bind()
    try:
        with pytest.raises(ReadOnlyObservationGetError, match="HOST_NOT_EEA_OKX|SCHEME_FORBIDDEN"):
            prepare_read_only_observation_get_v1(handle=handle, endpoint=endpoint)
    finally:
        release_read_only_observation_session_v1(handle)


def test_redirect_off_host_and_missing_sender() -> None:
    handle = _bind()
    try:
        prepared = prepare_read_only_observation_get_v1(
            handle=handle,
            endpoint="/api/v5/account/positions?instType=SWAP",
        )
        assert prepared.method == "GET"
        assert prepared.url.startswith(f"https://{AUTHORIZED_HOST}/")
        with pytest.raises(ReadOnlyObservationGetError, match="NETWORK_NOT_AUTHORIZED"):
            complete_read_only_observation_get_v1(prepared=prepared, sender_result=None)
        with pytest.raises(ReadOnlyObservationGetError, match="REDIRECT_OFF_HOST_FORBIDDEN"):
            complete_read_only_observation_get_v1(
                prepared=prepared,
                sender_result=ReadOnlyObservationSenderResultV1(
                    final_url="https://evil.example/api/v5/account/positions",
                    http_status=302,
                ),
            )
        with pytest.raises(ReadOnlyObservationGetError, match="REDIRECT_ENDPOINT_FORBIDDEN"):
            complete_read_only_observation_get_v1(
                prepared=prepared,
                sender_result=ReadOnlyObservationSenderResultV1(
                    final_url=f"https://{AUTHORIZED_HOST}/api/v5/trade/order",
                    http_status=302,
                ),
            )
    finally:
        release_read_only_observation_session_v1(handle)


def test_signer_rejects_body_and_repr_hides_material() -> None:
    handle = _bind()
    try:
        assert "ro-secret" not in repr(handle)
        with pytest.raises(ReadOnlyObservationGetError, match="SIGNER_BODY_FORBIDDEN_FOR_GET"):
            build_read_only_observation_get_headers_v1(
                handle=handle,
                url=f"https://{AUTHORIZED_HOST}/api/v5/account/balance",
                method="GET",
                body='{"side":"buy"}',
            )
    finally:
        release_read_only_observation_session_v1(handle)


def test_package_import_isolation_and_no_productive_importer() -> None:
    for path in _PACKAGE.glob("*.py"):
        source = path.read_text(encoding="utf-8")
        tree = ast.parse(source)
        imported: list[str] = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported.extend(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported.append(node.module)
        blob = "\n".join(imported) + "\n" + source
        for marker in _FORBIDDEN_IMPORT_MARKERS:
            assert marker not in blob, f"{path.name} references {marker}"
    root = Path("src")
    importers: list[str] = []
    for path in root.rglob("*.py"):
        if _PACKAGE.as_posix() in path.as_posix():
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        if "current_read_only_observation_get_path_v1" in text:
            importers.append(path.as_posix())
    assert importers == []
