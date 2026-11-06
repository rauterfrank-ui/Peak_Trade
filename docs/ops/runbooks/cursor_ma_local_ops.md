# Cursor MA Local Ops (ignored artifacts)

## Invariant: manifest referential integrity
- `out&#47;ai&#47;audit&#47;manifest.ndjson` stores `audit_path` references.
- Do **not** move audit JSON out of `out&#47;ai&#47;audit&#47;` after closeout.
- Archiving must **copy** audit into `out&#47;ai&#47;archive&#47;<RUN_ID>&#47;` while keeping (or restoring) `out&#47;ai&#47;audit&#47;<RUN_ID>_audit.json`.

## Recommended archive command (tracked)
- `scripts&#47;ops&#47;cursor_ma_archive_run.sh <RUN_ID> [NEW_RUN_ID]`

## Notes
- `out&#47;` is gitignored; ops helpers under `out&#47;ops&#47;` are local-only.
- If you need shareable artifacts, use snapshot + bundle (zip + sha256).
