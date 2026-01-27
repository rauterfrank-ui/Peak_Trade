# PR #999 — docs(grafana): fix DS_LOCAL uid templating in execution watch dashboard

## Summary
PR #999 wurde erfolgreich **gemerged** in `main`.

- PR: #999 (state: MERGED)
- MergedAt (UTC): 2026-01-27T07:17:45Z
- Merge-Commit: `dd9fb69` (`dd9fb692083d3b36b939cd24fbc290c122a2e86b`)
- Titel: docs(grafana): fix DS_LOCAL uid templating in execution watch dashboard

## Why
- Merge-Log / Audit-Trail konsistent halten.
- Ops-Dokumentation mit konkreten Referenzen aktualisieren.

## Changes
- Siehe PR-Diff / Commit-Inhalt

## Verification
- `git show --no-patch dd9fb69`
- `scripts/ops/validate_merge_dryrun_docs.sh` (exit 0)
- `git status` clean

## CI Checks
```
CI Health Gate (weekly_core)	pass	1m30s	https://github.com/rauterfrank-ui/Peak_Trade/actions/runs/21387959437/job/61568122968
Check Docs Link Debt Trend	pass	11s	https://github.com/rauterfrank-ui/Peak_Trade/actions/runs/21387959443/job/61568122974
Cursor Bugbot	pass	2m56s	https://cursor.com
Docs Diff Guard Policy Gate	pass	7s	https://github.com/rauterfrank-ui/Peak_Trade/actions/runs/21387959450/job/61568122967
Generate Docs Integrity Snapshot	pass	10s	https://github.com/rauterfrank-ui/Peak_Trade/actions/runs/21387959446/job/61568122919
Guard tracked files in reports directories	pass	4s	https://github.com/rauterfrank-ui/Peak_Trade/actions/runs/21387959453/job/61568122962
L4 Critic Determinism Tests	pass	4s	https://github.com/rauterfrank-ui/Peak_Trade/actions/runs/21387959451/job/61568132344
L4 Critic Replay Determinism	pass	2s	https://github.com/rauterfrank-ui/Peak_Trade/actions/runs/21387959451/job/61568132337
Lint Gate	pass	9s	https://github.com/rauterfrank-ui/Peak_Trade/actions/runs/21387959447/job/61568123010
PR Merge State Signal	pass	3s	https://github.com/rauterfrank-ui/Peak_Trade/actions/runs/21387959440/job/61568123050
Policy Critic Gate	pass	5s	https://github.com/rauterfrank-ui/Peak_Trade/actions/runs/21387959431/job/61568123020
Render Quarto Smoke Report	pass	27s	https://github.com/rauterfrank-ui/Peak_Trade/actions/runs/21387959439/job/61568122960
audit	pass	1m22s	https://github.com/rauterfrank-ui/Peak_Trade/actions/runs/21387959441/job/61568122930
changes	pass	5s	https://github.com/rauterfrank-ui/Peak_Trade/actions/runs/21387959432/job/61568123027
changes	pass	5s	https://github.com/rauterfrank-ui/Peak_Trade/actions/runs/21387959449/job/61568123057
changes	pass	5s	https://github.com/rauterfrank-ui/Peak_Trade/actions/runs/21387959451/job/61568123070
ci-required-contexts-contract	pass	5s	https://github.com/rauterfrank-ui/Peak_Trade/actions/runs/21387959449/job/61568123025
dispatch-guard	pass	5s	https://github.com/rauterfrank-ui/Peak_Trade/actions/runs/21387959433/job/61568123003
docs-reference-targets-gate	pass	7s	https://github.com/rauterfrank-ui/Peak_Trade/actions/runs/21387959455/job/61568122963
docs-token-policy-gate	pass	6s	https://github.com/rauterfrank-ui/Peak_Trade/actions/runs/21387959456/job/61568122996
evidence-pack-smoke-run	pass	3s	https://github.com/rauterfrank-ui/Peak_Trade/actions/runs/21387959432/job/61568131707
evidence-pack-validation-gate	pass	4s	https://github.com/rauterfrank-ui/Peak_Trade/actions/runs/21387959432/job/61568138812
merge-logs-sanity	pass	6s	https://github.com/rauterfrank-ui/Peak_Trade/actions/runs/21387959444/job/61568122976
required-checks-hygiene-gate	pass	11s	https://github.com/rauterfrank-ui/Peak_Trade/actions/runs/21387959438/job/61568122984
strategy-smoke	pass	5s	https://github.com/rauterfrank-ui/Peak_Trade/actions/runs/21387959449/job/61568138244
tests (3.10)	pass	3s	https://github.com/rauterfrank-ui/Peak_Trade/actions/runs/21387959449/job/61568132342
tests (3.11)	pass	3s	https://github.com/rauterfrank-ui/Peak_Trade/actions/runs/21387959449/job/61568132356
tests (3.9)	pass	3s	https://github.com/rauterfrank-ui/Peak_Trade/actions/runs/21387959449/job/61568132331
Daily Quick Health Check	skipping	0	https://github.com/rauterfrank-ui/Peak_Trade/actions/runs/21387959437/job/61568123246
Manual Health Check	skipping	0	https://github.com/rauterfrank-ui/Peak_Trade/actions/runs/21387959437/job/61568123282
R&D Experimental Health Check (Weekly)	skipping	0	https://github.com/rauterfrank-ui/Peak_Trade/actions/runs/21387959437/job/61568123271
Weekly Core Health Check	skipping	0	https://github.com/rauterfrank-ui/Peak_Trade/actions/runs/21387959437/job/61568123278
```

## Risk
Low — docs/ops only.

## Operator How-To
- Merge-Logs liegen unter: `docs/ops/`
- Docs validation:
  - `scripts/ops/validate_merge_dryrun_docs.sh`

## References
- PR: #999
- Merge-Commit: dd9fb692083d3b36b939cd24fbc290c122a2e86b
