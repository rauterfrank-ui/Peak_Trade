# Morning One-Shot — Runbook

Ziel
Ein einziger Befehl, der morgens:
- main synchronisiert
- E2E-Evidence-Workflows einmal anstößt, sofern `RUN_E2E` nicht auf `false` steht
- PRBI latest zieht
- ops_status verdict erzeugt
- DONE token + sha schreibt (lokal unter out/ops/, untracked)

Command
- ``.&#47;scripts&#47;ops&#47;run_morning_one_shot.sh`` <!-- pt:ref-target-ignore -->

Exit Codes
- 0: ops_status OK und E2E-Dispatch erfolgreich oder deaktiviert
- 1: E2E-Dispatch fehlgeschlagen, Details stehen im DONE-Token
- 2: Gate blockt (CONTINUE_* / NO_GO)
- other: unexpected failure
