"""Focused tests for OKX official min-notional mapping ratification owner."""

from __future__ import annotations

from decimal import Decimal
from pathlib import Path

import pytest

from src.ops.okx_min_notional_mapping_v1 import (
    FORMULA_ID,
    MIN_NOTIONAL_KIND,
    OkxMinNotionalMappingError,
    load_mapping_ratification_v1,
    map_okx_linear_swap_min_notional_v1,
)

REPO = Path(__file__).resolve().parents[2]


def test_ratification_markers_and_no_direct_field_claim() -> None:
    cfg = load_mapping_ratification_v1(repo_root=REPO)
    assert cfg["OKX_MIN_NOTIONAL_DIRECT_FIELD_AVAILABLE"] is False
    assert cfg["OKX_MIN_NOTIONAL_MAPPING_AUTHORIZED"] is True
    assert cfg["REFERENCE_PRICE_REQUIRED"] is True
    assert cfg["INVERSE_OR_AMBIGUOUS_CONTRACTS_FAIL_CLOSED"] is True
    assert cfg["DASHBOARD_AUTHORITY"] is False
    assert cfg["TRADING_AUTHORIZATION"] is False


def test_linear_swap_mapping_decimal_only() -> None:
    inst = {
        "instId": "ETH-USDT-SWAP",
        "instType": "SWAP",
        "uly": "ETH-USDT",
        "settleCcy": "USDT",
        "ctType": "linear",
        "ctVal": "0.1",
        "ctValCcy": "ETH",
        "minSz": "0.01",
        "state": "live",
    }
    result = map_okx_linear_swap_min_notional_v1(
        instrument=inst,
        reference_price="1859.58",
        reference_price_captured_at="2026-07-24T21:00:00Z",
        raw_capture_digest="abc",
        reference_price_fresh=True,
    )
    assert result.eligible is True
    assert result.min_notional_kind == MIN_NOTIONAL_KIND
    assert result.formula_id == FORMULA_ID
    expected = Decimal("0.01") * Decimal("0.1") * Decimal("1859.58")
    assert Decimal(result.computed_min_notional) == expected
    assert result.reference_price_type == "okx_public_mark_price"


def test_inverse_rejected() -> None:
    inst = {
        "instId": "ETH-USD-SWAP",
        "instType": "SWAP",
        "uly": "ETH-USD",
        "settleCcy": "ETH",
        "ctType": "inverse",
        "ctVal": "10",
        "ctValCcy": "USD",
        "minSz": "1",
    }
    result = map_okx_linear_swap_min_notional_v1(
        instrument=inst,
        reference_price="1859.58",
        reference_price_captured_at="2026-07-24T21:00:00Z",
        raw_capture_digest="abc",
    )
    assert result.eligible is False
    assert result.computed_min_notional is None


def test_missing_reference_price_rejected() -> None:
    inst = {
        "instId": "ETH-USDT-SWAP",
        "instType": "SWAP",
        "uly": "ETH-USDT",
        "settleCcy": "USDT",
        "ctType": "linear",
        "ctVal": "0.1",
        "ctValCcy": "ETH",
        "minSz": "0.01",
    }
    result = map_okx_linear_swap_min_notional_v1(
        instrument=inst,
        reference_price=None,
        reference_price_captured_at="2026-07-24T21:00:00Z",
        raw_capture_digest="abc",
    )
    assert result.eligible is False


def test_stale_reference_price_rejected() -> None:
    inst = {
        "instId": "ETH-USDT-SWAP",
        "instType": "SWAP",
        "uly": "ETH-USDT",
        "settleCcy": "USDT",
        "ctType": "linear",
        "ctVal": "0.1",
        "ctValCcy": "ETH",
        "minSz": "0.01",
    }
    result = map_okx_linear_swap_min_notional_v1(
        instrument=inst,
        reference_price="1859.58",
        reference_price_captured_at="2026-07-24T21:00:00Z",
        raw_capture_digest="abc",
        reference_price_fresh=False,
    )
    assert result.eligible is False


def test_float_money_rejected() -> None:
    inst = {
        "instId": "ETH-USDT-SWAP",
        "instType": "SWAP",
        "uly": "ETH-USDT",
        "settleCcy": "USDT",
        "ctType": "linear",
        "ctVal": "0.1",
        "ctValCcy": "ETH",
        "minSz": "0.01",
    }
    with pytest.raises(OkxMinNotionalMappingError):
        map_okx_linear_swap_min_notional_v1(
            instrument=inst,
            reference_price=1859.58,  # float forbidden
            reference_price_captured_at="2026-07-24T21:00:00Z",
            raw_capture_digest="abc",
        )


def test_btc_excluded() -> None:
    inst = {
        "instId": "BTC-USDT-SWAP",
        "instType": "SWAP",
        "uly": "BTC-USDT",
        "settleCcy": "USDT",
        "ctType": "linear",
        "ctVal": "0.01",
        "ctValCcy": "BTC",
        "minSz": "0.1",
    }
    result = map_okx_linear_swap_min_notional_v1(
        instrument=inst,
        reference_price="100000",
        reference_price_captured_at="2026-07-24T21:00:00Z",
        raw_capture_digest="abc",
    )
    assert result.eligible is False
