"""Bounded TASK_8 Real Chrome Playwright measurement — evidence-only."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from fastapi.testclient import TestClient
from playwright.sync_api import sync_playwright

from src.webui.app import create_app

REPO = Path(__file__).resolve().parents[4]
EVIDENCE = Path(__file__).resolve().parent

VIEWPORTS = (
    (1512, 982, "chrome_metrics_1512x982.json"),
    (1920, 1080, "chrome_metrics_1920x1080.json"),
)

RUNS_PER_VIEWPORT = 3


def _collect_html() -> str:
    client = TestClient(create_app())
    response = client.get("/market")
    assert response.status_code == 200
    return response.text


def _measure_once(page, html: str, width: int, height: int) -> dict:
    console_errors: list[str] = []
    page_errors: list[str] = []
    failed_requests: list[str] = []
    request_urls: list[str] = []
    transferred = {"bytes": 0}

    page.on(
        "console",
        lambda msg: (
            console_errors.append(f"{msg.type}:{msg.text}")
            if msg.type == "error"
            else None
        ),
    )
    page.on("pageerror", lambda exc: page_errors.append(str(exc)))

    def _on_request(request) -> None:  # type: ignore[no-untyped-def]
        request_urls.append(request.url)

    def _on_response(response) -> None:  # type: ignore[no-untyped-def]
        try:
            body = response.body()
            transferred["bytes"] += len(body)
        except Exception:
            pass

    def _on_fail(request) -> None:  # type: ignore[no-untyped-def]
        failed_requests.append(f"{request.failure}:{request.url}")

    page.on("request", _on_request)
    page.on("response", _on_response)
    page.on("requestfailed", _on_fail)

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
                route.fulfill(status=200, content_type=ctype, body=path.read_bytes())
                return
        route.fulfill(status=404, body=b"missing")

    page.route("**/*", _handler)

    # Enable performance observers before navigation where possible
    page.add_init_script(
        """
        window.__pt_perf = { longTasks: [], cls: 0, lcp: null, fcp: null };
        try {
          new PerformanceObserver((list) => {
            for (const e of list.getEntries()) {
              window.__pt_perf.longTasks.push({name: e.name, duration: e.duration, startTime: e.startTime});
            }
          }).observe({type: 'longtask', buffered: true});
        } catch (e) {}
        try {
          new PerformanceObserver((list) => {
            for (const e of list.getEntries()) {
              if (e.hadRecentInput) continue;
              window.__pt_perf.cls += e.value;
            }
          }).observe({type: 'layout-shift', buffered: true});
        } catch (e) {}
        try {
          new PerformanceObserver((list) => {
            const entries = list.getEntries();
            const last = entries[entries.length - 1];
            if (last) window.__pt_perf.lcp = last.startTime;
          }).observe({type: 'largest-contentful-paint', buffered: true});
        } catch (e) {}
        try {
          new PerformanceObserver((list) => {
            for (const e of list.getEntries()) {
              if (e.name === 'first-contentful-paint') window.__pt_perf.fcp = e.startTime;
            }
          }).observe({type: 'paint', buffered: true});
        } catch (e) {}
        """
    )

    page.goto("http://127.0.0.1:8765/market", wait_until="load")
    page.wait_for_timeout(500)  # allow LCP/CLS observers to settle (local, bounded)

    timing = page.evaluate(
        """() => {
          const nav = performance.getEntriesByType('navigation')[0];
          const paints = performance.getEntriesByType('paint');
          const fcpPaint = paints.find(p => p.name === 'first-contentful-paint');
          const perf = window.__pt_perf || {};
          const workspace = document.querySelector('[data-mdl-workspace="true"]');
          const chart = document.querySelector('[data-mdl-region="PRIMARY_CHART_STAGE"], [data-mdl-chart], .mdl-v2-chart, [data-mdl-field="chart"]');
          const chartStage = document.querySelector('[data-mdl-region="PRIMARY_CHART_WORKSPACE"], [data-mdl-region="CHART_STAGE"], .mdl-v2-stage, [data-mdl-region="PRIMARY_WORKSPACE"]');
          // Prefer primary chart container used by landscape v2
          const chartCandidates = [
            document.querySelector('[data-mdl-region="PRIMARY_CHART"]'),
            document.querySelector('.mdl-v2-chart-stage'),
            document.querySelector('[data-mdl-chart-stage]'),
            document.querySelector('.mdl-v2-stage'),
          ].filter(Boolean);
          const chartEl = chartCandidates[0] || chart || chartStage;
          const root = document.querySelector('[data-market-landscape-v2="true"]');
          const overflowX = document.documentElement.scrollWidth > document.documentElement.clientWidth + 1
            || document.body.scrollWidth > document.body.clientWidth + 1
            || (root ? root.scrollWidth > root.clientWidth + 1 : false);
          return {
            domContentLoaded_ms: nav ? nav.domContentLoadedEventEnd : null,
            loadEvent_ms: nav ? nav.loadEventEnd : null,
            responseStart_ms: nav ? nav.responseStart : null,
            fcp_ms: perf.fcp != null ? perf.fcp : (fcpPaint ? fcpPaint.startTime : null),
            lcp_ms: perf.lcp,
            cls: perf.cls,
            long_task_count: (perf.longTasks || []).length,
            long_tasks: perf.longTasks || [],
            dom_node_count: document.getElementsByTagName('*').length,
            primary_workspace_visible: !!(workspace && workspace.offsetParent !== null && workspace.getBoundingClientRect().height > 0),
            chart_container_present: !!chartEl,
            chart_container_non_empty: !!(chartEl && ((chartEl.textContent || '').trim().length > 0 || chartEl.children.length > 0)),
            no_horizontal_overflow: !overflowX,
            document_scroll_width: document.documentElement.scrollWidth,
            document_client_width: document.documentElement.clientWidth,
          };
        }"""
    )

    return {
        "viewport": {"width": width, "height": height},
        "timing": timing,
        "request_count": len(request_urls),
        "request_urls": request_urls,
        "transferred_bytes_fulfilled": transferred["bytes"],
        "console_errors": console_errors,
        "page_errors": page_errors,
        "failed_network_requests": failed_requests,
    }


def main() -> None:
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    html = _collect_html()
    console_all: list[str] = []
    page_err_all: list[str] = []
    failed_all: list[str] = []

    with sync_playwright() as p:
        try:
            browser = p.chromium.launch(channel="chrome", headless=True)
            channel = "chrome"
            browser_version = browser.version
        except Exception as exc:
            browser = p.chromium.launch(headless=True)
            channel = f"chromium_fallback:{exc}"
            browser_version = browser.version

        try:
            for width, height, out_name in VIEWPORTS:
                runs = []
                for run_i in range(RUNS_PER_VIEWPORT):
                    ctx = browser.new_context(
                        viewport={"width": width, "height": height},
                        bypass_csp=True,
                    )
                    # disable cache explicitly via CDP when available
                    page = ctx.new_page()
                    try:
                        cdp = ctx.new_cdp_session(page)
                        cdp.send("Network.enable")
                        cdp.send("Network.setCacheDisabled", {"cacheDisabled": True})
                    except Exception:
                        pass
                    result = _measure_once(page, html, width, height)
                    result["run_index"] = run_i
                    runs.append(result)
                    console_all.extend(result["console_errors"])
                    page_err_all.extend(result["page_errors"])
                    failed_all.extend(result["failed_network_requests"])
                    ctx.close()

                # aggregate last run as primary + all runs summary
                def _vals(key: str):
                    out = []
                    for r in runs:
                        v = r["timing"].get(key)
                        if v is not None:
                            out.append(v)
                    return out

                agg = {
                    "timestamp_utc": stamp,
                    "git_sha_note": "filled_by_wrapper",
                    "browser_channel": channel,
                    "browser_version": browser_version,
                    "viewport": {"width": width, "height": height},
                    "cache_mode": "disabled_via_cdp_Network.setCacheDisabled_when_available",
                    "run_count": RUNS_PER_VIEWPORT,
                    "harness": "playwright_sync_chrome_route_fulfill_static_and_html",
                    "measurement_environment": "localhost_controlled_route_fulfill_not_production_network",
                    "limitations": [
                        "Route-fulfill serves local HTML+static; not real TCP to review server",
                        "Canonical review_server.sh may be STALE_PID; not auto-repaired",
                        "Localhost only; not laboratory-grade or production-network performance",
                        "Transferred bytes are fulfilled body sizes, not wire/compressed transfer",
                        "LCP/CLS/longtask exposure depends on Chromium PerformanceObserver support",
                    ],
                    "runs": runs,
                    "aggregate": {
                        "domContentLoaded_ms_median": sorted(_vals("domContentLoaded_ms"))[
                            len(_vals("domContentLoaded_ms")) // 2
                        ]
                        if _vals("domContentLoaded_ms")
                        else None,
                        "loadEvent_ms_median": sorted(_vals("loadEvent_ms"))[
                            len(_vals("loadEvent_ms")) // 2
                        ]
                        if _vals("loadEvent_ms")
                        else None,
                        "fcp_ms_median": sorted(_vals("fcp_ms"))[len(_vals("fcp_ms")) // 2]
                        if _vals("fcp_ms")
                        else None,
                        "lcp_ms_median": sorted(_vals("lcp_ms"))[len(_vals("lcp_ms")) // 2]
                        if _vals("lcp_ms")
                        else None,
                        "cls_median": sorted(_vals("cls"))[len(_vals("cls")) // 2]
                        if _vals("cls")
                        else None,
                        "long_task_count_median": sorted(_vals("long_task_count"))[
                            len(_vals("long_task_count")) // 2
                        ]
                        if _vals("long_task_count")
                        else None,
                        "dom_node_count_last": runs[-1]["timing"]["dom_node_count"],
                        "request_count_last": runs[-1]["request_count"],
                        "transferred_bytes_last": runs[-1]["transferred_bytes_fulfilled"],
                        "primary_workspace_visible": runs[-1]["timing"][
                            "primary_workspace_visible"
                        ],
                        "chart_container_non_empty": runs[-1]["timing"][
                            "chart_container_non_empty"
                        ],
                        "no_horizontal_overflow": all(
                            r["timing"]["no_horizontal_overflow"] for r in runs
                        ),
                        "console_errors": [e for r in runs for e in r["console_errors"]],
                        "page_errors": [e for r in runs for e in r["page_errors"]],
                        "failed_network_requests": [
                            e for r in runs for e in r["failed_network_requests"]
                        ],
                    },
                }
                (EVIDENCE / out_name).write_text(
                    json.dumps(agg, indent=2) + "\n", encoding="utf-8"
                )
                print(f"WROTE {out_name} channel={channel} version={browser_version}")
        finally:
            browser.close()

    (EVIDENCE / "console.log").write_text(
        "\n".join(console_all) + ("\n" if console_all else "NO_CONSOLE_ERRORS\n"),
        encoding="utf-8",
    )
    (EVIDENCE / "page_errors.log").write_text(
        "\n".join(page_err_all) + ("\n" if page_err_all else "NO_PAGE_ERRORS\n"),
        encoding="utf-8",
    )
    (EVIDENCE / "network_failures.txt").write_text(
        "\n".join(failed_all) + ("\n" if failed_all else "NO_FAILED_NETWORK_REQUESTS\n"),
        encoding="utf-8",
    )
    meta = {
        "timestamp_utc": stamp,
        "browser_channel_attempt": "chrome",
        "runs_per_viewport": RUNS_PER_VIEWPORT,
        "viewports": [{"width": w, "height": h} for w, h, _ in VIEWPORTS],
        "cache_mode": "disabled_via_cdp_when_available",
        "stale_pid_note": "review_server.sh status STALE_PID not repaired; Playwright route-fulfill used",
    }
    (EVIDENCE / "chrome_measurement_meta.json").write_text(
        json.dumps(meta, indent=2) + "\n", encoding="utf-8"
    )


if __name__ == "__main__":
    main()
