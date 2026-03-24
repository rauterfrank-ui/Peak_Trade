# Update Officer v5 – CLI entrypoint

## Goal
Extend **Update Officer v4** with a deterministic, read-only CLI/operator entrypoint
for `notifier_payload.json`, without adding transport, scheduling, or autonomous behavior.

## Added in v5
| Component | Purpose |
|-----------|---------|
| `scripts/ops/update_officer_summary.py` | Read-only CLI for notifier payload summaries |
| `--payload` | Explicit path to `notifier_payload.json` |
| `--run-dir` | Resolves `<run-dir>&#47;notifier_payload.json` |

## Usage
```bash
python3 scripts/ops/update_officer_summary.py --payload out/ops/update_officer/<ts>/notifier_payload.json
python3 scripts/ops/update_officer_summary.py --run-dir out/ops/update_officer/<ts>
```

Run from the repository root (or any cwd; the script adds the repo root to `sys.path` so `src.ops` imports resolve).

## Exit codes
| Code | Meaning |
|------|---------|
| 0 | Payload loaded and summary printed to stdout |
| 2 | Missing/invalid arguments, missing file, invalid JSON, or schema validation failure |

Errors are written to stderr as `ERROR: …`.

## Wiring
- Uses `load_notifier_payload()` and `render_notifier_text_summary()` from `src.ops.update_officer_consumer`.
- Validation remains `validate_notifier_payload()` (via `load_notifier_payload`).

## Guardrails
- Read-only only (no writes except stdout/stderr)
- No dependency bumps
- No lockfile writes
- No paper/shadow/evidence mutation
- No runtime/live authority
- No background execution
- No external transport

## Deliverables
- `scripts/ops/update_officer_summary.py`
- `tests/ops/test_update_officer_summary.py`
- This runbook

## Version
- CLI slice on top of v4 consumer layer (`v3-min` payload contract)
