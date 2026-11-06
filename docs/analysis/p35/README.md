# P35 — Report Artifact Bundle v1

## Goal
Persist a validated backtest report (schema v1) plus an integrity manifest as a deterministic on-disk bundle.

## Files
- `report.json` — validated via P34/P33 schema v1
- `metrics_summary.json` — deterministic KPI snapshot (from report metrics if present; else derived)
- `manifest.json` — sha256 + bytes for each file

## Determinism
- JSON written UTF-8 with `sort_keys=true`, `indent=2`, trailing newline.
- Manifest is derived only from file contents; no timestamps.

## API
- `write_report_bundle_v1(dir_path, report_dict, include_metrics_summary=True) -> BundleManifestV1`
- `read_report_bundle_v1(dir_path) -> dict`
- `verify_report_bundle_v1(dir_path) -> BundleManifestV1` (raises `BundleIntegrityError`)

Non-goals: plotting, HTML/PDF generation, external services, live trading.
