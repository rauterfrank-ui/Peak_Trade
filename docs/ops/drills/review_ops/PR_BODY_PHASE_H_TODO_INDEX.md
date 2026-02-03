## Scope
- Add a portable (macOS-safe) helper script to generate a Phase H TODO index JSON from the newest runbook + open points doc.

## Evidence
- Script: `scripts/ops/phase_h_todo_index.sh`
- Output (local-only): `artifacts/closeout/PHASE_H_TODO_INDEX.json`

## Notes
- Uses BSD `stat -f '%m'` to pick the newest runbook by mtime (portable for macOS).
- Does not change runtime code paths; the generated artifacts remain local-only (not committed).
- `RUNBOOK` and `OPENPTS` are overridable via environment variables.
