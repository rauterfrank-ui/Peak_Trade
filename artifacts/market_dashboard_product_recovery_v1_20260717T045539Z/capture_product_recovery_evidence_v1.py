#!/usr/bin/env python3
"""One-off product recovery v1 Chrome evidence (real Google Chrome only)."""

from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

REPO = Path(__file__).resolve().parents[2]
EV = Path(__file__).resolve().parent
SHOTS = EV / "screenshots"
REVIEW_SH = REPO / "scripts" / "webui" / "review_server.sh"
PATH = "/market?timeframe=1h"


def run_review(cmd: str, *, bind_fixtures: bool = False) -> str:
    env = {**dict(**{k: v for k, v in __import__("os").environ.items()}), "PEAK_TRADE_WEBUI_REVIEW_BIND_FIXTURES": "1" if bind_fixtures else "0"}
    proc = subprocess.run(
        [str(REVIEW_SH), cmd],
        cwd=REPO,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    out = (proc.stdout or "") + (proc.stderr or "")
    if proc.returncode != 0 and cmd not in ("status", "stop"):
        raise RuntimeError(f"review_server {cmd} failed rc={proc.returncode}\n{out}")
    return out


def parse_status(blob: str) -> dict[str, str]:
    d: dict[str, str] = {}
    for line in blob.splitlines():
        if "=" in line:
            k, v = line.split("=", 1)
            d[k.strip()] = v.strip()
    return d


def launch_chrome_report(base_url: str, *, headless: bool = True) -> dict[str, Any]:
    from playwright.sync_api import sync_playwright

    allowed = f"{urlparse(base_url).scheme}://{urlparse(base_url).netloc}"
    url = base_url.rstrip("/") + PATH
    console_errors: list[str] = []
    network_errors: list[str] = []

    with sync_playwright() as p:
        try:
            browser = p.chromium.launch(channel="chrome", headless=headless)
            browser_actual = "GOOGLE_CHROME"
            chromium_fallback = False
        except Exception as exc:  # noqa: BLE001
            raise RuntimeError(f"REAL Google Chrome required; channel=chrome failed: {exc}") from exc

        context = browser.new_context()
        page = context.new_page()

        def on_console(msg: Any) -> None:
            if msg.type == "error":
                t = msg.text
                if "favicon" in t.lower():
                    return
                console_errors.append(t)

        def on_response(resp: Any) -> None:
            if resp.status >= 400 and "favicon" not in resp.url.lower():
                network_errors.append(f"{resp.status} {resp.url}")

        page.on("console", on_console)
        page.on("response", on_response)
        page.goto(url, wait_until="networkidle", timeout=90_000)
        page.wait_for_timeout(400)

        metrics_by_vp: dict[str, Any] = {}

        def capture_viewport(name: str, w: int, h: int, filename: str, *, full_page: bool) -> None:
            page.set_viewport_size({"width": w, "height": h})
            page.wait_for_timeout(250)
            dest = SHOTS / filename
            page.screenshot(path=str(dest), full_page=full_page)
            geom = page.evaluate(
                """() => {
                  const q = (s) => { const el = document.querySelector(s); if (!el) return null;
                    const r = el.getBoundingClientRect();
                    return {top:r.top,bottom:r.bottom,left:r.left,right:r.right,width:r.width,height:r.height}; };
                  return {
                    viewportWidth: window.innerWidth,
                    viewportHeight: window.innerHeight,
                    scrollWidth: document.documentElement.scrollWidth,
                    clientWidth: document.documentElement.clientWidth,
                    chartEmpty: !!document.querySelector('[data-market-chart-empty-compact-v1="true"]'),
                    header: q('[data-market-phase-1a-global-header-v1="true"]'),
                    chart: q('[data-market-phase-1a-chart-above-fold-v1="true"]'),
                    decision: q('[data-market-phase-2-critical-system-state-v1="true"]'),
                  };
                }"""
            )
            metrics_by_vp[name] = geom

        capture_viewport("1280x800", 1280, 800, "unavailable_1280x800_full.png", full_page=True)
        capture_viewport("1440x900_above", 1440, 900, "unavailable_1440x900_above_fold.png", full_page=False)
        capture_viewport("1440x900_full", 1440, 900, "unavailable_1440x900_full.png", full_page=True)
        capture_viewport("1728x1117", 1728, 1117, "unavailable_1728x1117_full.png", full_page=True)

        page.set_viewport_size({"width": 1440, "height": 900})
        page.wait_for_timeout(200)

        def clip_region(selector: str, out_name: str) -> None:
            el = page.query_selector(selector)
            if not el:
                page.screenshot(path=str(SHOTS / out_name), full_page=False)
                return
            box = el.bounding_box()
            if not box:
                page.screenshot(path=str(SHOTS / out_name), full_page=False)
                return
            page.screenshot(path=str(SHOTS / out_name), clip=box)

        clip_region('[data-market-phase-2-critical-system-state-v1="true"]', "decision_region.png")
        clip_region('[data-market-double-play-safety-region-v1="true"], [data-market-safety-compact-v1="true"]', "double_play_safety_region.png")
        clip_region('[data-market-economic-observability-visual-v1="true"]', "observability_region.png")

        bars_present = page.evaluate(
            """() => {
              const empty = document.querySelector('[data-market-chart-empty-compact-v1="true"]');
              const canvas = document.querySelector('[data-market-v0-close-chart-integrated-frame="true"] canvas, canvas[data-market-chart-canvas-v1="true"]');
              return !empty && !!canvas;
            }"""
        )

        browser.close()
        return {
            "BROWSER_ACTUAL": browser_actual,
            "CHROMIUM_FALLBACK_USED": chromium_fallback,
            "REAL_CHROME_VERIFIED": True,
            "base_url": base_url,
            "console_errors": console_errors,
            "network_errors": network_errors,
            "viewport_metrics": metrics_by_vp,
            "bars_present": bool(bars_present),
            "allowed_origin": allowed,
        }


def capture_available_prefix(report: dict[str, Any], *, prefix: str = "available") -> None:
    from playwright.sync_api import sync_playwright

    base_url = report["base_url"]
    url = base_url.rstrip("/") + PATH
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="chrome", headless=True)
        context = browser.new_context()
        page = context.new_page()
        page.goto(url, wait_until="networkidle", timeout=90_000)
        specs = [
            (f"{prefix}_1280x800_full.png", 1280, 800, True),
            (f"{prefix}_1440x900_above_fold.png", 1440, 900, False),
            (f"{prefix}_1440x900_full.png", 1440, 900, True),
            (f"{prefix}_1728x1117_full.png", 1728, 1117, True),
        ]
        for name, w, h, full in specs:
            page.set_viewport_size({"width": w, "height": h})
            page.wait_for_timeout(250)
            page.screenshot(path=str(SHOTS / name), full_page=full)
        browser.close()


