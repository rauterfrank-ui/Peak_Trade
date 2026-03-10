# Manual Deep Review — Branches

**Erstellt:** 2026-03-10  
**Modus:** Review-only

---

## recover-ops (20 Branches)

Gruppenweise Prüfung empfohlen. Keine automatische Klassifikation möglich.

| Gruppe | Branches |
|--------|----------|
| Kickoff/Roadmap | recover/p13-kickoff, recover/p22-roadmap-runbook-merge |
| Workbook/Exchange | recover/p101-workbook-checklists-stop-playbook-v1, recover/p105-exchange-execution-research-v1, recover/p105-exchange-shortlist-v1, recover/p105-readme-pointer-pin-v1 |
| Adapter/Selector | recover/p111-execution-adapter-selector-v1 |
| Online Readiness | recover/p64-online-readiness-runner-v1, recover/p65-online-readiness-loop-runner-v1, recover/p66-online-readiness-operator-entrypoint-v1 |
| Env/Contract | recover/p75-p72-env-contract-tests-v1 |
| Dashboard/Audit | recover/p92-audit-snapshot-runner-v1, recover/p94-p93-status-dashboard-retention-v1 |
| Dry-Run/Sandbox | recover/p97-p96-dry-run-sandbox-smoke |
| Plist/Launchd | recover/p99-guarded-plist-workingdir-v1 |
| PR Closeout | recover/pr-ops-v1-closeout-ff-fix, recover/pr-trigger-triage-v1 |
| Protected (Phase 3) | recover/p118-sha256sums-no-xargs-v1, recover/p54-switch-layer-routing-v1 |

---

## stash-wip-salvage (4 Branches)

Stash- und WIP-Branches. Inhalt vor Archiv prüfen.

| Branch |
|--------|
| recover/stash-2 |
| recover/stash-3 |
| wip/salvage-code-tests-untracked-20251224_082521 |
| wip/salvage-dirty-main-20260118 |
| wip/untracked-salvage-20251224_081737 |

---

## unknown (3 Branches)

| Branch | Hinweis |
|--------|---------|
| feat/salvage-manual-p22-roadmap-runbook-merge | Einziger verbleibender feat/salvage-* (nicht merged) |
| recover/fix-p76-result-path-in-ticks | Fix-Branch |
| wip/untracked-salvage-20251224_081737 | WIP-Salvage |

---

## Prüfschritte

1. `git log main..<branch> --oneline` — Commits die nicht in main sind
2. `git diff main..<branch> --stat` — Umfang der Änderungen
3. Entscheidung: SALVAGE (PR), ARCHIVE (löschen nach Backup), oder HOLD (weiter beobachten)
