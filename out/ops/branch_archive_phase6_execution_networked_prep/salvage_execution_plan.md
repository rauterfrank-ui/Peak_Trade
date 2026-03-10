# Salvage Execution Plan — Execution-Networked p122–p132

**Erstellt:** 2026-03-10  
**Modus:** Planung

---

## Goal

Integriere 7 STRONGLY_UNIQUE Branches in main via PR. p128 ist bereits auf main.

---

## Salvage-Now (7 Branches)

| Branch | Goal | Why |
|--------|------|-----|
| recover/p124-execution-networked-entry-contract-v1 | PR | entry_contract_v1.py; core execution gating |
| recover/p126-execution-networked-transport-stub-v1 | PR | http_client_stub_v1.py; transport |
| recover/p127-networked-provider-adapter-stub-v1 | PR | base_stub_v1.py; provider adapter |
| recover/p130-networked-allowlist-stub-v1 | PR | allowlist_v1.py; default-deny |
| recover/p132-networked-transport-allow-handshake-v1 | PR | handshake wiring |
| recover/p122-execution-runbook-v1 | PR | execution wiring runbook |
| recover/p123-execution-networked-onramp-v1 | PR | workbook A2Z |

---

## Defer/Archive (1 Branch)

| Branch | Rationale |
|--------|-----------|
| recover/p128-execution-networked-transport-stub-v1 | LIKELY_ALREADY_ON_MAIN; kein diff |

---

## Safety Gates

- PR-basierte Integration
- Kein Force-Push, kein Rebase
- Keine Remote-Mutation außer via PR
- Tests müssen grün sein

---

## Expected Outputs

- 7 PRs (oder 1 konsolidierter PR nach Review)
- `out&#47;ops&#47;branch_archive_phase7_salvage_exec&#47;` — Evidence pro Branch

---

## Go/No-Go

- **Go:** Manuelle Freigabe nach Review von top_candidates.md
- **No-Go:** Konflikte mit main → manuelle Auflösung
