# Cursor MA Ops CLI (tracked)

## Scope
This CLI wraps **local** helpers under `out&#47;ops&#47;` and one **tracked** helper under `scripts&#47;ops&#47;cursor_ma_archive_run.sh`.

## Commands
- `scripts&#47;ops&#47;ma next [--run-id <RUN_ID>]`  
  Generates and prints `out&#47;ai&#47;context&#47;<RUN_ID>_cursor_context.txt`.

- `scripts&#47;ops&#47;ma finalize <RUN_ID> [--force]`  
  Runs local finalize. `--force` requires `CONFIRM_FORCE=I_UNDERSTAND`.

- `scripts&#47;ops&#47;ma package <RUN_ID>`  
  Promote + bundle + archive (no closeout).

- `scripts&#47;ops&#47;ma verify`  
  Verifies `out&#47;ai&#47;audit&#47;manifest.ndjson` (index).

- `scripts&#47;ops&#47;ma journal-verify`  
  Parses `out&#47;ai&#47;audit&#47;journal.ndjson` (append-only).

- `scripts&#47;ops&#47;ma list [N]`

- `scripts&#47;ops&#47;ma dedupe`  
  Ensures "one row per run" in the manifest index.

## Manifest model
- `journal.ndjson`: append-only history (optional).  
- `manifest.ndjson`: **index** (latest-per-run), must remain referentially valid.
