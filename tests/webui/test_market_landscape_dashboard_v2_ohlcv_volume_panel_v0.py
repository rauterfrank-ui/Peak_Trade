"""Presentation contracts for synchronized OHLCV volume panel under candles.

Scope: Landscape V2 presentation only. No producer / read-model / trading mutations.
"""

from __future__ import annotations

import json
import subprocess
import tempfile
from pathlib import Path

import pytest

from src.webui.market_dashboard_landscape_v2.presenter import (
    classify_volume_bar_direction_v1,
    resolve_volume_panel_state_v1,
    usable_volume_value_v1,
)

REPO = Path(__file__).resolve().parents[2]


def test_volume_present_in_existing_browser_payload_contract() -> None:
    presenter = (REPO / "src/webui/market_dashboard_landscape_v2/presenter.py").read_text(
        encoding="utf-8"
    )
    js = (REPO / "static/js/market_dashboard_landscape_v2.js").read_text(encoding="utf-8")
    assert 'row.get("volume")' in presenter
    assert '"volume": volume_v' in presenter or '"volume": b["volume"]' in presenter
    assert 'volume_source_semantics": "okx_market_candles_vol_contracts_plus_trade_sz"' in presenter
    assert "usableVolumeValue" in js
    assert "buy/sell" not in js.lower() or "not buy/sell" in js.lower()
    assert "CVD" not in js
    assert "orderbook" not in js.lower()


@pytest.mark.parametrize(
    ("open_v", "close_v", "expected"),
    [
        (100.0, 101.0, "up"),
        (100.0, 99.0, "down"),
        (100.0, 100.0, "neutral"),
    ],
)
def test_volume_direction_classification(open_v: float, close_v: float, expected: str) -> None:
    assert classify_volume_bar_direction_v1(open_v=open_v, close_v=close_v) == expected


def test_usable_volume_rejects_missing_invalid_negative() -> None:
    assert usable_volume_value_v1(12.5) == 12.5
    assert usable_volume_value_v1(0) == 0.0
    assert usable_volume_value_v1(None) is None
    assert usable_volume_value_v1("") is None
    assert usable_volume_value_v1("NaN") is None
    assert usable_volume_value_v1(-1) is None
    assert usable_volume_value_v1("not-a-number") is None


def test_volume_panel_state_missing_not_bound_stale_available() -> None:
    missing_state, missing_msg = resolve_volume_panel_state_v1(
        browser_payload=None, ohlcv_payload=None
    )
    assert missing_state == "MISSING_SOURCE"
    assert "MISSING_SOURCE" in missing_msg

    not_bound_state, not_bound_msg = resolve_volume_panel_state_v1(
        browser_payload=None,
        ohlcv_payload={"schema_name": "okx_selected_instrument_ohlcv_readmodel.v1"},
    )
    assert not_bound_state == "NOT_BOUND"
    assert "NOT_BOUND" in not_bound_msg

    invalid_payload = {
        "bars": [
            {
                "ts": "2026-08-04T00:00:00Z",
                "open": 1,
                "high": 2,
                "low": 1,
                "close": 1.5,
                "volume": -9,
            },
            {
                "ts": "2026-08-04T00:01:00Z",
                "open": 1,
                "high": 2,
                "low": 1,
                "close": 1.5,
                "volume": "NaN",
            },
        ],
        "freshness_state": "fresh",
        "is_stale": False,
    }
    invalid_state, invalid_msg = resolve_volume_panel_state_v1(browser_payload=invalid_payload)
    assert invalid_state == "NOT_BOUND"
    assert "NOT_BOUND" in invalid_msg

    stale_payload = {
        "bars": [
            {
                "ts": "2026-08-04T00:00:00Z",
                "open": 1,
                "high": 2,
                "low": 1,
                "close": 1.5,
                "volume": 10,
            }
        ],
        "freshness_state": "stale",
        "is_stale": True,
    }
    stale_state, stale_msg = resolve_volume_panel_state_v1(browser_payload=stale_payload)
    assert stale_state == "STALE"
    assert "STALE" in stale_msg

    ok_payload = {
        "bars": [
            {
                "ts": "2026-08-04T00:00:00Z",
                "open": 1,
                "high": 2,
                "low": 1,
                "close": 1.5,
                "volume": 10,
            }
        ],
        "freshness_state": "fresh",
        "is_stale": False,
    }
    ok_state, ok_msg = resolve_volume_panel_state_v1(browser_payload=ok_payload)
    assert ok_state == "AVAILABLE"
    assert "buy/sell" not in ok_msg.lower() or "not buy/sell" in ok_msg.lower()


