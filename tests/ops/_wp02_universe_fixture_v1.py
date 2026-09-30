"""Shared offline universe fixtures for CURRENT-WP-02 tests."""

from __future__ import annotations


def wp02_eth_only_universe_source_payload_v1() -> dict:
    return {
        "code": "0",
        "msg": "",
        "data": [
            {
                "instId": "ETH-USDT-SWAP",
                "instType": "SWAP",
                "state": "live",
                "baseCcy": "ETH",
                "quoteCcy": "USDT",
                "settleCcy": "USDT",
                "ctType": "linear",
                "ctVal": "0.01",
                "ctValCcy": "ETH",
                "tickSz": "0.01",
                "lotSz": "1",
                "minSz": "1",
                "uly": "ETH-USDT",
                "expTime": "",
            }
        ],
    }


def wp02_eth_only_mark_price_payload_v1() -> dict:
    return {
        "code": "0",
        "msg": "",
        "data": [{"instId": "ETH-USDT-SWAP", "markPx": "100.5"}],
    }
