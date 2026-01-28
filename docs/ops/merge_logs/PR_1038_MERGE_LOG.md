# PR 1038 — MERGE LOG

## Summary
Docs-only Merge: Ergänzt Evidence-Pack für Tech-Debt Item **D** (Pandas FutureWarnings) und aktualisiert den Tech-Debt Backlog-Status inkl. Evidence/Findings-Verweisen.

## Why
- Tech-Debt Item **D** (Pandas FutureWarnings) soll reproduzierbar dokumentiert und für Operator/Triage nutzbar gemacht werden.
- Governance: Evidence-first, token-policy-safe Doku (inkl. Fundstellen + Verifikationspfade).

## Changes
Changed files (docs-only):
- docs&#47;ops&#47;evidence&#47;EV_TECH_DEBT_D_20260128.md
- docs&#47;TECH_DEBT_BACKLOG.md

## Verification
Post-Merge Evidence (Truth):
- PR: https://github.com/rauterfrank-ui/Peak_Trade/pull/1038
- state: MERGED
- mergedAt: 2026-01-28T06:21:14Z
- mergeCommit: b66425a478c01c1738a85f5f561e3ee18b67f791
- matched headRefOid (guarded --match-head-commit): bb3f7f25a90061d22340582101e62951d98bb1d7
- Required checks (required-only, vor Merge): alle PASS (u.a. tests 3.11, Lint Gate, docs-reference-targets-gate, audit, Policy Critic Gate, …)
- Approval Gate: exakter Kommentar "APPROVED" gefunden (approval_exact_comment_id=3809205006)

Operator verification (local):
```bash
# main up-to-date
git checkout main
git pull --ff-only origin main

# merged commit present
git show -s --oneline b66425a478c01c1738a85f5f561e3ee18b67f791

# files present
ls -la docs/TECH_DEBT_BACKLOG.md docs/ops/evidence/EV_TECH_DEBT_D_20260128.md

# docs gates (changed vs origin/main)
bash scripts/ops/pt_docs_gates_snapshot.sh --changed --base origin/main
```

## Risk
LOW — NO-LIVE / docs-only.

## Operator How-To
- Snapshot-only Verify: Siehe Commands in „Verification“ (kein Merge/Write-Workflow).

## References
- PR: https://github.com/rauterfrank-ui/Peak_Trade/pull/1038
- mergeCommit: `b66425a478c01c1738a85f5f561e3ee18b67f791`
- mergedAt: 2026-01-28T06:21:14Z
- Code-Truth PR #1036: https://github.com/rauterfrank-ui/Peak_Trade/pull/1036 (mergeCommit `7394f78cb01555f0888e300c50145140884e957f`, mergedAt 2026-01-28T05:58:36Z)
