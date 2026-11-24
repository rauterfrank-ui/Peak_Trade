"""Exercise the complete bounded GET path against an in-memory Demo venue."""

import base64
from copy import deepcopy
from datetime import datetime, timezone
import hmac
from io import BytesIO
import json
from urllib.parse import parse_qsl, urlsplit

import pytest

from scripts.ops import inspect_btc_demo_account_v1 as cli
from src.ops import btc_demo_lane3_v2 as demo
from tests.ops.test_btc_demo_source_observation_integrity_v1 import (
    NOW,
    CoverageReads,
    coverage_source,
)


class Response(BytesIO):
    status = 200

    def __init__(self, url, rows):
        super().__init__(json.dumps({"code": "0", "data": rows}).encode())
        self.url = url


def test_private_reads_unsigned_index_and_no_order(monkeypatch):
    rows = deepcopy(coverage_source())
    rows[demo._CONFIG][0].update(acctLv="2", settleCcy="USDC", settleCcyList=["USDC", "USD"])
    rows[demo._FEE][0]["feeGroup"][0]["maker"] = "-0.0002"
    rows[demo._FX][0]["ts"] = str(int(datetime.now(timezone.utc).timestamp() * 1000))
    calls = []

    class Opener:
        def open(self, req, timeout):
            url = urlsplit(req.full_url)
            headers = {key.lower(): value for key, value in req.header_items()}
            assert (url.scheme, url.netloc, req.method, req.data) == (
                "https",
                "eea.okx.com",
                "GET",
                None,
            )
            assert headers["x-simulated-trading"] == "1"
            if url.path == demo._FX:
                assert not any(k.startswith("ok-access-") for k in headers)
            else:
                assert headers["ok-access-key"] == "fixture-key"
                assert headers["ok-access-passphrase"] == "fixture-phrase"
                prehash = headers["ok-access-timestamp"] + "GET" + req.selector
                expected = hmac.digest(b"fixture-secret", prehash.encode(), "sha256")
                assert headers["ok-access-sign"] == base64.b64encode(expected).decode()
            calls.append((url.path, dict(parse_qsl(url.query))))
            return Response(req.full_url, rows[url.path])

    monkeypatch.setattr(demo, "build_opener", lambda *handlers: Opener())
    reader = cli.account_reader("fixture-key", "fixture-secret", "fixture-phrase")

    def now():
        return datetime.now(timezone.utc).timestamp()

    report = cli.inspect_account(reader, "142", now)
    assert calls == [
        (demo._CONFIG, {}),
        (demo._BALANCE, {"ccy": "USD,USDC"}),
        (demo._INSTRUMENTS, {"instType": "FUTURES", "instId": demo._NATIVE}),
        (demo._FEE, {"instType": "FUTURES", "instFamily": demo._FAMILY}),
        (demo._FX, {"instId": "USDC-USD"}),
    ]
    assert report["account_usd_m_settlement_currency"] == "USDC"
    assert report["private_instrument_settlement_currency"] == "USD"
    assert report["public_index_value_of_cap_usd"] == "24.9950"
    assert report["declared_budget_usdc"] == "25"
    assert report["maker_fee_rate_signed"] == "-0.0002"
    assert report["taker_fee_rate_signed"] == "-0.0005"
    assert report["sizing_verified"] is False
    assert report["trading_authority"] == "NONE"
    for private in ("142", "fixture-key", "fixture-phrase", "fixture-secret"):
        assert private not in {str(value) for value in report.values()}
    with pytest.raises(ValueError, match="ACCOUNT_MISMATCH"):
        cli.inspect_account(reader, "143", now)
    assert len(calls) == 6
    with pytest.raises(ValueError, match="OUT_OF_SCOPE"):
        reader.read(demo._ORDER, instId=demo._NATIVE)
    assert len(calls) == 6


def test_missing_active_settlement_cannot_be_inferred_from_list_or_balance():
    rows = coverage_source()
    rows[demo._CONFIG][0]["settleCcyList"] = ["USD", "USDC"]
    rows[demo._BALANCE][0]["details"][0].update(availBal="42", availEq="")
    report = cli.inspect_account(CoverageReads(rows=rows), "142", NOW.timestamp)
    assert report["usdc_in_account_settlement_choices"] is True
    assert report["account_usd_m_settlement_currency"] is None
    assert report["available_equity_usdc"] is None
    assert report["available_equity_covers_cap"] is None
    assert report["sizing_verified"] is False


