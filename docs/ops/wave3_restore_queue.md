# Wave3 Restore Queue – Peak_Trade

**Erstellt:** 2026-01-06  
**Status:** DRAFT – Pending Operator Review  
**Governance:** Safety-first, auditierbar, ein Branch = ein Kandidat

---

## Executive Summary

**Kontext:**
- Wave2 abgeschlossen (siehe Wave2 closeout docs)
- 0 offene PRs derzeit
- 73 ungemergte Remote-Branches identifiziert
- Analyse nach Typ, Impact, Risk für Restore-Priorisierung

**Ergebnis:**
- **Tier A (Safe docs/tooling):** 27 Kandidaten → Auto-merge möglich
- **Tier B (Tests/Refactor):** 12 Kandidaten → Review + minimale Tests
- **Tier C (Src/Config/Risk):** 8 Kandidaten → Explizite Freigabe erforderlich
- **Excluded (WIP/Stash):** 26 Branches → Archiv oder löschen

---

## Tier A: Docs & Tooling (Zero Runtime Impact)

**Merge-Strategie:** Auto-merge nach Conflict-Check  
**Verifikation:** `make docs-validate` + `git log --oneline -5`

### A1: Merge Log Backlog (11 Branches)

| Branch | Last Update | Subject | Verify |
|--------|-------------|---------|--------|
| docs/add-pr569-readme-link | 2026-01-05 | PR #569 merge log to README index | Check README links |
| docs/merge-log-pr488 | 2026-01-01 | Merge log for PR #488 | Check docs/ops/ |
| docs/cursor-multi-agent-phase4-runner | 2026-01-01 | PR #480 merge log + index | Check index |
| docs/merge-log-pr-350-docs-reference-targets-golden-corpus | 2025-12-25 | Merge log + path fixes | Check paths |
| docs/ops-pr206-merge-log | 2025-12-21 | Legacy merge log backlog | Check legacy docs |
| docs/ops-merge-both-prs-dryrun-workflow | 2025-12-23 | DRY_RUN workflow docs | Check workflow |
| docs/ops/pr-87-merge-log | 2025-12-16 | PR #87 merge log | Check docs/ops |
| docs/ops/pr-92-merge-log | 2025-12-16 | PR #92 merge log | Check docs/ops |
| docs/ops/pr-93-merge-log | 2025-12-16 | PR #93 merge log | Check docs/ops |
| docs/pr-76-merge-log | 2025-12-16 | PR #76 merge log | Check docs/ops |
| docs/ops-pr-85-merge-log | 2025-12-16 | PR #85 merge log | Check docs/ops |

**Operator Notes:**
- Pure documentation, no code impact
- Kann batch gemerged werden (Konflikte unwahrscheinlich)
- Post-merge: `git log --grep="merge log" --oneline | head -15`

---

### A2: Runbooks & Standards (6 Branches)

| Branch | Last Update | Subject | Impact |
|--------|-------------|---------|--------|
| docs/github-rulesets-runbook | 2026-01-03 | GitHub rulesets PR/review policy runbook | Policy docs |
| docs/frontdoor-roadmap-runner | 2025-12-31 | Live execution roadmap runner appendix | Roadmap |
| docs/fix-moved-script-paths-phase1 | 2025-12-30 | Fix moved script paths in docs | Path refs |
| docs/ops-doctor-noise-free-standard | 2025-12-27 | Noise-Free standard + uv export flags | Ops standard |
| docs/ops-worktree-policy | 2025-12-16 | Worktree policy standard | Policy |
| docs/ops-audit-logs-convention | 2025-12-15 | Audit log convention | Convention |

**Operator Notes:**
- Operational runbooks und Standards
- Keine Code-Änderungen
- Post-merge: Check `docs/ops/` + `docs/runbooks/` Struktur

---

### A3: Roadmaps & Housekeeping (5 Branches)

| Branch | Last Update | Subject | Category |
|--------|-------------|---------|----------|
| reboot/from-pr-380 | 2026-01-03 | Reboot roadmap v2 + plan + migration notes | Roadmap |
| docs/ops-docs-reference-targets-supported-formats | 2025-12-25 | Reference targets supported formats | Docs |
| docs/pr-74-delivery-note | 2025-12-16 | PR #75 as delivery transport for PR #74 | Meta |
| docs/pr-66-finalization | 2025-12-16 | Finalize PR #66 final report | Report |
| docs/pr-63-finalization | 2025-12-16 | Finalize PR #63 final report | Report |

**Operator Notes:**
- Roadmaps, Berichte, Meta-Dokumentation
- Safe to merge
- Check `docs/roadmaps/` und `docs/reports/`

---

### A4: Duplicate/Stale Doc Branches (5 Branches)

