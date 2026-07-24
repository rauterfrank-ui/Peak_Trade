"""Bounded TASK_8 measurement harness — evidence-only, not a production module."""

from __future__ import annotations

import json
import re
import statistics
import time
from datetime import datetime, timezone
from pathlib import Path

from fastapi.testclient import TestClient

from src.webui.app import create_app

REPO = Path(__file__).resolve().parents[4]
EVIDENCE = Path(__file__).resolve().parent


def looks_minified(path: Path) -> bool:
    text = path.read_text(encoding="utf-8", errors="replace")
    lines = text.splitlines()
    if not lines:
        return False
    if len(lines) == 1 and len(text) > 2000:
        return True
    avg = len(text) / max(len(lines), 1)
    return avg > 200


def file_bytes(url: str) -> int:
    rel = url.split("/static/", 1)[1]
    p = REPO / "static" / rel
    return p.stat().st_size if p.is_file() else -1


def main() -> None:
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    client = TestClient(create_app())

    resp = client.get("/market")
    html = resp.text
    html_bytes = len(resp.content)
    status = resp.status_code

    stylesheet_hrefs = re.findall(
        r'<link[^>]+rel=["\']stylesheet["\'][^>]*>', html, flags=re.I
    )
    script_tags = re.findall(r"<script\b[^>]*>", html, flags=re.I)
    hrefs = re.findall(r'href=["\']([^"\']+)["\']', "\n".join(stylesheet_hrefs))
    srcs = re.findall(r'src=["\']([^"\']+)["\']', "\n".join(script_tags))
    inline_scripts = [t for t in script_tags if "src=" not in t.lower()]

    page_css = [h for h in hrefs if "market_dashboard_landscape_v2.css" in h]
    page_js = [s for s in srcs if "market_dashboard_landscape_v2.js" in s]
    all_static_css = [h for h in hrefs if h.startswith("/static/")]
    all_static_js = [s for s in srcs if s.startswith("/static/")]

    css_sizes = {h: file_bytes(h) for h in all_static_css}
    js_sizes = {s: file_bytes(s) for s in all_static_js}
    dashboard_css = css_sizes.get("/static/css/market_dashboard_landscape_v2.css", -1)
    dashboard_js = js_sizes.get("/static/js/market_dashboard_landscape_v2.js", -1)
    page_owned_total = dashboard_css + dashboard_js
    all_static_total = sum(
        v for v in list(css_sizes.values()) + list(js_sizes.values()) if v > 0
    )

    dup_css = len(all_static_css) != len(set(all_static_css))
    dup_js = len(all_static_js) != len(set(all_static_js))
    dup_page = len(page_css) > 1 or len(page_js) > 1

    assets_meta = []
    for url, size in {**css_sizes, **js_sizes}.items():
        rel = url.split("/static/", 1)[1]
        p = REPO / "static" / rel
        text = p.read_text(encoding="utf-8", errors="replace") if p.is_file() else ""
        assets_meta.append(
            {
                "url": url,
                "bytes": size,
                "exists": p.is_file(),
                "minified_heuristic": looks_minified(p) if p.is_file() else None,
                "sourceMappingURL": "sourceMappingURL" in text,
                "page_owned": "market_dashboard_landscape_v2" in url,
            }
        )

    js_text = (REPO / "static/js/market_dashboard_landscape_v2.js").read_text(
        encoding="utf-8"
    )
    unused_notes = []
    if "fetch(" in js_text or "XMLHttpRequest" in js_text:
        unused_notes.append("network_calls_in_js")
    else:
        unused_notes.append("no_network_calls_in_page_js")
    unused_notes.append(
        "no_obvious_unused_page_specific_asset_refs_detected_without_deleting"
    )

    inv_lines = [
        f"TIMESTAMP_UTC={stamp}",
        f"HTML_RESPONSE_BYTES={html_bytes}",
        f"RENDERED_HTML_BYTES={html_bytes}",
        f"HTTP_STATUS={status}",
        f"STYLESHEET_TAG_COUNT={len(stylesheet_hrefs)}",
        f"SCRIPT_TAG_COUNT={len(script_tags)}",
        f"INLINE_SCRIPT_TAG_COUNT={len(inline_scripts)}",
        f"PAGE_OWNED_CSS_FILE_COUNT={len(set(page_css))}",
        f"PAGE_OWNED_JS_FILE_COUNT={len(set(page_js))}",
        f"DASHBOARD_CSS_BYTES={dashboard_css}",
        f"DASHBOARD_JS_BYTES={dashboard_js}",
        f"TOTAL_PAGE_OWNED_STATIC_BYTES={page_owned_total}",
        f"ALL_STATIC_LOADED_BYTES={all_static_total}",
        f"SHARED_BASE_CSS_BYTES={sum(v for k, v in css_sizes.items() if 'market_dashboard_landscape_v2' not in k)}",
        f"DUPLICATE_ASSET_LOADING={str(bool(dup_css or dup_js or dup_page)).lower()}",
        f"SOURCE_MAPS_OR_DEV_PAYLOADS_EXPOSED={str(any(a.get('sourceMappingURL') for a in assets_meta)).lower()}",
        "STYLESHEET_HREFS=" + ",".join(hrefs),
        "SCRIPT_SRCS=" + (",".join(srcs) if srcs else ""),
        "MINIFIED_HEURISTIC_JSON="
        + json.dumps({a["url"]: a["minified_heuristic"] for a in assets_meta}),
        "ASSETS_JSON=" + json.dumps(assets_meta, indent=2),
        "NOTES=" + ";".join(unused_notes),
        "LIMITATION=sizes from on-disk static files + TestClient HTML body; not gzip/brotli transfer encoding",
    ]
    (EVIDENCE / "asset_inventory.txt").write_text("\n".join(inv_lines) + "\n", encoding="utf-8")

    warmup = 5
    samples = 30
    for _ in range(warmup):
        r = client.get("/market")
        assert r.status_code == 200

    times_ms: list[float] = []
    statuses: list[int] = []
    sizes: list[int] = []
    errors: list[dict] = []
    for i in range(samples):
        t0 = time.perf_counter()
        try:
            r = client.get("/market")
            dt = (time.perf_counter() - t0) * 1000.0
            times_ms.append(dt)
            statuses.append(r.status_code)
            sizes.append(len(r.content))
            if r.status_code != 200:
                errors.append({"i": i, "status": r.status_code})
        except Exception as exc:  # noqa: BLE001 — measurement capture
            errors.append({"i": i, "error": str(exc)})

    times_sorted = sorted(times_ms)

    def pct(p: float) -> float:
        if not times_sorted:
            return float("nan")
        k = (len(times_sorted) - 1) * (p / 100.0)
        f = int(k)
        c = min(f + 1, len(times_sorted) - 1)
        if f == c:
            return times_sorted[f]
        return times_sorted[f] + (times_sorted[c] - times_sorted[f]) * (k - f)

    route = {
        "timestamp_utc": stamp,
        "harness": "fastapi.testclient.TestClient(create_app()).get('/market')",
        "command": "uv run python evidence/market_dashboard_v2/phase5/task8_performance/_measure_route_assets.py",
        "environment": "local_inprocess_asgi_testclient",
        "warmup_count": warmup,
        "measured_request_count": samples,
        "min_ms": round(min(times_ms), 3) if times_ms else None,
        "p50_ms": round(pct(50), 3) if times_ms else None,
        "p95_ms": round(pct(95), 3) if times_ms else None,
        "max_ms": round(max(times_ms), 3) if times_ms else None,
        "mean_ms": round(statistics.mean(times_ms), 3) if times_ms else None,
        "http_status_consistent": len(set(statuses)) == 1
        and bool(statuses)
        and statuses[0] == 200,
        "statuses_unique": sorted(set(statuses)),
        "response_byte_consistent": len(set(sizes)) == 1,
        "response_bytes_unique": sorted(set(sizes)),
        "errors_timeouts": errors,
        "samples_ms": [round(x, 3) for x in times_ms],
        "limitations": [
            "In-process TestClient ASGI timing, not production network RTT",
            "No concurrent load; bounded regression sample only",
            "Wall-clock dependent on local machine; not a ratified budget",
            "HTML byte size may vary slightly across samples if generated_at drifts",
        ],
    }
    (EVIDENCE / "route_timing.json").write_text(
        json.dumps(route, indent=2) + "\n", encoding="utf-8"
    )
    print(
        json.dumps(
            {
                "html_bytes": html_bytes,
                "status": status,
                "dashboard_css": dashboard_css,
                "dashboard_js": dashboard_js,
                "page_owned_total": page_owned_total,
                "duplicate": bool(dup_css or dup_js or dup_page),
                "route_summary": {
                    k: route[k]
                    for k in (
                        "min_ms",
                        "p50_ms",
                        "p95_ms",
                        "max_ms",
                        "mean_ms",
                        "http_status_consistent",
                        "response_byte_consistent",
                        "errors_timeouts",
                        "response_bytes_unique",
                    )
                },
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
