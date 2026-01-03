# 2026-01-03 — CI Hardening Session (Required Checks + Mergeability Quickflow)

## Context
Problem: Required Check `CI/tests (3.11)` hing/pending oder wurde teils cancelled, obwohl CI-Runs success waren → Merge blockiert (Ruleset). Hypothesen: nicht-deterministische Workflow-Job-Erzeugung (paths/if), Cross-PR concurrency cancels, Context-Name Drift.

## Goals
- Required Contexts müssen **immer** materialisieren (auch docs-only) → „fast-success/stub" statt Job nicht zu erstellen.
- Concurrency PR-isoliert: `group = "${{ github.workflow }}-${{ github.event.pull_request.number || github.ref }}"`, `cancel-in-progress: true` nur innerhalb der Gruppe.
- Robust gegen flaky change detection: fail-open wenn paths-filter/checkout Probleme.

## Implementation Summary

### CI Workflow Hardening (`.github/workflows/ci.yml`)
- PR-isolierte Concurrency Group ohne Prefix.
- `changes` Job fail-open:
  - `dorny/paths-filter` `continue-on-error: true`
  - Safe output computation: bei Filter-Failure `code_changed=true` (konservativ: Tests laufen).
- Required Jobs behalten deterministische Namen:
  - `tests (${{ matrix.python-version }})` → garantiert `tests (3.11)`
  - `strategy-smoke`
- Docs-only PRs: Steps skippen, aber Jobs materialisieren.

### Guardrail / Contract
- `ci-required-contexts-contract` blockiert Drift-Szenarien:
  - job-level `if:` auf required jobs
  - fehlende explizite Namen oder fehlende Matrix-Variable im Namen
  - Matrix ohne Python 3.11
  - non-PR-isolierte Concurrency (fehlende PR-Nummer/Ref)

### Operator Documentation
- Runbook: `docs/ops/runbooks/github_rulesets_pr_reviews_policy.md`
- Operator Quickflow „mergeable: UNKNOWN"
- Verlinkung an 3 Stellen:
  - Runbook selbst
  - `docs/ops/README.md` („GitHub Branch Protection & Rulesets")
  - Kommentar in `.github/workflows/ci.yml` im „CI Required Contexts Contract" Block

## PR Timeline / Outcomes
- **PR #512** (merged): CI required checks hardening (Fail-open changes + PR concurrency). Commit: `9caf5eb` → `2034db0`
- **PR #513** (closed): initial runbook attempt (replaced)
- **PR #514** (merged): mergeable UNKNOWN operator quickflow. Commit: `25f9686` → `bced46a`
- **PR #515** (merged): CI context guard strengthening. Commit: `e38a67e` → `5a93f19`
- **PR #516** (closed): PR #512 merge log attempt (gate failure, then closed)

## Verification
- Required Checks `tests (3.11)` und `strategy-smoke` sind deterministisch vorhanden und erfolgreich bei docs-only wie code-changes.
- `ci-required-contexts-contract` läuft auf jedem PR und blockiert Drift zuverlässig.
- Mergeability `UNKNOWN` kann trotz `statusCheckRollup: SUCCESS` auftreten; Merge-Versuch liefert Source-of-Truth.

## Notes
- Ruleset/Branch protection zeigte „PR reviews required: true, count: 0" (PR-Flow erzwingen, ohne Approvals). Nicht zwingend blocker, aber potenziell verwirrend; Runbook dokumentiert das sauber.

## Final State (main branch)
```
5a93f19  ops(ci): strengthen required context contract guard (#515)
bced46a  docs(ops): add mergeable UNKNOWN operator quickflow (#514)
2034db0  feat(execution): add fill idempotency guard for live retry/replay safety (#512)
```

## Operator Quickflow Reference
Bei `mergeable: UNKNOWN`:
1. Prüfe Required Status Checks SUCCESS (PR UI → Checks)
2. Prüfe Ruleset-Merge-Anforderungen (PR UI → „Merge requirements")
3. CLI-Snapshot (ohne Watch): `gh pr view <N> --json mergeable,mergeStateStatus,reviewDecision,statusCheckRollup`
4. Wenn Rollup SUCCESS: Merge-Versuch per `gh pr merge <N> --squash --delete-branch`
5. Falls blockiert: Fehlermeldung ist Source-of-Truth
6. Nur bei wiederkehrender Blockade: Ruleset/Branch-Policy korrigieren

Siehe: `docs/ops/runbooks/github_rulesets_pr_reviews_policy.md`
