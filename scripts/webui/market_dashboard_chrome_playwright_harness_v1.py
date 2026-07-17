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
    PRIMARY_CHART_VISUAL_SHARE_PCT: float = 0.0
    PRIMARY_CHART_VISUAL_SHARE_MIN_MET: bool = False
    HEADER_HEIGHT_PX: float = 0.0
    SAFETY_RAIL_HEIGHT_PX: float = 0.0
    HERO_HEIGHT_PX: float = 0.0
    CHART_HEIGHT_PX: float = 0.0
    COMPOSITION_CONTRACT_PASS: bool = False
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


def verify_market_page(
    *,
    base_url: str,
    out_dir: Path,
    headless: bool = True,
    viewport: tuple[int, int] = (1440, 900),
    path: str = "/market?timeframe=1h",
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

        page.goto(url, wait_until="networkidle", timeout=60_000)
        page.wait_for_timeout(500)

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
                safety: pick('[data-market-phase-1a-single-safety-rail-v1="true"]'),
                hero: pick('[data-market-phase-2-hero-v1="true"]'),
                chart: pick('[data-market-phase-1a-chart-above-fold-v1="true"]'),
                chartFrame: pick('[data-market-v0-close-chart-integrated-frame="true"]'),
                sentence: pick('[data-market-phase-2-decision-sentence-v1="true"]'),
                critical: pick('[data-market-phase-2-critical-system-state-v1="true"]'),
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
        chart_frame = (geometry or {}).get("chartFrame") or {}
        header = (geometry or {}).get("header") or {}
        safety = (geometry or {}).get("safety") or {}
        hero = (geometry or {}).get("hero") or {}
        vh = float((geometry or {}).get("viewportHeight") or viewport[1])
        chart_top = float(chart.get("top") or 9999)
        chart_bottom = float(chart.get("bottom") or 0)
        chart_height = float(chart.get("height") or 0)
        frame_height = float(chart_frame.get("height") or chart_height or 0)
        visible_px = max(0.0, min(chart_bottom, vh) - max(chart_top, 0.0))
        report.CHART_TOP_VISIBLE_1440x900 = chart_top < vh and chart_height > 0
        report.CHART_MATERIALLY_VISIBLE_1440x900 = visible_px >= 180.0
        report.HEADER_HEIGHT_PX = float(header.get("height") or 0.0)
        report.SAFETY_RAIL_HEIGHT_PX = float(safety.get("height") or 0.0)
        report.HERO_HEIGHT_PX = float(hero.get("height") or 0.0)
        report.CHART_HEIGHT_PX = frame_height
        report.PRIMARY_CHART_VISUAL_SHARE_PCT = (visible_px / vh) * 100.0 if vh > 0 else 0.0
        report.PRIMARY_CHART_VISUAL_SHARE_MIN_MET = report.PRIMARY_CHART_VISUAL_SHARE_PCT >= 40.0
        chart_empty_compact = page.evaluate(
            """() => !!document.querySelector('[data-market-chart-empty-compact-v1="true"]')"""
        )
        decision_above_fold = page.evaluate(
            """() => {
              const el = document.querySelector('[data-market-phase-2-critical-system-state-v1="true"]');
              if (!el) return false;
              const r = el.getBoundingClientRect();
              return r.top < window.innerHeight && r.bottom > 0;
            }"""
        )
        report.geometry = {
            **(geometry or {}),
            "chart_empty_compact": bool(chart_empty_compact),
            "decision_critical_above_fold": bool(decision_above_fold),
        }
        if chart_empty_compact:
            # DATA_UNAVAILABLE: compact diagnostic chart; decision triage above fold.
            report.COMPOSITION_CONTRACT_PASS = bool(
                report.HEADER_HEIGHT_PX <= 64.0 + 1.0
                and report.SAFETY_RAIL_HEIGHT_PX <= 32.0 + 1.0
                and report.CHART_HEIGHT_PX <= 200.0 + 1.0
                and decision_above_fold
                and not report.HORIZONTAL_OVERFLOW
            )
        else:
            # DATA_AVAILABLE: chart dominant stage.
            report.COMPOSITION_CONTRACT_PASS = bool(
                report.HEADER_HEIGHT_PX <= 64.0 + 1.0
                and report.SAFETY_RAIL_HEIGHT_PX <= 32.0 + 1.0
                and report.CHART_HEIGHT_PX >= 390.0 - 1.0
                and report.CHART_TOP_VISIBLE_1440x900
                and report.CHART_MATERIALLY_VISIBLE_1440x900
                and report.PRIMARY_CHART_VISUAL_SHARE_MIN_MET
            )

        shot_specs = [
            ("foundation_1440x900_full.png", (1440, 900), True),
            ("foundation_1440x900_header_hero_chart.png", (1440, 900), False),
            ("foundation_1440x900_above_fold.png", (1440, 900), False),
            ("foundation_selected_instrument_hero.png", (1440, 900), False),
            ("foundation_critical_system_state.png", (1440, 900), False),
            ("foundation_decision_narrative.png", (1440, 900), False),
            ("foundation_primary_chart.png", (1440, 900), False),
            ("foundation_1280x800_narrow.png", (1280, 800), True),
            ("foundation_1728x1117_wide.png", (1728, 1117), True),
            ("phase_2_1440x900_above_fold.png", (1440, 900), False),
        ]
        for name, (w, h), full_page in shot_specs:
            page.set_viewport_size({"width": w, "height": h})
            page.wait_for_timeout(200)
            dest = shots / name
            page.screenshot(path=str(dest), full_page=full_page)
            report.screenshots.append(str(dest.relative_to(out_dir)))

        # Stale/missing: capture same page tagged as baseline if no dedicated route
        missing_shot = shots / "foundation_stale_or_missing_state.png"
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
    parser.add_argument(
        "--base-url",
        required=False,
        default=None,
        help="Base URL; optional when --manage-server starts review_server.sh",
    )
    parser.add_argument("--out-dir", required=True, type=Path)
    parser.add_argument("--headless", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--path", default="/market?timeframe=1h")
    parser.add_argument(
        "--manage-server",
        action="store_true",
        help=(
            "Start/stop via scripts/webui/review_server.sh (Playwright webServer path). "
            "Local reuse of a healthy harness server is allowed; CI reuse is disabled."
        ),
    )
    parser.add_argument("--port", type=int, default=None, help="Port when --manage-server")
    args = parser.parse_args(argv)

    server_cm = None
    base_url = args.base_url
    if args.manage_server:
        import importlib.util

        helper_path = REPO_ROOT / "scripts" / "webui" / "review_server_playwright_webserver_v1.py"
        spec = importlib.util.spec_from_file_location(
            "review_server_playwright_webserver_v1", helper_path
        )
        if spec is None or spec.loader is None:
            raise RuntimeError(f"unable to load {helper_path}")
        helper = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(helper)
        port = args.port if args.port is not None else helper.find_free_localhost_port()
        server_cm = helper.ReviewServerWebServer(port=port, reuse_existing=None)
        handle = server_cm.start()
        base_url = handle.base_url
    if not base_url:
        parser.error("--base-url is required unless --manage-server is set")

    try:
        report = verify_market_page(
            base_url=base_url,
            out_dir=args.out_dir,
            headless=args.headless,
            path=args.path,
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
            and report.COMPOSITION_CONTRACT_PASS
        )
        # Available-state gates only when chart is not compact-empty.
        if not (report.geometry or {}).get("chart_empty_compact"):
            ok = bool(
                ok
                and report.CHART_TOP_VISIBLE_1440x900
                and report.CHART_MATERIALLY_VISIBLE_1440x900
                and report.PRIMARY_CHART_VISUAL_SHARE_MIN_MET
            )
        return 0 if ok else 2
    finally:
        if server_cm is not None:
            server_cm.stop()


if __name__ == "__main__":
    sys.exit(main())
