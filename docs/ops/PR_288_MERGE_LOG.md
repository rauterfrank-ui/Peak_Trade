# PR #288 — feat(ops): add merge-log health checks to ops doctor

## Summary
PR #288 wurde erfolgreich **gemerged** in `main`.

- PR: #288 (state: MERGED)
- MergedAt (UTC): 2025-12-24T23:21:50Z
- Merge-Commit: `6384092` (`638409292ae0c902a71fa8d7f557ae4a43136e8f`)
- Titel: feat(ops): add merge-log health checks to ops doctor

## Why
- Merge-Log / Audit-Trail konsistent halten.
- Ops-Dokumentation mit konkreten Referenzen aktualisieren.

## Changes
- Siehe PR-Diff / Commit-Inhalt

## Verification
- `git show --no-patch 6384092`
- `scripts/ops/validate_merge_dryrun_docs.sh` (exit 0)
- `git status` clean

## CI Checks
```
CI Health Gate (weekly_core)	pass	56s	https://github.com/rauterfrank-ui/Peak_Trade/actions/runs/20495370934/job/58894188956
Guard tracked files in reports directories	pass	4s	https://github.com/rauterfrank-ui/Peak_Trade/actions/runs/20495370936/job/58894188935
Lint Gate	pass	6s	https://github.com/rauterfrank-ui/Peak_Trade/actions/runs/20495370938/job/58894188964
Policy Critic Gate	pass	52s	https://github.com/rauterfrank-ui/Peak_Trade/actions/runs/20495370943/job/58894188974
Render Quarto Smoke Report	pass	23s	https://github.com/rauterfrank-ui/Peak_Trade/actions/runs/20495369519/job/58894186089
Render Quarto Smoke Report	pass	36s	https://github.com/rauterfrank-ui/Peak_Trade/actions/runs/20495370933/job/58894188948
audit	pass	2m46s	https://github.com/rauterfrank-ui/Peak_Trade/actions/runs/20495370945/job/58894188973
strategy-smoke	pass	1m12s	https://github.com/rauterfrank-ui/Peak_Trade/actions/runs/20495370944/job/58894318386
Daily Quick Health Check	skipping	0	https://github.com/rauterfrank-ui/Peak_Trade/actions/runs/20495370934/job/58894189015
Manual Health Check	skipping	0	https://github.com/rauterfrank-ui/Peak_Trade/actions/runs/20495370934/job/58894189017
R&D Experimental Health Check (Weekly)	skipping	0	https://github.com/rauterfrank-ui/Peak_Trade/actions/runs/20495370934/job/58894188985
Weekly Core Health Check	skipping	0	https://github.com/rauterfrank-ui/Peak_Trade/actions/runs/20495370934/job/58894189029
tests (3.11)	pass	5m6s	https://github.com/rauterfrank-ui/Peak_Trade/actions/runs/20495370944/job/58894189002
```

## Risk
Low — docs/ops only.

## Operator How-To
- Merge-Logs liegen unter: `docs/ops/`
- Docs validation:
  - `scripts/ops/validate_merge_dryrun_docs.sh`

## References
- PR: #288
- Merge-Commit: 638409292ae0c902a71fa8d7f557ae4a43136e8f
