# Resume state machine

Schema: `longer_chronological_pit_acquisition_state.v1`

## States

`PLANNED` → `DISCOVERED` → `ACQUIRING` → `ACQUIRED` → `CHECKSUM_VERIFIED` → `NORMALIZED` → `QUALIFIED`

Terminal: `QUARANTINED`, `FAILED` (FAILED may return to `PLANNED` for explicit replan only).

## Rules

- Illegal transitions raise `StateTransitionError` (fail-closed).
- `CHECKSUM_VERIFIED` &#47; `NORMALIZED` &#47; `QUALIFIED` partitions are skipped on resume.
- State file written atomically under `{archive}&#47;...&#47;state&#47;resume_state.json`.
- No silent overwrite of immutable raw partition artifacts.
