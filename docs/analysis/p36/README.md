# P36 — Report Bundle Tarball v1

## Purpose
Package a **P35 bundle directory** into a `.tgz` and restore it safely.

## Invariants
- Tarball members are relative, no absolute paths, no `..`.
- Only these files are permitted:
  - `report.json`
  - `metrics_summary.json` (optional)
  - `manifest.json`
- Verification delegates to `verify_report_bundle_v1()` after extraction.

## API
- `write_bundle_tarball_v1(bundle_dir, tar_path) -> tar_path`
- `read_bundle_tarball_v1(tar_path, out_dir) -> out_dir` (safe extract)
- `verify_bundle_tarball_v1(tar_path) -> None` (extract to temp + verify)
