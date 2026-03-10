# High-Value Salvage Prioritization

**Erstellt:** 2026-03-10  
**Modus:** Review-only

---

## SALVAGE_NOW — Execution-Networked (p123–p132)

**Rationale:** salvage_priority_list.md und POST_SCAN_DECISION_REPORT (referenziert) nennen p125–p139 Execution-Networked als „Fragmentarisch, KEEP: roadmap debt; dokumentieren“. Die feat/salvage-* Varianten wurden Phase 3 gelöscht (merged). Die recover/* Varianten sind die einzigen verbleibenden Träger dieser Stubs.

| Branch | Klassifikation |
|--------|----------------|
| recover/p122-execution-runbook-v1 | SALVAGE_REVIEW_REQUIRED |
| recover/p123-execution-networked-onramp-v1 | SALVAGE_REVIEW_REQUIRED |
| recover/p124-execution-networked-entry-contract-v1 | SALVAGE_REVIEW_REQUIRED |
| recover/p126-execution-networked-transport-stub-v1 | SALVAGE_REVIEW_REQUIRED |
| recover/p127-networked-provider-adapter-stub-v1 | SALVAGE_REVIEW_REQUIRED |
| recover/p128-execution-networked-transport-stub-v1 | skipped_protected |
| recover/p130-networked-allowlist-stub-v1 | SALVAGE_REVIEW_REQUIRED |
| recover/p132-networked-transport-allow-handshake-v1 | SALVAGE_REVIEW_REQUIRED |

**Nächster Schritt:** `git log main..<branch> --oneline` pro Branch. Wenn nicht leer → diff prüfen, ggf. PR vorbereiten oder in Roadmap-Dokumentation aufnehmen.

---

## ARCHIVE_AFTER_REVIEW — Ops/Supervisor/Launchd

**Rationale:** feat/salvage-p80, p81, p87, p88, p98, p99 wurden Phase 3 gelöscht (SAFE_DELETE_LOCAL_MERGED). recover/* Duplikate vermutlich redundant.

| Branch |
|--------|
| recover/p80-supervisor-stop-idempotent-v1 |
| recover/p81-supervisor-service-hardening-v1 |
| recover/p87-supervisor-plus-ingest-v1 |
| recover/p88-launchd-supervisor-smoke-script-v1 |
| recover/p98-ops-loop-orchestrator-v1 |
| recover/p99-launchd-hard-guardrails-v1 |
| recover/ops-launchd-supervisor-subcommands-v1 |
| recover/p102-launchd-templates-p93-p94-v1 |

**Nächster Schritt:** `git log main..<branch>` — wenn leer, archivieren/löschen. Wenn nicht leer, diff mit main vergleichen.

---

## LIKELY_ALREADY_ON_MAIN — backup/tmp/wip (archive-noise)

**Rationale:** Explizite Backups, temporäre Branches. Nach Verifizierung löschbar.

- backup/* (7)
- tmp/docs-runbook-to-finish-clean
- wip/local-*, wip/restore-* (4)

**Nächster Schritt:** `git log main..<branch>` — leer → `git branch -d`.

---

## MANUAL_DEEP_REVIEW — recover-ops, stash-wip-salvage, unknown

**Rationale:** Gemischte Gruppe. Keine klare Priorität ohne tiefere Prüfung.

- recover-ops (20 Branches): p13, p22, p101, p105, p111, p64–p66, p75, p92, p94, p97, p99, pr-ops, pr-trigger, p118, p54
- stash-wip-salvage: recover/stash-2, stash-3, wip/salvage-*
- unknown: feat/salvage-manual-p22-roadmap-runbook-merge, recover/fix-p76-result-path-in-ticks

**Nächster Schritt:** Gruppenweise Review, ggf. Roadmap-Ablage oder Löschung nach Prüfung.
