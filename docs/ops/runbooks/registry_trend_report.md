# Registry Trend Report — Runbook

Ziel
- Lokale Trend-/Regression-Auswertung aus der DONE-Registry (JSONL).
- Outputs sind **untracked** unter `out/ops/registry/reports/`.

Inputs
- `out/ops/registry/morning_one_shot_done_registry.jsonl`

Command
- `python3 scripts/ops/registry_trend_report.py`

Optionen
- `--limit 30` (default)
- `--outdir out/ops/registry/reports`

Outputs
- `out/ops/registry/reports/trend_report_latest.md`
- `out/ops/registry/reports/trend_report_latest.json`

Alerts (latest row)
- OPS_STATUS_FAIL
- PRBI_NOT_READY
- PRBG_STATUS_NOT_OK
- PRBG_ERRORS_PRESENT
- PRBG_SAMPLE_SIZE_DROP
