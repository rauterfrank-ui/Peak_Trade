"""OPS narrow-viewport containment — presentation-only layout regression.

CAPABILITY_ID=CAPABILITY_PRESENTATION_LANDSCAPE_OPS_NARROW_VIEWPORT_CONTAINMENT_V1

Proves long OPS reason strings stay inside their grid column at 1200/1512/1920
without changing the 3-column workspace shell or Context rail.
"""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
CSS = REPO / "static" / "css" / "market_dashboard_landscape_v2.css"
EVIDENCE_DIR = REPO / "evidence" / "market_dashboard_v2" / "ops_narrow_viewport_containment_v1"

VIEWPORTS = (
    (1200, 807, "ops_containment_1200x807.png"),
    (1512, 982, "ops_containment_1512x982.png"),
    (1920, 1080, "ops_containment_1920x1080.png"),
)

EVIDENCE_GENERATED_AT = datetime(2026, 8, 4, 12, 0, 0, tzinfo=timezone.utc)

_OPS_OVERLAP_JS = """
() => {
  function overlap(a, b) {
    return !(a.right <= b.left || b.right <= a.left || a.bottom <= b.top || b.bottom <= a.top);
  }
  function contained(a, b) {
    return (
      (a.left <= b.left + 0.5 && a.right >= b.right - 0.5 &&
       a.top <= b.top + 0.5 && a.bottom >= b.bottom - 0.5) ||
      (b.left <= a.left + 0.5 && b.right >= a.right - 0.5 &&
       b.top <= a.top + 0.5 && b.bottom >= a.bottom - 0.5)
    );
  }
  const rows = [...document.querySelectorAll('.mdl-v2-ops .mdl-v2-kv > div')];
  const overlaps = [];
  for (let i = 0; i < rows.length; i++) {
    const ra = rows[i].getBoundingClientRect();
    if (ra.width < 1 || ra.height < 1) continue;
    for (let j = i + 1; j < rows.length; j++) {
      if (rows[i].contains(rows[j]) || rows[j].contains(rows[i])) continue;
      const rb = rows[j].getBoundingClientRect();
      if (rb.width < 1 || rb.height < 1) continue;
      if (!overlap(ra, rb) || contained(ra, rb)) continue;
      const iw = Math.min(ra.right, rb.right) - Math.max(ra.left, rb.left);
      const ih = Math.min(ra.bottom, rb.bottom) - Math.max(ra.top, rb.top);
      if (iw > 2 && ih > 2) {
        overlaps.push({
          iw,
          ih,
          a: (rows[i].innerText || '').trim().slice(0, 80),
          b: (rows[j].innerText || '').trim().slice(0, 80),
        });
      }
    }
  }
  const workspace = document.querySelector('.mdl-v2-workspace');
  const railRight = document.querySelector('.mdl-v2-rail--right');
  const chartMetaDd = document.querySelector('.mdl-v2-chart__meta dd');
  const ws = workspace ? getComputedStyle(workspace) : null;
  const metaDd = chartMetaDd ? getComputedStyle(chartMetaDd) : null;
  return {
    ops_overlaps: overlaps,
    doc_overflow_x:
      document.documentElement.scrollWidth - document.documentElement.clientWidth,
    workspace_columns: ws ? ws.gridTemplateColumns : null,
    workspace_column_count: workspace ? workspace.children.length : 0,
    rail_right_width: railRight ? railRight.getBoundingClientRect().width : null,
    chart_meta_ellipsis: metaDd
      ? {
          whiteSpace: metaDd.whiteSpace,
          textOverflow: metaDd.textOverflow,
          overflow: metaDd.overflow,
        }
      : null,
    ops_col_min_width: (() => {
      const col = document.querySelector('.mdl-v2-ops__col');
      return col ? getComputedStyle(col).minWidth : null;
    })(),
    ops_dd_wrap: (() => {
      const dd = document.querySelector('.mdl-v2-ops .mdl-v2-kv dd');
      if (!dd) return null;
      const s = getComputedStyle(dd);
      return {
        minWidth: s.minWidth,
        overflowWrap: s.overflowWrap,
        wordBreak: s.wordBreak,
      };
    })(),
  };
}
"""


