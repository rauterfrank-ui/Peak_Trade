"""Flat exposure and independent live market price; explicit offline sources."""

from copy import deepcopy
import json
import socket
import subprocess
from pathlib import Path
from decimal import Decimal

import pytest

from src.ops.peak_trade_public_market_data_runtime_v1.consumer_adapters_v1 import (
    landscape_readmodel_from_live_facts_v1,
)
from src.webui.market_surface_greenfield_v1.market_projection_v1 import (
    project_market_state_from_ohlcv_doc,
)
from tests.ops.test_productive_futures_accounting_runtime_binding_v1 import _session

CAPTURED = "2026-11-07T12:00:00Z"


@pytest.fixture(autouse=True)
def no_network(monkeypatch):
    def deny(*args, **kwargs):
        raise AssertionError("Only synthetic documents and ASGI in-process calls allowed")

    monkeypatch.setattr(socket.socket, "connect", deny)
    monkeypatch.setattr(socket, "create_connection", deny)


def document(mark="101.25"):
    return {
        "instrument_id": "ETH-USDT-SWAP",
        "provider_instrument_id": "ETH-USDT-SWAP",
        "interval": "1m",
        "freshness_state": "FRESH",
        "is_stale": False,
        "last_timestamp": "2026-11-07T11:59:00Z",
        "bars": [
            {"ts": "2026-11-07T11:59:00Z", "open": "98", "high": "100", "low": "97", "close": "99"}
        ],
        **landscape_readmodel_from_live_facts_v1(
            mark_px=mark, live_mark_captured_at=CAPTURED, ohlcv_freshness_state="FRESH"
        ),
        "schema_name": "okx_selected_instrument_ohlcv_readmodel.v1",
        "live_mark_provider_ts": CAPTURED,
    }


def project(doc, now=CAPTURED):
    return project_market_state_from_ohlcv_doc(doc, refresh_meta={"status": "OK"}, observed_at=now)


def test_actual_adapter_decimal_mark_is_consumed_instead_of_candle_close():
    doc = document()
    before = deepcopy(doc)
    state = project(doc)
    assert state["last_price"] == 101.25
    assert state["candle_series"][-1]["close"] == 99
    assert doc == before


def test_flat_accounting_and_display_follow_multiple_market_updates():
    accounting = _session()
    for mark in ("101.25", "103.75", "100.50"):
        accounting.mark_to_market(mark)
        risk = accounting.risk_state()
        assert accounting.position is None
        assert risk.notional == Decimal("0")
        assert risk.mark_price == Decimal(mark)
        assert project(document(mark))["last_price"] == float(mark)


@pytest.mark.parametrize("position_mark", ["0", "999"])
def test_flat_position_row_is_not_the_current_market_price_source(position_mark):
    from tests.ops.test_prepost_position_source_admission_v1 import Port, prove, row

    positions = [{**row("0"), "markPx": position_mark}]
    proof = prove(Port(global_rows=positions, scoped_rows=positions))
    assert proof.position_truth == "FLAT"
    assert proof.new_entry_position_admissible is True
    assert project(document("101.25"))["last_price"] == 101.25


@pytest.mark.parametrize("value", [None, "", "NaN", "Infinity", "-1", "0", True])
def test_invalid_or_missing_mark_does_not_relabel_candle_as_live_mark(value):
    state = project(document(value))
    assert state["live_mark_price"] is None
    assert state["last_price"] == 99
    assert state["last_price_kind"] == "CANDLE_CLOSE"


def test_fresh_document_without_any_price_is_not_a_fresh_price():
    doc = document(None)
    doc["bars"] = []
    state = project(doc)
    assert state["last_price"] is None
    assert state["last_price_kind"] == "UNAVAILABLE"
    assert state["last_price_freshness"] == "UNKNOWN"
    assert state["last_price_timestamp"] is None


@pytest.mark.parametrize(
    ("capture", "freshness"),
    [
        ("2026-11-07T11:00:00Z", "STALE"),
        ("2026-11-07T12:00:01Z", "INVALID"),
        (None, "UNKNOWN"),
    ],
)
def test_mark_clock_is_separate_from_fresh_candles(capture, freshness):
    doc = document()
    doc["live_mark_captured_at"] = capture
    state = project(doc)
    assert state["last_price"] == 101.25
    assert state["market_freshness"] == "FRESH"
    assert state["last_price_kind"] == "MARK_PRICE"
    assert state["last_price_freshness"] == freshness


