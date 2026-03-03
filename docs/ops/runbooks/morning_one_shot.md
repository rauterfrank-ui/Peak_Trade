# Morning One-Shot — Runbook

Ziel
Ein einziger Befehl, der morgens:
- main synchronisiert
- E2E runner ausführt (best-effort)
- PRBI latest zieht
- ops_status verdict erzeugt
- DONE token + sha schreibt (lokal unter out/ops/, untracked)

Command
- `./scripts/ops/run_morning_one_shot.sh`

Exit Codes
- 0: ops_status OK (inkl. PRBI gate wenn vorhanden)
- 2: Gate blockt (CONTINUE_* / NO_GO)
- other: unexpected failure