def _css_without_comments() -> str:
    raw = CSS.read_text(encoding="utf-8")
    return re.sub(r"/\*.*?\*/", "", raw, flags=re.S)


def test_ops_narrow_viewport_css_containment_contract() -> None:
    """Static owner: OPS columns must shrink/wrap; workspace/ellipsis stay intact."""
    assert CSS.is_file()
    code = _css_without_comments()

    assert re.search(
        r"\.mdl-v2-ops__col\s*\{[^}]*min-width:\s*0",
        code,
        flags=re.S,
    ), "OPS_COL_MIN_WIDTH_0_REQUIRED"

    assert re.search(
        r"\.mdl-v2-ops\s+\.mdl-v2-kv\s+dd\s*\{[^}]*overflow-wrap:\s*anywhere",
        code,
        flags=re.S,
    ), "OPS_DD_OVERFLOW_WRAP_REQUIRED"
    assert re.search(
        r"\.mdl-v2-ops\s+\.mdl-v2-kv\s+dd\s*\{[^}]*word-break:\s*break-word",
        code,
        flags=re.S,
    ), "OPS_DD_WORD_BREAK_REQUIRED"
    assert re.search(
        r"\.mdl-v2-ops\s+\.mdl-v2-kv\s+dd\s*\{[^}]*min-width:\s*0",
        code,
        flags=re.S,
    ), "OPS_DD_MIN_WIDTH_0_REQUIRED"

    # Workspace 3-column shell must remain the canonical owner template.
    assert "grid-template-columns: minmax(150px, 190px) minmax(0, 1fr) minmax(160px, 210px)" in code
    assert ".mdl-v2-rail--right" in code

    # Canonical chart-meta ellipsis must not be removed by this capability.
    assert re.search(
        r"\.mdl-v2-chart__meta\s+dd\s*\{[^}]*text-overflow:\s*ellipsis",
        code,
        flags=re.S,
    ), "CHART_META_ELLIPSIS_MUST_REMAIN"
    assert re.search(
        r"\.mdl-v2-decision__fact--secondary\s+dd\s*\{[^}]*text-overflow:\s*ellipsis",
        code,
        flags=re.S,
    ), "DECISION_SECONDARY_ELLIPSIS_MUST_REMAIN"

    # Narrow breakpoint keeps OPS as a 3-col grid (collapse only at 980px).
    mq_1280 = re.search(
        r"@media\s*\(max-width:\s*1280px\)\s*\{(.*?)\n\}",
        code,
        flags=re.S,
    )
    assert mq_1280 is not None
    assert ".mdl-v2-ops" in mq_1280.group(1)
    assert "column-gap: 18px" in mq_1280.group(1)


def _render_landscape_html() -> str:
    from jinja2 import Environment, FileSystemLoader, select_autoescape

    from src.webui.market_dashboard_landscape_producer_binding_v2 import (
        bind_market_universe_slots,
    )
    from src.webui.market_dashboard_landscape_v2 import (
        MarketDashboardReadServiceV1,
        present_market_landscape_v2,
    )

    slots = bind_market_universe_slots(generated_at=EVIDENCE_GENERATED_AT)
    page = MarketDashboardReadServiceV1().load_page_snapshot(
        generated_at=EVIDENCE_GENERATED_AT,
        slot_overrides=slots,
    )
    context = present_market_landscape_v2(page)
    env = Environment(
        loader=FileSystemLoader(str(REPO / "templates" / "peak_trade_dashboard")),
        autoescape=select_autoescape(["html", "xml"]),
    )
    return env.get_template("market_landscape_v2.html").render(
        status={"project": "Peak_Trade"},
        **context,
    )