def test_canonical_api_market_updates_even_while_system_slice_stays_cached(tmp_path, monkeypatch):
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    from src.webui.market_surface_greenfield_v1 import canonical_state_v1 as canonical
    from src.webui.market_surface_greenfield_v1.router_v1 import router
    from src.ops.okx_selected_instrument_ohlcv_readmodel_v1 import OHLCV_RELATIVE_PATH

    clock = ["2026-11-07T11:59:59Z"]
    doc = document()
    target = tmp_path / OHLCV_RELATIVE_PATH
    target.parent.mkdir(parents=True)
    target.write_text(json.dumps(doc))

    def refresh(**kwargs):
        clock[0] = CAPTURED
        return {"status": "OK", "refresh_attempted": False}

    async def cached(**kwargs):
        return {
            "system": {"position_quantity": "0", "source": "EXPLICIT_SYNTHETIC_CACHED_SYSTEM_SLICE"}
        }, True

    monkeypatch.setattr(canonical, "resolve_workflow_dashboard_archive_root", lambda: tmp_path)
    monkeypatch.setattr(canonical, "refresh_selected_okx_ohlcv_readmodel_from_archive_v1", refresh)
    monkeypatch.setattr(canonical, "get_or_refresh_system_slice", cached)
    monkeypatch.setattr(canonical, "_utc_now_iso", lambda: clock[0])
    app = FastAPI()
    app.include_router(router)
    with TestClient(app) as client:
        for mark in ("101.25", "103.75", "100.50"):
            doc["live_mark_price"] = mark
            target.write_text(json.dumps(doc))
            response = client.get("/api/operator-trading-surface/v1/state")
            assert response.status_code == 200
            body = response.json()
            assert body["system"]["position_quantity"] == "0"
            assert body["observation"]["system_slice_from_cache"] is True
            assert body["market"]["last_price"] == float(mark)
            assert body["market"]["last_price_freshness"] == "FRESH"


def test_actual_browser_consumer_renders_live_source_and_age_across_flat_ticks():
    frames = [project(document(mark)) for mark in ("101.25", "103.75", "100.50")]
    frames[1] = project(document("103.75"), now="2026-11-07T12:03:00Z")
    script = r"""
const vm=require('vm'),fs=require('fs'),assert=require('assert');
const input=JSON.parse(fs.readFileSync(0,'utf8'));
const nodes=Object.fromEntries(['ots-header-instrument','ots-header-price','ots-header-freshness'].map(k=>[k,{textContent:''}]));
let scheduled, current=0, calls=0;
const context={window:{},document:{body:{getAttribute:()=>'/synthetic-state',classList:{add:()=>{},remove:()=>{}}},readyState:'complete',querySelectorAll:()=>[],getElementById:id=>nodes[id]||null},
 clearTimeout:()=>{},setTimeout:fn=>{scheduled=fn;return 1;},
 fetch:(url,options)=>{assert.equal(url,'/synthetic-state');assert.equal(options.method,'GET');calls++;return Promise.resolve({json:()=>Promise.resolve({market:input.frames[current],system:{position_quantity:'0'},safety:{},poll_interval_seconds:1})});}};
vm.runInNewContext(fs.readFileSync(input.source,'utf8'),context);
(async()=>{
 const rendered=[];
 for(current=0;current<input.frames.length;current++){
  if(current)scheduled();
  await new Promise(setImmediate);
  rendered.push({price:nodes['ots-header-price'].textContent,sourceAge:nodes['ots-header-freshness'].textContent});
 }
 assert.equal(calls,3);console.log(JSON.stringify(rendered));
})().catch(e=>{console.error(e);process.exitCode=1;});
"""
    source = (
        Path(__file__).resolve().parents[2]
        / "static/js/market_surface_greenfield_v1/surface_app_v1.js"
    )
    result = subprocess.run(
        ["node", "-e", script],
        input=json.dumps({"frames": frames, "source": str(source)}),
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    rendered = json.loads(result.stdout)
    assert [r["price"] for r in rendered] == ["101.25", "103.75", "100.5"]
    assert "MARK PRICE · FRESH" in rendered[0]["sourceAge"]
    assert "MARK PRICE · STALE" in rendered[1]["sourceAge"]
    assert CAPTURED in rendered[1]["sourceAge"]
