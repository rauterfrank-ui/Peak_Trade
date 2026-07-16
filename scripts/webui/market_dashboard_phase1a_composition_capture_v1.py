#!/usr/bin/env python3
"""Phase 1A composition foundation — Chrome Playwright evidence capture.

Uses review_server harness only. LOCALHOST_ONLY. UVICORN_RELOAD=false.
PRIMARY_BROWSER=GOOGLE_CHROME, channel=chrome.
"""

from __future__ import annotations

import json
import sys
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

REPO_ROOT = Path(__file__).resolve().parents[2]
VIEWPORTS = ((1280, 800), (1440, 900), (1728, 1117), (1024, 768))
EXPECTED_LANDMARKS = [
    "GLOBAL_HEADER",
    "PRIMARY_MARKET_SURFACE",
    "DECISION_SURFACE",
    "OBSERVABILITY_SURFACE",
    "ENGINEERING_DRAWER",
]


@dataclass
class CaptureReport:
    captured_at_utc: str
    head_sha: str
    origin_main_sha: str
    base_url: str
    review_url: str
    PRIMARY_BROWSER: str = "GOOGLE_CHROME"
    PRIMARY_PLAYWRIGHT_CHANNEL: str = "chrome"
    BROWSER_ACTUAL: str = "NONE"
    REAL_CHROME_VERIFIED: bool = False
    CHROMIUM_FALLBACK_USED: bool = False
    HTTP_200: bool = False
    CONSOLE_ERRORS: int = 0
    PAGE_ERRORS: int = 0
    FAILED_ASSETS: int = 0
    EXTERNAL_NETWORK_REQUESTS: int = 0
    UNEXPECTED_NETWORK_REQUESTS: int = 0
    external_requests: list[str] = field(default_factory=list)
    console_messages: list[str] = field(default_factory=list)
    viewports: dict[str, Any] = field(default_factory=dict)
    screenshots: list[str] = field(default_factory=list)
    landmark_order_observed: list[str] = field(default_factory=list)
    landmark_order_pass: bool = False
    engineering_drawer_default_hidden: bool | None = None
    geometry_1440x900: dict[str, Any] = field(default_factory=dict)
    geometry_assertions: dict[str, Any] = field(default_factory=dict)


def _is_self_only(url: str, allowed_origin: str) -> bool:
    if url.startswith(("data:", "blob:", "about:")):
        return True
    parsed = urlparse(url)
    if not parsed.scheme:
        return True
    return f"{parsed.scheme}://{parsed.netloc}" == allowed_origin


def _git_sha(ref: str) -> str:
    import subprocess

    try:
        return subprocess.check_output(
            ["git", "rev-parse", ref], cwd=str(REPO_ROOT), text=True
        ).strip()
    except Exception:  # noqa: BLE001
        return "UNKNOWN"