| Branch | Last Update | Subject | Status |
|--------|-------------|---------|--------|
| `beautiful-ritchie` | 2025-12-18 | Wave A+B stack complete, deployment runbook | Dupe? |
| `busy-cerf` | 2025-12-18 | Wave A+B stack complete, deployment runbook | Dupe? |
| `determined-matsumoto` | 2025-12-18 | Wave A+B stack complete, deployment runbook | Dupe? |
| `keen-aryabhata` | 2025-12-18 | Wave A+B stack complete, deployment runbook | Dupe? |
| `serene-elbakyan` | 2025-12-18 | Wave A+B stack complete, deployment runbook | Dupe? |

**Operator Notes:**
- **WARNING:** 5 Branches mit identischem Subject/Datum
- Vermutlich retries/duplicates aus CI/Cursor
- **Action:** Diff gegen main, dann merge EINEN oder löschen alle
- `git diff main..origin&#47;beautiful-ritchie --stat`

---

### A5: Docs Conflict Merges (4 Branches)

| Branch | Last Update | Subject | Risk |
|--------|-------------|---------|------|
| `condescending-rubin` | 2025-12-18 | Merge main into docs/ops-pr-70-final-report | Conflicts? |
| `dazzling-gates` | 2025-12-18 | Merge main into docs/ops-pr-70-final-report | Conflicts? |
| `sweet-kapitsa` | 2025-12-18 | Merge main into docs/ops-pr-70-final-report | Conflicts? |
| `magical-tesla` | 2025-12-18 | Merge main into docs/ops-pr-70-final-report | Conflicts? |

**Operator Notes:**
- Merge-Conflict Resolution Branches
- **CHECK FIRST:** Ist PR #70 schon in main?
- If yes → diese Branches obsolete → DELETE
- If no → merge eine davon

---

### A6: Tooling & Ops (1 Branch)

| Branch | Last Update | Subject | Impact |
|--------|-------------|---------|--------|
| `feat/ops-merge-log-tooling-v1` | 2025-12-31 | Merge log tooling v1 (generator + hygiene check) | Tooling |

**Operator Notes:**
- Ops tooling, nicht live-critical
- Verify: `scripts/ops/` neue Tools vorhanden
- Test: Dry-run mit existing merge log

---

## Tier B: Tests, Refactoring, CI (Minimal Runtime Risk)

**Merge-Strategie:** Review + pytest suite  
**Verifikation:** `make test` + betroffene Module prüfen

### B1: CI/Test Infrastructure (5 Branches)

| Branch | Last Update | Subject | Category |
|--------|-------------|---------|----------|
| `feat/execution-pipeline-fill-idempotency` | 2026-01-03 | Harden required checks (fail-open + concurrency) | CI |
| `fix/ci-required-checks-docs-prs` | 2025-12-26 | Trigger checks | CI |
| `chore/github-guardrails-p0-only` | 2025-12-26 | Ruff format (audit uses ruff not black) | Tooling |
| `chore/github-guardrails-p0` | 2025-12-23 | Complete P0 guardrails setup | GitHub |
| `test/p0-guardrails-drill` | 2025-12-23 | Drill PR for guardrails validation | Test |

**Operator Notes:**
- CI workflow changes, nicht runtime
- Aber: Kann CI-Verhalten ändern → Review-pflicht
- Test: Trigger CI on dummy branch, check output

---

### B2: Chore & Tooling (3 Branches)

| Branch | Last Update | Subject | Risk |
|--------|-------------|---------|------|
| `chore/tooling-uv-ruff` | 2025-12-17 | Add uv + ruff, modernize Python setup | Tooling |
| `chore/cleanup-gitignore-reports` | 2025-12-16 | Document reports/ generated artifacts policy | .gitignore |
| `pr-72` | 2025-12-16 | Enforce unicode guard in PR report automation | Ops script |

**Operator Notes:**
- Tooling modernization
- `chore/tooling-uv-ruff`: Check pyproject.toml changes
- Test: `make lint`, `make format`

---

### B3: Fix/Hotfix (3 Branches)

| Branch | Last Update | Subject | Scope |
|--------|-------------|---------|-------|
| `fix/requirements-txt-sync-correct-flags` | 2025-12-27 | Correct requirements.txt sync check fix-hint | requirements.txt |
| `nervous-wilbur` | 2026-01-04 | Move quarto sources to templates, restore /reports/ ignore | Reporting |
| `nervous-wilbur-local` | 2026-01-04 | (Same as nervous-wilbur) | Reporting |

**Operator Notes:**
- `nervous-wilbur` vs `-local`: Duplicates? Pick one
- `fix/requirements-txt-sync`: Check gegen actual requirements.txt
- Test: `uv pip compile pyproject.toml --compare`

---

### B4: Test Infrastructure (1 Branch)

| Branch | Last Update | Subject | Type |
|--------|-------------|---------|------|
| `test/ci-gate-block-trigger` | 2025-12-12 | Add AWS credentials pattern for CI gate | Test |

