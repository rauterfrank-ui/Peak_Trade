"""CURRENT canonical OKX POST-body serializer.

Synthetic payloads only. No network. No Keychain. No credential load.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

from src.ops.full_core_live_path_composition_root_v1.checkout_independent_canonical_okx_post_body_serialize_v1 import (
    serialize_canonical_okx_post_body_v1,
)
from src.ops.full_core_live_path_composition_root_v1.checkout_independent_credential_okx_venue_auth_headers_v1 import (
    serialize_k1_signed_post_body_v1,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
POST_SRC = (
    REPO_ROOT
    / "src/ops/full_core_live_path_composition_root_v1"
    / "full_core_productive_http_post_transport_v1.py"
)
GET_SRC = (
    REPO_ROOT
    / "src/ops/full_core_live_path_composition_root_v1"
    / "productive_read_only_get_transport_v1.py"
)
K1_SRC = (
    REPO_ROOT
    / "src/ops/full_core_live_path_composition_root_v1"
    / "checkout_independent_credential_okx_venue_auth_headers_v1.py"
)
SERIALIZER_SRC = (
    REPO_ROOT
    / "src/ops/full_core_live_path_composition_root_v1"
    / "checkout_independent_canonical_okx_post_body_serialize_v1.py"
)

_POST_PAYLOAD = {"instId": "SUI-USDT-SWAP", "tdMode": "cross", "side": "sell", "sz": "1"}
_POST_BODY = '{"instId":"SUI-USDT-SWAP","tdMode":"cross","side":"sell","sz":"1"}'


def _old_serializer_output(payload: Mapping[str, Any]) -> str:
    """Historical serialize_signed_post_body_v1 formula. Module remains deleted."""
    return json.dumps(dict(payload), separators=(",", ":"), ensure_ascii=True)


def test_old_serializer_output_equals_current_serializer_output() -> None:
    vectors: tuple[dict[str, Any], ...] = (
        dict(_POST_PAYLOAD),
        {},
        {"a": 1, "b": "x", "c": True},
        {"nested": {"k": "v"}, "n": 0},
        {"unicode": "ae", "empty": ""},
    )
    for payload in vectors:
        old = _old_serializer_output(payload)
        current = serialize_canonical_okx_post_body_v1(payload)
        assert old == current
        assert old.encode("utf-8") == current.encode("utf-8")


def test_current_serializer_matches_frozen_post_body() -> None:
    assert serialize_canonical_okx_post_body_v1(_POST_PAYLOAD) == _POST_BODY


def test_k1_signed_post_body_uses_current_serializer() -> None:
    assert serialize_k1_signed_post_body_v1(_POST_PAYLOAD) == serialize_canonical_okx_post_body_v1(
        _POST_PAYLOAD
    )
    assert serialize_k1_signed_post_body_v1(_POST_PAYLOAD) == _POST_BODY


def test_current_post_uses_current_serializer_and_k1_signer() -> None:
    post_src = POST_SRC.read_text(encoding="utf-8")
    get_src = GET_SRC.read_text(encoding="utf-8")
    k1_src = K1_SRC.read_text(encoding="utf-8")
    ser_src = SERIALIZER_SRC.read_text(encoding="utf-8")
    assert "serialize_canonical_okx_post_body_v1" in post_src
    assert "build_k1_okx_venue_auth_headers_v1" in post_src
    assert "build_k1_okx_venue_auth_headers_v1" in get_src
    assert "okx_live_canary_signer_v1" not in post_src
    assert "okx_live_canary_signer_v1" not in get_src
    assert "okx_live_canary_signer_v1" not in k1_src
    assert "okx_live_canary_signer_v1" not in ser_src
    assert "build_okx_live_canary_auth_headers_v1" not in post_src
    assert "build_okx_live_canary_auth_headers_v1" not in get_src
    assert "secretref" not in ser_src.lower()
    assert "vault" not in ser_src.lower()
    assert "ephemeral" not in ser_src.lower()
