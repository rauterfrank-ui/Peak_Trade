# P37 — Bundle Index v1

## Goal
Create a deterministic index over multiple **report bundles** produced by:
- **P35**: directory bundle (contains `report.json` + `manifest.json` [+ `metrics_summary.json`])
- **P36**: tarball bundle (a `.tgz` containing a P35-style bundle)

## Supported inputs
`index_bundles_v1(paths, base_dir=...)` accepts:
- A directory that contains `manifest.json` and `report.json` (treated as `dir_bundle`)
- A `.tgz` tarball (treated as `tarball`)

## Entry fields
- `kind`: `dir_bundle` | `tarball`
- `relpath`: stable path used as identifier (relative to `base_dir` if provided, else the given path)
- `sha256`, `bytes`: hash/size of:
  - `dir_bundle`: **manifest.json file contents** (avoids hashing whole dir)
  - `tarball`: tarball file contents
- `report_schema_version`: read from validated `report.json` (schema v1 via P34/P33)

## Determinism
- Index JSON written UTF-8 with `sort_keys=true`, `indent=2`, trailing newline.
- Entries are sorted by `relpath`.
- No timestamps, no host-specific metadata.

## Verify
`verify_bundle_index_v1(index, base_dir=...)`:
- validates version
- ensures **unique** `relpath`
- checks optional existence + sha/bytes match for each entry
