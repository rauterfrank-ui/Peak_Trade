"""Regression tests for bounded productive OKX read-only GET validation helpers."""

from __future__ import annotations

from src.ops.full_core_live_path_composition_root_v1.fresh_pretrade_runtime_get_v1 import (
    ENDPOINT_ACCOUNT_CONFIG,
)
from src.ops.full_core_live_path_composition_root_v1.ghv_current_okx_productive_read_only_reconciliation_get_validation_v1 import (
    build_bounded_read_only_get_endpoint_v1,
)
from src.ops.full_core_live_path_composition_root_v1.checkout_independent_credential_okx_venue_auth_headers_v1 import (
    _sign_request_path_from_url,
)


def test_empty_query_endpoint_matches_k1_sign_request_path() -> None:
    endpoint = build_bounded_read_only_get_endpoint_v1(ENDPOINT_ACCOUNT_CONFIG, {})
    assert endpoint == ENDPOINT_ACCOUNT_CONFIG
    assert "?" not in endpoint
    signed = _sign_request_path_from_url(f"https://eea.okx.com{endpoint}")
    assert signed == ENDPOINT_ACCOUNT_CONFIG


def test_non_empty_query_endpoint_matches_k1_sign_request_path() -> None:
    endpoint = build_bounded_read_only_get_endpoint_v1(
        "/api/v5/trade/orders-pending",
        {"instType": "SWAP", "instId": "BTC-USDT-SWAP"},
    )
    assert endpoint.startswith("/api/v5/trade/orders-pending?")
    signed = _sign_request_path_from_url(f"https://eea.okx.com{endpoint}")
    assert signed == endpoint