def test_real_chrome_ops_narrow_viewport_containment(tmp_path: Path) -> None:
    pytest.importorskip("playwright")
    from playwright.sync_api import sync_playwright

    html = _render_landscape_html()
    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    (EVIDENCE_DIR / "rendered_market.html").write_text(html, encoding="utf-8")

    console_errors: list[str] = []
    page_errors: list[str] = []
    metrics_by_shot: dict[str, object] = {}

    with sync_playwright() as p:
        try:
            browser = p.chromium.launch(channel="chrome", headless=True)
            channel = "chrome"
        except Exception:
            browser = p.chromium.launch(headless=True)
            channel = "chromium"

        try:
            for width, height, shot_name in VIEWPORTS:
                ctx = browser.new_context(viewport={"width": width, "height": height})
                page = ctx.new_page()
                page.on(
                    "console",
                    lambda msg: (
                        console_errors.append(f"{msg.type}:{msg.text}")
                        if msg.type == "error"
                        else None
                    ),
                )
                page.on("pageerror", lambda exc: page_errors.append(str(exc)))

                def _handler(route, request, _html=html):  # type: ignore[no-untyped-def]
                    url = request.url
                    if url.endswith("/market") or url.rstrip("/").endswith(":8765"):
                        route.fulfill(status=200, content_type="text/html", body=_html)
                        return
                    if "/static/" in url:
                        rel = url.split("/static/", 1)[1]
                        path = REPO / "static" / rel
                        if path.is_file():
                            ctype = (
                                "text/css"
                                if path.suffix == ".css"
                                else "application/javascript"
                                if path.suffix == ".js"
                                else "application/octet-stream"
                            )
                            route.fulfill(
                                status=200,
                                content_type=ctype,
                                body=path.read_bytes(),
                            )
                            return
                    route.fulfill(status=404, body=b"missing")

                page.route("**/*", _handler)
                page.goto("http://127.0.0.1:8765/market", wait_until="domcontentloaded")
                page.wait_for_timeout(250)

                metrics = page.evaluate(_OPS_OVERLAP_JS)
                assert metrics["ops_overlaps"] == [], (
                    f"OPS_CROSS_COLUMN_OVERLAP viewport={width}x{height} "
                    f"overlaps={metrics['ops_overlaps']}"
                )
                assert metrics["doc_overflow_x"] <= 1, (
                    f"HORIZONTAL_OVERFLOW viewport={width}x{height} "
                    f"overflow_x={metrics['doc_overflow_x']}"
                )
                assert metrics["workspace_column_count"] == 3
                assert metrics["rail_right_width"] is not None
                assert float(metrics["rail_right_width"]) <= 220.0
                assert metrics["ops_col_min_width"] == "0px"
                assert metrics["ops_dd_wrap"]["minWidth"] == "0px"
                assert metrics["ops_dd_wrap"]["overflowWrap"] in (
                    "anywhere",
                    "break-word",
                )
                assert metrics["chart_meta_ellipsis"]["textOverflow"] == "ellipsis"
                assert metrics["chart_meta_ellipsis"]["whiteSpace"] == "nowrap"

                shot_path = EVIDENCE_DIR / shot_name
                page.screenshot(path=str(shot_path), full_page=True)
                metrics_by_shot[shot_name] = {
                    "viewport": [width, height],
                    "channel": channel,
                    "ops_overlaps": metrics["ops_overlaps"],
                    "doc_overflow_x": metrics["doc_overflow_x"],
                    "workspace_columns": metrics["workspace_columns"],
                    "rail_right_width": metrics["rail_right_width"],
                    "ops_col_min_width": metrics["ops_col_min_width"],
                    "ops_dd_wrap": metrics["ops_dd_wrap"],
                    "chart_meta_ellipsis": metrics["chart_meta_ellipsis"],
                }
                ctx.close()
        finally:
            browser.close()

    assert console_errors == [], console_errors
    assert page_errors == [], page_errors

    (EVIDENCE_DIR / "containment_metrics.json").write_text(
        json.dumps(
            {
                "capability_id": (
                    "CAPABILITY_PRESENTATION_LANDSCAPE_OPS_NARROW_VIEWPORT_CONTAINMENT_V1"
                ),
                "channel_metrics": metrics_by_shot,
                "console_errors": console_errors,
                "page_errors": page_errors,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
