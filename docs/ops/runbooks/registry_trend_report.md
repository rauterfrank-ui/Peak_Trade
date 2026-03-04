# Registry Trend Report — Runbook

Ziel
- Lokale Trend-/Regression-Auswertung aus der DONE-Registry (JSONL).
- Outputs sind **untracked** unter ``out&#47;ops&#47;registry&#47;reports&#47;``.

Inputs
- ``out&#47;ops&#47;registry&#47;morning_one_shot_done_registry.jsonl``

Command
- ``python3 scripts&#47;ops&#47;registry_trend_report.py``

Optionen
- `--limit 30` (default)
- ``--outdir out&#47;ops&#47;registry&#47;reports``

Outputs
- ``out&#47;ops&#47;registry&#47;reports&#47;trend_report_latest.md``
- ``out&#47;ops&#47;registry&#47;reports&#47;trend_report_latest.json``

Alerts (latest row)
- OPS_STATUS_FAIL
- PRBI_NOT_READY
- PRBG_STATUS_NOT_OK
- PRBG_ERRORS_PRESENT
- PRBG_SAMPLE_SIZE_DROP