def main() -> int:
    SHOTS.mkdir(parents=True, exist_ok=True)
    notes: list[str] = []
    test_results: list[str] = []

    status_out = run_review("status")
    st = parse_status(status_out)
    test_results.append(f"initial_status={st.get('STATUS', 'UNKNOWN')}")
    if st.get("ACTION") == "ADOPTED_IDENTITY_OK_LISTENER":
        notes.append("Adopted identity-ok orphan on status.")

    def ensure_unavailable_server() -> dict[str, str]:
        blob = run_review("status")
        s = parse_status(blob)
        if s.get("STATUS") == "RUNNING_HEALTHY":
            stop_blob = run_review("stop")
            if "refuse to stop" in stop_blob.lower() or "ERROR" in stop_blob:
                notes.append(f"unavailable: could not stop owned server: {stop_blob.strip()[:300]}")
            else:
                time.sleep(0.5)
        run_review("start", bind_fixtures=False)
        time.sleep(1.2)
        return parse_status(run_review("status"))

    st = ensure_unavailable_server()

    base_url = st.get("REVIEW_URL") or "http://127.0.0.1:8000"
    test_results.append(f"unavailable_server_status={st.get('STATUS')}")

    report = launch_chrome_report(base_url)
    (EV / "viewport_metrics.json").write_text(json.dumps(report["viewport_metrics"], indent=2) + "\n", encoding="utf-8")
    (EV / "console_errors.json").write_text(json.dumps(report["console_errors"], indent=2) + "\n", encoding="utf-8")
    (EV / "network_errors.json").write_text(json.dumps(report["network_errors"], indent=2) + "\n", encoding="utf-8")

    # AVAILABLE attempt: stop only if owned, then fixture start
    available_note = "AVAILABLE_CAPTURE=SKIPPED"
    stop_out = run_review("stop")
    if "refuse to stop" in stop_out.lower() or "ERROR: refuse" in stop_out:
        available_note = "AVAILABLE_CAPTURE=SKIPPED_STOP_OWNERSHIP_UNCLEAR"
        notes.append(f"stop output: {stop_out.strip()[:500]}")
    else:
        try:
            run_review("start", bind_fixtures=True)
            time.sleep(1.5)
            st2 = parse_status(run_review("status"))
            base2 = st2.get("REVIEW_URL") or base_url
            rep2 = launch_chrome_report(base2)
            if rep2.get("bars_present"):
                capture_available_prefix(rep2)
                available_note = "AVAILABLE_CAPTURE=OK"
            else:
                available_note = "AVAILABLE_CAPTURE=SKIPPED_NO_BARS"
                notes.append("Fixtures bound but chart still compact-empty.")
        except Exception as exc:  # noqa: BLE001
            available_note = f"AVAILABLE_CAPTURE=FAILED:{type(exc).__name__}"
            notes.append(str(exc))

    test_results.append(available_note)
    test_results.append(f"REAL_CHROME_VERIFIED={report['REAL_CHROME_VERIFIED']}")
    test_results.append(f"BROWSER_ACTUAL={report['BROWSER_ACTUAL']}")
    (EV / "test_results.txt").write_text("\n".join(test_results) + "\n", encoding="utf-8")

    if notes:
        ba = (EV / "before_after.md").read_text(encoding="utf-8")
        ba += "\n\n## Evidence capture notes\n\n" + "\n".join(f"- {n}" for n in notes) + "\n"
        (EV / "before_after.md").write_text(ba, encoding="utf-8")

    return 0


if __name__ == "__main__":
    sys.exit(main())