**Operator Notes:**
- Test-only, no runtime code
- Check: tests/ci/ oder .github/workflows/

---

## Tier C: Source Code, Config, Risk (Explicit Approval Required)

**Merge-Strategie:** Full Review + Extended Tests + Operator Signoff  
**Verifikation:** `make test-full` + integration tests + manual spot-check

### C1: Risk & Execution Features (3 Branches)

| Branch | Last Update | Subject | Risk Level |
|--------|-------------|---------|------------|
| `pr-334-rebase` | 2026-01-03 | Canonical Order contract for risk gate | HIGH – Risk |
| `feat/risk-liquidity-gate-v1` | 2025-12-25 | Merge log + liquidity gate paper config | MEDIUM – Risk |
| `feat/governance-g4-telemetry-automation` | 2025-12-15 | G4 telemetry automation suite | MEDIUM – Telemetry |

**Operator Notes:**
- **DO NOT AUTO-MERGE**
- `pr-334-rebase`: Core execution/risk contract → Full regression
- `feat/risk-liquidity-gate-v1`: Config only? Check src/ changes
- Test Plan: backtest suite + paper trading smoke test

---

### C2: Strategy & Backtest (2 Branches)

| Branch | Last Update | Subject | Impact |
|--------|-------------|---------|--------|
| `feat/phase-9b-rolling-backtests` | 2025-12-29 | Merge main into feat (resolve conflicts) | Backtest |
| `feat/strategy-layer-vnext-tracking` | 2025-12-23 | Add tracker hooks to BacktestEngine | Engine |

**Operator Notes:**
- `feat/phase-9b-rolling-backtests`: Check conflict resolution quality
- `feat/strategy-layer-vnext-tracking`: Engine hooks → regression tests
- Test: `make test-backtests`

---

### C3: Data Lake & Observability (3 Branches)

| Branch | Last Update | Subject | Category |
|--------|-------------|---------|----------|
| `vigilant-thompson` | 2025-12-18 | Minimal data lake with DuckDB support | P2 feature |
| `stupefied-montalcini` | 2025-12-18 | (Same as vigilant-thompson) | Dupe? |
| `vibrant-antonelli` | 2025-12-19 | Suppress MLflow startup warnings | Dev env |

**Operator Notes:**
- Data lake branches: Check if already merged via other PR
- `vibrant-antonelli`: Dev env only, low risk but check MLflow impact
- Dupes: `vigilant-thompson` vs `stupefied-montalcini` → Diff zuerst

---

### C4: Live Status & Reporting (2 Branches)

| Branch | Last Update | Subject | Scope |
|--------|-------------|---------|-------|
| `feat/phase-57-live-status-snapshot-builder-api` | 2025-12-16 | Snapshot builder + JSON/HTML endpoints | Live status |
| `cool-williamson` | 2025-12-18 | Evidence chain artifacts + MLflow/Quarto reporting | Reporting |

**Operator Notes:**
- `feat/phase-57`: Live status API → security review (exposed endpoints?)
- `cool-williamson`: Reporting infrastructure, likely safe but check src/
- Test: Launch test runner, check new endpoints

---

## Tier X: Excluded (WIP/Stash/Obsolete)

**Action:** Archive oder DELETE nach Review

### X1: WIP Stash Archives (6 Branches)

```
wip/stash-archive-20251227_010347_3
wip/stash-archive-20251227_010344_2
wip/stash-archive-20251227_010341_1
wip/stash-archive-20251227_010316_0
wip/untracked-salvage-20251224_081737
wip/salvage-code-tests-untracked-20251224_082521
```

**Operator Notes:**
- Stash archives, nicht für merge gedacht
- **Check:** Enthält code der gebraucht wird?
- If yes → extrahieren in new branch
- If no → DELETE remote branches

---

### X2: Copilot & Obsolete (3 Branches)

```
copilot/add-health-check-system-again  (2025-12-18)
laughing-shockley  (2025-12-16)
laughing-hawking   (2025-12-17)
hotfix/policy-critic-ci-gate  (2025-12-12)
```

**Operator Notes:**
- Copilot experiment branches
- `hotfix/policy-critic-ci-gate`: Hotfix validated → merged or obsolete?
- Check history, dann DELETE

---

### X3: Docs Index Merges (1 Branch)

```
docs/ops-index-pr-61-63  (2025-12-16 – merge main)
```

**Operator Notes:**
- Merge conflict branch für docs index
- Check if PR #61/#63 in main → if yes DELETE

---

### X4: CI Fast Lane (2 Branches)

```
ci-fastlane-impl  (2025-12-15)
ci/fast-lane-matrix  (2025-12-15)
```

**Operator Notes:**
- Fast lane CI experiments
- Check if merged via other PR → likely obsolete

