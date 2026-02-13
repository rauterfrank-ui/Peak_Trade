# P37 — Bundle Index v1

## Concept
An **index.json** that lists multiple bundle artifacts (directory bundles or tarballs) with stable metadata:
- kind: `dir_bundle` | `tarball`
- relpath: relative path (preferred) or absolute path (allowed for local ops)
- sha256 + bytes of the artifact container (dir manifest.json hash for dir bundle; tarball hash for tarball)
- report schema version (from report.json)
- optional tags: strategy_id, run_id, timeframe (free-form)

## Determinism
- JSON UTF-8, sort_keys=true, indent=2, trailing newline
- Entries sorted by `relpath`
- No timestamps
