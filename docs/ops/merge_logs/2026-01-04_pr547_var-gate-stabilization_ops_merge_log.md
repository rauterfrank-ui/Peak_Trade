# PR #547 — VaR Gate Stabilization (CI Regression Gate + Fixtures)

## Summary
Stabilisierung der VaR Report Regression Gates durch ein robustes 3-Schritt Defer-Fail Pattern im Workflow sowie saubere CI-Green-Path Fixtures. Negative Regression-Fixtures bleiben für Tests erhalten.

## Why
CI schlug zuvor wegen Regressionen/Instabilität in Fixtures fehl; die Gates mussten deterministisch, artefakt-sicher (Upload immer), und auditierbar werden (klare Fail-Signale statt „silent" Abbrüche).

## Changes
### Workflow
- Implementiert: 3-Schritt Defer-Fail Pattern (Gate run → Artefakte immer uploaden → expliziter Fail-Step mit klarer Fehlermeldung)
- `continue-on-error: true` für Gate-Steps; harte Failure ausschließlich im dedizierten Fail-Step
- `if: always()` für Artefakt-Uploads, um Debugging-Daten unabhängig vom Gate-Exitcode zu sichern

### Fixtures (tests/fixtures/var_suite_reports/)
- Einführung CI-Green-Path Runs:
  - `run_baseline&#47;`
  - `run_candidate&#47;`
- Bewahrt für Negative-Tests (Regression Detection):
  - `run_known_regressions_baseline&#47;`
  - `run_known_regressions_candidate&#47;`
- Unverändert:
  - `run_pass_all&#47;` (Golden dataset)
- Dokumentation ergänzt: `README.md` zur Fixture-Struktur und Test-Intention

### Tests
- `test_report_compare.py`: Positive/Negative Fixtures neu verdrahtet
- `test_report_index.py`: Anpassung Index von 3 → 5 Runs
- Ruff-Format angewendet (Format/Style stabil)

## Fixture-Struktur (Semantik)
- `run_baseline&#47;` + `run_candidate&#47;`: CI Green Path (3 breaches, all PASS)
- `run_known_regressions_baseline&#47;`: Clean baseline (5 breaches, all PASS)
- `run_known_regressions_candidate&#47;`: 4 bekannte Regressionen (8 breaches, FAIL)
- `run_pass_all&#47;`: Golden dataset (unverändert)

## Verification
- VaR Report Regression Gates: grün (mehrere Runner-Ausführungen)
- Weitere Gates grün: Test Health Automation, Lint Gate, Policy Guards (Docs Diff/Guard/Critic), Quarto Smoke Test, Audit, CI/changes & contexts, Docs Reference Targets
- CI/tests: Python 3.9 / 3.10 / 3.11 (required contexts) — alle grün zum Merge-Zeitpunkt

## Stats
- Dateien: 17 geändert (+2,165 / -78)
- CI-Checks: 18/18 erfolgreich
- Tests: 23/23 bestanden (13 compare, 10 index)
- Merge: 2026-01-04T03:32:27Z (auto-merge squash)

## Risk
Niedrig bis mittel: Workflow-Änderung mit bewusstem Defer-Fail; funktionale Pfade bleiben getestet. Debuggability und Artefakt-Verfügbarkeit sind verbessert.

## Operator How-To
- Bei künftigen Gate-Issues: Artefakte aus dem Workflow-Run prüfen (Baseline/Candidate Reports + Compare/Index Outputs)
- Negative-Tests validieren bekannte Regressionen weiterhin über `run_known_regressions_*`
- Für neue Fixture-Szenarien: README im Fixture-Ordner als Quelle der Wahrheit nutzen

## References
- PR: #547
- Commits:
  - e880cd7 — fix(ci,risk): stabilize VAR suite regression gate and fixtures
  - 22adb71 — fix(tests): update test_report_index for 5 fixture runs
  - b1318ff — style(tests): run ruff format on test_report_compare.py