def test_keychain_cli_keeps_credentials_out_of_output(monkeypatch, capsys):
    from types import SimpleNamespace

    values = {"api-key": "fixture-key", "secret": "fixture-secret", "passphrase": "fixture-phrase"}
    calls = []

    def run(args, **kwargs):
        assert args[:3] == ["/usr/bin/security", "find-generic-password", "-s"]
        assert args[3] == "fixture-service"
        assert args[-1] == "-w"
        assert kwargs == {"capture_output": True, "check": True, "timeout": 60}
        calls.append(args[-2])
        return SimpleNamespace(stdout=(values[args[-2]] + "\n").encode())

    monkeypatch.setattr(cli.subprocess, "run", run)
    monkeypatch.setattr(
        cli.sys,
        "argv",
        ["inspect", "--lesen", "--keychain-service", "fixture-service", "--demo-uid", "142"],
    )
    monkeypatch.setattr(cli, "account_reader", lambda *fields: tuple(fields))

    def inspect(reader, uid, clock):
        assert reader == tuple(values.values()) and uid == "142"
        return {"trading_authority": "NONE", "sizing_verified": False}

    monkeypatch.setattr(cli, "inspect_account", inspect)
    assert cli.main() == 0
    output = capsys.readouterr()
    assert calls == list(values)
    assert all(secret not in output.out + output.err for secret in values.values())


def test_pretrade_demo_sources_retain_original_bytes_and_exact_cycle(monkeypatch):
    from hashlib import sha256

    rows = deepcopy(coverage_source())
    rows[demo._CONFIG][0]["posMode"] = "net_mode"
    for key, (path, _) in demo.BTC_DEMO_PRETRADE_QUERIES_V1.items():
        rows.setdefault(path, [])
    calls = []

    class Opener:
        def open(self, req, timeout):
            url = urlsplit(req.full_url)
            headers = {key.lower(): value for key, value in req.header_items()}
            assert url.hostname == "eea.okx.com" and req.method == "GET" and req.data is None
            assert headers["x-simulated-trading"] == "1"
            public = url.path in {"/api/v5/market/books", "/api/v5/public/funding-rate"}
            assert ("ok-access-sign" in headers) is not public
            response = Response(req.full_url, rows[url.path])
            calls.append((req.selector, response.getvalue()))
            return response

    monkeypatch.setattr(demo, "build_opener", lambda *handlers: Opener())
    reader = cli.pretrade_reader("fixture-key", "fixture-secret", "fixture-phrase")
    started = datetime.now(timezone.utc)
    result = demo.read_btc_demo_pretrade_sources_v1(
        reads=reader,
        expected_uid="142",
        decision_epoch=started.isoformat(),
        cycle_id="original-core-cycle",
        clock=lambda: datetime.now(timezone.utc).timestamp(),
    )
    assert list(result) == list(demo.BTC_DEMO_PRETRADE_QUERIES_V1)
    for (name, source), (endpoint, body) in zip(result.items(), calls):
        assert source.endpoint == endpoint and source.body_sha256 == sha256(body).hexdigest()
        assert source.payload == json.loads(body)
        assert source.transport_class == "OKX_EEA_DEMO_READ_ONLY_GET"
        assert source.data_safety_source_kind is None
        assert source.auth_header_sent is (name not in {"book", "funding"})
        assert json.loads(source.pretrade_decision_id) == {
            "decision_epoch": started.isoformat(),
            "cycle_id": "original-core-cycle",
        }
    assert len(calls) == 9
    with pytest.raises(ValueError, match="OUT_OF_SCOPE"):
        reader.read(demo._ORDER, instId=demo._NATIVE, clOrdId="anything")
    assert len(calls) == 9
    with pytest.raises(ValueError, match="ACCOUNT_MISMATCH"):
        demo.read_btc_demo_pretrade_sources_v1(
            reads=reader,
            expected_uid="143",
            decision_epoch=started.isoformat(),
            cycle_id="original-core-cycle",
            clock=lambda: datetime.now(timezone.utc).timestamp(),
        )
    assert len(calls) == 10


def test_pretrade_demo_rejects_expired_decision_before_network(monkeypatch):
    reader = cli.pretrade_reader("fixture-key", "fixture-secret", "fixture-phrase")
    monkeypatch.setattr(reader._opener, "open", lambda *a, **k: pytest.fail("expired network read"))
    with pytest.raises(ValueError, match="ACQUISITION_STALE"):
        demo.read_btc_demo_pretrade_sources_v1(
            reads=reader,
            expected_uid="142",
            decision_epoch=NOW.isoformat(),
            cycle_id="original-core-cycle",
            clock=lambda: NOW.timestamp() + 16,
        )
