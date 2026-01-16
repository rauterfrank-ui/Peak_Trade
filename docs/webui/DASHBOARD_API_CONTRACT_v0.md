# Peak_Trade Dashboard v0 — API Contract (Read-only)

Diese Spezifikation dokumentiert die **read-only** API Endpunkte für das Watch-Only Dashboard v0.1 (Phase 67).

## Scope
- Read-only Endpoints (kein Start/Stop, keine Orders).
- Contract-stabile v0 Namespace Endpunkte unter `&#47;api&#47;v0&#47;...` (Aliases + Detail/Metrics).

## Health
- GET `&#47;health`
- GET `&#47;api&#47;v0&#47;health` (Alias)

Antwort:
- `{"status":"ok","contract_version":"v0.1B","server_time":"<ISO8601_UTC>"}`

## Runs (Index)
- GET `&#47;runs`
- GET `&#47;api&#47;v0&#47;runs` (Alias)

Antwort: Liste von Run-Metadaten (max. 50).

## Run Snapshot (existing)
- GET `&#47;runs&#47;{run_id}&#47;snapshot`

Antwort: aggregierter Snapshot (Equity/PnL/Orders/Drawdown).

## Run Tail (existing)
- GET `&#47;runs&#47;{run_id}&#47;tail?limit=50`

Antwort: Liste der letzten Event-Zeilen (best effort).

## Run Alerts (existing)
- GET `&#47;runs&#47;{run_id}&#47;alerts?limit=20`

Antwort: Liste von Alerts (falls vorhanden).

## v0 Run Detail (meta + snapshot)
- GET `&#47;api&#47;v0&#47;runs&#47;{run_id}`

Antwort:
- `meta`: Inhalt aus `meta.json` (inkl. `config_snapshot`)
- `snapshot`: wie `&#47;runs&#47;{run_id}&#47;snapshot`

## v0 Metrics
- GET `&#47;api&#47;v0&#47;runs&#47;{run_id}&#47;metrics`

Antwort: Subset aus Snapshot (equity/pnl/drawdown + counts).

## v0 Equity Time Series
- GET `&#47;api&#47;v0&#47;runs&#47;{run_id}&#47;equity?limit=500`

Antwort: Liste von Punkten:
- `ts` (aus `ts_event` oder `ts_bar`)
- `equity`, `realized_pnl`, `unrealized_pnl`, `drawdown` (best effort)

Wenn Events fehlen, liefert der Endpoint 404 mit `equity_not_available`.

## v0.1B Signals / Positions / Orders (Read-only)
- GET `&#47;api&#47;v0&#47;runs&#47;{run_id}&#47;signals?limit=200`
- GET `&#47;api&#47;v0&#47;runs&#47;{run_id}&#47;positions?limit=200`
- GET `&#47;api&#47;v0&#47;runs&#47;{run_id}&#47;orders?limit=500&only_nonzero=true`

Antwort (Wrapper):
- `run_id` (string)
- `asof` (ISO8601 string, UTC; server-side snapshot time)
- `count` (int)
- `items` (list; best effort)

---

## v0.2 Control Center (Additive, Watch-Only)

Diese Endpunkte sind **additiv** (keine Breaking Changes) und bleiben **read-only**.

### Runs v0.2 (Index)
- GET `&#47;api&#47;v0&#47;runs_v02?limit=50`

Antwort: Liste von `RunSummaryV02` (best effort):
- `run_id`
- `status` (`active|inactive|completed|unknown`)
- `started_at`
- `last_heartbeat` (best effort; derzeit aus `last_event_time`)
- `strategy_id` (best effort; derzeit `strategy_name`)
- `tags` (list; aus `config_snapshot.tags` wenn vorhanden)
- `base_dir` (string)

### Run v0.2 (Detail)
- GET `&#47;api&#47;v0&#47;runs&#47;{run_id}&#47;detail_v02`

Antwort: `RunDetailV02`:
- `summary` (RunSummaryV02)
- `pointers` (URLs zu metrics/equity/signals/positions/orders/alerts/events)
- `alerts_summary` (best effort)
- `config_snapshot` (object)

### Health v0.2 (Components)
- GET `&#47;api&#47;v0&#47;health_v02`

Antwort: `HealthV02`:
- `status`, `contract_version`, `server_time`, `last_update`
- `components` (map; z.B. `live_dashboard`, `runs_dir`)

### Events / Logs v0.2 (JSON Poll oder SSE)

- JSON poll:
  - GET `&#47;api&#47;v0&#47;runs&#47;{run_id}&#47;events?since_seq=0&limit=200`

Antwort: `EventsPollResponseV02`:
- `run_id`, `asof`, `next_seq`, `count`, `items[]`

- SSE (optional):
  - GET `&#47;api&#47;v0&#47;runs&#47;{run_id}&#47;events?sse=1&follow=1&since_seq=0&max_seconds=30`
  - Header: `Accept: text&#47;event-stream`

SSE Event:
- `event: pt_event`
- `data: { ...EventItemV02... }`

## v0 Trades (optional)
- GET `&#47;api&#47;v0&#47;runs&#47;{run_id}&#47;trades`

Nur verfügbar, wenn im Run-Verzeichnis ein explizites Trades-Artefakt existiert (`trades.csv` oder `trades.parquet`).
Sonst 404 mit `trades_not_available`.
