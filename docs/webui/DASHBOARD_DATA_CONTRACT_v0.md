# Peak_Trade Dashboard v0 — Data Contract (Artifacts)

Diese Spezifikation beschreibt das **Datei-Layout** und die minimalen **Schemas**, die das Watch-Only Dashboard v0.1 (Phase 67) liest.

## Scope / Non-Goals
- **Read-only**: Das Dashboard **liest** Artefakte, schreibt sie nicht.
- **Kein Live-Trading**: Keine Order-Erzeugung über UI/API.
- **Kein Watch-Loop in Skripten**: Verifikation erfolgt via Snapshots/Checks.

## Artifact Root (Runs Directory)
Das Dashboard liest Runs aus einem konfigurierbaren Verzeichnis.

- Default in Code/CLI: `live_runs&#47;` (local-only, gitignored)
- CLI Override: `--base-runs-dir <PATH>` (siehe `scripts&#47;live_web_server.py`)

### Filesystem Layout
Pro Run existiert ein Ordner:

- `{base_runs_dir}&#47;{run_id}&#47;meta.json`
- `{base_runs_dir}&#47;{run_id}&#47;events.parquet` **oder** `{base_runs_dir}&#47;{run_id}&#47;events.csv`
- Optional: `{base_runs_dir}&#47;{run_id}&#47;alerts.jsonl`

## meta.json (Run Metadata)
Quelle: `src&#47;live&#47;run_logging.py` (`LiveRunMetadata`)

Minimal erforderliche Felder:
- `run_id` (string)
- `mode` (string; z.B. `shadow`, `paper`, `testnet`)
- `strategy_name` (string)
- `symbol` (string; z.B. `BTC&#47;EUR`)
- `timeframe` (string; z.B. `1m`)

Optionale Felder:
- `started_at` (ISO8601 string)
- `ended_at` (ISO8601 string oder null)
- `config_snapshot` (object)
- `notes` (string)

## events.parquet / events.csv (Time-Series Events)
Quelle: `src&#47;live&#47;run_logging.py` (`LiveRunEvent`), Reader: `load_run_events()`.

Das Dashboard nutzt “best effort” Spalten:
- Zeitstempel: `ts_event` (bevorzugt) oder `ts_bar`
- Equity: `equity`
- Realized PnL: `realized_pnl` (Fallback: `pnl`)
- Unrealized PnL: `unrealized_pnl`
- Optional bereits vorhanden: `drawdown`

Weitere häufige Felder (nicht strikt):
- `step`
- `position_size`
- `orders_generated`, `orders_filled`, `orders_blocked`
- `risk_allowed`, `risk_reasons`

## alerts.jsonl (Optional)
Wenn vorhanden, wird `alerts.jsonl` (eine JSON pro Zeile) read-only gelesen.
Die Web-UI nutzt u.a. Felder wie:
- `rule_id`
- `severity` (z.B. `info`, `warning`, `critical`)
- `message`
- `run_id`
- `timestamp`

## Notes (Stability)
- Das Contract ist **append-only** gedacht: neue Felder dürfen hinzugefügt werden, bestehende Felder sollten nicht umbenannt/entfernt werden.