---

### X5: P2 Features (4 Branches)

```
loving-gauss  (2025-12-18 – ADR_0001 finalize)
feat/p2-otel-minimal  (2025-12-18 – reporting cleanup)
competent-hawking  (2025-12-18 – evidence chain)
```

**Operator Notes:**
- P2 (lower priority) features
- Check gegen roadmap → defer to Wave4?

---

### X6: Folder Cleanup (1 Branch)

```
chore/folder-cleanup  (2025-12-11)
```

**Operator Notes:**
- Old cleanup branch
- Check if cleanup done → DELETE

---

## Wave3 Execution Plan

### Phase 1: Tier A Docs Blitz (Days 1-2)

**Target:** Merge all 27 Tier A branches  
**Approach:** Batch merge with conflict checks

```bash
# Example workflow:
for branch in docs/add-pr569-readme-link docs/merge-log-pr488 ...; do
  git checkout -b restore/$branch origin/$branch
  git rebase main
  # If clean:
  gh pr create --title "Wave3: restore $branch" --body "Tier A docs restore"
  gh pr merge --auto --squash
done
```

**Verification:**
- `make docs-validate`
- `git log --oneline --since="2 days ago" | wc -l` → expect ~27
- Manual spot-check: `docs/ops/`, `docs/runbooks/`

---

### Phase 2: Tier B Tests/CI (Days 3-4)

**Target:** Merge 12 Tier B branches  
**Approach:** One-by-one with CI verification

```bash
# Per branch:
git checkout -b restore/$branch origin/$branch
make test
# If pass:
gh pr create + review + merge
```

**Verification:**
- CI green on each PR
- `make test-full` nach letztem merge
- Check `.github/workflows/` changes

---

### Phase 3: Tier C Source Review (Days 5-7)

**Target:** Review 8 Tier C branches  
**Approach:** Full review + signoff

1. Diff review: `git diff main..origin&#47;$branch`
2. Risk assessment per branch
3. Test plan execution
4. Operator signoff required
5. Manual merge with extended verification

**Verification:**
- `make test-backtests`
- Paper trading smoke test für risk-relevante branches
- Rollback plan documented

---

### Phase 4: Cleanup (Day 8)

**Target:** Delete Tier X branches (26 branches)

```bash
# Nach Review:
git push origin --delete wip/stash-archive-20251227_010347_3
# ... repeat für alle X branches
```

**Verification:**
- `git branch -r | grep "origin&#47;" | wc -l` → expect ~20 (nur noch merged)
- Document deleted branches in Wave3 closeout

---

## Success Metrics

| Metric | Target | Verify |
|--------|--------|--------|
| Tier A merged | 27 | `git log --grep="Wave3.*Tier A"` |
| Tier B merged | 12 | `git log --grep="Wave3.*Tier B"` |
| Tier C reviewed | 8 | Operator signoff docs |
| Branches deleted | 26 | `git branch -r` count |
| CI green | 100% | GitHub Actions history |
| Docs valid | Pass | `make docs-validate` |
| Tests pass | 100% | `make test-full` |

---

## Risk Mitigation

### Pre-merge Checklist

- [ ] Branch rebased onto current main
- [ ] No conflicts
- [ ] CI passes (for non-docs)
- [ ] Tier classification reviewed
- [ ] Verification plan documented

### Rollback Plan

```bash
# If merge causes issues:
git revert <commit-hash>
# Or:
git reset --hard origin/main  (on feature branch)
# Document in Wave3 incident log
```

### Escalation

- Tier A/B issues → ops/wave3_issues.md
- Tier C issues → HALT, operator signoff required
- Production impact → STOP, invoke kill switch

---

## Operator Signoff

**Prepared by:** Cursor Agent  
**Review required by:** Human Operator  
**Approval gate:** Tier C branches require explicit GO

**Sign here after review:**
```
[ ] Wave3 Restore Queue reviewed
[ ] Tier classification validated
[ ] Execution plan approved
[ ] Risk mitigation understood

Operator: _______________  Date: ___________
```

---

## Appendix: Full Branch Inventory

### Summary Stats
- Total unmerged branches: 73
- Tier A (docs/tooling): 27
- Tier B (tests/ci): 12
- Tier C (src/config): 8
- Tier X (exclude): 26

### Branch Age Distribution
- < 1 week old: 3 branches
- 1-2 weeks: 8 branches
- 2-4 weeks: 42 branches
- > 4 weeks: 20 branches

### Branch Prefix Stats
- `docs/*`: 24 branches
- `feat/*`: 8 branches
- `wip/*`: 6 branches
- `chore/*`: 6 branches
- `fix/*`: 3 branches
- `test/*`: 2 branches
- Auto-generated names: 24 branches

---

**End of Wave3 Restore Queue**  
**Next:** Execute Phase 1 upon operator approval
