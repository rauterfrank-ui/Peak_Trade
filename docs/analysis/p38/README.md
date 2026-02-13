# P38 — Bundle Registry v1

## Goal
Aggregate bundle artifacts (P35 dir bundles, P36 tarballs) and bundle indices (P37) into one deterministic registry file for ops/crawlers.

## Files
- `registry.json` — schema v1, deterministic, no timestamps
- References:
  - P35: `manifest.json` sha256
  - P36: tarball sha256
  - P37: index json sha256

## Determinism
- Sort entries by `(bundle_id, kind, ref_path)`
- JSON: UTF-8, sort_keys, indent=2, trailing newline.

Non-goals: UI, plots, external services, live trading.
