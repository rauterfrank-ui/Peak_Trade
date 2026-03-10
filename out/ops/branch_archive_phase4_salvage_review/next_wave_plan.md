# Next-Wave Execution Plan

**Erstellt:** 2026-03-10  
**Modus:** Planung

---

## Option A — Salvage Implementation Wave (Execution-Networked)

### Ziel
Prüfen und ggf. in main integrieren: recover/p122–p132 Execution-Networked Transport-Stubs.

### Kandidaten
- recover/p122-execution-runbook-v1
- recover/p123-execution-networked-onramp-v1
- recover/p124-execution-networked-entry-contract-v1
- recover/p126-execution-networked-transport-stub-v1
- recover/p127-networked-provider-adapter-stub-v1
- recover/p128-execution-networked-transport-stub-v1
- recover/p130-networked-allowlist-stub-v1
- recover/p132-networked-transport-allow-handshake-v1

### Safety Gates
- `git log main..<branch> --oneline` pro Branch
- Kein Force-Push, kein Rebase
- PR-basierte Integration
- Keine Remote-Mutation außer via PR

### Erwartete Outputs
- `out/ops/branch_archive_phase5_salvage_exec/` — Diff-Reports, PR-Liste, Roadmap-Update
- Dokumentation: was fehlt in main, was ist Roadmap-Debt

### Go/No-Go
- **Go:** Manuelle Freigabe nach Review von high_value_salvage.md
- **No-Go:** Keine Zeit/Ressourcen → Option B priorisieren

---

## Option B — Archive/Delete Review Wave (Historical Noise)

### Ziel
backup/*, tmp/*, wip/local-*, wip/restore-* nach Prüfung löschen.

### Kandidaten
- backup/* (7)
- tmp/docs-runbook-to-finish-clean
- wip/local-uncommitted-20260128
- wip/local-unrelated-20260127-205436
- wip/restore-stash-after-pr432
- wip/restore-stash-operator-pack

### Safety Gates
- `git log main..<branch> --oneline` — muss leer sein
- `git branch -d` nur
- Kein -D
- Backup/Evidence vor Löschung

### Erwartete Outputs
- `out/ops/branch_archive_phase5_archive_exec/` — verified_delete, delete_log, post_verify

### Go/No-Go
- **Go:** Nach Verifizierung dass alle merged
- **No-Go:** Wenn unerwartete Commits → MANUAL_REVIEW

---

## Empfohlene Reihenfolge

1. **Option B zuerst** — niedriges Risiko, schneller Gewinn (12 Branches)
2. **Option A danach** — höherer Aufwand, Roadmap-relevant
