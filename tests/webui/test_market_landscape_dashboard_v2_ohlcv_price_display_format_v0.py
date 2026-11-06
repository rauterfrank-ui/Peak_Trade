"""Presentation-only market price display formatting for Landscape V2.

Scope: chrome formatting only. No producer / readmodel / trading mutations.
"""

from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path

import pytest

from src.webui.market_dashboard_landscape_v2.presenter import (
    format_market_change_pct_display_v1,
    format_market_price_display_v1,
    format_market_volume_display_v1,
)

REPO = Path(__file__).resolve().parents[2]


@pytest.mark.parametrize(
    ("value", "tick_size", "expected"),
    [
        ("0.000000009724", None, "0.000000009724"),
        ("9.724e-9", None, "0.000000009724"),
        (9.724e-9, None, "0.000000009724"),
        ("1919.06", None, "1919.06"),
        (1919.06, None, "1919.06"),
        ("0.000000009724", "0.000000000001", "0.000000009724"),
        ("100.5", "0.1", "100.5"),
        ("100.5", "0.01", "100.50"),
    ],
)
def test_format_market_price_display_plain_decimal(
    value: object, tick_size: str | None, expected: str
) -> None:
    rendered = format_market_price_display_v1(value, tick_size=tick_size)
    assert rendered == expected
    assert "e-" not in rendered.lower()
    assert "e+" not in rendered.lower()


def test_format_market_price_tick_precision_preferred_over_fallback() -> None:
    assert format_market_price_display_v1("1.234567", tick_size="0.01") == "1.23"
    # Absent tick → documented significant/normalize fallback (no invented tick).
    assert format_market_price_display_v1("1.234567", tick_size=None) == "1.234567"


def test_format_market_volume_and_change_display() -> None:
    assert format_market_volume_display_v1(929) == "929"
    assert format_market_volume_display_v1("929.0") == "929"
    assert format_market_volume_display_v1("12.5") == "12.5"
    assert format_market_change_pct_display_v1("100", "99.5") == "-0.5000%"
    assert format_market_change_pct_display_v1("100", "100.5") == "+0.5000%"


def test_html_css_declutters_volume_and_expands_ohlc_labels() -> None:
    html = (REPO / "templates/peak_trade_dashboard/market_landscape_v2.html").read_text(
        encoding="utf-8"
    )
    css = (REPO / "static/css/market_dashboard_landscape_v2.css").read_text(encoding="utf-8")
    js = (REPO / "static/js/market_dashboard_landscape_v2.js").read_text(encoding="utf-8")

    assert "<dt>Open</dt>" in html
    assert "<dt>High</dt>" in html
    assert "<dt>Low</dt>" in html
    assert "<dt>Close</dt>" in html
    assert "<dt>Change</dt>" in html
    assert "<dt>Volume</dt>" in html
    assert 'data-mdl-field="ohlcv_change"' in html
    assert 'mdl-v2-volume__label">Volume' not in html
    assert "Volume bound to authentic OHLCV bar volume" not in html
    assert "Volume bound to authentic OHLCV bar volume" not in js
    assert ".toExponential(" not in js
    assert "function formatMarketPriceDisplay(" in js
    assert "mdl-v2-last-price-marker__label" in css
    assert "--mdl-volume-chrome-band: 0px" in css
    assert "--mdl-volume-message-band: 0px" in css


def test_js_price_display_helpers_behavioral_small_normal_tick() -> None:
    js = (REPO / "static/js/market_dashboard_landscape_v2.js").read_text(encoding="utf-8")

    def _extract(name: str) -> str:
        start = js.index(name)
        rest = js[start + len(name) :]
        end_rel = rest.find("\n  function ")
        assert end_rel > 0, name
        return js[start : start + len(name) + end_rel].rstrip() + "\n"

    helpers = "\n".join(
        [
            _extract("function expandScientificToPlain(raw)"),
            _extract("function decimalSafePlainFromInput(value)"),
            _extract("function tickFractionDigits(tickSize)"),
            _extract("function formatMarketPriceDisplay(value, tickSize)"),
            _extract("function formatMarketVolumeDisplay(value)"),
            _extract("function formatMarketChangePctDisplay(openV, closeV)"),
        ]
    )
    harness = f"""
'use strict';
{helpers}
function assert(cond, msg) {{
  if (!cond) throw new Error(msg || 'assert failed');
}}
var tiny = formatMarketPriceDisplay('9.724e-9', null);
assert(tiny === '0.000000009724', 'tiny plain');
assert(tiny.indexOf('e') === -1 && tiny.indexOf('E') === -1, 'no sci');
var normal = formatMarketPriceDisplay(1919.06, null);
assert(String(normal).indexOf('e') === -1, 'normal no sci');
assert(formatMarketPriceDisplay('100.5', '0.01') === '100.50', 'tick digits');
assert(formatMarketVolumeDisplay(929) === '929', 'volume int');
assert(formatMarketChangePctDisplay(100, 99.5) === '-0.5000%', 'change');
console.log('PRICE_DISPLAY_HELPERS_BEHAVIORAL_PASS');
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
    assert "PRICE_DISPLAY_HELPERS_BEHAVIORAL_PASS" in completed.stdout
