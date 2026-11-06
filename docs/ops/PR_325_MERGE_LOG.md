# PR #325 — docs(ops): move drift guard operator notes to docs/ops/

## Summary
PR #325 wurde in `main` gemerged.
- PR: https://github.com/rauterfrank-ui/Peak_Trade/pull/325
- Merge-Commit: `21dc8ab`
- MergedAt (UTC): 2025-12-25T08:06:41Z
- Diff: +1737 / −372
- Files changed: 11
- Commits: 4

## Why
- Ops-Dokumentation konsolidieren: Drift-Guard Operator Notes gehören nach `docs/ops/`.
- Backward-Compatibility: Redirect-Stub im Repo-Root verhindert "tote Links".
- Nebenbei: Component VaR Reporting scaffold (WIP) wurde mitgezogen.

## Changes
- **Docs/Ops Re-Org**
  - Move der Drift-Guard Operator Notes nach `docs/ops/`
  - Referenzen aktualisiert (Quick Start / README / PR-Workflow / Merge-Log Referenzen)
  - Redirect-Stub im Repo-Root hinzugefügt (für externe Links / alte Pfade)
- **Risk / Reporting (WIP)**
  - Component VaR Report Scaffold (Script + Modul + Tests + Docs)
  - Ruff-Format-Fix für `component_var_report.py`

## Verification
Siehe `gh pr checks 325` Output:

```text
CI Health Gate (weekly_core)	pass	59s	https://github.com/rauterfrank-ui/Peak_Trade/actions/runs/20501600112/job/58909651210
Docs Diff Guard Policy Gate	pass	6s	https://github.com/rauterfrank-ui/Peak_Trade/actions/runs/20501600123/job/58909651245
Guard tracked files in reports directories	pass	5s	https://github.com/rauterfrank-ui/Peak_Trade/actions/runs/20501600121/job/58909651180
Lint Gate	pass	8s	https://github.com/rauterfrank-ui/Peak_Trade/actions/runs/20501600132/job/58909651202
Policy Critic Gate	pass	1m0s	https://github.com/rauterfrank-ui/Peak_Trade/actions/runs/20501600104/job/58909651191
Render Quarto Smoke Report	pass	22s	https://github.com/rauterfrank-ui/Peak_Trade/actions/runs/20501600118/job/58909651183
audit	pass	2m44s	https://github.com/rauterfrank-ui/Peak_Trade/actions/runs/20501600128/job/58909651215
lint	pass	12s	https://github.com/rauterfrank-ui/Peak_Trade/actions/runs/20501600101/job/58909651186
strategy-smoke	pass	1m12s	https://github.com/rauterfrank-ui/Peak_Trade/actions/runs/20501600119/job/58909840876
tests (3.11)	pass	4m54s	https://github.com/rauterfrank-ui/Peak_Trade/actions/runs/20501600119/job/58909651265
Daily Quick Health Check	skipping	0	https://github.com/rauterfrank-ui/Peak_Trade/actions/runs/20501600112/job/58909651360
Manual Health Check	skipping	0	https://github.com/rauterfrank-ui/Peak_Trade/actions/runs/20501600112/job/58909651283
R&D Experimental Health Check (Weekly)	skipping	0	https://github.com/rauterfrank-ui/Peak_Trade/actions/runs/20501600112/job/58909651274
Weekly Core Health Check	skipping	0	https://github.com/rauterfrank-ui/Peak_Trade/actions/runs/20501600112/job/58909651288
```

✅ GitHub Actions: **Alle Checks passed**

Wichtige Checks (alle SUCCESS):
- tests (3.11)
- strategy-smoke
- audit
- CI Health Gate (weekly_core)
- Policy Critic Gate
- Lint Gate
- Docs Diff Guard Policy Gate

## Risk
**Low → Medium**
- Docs-Umzug + Redirect ist low risk.
- Medium nur insofern, als **WIP VaR Reporting Code** samt Tests/Docs in `main` landet (aber ohne Live/Execution-Eingriffe).

## Operator How-To
- Neue Quelle der Wahrheit: `docs/ops/REQUIRED_CHECKS_DRIFT_GUARD_v1_OPERATOR_NOTES.md`
- Alte Links funktionieren via Redirect-Stub weiter (Repo-Root).
- Für Component VaR Reporting: als **WIP** behandeln (noch keine "prod-ready" Guarantees).

## Commits in PR
- `f23fcf6` — docs(ops): move drift guard operator notes to docs/ops/
- `33e6289` — docs(ops): update all references to moved operator notes
- `c2cca65` — wip(risk): component VaR report scaffold (script+module+tests+docs)
- `07c9580` — fix(risk): format component_var_report.py with ruff

---
*Generated: 2025-12-25T08:12:22.852284Z*
