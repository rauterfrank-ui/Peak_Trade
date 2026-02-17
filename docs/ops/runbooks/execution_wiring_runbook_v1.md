# Execution Wiring Runbook v1 (networkless, mocks-only)

## Scope / Non-goals

- **Scope:** Local, **networkless**, **mocks-only** execution wiring validation.
- **Modes allowed:** `shadow` or `paper`.
- **Non-goals:** No live trading, no real API keys, no external network calls.

## Hard guardrails (must hold)

- `--mode` must be `shadow|paper` (CLI rejects `live`).
- `--dry-run` must be `YES` (CLI guard rejects `NO` with rc=3).
- No secrets in env (do not export API keys). If in doubt: `env | grep -i key`.

## Canonical smoke (fast)

### 1) Unit + wiring tests

```bash
python3 -m pytest -q tests/p112 tests/p113 tests/p115 tests/p116 tests/p118
```

### 2) P121 one-shot (evidence + DONE pin)

```bash
MODE=shadow DRY_RUN=YES bash scripts/ops/p121_execution_wiring_proof_v1.sh
```

Outputs:

- Evidence dir: `out&#47;ops&#47;p121_execution_wiring_proof_<ts>&#47;`
- Bundle: `out&#47;ops&#47;p121_execution_wiring_proof_<ts>.bundle.tgz`
- DONE pin: `out&#47;ops&#47;P121_EXECUTION_WIRING_PROOF_DONE_<ts>.txt` (+ `.sha256`)

### 3) Verify latest P121 pin

```bash
PIN="$(ls -1 out/ops/P121_EXECUTION_WIRING_PROOF_DONE_*.txt 2>/dev/null | tail -n 1)"
shasum -a 256 -c "${PIN}.sha256"
```

## DONE pack pointers

| Pack | Path |
|------|------|
| P105 Execution A2Z | `out&#47;ops&#47;P105_EXECUTION_A2Z_DONE_*.txt` |
| P119 Execution Wiring Plan | `docs&#47;analysis&#47;p119&#47;README.md` |
| P121 Execution Wiring Proof | `out&#47;ops&#47;P121_EXECUTION_WIRING_PROOF_DONE_*.txt` |

## Troubleshooting

| Symptom | Cause | Fix |
|---------|-------|-----|
| `P121_GUARD_FAIL: mode_must_be_shadow_or_paper` | Invalid MODE | Use `MODE=shadow` or `MODE=paper` |
| `P121_GUARD_FAIL: dry_run_must_be_yes` | DRY_RUN not YES | Set `DRY_RUN=YES` |
| `P121_GUARD_FAIL: forbidden_env` | Live/trading env set | Unset LIVE, RECORD, API_KEY, etc. |
| P117 tests fail locally | p95_meta_gate needs Supervisor | P121 smoke excludes p117; run p112–p118 only |
| `ROUTER_CLI_GUARD_FAIL: dry_run_must_be_yes` | Router CLI dry-run disabled | CLI is mocks-only; always use `--dry-run YES` |

## Related docs

- P105: `docs&#47;analysis&#47;p105&#47;README.md` — Exchange/Execution research
- P119: `docs&#47;analysis&#47;p119&#47;README.md` — Execution wiring plan
- P121: `docs&#47;analysis&#47;p121&#47;README.md` — Execution wiring proof v1