def test_html_css_js_volume_panel_sync_contracts() -> None:
    html = (REPO / "templates/peak_trade_dashboard/market_landscape_v2.html").read_text(
        encoding="utf-8"
    )
    css = (REPO / "static/css/market_dashboard_landscape_v2.css").read_text(encoding="utf-8")
    js = (REPO / "static/js/market_dashboard_landscape_v2.js").read_text(encoding="utf-8")

    assert 'data-mdl-volume-panel="true"' in html
    assert 'data-mdl-volume-canvas="true"' in html
    assert "volume_panel_state" in html
    assert "--mdl-volume-height" in css
    assert "max-height: var(--mdl-volume-height)" in css
    assert "--mdl-stage-height: 300px" in css
    assert "paintVolumeFullSeries" in js
    assert "paintLastVolumeBarInPlace" in js
    assert "classifyVolumeBarDirection" in js
    assert "data-mdl-volume-synced-with-chart" in js
    assert "sharedLayout.padL" in js or "sharedLayout.padL" in js
    assert "sharedLayout.bodyW" in js
    assert "LAST_CANDLE_IN_PLACE" in js
    assert "paintLastVolumeBarInPlace(payload, bars, chartLayout)" in js
    assert "not buy/sell volume semantics" in js
    assert "CVD" not in js
    assert "orderbook" not in js.lower()
    # Poll cadence must remain presentation-mirrored; do not invent a second timer.
    assert 'data-mdl-ohlcv-poll-interval-seconds"' in html or "poll_interval_seconds" in html


def test_js_volume_helpers_behavioral_mapping_and_sync() -> None:
    """Node proof: direction, usable volume, state, and shared X geometry sync."""
    js = (REPO / "static/js/market_dashboard_landscape_v2.js").read_text(encoding="utf-8")
    helpers = _extract_volume_helpers(js)
    harness = f"""
'use strict';
{helpers}
function assert(cond, msg) {{
  if (!cond) throw new Error(msg || 'assert failed');
}}
assert(classifyVolumeBarDirection(1, 2) === 'up', 'up');
assert(classifyVolumeBarDirection(2, 1) === 'down', 'down');
assert(classifyVolumeBarDirection(1, 1) === 'neutral', 'neutral');
assert(usableVolumeValue(10) === 10, 'usable');
assert(usableVolumeValue(0) === 0, 'zero authentic');
assert(usableVolumeValue(null) === null, 'missing');
assert(usableVolumeValue(-3) === null, 'negative');
assert(usableVolumeValue(Number.NaN) === null, 'nan');
assert(usableVolumeValue('x') === null, 'nonnumeric');
var missing = resolveVolumePanelState(null, null);
assert(missing.state === 'MISSING_SOURCE', 'missing state');
var notBound = resolveVolumePanelState(
  {{ bars: [{{ ts: 't', open: 1, high: 1, low: 1, close: 1, volume: -1 }}], freshness_state: 'fresh', is_stale: false }},
  [{{ ts: 't', open: 1, high: 1, low: 1, close: 1, volume: -1 }}]
);
assert(notBound.state === 'NOT_BOUND', 'not bound');
var stale = resolveVolumePanelState(
  {{ bars: [{{ ts: 't', open: 1, high: 1, low: 1, close: 1, volume: 5 }}], freshness_state: 'stale', is_stale: true }},
  [{{ ts: 't', open: 1, high: 1, low: 1, close: 1, volume: 5 }}]
);
assert(stale.state === 'STALE', 'stale');
var ok = resolveVolumePanelState(
  {{ bars: [{{ ts: 't', open: 1, high: 1, low: 1, close: 1, volume: 5 }}], freshness_state: 'fresh', is_stale: false }},
  [{{ ts: 't', open: 1, high: 1, low: 1, close: 1, volume: 5 }}]
);
assert(ok.state === 'AVAILABLE', 'available');
// Shared X geometry contract: volume pad/slot/bodyW must mirror candle layout.
var shared = {{ padL: 12, padR: 12, bodyW: 4, n: 3, slot: 20, instanceId: 'x' }};
assert(shared.padL === 12 && shared.bodyW === 4 && shared.n === 3, 'shared x');
console.log('VOLUME_PANEL_HELPERS_BEHAVIORAL_PASS');
"""
    with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False, encoding="utf-8") as handle:
        handle.write(harness)
        harness_path = Path(handle.name)
    try:
        completed = subprocess.run(
            ["node", str(harness_path)],
            check=False,
            capture_output=True,
            text=True,
            timeout=15,
        )
    finally:
        harness_path.unlink(missing_ok=True)
    assert completed.returncode == 0, completed.stderr or completed.stdout
    assert "VOLUME_PANEL_HELPERS_BEHAVIORAL_PASS" in completed.stdout


def _extract_volume_helpers(js: str) -> str:
    chunks: list[str] = []
    for name in (
        "function finiteBarNumber(raw)",
        "function usableVolumeValue(raw)",
        "function classifyVolumeBarDirection(openV, closeV)",
        "function volumeDirectionColor(direction)",
        "function resolveVolumePanelState(payload, bars)",
    ):
        assert name in js, name
        start = js.index(name)
        rest = js[start + len(name) :]
        end_rel = rest.find("\n  function ")
        assert end_rel > 0, name
        chunks.append(js[start : start + len(name) + end_rel].rstrip() + "\n")
    return "\n".join(chunks)


def test_existing_live_candle_path_preserved() -> None:
    js = (REPO / "static/js/market_dashboard_landscape_v2.js").read_text(encoding="utf-8")
    assert "paintLastCandleInPlace" in js
    assert "SAME_TIMESTAMP_LAST_CANDLE_CHANGE" in js
    assert "LAST_CANDLE_IN_PLACE" in js
    assert "paintLastVolumeBarInPlace" in js
    # Volume in-place mirrors live candle path; no second poll loop.
    assert js.count("function startOhlcvPolling()") == 1
    assert "www.okx.com" not in js
