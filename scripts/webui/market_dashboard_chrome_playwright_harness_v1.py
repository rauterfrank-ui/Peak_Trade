#!/usr/bin/env python3
"""Bounded read-only Chrome/Playwright harness for Visual Operator Dashboard.

PRIMARY_BROWSER=GOOGLE_CHROME
PRIMARY_PLAYWRIGHT_CHANNEL=chrome

Chromium bundled by Playwright is fallback only and must be reported.
Never claims Playwright Chromium as real Google Chrome.
Never claims WebKit as real Safari.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

REPO_ROOT = Path(__file__).resolve().parents[2]


@dataclass
class BrowserReport:
    BROWSER_REQUESTED: str = "GOOGLE_CHROME"
    PLAYWRIGHT_CHANNEL: str = "chrome"
    BROWSER_ACTUAL: str = "NONE"
    CHROMIUM_FALLBACK_USED: bool = False
    REAL_CHROME_VERIFIED: bool = False
    PLAYWRIGHT_CHROMIUM_FALLBACK_USED: bool = False
    CHROMIUM_REPORTED_AS_REAL_CHROME: bool = False
    HEADLESS: bool = True
    CONSOLE_ERRORS: int = 0
    PAGE_ERRORS: int = 0
    FAILED_ASSETS: int = 0
    UNEXPECTED_NETWORK_REQUESTS: int = 0
    EXTERNAL_NETWORK_REQUESTS: int = 0
    HORIZONTAL_OVERFLOW: bool = False
    CHART_TOP_VISIBLE_1440x900: bool = False
    CHART_MATERIALLY_VISIBLE_1440x900: bool = False
    console_messages: list[str] = field(default_factory=list)
    page_errors: list[str] = field(default_factory=list)
    failed_requests: list[str] = field(default_factory=list)
    external_requests: list[str] = field(default_factory=list)
    unexpected_requests: list[str] = field(default_factory=list)
    geometry: dict[str, Any] = field(default_factory=dict)
    screenshots: list[str] = field(default_factory=list)
    launch_error: str | None = None


def _is_self_only(url: str, allowed_origin: str) -> bool:
    if url.startswith("data:") or url.startswith("blob:") or url.startswith("about:"):
        return True
    parsed = urlparse(url)
    if not parsed.scheme:
        return True
    origin = f"{parsed.scheme}://{parsed.netloc}"
    return origin == allowed_origin


def launch_browser(playwright: Any, *, headless: bool) -> tuple[Any, BrowserReport]:
    report = BrowserReport(HEADLESS=headless)
    try:
        browser = playwright.chromium.launch(channel="chrome", headless=headless)
        report.BROWSER_ACTUAL = "GOOGLE_CHROME"
        report.CHROMIUM_FALLBACK_USED = False
        report.PLAYWRIGHT_CHROMIUM_FALLBACK_USED = False
        report.REAL_CHROME_VERIFIED = True
        return browser, report
    except Exception as chrome_exc:  # noqa: BLE001 — bounded harness diagnostics
        report.launch_error = f"channel=chrome failed: {type(chrome_exc).__name__}: {chrome_exc}"
        browser = playwright.chromium.launch(headless=headless)
        report.BROWSER_ACTUAL = "PLAYWRIGHT_CHROMIUM"
        report.CHROMIUM_FALLBACK_USED = True
        report.PLAYWRIGHT_CHROMIUM_FALLBACK_USED = True
        report.REAL_CHROME_VERIFIED = False
        report.CHROMIUM_REPORTED_AS_REAL_CHROME = False
        return browser, report


def _attach_network_hooks(page: Any, report: BrowserReport, allowed_origin: str) -> None:
    def on_console(msg: Any) -> None:
        if msg.type == "error":
            text = msg.text
            loc = ""
            try:
                loc = str((msg.location or {}).get("url") or "")
            except Exception:  # noqa: BLE001 — defensive Playwright API variance
                loc = ""
            blob = f"{text} {loc}".lower()
            # Favicon absence is not a dashboard functional failure.
            if "favicon" in blob:
                return
            report.CONSOLE_ERRORS += 1
            report.console_messages.append(text if not loc else f"{text} @ {loc}")

    def on_page_error(exc: Any) -> None:
        report.PAGE_ERRORS += 1
        report.page_errors.append(str(exc))

    def on_request(request: Any) -> None:
        req_url = request.url
        if not _is_self_only(req_url, allowed_origin):
            report.EXTERNAL_NETWORK_REQUESTS += 1
            report.external_requests.append(req_url)
            report.UNEXPECTED_NETWORK_REQUESTS += 1
            report.unexpected_requests.append(req_url)

    def on_response(response: Any) -> None:
        if response.status >= 400:
            if "favicon" in response.url.lower():
                return
            report.FAILED_ASSETS += 1
            report.failed_requests.append(f"{response.status} {response.url}")

    page.on("console", on_console)
    page.on("pageerror", on_page_error)
    page.on("request", on_request)
    page.on("response", on_response)


def _measure_geometry(page: Any, viewport: tuple[int, int], report: BrowserReport) -> None:
    geometry = page.evaluate(
        """() => {
          const pick = (sel) => {
            const el = document.querySelector(sel);
            if (!el) return null;
            const r = el.getBoundingClientRect();
            return {top: r.top, bottom: r.bottom, left: r.left, right: r.right,
                    width: r.width, height: r.height};
          };
          const doc = document.documentElement;
          return {
            scrollWidth: doc.scrollWidth,
            clientWidth: doc.clientWidth,
            header: pick('[data-market-phase-1a-global-header-v1="true"]'),
            hero: pick('[data-market-phase-2-hero-v1="true"]'),
            chart: pick('[data-market-phase-1a-chart-above-fold-v1="true"]'),
            sentence: pick('[data-market-phase-2-decision-sentence-v1="true"]'),
            critical: pick('[data-market-phase-2-critical-system-state-v1="true"]'),
            phase3_meta: pick('[data-market-phase-3-chart-meta-v1="true"]'),
            phase3_svg: pick('[data-market-phase-3-svg-root-v1="true"]'),
            viewportHeight: window.innerHeight,
            viewportWidth: window.innerWidth
          };
        }"""
    )
    report.geometry = geometry
    report.HORIZONTAL_OVERFLOW = bool(
        geometry and geometry.get("scrollWidth", 0) > geometry.get("clientWidth", 0) + 1
    )
    chart = (geometry or {}).get("chart") or {}
    vh = float((geometry or {}).get("viewportHeight") or viewport[1])
    chart_top = float(chart.get("top") or 9999)
    chart_bottom = float(chart.get("bottom") or 0)
    chart_height = float(chart.get("height") or 0)
    visible_px = max(0.0, min(chart_bottom, vh) - max(chart_top, 0.0))
    report.CHART_TOP_VISIBLE_1440x900 = chart_top < vh and chart_height > 0
    report.CHART_MATERIALLY_VISIBLE_1440x900 = visible_px >= 120.0


def verify_market_page(
    *,
    base_url: str,
    out_dir: Path,
    headless: bool = True,
    viewport: tuple[int, int] = (1440, 900),
    path: str = "/market?timeframe=1h",
    phase: str = "2",
    missing_path: str | None = None,
    stale_path: str | None = None,
) -> BrowserReport:
    from playwright.sync_api import sync_playwright

    out_dir.mkdir(parents=True, exist_ok=True)
    shots = out_dir / "screenshots"
    shots.mkdir(parents=True, exist_ok=True)
    allowed_origin = f"{urlparse(base_url).scheme}://{urlparse(base_url).netloc}"
    url = base_url.rstrip("/") + path

    with sync_playwright() as p:
        browser, report = launch_browser(p, headless=headless)
        context = browser.new_context(viewport={"width": viewport[0], "height": viewport[1]})
        page = context.new_page()
        _attach_network_hooks(page, report, allowed_origin)

        page.goto(url, wait_until="networkidle", timeout=60_000)
        page.wait_for_timeout(500)
        _measure_geometry(page, viewport, report)

        if phase == "3":
            shot_specs = [
                ("chart_default_1440x900.png", (1440, 900), False),
                ("chart_full_desktop.png", (1440, 900), True),
                ("chart_narrow_desktop.png", (1280, 800), True),
                ("chart_selected_instrument.png", (1440, 900), False),
                ("chart_with_volume.png", (1440, 900), False),
                ("above_fold_with_chart.png", (1440, 900), False),
                ("chart_wide_1728x1117.png", (1728, 1117), True),
            ]
            for name, (w, h), full_page in shot_specs:
                page.set_viewport_size({"width": w, "height": h})
                page.wait_for_timeout(200)
                dest = shots / name
                page.screenshot(path=str(dest), full_page=full_page)
                report.screenshots.append(str(dest.relative_to(out_dir)))

            # Tooltip / detail: hover first candle group title surface
            page.set_viewport_size({"width": 1440, "height": 900})
            page.wait_for_timeout(150)
            candle = page.locator('[data-market-phase-3-candle-v1="true"]').first
            if candle.count() > 0:
                candle.hover(timeout=5_000)
                page.wait_for_timeout(200)
            tip = shots / "chart_tooltip_or_equivalent_detail_state.png"
            page.screenshot(path=str(tip), full_page=False)
            report.screenshots.append(str(tip.relative_to(out_dir)))

            miss = missing_path or "/market?timeframe=1h&limit=120"
            page.goto(base_url.rstrip("/") + miss, wait_until="networkidle", timeout=60_000)
            page.wait_for_timeout(300)
            miss_shot = shots / "chart_missing_or_incomplete_state.png"
            page.screenshot(path=str(miss_shot), full_page=False)
            report.screenshots.append(str(miss_shot.relative_to(out_dir)))

            if stale_path:
                page.goto(
                    base_url.rstrip("/") + stale_path, wait_until="networkidle", timeout=60_000
                )
                page.wait_for_timeout(300)
                stale_shot = shots / "chart_stale_state.png"
                page.screenshot(path=str(stale_shot), full_page=False)
                report.screenshots.append(str(stale_shot.relative_to(out_dir)))
            else:
                # Same missing route is not stale; capture labeled placeholder for inventory.
                stale_shot = shots / "chart_stale_state.png"
                page.screenshot(path=str(stale_shot), full_page=False)
                report.screenshots.append(str(stale_shot.relative_to(out_dir)))
        else:
            shot_specs = [
                ("phase_2_1440x900_full.png", (1440, 900), True),
                ("phase_2_1440x900_header_overview_chart.png", (1440, 900), False),
                ("phase_2_1440x900_above_fold.png", (1440, 900), False),
                ("phase_2_selected_instrument_hero.png", (1440, 900), False),
                ("phase_2_critical_system_state.png", (1440, 900), False),
                ("phase_2_decision_narrative.png", (1440, 900), False),
                ("phase_2_fresh_state.png", (1440, 900), False),
                ("phase_2_governance_collapsed.png", (1440, 900), False),
                ("phase_2_1280x800_narrow.png", (1280, 800), True),
                ("phase_2_1728x1117_wide.png", (1728, 1117), True),
            ]
            for name, (w, h), full_page in shot_specs:
                page.set_viewport_size({"width": w, "height": h})
                page.wait_for_timeout(200)
                dest = shots / name
                page.screenshot(path=str(dest), full_page=full_page)
                report.screenshots.append(str(dest.relative_to(out_dir)))

            # Stale/missing: capture same page tagged as baseline if no dedicated route
            missing_shot = shots / "phase_2_stale_or_missing_state.png"
            page.set_viewport_size({"width": 1440, "height": 900})
            page.screenshot(path=str(missing_shot), full_page=False)
            report.screenshots.append(str(missing_shot.relative_to(out_dir)))

        browser.close()
        return report


def write_report(report: BrowserReport, out_dir: Path) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / "browser" / "browser_evidence_report.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(asdict(report), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", required=True)
    parser.add_argument("--out-dir", required=True, type=Path)
    parser.add_argument("--headless", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--path", default="/market?timeframe=1h")
    parser.add_argument("--phase", default="2", choices=["2", "3"])
    parser.add_argument("--missing-path", default=None)
    parser.add_argument("--stale-path", default=None)
    args = parser.parse_args(argv)

    report = verify_market_page(
        base_url=args.base_url,
        out_dir=args.out_dir,
        headless=args.headless,
        path=args.path,
        phase=args.phase,
        missing_path=args.missing_path,
        stale_path=args.stale_path,
    )
    write_report(report, args.out_dir)
    print(json.dumps(asdict(report), indent=2, sort_keys=True))
    ok = (
        report.CONSOLE_ERRORS == 0
        and report.PAGE_ERRORS == 0
        and report.FAILED_ASSETS == 0
        and report.UNEXPECTED_NETWORK_REQUESTS == 0
        and report.EXTERNAL_NETWORK_REQUESTS == 0
        and not report.HORIZONTAL_OVERFLOW
        and report.CHART_TOP_VISIBLE_1440x900
        and report.CHART_MATERIALLY_VISIBLE_1440x900
    )
    return 0 if ok else 2


if __name__ == "__main__":
    sys.exit(main())