def _eval_geometry() -> str:
    return """() => {
      const pick = (sel) => {
        const el = document.querySelector(sel);
        if (!el) return null;
        const r = el.getBoundingClientRect();
        const st = window.getComputedStyle(el);
        return {
          top: r.top, bottom: r.bottom, left: r.left, right: r.right,
          width: r.width, height: r.height,
          display: st.display, visibility: st.visibility,
          open: el.hasAttribute('open')
        };
      };
      const doc = document.documentElement;
      const badges = Array.from(document.querySelectorAll(
        '[data-market-foundation-header-badge-v1="true"], [data-market-system-status-node-v1="true"]'
      ));
      const prominent = Array.from(document.querySelectorAll(
        '[data-market-foundation-header-badge-v1="true"]'
      ));
      const level4Open = Array.from(document.querySelectorAll(
        '[data-landmark="ENGINEERING_DRAWER"] details[open], [data-market-phase-1a-secondary-instrument-details-v1="true"][open]'
      ));
      const order = [];
      for (const name of [
        'GLOBAL_HEADER','PRIMARY_MARKET_SURFACE','DECISION_SURFACE',
        'OBSERVABILITY_SURFACE','ENGINEERING_DRAWER'
      ]) {
        const el = document.querySelector('[data-landmark=\"' + name + '\"]');
        if (el) order.push({name, top: el.getBoundingClientRect().top});
      }
      order.sort((a,b) => a.top - b.top);
      const drawer = document.querySelector('[data-landmark=\"ENGINEERING_DRAWER\"]');
      const openDetails = drawer
        ? Array.from(drawer.querySelectorAll('details')).filter(d => d.hasAttribute('open'))
        : [];
      const chart = pick('[data-market-phase-1a-chart-above-fold-v1=\"true\"]')
        || pick('[data-market-foundation-primary-chart-v1=\"true\"]');
      const header = pick('[data-market-phase-1a-global-header-v1=\"true\"]') || pick('header');
      const narrative = pick('[data-market-operator-decision-narrative-v1=\"true\"]');
      const visibleH = chart
        ? Math.max(0, Math.min(chart.bottom, window.innerHeight) - Math.max(chart.top, 0))
        : 0;
      return {
        scrollWidth: doc.scrollWidth,
        clientWidth: doc.clientWidth,
        viewportHeight: window.innerHeight,
        viewportWidth: window.innerWidth,
        header,
        safety: pick('[data-market-phase-1a-single-safety-rail-v1=\"true\"]'),
        hero: pick('[data-market-phase1a-pre-chart-context-v1=\"true\"]') || pick('[data-market-phase-2-hero-v1=\"true\"]'),
        chart,
        decision_sentence: narrative,
        post_chart_decision: pick('[data-market-phase1a-post-chart-decision-v1=\"true\"]'),
        ranking: pick('[data-market-governed-top20-primary-slot-v1=\"true\"]'),
        decision_funnel: pick('[data-market-decision-funnel-visual-v1=\"true\"]'),
        economic: pick('[data-market-economic-observability-visual-v1=\"true\"]'),
        landmark_order: order.map(x => x.name),
        engineering_open_details_count: openDetails.length,
        LEVEL4_VISIBLE_ELEMENT_COUNT: level4Open.length,
        PROMINENT_HEADER_BADGE_COUNT: prominent.filter(b => {
          const r = b.getBoundingClientRect();
          return r.width > 0 && r.height > 0 && r.top < window.innerHeight;
        }).length,
        VISIBLE_STATUS_BADGE_COUNT: badges.filter(b => {
          const r = b.getBoundingClientRect();
          return r.width > 0 && r.height > 0 && r.top < window.innerHeight;
        }).length,
        PRIMARY_CHART_VISIBLE_HEIGHT_PX: visibleH,
        HORIZONTAL_OVERFLOW_PX: Math.max(0, doc.scrollWidth - doc.clientWidth),
        HEADER_HEIGHT_PX: header ? header.height : null,
        PRIMARY_CHART_TOP_Y: chart ? chart.top : null,
        DECISION_NARRATIVE_TOP_Y: narrative ? narrative.top : null
      };
    }"""


