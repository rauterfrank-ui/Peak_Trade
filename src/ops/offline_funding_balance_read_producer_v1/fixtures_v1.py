"""Fixture envelopes for offline Funding Account balance observation tests.

These are test evidence only. They are not live venue observations.
"""

from __future__ import annotations

import json
from typing import Any, Mapping

FIXTURE_CLASS = "GOVERNED_TEST_FIXTURE_NOT_LIVE_OBSERVATION"


def _envelope(*, code: str = "0", msg: str = "", data: list[Any] | None = None) -> bytes:
    return json.dumps({"code": code, "msg": msg, "data": [] if data is None else data}).encode(
        "utf-8"
    )


def fixture_empty_funding_account_v1() -> bytes:
    return _envelope(data=[])


def fixture_usdc_nonzero_v1() -> bytes:
    return _envelope(data=[{"ccy": "USDC", "bal": "12.5", "frozenBal": "0", "availBal": "12.5"}])


def fixture_usd_nonzero_v1() -> bytes:
    return _envelope(data=[{"ccy": "USD", "bal": "3", "frozenBal": "0", "availBal": "3"}])


def fixture_multiple_asset_rows_v1() -> bytes:
    return _envelope(
        data=[
            {"ccy": "USDC", "bal": "10", "frozenBal": "1", "availBal": "9"},
            {"ccy": "USD", "bal": "2", "frozenBal": "0", "availBal": "2"},
            {"ccy": "BTC", "bal": "0.01", "frozenBal": "0", "availBal": "0.01"},
        ]
    )


def fixture_other_nonzero_currency_v1() -> bytes:
    return _envelope(data=[{"ccy": "BTC", "bal": "0.5", "frozenBal": "0", "availBal": "0.5"}])


def fixture_malformed_numeric_balance_v1() -> bytes:
    return _envelope(
        data=[{"ccy": "USDC", "bal": "not-a-number", "frozenBal": "0", "availBal": "0"}]
    )


def fixture_okx_code_nonzero_v1() -> bytes:
    return _envelope(code="50111", msg="Invalid OKX-API-Key", data=[])


def fixture_malformed_envelope_v1() -> bytes:
    return b"not-json"


def fixture_payload_as_mapping(body: bytes) -> Mapping[str, Any]:
    return json.loads(body.decode("utf-8"))
