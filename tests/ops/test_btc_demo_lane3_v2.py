from datetime import datetime, timedelta, timezone
from decimal import Decimal
from types import SimpleNamespace

import pytest

from src.ops import btc_demo_lane3_v2 as demo


def _read_fixture(rows):
    now = datetime(2026, 11, 18, tzinfo=timezone.utc)

    class Reads:
        def read(self, path, **query):
            return {"code": "0", "data": rows[path]}, now

    return Reads()


@pytest.mark.parametrize("fault", [None, "ack_only", "foreign_position", "fee_conflict"])
def test_only_confirmed_demo_fill_enters_the_v2_opening_handoff(fault):
    common = {
        "instId": demo._NATIVE,
        "clOrdId": "btcDemo3",
        "ordId": "432",
        "posSide": "net",
        "side": "buy",
    }
    time_ms = int(
        (datetime(2026, 11, 18, tzinfo=timezone.utc) - timedelta(seconds=2)).timestamp() * 1000
    )
    fill = {
        **common,
        "tradeId": "98",
        "fillTime": str(time_ms),
        "fillSz": "0.0001",
        "fillPx": "64000",
        "feeCcy": "USDC",
        "fee": "-0.0032",
    }
    rows = {
        demo._CONFIG: [{"uid": "142", "posMode": "net_mode"}],
        demo._PENDING: [],
        demo._ORDER: [
            {
                **common,
                "state": "filled",
                "reduceOnly": "false",
                "sz": "0.0001",
                "accFillSz": "0.0001",
            }
        ],
        demo._FILLS: [fill, dict(fill)],
        demo._POSITIONS: [
            {
                "instId": demo._NATIVE,
                "posSide": "net",
                "pos": "0.0001",
                "tradeId": "98",
                "avgPx": "64000",
                "uTime": str(time_ms + 1),
            }
        ],
    }
    identity = SimpleNamespace(
        account_identity="142",
        clordid="btcDemo3",
        native_id=demo._NATIVE,
        instrument_id=demo._NATIVE,
        execution_environment="TESTNET",
        exchange_ord_id=None,
        final_quantity="0.0001",
        quantity_unit="CONTRACTS",
        selected_side="LONG",
        identity_digest=lambda: "1" * 64,
    )
    if fault == "ack_only":
        rows[demo._ORDER][0].update(state="live", accFillSz="0")
        rows[demo._FILLS] = []
    elif fault == "foreign_position":
        rows[demo._POSITIONS][0].update(tradeId="99")
    elif fault == "fee_conflict":
        rows[demo._FILLS][1].update(fee="-0.012")
    if fault:
        with pytest.raises(ValueError):
            demo._confirmed_first_fill(_read_fixture(rows), identity)
        return
    confirmed = demo._confirmed_first_fill(_read_fixture(rows), identity)
    assert confirmed.price == Decimal("64000")
    assert confirmed.filled_quantity == "0.0001"
    assert confirmed.fee_rows == (("98", "USDC", "-0.0032"),)


def test_demo_collateral_uses_observed_rate_and_preserves_venue_currency():
    now = datetime(2026, 11, 18, tzinfo=timezone.utc)
    report = demo.read_btc_demo_coverage_v2(
        expected_uid="142",
        reads=_read_fixture(
            {
                demo._CONFIG: [{"uid": "142", "posMode": "net_mode"}],
                demo._BALANCE: [
                    {"details": [{"ccy": "USDC", "availEq": "23"}, {"ccy": "USD", "availEq": "9"}]}
                ],
                demo._INSTRUMENTS: [
                    {"instId": demo._NATIVE, "state": "live", "settleCcy": "USD", "groupId": "7"}
                ],
                demo._FEE: [
                    {"instType": "FUTURES", "feeGroup": [{"groupId": "7", "taker": "-0.0005"}]}
                ],
                demo._FX: [
                    {
                        "instId": "USDC-USD",
                        "idxPx": "0.9998",
                        "ts": str(int(now.timestamp() * 1000)),
                    }
                ],
            }
        ),
    )
    assert report["budget_value_usd"] == "24.9950"
    assert report["venue_settlement_currency"] == "USD"
    assert report["available_equity"] == {"USDC": "23", "USD": "9"}
    assert report["available_usdc_covers_declared_budget"] is False
