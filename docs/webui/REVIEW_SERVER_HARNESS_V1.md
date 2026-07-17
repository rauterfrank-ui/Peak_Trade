# WebUI Review Server Harness v1

Bounded, repo-owned localhost review-server lifecycle for Peak Trade WebUI operator review and automated browser smokes.

**No runtime / trading / authority effect.**
`LIVE_AUTHORIZED=false` · `ORDERS_ALLOWED=false` · `NETWORK_POLICY=LOCALHOST_ONLY`

Related technical surface: [`MARKET_SURFACE_V0.md`](./MARKET_SURFACE_V0.md) (`GET &#47;market`).
Dashboard master runbook SSOT remains [`docs/product/Peak_Trade_Runbook_v1.3_Composition_Landmark_Master_Runbook.md`](../product/Peak_Trade_Runbook_v1.3_Composition_Landmark_Master_Runbook.md) — this harness does **not** duplicate that runbook.

## Canonical commands

```bash
./scripts/webui/review_server.sh start
./scripts/webui/review_server.sh status
./scripts/webui/review_server.sh open
./scripts/webui/review_server.sh restart
./scripts/webui/review_server.sh stop
./scripts/webui/review_server.sh logs
# optional follow:
./scripts/webui/review_server.sh logs --follow
```

## Defaults

| Setting | Default |
|---|---|
| Host | `127.0.0.1` |
| Port | `8000` |
| ASGI | `src.webui.app:app` via `uv run python -m uvicorn` |
| Healthcheck | `GET &#47;api&#47;health` |
| Review URL | `http://127.0.0.1:8000/market` |
| State dir | `.run&#47;webui_review_server&#47;` |
| PID file | `.run&#47;webui_review_server&#47;review_server.pid` |
| Log file | `.run&#47;webui_review_server&#47;review_server.log` |
| Start timeout | `45s` |
| Stop timeout | `15s` |
| Reload | **disabled** (`UVICORN_RELOAD=false`) |
| Primary browser (open) | **Google Chrome** (never Safari as primary) |

## Environment overrides

- `PEAK_TRADE_WEBUI_HOST`
- `PEAK_TRADE_WEBUI_PORT`
- `PEAK_TRADE_WEBUI_START_TIMEOUT_SECONDS`
- `PEAK_TRADE_WEBUI_STOP_TIMEOUT_SECONDS`
- `PEAK_TRADE_WEBUI_STATE_DIR`
- `PEAK_TRADE_WEBUI_HEALTH_PATH`
- `PEAK_TRADE_WEBUI_REVIEW_PATH`
- `PEAK_TRADE_WEBUI_LOG_TAIL_LINES`
- `PEAK_TRADE_WEBUI_UV`
- `PEAK_TRADE_WEBUI_REUSE_EXISTING` (Playwright helper; local default true, CI forced false)

## Status values

- `RUNNING_HEALTHY`
- `RUNNING_UNHEALTHY`
- `STALE_PID`
- `PORT_OCCUPIED_BY_UNKNOWN_PROCESS`
- `STOPPED`

## Typical failure modes

| Symptom | Meaning | Operator action |
|---|---|---|
| `PORT_OCCUPIED_BY_UNKNOWN_PROCESS` | Foreign listener on port | Inspect with `lsof -nP -iTCP:<port> -sTCP:LISTEN`; harness will **not** kill it |
| `STALE_PID` | Pidfile present, process gone | `start` recovers automatically |
| `RUNNING_UNHEALTHY` | Owned process up, health failing | Check `logs`; then `restart` |
| Healthcheck timeout | App did not become ready in bound window | Tail logs; fix deps ([`scripts/ops/ensure_web_extra.sh`](../../scripts/ops/ensure_web_extra.sh)) |
| Chrome missing on `open` | No Google Chrome.app | Install Chrome; Chromium fallback only if explicitly available and reported |

## Manual operator review server vs Playwright test server

| | Manual review (`review_server.sh`) | Playwright webServer helper |
|---|---|---|
| Owner script | `scripts/webui/review_server.sh` | `scripts/webui/review_server_playwright_webserver_v1.py` |
| Lifecycle | Operator start/stop/open | Test starts; stops only if it started |
| Reuse healthy server | Always idempotent reuse | Local: allowed · CI (`CI`/`GITHUB_ACTIONS`): **forbidden** |
| Browser | `open -a "Google Chrome"` | Playwright `channel=chrome` |
| Purpose | Durable human review | Automated smoke / evidence |

Both paths share the same ASGI target, localhost bind, no `--reload`, and process-identity rules.

## Explicit non-goals

- No `uvicorn --reload` in the review start path
- Safari is never the primary browser
- Localhost only — non-loopback hosts fail closed
- No trading, risk, decision, credential, order, or authority semantics
- Does not replace `scripts/ops/run_webui.sh` (foreground/dev); that script remains for interactive reload workflows when explicitly requested via `RELOAD=1`
