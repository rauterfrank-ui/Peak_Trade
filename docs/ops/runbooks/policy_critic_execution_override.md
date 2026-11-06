# Policy Critic – Execution Override (ops/execution-reviewed)

## Zweck
Definiert einen auditierten Override-Prozess für PRs mit Execution-/Live-kritischen Änderungen (Day-Trading Safety Gate).

## Grundsatz
- Default: Execution-Touches => Policy Critic BLOCK (AUTO_APPLY_DENY).
- Override ist möglich, wenn:
  1) Manuelles Execution-Review durchgeführt wurde,
  2) Evidence/Test-Plan dokumentiert ist,
  3) PR das Label `ops/execution-reviewed` trägt,
  4) Auto-Merge ist deaktiviert (manual merge only).

## Evidence (Pflicht)
Bevor das Label gesetzt wird, muss mindestens eins existieren:
- Datei: `docs&#47;ops&#47;evidence&#47;PR_<nr>_EXECUTION_REVIEW.md` (Template nutzen), oder
- PR-Body enthält Abschnitt `## Test Plan`.

## Prozess (Operator)
1) Evidence erstellen (Template kopieren und ausfüllen)
2) Reviewer trägt Attestation ein (Name/Datum/Notes)
3) Label setzen: `ops/execution-reviewed`
4) Merge manuell (Squash/merge nach eurer Praxis)

## Anti-Pattern
- Kein Label ohne Evidence.
- Kein "stilles" Auto-Merge auf Execution-Touches.
- Admin-Override nur als Breakglass, mit Follow-up PR zur Governance-Reparatur.
