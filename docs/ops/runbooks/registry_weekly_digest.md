# Registry Weekly Digest — Runbook

Ziel
- Wöchentliche Zusammenfassung aus der lokalen DONE-Registry (JSONL).
- Outputs sind **untracked** unter `out/ops/registry/reports/`.

Inputs
- `out/ops/registry/morning_one_shot_done_registry.jsonl`

Command
- `python3 scripts/ops/registry_weekly_digest.py`

Optionen
- `--days 7` (default)
- `--outdir out/ops/registry/reports`

Outputs
- `out/ops/registry/reports/weekly_digest_latest.md`
- `out/ops/registry/reports/weekly_digest_latest.json`
