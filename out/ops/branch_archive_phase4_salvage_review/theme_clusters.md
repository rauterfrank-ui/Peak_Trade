# Salvage / Recover — Theme Clusters

**Erstellt:** 2026-03-10  
**Modus:** Review-only

---

## 1. execution-networked (8 Branches)

**Bewertung:** Wahrscheinlich noch einzigartig. Roadmap-relevant (p123–p132 Transport-Stubs).

| Branch | Bucket |
|--------|--------|
| recover/p122-execution-runbook-v1 | SALVAGE_REVIEW_REQUIRED |
| recover/p123-execution-networked-onramp-v1 | SALVAGE_REVIEW_REQUIRED |
| recover/p124-execution-networked-entry-contract-v1 | SALVAGE_REVIEW_REQUIRED |
| recover/p126-execution-networked-transport-stub-v1 | SALVAGE_REVIEW_REQUIRED |
| recover/p127-networked-provider-adapter-stub-v1 | SALVAGE_REVIEW_REQUIRED |
| recover/p130-networked-allowlist-stub-v1 | SALVAGE_REVIEW_REQUIRED |
| recover/p132-networked-transport-allow-handshake-v1 | SALVAGE_REVIEW_REQUIRED |
| recover/p128-execution-networked-transport-stub-v1 | skipped_protected |

**Empfehlung:** SALVAGE_NOW — manuelle Prüfung ob Stubs in main fehlen.

---

## 2. ops-supervisor-launchd (8 Branches)

**Bewertung:** Teilweise in main (feat/salvage-* Varianten wurden Phase 3 gelöscht). recover/* noch vorhanden.

| Branch | Bucket |
|--------|--------|
| recover/ops-launchd-supervisor-subcommands-v1 | SALVAGE_REVIEW_REQUIRED |
| recover/p102-launchd-templates-p93-p94-v1 | SALVAGE_REVIEW_REQUIRED |
| recover/p80-supervisor-stop-idempotent-v1 | SALVAGE_REVIEW_REQUIRED |
| recover/p87-supervisor-plus-ingest-v1 | SALVAGE_REVIEW_REQUIRED |
| recover/p88-launchd-supervisor-smoke-script-v1 | SALVAGE_REVIEW_REQUIRED |
| recover/p99-launchd-hard-guardrails-v1 | SALVAGE_REVIEW_REQUIRED |
| recover/p81-supervisor-service-hardening-v1 | skipped_protected |
| recover/p98-ops-loop-orchestrator-v1 | skipped_protected |

**Empfehlung:** ARCHIVE_AFTER_REVIEW oder MANUAL_DEEP_REVIEW — feat/salvage-* bereits gemerged.

---

## 3. archive-noise (12 Branches)

**Bewertung:** backup/tmp/wip — vermutlich entbehrlich nach Prüfung.

| Kategorie | Branches |
|-----------|----------|
| backup/* | 7 |
| tmp/* | 1 |
| wip/local-*, wip/restore-* | 4 |

**Empfehlung:** ARCHIVE_AFTER_REVIEW — `git log main..<branch>` prüfen, leer → löschbar.

---

## 4. recover-ops (20 Branches)

**Bewertung:** Gemischt. Viele p-Nummern, workbook, exchange, adapter, etc.

| Beispiele |
|-----------|
| recover/p13-kickoff, p22-roadmap-runbook-merge |
| recover/p101-workbook-checklists-stop-playbook-v1 |
| recover/p105-exchange-*, p111-execution-adapter-selector-v1 |
| recover/p64-online-readiness-*, p66-online-readiness-operator-entrypoint-v1 |
| recover/p75-p72-env-contract-tests-v1 |
| recover/p92-audit-snapshot-runner-v1, p94-p93-status-dashboard-retention-v1 |
| recover/p97-p96-dry-run-sandbox-smoke, p99-guarded-plist-workingdir-v1 |
| recover/pr-ops-v1-closeout-ff-fix, pr-trigger-triage-v1 |
| recover/p118-sha256sums-no-xargs-v1, p54-switch-layer-routing-v1 (skipped_protected) |

**Empfehlung:** MANUAL_DEEP_REVIEW — gruppenweise Prüfung.

---

## 5. reporting-accounting (5 Branches)

**Bewertung:** Backtest, Accounting, Report-Artifacts.

| Branch |
|--------|
| recover/p28-backtest-loop-positions-cash-v1 |
| recover/p29-accounting-v2-avgcost-realizedpnl |
| recover/p33-report-artifacts-v1 |
| recover/p51-ai-layer-guardrails-audit-v1 |
| recover/p92-audit-snapshot-runner-v1 |

**Empfehlung:** MANUAL_REVIEW — prüfen ob in main.

---

## 6. stash-wip-salvage (4 Branches)

**Bewertung:** Stash-Restore, uncommitted — unsicher.

| Branch |
|--------|
| recover/stash-2, recover/stash-3 |
| wip/salvage-code-tests-untracked-20251224_082521 |
| wip/salvage-dirty-main-20260118 |
| wip/untracked-salvage-20251224_081737 |

**Empfehlung:** MANUAL_DEEP_REVIEW — Inhalt prüfen vor Archiv.

---

## 7. unknown (3 Branches)

| Branch |
|--------|
| feat/salvage-manual-p22-roadmap-runbook-merge |
| recover/fix-p76-result-path-in-ticks |
| wip/untracked-salvage-20251224_081737 |

**Empfehlung:** MANUAL_REVIEW.
