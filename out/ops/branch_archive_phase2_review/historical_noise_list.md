# Historical Noise List

**Erstellt:** 2026-03-10  
**Modus:** Review-only

---

## Vermutlich entbehrlich (nach Prüfung)

### backup/* (9 Branches)
Explizite Backups mit Datumsstempel. Nach Verifizierung, dass Inhalt in main oder anderem Branch ist, löschbar.

| Branch | Typ |
|--------|-----|
| backup/docs/ev-strategy-risk-telemetry-* | Docs-Backup |
| backup/docs_merge-log-* | Merge-Log-Backup |
| backup/local-main-diverged-* | Pre-Sync-Backup |
| backup/local-main-pre-sync-770_* | Pre-Sync-Backup |
| backup/pr394-before-squash | PR-Backup |
| backup/pr60-local-* | PR-Backup |
| backup/pr642-pre-rebase-* | Rebase-Backup |
| backup/slice2-staged-* | Staged-Backup |

### tmp/* (2 Branches)
| Branch | Hinweis |
|--------|---------|
| tmp/docs-runbook-to-finish-clean | Temporär |
| tmp/stack-test | Temporär |

### wip/* (5 Branches)
| Branch | Hinweis |
|--------|---------|
| wip/local-uncommitted-* | Uncommitted |
| wip/local-unrelated-* | Unrelated |
| wip/pausepoint-branch-cleanup-recovery-* | Pausepoint |
| wip/restore-stash-after-pr432 | Stash-Restore |
| wip/restore-stash-operator-pack | Stash-Restore |
| wip/salvage-code-tests-untracked-* | Salvage |
| wip/salvage-dirty-main-* | Salvage |
| wip/untracked-salvage-* | Salvage |

### Cursor-Namen (46 Branches)
z. B. admiring-gagarin, adoring-margulis, … — typischerweise Cursor-generierte Namen. Wenn merged → löschbar.

---

## Empfehlung

Vor Löschung: `git log main..<branch> --oneline` ausführen. Leer = merged, sicher mit `git branch -d` löschbar.
