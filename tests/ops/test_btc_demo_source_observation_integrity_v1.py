"""Actual BTC source readers: original receipt times and source scope, offline only."""

from copy import deepcopy
from datetime import datetime, timedelta, timezone

import pytest

from src.ops import btc_demo_lane3_v2 as demo

NOW = datetime(2026, 11, 22, 9, tzinfo=timezone.utc)


def coverage_source():
    return {
        demo._CONFIG: [{"uid": "142", "posMode": "net_mode"}],
        demo._BALANCE: [
            {"details": [{"ccy": "USDC", "availEq": "30"}, {"ccy": "USD", "availEq": "7"}]}
        ],
        demo._INSTRUMENTS: [
            {"instId": demo._NATIVE, "state": "live", "settleCcy": "USD", "groupId": "7"}
        ],
        demo._FEE: [{"instType": "FUTURES", "feeGroup": [{"groupId": "7", "taker": "-0.0005"}]}],
        demo._FX: [
            {"instId": "USDC-USD", "idxPx": "0.9998", "ts": str(int(NOW.timestamp() * 1000))}
        ],
    }


class CoverageReads:
    def __init__(self, *, codes=None, times=None, rows=None):
        self.rows = coverage_source() if rows is None else rows
        self.codes = codes or {}
        self.times = times or {}
        self.calls = []

    def read(self, path, **query):
        self.calls.append((path, query))
        return {
            "code": self.codes.get(path, "0"),
            "data": deepcopy(self.rows[path]),
        }, self.times.get(path, NOW)


@pytest.mark.parametrize("path", list(coverage_source()))
def test_original_coverage_rejects_error_response_with_apparently_valid_rows(path):
    with pytest.raises(ValueError):
        demo.read_btc_demo_coverage_v2(
            reads=CoverageReads(codes={path: "50000"}), expected_uid="142"
        )


@pytest.mark.parametrize("path", [demo._CONFIG, demo._BALANCE, demo._INSTRUMENTS, demo._FEE])
@pytest.mark.parametrize("fault", ["stale", "future", "naive"])
def test_original_coverage_rejects_unordered_or_stale_receipt_times(path, fault):
    acquired = NOW + timedelta(seconds=-16 if fault == "stale" else 1)
    if fault == "naive":
        acquired = NOW.replace(tzinfo=None)
    with pytest.raises(ValueError):
        demo.read_btc_demo_coverage_v2(
            reads=CoverageReads(times={path: acquired}), expected_uid="142"
        )


@pytest.mark.parametrize("fault", ["settlement", "group"])
def test_original_coverage_does_not_admit_foreign_currency_or_unknown_fee_group(fault):
    rows = coverage_source()
    if fault == "settlement":
        rows[demo._INSTRUMENTS][0]["settleCcy"] = "EUR"
    else:
        rows[demo._INSTRUMENTS][0].pop("groupId")
        rows[demo._FEE][0]["feeGroup"][0].pop("groupId")
    with pytest.raises(ValueError):
        demo.read_btc_demo_coverage_v2(reads=CoverageReads(rows=rows), expected_uid="142")


def test_valid_report_retains_original_units_and_source_snapshot():
    reads = CoverageReads()
    original = deepcopy(reads.rows)
    report = demo.read_btc_demo_coverage_v2(reads=reads, expected_uid="142")
    assert report["budget_value_usd"] == "24.9950"
    assert report["venue_settlement_currency"] == "USD"
    assert report["available_equity"] == {"USDC": "30", "USD": "7"}
    assert report["available_usdc_covers_declared_budget"] is True
    assert report["account_identity"] == "142"
    assert report["coverage_observed_at"] == NOW.isoformat()
    assert report["coverage_digest"]
    assert len(report["source_observations"]) == 5
    assert reads.rows == original
    assert report["trading_authority"] == "NONE"
    assert report["usd_usdc_account_settlement_proven"] is False