def capture(*, out_dir: Path, port: int | None = None) -> CaptureReport:
    from playwright.sync_api import sync_playwright

    scripts_webui = str(REPO_ROOT / "scripts" / "webui")
    if scripts_webui not in sys.path:
        sys.path.insert(0, scripts_webui)
    import market_dashboard_chrome_playwright_harness_v1 as chrome_helper  # type: ignore
    import review_server_playwright_webserver_v1 as pw_helper  # type: ignore

    out_dir.mkdir(parents=True, exist_ok=True)
    shots = out_dir / "screenshots"
    shots.mkdir(parents=True, exist_ok=True)

    state_dir = out_dir / ".run_state"
    server = pw_helper.ReviewServerWebServer(
        host="127.0.0.1",
        port=port if port is not None else pw_helper.find_free_localhost_port(),
        state_dir=state_dir,
        reuse_existing=False,
        start_timeout_seconds=90,
    )
    handle = server.start()
    report = CaptureReport(
        captured_at_utc=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        head_sha=_git_sha("HEAD"),
        origin_main_sha=_git_sha("origin/main"),
        base_url=handle.base_url,
        review_url=handle.review_url,
    )

    try:
        import urllib.request

        with urllib.request.urlopen(handle.review_url, timeout=10) as resp:  # noqa: S310
            report.HTTP_200 = int(getattr(resp, "status", 200)) == 200

        allowed_origin = f"{urlparse(handle.base_url).scheme}://{urlparse(handle.base_url).netloc}"
        with sync_playwright() as p:
            browser, launch = chrome_helper.launch_browser(p, headless=True)
            report.BROWSER_ACTUAL = launch.BROWSER_ACTUAL
            report.REAL_CHROME_VERIFIED = launch.REAL_CHROME_VERIFIED
            report.CHROMIUM_FALLBACK_USED = launch.CHROMIUM_FALLBACK_USED

            context = browser.new_context(
                viewport={"width": 1440, "height": 900}, device_scale_factor=1
            )
            page = context.new_page()

            def on_console(msg: Any) -> None:
                if msg.type == "error":
                    text = msg.text
                    if "favicon" in text.lower():
                        return
                    report.CONSOLE_ERRORS += 1
                    report.console_messages.append(text)

            def on_page_error(_exc: Any) -> None:
                report.PAGE_ERRORS += 1

            def on_request(request: Any) -> None:
                url = request.url
                if not _is_self_only(url, allowed_origin):
                    report.EXTERNAL_NETWORK_REQUESTS += 1
                    report.UNEXPECTED_NETWORK_REQUESTS += 1
                    report.external_requests.append(url)

            def on_response(response: Any) -> None:
                if response.status >= 400 and "favicon" not in response.url.lower():
                    report.FAILED_ASSETS += 1

            page.on("console", on_console)
            page.on("pageerror", on_page_error)
            page.on("request", on_request)
            page.on("response", on_response)

            page.goto(handle.review_url, wait_until="networkidle", timeout=90_000)
            page.wait_for_timeout(700)

            for w, h in VIEWPORTS:
                key = f"{w}x{h}"
                page.set_viewport_size({"width": w, "height": h})
                page.wait_for_timeout(300)
                geom = page.evaluate(_eval_geometry())
                report.viewports[key] = geom
                if key == "1440x900":
                    report.geometry_1440x900 = geom
                    report.landmark_order_observed = list(geom.get("landmark_order") or [])
                    report.landmark_order_pass = (
                        report.landmark_order_observed == EXPECTED_LANDMARKS
                    )
                    report.engineering_drawer_default_hidden = (
                        int(geom.get("engineering_open_details_count") or 0) == 0
                    )
                    chart_top = geom.get("PRIMARY_CHART_TOP_Y")
                    header_h = geom.get("HEADER_HEIGHT_PX")
                    narr_top = geom.get("DECISION_NARRATIVE_TOP_Y")
                    report.geometry_assertions = {
                        "HEADER_HEIGHT_PX_LE_64": header_h is not None and header_h <= 64,
                        "PRIMARY_CHART_TOP_Y_LT_900": chart_top is not None and chart_top < 900,
                        "PRIMARY_CHART_VISIBLE_HEIGHT_PX_GE_280": (
                            float(geom.get("PRIMARY_CHART_VISIBLE_HEIGHT_PX") or 0) >= 280
                        ),
                        "HORIZONTAL_OVERFLOW_PX_EQ_0": int(geom.get("HORIZONTAL_OVERFLOW_PX") or 0)
                        == 0,
                        "LEVEL4_VISIBLE_ELEMENT_COUNT_EQ_0": int(
                            geom.get("LEVEL4_VISIBLE_ELEMENT_COUNT") or 0
                        )
                        == 0,
                        "PROMINENT_HEADER_BADGE_COUNT_LE_3": int(
                            geom.get("PROMINENT_HEADER_BADGE_COUNT") or 0
                        )
                        <= 3,
                        "VISIBLE_STATUS_BADGE_COUNT_LE_8": int(
                            geom.get("VISIBLE_STATUS_BADGE_COUNT") or 0
                        )
                        <= 8,
                        "DECISION_AFTER_CHART": (
                            narr_top is not None and chart_top is not None and narr_top >= chart_top
                        ),
                        "LANDMARK_ORDER_PASS": report.landmark_order_pass,
                        "ENGINEERING_DRAWER_DEFAULT_HIDDEN": report.engineering_drawer_default_hidden,
                    }

                full = shots / f"phase1a_{key}_full.png"
                above = shots / f"phase1a_{key}_above_fold.png"
                page.screenshot(path=str(full), full_page=True)
                page.screenshot(path=str(above), full_page=False)
                report.screenshots.append(str(full.relative_to(out_dir)))
                report.screenshots.append(str(above.relative_to(out_dir)))

            page.set_viewport_size({"width": 1440, "height": 900})
            page.wait_for_timeout(200)

            hh = shots / "phase1a_1440x900_header_hero_chart.png"
            page.screenshot(path=str(hh), full_page=False)
            report.screenshots.append(str(hh.relative_to(out_dir)))

            closed = shots / "phase1a_engineering_drawer_closed.png"
            page.evaluate(
                """() => {
                  document.querySelectorAll('[data-landmark=\"ENGINEERING_DRAWER\"] details[open]')
                    .forEach(d => d.removeAttribute('open'));
                  const eng = document.querySelector('[data-landmark=\"ENGINEERING_DRAWER\"]');
                  if (eng) eng.scrollIntoView({block: 'start'});
                }"""
            )
            page.wait_for_timeout(200)
            page.screenshot(path=str(closed), full_page=False)
            report.screenshots.append(str(closed.relative_to(out_dir)))

            for name, sel in (
                (
                    "phase1a_primary_chart_detail.png",
                    '[data-market-phase-1a-chart-above-fold-v1="true"]',
                ),
                (
                    "phase1a_safety_rail_detail.png",
                    '[data-market-phase-1a-single-safety-rail-v1="true"]',
                ),
            ):
                loc = page.locator(sel).first
                path = shots / name
                if loc.count() > 0:
                    loc.screenshot(path=str(path))
                else:
                    page.screenshot(path=str(path), full_page=False)
                report.screenshots.append(str(path.relative_to(out_dir)))

            landmark = shots / "phase1a_landmark_full_page_composition.png"
            page.screenshot(path=str(landmark), full_page=True)
            report.screenshots.append(str(landmark.relative_to(out_dir)))

            page.evaluate(
                """() => {
                  const eng = document.querySelector('[data-landmark=\"ENGINEERING_DRAWER\"]');
                  if (eng) eng.scrollIntoView({block: 'start'});
                  const d = document.querySelector('[data-market-diagnostics-drawer-v1=\"true\"]');
                  if (d && d.tagName.toLowerCase() === 'details') d.setAttribute('open', '');
                }"""
            )
            page.wait_for_timeout(250)
            opened = shots / "phase1a_engineering_drawer_opened.png"
            page.screenshot(path=str(opened), full_page=False)
            report.screenshots.append(str(opened.relative_to(out_dir)))

            page.evaluate(
                """() => {
                  document.querySelectorAll('[data-landmark=\"ENGINEERING_DRAWER\"] details[open]')
                    .forEach(d => d.removeAttribute('open'));
                }"""
            )
            browser.close()
    finally:
        server.stop()

    return report


def main(argv: list[str] | None = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=REPO_ROOT / "artifacts" / "market_dashboard_phase1a_composition_foundation_v1",
    )
    parser.add_argument("--port", type=int, default=None)
    args = parser.parse_args(argv)
    report = capture(out_dir=args.out_dir, port=args.port)
    out = args.out_dir / "capture_raw.json"
    out.write_text(json.dumps(asdict(report), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(asdict(report), indent=2, sort_keys=True))
    asserts = report.geometry_assertions
    ok = (
        report.HTTP_200
        and report.EXTERNAL_NETWORK_REQUESTS == 0
        and report.UNEXPECTED_NETWORK_REQUESTS == 0
        and report.REAL_CHROME_VERIFIED
        and not report.CHROMIUM_FALLBACK_USED
        and report.CONSOLE_ERRORS == 0
        and all(bool(v) for v in asserts.values())
    )
    return 0 if ok else 2


if __name__ == "__main__":
    sys.exit(main())
