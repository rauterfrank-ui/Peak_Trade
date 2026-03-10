# Salvage / Recover Priority List

**Erstellt:** 2026-03-10  
**Modus:** Review-only, keine Löschung

---

## Hochpriorität (potenziell einzigartige Arbeit)

Branches mit Execution-Networked-Transport / p125–p139-Fragmenten:

| Branch | Kategorie | Hinweis |
|--------|-----------|---------|
| feat/salvage-p123-execution-networked-onramp-v1 | salvage | Execution-Networked Onramp |
| feat/salvage-p124-execution-networked-entry-contract-* | salvage | Entry-Contract |
| feat/salvage-p126-execution-networked-transport-stub-* | salvage | Transport-Stub |
| feat/salvage-p127-networked-provider-adapter-stub-v1 | salvage | Provider-Adapter |
| feat/salvage-p128-execution-networked-transport-stub-* | salvage | Transport-Stub |
| feat/salvage-p130-networked-allowlist-stub-v1 | salvage | Allowlist |
| feat/salvage-p132-networked-transport-allow-handshake | salvage | Handshake |
| recover/p123-execution-networked-onramp-v1 | recover | Duplikat/Recover-Variante |
| recover/p124-execution-networked-entry-contract-v1 | recover | Duplikat |
| recover/p126-execution-networked-transport-stub-v1 | recover | Duplikat |
| recover/p127-networked-provider-adapter-stub-v1 | recover | Duplikat |
| recover/p128-execution-networked-transport-stub-v1 | recover | Duplikat |
| recover/p130-networked-allowlist-stub-v1 | recover | Duplikat |
| recover/p132-networked-transport-allow-handshake-v1 | recover | Duplikat |

**Rationale:** POST_SCAN_DECISION_REPORT nennt p125–p139 Execution-Networked als „Fragmentarisch, KEEP: roadmap debt; dokumentieren“. Diese Branches können Roadmap-relevante Stubs enthalten.

---

## Mittelpriorität (Ops/Launchd/Supervisor)

| Branch | Hinweis |
|--------|---------|
| feat/salvage-p80-supervisor-stop-idempotent-v1 | Supervisor Idempotenz |
| feat/salvage-p81-supervisor-service-hardening-v1 | Supervisor Hardening |
| feat/salvage-p87-supervisor-plus-ingest-v1 | Supervisor + Ingest |
| feat/salvage-p88-launchd-supervisor-smoke-script-v1 | Launchd Smoke |
| feat/salvage-p98-ops-loop-orchestrator-v1 | Ops-Loop-Orchestrator |
| recover/p80-supervisor-stop-idempotent-v1 | Recover-Duplikat |
| recover/p81-supervisor-service-hardening-v1 | Recover-Duplikat |
| recover/p98-ops-loop-orchestrator-v1 | Recover-Duplikat |

---

## Niedrigpriorität (vermutlich in main)

Viele salvage/recover-Branches sind bereits in `git branch --merged main`. Vor Löschung: `git log main..<branch> --oneline` prüfen. Wenn leer → sicher löschbar.
