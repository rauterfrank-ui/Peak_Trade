"""Shared offline fixtures for monetary normalization tests."""

from __future__ import annotations

from typing import Any


def usdt_usdc_index_tickers_payload_v1(*, idx_px: str = "0.999676") -> dict[str, Any]:
    return {
        "code": "0",
        "data": [{"instId": "USDC-USDT", "idxPx": idx_px, "ts": "1787913816371"}],
    }


def usdc_usdt_swap_instruments_row_v1() -> dict[str, str]:
    return {
        "instId": "USDC-USDT-SWAP",
        "instType": "SWAP",
        "state": "live",
        "ctType": "linear",
        "baseCcy": "USDC",
        "quoteCcy": "USDT",
        "settleCcy": "USDT",
        "ctVal": "10",
        "ctValCcy": "USDC",
        "lotSz": "1",
        "minSz": "1",
        "tickSz": "0.000001",
    }


def api3_usdt_swap_instruments_row_v1(*, inst_id: str = "API3-USDT-SWAP") -> dict[str, str]:
    return {
        "instId": inst_id,
        "instType": "SWAP",
        "state": "live",
        "ctType": "linear",
        "baseCcy": "API3",
        "quoteCcy": "USDT",
        "settleCcy": "USDT",
        "ctVal": "1",
        "ctValCcy": "API3",
        "lotSz": "1",
        "minSz": "1",
        "tickSz": "0.0001",
    }


def eth_usdt_swap_instruments_row_v1(*, inst_id: str = "inst-eth-usdt-perp") -> dict[str, str]:
    return {
        "instId": inst_id,
        "instType": "SWAP",
        "state": "live",
        "ctType": "linear",
        "baseCcy": "ETH",
        "quoteCcy": "USDT",
        "settleCcy": "USDT",
        "ctVal": "0.01",
        "ctValCcy": "ETH",
        "lotSz": "1",
        "minSz": "1",
        "tickSz": "0.01",
    }


def combined_instruments_payload_v1(*rows: dict[str, str]) -> dict[str, Any]:
    return {"code": "0", "data": list(rows)}


def conversion_pair_instruments_payload_v1() -> dict[str, Any]:
    return combined_instruments_payload_v1(usdc_usdt_swap_instruments_row_v1())
