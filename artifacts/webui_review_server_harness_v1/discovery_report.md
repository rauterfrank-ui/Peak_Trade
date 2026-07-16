# WebUI Review Server Harness v1 — Discovery Report

GO_TOKEN: `GO_PEAK_TRADE_WEBUI_REVIEW_SERVER_HARNESS_V1`
Worktree: `/Users/frnkhrz/Peak_Trade_review_server_harness_v1`
Branch: `feat/webui-review-server-harness-v1`
Base: `origin/main` @ `b9be86aa97d58ac5d00dc4e9885cdbbeab3125f1`

## Canonical ASGI target

- **ASGI:** `src.webui.app:app`
- **Owner:** `src/webui/app.py` (module-level `app` export)
- **Existing foreground launcher (reuse invocation pattern, not lifecycle):** `scripts/ops/run_webui.sh`
  - `uv run python -m uvicorn src.webui.app:app --host … --port …`
  - Optional `--reload` via `RELOAD=1` — **forbidden** for review harness

## Canonical Python environment invocation

- Prefer: `uv run python -m uvicorn …` (same as `scripts/ops/run_webui.sh`)
- Preflight deps: `scripts/ops/ensure_web_extra.sh` (fastapi + uvicorn)

## Existing reusable scripts / configs

| Surface | Path | Reuse decision |
|---|---|---|
| Foreground WebUI start | `scripts/ops/run_webui.sh` | Reuse ASGI/uv invocation; do **not** use as review lifecycle (foreground, optional reload) |
| Live WebUI start | `scripts/ops/run_live_webui.sh` | Out of scope (`src.live.web.app`) |
| Chrome/Playwright harness | `scripts/webui/market_dashboard_chrome_playwright_harness_v1.py` | Reuse `channel=chrome` + network accounting; add webServer lifecycle helper |
| Background job helper | `scripts/ops/bg_job.sh` | Pattern reference for PID/log; not WebUI-specific — do not overload |
| Node Playwright config | *(none found)* | N/A — Python Playwright is canonical |
| Dedicated review_server.sh | *(none)* | **Create** `scripts/webui/review_server.sh` |

## Selected host / port policy

- **Host default:** `127.0.0.1` (`PEAK_TRADE_WEBUI_HOST`) — localhost only
- **Port default:** `8000` (`PEAK_TRADE_WEBUI_PORT`) — matches repo docs / `run_webui.sh`
- Unknown listener on port → **fail-closed** (never kill foreign PID)

## Selected healthcheck route

- **Primary:** `GET &#47;api&#47;health` (always `{"status":"ok"}` in `src/webui/app.py`)
- **Review URL / secondary readiness:** `GET &#47;market`
- Override: `PEAK_TRADE_WEBUI_HEALTH_PATH`

## Selected runtime-state / log directories

- **State dir:** `.run&#47;webui_review_server&#47;` (override: `PEAK_TRADE_WEBUI_STATE_DIR`)
- **PID file:** `.run&#47;webui_review_server&#47;review_server.pid`
- **Log file:** `.run&#47;webui_review_server&#47;review_server.log`
- **Meta file:** `.run&#47;webui_review_server&#47;review_server.meta`
- Add `.run&#47;` to `.gitignore` (do not commit PID/logs)

## Playwright integration point

- No Node `playwright.config.*` / `webServer` block exists.
- Canonical browser path is Python Playwright in `scripts/webui/market_dashboard_chrome_playwright_harness_v1.py` (`channel=chrome`).
- **Plan:** add `scripts/webui/review_server_playwright_webserver_v1.py` that starts/stops via `review_server.sh`, with:
  - local reuse of healthy server allowed
  - CI (`CI`/`GITHUB_ACTIONS`) reuse disabled
  - bounded start timeout
  - primary channel `chrome`

## Files planned for mutation

1. `scripts/webui/review_server.sh` (new)
2. `scripts/webui/review_server_playwright_webserver_v1.py` (new)
3. `scripts/webui/market_dashboard_chrome_playwright_harness_v1.py` (minimal: optional `--manage-server`)
4. `tests/webui/test_review_server_harness_v1.py` (new)
5. `docs/webui/REVIEW_SERVER_HARNESS_V1.md` (new ops doc under existing `docs/webui/`)
6. `docs/webui/MARKET_SURFACE_V0.md` (short link only)
7. `.gitignore` (`.run&#47;`)
8. `artifacts&#47;webui_review_server_harness_v1&#47;*` (evidence)

## Non-goals / untouched

- Dashboard product runbook / phase matrices
- Active dashboard worktree/branch/PR #5250
- Trading, risk, decision, authority, credentials, orders
- `LIVE_AUTHORIZED=false`, `ORDERS_ALLOWED=false`, `NETWORK_POLICY=LOCALHOST_ONLY`
