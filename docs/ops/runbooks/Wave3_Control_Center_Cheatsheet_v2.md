# Peak_Trade — Wave3 Control Center Cheatsheet v2 (mit aktueller PR-Queue)
Stand: 2026-01-08 (Europe/Berlin) | Quelle: aktuelle gh pr list Ausgabe im Chat

## 1) Sofort-Plan (risiko-minimiert)
**P0 (jetzt):** PR **#608** (mergeable) — lokale Änderungen einordnen (commit/push oder verwerfen), dann Checks prüfen.  
**P1:** PR **#604** (mergeable, docs-only) — Checks → Diff → Merge.  
**P2:** PR **#592** (mergeable, Tier-C-relevant) — Checks (Lint/Audit) + Diff/Review → Merge.  
**P3:** Konflikt-Block (CONFLICTING) nacheinander via Checkout → Rebase → Regenerate/Resolve → Push → Checks → Merge: **#588, #590, #591, #587, #601, #598**.  
**Backlog:** **#586** (DRAFT) parken.

## 2) Pre-Flight (immer zuerst)
Wenn du in `>`, `dquote>`, heredoc hängst: **Ctrl-C**.
```bash
cd /Users/frnkhrz/Peak_Trade
pwd && git rev-parse --show-toplevel && git status -sb
```

## 3) Aktuelle PR-Queue (Top 10)
| PR | Branch | Status | Risiko | Tier | Next Action |
|---:|---|---|---|---|---|
| 608 | docs/pr607-merge-log | MERGEABLE | Low→Med (lokale Änderungen!) | A | Diff der lokalen Änderung prüfen → commit/push ODER restore → Checks → merge |
| 604 | docs/ops-evidence-linking | MERGEABLE | Low | B | Checks → Diff (Top) → merge |
| 592 | docs/frontdoor-roadmap-runner | MERGEABLE | Med | C | Checks (Lint/Audit) verifizieren → Diff/Review → merge |
| 601 | evidence-index-v0.1 | CONFLICTING | Med | B | Rebase/Regenerate (Index/Refs) → Checks → merge |
| 598 | docs/ops-placeholder-templates | CONFLICTING | Low→Med | X/B | Rebase/Regenerate → merge |
| 591 | restore/wave3-runbooks-core | CONFLICTING | Med | A | Rebase/Regenerate → merge |
| 590 | docs/ops-pr-85-merge-log | CONFLICTING | Low | A | Rebase/Regenerate → merge |
| 588 | docs/ops/pr-93-merge-log | CONFLICTING | Low | A | Rebase/Regenerate → merge |
| 587 | docs/merge-log-pr-350... | CONFLICTING | Low→Med | A/C | Rebase/Regenerate → Checks → merge |
| 586 | restore/w3-restore-queue | DRAFT + CONFLICTING | Backlog | A | Parken, erst später |

## 4) Entscheidungsbaum (PR → nächster Command)
### A) MERGEABLE (docs-only)
```bash
export GH_PAGER=cat PAGER=cat LESS='-FRX'
gh pr view <N> --json statusCheckRollup --jq '.statusCheckRollup[]|{name:.name,conclusion:.conclusion}'
```
```bash
gh pr diff <N> | sed -n '1,200p'
```
```bash
gh pr merge <N> --squash --delete-branch
```
```bash
git checkout main && git pull --ff-only && git status -sb
```

### B) MERGEABLE (Tier C: scripts/workflows, Lint/Audit)
- Erst **Checks** (insb. Lint/Audit) + **Diff/Review**, dann merge.

### C) CONFLICTING
```bash
gh pr checkout <N>
```
```bash
git fetch origin && git rebase origin/main
```
Wenn Konflikte: **Regenerate/Resolve via Agent** (minimal diff) → `git push` → Checks → Merge.

## 5) Tier B Evidence v0.1
- `EV-20260103-CI-HARDENING` existiert bereits: verifizieren (Links/Claims/Refs).
- Nächster Kandidat: Wave3 Session / Runbooks Core / Merge Logs.

## 6) Finish-Check
```bash
gh pr list --state open --limit 50
```
- main clean + CI grün  
- Evidence Index v0.1 gemerged  
- Audit trail clean (Merge Logs/Indizes konsistent)
