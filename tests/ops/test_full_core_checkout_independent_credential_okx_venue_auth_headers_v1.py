"""K1 CURRENT OKX venue-auth header contract.

Synthetic credentials and frozen vectors only. No network. No Keychain.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace

import pytest

from src.ops.full_core_live_path_composition_root_v1.checkout_independent_credential_okx_venue_auth_headers_v1 import (
    EXTERNAL_EFFECT_AUTHORIZED,
    JOIN_SEAM_ID,
    MATERIAL_LOADED,
    MAY_PERFORM_GET,
    MAY_POST,
    REAL_KEYCHAIN_ACCESS_AUTHORIZED,
    SIGNING_IMPLIES_NETWORK_AUTHORIZATION,
    SIGNING_IMPLIES_SEND_AUTHORITY,
    FullCoreK1BoundVenueAuthHandleV1,
    FullCoreK1OkxVenueAuthError,
    bind_already_held_k1_venue_auth_session_v1,
    build_k1_okx_venue_auth_headers_v1,
    format_k1_okx_access_timestamp_iso_ms_v1,
    prove_k1_signing_does_not_authorize_network_v1,
    release_k1_venue_auth_session_v1,
    serialize_k1_signed_post_body_v1,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
K1_SRC = (
    REPO_ROOT
    / "src/ops/full_core_live_path_composition_root_v1"
    / "checkout_independent_credential_okx_venue_auth_headers_v1.py"
)
GET_SRC = (
    REPO_ROOT
    / "src/ops/full_core_live_path_composition_root_v1"
    / "productive_read_only_get_transport_v1.py"
)
POST_SRC = (
    REPO_ROOT
    / "src/ops/full_core_live_path_composition_root_v1"
    / "full_core_productive_http_post_transport_v1.py"
)

_SYNTH_KEY = "parity-api-key-001"
_SYNTH_SECRET = "parity-api-secret-001"
_SYNTH_PASSPHRASE = "parity-passphrase-001"
_FIXED_TS = "2026-01-02T03:04:05.006Z"
_GET_URL = "https://eea.okx.com/api/v5/account/balance?ccy=USDC"
_POST_URL = "https://eea.okx.com/api/v5/trade/order"
_GET_SIGN = "XlCZYUqPCM8bnc9twJHuxUWQ34hwzjq9mb3To4X0LTw="
_POST_SIGN = "OiWRpCnkp4s5kGH80lxVrndFFjIBrGwYdbGwgI+swZw="
_POST_PAYLOAD = {"instId": "SUI-USDT-SWAP", "tdMode": "cross", "side": "sell", "sz": "1"}
_POST_BODY = '{"instId":"SUI-USDT-SWAP","tdMode":"cross","side":"sell","sz":"1"}'


def _freeze_timestamps(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "src.ops.full_core_live_path_composition_root_v1"
        ".checkout_independent_credential_okx_venue_auth_headers_v1"
        ".format_k1_okx_access_timestamp_iso_ms_v1",
        lambda **_kwargs: _FIXED_TS,
    )


def test_standing_pins_remain_fail_closed() -> None:
    proof = prove_k1_signing_does_not_authorize_network_v1()
    assert REAL_KEYCHAIN_ACCESS_AUTHORIZED is False
    assert MATERIAL_LOADED is False
    assert MAY_PERFORM_GET is False
    assert MAY_POST is False
    assert SIGNING_IMPLIES_SEND_AUTHORITY is False
    assert SIGNING_IMPLIES_NETWORK_AUTHORIZATION is False
    assert EXTERNAL_EFFECT_AUTHORIZED is False
    assert proof["EXTERNAL_EFFECT_AUTHORIZED"] == "false"
    assert JOIN_SEAM_ID == "CURRENT_PRODUCTIVE_K1_OKX_VENUE_AUTH_HEADERS_SEAM_V1"


def test_handle_rejects_material_loaded_true() -> None:
    with pytest.raises(FullCoreK1OkxVenueAuthError, match="CREDENTIAL_MATERIAL_LOADED_FORBIDDEN"):
        FullCoreK1BoundVenueAuthHandleV1(
            handle_id="k1-vah-forbidden",
            bound=True,
            can_sign=True,
            material_loaded=True,
        )


def test_handle_to_dict_has_no_plaintext() -> None:
    handle = bind_already_held_k1_venue_auth_session_v1(
        api_key=_SYNTH_KEY,
        api_secret=_SYNTH_SECRET,
        passphrase=_SYNTH_PASSPHRASE,
    )
    try:
        payload = handle.to_dict()
        blob = json.dumps(payload)
        assert _SYNTH_SECRET not in blob
        assert _SYNTH_PASSPHRASE not in blob
        assert payload["material_loaded"] == "false"
        assert payload["plaintext_present"] == "false"
    finally:
        release_k1_venue_auth_session_v1(handle)


def test_get_body_forbidden() -> None:
    handle = bind_already_held_k1_venue_auth_session_v1(
        api_key=_SYNTH_KEY,
        api_secret=_SYNTH_SECRET,
        passphrase=_SYNTH_PASSPHRASE,
    )
    try:
        with pytest.raises(FullCoreK1OkxVenueAuthError, match="SIGNER_BODY_FORBIDDEN_FOR_GET"):
            build_k1_okx_venue_auth_headers_v1(
                handle=handle,
                url=_GET_URL,
                method="GET",
                body="{}",
            )
    finally:
        release_k1_venue_auth_session_v1(handle)


def test_non_k1_handle_type_forbidden() -> None:
    with pytest.raises(FullCoreK1OkxVenueAuthError, match="K1_VENUE_AUTH_HANDLE_TYPE_FORBIDDEN"):
        build_k1_okx_venue_auth_headers_v1(
            handle=SimpleNamespace(bound=True, can_sign=True, material_loaded=False),  # type: ignore[arg-type]
            url=_GET_URL,
            method="GET",
        )


def test_timestamp_format_matches_okx_iso_ms() -> None:
    frozen = datetime(2026, 1, 2, 3, 4, 5, 6000, tzinfo=timezone.utc)
    assert format_k1_okx_access_timestamp_iso_ms_v1(now=frozen) == _FIXED_TS


def test_signing_contract_parity_get_and_post(monkeypatch: pytest.MonkeyPatch) -> None:
    _freeze_timestamps(monkeypatch)
    handle = bind_already_held_k1_venue_auth_session_v1(
        api_key=_SYNTH_KEY,
        api_secret=_SYNTH_SECRET,
        passphrase=_SYNTH_PASSPHRASE,
    )
    try:
        k1_get = build_k1_okx_venue_auth_headers_v1(handle=handle, url=_GET_URL, method="GET")
        assert k1_get["OK-ACCESS-KEY"] == _SYNTH_KEY
        assert k1_get["OK-ACCESS-TIMESTAMP"] == _FIXED_TS
        assert k1_get["OK-ACCESS-SIGN"] == _GET_SIGN
        assert k1_get["OK-ACCESS-PASSPHRASE"] == _SYNTH_PASSPHRASE
        assert k1_get["Content-Type"] == "application/json"

        k1_body = serialize_k1_signed_post_body_v1(_POST_PAYLOAD)
        assert k1_body == _POST_BODY

        k1_post = build_k1_okx_venue_auth_headers_v1(
            handle=handle, url=_POST_URL, method="POST", body=k1_body
        )
        assert k1_post["OK-ACCESS-SIGN"] == _POST_SIGN
        assert k1_post["OK-ACCESS-TIMESTAMP"] == _FIXED_TS
        assert k1_post["Content-Type"] == "application/json"
    finally:
        release_k1_venue_auth_session_v1(handle)


def test_current_get_and_post_import_k1_signer_not_k2() -> None:
    get_src = GET_SRC.read_text(encoding="utf-8")
    post_src = POST_SRC.read_text(encoding="utf-8")
    assert "build_k1_okx_venue_auth_headers_v1" in get_src
    assert "build_k1_okx_venue_auth_headers_v1" in post_src
    assert "serialize_canonical_okx_post_body_v1" in post_src
    assert "okx_live_canary_signer_v1" not in get_src
    assert "okx_live_canary_signer_v1" not in post_src
    assert "build_okx_live_canary_auth_headers_v1" not in get_src
    assert "build_okx_live_canary_auth_headers_v1" not in post_src
    assert "serialize_canonical_okx_post_body_v1" in post_src
    k1_src = K1_SRC.read_text(encoding="utf-8")
    assert "live_credential_ephemeral_v1" not in k1_src
    assert "secretref_v1" not in k1_src
    assert "vault_resolver_v1" not in k1_src
    assert "SecItemCopyMatching" not in k1_src
    assert "urllib.request" not in k1_src
